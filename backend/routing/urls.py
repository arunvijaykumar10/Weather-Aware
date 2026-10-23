from django.urls import path

from .views import HealthCheckView, RouteAnalyzeView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("routes/analyze/", RouteAnalyzeView.as_view(), name="route-analyze"),
]
