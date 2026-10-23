import { RouteAnalyzeResponse } from '../types/api';

/**
 * DEVELOPMENT ONLY MOCK FIXTURE
 * Clearly marked as MOCK. Never displayed as live operational routing results.
 */
export const MOCK_ROUTE_ANALYSIS_DATA: RouteAnalyzeResponse = {
  routes_requested: 3,
  routes_returned: 2,
  fewer_routes_reason:
    'Only 2 distinct driving corridors meet detour (<= 1.5x) and overlap (<= 80%) criteria.',
  routes: [
    {
      route_id: 'route_primary',
      provider_summary: 'I-80 W Commercial Corridor (Denver to Salt Lake City)',
      geometry: [
        [39.7392, -104.9903],
        [41.1399, -104.8202],
        [40.7608, -111.891],
      ],
      distance_miles: 504.2,
      duration_minutes: 480.0,
      checkpoints: [
        {
          checkpoint_id: 'cp_0',
          lat: 39.7392,
          lon: -104.9903,
          cumulative_distance_miles: 0.0,
          eta: '2026-10-23T14:00:00Z',
          forecast_timestamp: '2026-10-23T14:00:00Z',
          weather: {
            wind_speed_mph: 12.0,
            wind_gusts_mph: 18.0,
            wind_speed_availability: 'available',
            rain_in_per_hr: 0.0,
            rain_availability: 'available',
            snow_in_per_hr: 0.0,
            snow_availability: 'available',
          },
          condition_risks: {
            wind_risk: 'low',
            rain_risk: 'low',
            snow_risk: 'low',
          },
          weather_risk: 'low',
          load_adjusted_risk: 'low',
          load_rule_applied: null,
        },
        {
          checkpoint_id: 'cp_1',
          lat: 41.1399,
          lon: -104.8202,
          cumulative_distance_miles: 100.0,
          eta: '2026-10-23T15:35:00Z',
          forecast_timestamp: '2026-10-23T16:00:00Z',
          weather: {
            wind_speed_mph: 22.0,
            wind_gusts_mph: 32.0,
            wind_speed_availability: 'available',
            rain_in_per_hr: 0.02,
            rain_availability: 'available',
            snow_in_per_hr: 0.0,
            snow_availability: 'available',
          },
          condition_risks: {
            wind_risk: 'moderate',
            rain_risk: 'low',
            snow_risk: 'low',
          },
          weather_risk: 'moderate',
          load_adjusted_risk: 'moderate',
          load_rule_applied: null,
        },
        {
          checkpoint_id: 'cp_2',
          lat: 40.7608,
          lon: -111.891,
          cumulative_distance_miles: 504.2,
          eta: '2026-10-23T22:00:00Z',
          forecast_timestamp: '2026-10-23T22:00:00Z',
          weather: {
            wind_speed_mph: 8.0,
            wind_gusts_mph: 12.0,
            wind_speed_availability: 'available',
            rain_in_per_hr: 0.0,
            rain_availability: 'available',
            snow_in_per_hr: 0.0,
            snow_availability: 'available',
          },
          condition_risks: {
            wind_risk: 'low',
            rain_risk: 'low',
            snow_risk: 'low',
          },
          weather_risk: 'low',
          load_adjusted_risk: 'low',
          load_rule_applied: null,
        },
      ],
      metrics: {
        miles_per_risk_category: {
          low: 404.2,
          moderate: 100.0,
          high: 0.0,
          severe: 0.0,
          no_travel: 0.0,
          unknown: 0.0,
        },
        severe_miles: 0.0,
        high_miles: 0.0,
        no_travel_miles: 0.0,
        unknown_miles: 0.0,
        average_risk: 'low',
        has_no_travel_segment: false,
        forecast_coverage_pct: 100.0,
      },
      eligibility: {
        is_eligible: true,
        ineligibility_reasons: [],
      },
    },
    {
      route_id: 'route_alt_1',
      provider_summary: 'US-40 W Southern Bypass',
      geometry: [
        [39.7392, -104.9903],
        [40.05, -108.2],
        [40.7608, -111.891],
      ],
      distance_miles: 548.0,
      duration_minutes: 540.0,
      checkpoints: [
        {
          checkpoint_id: 'cp_alt_0',
          lat: 39.7392,
          lon: -104.9903,
          cumulative_distance_miles: 0.0,
          eta: '2026-10-23T14:00:00Z',
          forecast_timestamp: '2026-10-23T14:00:00Z',
          weather: {
            wind_speed_mph: 14.0,
            wind_gusts_mph: 20.0,
            wind_speed_availability: 'available',
            rain_in_per_hr: 0.0,
            rain_availability: 'available',
            snow_in_per_hr: 0.0,
            snow_availability: 'available',
          },
          condition_risks: {
            wind_risk: 'low',
            rain_risk: 'low',
            snow_risk: 'low',
          },
          weather_risk: 'low',
          load_adjusted_risk: 'low',
          load_rule_applied: null,
        },
        {
          checkpoint_id: 'cp_alt_1',
          lat: 40.7608,
          lon: -111.891,
          cumulative_distance_miles: 548.0,
          eta: '2026-10-23T23:00:00Z',
          forecast_timestamp: '2026-10-23T23:00:00Z',
          weather: {
            wind_speed_mph: 38.0,
            wind_gusts_mph: 46.0,
            wind_speed_availability: 'available',
            rain_in_per_hr: 0.15,
            rain_availability: 'available',
            snow_in_per_hr: 0.0,
            snow_availability: 'available',
          },
          condition_risks: {
            wind_risk: 'severe',
            rain_risk: 'moderate',
            snow_risk: 'low',
          },
          weather_risk: 'severe',
          load_adjusted_risk: 'severe',
          load_rule_applied: null,
        },
      ],
      metrics: {
        miles_per_risk_category: {
          low: 348.0,
          moderate: 150.0,
          high: 0.0,
          severe: 50.0,
          no_travel: 0.0,
          unknown: 0.0,
        },
        severe_miles: 50.0,
        high_miles: 0.0,
        no_travel_miles: 0.0,
        unknown_miles: 0.0,
        average_risk: 'moderate',
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
    recommended_route_id: 'route_primary',
    route_eligibility: {
      route_primary: true,
      route_alt_1: true,
    },
    ranking_reasons: [
      'Optimal safety: zero severe or no-travel weather exposure along the active corridor.',
      'Bypasses 50.0 miles of severe weather present on route_alt_1.',
      'Shorter travel time than route_alt_1 (480.0 min vs 540.0 min).',
    ],
    no_route_meets_safety_thresholds: false,
  },
  forecast_timeline: [],
  warnings: ['Long-distance route: alternative paths were derived via lateral corridor bypasses.'],
  provider_errors: [],
};

import { RouteForecastTimelineResponse, HourlyTimelineEntry } from '../types/api';

const generateMockHourlyTimeline = (
  baseTimestamp: string,
  baseWind = 15.0,
  baseRain = 0.0,
  baseSnow = 0.0
): HourlyTimelineEntry[] => {
  const baseDate = new Date(baseTimestamp);
  return Array.from({ length: 49 }, (_, h) => {
    const time = new Date(baseDate.getTime() + h * 3600 * 1000).toISOString();
    // Simulate changing weather across time
    const wind = Math.round((baseWind + Math.sin(h / 6) * 12) * 10) / 10;
    const rain = h >= 12 && h <= 20 ? Math.round(baseRain * 10 + 0.15 * 10) / 10 : baseRain;
    const snow = baseSnow;

    let risk: 'low' | 'moderate' | 'high' | 'severe' | 'no_travel' = 'low';
    let score = 0;
    if (wind >= 55) {
      risk = 'no_travel';
      score = 4;
    } else if (wind >= 45) {
      risk = 'severe';
      score = 3;
    } else if (wind >= 35) {
      risk = 'high';
      score = 2;
    } else if (wind >= 25 || rain >= 0.1) {
      risk = 'moderate';
      score = 1;
    }

    return {
      offset_hours: h,
      forecast_timestamp: time,
      wind_speed_mph: wind,
      rain_in_per_hr: rain,
      snow_in_per_hr: snow,
      condition_risks: {
        wind: wind >= 45 ? 'severe' : wind >= 35 ? 'high' : wind >= 25 ? 'moderate' : 'low',
        rain: rain >= 0.25 ? 'high' : rain >= 0.1 ? 'moderate' : 'low',
        snow: snow >= 0.5 ? 'moderate' : 'low',
      },
      weather_risk: risk,
      load_adjusted_risk: risk,
      numeric_risk_score: score,
      availability: 'available',
    };
  });
};

export const MOCK_FORECAST_TIMELINE_DATA: RouteForecastTimelineResponse = {
  departure_time: '2026-10-23T14:00:00Z',
  load_weight_lb: 35000.0,
  forecast_fetched_at: '2026-10-23T13:45:00Z',
  forecast_age_seconds: 900,
  hour_offsets: Array.from({ length: 49 }, (_, i) => i),
  routes: [
    {
      route_id: 'route_primary',
      checkpoints: [
        {
          checkpoint_id: 'cp_0',
          lat: 39.7392,
          lon: -104.9903,
          cumulative_distance_miles: 0.0,
          timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 12.0),
        },
        {
          checkpoint_id: 'cp_1',
          lat: 41.1399,
          lon: -104.8202,
          cumulative_distance_miles: 100.0,
          timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 22.0, 0.02),
        },
        {
          checkpoint_id: 'cp_2',
          lat: 40.7608,
          lon: -111.891,
          cumulative_distance_miles: 504.2,
          timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 10.0),
        },
      ],
    },
    {
      route_id: 'route_alt_1',
      checkpoints: [
        {
          checkpoint_id: 'cp_0',
          lat: 39.7392,
          lon: -104.9903,
          cumulative_distance_miles: 0.0,
          timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 12.0),
        },
        {
          checkpoint_id: 'cp_alt_1',
          lat: 40.05,
          lon: -108.2,
          cumulative_distance_miles: 220.0,
          timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 46.0),
        },
        {
          checkpoint_id: 'cp_2',
          lat: 40.7608,
          lon: -111.891,
          cumulative_distance_miles: 548.0,
          timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 10.0),
        },
      ],
    },
  ],
  corridor_grid: {
    total_points: 6,
    is_capped: false,
    max_points_cap: 120,
    sample_interval_miles: 25.0,
    corridor_half_width_miles: 15.0,
    samples: [
      {
        point_id: 'grid_0',
        lat: 39.8,
        lon: -105.1,
        offset_miles: 0.0,
        timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 14.0),
      },
      {
        point_id: 'grid_1',
        lat: 40.0,
        lon: -106.2,
        offset_miles: 15.0,
        timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 28.0),
      },
      {
        point_id: 'grid_2',
        lat: 40.3,
        lon: -107.5,
        offset_miles: -15.0,
        timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 38.0),
      },
      {
        point_id: 'grid_3',
        lat: 40.6,
        lon: -108.8,
        offset_miles: 0.0,
        timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 46.0),
      },
      {
        point_id: 'grid_4',
        lat: 40.7,
        lon: -110.2,
        offset_miles: 15.0,
        timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 18.0),
      },
      {
        point_id: 'grid_5',
        lat: 40.76,
        lon: -111.89,
        offset_miles: 0.0,
        timeline: generateMockHourlyTimeline('2026-10-23T14:00:00Z', 12.0),
      },
    ],
  },
  warnings: [],
};

