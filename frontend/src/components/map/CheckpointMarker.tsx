import React from 'react';
import { CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { Checkpoint } from '../../types/api';
import { RISK_STYLE_MAP } from './mapConstants';
import { formatEtaTimestamp } from '../../utils/timeFormat';

interface CheckpointMarkerProps {
  checkpoint: Checkpoint;
  isSelected: boolean;
  onSelectCheckpoint?: (checkpointId: string) => void;
}

export const CheckpointMarker: React.FC<CheckpointMarkerProps> = ({
  checkpoint,
  isSelected,
  onSelectCheckpoint,
}) => {
  const riskConfig = RISK_STYLE_MAP[checkpoint.load_adjusted_risk] || RISK_STYLE_MAP.unknown;
  const radius = isSelected ? 9 : 6;

  return (
    <CircleMarker
      center={[checkpoint.lat, checkpoint.lon]}
      radius={radius}
      pathOptions={{
        color: '#ffffff',
        weight: 2,
        fillColor: riskConfig.color,
        fillOpacity: 0.95,
      }}
      eventHandlers={{
        click: () => onSelectCheckpoint?.(checkpoint.checkpoint_id),
      }}
    >
      <Tooltip direction="top" offset={[0, -6]}>
        <strong>{checkpoint.checkpoint_id}</strong> (
        {checkpoint.cumulative_distance_miles.toFixed(1)} mi):{' '}
        <span style={{ color: riskConfig.color }}>
          {riskConfig.symbol} {riskConfig.label}
        </span>
      </Tooltip>
      <Popup>
        <div style={{ minWidth: 220, fontSize: '0.85rem' }}>
          <h4 style={{ margin: '0 0 6px 0', color: riskConfig.color }}>
            {riskConfig.symbol} {checkpoint.checkpoint_id} ({riskConfig.label})
          </h4>
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
                <td>
                  {checkpoint.forecast_timestamp
                    ? formatEtaTimestamp(checkpoint.forecast_timestamp)
                    : 'Unavailable'}
                </td>
              </tr>
              <tr>
                <td>
                  <strong>Wind (Gusts):</strong>
                </td>
                <td>
                  {checkpoint.weather.wind_speed_mph ?? 'N/A'} mph (
                  {checkpoint.weather.wind_gusts_mph ?? 'N/A'} mph)
                </td>
              </tr>
              <tr>
                <td>
                  <strong>Rain:</strong>
                </td>
                <td>{checkpoint.weather.rain_in_per_hr ?? 'N/A'} in/hr</td>
              </tr>
              <tr>
                <td>
                  <strong>Snow:</strong>
                </td>
                <td>{checkpoint.weather.snow_in_per_hr ?? 'N/A'} in/hr</td>
              </tr>
              <tr>
                <td>
                  <strong>Load Rule:</strong>
                </td>
                <td>{checkpoint.load_rule_applied || 'None'}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Popup>
    </CircleMarker>
  );
};
