import React from 'react';
import { Box, Typography, Grid, Alert, AlertTitle, Paper, Stack, Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import VerifiedIcon from '@mui/icons-material/Verified';
import { RouteAnalyzeResponse, Route } from '../../../types/api';
import { RouteCard } from './RouteCard';

export interface RouteComparisonSectionProps {
  analysis: RouteAnalyzeResponse;
  selectedRouteId?: string;
  onSelectRoute?: (routeId: string) => void;
}

const getDisplayRouteTitle = (r: Route): string => {
  if (r.route_id === 'route_primary') return 'Primary Corridor';
  if (r.provider_summary) {
    return r.provider_summary.split(':')[0].trim();
  }
  const match = r.route_id.match(/alt_(\d+)/);
  if (match) return `Commercial Corridor ${Number(match[1]) + 1}`;
  return r.route_id;
};

const formatReasonText = (text: string): string => {
  return text
    .replace(/route_primary/g, 'Primary Corridor')
    .replace(/route_alt_1/g, 'Commercial Corridor 2')
    .replace(/route_alt_2/g, 'Commercial Corridor 3')
    .replace(/route_alt_(\d+)/g, (_, n) => `Commercial Corridor ${Number(n) + 1}`);
};

export const RouteComparisonSection: React.FC<RouteComparisonSectionProps> = ({
  analysis,
  selectedRouteId,
  onSelectRoute,
}) => {
  const { routes, recommendation, fewer_routes_reason, warnings } = analysis;

  const recommendedRoute = routes.find(
    (r) => r.route_id === recommendation.recommended_route_id
  );
  const recommendedTitle = recommendedRoute
    ? getDisplayRouteTitle(recommendedRoute)
    : recommendation.recommended_route_id || 'Optimal Safety Route';

  return (
    <Stack spacing={{ xs: 2, sm: 2.5 }}>
      {/* Safety Recommendation Banner */}
      {recommendation.no_route_meets_safety_thresholds ? (
        <Alert
          severity="error"
          icon={<WarningAmberIcon fontSize="large" />}
          sx={{
            borderRadius: 3,
            border: '2px solid #ef4444',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.15)',
          }}
        >
          <AlertTitle sx={{ fontWeight: 800, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Safety Threshold Alert: No Safe Route Available
          </AlertTitle>
          All evaluated corridors exceed safety limits due to extreme weather hazards (No-Travel
          conditions). The corridors below are ordered by hazard exposure for reference, but none
          are recommended for travel.
        </Alert>
      ) : (
        <Paper
          elevation={0}
          sx={{
            p: { xs: 2, sm: 2.5, md: 3 },
            borderRadius: 3,
            border: '2px solid #2563eb',
            background:
              'linear-gradient(135deg, rgba(37, 99, 235, 0.04) 0%, rgba(2, 132, 199, 0.08) 100%)',
            boxShadow: '0 8px 24px -4px rgba(37, 99, 235, 0.12)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            mb={1.5}
            gap={1}
          >
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: { xs: 36, sm: 40 },
                  height: { xs: 36, sm: 40 },
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  color: '#ffffff',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
                  flexShrink: 0,
                }}
              >
                <VerifiedIcon sx={{ fontSize: { xs: 20, sm: 22 } }} />
              </Box>
              <Box>
                <Typography
                  variant="h6"
                  component="h3"
                  fontWeight={800}
                  color="primary.main"
                  sx={{ fontSize: { xs: '1rem', sm: '1.15rem' } }}
                >
                  Recommended Corridor: {recommendedTitle}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  fontWeight={500}
                  sx={{ fontSize: { xs: '0.72rem', sm: '0.78rem' }, display: 'block' }}
                >
                  Selected using backend safety criteria (fewest severe miles, fewest high miles, lowest average risk, shortest duration):
                </Typography>
              </Box>
            </Stack>

            <Chip
              label="DISPATCH CHOICE"
              size="small"
              sx={{
                fontWeight: 800,
                fontSize: '0.7rem',
                letterSpacing: '0.05em',
                bgcolor: 'primary.main',
                color: '#ffffff',
                alignSelf: { xs: 'flex-start', sm: 'center' },
              }}
            />
          </Stack>

          {/* Key ranking reasons with styled checkmarks */}
          <Box component="ul" sx={{ pl: 0.5, m: 0, listStyle: 'none' }}>
            {recommendation.ranking_reasons.map((reason, idx) => (
              <Stack
                component="li"
                direction="row"
                spacing={1.25}
                alignItems="flex-start"
                key={idx}
                sx={{ mb: 0.75 }}
              >
                <CheckCircleIcon
                  sx={{ fontSize: 18, color: '#10b981', mt: 0.25, flexShrink: 0 }}
                />
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    color: '#1e293b',
                    fontSize: { xs: '0.8rem', sm: '0.875rem' },
                  }}
                >
                  {formatReasonText(reason)}
                </Typography>
              </Stack>
            ))}
          </Box>
        </Paper>
      )}

      {/* Corridor Availability Notice */}
      {fewer_routes_reason && (
        <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ borderRadius: 2 }}>
          <AlertTitle sx={{ fontWeight: 700 }}>Corridor Availability Notice</AlertTitle>
          {fewer_routes_reason}
        </Alert>
      )}

      {/* Operational Warnings */}
      {warnings &&
        warnings.filter((w) => !w.toLowerCase().includes('graphhopper')).length > 0 && (
          <Alert
            severity="warning"
            sx={{
              borderRadius: 2,
              border: '1px solid #fed7aa',
              bgcolor: '#fffbeb',
            }}
          >
            <AlertTitle sx={{ fontWeight: 700 }}>Operational Warnings</AlertTitle>
            <Box component="ul" sx={{ pl: 2, m: 0 }}>
              {warnings
                .filter((w) => !w.toLowerCase().includes('graphhopper'))
                .map((warn, i) => (
                  <Typography component="li" variant="body2" key={i}>
                    {warn}
                  </Typography>
                ))}
            </Box>
          </Alert>
        )}

      {/* Corridor Comparison Cards Grid */}
      <Box sx={{ pt: 0.5 }}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'flex-end' }}
          mb={2}
          gap={0.5}
        >
          <Box>
            <Typography
              variant="h5"
              component="h2"
              fontWeight={800}
              sx={{
                letterSpacing: '-0.02em',
                fontSize: { xs: '1.15rem', sm: '1.35rem', md: '1.5rem' },
              }}
            >
              Driving Corridor Comparison ({routes.length} {routes.length === 1 ? 'Route' : 'Routes'})
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.78rem', sm: '0.85rem' } }}
            >
              Click any corridor below to switch map view, highlight checkpoints, and inspect weather risk.
            </Typography>
          </Box>
        </Stack>

        <Grid container spacing={{ xs: 2, sm: 2.5 }}>
          {routes.map((route) => (
            <Grid
              item
              xs={12}
              sm={routes.length === 1 ? 12 : 6}
              md={routes.length === 1 ? 12 : routes.length === 2 ? 6 : 4}
              lg={12}
              key={route.route_id}
            >
              <RouteCard
                route={route}
                isRecommended={route.route_id === recommendation.recommended_route_id}
                isSelected={route.route_id === selectedRouteId}
                onSelectRoute={onSelectRoute}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Stack>
  );
};

export default RouteComparisonSection;