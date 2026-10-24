from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.cache import cache

from routing.constants import is_graphhopper_key
from routing.errors import (
    NoRouteFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from routing.geocoding_service import GeocodingService
from routing.routing_service import RoutingService


def make_mock_gh_path(distance_m=800000.0, duration_ms=28800000.0, coordinates=None):
    """Generate a realistic mock GraphHopper path object with [lon, lat] coordinates."""
    if coordinates is None:
        coordinates = [
            [-104.9903 + i * (-111.8910 - -104.9903) / 19, 39.7392 + i * (40.7608 - 39.7392) / 19]
            for i in range(20)
        ]
    return {
        "distance": distance_m,
        "time": duration_ms,
        "points": {
            "type": "LineString",
            "coordinates": coordinates,
        },
    }


@pytest.fixture
def mock_geocoder():
    cache.clear()
    geocoder = MagicMock(spec=GeocodingService)
    geocoder.geocode.side_effect = lambda query: {
        "Denver, CO": (39.7392, -104.9903, "Denver, CO, USA"),
        "Salt Lake City, UT": (40.7608, -111.8910, "Salt Lake City, UT, USA"),
        "Boulder, CO": (40.0150, -105.2705, "Boulder, CO, USA"),
        "Fort Collins, CO": (40.5853, -105.0844, "Fort Collins, CO, USA"),
    }.get(query, (39.7392, -104.9903, query))
    return geocoder


@pytest.fixture
def routing_service(mock_geocoder):
    service = RoutingService(
        api_key="5ac5cb49-da24-412d-a6aa-eda41db9ef70", geocoding_service=mock_geocoder
    )
    return service


@pytest.fixture(autouse=True)
def mock_weather_enrichment_in_routing_service():
    with patch(
        "routing.routing_service.WeatherService.enrich_corridors_with_weather"
    ) as mock_enrich:
        mock_enrich.return_value = []
        yield mock_enrich


class TestRoutingServiceMocked:
    def test_routing_multiple_alternatives_success(self, routing_service):
        """Routing service parses up to 3 paths from GraphHopper and produces distinct corridors."""
        path1 = make_mock_gh_path(distance_m=800000.0, duration_ms=28800000.0)
        alt_coords_1 = [
            [-104.9903, 39.7392],
            [-107.0, 41.5],
            [-110.0, 41.6],
            [-111.8910, 40.7608],
        ]
        path2 = make_mock_gh_path(
            distance_m=830000.0, duration_ms=29800000.0, coordinates=alt_coords_1
        )
        alt_coords_2 = [
            [-104.9903, 39.7392],
            [-107.5, 38.8],
            [-110.5, 39.2],
            [-111.8910, 40.7608],
        ]
        path3 = make_mock_gh_path(
            distance_m=850000.0, duration_ms=30500000.0, coordinates=alt_coords_2
        )

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"paths": [path1, path2, path3]}

        with patch.object(routing_service.session, "get", return_value=mock_resp) as mock_get:
            result = routing_service.analyze_routes(
                origin="Denver, CO",
                destination="Salt Lake City, UT",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=42000,
                checkpoint_interval_miles=25,
            )
            assert mock_get.call_count == 1
            assert result["routes_returned"] == 3
            assert result["routes"][0]["route_id"] == "route_primary"
            assert result["routes"][1]["route_id"] == "route_alt_1"
            assert result["routes"][2]["route_id"] == "route_alt_2"
            assert result["fewer_routes_reason"] is None

    def test_detour_ratio_filters_excessive_alternative(self, routing_service):
        """Alternative paths with detour ratio > 1.5x are filtered out."""
        path1 = make_mock_gh_path(distance_m=500000.0, duration_ms=20000000.0)
        # Excessive detour: 900 km / 500 km = 1.8x > 1.5x
        excessive_path = make_mock_gh_path(distance_m=900000.0, duration_ms=36000000.0)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"paths": [path1, excessive_path]}

        with patch.object(routing_service.session, "get", return_value=mock_resp):
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

    def test_overlap_ratio_filters_duplicate_alternative(self, routing_service):
        """Alternative paths that share > 80% geometry with the primary route are filtered out."""
        path1 = make_mock_gh_path(distance_m=800000.0, duration_ms=28800000.0)
        # Identical geometry (100% overlap)
        duplicate_path = make_mock_gh_path(distance_m=805000.0, duration_ms=29000000.0)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"paths": [path1, duplicate_path]}

        with patch.object(routing_service.session, "get", return_value=mock_resp):
            result = routing_service.analyze_routes(
                origin="Denver, CO",
                destination="Salt Lake City, UT",
                departure_time_iso="2026-10-23T14:00:00Z",
                load_weight_lb=42000,
                checkpoint_interval_miles=25,
            )

            assert result["routes_returned"] == 1
            assert result["routes"][0]["route_id"] == "route_primary"

    def test_provider_timeout_raises_provider_timeout_error(self, routing_service):
        """Timeout calling GraphHopper raises ProviderTimeoutError."""
        with patch.object(routing_service.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Read timeout")

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

        with patch.object(routing_service.session, "get", return_value=mock_resp):
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

        with patch.object(routing_service.session, "get", return_value=mock_resp):
            with pytest.raises(ProviderAuthError):
                routing_service.analyze_routes(
                    origin="Denver, CO",
                    destination="Salt Lake City, UT",
                    departure_time_iso="2026-10-23T14:00:00Z",
                    load_weight_lb=42000,
                    checkpoint_interval_miles=25,
                )

    def test_no_paths_returned_raises_no_route_found_error(self, routing_service):
        """Empty paths list raises NoRouteFoundError."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"paths": []}

        with patch.object(routing_service.session, "get", return_value=mock_resp):
            with pytest.raises(NoRouteFoundError):
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
        geocoder = GeocodingService(api_key="5ac5cb49-da24-412d-a6aa-eda41db9ef70")

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "hits": [
                {
                    "point": {"lat": 39.7392, "lng": -104.9903},
                    "name": "Denver",
                    "state": "Colorado",
                }
            ]
        }

        with patch.object(geocoder.session, "get", return_value=mock_resp) as mock_get:
            lat1, lon1, label1 = geocoder.geocode("Denver, CO")
            assert mock_get.call_count == 1
            assert lat1 == 39.7392
            assert lon1 == -104.9903

            lat2, lon2, label2 = geocoder.geocode("Denver, CO")
            assert mock_get.call_count == 1
            assert lat2 == 39.7392
            assert lon2 == -104.9903


class TestGraphHopperProvider:
    def test_is_graphhopper_key_detection(self):
        valid_uuid = "5ac5cb49-da24-412d-a6aa-eda41db9ef70"
        assert is_graphhopper_key(valid_uuid) is True
        assert is_graphhopper_key(f"  {valid_uuid}  ") is True
        assert is_graphhopper_key("mock_key") is False
        assert is_graphhopper_key("5b3ce3597851110001cf6248d21234567890abcdef") is False
        assert is_graphhopper_key("") is False
        assert is_graphhopper_key(None) is False

    def test_graphhopper_geocoding_parsing(self):
        cache.clear()
        gh_key = "5ac5cb49-da24-412d-a6aa-eda41db9ef70"
        geocoder = GeocodingService(api_key=gh_key)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "hits": [
                {
                    "point": {"lat": 39.7392, "lng": -104.9903},
                    "name": "Denver",
                    "state": "Colorado",
                }
            ]
        }

        with patch.object(geocoder.session, "get", return_value=mock_resp) as mock_get:
            lat, lon, label = geocoder.geocode("Denver, CO")
            assert mock_get.call_count == 1
            assert lat == 39.7392
            assert lon == -104.9903
            assert label == "Denver, Colorado"
