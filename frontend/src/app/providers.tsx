import React, { ReactNode } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { appTheme } from '../theme';

interface AppProvidersProps {
  children: ReactNode;
}

export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};

export default AppProviders;
