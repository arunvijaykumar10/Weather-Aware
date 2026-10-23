import React, { useState } from 'react';
import { Stack, Alert } from '@mui/material';
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
  const [selectedRouteId, setSelectedRouteId] = useState<string | undefined>(undefined);
  const [selectedCheckpointId, setSelectedCheckpointId] = useState<string | undefined>(undefined);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);

  const handleAnalyze = async (requestData: RouteAnalyzeRequest) => {
    setIsAnalyzing(true);
    setApiError(null);
    setLastDepartureTime(requestData.departure_time);
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
      <Stack spacing={3}>
        {errorMessage && (
          <Alert severity="warning" onClose={() => setErrorMessage(null)}>
            Backend Connection Note: {errorMessage}. (Ensure Django is running on port 8000)
          </Alert>
        )}

        <TripPlannerForm isLoading={isAnalyzing} onAnalyze={handleAnalyze} />

        <StatusAlerts apiError={apiError} onClearError={() => setApiError(null)} />

        {analysisResult && (
          <>
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
            <RouteComparisonSection
              analysis={analysisResult}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />
          </>
        )}

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
