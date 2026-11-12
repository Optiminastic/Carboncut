import { dataConfidence } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import { sequentialColor, type ChartModule } from './theme'

// Colour encodes the systematic (per-workload) uncertainty, which does not average out over a year.
const SCALE_MAX = 30
const DARK_TEXT_THRESHOLD = 18
const ROUTING_SIGNAL_INDEX = 2

type Cell = { systematic: number; hourly: number } | null

function cellText(v: Cell, isRouting: boolean) {
  if (!v) return 'known'
  if (isRouting) return `±${v.systematic} pts mix`
  if (v.systematic === 0) return `±${v.hourly}% hourly`
  if (v.hourly === 0) return `±${v.systematic}% fixed`
  return `±${v.systematic}% / ±${v.hourly}%`
}

function cellTitle(component: string, signal: string, v: Cell, isRouting: boolean) {
  if (!v) return `${component}, ${signal}: known exactly`
  if (isRouting)
    return `${component}, ${signal}: routing mix uncertain by ±${v.systematic} percentage points`
  return `${component}, ${signal}: systematic ±${v.systematic}%, hourly ±${v.hourly}% (1σ)`
}

function Chart() {
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-separate border-spacing-1 text-sm">
          <thead>
            <tr>
              <th className="w-24" />
              {dataConfidence.signals.map((s) => (
                <th
                  key={s}
                  scope="col"
                  className="px-2 pb-1 text-center text-xs font-semibold text-neutral-600"
                >
                  {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataConfidence.rows.map((row) => (
              <tr key={row.component}>
                <th scope="row" className="pr-2 text-left text-xs font-semibold text-ink">
                  {row.component}
                </th>
                {row.values.map((v: Cell, i) => {
                  const signal = dataConfidence.signals[i]
                  const isRouting = i === ROUTING_SIGNAL_INDEX
                  const systematic = v?.systematic ?? 0
                  return (
                    <td
                      key={signal}
                      title={cellTitle(row.component, signal, v, isRouting)}
                      className="rounded-md px-2 py-3 text-center text-xs font-medium tabular-nums"
                      style={{
                        backgroundColor: sequentialColor(systematic / SCALE_MAX),
                        color: systematic > DARK_TEXT_THRESHOLD ? '#fff' : '#15221c',
                      }}
                    >
                      {cellText(v, isRouting)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs tabular-nums text-neutral-600">
        <span>Known</span>
        <span
          className="h-2.5 w-40 rounded"
          style={{
            background: `linear-gradient(to right, ${sequentialColor(0)}, ${sequentialColor(1)})`,
          }}
        />
        <span>±{SCALE_MAX}% systematic uncertainty (1σ). Cells read systematic / hourly.</span>
      </div>
    </div>
  )
}

const dataConfidenceChart: ChartModule = { Chart }
export default dataConfidenceChart
