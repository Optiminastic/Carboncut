import type React from 'react'

// Validated categorical palette in fixed order. Methods: Batch, Method 1, Method 2, Method 3.
// Components follow the same order. Matches the static manuscript figures.
export const SERIES = {
  batch: '#2a78d6',
  method1: '#eb6834',
  method2: '#1baf7a',
  method3: '#eda100',
  reference: '#52514e',
} as const

export const METHOD_COLORS = [SERIES.batch, SERIES.method1, SERIES.method2, SERIES.method3]

export const COMPONENT_COLORS: Record<string, string> = {
  Compute: '#2a78d6',
  Storage: '#eb6834',
  Network: '#1baf7a',
  CDN: '#eda100',
  Device: '#e87ba4',
}

export const INK = '#080c04'
export const GRID = '#e4e3df'
export const AXIS = '#6b6a66'
export const CHART_HEIGHT = 300
export const TICK = { fill: AXIS, fontSize: 12 }
export const HOVER_CURSOR = { fill: 'rgba(8,12,4,0.04)' }

/** Sequential single-hue scale (light to dark blue) for magnitudes. */
export const SEQUENTIAL = { light: [234, 242, 252], dark: [11, 58, 117] } as const

export function sequentialColor(t: number) {
  const k = Math.min(1, Math.max(0, t))
  const [r, g, b] = SEQUENTIAL.light.map((l, i) => Math.round(l + (SEQUENTIAL.dark[i] - l) * k))
  return `rgb(${r}, ${g}, ${b})`
}

export const tooltipStyle = {
  contentStyle: {
    borderRadius: 8,
    border: '1px solid #e8eaef',
    fontSize: 12,
    boxShadow: '0 4px 16px rgba(8,12,4,0.08)',
  },
  labelStyle: { color: INK, fontWeight: 600 },
}

export const pct = (v: number) => `${v.toFixed(1)}%`

export interface ChartTable {
  header: string[]
  rows: string[][]
}

/** A figure module: the visual plus an optional tabular view of its data. */
export interface ChartModule {
  Chart: React.FC
  table?: () => ChartTable
}
