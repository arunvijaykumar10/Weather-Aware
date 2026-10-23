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
    },
  },
};
