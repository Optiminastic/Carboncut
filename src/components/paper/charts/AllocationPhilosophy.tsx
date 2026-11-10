import {
  CartesianGrid,
  LabelList,
  Legend,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'

import { allocationPhilosophy } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import { AXIS, COMPONENT_COLORS, GRID, INK, TICK, type ChartModule } from './theme'

const THRESHOLD = 0.5
const X_MAX = 1.15
const MARKER_SIZE = 140
// Points that sit close to a neighbour get their label on the left to avoid overlap.
const LEFT_LABELS = new Set(['Device'])

type Point = (typeof allocationPhilosophy)[number]

function PointTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
  const p = payload?.[0]?.payload
  if (!active || !p) return null
  return (
    <div className="rounded-lg border border-neutral-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="font-semibold text-ink">{p.component}</p>
      <p className="mt-1 text-neutral-600">Hourly variability (CV): {p.cv.toFixed(2)}</p>
      <p className="text-neutral-600">Observability: {p.observability.toFixed(2)}</p>
      <p className="mt-1 font-medium text-ink">
        {p.deterministic ? 'Deterministic in Method 2' : 'Batch proxy in Method 2'}
      </p>
    </div>
  )
}

function Chart() {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ScatterChart margin={{ top: 16, right: 24, bottom: 28, left: 0 }}>
        <CartesianGrid stroke={GRID} />
        <ReferenceArea
          x1={THRESHOLD}
          x2={X_MAX}
          y1={THRESHOLD}
          y2={1.05}
          fill="#b0ea1d"
          fillOpacity={0.12}
          label={{
            value: 'Deterministic (event / hourly)',
            position: 'insideTopRight',
            fill: INK,
            fontSize: 11,
          }}
        />
        <ReferenceArea
          x1={0}
          x2={THRESHOLD}
          y1={0}
          y2={THRESHOLD}
          fill="#e4e3df"
          fillOpacity={0.35}
          label={{
            value: 'Batch proxy (short-interval average)',
            position: 'insideBottomLeft',
            fill: INK,
            fontSize: 11,
          }}
        />
        <ReferenceLine x={THRESHOLD} stroke={AXIS} strokeDasharray="4 4" />
        <ReferenceLine y={THRESHOLD} stroke={AXIS} strokeDasharray="4 4" />
        <XAxis
          type="number"
          dataKey="variability"
          domain={[0, X_MAX]}
          ticks={[0, 0.25, 0.5, 0.75, 1]}
          tick={TICK}
          stroke={GRID}
          label={{
            value: 'Temporal variability (normalised CV)',
            position: 'insideBottom',
            offset: -16,
            fill: AXIS,
            fontSize: 12,
          }}
        />
        <YAxis
          type="number"
          dataKey="observability"
          domain={[0, 1.05]}
          ticks={[0, 0.25, 0.5, 0.75, 1]}
          tick={TICK}
          stroke={GRID}
          width={44}
          label={{
            value: 'Observability',
            angle: -90,
            position: 'insideLeft',
            fill: AXIS,
            fontSize: 12,
          }}
        />
        <ZAxis range={[MARKER_SIZE, MARKER_SIZE]} />
        <Tooltip content={<PointTooltip />} cursor={{ strokeDasharray: '3 3' }} />
        <Legend verticalAlign="top" height={28} wrapperStyle={{ fontSize: 12 }} />
        {allocationPhilosophy.map((p) => (
          <Scatter
            key={p.component}
            name={p.component}
            data={[p]}
            fill={COMPONENT_COLORS[p.component]}
            shape={p.deterministic ? 'circle' : 'square'}
          >
            <LabelList
              dataKey="component"
              position={LEFT_LABELS.has(p.component) ? 'left' : 'right'}
              offset={10}
              fill={INK}
              fontSize={11}
            />
          </Scatter>
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  )
}

const allocationPhilosophyChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Component', 'Hourly CV', 'Observability', 'Method 2 treatment'],
    rows: allocationPhilosophy.map((p) => [
      p.component,
      p.cv.toFixed(2),
      p.observability.toFixed(2),
      p.deterministic ? 'Deterministic' : 'Batch proxy',
    ]),
  }),
}
export default allocationPhilosophyChart
