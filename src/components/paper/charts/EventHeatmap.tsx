'use client'

import { useEffect, useMemo, useRef, useState } from 'react'

import { eventHeatmap } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import { sequentialColor, type ChartModule } from './theme'

const DAYS = 365
const HOURS = 24
const HEIGHT = 240
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
const MONTH_STARTS = MONTH_LENGTHS.reduce<number[]>(
  (acc, _len, i) => [...acc, i === 0 ? 0 : acc[i - 1] + MONTH_LENGTHS[i - 1]],
  []
)
const HOUR_TICKS = [0, 6, 12, 18, 23]

const valueAt = (day: number, hour: number) => eventHeatmap[day * HOURS + hour]

function dayLabel(day: number) {
  let m = MONTH_STARTS.length - 1
  while (MONTH_STARTS[m] > day) m--
  return `${day - MONTH_STARTS[m] + 1} ${MONTHS[m]}`
}

function Chart() {
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [width, setWidth] = useState(0)
  const [hover, setHover] = useState<{ day: number; hour: number } | null>(null)
  const [min, max] = useMemo(() => [Math.min(...eventHeatmap), Math.max(...eventHeatmap)], [])

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const observer = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)))
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || width === 0) return
    const dpr = window.devicePixelRatio || 1
    canvas.width = width * dpr
    canvas.height = HEIGHT * dpr
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.scale(dpr, dpr)
    const cw = width / DAYS
    const ch = HEIGHT / HOURS
    for (let d = 0; d < DAYS; d++) {
      for (let h = 0; h < HOURS; h++) {
        ctx.fillStyle = sequentialColor((valueAt(d, h) - min) / (max - min))
        // Hour 0 at the bottom; overlap by a pixel fraction to avoid hairline gaps.
        ctx.fillRect(d * cw, (HOURS - 1 - h) * ch, cw + 0.5, ch + 0.5)
      }
    }
  }, [width, min, max])

  const onMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const day = Math.min(
      DAYS - 1,
      Math.max(0, Math.floor(((e.clientX - rect.left) / rect.width) * DAYS))
    )
    const hour = Math.min(
      HOURS - 1,
      Math.max(0, HOURS - 1 - Math.floor(((e.clientY - rect.top) / rect.height) * HOURS))
    )
    setHover({ day, hour })
  }

  return (
    <div>
      <p className="mb-2 h-5 text-sm tabular-nums text-neutral-700" aria-live="polite">
        {hover ? (
          <>
            <span className="font-semibold text-ink">
              {dayLabel(hover.day)}, {String(hover.hour).padStart(2, '0')}:00 UTC
            </span>
            : {valueAt(hover.day, hover.hour).toFixed(1)} g CO₂e per hour
          </>
        ) : (
          <span className="text-neutral-400">Hover over the heatmap to read hourly emissions</span>
        )}
      </p>
      <div className="flex gap-2">
        <div
          className="relative w-8 shrink-0 text-[11px] tabular-nums text-neutral-500"
          style={{ height: HEIGHT }}
        >
          {HOUR_TICKS.map((h) => (
            <span
              key={h}
              className="absolute right-0 -translate-y-1/2"
              style={{ top: ((HOURS - 1 - h + 0.5) / HOURS) * HEIGHT }}
            >
              {String(h).padStart(2, '0')}h
            </span>
          ))}
        </div>
        <div ref={wrapRef} className="min-w-0 flex-1">
          <canvas
            ref={canvasRef}
            onMouseMove={onMove}
            onMouseLeave={() => setHover(null)}
            className="block w-full cursor-crosshair rounded"
            style={{ height: HEIGHT }}
            role="img"
            aria-label={`Heatmap of hourly emissions over a year, from ${min.toFixed(1)} to ${max.toFixed(1)} g CO2e per hour`}
          />
          <div className="relative mt-1 h-4 text-[11px] text-neutral-500">
            {MONTHS.map((m, i) => (
              <span
                key={m}
                className="absolute"
                style={{ left: `${(MONTH_STARTS[i] / DAYS) * 100}%` }}
              >
                {m}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-4 flex items-center gap-3 text-xs tabular-nums text-neutral-600">
        <span>{min.toFixed(1)} g</span>
        <span
          className="h-2.5 w-40 rounded"
          style={{
            background: `linear-gradient(to right, ${sequentialColor(0)}, ${sequentialColor(1)})`,
          }}
        />
        <span>{max.toFixed(1)} g CO₂e per hour</span>
      </div>
    </div>
  )
}

function hourlyProfile() {
  return Array.from({ length: HOURS }, (_, h) => {
    const values = Array.from({ length: DAYS }, (_, d) => valueAt(d, h))
    const mean = values.reduce((a, b) => a + b, 0) / DAYS
    return [
      `${String(h).padStart(2, '0')}:00`,
      mean.toFixed(2),
      Math.min(...values).toFixed(2),
      Math.max(...values).toFixed(2),
    ]
  })
}

const eventHeatmapChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Hour (UTC)', 'Annual mean (g/h)', 'Minimum (g/h)', 'Maximum (g/h)'],
    rows: hourlyProfile(),
  }),
}
export default eventHeatmapChart
