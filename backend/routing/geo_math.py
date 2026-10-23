import math
from typing import List, Tuple

from .constants import (
    BASE_LATERAL_OFFSET_RATIO,
    EARTH_RADIUS_KM,
    KM_PER_DEGREE_LATITUDE,
    KM_PER_DEGREE_LONGITUDE_AT_EQUATOR,
    MAX_LATERAL_OFFSET_KM,
    MILES_PER_METER,
    MIN_LATERAL_OFFSET_KM,
    MINUTES_PER_SECOND,
    OVERLAP_BUFFER_KM,
)


def convert_meters_to_miles(distance_meters: float) -> float:
    return round(float(distance_meters) * MILES_PER_METER, 2)


def convert_seconds_to_minutes(duration_seconds: float) -> float:
    return round(float(duration_seconds) * MINUTES_PER_SECOND, 1)


def convert_geojson_lon_lat_to_leaflet_lat_lon(
    geojson_coordinates: List[List[float]],
) -> List[List[float]]:
    # GeoJSON specification dictates [lon, lat], whereas Leaflet and mapping UIs expect [lat, lon].
    return [[float(coord[1]), float(coord[0])] for coord in geojson_coordinates]


def convert_leaflet_lat_lon_to_geojson_lon_lat(
    leaflet_coordinates: List[List[float]],
) -> List[List[float]]:
    return [[float(coord[1]), float(coord[0])] for coord in leaflet_coordinates]


def haversine_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    phi_origin = math.radians(origin_latitude)
    phi_destination = math.radians(destination_latitude)
    delta_latitude = math.radians(destination_latitude - origin_latitude)
    delta_longitude = math.radians(destination_longitude - origin_longitude)

    haversine_term = (
        math.sin(delta_latitude / 2.0) ** 2
        + math.cos(phi_origin) * math.cos(phi_destination) * math.sin(delta_longitude / 2.0) ** 2
    )
    central_angle_radians = 2.0 * math.atan2(
        math.sqrt(haversine_term), math.sqrt(1.0 - haversine_term)
    )
    return EARTH_RADIUS_KM * central_angle_radians


def compute_polyline_length_km(corridor_coordinates_lat_lon: List[List[float]]) -> float:
    if len(corridor_coordinates_lat_lon) < 2:
        return 0.0
    accumulated_length_km = 0.0
    for segment_index in range(len(corridor_coordinates_lat_lon) - 1):
        accumulated_length_km += haversine_distance_km(
            corridor_coordinates_lat_lon[segment_index][0],
            corridor_coordinates_lat_lon[segment_index][1],
            corridor_coordinates_lat_lon[segment_index + 1][0],
            corridor_coordinates_lat_lon[segment_index + 1][1],
        )
    return accumulated_length_km


def scale_lateral_offset_km(trip_distance_km: float) -> float:
    # A flat offset over-deviates short trips and under-deviates long trips; 8% provides a safe bypass.
    proportional_offset_km = trip_distance_km * BASE_LATERAL_OFFSET_RATIO
    return max(
        MIN_LATERAL_OFFSET_KM,
        min(proportional_offset_km, MAX_LATERAL_OFFSET_KM),
    )


def compute_lateral_waypoint(
    segment_start_lat: float,
    segment_start_lon: float,
    segment_end_lat: float,
    segment_end_lon: float,
    offset_distance_km: float,
    lateral_side: str = "left",
) -> Tuple[float, float]:
    midpoint_latitude = (segment_start_lat + segment_end_lat) / 2.0
    midpoint_longitude = (segment_start_lon + segment_end_lon) / 2.0

    phi_start = math.radians(segment_start_lat)
    phi_end = math.radians(segment_end_lat)
    delta_lon = math.radians(segment_end_lon - segment_start_lon)

    component_y = math.sin(delta_lon) * math.cos(phi_end)
    component_x = math.cos(phi_start) * math.sin(phi_end) - math.sin(phi_start) * math.cos(
        phi_end
    ) * math.cos(delta_lon)
    segment_heading_radians = math.atan2(component_y, component_x)

    perpendicular_heading_radians = (
        segment_heading_radians - math.pi / 2.0
        if lateral_side == "left"
        else segment_heading_radians + math.pi / 2.0
    )

    phi_midpoint = math.radians(midpoint_latitude)
    lambda_midpoint = math.radians(midpoint_longitude)
    angular_distance_radians = offset_distance_km / EARTH_RADIUS_KM

    waypoint_phi = math.asin(
        math.sin(phi_midpoint) * math.cos(angular_distance_radians)
        + math.cos(phi_midpoint)
        * math.sin(angular_distance_radians)
        * math.cos(perpendicular_heading_radians)
    )
    waypoint_lambda = lambda_midpoint + math.atan2(
        math.sin(perpendicular_heading_radians)
        * math.sin(angular_distance_radians)
        * math.cos(phi_midpoint),
        math.cos(angular_distance_radians) - math.sin(phi_midpoint) * math.sin(waypoint_phi),
    )

    return round(math.degrees(waypoint_phi), 6), round(math.degrees(waypoint_lambda), 6)


