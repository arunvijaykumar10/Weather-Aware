from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from routing.forecast_timeline_service import ForecastTimelineService


def create_mock_hourly_forecast(base_time: datetime, count_hours: int = 72) -> dict:
    time_series = [
        (base_time + timedelta(hours=h)).strftime("%Y-%m-%dT%H:00:00Z") for h in range(count_hours)
    ]
    lookup = {}
    for ts in time_series:
        lookup[ts] = {
            "wind_speed_mph": 15.0,
            "wind_gusts_mph": 22.0,
            "rain_in_per_hr": 0.05,
            "snow_in_per_hr": 0.0,
        }
    return lookup


@pytest.fixture
def api_client():
    cache.clear()
    return APIClient()


@pytest.fixture
def mock_corridor():
    return {
        "route_id": "route_primary",
        "distance_miles": 150.0,
        "duration_minutes": 160.0,
        "geometry": [
            [39.7392, -104.9903],
            [40.0, -105.5],
            [40.5, -106.0],
            [40.7608, -111.8910],
        ],
        "checkpoints": [
            {
                "checkpoint_id": "cp_0",
                "lat": 39.7392,
                "lon": -104.9903,
                "cumulative_distance_miles": 0.0,
                "eta": "2026-10-24T14:00:00Z",
            },
            {
                "checkpoint_id": "cp_1",
                "lat": 40.7608,
                "lon": -111.8910,
                "cumulative_distance_miles": 150.0,
                "eta": "2026-10-24T17:00:00Z",
            },
        ],
    }


class TestForecastTimelineHourBounds:
    def test_hour_bounds_service_validation(self):
        # 0 and 48 are valid
        assert ForecastTimelineService.validate_hour_offset(0) == 0
        assert ForecastTimelineService.validate_hour_offset(48) == 48
        assert ForecastTimelineService.validate_hour_offset(24) == 24

        # -1 and 49 are rejected
        with pytest.raises(ValueError, match="between 0 and 48"):
            ForecastTimelineService.validate_hour_offset(-1)

        with pytest.raises(ValueError, match="between 0 and 48"):
            ForecastTimelineService.validate_hour_offset(49)

    def test_api_view_rejects_out_of_bounds_hours(self, api_client):
        base_request = {
            "origin": "Denver, CO",
            "destination": "Salt Lake City, UT",
            "departure_time": "2026-10-24T14:00:00Z",
            "load_weight_lb": 35000.0,
            "checkpoint_interval_miles": 25,
        }

        # hour_offset -1 is rejected with 400
        resp_neg = api_client.post(
            "/api/routes/forecast-timeline/",
            {**base_request, "hour_offset": -1},
            format="json",
        )
        assert resp_neg.status_code == status.HTTP_400_BAD_REQUEST
        assert "hour_offset" in str(resp_neg.data)

        # hour_offset 49 is rejected with 400
        resp_over = api_client.post(
            "/api/routes/forecast-timeline/",
            {**base_request, "hour_offset": 49},
            format="json",
        )
        assert resp_over.status_code == status.HTTP_400_BAD_REQUEST
        assert "hour_offset" in str(resp_over.data)

    def test_api_view_accepts_valid_hour_bounds(self, api_client, mock_corridor):
        with patch("routing.views.RoutingService") as mock_routing_cls:
            mock_routing_cls.return_value.analyze_routes.return_value = {
                "routes": [mock_corridor],
                "warnings": [],
            }
            with patch(
                "routing.forecast_timeline_service.WeatherService.load_grid_forecasts"
            ) as mock_weather:
                base_time = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
                mock_weather.return_value = {
                    (39.74, -104.99): create_mock_hourly_forecast(base_time),
                    (40.76, -111.89): create_mock_hourly_forecast(base_time),
                }

                # hour_offset 0 is valid
                resp_0 = api_client.post(
                    "/api/routes/forecast-timeline/",
                    {
                        "origin": "Denver, CO",
                        "destination": "Salt Lake City, UT",
                        "departure_time": "2026-10-24T14:00:00Z",
                        "load_weight_lb": 35000.0,
                        "checkpoint_interval_miles": 25,
                        "hour_offset": 0,
                    },
                    format="json",
                )
                assert resp_0.status_code == status.HTTP_200_OK
                assert resp_0.data["hour_offsets"] == [0]

                # hour_offset 48 is valid
                resp_48 = api_client.post(
                    "/api/routes/forecast-timeline/",
                    {
                        "origin": "Denver, CO",
                        "destination": "Salt Lake City, UT",
                        "departure_time": "2026-10-24T14:00:00Z",
                        "load_weight_lb": 35000.0,
                        "checkpoint_interval_miles": 25,
                        "hour_offset": 48,
                    },
                    format="json",
                )
                assert resp_48.status_code == status.HTTP_200_OK
                assert resp_48.data["hour_offsets"] == [48]


