import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RouteMap } from './RouteMap';
import { MOCK_ROUTE_ANALYSIS_DATA, MOCK_FORECAST_TIMELINE_DATA } from '../../mock/mockRouteAnalysis';

describe('RouteMap component', () => {
  const mockRoutes = MOCK_ROUTE_ANALYSIS_DATA.routes;

  it('renders map container, polylines, and multi-symbol legend', () => {
    render(
      <RouteMap routes={mockRoutes} selectedRouteId="route_primary" onSelectRoute={vi.fn()} />
    );

    expect(screen.getByTestId('leaflet-map-container')).toBeInTheDocument();
    expect(screen.getByTestId('leaflet-tile-layer')).toBeInTheDocument();

    // Check legend items (symbols and line patterns)
    expect(screen.getByText(/primary corridor \(solid\)/i)).toBeInTheDocument();
    expect(screen.getByText(/alternative 1 \(dashed\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/low risk/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/no travel hazard/i).length).toBeGreaterThan(0);
  });

  it('renders polylines for every returned route', () => {
    render(
      <RouteMap routes={mockRoutes} selectedRouteId="route_primary" onSelectRoute={vi.fn()} />
    );

    const polylines = screen.getAllByTestId('leaflet-polyline');
    expect(polylines).toHaveLength(mockRoutes.length);
  });

  it('renders checkpoint markers for active selected route', () => {
    render(
      <RouteMap routes={mockRoutes} selectedRouteId="route_primary" onSelectRoute={vi.fn()} />
    );

    const primaryCheckpoints = mockRoutes[0].checkpoints;
    const markers = screen.getAllByTestId('leaflet-circle-marker');
    expect(markers).toHaveLength(primaryCheckpoints.length);
  });

  it('renders forecast timeline slider, quick buttons, and explanatory notice', () => {
    render(
      <RouteMap
        routes={mockRoutes}
        selectedRouteId="route_primary"
        timeline={MOCK_FORECAST_TIMELINE_DATA}
        departureTime="2026-10-23T14:00:00Z"
      />
    );

    expect(screen.getByText(/corridor forecast timeline \(0h to 48h\)/i)).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: /corridor forecast hour offset slider/i })).toBeInTheDocument();

    // Explanatory note confirming recommendation uses ETA-matched weather
    expect(
      screen.getByText(/route rankings and safety recommendations remain fixed based on predicted arrival times/i)
    ).toBeInTheDocument();

    // Quick jump buttons
    expect(screen.getByRole('button', { name: /\+0h/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /\+12h/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /\+24h/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /\+48h/i })).toBeInTheDocument();
  });

  it('renders corridor heatmap circles when heatmap toggle is enabled', () => {
    render(
      <RouteMap
        routes={mockRoutes}
        selectedRouteId="route_primary"
        timeline={MOCK_FORECAST_TIMELINE_DATA}
        departureTime="2026-10-23T14:00:00Z"
      />
    );

    const heatmapSwitch = screen.getByRole('checkbox', { name: /heatmap overlay/i });
    expect(heatmapSwitch).toBeChecked();

    const heatmapCircles = screen.getAllByTestId('leaflet-circle');
    expect(heatmapCircles.length).toBe(MOCK_FORECAST_TIMELINE_DATA.corridor_grid.samples.length);

    // Toggle heatmap off
    fireEvent.click(heatmapSwitch);
    expect(screen.queryAllByTestId('leaflet-circle')).toHaveLength(0);
  });

  it('shows empty state gracefully when no routes are supplied', () => {
    render(<RouteMap routes={[]} />);

    expect(screen.getByText(/no route corridors to display on map/i)).toBeInTheDocument();
  });
});
