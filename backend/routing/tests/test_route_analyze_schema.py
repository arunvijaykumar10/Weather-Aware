from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    cache.clear()
    return APIClient()


@pytest.fixture
def valid_payload():
    return {
        "origin": "Denver, CO",
        "destination": "Salt Lake City, UT",
        "departure_time": "2026-10-23T14:00:00Z",
        "load_weight_lb": 42000.0,
        "checkpoint_interval_miles": 25,
    }


@pytest.fixture(autouse=True)
def mock_routing_service_in_view():
    with patch("routing.views.RoutingService") as mock_cls:
        service_instance = mock_cls.return_value
        service_instance.analyze_routes.return_value = {
            "routes_requested": 3,
            "routes_returned": 1,
            "fewer_routes_reason": ("Single primary corridor identified in simulation."),
            "routes": [
                {
                    "route_id": "route_primary",
                    "provider_summary": (
                        "Simulated corridor from Denver, CO to Salt Lake City, UT"
                    ),
                    "geometry": [[39.7392, -104.9903], [40.7608, -111.8910]],
                    "distance_miles": 504.2,
                    "duration_minutes": 480.0,
                    "checkpoints": [
                        {
                            "checkpoint_id": "cp_0",
                            "lat": 39.7392,
                            "lon": -104.9903,
                            "cumulative_distance_miles": 0.0,
                            "eta": "2026-10-23T14:00:00Z",
                            "forecast_timestamp": "2026-10-23T14:00:00Z",
                            "weather": {
                                "wind_speed_mph": 12.0,
                                "wind_speed_availability": "available",
                                "rain_in_per_hr": 0.0,
                                "rain_availability": "available",
                                "snow_in_per_hr": 0.0,
                                "snow_availability": "available",
                            },
                            "condition_risks": {
                                "wind_risk": "low",
                                "rain_risk": "low",
                                "snow_risk": "low",
                            },
                            "weather_risk": "low",
                            "load_adjusted_risk": "low",
                            "load_rule_applied": None,
                        }
                    ],
                    "metrics": {
                        "miles_per_risk_category": {
                            "low": 504.2,
                            "moderate": 0.0,
                            "high": 0.0,
                            "severe": 0.0,
                            "no_travel": 0.0,
                            "unknown": 0.0,
                        },
                        "severe_miles": 0.0,
                        "high_miles": 0.0,
                        "no_travel_miles": 0.0,
                        "unknown_miles": 0.0,
                        "average_risk": "low",
                        "has_no_travel_segment": False,
                        "forecast_coverage_pct": 100.0,
                    },
                    "eligibility": {
                        "is_eligible": True,
                        "ineligibility_reasons": [],
                    },
                }
            ],
            "recommendation": {
                "recommended_route_id": "route_primary",
                "route_eligibility": {"route_primary": True},
                "ranking_reasons": ["Optimal road conditions and clear weather."],
                "no_route_meets_safety_thresholds": False,
            },
            "forecast_timeline": [],
            "warnings": [],
            "provider_errors": [],
        }
        yield service_instance


