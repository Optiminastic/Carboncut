'use client'

import type { InteractiveChartId } from '@/types/research'

import AllocationPhilosophy from './AllocationPhilosophy'
import BoundaryOmissions from './BoundaryOmissions'
import CapabilityMatrix from './CapabilityMatrix'
import ChartDataTable from './ChartDataTable'
import ComponentError from './ComponentError'
import ComponentShares from './ComponentShares'
import DataConfidence from './DataConfidence'
import EventHeatmap from './EventHeatmap'
import ExperimentalArchitecture from './ExperimentalArchitecture'
import GridCoupling from './GridCoupling'
import LegacyVsHybrid from './LegacyVsHybrid'
import LiteratureShare from './LiteratureShare'
import MethodError from './MethodError'
import Roadmap from './Roadmap'
import TelemetryCoverage from './TelemetryCoverage'
import type { ChartModule } from './theme'
import WeeklySeries from './WeeklySeries'

const CHARTS: Record<InteractiveChartId, ChartModule> = {
  'literature-share': LiteratureShare,
  'weekly-series': WeeklySeries,
  'boundary-omissions': BoundaryOmissions,
  'component-shares': ComponentShares,
  'capability-matrix': CapabilityMatrix,
  'method-error': MethodError,
  'allocation-philosophy': AllocationPhilosophy,
  'legacy-vs-hybrid': LegacyVsHybrid,
  'component-error': ComponentError,
  'event-heatmap': EventHeatmap,
  'experimental-architecture': ExperimentalArchitecture,
  'grid-coupling': GridCoupling,
  'telemetry-coverage': TelemetryCoverage,
  'data-confidence': DataConfidence,
  roadmap: Roadmap,
}

/** Renders an interactive figure and, for data-driven figures, its "Show data" table. */
export default function ResearchChart({ id }: { id: InteractiveChartId }) {
  const { Chart, table } = CHARTS[id]
  return (
    <div>
      <Chart />
      {table && <ChartDataTable table={table()} />}
    </div>
  )
}
