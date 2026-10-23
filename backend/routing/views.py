from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .routing_service import RoutingService
from .serializers import (
    RouteAnalyzeRequestSerializer,
    RouteAnalyzeResponseSerializer,
)


class HealthCheckView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "healthy",
                "service": "spotter-weather-aware-routing-backend",
            },
            status=status.HTTP_200_OK,
        )


class RouteAnalyzeView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "route_analysis"

    def post(self, request, *args, **kwargs):
        request_serializer = RouteAnalyzeRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_parameters = request_serializer.validated_data

        routing_service = RoutingService()
        route_assessment = routing_service.analyze_routes(
            origin=validated_parameters["origin"],
            destination=validated_parameters["destination"],
            departure_time_iso=validated_parameters["departure_time"].isoformat(),
            load_weight_lb=validated_parameters["load_weight_lb"],
            checkpoint_interval_miles=validated_parameters["checkpoint_interval_miles"],
        )

        response_serializer = RouteAnalyzeResponseSerializer(data=route_assessment)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
