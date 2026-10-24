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
  InputAdornment,
} from '@mui/material';
import NavigationIcon from '@mui/icons-material/Navigation';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import ScaleIcon from '@mui/icons-material/Scale';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import RouteIcon from '@mui/icons-material/Route';
import { CheckpointInterval, RouteAnalyzeRequest } from '../../types/api';
import { getUserTimeZone } from '../../utils/timeFormat';
import { useTripForm, TRIP_PRESETS, TripPreset } from '../../hooks/useTripForm';

export interface TripPlannerFormProps {
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
    <Paper
      elevation={0}
      sx={{
        p: { xs: 2.5, sm: 3 },
        border: '1px solid #e2e8f0',
        borderRadius: 3,
        background: '#ffffff',
        boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02)',
      }}
    >
      {/* Header and Reset Action */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          mb: 2,
          gap: 1.5,
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 36,
              height: 36,
              borderRadius: 2,
              bgcolor: 'rgba(30, 58, 138, 0.08)',
              color: 'primary.main',
            }}
          >
            <RouteIcon sx={{ fontSize: 20 }} />
          </Box>
          <Box>
            <Typography variant="h6" component="h2" color="text.primary" sx={{ fontWeight: 800 }}>
              Plan Weather-Aware Truck Route
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Enter real-time locations or select a sample freight corridor below
            </Typography>
          </Box>
        </Stack>

        <Button
          variant="outlined"
          size="small"
          startIcon={<RestartAltIcon sx={{ fontSize: 16 }} />}
          onClick={handleClear}
          disabled={isLoading}
          aria-label="Clear form inputs"
          sx={{
            borderColor: '#e2e8f0',
            color: 'text.secondary',
            '&:hover': {
              borderColor: '#cbd5e1',
              bgcolor: '#f8fafc',
            },
          }}
        >
          Clear Form
        </Button>
      </Box>

      {/* Modern Quick Presets Bar */}
      <Box
        sx={{
          mb: 3,
          p: 1.5,
          bgcolor: '#f8fafc',
          borderRadius: 2,
          border: '1px solid #f1f5f9',
        }}
      >
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 700,
              color: 'text.secondary',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.7rem',
              minWidth: 100,
            }}
          >
            Quick Examples:
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.75 }}>
            {TRIP_PRESETS.map((preset: TripPreset) => {
              const isSelected = origin === preset.origin && destination === preset.destination;
              return (
                <Chip
                  key={preset.id}
                  label={preset.label}
                  size="small"
                  variant={isSelected ? 'filled' : 'outlined'}
                  clickable
                  onClick={() => applyPreset(preset)}
                  disabled={isLoading}
                  color={isSelected ? 'primary' : 'default'}
                  sx={{
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    bgcolor: isSelected ? 'primary.main' : '#ffffff',
                    borderColor: isSelected ? 'primary.main' : '#e2e8f0',
                    transition: 'all 0.15s ease',
                    '&:hover': {
                      borderColor: 'primary.light',
                      transform: 'translateY(-1px)',
                    },
                  }}
                />
              );
            })}
          </Stack>
        </Stack>
      </Box>

      {/* Main Trip Planning Form */}
      <form onSubmit={handleSubmit} noValidate>
        <Grid container spacing={2}>
          {/* Origin Input */}
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
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <MyLocationIcon sx={{ color: '#10b981', fontSize: 20 }} />
                  </InputAdornment>
                ),
              }}
              inputProps={{ 'aria-label': 'Origin address or coordinates' }}
            />
          </Grid>

          {/* Destination Input */}
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
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LocationOnIcon sx={{ color: '#ef4444', fontSize: 20 }} />
                  </InputAdornment>
                ),
              }}
              inputProps={{ 'aria-label': 'Destination address or coordinates' }}
            />
          </Grid>

          {/* Departure Date & Time */}
          <Grid item xs={12} sm={5}>
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
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <AccessTimeIcon sx={{ color: 'text.secondary', fontSize: 18 }} />
                  </InputAdornment>
                ),
              }}
              inputProps={{ 'aria-label': 'Departure date and time in local timezone' }}
            />
          </Grid>

          {/* Load Weight */}
          <Grid item xs={12} sm={3.5}>
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
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <ScaleIcon sx={{ color: 'text.secondary', fontSize: 18 }} />
                  </InputAdornment>
                ),
                endAdornment: <InputAdornment position="end">lbs</InputAdornment>,
              }}
              inputProps={{ min: 1, step: 1000, 'aria-label': 'Cargo load weight in pounds' }}
            />
          </Grid>

          {/* Checkpoint Spacing */}
          <Grid item xs={12} sm={3.5}>
            <FormControl fullWidth>
              <FormLabel
                sx={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                  mb: 0.5,
                }}
              >
                Checkpoint Spacing
              </FormLabel>
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
                sx={{
                  bgcolor: '#f8fafc',
                  '& .MuiToggleButton-root': {
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    py: 1,
                    borderColor: '#e2e8f0',
                    '&.Mui-selected': {
                      bgcolor: 'primary.main',
                      color: '#ffffff',
                      '&:hover': {
                        bgcolor: 'primary.dark',
                      },
                    },
                  },
                }}
              >
                <ToggleButton value={10}>10 mi</ToggleButton>
                <ToggleButton value={25}>25 mi</ToggleButton>
                <ToggleButton value={50}>50 mi</ToggleButton>
              </ToggleButtonGroup>
            </FormControl>
          </Grid>

          {/* Submit Action Button */}
          <Grid item xs={12} sx={{ mt: 1 }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={isLoading}
              startIcon={
                isLoading ? (
                  <CircularProgress size={22} color="inherit" />
                ) : (
                  <NavigationIcon sx={{ transform: 'rotate(45deg)' }} />
                )
              }
              fullWidth
              sx={{
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 800,
                letterSpacing: '0.02em',
                borderRadius: 2.5,
                boxShadow: '0 4px 14px 0 rgba(37, 99, 235, 0.35)',
              }}
            >
              {isLoading
                ? 'Synthesizing Live Routes & Micro-Weather...'
                : 'Analyze Driving Corridors'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default TripPlannerForm;
