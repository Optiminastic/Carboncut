import { type ChartModule } from './theme'

// Values as reported in the cited sources (see the paper's reference list).
const ROWS = [
  { source: 'Malmodin & Lundén (2018)', detail: 'ICT sector, 2015', low: 1.4, high: 1.4 },
  {
    source: 'Freitag et al. (2021)',
    detail: 'ICT incl. supply-chain adjustment',
    low: 2.1,
    high: 3.9,
  },
  { source: 'Range used in this paper', detail: 'Section 1', low: 3, high: 4 },
]
const AXIS_MAX = 5
const TICKS = [0, 1, 2, 3, 4, 5]

const label = (r: (typeof ROWS)[number]) =>
  r.low === r.high ? `${r.low.toFixed(1)}%` : `${r.low.toFixed(1)}-${r.high.toFixed(1)}%`
const toPct = (v: number) => `${(v / AXIS_MAX) * 100}%`

function Chart() {
  return (
    <div className="py-2">
      <ul className="space-y-5">
        {ROWS.map((r) => (
          <li
            key={r.source}
            className="grid gap-2 sm:grid-cols-[200px_minmax(0,1fr)] sm:items-center"
          >
            <div className="text-sm">
              <p className="font-medium text-ink">{r.source}</p>
              <p className="text-xs text-neutral-500">{r.detail}</p>
            </div>
            <div className="relative h-7" title={`${r.source}: ${label(r)}`}>
              <div className="absolute inset-y-[13px] left-0 right-0 rounded bg-neutral-100" />
              {r.low === r.high ? (
                <span
                  className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#2a78d6] ring-2 ring-white"
                  style={{ left: toPct(r.low) }}
                />
              ) : (
                <span
                  className="absolute top-1/2 h-3 -translate-y-1/2 rounded-full bg-[#2a78d6]"
                  style={{ left: toPct(r.low), width: toPct(r.high - r.low) }}
                />
              )}
              <span
                className="absolute top-1/2 -translate-y-1/2 pl-3 text-xs font-semibold tabular-nums text-ink"
                style={{ left: toPct(r.high) }}
              >
                {label(r)}
              </span>
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-4 grid sm:grid-cols-[200px_minmax(0,1fr)]">
        <span className="hidden sm:block" />
        <div>
          <div className="relative h-4 text-[11px] tabular-nums text-neutral-500">
            {TICKS.map((t) => (
              <span key={t} className="absolute -translate-x-1/2" style={{ left: toPct(t) }}>
                {t}%
              </span>
            ))}
          </div>
          <p className="mt-2 text-xs text-neutral-500">Share of global greenhouse gas emissions</p>
        </div>
      </div>
    </div>
  )
}

const literatureShareChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['Source', 'Scope', 'Share of global emissions'],
    rows: ROWS.map((r) => [r.source, r.detail, label(r)]),
  }),
}
export default literatureShareChart
