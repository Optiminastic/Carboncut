'use client'

import React, { useEffect, useMemo, useState } from 'react'

import { cn } from '@/lib/cn'
import type { ResearchSection } from '@/types/research'

const MAX_TOC_LEVEL = 2
// A heading becomes "current" once its top passes 30% of the viewport height.
const ACTIVE_LINE_RATIO = 0.3

interface TocItem {
  id: string
  label: string
  level: number
}

/** Scroll-spy: the active section is the last heading above the activation line. */
function useActiveSection(ids: string[]) {
  const [active, setActive] = useState(ids[0])

  useEffect(() => {
    let frame = 0
    const update = () => {
      frame = 0
      const line = window.innerHeight * ACTIVE_LINE_RATIO
      let current = ids[0]
      for (const id of ids) {
        const el = document.getElementById(id)
        if (el && el.getBoundingClientRect().top <= line) current = id
      }
      setActive(current)
    }
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update)
    }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (frame) window.cancelAnimationFrame(frame)
    }
  }, [ids])

  return active
}

function TocLinks({ items, active }: { items: TocItem[]; active?: string }) {
  return (
    <ol className="space-y-1">
      {items.map((item) => (
        <li key={item.id}>
          <a
            href={`#${item.id}`}
            className={cn(
              'block rounded-md border-l-2 py-1 pr-2 text-sm leading-snug transition-colors',
              item.level === 1 ? 'pl-3 font-medium' : 'pl-6 text-[13px]',
              item.id === active
                ? 'border-[#80b000] bg-[#b0ea1d]/15 text-[#080c04]'
                : 'border-transparent text-neutral-500 hover:text-[#080c04]'
            )}
            aria-current={item.id === active ? 'location' : undefined}
          >
            {item.label}
          </a>
        </li>
      ))}
    </ol>
  )
}

export default function ResearchTableOfContents({ sections }: { sections: ResearchSection[] }) {
  const items = useMemo<TocItem[]>(
    () => [
      { id: 'abstract', label: 'Abstract', level: 1 },
      ...sections
        .filter((s) => s.level <= MAX_TOC_LEVEL)
        .map((s) => ({ id: s.id, label: `${s.number} ${s.title}`, level: s.level })),
      { id: 'references', label: 'References', level: 1 },
    ],
    [sections]
  )
  const ids = useMemo(() => items.map((i) => i.id), [items])
  const active = useActiveSection(ids)

  return (
    <>
      {/* Mobile / tablet: collapsible list above the article */}
      <details className="mb-8 rounded-xl border border-neutral-200 bg-white p-4 lg:hidden">
        <summary className="cursor-pointer select-none text-sm font-semibold text-[#080c04]">
          Contents
        </summary>
        <nav aria-label="Table of contents" className="mt-3">
          <TocLinks items={items} />
        </nav>
      </details>

      {/* Desktop: sticky sidebar with scroll-spy */}
      <nav
        aria-label="Table of contents"
        className="sticky top-24 hidden max-h-[calc(100vh-7rem)] overflow-y-auto pb-8 lg:block"
      >
        <p className="mb-3 pl-3 text-xs font-semibold uppercase tracking-wider text-neutral-400">
          Contents
        </p>
        <TocLinks items={items} active={active} />
      </nav>
    </>
  )
}
