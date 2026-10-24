import React from 'react';
import { Paper, Typography, Grid, Card, CardContent, Stack, Box } from '@mui/material';
import AltRouteIcon from '@mui/icons-material/AltRoute';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import ShieldIcon from '@mui/icons-material/Shield';

const CAPABILITY_PILLARS = [
  {
    title: 'Multi-Corridor Generation',
    description:
      'Computes alternative interstate highway corridors using high-performance routing with turn-by-turn geometry and detour validation.',
    icon: <AltRouteIcon sx={{ color: '#2563eb', fontSize: 24 }} />,
    color: '#2563eb',
    badge: 'Corridor Routing',
  },
  {
    title: 'Dynamic Weather Telemetry',
    description:
      'Continuously queries high-resolution atmospheric models at continuous intervals along the truck trajectory to evaluate wind, rain, and snow hazards.',
    icon: <CloudQueueIcon sx={{ color: '#0284c7', fontSize: 24 }} />,
    color: '#0284c7',
    badge: 'Micro-Forecast',
  },
  {
    title: 'Load-Adaptive Safety Engine',
    description:
      'Dynamically scales crosswind rollover and traction thresholds based on gross vehicle weight to recommend the safest operational corridor.',
    icon: <LocalShippingIcon sx={{ color: '#10b981', fontSize: 24 }} />,
    color: '#10b981',
    badge: 'Safety Compliance',
  },
];

export const SystemOverviewCards: React.FC = () => (
  <Paper
    elevation={0}
    sx={{
      p: { xs: 2.5, sm: 3.5 },
      borderRadius: 3,
      border: '1px solid #e2e8f0',
      bgcolor: '#ffffff',
      boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.05)',
    }}
  >
    <Stack direction="row" spacing={1.5} alignItems="center" mb={1}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 32,
          height: 32,
          borderRadius: 1.5,
          bgcolor: 'rgba(37, 99, 235, 0.08)',
          color: 'primary.main',
        }}
      >
        <ShieldIcon sx={{ fontSize: 18 }} />
      </Box>
      <Typography variant="h5" component="h2" color="text.primary" sx={{ fontWeight: 800 }}>
        Fleet Safety Intelligence & Capabilities
      </Typography>
    </Stack>

    <Typography variant="body1" color="text.secondary" paragraph sx={{ maxWidth: 800, mb: 3 }}>
      Calculates commercial driving corridors for heavy freight, continuously monitoring weather hazards
      along active routes to dynamically recommend the safest and most efficient path.
    </Typography>

    <Grid container spacing={{ xs: 2, sm: 2.5 }}>
      {CAPABILITY_PILLARS.map((pillar) => (
        <Grid item xs={12} sm={6} md={4} key={pillar.title}>
          <Card
            elevation={0}
            sx={{
              height: '100%',
              borderRadius: 2.5,
              border: '1px solid #f1f5f9',
              bgcolor: '#f8fafc',
              p: 1,
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: '#cbd5e1',
                boxShadow: '0 6px 16px rgba(15, 23, 42, 0.06)',
                transform: 'translateY(-2px)',
              },
            }}
          >
            <CardContent>
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 700,
                  fontSize: '0.65rem',
                  textTransform: 'uppercase',
                  color: pillar.color,
                  letterSpacing: '0.05em',
                  display: 'block',
                  mb: 1,
                }}
              >
                {pillar.badge}
              </Typography>
              <Stack direction="row" spacing={1.5} alignItems="center" mb={1.5}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 38,
                    height: 38,
                    borderRadius: 2,
                    bgcolor: '#ffffff',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  {pillar.icon}
                </Box>
                <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 800 }}>
                  {pillar.title}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
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
