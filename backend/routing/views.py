from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


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
