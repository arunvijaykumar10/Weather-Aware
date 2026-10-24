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
        self.api_key = api_key or os.environ.get("GRAPHHOPPER_API_KEY", "").strip()
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

        latitude, longitude, display_label = self._fetch_graphhopper_feature(cleaned_query)

        cache.set(
            cache_key,
            {"lat": latitude, "lon": longitude, "label": display_label},
            timeout=GEOCODE_CACHE_TTL_SECONDS,
        )
        return latitude, longitude, display_label
