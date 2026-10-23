import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App from './App';

describe('App component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the Spotter app title and system overview', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'healthy',
        service: 'spotter-weather-aware-routing-backend',
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<App />);

    expect(
      screen.getByRole('heading', { name: /spotter weather-aware truck routing/i })
    ).toBeInTheDocument();

    expect(
      screen.getByRole('heading', { name: /system overview & architecture/i })
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/backend connected/i)).toBeInTheDocument();
    });
  });

  it('handles backend connection failure gracefully', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));
    vi.stubGlobal('fetch', mockFetch);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/backend disconnected/i)).toBeInTheDocument();
      expect(screen.getByText(/backend connection note/i)).toBeInTheDocument();
    });
  });
});
