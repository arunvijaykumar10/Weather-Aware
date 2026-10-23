from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.cache import cache

from routing.errors import (
    ProviderRateLimitError,
    ProviderTimeoutError,
    WeatherProviderError,
    WeatherServiceError,
)
from routing.weather_service import WeatherService


def create_mock_open_meteo_response(
    coordinates_count: int = 1,
    wind_speed: float = 18.5,
    wind_gusts: float = 28.0,
    rain: float = 0.08,
    showers: float = 0.04,
    snowfall: float = 0.0,
) -> list:
    base_time = datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)
    time_series = [(base_time + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(72)]

    payloads = []
    for _ in range(coordinates_count):
        payloads.append(
            {
                "latitude": 39.74,
                "longitude": -104.99,
                "hourly": {
                    "time": time_series,
                    "wind_speed_10m": [wind_speed] * 72,
                    "wind_gusts_10m": [wind_gusts] * 72,
                    "rain": [rain] * 72,
                    "showers": [showers] * 72,
                    "snowfall": [snowfall] * 72,
                },
            }
        )
    return payloads


class TestWeatherService:
    @pytest.fixture(autouse=True)
    def clear_cache_before_each_test(self):
        cache.clear()
        yield
        cache.clear()

    @pytest.mark.parametrize(
        "lat,lon,expected_grid",
        [
            (39.7392, -104.9903, (39.74, -104.99)),
            (39.7410, -104.9920, (39.74, -104.99)),
            (40.7608, -111.8910, (40.76, -111.89)),
        ],
    )
    def test_forecast_grid_rounding_groups_nearby_coordinates(
        self, lat: float, lon: float, expected_grid: tuple
    ) -> None:
        assert WeatherService.round_to_forecast_grid(lat, lon) == expected_grid

    def test_reject_past_departure_beyond_threshold(self) -> None:
        past_departure = datetime.now(timezone.utc) - timedelta(hours=10)
        future_eta = datetime.now(timezone.utc) + timedelta(hours=5)

        with pytest.raises(WeatherServiceError, match="hours in the past"):
            WeatherService.compute_required_forecast_days(past_departure, future_eta)

    def test_compute_required_forecast_days_enforces_minimum_window(
        self,
    ) -> None:
        now_utc = datetime.now(timezone.utc)
        short_eta = now_utc + timedelta(hours=4)
        # Minimum forecast window is 48h (at least 3 days).
        days = WeatherService.compute_required_forecast_days(now_utc, short_eta)
        assert days >= 3

    @pytest.mark.parametrize(
        "checkpoint_eta,expected_forecast_hour",
        [
            ("2026-10-23T14:20:00Z", "2026-10-23T14:00:00Z"),
            ("2026-10-23T14:38:00Z", "2026-10-23T15:00:00Z"),
            ("2026-10-23T10:00:00Z", "2026-10-23T10:00:00Z"),
        ],
    )
    def test_select_nearest_forecast_hour(
        self, checkpoint_eta: str, expected_forecast_hour: str
    ) -> None:
        raw_response = create_mock_open_meteo_response(1)[0]
        hourly_lookup = WeatherService.parse_hourly_forecast(raw_response)

        selected_hour, weather_values = WeatherService.select_nearest_forecast_hour(
            hourly_lookup, checkpoint_eta
        )
        assert selected_hour == expected_forecast_hour
        assert weather_values is not None
        assert weather_values["wind_speed_mph"] == 18.5
        assert weather_values["wind_gusts_mph"] == 28.0

    def test_combining_stratiform_rain_and_convective_showers(self) -> None:
        raw_response = create_mock_open_meteo_response(1, rain=0.12, showers=0.08)[0]
        hourly_lookup = WeatherService.parse_hourly_forecast(raw_response)

        sample = hourly_lookup["2026-10-23T14:00:00Z"]
        # 0.12 rain + 0.08 showers = 0.20 inches/hour
        assert sample["rain_in_per_hr"] == 0.20

    def test_missing_weather_values_remain_unavailable_never_zeroed(
        self,
    ) -> None:
        raw_payload = {
            "latitude": 39.74,
            "longitude": -104.99,
            "hourly": {
                "time": ["2026-10-23T14:00"],
                "wind_speed_10m": [None],
                "wind_gusts_10m": [None],
                "rain": [None],
                "showers": [None],
                "snowfall": [None],
            },
        }
        hourly_lookup = WeatherService.parse_hourly_forecast(raw_payload)
        sample = hourly_lookup["2026-10-23T14:00:00Z"]

        assert sample["wind_speed_mph"] is None
        assert sample["rain_in_per_hr"] is None
        assert sample["snow_in_per_hr"] is None

        checkpoint = {
            "lat": 39.74,
            "lon": -104.99,
            "eta": "2026-10-23T14:00:00Z",
        }
        grid_map = {(39.74, -104.99): hourly_lookup}
        WeatherService.populate_checkpoint_weather(checkpoint, grid_map)

        weather = checkpoint["weather"]
        assert weather["wind_speed_mph"] is None
        assert weather["wind_speed_availability"] == "unavailable"
        assert weather["rain_in_per_hr"] is None
        assert weather["rain_availability"] == "unavailable"
        assert weather["snow_in_per_hr"] is None
        assert weather["snow_availability"] == "unavailable"

    def test_enrich_corridors_with_weather_updates_checkpoints_and_coverage(
        self,
    ) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_open_meteo_response(
            coordinates_count=2,
            wind_speed=15.0,
            wind_gusts=25.0,
            rain=0.05,
            showers=0.05,
        )

        corridors = [
            {
                "route_id": "route_primary",
                "checkpoints": [
                    {
                        "checkpoint_id": "cp_0",
                        "lat": 39.7392,
                        "lon": -104.9903,
                        "eta": "2026-10-23T14:00:00Z",
                    },
                    {
                        "checkpoint_id": "cp_1",
                        "lat": 40.7608,
                        "lon": -111.8910,
                        "eta": "2026-10-23T18:00:00Z",
                    },
                ],
                "metrics": {},
            }
        ]

        with patch("requests.Session.get", return_value=mock_response):
            warnings = WeatherService.enrich_corridors_with_weather(
                corridors, departure_time_iso="2026-10-23T14:00:00Z"
            )

        assert len(warnings) == 0
        assert corridors[0]["metrics"]["forecast_coverage_pct"] == 100.0

        cp0 = corridors[0]["checkpoints"][0]
        assert cp0["forecast_timestamp"] == "2026-10-23T14:00:00Z"
        assert cp0["weather"]["wind_speed_mph"] == 15.0
        assert cp0["weather"]["wind_gusts_mph"] == 25.0
        assert cp0["weather"]["wind_speed_availability"] == "available"
        assert cp0["weather"]["rain_in_per_hr"] == 0.10

    def test_open_meteo_rate_limit_429_raises_provider_rate_limit_error(
        self,
    ) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429

        with patch("requests.Session.get", return_value=mock_response):
            with pytest.raises(ProviderRateLimitError):
                WeatherService.fetch_batch_from_open_meteo([(39.74, -104.99)], forecast_days=3)

    def test_open_meteo_timeout_raises_provider_timeout_error(self) -> None:
        with patch(
            "requests.Session.get",
            side_effect=requests.exceptions.Timeout("Connection timeout"),
        ):
            with pytest.raises(ProviderTimeoutError):
                WeatherService.fetch_batch_from_open_meteo([(39.74, -104.99)], forecast_days=3)

    def test_open_meteo_server_error_raises_weather_provider_error(
        self,
    ) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("requests.Session.get", return_value=mock_response):
            with pytest.raises(WeatherProviderError):
                WeatherService.fetch_batch_from_open_meteo([(39.74, -104.99)], forecast_days=3)
