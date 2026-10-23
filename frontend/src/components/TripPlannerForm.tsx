import React from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  CircularProgress,
  ToggleButtonGroup,
  ToggleButton,
  FormControl,
  FormLabel,
  Box,
  Chip,
  Stack,
} from '@mui/material';
import NavigationIcon from '@mui/icons-material/Navigation';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { CheckpointInterval, RouteAnalyzeRequest } from '../types/api';
import { getUserTimeZone } from '../utils/timeFormat';
import { useTripForm, TRIP_PRESETS, TripPreset } from '../hooks/useTripForm';

interface TripPlannerFormProps {
  isLoading: boolean;
  onAnalyze: (request: RouteAnalyzeRequest) => Promise<void>;
}

export const TripPlannerForm: React.FC<TripPlannerFormProps> = ({ isLoading, onAnalyze }) => {
  const {
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
  } = useTripForm(onAnalyze);

  const localTimeZoneDisplay = getUserTimeZone();

  return (
    <Paper elevation={0} sx={{ p: 3, border: 1, borderColor: 'divider' }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          mb: 2,
          gap: 1,
        }}
      >
        <div>
          <Typography variant="h5" component="h2" color="primary" sx={{ fontWeight: 700 }}>
            Plan Weather-Aware Truck Route
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Enter real-time locations or select a sample freight corridor below
          </Typography>
        </div>

        <Button
          variant="outlined"
          size="small"
          color="secondary"
          startIcon={<RestartAltIcon />}
          onClick={handleClear}
          disabled={isLoading}
          aria-label="Clear form inputs"
        >
          Clear Form
        </Button>
      </Box>

      {/* Quick Example Presets */}
      <Box sx={{ mb: 2.5, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
          <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', mr: 0.5 }}>
            Quick Examples:
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.75 }}>
            {TRIP_PRESETS.map((preset: TripPreset) => (
              <Chip
                key={preset.id}
                label={preset.label}
                size="small"
                variant="outlined"
                clickable
                onClick={() => applyPreset(preset)}
                disabled={isLoading}
                color={
                  origin === preset.origin && destination === preset.destination
                    ? 'primary'
                    : 'default'
                }
                sx={{ fontSize: '0.75rem' }}
              />
            ))}
          </Stack>
        </Stack>
      </Box>

      <form onSubmit={handleSubmit} noValidate>
        <Grid container spacing={2.5}>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Origin"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g. Dallas, TX or 32.7767, -96.7970"
              error={Boolean(validationErrors.origin)}
              helperText={validationErrors.origin || 'City, State or "lat, lon" coordinates'}
              fullWidth
              required
              disabled={isLoading}
              inputProps={{ 'aria-label': 'Origin address or coordinates' }}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Destination"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Houston, TX or 29.7604, -95.3698"
              error={Boolean(validationErrors.destination)}
              helperText={validationErrors.destination || 'City, State or "lat, lon" coordinates'}
              fullWidth
              required
              disabled={isLoading}
              inputProps={{ 'aria-label': 'Destination address or coordinates' }}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Departure Date & Time"
              type="datetime-local"
              value={departureDateTime}
              onChange={(e) => setDepartureDateTime(e.target.value)}
              error={Boolean(validationErrors.departureDateTime)}
              helperText={
                validationErrors.departureDateTime ||
                `Assumed local timezone: ${localTimeZoneDisplay}`
              }
              fullWidth
              required
              disabled={isLoading}
              InputLabelProps={{ shrink: true }}
              inputProps={{ 'aria-label': 'Departure date and time in local timezone' }}
            />
          </Grid>

          <Grid item xs={12} sm={3}>
            <TextField
              label="Cargo Load Weight"
              type="number"
              value={loadWeightLb}
              onChange={(e) =>
                setLoadWeightLb(e.target.value === '' ? '' : Number(e.target.value))
              }
              placeholder="e.g. 42000"
              error={Boolean(validationErrors.loadWeightLb)}
              helperText={validationErrors.loadWeightLb || 'Gross cargo weight in pounds'}
              fullWidth
              required
              disabled={isLoading}
              inputProps={{ min: 1, step: 1000, 'aria-label': 'Cargo load weight in pounds' }}
            />
          </Grid>

          <Grid item xs={12} sm={3}>
            <FormControl fullWidth>
              <FormLabel sx={{ fontSize: '0.75rem', mb: 0.5 }}>Checkpoint Spacing</FormLabel>
              <ToggleButtonGroup
                value={checkpointInterval}
                exclusive
                onChange={(_, value) => {
                  if (value) setCheckpointInterval(value as CheckpointInterval);
                }}
                disabled={isLoading}
                fullWidth
                size="small"
                aria-label="Checkpoint interval in miles"
              >
                <ToggleButton value={10}>10 mi</ToggleButton>
                <ToggleButton value={25}>25 mi</ToggleButton>
                <ToggleButton value={50}>50 mi</ToggleButton>
              </ToggleButtonGroup>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={isLoading}
              startIcon={
                isLoading ? <CircularProgress size={20} color="inherit" /> : <NavigationIcon />
              }
              sx={{ px: 4, py: 1.2, fontWeight: 700 }}
            >
              {isLoading ? 'Calculating Corridors & Weather...' : 'Analyze Driving Corridors'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};
