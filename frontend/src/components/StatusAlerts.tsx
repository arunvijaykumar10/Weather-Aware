import React from 'react';
import { Alert, AlertTitle, Box, Typography } from '@mui/material';
import { ApiError } from '../api/routeClient';

interface StatusAlertsProps {
  apiError: ApiError | null;
  onClearError: () => void;
}

export const StatusAlerts: React.FC<StatusAlertsProps> = ({ apiError, onClearError }) => {
  if (!apiError) return null;

  const isRateLimited = apiError.code === 'request_throttled';

  return (
    <Alert severity={isRateLimited ? 'warning' : 'error'} onClose={onClearError} sx={{ mb: 2 }}>
      <AlertTitle sx={{ fontWeight: 700 }}>
        {isRateLimited
          ? 'Rate Limit Active (429)'
          : apiError.code === 'validation_error'
            ? 'Validation Error'
            : 'Route Analysis Failed'}
      </AlertTitle>
      <Typography variant="body2">{apiError.message}</Typography>
      {apiError.waitSeconds && (
        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
          Quota cooldown active: ready in ~{apiError.waitSeconds} seconds.
        </Typography>
      )}
      {apiError.details && Object.keys(apiError.details).length > 0 && (
        <Box component="ul" sx={{ pl: 2, mt: 1, mb: 0 }}>
          {Object.entries(apiError.details).map(([field, errs]) => (
            <Typography component="li" variant="caption" key={field}>
              <strong>{field}:</strong> {Array.isArray(errs) ? errs.join(', ') : String(errs)}
            </Typography>
          ))}
        </Box>
      )}
    </Alert>
  );
};
