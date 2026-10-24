import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  Slider,
  Stack,
  FormControlLabel,
  Switch,
  Chip,
  Button,
  ButtonGroup,
  Alert,
} from '@mui/material';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LayersIcon from '@mui/icons-material/Layers';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import { formatTimelineTimestamp, formatForecastFreshness } from '../../utils/timelineUtils';

export interface ForecastTimelineSliderProps {
  selectedHour: number;
  onHourChange: (hour: number) => void;
  departureTime: string;
  forecastFetchedAt?: string;
  forecastAgeSeconds?: number;
  showHeatmap: boolean;
  onToggleHeatmap: (show: boolean) => void;
  heatmapOpacity: number;
  onChangeOpacity: (opacity: number) => void;
  isLoadingTimeline?: boolean;
}

const QUICK_HOURS = [0, 6, 12, 24, 48];

export const ForecastTimelineSlider: React.FC<ForecastTimelineSliderProps> = ({
  selectedHour,
  onHourChange,
  departureTime,
  forecastFetchedAt,
  forecastAgeSeconds,
  showHeatmap,
  onToggleHeatmap,
  heatmapOpacity,
  onChangeOpacity,
  isLoadingTimeline = false,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;
    if (isPlaying) {
      timer = setInterval(() => {
        onHourChange((selectedHour + 1) % 49);
      }, 500);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, selectedHour, onHourChange]);

  const formattedTime = formatTimelineTimestamp(departureTime, selectedHour);
  const freshnessText =
    forecastFetchedAt && forecastAgeSeconds !== undefined
      ? formatForecastFreshness(forecastFetchedAt, forecastAgeSeconds)
      : null;

  return (
    <Paper
      elevation={0}
      sx={{
        p: { xs: 2, sm: 2.5 },
        mb: 2,
        border: '1px solid #e2e8f0',
        borderRadius: 3,
        bgcolor: '#ffffff',
        boxShadow: '0 4px 16px -2px rgba(15, 23, 42, 0.05)',
      }}
    >
      <Stack spacing={2}>
        {/* Header with Title and Current Scrubber Time */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={1}
        >
          <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" sx={{ gap: 1 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 32,
                height: 32,
                borderRadius: 1.5,
                bgcolor: 'rgba(37, 99, 235, 0.08)',
                color: 'primary.main',
                flexShrink: 0,
              }}
            >
              <AccessTimeIcon sx={{ fontSize: 18 }} />
            </Box>
            <Box>
              <Typography variant="subtitle2" fontWeight={800} sx={{ color: 'text.primary', fontSize: { xs: '0.85rem', sm: '0.9rem' } }}>
                Corridor Forecast Timeline (0h to 48h)
              </Typography>
            </Box>
            <Chip
              label={`+${selectedHour}h: ${formattedTime}`}
              color="primary"
              size="small"
              sx={{
                fontWeight: 700,
                fontSize: '0.75rem',
                bgcolor: 'primary.main',
                color: '#ffffff',
              }}
            />
          </Stack>

          {freshnessText && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500, fontSize: '0.72rem' }}>
              {freshnessText}
            </Typography>
          )}
        </Stack>

        {/* Timeline Range Slider */}
        <Box sx={{ px: 1.5 }}>
          <Slider
            value={selectedHour}
            min={0}
            max={48}
            step={1}
            disabled={isLoadingTimeline}
            onChange={(_, val) => {
              if (isPlaying) setIsPlaying(false);
              onHourChange(val as number);
            }}
            aria-label="Corridor Forecast Hour Offset Slider"
            valueLabelDisplay="auto"
            valueLabelFormat={(val) => `+${val}h`}
            marks={[
              { value: 0, label: '0h (Dep)' },
              { value: 12, label: '+12h' },
              { value: 24, label: '+24h' },
              { value: 36, label: '+36h' },
              { value: 48, label: '+48h' },
            ]}
            sx={{
              height: 6,
              '& .MuiSlider-track': {
                background: 'linear-gradient(90deg, #2563eb 0%, #06b6d4 100%)',
                border: 'none',
              },
              '& .MuiSlider-thumb': {
                width: 18,
                height: 18,
                bgcolor: '#ffffff',
                border: '3px solid #2563eb',
                boxShadow: '0 2px 8px rgba(37, 99, 235, 0.4)',
                '&:hover, &.Mui-focusVisible': {
                  boxShadow: '0 0 0 8px rgba(37, 99, 235, 0.16)',
                },
              },
              '& .MuiSlider-markLabel': {
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'text.secondary',
              },
            }}
          />
        </Box>

        {/* Controls: Play/Pause, Quick Jumps, and Heatmap Layer Switch */}
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'stretch', md: 'center' }}
          spacing={1.5}
          sx={{ pt: 0.5 }}
        >
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ gap: 1 }}>
            {/* Play/Pause Button */}
            <Button
              size="small"
              variant={isPlaying ? 'contained' : 'outlined'}
              color={isPlaying ? 'secondary' : 'primary'}
              startIcon={isPlaying ? <PauseIcon sx={{ fontSize: 16 }} /> : <PlayArrowIcon sx={{ fontSize: 16 }} />}
              onClick={() => setIsPlaying(!isPlaying)}
              sx={{
                fontWeight: 700,
                fontSize: '0.75rem',
                px: 1.5,
                borderRadius: 2,
              }}
            >
              {isPlaying ? 'Pause' : 'Play 48h Radar'}
            </Button>

            {/* Quick Jumps */}
            <ButtonGroup size="small" variant="outlined" aria-label="Quick Jump Timeline Hours" sx={{ borderRadius: 2 }}>
              {QUICK_HOURS.map((h) => (
                <Button
                  key={h}
                  variant={selectedHour === h ? 'contained' : 'outlined'}
                  onClick={() => {
                    if (isPlaying) setIsPlaying(false);
                    onHourChange(h);
                  }}
                  sx={{
                    px: { xs: 0.85, sm: 1.25 },
                    py: 0.5,
                    fontSize: { xs: '0.7rem', sm: '0.75rem' },
                    fontWeight: 700,
                  }}
                >
                  +{h}h
                </Button>
              ))}
            </ButtonGroup>
          </Stack>

          {/* Layer and Opacity Controls */}
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" sx={{ gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={showHeatmap}
                  onChange={(e) => onToggleHeatmap(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Typography variant="caption" fontWeight={700} sx={{ color: 'text.primary', fontSize: '0.75rem' }}>
                  Heatmap Overlay
                </Typography>
              }
              sx={{ m: 0 }}
            />

            {showHeatmap && (
              <Stack direction="row" spacing={1} alignItems="center" sx={{ width: { xs: 110, sm: 130 } }}>
                <LayersIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Slider
                  size="small"
                  value={Math.round(heatmapOpacity * 100)}
                  min={10}
                  max={100}
                  step={5}
                  onChange={(_, val) => onChangeOpacity((val as number) / 100)}
                  aria-label="Heatmap Opacity"
                  valueLabelDisplay="auto"
                  valueLabelFormat={(val) => `${val}%`}
                />
              </Stack>
            )}
          </Stack>
        </Stack>

        <Alert
          severity="info"
          icon={<InfoOutlinedIcon fontSize="small" />}
          sx={{
            py: 0.5,
            px: 1.5,
            fontSize: '0.78rem',
            borderRadius: 2,
            bgcolor: 'rgba(2, 132, 199, 0.05)',
            border: '1px solid rgba(2, 132, 199, 0.15)',
            '& .MuiAlert-message': { p: 0.5 },
          }}
        >
          <strong>Exploration Mode:</strong> The slider lets you preview forecasted conditions at
          any departure offset. Route rankings and safety recommendations remain fixed based on
          predicted arrival times (ETA-matched weather).
        </Alert>
      </Stack>
    </Paper>
  );
};

export default ForecastTimelineSlider;
