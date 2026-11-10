'use client'

import React from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ErrorBar,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  componentError,
  methodError,
  telemetryCoverage,
  telemetryCoverageReferences,
  weeklySeries,
} from '@/constants/papers/nearRealTimeCarbonAccountingCharts'
import type { InteractiveChartId } from '@/types/research'

// Validated categorical palette, fixed order: Batch, Method 1, Method 2, Method 3.
// Matches the static manuscript figures so colours mean the same thing everywhere.
const SERIES = {
  batch: '#2a78d6',
  method1: '#eb6834',
  method2: '#1baf7a',
  method3: '#eda100',
  reference: '#52514e',
} as const
const GRID = '#e4e3df'
const AXIS = '#6b6a66'
const CHART_HEIGHT = 300
const TICK = { fill: AXIS, fontSize: 12 }
const HOURS_PER_DAY = 24
const DAY_TICKS = Array.from({ length: 7 }, (_, d) => d * HOURS_PER_DAY)
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const Y_STEP = 5
const REFERENCE_LABEL_SPACE = 104

const tooltipStyle = {
  contentStyle: {
    borderRadius: 8,
    border: '1px solid #e8eaef',
    fontSize: 12,
    boxShadow: '0 4px 16px rgba(8,12,4,0.08)',
  },
  labelStyle: { color: '#080c04', fontWeight: 600 },
}

const pct = (v: number) => `${v.toFixed(1)}%`

