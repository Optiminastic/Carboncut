import { PUBLISHER } from '@/lib/site'

export default function SiteFooter() {
  return (
    <footer className="border-t border-rule bg-panel">
      <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-muted sm:px-6 lg:px-8">
        <p>
          © {new Date().getFullYear()} {PUBLISHER}. This paper is a preprint and has not yet been
          peer reviewed.
        </p>
      </div>
    </footer>
  )
}
