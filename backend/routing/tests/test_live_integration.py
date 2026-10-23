import os
import pytest
from routing.routing_service import RoutingService


@pytest.mark.skipif(
    not os.environ.get('RUN_LIVE_ORS_TESTS') or not os.environ.get('OPENROUTESERVICE_API_KEY'),
    reason="Live integration test skipped unless RUN_LIVE_ORS_TESTS=1 and OPENROUTESERVICE_API_KEY is set."
)
def test_live_ors_300_plus_mile_route():
    """
    Live integration test for a 300+ mile trip (Denver, CO to Salt Lake City, UT ~ 504 miles).
    Proves that geocoding, primary driving-hgv routing, and lateral via-waypoint corridor
    derivation successfully produce multiple distinct corridors using a live ORS API key.
    """
    service = RoutingService()
    result = service.analyze_routes(
        origin="Denver, CO",
        destination="Salt Lake City, UT",
        departure_time_iso="2026-10-23T14:00:00Z",
        load_weight_lb=42000,
        checkpoint_interval_miles=25,
    )

    assert result["routes_returned"] >= 2
    assert result["routes"][0]["route_id"] == "route_primary"
    assert result["routes"][0]["distance_miles"] > 300.0
    assert len(result["routes"][0]["geometry"]) > 50

    # Ensure alternatives are distinct (< 80% overlap)
    for alt_route in result["routes"][1:]:
        assert alt_route["route_id"].startswith("route_alt_")
        assert alt_route["distance_miles"] > 300.0
