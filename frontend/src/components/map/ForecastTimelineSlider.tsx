import React from 'react';
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
import { formatTimelineTimestamp, formatForecastFreshness } from '../../utils/timelineUtils';

interface ForecastTimelineSliderProps {
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
  const formattedTime = formatTimelineTimestamp(departureTime, selectedHour);
  const freshnessText =
    forecastFetchedAt && forecastAgeSeconds !== undefined
      ? formatForecastFreshness(forecastFetchedAt, forecastAgeSeconds)
      : null;

  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        mb: 2,
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        bgcolor: '#f8fafc',
      }}
    >
      <Stack spacing={1.5}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={1}
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <AccessTimeIcon color="primary" fontSize="small" />
            <Typography variant="subtitle2" fontWeight={700}>
              Corridor Forecast Timeline (0h to 48h)
            </Typography>
            <Chip
              label={`+${selectedHour}h: ${formattedTime}`}
              color="primary"
              size="small"
              sx={{ fontWeight: 600 }}
            />
          </Stack>

          {freshnessText && (
            <Typography variant="caption" color="text.secondary">
              {freshnessText}
            </Typography>
          )}
        </Stack>

        <Box sx={{ px: 1 }}>
          <Slider
            value={selectedHour}
            min={0}
            max={48}
            step={1}
            disabled={isLoadingTimeline}
            onChange={(_, val) => onHourChange(val as number)}
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
              '& .MuiSlider-markLabel': { fontSize: '0.75rem' },
            }}
          />
        </Box>

        <Stack
          direction={{ xs: 'column', md: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'stretch', md: 'center' }}
          spacing={1}
        >
          <ButtonGroup size="small" variant="outlined" aria-label="Quick Jump Timeline Hours">
            {QUICK_HOURS.map((h) => (
              <Button
                key={h}
                variant={selectedHour === h ? 'contained' : 'outlined'}
                onClick={() => onHourChange(h)}
                sx={{ px: 1.5, py: 0.25, fontSize: '0.75rem' }}
              >
                +{h}h
              </Button>
            ))}
          </ButtonGroup>

          <Stack direction="row" spacing={2} alignItems="center">
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
                <Typography variant="caption" fontWeight={600}>
                  Heatmap Overlay
                </Typography>
              }
              sx={{ m: 0 }}
            />

            {showHeatmap && (
              <Stack direction="row" spacing={1} alignItems="center" sx={{ width: 140 }}>
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
          sx={{ py: 0.5, px: 1.5, fontSize: '0.78rem', '& .MuiAlert-message': { p: 0.5 } }}
        >
          <strong>Exploration Mode:</strong> The slider lets you preview forecasted conditions at
          any departure offset. Route rankings and safety recommendations remain fixed based on
          predicted arrival times (ETA-matched weather).
        </Alert>
      </Stack>
    </Paper>
  );
};