@pytest.mark.django_db
class TestRouteAnalyzeEndpoint:
    url = "/api/routes/analyze/"

    def test_valid_request_returns_200_and_expected_schema(
        self, api_client: APIClient, valid_payload: dict
    ) -> None:
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        analysis_payload = response.json()

        assert "routes_requested" in analysis_payload
        assert "routes_returned" in analysis_payload
        assert "routes" in analysis_payload
        assert "recommendation" in analysis_payload
        assert "forecast_timeline" in analysis_payload
        assert "warnings" in analysis_payload
        assert "provider_errors" in analysis_payload

        assert len(analysis_payload["routes"]) == 1
        evaluated_route = analysis_payload["routes"][0]
        assert "route_id" in evaluated_route
        assert "provider_summary" in evaluated_route
        assert "geometry" in evaluated_route
        assert "distance_miles" in evaluated_route
        assert "duration_minutes" in evaluated_route
        assert "checkpoints" in evaluated_route
        assert "metrics" in evaluated_route
        assert "eligibility" in evaluated_route

        assert len(evaluated_route["checkpoints"]) > 0
        first_checkpoint = evaluated_route["checkpoints"][0]
        assert "checkpoint_id" in first_checkpoint
        assert "lat" in first_checkpoint
        assert "lon" in first_checkpoint
        assert "cumulative_distance_miles" in first_checkpoint
        assert "eta" in first_checkpoint
        assert "weather" in first_checkpoint
        assert "condition_risks" in first_checkpoint
        assert "weather_risk" in first_checkpoint
        assert "load_adjusted_risk" in first_checkpoint
        assert first_checkpoint["weather"]["wind_speed_availability"] in [
            "available",
            "unavailable",
            "missing",
        ]

        recommendation = analysis_payload["recommendation"]
        assert "recommended_route_id" in recommendation
        assert "route_eligibility" in recommendation
        assert "ranking_reasons" in recommendation
        assert "no_route_meets_safety_thresholds" in recommendation

    def test_departure_time_with_numeric_timezone_offset_accepted(
        self, api_client: APIClient, valid_payload: dict
    ) -> None:
        valid_payload["departure_time"] = "2026-10-23T08:00:00-06:00"
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_reject_naive_departure_time_without_timezone_offset(
        self, api_client: APIClient, valid_payload: dict
    ) -> None:
        valid_payload["departure_time"] = "2026-10-23T14:00:00"
        response = api_client.post(self.url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_payload = response.json()
        assert "error" in error_payload
        assert error_payload["error"]["code"] == "validation_error"
        assert "departure_time" in error_payload["error"]["details"]
        assert "timezone" in str(error_payload["error"]["details"]["departure_time"]).lower()

    @pytest.mark.parametrize("invalid_weight", [0, -500.0, -0.01])
    def test_reject_zero_or_negative_load_weight(
        self,
        api_client: APIClient,
        valid_payload: dict,
        invalid_weight: float,
    ) -> None:
        valid_payload["load_weight_lb"] = invalid_weight
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_payload = response.json()
        assert error_payload["error"]["code"] == "validation_error"
        assert "load_weight_lb" in error_payload["error"]["details"]

    @pytest.mark.parametrize("invalid_interval", [0, 5, 15, 30, 100])
    def test_reject_invalid_checkpoint_interval(
        self,
        api_client: APIClient,
        valid_payload: dict,
        invalid_interval: int,
    ) -> None:
        valid_payload["checkpoint_interval_miles"] = invalid_interval
        response = api_client.post(self.url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_payload = response.json()
        assert error_payload["error"]["code"] == "validation_error"
        assert "checkpoint_interval_miles" in error_payload["error"]["details"]

    def test_reject_empty_origin_and_destination(
        self, api_client: APIClient, valid_payload: dict
    ) -> None:
        valid_payload["origin"] = "   "
        valid_payload["destination"] = ""
        response = api_client.post(self.url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_payload = response.json()
        assert error_payload["error"]["code"] == "validation_error"
        assert "origin" in error_payload["error"]["details"]
        assert "destination" in error_payload["error"]["details"]

    def test_missing_all_fields_returns_structured_error(self, api_client: APIClient) -> None:
        response = api_client.post(self.url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_payload = response.json()
        assert "error" in error_payload
        assert error_payload["error"]["code"] == "validation_error"
        assert "origin" in error_payload["error"]["details"]
        assert "destination" in error_payload["error"]["details"]
        assert "departure_time" in error_payload["error"]["details"]
        assert "load_weight_lb" in error_payload["error"]["details"]
        assert "checkpoint_interval_miles" in error_payload["error"]["details"]

    def test_endpoint_throttling_triggers_after_rate_limit(
        self, api_client: APIClient, valid_payload: dict
    ) -> None:
        cache.clear()
        throttled_response = None
        for _ in range(32):
            res = api_client.post(self.url, valid_payload, format="json")
            if res.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                throttled_response = res
                break

        assert throttled_response is not None
        assert throttled_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        error_payload = throttled_response.json()
        assert "error" in error_payload
        assert error_payload["error"]["code"] == "request_throttled"
        assert "wait_seconds" in error_payload["error"]["details"]

    def test_geocoding_error_returns_400(
        self, api_client: APIClient, valid_payload: dict, mock_routing_service_in_view
    ) -> None:
        from routing.errors import GeocodingError

        mock_routing_service_in_view.analyze_routes.side_effect = GeocodingError(
            "Location not found: 'InvalidPlaceXYZ'"
        )
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body["error"]["code"] == "geocoding_error"
        assert "InvalidPlaceXYZ" in body["error"]["message"]

    def test_provider_timeout_returns_504(
        self, api_client: APIClient, valid_payload: dict, mock_routing_service_in_view
    ) -> None:
        from routing.errors import ProviderTimeoutError

        mock_routing_service_in_view.analyze_routes.side_effect = ProviderTimeoutError(
            "Routing provider timed out after 10.0s."
        )
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        body = response.json()
        assert body["error"]["code"] == "provider_timeout"

    def test_provider_rate_limit_returns_429(
        self, api_client: APIClient, valid_payload: dict, mock_routing_service_in_view
    ) -> None:
        from routing.errors import ProviderRateLimitError

        mock_routing_service_in_view.analyze_routes.side_effect = ProviderRateLimitError(
            "Upstream routing provider rate limit reached."
        )
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        body = response.json()
        assert body["error"]["code"] == "provider_rate_limited"

    def test_no_route_found_returns_404(
        self, api_client: APIClient, valid_payload: dict, mock_routing_service_in_view
    ) -> None:
        from routing.errors import NoRouteFoundError

        mock_routing_service_in_view.analyze_routes.side_effect = NoRouteFoundError(
            "No drivable route found between origin and destination."
        )
        response = api_client.post(self.url, valid_payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        body = response.json()
        assert body["error"]["code"] == "no_route_found"
