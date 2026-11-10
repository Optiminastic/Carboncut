import Image from 'next/image'
import Link from 'next/link'

import { MAIN_SITE_URL } from '@/lib/site'

export default function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-neutral-200/70 bg-white/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3" aria-label="CarbonCut Research home">
          <Image src="/CC.svg" alt="" width={32} height={32} className="h-8 w-auto" priority />
          <span className="text-sm font-semibold tracking-tight text-ink">
            CarbonCut <span className="text-neutral-400">Research</span>
          </span>
        </Link>
        <a
          href={MAIN_SITE_URL}
          className="rounded-lg bg-lime px-4 py-2 text-sm font-semibold text-ink transition hover:opacity-90"
        >
          Visit CarbonCut
        </a>
      </div>
    </header>
  )
}
