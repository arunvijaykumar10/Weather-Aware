import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from django.core.cache import cache

from .checkpoint_service import CheckpointService, parse_and_validate_departure_time
from .constants import (
    DEFAULT_CORRIDOR_HALF_WIDTH_MILES,
    DEFAULT_GRID_SAMPLE_INTERVAL_MILES,
    MAX_HEATMAP_GRID_POINTS,
    MAX_TIMELINE_OFFSET_HOURS,
    MILES_PER_KM,
    MIN_TIMELINE_OFFSET_HOURS,
)
from .geo_math import compute_lateral_waypoint, haversine_distance_km
from .risk_engine import evaluate_checkpoint_risk
from .weather_service import WeatherService

logger = logging.getLogger(__name__)


class ForecastTimelineService:
    @staticmethod
    def validate_hour_offset(offset_hours: int) -> int:
        if offset_hours < MIN_TIMELINE_OFFSET_HOURS or offset_hours > MAX_TIMELINE_OFFSET_HOURS:
            raise ValueError(
                f"offset_hours must be between {MIN_TIMELINE_OFFSET_HOURS} and "
                f"{MAX_TIMELINE_OFFSET_HOURS} inclusive. Received: {offset_hours}"
            )
        return offset_hours

    @classmethod
    def evaluate_hourly_entry(
        cls,
        offset_hours: int,
        target_utc: datetime,
        hourly_lookup: Dict[str, Dict[str, Optional[float]]],
        load_weight_lb: float,
    ) -> Dict[str, Any]:
        cls.validate_hour_offset(offset_hours)
        target_iso = target_utc.strftime("%Y-%m-%dT%H:00:00Z")

        nearest_hour, weather_data = WeatherService.select_nearest_forecast_hour(
            hourly_lookup, target_utc.isoformat()
        )

        max_forecast_time = max(hourly_lookup.keys()) if hourly_lookup else None
        availability = "available"

        if max_forecast_time:
            max_dt = datetime.fromisoformat(max_forecast_time).astimezone(timezone.utc)
            if target_utc > max_dt + timedelta(hours=3):
                availability = "beyond_forecast"
                weather_data = None
                nearest_hour = target_iso

        if weather_data is None:
            if availability != "beyond_forecast":
                availability = "unavailable"
            nearest_hour = nearest_hour or target_iso

        wind_val = weather_data.get("wind_speed_mph") if weather_data else None
        gust_val = weather_data.get("wind_gusts_mph") if weather_data else None
        rain_val = weather_data.get("rain_in_per_hr") if weather_data else None
        snow_val = weather_data.get("snow_in_per_hr") if weather_data else None

        if (
            availability == "available"
            and wind_val is None
            and rain_val is None
            and snow_val is None
        ):
            availability = "unavailable"

        risk_assessment = evaluate_checkpoint_risk(
            wind_speed_mph=wind_val,
            wind_gusts_mph=gust_val,
            rain_in_per_hr=rain_val,
            snow_in_per_hr=snow_val,
            load_weight_lb=load_weight_lb,
        )

        return {
            "offset_hours": offset_hours,
            "forecast_timestamp": nearest_hour or target_iso,
            "wind_speed_mph": wind_val,
            "rain_in_per_hr": rain_val,
            "snow_in_per_hr": snow_val,
            "condition_risks": {
                "wind": risk_assessment.wind_risk.value,
                "rain": risk_assessment.rain_risk.value,
                "snow": risk_assessment.snow_risk.value,
            },
            "weather_risk": risk_assessment.weather_risk.value,
            "load_adjusted_risk": risk_assessment.load_adjusted_risk.value,
            "numeric_risk_score": risk_assessment.numeric_risk_score,
            "availability": availability,
        }

    @classmethod
    def generate_point_timeline(
        cls,
        grid_lat: float,
        grid_lon: float,
        departure_utc: datetime,
        grid_forecast_map: Dict[Tuple[float, float], Dict[str, Dict[str, Optional[float]]]],
        load_weight_lb: float,
        target_offset_hour: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        hourly_lookup = grid_forecast_map.get((grid_lat, grid_lon), {})
        offsets = (
            [target_offset_hour]
            if target_offset_hour is not None
            else list(range(MIN_TIMELINE_OFFSET_HOURS, MAX_TIMELINE_OFFSET_HOURS + 1))
        )

        timeline_entries: List[Dict[str, Any]] = []
        for offset_h in offsets:
            target_utc = departure_utc + timedelta(hours=offset_h)
            entry = cls.evaluate_hourly_entry(
                offset_hours=offset_h,
                target_utc=target_utc,
                hourly_lookup=hourly_lookup,
                load_weight_lb=load_weight_lb,
            )
            timeline_entries.append(entry)

        return timeline_entries

    @staticmethod
    def _interpolate_corridor_cross_sections(
        geometry: List[List[float]],
        total_miles: float,
        sample_interval_miles: float,
        corridor_half_width_miles: float,
    ) -> List[Tuple[float, float, float]]:
        if len(geometry) < 2 or total_miles <= 0.0:
            return []

        scaled_distances, _ = CheckpointService.compute_scaled_vertex_distances_miles(
            geometry, total_miles
        )
        sample_mileages = [
            i * sample_interval_miles
            for i in range(math.floor(total_miles / sample_interval_miles) + 1)
        ]
        if total_miles not in sample_mileages and (total_miles - sample_mileages[-1]) > 5.0:
            sample_mileages.append(total_miles)

        cross_section_points: List[Tuple[float, float, float]] = []
        offset_km = corridor_half_width_miles / MILES_PER_KM

        for distance in sample_mileages:
            center_lat, center_lon = CheckpointService.interpolate_coordinate_at_distance(
                geometry, scaled_distances, distance
            )
            cross_section_points.append((center_lat, center_lon, 0.0))

            delta_sample_miles = min(2.0, max(0.5, sample_interval_miles / 4.0))
            coord_prev = CheckpointService.interpolate_coordinate_at_distance(
                geometry, scaled_distances, max(0.0, distance - delta_sample_miles)
            )
            coord_next = CheckpointService.interpolate_coordinate_at_distance(
                geometry, scaled_distances, min(total_miles, distance + delta_sample_miles)
            )

            if (
                haversine_distance_km(coord_prev[0], coord_prev[1], coord_next[0], coord_next[1])
                >= 0.01
            ):
                left_lat, left_lon = compute_lateral_waypoint(
                    coord_prev[0], coord_prev[1], coord_next[0], coord_next[1], offset_km, "left"
                )
                right_lat, right_lon = compute_lateral_waypoint(
                    coord_prev[0], coord_prev[1], coord_next[0], coord_next[1], offset_km, "right"
                )
                cross_section_points.append((left_lat, left_lon, corridor_half_width_miles))
                cross_section_points.append((right_lat, right_lon, -corridor_half_width_miles))

        return cross_section_points

    @classmethod
    def generate_corridor_sample_grid(
        cls,
        corridors: List[Dict[str, Any]],
        sample_interval_miles: float = DEFAULT_GRID_SAMPLE_INTERVAL_MILES,
        corridor_half_width_miles: float = DEFAULT_CORRIDOR_HALF_WIDTH_MILES,
        max_grid_points: int = MAX_HEATMAP_GRID_POINTS,
    ) -> Tuple[List[Dict[str, Any]], bool, List[str]]:
        unique_cells: Set[Tuple[float, float]] = set()
        raw_samples: List[Dict[str, Any]] = []

        for corridor in corridors:
            geometry = corridor.get("geometry", [])
            total_miles = corridor.get("distance_miles", 0.0)
            points = cls._interpolate_corridor_cross_sections(
                geometry=geometry,
                total_miles=total_miles,
                sample_interval_miles=sample_interval_miles,
                corridor_half_width_miles=corridor_half_width_miles,
            )
            for lat, lon, offset_mi in points:
                grid_coord = WeatherService.round_to_forecast_grid(lat, lon)
                if grid_coord not in unique_cells:
                    unique_cells.add(grid_coord)
                    raw_samples.append(
                        {
                            "lat": grid_coord[0],
                            "lon": grid_coord[1],
                            "offset_miles": round(offset_mi, 1),
                        }
                    )

        total_points = len(raw_samples)
        is_capped = total_points > max_grid_points
        warnings: List[str] = []

        if is_capped:
            warnings.append(
                f"Heatmap corridor sample grid capped at {max_grid_points} points "
                f"(requested {total_points})."
            )
            raw_samples = raw_samples[:max_grid_points]

        for index, sample in enumerate(raw_samples):
            sample["point_id"] = f"grid_{index}"

        return raw_samples, is_capped, warnings

    @classmethod
    def determine_forecast_metadata(
        cls,
        grid_cells: List[Tuple[float, float]],
    ) -> Tuple[str, int]:
        now_utc = datetime.now(timezone.utc)
        earliest_fetched_dt: Optional[datetime] = None

        for lat, lon in grid_cells:
            meta = cache.get(f"{WeatherService.build_cache_key(lat, lon)}_meta")
            if meta and isinstance(meta, dict) and "fetched_at" in meta:
                try:
                    fetched_dt = datetime.fromisoformat(meta["fetched_at"]).astimezone(timezone.utc)
                    if earliest_fetched_dt is None or fetched_dt < earliest_fetched_dt:
                        earliest_fetched_dt = fetched_dt
                except (ValueError, TypeError):
                    continue

        if earliest_fetched_dt is None:
            earliest_fetched_dt = now_utc

        age_seconds = max(0, int((now_utc - earliest_fetched_dt).total_seconds()))
        return earliest_fetched_dt.isoformat(), age_seconds

    @classmethod
    def generate_timeline_response(
        cls,
        corridors: List[Dict[str, Any]],
        departure_time_iso: str,
        load_weight_lb: float,
        sample_interval_miles: float = DEFAULT_GRID_SAMPLE_INTERVAL_MILES,
        corridor_half_width_miles: float = DEFAULT_CORRIDOR_HALF_WIDTH_MILES,
        max_grid_points: int = MAX_HEATMAP_GRID_POINTS,
        target_offset_hour: Optional[int] = None,
        operational_warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        departure_utc = parse_and_validate_departure_time(departure_time_iso)
        if target_offset_hour is not None:
            cls.validate_hour_offset(target_offset_hour)

        sample_points, is_capped, cap_warnings = cls.generate_corridor_sample_grid(
            corridors=corridors,
            sample_interval_miles=sample_interval_miles,
            corridor_half_width_miles=corridor_half_width_miles,
            max_grid_points=max_grid_points,
        )

        all_grid_cells: Set[Tuple[float, float]] = set()
        for corridor in corridors:
            for cp in corridor.get("checkpoints", []):
                all_grid_cells.add(WeatherService.round_to_forecast_grid(cp["lat"], cp["lon"]))
        for sample in sample_points:
            all_grid_cells.add((sample["lat"], sample["lon"]))

        max_target_dt = departure_utc + timedelta(
            hours=(
                target_offset_hour if target_offset_hour is not None else MAX_TIMELINE_OFFSET_HOURS
            )
        )
        forecast_days = WeatherService.compute_required_forecast_days(departure_utc, max_target_dt)
        grid_forecast_map = WeatherService.load_grid_forecasts(list(all_grid_cells), forecast_days)

        routes_timeline: List[Dict[str, Any]] = []
        for corridor in corridors:
            checkpoint_timelines: List[Dict[str, Any]] = []
            for cp in corridor.get("checkpoints", []):
                grid_coord = WeatherService.round_to_forecast_grid(cp["lat"], cp["lon"])
                timeline = cls.generate_point_timeline(
                    grid_lat=grid_coord[0],
                    grid_lon=grid_coord[1],
                    departure_utc=departure_utc,
                    grid_forecast_map=grid_forecast_map,
                    load_weight_lb=load_weight_lb,
                    target_offset_hour=target_offset_hour,
                )
                checkpoint_timelines.append(
                    {
                        "checkpoint_id": cp["checkpoint_id"],
                        "lat": cp["lat"],
                        "lon": cp["lon"],
                        "cumulative_distance_miles": cp.get("cumulative_distance_miles", 0.0),
                        "timeline": timeline,
                    }
                )

            routes_timeline.append(
                {
                    "route_id": corridor["route_id"],
                    "checkpoints": checkpoint_timelines,
                }
            )

        for sample in sample_points:
            sample["timeline"] = cls.generate_point_timeline(
                grid_lat=sample["lat"],
                grid_lon=sample["lon"],
                departure_utc=departure_utc,
                grid_forecast_map=grid_forecast_map,
                load_weight_lb=load_weight_lb,
                target_offset_hour=target_offset_hour,
            )

        fetched_at_iso, age_seconds = cls.determine_forecast_metadata(list(all_grid_cells))

        all_warnings: List[str] = list(operational_warnings or [])
        all_warnings.extend(cap_warnings)

        payload: Dict[str, Any] = {
            "departure_time": departure_utc.isoformat(),
            "load_weight_lb": load_weight_lb,
            "forecast_fetched_at": fetched_at_iso,
            "forecast_age_seconds": age_seconds,
            "hour_offsets": (
                [target_offset_hour]
                if target_offset_hour is not None
                else list(range(MIN_TIMELINE_OFFSET_HOURS, MAX_TIMELINE_OFFSET_HOURS + 1))
            ),
            "routes": routes_timeline,
            "corridor_grid": {
                "total_points": len(sample_points),
                "is_capped": is_capped,
                "max_points_cap": max_grid_points,
                "sample_interval_miles": sample_interval_miles,
                "corridor_half_width_miles": corridor_half_width_miles,
                "samples": sample_points,
            },
            "warnings": all_warnings,
        }

        # Measure response size to verify compact payload requirements
        raw_size_bytes = len(json.dumps(payload).encode("utf-8"))
        payload["payload_size_bytes"] = raw_size_bytes
        logger.info(
            "Forecast timeline generated: %d routes, %d grid points, size=%.1f KB",
            len(routes_timeline),
            len(sample_points),
            raw_size_bytes / 1024.0,
        )

        return payload
