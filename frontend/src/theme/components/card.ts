import { Components, Theme } from '@mui/material/styles';

export const paperOverrides: Components<Theme>['MuiPaper'] = {
  styleOverrides: {
    root: {
      borderRadius: 12,
      backgroundImage: 'none',
    },
    elevation0: {
      border: '1px solid #e2e8f0',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
    },
  },
};
