import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

import ResearchPaperPage from '@/components/paper/ResearchPaperPage'
import { getPaper, papers } from '@/constants/papers'
import { paperPath, SITE_URL } from '@/lib/site'

interface PageProps {
  params: Promise<{ slug: string }>
}

export const dynamicParams = false

export function generateStaticParams() {
  return papers.map((p) => ({ slug: p.slug }))
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const paper = getPaper((await params).slug)
  if (!paper) return {}
  const path = paperPath(paper.slug)
  const ogFigure = paper.figures.find((f) => !f.interactive) ?? paper.figures[0]
  return {
    title: paper.shortTitle,
    description: paper.abstract.slice(0, 300),
    keywords: paper.keywords,
    authors: paper.authors.map((a) => ({ name: a.name })),
    alternates: { canonical: path },
    openGraph: {
      type: 'article',
      url: path,
      title: paper.title,
      description: paper.abstract.slice(0, 300),
      publishedTime: paper.publishedDate,
      authors: paper.authors.map((a) => a.name),
      images: ogFigure
        ? [{ url: ogFigure.src, alt: `Figure ${ogFigure.number}: ${ogFigure.caption}` }]
        : [],
    },
    twitter: { card: 'summary_large_image', title: paper.shortTitle },
  }
}

export default async function PaperPage({ params }: PageProps) {
  const paper = getPaper((await params).slug)
  if (!paper) notFound()

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
    publisher: { '@type': 'Organization', name: 'Carbon Tech International Limited' },
    encoding: {
      '@type': 'MediaObject',
      contentUrl: `${SITE_URL}${paper.pdfUrl}`,
      encodingFormat: 'application/pdf',
    },
    url: `${SITE_URL}${paperPath(paper.slug)}`,
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
