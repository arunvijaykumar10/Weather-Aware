import React from 'react';
import { Paper, Typography, Grid, Card, CardContent, Stack } from '@mui/material';
import AltRouteIcon from '@mui/icons-material/AltRoute';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';

const ARCHITECTURE_PILLARS = [
  {
    title: 'Up to 3 Routes',
    description:
      'Generates alternative driving paths using routing engine APIs with geometry and maneuver segments.',
    icon: <AltRouteIcon color="primary" />,
  },
  {
    title: 'Weather Risk Scoring',
    description:
      'Backend checks weather forecasts (wind, precipitation, snow, visibility) at checkpoints along each route.',
    icon: <CloudQueueIcon color="secondary" />,
  },
  {
    title: 'Driver Safety Ranking',
    description:
      'The backend serves as the single source of truth for weather risk ranking and route recommendations.',
    icon: <LocalShippingIcon color="success" />,
  },
];

export const SystemOverviewCards: React.FC = () => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      border: 1,
      borderColor: 'divider',
    }}
  >
    <Typography variant="h5" component="h2" gutterBottom color="primary">
      System Overview & Architecture
    </Typography>
    <Typography variant="body1" color="text.secondary" paragraph>
      Spotter calculates driving routes for heavy freight, continuously monitoring weather hazards
      along active corridors to rank routes by safety and efficiency.
    </Typography>

    <Grid container spacing={2} sx={{ mt: 1 }}>
      {ARCHITECTURE_PILLARS.map((pillar) => (
        <Grid item xs={12} md={4} key={pillar.title}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                {pillar.icon}
                <Typography variant="subtitle1" component="h3">
                  {pillar.title}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                {pillar.description}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  </Paper>
);

export default SystemOverviewCards;
