"""
Geocoding service integrating OpenRouteService Pelias geocoder with local caching.
Resolves addresses or raw coordinate inputs into normalized (latitude, longitude).
"""

import os
import re
import logging
import requests
from typing import Tuple
from django.core.cache import cache

from .constants import (
    ORS_GEOCODE_ENDPOINT,
    DEFAULT_REQUEST_TIMEOUT,
    GEOCODE_CACHE_TTL_SECONDS,
)
from .errors import (
    GeocodingError,
    ProviderRateLimitError,
    ProviderAuthError,
    ProviderTimeoutError,
    RoutingServiceError,
)

logger = logging.getLogger(__name__)

# Regex to detect raw coordinate inputs like "39.7392, -104.9903"
COORD_REGEX = re.compile(r'^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$')


class GeocodingService:
    def __init__(self, api_key: str = None, session: requests.Session = None):
        self.api_key = api_key or os.environ.get('OPENROUTESERVICE_API_KEY', '')
        self.session = session or requests.Session()

    def geocode(self, query: str) -> Tuple[float, float, str]:
        """
        Geocode a location query string to (latitude, longitude, display_label).
        Checks for direct coordinate input and caches resolved queries.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            raise GeocodingError("Location query cannot be empty.")

        # 1. Direct coordinate check
        coord_match = COORD_REGEX.match(cleaned_query)
        if coord_match:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return lat, lon, f"{lat:.4f}, {lon:.4f}"
            raise GeocodingError(f"Coordinates out of bounds: lat={lat}, lon={lon}")

        # 2. Cache lookup
        import hashlib
        query_hash = hashlib.sha256(cleaned_query.lower().encode('utf-8')).hexdigest()
        cache_key = f"geocode_{query_hash}"
        cached = cache.get(cache_key)
        if cached:
            return cached['lat'], cached['lon'], cached['label']

        # 3. Upstream Pelias Geocoding request
        if not self.api_key:
            raise ProviderAuthError(
                "OPENROUTESERVICE_API_KEY is not configured. Please supply an API key in .env."
            )

        headers = {
            "Authorization": self.api_key,
            "Accept": "application/json, application/geo+json",
        }
        params = {
            "text": cleaned_query,
            "size": 1,
        }

        try:
            # Note: headers are not logged to protect the API key
            resp = self.session.get(
                ORS_GEOCODE_ENDPOINT,
                headers=headers,
                params=params,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
        except requests.exceptions.Timeout as e:
            logger.warning("Geocoding request timed out for location: %s", cleaned_query)
            raise ProviderTimeoutError(f"Geocoding request timed out for '{cleaned_query}'.") from e
        except requests.exceptions.RequestException as e:
            logger.error("Network error during geocoding: %s", str(e))
            raise RoutingServiceError(f"Network error geocoding '{cleaned_query}': {str(e)}") from e

        if resp.status_code == 429:
            raise ProviderRateLimitError("OpenRouteService geocoding rate limit exceeded (429).")
        if resp.status_code in (401, 403):
            raise ProviderAuthError("OpenRouteService rejected the API key (401/403 Unauthorized).")
        if not resp.ok:
            raise GeocodingError(
                f"Geocoding failed for '{cleaned_query}' with HTTP {resp.status_code}."
            )

        data = resp.json()
        features = data.get('features', [])
        if not features:
            raise GeocodingError(f"Location not found: '{cleaned_query}'.")

        feature = features[0]
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [])
        if len(coordinates) < 2:
            raise GeocodingError(f"Invalid coordinate format returned for '{cleaned_query}'.")

        # GeoJSON is [lon, lat]
        lon = float(coordinates[0])
        lat = float(coordinates[1])
        properties = feature.get('properties', {})
        label = properties.get('label') or properties.get('name') or cleaned_query

        # Cache result
        cache.set(
            cache_key,
            {'lat': lat, 'lon': lon, 'label': label},
            timeout=GEOCODE_CACHE_TTL_SECONDS,
        )

        return lat, lon, label
