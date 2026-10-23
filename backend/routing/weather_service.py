import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.core.cache import cache

from .constants import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    MAX_FORECAST_HORIZON_DAYS,
    MAX_PAST_DEPARTURE_HOURS,
    MAX_WEATHER_COORDINATES_PER_BATCH,
    MIN_FORECAST_HORIZON_HOURS,
    OPEN_METEO_FORECAST_ENDPOINT,
    WEATHER_CACHE_TTL_SECONDS,
    WEATHER_GRID_DECIMALS,
)
from .errors import (
    ProviderRateLimitError,
    ProviderTimeoutError,
    WeatherProviderError,
    WeatherServiceError,
)

logger = logging.getLogger(__name__)


class WeatherService:
    @staticmethod
    def round_to_forecast_grid(latitude: float, longitude: float) -> Tuple[float, float]:
        # Open-Meteo models have ~1-11 km grid resolution; 2 decimals (~1.1 km) groups collocated checkpoints.
        return (
            round(float(latitude), WEATHER_GRID_DECIMALS),
            round(float(longitude), WEATHER_GRID_DECIMALS),
        )

    @staticmethod
    def build_cache_key(latitude: float, longitude: float) -> str:
        return f"weather_grid_{latitude:.2f}_{longitude:.2f}"

    @classmethod
    def compute_required_forecast_days(cls, departure_utc: datetime, max_eta_utc: datetime) -> int:
        current_time_utc = datetime.now(timezone.utc)
        if departure_utc < (current_time_utc - timedelta(hours=MAX_PAST_DEPARTURE_HOURS)):
            raise WeatherServiceError(
                f"Departure time '{departure_utc.isoformat()}' is more than {MAX_PAST_DEPARTURE_HOURS} "
                "hours in the past. Historic weather queries require archive endpoints."
            )

        elapsed_travel_seconds = max(0.0, (max_eta_utc - current_time_utc).total_seconds())
        travel_hours = elapsed_travel_seconds / 3600.0
        # Task 10A requires at least departure + 48 hours for departure window re-evaluation.
        evaluation_window_hours = max(float(MIN_FORECAST_HORIZON_HOURS), travel_hours + 24.0)
        required_days = int(math.ceil(evaluation_window_hours / 24.0))
        return min(max(3, required_days), MAX_FORECAST_HORIZON_DAYS)

    @classmethod
    def fetch_batch_from_open_meteo(
        cls,
        coordinates_batch: List[Tuple[float, float]],
        forecast_days: int,
        session: Optional[requests.Session] = None,
    ) -> List[Dict[str, Any]]:
        if not coordinates_batch:
            return []

        active_session = session or requests.Session()
        latitude_param = ",".join(f"{lat:.2f}" for lat, _ in coordinates_batch)
        longitude_param = ",".join(f"{lon:.2f}" for _, lon in coordinates_batch)

        query_params = {
            "latitude": latitude_param,
            "longitude": longitude_param,
            "hourly": "wind_speed_10m,wind_gusts_10m,rain,showers,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "UTC",
            "forecast_days": forecast_days,
        }

        try:
            response = active_session.get(
                OPEN_METEO_FORECAST_ENDPOINT,
                params=query_params,
                timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout as timeout_error:
            logger.warning(
                "Open-Meteo forecast timed out for %d coordinates",
                len(coordinates_batch),
            )
            raise ProviderTimeoutError("Weather provider request timed out.") from timeout_error
        except requests.exceptions.RequestException as network_error:
            logger.error("Open-Meteo connection error: %s", str(network_error))
            raise WeatherProviderError(
                f"Network failure connecting to weather provider: {str(network_error)}"
            ) from network_error

        if response.status_code == 429:
            raise ProviderRateLimitError("Open-Meteo forecast rate limit exceeded (429).")
        if not response.ok:
            raise WeatherProviderError(
                f"Open-Meteo returned HTTP {response.status_code}: {response.text[:200]}"
            )

        parsed_payload = response.json()
        # Open-Meteo returns a single object for one coordinate, and a list of objects for multiple.
        return parsed_payload if isinstance(parsed_payload, list) else [parsed_payload]

    @staticmethod
    def parse_hourly_forecast(
        forecast_payload: Dict[str, Any],
    ) -> Dict[str, Dict[str, Optional[float]]]:
        hourly_block = forecast_payload.get("hourly", {})
        time_series = hourly_block.get("time", [])
        wind_speeds = hourly_block.get("wind_speed_10m", [])
        wind_gusts = hourly_block.get("wind_gusts_10m", [])
        stratiform_rains = hourly_block.get("rain", [])
        convective_showers = hourly_block.get("showers", [])
        snowfalls = hourly_block.get("snowfall", [])

        hourly_lookup: Dict[str, Dict[str, Optional[float]]] = {}
        for index, raw_time in enumerate(time_series):
            # Normalize Open-Meteo ISO time "2026-10-23T14:00" to UTC "2026-10-23T14:00:00Z"
            normalized_iso = f"{raw_time}:00Z" if len(raw_time) == 16 else raw_time
            rain_val = stratiform_rains[index] if index < len(stratiform_rains) else None
            showers_val = convective_showers[index] if index < len(convective_showers) else None

            # Open-Meteo separates large-scale rain and convective showers; sum yields total liquid precipitation.
            combined_rain: Optional[float] = None
            if rain_val is not None or showers_val is not None:
                combined_rain = round(float(rain_val or 0.0) + float(showers_val or 0.0), 3)

            hourly_lookup[normalized_iso] = {
                "wind_speed_mph": (
                    float(wind_speeds[index])
                    if index < len(wind_speeds) and wind_speeds[index] is not None
                    else None
                ),
                "wind_gusts_mph": (
                    float(wind_gusts[index])
                    if index < len(wind_gusts) and wind_gusts[index] is not None
                    else None
                ),
                "rain_in_per_hr": combined_rain,
                "snow_in_per_hr": (
                    float(snowfalls[index])
                    if index < len(snowfalls) and snowfalls[index] is not None
                    else None
                ),
            }
        return hourly_lookup

    @classmethod
    def load_grid_forecasts(
        cls,
        unique_grid_cells: List[Tuple[float, float]],
        forecast_days: int,
        session: Optional[requests.Session] = None,
    ) -> Dict[Tuple[float, float], Dict[str, Dict[str, Optional[float]]]]:
        grid_forecast_map: Dict[Tuple[float, float], Dict[str, Dict[str, Optional[float]]]] = {}
        missing_cells: List[Tuple[float, float]] = []

        for grid_lat, grid_lon in unique_grid_cells:
            cache_key = cls.build_cache_key(grid_lat, grid_lon)
            cached_forecast = cache.get(cache_key)
            if cached_forecast:
                grid_forecast_map[(grid_lat, grid_lon)] = cached_forecast
            else:
                missing_cells.append((grid_lat, grid_lon))

        for batch_start in range(0, len(missing_cells), MAX_WEATHER_COORDINATES_PER_BATCH):
            batch = missing_cells[batch_start : batch_start + MAX_WEATHER_COORDINATES_PER_BATCH]
            batch_results = cls.fetch_batch_from_open_meteo(batch, forecast_days, session=session)
            for (grid_lat, grid_lon), single_result in zip(batch, batch_results):
                parsed = cls.parse_hourly_forecast(single_result)
                grid_forecast_map[(grid_lat, grid_lon)] = parsed
                cache.set(
                    cls.build_cache_key(grid_lat, grid_lon),
                    parsed,
                    timeout=WEATHER_CACHE_TTL_SECONDS,
                )

        return grid_forecast_map

    @staticmethod
    def select_nearest_forecast_hour(
        hourly_lookup: Dict[str, Dict[str, Optional[float]]],
        checkpoint_eta: str,
    ) -> Tuple[Optional[str], Optional[Dict[str, Optional[float]]]]:
        if not hourly_lookup:
            return None, None

        eta_datetime = datetime.fromisoformat(checkpoint_eta).astimezone(timezone.utc)
        nearest_timestamp: Optional[str] = None
        smallest_delta_seconds = float("inf")

        for iso_timestamp in hourly_lookup:
            forecast_dt = datetime.fromisoformat(iso_timestamp).astimezone(timezone.utc)
            delta_seconds = abs((forecast_dt - eta_datetime).total_seconds())
            if delta_seconds < smallest_delta_seconds:
                smallest_delta_seconds = delta_seconds
                nearest_timestamp = iso_timestamp

        # If checkpoint ETA is more than 3 hours beyond provider horizon, mark as unavailable.
        if smallest_delta_seconds > 10800.0:
            return None, None

        return nearest_timestamp, hourly_lookup.get(nearest_timestamp)

    @classmethod
    def populate_checkpoint_weather(
        cls,
        checkpoint: Dict[str, Any],
        grid_forecast_map: Dict[Tuple[float, float], Dict[str, Dict[str, Optional[float]]]],
    ) -> None:
        grid_coord = cls.round_to_forecast_grid(checkpoint["lat"], checkpoint["lon"])
        hourly_lookup = grid_forecast_map.get(grid_coord, {})
        nearest_hour, weather_data = cls.select_nearest_forecast_hour(
            hourly_lookup, checkpoint["eta"]
        )

        checkpoint["forecast_timestamp"] = nearest_hour
        wind_val = weather_data.get("wind_speed_mph") if weather_data else None
        gust_val = weather_data.get("wind_gusts_mph") if weather_data else None
        rain_val = weather_data.get("rain_in_per_hr") if weather_data else None
        snow_val = weather_data.get("snow_in_per_hr") if weather_data else None

        checkpoint["weather"] = {
            "wind_speed_mph": wind_val,
            "wind_gusts_mph": gust_val,
            "wind_speed_availability": ("available" if wind_val is not None else "unavailable"),
            "rain_in_per_hr": rain_val,
            "rain_availability": ("available" if rain_val is not None else "unavailable"),
            "snow_in_per_hr": snow_val,
            "snow_availability": ("available" if snow_val is not None else "unavailable"),
        }

    @classmethod
    def enrich_corridors_with_weather(
        cls,
        corridors: List[Dict[str, Any]],
        departure_time_iso: str,
        session: Optional[requests.Session] = None,
    ) -> List[str]:
        if not corridors:
            return []

        all_checkpoints: List[Dict[str, Any]] = []
        for corridor in corridors:
            all_checkpoints.extend(corridor.get("checkpoints", []))

        if not all_checkpoints:
            return []

        departure_utc = datetime.fromisoformat(departure_time_iso).astimezone(timezone.utc)
        max_eta_utc = max(
            datetime.fromisoformat(cp["eta"]).astimezone(timezone.utc) for cp in all_checkpoints
        )
        forecast_days = cls.compute_required_forecast_days(departure_utc, max_eta_utc)

        unique_grid_cells = list(
            {cls.round_to_forecast_grid(cp["lat"], cp["lon"]) for cp in all_checkpoints}
        )
        grid_forecast_map = cls.load_grid_forecasts(
            unique_grid_cells, forecast_days, session=session
        )

        for checkpoint in all_checkpoints:
            cls.populate_checkpoint_weather(checkpoint, grid_forecast_map)

        weather_warnings: List[str] = []
        for corridor in corridors:
            route_checkpoints = corridor.get("checkpoints", [])
            total_points = len(route_checkpoints)
            covered_points = sum(
                1
                for cp in route_checkpoints
                if cp["weather"]["wind_speed_availability"] == "available"
            )
            coverage_pct = (
                round((covered_points / total_points) * 100.0, 1) if total_points > 0 else 0.0
            )
            corridor["metrics"]["forecast_coverage_pct"] = coverage_pct
            if coverage_pct < 100.0:
                weather_warnings.append(
                    f"Route {corridor['route_id']} forecast coverage is {coverage_pct}%: "
                    f"{total_points - covered_points} checkpoints lack available forecast data."
                )

        return weather_warnings
