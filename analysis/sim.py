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

Design choices that guard against a self-confirming evaluation:
  - The reference ("true") system differs from the estimators' models in structure, not only
    through random noise: each workload has its own idle power floor, routing-path mix,
    seasonal PUE and true energy intensities for network, CDN, storage and devices, which the
    estimators only know through nominal factors or imperfect calibration.
  - Estimators carry per-workload systematic (calibration) errors that do not average out over
    the year, in addition to independent hourly measurement noise.
  - Every workload gets its own grid-intensity realisation, so workloads are independent.
  - An "annualised control" (Method 2's annual totals spread evenly over the year) separates the
    effect of temporal resolution from that of boundary and factor choices.
  - Equivalence between Method 2 and Method 3 is tested with a margin (TOST via bootstrap),
    not inferred from a non-significant difference.

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
CDN_KWH_PER_GB = CDN_KG_PER_GB_DEFAULT / (DEFAULT_GRID / 1000)
CPU_W_PER_CORE, RAM_W_PER_GB, SSD_W_PER_TB = 5.0, 0.375, 1.2
PUE_PRESETS = (1.1, 1.3, 1.6, 2.0)
STORAGE_REPLICAS = 3
NOMINAL_IDLE_FLOOR = 0.35                     # idle power as a share of peak, assumed by estimators
NOMINAL_PATH_WEIGHT = 0.7                     # share of path energy at the user market's grid
PUE_SEASONAL_AMP = 0.04                       # cooling overhead peaks in summer
PUE_PEAK_DAY = 200
BATCH_UTILISATION = 0.5
MATERIALITY_PCT = 5.0
EQUIVALENCE_MARGIN_PP = 1.0

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
    systematic_scale: float = 1.0     # multiplies every per-workload systematic error below


# Independent hourly measurement noise (multiplicative lognormal sigma, per hour unless noted).
NOISE = {
    "ci_signal": 0.05,        # published hourly grid intensity vs. true
    "util": 0.05,             # utilisation-based server power
    "cdn_logs": 0.05,
    "storage_meter": 0.05,
    "route_energy": 0.08,     # per-path network energy inference (Method 3)
    "device_class": 0.15,     # device-class power from tracker metadata
    "provider_month": 0.03,   # provider monthly report, per month
    "bytes": 0.02,            # tracker-observed transfer size
}

# How far the true system departs from the nominal factors, per workload (lognormal sigma).
# These are factor uncertainties that no estimator observes directly.
TRUTH_DEVIATION = {
    "network": 0.25,          # true network energy per GB vs. the platform factor
    "cdn": 0.25,              # true CDN energy per GB vs. the platform factor
    "storage": 0.20,          # true storage power vs. the SSD power model
    "device": 0.30,           # true device power vs. the device-class catalogue
}
TRUTH_IDLE_FLOOR_HALF_RANGE = 0.10   # true idle floor ~ U(0.35 +/- 0.10)
TRUTH_PATH_WEIGHT_HALF_RANGE = 0.15  # true path weight ~ U(0.70 +/- 0.15)

# Per-workload systematic error of each estimator's inputs (lognormal sigma unless noted).
CALIBRATION = {
    "power_model": 0.10,      # server peak power from spec sheets (Methods 2, 3)
    "pue_reported": 0.05,     # annual PUE reported by the provider (Methods 2, 3)
    "idle_capacity": 0.20,    # idle provisioned capacity inferred from inventory (Methods 2, 3)
    "grid_bias": 0.05,        # bias of the grid-intensity data source, per region (all hourly methods)
    "provider_report": 0.10,  # provider carbon reports vs. reality (Method 1)
    "route_model": 0.15,      # path-level network energy vs. reality (Method 3)
    "path_weight_abs": 0.10,  # absolute error of the inferred routing mix (Method 3)
    "device_telemetry": 0.15,  # device-class power vs. reality (Method 3)
    "storage_telemetry": 0.10,  # storage telemetry vs. reality (Method 3)
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


def pue_profile(pue):
    """Hourly PUE with a summer cooling peak, mean equal to the annual PUE."""
    doy = np.arange(HOURS) / 24.0
    return pue * (1 + PUE_SEASONAL_AMP * np.cos(2 * np.pi * (doy - PUE_PEAK_DAY) / 365.0))


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


def _ln(rng, sigma, shape=None):
    """Mean-one lognormal multiplier."""
    return np.exp(rng.normal(-0.5 * sigma**2, sigma, size=shape))


@dataclass(frozen=True)
class TrueSystem:
    """Per-workload properties of the reference system that estimators do not observe."""
    idle_floor: float
    path_weight: float
    network_dev: float
    cdn_dev: float
    storage_dev: float
    device_dev: float


def sample_true_system(rng, scale):
    return TrueSystem(
        idle_floor=float(NOMINAL_IDLE_FLOOR + rng.uniform(-1, 1) * TRUTH_IDLE_FLOOR_HALF_RANGE * scale),
        path_weight=float(np.clip(NOMINAL_PATH_WEIGHT + rng.uniform(-1, 1) * TRUTH_PATH_WEIGHT_HALF_RANGE * scale,
                                  0.05, 0.95)),
        network_dev=float(_ln(rng, TRUTH_DEVIATION["network"] * scale)),
        cdn_dev=float(_ln(rng, TRUTH_DEVIATION["cdn"] * scale)),
        storage_dev=float(_ln(rng, TRUTH_DEVIATION["storage"] * scale)),
        device_dev=float(_ln(rng, TRUTH_DEVIATION["device"] * scale)),
    )


@dataclass(frozen=True)
class Calibration:
    """Per-workload systematic errors of the estimators' inputs (multipliers, except path_weight)."""
    power: float
    pue: float
    idle: float
    grid: np.ndarray
    provider: float
    route: float
    path_weight: float
    device: float
    storage: float


def sample_calibration(rng, scale, true_path_weight):
    c = {k: v * scale for k, v in CALIBRATION.items()}
    return Calibration(
        power=float(_ln(rng, c["power_model"])),
        pue=float(_ln(rng, c["pue_reported"])),
        idle=float(_ln(rng, c["idle_capacity"])),
        grid=_ln(rng, c["grid_bias"], len(REGIONS)),
        provider=float(_ln(rng, c["provider_report"])),
        route=float(_ln(rng, c["route_model"])),
        path_weight=float(np.clip(true_path_weight + rng.normal(0, c["path_weight_abs"]), 0.05, 0.95)),
        device=float(_ln(rng, c["device_telemetry"])),
        storage=float(_ln(rng, c["storage_telemetry"])),
    )


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


def device_kwh_per_visit(w: Workload):
    return w.view_min * (w.mobile_share * DEVICE_KWH_PER_MIN["mobile"]
                         + (1 - w.mobile_share) * DEVICE_KWH_PER_MIN["desktop"])


def simulate_truth(rng, w: Workload, a: Assumptions, ci, ts: TrueSystem):
    visits = make_traffic(rng, w, a.traffic_peak_to_mean)            # (R,H)
    page_mb = w.page_mb * np.exp(rng.normal(0, 0.1, size=visits.shape))
    gb = visits * page_mb / 1024                                     # (R,H)
    tot_visits = visits.sum(0)
    load = tot_visits / np.percentile(tot_visits, 99)
    pue_h = pue_profile(a.pue)

    # compute: idle floor (workload-specific) plus utilisation driven by origin load after caching
    origin = tot_visits * (1 - w.cache_hit)
    u = np.clip(0.08 + 0.67 * origin / np.percentile(origin, 99), 0, 1)
    pmax = server_pmax_w(w.vcpu) * w.n_instances
    active_kwh = pmax * (ts.idle_floor + (1 - ts.idle_floor) * u) * pue_h / 1000 \
        + ORIGIN_KWH_PER_VISIT * origin
    storage_base_kwh = w.storage_tb * STORAGE_REPLICAS * SSD_W_PER_TB / 1000 * (1 + 0.3 * load)
    storage_kwh = storage_base_kwh * pue_h * ts.storage_dev

    ovh = 0.05 + 0.06 * load                                         # protocol / retransmission
    net_kwh = gb * a.network_kwh_per_gb * ts.network_dev * (1 + ovh)  # (R,H)
    cdn_kwh = gb * CDN_KWH_PER_GB * ts.cdn_dev                       # (R,H)
    dev_nominal = device_kwh_per_visit(w)
    dev_kwh = visits * dev_nominal * ts.device_dev

    # standby / idle provisioned capacity sized to the requested share of total energy
    non_idle = active_kwh.sum() + storage_kwh.sum() + net_kwh.sum() + cdn_kwh.sum() + dev_kwh.sum()
    idle_kwh_h = a.idle_share / (1 - a.idle_share) * non_idle / HOURS
    compute_kwh = active_kwh + idle_kwh_h

    ci_kg = ci / 1000.0
    path_ci = ts.path_weight * ci_kg + (1 - ts.path_weight) * ci_kg[CLOUD_REGION]
    truth = {
        "Compute": compute_kwh * ci_kg[CLOUD_REGION],
        "Storage": storage_kwh * ci_kg[CLOUD_REGION],
        "Network": (net_kwh * path_ci).sum(0),
        "CDN": (cdn_kwh * ci_kg).sum(0),
        "Device": (dev_kwh * ci_kg).sum(0),
    }
    state = dict(visits=visits, gb=gb, u=u, pmax=pmax, origin=origin, ovh=ovh,
                 compute_kwh=compute_kwh, active_kwh=active_kwh, idle_kwh_h=idle_kwh_h,
                 storage_base_kwh=storage_base_kwh, storage_kwh=storage_kwh, net_kwh=net_kwh,
                 cdn_kwh=cdn_kwh, dev_kwh=dev_kwh, dev_nominal=dev_nominal)
    return truth, state


# ---------------------------------------------------------------- helpers for estimators
MONTH_EDGES = np.linspace(0, HOURS, 13).astype(int)


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


# ---------------------------------------------------------------- the approaches
def est_batch(w, a, st):
    """Annual activity x static platform factors, partial boundary (cloud + data transfer)."""
    annual_compute_kwh = server_pmax_w(w.vcpu) * w.n_instances * BATCH_UTILISATION * a.pue * HOURS / 1000
    cloud_ci = GRID_MEAN[CLOUD_REGION] / 1000
    compute = np.full(HOURS, annual_compute_kwh * cloud_ci / HOURS)
    storage = np.full(HOURS, w.storage_tb * 1024 * STORAGE_KG_PER_GB_MONTH * 12 / HOURS)
    network = np.full(HOURS, st["gb"].sum() * NETWORK_KWH_PER_GB * DEFAULT_GRID / 1000 / HOURS)
    zero = np.zeros(HOURS)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": zero, "Device": zero}


def est_m1(rng, a, st, ci_sig, truth, cal: Calibration):
    """Operational hybrid: event-level web transfer, monthly provider / CDN / storage data."""
    pm = _ln(rng, NOISE["provider_month"], 12) * cal.provider
    compute = spread_monthly(truth["Compute"], pm)
    storage = spread_monthly(truth["Storage"], pm)
    gb_obs = st["gb"] * _ln(rng, NOISE["bytes"], st["gb"].shape)
    network = (gb_obs * a.network_kwh_per_gb * ci_sig / 1000).sum(0)
    cdn = spread_monthly(st["gb"].sum(0) * CDN_KG_PER_GB_DEFAULT)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": cdn,
            "Device": np.zeros(HOURS)}


def _compute_deterministic(rng, a, st, ci_sig_cloud, cal: Calibration):
    """Utilisation-driven power model with the nominal idle floor and calibrated inputs."""
    pmax_hat, pue_hat = st["pmax"] * cal.power, a.pue * cal.pue
    p = pmax_hat * (NOMINAL_IDLE_FLOOR + (1 - NOMINAL_IDLE_FLOOR) * st["u"]) * pue_hat / 1000 \
        + ORIGIN_KWH_PER_VISIT * st["origin"]
    p = p * _ln(rng, NOISE["util"], HOURS)
    return (p + st["idle_kwh_h"] * cal.idle) * ci_sig_cloud / 1000


def _cdn_deterministic(rng, st, ci_sig):
    """CDN logs give hourly bytes per edge; energy per GB is the nominal platform factor."""
    kwh = st["gb"] * CDN_KWH_PER_GB * _ln(rng, NOISE["cdn_logs"], st["gb"].shape)
    return (kwh * ci_sig / 1000).sum(0)


def est_m2(rng, a, st, ci_sig, m1, cal: Calibration):
    """Hybrid: deterministic compute + CDN (+ transfer volume), short-interval proxies elsewhere."""
    cov = a.telemetry_coverage
    compute = cov * _compute_deterministic(rng, a, st, ci_sig[CLOUD_REGION], cal) + (1 - cov) * m1["Compute"]
    cdn = cov * _cdn_deterministic(rng, st, ci_sig) + (1 - cov) * m1["CDN"]

    storage_kwh = st["storage_base_kwh"] * a.pue * cal.pue * _ln(rng, NOISE["storage_meter"], HOURS)
    storage = daily_mean(storage_kwh) * daily_mean(ci_sig[CLOUD_REGION]) / 1000
    gb_obs = st["gb"] * _ln(rng, NOISE["bytes"], st["gb"].shape)
    network = (gb_obs * a.network_kwh_per_gb * (1 + st["ovh"].mean()) * daily_mean(ci_sig) / 1000).sum(0)
    device = (daily_mean(st["visits"]) * st["dev_nominal"] * daily_mean(ci_sig) / 1000).sum(0)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": cdn, "Device": device}


def est_m3(rng, a, st, ci_sig, cal: Calibration):
    """Full event-level attribution with component telemetry (still calibrated, not perfect)."""
    compute = _compute_deterministic(rng, a, st, ci_sig[CLOUD_REGION], cal)
    storage = st["storage_kwh"] * cal.storage * _ln(rng, NOISE["storage_meter"], HOURS) \
        * ci_sig[CLOUD_REGION] / 1000
    path_sig = cal.path_weight * ci_sig + (1 - cal.path_weight) * ci_sig[CLOUD_REGION]
    net = st["net_kwh"] * cal.route * _ln(rng, NOISE["route_energy"], st["net_kwh"].shape)
    network = (net * path_sig / 1000).sum(0)
    cdn = _cdn_deterministic(rng, st, ci_sig)
    dev = st["dev_kwh"] * cal.device * _ln(rng, NOISE["device_class"], st["dev_kwh"].shape)
    device = (dev * ci_sig / 1000).sum(0)
    return {"Compute": compute, "Storage": storage, "Network": network, "CDN": cdn, "Device": device}


def annualised(est):
    """Same annual totals per component, spread evenly over the year (temporal-resolution control)."""
    return {c: np.full(HOURS, est[c].sum() / HOURS) for c in COMPONENTS}


METHODS = ["Batch", "Method 1", "Method 2", "Method 3"]
CONTROL = "Annualised Method 2"
ALL_METHODS = METHODS + [CONTROL]


def run_workload(rng, w, a, ci):
    ts = sample_true_system(rng, a.systematic_scale)
    truth, st = simulate_truth(rng, w, a, ci, ts)
    cal = sample_calibration(rng, a.systematic_scale, ts.path_weight)
    ci_sig = ci * cal.grid[:, None] * _ln(rng, NOISE["ci_signal"], ci.shape)
    b = est_batch(w, a, st)
    m1 = est_m1(rng, a, st, ci_sig, truth, cal)
    m2 = est_m2(rng, a, st, ci_sig, m1, cal)
    m3 = est_m3(rng, a, st, ci_sig, cal)
    est = {"Batch": b, "Method 1": m1, "Method 2": m2, "Method 3": m3, CONTROL: annualised(m2)}
    return truth, est, st


def _total(d):
    return sum(d[c] for c in COMPONENTS)


def wape(est, true):
    return float(np.abs(est - true).sum() / true.sum() * 100)


def evaluate(a: Assumptions, n_workloads, seed, keep_series=False):
    rng = np.random.default_rng(seed)
    workloads = sample_workloads(rng, n_workloads)
    rec = {m: {"mae": [], "bias": [], "daily": [], "comp": {c: [] for c in COMPONENTS},
               "annual": {c: [] for c in COMPONENTS}}
           for m in ALL_METHODS}
    shares, peak_share, idle_share_obs, annual_kg, visits_m, grid = [], [], [], [], [], []
    series = None
    for i, w in enumerate(workloads):
        ci = make_grid(rng, a.grid_diurnal_amp)            # independent grid year per workload
        truth, est, st = run_workload(rng, w, a, ci)
        t_tot = _total(truth)
        shares.append([truth[c].sum() / t_tot.sum() for c in COMPONENTS])
        annual_kg.append(float(t_tot.sum()))
        visits_m.append(float(st["visits"].sum() / 12))
        grid.append([[ci[r].mean(), np.percentile(ci[r], 5), np.percentile(ci[r], 95)]
                     for r in range(len(REGIONS))])
        ci_w = (truth["Compute"] + truth["Storage"]) / t_tot   # weight for top-CI hours
        eff_ci = (ci[CLOUD_REGION] * ci_w + (1 - ci_w) * (ci * w.mix[:, None]).sum(0))
        top = eff_ci >= np.percentile(eff_ci, 90)
        peak_share.append(t_tot[top].sum() / t_tot.sum() * 100)
        idle_share_obs.append(st["idle_kwh_h"] * HOURS / (
            st["compute_kwh"].sum() + st["storage_kwh"].sum() + st["net_kwh"].sum()
            + st["cdn_kwh"].sum() + st["dev_kwh"].sum()) * 100)
        for m in ALL_METHODS:
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
                idle_share=np.array(idle_share_obs), grid=np.array(grid), series=series,
                annual_kg=np.array(annual_kg), visits_m=np.array(visits_m))


