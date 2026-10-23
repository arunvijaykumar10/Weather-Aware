from typing import Optional

import pytest

from routing.risk_engine import (
    RULE_WIND_35_45_LOAD_GT_40K,
    RULE_WIND_45_55_LOAD_GT_30K,
    RULE_WIND_GE_55_ANY_LOAD,
    RiskLevel,
    apply_load_rules,
    classify_rain_risk,
    classify_snow_risk,
    classify_wind_risk,
    combine_weather_risks,
    evaluate_checkpoint_risk,
)


@pytest.mark.parametrize(
    "wind_speed,expected_risk",
    [
        (0.0, RiskLevel.LOW),
        (24.9, RiskLevel.LOW),
        (25.0, RiskLevel.MODERATE),
        (25.1, RiskLevel.MODERATE),
        (34.9, RiskLevel.MODERATE),
        (35.0, RiskLevel.HIGH),
        (35.1, RiskLevel.HIGH),
        (44.9, RiskLevel.HIGH),
        (45.0, RiskLevel.SEVERE),
        (45.1, RiskLevel.SEVERE),
        (54.9, RiskLevel.SEVERE),
        (55.0, RiskLevel.NO_TRAVEL),
        (55.1, RiskLevel.NO_TRAVEL),
        (75.0, RiskLevel.NO_TRAVEL),
        (None, RiskLevel.UNKNOWN),
    ],
)
def test_wind_risk_boundary_classification(
    wind_speed: Optional[float], expected_risk: RiskLevel
) -> None:
    assert classify_wind_risk(wind_speed) == expected_risk


def test_wind_gusts_take_precedence_over_sustained_speed() -> None:
    # Sustained 20 mph is Low, but gust of 48 mph escalates risk to Severe.
    assert classify_wind_risk(20.0, wind_gusts_mph=48.0) == RiskLevel.SEVERE


@pytest.mark.parametrize(
    "rain_rate,expected_risk",
    [
        (0.0, RiskLevel.LOW),
        (0.09, RiskLevel.LOW),
        (0.10, RiskLevel.MODERATE),
        (0.11, RiskLevel.MODERATE),
        (0.24, RiskLevel.MODERATE),
        (0.25, RiskLevel.HIGH),
        (0.26, RiskLevel.HIGH),
        (0.49, RiskLevel.HIGH),
        (0.50, RiskLevel.SEVERE),
        (0.51, RiskLevel.SEVERE),
        (0.99, RiskLevel.SEVERE),
        (1.00, RiskLevel.SEVERE),  # Rain assessment defines Severe through 1.00 inclusive
        (1.01, RiskLevel.NO_TRAVEL),
        (2.50, RiskLevel.NO_TRAVEL),
        (None, RiskLevel.UNKNOWN),
    ],
)
def test_rain_risk_boundary_classification(
    rain_rate: Optional[float], expected_risk: RiskLevel
) -> None:
    assert classify_rain_risk(rain_rate) == expected_risk


@pytest.mark.parametrize(
    "snow_rate,expected_risk",
    [
        (0.0, RiskLevel.LOW),
        (0.49, RiskLevel.LOW),
        (0.50, RiskLevel.MODERATE),
        (0.51, RiskLevel.MODERATE),
        (0.99, RiskLevel.MODERATE),
        (1.00, RiskLevel.HIGH),
        (1.01, RiskLevel.HIGH),
        (1.99, RiskLevel.HIGH),
        (2.00, RiskLevel.SEVERE),
        (2.01, RiskLevel.SEVERE),
        (2.99, RiskLevel.SEVERE),
        (3.00, RiskLevel.SEVERE),  # Snow assessment defines Severe through 3.00 inclusive
        (3.01, RiskLevel.NO_TRAVEL),
        (5.00, RiskLevel.NO_TRAVEL),
        (None, RiskLevel.UNKNOWN),
    ],
)
def test_snow_risk_boundary_classification(
    snow_rate: Optional[float], expected_risk: RiskLevel
) -> None:
    assert classify_snow_risk(snow_rate) == expected_risk


