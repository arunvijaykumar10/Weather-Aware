import React from 'react';
import { Paper, Typography, Stack, Box, Divider } from '@mui/material';
import { RISK_STYLE_MAP, ROUTE_STYLE_MAP, RiskStyleConfig } from './mapConstants';
import { RiskLevel } from '../../types/api';

export const MapLegend: React.FC = () => (
  <Paper
    elevation={1}
    sx={{
      p: 1.5,
      border: 1,
      borderColor: 'divider',
      bgcolor: 'rgba(255, 255, 255, 0.95)',
    }}
  >
    <Typography variant="caption" fontWeight={700} display="block" mb={0.5}>
      Route Corridors (Pattern & Color)
    </Typography>
    <Stack direction="row" spacing={2} flexWrap="wrap" mb={1}>
      {Object.entries(ROUTE_STYLE_MAP).map(([routeId, config]) => (
        <Stack direction="row" spacing={0.75} alignItems="center" key={routeId}>
          <Box
            sx={{
              width: 22,
              height: 0,
              borderTop: 3,
              borderColor: config.color,
              borderStyle: config.dashArray ? 'dashed' : 'solid',
            }}
          />
          <Typography variant="caption">{config.name}</Typography>
        </Stack>
      ))}
    </Stack>

    <Divider sx={{ my: 0.75 }} />

    <Typography variant="caption" fontWeight={700} display="block" mb={0.5}>
      Checkpoint Weather Risk (Symbol, Label & Color)
    </Typography>
    <Stack direction="row" spacing={1.5} flexWrap="wrap">
      {(Object.entries(RISK_STYLE_MAP) as [RiskLevel, RiskStyleConfig][]).map(([level, config]) => (
        <Stack direction="row" spacing={0.5} alignItems="center" key={level}>
          <Typography
            component="span"
            sx={{ color: config.color, fontWeight: 900, fontSize: '0.875rem' }}
          >
            {config.symbol}
          </Typography>
          <Typography variant="caption">{config.label}</Typography>
        </Stack>
      ))}
    </Stack>
  </Paper>
);
