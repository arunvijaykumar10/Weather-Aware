import { describe, it, expect } from 'vitest';
import {
  clampHourOffset,
  formatTimelineTimestamp,
  formatForecastFreshness,
  getNumericRiskColor,
  RISK_COLOR_MAP,
} from './timelineUtils';

describe('timelineUtils', () => {
  describe('clampHourOffset', () => {
    it('clamps negative hours to 0', () => {
      expect(clampHourOffset(-1)).toBe(0);
      expect(clampHourOffset(-24)).toBe(0);
    });

    it('clamps hours greater than 48 to 48', () => {
      expect(clampHourOffset(49)).toBe(48);
      expect(clampHourOffset(100)).toBe(48);
    });

    it('preserves valid hour bounds between 0 and 48', () => {
      expect(clampHourOffset(0)).toBe(0);
      expect(clampHourOffset(48)).toBe(48);
      expect(clampHourOffset(24)).toBe(24);
      expect(clampHourOffset(12.4)).toBe(12);
    });

    it('handles NaN gracefully defaulting to 0', () => {
      expect(clampHourOffset(NaN)).toBe(0);
    });
  });

  describe('formatTimelineTimestamp', () => {
    const baseDeparture = '2026-10-24T14:00:00Z';

    it('correctly converts 0h offset to departure timestamp in UTC', () => {
      const formatted = formatTimelineTimestamp(baseDeparture, 0, 'UTC');
      expect(formatted).toContain('Oct 24');
      expect(formatted).toContain('2:00 PM');
      expect(formatted).toContain('UTC');
    });

    it('correctly computes +6h offset', () => {
      const formatted = formatTimelineTimestamp(baseDeparture, 6, 'UTC');
      expect(formatted).toContain('Oct 24');
      expect(formatted).toContain('8:00 PM');
      expect(formatted).toContain('UTC');
    });

    it('correctly computes +48h offset spanning two days', () => {
      const formatted = formatTimelineTimestamp(baseDeparture, 48, 'UTC');
      expect(formatted).toContain('Oct 26');
      expect(formatted).toContain('2:00 PM');
      expect(formatted).toContain('UTC');
    });

    it('returns error string for invalid departure timestamp', () => {
      expect(formatTimelineTimestamp('invalid-date', 0)).toBe('Invalid Departure Time');
    });
  });

  describe('formatForecastFreshness', () => {
    it('formats recent age under a minute', () => {
      const text = formatForecastFreshness('2026-10-24T14:00:00Z', 30);
      expect(text).toContain('Fetched just now');
    });

    it('formats minutes elapsed', () => {
      const text = formatForecastFreshness('2026-10-24T14:00:00Z', 300);
      expect(text).toContain('Fetched 5m ago');
    });

    it('formats hours elapsed', () => {
      const text = formatForecastFreshness('2026-10-24T14:00:00Z', 7200);
      expect(text).toContain('Fetched 2h 0m ago');
    });
  });

  describe('getNumericRiskColor and missing values', () => {
    it('returns appropriate color per numeric risk score', () => {
      expect(getNumericRiskColor(0)).toContain('22, 163, 74'); // Low
      expect(getNumericRiskColor(1)).toContain('217, 119, 6'); // Moderate
      expect(getNumericRiskColor(2)).toContain('234, 88, 12'); // High
      expect(getNumericRiskColor(3)).toContain('220, 38, 38'); // Severe
      expect(getNumericRiskColor(4)).toContain('127, 29, 29'); // No Travel
    });

    it('handles missing/null numeric score as grey/unknown', () => {
      expect(getNumericRiskColor(null)).toContain('156, 163, 175');
      expect(RISK_COLOR_MAP.unknown).toBe('#9ca3af');
    });
  });
});
