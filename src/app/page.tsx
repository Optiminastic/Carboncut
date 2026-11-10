import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

import { papers } from '@/constants/papers'
import { paperPath } from '@/lib/site'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export default function HomePage() {
  return (
    <div className="bg-cream">
      <section className="mx-auto max-w-6xl px-4 pb-10 pt-16 sm:px-6 sm:pt-24 lg:px-8">
        <span className="rounded-full bg-ink px-3 py-1 text-sm font-medium text-lime">
          Research
        </span>
        <h1 className="mt-6 max-w-3xl text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl">
          Measuring digital emissions with the accuracy regulation now demands
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-neutral-600">
          Papers from the CarbonCut team on real-time, auditable carbon accounting for internet
          infrastructure, published as interactive web articles.
        </p>
      </section>

      <section aria-label="Papers" className="mx-auto max-w-6xl px-4 pb-24 sm:px-6 lg:px-8">
        <ul className="grid gap-6">
          {papers.map((paper) => (
            <li key={paper.slug}>
              <Link
                href={paperPath(paper.slug)}
                className="group block rounded-2xl border border-neutral-200 bg-white p-6 transition hover:border-ink sm:p-8"
              >
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-0.5 font-medium text-amber-800">
                    {paper.status}
                  </span>
                  <span className="text-neutral-500">{formatDate(paper.publishedDate)}</span>
                </div>
                <h2 className="mt-4 text-2xl font-bold leading-snug tracking-tight text-ink">
                  {paper.title}
                </h2>
                <p className="mt-2 text-sm text-neutral-500">
                  {paper.authors.map((a) => a.name).join(' and ')}
                </p>
                <p className="mt-4 line-clamp-3 leading-relaxed text-neutral-700">
                  {paper.abstract}
                </p>
                <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-ink">
                  Read the paper
                  <ArrowRight
                    className="h-4 w-4 transition-transform group-hover:translate-x-1"
                    aria-hidden="true"
                  />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
