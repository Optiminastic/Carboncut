import { type ChartModule } from './theme'

const CRITERIA = [
  'Temporal resolution',
  'Boundary completeness',
  'Grid-signal integration',
  'Auditability',
  'Deployability today',
  'Telemetry needed',
]
// Level 1-3: higher is more favourable for the criterion.
const ROWS: { method: string; cells: [string, 1 | 2 | 3][] }[] = [
  {
    method: 'Conventional batch',
    cells: [
      ['Annual', 1],
      ['Partial', 1],
      ['None', 1],
      ['Medium', 2],
      ['High', 3],
      ['Minimal', 3],
    ],
  },
  {
    method: 'Method 1: Operational hybrid',
    cells: [
      ['Event + monthly', 2],
      ['Full (proxies)', 3],
      ['Event sources', 2],
      ['High', 3],
      ['High', 3],
      ['Low', 3],
    ],
  },
  {
    method: 'Method 2: Hybrid deterministic-batch',
    cells: [
      ['Hourly / daily', 3],
      ['Full', 3],
      ['Hourly', 3],
      ['Medium', 2],
      ['Medium', 2],
      ['Medium', 2],
    ],
  },
  {
    method: 'Method 3: Full event-level',
    cells: [
      ['Event-level', 3],
      ['Full', 3],
      ['Hourly, path-level', 3],
      ['Medium', 2],
      ['Low', 1],
      ['Full', 1],
    ],
  },
]
// Least favourable red, moderate yellow, most favourable blue (matches the static figure).
const LEVEL_CLASS: Record<1 | 2 | 3, string> = {
  1: 'bg-[#c8372d] text-white',
  2: 'bg-[#f2c230] text-ink',
  3: 'bg-[#2a78d6] text-white',
}

function Chart() {
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-1 text-xs">
          <thead>
            <tr>
              <th className="w-44" />
              {CRITERIA.map((c) => (
                <th
                  key={c}
                  scope="col"
                  className="px-2 pb-1 text-center font-semibold text-neutral-600"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.method}>
                <th scope="row" className="pr-2 text-left font-semibold text-ink">
                  {row.method}
                </th>
                {row.cells.map(([text, level], i) => (
                  <td
                    key={CRITERIA[i]}
                    className={`rounded-md px-2 py-3 text-center font-medium ${LEVEL_CLASS[level]}`}
                  >
                    {text}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-neutral-600">
        {([1, 2, 3] as const).map((l) => (
          <span key={l} className="inline-flex items-center gap-1.5">
            <span className={`h-3 w-3 rounded ${LEVEL_CLASS[l]}`} />
            {l === 1 ? 'Least favourable' : l === 2 ? 'Moderate' : 'Most favourable'}
          </span>
        ))}
      </div>
    </div>
  )
}

const capabilityMatrixChart: ChartModule = { Chart }
export default capabilityMatrixChart