class TestForecastTimelineUtcConversion:
    def test_utc_conversion_from_local_timezone_offset(self, mock_corridor):
        # Departure at 08:00 Mountain Daylight Time (-06:00) -> 14:00 UTC
        local_departure = "2026-10-24T08:00:00-06:00"
        departure_utc = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        hourly_data = create_mock_hourly_forecast(departure_utc)

        with patch(
            "routing.forecast_timeline_service.WeatherService.load_grid_forecasts"
        ) as mock_weather:
            mock_weather.return_value = {
                (39.74, -104.99): hourly_data,
                (40.76, -111.89): hourly_data,
            }

            payload = ForecastTimelineService.generate_timeline_response(
                corridors=[mock_corridor],
                departure_time_iso=local_departure,
                load_weight_lb=30000.0,
            )

        assert payload["departure_time"] == "2026-10-24T14:00:00+00:00"
        cp0_timeline = payload["routes"][0]["checkpoints"][0]["timeline"]

        # Exactly 49 hourly entries (offsets 0 through 48)
        assert len(cp0_timeline) == 49
        assert cp0_timeline[0]["offset_hours"] == 0
        assert cp0_timeline[0]["forecast_timestamp"] == "2026-10-24T14:00:00Z"
        assert cp0_timeline[1]["offset_hours"] == 1
        assert cp0_timeline[1]["forecast_timestamp"] == "2026-10-24T15:00:00Z"
        assert cp0_timeline[48]["offset_hours"] == 48
        assert cp0_timeline[48]["forecast_timestamp"] == "2026-10-26T14:00:00Z"

        # All entries must have UTC timestamps
        for entry in cp0_timeline:
            assert (
                entry["forecast_timestamp"].endswith("Z") or "+00:00" in entry["forecast_timestamp"]
            )


class TestForecastTimelineMissingAndUnavailableHours:
    def test_missing_hours_remain_none_never_zeroed(self):
        target_utc = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        # Provider returns null values for all weather variables
        hourly_lookup = {
            "2026-10-24T14:00:00Z": {
                "wind_speed_mph": None,
                "wind_gusts_mph": None,
                "rain_in_per_hr": None,
                "snow_in_per_hr": None,
            }
        }

        entry = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=40000.0,
        )

        assert entry["availability"] == "unavailable"
        assert entry["wind_speed_mph"] is None
        assert entry["rain_in_per_hr"] is None
        assert entry["snow_in_per_hr"] is None
        assert entry["weather_risk"] == "unknown"
        assert entry["load_adjusted_risk"] == "unknown"
        assert entry["numeric_risk_score"] is None

    def test_beyond_forecast_horizon_flagged(self):
        target_utc = datetime(2026, 10, 26, 14, 0, tzinfo=timezone.utc)
        # Provider only has data up to 2026-10-24T18:00:00Z
        hourly_lookup = {
            "2026-10-24T18:00:00Z": {
                "wind_speed_mph": 12.0,
                "wind_gusts_mph": 18.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
            }
        }

        entry = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=48,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=30000.0,
        )

        assert entry["availability"] == "beyond_forecast"
        assert entry["wind_speed_mph"] is None
        assert entry["weather_risk"] == "unknown"

    def test_known_high_condition_not_hidden_by_missing_rain(self):
        target_utc = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        # Wind is 38 mph (High risk), but rain and snow are missing
        hourly_lookup = {
            "2026-10-24T14:00:00Z": {
                "wind_speed_mph": 38.0,
                "wind_gusts_mph": 40.0,
                "rain_in_per_hr": None,
                "snow_in_per_hr": None,
            }
        }

        entry = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=30000.0,
        )

        assert entry["availability"] == "available"
        assert entry["condition_risks"]["wind"] == "high"
        assert entry["condition_risks"]["rain"] == "unknown"
        assert entry["weather_risk"] == "high"


