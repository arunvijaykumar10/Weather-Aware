import React from 'react';
import { Box, Typography } from '@mui/material';

export const FooterBar: React.FC = () => (
  <Box
    component="footer"
    sx={{
      py: 2.5,
      px: 2,
      mt: 'auto',
      bgcolor: 'background.paper',
      borderTop: 1,
      borderColor: 'divider',
      textAlign: 'center',
    }}
  >
    <Typography variant="body2" color="text.secondary">
      Commercial Route Intelligence Platform • Real-time Telemetry & Micro-Forecast Integration
    </Typography>
  </Box>
);

export default FooterBar;
