import React from 'react';
import { CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { Checkpoint, HourlyTimelineEntry } from '../../types/api';
import { RISK_STYLE_MAP } from './mapConstants';
import { formatEtaTimestamp } from '../../utils/timeFormat';

interface CheckpointMarkerProps {
  checkpoint: Checkpoint;
  isSelected: boolean;
  hourlyEntry?: HourlyTimelineEntry | null;
  onSelectCheckpoint?: (checkpointId: string) => void;
}

export const CheckpointMarker: React.FC<CheckpointMarkerProps> = ({
  checkpoint,
  isSelected,
  hourlyEntry,
  onSelectCheckpoint,
}) => {
  const isUnavailable =
    hourlyEntry?.availability === 'unavailable' || hourlyEntry?.availability === 'beyond_forecast';

  const riskLevel = isUnavailable
    ? 'unknown'
    : hourlyEntry?.load_adjusted_risk || checkpoint.load_adjusted_risk;

  const riskConfig = isUnavailable
    ? {
        color: '#9ca3af',
        label: hourlyEntry?.availability === 'beyond_forecast' ? 'Beyond Forecast' : 'Forecast Unavailable',
        symbol: '❓',
      }
    : RISK_STYLE_MAP[riskLevel] || RISK_STYLE_MAP.unknown;

  const radius = isSelected ? 9 : 6;

  // Displayed weather values (hourly timeline overrides baseline when available)
  const displayWind = hourlyEntry
    ? hourlyEntry.wind_speed_mph
    : checkpoint.weather.wind_speed_mph;
  const displayRain = hourlyEntry
    ? hourlyEntry.rain_in_per_hr
    : checkpoint.weather.rain_in_per_hr;
  const displaySnow = hourlyEntry
    ? hourlyEntry.snow_in_per_hr
    : checkpoint.weather.snow_in_per_hr;
  const displayTime = hourlyEntry
    ? hourlyEntry.forecast_timestamp
    : checkpoint.forecast_timestamp;

  return (
    <CircleMarker
      center={[checkpoint.lat, checkpoint.lon]}
      radius={radius}
      pathOptions={{
        color: isUnavailable ? '#4b5563' : '#ffffff',
        weight: 2,
        fillColor: riskConfig.color,
        fillOpacity: isUnavailable ? 0.6 : 0.95,
        dashArray: isUnavailable ? '3, 3' : undefined,
      }}
      eventHandlers={{
        click: () => onSelectCheckpoint?.(checkpoint.checkpoint_id),
      }}
    >
      <Tooltip direction="top" offset={[0, -6]}>
        <strong>{checkpoint.checkpoint_id}</strong> (
        {checkpoint.cumulative_distance_miles.toFixed(1)} mi):{' '}
        <span style={{ color: riskConfig.color, fontWeight: 700 }}>
          {riskConfig.symbol} {riskConfig.label}
        </span>
      </Tooltip>
      <Popup>
        <div style={{ minWidth: 220, fontSize: '0.85rem' }}>
          <h4 style={{ margin: '0 0 6px 0', color: riskConfig.color }}>
            {riskConfig.symbol} {checkpoint.checkpoint_id} ({riskConfig.label})
          </h4>

          {isUnavailable ? (
            <p style={{ margin: '4px 0', color: '#6b7280', fontSize: '0.8rem' }}>
              Weather forecast is {riskConfig.label.toLowerCase()} for this checkpoint at the selected
              hour offset.
            </p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <tbody>
                <tr>
                  <td>
                    <strong>Distance:</strong>
                  </td>
                  <td>{checkpoint.cumulative_distance_miles.toFixed(1)} mi</td>
                </tr>
                <tr>
                  <td>
                    <strong>ETA:</strong>
                  </td>
                  <td>{formatEtaTimestamp(checkpoint.eta)}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Forecast Time:</strong>
                  </td>
                  <td>{displayTime ? formatEtaTimestamp(displayTime) : 'Unavailable'}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Wind Speed:</strong>
                  </td>
                  <td>{displayWind !== null && displayWind !== undefined ? `${displayWind} mph` : 'N/A'}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Rain:</strong>
                  </td>
                  <td>{displayRain !== null && displayRain !== undefined ? `${displayRain} in/hr` : 'N/A'}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Snow:</strong>
                  </td>
                  <td>{displaySnow !== null && displaySnow !== undefined ? `${displaySnow} in/hr` : 'N/A'}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Risk:</strong>
                  </td>
                  <td style={{ color: riskConfig.color, fontWeight: 700 }}>
                    {riskConfig.symbol} {riskConfig.label}
                  </td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      </Popup>
    </CircleMarker>
  );
};
