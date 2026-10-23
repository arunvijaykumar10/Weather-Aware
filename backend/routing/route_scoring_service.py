from typing import Any, Dict, List, Tuple

from .constants import (
    RANKING_AVG_RISK_PRECISION_DECIMALS,
    RANKING_DURATION_PRECISION_DECIMALS,
    RANKING_MILEAGE_PRECISION_DECIMALS,
)
from .risk_engine import NUMERIC_RISK_SCORE_MAP, RiskLevel, elevate_risk_level


def attribute_segment_mileages_and_risks(
    checkpoints: List[Dict[str, Any]], total_distance_miles: float
) -> Tuple[Dict[str, float], float, bool]:
    miles_by_category = {level.value: 0.0 for level in RiskLevel}
    if not checkpoints:
        return miles_by_category, 0.0, False

    if len(checkpoints) == 1:
        single_risk = checkpoints[0].get("load_adjusted_risk", RiskLevel.UNKNOWN.value)
        miles_by_category[single_risk] = round(total_distance_miles, 2)
        has_no_travel = single_risk == RiskLevel.NO_TRAVEL.value
        return miles_by_category, round(total_distance_miles, 2), has_no_travel

    accumulated_interval_miles = 0.0
    for index in range(len(checkpoints) - 1):
        cp_start = checkpoints[index]
        cp_end = checkpoints[index + 1]
        interval_length_miles = max(
            0.0,
            cp_end.get("cumulative_distance_miles", 0.0)
            - cp_start.get("cumulative_distance_miles", 0.0),
        )
        accumulated_interval_miles += interval_length_miles

        risk_start = RiskLevel(cp_start.get("load_adjusted_risk", RiskLevel.UNKNOWN.value))
        risk_end = RiskLevel(cp_end.get("load_adjusted_risk", RiskLevel.UNKNOWN.value))

        # Conservative safety rule: higher risk on segment endpoints governs the interval.
        interval_risk = _resolve_interval_risk(risk_start, risk_end)
        miles_by_category[interval_risk.value] = round(
            miles_by_category[interval_risk.value] + interval_length_miles, 2
        )

    # Ensure total allocated miles exactly matches authoritative total route distance.
    _normalize_mileage_sum(miles_by_category, accumulated_interval_miles, total_distance_miles)

    has_no_travel = miles_by_category[RiskLevel.NO_TRAVEL.value] > 0.0 or any(
        cp.get("is_no_travel", False) for cp in checkpoints
    )
    return miles_by_category, accumulated_interval_miles, has_no_travel


def _resolve_interval_risk(risk_start: RiskLevel, risk_end: RiskLevel) -> RiskLevel:
    if risk_start == RiskLevel.UNKNOWN and risk_end == RiskLevel.UNKNOWN:
        return RiskLevel.UNKNOWN

    # Severe hazards on either endpoint must never be masked by missing data on the other.
    if RiskLevel.NO_TRAVEL in (risk_start, risk_end):
        return RiskLevel.NO_TRAVEL
    if RiskLevel.SEVERE in (risk_start, risk_end):
        return RiskLevel.SEVERE

    # If unverified weather could hide an unmeasured hazard, interval cannot be certified as safe.
    if RiskLevel.UNKNOWN in (risk_start, risk_end):
        return RiskLevel.UNKNOWN

    return elevate_risk_level(risk_start, risk_end)


def _normalize_mileage_sum(
    miles_by_category: Dict[str, float],
    accumulated_interval_miles: float,
    total_distance_miles: float,
) -> None:
    discrepancy = round(total_distance_miles - accumulated_interval_miles, 2)
    if abs(discrepancy) > 0.001:
        # Float discretization delta attributed to largest existing risk category.
        dominant_category = max(miles_by_category.keys(), key=lambda cat: miles_by_category[cat])
        miles_by_category[dominant_category] = round(
            max(0.0, miles_by_category[dominant_category] + discrepancy), 2
        )


