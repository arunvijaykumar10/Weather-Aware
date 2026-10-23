import { useState, useCallback } from 'react';
import { CheckpointInterval, RouteAnalyzeRequest } from '../types/api';
import { convertLocalToIsoWithOffset } from '../utils/timeFormat';

export interface TripPreset {
  id: string;
  label: string;
  origin: string;
  destination: string;
  loadWeightLb: number;
  checkpointInterval: CheckpointInterval;
}

export const TRIP_PRESETS: TripPreset[] = [
  {
    id: 'denver-slc',
    label: 'Denver, CO → Salt Lake City, UT (42k lbs)',
    origin: 'Denver, CO',
    destination: 'Salt Lake City, UT',
    loadWeightLb: 42000,
    checkpointInterval: 25,
  },
  {
    id: 'dallas-houston',
    label: 'Dallas, TX → Houston, TX (35k lbs)',
    origin: 'Dallas, TX',
    destination: 'Houston, TX',
    loadWeightLb: 35000,
    checkpointInterval: 25,
  },
  {
    id: 'chicago-detroit',
    label: 'Chicago, IL → Detroit, MI (48k lbs)',
    origin: 'Chicago, IL',
    destination: 'Detroit, MI',
    loadWeightLb: 48000,
    checkpointInterval: 25,
  },
];

const getDefaultDepartureDateTime = (): string => {
  const nextHourDate = new Date(Date.now() + 3600 * 1000);
  nextHourDate.setMinutes(0, 0, 0);
  // Pad local datetime for datetime-local input YYYY-MM-DDTHH:mm
  const localYear = nextHourDate.getFullYear();
  const localMonth = String(nextHourDate.getMonth() + 1).padStart(2, '0');
  const localDay = String(nextHourDate.getDate()).padStart(2, '0');
  const localHours = String(nextHourDate.getHours()).padStart(2, '0');
  const localMinutes = String(nextHourDate.getMinutes()).padStart(2, '0');
  return `${localYear}-${localMonth}-${localDay}T${localHours}:${localMinutes}`;
};

export const useTripForm = (onAnalyze: (request: RouteAnalyzeRequest) => Promise<void>) => {
  const [origin, setOrigin] = useState<string>('');
  const [destination, setDestination] = useState<string>('');
  const [departureDateTime, setDepartureDateTime] = useState<string>(getDefaultDepartureDateTime);
  const [loadWeightLb, setLoadWeightLb] = useState<number | ''>('');
  const [checkpointInterval, setCheckpointInterval] = useState<CheckpointInterval>(25);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!origin.trim()) errors.origin = 'Origin address or coordinates are required.';
    if (!destination.trim()) errors.destination = 'Destination is required.';
    if (!departureDateTime) errors.departureDateTime = 'Departure date & time is required.';
    if (loadWeightLb === '' || Number(loadWeightLb) <= 0) {
      errors.loadWeightLb = 'Load weight must be a positive number of pounds (> 0).';
    }
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const applyPreset = useCallback((preset: TripPreset) => {
    setOrigin(preset.origin);
    setDestination(preset.destination);
    setLoadWeightLb(preset.loadWeightLb);
    setCheckpointInterval(preset.checkpointInterval);
    setValidationErrors({});
  }, []);

  const handleClear = useCallback(() => {
    setOrigin('');
    setDestination('');
    setDepartureDateTime(getDefaultDepartureDateTime());
    setLoadWeightLb('');
    setCheckpointInterval(25);
    setValidationErrors({});
  }, []);

  const handleSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      if (!validate()) return;

      try {
        const departureIsoUtc = convertLocalToIsoWithOffset(departureDateTime);
        await onAnalyze({
          origin: origin.trim(),
          destination: destination.trim(),
          departure_time: departureIsoUtc,
          load_weight_lb: Number(loadWeightLb),
          checkpoint_interval_miles: checkpointInterval,
        });
      } catch {
        // Handled by parent onAnalyze error state
      }
    },
    [origin, destination, departureDateTime, loadWeightLb, checkpointInterval, onAnalyze]
  );

  return {
    origin,
    setOrigin,
    destination,
    setDestination,
    departureDateTime,
    setDepartureDateTime,
    loadWeightLb,
    setLoadWeightLb,
    checkpointInterval,
    setCheckpointInterval,
    validationErrors,
    applyPreset,
    handleClear,
    handleSubmit,
  };
};
