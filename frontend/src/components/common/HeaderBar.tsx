import React from 'react';
import { AppBar, Toolbar, Typography, Chip } from '@mui/material';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';

export interface HeaderBarProps {
  isConnected: boolean;
  isLoading: boolean;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({ isConnected, isLoading }) => {
  const connectionLabel = isLoading
    ? 'Checking Backend...'
    : isConnected
      ? 'Backend Connected'
      : 'Backend Disconnected';

  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        <LocalShippingIcon sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h6" component="h1" sx={{ flexGrow: 1, fontWeight: 700 }}>
          Spotter Weather-Aware Truck Routing
        </Typography>
        <Chip
          label={connectionLabel}
          color={isConnected ? 'success' : 'error'}
          size="small"
          sx={{ fontWeight: 600 }}
        />
      </Toolbar>
    </AppBar>
  );
};

export default HeaderBar;