def compute_average_risk_score(
    miles_by_category: Dict[str, float],
) -> Tuple[str, float]:
    total_known_miles = 0.0
    accumulated_score = 0.0
    for level, score in NUMERIC_RISK_SCORE_MAP.items():
        category_miles = miles_by_category.get(level.value, 0.0)
        total_known_miles += category_miles
        accumulated_score += category_miles * score

    if total_known_miles <= 1e-4:
        return RiskLevel.UNKNOWN.value, 0.0

    numeric_average = round(accumulated_score / total_known_miles, 4)
    rounded_score = int(round(numeric_average))
    score_to_level = {v: k.value for k, v in NUMERIC_RISK_SCORE_MAP.items()}
    return score_to_level.get(rounded_score, RiskLevel.UNKNOWN.value), numeric_average


def compute_route_summary_metrics(
    checkpoints: List[Dict[str, Any]],
    distance_miles: float,
    duration_minutes: float,
) -> Dict[str, Any]:
    miles_by_cat, _, has_no_travel = attribute_segment_mileages_and_risks(
        checkpoints, distance_miles
    )
    avg_level_str, numeric_avg = compute_average_risk_score(miles_by_cat)

    known_miles = distance_miles - miles_by_cat[RiskLevel.UNKNOWN.value]
    coverage_pct = (
        round((known_miles / distance_miles) * 100.0, 1) if distance_miles > 0.0 else 100.0
    )

    return {
        "miles_per_risk_category": miles_by_cat,
        "severe_miles": miles_by_cat[RiskLevel.SEVERE.value],
        "high_miles": miles_by_cat[RiskLevel.HIGH.value],
        "no_travel_miles": miles_by_cat[RiskLevel.NO_TRAVEL.value],
        "unknown_miles": miles_by_cat[RiskLevel.UNKNOWN.value],
        "average_risk": avg_level_str,
        "numeric_average_risk": numeric_avg,
        "has_no_travel_segment": has_no_travel,
        "forecast_coverage_pct": max(0.0, min(100.0, coverage_pct)),
        "distance_miles": distance_miles,
        "duration_minutes": duration_minutes,
    }


