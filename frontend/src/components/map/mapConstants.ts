import { RiskLevel } from '../../types/api';

export const OPENSTREETMAP_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

export const OPENSTREETMAP_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

export interface RouteStyleConfig {
  color: string;
  dashArray?: string;
  name: string;
}

export const ROUTE_STYLE_MAP: Record<string, RouteStyleConfig> = {
  route_primary: {
    color: '#1e3a8a', // Deep Blue
    name: 'Primary Corridor (Solid)',
  },
  route_alt_1: {
    color: '#059669', // Emerald Green
    dashArray: '8, 6', // Dashed
    name: 'Alternative 1 (Dashed)',
  },
  route_alt_2: {
    color: '#7c3aed', // Purple
    dashArray: '3, 6', // Dotted
    name: 'Alternative 2 (Dotted)',
  },
};

export const DEFAULT_ROUTE_STYLE: RouteStyleConfig = {
  color: '#475569',
  dashArray: '6, 6',
  name: 'Corridor Route',
};

export interface RiskStyleConfig {
  color: string;
  label: string;
  symbol: string;
}

export const RISK_STYLE_MAP: Record<RiskLevel, RiskStyleConfig> = {
  low: {
    color: '#16a34a',
    label: 'Low Risk',
    symbol: '●',
  },
  moderate: {
    color: '#d97706',
    label: 'Moderate Risk',
    symbol: '▲',
  },
  high: {
    color: '#ea580c',
    label: 'High Risk',
    symbol: '◆',
  },
  severe: {
    color: '#dc2626',
    label: 'Severe Risk',
    symbol: '✖',
  },
  no_travel: {
    color: '#7f1d1d',
    label: 'No Travel Hazard',
    symbol: '🛑',
  },
  unknown: {
    color: '#6b7280',
    label: 'Unknown / Unverified',
    symbol: '❓',
  },
};
