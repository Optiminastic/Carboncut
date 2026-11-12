"""Generate the website content + chart data TS modules from the filled manuscript and results.

Usage: python gen_content.py <unpacked_docx_dir> <repo_root>
Run sim.py and figs.py first (this reads results.json, series.npz and figures/).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SLUG = "near-real-time-carbon-accounting"

# heading text in the docx -> (number, id)
HEADINGS = {
    "Introduction": ("1", "introduction"),
    "Data and Methodology": ("2", "data-and-methodology"),
    "Data": ("2.1", "data"),
    "Methods": ("2.2", "methods"),
    "Conceptualisation of the Internet Transmission Circuit": ("2.2.1", "transmission-circuit"),
    "Baseline: Conventional Batch Accounting": ("2.2.2", "baseline-batch"),
    "Method 1: Operational Hybrid Resolution": ("2.2.3", "method-1"),
    "Method 2: Hybrid Deterministic-Batch Attribution": ("2.2.4", "method-2"),
    "Method 3: Full Event Level Deterministic Attribution": ("2.2.5", "method-3"),
    "2.3 Experimental Setup": ("2.3", "experimental-setup"),
    "Results": ("3", "results"),
    "Overall Attribution Accuracy": ("3.1", "overall-accuracy"),
    "Component-Level Error Behaviour": ("3.2", "component-error"),
    "Temporal Responsiveness and Peak Capture": ("3.3", "temporal-responsiveness"),
    "Resolution Ladder and Marginal Gains": ("3.4", "resolution-ladder"),
    "Marginal Gains along the Resolution Ladder": ("3.5", "marginal-gains"),
    "Separability and Uncertainty of Method Performance": ("3.6", "separability"),
    "Component Contributions to Accuracy Gains": ("3.7", "component-contributions"),
    "Error Direction and Implications for Reporting": ("3.8", "error-direction"),
    "Sensitivity to Modelling Assumptions": ("3.9", "sensitivity"),
    "Critical Appraisal of the Results": ("3.10", "critical-appraisal"),
    "Discussion": ("4", "discussion"),
    "Conclusion": ("5", "conclusion"),
}

# figure placement: insert after the paragraph that starts with this text
FIGURE_AFTER = {
    1: "The internet and associated digital infrastructure",
    4: "Hourly grid carbon intensity was synthesised",
    5: "This study develops a resolution-based",
    3: "Internet data transmission is conceptualised",
    2: "Annualised batch methods tend to smooth",
    8: "At system level, Method 2 extends",
    11: "Experimental evaluation focuses on comparing",
    14: "Each estimator carries two kinds of error",
    6: "Method 1, which combines event",
    9: "Beyond aggregate MAE, the analysis examines",
    10: "All three proposed methods capture temporal",
    12: "Temporal responsiveness is evaluated",
    13: "To move beyond aggregate error values",
    7: "decomposes the error reduction achieved",
    15: "The final stage, full event",
}
TABLE_AFTER = {"table-1": "To move beyond aggregate error values", "table-2": "Because the results are derived"}
INTERACTIVE = {
    1: "literature-share", 2: "weekly-series", 3: "boundary-omissions", 4: "component-shares",
    5: "capability-matrix", 6: "method-error", 7: "allocation-philosophy", 8: "legacy-vs-hybrid",
    9: "component-error", 10: "event-heatmap", 11: "experimental-architecture", 12: "grid-coupling",
    13: "telemetry-coverage", 14: "data-confidence", 15: "roadmap",
}
# Assumed observability (telemetry quality, 0-1) per component; matches figs.py Figure 7.
OBSERVABILITY = {"Compute": 0.9, "CDN": 0.85, "Storage": 0.6, "Network": 0.3, "Device": 0.25}
DETERMINISTIC_IN_M2 = {"Compute", "CDN"}
CONFIDENCE_SIGNALS = ["Activity volume", "Energy model", "Routing / location", "Grid intensity"]
INTERACTIVE_CAPTION = {
    2: "One week of hourly emissions for an example workload: the reference series, conventional batch accounting "
       "(annual) and Method 1 (monthly totals plus event-level web traffic). Batch methods smooth emissions over time, "
       "masking both load-driven and grid-intensity-driven variability.",
    6: "Hourly attribution error (WAPE) across 200 synthetic workloads. Bars show the mean; whiskers show the "
       "5th-95th percentile range. The grey control spreads Method 2's annual totals evenly over the year, so the gap "
       "between it and Method 2 is the effect of temporal resolution alone. Hover for the annual-total error.",
    9: "Component-level hourly error under conventional batch accounting and Method 2. Storage and CDN improve most in "
       "relative terms; compute, at over 80% of emissions, contributes most of the aggregate gain.",
    13: "Hourly attribution error of Method 2 as telemetry coverage of its deterministic components increases, against "
        "the other approaches on the same workloads. Beyond about 80% coverage the remaining error is set by "
        "calibration, not coverage.",
}
CAPTION_WEB = {
    3: "Structural omissions introduced by conventional subsystem-focused accounting.",
    5: "Methodological capabilities of existing and proposed approaches.",
    7: "Allocation philosophy underpinning the hybrid approach.",
    10: "Temporal granularity achievable under full event-level attribution.",
    12: "Coupling between grid carbon intensity and attributed emissions under near-real-time methods.",
}
EQUATION_MARKERS = ("For a given event", ",", "where ")


def clean(s: str) -> str:
    s = s.replace("​", "").replace("—", "-").replace("–", "-").replace("&amp;", "&")
    s = s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
    return re.sub(r"\s+", " ", s).strip()


def paragraphs(doc: str):
    for p in re.findall(r"<w:p[ >].*?</w:p>", doc, re.S):
        if "<w:tbl" in p:
            continue
        x = p.replace("<w:noBreakHyphen/>", "<w:t>-</w:t>")
        text = clean("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", x)))
        yield text, ("<m:oMath" in p), ("<w:drawing" in p)


def ts(v) -> str:
    return json.dumps(v, ensure_ascii=False, indent=2)


def build_sections(doc: str):
    body = doc.split("<w:body>")[1]
    body = re.sub(r"<w:tbl>.*?</w:tbl>", "", body, flags=re.S)
    paras = list(paragraphs(body))
    start = next(i for i, (t, _, _) in enumerate(paras) if t == "Introduction")
    end = next(i for i, (t, _, _) in enumerate(paras) if t.startswith("Acknowledgement"))
    sections, cur = [], None
    for text, has_math, _ in paras[start:end]:
        if not text and not has_math:
            continue
        norm = text.replace("–", "-")
        if norm in HEADINGS:
            num, sid = HEADINGS[norm]
            title = norm.replace("2.3 ", "")
            cur = {"id": sid, "number": num, "title": title, "level": num.count(".") + 1, "blocks": []}
            sections.append(cur)
            continue
        if has_math:
            if text.startswith("For a given event"):
                cur["blocks"].append({"kind": "p", "text": "Method 3 defines a fully deterministic event-level "
                                      "attribution framework in which emissions are attributed to individual "
                                      "transmission events across the entire circuit using timestamped, "
                                      "component-level energy estimates. For a given event e, emissions are "
                                      "calculated as"})
                cur["blocks"].append({"kind": "equation"})
            elif text.startswith("where"):
                cur["blocks"].append({"kind": "p", "text": "where E(k,e) denotes the energy attributable to "
                                      "component k for event e, and CI(k,t) is the carbon intensity of the "
                                      "electricity supplying component k at time t."})
            continue
        if text == "," or re.match(r"Table \d\.", text):
            continue  # stray equation punctuation / table captions (rendered with the table itself)
        block = {"kind": "p", "text": text}
        cur["blocks"].append(block)
        for n, key in FIGURE_AFTER.items():
            if text.startswith(key) or key in text[:80]:
                cur["blocks"].append({"kind": "figure", "figure": n})
        for tid, key in TABLE_AFTER.items():
            if text.startswith(key):
                cur["blocks"].append({"kind": "table", "table": tid})
    placed = sorted(b["figure"] for s in sections for b in s["blocks"] if b["kind"] == "figure")
    assert placed == list(range(1, 16)), placed
    tables = [b["table"] for s in sections for b in s["blocks"] if b["kind"] == "table"]
    assert tables == ["table-1", "table-2"], tables
    return sections


def build_meta(doc: str):
    paras = [t for t, _, _ in paragraphs(doc.split("<w:body>")[1])]
    after_abstract = [t for t in paras[paras.index("Abstract") + 1:] if t]
    abstract = after_abstract[0]
    keywords = after_abstract[1].replace("Keywords:", "").strip()
    assert abstract.startswith("Digital infrastructure") and after_abstract[1].startswith("Keywords:")
    refs_start = next(i for i, t in enumerate(paras) if t.startswith("References"))
    refs_end = paras.index("Figures")
    refs = [t for t in paras[refs_start + 1:refs_end] if t]
    tail = {k: next(t for t in paras if t.startswith(k)) for k in
            ["Acknowledgement", "Funding", "Data Availability", "Conflict of interest"]}
    ack_i = paras.index(tail["Acknowledgement"])
    tail["Acknowledgement"] = tail["Acknowledgement"] + " " + paras[ack_i + 1]
    captions = {}
    for t in paras[refs_end + 1:]:
        m = re.match(r"Figure (\d+)A? ?(and 8B\.)? ?(.*)", t)
        if m and t and int(m.group(1)) not in captions:
            captions[int(m.group(1))] = t
    return abstract, [k.strip() for k in keywords.split(";")], refs, tail


def figure_captions(doc: str):
    """Captions as they appear under each embedded image (may span several paragraphs)."""
    body = doc.split("<w:body>")[1]
    paras = list(paragraphs(body))
    caps, i = {}, 0
    while i < len(paras):
        if paras[i][2]:
            j, parts = i + 1, []
            while j < len(paras) and not paras[j][0] and not paras[j][2]:
                j += 1
            while j < len(paras) and not paras[j][2] and paras[j][0]:
                parts.append(paras[j][0])
                j += 1
            n = len(caps) + 1
            cap = " ".join(parts)
            cap = re.sub(r"^Figure \d+A? and 8B\.\s*", "", cap)
            cap = re.sub(r"^Figure \d+\s*", "", cap)
            caps[n] = cap[0].upper() + cap[1:]
            i = j
        else:
            i += 1
    assert len(caps) == 15
    return caps


def table_rows(doc: str, index: int):
    tbl = re.findall(r"<w:tbl>.*?</w:tbl>", doc, re.S)[index]
    rows = []
    for tr in re.findall(r"<w:tr[ >].*?</w:tr>", tbl, re.S):
        cells = []
        for tc in re.findall(r"<w:tc>.*?</w:tc>", tr, re.S):
            x = tc.replace("<w:noBreakHyphen/>", "<w:t>-</w:t>")
            cells.append(clean(" ".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", x))))
        rows.append(cells)
    return rows


def table_caption(doc: str, prefix: str):
    for t, _, _ in paragraphs(doc):
        if t.startswith(prefix):
            return re.sub(r"^Table \d\.\s*", "", t)
    raise KeyError(prefix)


def chart_data():
    r = json.loads((HERE / "results.json").read_text())
    s = np.load(HERE / "series.npz")
    start = (59 + (7 - 59 % 7) % 7) * 24
    sl = slice(start, start + 7 * 24)
    truth = sum(s[f"truth_{c}"] for c in r["components"])[sl] * 1000
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly = [{"hour": i, "label": f"{days[i // 24]} {i % 24:02d}:00", "reference": round(float(truth[i]), 2),
               "batch": round(float(s["est_Batch"][sl][i] * 1000), 2),
               "method1": round(float(s["est_Method_1"][sl][i] * 1000), 2),
               "method2": round(float(s["est_Method_2"][sl][i] * 1000), 2),
               "method3": round(float(s["est_Method_3"][sl][i] * 1000), 2)} for i in range(7 * 24)]
    methods = []
    for key, name in [("Batch", "Conventional batch"), ("Method 1", "Method 1"), ("Method 2", "Method 2"),
                      ("Method 3", "Method 3")]:
        m = r["summary"][key]
        methods.append({"method": name, "mae": round(m["mae"], 1), "p5": round(m["p5"], 1), "p95": round(m["p95"], 1),
                        "annualError": round(m["annual_abs"], 1)})
    comps = [{"component": c, "batch": round(r["summary"]["Batch"]["comp"][c], 1),
              "method2": round(r["summary"]["Method 2"]["comp"][c], 1)} for c in r["components"]]
    cov = [{"coverage": round(c["coverage"] * 100), "method2": round(c["mae_m2"], 1)} for c in r["coverage"]]
    refs = {k: round(float(np.mean([c[key] for c in r["coverage"]])), 1) for k, key in
            [("batch", "mae_batch"), ("method1", "mae_m1"), ("method3", "mae_m3")]}
    extras = extra_chart_data(r, s, start)
    b, m2 = r["summary"]["Batch"]["mae"], r["summary"]["Method 2"]["mae"]
    headline = {"batchMae": round(b, 1), "method2Mae": round(m2, 1), "errorRatio": round(b / m2, 1),
                "method3Mae": round(r["summary"]["Method 3"]["mae"], 1),
                "controlMae": round(r["summary"]["Annualised Method 2"]["mae"], 1),
                "equivalenceMarginPp": r["equivalence"]["hourly"]["margin"],
                "m2VsM3MeanDiffPp": round(r["equivalence"]["hourly"]["mean_diff"], 1),
                "method3AnnualError": round(r["summary"]["Method 3"]["annual_abs"], 1),
                "materialityPct": r["materiality_pct"],
                "method1OverMaterialityShare": round(r["summary"]["Method 1"]["share_over_materiality"]),
                "method2OverMaterialityShare": round(r["summary"]["Method 2"]["share_over_materiality"]),
                "workloads": r["n_workloads"],
                "batchBias": round(r["summary"]["Batch"]["bias"], 1),
                "method1AnnualError": round(r["summary"]["Method 1"]["annual_abs"], 1),
                "method2AnnualError": round(r["summary"]["Method 2"]["annual_abs"], 1),
                "computeShare": round(r["shares_mean"]["Compute"]),
                "peakHourShare": round(r["peak_share"]["mean"], 1),
                "medianAnnualKg": round(r["annual_kg"]["median"]),
                "medianMonthlyVisits": round(r["visits_month"]["median"], -3),
                **coverage_quarter(r)}
    return weekly, methods, comps, cov, refs, headline, extras


def coverage_quarter(r):
    run = next(x for x in r["sensitivity"] if x["key"] == "telemetry_coverage")["runs"][0]
    sys_lo, sys_hi = next(x for x in r["sensitivity"] if x["key"] == "systematic_scale")["runs"]
    return {"quarterCoverageMethod2Mae": round(run["m2"], 1), "quarterCoverageRatio": round(run["ratio"], 1),
            "halfSystematicMethod2Mae": round(sys_lo["m2"], 1), "doubleSystematicMethod2Mae": round(sys_hi["m2"], 1)}


def confidence_matrix(r):
    """(systematic, hourly) sigma in % of the best available signal; mirrors figs.py Figure 14."""
    n, cal, dev = r["noise"], r["calibration"], r["truth_deviation"]
    pc = lambda v: round(v * 100)
    grid = (pc(cal["grid_bias"]), pc(n["ci_signal"]))
    return [
        ("Compute", [(0, pc(n["util"])), (pc(cal["power_model"]), pc(n["util"])), None, grid]),
        ("Storage", [(0, pc(n["storage_meter"])), (pc(cal["storage_telemetry"]), pc(n["storage_meter"])), None, grid]),
        ("Network", [(0, pc(n["bytes"])), (pc(cal["route_model"]), pc(n["route_energy"])),
                     (pc(cal["path_weight_abs"]), 0), grid]),
        ("CDN", [(0, pc(n["cdn_logs"])), (pc(dev["cdn"]), 0), None, grid]),
        ("Device", [(0, pc(n["bytes"])), (pc(cal["device_telemetry"]), pc(n["device_class"])), None, grid]),
    ]


def extra_chart_data(r, s, week_start):
    comps = r["components"]
    true_sh, batch_sh = r["shares_mean"], r["summary"]["Batch"]["annual_pct_of_true"]
    boundary = [
        {"row": "Reference (full circuit)", **{c: round(true_sh[c], 1) for c in comps}},
        {"row": "Batch estimate", **{c: round(batch_sh[c], 1) for c in comps}},
    ]
    sh = s["shares"] * 100
    shares = sorted(
        ({"component": c, "mean": round(float(sh[:, i].mean()), 1),
          "p5": round(float(np.percentile(sh[:, i], 5)), 1),
          "p95": round(float(np.percentile(sh[:, i], 95)), 1)} for i, c in enumerate(comps)),
        key=lambda d: -d["mean"])
    cv = {c: float(np.std(s[f"truth_{c}"]) / np.mean(s[f"truth_{c}"])) for c in comps}
    cv_max = max(cv.values())
    allocation = [{"component": c, "cv": round(cv[c], 2), "variability": round(cv[c] / cv_max, 3),
                   "observability": OBSERVABILITY[c], "deterministic": c in DETERMINISTIC_IN_M2} for c in comps]
    heat = [round(float(v) * 1000, 1) for v in s["est_Method_3"]]
    sl = slice(week_start, week_start + 72)
    truth = sum(s[f"truth_{c}"] for c in comps)[sl] * 1000
    days = ["Mon", "Tue", "Wed"]
    coupling = [{"hour": i, "label": f"{days[i // 24]} {i % 24:02d}:00",
                 "gridIntensity": round(float(s["ci"][0][sl][i]), 1),
                 "reference": round(float(truth[i]), 2),
                 "batch": round(float(s["est_Batch"][sl][i] * 1000), 2),
                 "method2": round(float(s["est_Method_2"][sl][i] * 1000), 2),
                 "method3": round(float(s["est_Method_3"][sl][i] * 1000), 2)} for i in range(72)]
    confidence = {"signals": CONFIDENCE_SIGNALS, "rows": [
        {"component": comp, "values": [None if v is None else {"systematic": v[0], "hourly": v[1]} for v in vals]}
        for comp, vals in confidence_matrix(r)]}
    return dict(boundary=boundary, shares=shares, allocation=allocation, heat=heat,
                coupling=coupling, confidence=confidence, n_workloads=r["n_workloads"])


def main(unpacked: Path, fe: Path):
    doc = (unpacked / "word/document.xml").read_text(encoding="utf8")
    sections = build_sections(doc)
    abstract, keywords, refs, tail = build_meta(doc)
    caps = figure_captions(doc)
    t1, t2 = table_rows(doc, 0), table_rows(doc, 1)
    figures = []
    for n in range(1, 16):
        w, h = Image.open(fe / "public/papers" / SLUG / f"fig{n:02d}.png").size
        fig = {"number": n, "src": f"/papers/{SLUG}/fig{n:02d}.png", "width": w, "height": h, "caption": caps[n]}
        if n in CAPTION_WEB:
            fig["caption"] = CAPTION_WEB[n]
        if n in INTERACTIVE:
            fig["interactive"] = INTERACTIVE[n]
            fig["caption"] = INTERACTIVE_CAPTION.get(n, fig["caption"])
        figures.append(fig)
    tables = [
        {"id": "table-1", "number": 1, "caption": table_caption(doc, "Table 1."), "header": t1[0], "rows": t1[1:]},
        {"id": "table-2", "number": 2, "caption": table_caption(doc, "Table 2."), "header": t2[0], "rows": t2[1:]},
    ]
    weekly, methods, comps, cov, cov_refs, headline, ex = chart_data()
    ctrl = json.loads((HERE / "results.json").read_text())["summary"]["Annualised Method 2"]
    control = {"method": "Annualised M2", "mae": round(ctrl["mae"], 1), "p5": round(ctrl["p5"], 1),
               "p95": round(ctrl["p95"], 1), "annualError": round(ctrl["annual_abs"], 1)}

    out_dir = fe / "src/constants/papers"
    out_dir.mkdir(parents=True, exist_ok=True)
    content = f"""// Content of the CarbonCut research paper rendered at /papers/{SLUG}.
