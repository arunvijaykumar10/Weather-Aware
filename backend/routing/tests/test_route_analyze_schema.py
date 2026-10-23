import pytest
from unittest.mock import patch
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
    """Ensure endpoint tests never make live network calls."""
    with patch('routing.views.RoutingService') as mock_cls:
        instance = mock_cls.return_value
        instance.analyze_routes.return_value = {
            "routes_requested": 3,
            "routes_returned": 1,
            "fewer_routes_reason": "Single primary corridor identified in simulation.",
            "routes": [
                {
                    "route_id": "route_primary",
                    "provider_summary": "Simulated corridor from Denver, CO to Salt Lake City, UT",
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
        yield instance


@pytest.mark.django_db
class TestRouteAnalyzeEndpoint:
    url = '/api/routes/analyze/'

    def test_valid_request_returns_200_and_expected_schema(self, api_client, valid_payload):
        response = api_client.post(self.url, valid_payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check top-level contract keys
        assert "routes_requested" in data
        assert "routes_returned" in data
        assert "routes" in data
        assert "recommendation" in data
        assert "forecast_timeline" in data
        assert "warnings" in data
        assert "provider_errors" in data

        # Check route schema
        assert len(data["routes"]) == 1
        route = data["routes"][0]
        assert "route_id" in route
        assert "provider_summary" in route
        assert "geometry" in route
        assert "distance_miles" in route
        assert "duration_minutes" in route
        assert "checkpoints" in route
        assert "metrics" in route
        assert "eligibility" in route

        # Check checkpoint schema
        assert len(route["checkpoints"]) > 0
        cp = route["checkpoints"][0]
        assert "checkpoint_id" in cp
        assert "lat" in cp
        assert "lon" in cp
        assert "cumulative_distance_miles" in cp
        assert "eta" in cp
        assert "weather" in cp
        assert "condition_risks" in cp
        assert "weather_risk" in cp
        assert "load_adjusted_risk" in cp
        assert cp["weather"]["wind_speed_availability"] in ["available", "unavailable", "missing"]

        # Check recommendation schema
        rec = data["recommendation"]
        assert "recommended_route_id" in rec
        assert "route_eligibility" in rec
        assert "ranking_reasons" in rec
        assert "no_route_meets_safety_thresholds" in rec

    def test_departure_time_with_numeric_timezone_offset_accepted(self, api_client, valid_payload):
        valid_payload["departure_time"] = "2026-10-23T08:00:00-06:00"
        response = api_client.post(self.url, valid_payload, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_reject_naive_departure_time_without_timezone_offset(self, api_client, valid_payload):
        valid_payload["departure_time"] = "2026-10-23T14:00:00"  # Naive timestamp
        response = api_client.post(self.url, valid_payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert "departure_time" in data["error"]["details"]
        assert "timezone" in str(data["error"]["details"]["departure_time"]).lower()

    def test_reject_zero_or_negative_load_weight(self, api_client, valid_payload):
        valid_payload["load_weight_lb"] = 0
        response = api_client.post(self.url, valid_payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "validation_error"
        assert "load_weight_lb" in data["error"]["details"]

        valid_payload["load_weight_lb"] = -500.0
        response2 = api_client.post(self.url, valid_payload, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_invalid_checkpoint_interval(self, api_client, valid_payload):
        valid_payload["checkpoint_interval_miles"] = 15  # only 10, 25, 50 allowed
        response = api_client.post(self.url, valid_payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "validation_error"
        assert "checkpoint_interval_miles" in data["error"]["details"]

    def test_reject_empty_origin_and_destination(self, api_client, valid_payload):
        valid_payload["origin"] = "   "
        valid_payload["destination"] = ""
        response = api_client.post(self.url, valid_payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "validation_error"
        assert "origin" in data["error"]["details"]
        assert "destination" in data["error"]["details"]

    def test_missing_all_fields_returns_structured_error(self, api_client):
        response = api_client.post(self.url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert "origin" in data["error"]["details"]
        assert "destination" in data["error"]["details"]
        assert "departure_time" in data["error"]["details"]
        assert "load_weight_lb" in data["error"]["details"]
        assert "checkpoint_interval_miles" in data["error"]["details"]

    def test_endpoint_throttling_triggers_after_rate_limit(self, api_client, valid_payload):
        # Rate limit is 30/minute for route_analysis scope
        cache.clear()
        throttled_response = None
        for _ in range(32):
            res = api_client.post(self.url, valid_payload, format='json')
            if res.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                throttled_response = res
                break

        assert throttled_response is not None
        assert throttled_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = throttled_response.json()
        assert "error" in data
        assert data["error"]["code"] == "request_throttled"
        assert "wait_seconds" in data["error"]["details"]