class TestForecastTimelineLoadAdjustedRiskPerHour:
    def test_load_greater_than_40k_elevates_wind_to_severe(self):
        target_utc = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        # Wind 38 mph is High weather risk; load > 40,000 lb elevates to at least Severe
        hourly_lookup = {
            "2026-10-24T14:00:00Z": {
                "wind_speed_mph": 38.0,
                "wind_gusts_mph": 38.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
            }
        }

        entry_heavy = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=42000.0,
        )
        assert entry_heavy["weather_risk"] == "high"
        assert entry_heavy["load_adjusted_risk"] == "severe"

        # At exactly 40,000 lb, rule does strictly greater than: rule does NOT trigger
        entry_boundary = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=40000.0,
        )
        assert entry_boundary["load_adjusted_risk"] == "high"

    def test_load_greater_than_30k_elevates_wind_to_no_travel(self):
        target_utc = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        # Wind 48 mph is Severe weather risk; load > 30,000 lb elevates to No Travel
        hourly_lookup = {
            "2026-10-24T14:00:00Z": {
                "wind_speed_mph": 48.0,
                "wind_gusts_mph": 48.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
            }
        }

        entry_heavy = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=35000.0,
        )
        assert entry_heavy["weather_risk"] == "severe"
        assert entry_heavy["load_adjusted_risk"] == "no_travel"

        # At or below 30,000 lb, rule does NOT trigger
        entry_light = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=30000.0,
        )
        assert entry_light["load_adjusted_risk"] == "severe"

    def test_wind_ge_55_no_travel_for_any_load(self):
        target_utc = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        hourly_lookup = {
            "2026-10-24T14:00:00Z": {
                "wind_speed_mph": 56.0,
                "wind_gusts_mph": 58.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
            }
        }

        entry = ForecastTimelineService.evaluate_hourly_entry(
            offset_hours=0,
            target_utc=target_utc,
            hourly_lookup=hourly_lookup,
            load_weight_lb=10000.0,
        )
        assert entry["weather_risk"] == "no_travel"
        assert entry["load_adjusted_risk"] == "no_travel"


class TestCorridorSampleGridCap:
    def test_sample_point_cap_enforced_with_warning(self, mock_corridor):
        # Request with a low cap of 5 sample points
        samples, is_capped, warnings = ForecastTimelineService.generate_corridor_sample_grid(
            corridors=[mock_corridor],
            sample_interval_miles=15.0,
            corridor_half_width_miles=15.0,
            max_grid_points=5,
        )

        assert len(samples) == 5
        assert is_capped is True
        assert any("Heatmap corridor sample grid capped at 5 points" in w for w in warnings)

    def test_sample_point_uncapped_within_limit(self, mock_corridor):
        samples, is_capped, warnings = ForecastTimelineService.generate_corridor_sample_grid(
            corridors=[mock_corridor],
            sample_interval_miles=50.0,
            corridor_half_width_miles=15.0,
            max_grid_points=100,
        )

        assert len(samples) <= 100
        assert is_capped is False
        assert len(warnings) == 0

    def test_full_response_measures_payload_size(self, mock_corridor):
        base_time = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
        hourly_data = create_mock_hourly_forecast(base_time)

        with patch(
            "routing.forecast_timeline_service.WeatherService.load_grid_forecasts"
        ) as mock_weather:
            mock_weather.return_value = {
                (39.74, -104.99): hourly_data,
                (40.76, -111.89): hourly_data,
            }

            payload = ForecastTimelineService.generate_timeline_response(
                corridors=[mock_corridor],
                departure_time_iso="2026-10-24T14:00:00Z",
                load_weight_lb=35000.0,
                max_grid_points=20,
            )

        assert "payload_size_bytes" in payload
        assert payload["payload_size_bytes"] > 0
        assert "corridor_grid" in payload
        assert "samples" in payload["corridor_grid"]
        assert len(payload["corridor_grid"]["samples"]) <= 20
