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

import { componentShares } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import {
  COMPONENT_COLORS,
  GRID,
  HOVER_CURSOR,
  INK,
  pct,
  TICK,
  tooltipStyle,
  type ChartModule,
} from './theme'

const data = componentShares.map((c) => ({
  ...c,
  range: [c.mean - c.p5, c.p95 - c.mean] as [number, number],
}))

function Chart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 8, right: 24, bottom: 4, left: 8 }}
        barSize={22}
      >
        <CartesianGrid stroke={GRID} horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={TICK} stroke={GRID} unit="%" />
        <YAxis type="category" dataKey="component" tick={TICK} stroke={GRID} width={72} />
        <Tooltip
          {...tooltipStyle}
          cursor={HOVER_CURSOR}
          formatter={(_v: number, _n: string, item: { payload?: (typeof data)[number] }) => {
            const p = item.payload
            return p
              ? [`${pct(p.mean)} (5th-95th percentile ${pct(p.p5)} - ${pct(p.p95)})`, 'Share']
              : ''
          }}
        />
        <Bar dataKey="mean" name="Share" radius={[0, 4, 4, 0]}>
          {data.map((d) => (
            <Cell key={d.component} fill={COMPONENT_COLORS[d.component]} />
          ))}
          <ErrorBar dataKey="range" direction="x" width={6} strokeWidth={1.25} stroke={INK} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

const componentSharesChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Component', 'Mean share', '5th percentile', '95th percentile'],
    rows: componentShares.map((c) => [c.component, pct(c.mean), pct(c.p5), pct(c.p95)]),
  }),
}
export default componentSharesChart
