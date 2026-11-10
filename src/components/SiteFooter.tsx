import { MAIN_SITE_URL } from '@/lib/site'

const FOOTER_LINKS = [
  { label: 'CarbonCut', href: MAIN_SITE_URL },
  { label: 'Methodology', href: `${MAIN_SITE_URL}/methodology` },
  { label: 'Blog', href: `${MAIN_SITE_URL}/blogs` },
  { label: 'Privacy Policy', href: `${MAIN_SITE_URL}/policy` },
]

export default function SiteFooter() {
  return (
    <footer className="bg-ink text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-12 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p className="text-sm text-white/70">
          © {new Date().getFullYear()} Carbon Tech International Limited
        </p>
        <nav aria-label="Footer">
          <ul className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {FOOTER_LINKS.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="text-white/80 transition-colors hover:text-lime">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </footer>
  )
}
