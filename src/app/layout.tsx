import type { Metadata } from 'next'
import { Instrument_Sans, Newsreader } from 'next/font/google'

import SiteFooter from '@/components/SiteFooter'
import SiteHeader from '@/components/SiteHeader'
import { nearRealTimeCarbonAccountingPaper as paper } from '@/constants/papers/nearRealTimeCarbonAccounting'
import { SITE_NAME, SITE_URL } from '@/lib/site'

import './globals.css'

const newsreader = Newsreader({
  subsets: ['latin'],
  variable: '--font-newsreader',
  style: ['normal', 'italic'],
  axes: ['opsz'],
})
const instrument = Instrument_Sans({ subsets: ['latin'], variable: '--font-instrument' })

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `${paper.shortTitle} | ${SITE_NAME}`, template: `%s | ${SITE_NAME}` },
  description: paper.abstract.slice(0, 300),
  icons: { icon: '/favicon.svg' },
  robots: { index: true, follow: true },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${newsreader.variable} ${instrument.variable}`}>
      <body className="font-sans antialiased">
        <SiteHeader pdfUrl={paper.pdfUrl} />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  )
}
