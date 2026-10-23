import pytest

from routing.geo_math import (
    compute_geometry_overlap_ratio,
    compute_lateral_waypoint,
    convert_geojson_lon_lat_to_leaflet_lat_lon,
    convert_leaflet_lat_lon_to_geojson_lon_lat,
    convert_meters_to_miles,
    convert_seconds_to_minutes,
    haversine_distance_km,
    scale_lateral_offset_km,
)


@pytest.mark.parametrize(
    "distance_meters,expected_miles",
    [
        (1000.0, 0.62),
        (160934.4, 100.0),
        (0.0, 0.0),
        (8046.72, 5.0),
    ],
)
def test_meters_to_miles_conversion_matches_expected_precision(
    distance_meters: float, expected_miles: float
) -> None:
    assert convert_meters_to_miles(distance_meters) == expected_miles


@pytest.mark.parametrize(
    "duration_seconds,expected_minutes",
    [
        (3600.0, 60.0),
        (90.0, 1.5),
        (0.0, 0.0),
        (180.0, 3.0),
    ],
)
def test_seconds_to_minutes_conversion_matches_expected_precision(
    duration_seconds: float, expected_minutes: float
) -> None:
    assert convert_seconds_to_minutes(duration_seconds) == expected_minutes


def test_geojson_to_leaflet_coordinate_inversion_preserves_order() -> None:
    geojson_coordinates = [[-104.9903, 39.7392], [-111.8910, 40.7608]]
    leaflet_coordinates = convert_geojson_lon_lat_to_leaflet_lat_lon(geojson_coordinates)

    assert leaflet_coordinates == [[39.7392, -104.9903], [40.7608, -111.8910]]
    assert convert_leaflet_lat_lon_to_geojson_lon_lat(leaflet_coordinates) == geojson_coordinates


def test_haversine_distance_between_denver_and_salt_lake_city() -> None:
    distance_km = haversine_distance_km(39.7392, -104.9903, 40.7608, -111.8910)
    # Denver to Salt Lake City great-circle distance is ~600 km.
    assert 590.0 < distance_km < 610.0


@pytest.mark.parametrize(
    "trip_distance_km,expected_offset_km",
    [
        (100.0, 20.0),  # Under floor threshold, clamped to MIN_LATERAL_OFFSET_KM (20 km)
        (500.0, 40.0),  # 500 * 0.08 = 40.0 km
        (1500.0, 80.0),  # Over ceiling threshold, clamped to MAX_LATERAL_OFFSET_KM (80 km)
    ],
)
def test_lateral_offset_clamping_boundary_limits(
    trip_distance_km: float, expected_offset_km: float
) -> None:
    assert scale_lateral_offset_km(trip_distance_km) == expected_offset_km


def test_lateral_waypoint_perpendicular_projection_heading() -> None:
    # Segment runs due North along longitude -100: left projects West, right projects East.
    left_waypoint = compute_lateral_waypoint(
        35.0, -100.0, 37.0, -100.0, offset_distance_km=50.0, lateral_side="left"
    )
    right_waypoint = compute_lateral_waypoint(
        35.0,
        -100.0,
        37.0,
        -100.0,
        offset_distance_km=50.0,
        lateral_side="right",
    )

    assert left_waypoint[1] < -100.0
    assert right_waypoint[1] > -100.0
    assert abs(left_waypoint[0] - 36.0) < 0.1


@pytest.mark.parametrize(
    "candidate_route,reference_route,min_overlap,max_overlap",
    [
        (
            [[39.7, -104.9], [40.2, -108.5], [40.7, -111.8]],
            [[39.7, -104.9], [40.2, -108.5], [40.7, -111.8]],
            1.0,
            1.0,
        ),
        (
            [[39.7, -104.9], [40.2, -108.5], [42.0, -111.8]],
            [[39.7, -104.9], [40.2, -108.5], [40.7, -111.8]],
            0.35,
            0.65,
        ),
        (
            [[40.5, -100.0], [40.5, -95.0]],
            [[40.0, -100.0], [40.0, -95.0]],
            0.0,
            0.0,
        ),
    ],
)
def test_corridor_overlap_ratio_detection(
    candidate_route, reference_route, min_overlap: float, max_overlap: float
) -> None:
    overlap_ratio = compute_geometry_overlap_ratio(candidate_route, reference_route)
    assert min_overlap <= overlap_ratio <= max_overlap
