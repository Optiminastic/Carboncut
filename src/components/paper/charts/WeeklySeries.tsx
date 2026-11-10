import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { weeklySeries } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import { AXIS, CHART_HEIGHT, GRID, SERIES, TICK, tooltipStyle, type ChartModule } from './theme'

const HOURS_PER_DAY = 24
const DAY_TICKS = Array.from({ length: 7 }, (_, d) => d * HOURS_PER_DAY)
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function Chart() {
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

const weeklySeriesChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Hour', 'Reference (g)', 'Batch (g)', 'Method 1 (g)'],
    rows: weeklySeries.map((r) => [
      r.label,
      r.reference.toFixed(2),
      r.batch.toFixed(2),
      r.method1.toFixed(2),
    ]),
  }),
}
export default weeklySeriesChart
