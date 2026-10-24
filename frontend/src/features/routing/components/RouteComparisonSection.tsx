import React from 'react';
import { Box, Typography, Grid, Alert, AlertTitle, Paper, Stack, Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import VerifiedIcon from '@mui/icons-material/Verified';
import { RouteAnalyzeResponse } from '../../../types/api';
import { RouteCard } from './RouteCard';

export interface RouteComparisonSectionProps {
  analysis: RouteAnalyzeResponse;
  selectedRouteId?: string;
  onSelectRoute?: (routeId: string) => void;
}

export const RouteComparisonSection: React.FC<RouteComparisonSectionProps> = ({
  analysis,
  selectedRouteId,
  onSelectRoute,
}) => {
  const { routes, recommendation, fewer_routes_reason, warnings } = analysis;

  return (
    <Stack spacing={2.5}>
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
          <AlertTitle sx={{ fontWeight: 800, fontSize: '1.1rem' }}>
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
            p: { xs: 2.5, sm: 3 },
            borderRadius: 3,
            border: '2px solid #2563eb',
            background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.04) 0%, rgba(2, 132, 199, 0.08) 100%)',
            boxShadow: '0 8px 24px -4px rgba(37, 99, 235, 0.12)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ sm: 'center' }} mb={1.5} gap={1}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  color: '#ffffff',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
                }}
              >
                <VerifiedIcon sx={{ fontSize: 22 }} />
              </Box>
              <Box>
                <Typography variant="h6" component="h3" fontWeight={800} color="primary.main">
                  Recommended Corridor: {recommendation.recommended_route_id}
                </Typography>
                <Typography variant="caption" color="text.secondary" fontWeight={500}>
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
          <Box component="ul" sx={{ pl: 1, m: 0, listStyle: 'none' }}>
            {recommendation.ranking_reasons.map((reason, idx) => (
              <Stack
                component="li"
                direction="row"
                spacing={1.25}
                alignItems="flex-start"
                key={idx}
                sx={{ mb: 0.75 }}
              >
                <CheckCircleIcon sx={{ fontSize: 18, color: '#10b981', mt: 0.25, flexShrink: 0 }} />
                <Typography variant="body2" sx={{ fontWeight: 600, color: '#1e293b' }}>
                  {reason}
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
      {warnings && warnings.length > 0 && (
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
            {warnings.map((warn, i) => (
              <Typography component="li" variant="body2" key={i}>
                {warn}
              </Typography>
            ))}
          </Box>
        </Alert>
      )}

      {/* Corridor Comparison Cards Grid */}
      <Box sx={{ pt: 1 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-end" mb={2}>
          <Box>
            <Typography variant="h5" component="h2" fontWeight={800} sx={{ letterSpacing: '-0.02em' }}>
              Driving Corridor Comparison ({routes.length} {routes.length === 1 ? 'Route' : 'Routes'})
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Click any corridor below to switch map view, highlight checkpoints, and inspect weather risk.
            </Typography>
          </Box>
        </Stack>

        <Grid container spacing={2.5}>
          {routes.map((route) => (
            <Grid
              item
              xs={12}
              md={routes.length === 1 ? 12 : routes.length === 2 ? 6 : 4}
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
