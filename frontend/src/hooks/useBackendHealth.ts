import { useState, useEffect, useCallback } from 'react';

export interface HealthResponse {
  status: string;
  service: string;
}

export const useBackendHealth = () => {
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refreshHealth = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const backendBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendBaseUrl}/api/health/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const responsePayload: HealthResponse = await response.json();
      setHealthStatus(responsePayload);
    } catch (caughtError: unknown) {
      const message =
        caughtError instanceof Error ? caughtError.message : 'Failed to connect to backend';
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  return { healthStatus, isLoading, errorMessage, refreshHealth, setErrorMessage };
};