function WeeklySeriesChart() {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <LineChart data={weeklySeries} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="hour"
          ticks={DAY_TICKS}
          tickFormatter={(h: number) => DAY_NAMES[Math.floor(h / HOURS_PER_DAY)]}
          tick={TICK}
          stroke={GRID}
        />
        <YAxis
          tick={TICK}
          stroke={GRID}
          width={44}
          label={{
            value: 'g CO₂e / hour',
            angle: -90,
            position: 'insideLeft',
            fill: AXIS,
            fontSize: 12,
          }}
        />
        <Tooltip
          {...tooltipStyle}
          labelFormatter={(h: number) => weeklySeries[h]?.label ?? ''}
          formatter={(v: number) => `${v.toFixed(2)} g`}
        />
        <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
        <Line
          dataKey="reference"
          name="Reference (true hourly)"
          stroke={SERIES.reference}
          strokeWidth={1.5}
          dot={false}
        />
        <Line
          dataKey="batch"
          name="Conventional batch"
          stroke={SERIES.batch}
          strokeWidth={2}
          dot={false}
        />
        <Line
          dataKey="method1"
          name="Method 1"
          stroke={SERIES.method1}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function MethodErrorChart() {
  const colors = [SERIES.batch, SERIES.method1, SERIES.method2, SERIES.method3]
  const data = methodError.map((m, i) => ({
    ...m,
    range: [m.mae - m.p5, m.p95 - m.mae] as [number, number],
    fill: colors[i],
  }))
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={data} margin={{ top: 16, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="method" tick={TICK} stroke={GRID} interval={0} />
        <YAxis tick={TICK} stroke={GRID} width={44} unit="%" />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: 'rgba(8,12,4,0.04)' }}
          formatter={(_v: number, _n: string, item: { payload?: (typeof data)[number] }) => {
            const p = item.payload
            return p ? [`${pct(p.mae)} (range ${pct(p.p5)} - ${pct(p.p95)})`, 'Mean error'] : ''
          }}
        />
        <Bar dataKey="mae" name="Mean error" radius={[4, 4, 0, 0]} maxBarSize={72}>
          <ErrorBar dataKey="range" width={8} strokeWidth={1.5} stroke="#080c04" />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function ComponentErrorChart() {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={componentError} margin={{ top: 8, right: 12, bottom: 4, left: 0 }} barGap={2}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="component" tick={TICK} stroke={GRID} />
        <YAxis tick={TICK} stroke={GRID} width={44} unit="%" />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: 'rgba(8,12,4,0.04)' }}
          formatter={(v: number) => pct(v)}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          dataKey="batch"
          name="Conventional batch"
          fill={SERIES.batch}
          radius={[4, 4, 0, 0]}
          maxBarSize={36}
        />
        <Bar
          dataKey="method2"
          name="Method 2"
          fill={SERIES.method2}
          radius={[4, 4, 0, 0]}
          maxBarSize={36}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

function TelemetryCoverageChart() {
  const refs = [
    { value: telemetryCoverageReferences.batch, label: 'Batch', color: SERIES.batch },
    {
      value: telemetryCoverageReferences.method1,
      label: 'Method 1',
      color: SERIES.method1,
    },
    {
      value: telemetryCoverageReferences.method3,
      label: 'Method 3',
      color: SERIES.method3,
    },
  ]
  // Include every reference line in the y-range, rounded up to the next axis step.
  const yMax =
    Math.ceil(
      Math.max(...refs.map((r) => r.value), ...telemetryCoverage.map((c) => c.method2)) / Y_STEP
    ) * Y_STEP
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <LineChart
        data={telemetryCoverage}
        margin={{ top: 12, right: REFERENCE_LABEL_SPACE, bottom: 4, left: 0 }}
      >
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="coverage"
          tick={TICK}
          stroke={GRID}
          unit="%"
          type="number"
          domain={[0, 100]}
        />
        <YAxis
          tick={TICK}
          stroke={GRID}
          width={44}
          unit="%"
          domain={[0, yMax]}
          ticks={Array.from({ length: yMax / Y_STEP + 1 }, (_, i) => i * Y_STEP)}
        />
        <Tooltip
          {...tooltipStyle}
          labelFormatter={(c: number) => `Telemetry coverage ${c}%`}
          formatter={(v: number) => [pct(v), 'Method 2 error']}
        />
        {refs.map((r) => (
          <ReferenceLine
            key={r.label}
            y={r.value}
            stroke={r.color}
            strokeDasharray="5 4"
            label={{
              value: `${r.label} ${pct(r.value)}`,
              position: 'right',
              fill: AXIS,
              fontSize: 11,
            }}
          />
        ))}
        <Line
          dataKey="method2"
          name="Method 2"
          stroke={SERIES.method2}
          strokeWidth={2.5}
          dot={{ r: 4, fill: SERIES.method2, stroke: '#fff', strokeWidth: 2 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

/** Accessible data view rendered under each interactive chart. */
function ChartDataTable({ id }: { id: InteractiveChartId }) {
  const table = chartTable(id)
  return (
    <details className="mt-3 text-sm text-neutral-600">
      <summary className="cursor-pointer select-none font-medium text-neutral-700 hover:text-[#080c04]">
        Show data
      </summary>
      <div className="mt-2 max-h-64 overflow-auto rounded-lg border border-neutral-200">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-neutral-50">
            <tr>
              {table.header.map((h) => (
                <th key={h} className="px-3 py-2 font-semibold text-neutral-700">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, i) => (
              <tr key={i} className="border-t border-neutral-100">
                {row.map((cell, j) => (
                  <td key={j} className="px-3 py-1.5 tabular-nums">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

function chartTable(id: InteractiveChartId): { header: string[]; rows: string[][] } {
  switch (id) {
    case 'weekly-series':
      return {
        header: ['Hour', 'Reference (g)', 'Batch (g)', 'Method 1 (g)'],
        rows: weeklySeries.map((r) => [
          r.label,
          r.reference.toFixed(2),
          r.batch.toFixed(2),
          r.method1.toFixed(2),
        ]),
      }
    case 'method-error':
      return {
        header: ['Approach', 'Mean error', '5th percentile', '95th percentile'],
        rows: methodError.map((m) => [m.method, pct(m.mae), pct(m.p5), pct(m.p95)]),
      }
    case 'component-error':
      return {
        header: ['Component', 'Batch error', 'Method 2 error'],
        rows: componentError.map((c) => [c.component, pct(c.batch), pct(c.method2)]),
      }
    case 'telemetry-coverage':
      return {
        header: ['Telemetry coverage', 'Method 2 error'],
        rows: telemetryCoverage.map((c) => [`${c.coverage}%`, pct(c.method2)]),
      }
  }
}

const CHARTS: Record<InteractiveChartId, React.FC> = {
  'weekly-series': WeeklySeriesChart,
  'method-error': MethodErrorChart,
  'component-error': ComponentErrorChart,
  'telemetry-coverage': TelemetryCoverageChart,
}

export default function ResearchChart({ id }: { id: InteractiveChartId }) {
  const Chart = CHARTS[id]
  return (
    <div>
      <Chart />
      <ChartDataTable id={id} />
    </div>
  )
}
