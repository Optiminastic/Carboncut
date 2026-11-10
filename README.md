# CarbonCut Research

CarbonCut research papers, published as interactive web articles.

Current paper:

- [Towards Near-Real-Time Carbon Accounting for Internet Data Transmission](src/constants/papers/nearRealTimeCarbonAccounting.ts) - served at `/papers/near-real-time-carbon-accounting` (preprint).

## Stack

- Next.js 16 (App Router, fully static output), React 19, TypeScript.
- Tailwind CSS v4.
- Recharts for the interactive figures (loaded only when a chart is on screen).

## Getting started

```bash
pnpm install
pnpm dev          # http://localhost:3000
pnpm build        # production build
pnpm typecheck
pnpm format
```

Requires Node.js 20 or newer and pnpm.

## Deploying on Vercel

1. Push this repository to GitHub.
2. In Vercel, choose **Add New > Project** and import the repository.
   The framework preset (Next.js) and build command (`pnpm build`) are detected automatically.
3. Optional: set `NEXT_PUBLIC_SITE_URL` to the final domain (for example `https://research.carboncut.co`).
   Without it, canonical URLs and the sitemap use the Vercel production domain.
4. Optional: add a custom domain under **Settings > Domains**.

No other environment variables or backend services are needed.

## Project structure

```
src/
  app/                      routes: home, /papers/[slug], sitemap, robots
  components/
    SiteHeader.tsx, SiteFooter.tsx
    paper/                  article layout, table of contents, figures, tables, charts
  constants/papers/
    index.ts                registry of published papers
    nearRealTimeCarbonAccounting.ts        paper content (text, figures, tables, references)
    nearRealTimeCarbonAccountingCharts.ts  data behind the interactive charts
  types/research.ts         content types
public/papers/<slug>/       figures (PNG) and the downloadable PDF
analysis/                   simulation and figure code used to produce the paper's results
```

## Adding a paper

1. Add a content module in `src/constants/papers/` that exports a `ResearchPaper`.
2. Register it in `src/constants/papers/index.ts`.
3. Put its figures and PDF in `public/papers/<slug>/`.

The page, home-page listing and sitemap entry are generated from the registry.
Interactive charts are paper-specific and live in `src/components/paper/ResearchCharts.tsx`.

## Reproducing the results

The `analysis/` folder contains the synthetic-data simulation behind the paper.
Emission factors come from the CarbonCut platform calculators.

```bash
cd analysis
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python sim.py      # writes results.json and series.npz (fixed seed)
.venv/bin/python figs.py     # writes figures/fig01.png ... fig15.png
```

To refresh the website from a new version of the manuscript:

1. Unzip the `.docx` into a folder.
2. Run `python gen_content.py <unzipped_docx_dir> ..` from `analysis/` to regenerate `src/constants/papers/*`.
3. Copy `analysis/figures/*.png` and the exported PDF into `public/papers/near-real-time-carbon-accounting/`.

`edit.py` is the script that filled the manuscript's placeholders, tables and figures from `results.json`.
