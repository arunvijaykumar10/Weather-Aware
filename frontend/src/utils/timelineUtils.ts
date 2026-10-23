import { RiskLevel } from '../types/api';

export const MIN_TIMELINE_HOUR = 0;
export const MAX_TIMELINE_HOUR = 48;

/**
 * Clamps a timeline hour offset strictly within [0, 48].
 */
export const clampHourOffset = (offset: number): number => {
  if (isNaN(offset)) return MIN_TIMELINE_HOUR;
  return Math.max(MIN_TIMELINE_HOUR, Math.min(Math.round(offset), MAX_TIMELINE_HOUR));
};

/**
 * Computes and formats the date and time for a given integer hour offset from departure.
 */
export const formatTimelineTimestamp = (
  departureIso: string,
  offsetHours: number,
  timeZone?: string
): string => {
  const departureDate = new Date(departureIso);
  if (isNaN(departureDate.getTime())) {
    return 'Invalid Departure Time';
  }

  const targetDate = new Date(departureDate.getTime() + clampHourOffset(offsetHours) * 3600 * 1000);
  const targetTz = timeZone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

  const formatter = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZone: targetTz,
    timeZoneName: 'short',
  });

  return formatter.format(targetDate);
};

/**
 * Formats forecast age in minutes/seconds with timestamp summary.
 */
export const formatForecastFreshness = (fetchedAtIso: string, ageSeconds: number): string => {
  const date = new Date(fetchedAtIso);
  const timeStr = isNaN(date.getTime())
    ? 'Unknown'
    : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });

  if (ageSeconds < 60) {
    return `Fetched just now (${timeStr})`;
  }
  const minutes = Math.floor(ageSeconds / 60);
  if (minutes < 60) {
    return `Fetched ${minutes}m ago (${timeStr})`;
  }
  const hours = Math.floor(minutes / 60);
  return `Fetched ${hours}h ${minutes % 60}m ago (${timeStr})`;
};

/**
 * Risk level to hex color.
 */
export const RISK_COLOR_MAP: Record<RiskLevel, string> = {
  low: '#16a34a',
  moderate: '#d97706',
  high: '#ea580c',
  severe: '#dc2626',
  no_travel: '#7f1d1d',
  unknown: '#9ca3af',
};

/**
 * Map numeric risk score (0-4) to translucent RGBA string for heatmap rendering.
 */
export const getNumericRiskColor = (score: number | null, alpha = 0.55): string => {
  switch (score) {
    case 0:
      return `rgba(22, 163, 74, ${alpha})`; // Low - Green
    case 1:
      return `rgba(217, 119, 6, ${alpha})`; // Moderate - Amber
    case 2:
      return `rgba(234, 88, 12, ${alpha})`; // High - Orange
    case 3:
      return `rgba(220, 38, 38, ${alpha})`; // Severe - Red
    case 4:
      return `rgba(127, 29, 29, ${alpha})`; // No Travel - Dark Maroon
    default:
      return `rgba(156, 163, 175, ${alpha * 0.4})`; // Unknown / Unverified - Grey
  }
};
