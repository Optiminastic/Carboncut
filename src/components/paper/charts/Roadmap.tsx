import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
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

const STAGES = [
  { stage: 'Conventional batch', requires: 'Annual activity data and static factors' },
  {
    stage: 'Method 1: Operational hybrid',
    requires: 'Page-view tracker plus monthly provider and CDN data',
  },
  {
    stage: 'Method 2: Hybrid deterministic-batch',
    requires: 'Hourly utilisation, CDN logs and a grid-intensity signal',
  },
  {
    stage: 'Method 3: Full event-level',
    requires: 'Path-level routing and per-component energy telemetry',
  },
]
const data = methodError.map((m, i) => ({ ...m, ...STAGES[i] }))
const Y_STEP = 10
// Headroom above the tallest bar for its value label, rounded to the axis step.
const Y_MAX = Math.ceil((Math.max(...data.map((d) => d.mae)) + Y_STEP / 2) / Y_STEP) * Y_STEP
const Y_TICKS = Array.from({ length: Y_MAX / Y_STEP + 1 }, (_, i) => i * Y_STEP)

function Chart() {
  return (
    <div>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <BarChart data={data} margin={{ top: 24, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="method" tick={TICK} stroke={GRID} interval={0} />
          <YAxis
            tick={TICK}
            stroke={GRID}
            width={44}
            unit="%"
            domain={[0, Y_MAX]}
            ticks={Y_TICKS}
          />
          <Tooltip
            {...tooltipStyle}
            cursor={HOVER_CURSOR}
            formatter={(v: number) => [pct(v), 'Hourly attribution error']}
          />
          <Bar dataKey="mae" radius={[4, 4, 0, 0]} maxBarSize={72}>
            {data.map((d, i) => (
              <Cell key={d.method} fill={METHOD_COLORS[i]} />
            ))}
            <LabelList
              dataKey="mae"
              position="top"
              formatter={(v: number) => pct(v)}
              fill={INK}
              fontSize={12}
              fontWeight={600}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <ol className="mt-4 grid gap-3 sm:grid-cols-4">
        {data.map((d, i) => (
          <li key={d.stage} className="rounded-lg border border-neutral-200 p-3 text-xs">
            <p className="flex items-center gap-2 font-semibold text-ink">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: METHOD_COLORS[i] }}
              />
              Stage {i + 1}
            </p>
            <p className="mt-1 text-neutral-600">{d.requires}</p>
          </li>
        ))}
      </ol>
    </div>
  )
}

const roadmapChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Stage', 'Data required', 'Hourly attribution error'],
    rows: data.map((d) => [d.stage, d.requires, pct(d.mae)]),
  }),
}
export default roadmapChart
