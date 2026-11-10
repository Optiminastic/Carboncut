import React from 'react'
import { ArrowDownToLine, CalendarDays, FileText, Info } from 'lucide-react'

import type { ResearchBlock, ResearchPaper, ResearchSection } from '@/types/research'

import ResearchFigureView from './ResearchFigureView'
import ResearchTableOfContents from './ResearchTableOfContents'
import ResearchTableView from './ResearchTableView'

const HEADING_CLASS: Record<number, string> = {
  1: 'mt-16 border-t border-neutral-200 pt-10 text-2xl font-bold tracking-tight text-[#080c04] sm:text-3xl',
  2: 'mt-12 text-xl font-semibold tracking-tight text-[#080c04]',
  3: 'mt-10 text-lg font-semibold text-[#080c04]',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function StatTile({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-xl bg-[#080c04] p-5">
      <p className="text-3xl font-bold tracking-tight text-[#b0ea1d] tabular-nums sm:text-4xl">
        {value}
      </p>
      <p className="mt-2 text-sm leading-snug text-white/75">{label}</p>
    </div>
  )
}

/** Method 3 attribution equation: CO2e_e = sum over components of E(k,e) x CI(k,t). */
function AttributionEquation() {
  return (
    <div
      className="my-8 overflow-x-auto rounded-xl border border-neutral-200 bg-neutral-50 px-6 py-5 text-center font-serif text-xl text-[#080c04]"
      role="math"
      aria-label="CO2e for event e equals the sum over circuit components k of E k e times CI k t"
    >
      CO<sub>2</sub>e<sub>e</sub> = <span className="mx-1 text-2xl">Σ</span>
      <sub className="mr-1 font-sans text-xs">k ∈ circuit</sub>( E<sub>k,e</sub> × CI
      <sub>k,t</sub> )
    </div>
  )
}

function Block({ block, paper }: { block: ResearchBlock; paper: ResearchPaper }) {
  switch (block.kind) {
    case 'p':
      return <p className="mt-5 text-[17px] leading-[1.8] text-neutral-800">{block.text}</p>
    case 'equation':
      return <AttributionEquation />
    case 'figure': {
      const figure = paper.figures.find((f) => f.number === block.figure)
      return figure ? <ResearchFigureView figure={figure} /> : null
    }
    case 'table': {
      const table = paper.tables.find((t) => t.id === block.table)
      return table ? <ResearchTableView table={table} /> : null
    }
  }
}

function Section({ section, paper }: { section: ResearchSection; paper: ResearchPaper }) {
  const Heading = (section.level === 1 ? 'h2' : section.level === 2 ? 'h3' : 'h4') as
    'h2' | 'h3' | 'h4'
  return (
    <section aria-labelledby={section.id}>
      <Heading id={section.id} className={`${HEADING_CLASS[section.level]} scroll-mt-24`}>
        <span className="mr-2 text-neutral-400 tabular-nums">{section.number}</span>
        {section.title}
      </Heading>
      {section.blocks.map((block, i) => (
        <Block key={i} block={block} paper={paper} />
      ))}
    </section>
  )
}

function Hero({ paper }: { paper: ResearchPaper }) {
  return (
    <header className="bg-[#fcfdf6] pb-14 pt-14 sm:pt-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className="rounded-full bg-[#080c04] px-3 py-1 font-medium text-[#b0ea1d]">
            Research
          </span>
          <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 font-medium text-amber-800">
            {paper.status}
          </span>
          <span className="inline-flex items-center gap-1.5 text-neutral-500">
            <CalendarDays className="h-4 w-4" aria-hidden="true" />
            {formatDate(paper.publishedDate)}
          </span>
        </div>

        <h1 className="mt-6 max-w-4xl text-3xl font-bold leading-tight tracking-tight text-[#080c04] sm:text-4xl lg:text-5xl">
          {paper.title}
        </h1>

        <div className="mt-6 text-neutral-700">
          <p className="text-base font-medium">
            {paper.authors.map((a, i) => (
              <span key={a.name}>
                {a.name}
                <sup className="ml-0.5 text-xs text-neutral-500">
                  {a.affiliations.join(',')}
                  {a.corresponding ? '*' : ''}
                </sup>
                {i < paper.authors.length - 1 ? ' and ' : ''}
              </span>
            ))}
          </p>
          <ol className="mt-2 space-y-0.5 text-sm text-neutral-500">
            {paper.affiliations.map((aff, i) => (
              <li key={aff}>
                <sup className="mr-1">{i + 1}</sup>
                {aff}
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={paper.pdfUrl}
            download
            className="inline-flex items-center gap-2 rounded-lg bg-[#b0ea1d] px-5 py-3 text-sm font-semibold text-[#080c04] transition hover:opacity-90"
          >
            <ArrowDownToLine className="h-4 w-4" aria-hidden="true" />
            Download PDF
          </a>
          <a
            href="#abstract"
            className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-5 py-3 text-sm font-semibold text-[#080c04] transition hover:border-[#080c04]"
          >
            <FileText className="h-4 w-4" aria-hidden="true" />
            Read the paper
          </a>
        </div>

        {paper.highlights.length > 0 && (
          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            {paper.highlights.map((h) => (
              <StatTile key={h.label} value={h.value} label={h.label} />
            ))}
          </div>
        )}
      </div>
    </header>
  )
}

export default function ResearchPaperPage({ paper }: { paper: ResearchPaper }) {
  return (
    <div className="bg-white">
      <Hero paper={paper} />

      <div className="mx-auto grid max-w-6xl grid-cols-[minmax(0,1fr)] gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[220px_minmax(0,1fr)] lg:px-8">
        <aside className="min-w-0">
          <ResearchTableOfContents sections={paper.sections} />
        </aside>

        <article className="min-w-0 max-w-3xl">
          <div
            className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"
            role="note"
          >
            <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <p>
              {paper.statusNote} Results are based on synthetic data generated with the emission
              factors used by the CarbonCut platform.
            </p>
          </div>

          <section aria-labelledby="abstract" className="mt-10">
            <h2
              id="abstract"
              className="scroll-mt-24 text-2xl font-bold tracking-tight text-[#080c04]"
            >
              Abstract
            </h2>
            <p className="mt-5 text-[17px] leading-[1.8] text-neutral-800">{paper.abstract}</p>
            <ul className="mt-6 flex flex-wrap gap-2" aria-label="Keywords">
              {paper.keywords.map((k) => (
                <li
                  key={k}
                  className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600"
                >
                  {k}
                </li>
              ))}
            </ul>
          </section>

          {paper.sections.map((section) => (
            <Section key={section.id} section={section} paper={paper} />
          ))}

          <section className="mt-16 space-y-4 border-t border-neutral-200 pt-10 text-sm leading-relaxed text-neutral-700">
            {paper.backMatter.map((item) => (
              <p key={item.label}>
                <span className="font-semibold text-[#080c04]">{item.label}: </span>
                {item.text}
              </p>
            ))}
          </section>

          <section aria-labelledby="references" className="mt-12">
            <h2
              id="references"
              className="scroll-mt-24 text-2xl font-bold tracking-tight text-[#080c04]"
            >
              References
            </h2>
            <ol className="mt-6 space-y-3 text-sm leading-relaxed text-neutral-700">
              {paper.references.map((ref) => (
                <li key={ref} className="pl-6 -indent-6">
                  {ref}
                </li>
              ))}
            </ol>
          </section>
        </article>
      </div>
    </div>
  )
}
