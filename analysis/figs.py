"""Generate Figures 1-15 for the manuscript from results.json / series.npz (see sim.py)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
R = json.loads((HERE / "results.json").read_text())
S = np.load(HERE / "series.npz")

WIDTH = 6.0
DPI = 300
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
METHODS = ["Batch", "Method 1", "Method 2", "Method 3"]
M_LABEL = {"Batch": "Conventional batch", "Method 1": "Method 1: Operational hybrid",
           "Method 2": "Method 2: Hybrid deterministic-batch", "Method 3": "Method 3: Full event-level"}
M_SHORT = {"Batch": "Batch", "Method 1": "Method 1", "Method 2": "Method 2", "Method 3": "Method 3"}
M_COLOR = dict(zip(METHODS, SLOTS[:4]))
CONTROL = "Annualised Method 2"
COMPONENTS = R["components"]
C_COLOR = dict(zip(COMPONENTS, SLOTS[:5]))
SUM = R["summary"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9.5,
    "axes.titleweight": "bold", "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False, "lines.linewidth": 1.6,
    "savefig.facecolor": "white", "figure.facecolor": "white",
})


def save(fig, n):
    fig.savefig(OUT / f"fig{n:02d}.png", dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def week_slice():
    """First full Monday-Sunday week of March (hour 0 = Monday 1 Jan in the model)."""
    start = (59 + (7 - 59 % 7) % 7) * 24
    return slice(start, start + 7 * 24)


def total_truth():
    return sum(S[f"truth_{c}"] for c in COMPONENTS)


# ------------------------------------------------------------------ Figure 1
def fig01():
    rows = [  # (label, lo, hi) - values as reported in the cited sources
        ("Malmodin & Lundén (2018)\nICT sector, 2015", 1.4, 1.4),
        ("Freitag et al. (2021)\nICT incl. supply-chain adjustment", 2.1, 3.9),
        ("Range used in this paper", 3.0, 4.0),
    ]
    fig, ax = plt.subplots(figsize=(WIDTH, 2.4))
    for i, (lab, lo, hi) in enumerate(rows):
        y = len(rows) - 1 - i
        if hi > lo:
            ax.plot([lo, hi], [y, y], color=SLOTS[0], lw=7, solid_capstyle="round")
            ax.text(hi + 0.08, y, f"{lo:.1f}-{hi:.1f}%", va="center", color=INK)
        else:
            ax.plot(lo, y, "o", color=SLOTS[0], ms=9)
            ax.text(lo + 0.12, y, f"{lo:.1f}%", va="center", color=INK)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlim(0, 5)
    ax.set_xlabel("Share of global greenhouse gas emissions (%)")
    ax.set_title("Estimated share of digital infrastructure in global emissions", loc="left")
    ax.grid(axis="y", visible=False)
    save(fig, 1)


# ------------------------------------------------------------------ Figure 2
def fig02():
    sl = week_slice()
    t = np.arange(sl.stop - sl.start)
    fig, ax = plt.subplots(figsize=(WIDTH, 2.9))
    ax.plot(t, total_truth()[sl] * 1000, color=INK2, lw=1.2, label="Reference (true hourly)")
    ax.plot(t, S["est_Batch"][sl] * 1000, color=M_COLOR["Batch"], lw=2, label="Conventional batch (annual)")
    ax.plot(t, S["est_Method_1"][sl] * 1000, color=M_COLOR["Method 1"], lw=1.6, label="Method 1 (monthly + event)")
    ax.set_xticks(np.arange(0, 7 * 24 + 1, 24))
    ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", ""])
    ax.set_xlim(0, 7 * 24)
    ax.set_ylabel("Emissions (g CO$_2$e per hour)")
    ax.set_title("One week of attributed emissions, example workload", loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7.5)
    ax.set_ylim(0, None)
    save(fig, 2)


# ------------------------------------------------------------------ Figure 3
def fig03():
    true_sh = R["shares_mean"]
    bat = SUM["Batch"]["annual_pct_of_true"]
    fig, ax = plt.subplots(figsize=(WIDTH, 2.6))
    for y, (name, vals) in enumerate([("Batch estimate", bat), ("Reference (full circuit)", true_sh)]):
        left = 0.0
        for c in COMPONENTS:
            v = vals[c]
            if v <= 0:
                continue
            ax.barh(y, v, left=left, color=C_COLOR[c], edgecolor="white", linewidth=1.5, height=0.55)
            if v > 3.5:
                ax.text(left + v / 2, y, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=7.5)
            left += v
        ax.text(left + 1, y, f"{left:.0f}%", va="center", color=INK, fontweight="bold")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Batch estimate", "Reference\n(full circuit)"])
    ax.set_xlim(0, 112)
    ax.set_xlabel("Annual emissions, % of reference total (mean of 200 workloads)")
    ax.set_title("Boundary omissions in conventional batch accounting", loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=C_COLOR[c]) for c in COMPONENTS]
    ax.legend(handles, COMPONENTS, ncol=5, loc="upper center", bbox_to_anchor=(0.45, -0.28), fontsize=7.5)
    ax.grid(axis="y", visible=False)
    save(fig, 3)


# ------------------------------------------------------------------ Figure 4
def fig04():
    sh = S["shares"] * 100
    mean = sh.mean(0)
    lo, hi = np.percentile(sh, 5, axis=0), np.percentile(sh, 95, axis=0)
    order = np.argsort(mean)
    fig, ax = plt.subplots(figsize=(WIDTH, 2.7))
    y = np.arange(len(COMPONENTS))
    ax.barh(y, mean[order], color=[C_COLOR[COMPONENTS[i]] for i in order], height=0.55)
    ax.errorbar(mean[order], y, xerr=[mean[order] - lo[order], hi[order] - mean[order]],
                fmt="none", ecolor=INK2, capsize=3, lw=1)
    for yi, i in zip(y, order):
        ax.text(hi[i] + 1.2, yi, f"{mean[i]:.1f}%", va="center", color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([COMPONENTS[i] for i in order])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of annual reference emissions (%); bars = mean, whiskers = 5th-95th percentile")
    ax.set_title("Emissions contribution by circuit component", loc="left")
    ax.grid(axis="y", visible=False)
    save(fig, 4)


# ------------------------------------------------------------------ Figure 5
def fig05():
    crit = ["Temporal\nresolution", "Boundary\ncompleteness", "Grid-signal\nintegration",
            "Auditability", "Deployability\ntoday", "Telemetry\nneeded"]
    labels = [
        ["Annual", "Partial", "None", "Medium", "High", "Minimal"],
        ["Event +\nmonthly", "Full\n(proxies)", "Event\nsources", "High", "High", "Low"],
        ["Hourly /\ndaily", "Full", "Hourly", "Medium", "Medium", "Medium"],
        ["Event-level", "Full", "Hourly,\npath-level", "Medium", "Low", "Full"],
    ]
    score = np.array([[1, 1, 1, 2, 3, 3], [2, 3, 2, 3, 3, 3], [3, 3, 3, 2, 2, 2], [3, 3, 3, 2, 1, 1]])
    cmap = matplotlib.colors.ListedColormap(["#d6e6f8", "#86b4ea", "#2a78d6"])
    fig, ax = plt.subplots(figsize=(WIDTH, 3.0))
    ax.imshow(score, cmap=cmap, vmin=0.5, vmax=3.5, aspect="auto")
    for i in range(4):
        for j in range(len(crit)):
            ax.text(j, i, labels[i][j], ha="center", va="center", fontsize=7,
                    color="white" if score[i, j] == 3 else INK)
    ax.set_xticks(range(len(crit)))
    ax.set_xticklabels(crit, fontsize=7.5)
    ax.set_yticks(range(4))
    ax.set_yticklabels([M_LABEL[m].replace(": ", ":\n") for m in METHODS], fontsize=7.5)
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(crit)), minor=True)
    ax.set_yticks(np.arange(-0.5, 4), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    ax.xaxis.tick_top()
    ax.set_title("Methodological capabilities (darker = more favourable)", loc="left", pad=34)
    save(fig, 5)


# ------------------------------------------------------------------ Figure 6
def fig06():
    keys = METHODS + [CONTROL]
    data = [S[f"mae_{m.replace(' ', '_')}"] for m in keys]
    colors = [M_COLOR[m] for m in METHODS] + [MUTED]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.2))
    rng = np.random.default_rng(1)
    for i, (m, d) in enumerate(zip(keys, data)):
        ax.scatter(i + rng.uniform(-0.18, 0.18, d.size), d, s=8, color=colors[i], alpha=0.55, lw=0)
        ax.boxplot(d, positions=[i], widths=0.5, showfliers=False,
                   medianprops=dict(color=INK, lw=1.5), boxprops=dict(color=INK2),
                   whiskerprops=dict(color=INK2), capprops=dict(color=INK2))
        ax.text(i, d.max() + 1.5, f"{d.mean():.1f}%", ha="center", color=INK, fontweight="bold")
    ax.axvline(3.5, color=GRID, lw=1)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(["Conventional\nbatch", "Method 1\nOperational\nhybrid", "Method 2\nHybrid det.-\nbatch",
                        "Method 3\nFull\nevent-level", "Control:\nMethod 2\nannualised"], fontsize=7.5)
    ax.set_ylabel("Hourly attribution error, WAPE (%)")
    ax.set_ylim(0, max(d.max() for d in data) + 6)
    ax.set_title(f"Attribution error across {R['n_workloads']} synthetic workloads (label = mean)", loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, 6)


# ------------------------------------------------------------------ Figure 7
def fig07():
    cv = {c: float(np.std(S[f"truth_{c}"]) / np.mean(S[f"truth_{c}"])) for c in COMPONENTS}
    obs = {"Compute": 0.9, "CDN": 0.85, "Storage": 0.6, "Network": 0.3, "Device": 0.25}
    det = {"Compute", "CDN"}
    fig, ax = plt.subplots(figsize=(WIDTH, 3.4))
    xmid = 0.5
    ax.axvline(xmid, color=MUTED, lw=1, ls="--")
    ax.axhline(0.5, color=MUTED, lw=1, ls="--")
    for c in COMPONENTS:
        x = cv[c] / max(cv.values())
        ax.scatter(x, obs[c], s=90, color=C_COLOR[c], edgecolor="white", lw=1.5, zorder=3,
                   marker="o" if c in det else "s")
        off = {"Device": (-62, -6), "Network": (8, 2)}.get(c, (8, 4))
        ax.annotate(f"{c}\n(CV {cv[c]:.2f})", (x, obs[c]), xytext=off, textcoords="offset points",
                    fontsize=7.5, color=INK)
    ax.text(0.98, 0.52, "Deterministic\n(event / hourly)", ha="right", va="bottom", transform=ax.transAxes,
            color=INK2, fontsize=8, fontweight="bold")
    ax.text(0.02, 0.03, "Batch proxy\n(short-interval average)", ha="left", va="bottom",
            transform=ax.transAxes, color=INK2, fontsize=8, fontweight="bold")
    ax.set_xlim(0, 1.15)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Temporal variability of hourly emissions (CV, normalised to the most variable component)")
    ax.set_ylabel("Observability (telemetry quality, 0-1)")
    ax.set_title("Allocation philosophy of the hybrid approach (circle = deterministic in Method 2)",
                 loc="left", fontsize=9)
    save(fig, 7)


# ------------------------------------------------------------------ diagram helpers
def box(ax, x, y, w, h, text, fc="#eef4fc", ec=SLOTS[0], fs=7.5, bold=False, color=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015",
                                fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=color, wrap=True)


def arrow(ax, p, q, color=INK2, ls="-", lw=1.1):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, color=color, lw=lw, ls=ls))


def blank(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


# ------------------------------------------------------------------ Figure 8
def fig08():
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 3.9))
    gray_fc, gray_ec = "#f1f0ed", MUTED
    for ax, title in zip(axes, ["(A) Legacy batch accounting", "(B) Hybrid deterministic-batch"]):
        blank(ax)
        ax.set_ylim(-0.03, 1)
        ax.set_title(title, loc="left", fontsize=9)
    comps = ["End-user devices", "Access / backbone", "CDN edge", "Cloud compute", "Storage / DB"]
    ys = [0.78, 0.63, 0.48, 0.33, 0.18]
    legacy_in = {"Cloud compute", "Storage / DB", "Access / backbone"}
    hybrid_mode = {"End-user devices": "daily proxy", "Access / backbone": "volume hourly,\nenergy daily proxy",
                   "CDN edge": "hourly (logs)", "Cloud compute": "hourly (utilisation)",
                   "Storage / DB": "daily proxy"}
    ax = axes[0]
    for c, y in zip(comps, ys):
        inside = c in legacy_in
        box(ax, 0.02, y, 0.44, 0.11, c, fc="#eef4fc" if inside else gray_fc,
            ec=SLOTS[0] if inside else gray_ec, color=INK if inside else MUTED)
        ax.text(0.5, y + 0.055, "annual total" if inside else "excluded", va="center", fontsize=7,
                color=INK2 if inside else MUTED)
    box(ax, 0.02, 0.0, 0.96, 0.12, "x annual average factor\n-> one annual figure", fc="#fdf0ea", ec=SLOTS[1], fs=7)
    ax = axes[1]
    for c, y in zip(comps, ys):
        det = "hourly" in hybrid_mode[c] and "proxy" not in hybrid_mode[c]
        box(ax, 0.02, y, 0.44, 0.11, c, fc="#e7f6f0" if det else "#fdf6e6",
            ec=SLOTS[2] if det else SLOTS[3])
        ax.text(0.5, y + 0.055, hybrid_mode[c], va="center", fontsize=7, color=INK2)
    box(ax, 0.02, 0.0, 0.96, 0.12, "x hourly regional grid intensity\n-> hourly series", fc="#e7f6f0", ec=SLOTS[2], fs=7)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=f, ec=e) for f, e in
               [("#eef4fc", SLOTS[0]), (gray_fc, gray_ec), ("#e7f6f0", SLOTS[2]), ("#fdf6e6", SLOTS[3])]]
    fig.legend(handles, ["In batch boundary", "Outside boundary", "Deterministic", "Batch-allocated residual"],
               ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.04), fontsize=7.5)
    save(fig, 8)


# ------------------------------------------------------------------ Figure 9
def fig09():
    b = SUM["Batch"]["comp"]
    m2 = SUM["Method 2"]["comp"]
    red = {c: (b[c] - m2[c]) / b[c] * 100 for c in COMPONENTS}
    order = sorted(COMPONENTS, key=lambda c: red[c])
    fig, ax = plt.subplots(figsize=(WIDTH, 2.9))
    y = np.arange(len(order))
    h = 0.36
    ax.barh(y + h / 2, [b[c] for c in order], height=h, color=M_COLOR["Batch"], label="Conventional batch")
    ax.barh(y - h / 2, [m2[c] for c in order], height=h, color=M_COLOR["Method 2"], label="Method 2")
    for yi, c in zip(y, order):
        ax.text(max(b[c], m2[c]) + 2, yi, f"-{red[c]:.0f}%", va="center", color=INK, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(order)
    ax.set_xlim(0, 120)
    ax.set_xlabel("Component-level hourly error, WAPE (%)  (label = relative reduction)")
    ax.set_title("Error reduction by component: batch vs. Method 2", loc="left")
    ax.legend(loc="lower right", fontsize=7.5)
    ax.grid(axis="y", visible=False)
    save(fig, 9)


# ------------------------------------------------------------------ Figure 10
def fig10():
    m3 = S["est_Method_3"].reshape(365, 24) * 1000
    fig, ax = plt.subplots(figsize=(WIDTH, 3.0))
    im = ax.imshow(m3.T, aspect="auto", cmap="Blues", origin="lower", interpolation="nearest")
    ax.set_xlabel("Day of year")
    ax.set_ylabel("Hour of day (UTC)")
    ax.set_yticks([0, 6, 12, 18, 23])
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=0.015)
    cb.set_label("g CO$_2$e per hour", color=INK2)
    cb.outline.set_visible(False)
    ax.set_title("Hourly emissions under full event-level attribution (example workload)", loc="left")
    save(fig, 10)


# ------------------------------------------------------------------ Figure 11
def fig11():
    w = R["example_workload"]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.6))
    blank(ax)
    ax.set_xlim(-0.01, 1.01)
    regions = ["UK", "US", "India", "Germany"]
    grid = R["grid_mean"]
    for i, (r, g) in enumerate(zip(regions, grid)):
        y = 0.80 - i * 0.2
        box(ax, 0.0, y, 0.2, 0.13, f"Users: {r}\n{g:.0f} gCO$_2$/kWh", fs=7)
        box(ax, 0.27, y, 0.17, 0.13, "Access ISP +\nbackbone", fc="#fdf6e6", ec=SLOTS[3], fs=7)
        box(ax, 0.51, y, 0.15, 0.13, "CDN edge\n(local grid)", fc="#e7f6f0", ec=SLOTS[2], fs=7)
        arrow(ax, (0.2, y + 0.065), (0.27, y + 0.065))
        arrow(ax, (0.44, y + 0.065), (0.51, y + 0.065))
        arrow(ax, (0.66, y + 0.065), (0.74, 0.47), color=MUTED)
    box(ax, 0.74, 0.30, 0.26, 0.34, "Origin cloud region\n(London, UK grid)\n\nCompute instances\n"
        "Object storage + DB\nIdle provisioned capacity", fc="#fdf0ea", ec=SLOTS[1], fs=7)
    box(ax, 0.74, 0.80, 0.26, 0.13, "Hourly grid-intensity\nsignal (4 regions)", fc="#f1f0ed", ec=MUTED, fs=7)
    box(ax, 0.74, 0.04, 0.26, 0.16, "Telemetry: page-view tracker,\nCDN logs, utilisation,\nprovider reports",
        fc="#f1f0ed", ec=MUTED, fs=6.3)
    arrow(ax, (0.87, 0.80), (0.87, 0.64), color=MUTED, ls="--")
    arrow(ax, (0.87, 0.20), (0.87, 0.30), color=MUTED, ls="--")
    ax.set_title(f"Experimental architecture (200 workloads; median {R['visits_month']['median'] / 1000:.0f}k visits/month)",
                 loc="left")
    save(fig, 11)


# ------------------------------------------------------------------ Figure 12
def fig12():
    sl = week_slice()
    sl = slice(sl.start, sl.start + 72)
    t = np.arange(72)
    ci = S["ci"][0][sl]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(WIDTH, 3.8), sharex=True,
                                 gridspec_kw=dict(height_ratios=[1, 1.4], hspace=0.12))
    a1.plot(t, ci, color=INK2)
    a1.set_ylabel("Grid intensity,\norigin (gCO$_2$/kWh)")
    a1.set_title("Grid carbon intensity and attributed emissions, three weekdays", loc="left")
    a2.plot(t, total_truth()[sl] * 1000, color=INK2, lw=1.2, label="Reference")
    for m in ["Batch", "Method 2", "Method 3"]:
        a2.plot(t, S[f"est_{m.replace(' ', '_')}"][sl] * 1000, color=M_COLOR[m], label=M_SHORT[m],
                lw=1.6 if m != "Method 3" else 1.2, ls="-" if m != "Method 3" else "--")
    a2.set_ylabel("Emissions\n(g CO$_2$e per hour)")
    a2.set_xlabel("Hour (UTC)")
    a2.set_xticks(np.arange(0, 73, 12))
    a2.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.32), fontsize=7.5)
    a2.set_ylim(0, None)
    save(fig, 12)


# ------------------------------------------------------------------ Figure 13
def fig13():
    cov = R["coverage"]
    x = np.array([c["coverage"] for c in cov]) * 100
    m2 = np.array([c["mae_m2"] for c in cov])
    fig, ax = plt.subplots(figsize=(WIDTH, 2.9))
    ref_key = {"Batch": "mae_batch", "Method 1": "mae_m1", "Method 3": "mae_m3"}
    for m in ["Batch", "Method 1", "Method 3"]:
        v = float(np.mean([c[ref_key[m]] for c in cov]))
        ax.axhline(v, color=M_COLOR[m], lw=1.2, ls="--")
        ax.text(101, v, f"{M_SHORT[m]} ({v:.1f}%)", va="center", fontsize=7.5, color=INK2)
    ax.plot(x, m2, color=M_COLOR["Method 2"], marker="o", ms=4, lw=2, label="Method 2")
    ax.text(x[2] + 2, m2[2] + 1.0, "Method 2", color=INK, fontsize=8, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, None)
    ax.set_xlabel("Telemetry coverage of deterministic components (%)")
    ax.set_ylabel("Hourly attribution error, WAPE (%)")
    ax.set_title("Attribution error vs. telemetry availability", loc="left")
    save(fig, 13)


# ------------------------------------------------------------------ Figure 14
def confidence_matrix():
    """Assumed uncertainty of the best available signal (Method 3), as (systematic, hourly) sigma in %.

    Systematic = per-workload error that persists all year; hourly = independent noise.
    None marks a quantity that is known exactly.
    """
    n, cal, dev = R["noise"], R["calibration"], R["truth_deviation"]
    pc = lambda v: round(v * 100)
    return [
        ("Compute", [(0, pc(n["util"])), (pc(cal["power_model"]), pc(n["util"])), None,
                     (pc(cal["grid_bias"]), pc(n["ci_signal"]))]),
        ("Storage", [(0, pc(n["storage_meter"])), (pc(cal["storage_telemetry"]), pc(n["storage_meter"])), None,
                     (pc(cal["grid_bias"]), pc(n["ci_signal"]))]),
        ("Network", [(0, pc(n["bytes"])), (pc(cal["route_model"]), pc(n["route_energy"])),
                     (pc(cal["path_weight_abs"]), 0), (pc(cal["grid_bias"]), pc(n["ci_signal"]))]),
        ("CDN", [(0, pc(n["cdn_logs"])), (pc(dev["cdn"]), 0), None, (pc(cal["grid_bias"]), pc(n["ci_signal"]))]),
        ("Device", [(0, pc(n["bytes"])), (pc(cal["device_telemetry"]), pc(n["device_class"])), None,
                    (pc(cal["grid_bias"]), pc(n["ci_signal"]))]),
    ]


def cell_label(v, routing=False):
    if v is None:
        return "known"
    sys_err, hourly = v
    if routing:
        return f"±{sys_err} pts mix"
    if sys_err == 0:
        return f"±{hourly}% hourly"
    if hourly == 0:
        return f"±{sys_err}% fixed"
    return f"±{sys_err}% / ±{hourly}%"


def fig14():
    signals = ["Activity volume", "Energy model", "Routing / location", "Grid intensity"]
    rows = confidence_matrix()
    sysv = np.array([[0 if v is None else v[0] for v in vals] for _, vals in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(WIDTH, 2.9))
    im = ax.imshow(sysv, cmap="Blues", vmin=0, vmax=30, aspect="auto")
    for i, (_, vals) in enumerate(rows):
        for j, v in enumerate(vals):
            txt = cell_label(v, routing=j == 2)
            ax.text(j, i, txt, ha="center", va="center", fontsize=7.2,
                    color="white" if sysv[i, j] > 18 else INK)
    ax.set_xticks(range(len(signals)))
    ax.set_xticklabels(signals)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([c for c, _ in rows])
    ax.grid(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, pad=0.015)
    cb.set_label("Systematic uncertainty (1σ, %)", color=INK2)
    cb.outline.set_visible(False)
    ax.set_title("Data confidence by component and signal (systematic / hourly, 1σ)", loc="left")
    save(fig, 14)


# ------------------------------------------------------------------ Figure 15
def fig15():
    steps = [("Conventional\nbatch", "Batch", "Annual activity data,\nstatic factors"),
             ("Method 1\nOperational hybrid", "Method 1", "Tracker + monthly\nprovider/CDN data"),
             ("Method 2\nHybrid det.-batch", "Method 2", "Hourly utilisation +\nCDN logs + grid signal"),
             ("Method 3\nFull event-level", "Method 3", "Path-level routing +\nper-component energy")]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.0))
    x = np.arange(len(steps))
    vals = [SUM[m]["mae"] for _, m, _ in steps]
    ax.bar(x, vals, color=[M_COLOR[m] for _, m, _ in steps], width=0.6)
    for xi, v, (_, m, req) in zip(x, vals, steps):
        ax.text(xi, v + 1.0, f"{v:.1f}%", ha="center", color=INK, fontweight="bold")
        ax.text(xi, -9.5, req, ha="center", va="top", fontsize=6.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([s for s, _, _ in steps], fontsize=7.5)
    ax.set_ylabel("Hourly attribution error, WAPE (%)")
    ax.set_ylim(0, max(vals) + 6)
    ax.set_title("Roadmap from batch estimation to full deterministic accounting", loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, 15)


if __name__ == "__main__":
    for f in [fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10,
              fig11, fig12, fig13, fig14, fig15]:
        f()
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))
