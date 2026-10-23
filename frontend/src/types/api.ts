/**
 * Spotter Weather-Aware Truck Routing - Typed API Contracts
 * Single source of truth aligned directly with Django REST Framework serializers.
 */

export type RiskLevel = 'low' | 'moderate' | 'high' | 'severe' | 'no_travel' | 'unknown';

export type WeatherAvailability = 'available' | 'unavailable' | 'missing';

export type CheckpointInterval = 10 | 25 | 50;

/**
 * Request payload for POST /api/routes/analyze/
 */
export interface RouteAnalyzeRequest {
  origin: string;
  destination: string;
  /** ISO 8601 timestamp with explicit timezone offset (e.g. 2026-10-23T14:00:00Z) */
  departure_time: string;
  /** Positive load weight in pounds */
  load_weight_lb: number;
  /** Sampling corridor interval in miles */
  checkpoint_interval_miles: CheckpointInterval;
}

/**
 * Weather observation or forecast values at a coordinate checkpoint.
 */
export interface WeatherValues {
  wind_speed_mph: number | null;
  wind_gusts_mph?: number | null;
  wind_speed_availability: WeatherAvailability;
  rain_in_per_hr: number | null;
  rain_availability: WeatherAvailability;
  snow_in_per_hr: number | null;
  snow_availability: WeatherAvailability;
}

/**
 * Independent risk assessments for individual meteorological dimensions.
 */
export interface ConditionRisks {
  wind_risk: RiskLevel;
  rain_risk: RiskLevel;
  snow_risk: RiskLevel;
}

/**
 * Sampled corridor checkpoint along a truck route.
 */
export interface Checkpoint {
  checkpoint_id: string;
  lat: number;
  lon: number;
  cumulative_distance_miles: number;
  eta: string;
  forecast_timestamp: string | null;
  weather: WeatherValues;
  condition_risks: ConditionRisks;
  weather_risk: RiskLevel;
  load_adjusted_risk: RiskLevel;
  load_rule_applied: string | null;
}

/**
 * Cumulative mileage exposure per risk category.
 */
export interface MilesPerRiskCategory {
  low: number;
  moderate: number;
  high: number;
  severe: number;
  no_travel: number;
  unknown: number;
}

/**
 * Aggregate safety and weather exposure metrics for a route alternative.
 */
export interface RouteMetrics {
  miles_per_risk_category: MilesPerRiskCategory;
  severe_miles: number;
  high_miles: number;
  no_travel_miles: number;
  unknown_miles: number;
  average_risk: RiskLevel;
  has_no_travel_segment: boolean;
  forecast_coverage_pct: number;
}

/**
 * Route compliance with driver safety rules.
 */
export interface RouteEligibility {
  is_eligible: boolean;
  ineligibility_reasons: string[];
}

/**
 * Complete driving corridor alternative.
 */
export interface Route {
  route_id: string;
  provider_summary: string;
  /** Array of [lat, lon] tuples representing coordinate geometry */
  geometry: [number, number][];
  distance_miles: number;
  duration_minutes: number;
  checkpoints: Checkpoint[];
  metrics: RouteMetrics;
  eligibility: RouteEligibility;
}

/**
 * Backend recommendation decision and ranking rationale.
 */
export interface Recommendation {
  recommended_route_id: string | null;
  route_eligibility: Record<string, boolean>;
  ranking_reasons: string[];
  no_route_meets_safety_thresholds: boolean;
}

/**
 * Hourly forecast point for corridor timeline visualization.
 */
export interface HourlyRiskForecast {
  hour_offset: number;
  forecast_time: string;
  weather: WeatherValues;
  risk: RiskLevel;
}

/**
 * 48-hour forward timeline per checkpoint (placeholder for Task 10A).
 */
export interface CheckpointTimeline {
  checkpoint_id: string;
  lat: number;
  lon: number;
  hourly_forecasts: HourlyRiskForecast[];
}

/**
 * Upstream provider error or warning detail.
 */
export interface ProviderError {
  provider: string;
  code: string | null;
  message: string;
}

/**
 * Root response from POST /api/routes/analyze/
 */
export interface RouteAnalyzeResponse {
  routes_requested: number;
  routes_returned: number;
  fewer_routes_reason?: string | null;
  routes: Route[];
  recommendation: Recommendation;
  forecast_timeline: CheckpointTimeline[];
  warnings: string[];
  provider_errors: ProviderError[];
}

/**
 * Hourly risk forecast entry for a single integer hour offset (0 through 48).
 */
export interface HourlyTimelineEntry {
  offset_hours: number;
  forecast_timestamp: string;
  wind_speed_mph: number | null;
  rain_in_per_hr: number | null;
  snow_in_per_hr: number | null;
  condition_risks: {
    wind: RiskLevel;
    rain: RiskLevel;
    snow: RiskLevel;
  };
  weather_risk: RiskLevel;
  load_adjusted_risk: RiskLevel;
  numeric_risk_score: number | null;
  availability: 'available' | 'unavailable' | 'beyond_forecast';
}

/**
 * Checkpoint 0-48h forecast timeline.
 */
export interface RouteCheckpointTimeline {
  checkpoint_id: string;
  lat: number;
  lon: number;
  cumulative_distance_miles: number;
  timeline: HourlyTimelineEntry[];
}

/**
 * Route timeline containing checkpoints.
 */
export interface RouteTimeline {
  route_id: string;
  checkpoints: RouteCheckpointTimeline[];
}

/**
 * Heatmap grid sample point along or offset perpendicular to the corridor.
 */
export interface HeatmapSamplePoint {
  point_id: string;
  lat: number;
  lon: number;
  offset_miles: number;
  timeline: HourlyTimelineEntry[];
}

/**
 * Heatmap corridor grid containing all sample points.
 */
export interface CorridorGrid {
  total_points: number;
  is_capped: boolean;
  max_points_cap: number;
  sample_interval_miles: number;
  corridor_half_width_miles: number;
  samples: HeatmapSamplePoint[];
}

/**
 * Response from POST /api/routes/forecast-timeline/
 */
export interface RouteForecastTimelineResponse {
  departure_time: string;
  load_weight_lb: number;
  forecast_fetched_at: string;
  forecast_age_seconds: number;
  hour_offsets: number[];
  routes: RouteTimeline[];
  corridor_grid: CorridorGrid;
  warnings: string[];
  payload_size_bytes?: number;
}

/**
 * Standardized error envelope returned on 400/429/500 API responses.
 */
export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, string[] | string | number | undefined>;
  };
}