@pytest.mark.parametrize(
    "wind,load,expected_risk,expected_rule",
    [
        # Rule 1: Wind >= 55 mph -> No Travel for any load
        (55.0, 10000.0, RiskLevel.NO_TRAVEL, RULE_WIND_GE_55_ANY_LOAD),
        (60.0, 75000.0, RiskLevel.NO_TRAVEL, RULE_WIND_GE_55_ANY_LOAD),
        # Rule 2: Wind 45 to <55 mph AND load > 30,000 lb -> No Travel
        (50.0, 29999.0, RiskLevel.SEVERE, None),
        (50.0, 30000.0, RiskLevel.SEVERE, None),  # Exactly 30k does NOT trigger strictly greater
        (50.0, 30000.1, RiskLevel.NO_TRAVEL, RULE_WIND_45_55_LOAD_GT_30K),
        (54.9, 45000.0, RiskLevel.NO_TRAVEL, RULE_WIND_45_55_LOAD_GT_30K),
        # Rule 3: Wind 35 to <45 mph AND load > 40,000 lb -> at least Severe
        (40.0, 39999.0, RiskLevel.HIGH, None),
        (40.0, 40000.0, RiskLevel.HIGH, None),  # Exactly 40k does NOT trigger strictly greater
        (40.0, 40000.1, RiskLevel.SEVERE, RULE_WIND_35_45_LOAD_GT_40K),
        (35.0, 60000.0, RiskLevel.SEVERE, RULE_WIND_35_45_LOAD_GT_40K),
    ],
)
def test_load_rule_boundary_triggers(
    wind: float,
    load: float,
    expected_risk: RiskLevel,
    expected_rule: Optional[str],
) -> None:
    weather_risk = classify_wind_risk(wind)
    adjusted_risk, rule_applied = apply_load_rules(weather_risk, wind, None, load)
    assert adjusted_risk == expected_risk
    assert rule_applied == expected_rule


def test_load_rule_never_downgrades_higher_weather_risk() -> None:
    # Extreme snow (3.5 in/hr) produces No Travel weather risk.
    # Wind of 38 mph with load 45,000 lb triggers Rule 3 (at least Severe).
    # Final load-adjusted risk must remain No Travel.
    assessment = evaluate_checkpoint_risk(
        wind_speed_mph=38.0,
        wind_gusts_mph=None,
        rain_in_per_hr=0.0,
        snow_in_per_hr=3.5,
        load_weight_lb=45000.0,
    )
    assert assessment.weather_risk == RiskLevel.NO_TRAVEL
    assert assessment.load_adjusted_risk == RiskLevel.NO_TRAVEL
    assert assessment.load_rule_applied == RULE_WIND_35_45_LOAD_GT_40K
    assert assessment.is_no_travel is True
    assert assessment.numeric_risk_score == 4


@pytest.mark.parametrize(
    "wind,rain,snow,expected_max_risk",
    [
        (RiskLevel.LOW, RiskLevel.SEVERE, RiskLevel.MODERATE, RiskLevel.SEVERE),
        (RiskLevel.HIGH, RiskLevel.LOW, RiskLevel.LOW, RiskLevel.HIGH),
        (RiskLevel.MODERATE, RiskLevel.MODERATE, RiskLevel.NO_TRAVEL, RiskLevel.NO_TRAVEL),
        (RiskLevel.LOW, RiskLevel.LOW, RiskLevel.LOW, RiskLevel.LOW),
    ],
)
def test_mixed_conditions_select_highest_risk(
    wind: RiskLevel,
    rain: RiskLevel,
    snow: RiskLevel,
    expected_max_risk: RiskLevel,
) -> None:
    combined, has_unknown = combine_weather_risks(wind, rain, snow)
    assert combined == expected_max_risk
    assert has_unknown is False


def test_single_missing_variable_does_not_mask_known_higher_risk() -> None:
    # High wind (40 mph) with missing rain and low snow
    assessment = evaluate_checkpoint_risk(
        wind_speed_mph=40.0,
        wind_gusts_mph=None,
        rain_in_per_hr=None,
        snow_in_per_hr=0.1,
        load_weight_lb=25000.0,
    )
    assert assessment.wind_risk == RiskLevel.HIGH
    assert assessment.rain_risk == RiskLevel.UNKNOWN
    assert assessment.snow_risk == RiskLevel.LOW
    assert assessment.weather_risk == RiskLevel.HIGH
    assert assessment.has_unknown_conditions is True


def test_all_missing_variables_produce_unknown_risk() -> None:
    assessment = evaluate_checkpoint_risk(
        wind_speed_mph=None,
        wind_gusts_mph=None,
        rain_in_per_hr=None,
        snow_in_per_hr=None,
        load_weight_lb=40000.0,
    )
    assert assessment.weather_risk == RiskLevel.UNKNOWN
    assert assessment.load_adjusted_risk == RiskLevel.UNKNOWN
    assert assessment.numeric_risk_score is None
    assert assessment.has_unknown_conditions is True
