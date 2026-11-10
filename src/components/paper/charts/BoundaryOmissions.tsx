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

import { boundaryOmissions } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import {
  COMPONENT_COLORS,
  GRID,
  HOVER_CURSOR,
  pct,
  TICK,
  tooltipStyle,
  type ChartModule,
} from './theme'

const COMPONENTS = Object.keys(COMPONENT_COLORS) as (keyof (typeof boundaryOmissions)[number])[]
const total = (row: (typeof boundaryOmissions)[number]) =>
  COMPONENTS.reduce((sum, c) => sum + Number(row[c]), 0)
const [reference, batch] = boundaryOmissions

function Chart() {
  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={boundaryOmissions}
          layout="vertical"
          margin={{ top: 8, right: 16, bottom: 4, left: 8 }}
          barSize={40}
        >
          <CartesianGrid stroke={GRID} horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={TICK} stroke={GRID} unit="%" />
          <YAxis type="category" dataKey="row" tick={TICK} stroke={GRID} width={150} />
          <Tooltip {...tooltipStyle} cursor={HOVER_CURSOR} formatter={(v: number) => pct(v)} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {COMPONENTS.map((c) => (
            <Bar
              key={String(c)}
              dataKey={String(c)}
              stackId="total"
              fill={COMPONENT_COLORS[String(c)]}
              stroke="#fff"
              strokeWidth={1}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-1 text-sm text-neutral-600">
        The batch estimate captures{' '}
        <strong className="font-semibold text-[#080c04]">{pct(total(batch))}</strong> of reference
        emissions; CDN and device emissions are outside its boundary.
      </p>
    </div>
  )
}

const boundaryOmissionsChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Component', 'Reference (% of total)', 'Batch estimate (% of reference total)'],
    rows: [
      ...COMPONENTS.map((c) => [String(c), pct(Number(reference[c])), pct(Number(batch[c]))]),
      // Reference shares are rounded per component; their exact total is 100%.
      ['Total', pct(100), pct(total(batch))],
    ],
  }),
}
export default boundaryOmissionsChart
