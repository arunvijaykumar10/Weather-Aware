import React from 'react';
import { Paper, Typography, Stack, Box, Divider } from '@mui/material';
import { RISK_STYLE_MAP, ROUTE_STYLE_MAP, RiskStyleConfig } from './mapConstants';
import { RiskLevel } from '../../types/api';

export const MapLegend: React.FC<{ showHeatmap?: boolean }> = ({ showHeatmap = true }) => (
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

    {showHeatmap && (
      <>
        <Divider sx={{ my: 0.75 }} />
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
        >
          <Typography variant="caption" fontWeight={700}>
            Heatmap Intensity (0-4 Numeric Risk Score)
          </Typography>
          <Typography variant="caption" color="text.secondary" fontStyle="italic">
            Interpolated between forecast samples
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1.5} flexWrap="wrap" mt={0.5}>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#16a34a' }} />
            <Typography variant="caption">0: Low</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#d97706' }} />
            <Typography variant="caption">1: Mod</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#ea580c' }} />
            <Typography variant="caption">2: High</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#dc2626' }} />
            <Typography variant="caption">3: Severe</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#7f1d1d' }} />
            <Typography variant="caption">4: No Travel</Typography>
          </Stack>
        </Stack>
      </>
    )}
  </Paper>
);
