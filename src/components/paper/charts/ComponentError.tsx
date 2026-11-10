import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { componentError } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import {
  CHART_HEIGHT,
  GRID,
  HOVER_CURSOR,
  pct,
  SERIES,
  TICK,
  tooltipStyle,
  type ChartModule,
} from './theme'

function Chart() {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={componentError} margin={{ top: 8, right: 12, bottom: 4, left: 0 }} barGap={2}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="component" tick={TICK} stroke={GRID} />
        <YAxis tick={TICK} stroke={GRID} width={44} unit="%" />
        <Tooltip {...tooltipStyle} cursor={HOVER_CURSOR} formatter={(v: number) => pct(v)} />
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

const componentErrorChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Component', 'Batch error', 'Method 2 error'],
    rows: componentError.map((c) => [c.component, pct(c.batch), pct(c.method2)]),
  }),
}
export default componentErrorChart
