from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .forecast_timeline_service import ForecastTimelineService
from .routing_service import RoutingService
from .serializers import (
    RouteAnalyzeRequestSerializer,
    RouteAnalyzeResponseSerializer,
    RouteForecastTimelineRequestSerializer,
    RouteForecastTimelineResponseSerializer,
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


class RouteForecastTimelineView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "route_analysis"

    def post(self, request, *args, **kwargs):
        request_serializer = RouteForecastTimelineRequestSerializer(data=request.data)
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

        timeline_payload = ForecastTimelineService.generate_timeline_response(
            corridors=route_assessment["routes"],
            departure_time_iso=validated_parameters["departure_time"].isoformat(),
            load_weight_lb=validated_parameters["load_weight_lb"],
            sample_interval_miles=validated_parameters.get("sample_interval_miles", 25.0),
            corridor_half_width_miles=validated_parameters.get("corridor_half_width_miles", 15.0),
            max_grid_points=validated_parameters.get("max_grid_points", 120),
            target_offset_hour=validated_parameters.get("hour_offset"),
            operational_warnings=route_assessment.get("warnings", []),
        )

        response_serializer = RouteForecastTimelineResponseSerializer(data=timeline_payload)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
