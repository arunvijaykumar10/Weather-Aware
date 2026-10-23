import React from 'react';
import { Card, CardContent, Typography, Chip, Stack, Box, Divider, Alert } from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import DangerousIcon from '@mui/icons-material/Dangerous';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Route, RiskLevel } from '../types/api';
import { formatDurationMinutes, formatEtaTimestamp } from '../utils/timeFormat';

interface RouteCardProps {
  route: Route;
  isRecommended: boolean;
  isSelected?: boolean;
  onSelectRoute?: (routeId: string) => void;
}

const getRiskChipColor = (risk: RiskLevel): 'success' | 'warning' | 'error' | 'default' => {
  switch (risk) {
    case 'low':
      return 'success';
    case 'moderate':
      return 'warning';
    case 'high':
    case 'severe':
    case 'no_travel':
      return 'error';
    default:
      return 'default';
  }
};

export const RouteCard: React.FC<RouteCardProps> = ({
  route,
  isRecommended,
  isSelected,
  onSelectRoute,
}) => {
  const { metrics, eligibility } = route;
  const lastCheckpoint = route.checkpoints[route.checkpoints.length - 1];
  const finalEtaFormatted = lastCheckpoint ? formatEtaTimestamp(lastCheckpoint.eta) : 'Unknown';

  return (
    <Card
      variant="outlined"
      onClick={() => onSelectRoute?.(route.route_id)}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        border: 2,
        borderColor: isRecommended ? 'primary.main' : isSelected ? 'secondary.main' : 'divider',
        bgcolor: isRecommended ? 'rgba(30, 58, 138, 0.02)' : 'background.paper',
        cursor: onSelectRoute ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        '&:hover': onSelectRoute ? { borderColor: 'primary.light', boxShadow: 2 } : {},
      }}
      tabIndex={onSelectRoute ? 0 : undefined}
      role={onSelectRoute ? 'button' : undefined}
      aria-label={`Route ${route.route_id}, ${route.distance_miles} miles`}
    >
      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Box>
            <Typography variant="h6" component="h3" fontWeight={700}>
              {route.route_id === 'route_primary'
                ? 'Primary Corridor'
                : route.provider_summary || route.route_id}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {route.checkpoints.length} sampled checkpoints
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            {isRecommended && (
              <Chip
                icon={<StarIcon sx={{ '&&': { color: '#ffffff' } }} />}
                label="Recommended"
                color="primary"
                size="small"
                sx={{ fontWeight: 700 }}
              />
            )}
            {!eligibility.is_eligible && (
              <Chip
                icon={<DangerousIcon />}
                label="No-Travel Hazard"
                color="error"
                size="small"
                sx={{ fontWeight: 700 }}
              />
            )}
          </Stack>
        </Stack>

        <Stack direction="row" spacing={2} my={1.5} alignItems="baseline">
          <Typography variant="h4" component="span" fontWeight={800} color="text.primary">
            {route.distance_miles.toFixed(1)}{' '}
            <Typography variant="body2" component="span" color="text.secondary">
              mi
            </Typography>
          </Typography>
          <Divider orientation="vertical" flexItem />
          <Box>
            <Typography variant="body1" fontWeight={700}>
              {formatDurationMinutes(route.duration_minutes)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              ETA: {finalEtaFormatted}
            </Typography>
          </Box>
        </Stack>

        <Divider sx={{ my: 1.5 }} />

        <Stack spacing={1} mb={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="text.secondary">
              Average Risk Level:
            </Typography>
            <Chip
              label={metrics.average_risk.toUpperCase()}
              color={getRiskChipColor(metrics.average_risk)}
              size="small"
              sx={{ fontWeight: 700 }}
            />
          </Stack>

          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">
              Severe Weather Exposure:
            </Typography>
            <Typography
              variant="body2"
              fontWeight={700}
              color={metrics.severe_miles > 0 ? 'error.main' : 'text.primary'}
            >
              {metrics.severe_miles.toFixed(1)} mi
            </Typography>
          </Stack>

          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">
              High Weather Exposure:
            </Typography>
            <Typography
              variant="body2"
              fontWeight={700}
              color={metrics.high_miles > 0 ? 'warning.main' : 'text.primary'}
            >
              {metrics.high_miles.toFixed(1)} mi
            </Typography>
          </Stack>

          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">
              Forecast Coverage:
            </Typography>
            <Typography
              variant="body2"
              fontWeight={600}
              color={metrics.forecast_coverage_pct < 100 ? 'warning.dark' : 'success.main'}
            >
              {metrics.forecast_coverage_pct.toFixed(0)}%
            </Typography>
          </Stack>
        </Stack>

        {metrics.has_no_travel_segment && (
          <Alert severity="error" icon={<DangerousIcon />} sx={{ mt: 'auto', py: 0.5 }}>
            <Typography variant="caption" fontWeight={700}>
              Contains {metrics.no_travel_miles.toFixed(1)} mi of hazardous No-Travel weather.
            </Typography>
          </Alert>
        )}

        {!metrics.has_no_travel_segment && isRecommended && (
          <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mt: 'auto', py: 0.5 }}>
            <Typography variant="caption" fontWeight={700}>
              Complies with commercial driver safety thresholds.
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
