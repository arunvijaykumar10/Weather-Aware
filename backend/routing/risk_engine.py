from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

WIND_MODERATE_THRESHOLD_MPH = 25.0
WIND_HIGH_THRESHOLD_MPH = 35.0
WIND_SEVERE_THRESHOLD_MPH = 45.0
WIND_NO_TRAVEL_THRESHOLD_MPH = 55.0

RAIN_MODERATE_THRESHOLD_IN_PER_HR = 0.10
RAIN_HIGH_THRESHOLD_IN_PER_HR = 0.25
RAIN_SEVERE_THRESHOLD_IN_PER_HR = 0.50
RAIN_NO_TRAVEL_THRESHOLD_IN_PER_HR = 1.00

SNOW_MODERATE_THRESHOLD_IN_PER_HR = 0.50
SNOW_HIGH_THRESHOLD_IN_PER_HR = 1.00
SNOW_SEVERE_THRESHOLD_IN_PER_HR = 2.00
SNOW_NO_TRAVEL_THRESHOLD_IN_PER_HR = 3.00

LOAD_RULE_HIGH_WIND_WEIGHT_FLOOR_LB = 30000.0
LOAD_RULE_MODERATE_WIND_WEIGHT_FLOOR_LB = 40000.0

RULE_WIND_GE_55_ANY_LOAD = "wind_ge_55_any_load"
RULE_WIND_45_55_LOAD_GT_30K = "wind_45_55_load_gt_30k"
RULE_WIND_35_45_LOAD_GT_40K = "wind_35_45_load_gt_40k"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    NO_TRAVEL = "no_travel"
    UNKNOWN = "unknown"


NUMERIC_RISK_SCORE_MAP = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.SEVERE: 3,
    RiskLevel.NO_TRAVEL: 4,
}


@dataclass(frozen=True)
class CheckpointRiskAssessment:
    wind_risk: RiskLevel
    rain_risk: RiskLevel
    snow_risk: RiskLevel
    weather_risk: RiskLevel
    load_adjusted_risk: RiskLevel
    load_rule_applied: Optional[str]
    is_no_travel: bool
    numeric_risk_score: Optional[int]
    has_unknown_conditions: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_risks": {
                "wind_risk": self.wind_risk.value,
                "rain_risk": self.rain_risk.value,
                "snow_risk": self.snow_risk.value,
            },
            "weather_risk": self.weather_risk.value,
            "load_adjusted_risk": self.load_adjusted_risk.value,
            "load_rule_applied": self.load_rule_applied,
            "is_no_travel": self.is_no_travel,
            "numeric_risk_score": self.numeric_risk_score,
            "has_unknown_conditions": self.has_unknown_conditions,
        }


def classify_wind_risk(
    wind_speed_mph: Optional[float], wind_gusts_mph: Optional[float] = None
) -> RiskLevel:
    # Gusts drive truck roll-over risk; fall back to sustained speed when gusts are not reported.
    effective_wind = wind_gusts_mph if wind_gusts_mph is not None else wind_speed_mph
    if effective_wind is None:
        return RiskLevel.UNKNOWN

    if effective_wind < WIND_MODERATE_THRESHOLD_MPH:
        return RiskLevel.LOW
    if effective_wind < WIND_HIGH_THRESHOLD_MPH:
        return RiskLevel.MODERATE
    if effective_wind < WIND_SEVERE_THRESHOLD_MPH:
        return RiskLevel.HIGH
    if effective_wind < WIND_NO_TRAVEL_THRESHOLD_MPH:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def classify_rain_risk(rain_in_per_hr: Optional[float]) -> RiskLevel:
    if rain_in_per_hr is None:
        return RiskLevel.UNKNOWN

    if rain_in_per_hr < RAIN_MODERATE_THRESHOLD_IN_PER_HR:
        return RiskLevel.LOW
    if rain_in_per_hr < RAIN_HIGH_THRESHOLD_IN_PER_HR:
        return RiskLevel.MODERATE
    if rain_in_per_hr < RAIN_SEVERE_THRESHOLD_IN_PER_HR:
        return RiskLevel.HIGH
    # Rain assessment defines Severe as 0.50 through 1.00 inclusive; strictly greater is No Travel.
    if rain_in_per_hr <= RAIN_NO_TRAVEL_THRESHOLD_IN_PER_HR:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def classify_snow_risk(snow_in_per_hr: Optional[float]) -> RiskLevel:
    if snow_in_per_hr is None:
        return RiskLevel.UNKNOWN

    if snow_in_per_hr < SNOW_MODERATE_THRESHOLD_IN_PER_HR:
        return RiskLevel.LOW
    if snow_in_per_hr < SNOW_HIGH_THRESHOLD_IN_PER_HR:
        return RiskLevel.MODERATE
    if snow_in_per_hr < SNOW_SEVERE_THRESHOLD_IN_PER_HR:
        return RiskLevel.HIGH
    # Snow assessment defines Severe as 2.0 through 3.0 inclusive; strictly greater is No Travel.
    if snow_in_per_hr <= SNOW_NO_TRAVEL_THRESHOLD_IN_PER_HR:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def elevate_risk_level(base_risk: RiskLevel, candidate_risk: RiskLevel) -> RiskLevel:
    if candidate_risk == RiskLevel.UNKNOWN:
        return base_risk
    if base_risk == RiskLevel.UNKNOWN:
        return candidate_risk

    base_score = NUMERIC_RISK_SCORE_MAP[base_risk]
    candidate_score = NUMERIC_RISK_SCORE_MAP[candidate_risk]
    return candidate_risk if candidate_score > base_score else base_risk


