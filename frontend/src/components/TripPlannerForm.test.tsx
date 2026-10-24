import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TripPlannerForm } from './TripPlannerForm';

describe('TripPlannerForm component', () => {
  it('renders all required form inputs and controls with empty initial values', () => {
    render(<TripPlannerForm isLoading={false} onAnalyze={vi.fn()} />);

    expect(
      screen.getByRole('heading', { name: /dispatch & route configuration/i })
    ).toBeInTheDocument();
    const originInput = screen.getByLabelText(/origin address/i) as HTMLInputElement;
    const destInput = screen.getByLabelText(/destination address/i) as HTMLInputElement;
    const weightInput = screen.getByLabelText(/cargo load weight/i) as HTMLInputElement;

    expect(originInput.value).toBe('');
    expect(destInput.value).toBe('');
    expect(weightInput.value).toBe('');

    expect(screen.getByLabelText(/departure date and time/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze driving corridors/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clear form inputs/i })).toBeInTheDocument();
  });

  it('populates fields when a quick preset chip is clicked', () => {
    render(<TripPlannerForm isLoading={false} onAnalyze={vi.fn()} />);

    const presetChip = screen.getByText(/Dallas, TX → Houston, TX/i);
    fireEvent.click(presetChip);

    const originInput = screen.getByLabelText(/origin address/i) as HTMLInputElement;
    const destInput = screen.getByLabelText(/destination address/i) as HTMLInputElement;
    const weightInput = screen.getByLabelText(/cargo load weight/i) as HTMLInputElement;

    expect(originInput.value).toBe('Dallas, TX');
    expect(destInput.value).toBe('Houston, TX');
    expect(weightInput.value).toBe('35000');
  });

  it('clears form inputs when Clear Form button is clicked', () => {
    render(<TripPlannerForm isLoading={false} onAnalyze={vi.fn()} />);

    // First populate via preset
    const presetChip = screen.getByText(/Dallas, TX → Houston, TX/i);
    fireEvent.click(presetChip);

    // Then clear
    const clearBtn = screen.getByRole('button', { name: /clear form inputs/i });
    fireEvent.click(clearBtn);

    const originInput = screen.getByLabelText(/origin address/i) as HTMLInputElement;
    const destInput = screen.getByLabelText(/destination address/i) as HTMLInputElement;
    const weightInput = screen.getByLabelText(/cargo load weight/i) as HTMLInputElement;

    expect(originInput.value).toBe('');
    expect(destInput.value).toBe('');
    expect(weightInput.value).toBe('');
  });

  it('validates empty origin and destination', async () => {
    const mockOnAnalyze = vi.fn();
    render(<TripPlannerForm isLoading={false} onAnalyze={mockOnAnalyze} />);

    const submitBtn = screen.getByRole('button', {
      name: /analyze driving corridors/i,
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/origin address or coordinates are required/i)).toBeInTheDocument();
    });
    expect(mockOnAnalyze).not.toHaveBeenCalled();
  });

  it('validates zero or negative load weight', async () => {
    const mockOnAnalyze = vi.fn();
    render(<TripPlannerForm isLoading={false} onAnalyze={mockOnAnalyze} />);

    const originInput = screen.getByLabelText(/origin address/i);
    fireEvent.change(originInput, { target: { value: 'Denver, CO' } });

    const destInput = screen.getByLabelText(/destination address/i);
    fireEvent.change(destInput, { target: { value: 'Salt Lake City, UT' } });

    const weightInput = screen.getByLabelText(/cargo load weight/i);
    fireEvent.change(weightInput, { target: { value: '-500' } });

    const submitBtn = screen.getByRole('button', {
      name: /analyze driving corridors/i,
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/load weight must be a positive number/i)).toBeInTheDocument();
    });
    expect(mockOnAnalyze).not.toHaveBeenCalled();
  });

  it('submits valid form data converted to ISO 8601 string with offset', async () => {
    const mockOnAnalyze = vi.fn().mockResolvedValue(undefined);
    render(<TripPlannerForm isLoading={false} onAnalyze={mockOnAnalyze} />);

    const originInput = screen.getByLabelText(/origin address/i);
    fireEvent.change(originInput, { target: { value: 'Chicago, IL' } });

    const destInput = screen.getByLabelText(/destination address/i);
    fireEvent.change(destInput, { target: { value: 'Detroit, MI' } });

    const weightInput = screen.getByLabelText(/cargo load weight/i);
    fireEvent.change(weightInput, { target: { value: '45000' } });

    const dateInput = screen.getByLabelText(/departure date and time/i);
    fireEvent.change(dateInput, { target: { value: '2026-10-23T14:30' } });

    const submitBtn = screen.getByRole('button', {
      name: /analyze driving corridors/i,
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockOnAnalyze).toHaveBeenCalledTimes(1);
    });

    const callPayload = mockOnAnalyze.mock.calls[0][0];
    expect(callPayload.origin).toBe('Chicago, IL');
    expect(callPayload.destination).toBe('Detroit, MI');
    expect(callPayload.load_weight_lb).toBe(45000);
    expect(callPayload.checkpoint_interval_miles).toBe(25);
    // Departure time must be timezone-aware (ISO format with Z or offset)
    expect(callPayload.departure_time).toMatch(
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/
    );
  });
});
