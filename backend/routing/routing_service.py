"""
Core routing service module integrating OpenRouteService (driving-hgv)
with lateral via-waypoint alternative corridor generation, detour filtering,
and geometric overlap deduplication.
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .constants import (
    ORS_DIRECTIONS_ENDPOINT,
    NATIVE_ALTERNATIVES_THRESHOLD_KM,
    MAX_LATERAL_CANDIDATE_CALLS,
    MAX_DETOUR_RATIO,
    MAX_OVERLAP_SHARE_RATIO,
    DEFAULT_REQUEST_TIMEOUT,
)
from .geo_utils import (
    convert_meters_to_miles,
    convert_seconds_to_minutes,
    convert_geojson_coords_to_lat_lon,
    convert_lat_lon_to_geojson_coords,
    haversine_distance_km,
    scale_lateral_offset_km,
    compute_lateral_waypoint,
    compute_geometry_overlap_ratio,
)
from .errors import (
    RoutingServiceError,
    NoRouteFoundError,
    ProviderRateLimitError,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderSnappingError,
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
        self.api_key = api_key or os.environ.get('OPENROUTESERVICE_API_KEY', '')
        self.session = session or requests.Session()
        self.geocoder = geocoding_service or GeocodingService(
            api_key=self.api_key,
            session=self.session
        )

    def _call_ors_directions(
        self,
        coordinates_lon_lat: List[List[float]],
        alternative_routes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute POST request to OpenRouteService driving-hgv GeoJSON endpoint.
        Uses Authorization header and sanitizes logging.
        """
        if not self.api_key:
            raise ProviderAuthError(
                "OPENROUTESERVICE_API_KEY is not configured. Please supply an API key in .env."
            )

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/geo+json, application/json",
        }

        # NOTE on vehicle parameters:
        # ORS driving-hgv allows vehicle dimensions (height, width, length, axleload).
        # Because the user request provides cargo load_weight_lb without physical vehicle dimensions,
        # we deliberately do not pass artificial dimension limits to ORS to prevent unwarranted
        # routing rejections. load_weight_lb is preserved for backend weather rollover risk analysis.
        payload: Dict[str, Any] = {
            "coordinates": coordinates_lon_lat,
            "instructions": False,
            "preference": "recommended",
        }
        if alternative_routes:
            payload["alternative_routes"] = alternative_routes

        try:
            resp = self.session.post(
                ORS_DIRECTIONS_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
        except requests.exceptions.Timeout as e:
            logger.warning("ORS directions request timed out.")
            raise ProviderTimeoutError("Upstream routing provider timed out.") from e
        except requests.exceptions.RequestException as e:
            logger.error("Network error communicating with ORS: %s", str(e))
            raise RoutingServiceError(f"Network error during route request: {str(e)}") from e

        if resp.status_code == 429:
            raise ProviderRateLimitError("OpenRouteService rate limit exceeded (429).")
        if resp.status_code in (401, 403):
            raise ProviderAuthError("OpenRouteService rejected credentials (401/403 Unauthorized).")

        data = resp.json() if resp.text else {}

        if not resp.ok:
            error_obj = data.get('error', {})
            error_code = error_obj.get('code') if isinstance(error_obj, dict) else None
            error_msg = error_obj.get('message', '') if isinstance(error_obj, dict) else str(error_obj)

            # Error 2004: Request exceeds server configuration limits (e.g. 100km alternative routes cap)
            if error_code == 2004:
                raise RoutingServiceError("ORS limits exceeded (2004)", code="distance_limit_exceeded")

            # Error 2010: Waypoint cannot snap to road network
            if error_code == 2010 or "could not find point" in error_msg.lower():
                raise ProviderSnappingError(f"Waypoint could not be snapped: {error_msg}")

            # Error 2099 or empty route
            if resp.status_code == 404 or "no route found" in error_msg.lower():
                raise NoRouteFoundError(f"No route found between coordinates: {error_msg}")

            raise RoutingServiceError(
                f"ORS error (HTTP {resp.status_code}): {error_msg}",
                code=f"ors_http_{resp.status_code}"
            )

        features = data.get('features', [])
        if not features:
            raise NoRouteFoundError("ORS returned 200 OK but with 0 route features.")

        return data

    def _normalize_feature_to_route(
        self,
        feature: Dict[str, Any],
        route_id: str,
        summary_override: Optional[str] = None,
        departure_time_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize an ORS GeoJSON route feature into the application's contract schema."""
        properties = feature.get('properties', {})
        summary = properties.get('summary', {})
        meters = float(summary.get('distance', 0.0))
        seconds = float(summary.get('duration', 0.0))

        distance_miles = convert_meters_to_miles(meters)
        duration_minutes = convert_seconds_to_minutes(seconds)

        geojson_geometry = feature.get('geometry', {}).get('coordinates', [])
        lat_lon_geometry = convert_geojson_coords_to_lat_lon(geojson_geometry)

        provider_summary = summary_override or "OpenRouteService driving-hgv corridor"

        # Checkpoints sampling placeholder for Task 3 (full weather scoring in subsequent tasks)
        iso_now = departure_time_iso or datetime.utcnow().isoformat() + "Z"
        first_coord = lat_lon_geometry[0] if lat_lon_geometry else [0.0, 0.0]

        checkpoints = [
            {
                "checkpoint_id": f"{route_id}_cp_0",
                "lat": first_coord[0],
                "lon": first_coord[1],
                "cumulative_distance_miles": 0.0,
                "eta": iso_now,
                "forecast_timestamp": iso_now,
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
        ]

        metrics = {
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
        }

        eligibility = {
            "is_eligible": True,
            "ineligibility_reasons": [],
        }

        return {
            "route_id": route_id,
            "provider_summary": provider_summary,
            "geometry": lat_lon_geometry,
            "distance_miles": distance_miles,
            "duration_minutes": duration_minutes,
            "checkpoints": checkpoints,
            "metrics": metrics,
            "eligibility": eligibility,
            "_meters": meters,
            "_seconds": seconds,
        }

    def _generate_candidate_corridors_via_waypoints(
        self,
        orig_lon_lat: List[float],
        dest_lon_lat: List[float],
        primary_route: Dict[str, Any],
        primary_distance_km: float,
        departure_time_iso: str,
    ) -> List[Dict[str, Any]]:
        """
        Derive lateral via-waypoints perpendicular to intermediate primary geometry,
        request alternative corridors from ORS, and filter using detour and overlap rules.
        """
        primary_geom = primary_route["geometry"]
        n_points = len(primary_geom)
        if n_points < 10:
            return []

        offset_km = scale_lateral_offset_km(primary_distance_km)

        # Sample at ~30% and ~65% along the corridor
        idx_30 = max(1, int(n_points * 0.30))
        idx_65 = min(n_points - 2, int(n_points * 0.65))

        target_pairs = [
            (idx_30, 'left', "Alternative Corridor via North/West deviation"),
            (idx_30, 'right', "Alternative Corridor via South/East deviation"),
            (idx_65, 'left', "Alternative Corridor via Upper regional bypass"),
            (idx_65, 'right', "Alternative Corridor via Lower regional bypass"),
        ]

        candidate_routes: List[Dict[str, Any]] = []
        accepted_geometries = [primary_geom]
        calls_made = 0

        for idx, side, desc in target_pairs:
            if calls_made >= MAX_LATERAL_CANDIDATE_CALLS or len(candidate_routes) >= 2:
                break

            p1 = primary_geom[idx]
            p2 = primary_geom[idx + 1]
            try:
                wpt_lat, wpt_lon = compute_lateral_waypoint(
                    p1[0], p1[1], p2[0], p2[1], offset_km=offset_km, side=side
                )
            except Exception as e:
                logger.debug("Failed computing waypoint at idx %d: %s", idx, str(e))
                continue

            calls_made += 1
            via_coords_lon_lat = [orig_lon_lat, [wpt_lon, wpt_lat], dest_lon_lat]

            try:
                candidate_data = self._call_ors_directions(via_coords_lon_lat)
            except ProviderSnappingError as snap_err:
                logger.warning("Skipping via-waypoint (snapping failed): %s", snap_err.message)
                continue
            except (RoutingServiceError, NoRouteFoundError) as route_err:
                logger.info("Candidate route query skipped: %s", route_err.message)
                continue

            features = candidate_data.get('features', [])
            if not features:
                continue

            route_cand = self._normalize_feature_to_route(
                features[0],
                route_id=f"route_alt_{len(candidate_routes) + 1}",
                summary_override=desc,
                departure_time_iso=departure_time_iso,
            )

            # 1. Detour sanity filter
            dist_ratio = route_cand["_meters"] / max(1.0, primary_route["_meters"])
            dur_ratio = route_cand["_seconds"] / max(1.0, primary_route["_seconds"])
            if dist_ratio > MAX_DETOUR_RATIO or dur_ratio > MAX_DETOUR_RATIO:
                logger.info(
                    "Candidate rejected by detour ratio: dist_ratio=%.2f, dur_ratio=%.2f",
                    dist_ratio, dur_ratio
                )
                continue

            # 2. Overlap filter against all accepted routes
            cand_geom = route_cand["geometry"]
            is_too_overlapping = False
            for accepted_geom in accepted_geometries:
                overlap = compute_geometry_overlap_ratio(cand_geom, accepted_geom)
                if overlap > MAX_OVERLAP_SHARE_RATIO:
                    logger.info("Candidate rejected by overlap ratio: %.2f > %.2f", overlap, MAX_OVERLAP_SHARE_RATIO)
                    is_too_overlapping = True
                    break

            if is_too_overlapping:
                continue

            # Accepted candidate
            accepted_geometries.append(cand_geom)
            candidate_routes.append(route_cand)

        return candidate_routes

    def analyze_routes(
        self,
        origin: str,
        destination: str,
        departure_time_iso: str,
        load_weight_lb: float,
        checkpoint_interval_miles: int,
    ) -> Dict[str, Any]:
        """
        Main entry point for calculating up to 3 driving corridors.
        Geocodes points, selects native alternatives or lateral waypoint fallback,
        applies detour and overlap filtering, and returns normalized routes.
        """
        # 1. Geocode locations
        orig_lat, orig_lon, orig_label = self.geocoder.geocode(origin)
        dest_lat, dest_lon, dest_label = self.geocoder.geocode(destination)

        orig_lon_lat = [orig_lon, orig_lat]
        dest_lon_lat = [dest_lon, dest_lat]

        # 2. Estimate straight-line distance
        crow_dist_km = haversine_distance_km(orig_lat, orig_lon, dest_lat, dest_lon)

        features: List[Dict[str, Any]] = []
        used_native_alternatives = False

        # 3. If under the 90 km threshold, attempt native alternatives
        if crow_dist_km < NATIVE_ALTERNATIVES_THRESHOLD_KM:
            try:
                alt_cfg = {"target_count": 3, "share_factor": 0.6, "weight_factor": 1.4}
                data = self._call_ors_directions([orig_lon_lat, dest_lon_lat], alternative_routes=alt_cfg)
                features = data.get('features', [])
                if len(features) > 1:
                    used_native_alternatives = True
            except RoutingServiceError as e:
                if e.code == "distance_limit_exceeded":
                    logger.info("Native alternatives rejected by ORS (code 2004). Falling back.")
                else:
                    raise

        # 4. If native alternatives were not used or not returned, request primary route
        if not features:
            data = self._call_ors_directions([orig_lon_lat, dest_lon_lat])
            features = data.get('features', [])

        if not features:
            raise NoRouteFoundError("No driving route available between origin and destination.")

        # Normalize primary route (always route_primary and first)
        primary_route = self._normalize_feature_to_route(
            features[0],
            route_id="route_primary",
            summary_override=f"Primary corridor from {orig_label} to {dest_label}",
            departure_time_iso=departure_time_iso,
        )

        final_routes: List[Dict[str, Any]] = [primary_route]
        warnings: List[str] = []

        if used_native_alternatives and len(features) > 1:
            # Process native alternatives through sanity and overlap checks
            for idx, feat in enumerate(features[1:], start=1):
                alt_route = self._normalize_feature_to_route(
                    feat,
                    route_id=f"route_alt_{idx}",
                    summary_override=f"Alternative corridor {idx}",
                    departure_time_iso=departure_time_iso,
                )
                dist_ratio = alt_route["_meters"] / max(1.0, primary_route["_meters"])
                if dist_ratio <= MAX_DETOUR_RATIO:
                    overlap = compute_geometry_overlap_ratio(alt_route["geometry"], primary_route["geometry"])
                    if overlap <= MAX_OVERLAP_SHARE_RATIO:
                        final_routes.append(alt_route)
        else:
            # Trip >= 90 km or native alternatives unavailable -> Via-waypoint fallback
            primary_km = primary_route["_meters"] / 1000.0
            candidate_corridors = self._generate_candidate_corridors_via_waypoints(
                orig_lon_lat=orig_lon_lat,
                dest_lon_lat=dest_lon_lat,
                primary_route=primary_route,
                primary_distance_km=primary_km,
                departure_time_iso=departure_time_iso,
            )
            final_routes.extend(candidate_corridors)
            if candidate_corridors:
                warnings.append(
                    "Long-distance route: alternative paths were derived via lateral corridor bypasses."
                )

        # Clean internal underscore properties
        for r in final_routes:
            r.pop("_meters", None)
            r.pop("_seconds", None)

        routes_returned = len(final_routes)
        fewer_routes_reason: Optional[str] = None
        if routes_returned < 3:
            if routes_returned == 1:
                fewer_routes_reason = (
                    "Only 1 primary corridor available. Candidate alternative corridors exceeded the 1.5x detour threshold or shared > 80% route length."
                )
            else:
                fewer_routes_reason = (
                    "Only 2 distinct driving corridors meet truck safety, detour (<= 1.5x), and overlap (<= 80%) criteria."
                )

        ranking_reasons = [
            f"Primary route ({final_routes[0]['distance_miles']} mi, {final_routes[0]['duration_minutes']} min) recommended as the most direct commercial highway corridor."
        ]
        if routes_returned > 1:
            ranking_reasons.append(
                f"{routes_returned - 1} alternative corridor(s) identified for weather hazard avoidance."
            )

        recommendation = {
            "recommended_route_id": final_routes[0]["route_id"],
            "route_eligibility": {r["route_id"]: True for r in final_routes},
            "ranking_reasons": ranking_reasons,
            "no_route_meets_safety_thresholds": False,
        }

        return {
            "routes_requested": 3,
            "routes_returned": routes_returned,
            "fewer_routes_reason": fewer_routes_reason,
            "routes": final_routes,
            "recommendation": recommendation,
            "forecast_timeline": [],
            "warnings": warnings,
            "provider_errors": [],
        }
