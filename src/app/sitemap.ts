import type { MetadataRoute } from 'next'

import { nearRealTimeCarbonAccountingPaper as paper } from '@/constants/papers/nearRealTimeCarbonAccounting'
import { SITE_URL } from '@/lib/site'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: SITE_URL,
      lastModified: new Date(paper.publishedDate),
      changeFrequency: 'monthly',
      priority: 1,
    },
  ]
}
