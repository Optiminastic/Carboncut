import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  telemetryCoverage,
  telemetryCoverageReferences,
} from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import {
  AXIS,
  CHART_HEIGHT,
  GRID,
  pct,
  SERIES,
  TICK,
  tooltipStyle,
  type ChartModule,
} from './theme'

const Y_STEP = 5
const REFERENCE_LABEL_SPACE = 104

const refs = [
  { value: telemetryCoverageReferences.batch, label: 'Batch', color: SERIES.batch },
  { value: telemetryCoverageReferences.method1, label: 'Method 1', color: SERIES.method1 },
  { value: telemetryCoverageReferences.method3, label: 'Method 3', color: SERIES.method3 },
]
// Include every reference line in the y-range, rounded up to the next axis step.
const yMax =
  Math.ceil(
    Math.max(...refs.map((r) => r.value), ...telemetryCoverage.map((c) => c.method2)) / Y_STEP
  ) * Y_STEP

function Chart() {
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

const telemetryCoverageChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Telemetry coverage', 'Method 2 error'],
    rows: telemetryCoverage.map((c) => [`${c.coverage}%`, pct(c.method2)]),
  }),
}
export default telemetryCoverageChart