def combine_weather_risks(
    wind_risk: RiskLevel, rain_risk: RiskLevel, snow_risk: RiskLevel
) -> Tuple[RiskLevel, bool]:
    condition_list = [wind_risk, rain_risk, snow_risk]
    has_unknown = any(risk == RiskLevel.UNKNOWN for risk in condition_list)

    known_risks = [risk for risk in condition_list if risk != RiskLevel.UNKNOWN]
    if not known_risks:
        return RiskLevel.UNKNOWN, has_unknown

    highest_known_risk = known_risks[0]
    for risk in known_risks[1:]:
        highest_known_risk = elevate_risk_level(highest_known_risk, risk)

    return highest_known_risk, has_unknown


def apply_load_rules(
    weather_risk: RiskLevel,
    wind_speed_mph: Optional[float],
    wind_gusts_mph: Optional[float],
    load_weight_lb: float,
) -> Tuple[RiskLevel, Optional[str]]:
    effective_wind = wind_gusts_mph if wind_gusts_mph is not None else wind_speed_mph
    if effective_wind is None:
        return weather_risk, None

    if effective_wind >= WIND_NO_TRAVEL_THRESHOLD_MPH:
        return RiskLevel.NO_TRAVEL, RULE_WIND_GE_55_ANY_LOAD

    # 'Load >' is strictly greater than the threshold weight.
    if (
        WIND_SEVERE_THRESHOLD_MPH <= effective_wind < WIND_NO_TRAVEL_THRESHOLD_MPH
        and load_weight_lb > LOAD_RULE_HIGH_WIND_WEIGHT_FLOOR_LB
    ):
        return RiskLevel.NO_TRAVEL, RULE_WIND_45_55_LOAD_GT_30K

    if (
        WIND_HIGH_THRESHOLD_MPH <= effective_wind < WIND_SEVERE_THRESHOLD_MPH
        and load_weight_lb > LOAD_RULE_MODERATE_WIND_WEIGHT_FLOOR_LB
    ):
        # Load rules escalate risk but must never reduce an already-higher weather risk.
        adjusted_risk = elevate_risk_level(weather_risk, RiskLevel.SEVERE)
        return adjusted_risk, RULE_WIND_35_45_LOAD_GT_40K

    return weather_risk, None


