import React from 'react'

import { brief } from '@/constants/papers/nearRealTimeCarbonAccountingBrief'

const PROSE = 'font-serif text-[1.1875rem] leading-[1.75] text-ink-soft'

function Row({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-4 border-t border-rule py-10 lg:grid-cols-[210px_minmax(0,1fr)] lg:gap-12">
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <div className="max-w-[70ch]">{children}</div>
    </div>
  )
}

/** Plain-language walkthrough of the whole paper, shown before the full text. */
export default function PaperBrief() {
  return (
    <section aria-labelledby="brief" className="mx-auto max-w-6xl px-4 pb-6 sm:px-6 lg:px-8">
      <h2
        id="brief"
        className="scroll-mt-20 pb-8 font-serif text-3xl font-medium tracking-tight text-ink sm:text-4xl"
      >
        The paper in brief
      </h2>

      <Row title="Why it matters">
        <div className="space-y-5">
          {brief.problem.map((p) => (
            <p key={p} className={PROSE}>
              {p}
            </p>
          ))}
        </div>
      </Row>

      <Row title="How it was tested">
        <div className="space-y-5">
          {brief.method.map((p) => (
            <p key={p} className={PROSE}>
              {p}
            </p>
          ))}
        </div>
      </Row>

      <Row title="What it found">
        <ul className="divide-y divide-rule">
          {brief.findings.map((f) => (
            <li
              key={f.value}
              className="grid gap-2 py-5 first:pt-0 last:pb-0 sm:grid-cols-[140px_minmax(0,1fr)] sm:gap-6"
            >
              <span className="font-serif text-4xl font-medium leading-none tracking-tight text-ink tabular-nums">
                {f.value}
              </span>
              <p className="text-base leading-relaxed text-ink-soft">{f.text}</p>
            </li>
          ))}
        </ul>
      </Row>

      <Row title="What it means">
        <ul className="divide-y divide-rule">
          {brief.implications.map((item) => (
            <li
              key={item.title}
              className="grid gap-2 py-5 first:pt-0 last:pb-0 sm:grid-cols-[140px_minmax(0,1fr)] sm:gap-6"
            >
              <h4 className="font-serif text-xl font-medium leading-snug text-ink">{item.title}</h4>
              <p className="text-base leading-relaxed text-ink-soft">{item.text}</p>
            </li>
          ))}
        </ul>
      </Row>

      <Row title="Limits">
        <p className={PROSE}>{brief.limits}</p>
        <a
          href="#full-paper"
          className="mt-8 inline-flex rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-ink-soft"
        >
          Read the full paper
        </a>
      </Row>
    </section>
  )
}
