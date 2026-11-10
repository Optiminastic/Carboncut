# CarbonCut Research

A single-page site for the CarbonCut preprint _Towards Near-Real-Time Carbon Accounting for Internet Data Transmission_.

The page has three parts:

- An interactive resolution ladder that shows the same week of emissions at four levels of detail.
- "The paper in brief", a plain-language walkthrough of the problem, method, findings and limits.
- The full paper with all 15 figures as interactive charts and a downloadable PDF.

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
  app/                      the page (/), sitemap, robots
  components/
    SiteHeader.tsx, SiteFooter.tsx, ReadingProgress.tsx
    paper/                  hero ladder, brief, article layout, table of contents, figures, tables
    paper/charts/           one module per interactive figure, plus a shared theme and registry
  constants/papers/
    nearRealTimeCarbonAccounting.ts        paper content (text, figures, tables, references)
    nearRealTimeCarbonAccountingCharts.ts  data behind the interactive charts and headline numbers
    nearRealTimeCarbonAccountingBrief.ts   plain-language summary and ladder copy
  types/research.ts         content types
public/papers/<slug>/       figures (PNG) and the downloadable PDF
analysis/                   simulation and figure code used to produce the paper's results
```

## Editing the summary

The plain-language summary lives in `src/constants/papers/nearRealTimeCarbonAccountingBrief.ts`.
Its numbers are read from the generated chart data, so re-running the analysis updates them automatically.

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