def summarise(res, n_boot=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    out = {}
    for m in ALL_METHODS:
        x = np.array(res["rec"][m]["mae"])
        bias = np.array(res["rec"][m]["bias"])
        boots = rng.choice(x, size=(n_boot, x.size), replace=True).mean(1)
        out[m] = dict(
            mae=float(x.mean()), p5=float(np.percentile(x, 5)), p95=float(np.percentile(x, 95)),
            ci_lo=float(np.percentile(boots, 2.5)), ci_hi=float(np.percentile(boots, 97.5)),
            bias=float(bias.mean()),
            bias_p5=float(np.percentile(bias, 5)),
            bias_p95=float(np.percentile(bias, 95)),
            annual_abs=float(np.mean(np.abs(bias))),
            annual_abs_p95=float(np.percentile(np.abs(bias), 95)),
            share_over_materiality=float(np.mean(np.abs(bias) > MATERIALITY_PCT) * 100),
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
                mean_diff=float(np.mean(x - y)), share_a_worse=float(np.mean(x > y) * 100))


def equivalence(x, y, margin, n_boot=10000, seed=SEED):
    """Paired TOST via bootstrap: equivalent if the 90% CI of the mean difference lies within +/- margin."""
    rng = np.random.default_rng(seed)
    d = np.asarray(x) - np.asarray(y)
    boots = rng.choice(d, size=(n_boot, d.size), replace=True).mean(1)
    lo, hi = float(np.percentile(boots, 5)), float(np.percentile(boots, 95))
    return dict(mean_diff=float(d.mean()), ci90_lo=lo, ci90_hi=hi, margin=margin,
                equivalent=bool(lo > -margin and hi < margin))


SENSITIVITY = [
    ("network_kwh_per_gb", "Network electricity intensity (kWh/GB)", (0.002, 0.06)),
    ("grid_diurnal_amp", "Diurnal amplitude of grid carbon intensity", (0.10, 0.50)),
    ("traffic_peak_to_mean", "Traffic peak-to-mean ratio", (1.5, 3.0)),
    ("idle_share", "Idle capacity share of total energy", (0.05, 0.20)),
    ("pue", "Power usage effectiveness (PUE)", (1.1, 1.6)),
    ("systematic_scale", "Scale of systematic factor and calibration errors", (0.5, 2.0)),
    ("telemetry_coverage", "Telemetry coverage of deterministic components", (0.25, 1.0)),
]


def _run_stats(r):
    b = float(np.mean(r["rec"]["Batch"]["mae"]))
    m2 = float(np.mean(r["rec"]["Method 2"]["mae"]))
    m3 = float(np.mean(r["rec"]["Method 3"]["mae"]))
    m2_annual = float(np.mean(np.abs(r["rec"]["Method 2"]["bias"])))
    return dict(batch=b, m2=m2, m3=m3, ratio=b / m2, m2_annual_abs=m2_annual)


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
    abs_bias = {m: np.abs(res["rec"][m]["bias"]) for m in METHODS}
    equiv = {"hourly": equivalence(res["rec"]["Method 2"]["mae"], res["rec"]["Method 3"]["mae"],
                                   EQUIVALENCE_MARGIN_PP),
             "annual": equivalence(abs_bias["Method 2"], abs_bias["Method 3"], EQUIVALENCE_MARGIN_PP)}

    sens_base = _run_stats(evaluate(base, n_sens, SEED + 1))
    sens = []
    for key, label, (lo, hi) in SENSITIVITY:
        row = dict(key=key, label=label, baseline=getattr(base, key), lo=lo, hi=hi, runs=[])
        for v in (lo, hi):
            r = evaluate(replace(base, **{key: v}), n_sens, SEED + 1)
            row["runs"].append(dict(value=v, **_run_stats(r)))
        sens.append(row)
    cov = coverage_curve(base, n_sens, SEED + 2)

    s = res["series"]
    w = s["workload"]
    np.savez_compressed(
        OUT_DIR / "series.npz", ci=s["ci"], visits=s["visits"],
        **{f"truth_{c}": s["truth"][c] for c in COMPONENTS},
        **{f"est_{m.replace(' ', '_')}": s["est"][m] for m in METHODS},
        **{f"mae_{m.replace(' ', '_')}": np.array(res["rec"][m]["mae"]) for m in ALL_METHODS},
        shares=res["shares"],
    )
    g = res["grid"]   # (workloads, regions, [mean, p5, p95])
    results = dict(
        n_workloads=n_workloads, n_sensitivity=n_sens, seed=SEED,
        regions=REGIONS, grid_mean=GRID_MEAN.tolist(), components=COMPONENTS,
        factors=dict(network_kwh_per_gb=NETWORK_KWH_PER_GB, origin_kwh_per_visit=ORIGIN_KWH_PER_VISIT,
                     cdn_kg_per_gb=CDN_KG_PER_GB_DEFAULT, default_grid=DEFAULT_GRID,
                     bytes_per_visit_mb=BYTES_PER_VISIT_DEFAULT_MB,
                     storage_kg_per_gb_month=STORAGE_KG_PER_GB_MONTH),
        noise=NOISE, truth_deviation=TRUTH_DEVIATION, calibration=CALIBRATION,
        truth_ranges=dict(idle_floor=[NOMINAL_IDLE_FLOOR - TRUTH_IDLE_FLOOR_HALF_RANGE,
                                      NOMINAL_IDLE_FLOOR + TRUTH_IDLE_FLOOR_HALF_RANGE],
                          path_weight=[NOMINAL_PATH_WEIGHT - TRUTH_PATH_WEIGHT_HALF_RANGE,
                                       NOMINAL_PATH_WEIGHT + TRUTH_PATH_WEIGHT_HALF_RANGE],
                          pue_seasonal_amp=PUE_SEASONAL_AMP),
        materiality_pct=MATERIALITY_PCT,
        baseline=base.__dict__,
        summary=summary, tests=tests, equivalence=equiv,
        sensitivity_baseline=sens_base, sensitivity=sens, coverage=cov,
        shares_mean={c: float(res["shares"][:, i].mean() * 100) for i, c in enumerate(COMPONENTS)},
        peak_share=dict(mean=float(res["peak_share"].mean()), p5=float(np.percentile(res["peak_share"], 5)),
                        p95=float(np.percentile(res["peak_share"], 95))),
        idle_share_obs=float(res["idle_share"].mean()),
        example_workload=dict(monthly_visits=w.monthly_visits, page_mb=w.page_mb, mix=w.mix.tolist(),
                              cache_hit=w.cache_hit, n_instances=w.n_instances, vcpu=w.vcpu,
                              storage_tb=w.storage_tb),
        annual_kg=dict(mean=float(res["annual_kg"].mean()), median=float(np.median(res["annual_kg"])),
                       p5=float(np.percentile(res["annual_kg"], 5)), p95=float(np.percentile(res["annual_kg"], 95))),
        visits_month=dict(median=float(np.median(res["visits_m"])), p5=float(np.percentile(res["visits_m"], 5)),
                          p95=float(np.percentile(res["visits_m"], 95))),
        grid_stats={r: dict(mean=float(g[:, i, 0].mean()), p5=float(g[:, i, 1].mean()), p95=float(g[:, i, 2].mean()))
                    for i, r in enumerate(REGIONS)},
    )
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    r = main()
    for m, v in r["summary"].items():
        print(f"{m:20s} MAE {v['mae']:6.1f} [{v['p5']:.1f}-{v['p95']:.1f}] CI95 {v['ci_lo']:.1f}-{v['ci_hi']:.1f}"
              f" bias {v['bias']:+.1f} |annual| {v['annual_abs']:.1f} (p95 {v['annual_abs_p95']:.1f},"
              f" >5%: {v['share_over_materiality']:.0f}%) daily {v['daily_mae']:.1f} comp " +
              " ".join(f"{c[:4]}={x:.0f}" for c, x in v['comp'].items()))
    print("shares", {k: round(v, 1) for k, v in r["shares_mean"].items()})
    print("tests", r["tests"])
    print("equivalence", r["equivalence"])
    print("peak", r["peak_share"], "idle", r["idle_share_obs"], "kg", r["annual_kg"])
    print("sens base", r["sensitivity_baseline"])
    for s in r["sensitivity"]:
        print(s["label"], [(x["value"], round(x["batch"], 1), round(x["m2"], 1), round(x["m3"], 1),
                            round(x["ratio"], 2), round(x["m2_annual_abs"], 1)) for x in s["runs"]])
    print([(c["coverage"], round(c["mae_m2"], 1)) for c in r["coverage"]])
