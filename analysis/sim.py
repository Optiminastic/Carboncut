"""
Synthetic evaluation of the resolution ladder for a mid-size SaaS / marketing website.

Emission and energy factors are taken from the CarbonCut codebase:
  - fe/src/protocols/ghgProtocolCalculator.ts  (website formula, network_data_transfer,
    website_page_view, device_energy_*, cloud_storage_per_gb_month, bytes_per_visit_default)
  - fe/src/services/grid-intensity-service.ts  (annual average grid intensity by country)
  - fe/src/app/(dashboard)/dashboard/on-prem/page.tsx (server TDP model, PUE presets)
  - fe/src/app/(dashboard)/dashboard/cdn/page.tsx (default CDN factor, kg CO2e / GB)

As in the calculator code, the "per MB" / "per page view" / "per minute" factors are
multiplied by grid intensity, so they are used here as energy intensities (kWh per unit).

Run:  python sim.py  -> writes results.json and series.npz next to this file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from scipy import stats

OUT_DIR = Path(__file__).parent
HOURS = 8760
SEED = 20261109

# ---------------------------------------------------------------- codebase factors
NETWORK_KWH_PER_GB = 0.000006 * 1024          # network_data_transfer, per MB -> per GB
ORIGIN_KWH_PER_VISIT = 0.000004               # website_page_view
DEVICE_KWH_PER_MIN = {"mobile": 0.0000012, "desktop": 0.0000028}
STORAGE_KG_PER_GB_MONTH = 0.000012            # cloud_storage_per_gb_month (used as kg directly)
BYTES_PER_VISIT_DEFAULT_MB = 2000000 / 1024 / 1024
CDN_KG_PER_GB_DEFAULT = 0.00030               # CDN dashboard fallback factor
DEFAULT_GRID = 387.0                          # grid-intensity-service 'default'
CPU_W_PER_CORE, RAM_W_PER_GB, SSD_W_PER_TB = 5.0, 0.375, 1.2
PUE_PRESETS = (1.1, 1.3, 1.6, 2.0)

REGIONS = ["United Kingdom", "United States", "India", "Germany"]
GRID_MEAN = np.array([162.0, 342.0, 589.0, 298.0])      # gCO2/kWh, codebase fallbacks
TZ = np.array([0, -6, 5, 1])                            # hours from UTC
WEATHER_SIGMA = np.array([0.18, 0.06, 0.05, 0.15])      # wind/solar driven variability
WEATHER_PHI = 0.97
SEASONAL_AMP = np.array([0.12, -0.05, -0.05, 0.12])     # + = winter peak
CLOUD_REGION = 0                                        # origin in London (UK grid)
BATCH_RAM_GB_PER_VCPU = 4

COMPONENTS = ["Compute", "Storage", "Network", "CDN", "Device"]


@dataclass(frozen=True)
class Assumptions:
    """Parameters varied in the sensitivity analysis (Table 2)."""
    network_kwh_per_gb: float = NETWORK_KWH_PER_GB
    grid_diurnal_amp: float = 0.25
    traffic_peak_to_mean: float = 2.0
    idle_share: float = 0.10
    pue: float = 1.3
    telemetry_coverage: float = 1.0


# telemetry / signal noise (multiplicative lognormal sigma, per hour unless noted)
NOISE = {
    "ci_signal": 0.05,        # published hourly grid intensity vs. true
    "util": 0.05,             # utilisation-based server power
    "cdn_logs": 0.05,
    "storage_meter": 0.05,
    "route_energy": 0.08,     # per-path network energy inference (Method 3)
    "device_class": 0.15,     # device-class power from tracker metadata
    "provider_month": 0.03,   # provider monthly report
    "bytes": 0.02,            # tracker-observed transfer size
}


# ---------------------------------------------------------------- generators
def _ar1(rng, n_series, n, phi, sigma):
    eps = rng.normal(0, sigma * np.sqrt(1 - phi**2), size=(n_series, n))
    out = np.empty_like(eps)
    out[:, 0] = rng.normal(0, sigma, size=n_series)
    for t in range(1, n):
        out[:, t] = phi * out[:, t - 1] + eps[:, t]
    return out


def _norm_shape(x):
    x = x - x.mean()
    return x / np.abs(x).max()


def grid_diurnal_shapes():
    lh = np.arange(24)
    g = lambda c, w: np.exp(-((lh - c) / w) ** 2)
    shapes = np.stack([
        _norm_shape(0.9 * g(18, 2.5) - 0.35 * g(13, 2.5) - 0.5 * g(4, 3)),   # UK
        _norm_shape(0.8 * g(19, 3.0) - 0.6 * g(4, 3.5)),                      # US
        _norm_shape(0.8 * g(21, 3.0) - 0.7 * g(13, 3.0)),                     # India
        _norm_shape(0.7 * g(19, 2.5) - 1.0 * g(13, 2.5)),                     # Germany
    ])
    return shapes


def make_grid(rng, amp):
    """True hourly grid carbon intensity per region, gCO2/kWh, shape (R, H)."""
    h = np.arange(HOURS)
    doy = h / 24.0
    shapes = grid_diurnal_shapes()
    ci = np.empty((len(REGIONS), HOURS))
    weather = _ar1(rng, len(REGIONS), HOURS, WEATHER_PHI, 1.0) * WEATHER_SIGMA[:, None]
    for r in range(len(REGIONS)):
        lh = (h + TZ[r]) % 24
        seas = SEASONAL_AMP[r] * np.cos(2 * np.pi * doy / 365.0)
        x = 1 + amp * shapes[r][lh] + seas + weather[r]
        x = np.clip(x, 0.2, None)
        ci[r] = GRID_MEAN[r] * x / x.mean()
    return ci


def traffic_diurnal(peak_to_mean):
    lh = np.arange(24)
    base = 0.25 * np.exp(-((lh - 11) / 3.0) ** 2) + 0.2 * np.exp(-((lh - 15) / 2.5) ** 2) \
        + 0.12 * np.exp(-((lh - 20.5) / 2.0) ** 2)
    base = base / base.mean() - 1.0                      # zero-mean shape
    a = (peak_to_mean - 1.0) / base.max()
    prof = np.clip(1 + a * base, 0.05, None)
    return prof / prof.mean()


@dataclass(frozen=True)
class Workload:
    monthly_visits: float
    page_mb: float
    mix: np.ndarray
    cache_hit: float
    n_instances: int
    vcpu: int
    storage_tb: float
    view_min: float
    mobile_share: float


def sample_workloads(rng, n):
    out = []
    for _ in range(n):
        out.append(Workload(
            monthly_visits=float(np.exp(rng.uniform(np.log(20e3), np.log(120e3)))),
            page_mb=float(rng.uniform(0.6, 1.75) * BYTES_PER_VISIT_DEFAULT_MB),
            mix=rng.dirichlet([8, 6, 3, 3]),
            cache_hit=float(rng.uniform(0.75, 0.95)),
            n_instances=int(rng.choice([1, 2, 3, 4], p=[0.2, 0.4, 0.25, 0.15])),
            vcpu=int(rng.choice([2, 4, 8], p=[0.3, 0.5, 0.2])),
            storage_tb=float(rng.uniform(0.2, 2.0)),
            view_min=float(rng.uniform(1.0, 2.5)),
            mobile_share=float(rng.uniform(0.4, 0.7)),
        ))
    return out


def make_traffic(rng, w: Workload, peak_to_mean):
    """Hourly visits per region, shape (R, H)."""
    h = np.arange(HOURS)
    day = h // 24
    prof = traffic_diurnal(peak_to_mean)
    weekday = np.where((day % 7) < 5, 1.0, 0.6)
    seas = 1 - 0.12 * np.exp(-((day - 225) / 12.0) ** 2) - 0.15 * np.exp(-((day - 358) / 6.0) ** 2)
    campaign = np.ones(HOURS)
    for start in rng.choice(np.arange(7, 355), size=6, replace=False):
        campaign[start * 24:(start + 2) * 24] *= rng.uniform(1.5, 2.5)
    lam = np.empty((len(REGIONS), HOURS))
    hourly_mean = w.monthly_visits * 12 / HOURS
    for r in range(len(REGIONS)):
        lh = (h + TZ[r]) % 24
        shape = prof[lh] * weekday * seas * campaign
        lam[r] = hourly_mean * w.mix[r] * shape / shape.mean()
    return rng.poisson(lam).astype(float)


# ---------------------------------------------------------------- truth model
def server_pmax_w(vcpu):
    return vcpu * CPU_W_PER_CORE + vcpu * BATCH_RAM_GB_PER_VCPU * RAM_W_PER_GB + 0.1 * SSD_W_PER_TB


def simulate_truth(rng, w: Workload, a: Assumptions, ci):
    visits = make_traffic(rng, w, a.traffic_peak_to_mean)            # (R,H)
    page_mb = w.page_mb * np.exp(rng.normal(0, 0.1, size=visits.shape))
    gb = visits * page_mb / 1024                                     # (R,H)
    tot_visits = visits.sum(0)
    load = tot_visits / np.percentile(tot_visits, 99)

    # compute: active servers, idle floor 35% of Pmax, utilisation driven by origin load
    origin = tot_visits * (1 - w.cache_hit)
    u = np.clip(0.08 + 0.67 * origin / np.percentile(origin, 99), 0, 1)
    pmax = server_pmax_w(w.vcpu) * w.n_instances
    active_kwh = pmax * (0.35 + 0.65 * u) * a.pue / 1000 + ORIGIN_KWH_PER_VISIT * origin
    # standby / idle provisioned capacity sized to the requested share of total energy
    storage_kwh = w.storage_tb * 3 * SSD_W_PER_TB * a.pue / 1000 * (1 + 0.3 * load)

    ovh = 0.05 + 0.06 * load                                         # protocol / retransmission
    net_kwh = gb * a.network_kwh_per_gb * (1 + ovh)                  # (R,H)
    cdn_kwh = gb * (CDN_KG_PER_GB_DEFAULT / (DEFAULT_GRID / 1000))   # (R,H) energy per GB
    dev_kwh_per_visit = w.view_min * (w.mobile_share * DEVICE_KWH_PER_MIN["mobile"]
                                      + (1 - w.mobile_share) * DEVICE_KWH_PER_MIN["desktop"])
    dev_kwh = visits * dev_kwh_per_visit

    non_idle = active_kwh.sum() + storage_kwh.sum() + net_kwh.sum() + cdn_kwh.sum() + dev_kwh.sum()
    idle_kwh_h = a.idle_share / (1 - a.idle_share) * non_idle / HOURS
    compute_kwh = active_kwh + idle_kwh_h

    ci_kg = ci / 1000.0
    path_ci = 0.7 * ci_kg + 0.3 * ci_kg[CLOUD_REGION]                # backbone spans to origin
    truth = {
        "Compute": compute_kwh * ci_kg[CLOUD_REGION],
        "Storage": storage_kwh * ci_kg[CLOUD_REGION],
        "Network": (net_kwh * path_ci).sum(0),
        "CDN": (cdn_kwh * ci_kg).sum(0),
        "Device": (dev_kwh * ci_kg).sum(0),
    }
    state = dict(visits=visits, gb=gb, u=u, pmax=pmax, origin=origin, ovh=ovh,
                 compute_kwh=compute_kwh, active_kwh=active_kwh, idle_kwh_h=idle_kwh_h,
                 storage_kwh=storage_kwh, net_kwh=net_kwh, cdn_kwh=cdn_kwh,
                 dev_kwh=dev_kwh, dev_kwh_per_visit=dev_kwh_per_visit)
    return truth, state


# ---------------------------------------------------------------- helpers for estimators
MONTH_EDGES = np.linspace(0, HOURS, 13).astype(int)


def _ln(rng, sigma, shape):
    return np.exp(rng.normal(-0.5 * sigma**2, sigma, size=shape))


def spread_monthly(x_hourly, noise=None):
    out = np.empty_like(x_hourly)
    for i in range(12):
        s, e = MONTH_EDGES[i], MONTH_EDGES[i + 1]
        tot = x_hourly[..., s:e].sum(-1, keepdims=True)
        if noise is not None:
            tot = tot * noise[i]
        out[..., s:e] = tot / (e - s)
    return out


def daily_mean(x):
    shp = x.shape
    d = x.reshape(*shp[:-1], HOURS // 24, 24).mean(-1, keepdims=True)
    return np.broadcast_to(d, (*shp[:-1], HOURS // 24, 24)).reshape(shp)


# ---------------------------------------------------------------- the four approaches
def est_batch(w, a, st, ci):
    """Annual activity x static factors, partial boundary (cloud + data transfer)."""
    annual_compute_kwh = server_pmax_w(w.vcpu) * w.n_instances * 0.5 * a.pue * HOURS / 1000
    cloud_ci = GRID_MEAN[CLOUD_REGION] / 1000
    compute = np.full(HOURS, annual_compute_kwh * cloud_ci / HOURS)
    storage = np.full(HOURS, w.storage_tb * 1024 * STORAGE_KG_PER_GB_MONTH * 12 / HOURS)
    network = np.full(HOURS, st["gb"].sum() * NETWORK_KWH_PER_GB * DEFAULT_GRID / 1000 / HOURS)
    zero = np.zeros(HOURS)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": zero, "Device": zero}


def est_m1(rng, w, a, st, ci, ci_sig, truth):
    """Operational hybrid: event-level web transfer, monthly provider / CDN / storage data."""
    pm = _ln(rng, NOISE["provider_month"], 12)
    compute = spread_monthly(truth["Compute"], pm)
    storage = spread_monthly(truth["Storage"], pm)
    gb_obs = st["gb"] * _ln(rng, NOISE["bytes"], st["gb"].shape)
    network = (gb_obs * NETWORK_KWH_PER_GB * ci_sig / 1000).sum(0)
    cdn = spread_monthly(st["gb"].sum(0) * CDN_KG_PER_GB_DEFAULT)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": cdn,
            "Device": np.zeros(HOURS)}


def _compute_deterministic(rng, a, st, ci_sig_cloud):
    p = st["pmax"] * (0.35 + 0.65 * st["u"]) * a.pue / 1000 + ORIGIN_KWH_PER_VISIT * st["origin"]
    p = p * _ln(rng, NOISE["util"], HOURS)
    return (p + st["idle_kwh_h"]) * ci_sig_cloud / 1000


def est_m2(rng, w, a, st, ci, ci_sig, truth, m1):
    """Hybrid: deterministic compute + CDN (+ transfer volume), short-interval proxies elsewhere."""
    cov = a.telemetry_coverage
    comp_det = _compute_deterministic(rng, a, st, ci_sig[CLOUD_REGION])
    cdn_det = (st["cdn_kwh"] * _ln(rng, NOISE["cdn_logs"], st["cdn_kwh"].shape) * ci_sig / 1000).sum(0)
    compute = cov * comp_det + (1 - cov) * m1["Compute"]
    cdn = cov * cdn_det + (1 - cov) * m1["CDN"]

    storage = daily_mean(st["storage_kwh"] * _ln(rng, NOISE["storage_meter"], HOURS)) \
        * daily_mean(ci_sig[CLOUD_REGION]) / 1000
    mean_ovh = st["ovh"].mean()
    gb_obs = st["gb"] * _ln(rng, NOISE["bytes"], st["gb"].shape)
    network = (gb_obs * a.network_kwh_per_gb * (1 + mean_ovh) * daily_mean(ci_sig) / 1000).sum(0)
    device = (daily_mean(st["visits"]) * st["dev_kwh_per_visit"] * daily_mean(ci_sig) / 1000).sum(0)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": cdn, "Device": device}


def est_m3(rng, w, a, st, ci, ci_sig):
    """Full event-level deterministic attribution with component telemetry."""
    compute = _compute_deterministic(rng, a, st, ci_sig[CLOUD_REGION])
    storage = st["storage_kwh"] * _ln(rng, NOISE["storage_meter"], HOURS) * ci_sig[CLOUD_REGION] / 1000
    path_sig = 0.7 * ci_sig + 0.3 * ci_sig[CLOUD_REGION]
    net = st["net_kwh"] * _ln(rng, NOISE["route_energy"], st["net_kwh"].shape)
    network = (net * path_sig / 1000).sum(0)
    cdn = (st["cdn_kwh"] * _ln(rng, NOISE["cdn_logs"], st["cdn_kwh"].shape) * ci_sig / 1000).sum(0)
    dev = st["dev_kwh"] * _ln(rng, NOISE["device_class"], st["dev_kwh"].shape)
    device = (dev * ci_sig / 1000).sum(0)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": cdn, "Device": device}


METHODS = ["Batch", "Method 1", "Method 2", "Method 3"]


def run_workload(rng, w, a, ci):
    truth, st = simulate_truth(rng, w, a, ci)
    ci_sig = ci * _ln(rng, NOISE["ci_signal"], ci.shape)
    b = est_batch(w, a, st, ci)
    m1 = est_m1(rng, w, a, st, ci, ci_sig, truth)
    m2 = est_m2(rng, w, a, st, ci, ci_sig, truth, m1)
    m3 = est_m3(rng, w, a, st, ci, ci_sig)
    return truth, {"Batch": b, "Method 1": m1, "Method 2": m2, "Method 3": m3}, st


def _total(d):
    return sum(d[c] for c in COMPONENTS)


def wape(est, true):
    return float(np.abs(est - true).sum() / true.sum() * 100)


def evaluate(a: Assumptions, n_workloads, seed, keep_series=False):
    rng = np.random.default_rng(seed)
    ci = make_grid(rng, a.grid_diurnal_amp)
    workloads = sample_workloads(rng, n_workloads)
    rec = {m: {"mae": [], "bias": [], "daily": [], "comp": {c: [] for c in COMPONENTS},
               "annual": {c: [] for c in COMPONENTS}}
           for m in METHODS}
    shares, peak_share, idle_share_obs, annual_kg, visits_m = [], [], [], [], []
    series = None
    for i, w in enumerate(workloads):
        truth, est, st = run_workload(rng, w, a, ci)
        t_tot = _total(truth)
        shares.append([truth[c].sum() / t_tot.sum() for c in COMPONENTS])
        annual_kg.append(float(t_tot.sum()))
        visits_m.append(float(st["visits"].sum() / 12))
        ci_w = (truth["Compute"] + truth["Storage"]) / t_tot   # weight for top-CI hours
        eff_ci = (ci[CLOUD_REGION] * ci_w + (1 - ci_w) * (ci * w.mix[:, None]).sum(0))
        top = eff_ci >= np.percentile(eff_ci, 90)
        peak_share.append(t_tot[top].sum() / t_tot.sum() * 100)
        idle_share_obs.append(st["idle_kwh_h"] * HOURS / (
            st["compute_kwh"].sum() + st["storage_kwh"].sum() + st["net_kwh"].sum()
            + st["cdn_kwh"].sum() + st["dev_kwh"].sum()) * 100)
        for m in METHODS:
            e_tot = _total(est[m])
            rec[m]["mae"].append(wape(e_tot, t_tot))
            rec[m]["bias"].append(float((e_tot.sum() - t_tot.sum()) / t_tot.sum() * 100))
            rec[m]["daily"].append(wape(e_tot.reshape(-1, 24).sum(1), t_tot.reshape(-1, 24).sum(1)))
            for c in COMPONENTS:
                rec[m]["comp"][c].append(wape(est[m][c], truth[c]))
                rec[m]["annual"][c].append(float(est[m][c].sum() / t_tot.sum() * 100))
        if keep_series and i == 0:
            series = dict(ci=ci, truth={c: truth[c] for c in COMPONENTS},
                          est={m: _total(est[m]) for m in METHODS},
                          visits=st["visits"].sum(0), workload=w)
    return dict(rec=rec, shares=np.array(shares), peak_share=np.array(peak_share),
                idle_share=np.array(idle_share_obs), ci=ci, series=series,
                annual_kg=np.array(annual_kg), visits_m=np.array(visits_m))


def summarise(res, n_boot=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    out = {}
    for m in METHODS:
        x = np.array(res["rec"][m]["mae"])
        boots = rng.choice(x, size=(n_boot, x.size), replace=True).mean(1)
        out[m] = dict(
            mae=float(x.mean()), p5=float(np.percentile(x, 5)), p95=float(np.percentile(x, 95)),
            ci_lo=float(np.percentile(boots, 2.5)), ci_hi=float(np.percentile(boots, 97.5)),
            bias=float(np.mean(res["rec"][m]["bias"])),
            bias_p5=float(np.percentile(res["rec"][m]["bias"], 5)),
            bias_p95=float(np.percentile(res["rec"][m]["bias"], 95)),
            annual_abs=float(np.mean(np.abs(res["rec"][m]["bias"]))),
            daily_mae=float(np.mean(res["rec"][m]["daily"])),
            comp={c: float(np.mean(res["rec"][m]["comp"][c])) for c in COMPONENTS},
            annual_pct_of_true={c: float(np.mean(res["rec"][m]["annual"][c])) for c in COMPONENTS},
        )
    return out


def wilcoxon(res, a_m, b_m):
    x = np.array(res["rec"][a_m]["mae"])
    y = np.array(res["rec"][b_m]["mae"])
    stat, p = stats.wilcoxon(x, y)
    return dict(stat=float(stat), p=float(p), median_diff=float(np.median(x - y)),
                share_a_worse=float(np.mean(x > y) * 100))


SENSITIVITY = [
    ("network_kwh_per_gb", "Network electricity intensity (kWh/GB)", (0.002, 0.06)),
    ("grid_diurnal_amp", "Diurnal amplitude of grid carbon intensity", (0.10, 0.50)),
    ("traffic_peak_to_mean", "Traffic peak-to-mean ratio", (1.5, 3.0)),
    ("idle_share", "Idle capacity share of total energy", (0.05, 0.20)),
    ("pue", "Power usage effectiveness (PUE)", (1.1, 1.6)),
    ("telemetry_coverage", "Telemetry coverage of deterministic components", (0.25, 1.0)),
]


def coverage_curve(base, n, seed):
    out = []
    for cov in np.linspace(0, 1, 11):
        r = evaluate(replace(base, telemetry_coverage=float(cov)), n, seed)
        out.append(dict(coverage=float(cov), mae_m2=float(np.mean(r["rec"]["Method 2"]["mae"])),
                        mae_batch=float(np.mean(r["rec"]["Batch"]["mae"])),
                        mae_m1=float(np.mean(r["rec"]["Method 1"]["mae"])),
                        mae_m3=float(np.mean(r["rec"]["Method 3"]["mae"]))))
    return out


def main(n_workloads=200, n_sens=100):
    base = Assumptions()
    res = evaluate(base, n_workloads, SEED, keep_series=True)
    summary = summarise(res)
    tests = {"M2_vs_M3": wilcoxon(res, "Method 2", "Method 3"),
             "Batch_vs_M2": wilcoxon(res, "Batch", "Method 2"),
             "M1_vs_M2": wilcoxon(res, "Method 1", "Method 2")}

    sens = []
    for key, label, (lo, hi) in SENSITIVITY:
        row = dict(key=key, label=label, baseline=getattr(base, key), lo=lo, hi=hi, runs=[])
        for v in (lo, hi):
            r = evaluate(replace(base, **{key: v}), n_sens, SEED + 1)
            b = float(np.mean(r["rec"]["Batch"]["mae"]))
            m2 = float(np.mean(r["rec"]["Method 2"]["mae"]))
            row["runs"].append(dict(value=v, batch=b, m2=m2, ratio=b / m2))
        sens.append(row)
    cov = coverage_curve(base, n_sens, SEED + 2)

    s = res["series"]
    w = s["workload"]
    np.savez_compressed(
        OUT_DIR / "series.npz", ci=s["ci"], visits=s["visits"],
        **{f"truth_{c}": s["truth"][c] for c in COMPONENTS},
        **{f"est_{m.replace(' ', '_')}": s["est"][m] for m in METHODS},
        **{f"mae_{m.replace(' ', '_')}": np.array(res["rec"][m]["mae"]) for m in METHODS},
        shares=res["shares"],
    )
    results = dict(
        n_workloads=n_workloads, n_sensitivity=n_sens, seed=SEED,
        regions=REGIONS, grid_mean=GRID_MEAN.tolist(), components=COMPONENTS,
        factors=dict(network_kwh_per_gb=NETWORK_KWH_PER_GB, origin_kwh_per_visit=ORIGIN_KWH_PER_VISIT,
                     cdn_kg_per_gb=CDN_KG_PER_GB_DEFAULT, default_grid=DEFAULT_GRID,
                     bytes_per_visit_mb=BYTES_PER_VISIT_DEFAULT_MB),
        noise=NOISE, baseline=base.__dict__,
        summary=summary, tests=tests, sensitivity=sens, coverage=cov,
        shares_mean={c: float(res["shares"][:, i].mean() * 100) for i, c in enumerate(COMPONENTS)},
        peak_share=dict(mean=float(res["peak_share"].mean()), p5=float(np.percentile(res["peak_share"], 5)),
                        p95=float(np.percentile(res["peak_share"], 95))),
        idle_share_obs=float(res["idle_share"].mean()),
        example_workload=dict(monthly_visits=w.monthly_visits, page_mb=w.page_mb, mix=w.mix.tolist(),
                              cache_hit=w.cache_hit, n_instances=w.n_instances, vcpu=w.vcpu,
                              storage_tb=w.storage_tb),
        annual_kg=dict(mean=float(res["annual_kg"].mean()), median=float(np.median(res["annual_kg"])), p5=float(np.percentile(res["annual_kg"], 5)), p95=float(np.percentile(res["annual_kg"], 95))),
        visits_month=dict(median=float(np.median(res["visits_m"])), p5=float(np.percentile(res["visits_m"], 5)), p95=float(np.percentile(res["visits_m"], 95))),
        grid_stats={r: dict(mean=float(res["ci"][i].mean()), p5=float(np.percentile(res["ci"][i],5)), p95=float(np.percentile(res["ci"][i],95))) for i, r in enumerate(REGIONS)},
    )
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    r = main()
    for m, v in r["summary"].items():
        print(f"{m:9s} MAE {v['mae']:6.1f}  [{v['p5']:.1f}-{v['p95']:.1f}]  CI95 {v['ci_lo']:.1f}-{v['ci_hi']:.1f}"
              f"  bias {v['bias']:+.1f}  daily {v['daily_mae']:.1f}  comp " +
              " ".join(f"{c[:4]}={x:.0f}" for c, x in v['comp'].items()))
    print("shares", {k: round(v, 1) for k, v in r["shares_mean"].items()})
    print("tests", r["tests"])
    print("peak", r["peak_share"], "idle", r["idle_share_obs"])
    for s in r["sensitivity"]:
        print(s["label"], [(x["value"], round(x["batch"], 1), round(x["m2"], 1), round(x["ratio"], 2)) for x in s["runs"]])
    print([(c["coverage"], round(c["mae_m2"], 1)) for c in r["coverage"]])
