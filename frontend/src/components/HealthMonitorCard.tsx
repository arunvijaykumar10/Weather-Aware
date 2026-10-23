import React from 'react';
import { Card, CardContent, Typography, Stack, Button, CircularProgress } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { HealthResponse } from '../hooks/useBackendHealth';

interface HealthMonitorCardProps {
  healthStatus: HealthResponse | null;
  isLoading: boolean;
  onRefreshHealth: () => void;
}

export const HealthMonitorCard: React.FC<HealthMonitorCardProps> = ({
  healthStatus,
  isLoading,
  onRefreshHealth,
}) => (
  <Card elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }}>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        Service Health Monitor
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" sx={{ mt: 2 }}>
        <Button
          variant="contained"
          startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
          onClick={onRefreshHealth}
          disabled={isLoading}
          aria-label="Check backend health"
        >
          {isLoading ? 'Checking...' : 'Check Backend Health'}
        </Button>
        {healthStatus && (
          <Typography variant="body2" color="success.main" fontWeight={500}>
            Connected: {healthStatus.service} (status: {healthStatus.status})
          </Typography>
        )}
      </Stack>
    </CardContent>
  </Card>
);