def evaluate_route_eligibility(
    metrics: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    ineligibility_reasons: List[str] = []
    if metrics.get("has_no_travel_segment") or metrics.get("no_travel_miles", 0.0) > 0.0:
        ineligibility_reasons.append(
            f"Route contains {metrics.get('no_travel_miles', 0.0):.1f} miles of hazardous No-Travel weather conditions."
        )

    is_eligible = len(ineligibility_reasons) == 0
    return is_eligible, ineligibility_reasons


def _build_ranking_key(route: Dict[str, Any]) -> tuple:
    metrics = route["metrics"]
    return (
        round(metrics["severe_miles"], RANKING_MILEAGE_PRECISION_DECIMALS),
        round(metrics["high_miles"], RANKING_MILEAGE_PRECISION_DECIMALS),
        round(
            metrics["numeric_average_risk"],
            RANKING_AVG_RISK_PRECISION_DECIMALS,
        ),
        round(route["duration_minutes"], RANKING_DURATION_PRECISION_DECIMALS),
    )


def _build_unsafe_ranking_key(route: Dict[str, Any]) -> tuple:
    metrics = route["metrics"]
    return (
        round(metrics["no_travel_miles"], RANKING_MILEAGE_PRECISION_DECIMALS),
        *_build_ranking_key(route),
    )


def _generate_ranking_rationale(
    recommended_route: Dict[str, Any],
    all_routes: List[Dict[str, Any]],
    is_incomplete_forecast: bool,
) -> List[str]:
    reasons: List[str] = []
    rec_metrics = recommended_route["metrics"]
    rec_id = recommended_route["route_id"]

    if is_incomplete_forecast:
        unknown_pct = 100.0 - rec_metrics["forecast_coverage_pct"]
        reasons.append(
            f"Recommended corridor has incomplete weather forecast ({unknown_pct:.1f}% unverified); proceed with heightened caution."
        )

    if rec_metrics["severe_miles"] == 0.0:
        reasons.append(
            "Optimal safety: zero severe or no-travel weather exposure along the active corridor."
        )
    else:
        reasons.append(
            f"Lowest severe weather exposure among alternatives ({rec_metrics['severe_miles']:.1f} mi)."
        )

    for other_route in all_routes:
        if other_route["route_id"] == rec_id:
            continue
        other_metrics = other_route["metrics"]
        if other_metrics["has_no_travel_segment"] or other_metrics["no_travel_miles"] > 0.0:
            reasons.append(
                f"Alternative corridor {other_route['route_id']} was disqualified due to {other_metrics['no_travel_miles']:.1f} miles of No-Travel conditions."
            )
            continue
        if other_metrics["severe_miles"] > rec_metrics["severe_miles"] + 0.1:
            reasons.append(
                f"Bypasses {other_metrics['severe_miles']:.1f} miles of severe weather present on {other_route['route_id']}."
            )
        elif other_metrics["high_miles"] > rec_metrics["high_miles"] + 0.1:
            reasons.append(
                f"Reduces high-risk weather miles compared to {other_route['route_id']} ({rec_metrics['high_miles']:.1f} mi vs {other_metrics['high_miles']:.1f} mi)."
            )
        elif other_metrics["numeric_average_risk"] > rec_metrics["numeric_average_risk"] + 0.05:
            reasons.append(
                f"Lower average weather hazard score than {other_route['route_id']} ({rec_metrics['numeric_average_risk']:.2f} vs {other_metrics['numeric_average_risk']:.2f})."
            )
        elif other_route["duration_minutes"] > recommended_route["duration_minutes"] + 1.0:
            reasons.append(
                f"Shorter travel time than {other_route['route_id']} ({recommended_route['duration_minutes']:.1f} min vs {other_route['duration_minutes']:.1f} min)."
            )

    return reasons


def rank_and_score_corridors(
    corridors: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not corridors:
        return [], {
            "recommended_route_id": None,
            "route_eligibility": {},
            "ranking_reasons": ["No route corridors were provided for analysis."],
            "no_route_meets_safety_thresholds": True,
        }

    for corridor in corridors:
        corridor["metrics"] = compute_route_summary_metrics(
            checkpoints=corridor.get("checkpoints", []),
            distance_miles=corridor.get("distance_miles", 0.0),
            duration_minutes=corridor.get("duration_minutes", 0.0),
        )
        is_eligible, ineligibility_reasons = evaluate_route_eligibility(corridor["metrics"])
        corridor["eligibility"] = {
            "is_eligible": is_eligible,
            "ineligibility_reasons": ineligibility_reasons,
        }

    route_eligibility_map = {c["route_id"]: c["eligibility"]["is_eligible"] for c in corridors}
    eligible_corridors = [c for c in corridors if c["eligibility"]["is_eligible"]]

    if not eligible_corridors:
        sorted_corridors = sorted(corridors, key=_build_unsafe_ranking_key)
        return sorted_corridors, {
            "recommended_route_id": None,
            "route_eligibility": route_eligibility_map,
            "ranking_reasons": [
                "No route meets the supplied safety thresholds; all candidate corridors contain hazardous No-Travel weather."
            ],
            "no_route_meets_safety_thresholds": True,
        }

    # Prefer eligible corridors with 100% verified forecast coverage.
    full_coverage_corridors = [
        c for c in eligible_corridors if c["metrics"]["forecast_coverage_pct"] >= 100.0
    ]
    candidate_pool = full_coverage_corridors if full_coverage_corridors else eligible_corridors
    is_incomplete = len(full_coverage_corridors) == 0

    sorted_eligible = sorted(candidate_pool, key=_build_ranking_key)
    recommended_route = sorted_eligible[0]

    ranking_reasons = _generate_ranking_rationale(recommended_route, corridors, is_incomplete)

    ineligible_corridors = [c for c in corridors if not c["eligibility"]["is_eligible"]]
    ordered_corridors = (
        sorted_eligible
        + [c for c in eligible_corridors if c not in sorted_eligible]
        + sorted(ineligible_corridors, key=_build_unsafe_ranking_key)
    )

    recommendation_payload = {
        "recommended_route_id": recommended_route["route_id"],
        "route_eligibility": route_eligibility_map,
        "ranking_reasons": ranking_reasons,
        "no_route_meets_safety_thresholds": False,
    }
    return ordered_corridors, recommendation_payload
