import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RouteMap } from './RouteMap';
import { MOCK_ROUTE_ANALYSIS_DATA } from '../../mock/mockRouteAnalysis';

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

  it('shows empty state gracefully when no routes are supplied', () => {
    render(<RouteMap routes={[]} />);

    expect(screen.getByText(/no route corridors to display on map/i)).toBeInTheDocument();
  });
});
