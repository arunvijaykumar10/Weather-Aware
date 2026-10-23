from typing import Any, Dict, List

from routing.route_scoring_service import (
    attribute_segment_mileages_and_risks,
    rank_and_score_corridors,
)


def make_test_checkpoint(
    cp_id: str,
    distance_miles: float,
    load_adjusted_risk: str = "low",
    is_no_travel: bool = False,
) -> Dict[str, Any]:
    return {
        "checkpoint_id": cp_id,
        "cumulative_distance_miles": distance_miles,
        "load_adjusted_risk": load_adjusted_risk,
        "is_no_travel": is_no_travel,
        "weather": {
            "wind_speed_availability": (
                "unavailable" if load_adjusted_risk == "unknown" else "available"
            )
        },
    }


def make_test_corridor(
    route_id: str,
    distance_miles: float,
    duration_minutes: float,
    checkpoints: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "route_id": route_id,
        "distance_miles": distance_miles,
        "duration_minutes": duration_minutes,
        "checkpoints": checkpoints,
    }


class TestRouteScoringAndRecommendation:
    def test_interval_miles_sum_strictly_equals_total_route_distance(
        self,
    ) -> None:
        # 5 checkpoints with irregular intervals: 0.0, 15.2, 38.6, 62.1, 75.0 miles
        checkpoints = [
            make_test_checkpoint("cp_0", 0.0, "low"),
            make_test_checkpoint("cp_1", 15.2, "moderate"),
            make_test_checkpoint("cp_2", 38.6, "low"),
            make_test_checkpoint("cp_3", 62.1, "high"),
            make_test_checkpoint("cp_4", 75.0, "low"),
        ]
        total_dist = 75.0

        miles_by_cat, _, _ = attribute_segment_mileages_and_risks(checkpoints, total_dist)
        total_allocated_miles = sum(miles_by_cat.values())
        assert round(total_allocated_miles, 2) == total_dist

    def test_ranking_criterion_1_fewest_severe_miles_decides_winner(
        self,
    ) -> None:
        # Route A has 5 miles Severe, Route B has 15 miles Severe. Route A must win.
        route_a = make_test_corridor(
            "route_a",
            100.0,
            120.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "low"),
                make_test_checkpoint("cp_a1", 95.0, "low"),
                make_test_checkpoint("cp_a2", 100.0, "severe"),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            100.0,
            100.0,  # Shorter time, but worse severe exposure!
            [
                make_test_checkpoint("cp_b0", 0.0, "low"),
                make_test_checkpoint("cp_b1", 85.0, "low"),
                make_test_checkpoint("cp_b2", 100.0, "severe"),
            ],
        )

        ordered, recommendation = rank_and_score_corridors([route_b, route_a])
        assert recommendation["recommended_route_id"] == "route_a"
        assert ordered[0]["route_id"] == "route_a"

    def test_ranking_criterion_2_fewest_high_miles_decides_winner(self) -> None:
        # Severe miles are equal (0.0). Route A has 10 mi High; Route B has 25 mi High.
        route_a = make_test_corridor(
            "route_a",
            100.0,
            120.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "low"),
                make_test_checkpoint("cp_a1", 90.0, "low"),
                make_test_checkpoint("cp_a2", 100.0, "high"),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            100.0,
            100.0,
            [
                make_test_checkpoint("cp_b0", 0.0, "low"),
                make_test_checkpoint("cp_b1", 75.0, "low"),
                make_test_checkpoint("cp_b2", 100.0, "high"),
            ],
        )

        _, recommendation = rank_and_score_corridors([route_b, route_a])
        assert recommendation["recommended_route_id"] == "route_a"

    def test_ranking_criterion_3_lowest_average_risk_decides_winner(
        self,
    ) -> None:
        # Severe miles equal (0), High miles equal (0).
        # Route A has mostly Low (avg risk lower), Route B has mostly Moderate.
        route_a = make_test_corridor(
            "route_a",
            100.0,
            120.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "low"),
                make_test_checkpoint("cp_a1", 100.0, "low"),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            100.0,
            110.0,  # Slightly faster, but higher average risk!
            [
                make_test_checkpoint("cp_b0", 0.0, "moderate"),
                make_test_checkpoint("cp_b1", 100.0, "moderate"),
            ],
        )

        _, recommendation = rank_and_score_corridors([route_b, route_a])
        assert recommendation["recommended_route_id"] == "route_a"

    def test_ranking_criterion_4_shortest_duration_decides_winner(
        self,
    ) -> None:
        # Weather hazards identical (all Low). Faster duration wins.
        route_a = make_test_corridor(
            "route_a",
            100.0,
            95.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "low"),
                make_test_checkpoint("cp_a1", 100.0, "low"),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            100.0,
            110.0,
            [
                make_test_checkpoint("cp_b0", 0.0, "low"),
                make_test_checkpoint("cp_b1", 100.0, "low"),
            ],
        )

        _, recommendation = rank_and_score_corridors([route_b, route_a])
        assert recommendation["recommended_route_id"] == "route_a"

    def test_no_travel_route_is_disqualified_from_recommendation(self) -> None:
        # Route A is short and fast but has a No Travel segment. Route B is eligible.
        route_a = make_test_corridor(
            "route_a",
            80.0,
            60.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "low"),
                make_test_checkpoint("cp_a1", 80.0, "no_travel", is_no_travel=True),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            120.0,
            120.0,
            [
                make_test_checkpoint("cp_b0", 0.0, "moderate"),
                make_test_checkpoint("cp_b1", 120.0, "moderate"),
            ],
        )

        ordered, recommendation = rank_and_score_corridors([route_a, route_b])
        assert recommendation["recommended_route_id"] == "route_b"
        assert recommendation["route_eligibility"]["route_a"] is False
        assert recommendation["route_eligibility"]["route_b"] is True
        # Ineligible route placed last in display order
        assert ordered[-1]["route_id"] == "route_a"

    def test_all_routes_contain_no_travel_returns_null_recommendation(
        self,
    ) -> None:
        route_a = make_test_corridor(
            "route_a",
            100.0,
            100.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "low"),
                make_test_checkpoint("cp_a1", 100.0, "no_travel", is_no_travel=True),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            100.0,
            110.0,
            [
                make_test_checkpoint("cp_b0", 0.0, "no_travel", is_no_travel=True),
                make_test_checkpoint("cp_b1", 100.0, "no_travel", is_no_travel=True),
            ],
        )

        ordered, recommendation = rank_and_score_corridors([route_b, route_a])
        assert recommendation["recommended_route_id"] is None
        assert recommendation["no_route_meets_safety_thresholds"] is True
        assert recommendation["route_eligibility"]["route_a"] is False
        assert recommendation["route_eligibility"]["route_b"] is False
        # Route A has less no_travel exposure (100 mi vs 100 mi, tie breaks by duration)
        assert ordered[0]["route_id"] == "route_a"

    def test_full_forecast_coverage_preferred_over_incomplete_forecast(
        self,
    ) -> None:
        # Route A has full coverage with Moderate risk.
        # Route B has Low risk on known segments, but 25% unknown weather.
        route_a = make_test_corridor(
            "route_a",
            100.0,
            120.0,
            [
                make_test_checkpoint("cp_a0", 0.0, "moderate"),
                make_test_checkpoint("cp_a1", 100.0, "moderate"),
            ],
        )
        route_b = make_test_corridor(
            "route_b",
            100.0,
            100.0,
            [
                make_test_checkpoint("cp_b0", 0.0, "low"),
                make_test_checkpoint("cp_b1", 75.0, "low"),
                make_test_checkpoint("cp_b2", 100.0, "unknown"),
            ],
        )

        _, recommendation = rank_and_score_corridors([route_b, route_a])
        assert recommendation["recommended_route_id"] == "route_a"

    def test_incomplete_forecast_recommended_with_warning_when_only_option(
        self,
    ) -> None:
        route_b = make_test_corridor(
            "route_b",
            100.0,
            100.0,
            [
                make_test_checkpoint("cp_b0", 0.0, "low"),
                make_test_checkpoint("cp_b1", 80.0, "low"),
                make_test_checkpoint("cp_b2", 100.0, "unknown"),
            ],
        )

        _, recommendation = rank_and_score_corridors([route_b])
        assert recommendation["recommended_route_id"] == "route_b"
        reasons_text = " ".join(recommendation["ranking_reasons"])
        assert "incomplete weather forecast" in reasons_text.lower()

    def test_single_route_input_produces_valid_recommendation(self) -> None:
        single_route = make_test_corridor(
            "route_single",
            50.0,
            45.0,
            [
                make_test_checkpoint("cp_0", 0.0, "low"),
                make_test_checkpoint("cp_1", 50.0, "low"),
            ],
        )

        ordered, recommendation = rank_and_score_corridors([single_route])
        assert len(ordered) == 1
        assert recommendation["recommended_route_id"] == "route_single"
        assert recommendation["route_eligibility"]["route_single"] is True
        assert recommendation["no_route_meets_safety_thresholds"] is False
