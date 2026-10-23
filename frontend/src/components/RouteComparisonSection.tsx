import React from 'react';
import { Box, Typography, Grid, Alert, AlertTitle, Paper, Stack } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { RouteAnalyzeResponse } from '../types/api';
import { RouteCard } from './RouteCard';

interface RouteComparisonSectionProps {
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
    <Stack spacing={3} sx={{ mt: 3 }}>
      {recommendation.no_route_meets_safety_thresholds ? (
        <Alert severity="error" icon={<WarningAmberIcon fontSize="large" />}>
          <AlertTitle sx={{ fontWeight: 800 }}>
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
            p: 2.5,
            border: 2,
            borderColor: 'primary.light',
            bgcolor: 'rgba(30, 58, 138, 0.04)',
          }}
        >
          <Stack direction="row" spacing={1.5} alignItems="center" mb={1}>
            <CheckCircleOutlineIcon color="primary" fontSize="medium" />
            <Typography variant="h6" component="h3" fontWeight={700} color="primary">
              Recommended Corridor: {recommendation.recommended_route_id}
            </Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            Selected using backend safety criteria (fewest severe miles, fewest high miles, lowest
            average risk, shortest duration):
          </Typography>
          <Box component="ul" sx={{ pl: 2.5, m: 0 }}>
            {recommendation.ranking_reasons.map((reason, idx) => (
              <Typography component="li" variant="body2" key={idx} sx={{ mb: 0.5 }}>
                {reason}
              </Typography>
            ))}
          </Box>
        </Paper>
      )}

      {fewer_routes_reason && (
        <Alert severity="info" icon={<InfoOutlinedIcon />}>
          <AlertTitle sx={{ fontWeight: 700 }}>Corridor Availability Notice</AlertTitle>
          {fewer_routes_reason}
        </Alert>
      )}

      {warnings && warnings.length > 0 && (
        <Alert severity="warning">
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

      <Box>
        <Typography variant="h5" component="h2" fontWeight={700} gutterBottom>
          Driving Corridor Comparison ({routes.length} {routes.length === 1 ? 'Route' : 'Routes'})
        </Typography>
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
