import '@testing-library/jest-dom';
import React from 'react';
import { vi } from 'vitest';

// Mock Leaflet and React-Leaflet for jsdom environment (where HTML5 Canvas is not natively implemented)
vi.mock('react-leaflet', async () => {
  const actual = await vi.importActual('react-leaflet');
  return {
    ...actual,
    MapContainer: ({ children }: { children?: React.ReactNode }) =>
      React.createElement('div', { 'data-testid': 'leaflet-map-container' }, children),
    TileLayer: () => React.createElement('div', { 'data-testid': 'leaflet-tile-layer' }),
    Polyline: ({
      eventHandlers,
      positions,
    }: {
      eventHandlers?: { click?: () => void };
      positions: unknown;
    }) =>
      React.createElement('div', {
        'data-testid': 'leaflet-polyline',
        onClick: eventHandlers?.click,
        'data-positions': JSON.stringify(positions),
      }),
    CircleMarker: ({
      eventHandlers,
      center,
      children,
    }: {
      eventHandlers?: { click?: () => void };
      center: unknown;
      children?: React.ReactNode;
    }) =>
      React.createElement(
        'div',
        {
          'data-testid': 'leaflet-circle-marker',
          onClick: eventHandlers?.click,
          'data-center': JSON.stringify(center),
        },
        children
      ),
    Popup: ({ children }: { children?: React.ReactNode }) =>
      React.createElement('div', { 'data-testid': 'leaflet-popup' }, children),
    Tooltip: ({ children }: { children?: React.ReactNode }) =>
      React.createElement('div', { 'data-testid': 'leaflet-tooltip' }, children),
    useMap: () => ({
      fitBounds: vi.fn(),
      invalidateSize: vi.fn(),
    }),
  };
});
