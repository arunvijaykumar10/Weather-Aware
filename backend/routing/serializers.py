import re
from enum import Enum

from rest_framework import serializers


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    NO_TRAVEL = "no_travel"
    UNKNOWN = "unknown"


class WeatherAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MISSING = "missing"


RISK_LEVEL_CHOICES = [level.value for level in RiskLevel]
WEATHER_AVAILABILITY_CHOICES = [status.value for status in WeatherAvailability]


class RouteAnalyzeRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(
        max_length=255,
        min_length=1,
        trim_whitespace=True,
        error_messages={
            "blank": "Origin cannot be empty.",
            "required": "Origin address or coordinates are required.",
        },
    )
    destination = serializers.CharField(
        max_length=255,
        min_length=1,
        trim_whitespace=True,
        error_messages={
            "blank": "Destination cannot be empty.",
            "required": "Destination address or coordinates are required.",
        },
    )
    departure_time = serializers.DateTimeField(
        error_messages={
            "invalid": "departure_time must be a valid ISO 8601 timestamp (e.g. 2026-10-23T14:00:00Z).",
            "required": "departure_time is required.",
        }
    )
    load_weight_lb = serializers.FloatField(
        min_value=0.0001,
        error_messages={
            "min_value": "load_weight_lb must be a positive number greater than 0.",
            "required": "load_weight_lb is required.",
            "invalid": "load_weight_lb must be a valid numeric weight in pounds.",
        },
    )
    checkpoint_interval_miles = serializers.ChoiceField(
        choices=[10, 25, 50],
        error_messages={
            "invalid_choice": "checkpoint_interval_miles must be one of [10, 25, 50].",
            "required": "checkpoint_interval_miles is required.",
        },
    )

    def validate_departure_time(self, departure_datetime):
        raw_departure = self.initial_data.get("departure_time")
        # Without an explicit timezone indicator, cross-corridor weather forecast queries drift across timezones.
        if isinstance(raw_departure, str):
            timezone_suffix_pattern = r"(Z|[+-]\d{2}(?::?\d{2})?)$"
            if not re.search(timezone_suffix_pattern, raw_departure.strip()):
                raise serializers.ValidationError(
                    "departure_time must include an explicit timezone offset (e.g. '2026-10-23T14:00:00Z' or '2026-10-23T09:00:00-05:00'). Naive timestamps are rejected."
                )

        if (
            departure_datetime.tzinfo is None
            or departure_datetime.tzinfo.utcoffset(departure_datetime) is None
        ):
            raise serializers.ValidationError(
                "departure_time must be timezone-aware with an explicit offset."
            )
        return departure_datetime


class WeatherValuesSerializer(serializers.Serializer):
    wind_speed_mph = serializers.FloatField(allow_null=True)
    wind_gusts_mph = serializers.FloatField(allow_null=True, required=False, default=None)
    wind_speed_availability = serializers.ChoiceField(choices=WEATHER_AVAILABILITY_CHOICES)
    rain_in_per_hr = serializers.FloatField(allow_null=True)
    rain_availability = serializers.ChoiceField(choices=WEATHER_AVAILABILITY_CHOICES)
    snow_in_per_hr = serializers.FloatField(allow_null=True)
    snow_availability = serializers.ChoiceField(choices=WEATHER_AVAILABILITY_CHOICES)


class ConditionRisksSerializer(serializers.Serializer):
    wind_risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)
    rain_risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)
    snow_risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)


class CheckpointSerializer(serializers.Serializer):
    checkpoint_id = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    cumulative_distance_miles = serializers.FloatField()
    eta = serializers.DateTimeField()
    forecast_timestamp = serializers.DateTimeField(allow_null=True, required=False)
    weather = WeatherValuesSerializer()
    condition_risks = ConditionRisksSerializer()
    weather_risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)
    load_adjusted_risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)
    load_rule_applied = serializers.CharField(allow_null=True, required=False)


class MilesPerRiskCategorySerializer(serializers.Serializer):
    low = serializers.FloatField(default=0.0)
    moderate = serializers.FloatField(default=0.0)
    high = serializers.FloatField(default=0.0)
    severe = serializers.FloatField(default=0.0)
    no_travel = serializers.FloatField(default=0.0)
    unknown = serializers.FloatField(default=0.0)


class RouteMetricsSerializer(serializers.Serializer):
    miles_per_risk_category = MilesPerRiskCategorySerializer()
    severe_miles = serializers.FloatField()
    high_miles = serializers.FloatField()
    no_travel_miles = serializers.FloatField()
    unknown_miles = serializers.FloatField()
    average_risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)
    has_no_travel_segment = serializers.BooleanField()
    forecast_coverage_pct = serializers.FloatField(min_value=0.0, max_value=100.0)


class RouteEligibilitySerializer(serializers.Serializer):
    is_eligible = serializers.BooleanField()
    ineligibility_reasons = serializers.ListField(child=serializers.CharField(), default=list)


class RouteSerializer(serializers.Serializer):
    route_id = serializers.CharField()
    provider_summary = serializers.CharField()
    geometry = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)
    )
    distance_miles = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    checkpoints = serializers.ListField(child=CheckpointSerializer())
    metrics = RouteMetricsSerializer()
    eligibility = RouteEligibilitySerializer()


class RecommendationSerializer(serializers.Serializer):
    recommended_route_id = serializers.CharField(allow_null=True)
    route_eligibility = serializers.DictField(child=serializers.BooleanField())
    ranking_reasons = serializers.ListField(child=serializers.CharField())
    no_route_meets_safety_thresholds = serializers.BooleanField()


class HourlyRiskForecastSerializer(serializers.Serializer):
    hour_offset = serializers.IntegerField(min_value=0, max_value=48)
    forecast_time = serializers.DateTimeField()
    weather = WeatherValuesSerializer()
    risk = serializers.ChoiceField(choices=RISK_LEVEL_CHOICES)


class CheckpointTimelineSerializer(serializers.Serializer):
    checkpoint_id = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    hourly_forecasts = serializers.ListField(child=HourlyRiskForecastSerializer())


class ProviderErrorSerializer(serializers.Serializer):
    provider = serializers.CharField()
    code = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()


class RouteAnalyzeResponseSerializer(serializers.Serializer):
    routes_requested = serializers.IntegerField(default=3)
    routes_returned = serializers.IntegerField()
    fewer_routes_reason = serializers.CharField(allow_null=True, required=False)
    routes = serializers.ListField(child=RouteSerializer())
    recommendation = RecommendationSerializer()
    forecast_timeline = serializers.ListField(
        child=CheckpointTimelineSerializer(), default=list, required=False
    )
    warnings = serializers.ListField(child=serializers.CharField(), default=list)
    provider_errors = serializers.ListField(child=ProviderErrorSerializer(), default=list)
