'use client'

import React, { useRef } from 'react'
import dynamic from 'next/dynamic'
import Image from 'next/image'
import { Maximize2, X } from 'lucide-react'

import type { ResearchFigure } from '@/types/research'

// Recharts is only needed for the interactive figures; keep it out of the initial bundle.
const ResearchChart = dynamic(() => import('./charts'), {
  ssr: false,
  loading: () => <div className="h-[300px] animate-pulse rounded-lg bg-neutral-100" />,
})

function FigureCaption({ figure }: { figure: ResearchFigure }) {
  return (
    <figcaption className="text-sm leading-relaxed text-ink-soft">
      <span className="font-semibold text-ink">Figure {figure.number}.</span> {figure.caption}
    </figcaption>
  )
}

function StaticFigure({ figure }: { figure: ResearchFigure }) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const alt = `Figure ${figure.number}: ${figure.caption}`

  // Close when the backdrop (the dialog element itself, outside its content) is clicked.
  const onDialogClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === dialogRef.current) dialogRef.current?.close()
  }

  return (
    <>
      <button
        type="button"
        onClick={() => dialogRef.current?.showModal()}
        className="group relative block w-full cursor-zoom-in overflow-hidden rounded-lg"
        aria-label={`Enlarge figure ${figure.number}`}
      >
        <Image
          src={figure.src}
          alt={alt}
          width={figure.width}
          height={figure.height}
          sizes="(min-width: 1024px) 760px, 100vw"
          className="h-auto w-full"
        />
        <span className="absolute right-3 top-3 rounded-md bg-white/90 p-1.5 text-neutral-700 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
          <Maximize2 className="h-4 w-4" aria-hidden="true" />
        </span>
      </button>
      <dialog
        ref={dialogRef}
        onClick={onDialogClick}
        aria-label={`Figure ${figure.number}`}
        className="m-auto w-[min(1200px,95vw)] max-w-none rounded-xl bg-white p-0 backdrop:bg-black/60"
      >
        <div className="relative p-4 sm:p-6">
          <button
            type="button"
            onClick={() => dialogRef.current?.close()}
            className="absolute right-3 top-3 rounded-md p-1.5 text-neutral-500 hover:bg-neutral-100 hover:text-ink"
            aria-label="Close"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
          <Image
            src={figure.src}
            alt={alt}
            width={figure.width}
            height={figure.height}
            sizes="95vw"
            className="h-auto w-full"
          />
          <FigureCaption figure={figure} />
        </div>
      </dialog>
    </>
  )
}

export default function ResearchFigureView({ figure }: { figure: ResearchFigure }) {
  return (
    <figure id={`figure-${figure.number}`} className="my-12 scroll-mt-24">
      <div className="rounded-xl bg-panel p-4 sm:p-6">
        {figure.interactive ? (
          <div className="rounded-lg bg-white p-3 sm:p-5">
            <ResearchChart id={figure.interactive} />
          </div>
        ) : (
          <StaticFigure figure={figure} />
        )}
      </div>
      <div className="mt-3 flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <FigureCaption figure={figure} />
        {figure.interactive && (
          <a
            href={figure.src}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-xs font-medium text-muted underline underline-offset-2 hover:text-ink"
          >
            Figure as printed
          </a>
        )}
      </div>
    </figure>
  )
}
