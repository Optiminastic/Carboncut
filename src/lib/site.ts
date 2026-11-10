// Site-wide settings for the CarbonCut research site.

const DEFAULT_SITE_URL = 'http://localhost:3000'

function resolveSiteUrl() {
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL
  // Set automatically by Vercel at build time (production domain, without protocol).
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) {
    return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  }
  return DEFAULT_SITE_URL
}

/**
 * Absolute base URL for canonical links, Open Graph and the sitemap.
 * Override with NEXT_PUBLIC_SITE_URL (e.g. a custom domain); on Vercel it otherwise
 * falls back to the project's production domain.
 */
export const SITE_URL = resolveSiteUrl().replace(/\/$/, '')

export const SITE_NAME = 'CarbonCut Research'
export const SITE_DESCRIPTION =
  'Research from CarbonCut on real-time, auditable carbon accounting for digital infrastructure.'
export const MAIN_SITE_URL = 'https://carboncut.co'

export const paperPath = (slug: string) => `/papers/${slug}`