def evaluate_checkpoint_risk(
    wind_speed_mph: Optional[float],
    wind_gusts_mph: Optional[float],
    rain_in_per_hr: Optional[float],
    snow_in_per_hr: Optional[float],
    load_weight_lb: float,
) -> CheckpointRiskAssessment:
    wind_risk = classify_wind_risk(wind_speed_mph, wind_gusts_mph)
    rain_risk = classify_rain_risk(rain_in_per_hr)
    snow_risk = classify_snow_risk(snow_in_per_hr)

    weather_risk, has_unknown = combine_weather_risks(wind_risk, rain_risk, snow_risk)
    load_adjusted_risk, rule_applied = apply_load_rules(
        weather_risk, wind_speed_mph, wind_gusts_mph, load_weight_lb
    )

    numeric_score = NUMERIC_RISK_SCORE_MAP.get(load_adjusted_risk)
    is_no_travel = load_adjusted_risk == RiskLevel.NO_TRAVEL

    return CheckpointRiskAssessment(
        wind_risk=wind_risk,
        rain_risk=rain_risk,
        snow_risk=snow_risk,
        weather_risk=weather_risk,
        load_adjusted_risk=load_adjusted_risk,
        load_rule_applied=rule_applied,
        is_no_travel=is_no_travel,
        numeric_risk_score=numeric_score,
        has_unknown_conditions=has_unknown,
    )


def _compute_average_corridor_risk(miles_by_category: Dict[str, float]) -> str:
    total_known_miles = 0.0
    weighted_score_sum = 0.0
    for level, score in NUMERIC_RISK_SCORE_MAP.items():
        miles = miles_by_category.get(level.value, 0.0)
        total_known_miles += miles
        weighted_score_sum += miles * score

    if total_known_miles <= 1e-4:
        return RiskLevel.UNKNOWN.value

    # Nearest integer score maps back to representative RiskLevel.
    mean_score = int(round(weighted_score_sum / total_known_miles))
    score_to_level = {v: k.value for k, v in NUMERIC_RISK_SCORE_MAP.items()}
    return score_to_level.get(mean_score, RiskLevel.UNKNOWN.value)


def compute_corridor_risk_metrics(
    checkpoints: list,
    total_distance_miles: float,
    forecast_coverage_pct: float,
) -> Dict[str, Any]:
    miles_by_category = {level.value: 0.0 for level in RiskLevel}
    if not checkpoints:
        return {
            "miles_per_risk_category": miles_by_category,
            "severe_miles": 0.0,
            "high_miles": 0.0,
            "no_travel_miles": 0.0,
            "unknown_miles": 0.0,
            "average_risk": RiskLevel.UNKNOWN.value,
            "has_no_travel_segment": False,
            "forecast_coverage_pct": forecast_coverage_pct,
        }

    if len(checkpoints) == 1:
        single_risk = checkpoints[0].get("load_adjusted_risk", RiskLevel.UNKNOWN.value)
        miles_by_category[single_risk] = round(total_distance_miles, 2)
    else:
        for index in range(len(checkpoints) - 1):
            cp_start = checkpoints[index]
            cp_end = checkpoints[index + 1]
            segment_miles = max(
                0.0,
                cp_end.get("cumulative_distance_miles", 0.0)
                - cp_start.get("cumulative_distance_miles", 0.0),
            )
            # Conservative safety principle: the higher risk of adjacent checkpoints governs the connecting segment.
            risk_start = RiskLevel(cp_start.get("load_adjusted_risk", RiskLevel.UNKNOWN.value))
            risk_end = RiskLevel(cp_end.get("load_adjusted_risk", RiskLevel.UNKNOWN.value))
            segment_risk = elevate_risk_level(risk_start, risk_end)
            miles_by_category[segment_risk.value] = round(
                miles_by_category[segment_risk.value] + segment_miles, 2
            )

    has_no_travel = miles_by_category[RiskLevel.NO_TRAVEL.value] > 0.0 or any(
        cp.get("is_no_travel", False) for cp in checkpoints
    )

    return {
        "miles_per_risk_category": miles_by_category,
        "severe_miles": miles_by_category[RiskLevel.SEVERE.value],
        "high_miles": miles_by_category[RiskLevel.HIGH.value],
        "no_travel_miles": miles_by_category[RiskLevel.NO_TRAVEL.value],
        "unknown_miles": miles_by_category[RiskLevel.UNKNOWN.value],
        "average_risk": _compute_average_corridor_risk(miles_by_category),
        "has_no_travel_segment": has_no_travel,
        "forecast_coverage_pct": forecast_coverage_pct,
    }
