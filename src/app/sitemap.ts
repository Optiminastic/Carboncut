import type { MetadataRoute } from 'next'

import { papers } from '@/constants/papers'
import { paperPath, SITE_URL } from '@/lib/site'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: SITE_URL, changeFrequency: 'monthly', priority: 1 },
    ...papers.map((p) => ({
      url: `${SITE_URL}${paperPath(p.slug)}`,
      lastModified: new Date(p.publishedDate),
      changeFrequency: 'monthly' as const,
      priority: 0.9,
    })),
  ]
}
