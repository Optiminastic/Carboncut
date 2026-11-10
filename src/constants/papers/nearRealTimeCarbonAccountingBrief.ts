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
    'Digital infrastructure produces an estimated 3-4% of global greenhouse gas emissions, about as much as aviation.',
    'Most organisations report these emissions once a year, by multiplying annual totals by average emission factors. That hides two things. Electricity gets cleaner and dirtier hour by hour, and several parts of the path a web page travels, such as content delivery networks, user devices and idle servers, are often left out entirely.',
    'Rules such as the EU CSRD, California SB 253 and IFRS S2 now expect emissions figures that are accurate and auditable. The paper asks how close to real time internet emissions can be measured, and how much more accurate that makes them.',
  ],
  ladderIntro:
    'The paper compares four ways of attributing emissions, each one step finer than the last. Choose a step to see how closely it tracks the true hourly emissions of a typical website.',
  method: [
    `The approaches were tested on ${h.workloads} simulated mid-size websites, each modelled hour by hour for a full year. A typical site has about ${h.medianMonthlyVisits.toLocaleString('en-GB')} visits a month, users in the UK, US, India and Germany, and servers in a London cloud region. Emission factors come from the CarbonCut platform's calculators.`,
    'Each approach was scored against a more detailed reference model of the same websites, by how far its hourly emissions were from the reference.',
  ],
  findings: [
    {
      value: `${h.batchMae}%`,
      text: `Annual batch accounting is off by ${h.batchMae}% hour to hour, and undercounts the yearly total by ${Math.abs(h.batchBias)}% because it leaves parts of the system out.`,
    },
    {
      value: `${h.errorRatio}×`,
      text: `Tracking compute and CDN hourly cuts the error to ${h.method2Mae}%, about ${Math.round(h.errorRatio)} times lower than annual batch accounting.`,
    },
    {
      value: `p = ${h.m2VsM3P.toFixed(2)}`,
      text: `Tracking every single event adds almost nothing on top (${method3.mae}% error, not a statistically significant difference), because compute makes up ${h.computeShare}% of a typical website's footprint.`,
    },
    {
      value: `${h.quarterCoverageRatio}×`,
      text: `Data coverage matters most. With hourly data for only a quarter of components, the error rises to ${h.quarterCoverageMethod2Mae}%, still ${h.quarterCoverageRatio} times better than batch accounting.`,
    },
    {
      value: `${h.peakHourShare}%`,
      text: `The 10% of hours when the grid is dirtiest produce ${h.peakHourShare}% of emissions. Annual averages hide these peaks, which are exactly when shifting or reducing load helps most.`,
    },
  ],
  implications: [
    {
      title: 'For reporting',
      text: `Start with the operational hybrid. It covers every material source, labels where each number came from, and keeps annual totals within ${h.method1AnnualError}% of the reference, well inside the 5% materiality threshold auditors typically apply.`,
    },
    {
      title: 'For operations',
      text: `Move to hourly tracking of compute and CDN. It brings the error down to ${h.method2Mae}% and shows when emissions peak, which makes carbon-aware scheduling possible.`,
    },
    {
      title: 'For the long term',
      text: 'Treat full event-level tracking as a benchmark. It shows where better provider data would help most, but it is not needed to get most of the benefit.',
    },
  ],
  limits:
    'The results come from simulated data for one type of platform, so they show how the methods compare rather than their exact real-world accuracy. The errors of the two finest methods depend on assumed data quality. The study covers electricity use only, not the emissions from manufacturing hardware. Testing against metered data from a live system is the next step.',
}
