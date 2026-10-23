import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  ThemeProvider,
  createTheme,
  CssBaseline,
} from '@mui/material';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import AltRouteIcon from '@mui/icons-material/AltRoute';
import RefreshIcon from '@mui/icons-material/Refresh';
import 'leaflet/dist/leaflet.css';

interface HealthResponse {
  status: string;
  service: string;
}

const theme = createTheme({
  palette: {
    primary: {
      main: '#1e3a8a', // Deep Blue
    },
    secondary: {
      main: '#f59e0b', // Amber
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/health/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: HealthResponse = await response.json();
      setHealth(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" elevation={2}>
          <Toolbar>
            <LocalShippingIcon sx={{ mr: 2, fontSize: 32 }} />
            <Typography variant="h6" component="h1" sx={{ flexGrow: 1, fontWeight: 700 }}>
              Spotter Weather-Aware Truck Routing
            </Typography>
            <Chip
              label={
                loading
                  ? 'Checking Backend...'
                  : health
                  ? 'Backend Connected'
                  : 'Backend Disconnected'
              }
              color={health ? 'success' : 'error'}
              size="small"
              sx={{ color: '#fff', fontWeight: 600 }}
            />
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
          <Stack spacing={3}>
            {error && (
              <Alert severity="warning" onClose={() => setError(null)}>
                Backend Connection Note: {error}. (Ensure Django is running on port 8000)
              </Alert>
            )}

            <Paper elevation={0} sx={{ p: 3, bgcolor: '#ffffff', borderRadius: 2, border: '1px solid #e2e8f0' }}>
              <Typography variant="h5" component="h2" gutterBottom fontWeight={600} color="primary">
                System Overview & Architecture
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Spotter calculates driving routes for heavy freight, continuously monitoring weather hazards
                along active corridors to rank routes by safety and efficiency.
              </Typography>

              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                        <AltRouteIcon color="primary" />
                        <Typography variant="subtitle1" fontWeight={600}>
                          Up to 3 Routes
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        Generates alternative driving paths using routing engine APIs with geometry and maneuver segments.
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                        <CloudQueueIcon color="secondary" />
                        <Typography variant="subtitle1" fontWeight={600}>
                          Weather Risk Scoring
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        Backend checks weather forecasts (wind, precipitation, snow, visibility) at checkpoints along each route.
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                        <LocalShippingIcon color="success" />
                        <Typography variant="subtitle1" fontWeight={600}>
                          Driver Safety Ranking
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        The backend serves as the single source of truth for weather risk ranking and route recommendations.
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>

            <Card elevation={0} sx={{ p: 2, bgcolor: '#ffffff', borderRadius: 2, border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Service Health Monitor
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" sx={{ mt: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
                    onClick={checkHealth}
                    disabled={loading}
                    aria-label="Check backend health"
                  >
                    {loading ? 'Checking...' : 'Check Backend Health'}
                  </Button>
                  {health && (
                    <Typography variant="body2" color="success.main" fontWeight={500}>
                      Connected: {health.service} (status: {health.status})
                    </Typography>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        </Container>

        <Box component="footer" sx={{ py: 2, px: 2, mt: 'auto', bgcolor: '#ffffff', borderTop: '1px solid #e2e8f0', textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Spotter Truck Routing Platform • Leaflet & Open-Meteo Integration
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;
