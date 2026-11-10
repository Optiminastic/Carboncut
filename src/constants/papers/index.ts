// Registry of published papers. Add new papers here to list them and generate their pages.
import type { ResearchPaper } from '@/types/research'

import { nearRealTimeCarbonAccountingPaper } from './nearRealTimeCarbonAccounting'

export const papers: ResearchPaper[] = [nearRealTimeCarbonAccountingPaper]

export function getPaper(slug: string): ResearchPaper | undefined {
  return papers.find((p) => p.slug === slug)
}
