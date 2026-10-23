"""
Geospatial and mathematical utility functions:
- Unit conversions (meters to miles, seconds to minutes)
- Coordinate system conversions (GeoJSON [lon, lat] <-> Leaflet [lat, lon])
- Great-circle distance (Haversine)
- Lateral via-waypoint calculation
- Overlap ratio calculation between polylines
"""

import math
from typing import List, Tuple
from .constants import (
    METERS_TO_MILES,
    SECONDS_TO_MINUTES,
    BASE_LATERAL_OFFSET_RATIO,
    MIN_LATERAL_OFFSET_KM,
    MAX_LATERAL_OFFSET_KM,
    OVERLAP_BUFFER_KM,
)

EARTH_RADIUS_KM = 6371.0


def convert_meters_to_miles(meters: float) -> float:
    """Convert distance in meters to miles, rounded to 2 decimal places."""
    return round(float(meters) * METERS_TO_MILES, 2)


def convert_seconds_to_minutes(seconds: float) -> float:
    """Convert duration in seconds to minutes, rounded to 1 decimal place."""
    return round(float(seconds) * SECONDS_TO_MINUTES, 1)


def convert_geojson_coords_to_lat_lon(coords: List[List[float]]) -> List[List[float]]:
    """
    Convert GeoJSON coordinate order [longitude, latitude]
    to Leaflet/UI coordinate order [latitude, longitude].
    """
    return [[float(c[1]), float(c[0])] for c in coords]


def convert_lat_lon_to_geojson_coords(coords: List[List[float]]) -> List[List[float]]:
    """
    Convert Leaflet/UI coordinate order [latitude, longitude]
    to GeoJSON / ORS coordinate order [longitude, latitude].
    """
    return [[float(c[1]), float(c[0])] for c in coords]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def compute_polyline_length_km(geometry_lat_lon: List[List[float]]) -> float:
    """Compute total length of a polyline in kilometers."""
    if len(geometry_lat_lon) < 2:
        return 0.0
    total = 0.0
    for i in range(len(geometry_lat_lon) - 1):
        total += haversine_distance_km(
            geometry_lat_lon[i][0],
            geometry_lat_lon[i][1],
            geometry_lat_lon[i + 1][0],
            geometry_lat_lon[i + 1][1],
        )
    return total


def scale_lateral_offset_km(trip_distance_km: float) -> float:
    """
    Scale lateral waypoint offset distance based on total trip length.
    Constrained between MIN_LATERAL_OFFSET_KM and MAX_LATERAL_OFFSET_KM.
    """
    computed = trip_distance_km * BASE_LATERAL_OFFSET_RATIO
    return max(MIN_LATERAL_OFFSET_KM, min(computed, MAX_LATERAL_OFFSET_KM))


def compute_lateral_waypoint(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    offset_km: float,
    side: str = 'left'
) -> Tuple[float, float]:
    """
    Given a segment from (lat1, lon1) to (lat2, lon2), compute a lateral waypoint
    perpendicular to the midpoint of the segment at distance offset_km.
    side: 'left' or 'right' relative to heading.
    """
    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.atan2(y, x)

    # Perpendicular angle
    if side == 'left':
        perp_bearing = bearing - math.pi / 2.0
    else:
        perp_bearing = bearing + math.pi / 2.0

    # Project from midpoint
    mid_phi = math.radians(mid_lat)
    mid_lam = math.radians(mid_lon)
    angular_dist = offset_km / EARTH_RADIUS_KM

    dest_phi = math.asin(
        math.sin(mid_phi) * math.cos(angular_dist)
        + math.cos(mid_phi) * math.sin(angular_dist) * math.cos(perp_bearing)
    )
    dest_lam = mid_lam + math.atan2(
        math.sin(perp_bearing) * math.sin(angular_dist) * math.cos(mid_phi),
        math.cos(angular_dist) - math.sin(mid_phi) * math.sin(dest_phi),
    )

    dest_lat = math.degrees(dest_phi)
    dest_lon = math.degrees(dest_lam)
    return round(dest_lat, 6), round(dest_lon, 6)


