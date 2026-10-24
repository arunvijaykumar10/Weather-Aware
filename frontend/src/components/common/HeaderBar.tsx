import React from 'react';
import { AppBar, Toolbar, Typography, Chip, Box, Stack } from '@mui/material';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import SensorsIcon from '@mui/icons-material/Sensors';

export interface HeaderBarProps {
  isConnected?: boolean;
  isLoading?: boolean;
}

export const HeaderBar: React.FC<HeaderBarProps> = () => {
  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar
        sx={{
          justifyContent: 'space-between',
          px: { xs: 1.5, sm: 2.5, md: 3, lg: 4 },
          minHeight: { xs: 56, sm: 64 },
          gap: 1,
        }}
      >
        <Stack direction="row" spacing={{ xs: 1.25, sm: 2 }} alignItems="center" sx={{ minWidth: 0 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: { xs: 36, sm: 42 },
              height: { xs: 36, sm: 42 },
              borderRadius: 2.5,
              background: 'linear-gradient(135deg, #2563eb 0%, #06b6d4 100%)',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
              color: '#ffffff',
              flexShrink: 0,
            }}
          >
            <LocalShippingIcon sx={{ fontSize: { xs: 20, sm: 24 } }} />
          </Box>
          <Box sx={{ minWidth: 0 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography
                variant="h6"
                component="h1"
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: '0.875rem', sm: '1.15rem', md: '1.25rem' },
                  letterSpacing: '-0.02em',
                  color: '#ffffff',
                  lineHeight: 1.25,
                }}
              >
                Weather-Aware Truck Route Intelligence
              </Typography>
              <Chip
                label="LIVE FLEET DISPATCH"
                size="small"
                sx={{
                  display: { xs: 'none', md: 'inline-flex' },
                  height: 20,
                  fontSize: '0.65rem',
                  fontWeight: 800,
                  bgcolor: 'rgba(56, 189, 248, 0.15)',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              />
            </Stack>
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255, 255, 255, 0.65)',
                fontSize: '0.75rem',
                display: { xs: 'none', sm: 'block' },
              }}
            >
              Commercial Multi-Corridor Safety Assessment & 0–48h Micro-Forecast Engine
            </Typography>
          </Box>
        </Stack>

        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ flexShrink: 0 }}>
          <Chip
            icon={<SensorsIcon sx={{ fontSize: '14px !important', color: '#10b981' }} />}
            label="Live Radar Active"
            size="small"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '0.7rem', sm: '0.75rem' },
              height: { xs: 24, sm: 28 },
              bgcolor: 'rgba(16, 185, 129, 0.12)',
              color: '#34d399',
              border: '1px solid rgba(16, 185, 129, 0.3)',
            }}
          />
        </Stack>
      </Toolbar>
    </AppBar>
  );
};

export default HeaderBar;
