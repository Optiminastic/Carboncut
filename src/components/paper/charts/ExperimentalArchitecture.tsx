import { ArrowDown, ArrowRight } from 'lucide-react'

import { type ChartModule } from './theme'

// Annual average grid intensity used by the CarbonCut platform for each market (gCO2/kWh).
const MARKETS = [
  { name: 'United Kingdom', intensity: 162 },
  { name: 'United States', intensity: 342 },
  { name: 'India', intensity: 589 },
  { name: 'Germany', intensity: 298 },
]

const Box = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`rounded-lg border px-3 py-2 text-center text-xs ${className}`}>{children}</div>
)

const Arrow = () => (
  <>
    <ArrowRight className="hidden h-4 w-4 shrink-0 text-neutral-400 md:block" aria-hidden="true" />
    <ArrowDown className="mx-auto h-4 w-4 shrink-0 text-neutral-400 md:hidden" aria-hidden="true" />
  </>
)

function Chart() {
  return (
    <div className="grid gap-4 md:grid-cols-[minmax(0,1.7fr)_auto_minmax(0,1fr)] md:items-center">
      <ul className="space-y-3" aria-label="User markets">
        {MARKETS.map((m) => (
          <li
            key={m.name}
            className="grid grid-cols-[minmax(0,1.25fr)_auto_minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2"
          >
            <Box className="border-[#2a78d6] bg-[#eef4fc]">
              <p className="text-[10px] uppercase tracking-wide text-neutral-500">Users</p>
              <p className="font-semibold text-[#080c04]">{m.name}</p>
              <p className="text-neutral-600">{m.intensity} gCO₂/kWh</p>
            </Box>
            <ArrowRight className="h-4 w-4 text-neutral-400" aria-hidden="true" />
            <Box className="border-[#eda100] bg-[#fdf6e6]">Access ISP + backbone</Box>
            <ArrowRight className="h-4 w-4 text-neutral-400" aria-hidden="true" />
            <Box className="border-[#1baf7a] bg-[#e7f6f0]">CDN edge (local grid)</Box>
          </li>
        ))}
      </ul>
      <Arrow />
      <div className="space-y-3">
        <Box className="border-neutral-300 bg-neutral-50 text-neutral-700">
          Hourly grid-intensity signal for all four markets
        </Box>
        <Box className="border-[#eb6834] bg-[#fdf0ea] py-4">
          <p className="text-sm font-semibold text-[#080c04]">Origin cloud region</p>
          <p className="text-neutral-600">London, UK grid</p>
          <ul className="mt-2 space-y-0.5 text-neutral-700">
            <li>Compute instances</li>
            <li>Object storage + database</li>
            <li>Idle provisioned capacity</li>
          </ul>
        </Box>
        <Box className="border-neutral-300 bg-neutral-50 text-neutral-700">
          Telemetry: page-view tracker, CDN logs, utilisation, provider reports
        </Box>
      </div>
    </div>
  )
}

const experimentalArchitectureChart: ChartModule = {
  Chart,
  table: () => ({
    header: ['User market', 'Annual grid intensity (gCO₂/kWh)'],
    rows: MARKETS.map((m) => [m.name, String(m.intensity)]),
  }),
}
export default experimentalArchitectureChart
