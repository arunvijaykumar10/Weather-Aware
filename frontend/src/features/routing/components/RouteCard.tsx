import React from 'react';
import { Card, CardContent, Typography, Chip, Stack, Box, Divider, Alert } from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import DangerousIcon from '@mui/icons-material/Dangerous';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Route, RiskLevel } from '../../../types/api';
import { formatDurationMinutes, formatEtaTimestamp } from '../../../utils/timeFormat';

export interface RouteCardProps {
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

const getDisplayRouteTitle = (r: Route): string => {
  if (r.route_id === 'route_primary') return 'Primary Corridor';
  if (r.provider_summary) {
    return r.provider_summary.split(':')[0].trim();
  }
  const match = r.route_id.match(/alt_(\d+)/);
  if (match) return `Commercial Corridor ${Number(match[1]) + 1}`;
  return r.route_id;
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

  const totalMiles = Math.max(1, route.distance_miles);
  const severePct = Math.min(100, (metrics.severe_miles / totalMiles) * 100);
  const highPct = Math.min(100 - severePct, (metrics.high_miles / totalMiles) * 100);
  const safePct = Math.max(0, 100 - severePct - highPct);

  return (
    <Card
      elevation={0}
      onClick={() => onSelectRoute?.(route.route_id)}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 3,
        border: '2px solid',
        borderColor: isSelected
          ? 'primary.main'
          : isRecommended
            ? 'primary.light'
            : '#e2e8f0',
        bgcolor: isSelected
          ? 'rgba(37, 99, 235, 0.03)'
          : '#ffffff',
        cursor: onSelectRoute ? 'pointer' : 'default',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: isSelected
          ? '0 12px 28px -4px rgba(37, 99, 235, 0.18)'
          : isRecommended
            ? '0 6px 20px -2px rgba(15, 23, 42, 0.08)'
            : '0 2px 8px -2px rgba(15, 23, 42, 0.04)',
        '&:hover': onSelectRoute
          ? {
              transform: 'translateY(-2px)',
              borderColor: isSelected ? 'primary.main' : '#94a3b8',
              boxShadow: '0 12px 24px -4px rgba(15, 23, 42, 0.12)',
            }
          : {},
      }}
      tabIndex={onSelectRoute ? 0 : undefined}
      role={onSelectRoute ? 'button' : undefined}
      aria-label={`Route ${route.route_id}, ${route.distance_miles} miles`}
    >
      {/* Top Accent Stripe */}
      <Box
        sx={{
          height: 4,
          width: '100%',
          bgcolor: isRecommended
            ? 'primary.main'
            : isSelected
              ? 'secondary.main'
              : 'transparent',
        }}
      />

      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: { xs: 2, sm: 2.5 } }}>
        {/* Card Header & Badges */}
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="flex-start"
          flexWrap="wrap"
          gap={1}
          mb={1.5}
        >
          <Box sx={{ pr: 1, minWidth: { xs: 120, sm: 140 } }}>
            <Typography
              variant="h6"
              component="h3"
              sx={{
                fontWeight: 800,
                fontSize: { xs: '0.95rem', sm: '1.05rem' },
                lineHeight: 1.3,
                color: 'text.primary',
              }}
            >
              {getDisplayRouteTitle(route)}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500, fontSize: '0.75rem' }}>
              {route.checkpoints.length} sampled checkpoints
            </Typography>
          </Box>

          <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap" sx={{ gap: 0.5 }}>
            {isRecommended && (
              <Chip
                icon={<StarIcon sx={{ '&&': { color: '#ffffff', fontSize: 16 } }} />}
                label="Recommended"
                color="primary"
                size="small"
                sx={{
                  fontWeight: 800,
                  fontSize: '0.72rem',
                  letterSpacing: '0.02em',
                  background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)',
                  boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
                }}
              />
            )}
            {!eligibility.is_eligible && (
              <Chip
                icon={<DangerousIcon sx={{ fontSize: 16 }} />}
                label="No-Travel Hazard"
                color="error"
                size="small"
                sx={{ fontWeight: 800, fontSize: '0.72rem' }}
              />
            )}
          </Stack>
        </Stack>

        {/* Primary Travel Numbers */}
        <Box
          sx={{
            my: 1.5,
            p: { xs: 1.25, sm: 1.5 },
            bgcolor: isSelected ? 'rgba(37, 99, 235, 0.05)' : '#f8fafc',
            borderRadius: 2,
            border: '1px solid #f1f5f9',
          }}
        >
          <Stack
            direction="row"
            spacing={{ xs: 1.5, sm: 3 }}
            alignItems="center"
            justifyContent="space-between"
          >
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, fontSize: '0.7rem' }}>
                Distance
              </Typography>
              <Typography
                variant="h5"
                component="div"
                sx={{
                  fontWeight: 800,
                  color: 'text.primary',
                  fontSize: { xs: '1.2rem', sm: '1.35rem' },
                }}
              >
                {route.distance_miles.toFixed(1)}{' '}
                <Typography
                  variant="caption"
                  component="span"
                  sx={{ color: 'text.secondary', fontWeight: 600 }}
                >
                  mi
                </Typography>
              </Typography>
            </Box>

            <Divider orientation="vertical" flexItem sx={{ borderColor: '#e2e8f0' }} />

            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, fontSize: '0.7rem' }}>
                Travel Time
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontWeight: 800,
                  color: 'text.primary',
                  fontSize: { xs: '0.95rem', sm: '1.05rem' },
                }}
              >
                {formatDurationMinutes(route.duration_minutes)}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  display: 'block',
                  fontSize: '0.7rem',
                  whiteSpace: 'nowrap',
                }}
              >
                ETA: {finalEtaFormatted}
              </Typography>
            </Box>
          </Stack>
        </Box>

        {/* Visual Weather Risk Meter (Horizontal Progress Bar) */}
        <Box sx={{ mb: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={0.75}>
            <Typography
              variant="caption"
              sx={{
                fontWeight: 700,
                color: 'text.secondary',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                fontSize: '0.68rem',
              }}
            >
              Safety Exposure Meter
            </Typography>
            <Chip
              label={metrics.average_risk.toUpperCase()}
              color={getRiskChipColor(metrics.average_risk)}
              size="small"
              sx={{ fontWeight: 800, height: 20, fontSize: '0.65rem' }}
            />
          </Stack>

          {/* Segmented bar */}
          <Box
            sx={{
              display: 'flex',
              height: 8,
              borderRadius: 4,
              overflow: 'hidden',
              bgcolor: '#e2e8f0',
              width: '100%',
            }}
          >
            <Box
              sx={{ width: `${safePct}%`, bgcolor: '#10b981', transition: 'width 0.4s ease' }}
              title="Safe miles"
            />
            <Box
              sx={{ width: `${highPct}%`, bgcolor: '#f97316', transition: 'width 0.4s ease' }}
              title="High weather miles"
            />
            <Box
              sx={{ width: `${severePct}%`, bgcolor: '#ef4444', transition: 'width 0.4s ease' }}
              title="Severe weather miles"
            />
          </Box>
        </Box>

        {/* Hazard Mileage Rows */}
        <Stack spacing={0.75} mb={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: { xs: '0.78rem', sm: '0.82rem' } }}>
              Severe Weather Exposure:
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 700,
                fontSize: { xs: '0.8rem', sm: '0.85rem' },
                color: metrics.severe_miles > 0 ? 'error.main' : 'text.primary',
              }}
            >
              {metrics.severe_miles.toFixed(1)} mi
            </Typography>
          </Stack>

          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: { xs: '0.78rem', sm: '0.82rem' } }}>
              High Weather Exposure:
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 700,
                fontSize: { xs: '0.8rem', sm: '0.85rem' },
                color: metrics.high_miles > 0 ? 'warning.main' : 'text.primary',
              }}
            >
              {metrics.high_miles.toFixed(1)} mi
            </Typography>
          </Stack>

          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: { xs: '0.78rem', sm: '0.82rem' } }}>
              Forecast Coverage:
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 700,
                fontSize: { xs: '0.8rem', sm: '0.85rem' },
                color: metrics.forecast_coverage_pct < 100 ? 'warning.dark' : 'success.main',
              }}
            >
              {metrics.forecast_coverage_pct.toFixed(0)}%
            </Typography>
          </Stack>
        </Stack>

        {/* No-Travel Alert or Compliance Banner */}
        {metrics.has_no_travel_segment && (
          <Alert
            severity="error"
            icon={<DangerousIcon sx={{ fontSize: 18 }} />}
            sx={{
              mt: 'auto',
              py: 0.5,
              borderRadius: 2,
              '& .MuiAlert-message': { p: 0 },
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 700, display: 'block' }}>
              Contains {metrics.no_travel_miles.toFixed(1)} mi of hazardous No-Travel weather.
            </Typography>
          </Alert>
        )}

        {!metrics.has_no_travel_segment && isRecommended && (
          <Alert
            severity="success"
            icon={<CheckCircleIcon sx={{ fontSize: 18, color: '#10b981' }} />}
            sx={{
              mt: 'auto',
              py: 0.5,
              borderRadius: 2,
              bgcolor: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              '& .MuiAlert-message': { p: 0 },
            }}
          >
            <Typography
              variant="caption"
              sx={{ fontWeight: 700, color: '#065f46', display: 'block', fontSize: '0.75rem' }}
            >
              Complies with commercial driver safety thresholds.
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default RouteCard;