// Generated from the manuscript (CarbonCut_Manuscript_filled.docx); keep in sync with the paper.
import type {{ ResearchPaper }} from '@/types/research'

export const nearRealTimeCarbonAccountingPaper: ResearchPaper = {{
  slug: '{SLUG}',
  title:
    'Towards Near-Real-Time Carbon Accounting for Internet Data Transmission: A Resolution-Based Attribution Framework',
  shortTitle: 'Near-Real-Time Carbon Accounting for Internet Data Transmission',
  status: 'Preprint',
  statusNote: 'This is a preprint. It has not yet been peer reviewed.',
  publishedDate: '2026-11-09',
  pdfUrl: '/papers/{SLUG}/paper.pdf',
  authors: [
    {{ name: 'Kanhu Charan Pattnayak', affiliations: [1, 2], corresponding: true }},
    {{ name: 'Akshae Golekar', affiliations: [1] }},
  ],
  affiliations: [
    'Carbon Tech International Limited, London, United Kingdom',
    'Cambridge Judge Business School, University of Cambridge, Cambridge, United Kingdom',
  ],
  abstract: {ts(abstract)},
  keywords: {ts(keywords)},
  sections: {ts(sections)},
  figures: {ts(figures)},
  tables: {ts(tables)},
  backMatter: [
    {{ label: 'Acknowledgement', text: {ts(tail['Acknowledgement'].split(':', 1)[1].strip())} }},
    {{ label: 'Funding', text: {ts(tail['Funding'].split(':', 1)[1].strip())} }},
    {{ label: 'Data availability', text: {ts(tail['Data Availability'].split(':', 1)[1].strip())} }},
    {{ label: 'Conflict of interest', text: {ts(tail['Conflict of interest'].split(':', 1)[1].strip())} }},
  ],
  references: {ts(refs)},
}}
"""
    data = f"""// Chart data for the interactive figures of /papers/{SLUG}.
