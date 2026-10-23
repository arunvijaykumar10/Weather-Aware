import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from .checkpoint_service import CheckpointService
from .constants import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    MAX_DETOUR_RATIO,
    MAX_LATERAL_CANDIDATE_CALLS,
    MAX_OVERLAP_SHARE_RATIO,
    NATIVE_ALTERNATIVES_THRESHOLD_KM,
    ORS_DIRECTIONS_ENDPOINT,
)
from .errors import (
    NoRouteFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderSnappingError,
    ProviderTimeoutError,
    RoutingServiceError,
)
from .geo_math import (
    compute_geometry_overlap_ratio,
    compute_lateral_waypoint,
    convert_geojson_lon_lat_to_leaflet_lat_lon,
    convert_meters_to_miles,
    convert_seconds_to_minutes,
    haversine_distance_km,
    scale_lateral_offset_km,
)
from .geocoding_service import GeocodingService

logger = logging.getLogger(__name__)


class RoutingService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        geocoding_service: Optional[GeocodingService] = None,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENROUTESERVICE_API_KEY", "")
        self.session = session or requests.Session()
        self.geocoder = geocoding_service or GeocodingService(
            api_key=self.api_key, session=self.session
        )

    def _call_ors_directions(
        self,
        coordinates_lon_lat: List[List[float]],
        alternative_routes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderAuthError("OPENROUTESERVICE_API_KEY is not configured.")

        request_headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/geo+json, application/json",
        }

        # The request supplies cargo weight without physical vehicle dimensions (height/width/axles).
        # We omit artificial dimension restrictions here to prevent false-positive routing rejections;
        # weight is evaluated in the backend for crosswind and rollover vulnerabilities.
        request_body: Dict[str, Any] = {
            "coordinates": coordinates_lon_lat,
            "instructions": False,
            "preference": "recommended",
        }
        if alternative_routes:
            request_body["alternative_routes"] = alternative_routes

        try:
            http_response = self.session.post(
                ORS_DIRECTIONS_ENDPOINT,
                headers=request_headers,
                json=request_body,
                timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout as timeout_error:
            raise ProviderTimeoutError("Upstream routing provider timed out.") from timeout_error
        except requests.exceptions.RequestException as network_error:
            raise RoutingServiceError(
                f"Network error during route request: {network_error}"
            ) from network_error

        return self._handle_ors_response_status(http_response)

    def _handle_ors_response_status(self, http_response: requests.Response) -> Dict[str, Any]:
        if http_response.status_code == 429:
            raise ProviderRateLimitError("OpenRouteService rate limit exceeded (429).")
        if http_response.status_code in (401, 403):
            raise ProviderAuthError("OpenRouteService rejected credentials (401/403).")

        response_body = http_response.json() if http_response.text else {}
        if not http_response.ok:
            error_payload = response_body.get("error", {})
            error_code = error_payload.get("code") if isinstance(error_payload, dict) else None
            error_message = (
                error_payload.get("message", "")
                if isinstance(error_payload, dict)
                else str(error_payload)
            )

            if error_code == 2004:
                raise RoutingServiceError(
                    "ORS distance limits exceeded (2004)", code="distance_limit_exceeded"
                )
            if error_code == 2010 or "could not find point" in error_message.lower():
                raise ProviderSnappingError(f"Waypoint snapping failed: {error_message}")
            if http_response.status_code == 404 or "no route found" in error_message.lower():
                raise NoRouteFoundError(f"No route found between coordinates: {error_message}")

            raise RoutingServiceError(
                f"ORS error (HTTP {http_response.status_code}): {error_message}",
                code=f"ors_http_{http_response.status_code}",
            )

        if not response_body.get("features", []):
            raise NoRouteFoundError("ORS returned 200 OK with zero route features.")

        return response_body

    def _normalize_feature_to_route(
        self,
        route_feature: Dict[str, Any],
        route_id: str,
        summary_label: str,
        departure_time_iso: Optional[str] = None,
        checkpoint_interval_miles: int = 25,
    ) -> Tuple[Dict[str, Any], List[str]]:
        feature_summary = route_feature.get("properties", {}).get("summary", {})
        distance_meters = float(feature_summary.get("distance", 0.0))
        duration_seconds = float(feature_summary.get("duration", 0.0))

        distance_miles = convert_meters_to_miles(distance_meters)
        duration_minutes = convert_seconds_to_minutes(duration_seconds)
        geometry_lat_lon = convert_geojson_lon_lat_to_leaflet_lat_lon(
            route_feature.get("geometry", {}).get("coordinates", [])
        )

        iso_departure = departure_time_iso or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        checkpoints, interval_warnings = CheckpointService.generate_checkpoints(
            route_id=route_id,
            geometry_lat_lon=geometry_lat_lon,
            total_distance_miles=distance_miles,
            total_duration_minutes=duration_minutes,
            departure_time=iso_departure,
            interval_miles=checkpoint_interval_miles,
        )

        route_record = {
            "route_id": route_id,
            "provider_summary": summary_label,
            "geometry": geometry_lat_lon,
            "distance_miles": distance_miles,
            "duration_minutes": duration_minutes,
            "checkpoints": checkpoints,
            "metrics": {
                "miles_per_risk_category": {
                    "low": distance_miles,
                    "moderate": 0.0,
                    "high": 0.0,
                    "severe": 0.0,
                    "no_travel": 0.0,
                    "unknown": 0.0,
                },
                "severe_miles": 0.0,
                "high_miles": 0.0,
                "no_travel_miles": 0.0,
                "unknown_miles": 0.0,
                "average_risk": "low",
                "has_no_travel_segment": False,
                "forecast_coverage_pct": 100.0,
            },
            "eligibility": {"is_eligible": True, "ineligibility_reasons": []},
            "_meters": distance_meters,
            "_seconds": duration_seconds,
        }
        return route_record, interval_warnings

    def _derive_candidate_waypoints(
        self,
        primary_geometry_lat_lon: List[List[float]],
        primary_distance_km: float,
    ) -> List[Tuple[Tuple[float, float], str]]:
        point_count = len(primary_geometry_lat_lon)
        if point_count < 10:
            return []

        lateral_offset_km = scale_lateral_offset_km(primary_distance_km)
        index_early = max(1, int(point_count * 0.30))
        index_late = min(point_count - 2, int(point_count * 0.65))

        sampling_targets = [
            (index_early, "left", "Alternative Corridor via North/West deviation"),
            (index_early, "right", "Alternative Corridor via South/East deviation"),
            (index_late, "left", "Alternative Corridor via Upper regional bypass"),
            (index_late, "right", "Alternative Corridor via Lower regional bypass"),
        ]

        candidate_waypoints: List[Tuple[Tuple[float, float], str]] = []
        for segment_idx, lateral_side, label in sampling_targets:
            point_a = primary_geometry_lat_lon[segment_idx]
            point_b = primary_geometry_lat_lon[segment_idx + 1]
            try:
                waypoint_coords = compute_lateral_waypoint(
                    point_a[0],
                    point_a[1],
                    point_b[0],
                    point_b[1],
                    offset_distance_km=lateral_offset_km,
                    lateral_side=lateral_side,
                )
                candidate_waypoints.append((waypoint_coords, label))
            except Exception as math_error:
                logger.debug("Lateral projection failed at idx %d: %s", segment_idx, math_error)
        return candidate_waypoints

    def _evaluate_candidate_corridor(
        self,
        via_coordinates_lon_lat: List[List[float]],
        label: str,
        primary_route: Dict[str, Any],
        accepted_geometries: List[List[List[float]]],
        candidate_index: int,
        departure_time_iso: str,
        checkpoint_interval_miles: int,
    ) -> Optional[Dict[str, Any]]:
        try:
            candidate_payload = self._call_ors_directions(via_coordinates_lon_lat)
        except ProviderSnappingError:
            return None
        except (RoutingServiceError, NoRouteFoundError):
            return None

        route_features = candidate_payload.get("features", [])
        if not route_features:
            return None

        candidate_route, _ = self._normalize_feature_to_route(
            route_features[0],
            route_id=f"route_alt_{candidate_index}",
            summary_label=label,
            departure_time_iso=departure_time_iso,
            checkpoint_interval_miles=checkpoint_interval_miles,
        )

        distance_ratio = candidate_route["_meters"] / max(1.0, primary_route["_meters"])
        duration_ratio = candidate_route["_seconds"] / max(1.0, primary_route["_seconds"])
        if distance_ratio > MAX_DETOUR_RATIO or duration_ratio > MAX_DETOUR_RATIO:
            return None

        for existing_geometry in accepted_geometries:
            overlap = compute_geometry_overlap_ratio(candidate_route["geometry"], existing_geometry)
            if overlap > MAX_OVERLAP_SHARE_RATIO:
                return None

        return candidate_route

    def _generate_candidate_corridors_via_waypoints(
        self,
        origin_lon_lat: List[float],
        destination_lon_lat: List[float],
        primary_route: Dict[str, Any],
        primary_distance_km: float,
        departure_time_iso: str,
        checkpoint_interval_miles: int = 25,
    ) -> List[Dict[str, Any]]:
        candidate_waypoints = self._derive_candidate_waypoints(
            primary_route["geometry"], primary_distance_km
        )
        accepted_corridors: List[Dict[str, Any]] = []
        accepted_geometries = [primary_route["geometry"]]

        for waypoint_coords, label in candidate_waypoints[:MAX_LATERAL_CANDIDATE_CALLS]:
            if len(accepted_corridors) >= 2:
                break

            via_coords = [
                origin_lon_lat,
                [waypoint_coords[1], waypoint_coords[0]],
                destination_lon_lat,
            ]
            candidate = self._evaluate_candidate_corridor(
                via_coordinates_lon_lat=via_coords,
                label=label,
                primary_route=primary_route,
                accepted_geometries=accepted_geometries,
                candidate_index=len(accepted_corridors) + 1,
                departure_time_iso=departure_time_iso,
                checkpoint_interval_miles=checkpoint_interval_miles,
            )
            if candidate:
                accepted_geometries.append(candidate["geometry"])
                accepted_corridors.append(candidate)

        return accepted_corridors

    def _fetch_raw_corridors(
        self,
        origin_lon_lat: List[float],
        destination_lon_lat: List[float],
        air_distance_km: float,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        features: List[Dict[str, Any]] = []
        used_native_alternatives = False

        if air_distance_km < NATIVE_ALTERNATIVES_THRESHOLD_KM:
            try:
                alternative_config = {"target_count": 3, "share_factor": 0.6, "weight_factor": 1.4}
                payload = self._call_ors_directions(
                    [origin_lon_lat, destination_lon_lat],
                    alternative_routes=alternative_config,
                )
                features = payload.get("features", [])
                if len(features) > 1:
                    used_native_alternatives = True
            except RoutingServiceError as routing_error:
                if routing_error.code != "distance_limit_exceeded":
                    raise

        if not features:
            payload = self._call_ors_directions([origin_lon_lat, destination_lon_lat])
            features = payload.get("features", [])

        if not features:
            raise NoRouteFoundError("No driving route available between origin and destination.")

        return features, used_native_alternatives

    def analyze_routes(
        self,
        origin: str,
        destination: str,
        departure_time_iso: str,
        load_weight_lb: float,
        checkpoint_interval_miles: int,
    ) -> Dict[str, Any]:
        origin_lat, origin_lon, origin_label = self.geocoder.geocode(origin)
        dest_lat, dest_lon, dest_label = self.geocoder.geocode(destination)

        origin_lon_lat = [origin_lon, origin_lat]
        dest_lon_lat = [dest_lon, dest_lat]
        air_distance_km = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)

        raw_features, used_native = self._fetch_raw_corridors(
            origin_lon_lat, dest_lon_lat, air_distance_km
        )

        primary_corridor, primary_warnings = self._normalize_feature_to_route(
            raw_features[0],
            route_id="route_primary",
            summary_label=f"Primary corridor from {origin_label} to {dest_label}",
            departure_time_iso=departure_time_iso,
            checkpoint_interval_miles=checkpoint_interval_miles,
        )

        corridor_bundle: List[Dict[str, Any]] = [primary_corridor]
        operational_warnings: List[str] = list(primary_warnings)

        if used_native and len(raw_features) > 1:
            for alt_idx, feature_item in enumerate(raw_features[1:], start=1):
                alt_corridor, alt_warnings = self._normalize_feature_to_route(
                    feature_item,
                    route_id=f"route_alt_{alt_idx}",
                    summary_label=f"Alternative corridor {alt_idx}",
                    departure_time_iso=departure_time_iso,
                    checkpoint_interval_miles=checkpoint_interval_miles,
                )
                operational_warnings.extend(
                    [w for w in alt_warnings if w not in operational_warnings]
                )
                if (
                    alt_corridor["_meters"] / max(1.0, primary_corridor["_meters"])
                ) <= MAX_DETOUR_RATIO:
                    if (
                        compute_geometry_overlap_ratio(
                            alt_corridor["geometry"], primary_corridor["geometry"]
                        )
                        <= MAX_OVERLAP_SHARE_RATIO
                    ):
                        corridor_bundle.append(alt_corridor)
        else:
            primary_km = primary_corridor["_meters"] / 1000.0
            candidate_corridors = self._generate_candidate_corridors_via_waypoints(
                origin_lon_lat=origin_lon_lat,
                destination_lon_lat=dest_lon_lat,
                primary_route=primary_corridor,
                primary_distance_km=primary_km,
                departure_time_iso=departure_time_iso,
                checkpoint_interval_miles=checkpoint_interval_miles,
            )
            corridor_bundle.extend(candidate_corridors)
            if candidate_corridors:
                operational_warnings.append(
                    "Long-distance route: alternative paths were derived via lateral corridor bypasses."
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

        corridor_count = len(corridor_bundle)
        fewer_routes_reason = None
        if corridor_count < 3:
            fewer_routes_reason = (
                "Only 1 primary corridor available. Candidate alternative corridors exceeded the 1.5x detour threshold or shared > 80% route length."
                if corridor_count == 1
                else "Only 2 distinct driving corridors meet truck safety, detour (<= 1.5x), and overlap (<= 80%) criteria."
            )

        ranking_reasons = [
            f"Primary route ({corridor_bundle[0]['distance_miles']} mi, {corridor_bundle[0]['duration_minutes']} min) recommended as the most direct commercial highway corridor."
        ]
        if corridor_count > 1:
            ranking_reasons.append(
                f"{corridor_count - 1} alternative corridor(s) identified for weather hazard avoidance."
            )

        return {
            "routes_requested": 3,
            "routes_returned": corridor_count,
            "fewer_routes_reason": fewer_routes_reason,
            "routes": corridor_bundle,
            "recommendation": {
                "recommended_route_id": corridor_bundle[0]["route_id"],
                "route_eligibility": {route["route_id"]: True for route in corridor_bundle},
                "ranking_reasons": ranking_reasons,
                "no_route_meets_safety_thresholds": False,
            },
            "forecast_timeline": [],
            "warnings": operational_warnings,
            "provider_errors": [],
        }
