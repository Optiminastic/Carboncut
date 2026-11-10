'use client'

import { useRef, useState } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  resolutionLadder,
  type LadderMethodKey,
} from '@/constants/papers/nearRealTimeCarbonAccountingBrief'
import {
  researchHeadline,
  weeklySeries,
} from '@/constants/papers/nearRealTimeCarbonAccountingCharts'
import { cn } from '@/lib/cn'

import { AXIS, GRID, SERIES, TICK, tooltipStyle } from './charts/theme'

const HOURS_PER_DAY = 24
const DAY_TICKS = Array.from({ length: 7 }, (_, d) => d * HOURS_PER_DAY)
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const CHART_HEIGHT = 280
const DEFAULT_RUNG = 0

const METHOD_COLOR: Record<LadderMethodKey, string> = {
  batch: SERIES.batch,
  method1: SERIES.method1,
  method2: SERIES.method2,
  method3: SERIES.method3,
}

/**
 * Interactive "resolution ladder": the same week of emissions estimated by each of the
 * paper's four approaches, drawn against the true hourly reference.
 */
export default function ResolutionLadder() {
  const [index, setIndex] = useState(DEFAULT_RUNG)
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])
  const rung = resolutionLadder[index]
  const color = METHOD_COLOR[rung.key]

  const select = (i: number) => {
    const next = (i + resolutionLadder.length) % resolutionLadder.length
    setIndex(next)
    tabRefs.current[next]?.focus()
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight') select(index + 1)
    else if (e.key === 'ArrowLeft') select(index - 1)
    else if (e.key === 'Home') select(0)
    else if (e.key === 'End') select(resolutionLadder.length - 1)
    else return
    e.preventDefault()
  }

  return (
    <div className="rounded-2xl bg-panel p-4 sm:p-6">
      <div
        role="tablist"
        aria-label="Accounting approach"
        onKeyDown={onKeyDown}
        className="grid grid-cols-2 gap-1.5 rounded-xl bg-white p-1.5 sm:grid-cols-4"
      >
        {resolutionLadder.map((r, i) => (
          <button
            key={r.key}
            ref={(el) => {
              tabRefs.current[i] = el
            }}
            role="tab"
            id={`ladder-tab-${r.key}`}
            aria-selected={i === index}
            aria-controls="ladder-panel"
            tabIndex={i === index ? 0 : -1}
            onClick={() => setIndex(i)}
            className={cn(
              'rounded-lg px-3 py-2.5 text-left transition-colors',
              i === index ? 'bg-ink text-white' : 'text-ink-soft hover:bg-panel'
            )}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ backgroundColor: METHOD_COLOR[r.key] }}
              />
              {r.name}
            </span>
            <span
              className={cn('mt-0.5 block text-xs', i === index ? 'text-white/70' : 'text-muted')}
            >
              {r.cadence}
            </span>
          </button>
        ))}
      </div>

      <div
        id="ladder-panel"
        role="tabpanel"
        aria-labelledby={`ladder-tab-${rung.key}`}
        className="mt-5 grid gap-6 lg:grid-cols-[minmax(0,1fr)_220px]"
      >
        <div>
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <ComposedChart data={weeklySeries} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis
                dataKey="hour"
                ticks={DAY_TICKS}
                tickFormatter={(hour: number) => DAY_NAMES[Math.floor(hour / HOURS_PER_DAY)]}
                tick={TICK}
                stroke={GRID}
              />
              <YAxis tick={TICK} stroke={GRID} width={40} domain={[0, 'auto']} />
              <Tooltip
                {...tooltipStyle}
                labelFormatter={(hour: number) => weeklySeries[hour]?.label ?? ''}
                formatter={(v: number, name: string) => [`${v.toFixed(2)} g CO₂e`, name]}
              />
              <Area
                dataKey="reference"
                name="True hourly emissions"
                stroke={AXIS}
                strokeWidth={1}
                fill={AXIS}
                fillOpacity={0.12}
                isAnimationActive={false}
              />
              <Line
                key={rung.key}
                dataKey={rung.key}
                name={rung.name}
                stroke={color}
                strokeWidth={2.5}
                dot={false}
                animationDuration={500}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
            <span className="inline-flex items-center gap-1.5">
              <span
                className="h-2.5 w-4 rounded-sm"
                style={{ backgroundColor: AXIS, opacity: 0.25 }}
              />
              True hourly emissions
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-0.5 w-4" style={{ backgroundColor: color }} />
              {rung.name} estimate
            </span>
            <span>One week, example website, g CO₂e per hour</span>
          </p>
        </div>

        <div className="flex flex-col justify-between gap-4 border-t border-rule pt-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          <div>
            <p className="font-serif text-6xl font-medium leading-none tracking-tight text-ink tabular-nums">
              {rung.error.toFixed(1)}
              <span className="text-3xl">%</span>
            </p>
            <p className="mt-2 text-sm text-ink-soft">
              average hourly error across {researchHeadline.workloads} websites
            </p>
          </div>
          <p className="text-sm leading-relaxed text-ink-soft">{rung.uses}</p>
        </div>
      </div>
    </div>
  )
}
