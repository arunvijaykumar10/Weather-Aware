import React, { useMemo } from 'react';
import { Circle, Tooltip } from 'react-leaflet';
import { HeatmapSamplePoint } from '../../types/api';
import { RISK_COLOR_MAP } from '../../utils/timelineUtils';

interface CorridorHeatmapLayerProps {
  samples: HeatmapSamplePoint[];
  selectedHour: number;
  opacity: number;
  visible: boolean;
  corridorHalfWidthMiles?: number;
}

export const CorridorHeatmapLayer: React.FC<CorridorHeatmapLayerProps> = ({
  samples,
  selectedHour,
  opacity,
  visible,
  corridorHalfWidthMiles = 15.0,
}) => {
  if (!visible || !samples || samples.length === 0) {
    return null;
  }

  const radiusMeters = Math.max(10000, corridorHalfWidthMiles * 1609.34);

  const renderedSamples = useMemo(() => {
    return samples.map((sample) => {
      const entry =
        sample.timeline.find((t) => t.offset_hours === selectedHour) || sample.timeline[0];

      const score = entry?.numeric_risk_score ?? null;
      const risk = entry?.load_adjusted_risk ?? 'unknown';
      const color = RISK_COLOR_MAP[risk] || '#9ca3af';

      return {
        pointId: sample.point_id,
        lat: sample.lat,
        lon: sample.lon,
        score,
        risk,
        color,
        availability: entry?.availability ?? 'unavailable',
      };
    });
  }, [samples, selectedHour]);

  return (
    <>
      {renderedSamples.map((item) => (
        <Circle
          key={item.pointId}
          center={[item.lat, item.lon]}
          radius={radiusMeters}
          pathOptions={{
            color: item.color,
            weight: 0,
            fillColor: item.color,
            fillOpacity: opacity * 0.4,
          }}
        >
          <Tooltip direction="top" offset={[0, -10]}>
            <span>
              <strong>Interpolated between forecast samples</strong>
              <br />
              Risk Intensity: {item.score !== null ? `${item.score}/4 (${item.risk})` : 'Unknown'}
            </span>
          </Tooltip>
        </Circle>
      ))}
    </>
  );
};