def point_to_segment_distance_km(
    point_lat: float,
    point_lon: float,
    segment_a_lat: float,
    segment_a_lon: float,
    segment_b_lat: float,
    segment_b_lon: float,
) -> float:
    # Equirectangular projection is locally conformal and avoids spherical trigonometry for micro-segments.
    mid_latitude_radians = math.radians((segment_a_lat + segment_b_lat) / 2.0)
    cos_mid_latitude = math.cos(mid_latitude_radians)

    vector_b_x = (
        (segment_b_lon - segment_a_lon) * KM_PER_DEGREE_LONGITUDE_AT_EQUATOR * cos_mid_latitude
    )
    vector_b_y = (segment_b_lat - segment_a_lat) * KM_PER_DEGREE_LATITUDE
    vector_p_x = (point_lon - segment_a_lon) * KM_PER_DEGREE_LONGITUDE_AT_EQUATOR * cos_mid_latitude
    vector_p_y = (point_lat - segment_a_lat) * KM_PER_DEGREE_LATITUDE

    segment_length_squared = vector_b_x * vector_b_x + vector_b_y * vector_b_y
    if segment_length_squared < 1e-6:
        return math.hypot(vector_p_x, vector_p_y)

    projection_scalar = max(
        0.0,
        min(
            1.0,
            (vector_p_x * vector_b_x + vector_p_y * vector_b_y) / segment_length_squared,
        ),
    )
    projected_x = projection_scalar * vector_b_x
    projected_y = projection_scalar * vector_b_y

    return math.hypot(vector_p_x - projected_x, vector_p_y - projected_y)


def _extract_sample_points(
    corridor_coordinates_lat_lon: List[List[float]],
) -> List[Tuple[float, float, float]]:
    sample_points: List[Tuple[float, float, float]] = []
    for segment_index in range(len(corridor_coordinates_lat_lon) - 1):
        coord_start = corridor_coordinates_lat_lon[segment_index]
        coord_end = corridor_coordinates_lat_lon[segment_index + 1]
        segment_distance_km = haversine_distance_km(
            coord_start[0], coord_start[1], coord_end[0], coord_end[1]
        )
        if segment_distance_km <= 1e-4:
            continue

        step_count = max(1, int(math.ceil(segment_distance_km / 2.0)))
        step_weight_km = segment_distance_km / step_count
        for step in range(step_count):
            fractional_offset = (step + 0.5) / step_count
            sample_lat = coord_start[0] + fractional_offset * (coord_end[0] - coord_start[0])
            sample_lon = coord_start[1] + fractional_offset * (coord_end[1] - coord_start[1])
            sample_points.append((sample_lat, sample_lon, step_weight_km))
    return sample_points


def compute_geometry_overlap_ratio(
    candidate_coordinates_lat_lon: List[List[float]],
    reference_coordinates_lat_lon: List[List[float]],
    corridor_buffer_km: float = OVERLAP_BUFFER_KM,
) -> float:
    total_candidate_length_km = compute_polyline_length_km(candidate_coordinates_lat_lon)
    if total_candidate_length_km <= 1e-4:
        return 1.0

    sample_points = _extract_sample_points(candidate_coordinates_lat_lon)
    if not sample_points:
        return 0.0

    bounding_boxes = []
    for segment_index in range(len(reference_coordinates_lat_lon) - 1):
        ref_start = reference_coordinates_lat_lon[segment_index]
        ref_end = reference_coordinates_lat_lon[segment_index + 1]
        bounding_boxes.append(
            (
                ref_start,
                ref_end,
                min(ref_start[0], ref_end[0]) - (corridor_buffer_km / 110.0),
                max(ref_start[0], ref_end[0]) + (corridor_buffer_km / 110.0),
                min(ref_start[1], ref_end[1]) - (corridor_buffer_km / 80.0),
                max(ref_start[1], ref_end[1]) + (corridor_buffer_km / 80.0),
            )
        )

    matched_length_km = 0.0
    for sample_lat, sample_lon, weight_km in sample_points:
        for ref_start, ref_end, min_lat, max_lat, min_lon, max_lon in bounding_boxes:
            if min_lat <= sample_lat <= max_lat and min_lon <= sample_lon <= max_lon:
                distance_to_segment_km = point_to_segment_distance_km(
                    sample_lat, sample_lon, ref_start[0], ref_start[1], ref_end[0], ref_end[1]
                )
                if distance_to_segment_km <= corridor_buffer_km:
                    matched_length_km += weight_km
                    break

    overlap_proportion = matched_length_km / total_candidate_length_km
    return min(1.0, max(0.0, round(overlap_proportion, 4)))
