import React, { ReactNode } from 'react';
import { Box, Container } from '@mui/material';
import { HeaderBar } from '../components/HeaderBar';
import { FooterBar } from '../components/FooterBar';

interface MainLayoutProps {
  isConnected: boolean;
  isCheckingHealth: boolean;
  children: ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  isConnected,
  isCheckingHealth,
  children,
}) => {
  return (
    <Box
      sx={{
        flexGrow: 1,
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <HeaderBar isConnected={isConnected} isLoading={isCheckingHealth} />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
        {children}
      </Container>
      <FooterBar />
    </Box>
  );
};

export default MainLayout;
