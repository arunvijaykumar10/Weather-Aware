"""
Configuration constants and mathematical thresholds for OpenRouteService routing,
alternative corridor derivation, and coordinate conversions.
"""

import os

# Distance threshold: requests under 90 km can attempt native ORS alternatives.
# Requests >= 90 km (or whenever ORS returns error 2004) use lateral via-waypoint fallback.
NATIVE_ALTERNATIVES_THRESHOLD_KM = 90.0

# Lateral via-waypoint scaling constants
BASE_LATERAL_OFFSET_RATIO = 0.08  # 8% of total corridor length
MIN_LATERAL_OFFSET_KM = 20.0       # Minimum lateral displacement (km)
MAX_LATERAL_OFFSET_KM = 80.0       # Maximum lateral displacement (km)

# Rate limiting & quota safety
MAX_LATERAL_CANDIDATE_CALLS = 4    # Strict cap on candidate routing calls per analyze request
DEFAULT_REQUEST_TIMEOUT = (5.0, 15.0)  # (connect timeout, read timeout) in seconds

# Route sanity & filtering thresholds
MAX_DETOUR_RATIO = 1.5             # Reject routes > 1.5x primary distance or duration
MAX_OVERLAP_SHARE_RATIO = 0.80     # Reject candidate routes sharing > 80% length with accepted routes
OVERLAP_BUFFER_KM = 5.0            # Spatial tolerance buffer (km) when checking shared corridors

# Unit conversion factors
METERS_TO_MILES = 0.000621371192
SECONDS_TO_MINUTES = 1.0 / 60.0

# OpenRouteService API endpoints (HeiGIT unified gateway infrastructure)
ORS_BASE_URL = os.environ.get("ORS_BASE_URL", "https://api.heigit.org")
ORS_DIRECTIONS_ENDPOINT = os.environ.get(
    "ORS_DIRECTIONS_ENDPOINT",
    "https://api.heigit.org/openrouteservice/v2/directions/driving-hgv/geojson"
)
ORS_GEOCODE_ENDPOINT = os.environ.get(
    "ORS_GEOCODE_ENDPOINT",
    "https://api.heigit.org/pelias/v1/search"
)

# Caching TTL for geocoded locations (7 days)
GEOCODE_CACHE_TTL_SECONDS = 86400 * 7
