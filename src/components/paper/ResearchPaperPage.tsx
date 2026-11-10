import React from 'react'

import { brief } from '@/constants/papers/nearRealTimeCarbonAccountingBrief'
import type { ResearchBlock, ResearchPaper, ResearchSection } from '@/types/research'

import FigureGallery from './FigureGallery'
import PaperBrief from './PaperBrief'
import ResearchFigureView from './ResearchFigureView'
import ResearchTableOfContents from './ResearchTableOfContents'
import ResearchTableView from './ResearchTableView'
import ResolutionLadder from './ResolutionLadder'

const HEADING_CLASS: Record<number, string> = {
  1: 'mt-20 font-serif text-3xl font-medium tracking-tight text-ink sm:text-[2.125rem]',
  2: 'mt-14 font-serif text-2xl font-medium tracking-tight text-ink',
  3: 'mt-10 font-serif text-xl font-medium text-ink',
}
const BODY_TEXT = 'mt-5 font-serif text-[1.1875rem] leading-[1.75] text-ink-soft'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/** Method 3 attribution equation: CO2e_e = sum over components of E(k,e) x CI(k,t). */
function AttributionEquation() {
  return (
    <div
      className="my-8 overflow-x-auto rounded-xl bg-panel px-6 py-6 text-center font-serif text-2xl italic text-ink"
      role="math"
      aria-label="CO2e for event e equals the sum over circuit components k of E k e times CI k t"
    >
      CO<sub>2</sub>e<sub>e</sub> = <span className="mx-1 not-italic">Σ</span>
      <sub className="mr-1 font-sans text-xs not-italic">k ∈ circuit</sub>( E<sub>k,e</sub> × CI
      <sub>k,t</sub> )
    </div>
  )
}

function Block({ block, paper }: { block: ResearchBlock; paper: ResearchPaper }) {
  switch (block.kind) {
    case 'p':
      return <p className={BODY_TEXT}>{block.text}</p>
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
        <span className="mr-3 font-sans text-[0.6em] font-medium text-muted tabular-nums">
          {section.number}
        </span>
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
    <header
      id="top"
      className="mx-auto max-w-6xl scroll-mt-20 px-4 pb-16 pt-14 sm:px-6 sm:pt-20 lg:px-8"
    >
      <p className="text-sm text-muted">
        <span className="mr-2 rounded-full bg-amber-100 px-2.5 py-0.5 font-medium text-amber-900">
          {paper.status}
        </span>
        Published {formatDate(paper.publishedDate)}
      </p>

      <h1 className="mt-6 max-w-4xl font-serif text-4xl font-medium leading-[1.1] tracking-tight text-ink sm:text-5xl lg:text-[3.5rem]">
        {paper.title}
      </h1>

      <div className="mt-6 text-ink-soft">
        <p className="text-base font-medium text-ink">
          {paper.authors.map((a, i) => (
            <span key={a.name}>
              {a.name}
              <sup className="ml-0.5 text-xs text-muted">
                {a.affiliations.join(',')}
                {a.corresponding ? '*' : ''}
              </sup>
              {i < paper.authors.length - 1 ? ' and ' : ''}
            </span>
          ))}
        </p>
        <ol className="mt-1.5 space-y-0.5 text-sm text-muted">
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
          href="#full-paper"
          className="inline-flex rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-ink-soft"
        >
          Read the full paper
        </a>
        <a
          href="#figures"
          className="inline-flex rounded-full border border-ink/20 px-5 py-2.5 text-sm font-medium text-ink transition-colors hover:border-ink"
        >
          See all {paper.figures.length} figures
        </a>
      </div>

      <div className="mt-14">
        <h2 className="font-serif text-2xl font-medium tracking-tight text-ink">
          The resolution ladder
        </h2>
        <p className="mb-5 mt-2 max-w-2xl text-base leading-relaxed text-ink-soft">
          {brief.ladderIntro}
        </p>
        <ResolutionLadder />
      </div>
    </header>
  )
}

export default function ResearchPaperPage({ paper }: { paper: ResearchPaper }) {
  return (
    <div className="bg-white">
      <Hero paper={paper} />
      <PaperBrief />
      <FigureGallery figures={paper.figures} />

      <div
        id="full-paper"
        className="mx-auto grid max-w-6xl scroll-mt-16 grid-cols-[minmax(0,1fr)] gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[210px_minmax(0,1fr)] lg:px-8"
      >
        <aside className="min-w-0">
          <ResearchTableOfContents sections={paper.sections} />
        </aside>

        <article className="min-w-0 max-w-[70ch]">
          <p className="text-sm text-muted">The full paper</p>
          <section aria-labelledby="abstract" className="mt-2">
            <h2
              id="abstract"
              className="scroll-mt-24 font-serif text-3xl font-medium tracking-tight text-ink"
            >
              Abstract
            </h2>
            <p className={BODY_TEXT}>{paper.abstract}</p>
            <ul className="mt-6 flex flex-wrap gap-2" aria-label="Keywords">
              {paper.keywords.map((k) => (
                <li
                  key={k}
                  className="rounded-full bg-panel px-3 py-1 text-xs font-medium text-ink-soft"
                >
                  {k}
                </li>
              ))}
            </ul>
          </section>

          {paper.sections.map((section) => (
            <Section key={section.id} section={section} paper={paper} />
          ))}

          <section className="mt-20 space-y-4 border-t border-rule pt-10 text-sm leading-relaxed text-ink-soft">
            {paper.backMatter.map((item) => (
              <p key={item.label}>
                <span className="font-semibold text-ink">{item.label}: </span>
                {item.text}
              </p>
            ))}
          </section>

          <section aria-labelledby="references" className="mt-14">
            <h2
              id="references"
              className="scroll-mt-24 font-serif text-3xl font-medium tracking-tight text-ink"
            >
              References
            </h2>
            <ol className="mt-6 space-y-3 text-sm leading-relaxed text-ink-soft">
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
