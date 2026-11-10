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

import { methodError } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import {
  CHART_HEIGHT,
  GRID,
  HOVER_CURSOR,
  INK,
  METHOD_COLORS,
  pct,
  TICK,
  tooltipStyle,
  type ChartModule,
} from './theme'

const data = methodError.map((m) => ({
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
            return p ? [`${pct(p.mae)} (range ${pct(p.p5)} - ${pct(p.p95)})`, 'Mean error'] : ''
          }}
        />
        <Bar dataKey="mae" name="Mean error" radius={[4, 4, 0, 0]} maxBarSize={72}>
          {data.map((d, i) => (
            <Cell key={d.method} fill={METHOD_COLORS[i]} />
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
    header: ['Approach', 'Mean error', '5th percentile', '95th percentile'],
    rows: methodError.map((m) => [m.method, pct(m.mae), pct(m.p5), pct(m.p95)]),
  }),
}
export default methodErrorChart
