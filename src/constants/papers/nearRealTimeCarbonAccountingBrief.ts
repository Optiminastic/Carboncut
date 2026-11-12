// Plain-language summary of the paper shown above the full text.
// Numbers are read from the generated simulation results so the summary never drifts from the paper.
import { methodError, researchHeadline as h } from './nearRealTimeCarbonAccountingCharts'

const [batch, method1, method2, method3] = methodError

export type LadderMethodKey = 'batch' | 'method1' | 'method2' | 'method3'

export interface LadderRung {
  key: LadderMethodKey
  name: string
  cadence: string
  error: number
  uses: string
}

/** The four approaches compared in the paper, from coarsest to finest resolution. */
export const resolutionLadder: LadderRung[] = [
  {
    key: 'batch',
    name: 'Annual batch',
    cadence: 'One figure per year',
    error: batch.mae,
    uses: 'Annual totals multiplied by average factors. CDN, devices and idle capacity are left out.',
  },
  {
    key: 'method1',
    name: 'Operational hybrid',
    cadence: 'Monthly, plus live web traffic',
    error: method1.mae,
    uses: 'Monthly cloud and CDN reports, with website traffic measured event by event.',
  },
  {
    key: 'method2',
    name: 'Hybrid deterministic',
    cadence: 'Hourly',
    error: method2.mae,
    uses: 'Compute and CDN tracked hour by hour against the live grid. Smaller parts estimated daily.',
  },
  {
    key: 'method3',
    name: 'Full event-level',
    cadence: 'Every event',
    error: method3.mae,
    uses: 'Every component tracked with full telemetry. A benchmark rather than something deployable today.',
  },
]

export const brief = {
  problem: [
    'Digital infrastructure produces an estimated 2-4% of global greenhouse gas emissions, about as much as aviation.',
    'Most organisations report these emissions once a year, by multiplying annual totals by average emission factors. That hides two things. Electricity gets cleaner and dirtier hour by hour, and several parts of the path a web page travels, such as content delivery networks, user devices and idle servers, are often left out entirely.',
    'Rules such as the EU CSRD, California SB 253 and IFRS S2 now expect emissions figures that are accurate and auditable. The paper asks how close to real time internet emissions can be measured, and how much more accurate that makes them.',
  ],
  ladderIntro:
    'The paper compares four ways of attributing emissions, each one step finer than the last. Choose a step to see how closely it tracks the true hourly emissions of a typical website.',
  method: [
    `The approaches were tested on a simulated mid-size SaaS platform: ${h.workloads} workloads, each modelled hour by hour for a full year. A typical workload has about ${h.medianMonthlyVisits.toLocaleString('en-GB')} visits a month, users in the UK, US, India and Germany, and servers in a London cloud region. Emission factors come from the CarbonCut platform's calculators.`,
    'Each approach was scored against a more detailed reference model of the same websites. To keep the test fair, the reference works differently from every method, and every method starts with realistic calibration errors (for example in server power and emission factors) that do not cancel out over a year.',
  ],
  findings: [
    {
      value: `${h.batchMae}%`,
      text: `Annual batch accounting is off by ${h.batchMae}% hour to hour, and undercounts the yearly total by ${Math.abs(h.batchBias)}% because it leaves parts of the system out and uses a storage factor that is far too low.`,
    },
    {
      value: `${h.errorRatio}×`,
      text: `Tracking compute and CDN hourly cuts the hourly error to ${h.method2Mae}%, about ${h.errorRatio} times lower than annual batch accounting.`,
    },
    {
      value: `< ${h.equivalenceMarginPp} pt`,
      text: `Tracking every single event adds very little on top (${h.method3Mae}% error). The two methods are within ${h.equivalenceMarginPp} percentage point of each other, because compute makes up ${h.computeShare}% of a typical website's footprint and both use the same compute model.`,
    },
    {
      value: `${h.controlMae}%`,
      text: `Timing matters on its own. Taking the hourly method's yearly totals and spreading them evenly over the year raises the hourly error from ${h.method2Mae}% to ${h.controlMae}%.`,
    },
    {
      value: `~${Math.round(h.method2AnnualError)}%`,
      text: `Finer timing does not fix yearly totals. All three new methods still miss the true annual figure by about ${Math.round(h.method1AnnualError)}-${Math.round(Math.max(h.method2AnnualError, h.method3AnnualError))}% on average, because that error comes from calibration and emission factors, not from timing.`,
    },
    {
      value: `${h.quarterCoverageRatio}×`,
      text: `With hourly data for only a quarter of components, the hourly error rises to ${h.quarterCoverageMethod2Mae}%, still ${h.quarterCoverageRatio} times better than batch accounting.`,
    },
  ],
  implications: [
    {
      title: 'For reporting',
      text: `Start with the operational hybrid. It covers every material source and labels where each number came from. Its annual totals are within ${h.method1AnnualError}% of the reference on average, but ${h.method1OverMaterialityShare}% of simulated sites still miss the ${h.materialityPct}% materiality threshold, so calibrate factors against metered or provider energy data before relying on the totals.`,
    },
    {
      title: 'For operations',
      text: `Move to hourly tracking of compute and CDN. It brings the hourly error down to ${h.method2Mae}% and shows when emissions peak, which makes carbon-aware scheduling possible.`,
    },
    {
      title: 'For the long term',
      text: 'Treat full event-level tracking as a benchmark. Better calibration of the compute energy model and network and CDN factors would help more than extra telemetry for minor components.',
    },
  ],
  limits: `The results come from simulated data for one type of platform, so they show how the methods compare rather than their exact real-world accuracy. The size of the calibration errors is assumed, and halving or doubling it moves the hourly method between about ${Math.round(h.halfSystematicMethod2Mae)}% and ${Math.round(h.doubleSystematicMethod2Mae)}% error. Network energy is treated as proportional to data, the platform grid averages for India and Germany are lower than official figures, and only electricity use is covered, not hardware manufacturing. Testing against metered data from a live system is the next step.`,
}
