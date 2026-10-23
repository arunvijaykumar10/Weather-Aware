import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { Route } from '../../types/api';

interface MapBoundsUpdaterProps {
  routes: Route[];
}

export const MapBoundsUpdater: React.FC<MapBoundsUpdaterProps> = ({ routes }) => {
  const map = useMap();

  useEffect(() => {
    map.invalidateSize();
    if (!routes || routes.length === 0) return;

    const validCoordinates = routes
      .flatMap((r) => r.geometry || [])
      .filter(
        (coord) => Array.isArray(coord) && coord.length >= 2 && !isNaN(coord[0]) && !isNaN(coord[1])
      );

    if (validCoordinates.length === 0) return;

    const latLngBounds = L.latLngBounds(validCoordinates as L.LatLngExpression[]);
    if (latLngBounds.isValid()) {
      map.fitBounds(latLngBounds, { padding: [50, 50], maxZoom: 13 });
    }
  }, [routes, map]);

  useEffect(() => {
    const handleResize = () => map.invalidateSize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [map]);

  return null;
};
