from datetime import timezone

import pytest

from routing.checkpoint_service import (
    CheckpointService,
    parse_and_validate_departure_time,
)
from routing.constants import MAX_CHECKPOINTS_SAFETY_LIMIT


class TestCheckpointService:
    def test_straight_line_route_interpolates_checkpoints_and_etas(self) -> None:
        geometry = [[39.0, -105.0], [40.0, -105.0]]
        total_distance = 50.0
        total_duration = 60.0
        departure_iso = "2026-10-23T14:00:00Z"

        checkpoints, warnings = CheckpointService.generate_checkpoints(
            route_id="route_1",
            geometry=geometry,
            total_distance_miles=total_distance,
            total_duration_minutes=total_duration,
            departure_time=departure_iso,
            interval_miles=25,
        )

        assert len(warnings) == 0
        assert len(checkpoints) == 3
        assert [cp["cumulative_distance_miles"] for cp in checkpoints] == [
            0.0,
            25.0,
            50.0,
        ]
        assert abs(checkpoints[1]["lat"] - 39.5) < 0.001
        assert checkpoints[1]["lon"] == -105.0
        assert checkpoints[0]["eta"] == "2026-10-23T14:00:00Z"
        assert checkpoints[1]["eta"] == "2026-10-23T14:30:00Z"
        assert checkpoints[2]["eta"] == "2026-10-23T15:00:00Z"

    def test_multi_segment_route_samples_along_geometry(self) -> None:
        geometry = [
            [39.0, -105.0],
            [39.5, -105.0],
            [39.5, -104.5],
            [40.0, -104.5],
        ]
        checkpoints, _ = CheckpointService.generate_checkpoints(
            route_id="route_1",
            geometry=geometry,
            total_distance_miles=75.0,
            total_duration_minutes=90.0,
            departure_time="2026-10-23T10:00:00Z",
            interval_miles=25,
        )

        assert len(checkpoints) == 4
        assert [cp["cumulative_distance_miles"] for cp in checkpoints] == [
            0.0,
            25.0,
            50.0,
            75.0,
        ]
        assert checkpoints[-1]["lat"] == 40.0
        assert checkpoints[-1]["lon"] == -104.5

    @pytest.mark.parametrize(
        "total_miles,interval,expected_cumulative_milestones",
        [
            (15.0, 25, [0.0, 15.0]),  # Shorter than interval: origin and destination only
            (50.0, 25, [0.0, 25.0, 50.0]),  # Exact boundary: 3 checkpoints
            (51.0, 25, [0.0, 25.0, 50.0, 51.0]),  # 1 mile past interval: destination appended
        ],
    )
    def test_boundary_and_destination_inclusion(
        self,
        total_miles: float,
        interval: int,
        expected_cumulative_milestones: list,
    ) -> None:
        geometry = [[39.0, -105.0], [40.0, -105.0]]
        checkpoints, _ = CheckpointService.generate_checkpoints(
            route_id="route_1",
            geometry=geometry,
            total_distance_miles=total_miles,
            total_duration_minutes=60.0,
            departure_time="2026-10-23T14:00:00Z",
            interval_miles=interval,
        )
        assert [
            cp["cumulative_distance_miles"] for cp in checkpoints
        ] == expected_cumulative_milestones

    def test_geometry_distance_scaling_matches_provider_total(self) -> None:
        # Straight-line distance is ~69 miles, but provider reports 75.0 due to road turns.
        geometry = [[39.0, -105.0], [40.0, -105.0]]
        provider_distance_miles = 75.0

        scaled_distances, raw_len = CheckpointService.compute_scaled_vertex_distances(
            geometry, provider_distance_miles
        )
        assert scaled_distances[0] == 0.0
        assert scaled_distances[-1] == provider_distance_miles
        assert raw_len < provider_distance_miles

        checkpoints, _ = CheckpointService.generate_checkpoints(
            route_id="route_1",
            geometry=geometry,
            total_distance_miles=provider_distance_miles,
            total_duration_minutes=90.0,
            departure_time="2026-10-23T14:00:00Z",
            interval_miles=25,
        )
        assert [cp["cumulative_distance_miles"] for cp in checkpoints] == [
            0.0,
            25.0,
            50.0,
            75.0,
        ]

    def test_offset_timestamps_converted_to_utc_iso_format(self) -> None:
        departure_offset = "2026-10-23T19:30:00+05:30"
        departure_utc = parse_and_validate_departure_time(departure_offset)

        assert departure_utc.tzinfo == timezone.utc
        assert departure_utc.hour == 14
        assert departure_utc.minute == 0

        geometry = [[39.0, -105.0], [40.0, -105.0]]
        checkpoints, _ = CheckpointService.generate_checkpoints(
            route_id="route_1",
            geometry=geometry,
            total_distance_miles=50.0,
            total_duration_minutes=60.0,
            departure_time=departure_offset,
            interval_miles=25,
        )
        assert checkpoints[0]["eta"] == "2026-10-23T14:00:00Z"
        assert checkpoints[-1]["eta"] == "2026-10-23T15:00:00Z"

    def test_naive_timestamp_rejected_with_validation_error(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            parse_and_validate_departure_time("2026-10-23T14:00:00")

    def test_safety_limit_auto_adapts_interval_without_truncation(self) -> None:
        # Cross-country 3000 miles at interval 10 would yield 300 checkpoints.
        geometry = [[39.0, -105.0], [40.0, -105.0]]
        checkpoints, warnings = CheckpointService.generate_checkpoints(
            route_id="route_1",
            geometry=geometry,
            total_distance_miles=3000.0,
            total_duration_minutes=3600.0,
            departure_time="2026-10-23T14:00:00Z",
            interval_miles=10,
        )

        assert len(warnings) > 0
        assert f"safety limit of {MAX_CHECKPOINTS_SAFETY_LIMIT}" in warnings[0]
        assert len(checkpoints) <= MAX_CHECKPOINTS_SAFETY_LIMIT
        assert checkpoints[0]["cumulative_distance_miles"] == 0.0
        assert checkpoints[-1]["cumulative_distance_miles"] == 3000.0
