import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from .constants import (
    MAX_CHECKPOINTS_SAFETY_LIMIT,
    MILES_PER_KM,
    MIN_DESTINATION_GAP_MILES,
)
from .geo_math import haversine_distance_km


def parse_and_validate_departure_time(departure_time: Union[str, datetime]) -> datetime:
    if isinstance(departure_time, str):
        cleaned_iso = departure_time.strip()
        try:
            parsed_datetime = datetime.fromisoformat(cleaned_iso)
        except ValueError as parse_error:
            raise ValueError(
                f"Invalid departure_time ISO 8601 string: '{cleaned_iso}'. "
                "Must include timezone offset (e.g. '2026-10-23T14:00:00Z')."
            ) from parse_error
    elif isinstance(departure_time, datetime):
        parsed_datetime = departure_time
    else:
        raise ValueError("departure_time must be an ISO 8601 string or datetime object.")

    if parsed_datetime.tzinfo is None or parsed_datetime.tzinfo.utcoffset(parsed_datetime) is None:
        raise ValueError(
            "departure_time must be timezone-aware with an explicit offset (e.g. UTC 'Z' or '+02:00'). "
            "Naive timestamps are rejected."
        )

    return parsed_datetime.astimezone(timezone.utc)


class CheckpointService:
    @staticmethod
    def compute_scaled_vertex_distances_miles(
        geometry_lat_lon: List[List[float]],
        provider_distance_miles: float,
    ) -> Tuple[List[float], float]:
        if len(geometry_lat_lon) < 2:
            return [0.0] * len(geometry_lat_lon), 0.0

        raw_cumulative_miles: List[float] = [0.0]
        running_total_miles = 0.0

        for segment_index in range(len(geometry_lat_lon) - 1):
            point_a = geometry_lat_lon[segment_index]
            point_b = geometry_lat_lon[segment_index + 1]
            segment_distance_km = haversine_distance_km(
                point_a[0], point_a[1], point_b[0], point_b[1]
            )
            running_total_miles += segment_distance_km * MILES_PER_KM
            raw_cumulative_miles.append(running_total_miles)

        if running_total_miles <= 1e-6 or provider_distance_miles <= 1e-6:
            return [0.0] * len(geometry_lat_lon), running_total_miles

        # Provider distance includes highway ramp geometry and real road curves that straight-line chords underestimate.
        distance_scale_ratio = provider_distance_miles / running_total_miles
        scaled_distances = [d * distance_scale_ratio for d in raw_cumulative_miles]
        scaled_distances[-1] = provider_distance_miles

        return scaled_distances, running_total_miles

    compute_scaled_vertex_distances = compute_scaled_vertex_distances_miles

    @staticmethod
    def interpolate_coordinate_at_distance(
        geometry_lat_lon: List[List[float]],
        scaled_vertex_distances_miles: List[float],
        target_mileage: float,
    ) -> Tuple[float, float]:
        if not geometry_lat_lon:
            return 0.0, 0.0
        if len(geometry_lat_lon) == 1 or target_mileage <= 0.0:
            return geometry_lat_lon[0][0], geometry_lat_lon[0][1]
        if target_mileage >= scaled_vertex_distances_miles[-1]:
            return geometry_lat_lon[-1][0], geometry_lat_lon[-1][1]

        for index in range(len(scaled_vertex_distances_miles) - 1):
            mileage_start = scaled_vertex_distances_miles[index]
            mileage_end = scaled_vertex_distances_miles[index + 1]

            if mileage_start <= target_mileage <= mileage_end:
                segment_span_miles = mileage_end - mileage_start
                if segment_span_miles <= 1e-7:
                    return geometry_lat_lon[index][0], geometry_lat_lon[index][1]

                segment_fraction = (target_mileage - mileage_start) / segment_span_miles
                point_start = geometry_lat_lon[index]
                point_end = geometry_lat_lon[index + 1]

                interpolated_lat = point_start[0] + segment_fraction * (
                    point_end[0] - point_start[0]
                )
                interpolated_lon = point_start[1] + segment_fraction * (
                    point_end[1] - point_start[1]
                )
                return round(interpolated_lat, 6), round(interpolated_lon, 6)

        return geometry_lat_lon[-1][0], geometry_lat_lon[-1][1]

    @staticmethod
    def _determine_effective_sampling_interval_miles(
        total_distance_miles: float,
        requested_interval_miles: int,
    ) -> Tuple[int, List[str]]:
        estimated_checkpoint_count = (
            math.ceil(total_distance_miles / max(1, requested_interval_miles)) + 1
        )
        if estimated_checkpoint_count <= MAX_CHECKPOINTS_SAFETY_LIMIT:
            return requested_interval_miles, []

        # Auto-adaptation prevents downstream weather API quotas from blowing up on transcontinental trips.
        safe_interval_miles = max(
            int(math.ceil(total_distance_miles / (MAX_CHECKPOINTS_SAFETY_LIMIT - 2))),
            50,
        )
        adaptation_warning = (
            f"Trip distance ({total_distance_miles:.1f} mi) with requested interval "
            f"({requested_interval_miles} mi) exceeds safety limit of {MAX_CHECKPOINTS_SAFETY_LIMIT} checkpoints. "
            f"Sampling interval automatically adapted to {safe_interval_miles} mi."
        )
        return safe_interval_miles, [adaptation_warning]

    @staticmethod
    def _calculate_target_mileages(
        total_distance_miles: float,
        sampling_interval_miles: int,
    ) -> List[float]:
        target_mileages: List[float] = [0.0]
        current_mileage = float(sampling_interval_miles)

        while current_mileage < (total_distance_miles - MIN_DESTINATION_GAP_MILES):
            target_mileages.append(round(current_mileage, 2))
            current_mileage += float(sampling_interval_miles)

        if total_distance_miles > 0.0:
            target_mileages.append(round(total_distance_miles, 2))

        return target_mileages

    @classmethod
    def generate_checkpoints(
        cls,
        route_id: str,
        geometry_lat_lon: Optional[List[List[float]]] = None,
        total_distance_miles: float = 0.0,
        total_duration_minutes: float = 0.0,
        departure_time: Union[str, datetime] = "",
        interval_miles: int = 25,
        geometry: Optional[List[List[float]]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        route_geometry = geometry_lat_lon if geometry_lat_lon is not None else (geometry or [])
        if len(route_geometry) < 2:
            raise ValueError("Route geometry must contain at least 2 coordinate points.")

        departure_datetime_utc = parse_and_validate_departure_time(departure_time)
        effective_interval, interval_warnings = cls._determine_effective_sampling_interval_miles(
            total_distance_miles, interval_miles
        )

        scaled_distances, _ = cls.compute_scaled_vertex_distances_miles(
            route_geometry, total_distance_miles
        )
        target_mileages = cls._calculate_target_mileages(total_distance_miles, effective_interval)

        checkpoints: List[Dict[str, Any]] = []
        for sequence_index, mileage in enumerate(target_mileages):
            latitude, longitude = cls.interpolate_coordinate_at_distance(
                route_geometry, scaled_distances, mileage
            )

            # Linear time progression along the corridor; assumes steady commercial cruising speed.
            progress_fraction = (
                mileage / total_distance_miles if total_distance_miles > 0.0 else 0.0
            )
            elapsed_travel_minutes = progress_fraction * total_duration_minutes
            estimated_arrival_utc = departure_datetime_utc + timedelta(
                minutes=elapsed_travel_minutes
            )
            eta_iso = estimated_arrival_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            checkpoints.append(
                {
                    "checkpoint_id": f"{route_id}_cp_{sequence_index}",
                    "lat": latitude,
                    "lon": longitude,
                    "cumulative_distance_miles": mileage,
                    "eta": eta_iso,
                    "forecast_timestamp": eta_iso,
                    "weather": {
                        "wind_speed_mph": None,
                        "wind_speed_availability": "missing",
                        "rain_in_per_hr": None,
                        "rain_availability": "missing",
                        "snow_in_per_hr": None,
                        "snow_availability": "missing",
                    },
                    "condition_risks": {
                        "wind_risk": "low",
                        "rain_risk": "low",
                        "snow_risk": "low",
                    },
                    "weather_risk": "low",
                    "load_adjusted_risk": "low",
                    "load_rule_applied": None,
                }
            )

        return checkpoints, interval_warnings
