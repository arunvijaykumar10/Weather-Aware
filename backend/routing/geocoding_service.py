import hashlib
import logging
import os
import re
from typing import Optional, Tuple

import requests
from django.core.cache import cache

from .constants import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    GEOCODE_CACHE_TTL_SECONDS,
    GRAPHHOPPER_GEOCODE_ENDPOINT,
    ORS_GEOCODE_ENDPOINT,
    is_graphhopper_key,
)
from .errors import (
    GeocodingError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    RoutingServiceError,
)

logger = logging.getLogger(__name__)

# Accepts lat,lon format e.g. "39.7392, -104.9903" to avoid external geocoder round-trips.
DIRECT_COORDINATE_PATTERN = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$")


class GeocodingService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        ors_key = os.environ.get("OPENROUTESERVICE_API_KEY", "").strip()
        gh_key = os.environ.get("GRAPHHOPPER_API_KEY", "").strip()
        routing_provider = os.environ.get("ROUTING_PROVIDER", "").strip().lower()

        if api_key is not None:
            self.api_key = api_key
            self.is_gh = is_graphhopper_key(api_key) or routing_provider == "graphhopper"
        elif routing_provider == "graphhopper" and gh_key:
            self.api_key = gh_key
            self.is_gh = True
        elif routing_provider == "openrouteservice" and ors_key:
            self.api_key = ors_key
            self.is_gh = False
        elif is_graphhopper_key(ors_key):
            self.api_key = ors_key
            self.is_gh = True
        elif gh_key and (not ors_key or is_graphhopper_key(gh_key)):
            self.api_key = gh_key
            self.is_gh = True
        else:
            self.api_key = ors_key
            self.is_gh = False

        self.session = session or requests.Session()

    def _parse_direct_coordinates(self, query: str) -> Optional[Tuple[float, float, str]]:
        match = DIRECT_COORDINATE_PATTERN.match(query)
        if not match:
            return None

        latitude = float(match.group(1))
        longitude = float(match.group(2))
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            raise GeocodingError(f"Coordinates out of bounds: lat={latitude}, lon={longitude}")
        return latitude, longitude, f"{latitude:.4f}, {longitude:.4f}"

    def _fetch_graphhopper_feature(self, query: str) -> Tuple[float, float, str]:
        key = self.api_key or os.environ.get("GRAPHHOPPER_API_KEY", "")
        if not key:
            raise ProviderAuthError(
                "GRAPHHOPPER_API_KEY is not configured. Please supply an API key in .env."
            )
        params = {"q": query, "limit": 1, "key": key}
        try:
            response = self.session.get(
                GRAPHHOPPER_GEOCODE_ENDPOINT,
                params=params,
                timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout as timeout_err:
            raise ProviderTimeoutError(
                f"Geocoding request timed out for '{query}'."
            ) from timeout_err
        except requests.exceptions.RequestException as network_err:
            raise RoutingServiceError(
                f"Network error geocoding '{query}': {network_err}"
            ) from network_err

        if response.status_code == 429:
            raise ProviderRateLimitError("GraphHopper geocoding rate limit exceeded (429).")
        if response.status_code in (401, 403):
            raise ProviderAuthError("GraphHopper rejected the API key (401/403 Unauthorized).")
        if not response.ok:
            raise GeocodingError(
                f"Geocoding failed for '{query}' with HTTP {response.status_code}."
            )

        payload = response.json()
        hits = payload.get("hits", [])
        if not hits:
            raise GeocodingError(f"Location not found: '{query}'.")
        first_hit = hits[0]
        point = first_hit.get("point", {})
        lat = float(point.get("lat"))
        lon = float(point.get("lng"))
        name = first_hit.get("name") or query
        state = first_hit.get("state")
        label = f"{name}, {state}" if state else name
        return lat, lon, label

    def _fetch_pelias_feature(self, query: str) -> dict:
        if not self.api_key:
            raise ProviderAuthError(
                "OPENROUTESERVICE_API_KEY is not configured. Please supply an API key in .env."
            )

        # Do not log auth header values to prevent credential exposure in logs.
        request_headers = {
            "Authorization": self.api_key,
            "Accept": "application/json, application/geo+json",
        }
        request_params = {"text": query, "size": 1}

        try:
            response = self.session.get(
                ORS_GEOCODE_ENDPOINT,
                headers=request_headers,
                params=request_params,
                timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout as timeout_err:
            logger.warning("Geocoding request timed out for location: %s", query)
            raise ProviderTimeoutError(
                f"Geocoding request timed out for '{query}'."
            ) from timeout_err
        except requests.exceptions.RequestException as network_err:
            logger.error("Network error during geocoding: %s", str(network_err))
            raise RoutingServiceError(
                f"Network error geocoding '{query}': {str(network_err)}"
            ) from network_err

        if response.status_code == 429:
            raise ProviderRateLimitError("OpenRouteService geocoding rate limit exceeded (429).")
        if response.status_code in (401, 403):
            raise ProviderAuthError("OpenRouteService rejected the API key (401/403 Unauthorized).")
        if not response.ok:
            raise GeocodingError(
                f"Geocoding failed for '{query}' with HTTP {response.status_code}."
            )

        pelias_payload = response.json()
        features = pelias_payload.get("features", [])
        if not features:
            raise GeocodingError(f"Location not found: '{query}'.")
        return features[0]

    def _extract_coordinates_from_feature(
        self, feature: dict, fallback_query: str
    ) -> Tuple[float, float, str]:
        geometry = feature.get("geometry", {})
        coordinate_pair = geometry.get("coordinates", [])
        if len(coordinate_pair) < 2:
            raise GeocodingError(f"Invalid coordinate format returned for '{fallback_query}'.")

        # GeoJSON standard specifies [longitude, latitude] ordering.
        longitude = float(coordinate_pair[0])
        latitude = float(coordinate_pair[1])
        properties = feature.get("properties", {})
        display_label = properties.get("label") or properties.get("name") or fallback_query
        return latitude, longitude, display_label

    def geocode(self, query: str) -> Tuple[float, float, str]:
        cleaned_query = query.strip()
        if not cleaned_query:
            raise GeocodingError("Location query cannot be empty.")

        direct_coordinates = self._parse_direct_coordinates(cleaned_query)
        if direct_coordinates:
            return direct_coordinates

        query_hash = hashlib.sha256(cleaned_query.lower().encode("utf-8")).hexdigest()
        cache_key = f"geocode_{query_hash}"
        cached_entry = cache.get(cache_key)
        if cached_entry:
            return (
                cached_entry["lat"],
                cached_entry["lon"],
                cached_entry["label"],
            )

        if self.is_gh:
            latitude, longitude, display_label = self._fetch_graphhopper_feature(cleaned_query)
        else:
            feature = self._fetch_pelias_feature(cleaned_query)
            latitude, longitude, display_label = self._extract_coordinates_from_feature(
                feature, cleaned_query
            )

        cache.set(
            cache_key,
            {"lat": latitude, "lon": longitude, "label": display_label},
            timeout=GEOCODE_CACHE_TTL_SECONDS,
        )
        return latitude, longitude, display_label
