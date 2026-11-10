// Types for research papers rendered as web articles under /research.

export type ResearchBlock =
  | { kind: 'p'; text: string }
  | { kind: 'figure'; figure: number }
  | { kind: 'table'; table: string }
  | { kind: 'equation' }

export interface ResearchSection {
  id: string
  number: string
  title: string
  /** 1 = top-level section, 2 = subsection, 3 = sub-subsection */
  level: number
  blocks: ResearchBlock[]
}

export type InteractiveChartId =
  | 'literature-share'
  | 'weekly-series'
  | 'boundary-omissions'
  | 'component-shares'
  | 'capability-matrix'
  | 'method-error'
  | 'allocation-philosophy'
  | 'legacy-vs-hybrid'
  | 'component-error'
  | 'event-heatmap'
  | 'experimental-architecture'
  | 'grid-coupling'
  | 'telemetry-coverage'
  | 'data-confidence'
  | 'roadmap'

export interface ResearchFigure {
  number: number
  src: string
  /** Intrinsic pixel size of the static image, used to reserve layout space. */
  width: number
  height: number
  caption: string
  /** When set, the figure is rendered as an interactive chart instead of the static image. */
  interactive?: InteractiveChartId
}

export interface ResearchTable {
  id: string
  number: number
  caption: string
  header: string[]
  rows: string[][]
}

export interface ResearchAuthor {
  name: string
  /** 1-based indexes into ResearchPaper.affiliations */
  affiliations: number[]
  corresponding?: boolean
}

export interface ResearchPaper {
  slug: string
  title: string
  shortTitle: string
  status: 'Preprint' | 'Published'
  statusNote: string
  publishedDate: string
  pdfUrl: string
  authors: ResearchAuthor[]
  affiliations: string[]
  abstract: string
  keywords: string[]
  sections: ResearchSection[]
  figures: ResearchFigure[]
  tables: ResearchTable[]
  backMatter: { label: string; text: string }[]
  references: string[]
}
