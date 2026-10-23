import pytest
from routing.geo_utils import (
    convert_meters_to_miles,
    convert_seconds_to_minutes,
    convert_geojson_coords_to_lat_lon,
    convert_lat_lon_to_geojson_coords,
    haversine_distance_km,
    scale_lateral_offset_km,
    compute_lateral_waypoint,
    compute_geometry_overlap_ratio,
)


def test_unit_conversions():
    # 1000 meters ~ 0.62 miles
    assert convert_meters_to_miles(1000.0) == 0.62
    # 160934 meters ~ 100.0 miles
    assert convert_meters_to_miles(160934.4) == 100.0
    # 3600 seconds = 60.0 minutes
    assert convert_seconds_to_minutes(3600.0) == 60.0
    # 90 seconds = 1.5 minutes
    assert convert_seconds_to_minutes(90.0) == 1.5


def test_coordinate_order_conversions():
    # GeoJSON: [lon, lat]
    geojson_coords = [[-104.9903, 39.7392], [-111.8910, 40.7608]]
    # Leaflet / UI: [lat, lon]
    lat_lon_coords = convert_geojson_coords_to_lat_lon(geojson_coords)
    assert lat_lon_coords == [[39.7392, -104.9903], [40.7608, -111.8910]]

    # Round trip
    assert convert_lat_lon_to_geojson_coords(lat_lon_coords) == geojson_coords


def test_haversine_distance():
    # Denver (39.7392, -104.9903) to Salt Lake City (40.7608, -111.8910) ~ 600 km
    dist = haversine_distance_km(39.7392, -104.9903, 40.7608, -111.8910)
    assert 590.0 < dist < 610.0


def test_scale_lateral_offset():
    # Short trip (100 km) -> clamped to minimum 20 km
    assert scale_lateral_offset_km(100.0) == 20.0
    # Long trip (1500 km) -> clamped to maximum 80 km
    assert scale_lateral_offset_km(1500.0) == 80.0
    # Medium trip (500 km) -> 500 * 0.08 = 40 km
    assert scale_lateral_offset_km(500.0) == 40.0


def test_compute_lateral_waypoint():
    # Route heading due North along lon -100: from (35, -100) to (37, -100)
    # Left should project West (more negative longitude), Right should project East
    left_wpt = compute_lateral_waypoint(35.0, -100.0, 37.0, -100.0, offset_km=50.0, side='left')
    right_wpt = compute_lateral_waypoint(35.0, -100.0, 37.0, -100.0, offset_km=50.0, side='right')

    assert left_wpt[1] < -100.0  # West
    assert right_wpt[1] > -100.0  # East
    assert abs(left_wpt[0] - 36.0) < 0.1  # Latitude stays near midpoint


def test_overlap_ratio_identical_routes():
    route_a = [[39.7, -104.9], [40.2, -108.5], [40.7, -111.8]]
    # An identical route must have 1.0 (100%) overlap
    overlap = compute_geometry_overlap_ratio(route_a, route_a)
    assert overlap == 1.0


def test_overlap_ratio_partly_overlapping_routes():
    # Route A and Route B share the first segment (39.7, -104.9) to (40.2, -108.5),
    # but Route B diverges to (42.0, -111.8) while Route A goes to (40.7, -111.8)
    route_a = [[39.7, -104.9], [40.2, -108.5], [40.7, -111.8]]
    route_b = [[39.7, -104.9], [40.2, -108.5], [42.0, -111.8]]

    overlap = compute_geometry_overlap_ratio(route_b, route_a)
    # The first segment is shared, second diverges by > 100km -> overlap should be roughly 45-55%
    assert 0.35 < overlap < 0.65


def test_overlap_ratio_completely_distinct_routes():
    # Parallel routes separated by ~50 km (more than 5 km buffer)
    route_a = [[40.0, -100.0], [40.0, -95.0]]
    route_b = [[40.5, -100.0], [40.5, -95.0]]  # ~55 km North

    overlap = compute_geometry_overlap_ratio(route_b, route_a)
    assert overlap == 0.0
