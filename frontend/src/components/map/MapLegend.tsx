import React from 'react';
import { Paper, Typography, Stack, Box, Divider } from '@mui/material';
import { RISK_STYLE_MAP, ROUTE_STYLE_MAP, RiskStyleConfig } from './mapConstants';
import { RiskLevel } from '../../types/api';

export const MapLegend: React.FC<{ showHeatmap?: boolean }> = ({ showHeatmap = true }) => (
  <Paper
    elevation={0}
    sx={{
      p: 2,
      borderRadius: 2.5,
      border: '1px solid #e2e8f0',
      bgcolor: '#ffffff',
      boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
    }}
  >
    <Typography variant="caption" fontWeight={800} display="block" mb={0.75} sx={{ textTransform: 'uppercase', color: 'text.secondary', letterSpacing: '0.04em' }}>
      Route Corridors (Pattern & Color)
    </Typography>
    <Stack direction="row" spacing={2} flexWrap="wrap" mb={1.25}>
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
          <Typography variant="caption" fontWeight={600}>{config.name}</Typography>
        </Stack>
      ))}
    </Stack>

    <Divider sx={{ my: 1 }} />

    <Typography variant="caption" fontWeight={800} display="block" mb={0.75} sx={{ textTransform: 'uppercase', color: 'text.secondary', letterSpacing: '0.04em' }}>
      Checkpoint Weather Risk (Symbol, Label & Color)
    </Typography>
    <Stack direction="row" spacing={1.5} flexWrap="wrap" sx={{ gap: 0.5 }}>
      {(Object.entries(RISK_STYLE_MAP) as [RiskLevel, RiskStyleConfig][]).map(([level, config]) => (
        <Stack direction="row" spacing={0.5} alignItems="center" key={level}>
          <Typography
            component="span"
            sx={{ color: config.color, fontWeight: 900, fontSize: '0.875rem' }}
          >
            {config.symbol}
          </Typography>
          <Typography variant="caption" fontWeight={500}>{config.label}</Typography>
        </Stack>
      ))}
    </Stack>

    {showHeatmap && (
      <>
        <Divider sx={{ my: 1 }} />
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          mb={0.5}
        >
          <Typography variant="caption" fontWeight={800} sx={{ textTransform: 'uppercase', color: 'text.secondary', letterSpacing: '0.04em' }}>
            Heatmap Intensity (0-4 Numeric Risk Score)
          </Typography>
          <Typography variant="caption" color="text.secondary" fontStyle="italic">
            Interpolated between forecast samples
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1.5} flexWrap="wrap" mt={0.5} sx={{ gap: 0.5 }}>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#16a34a' }} />
            <Typography variant="caption" fontWeight={600}>0: Low</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#d97706' }} />
            <Typography variant="caption" fontWeight={600}>1: Mod</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#ea580c' }} />
            <Typography variant="caption" fontWeight={600}>2: High</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#dc2626' }} />
            <Typography variant="caption" fontWeight={600}>3: Severe</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#7f1d1d' }} />
            <Typography variant="caption" fontWeight={600}>4: No Travel</Typography>
          </Stack>
        </Stack>
      </>
    )}
  </Paper>
);

export default MapLegend;
