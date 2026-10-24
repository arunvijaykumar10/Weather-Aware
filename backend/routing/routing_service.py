import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .checkpoint_service import CheckpointService
from .constants import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    GRAPHHOPPER_ROUTE_ENDPOINT,
    MAX_DETOUR_RATIO,
    MAX_OVERLAP_SHARE_RATIO,
)
from .errors import (
    NoRouteFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    RoutingServiceError,
)
from .geo_math import (
    compute_geometry_overlap_ratio,
    convert_geojson_lon_lat_to_leaflet_lat_lon,
    convert_meters_to_miles,
    convert_seconds_to_minutes,
)
from .geocoding_service import GeocodingService
from .risk_engine import compute_corridor_risk_metrics, evaluate_checkpoint_risk
from .route_scoring_service import rank_and_score_corridors
from .weather_service import WeatherService

logger = logging.getLogger(__name__)


class RoutingService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        geocoding_service: Optional[GeocodingService] = None,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or os.environ.get("GRAPHHOPPER_API_KEY", "").strip()
        self.session = session or requests.Session()
        self.geocoder = geocoding_service or GeocodingService(
            api_key=self.api_key, session=self.session
        )

    def _call_graphhopper_directions(
        self,
        origin_lon_lat: List[float],
        dest_lon_lat: List[float],
        departure_time_iso: str,
        checkpoint_interval_miles: int,
    ) -> List[Dict[str, Any]]:
        key = self.api_key or os.environ.get("GRAPHHOPPER_API_KEY", "")
        if not key:
            raise ProviderAuthError(
                "GRAPHHOPPER_API_KEY is not configured. Please supply an API key in .env."
            )
        params = [
            ("point", f"{origin_lon_lat[1]},{origin_lon_lat[0]}"),
            ("point", f"{dest_lon_lat[1]},{dest_lon_lat[0]}"),
            ("profile", "car"),
            ("algorithm", "alternative_route"),
            ("alternative_route.max_paths", 3),
            ("points_encoded", "false"),
            ("key", key),
        ]
        try:
            resp = self.session.get(
                GRAPHHOPPER_ROUTE_ENDPOINT,
                params=params,
                timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout as timeout_err:
            raise ProviderTimeoutError("GraphHopper routing request timed out.") from timeout_err
        except requests.exceptions.RequestException as net_err:
            raise RoutingServiceError(f"Network error calling GraphHopper: {net_err}") from net_err

        if resp.status_code == 429:
            raise ProviderRateLimitError("GraphHopper rate limit exceeded (429).")
        if resp.status_code in (401, 403):
            raise ProviderAuthError("GraphHopper rejected credentials (401/403).")
        if not resp.ok:
            raise RoutingServiceError(f"GraphHopper error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        paths = data.get("paths", [])
        if not paths:
            raise NoRouteFoundError("No driving route found by GraphHopper.")

        corridors: List[Dict[str, Any]] = []
        route_ids = ["route_primary", "route_alt_1", "route_alt_2"]
        primary_meters = float(paths[0]["distance"]) if paths else 1.0
        primary_geom: Optional[List[List[float]]] = None

        for path in paths[:3]:
            geojson_coords = path["points"]["coordinates"]
            leaflet_geometry = convert_geojson_lon_lat_to_leaflet_lat_lon(geojson_coords)
            distance_meters = float(path["distance"])
            duration_seconds = float(path["time"]) / 1000.0

            # Filter alternatives exceeding detour or geometry overlap thresholds
            if primary_geom is not None:
                if (distance_meters / max(1.0, primary_meters)) > MAX_DETOUR_RATIO:
                    continue
                if (
                    compute_geometry_overlap_ratio(leaflet_geometry, primary_geom)
                    > MAX_OVERLAP_SHARE_RATIO
                ):
                    continue
            else:
                primary_geom = leaflet_geometry

            route_id = (
                route_ids[len(corridors)]
                if len(corridors) < len(route_ids)
                else f"route_alt_{len(corridors)}"
            )
            distance_miles = convert_meters_to_miles(distance_meters)
            duration_minutes = convert_seconds_to_minutes(duration_seconds)

            checkpoints, _ = CheckpointService.generate_checkpoints(
                route_id=route_id,
                geometry_lat_lon=leaflet_geometry,
                total_distance_miles=distance_miles,
                total_duration_minutes=duration_minutes,
                departure_time=departure_time_iso,
                interval_miles=checkpoint_interval_miles,
            )

            corridor_label = (
                "Primary Corridor"
                if len(corridors) == 0
                else f"Commercial Corridor {len(corridors) + 1}"
            )

            corridors.append(
                {
                    "route_id": route_id,
                    "provider_summary": corridor_label,
                    "geometry": leaflet_geometry,
                    "distance_miles": distance_miles,
                    "duration_minutes": duration_minutes,
                    "checkpoints": checkpoints,
                    "metrics": {},
                    "eligibility": {"is_eligible": True, "ineligibility_reasons": []},
                    "_meters": distance_meters,
                    "_seconds": duration_seconds,
                }
            )

        return corridors

    def analyze_routes(
        self,
        origin: str,
        destination: str,
        departure_time_iso: str,
        load_weight_lb: float,
        checkpoint_interval_miles: int,
    ) -> Dict[str, Any]:
        origin_lat, origin_lon, _ = self.geocoder.geocode(origin)
        dest_lat, dest_lon, _ = self.geocoder.geocode(destination)

        origin_lon_lat = [origin_lon, origin_lat]
        dest_lon_lat = [dest_lon, dest_lat]

        corridor_bundle = self._call_graphhopper_directions(
            origin_lon_lat=origin_lon_lat,
            dest_lon_lat=dest_lon_lat,
            departure_time_iso=departure_time_iso,
            checkpoint_interval_miles=checkpoint_interval_miles,
        )
        operational_warnings: List[str] = []

        weather_warnings = WeatherService.enrich_corridors_with_weather(
            corridor_bundle,
            departure_time_iso=departure_time_iso,
            session=self.session,
        )
        for warning in weather_warnings:
            if warning not in operational_warnings:
                operational_warnings.append(warning)

        for corridor in corridor_bundle:
            for checkpoint in corridor.get("checkpoints", []):
                weather_dict = checkpoint.get("weather", {})
                risk_assessment = evaluate_checkpoint_risk(
                    wind_speed_mph=weather_dict.get("wind_speed_mph"),
                    wind_gusts_mph=weather_dict.get("wind_gusts_mph"),
                    rain_in_per_hr=weather_dict.get("rain_in_per_hr"),
                    snow_in_per_hr=weather_dict.get("snow_in_per_hr"),
                    load_weight_lb=load_weight_lb,
                )
                checkpoint.update(risk_assessment.to_dict())

            corridor["metrics"] = compute_corridor_risk_metrics(
                checkpoints=corridor.get("checkpoints", []),
                total_distance_miles=corridor.get("distance_miles", 0.0),
                forecast_coverage_pct=corridor.get("metrics", {}).get(
                    "forecast_coverage_pct", 100.0
                ),
            )

        return self._format_final_analysis_response(corridor_bundle, operational_warnings)

    @staticmethod
    def _format_final_analysis_response(
        corridor_bundle: List[Dict[str, Any]],
        operational_warnings: List[str],
    ) -> Dict[str, Any]:
        for route_record in corridor_bundle:
            route_record.pop("_meters", None)
            route_record.pop("_seconds", None)

        ordered_corridors, recommendation_payload = rank_and_score_corridors(corridor_bundle)

        corridor_count = len(ordered_corridors)
        fewer_routes_reason = None
        if corridor_count < 3:
            fewer_routes_reason = (
                "Only 1 primary corridor available. Candidate alternative corridors exceeded the 1.5x detour threshold or shared > 80% route length."
                if corridor_count == 1
                else "Only 2 distinct driving corridors meet truck safety, detour (<= 1.5x), and overlap (<= 80%) criteria."
            )

        return {
            "routes_requested": 3,
            "routes_returned": corridor_count,
            "fewer_routes_reason": fewer_routes_reason,
            "routes": ordered_corridors,
            "recommendation": recommendation_payload,
            "forecast_timeline": [],
            "warnings": operational_warnings,
            "provider_errors": [],
        }
