// Named color palettes usable in themes — `inkletter/colors.py`. Never
// mandatory: any CSS color string works wherever a color is expected.

export const WHITE = '#ffffff';
export const BLACK = '#000000';

export interface Hue {
  LIGHTEST: string;
  LIGHT: string;
  BASE: string;
  DARK: string;
  DARKEST: string;
}

export const Slate: Hue = { LIGHTEST: '#f8fafc', LIGHT: '#e2e8f0', BASE: '#64748b', DARK: '#334155', DARKEST: '#0f172a' };
export const Gray: Hue = { LIGHTEST: '#f9fafb', LIGHT: '#e5e7eb', BASE: '#6b7280', DARK: '#374151', DARKEST: '#111827' };
export const Blue: Hue = { LIGHTEST: '#eff6ff', LIGHT: '#bfdbfe', BASE: '#3b82f6', DARK: '#1d4ed8', DARKEST: '#1e3a8a' };
export const Red: Hue = { LIGHTEST: '#fef2f2', LIGHT: '#fecaca', BASE: '#ef4444', DARK: '#b91c1c', DARKEST: '#7f1d1d' };
export const Green: Hue = { LIGHTEST: '#f0fdf4', LIGHT: '#bbf7d0', BASE: '#22c55e', DARK: '#15803d', DARKEST: '#14532d' };
export const Yellow: Hue = { LIGHTEST: '#fefce8', LIGHT: '#fef08a', BASE: '#eab308', DARK: '#a16207', DARKEST: '#713f12' };
