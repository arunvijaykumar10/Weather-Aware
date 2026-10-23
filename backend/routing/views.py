from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

from .serializers import (
    RouteAnalyzeRequestSerializer,
    RouteAnalyzeResponseSerializer,
)
from .routing_service import RoutingService


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

        # 2. Invoke routing service for geocoding and corridor generation
        routing_service = RoutingService()
        analysis_result = routing_service.analyze_routes(
            origin=validated_data['origin'],
            destination=validated_data['destination'],
            departure_time_iso=departure_time_iso,
            load_weight_lb=validated_data['load_weight_lb'],
            checkpoint_interval_miles=validated_data['checkpoint_interval_miles'],
        )

        # 3. Validate serialized output matches the typed response schema
        res_serializer = RouteAnalyzeResponseSerializer(data=analysis_result)
        res_serializer.is_valid(raise_exception=True)

        return Response(res_serializer.data, status=status.HTTP_200_OK)
