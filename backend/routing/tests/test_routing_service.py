import pytest
from unittest.mock import MagicMock, patch
import requests
from django.core.cache import cache

from routing.routing_service import RoutingService
from routing.geocoding_service import GeocodingService
from routing.errors import (
    GeocodingError,
    NoRouteFoundError,
    ProviderRateLimitError,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderSnappingError,
)


def make_mock_ors_feature(distance_m=800000.0, duration_s=28800.0, coordinates=None):
    """Generate a realistic mock ORS GeoJSON feature with [lon, lat] coordinates."""
    if coordinates is None:
        # Default 20-point polyline from Denver to Salt Lake City
        coordinates = [
            [-104.9903 + i * (-111.8910 - -104.9903) / 19, 39.7392 + i * (40.7608 - 39.7392) / 19]
            for i in range(20)
        ]
    return {
        "type": "Feature",
        "properties": {
            "summary": {
                "distance": distance_m,
                "duration": duration_s,
            }
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates,
        },
    }


@pytest.fixture
def mock_geocoder():
    cache.clear()
    geocoder = MagicMock(spec=GeocodingService)
    # Default: Denver and Salt Lake City
    geocoder.geocode.side_effect = lambda query: {
        "Denver, CO": (39.7392, -104.9903, "Denver, CO, USA"),
        "Salt Lake City, UT": (40.7608, -111.8910, "Salt Lake City, UT, USA"),
        "Boulder, CO": (40.0150, -105.2705, "Boulder, CO, USA"),
        "Fort Collins, CO": (40.5853, -105.0844, "Fort Collins, CO, USA"),
    }.get(query, (39.7392, -104.9903, query))
    return geocoder


@pytest.fixture
def routing_service(mock_geocoder):
    service = RoutingService(api_key="mock_test_key", geocoding_service=mock_geocoder)
    return service


