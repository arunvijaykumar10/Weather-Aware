import React, { useState } from 'react';
import {
  Stack,
  Alert,
  Box,
  Grid,
  Button,
  Collapse,
  Typography,
  Paper,
} from '@mui/material';
import EditLocationAltIcon from '@mui/icons-material/EditLocationAlt';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import 'leaflet/dist/leaflet.css';

import { AppProviders } from './providers';
import { MainLayout } from '../layouts/MainLayout';
import { useBackendHealth } from '../hooks/useBackendHealth';
import { TripPlannerForm } from '../components/TripPlannerForm';
import { RouteComparisonSection } from '../components/RouteComparisonSection';
import { RouteMap } from '../components/map/RouteMap';
import { StatusAlerts } from '../components/StatusAlerts';
import { SystemOverviewCards } from '../components/SystemOverviewCards';
import { analyzeRoutes, fetchForecastTimeline, ApiError } from '../api/routeClient';
import {
  RouteAnalyzeRequest,
  RouteAnalyzeResponse,
  RouteForecastTimelineResponse,
} from '../types/api';

export const AppContent: React.FC = () => {
  const {
    healthStatus,
    isLoading: isCheckingHealth,
    errorMessage,
    setErrorMessage,
  } = useBackendHealth();

  const [analysisResult, setAnalysisResult] = useState<RouteAnalyzeResponse | null>(null);
  const [timelineResult, setTimelineResult] = useState<RouteForecastTimelineResponse | null>(null);
  const [isTimelineLoading, setIsTimelineLoading] = useState<boolean>(false);
  const [lastDepartureTime, setLastDepartureTime] = useState<string | undefined>(undefined);
  const [lastRequest, setLastRequest] = useState<RouteAnalyzeRequest | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | undefined>(undefined);
  const [selectedCheckpointId, setSelectedCheckpointId] = useState<string | undefined>(undefined);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [isFormExpanded, setIsFormExpanded] = useState<boolean>(true);

  const handleAnalyze = async (requestData: RouteAnalyzeRequest) => {
    setIsAnalyzing(true);
    setApiError(null);
    setLastDepartureTime(requestData.departure_time);
    setLastRequest(requestData);
    try {
      const response = await analyzeRoutes(requestData);
      setAnalysisResult(response);
      setSelectedRouteId(
        response.recommendation.recommended_route_id || response.routes[0]?.route_id
      );

      // Asynchronously fetch full 0-48h forecast timeline & corridor heatmap grid
      setIsTimelineLoading(true);
      fetchForecastTimeline(requestData)
        .then((timeline) => setTimelineResult(timeline))
        .catch((timelineErr) => {
          console.warn('Forecast timeline fetch notice:', timelineErr);
        })
        .finally(() => setIsTimelineLoading(false));
    } catch (caughtError: unknown) {
      if (caughtError instanceof ApiError) {
        setApiError(caughtError);
      } else {
        setApiError(
          new ApiError(caughtError instanceof Error ? caughtError.message : 'Unexpected error', 0)
        );
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <MainLayout isConnected={Boolean(healthStatus)} isCheckingHealth={isCheckingHealth}>
      <Stack spacing={2.5}>
        {errorMessage && (
          <Alert severity="warning" onClose={() => setErrorMessage(null)} sx={{ borderRadius: 2 }}>
            Backend Connection Note: {errorMessage}. (Ensure Django is running on port 8000)
          </Alert>
        )}

        {/* Compact Trip Header Bar when results exist */}
        {analysisResult && lastRequest && (
          <Paper
            elevation={0}
            sx={{
              p: 2,
              borderRadius: 3,
              border: '1px solid #e2e8f0',
              bgcolor: '#ffffff',
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', sm: 'center' },
              gap: 1.5,
              boxShadow: '0 2px 10px rgba(15, 23, 42, 0.04)',
            }}
          >
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 38,
                  height: 38,
                  borderRadius: 2,
                  bgcolor: 'primary.main',
                  color: '#ffffff',
                }}
              >
                <LocalShippingIcon sx={{ fontSize: 20 }} />
              </Box>
              <Box>
                <Typography variant="subtitle1" fontWeight={800} color="text.primary">
                  {lastRequest.origin} ➔ {lastRequest.destination}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                  <Typography variant="caption" color="text.secondary">
                    Load: <strong>{lastRequest.load_weight_lb.toLocaleString()} lbs</strong>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">•</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Checkpoints: <strong>Every {lastRequest.checkpoint_interval_miles} mi</strong>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">•</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Status: <strong style={{ color: '#10b981' }}>Routes Computed</strong>
                  </Typography>
                </Stack>
              </Box>
            </Stack>

            <Button
              variant="outlined"
              size="small"
              startIcon={<EditLocationAltIcon sx={{ fontSize: 16 }} />}
              endIcon={isFormExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              onClick={() => setIsFormExpanded(!isFormExpanded)}
              sx={{
                fontWeight: 700,
                fontSize: '0.8rem',
                borderRadius: 2,
                borderColor: '#cbd5e1',
                color: 'text.primary',
              }}
            >
              {isFormExpanded ? 'Hide Trip Planner' : 'Edit Trip Planner'}
            </Button>
          </Paper>
        )}

        {/* Form Container (collapsible when analysisResult is present) */}
        <Collapse in={!analysisResult || isFormExpanded} timeout="auto">
          <TripPlannerForm isLoading={isAnalyzing} onAnalyze={handleAnalyze} />
        </Collapse>

        <StatusAlerts apiError={apiError} onClearError={() => setApiError(null)} />

        {/* Cockpit Two-Column Layout once routes are calculated */}
        {analysisResult && (
          <Grid container spacing={3} alignItems="flex-start">
            {/* Left Column: Recommended Banner & 3 Interactive Route Cards */}
            <Grid item xs={12} lg={5.5}>
              <RouteComparisonSection
                analysis={analysisResult}
                selectedRouteId={selectedRouteId}
                onSelectRoute={setSelectedRouteId}
              />
            </Grid>

            {/* Right Column: Sticky Interactive Map & 0-48h Timeline Scrubber */}
            <Grid
              item
              xs={12}
              lg={6.5}
              sx={{
                position: { lg: 'sticky' },
                top: { lg: 84 },
                zIndex: 1,
              }}
            >
              <RouteMap
                routes={analysisResult.routes}
                selectedRouteId={selectedRouteId}
                selectedCheckpointId={selectedCheckpointId}
                timeline={timelineResult}
                departureTime={lastDepartureTime}
                isLoadingTimeline={isTimelineLoading}
                onSelectRoute={setSelectedRouteId}
                onSelectCheckpoint={setSelectedCheckpointId}
              />
            </Grid>
          </Grid>
        )}

        {/* Empty state system overview cards */}
        {!analysisResult && <SystemOverviewCards />}
      </Stack>
    </MainLayout>
  );
};

export const App: React.FC = () => {
  return (
    <AppProviders>
      <AppContent />
    </AppProviders>
  );
};

export default App;
