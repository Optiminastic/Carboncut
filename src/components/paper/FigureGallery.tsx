import Image from 'next/image'

import type { ResearchFigure } from '@/types/research'

const THUMB_SIZES = '(min-width: 1024px) 340px, (min-width: 640px) 45vw, 90vw'

/** Thumbnail index of every figure; each links to its interactive version in the full paper. */
export default function FigureGallery({ figures }: { figures: ResearchFigure[] }) {
  return (
    <section aria-labelledby="figures" className="bg-panel">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <h2
          id="figures"
          className="scroll-mt-20 font-serif text-3xl font-medium tracking-tight text-ink sm:text-4xl"
        >
          All {figures.length} figures
        </h2>
        <p className="mt-2 max-w-2xl text-base leading-relaxed text-ink-soft">
          Every figure in the paper is interactive. Choose one to open it in context, with hover
          values and the data behind it.
        </p>
        <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {figures.map((f) => (
            <li key={f.number}>
              <a
                href={`#figure-${f.number}`}
                className="group block h-full rounded-xl bg-white p-3 ring-1 ring-rule transition-shadow hover:ring-ink/40"
              >
                <div className="relative aspect-[16/10] overflow-hidden rounded-lg bg-white">
                  <Image
                    src={f.src}
                    alt=""
                    fill
                    sizes={THUMB_SIZES}
                    className="object-contain p-1 transition-transform duration-300 group-hover:scale-[1.02]"
                  />
                </div>
                <p className="mt-3 px-1 text-sm leading-snug text-ink-soft">
                  <span className="font-semibold text-ink">Figure {f.number}.</span> {f.caption}
                </p>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
