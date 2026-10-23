from django.urls import path

from .views import HealthCheckView, RouteAnalyzeView, RouteForecastTimelineView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("routes/analyze/", RouteAnalyzeView.as_view(), name="route-analyze"),
    path(
        "routes/forecast-timeline/",
        RouteForecastTimelineView.as_view(),
        name="route-forecast-timeline",
    ),
]
