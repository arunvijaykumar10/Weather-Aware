import React, { useState } from 'react';
import { ThemeProvider, CssBaseline, Box, Container, Stack, Alert } from '@mui/material';
import 'leaflet/dist/leaflet.css';

import { appTheme } from './theme/theme';
import { useBackendHealth } from './hooks/useBackendHealth';
import { HeaderBar } from './components/HeaderBar';
import { TripPlannerForm } from './components/TripPlannerForm';
import { RouteComparisonSection } from './components/RouteComparisonSection';
import { StatusAlerts } from './components/StatusAlerts';
import { SystemOverviewCards } from './components/SystemOverviewCards';
import { FooterBar } from './components/FooterBar';
import { analyzeRoutes, ApiError } from './api/routeClient';
import { RouteAnalyzeRequest, RouteAnalyzeResponse } from './types/api';

export const App: React.FC = () => {
  const {
    healthStatus,
    isLoading: isCheckingHealth,
    errorMessage,
    setErrorMessage,
  } = useBackendHealth();

  const [analysisResult, setAnalysisResult] = useState<RouteAnalyzeResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | undefined>(undefined);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);

  const handleAnalyze = async (requestData: RouteAnalyzeRequest) => {
    setIsAnalyzing(true);
    setApiError(null);
    try {
      const response = await analyzeRoutes(requestData);
      setAnalysisResult(response);
      setSelectedRouteId(
        response.recommendation.recommended_route_id || response.routes[0]?.route_id
      );
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
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <Box
        sx={{
          flexGrow: 1,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <HeaderBar isConnected={Boolean(healthStatus)} isLoading={isCheckingHealth} />

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
          <Stack spacing={3}>
            {errorMessage && (
              <Alert severity="warning" onClose={() => setErrorMessage(null)}>
                Backend Connection Note: {errorMessage}. (Ensure Django is running on port 8000)
              </Alert>
            )}

            <TripPlannerForm isLoading={isAnalyzing} onAnalyze={handleAnalyze} />

            <StatusAlerts apiError={apiError} onClearError={() => setApiError(null)} />

            {analysisResult && (
              <RouteComparisonSection
                analysis={analysisResult}
                selectedRouteId={selectedRouteId}
                onSelectRoute={setSelectedRouteId}
              />
            )}

            {!analysisResult && <SystemOverviewCards />}
          </Stack>
        </Container>

        <FooterBar />
      </Box>
    </ThemeProvider>
  );
};

export default App;
