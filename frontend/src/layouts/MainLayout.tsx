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
        bgcolor: '#f8fafc',
      }}
    >
      <HeaderBar isConnected={isConnected} isLoading={isCheckingHealth} />
      <Container
        maxWidth={false}
        sx={{
          mt: { xs: 2, sm: 2.5 },
          mb: 4,
          flexGrow: 1,
          px: { xs: 1.5, sm: 2.5, md: 3, lg: 4 },
        }}
      >
        {children}
      </Container>
      <FooterBar />
    </Box>
  );
};

export default MainLayout;
