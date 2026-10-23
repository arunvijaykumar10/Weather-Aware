import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RouteCard } from './RouteCard';
import { MOCK_ROUTE_ANALYSIS_DATA } from '../mock/mockRouteAnalysis';

describe('RouteCard component', () => {
  const primaryRoute = MOCK_ROUTE_ANALYSIS_DATA.routes[0];
  const alternativeRoute = MOCK_ROUTE_ANALYSIS_DATA.routes[1];

  it('renders primary route metrics and recommended badge', () => {
    render(<RouteCard route={primaryRoute} isRecommended={true} />);

    expect(screen.getByRole('heading', { name: /primary corridor/i })).toBeInTheDocument();
    expect(screen.getByText('504.2')).toBeInTheDocument();
    expect(screen.getByText(/recommended/i)).toBeInTheDocument();
    expect(screen.getByText(/low/i)).toBeInTheDocument();
    expect(screen.getByText(/100%/i)).toBeInTheDocument();
    expect(
      screen.getByText(/complies with commercial driver safety thresholds/i)
    ).toBeInTheDocument();
  });

  it('renders alternative route metrics without recommendation badge', () => {
    render(<RouteCard route={alternativeRoute} isRecommended={false} />);

    expect(screen.getByRole('heading', { name: /us-40 w southern bypass/i })).toBeInTheDocument();
    expect(screen.getByText('548.0')).toBeInTheDocument();
    expect(screen.queryByText(/recommended/i)).not.toBeInTheDocument();
    expect(screen.getByText('50.0 mi')).toBeInTheDocument();
  });

  it('displays No-Travel hazard badge and warning alert when present', () => {
    const hazardousRoute = {
      ...alternativeRoute,
      metrics: {
        ...alternativeRoute.metrics,
        has_no_travel_segment: true,
        no_travel_miles: 24.5,
      },
      eligibility: {
        is_eligible: false,
        ineligibility_reasons: ['Contains No-Travel conditions.'],
      },
    };

    render(<RouteCard route={hazardousRoute} isRecommended={false} />);

    expect(screen.getByText(/no-travel hazard/i)).toBeInTheDocument();
    expect(
      screen.getByText(/contains 24.5 mi of hazardous no-travel weather/i)
    ).toBeInTheDocument();
  });
});
