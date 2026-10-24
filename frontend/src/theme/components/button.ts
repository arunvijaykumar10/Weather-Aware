import { Components, Theme } from '@mui/material/styles';

export const buttonOverrides: Components<Theme>['MuiButton'] = {
  defaultProps: {
    disableElevation: true,
  },
  styleOverrides: {
    root: {
      textTransform: 'none',
      borderRadius: 8,
      fontWeight: 600,
      padding: '8px 18px',
      transition: 'all 0.15s ease-in-out',
      '&:hover': {
        transform: 'translateY(-1px)',
      },
      '&:active': {
        transform: 'translateY(0)',
      },
    },
    containedPrimary: {
      background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)',
      '&:hover': {
        background: 'linear-gradient(135deg, #172554 0%, #1d4ed8 100%)',
        boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
      },
    },
  },
};
