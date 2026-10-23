import { Components, Theme } from '@mui/material/styles';

export const paperOverrides: Components<Theme>['MuiPaper'] = {
  styleOverrides: {
    rounded: {
      borderRadius: 8,
    },
  },
};
