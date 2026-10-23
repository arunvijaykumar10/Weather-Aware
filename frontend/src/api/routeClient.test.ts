import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { analyzeRoutes, fetchForecastTimeline, ApiError } from './routeClient';
import { RouteAnalyzeRequest } from '../types/api';
import { MOCK_ROUTE_ANALYSIS_DATA, MOCK_FORECAST_TIMELINE_DATA } from '../mock/mockRouteAnalysis';

describe('routeClient', () => {
  const sampleRequest: RouteAnalyzeRequest = {
    origin: 'Denver, CO',
    destination: 'Salt Lake City, UT',
    departure_time: '2026-10-23T14:00:00Z',
    load_weight_lb: 42000,
    checkpoint_interval_miles: 25,
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('successfully returns route analysis data on 200 response', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_ROUTE_ANALYSIS_DATA,
    });
    vi.stubGlobal('fetch', mockFetch);

    const result = await analyzeRoutes(sampleRequest);
    expect(result.routes_returned).toBe(2);
    expect(result.recommendation.recommended_route_id).toBe('route_primary');
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('maps 400 validation error envelope to ApiError with details', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        error: {
          code: 'validation_error',
          message: 'Invalid request payload or parameters.',
          details: {
            load_weight_lb: ['Ensure this value is greater than 0.'],
          },
        },
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(analyzeRoutes(sampleRequest)).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      code: 'validation_error',
      details: {
        load_weight_lb: ['Ensure this value is greater than 0.'],
      },
    });
  });

  it('maps 429 rate limit error to ApiError with wait_seconds', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({
        error: {
          code: 'request_throttled',
          message: 'Request was throttled. Expected available in 14 seconds.',
          details: {
            wait_seconds: 14,
          },
        },
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    try {
      await analyzeRoutes(sampleRequest);
      expect.unreachable('Should have thrown an ApiError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(429);
      expect(apiErr.code).toBe('request_throttled');
      expect(apiErr.waitSeconds).toBe(14);
    }
  });

  it('maps network disconnect to network_error ApiError', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));
    vi.stubGlobal('fetch', mockFetch);

    await expect(analyzeRoutes(sampleRequest)).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      code: 'network_error',
    });
  });

  it('successfully fetches forecast timeline data', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_FORECAST_TIMELINE_DATA,
    });
    vi.stubGlobal('fetch', mockFetch);

    const timeline = await fetchForecastTimeline(sampleRequest);
    expect(timeline.hour_offsets).toHaveLength(49);
    expect(timeline.corridor_grid.samples).toHaveLength(6);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/routes/forecast-timeline/'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});