def point_to_segment_distance_km(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float
) -> float:
    """
    Approximate minimum distance from point P to segment A-B in kilometers
    using equirectangular projection centered on the segment.
    """
    mean_lat = math.radians((a_lat + b_lat) / 2.0)
    cos_lat = math.cos(mean_lat)

    # Convert coordinates to km relative to A
    ax, ay = 0.0, 0.0
    bx = (b_lon - a_lon) * 111.320 * cos_lat
    by = (b_lat - a_lat) * 110.574
    px = (p_lon - a_lon) * 111.320 * cos_lat
    py = (p_lat - a_lat) * 110.574

    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-6:
        # A and B are essentially the same point
        return math.hypot(px - ax, py - ay)

    # Projection factor t of P onto line AB
    t = max(0.0, min(1.0, (px * dx + py * dy) / seg_len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy

    return math.hypot(px - proj_x, py - proj_y)


def compute_geometry_overlap_ratio(
    candidate_lat_lon: List[List[float]],
    reference_lat_lon: List[List[float]],
    buffer_km: float = OVERLAP_BUFFER_KM
) -> float:
    """
    Calculate what proportion (0.0 to 1.0) of candidate_lat_lon's total length
    lies within buffer_km of reference_lat_lon's corridor.
    """
    if not candidate_lat_lon or not reference_lat_lon:
        return 0.0

    total_candidate_len = compute_polyline_length_km(candidate_lat_lon)
    if total_candidate_len <= 1e-4:
        return 1.0

    # Sample points along candidate at ~2 km increments
    sample_points: List[Tuple[float, float, float]] = []  # (lat, lon, segment_weight_km)
    accumulated_len = 0.0

    for i in range(len(candidate_lat_lon) - 1):
        p1 = candidate_lat_lon[i]
        p2 = candidate_lat_lon[i + 1]
        seg_dist = haversine_distance_km(p1[0], p1[1], p2[0], p2[1])
        if seg_dist <= 1e-4:
            continue

        steps = max(1, int(math.ceil(seg_dist / 2.0)))
        step_weight = seg_dist / steps
        for s in range(steps):
            frac = (s + 0.5) / steps
            sample_lat = p1[0] + frac * (p2[0] - p1[0])
            sample_lon = p1[1] + frac * (p2[1] - p1[1])
            sample_points.append((sample_lat, sample_lon, step_weight))

    if not sample_points:
        return 0.0

    # Bounding boxes for reference segments to speed up lookup
    ref_segments = []
    for j in range(len(reference_lat_lon) - 1):
        r1 = reference_lat_lon[j]
        r2 = reference_lat_lon[j + 1]
        min_lat = min(r1[0], r2[0]) - (buffer_km / 110.0)
        max_lat = max(r1[0], r2[0]) + (buffer_km / 110.0)
        min_lon = min(r1[1], r2[1]) - (buffer_km / 80.0)
        max_lon = max(r1[1], r2[1]) + (buffer_km / 80.0)
        ref_segments.append((r1, r2, min_lat, max_lat, min_lon, max_lon))

    # Evaluate overlap
    overlapped_length = 0.0
    for s_lat, s_lon, weight in sample_points:
        is_covered = False
        for r1, r2, min_lat, max_lat, min_lon, max_lon in ref_segments:
            if min_lat <= s_lat <= max_lat and min_lon <= s_lon <= max_lon:
                dist = point_to_segment_distance_km(s_lat, s_lon, r1[0], r1[1], r2[0], r2[1])
                if dist <= buffer_km:
                    is_covered = True
                    break
        if is_covered:
            overlapped_length += weight

    ratio = overlapped_length / total_candidate_len
    return min(1.0, max(0.0, round(ratio, 4)))
