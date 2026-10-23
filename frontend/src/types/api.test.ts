import { describe, it, expect } from 'vitest';
import { RouteAnalyzeRequest, RouteAnalyzeResponse, RiskLevel, WeatherAvailability } from './api';

describe('API Contract Types', () => {
  it('validates TypeScript shapes against a full response fixture', () => {
    const mockResponse: RouteAnalyzeResponse = {
      routes_requested: 3,
      routes_returned: 1,
      fewer_routes_reason: 'Only one primary highway route is available.',
      routes: [
        {
          route_id: 'route_alpha',
          provider_summary: 'I-80 W corridor',
          geometry: [
            [39.7392, -104.9903],
            [40.7608, -111.891],
          ],
          distance_miles: 504.2,
          duration_minutes: 480.0,
          checkpoints: [
            {
              checkpoint_id: 'cp_01',
              lat: 39.7392,
              lon: -104.9903,
              cumulative_distance_miles: 0,
              eta: '2026-10-23T14:00:00Z',
              forecast_timestamp: '2026-10-23T14:00:00Z',
              weather: {
                wind_speed_mph: 15.0,
                wind_speed_availability: 'available' as WeatherAvailability,
                rain_in_per_hr: 0.05,
                rain_availability: 'available' as WeatherAvailability,
                snow_in_per_hr: 0.0,
                snow_availability: 'available' as WeatherAvailability,
              },
              condition_risks: {
                wind_risk: 'low' as RiskLevel,
                rain_risk: 'moderate' as RiskLevel,
                snow_risk: 'low' as RiskLevel,
              },
              weather_risk: 'moderate' as RiskLevel,
              load_adjusted_risk: 'moderate' as RiskLevel,
              load_rule_applied: null,
            },
          ],
          metrics: {
            miles_per_risk_category: {
              low: 450.0,
              moderate: 54.2,
              high: 0,
              severe: 0,
              no_travel: 0,
              unknown: 0,
            },
            severe_miles: 0,
            high_miles: 0,
            no_travel_miles: 0,
            unknown_miles: 0,
            average_risk: 'low' as RiskLevel,
            has_no_travel_segment: false,
            forecast_coverage_pct: 100.0,
          },
          eligibility: {
            is_eligible: true,
            ineligibility_reasons: [],
          },
        },
      ],
      recommendation: {
        recommended_route_id: 'route_alpha',
        route_eligibility: { route_alpha: true },
        ranking_reasons: ['Lowest risk corridor with full forecast coverage'],
        no_route_meets_safety_thresholds: false,
      },
      forecast_timeline: [],
      warnings: [],
      provider_errors: [],
    };

    expect(mockResponse.routes.length).toBe(1);
    expect(mockResponse.routes[0].checkpoints[0].weather_risk).toBe('moderate');
    expect(mockResponse.recommendation.no_route_meets_safety_thresholds).toBe(false);
  });

  it('validates request type construction', () => {
    const request: RouteAnalyzeRequest = {
      origin: 'Chicago, IL',
      destination: 'Detroit, MI',
      departure_time: '2026-10-23T14:00:00Z',
      load_weight_lb: 45000,
      checkpoint_interval_miles: 25,
    };

    expect(request.origin).toBe('Chicago, IL');
    expect(request.checkpoint_interval_miles).toBe(25);
  });
});
