import React from 'react';
import { ThemeProvider, CssBaseline, Box, Container, Stack, Alert } from '@mui/material';
import 'leaflet/dist/leaflet.css';

import { appTheme } from './theme/theme';
import { useBackendHealth } from './hooks/useBackendHealth';
import { HeaderBar } from './components/HeaderBar';
import { SystemOverviewCards } from './components/SystemOverviewCards';
import { HealthMonitorCard } from './components/HealthMonitorCard';
import { FooterBar } from './components/FooterBar';

export const App: React.FC = () => {
  const { healthStatus, isLoading, errorMessage, refreshHealth, setErrorMessage } =
    useBackendHealth();

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
        <HeaderBar isConnected={Boolean(healthStatus)} isLoading={isLoading} />

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
          <Stack spacing={3}>
            {errorMessage && (
              <Alert severity="warning" onClose={() => setErrorMessage(null)}>
                Backend Connection Note: {errorMessage}. (Ensure Django is running on port 8000)
              </Alert>
            )}
            <SystemOverviewCards />
            <HealthMonitorCard
              healthStatus={healthStatus}
              isLoading={isLoading}
              onRefreshHealth={refreshHealth}
            />
          </Stack>
        </Container>

        <FooterBar />
      </Box>
    </ThemeProvider>
  );
};

export default App;
