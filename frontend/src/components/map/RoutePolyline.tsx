import React from 'react';
import { Polyline, Tooltip } from 'react-leaflet';
import { Route } from '../../types/api';
import { DEFAULT_ROUTE_STYLE, ROUTE_STYLE_MAP } from './mapConstants';

interface RoutePolylineProps {
  route: Route;
  isSelected: boolean;
  hasSelection: boolean;
  onSelectRoute?: (routeId: string) => void;
}

export const RoutePolyline: React.FC<RoutePolylineProps> = ({
  route,
  isSelected,
  hasSelection,
  onSelectRoute,
}) => {
  if (!route.geometry || route.geometry.length < 2) return null;

  const styleConfig = ROUTE_STYLE_MAP[route.route_id] || DEFAULT_ROUTE_STYLE;
  const weight = isSelected ? 6 : 4;
  const opacity = isSelected ? 0.95 : hasSelection ? 0.35 : 0.75;

  return (
    <Polyline
      positions={route.geometry}
      pathOptions={{
        color: styleConfig.color,
        weight,
        opacity,
        dashArray: styleConfig.dashArray,
      }}
      eventHandlers={{
        click: () => onSelectRoute?.(route.route_id),
      }}
    >
      <Tooltip sticky>
        <strong>{styleConfig.name}</strong>: {route.distance_miles.toFixed(1)} mi,{' '}
        {Math.round(route.duration_minutes)} min (Click to select)
      </Tooltip>
    </Polyline>
  );
};
