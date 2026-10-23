from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

from .serializers import (
    RouteAnalyzeRequestSerializer,
    RouteAnalyzeResponseSerializer,
)


class HealthCheckView(APIView):
    """
    Health check endpoint to verify backend service readiness and status.
    """
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "healthy",
                "service": "spotter-weather-aware-routing-backend",
            },
            status=status.HTTP_200_OK,
        )


class RouteAnalyzeView(APIView):
    """
    Main endpoint for analyzing driving routes and weather-aware risks:
    POST /api/routes/analyze/

    Protected by DRF scoped rate throttling to prevent upstream provider quota exhaustion.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'route_analysis'

    def post(self, request, *args, **kwargs):
        # 1. Validate request payload against strict contract
        req_serializer = RouteAnalyzeRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        validated_data = req_serializer.validated_data

        departure_time_iso = validated_data['departure_time'].isoformat()

        # 2. Schema-compliant mock response (Live providers will be connected in subsequent tasks)
        stub_response_data = {
            "routes_requested": 3,
            "routes_returned": 1,
            "fewer_routes_reason": "Single primary corridor identified in contract simulation stub.",
            "routes": [
                {
                    "route_id": "route_stub_1",
                    "provider_summary": f"Simulated highway corridor from {validated_data['origin']} to {validated_data['destination']}",
                    "geometry": [
                        [37.7749, -122.4194],
                        [38.5816, -121.4944],
                    ],
                    "distance_miles": 87.5,
                    "duration_minutes": 95.0,
                    "checkpoints": [
                        {
                            "checkpoint_id": "cp_origin",
                            "lat": 37.7749,
                            "lon": -122.4194,
                            "cumulative_distance_miles": 0.0,
                            "eta": departure_time_iso,
                            "forecast_timestamp": departure_time_iso,
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
                            "low": 87.5,
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
                "recommended_route_id": "route_stub_1",
                "route_eligibility": {"route_stub_1": True},
                "ranking_reasons": [
                    "Optimal road conditions and clear weather throughout corridor."
                ],
                "no_route_meets_safety_thresholds": False,
            },
            "forecast_timeline": [],
            "warnings": [
                "Contract schema active. Live provider calls are disabled in Task 2."
            ],
            "provider_errors": [],
        }

        # Verify response matches contract serializer before returning
        res_serializer = RouteAnalyzeResponseSerializer(data=stub_response_data)
        res_serializer.is_valid(raise_exception=True)

        return Response(res_serializer.data, status=status.HTTP_200_OK)
