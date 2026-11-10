import type { Metadata } from 'next'

import ResearchPaperPage from '@/components/paper/ResearchPaperPage'
import { nearRealTimeCarbonAccountingPaper as paper } from '@/constants/papers/nearRealTimeCarbonAccounting'
import { PUBLISHER, SITE_URL } from '@/lib/site'

const DESCRIPTION = paper.abstract.slice(0, 300)
const OG_FIGURE = paper.figures[5]

export const metadata: Metadata = {
  title: { absolute: paper.title },
  description: DESCRIPTION,
  keywords: paper.keywords,
  authors: paper.authors.map((a) => ({ name: a.name })),
  alternates: { canonical: '/' },
  openGraph: {
    type: 'article',
    url: '/',
    title: paper.title,
    description: DESCRIPTION,
    publishedTime: paper.publishedDate,
    authors: paper.authors.map((a) => a.name),
    images: [{ url: OG_FIGURE.src, alt: `Figure ${OG_FIGURE.number}: ${OG_FIGURE.caption}` }],
  },
  twitter: { card: 'summary_large_image', title: paper.shortTitle, description: DESCRIPTION },
}

export default function HomePage() {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ScholarlyArticle',
    headline: paper.title,
    abstract: paper.abstract,
    keywords: paper.keywords.join(', '),
    datePublished: paper.publishedDate,
    creativeWorkStatus: paper.status,
    author: paper.authors.map((a) => ({
      '@type': 'Person',
      name: a.name,
      affiliation: a.affiliations.map((i) => ({
        '@type': 'Organization',
        name: paper.affiliations[i - 1],
      })),
    })),
    publisher: { '@type': 'Organization', name: PUBLISHER },
    encoding: {
      '@type': 'MediaObject',
      contentUrl: `${SITE_URL}${paper.pdfUrl}`,
      encodingFormat: 'application/pdf',
    },
    url: SITE_URL,
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <ResearchPaperPage paper={paper} />
    </>
  )
}