class TestRoutingServiceMocked:

    def test_short_route_attempts_native_alternatives(self, routing_service):
        """Short route (< 90 km, e.g. Boulder to Fort Collins ~ 70 km) should request native alternatives."""
        routing_service.geocoder.geocode.side_effect = lambda q: {
            "Boulder, CO": (40.0150, -105.2705, "Boulder, CO"),
            "Fort Collins, CO": (40.5853, -105.0844, "Fort Collins, CO"),
        }[q]

        # Return 2 native features from ORS
        feature1 = make_mock_ors_feature(distance_m=72000.0, duration_s=3600.0)
        feature2 = make_mock_ors_feature(
            distance_m=78000.0,
            duration_s=3900.0,
            coordinates=[[-105.2705, 40.0150], [-105.15, 40.30], [-105.0844, 40.5853]]
        )

        with patch.object(routing_service, '_call_ors_directions') as mock_call:
            mock_call.return_value = {"features": [feature1, feature2]}

            result = routing_service.analyze_routes(
                origin="Boulder, CO",
                destination="Fort Collins, CO",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=40000,
                checkpoint_interval_miles=25,
            )

            assert mock_call.call_count == 1
            # Check alternative_routes was passed in payload
            _, kwargs = mock_call.call_args
            assert "alternative_routes" in kwargs

            assert result["routes_returned"] == 2
            assert result["routes"][0]["route_id"] == "route_primary"
            assert result["routes"][1]["route_id"] == "route_alt_1"
            assert result["fewer_routes_reason"] is not None

    def test_long_route_uses_lateral_via_waypoints_fallback(self, routing_service):
        """Long route (> 90 km, e.g. 600 km trip) should generate via-waypoint corridors."""
        primary_feature = make_mock_ors_feature(distance_m=800000.0, duration_s=28800.0)

        # Distinct alternative corridor (deviates significantly)
        alt_coords_1 = [
            [-104.9903, 39.7392],
            [-107.0, 41.5],  # Diverges North into Wyoming
            [-110.0, 41.6],
            [-111.8910, 40.7608]
        ]
        alt_feature_1 = make_mock_ors_feature(distance_m=860000.0, duration_s=30000.0, coordinates=alt_coords_1)

        # Second distinct alternative corridor (deviates South through Utah)
        alt_coords_2 = [
            [-104.9903, 39.7392],
            [-107.5, 38.8],  # Diverges South
            [-110.5, 39.2],
            [-111.8910, 40.7608]
        ]
        alt_feature_2 = make_mock_ors_feature(distance_m=890000.0, duration_s=31000.0, coordinates=alt_coords_2)

        with patch.object(routing_service, '_call_ors_directions') as mock_call:
            mock_call.side_effect = [
                {"features": [primary_feature]},  # 1. Primary route
                {"features": [alt_feature_1]},    # 2. First waypoint candidate (North)
                {"features": [alt_feature_2]},    # 3. Second waypoint candidate (South)
            ]

            result = routing_service.analyze_routes(
                origin="Denver, CO",
                destination="Salt Lake City, UT",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=42000,
                checkpoint_interval_miles=25,
            )

            assert result["routes_returned"] == 3
            assert result["routes"][0]["route_id"] == "route_primary"
            assert result["routes"][1]["route_id"] == "route_alt_1"
            assert result["routes"][2]["route_id"] == "route_alt_2"
            assert result["fewer_routes_reason"] is None
            assert len(result["warnings"]) > 0
            assert "lateral corridor" in result["warnings"][0].lower()

    def test_native_alternatives_2004_triggers_automatic_fallback(self, routing_service):
        """When ORS returns 2004 (exceeds server limit for alternatives), it automatically falls back."""
        routing_service.geocoder.geocode.side_effect = lambda q: {
            "Boulder, CO": (40.0150, -105.2705, "Boulder, CO"),
            "Fort Collins, CO": (40.5853, -105.0844, "Fort Collins, CO"),
        }[q]

        from routing.errors import RoutingServiceError
        err_2004 = RoutingServiceError("ORS limits exceeded (2004)", code="distance_limit_exceeded")

        primary_feature = make_mock_ors_feature(distance_m=75000.0, duration_s=3600.0)

        with patch.object(routing_service, '_call_ors_directions') as mock_call:
            # 1. Native alternatives call fails with 2004
            # 2. Primary call succeeds
            # 3..6. Via-waypoint candidate calls return empty or snapping error
            mock_call.side_effect = [
                err_2004,
                {"features": [primary_feature]},
                {"features": []},
                {"features": []},
                {"features": []},
                {"features": []},
            ]

            result = routing_service.analyze_routes(
                origin="Boulder, CO",
                destination="Fort Collins, CO",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=30000,
                checkpoint_interval_miles=10,
            )

            # Successfully fell back to primary route
            assert result["routes_returned"] >= 1
            assert result["routes"][0]["route_id"] == "route_primary"

    def test_snapping_error_2010_skips_bad_candidate_gracefully(self, routing_service):
        """Candidate via-waypoint that fails snapping (error 2010) is skipped without failing the request."""
        primary_feature = make_mock_ors_feature(distance_m=800000.0, duration_s=28800.0)

        alt_coords = [
            [-104.9903, 39.7392],
            [-108.0, 42.0],
            [-111.8910, 40.7608]
        ]
        valid_alt_feature = make_mock_ors_feature(distance_m=850000.0, duration_s=29500.0, coordinates=alt_coords)

        snap_err = ProviderSnappingError("Waypoint could not be snapped (2010)")

        with patch.object(routing_service, '_call_ors_directions') as mock_call:
            mock_call.side_effect = [
                {"features": [primary_feature]},   # Primary call
                snap_err,                          # Candidate 1 fails snapping
                {"features": [valid_alt_feature]}, # Candidate 2 succeeds
                snap_err,                          # Candidate 3 fails snapping
                {"features": []},                  # Candidate 4 returns empty
            ]

            result = routing_service.analyze_routes(
                origin="Denver, CO",
                destination="Salt Lake City, UT",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=42000,
                checkpoint_interval_miles=25,
            )

            # 1 primary + 1 valid alternative = 2 routes
            assert result["routes_returned"] == 2
            assert result["routes"][0]["route_id"] == "route_primary"
            assert result["routes"][1]["route_id"] == "route_alt_1"
            assert result["fewer_routes_reason"] is not None

    def test_detour_ratio_and_overlap_filter_returns_only_one_distinct_route(self, routing_service):
        """When all candidates exceed 1.5x detour or > 80% overlap, only primary route is returned."""
        primary_feature = make_mock_ors_feature(distance_m=500000.0, duration_s=20000.0)

        # Candidate 1: Huge detour (dist_ratio = 1.8x > 1.5x)
        excessive_detour = make_mock_ors_feature(distance_m=900000.0, duration_s=36000.0)

        with patch.object(routing_service, '_call_ors_directions') as mock_call:
            mock_call.side_effect = [
                {"features": [primary_feature]},
                {"features": [excessive_detour]},
                {"features": [excessive_detour]},
                {"features": [excessive_detour]},
                {"features": [excessive_detour]},
            ]

            result = routing_service.analyze_routes(
                origin="Denver, CO",
                destination="Salt Lake City, UT",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=42000,
                checkpoint_interval_miles=25,
            )

            assert result["routes_returned"] == 1
            assert result["routes"][0]["route_id"] == "route_primary"
            assert "Only 1 primary corridor available" in result["fewer_routes_reason"]

    def test_provider_timeout_raises_provider_timeout_error(self, routing_service):
        """Timeout calling ORS raises ProviderTimeoutError."""
        with patch.object(routing_service.session, 'post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Read timeout")

            with pytest.raises(ProviderTimeoutError):
                routing_service.analyze_routes(
                    origin="Denver, CO",
                    destination="Salt Lake City, UT",
                    departure_time_iso="2026-10-23T14:00:00Z",
                    load_weight_lb=42000,
                    checkpoint_interval_miles=25,
                )

    def test_provider_rate_limit_429_raises_provider_rate_limit_error(self, routing_service):
        """HTTP 429 raises ProviderRateLimitError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.ok = False

        with patch.object(routing_service.session, 'post', return_value=mock_resp):
            with pytest.raises(ProviderRateLimitError):
                routing_service.analyze_routes(
                    origin="Denver, CO",
                    destination="Salt Lake City, UT",
                    departure_time_iso="2026-10-23T14:00:00Z",
                    load_weight_lb=42000,
                    checkpoint_interval_miles=25,
                )

    def test_provider_auth_error_401_403_raises_provider_auth_error(self, routing_service):
        """HTTP 401/403 raises ProviderAuthError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.ok = False

        with patch.object(routing_service.session, 'post', return_value=mock_resp):
            with pytest.raises(ProviderAuthError):
                routing_service.analyze_routes(
                    origin="Denver, CO",
                    destination="Salt Lake City, UT",
                    departure_time_iso="2026-10-23T14:00:00Z",
                    load_weight_lb=42000,
                    checkpoint_interval_miles=25,
                )

    def test_geocoding_caches_resolved_locations(self):
        """Repeated geocoding queries hit local cache rather than upstream API."""
        cache.clear()
        geocoder = GeocodingService(api_key="mock_key")

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "features": [
                {
                    "geometry": {"coordinates": [-104.9903, 39.7392]},
                    "properties": {"label": "Denver, CO, USA"},
                }
            ]
        }

        with patch.object(geocoder.session, 'get', return_value=mock_resp) as mock_get:
            # First call -> hits session.get
            lat1, lon1, label1 = geocoder.geocode("Denver, CO")
            assert mock_get.call_count == 1
            assert lat1 == 39.7392
            assert lon1 == -104.9903

            # Second call -> served from cache
            lat2, lon2, label2 = geocoder.geocode("Denver, CO")
            assert mock_get.call_count == 1  # Unchanged!
            assert lat2 == 39.7392
            assert lon2 == -104.9903
