import React from 'react';
import { Box, Typography } from '@mui/material';

export const FooterBar: React.FC = () => (
  <Box
    component="footer"
    sx={{
      py: 2,
      px: 2,
      mt: 'auto',
      bgcolor: 'background.paper',
      borderTop: 1,
      borderColor: 'divider',
      textAlign: 'center',
    }}
  >
    <Typography variant="body2" color="text.secondary">
      Spotter Truck Routing Platform • Leaflet & Open-Meteo Integration
    </Typography>
  </Box>
);

export default FooterBar;
