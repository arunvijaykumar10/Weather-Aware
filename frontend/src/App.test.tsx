import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App from './App';
import { MOCK_ROUTE_ANALYSIS_DATA, MOCK_FORECAST_TIMELINE_DATA } from './mock/mockRouteAnalysis';

describe('App component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the application header, dispatch configuration, and fleet capabilities', async () => {
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/health/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            status: 'healthy',
            service: 'weather-aware-routing-backend',
          }),
        });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<App />);

    expect(
      screen.getByRole('heading', {
        name: /weather-aware truck route intelligence/i,
      })
    ).toBeInTheDocument();

    expect(
      screen.getByRole('heading', {
        name: /dispatch & route configuration/i,
      })
    ).toBeInTheDocument();

    expect(
      screen.getByRole('heading', {
        name: /fleet safety intelligence & capabilities/i,
      })
    ).toBeInTheDocument();

    expect(screen.getByText(/live radar active/i)).toBeInTheDocument();
  });

  it('handles service connection failure gracefully with service notice', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));
    vi.stubGlobal('fetch', mockFetch);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/service notification/i)).toBeInTheDocument();
    });
  });

  it('submits trip form and renders route comparison cards with recommendation', async () => {
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/health/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            status: 'healthy',
            service: 'weather-aware-routing-backend',
          }),
        });
      }
      if (url.includes('/api/routes/analyze/')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => MOCK_ROUTE_ANALYSIS_DATA,
        });
      }
      if (url.includes('/api/routes/forecast-timeline/')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => MOCK_FORECAST_TIMELINE_DATA,
        });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<App />);

    const presetChip = screen.getByText(/Denver, CO → Salt Lake City, UT/i);
    fireEvent.click(presetChip);

    const submitBtn = screen.getByRole('button', {
      name: /analyze driving corridors/i,
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: /driving corridor comparison/i })
      ).toBeInTheDocument();
    });

    expect(screen.getByText(/recommended corridor: primary corridor/i)).toBeInTheDocument();
    expect(
      screen.getByText(/optimal safety: zero severe or no-travel weather/i)
    ).toBeInTheDocument();
    expect(screen.getByText('504.2')).toBeInTheDocument();
    expect(screen.getByText('548.0')).toBeInTheDocument();
  });
});
