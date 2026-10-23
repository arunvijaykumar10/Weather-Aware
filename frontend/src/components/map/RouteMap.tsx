import React, { useMemo } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { MapContainer, TileLayer } from 'react-leaflet';
import { Route } from '../../types/api';
import { OPENSTREETMAP_ATTRIBUTION, OPENSTREETMAP_TILE_URL } from './mapConstants';
import { MapBoundsUpdater } from './MapBoundsUpdater';
import { RoutePolyline } from './RoutePolyline';
import { CheckpointMarker } from './CheckpointMarker';
import { MapLegend } from './MapLegend';

interface RouteMapProps {
  routes: Route[];
  selectedRouteId?: string;
  selectedCheckpointId?: string;
  onSelectRoute?: (routeId: string) => void;
  onSelectCheckpoint?: (checkpointId: string) => void;
}

const DEFAULT_CENTER: [number, number] = [39.8283, -98.5795]; // Center of Continental USA

export const RouteMap: React.FC<RouteMapProps> = ({
  routes,
  selectedRouteId,
  selectedCheckpointId,
  onSelectRoute,
  onSelectCheckpoint,
}) => {
  const activeRoute = useMemo(
    () => routes.find((r) => r.route_id === selectedRouteId) || routes[0],
    [routes, selectedRouteId]
  );

  const activeCheckpoints = useMemo(() => activeRoute?.checkpoints || [], [activeRoute]);

  if (!routes || routes.length === 0) {
    return (
      <Paper elevation={0} sx={{ p: 4, textAlign: 'center', border: 1, borderColor: 'divider' }}>
        <Typography variant="body1" color="text.secondary">
          No route corridors to display on map. Plan a trip above to visualize corridors.
        </Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ position: 'relative', width: '100%', mb: 3 }}>
      <Paper
        elevation={0}
        sx={{
          height: 520,
          width: '100%',
          borderRadius: 2,
          overflow: 'hidden',
          border: 1,
          borderColor: 'divider',
        }}
      >
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={5}
          preferCanvas={true}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer url={OPENSTREETMAP_TILE_URL} attribution={OPENSTREETMAP_ATTRIBUTION} />
          <MapBoundsUpdater routes={routes} />

          {routes.map((route) => (
            <RoutePolyline
              key={route.route_id}
              route={route}
              isSelected={route.route_id === selectedRouteId}
              hasSelection={Boolean(selectedRouteId)}
              onSelectRoute={onSelectRoute}
            />
          ))}

          {activeCheckpoints.map((cp) => (
            <CheckpointMarker
              key={cp.checkpoint_id}
              checkpoint={cp}
              isSelected={cp.checkpoint_id === selectedCheckpointId}
              onSelectCheckpoint={onSelectCheckpoint}
            />
          ))}
        </MapContainer>
      </Paper>

      <Box sx={{ mt: 1.5 }}>
        <MapLegend />
      </Box>
    </Box>
  );
};
