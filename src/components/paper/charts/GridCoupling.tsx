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

import { gridCoupling } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import { AXIS, GRID, SERIES, TICK, tooltipStyle, type ChartModule } from './theme'

const SYNC_ID = 'grid-coupling'
const HOUR_TICKS = [0, 12, 24, 36, 48, 60, 71]
const labelFor = (h: number) => gridCoupling[h]?.label ?? ''

function Chart() {
  return (
    <div>
      <p className="mb-1 text-xs font-medium text-neutral-500">
        Grid carbon intensity at the origin (gCO₂/kWh)
      </p>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart
          data={gridCoupling}
          syncId={SYNC_ID}
          margin={{ top: 4, right: 12, bottom: 0, left: 0 }}
        >
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="hour" ticks={HOUR_TICKS} tick={false} stroke={GRID} height={4} />
          <YAxis tick={TICK} stroke={GRID} width={44} domain={['auto', 'auto']} />
          <Tooltip
            {...tooltipStyle}
            labelFormatter={labelFor}
            formatter={(v: number) => [`${v.toFixed(0)} gCO₂/kWh`, 'Grid intensity']}
          />
          <Line
            dataKey="gridIntensity"
            name="Grid intensity"
            stroke={AXIS}
            strokeWidth={1.75}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="mb-1 mt-4 text-xs font-medium text-neutral-500">
        Attributed emissions (g CO₂e per hour)
      </p>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart
          data={gridCoupling}
          syncId={SYNC_ID}
          margin={{ top: 4, right: 12, bottom: 4, left: 0 }}
        >
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis
            dataKey="hour"
            ticks={HOUR_TICKS}
            tick={TICK}
            stroke={GRID}
            tickFormatter={(h: number) => `${h}h`}
          />
          <YAxis tick={TICK} stroke={GRID} width={44} />
          <Tooltip
            {...tooltipStyle}
            labelFormatter={labelFor}
            formatter={(v: number) => `${v.toFixed(2)} g`}
          />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
          <Line
            dataKey="reference"
            name="Reference"
            stroke={SERIES.reference}
            strokeWidth={1.5}
            dot={false}
          />
          <Line dataKey="batch" name="Batch" stroke={SERIES.batch} strokeWidth={2} dot={false} />
          <Line
            dataKey="method2"
            name="Method 2"
            stroke={SERIES.method2}
            strokeWidth={2}
            dot={false}
          />
          <Line
            dataKey="method3"
            name="Method 3"
            stroke={SERIES.method3}
            strokeWidth={1.5}
            strokeDasharray="5 3"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

const gridCouplingChart: ChartModule = {
  Chart,
  table: () => ({
    header: [
      'Hour (UTC)',
      'Grid intensity (gCO₂/kWh)',
      'Reference (g)',
      'Batch (g)',
      'Method 2 (g)',
      'Method 3 (g)',
    ],
    rows: gridCoupling.map((r) => [
      r.label,
      r.gridIntensity.toFixed(0),
      r.reference.toFixed(2),
      r.batch.toFixed(2),
      r.method2.toFixed(2),
      r.method3.toFixed(2),
    ]),
  }),
}
export default gridCouplingChart
