import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ErrorBar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  methodError,
  methodErrorControl,
} from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import {
  CHART_HEIGHT,
  GRID,
  HOVER_CURSOR,
  INK,
  METHOD_COLORS,
  MUTED,
  pct,
  TICK,
  tooltipStyle,
  type ChartModule,
} from './theme'

// The control (Method 2's annual totals spread evenly over the year) isolates temporal resolution.
const rows = [...methodError, methodErrorControl]
const colors = [...METHOD_COLORS, MUTED]

const data = rows.map((m) => ({
  ...m,
  range: [m.mae - m.p5, m.p95 - m.mae] as [number, number],
}))

function Chart() {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={data} margin={{ top: 16, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="method" tick={TICK} stroke={GRID} interval={0} />
        <YAxis tick={TICK} stroke={GRID} width={44} unit="%" />
        <Tooltip
          {...tooltipStyle}
          cursor={HOVER_CURSOR}
          formatter={(_v: number, _n: string, item: { payload?: (typeof data)[number] }) => {
            const p = item.payload
            return p
              ? [
                  `${pct(p.mae)} hourly (range ${pct(p.p5)} - ${pct(p.p95)}), ${pct(p.annualError)} annual total`,
                  'Mean error',
                ]
              : ''
          }}
        />
        <Bar dataKey="mae" name="Mean error" radius={[4, 4, 0, 0]} maxBarSize={72}>
          {data.map((d, i) => (
            <Cell key={d.method} fill={colors[i]} />
          ))}
          <ErrorBar dataKey="range" width={8} strokeWidth={1.5} stroke={INK} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

const methodErrorChart: ChartModule = {
  Chart,
  table: () => ({
    header: [
      'Approach',
      'Mean hourly error',
      '5th percentile',
      '95th percentile',
      'Mean annual-total error',
    ],
    rows: rows.map((m) => [m.method, pct(m.mae), pct(m.p5), pct(m.p95), pct(m.annualError)]),
  }),
}
export default methodErrorChart
