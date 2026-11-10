import { dataConfidence } from '@/constants/papers/nearRealTimeCarbonAccountingCharts'

import { sequentialColor, type ChartModule } from './theme'

const SCALE_MAX = 16
const DARK_TEXT_THRESHOLD = 10

const cellText = (v: number) => (v === 0 ? 'known' : `±${v}%`)

function Chart() {
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] border-separate border-spacing-1 text-sm">
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
                <th scope="row" className="pr-2 text-left text-xs font-semibold text-[#080c04]">
                  {row.component}
                </th>
                {row.values.map((v, i) => (
                  <td
                    key={dataConfidence.signals[i]}
                    title={`${row.component}, ${dataConfidence.signals[i]}: ${v === 0 ? 'known exactly' : `±${v}% (1σ)`}`}
                    className="rounded-md px-2 py-3 text-center text-xs font-medium tabular-nums"
                    style={{
                      backgroundColor: sequentialColor(v / SCALE_MAX),
                      color: v > DARK_TEXT_THRESHOLD ? '#fff' : '#080c04',
                    }}
                  >
                    {cellText(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center gap-3 text-xs tabular-nums text-neutral-600">
        <span>Known</span>
        <span
          className="h-2.5 w-40 rounded"
          style={{
            background: `linear-gradient(to right, ${sequentialColor(0)}, ${sequentialColor(1)})`,
          }}
        />
        <span>±{SCALE_MAX}% assumed hourly uncertainty (1σ)</span>
      </div>
    </div>
  )
}

const dataConfidenceChart: ChartModule = { Chart }
export default dataConfidenceChart
