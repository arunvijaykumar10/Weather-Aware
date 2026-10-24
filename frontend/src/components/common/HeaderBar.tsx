import React from 'react';
import { AppBar, Toolbar, Typography, Chip, Box, Stack } from '@mui/material';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';

export interface HeaderBarProps {
  isConnected: boolean;
  isLoading: boolean;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({ isConnected, isLoading }) => {
  const connectionLabel = isLoading
    ? 'Connecting...'
    : isConnected
      ? 'Backend Connected'
      : 'Backend Disconnected';

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
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, sm: 3 }, minHeight: 64 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 42,
              height: 42,
              borderRadius: 2.5,
              background: 'linear-gradient(135deg, #2563eb 0%, #06b6d4 100%)',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
              color: '#ffffff',
            }}
          >
            <LocalShippingIcon sx={{ fontSize: 24 }} />
          </Box>
          <Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography
                variant="h6"
                component="h1"
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: '1rem', sm: '1.2rem' },
                  letterSpacing: '-0.02em',
                  color: '#ffffff',
                }}
              >
                Spotter Weather-Aware Truck Routing
              </Typography>
              <Chip
                label="PRO DISPATCH"
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
                color: 'rgba(255, 255, 255, 0.6)',
                fontSize: '0.75rem',
                display: { xs: 'none', sm: 'block' },
              }}
            >
              Intelligent Multi-Corridor Safety Assessment & 0–48h Micro-Forecast Engine
            </Typography>
          </Box>
        </Stack>

        <Stack direction="row" spacing={1.5} alignItems="center">
          <Chip
            icon={
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: isConnected ? '#10b981' : '#ef4444',
                  boxShadow: isConnected
                    ? '0 0 8px #10b981'
                    : '0 0 8px #ef4444',
                  ml: 1,
                }}
              />
            }
            label={connectionLabel}
            size="small"
            sx={{
              fontWeight: 700,
              fontSize: '0.75rem',
              bgcolor: isConnected
                ? 'rgba(16, 185, 129, 0.12)'
                : 'rgba(239, 68, 68, 0.12)',
              color: isConnected ? '#34d399' : '#f87171',
              border: `1px solid ${
                isConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
              }`,
            }}
          />
        </Stack>
      </Toolbar>
    </AppBar>
  );
};

export default HeaderBar;
