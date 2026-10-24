import React, { useMemo, useState, useRef, useEffect } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { MapContainer, TileLayer } from 'react-leaflet';
import { Route, RouteForecastTimelineResponse, HourlyTimelineEntry } from '../../types/api';
import { OPENSTREETMAP_ATTRIBUTION, OPENSTREETMAP_TILE_URL } from './mapConstants';
import { MapBoundsUpdater } from './MapBoundsUpdater';
import { RoutePolyline } from './RoutePolyline';
import { CheckpointMarker } from './CheckpointMarker';
import { CorridorHeatmapLayer } from './CorridorHeatmapLayer';
import { ForecastTimelineSlider } from './ForecastTimelineSlider';
import { MapLegend } from './MapLegend';

export interface RouteMapProps {
  routes: Route[];
  selectedRouteId?: string;
  selectedCheckpointId?: string;
  timeline?: RouteForecastTimelineResponse | null;
  departureTime?: string;
  isLoadingTimeline?: boolean;
  onSelectRoute?: (routeId: string) => void;
  onSelectCheckpoint?: (checkpointId: string) => void;
}

const DEFAULT_CENTER: [number, number] = [39.8283, -98.5795];

export const RouteMap: React.FC<RouteMapProps> = ({
  routes,
  selectedRouteId,
  selectedCheckpointId,
  timeline,
  departureTime,
  isLoadingTimeline = false,
  onSelectRoute,
  onSelectCheckpoint,
}) => {
  const [sliderHour, setSliderHour] = useState<number>(0);
  const [deferredHour, setDeferredHour] = useState<number>(0);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(0.6);
  const rafId = useRef<number | null>(null);

  // Throttled map updates so dragging the slider stays smooth at 60fps
  const handleHourChange = (newHour: number) => {
    setSliderHour(newHour);
    if (rafId.current) {
      cancelAnimationFrame(rafId.current);
    }
    rafId.current = requestAnimationFrame(() => {
      setDeferredHour(newHour);
    });
  };

  useEffect(() => {
    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, []);

  const activeRoute = useMemo(
    () => routes.find((r) => r.route_id === selectedRouteId) || routes[0],
    [routes, selectedRouteId]
  );

  const activeCheckpoints = useMemo(() => activeRoute?.checkpoints || [], [activeRoute]);

  const activeRouteTimeline = useMemo(() => {
    if (!timeline?.routes) return null;
    return timeline.routes.find((r) => r.route_id === (selectedRouteId || routes[0]?.route_id));
  }, [timeline, selectedRouteId, routes]);

  const checkpointTimelineMap = useMemo(() => {
    if (!activeRouteTimeline) return new Map<string, HourlyTimelineEntry>();
    const map = new Map<string, HourlyTimelineEntry>();
    for (const cp of activeRouteTimeline.checkpoints) {
      const entry = cp.timeline.find((t) => t.offset_hours === deferredHour);
      if (entry) {
        map.set(cp.checkpoint_id, entry);
      }
    }
    return map;
  }, [activeRouteTimeline, deferredHour]);

  if (!routes || routes.length === 0) {
    return (
      <Paper elevation={0} sx={{ p: 4, textAlign: 'center', border: 1, borderColor: 'divider' }}>
        <Typography variant="body1" color="text.secondary">
          No route corridors to display on map. Plan a trip above to visualize corridors.
        </Typography>
      </Paper>
    );
  }

  const effectiveDeparture =
    departureTime || timeline?.departure_time || activeCheckpoints[0]?.eta || new Date().toISOString();

  return (
    <Box sx={{ position: 'relative', width: '100%', mb: 3 }}>
      <ForecastTimelineSlider
        selectedHour={sliderHour}
        onHourChange={handleHourChange}
        departureTime={effectiveDeparture}
        forecastFetchedAt={timeline?.forecast_fetched_at}
        forecastAgeSeconds={timeline?.forecast_age_seconds}
        showHeatmap={showHeatmap}
        onToggleHeatmap={setShowHeatmap}
        heatmapOpacity={heatmapOpacity}
        onChangeOpacity={setHeatmapOpacity}
        isLoadingTimeline={isLoadingTimeline}
      />

      <Paper
        elevation={0}
        sx={{
          height: { xs: 360, sm: 440, md: 500, lg: 560, xl: 620 },
          width: '100%',
          borderRadius: 3,
          overflow: 'hidden',
          border: '1px solid #e2e8f0',
          boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.08)',
        }}
      >
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={5}
          preferCanvas={true}
          scrollWheelZoom={false}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer url={OPENSTREETMAP_TILE_URL} attribution={OPENSTREETMAP_ATTRIBUTION} />
          <MapBoundsUpdater routes={routes} />

          <CorridorHeatmapLayer
            samples={timeline?.corridor_grid?.samples || []}
            selectedHour={deferredHour}
            opacity={heatmapOpacity}
            visible={showHeatmap}
            corridorHalfWidthMiles={timeline?.corridor_grid?.corridor_half_width_miles || 15.0}
          />

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
              hourlyEntry={checkpointTimelineMap.get(cp.checkpoint_id)}
              onSelectCheckpoint={onSelectCheckpoint}
            />
          ))}
        </MapContainer>
      </Paper>

      <Box sx={{ mt: 1.5 }}>
        <MapLegend showHeatmap={showHeatmap} />
      </Box>
    </Box>
  );
};

export default RouteMap;