// Generated from the simulation results (results.json / series.npz); values in % unless noted.

export const researchHeadline = {ts(headline)} as const

/** One week of hourly emissions for the example workload, g CO2e per hour. */
export const weeklySeries = {ts(weekly)}

/** Hourly attribution error (WAPE) across workloads: mean and 5th-95th percentile; mean absolute annual-total error. */
export const methodError = {ts(methods)}

/** Control: Method 2's annual totals spread evenly over the year (isolates temporal resolution). */
export const methodErrorControl = {ts(control)}

/** Component-level hourly error, conventional batch vs Method 2. */
export const componentError = {ts(comps)}

/** Method 2 error by telemetry coverage (%), with reference levels of the other approaches. */
export const telemetryCoverage = {ts(cov)}
export const telemetryCoverageReferences = {ts(cov_refs)} as const

/** Annual emissions by component as % of the reference total: full circuit vs batch estimate. */
export const boundaryOmissions = {ts(ex["boundary"])}

/** Share of annual reference emissions by component across {ex["n_workloads"]} workloads (%). */
export const componentShares = {ts(ex["shares"])}

/** Temporal variability (CV, also normalised 0-1) vs assumed observability per component. */
export const allocationPhilosophy = {ts(ex["allocation"])}

/** Hourly emissions under Method 3 for the example workload: 365 days x 24 hours, g CO2e per hour. */
export const eventHeatmap: number[] = {json.dumps(ex["heat"])}

/** Three weekdays of origin grid intensity (gCO2/kWh) and attributed emissions (g CO2e per hour). */
export const gridCoupling = {ts(ex["coupling"])}

/** Assumed uncertainty (1 sigma, %) of the best available signal: systematic (per workload) and hourly; null = known. */
export const dataConfidence = {ts(ex["confidence"])}
"""
    (out_dir / "nearRealTimeCarbonAccounting.ts").write_text(content, encoding="utf8")
    (out_dir / "nearRealTimeCarbonAccountingCharts.ts").write_text(data, encoding="utf8")
    print("sections", len(sections), "refs", len(refs), "weekly", len(weekly))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
