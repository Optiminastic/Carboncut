import Image from 'next/image'
import { ArrowDownToLine } from 'lucide-react'

import ReadingProgress from './ReadingProgress'

export default function SiteHeader({ pdfUrl }: { pdfUrl: string }) {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <a href="#top" className="flex items-center gap-2.5" aria-label="Back to top">
          <Image src="/CC.svg" alt="" width={28} height={28} className="h-7 w-auto" priority />
          <span className="text-[15px] font-semibold tracking-tight text-ink">
            CarbonCut <span className="font-normal text-muted">Research</span>
          </span>
        </a>
        <a
          href={pdfUrl}
          download
          className="inline-flex items-center gap-2 rounded-full border border-ink/15 px-4 py-1.5 text-sm font-medium text-ink transition-colors hover:border-ink hover:bg-ink hover:text-white"
        >
          <ArrowDownToLine className="h-4 w-4" aria-hidden="true" />
          <span>
            Download <span className="hidden sm:inline">the paper </span>(PDF)
          </span>
        </a>
      </div>
      <ReadingProgress />
    </header>
  )
}
