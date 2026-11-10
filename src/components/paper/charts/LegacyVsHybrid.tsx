import { type ChartModule } from './theme'

type Treatment = 'in' | 'out' | 'det' | 'proxy'

const TREATMENT: Record<Treatment, { label: string; className: string }> = {
  in: { label: 'In batch boundary', className: 'border-[#2a78d6] bg-[#eef4fc]' },
  out: {
    label: 'Outside boundary',
    className: 'border-neutral-300 bg-neutral-50 text-neutral-400',
  },
  det: { label: 'Deterministic', className: 'border-[#1baf7a] bg-[#e7f6f0]' },
  proxy: { label: 'Batch-allocated residual', className: 'border-[#eda100] bg-[#fdf6e6]' },
}

const COMPONENTS: { name: string; legacy: [Treatment, string]; hybrid: [Treatment, string] }[] = [
  { name: 'End-user devices', legacy: ['out', 'Excluded'], hybrid: ['proxy', 'Daily proxy'] },
  {
    name: 'Access / backbone',
    legacy: ['in', 'Annual total'],
    hybrid: ['proxy', 'Hourly volume, daily energy proxy'],
  },
  { name: 'CDN edge', legacy: ['out', 'Excluded'], hybrid: ['det', 'Hourly (CDN logs)'] },
  {
    name: 'Cloud compute',
    legacy: ['in', 'Annual total'],
    hybrid: ['det', 'Hourly (utilisation)'],
  },
  { name: 'Storage / DB', legacy: ['in', 'Annual total'], hybrid: ['proxy', 'Daily proxy'] },
]

function Column({
  title,
  side,
  outcome,
}: {
  title: string
  side: 'legacy' | 'hybrid'
  outcome: string
}) {
  return (
    <div className="rounded-xl border border-neutral-200 p-4">
      <p className="text-sm font-semibold text-[#080c04]">{title}</p>
      <ul className="mt-3 space-y-2">
        {COMPONENTS.map((c) => {
          const [treatment, detail] = c[side]
          return (
            <li
              key={c.name}
              className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm ${TREATMENT[treatment].className}`}
            >
              <span className="font-medium">{c.name}</span>
              <span className="text-right text-xs text-neutral-600">{detail}</span>
            </li>
          )
        })}
      </ul>
      <p className="mt-3 rounded-lg bg-[#080c04] px-3 py-2 text-center text-xs font-medium text-white">
        {outcome}
      </p>
    </div>
  )
}

function Chart() {
  return (
    <div>
      <div className="grid gap-4 md:grid-cols-2">
        <Column
          title="(A) Legacy batch accounting"
          side="legacy"
          outcome="× annual average factor → one annual figure"
        />
        <Column
          title="(B) Hybrid deterministic-batch"
          side="hybrid"
          outcome="× hourly regional grid intensity → hourly series"
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-neutral-600">
        {(Object.keys(TREATMENT) as Treatment[]).map((t) => (
          <span key={t} className="inline-flex items-center gap-1.5">
            <span className={`h-3 w-3 rounded border ${TREATMENT[t].className}`} />
            {TREATMENT[t].label}
          </span>
        ))}
      </div>
    </div>
  )
}

const legacyVsHybridChart: ChartModule = { Chart }
export default legacyVsHybridChart
