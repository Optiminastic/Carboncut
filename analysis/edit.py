"""Fill the manuscript (unpacked in ../ed) with simulation results and new figures.

Usage: python edit.py <unpacked_docx_dir>
All numbers come from results.json (written by sim.py); figures from figures/*.png.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

HERE = Path(__file__).parent
R = json.loads((HERE / "results.json").read_text())
S = R["summary"]
B, M1, M2, M3 = (S[m] for m in ["Batch", "Method 1", "Method 2", "Method 3"])
SENS = {row["key"]: row for row in R["sensitivity"]}
COV = R["coverage"]
T = R["tests"]
SH = R["shares_mean"]
FIG_WIDTH_IN = 6.0
EMU_PER_IN = 914400


def f1(x):
    return f"{x:.1f}"


def rng(m):
    return f"{m['p5']:.1f}-{m['p95']:.1f}"


def ci(m):
    return f"{m['ci_lo']:.1f}-{m['ci_hi']:.1f}%"


def red_pp(m):
    return B["mae"] - m["mae"]


def red_rel(m):
    return red_pp(m) / B["mae"] * 100


def gain_share(m):
    return red_pp(m) / red_pp(M3) * 100


def step(a, b):
    return (a["mae"] - b["mae"]) / a["mae"] * 100


def comp_red(c):
    return (B["comp"][c] - M2["comp"][c]) / B["comp"][c] * 100


def tco2(m):
    return m["annual_abs"] * 10  # per 1,000 tCO2e


cov25 = SENS["telemetry_coverage"]["runs"][0]
NON_PHYSICAL = {"telemetry_coverage", "systematic_scale"}
phys_ratios = [r["ratio"] for k, row in SENS.items() if k not in NON_PHYSICAL for r in row["runs"]]
peak = R["peak_share"]
gs = R["grid_stats"]
ak = R["annual_kg"]
vm = R["visits_month"]
minor_share = SH["Network"] + SH["Device"] + SH["Storage"]

# ---------------------------------------------------------------- new / replaced text
C = S["Annualised Method 2"]
EQ = R["equivalence"]
SB = R["sensitivity_baseline"]
CAL = R["calibration"]
DEV = R["truth_deviation"]
NZ = R["noise"]
TR = R["truth_ranges"]
MAT = R["materiality_pct"]
sysr = SENS["systematic_scale"]["runs"]


def pc(v):
    return f"{v * 100:.0f}%"


DATA_PARAS = [
    "The methods were tested on a simulated mid-size software-as-a-service (SaaS) and marketing platform, a "
    "common type of platform for which internet-related emissions are reported. Emission and energy factors are taken directly from the production implementation of the CarbonCut carbon "
    "accounting platform, so that the analysis reflects factors used in practice: network data transfer of 0.006 kWh/GB, "
    "origin and CDN processing of 0.004 Wh per visit, a default page weight of 2 MB per visit, CDN delivery of 0.30 g "
    "CO₂e/GB, end-user device energy of 0.0012 Wh (mobile) and 0.0028 Wh (desktop) per minute of viewing, a component "
    "power model for servers (5 W per vCPU, 0.375 W per GB of memory and 1.2 W per TB of SSD storage) and data centre PUE "
    "presets between 1.1 and 2.0 (ISO/IEC, 2016). These factors are treated as nominal values: the reference system "
    "described in Section 2.3 departs from them by a workload-specific amount, reflecting the wide uncertainty in "
    "published intensities (Coroama and Hilty, 2014; Aslan et al., 2018).",

    f"Two hundred workloads were generated, each simulated hourly for one year (8,760 hours). Workload parameters were "
    f"sampled to span the range typical of this platform class: monthly visits log-uniformly between 20,000 and 120,000 "
    f"(median {vm['median']:,.0f}), page weight of 1.1-3.3 MB per visit, a CDN cache-hit ratio of 75-95%, one to four cloud "
    f"instances of 2-8 vCPU, 0.2-2 TB of triple-replicated storage, and a traffic mix across four markets (United Kingdom, "
    f"United States, India and Germany) drawn from a Dirichlet distribution centred on 40/30/15/15%. Hourly traffic "
    f"combines a working-day diurnal profile in each market's local time (peak-to-mean ratio 2.0), a weekend reduction, "
    f"seasonal troughs in August and late December, six two-day marketing campaigns per year and Poisson noise. The origin "
    f"infrastructure is located in a single London cloud region.",

    f"Hourly grid carbon intensity was synthesised separately for every workload, so that workloads are statistically "
    f"independent, by combining the annual averages used by the platform (United Kingdom 162, United States 342, India 589 "
    f"and Germany 298 gCO₂/kWh) with market-specific diurnal profiles (evening peaks and, where solar generation is "
    f"significant, midday troughs) of ±25% amplitude, seasonal variation and autocorrelated weather-driven variability, "
    f"consistent with the documented within-day and between-region variation in grid intensity (Hawkes, 2010; "
    f"Siler-Evans et al., 2012; Miller et al., 2022). The platform averages for India and Germany are lower than recent "
    f"national statistics (roughly 700 and 350-380 gCO₂/kWh respectively); because all errors are expressed relative to "
    f"the reference, the comparison between methods is largely insensitive to these levels, but absolute emissions for "
    f"those markets are understated. The resulting hourly intensities (mean 5th-95th percentile) range from "
    f"{gs['United Kingdom']['p5']:.0f} to {gs['United Kingdom']['p95']:.0f}, "
    f"{gs['United States']['p5']:.0f} to {gs['United States']['p95']:.0f}, {gs['India']['p5']:.0f} to "
    f"{gs['India']['p95']:.0f} and {gs['Germany']['p5']:.0f} to {gs['Germany']['p95']:.0f} gCO₂/kWh respectively. The "
    f"simulated workloads have median annual operational emissions of {ak['median']:.0f} kg CO₂e (5th-95th percentile "
    f"{ak['p5']:.0f}-{ak['p95']:.0f} kg), of which cloud compute accounts for {SH['Compute']:.0f}%, storage "
    f"{SH['Storage']:.0f}%, network transmission {SH['Network']:.0f}%, end-user devices {SH['Device']:.0f}% and CDN "
    f"delivery {SH['CDN']:.1f}% (Figure 4). These shares reflect a small site whose cloud instances are attributed to it in "
    f"full; the Sustainable Web Design approach, which allocates energy per gigabyte, assigns a far larger share to "
    f"networks and devices, so the shares should not be generalised to other allocation conventions.",
]

SETUP_PARAS = [
    "The reference (\"true\") emissions are generated by a component-level hourly model that is deliberately different "
    "in structure from the estimators, so that no method can reproduce it exactly. Compute energy follows a linear server "
    f"power model whose idle floor varies between workloads ({pc(TR['idle_floor'][0])}-{pc(TR['idle_floor'][1])} of peak "
    "power, whereas the estimators assume 35%), driven by origin request load after CDN caching and multiplied by an "
    f"hourly PUE with a ±{pc(TR['pue_seasonal_amp'])} summer cooling peak around its annual value (1.3 at baseline), plus "
    "a constant idle provisioned-capacity term sized to 10% of total energy. Storage energy combines replicated SSD power "
    "with a load-dependent input/output term. Network energy applies the network intensity to transferred volume plus a "
    "load-dependent protocol and retransmission overhead of 5-11%, and is attributed at the carbon intensity of the "
    f"routing path, whose share at the user market varies between workloads ({pc(TR['path_weight'][0])}-"
    f"{pc(TR['path_weight'][1])}, the remainder at the origin region). CDN energy is attributed at the intensity of the "
    "edge market and device energy at the intensity of the user market. For every workload the true energy intensities of "
    f"network transmission, CDN delivery, storage and devices also depart from the nominal platform factors (lognormal, 1σ "
    f"of {pc(DEV['network'])}, {pc(DEV['cdn'])}, {pc(DEV['storage'])} and {pc(DEV['device'])} respectively), "
    "representing the factor uncertainty that no estimator observes directly.",

    "The four approaches observe this system through different data. Conventional batch accounting multiplies annual "
    "instance-hours at an assumed 50% utilisation, annual stored volume and annual transferred data by static factors (the "
    "annual average of the cloud region, the platform storage factor and the platform default of 387 gCO₂/kWh), excludes "
    "CDN, device, protocol-overhead and idle-capacity energy, and spreads the annual total evenly over the year. Method 1 "
    "uses event-level transfer volumes from the page-view tracker with the hourly grid signal, monthly provider reports "
    "for compute and storage, and monthly CDN volumes multiplied by the platform CDN factor. Method 2 attributes compute "
    "(from hourly utilisation and a nominal power model) and CDN (from hourly logs and the nominal CDN factor) "
    "deterministically with the hourly grid signal, uses hourly transfer volumes with a mean overhead and daily average "
    "intensity for the network, and daily proxies for storage and devices. Method 3 attributes every component hourly "
    "from component telemetry and inferred routing paths. To isolate the effect of temporal resolution, an annualised "
    "control spreads the annual totals of Method 2 evenly over the year: it has the same boundary, data and annual totals "
    "as Method 2 and differs only in timing.",

    "Each estimator carries two kinds of error (Figure 14). Systematic errors are drawn once per workload and persist "
    f"all year: server peak power from specification data (1σ {pc(CAL['power_model'])}), reported PUE "
    f"({pc(CAL['pue_reported'])}), idle provisioned capacity inferred from inventory ({pc(CAL['idle_capacity'])}), the "
    f"bias of the grid-intensity data source in each market ({pc(CAL['grid_bias'])}), provider carbon reports "
    f"({pc(CAL['provider_report'])}), and, for Method 3 only, path-level network energy ({pc(CAL['route_model'])}), the "
    f"inferred routing mix (±{CAL['path_weight_abs'] * 100:.0f} percentage points), device-class power "
    f"({pc(CAL['device_telemetry'])}) and storage telemetry ({pc(CAL['storage_telemetry'])}). Independent hourly "
    f"measurement noise is added on top: grid-intensity signal ±{pc(NZ['ci_signal'])}, utilisation-based power and CDN "
    f"logs ±{pc(NZ['util'])}, path-level network energy ±{pc(NZ['route_energy'])}, device-class power "
    f"±{pc(NZ['device_class'])} and monthly provider reports ±{pc(NZ['provider_month'])}. Without systematic errors, "
    "hourly noise largely cancels over a year, which would make the annual totals of every high-resolution method "
    "unrealistically exact.",

    f"Attribution error is measured for each workload as the weighted absolute percentage error of the hourly emissions "
    f"series, that is, the sum of absolute hourly deviations divided by total reference emissions, which avoids "
    f"instability in low-traffic hours. MAE denotes the mean of this quantity across the {R['n_workloads']} workloads and "
    f"the error range its 5th-95th percentile. Because a series that is flat in time is penalised by this metric even "
    f"when its annual total is correct, the absolute error in annual totals is reported separately as the "
    f"decision-relevant quantity for annual disclosure, and bias is the signed error in annual totals. Uncertainty in "
    f"the MAE is quantified with 10,000 bootstrap resamples of workloads; these intervals describe Monte Carlo "
    f"uncertainty within the simulation, not real-world uncertainty. Paired differences between methods are tested with "
    f"the Wilcoxon signed-rank test, and practical equivalence between Methods 2 and 3 with a paired two one-sided test "
    f"(90% bootstrap interval of the mean difference within ±{EQ['hourly']['margin']:.0f} percentage point). Sensitivity "
    f"is assessed one parameter at a time on {R['n_sensitivity']} workloads against a baseline run on the same workloads "
    f"(Section 3.9). The simulation code is written in Python (NumPy, SciPy) with a fixed random seed.",
]

REPLACE = {
    # ---- title
    "Towards Near-Real-Time Carbon Accounting for Internet Data Transmission":
        "Challenging the Legacy Internet Carbon Accounting",

    # ---- abstract
    "Using synthetic datasets designed to reflect the architecture":
        "Digital infrastructure and internet-based services contribute an estimated 2-4% of global CO₂e emissions, a share "
        "comparable to aviation and projected to grow. Current carbon accounting practices for internet data transmission "
        "rely on annualised, batch-based estimation methods, which lack temporal granularity, omit critical components of "
        "the transmission circuit, and introduce structural bias into emissions reporting. This paper proposes and evaluates "
        "three complementary attribution methodologies designed to overcome these limitations: (1) an operational hybrid "
        "resolution method for compliance-grade reporting; (2) a hybrid deterministic-batch method for improved accuracy "
        "under real-world telemetry constraints; and (3) a fully deterministic event-level framework representing the "
        "theoretical upper bound of attribution fidelity. Using synthetic hourly datasets for 200 workloads of a "
        "representative mid-size website, built with the emission factors of a production carbon accounting platform and "
        "including realistic systematic calibration errors, we show that the hybrid deterministic-batch method reduces "
        f"hourly attribution error from {B['mae']:.0f}% under conventional batch accounting to {M2['mae']:.0f}%, within "
        f"{EQ['hourly']['margin']:.0f} percentage point of the fully deterministic benchmark, and by about "
        f"{(1 - cov25['m2'] / cov25['batch']) * 100:.0f}% when only a quarter of its deterministic components are covered "
        f"by telemetry. All three methods remove most of the {-B['bias']:.0f}% annual underestimate of batch accounting, "
        f"but their annual totals remain uncertain by about {M1['annual_abs']:.0f}-{max(M2['annual_abs'], M3['annual_abs']):.0f}% "
        "on average, because emission factors and calibration, rather than temporal resolution, limit annual accuracy. Our "
        "findings indicate that near-real-time carbon accounting for internet data transmission is technically feasible "
        "and substantially improves the temporal fidelity needed for operational decisions, while accurate annual "
        "disclosure additionally depends on better calibrated energy and emission factors.",

    # ---- introduction (statistic aligned with the cited range)
    "The internet and associated digital infrastructure now account for an estimated":
        "The internet and associated digital infrastructure now account for an estimated 2-4% of global CO₂e emissions, a "
        "share comparable to that of the aviation sector (Belkhir and Elmeligi, 2018; Malmodin and Lundén, 2018; Freitag et "
        "al., 2021) and expected to rise with continued growth in cloud computing, artificial intelligence, and "
        "data-intensive digital services (Andrae and Edler, 2015; Obringer et al., 2021). Projections suggest that, in the "
        "absence of targeted methodological and operational interventions, emissions from digital infrastructure will "
        "continue to increase in both absolute and relative terms, amplifying the importance of robust carbon accounting "
        "for internet activity. Data centre electricity demand is projected to rise substantially with the expansion of AI "
        "workloads (IEA, 2025), although estimates of current and future energy use remain highly sensitive to "
        "methodological assumptions and data sources (Masanet et al., 2020; Mytton and Ashtine, 2022). Sector-specific "
        "assessments, for example of online advertising, likewise indicate a substantial but highly uncertain footprint "
        "(Pärssinen et al., 2018).",

    # ---- 2.3 experimental setup
    "To evaluate the methodologies, representative pilot data":
        "To evaluate the methodologies, the dataset described in Section 2.1 is used to construct, for every workload and "
        "hour, a reference emissions series and the estimates produced by each approach. The simulated platform is designed "
        "to preserve the essential statistical and structural characteristics of a production mid-size SaaS system.",
    "Experimental evaluation focuses on comparing Method 2 against Method 3":
        "Experimental evaluation focuses on comparing Method 2 against Method 3, with conventional batch accounting serving "
        "as the reference baseline; Method 1 is treated as an operational standard and is reported for completeness but not "
        "optimised for error. The experimental architecture (Figure 11) includes user devices in four markets, access and "
        "backbone network segments, CDN edges in each market and a single-region cloud origin.",

    # ---- 3.1
    "Attribution accuracy is assessed using mean absolute error (MAE)":
        "Attribution accuracy is assessed using mean absolute error (MAE) and error ranges for four approaches: conventional "
        "batch accounting, Method 1, Method 2 and Method 3, each operating at a different point on the resolution ladder "
        f"(Figure 6). Conventional batch accounting, with annual temporal resolution and partial system boundary coverage, "
        f"exhibits a MAE of {f1(B['mae'])}% with a range of {rng(B)}%. Two distinct causes contribute. Batch accounting "
        f"understates annual emissions by {-B['bias']:.1f}% on average, because it omits CDN, device, protocol-overhead and "
        f"idle-capacity energy and relies on a storage factor and a utilisation assumption that understate actual energy use "
        f"(Figure 3). Separately, its flat profile cannot follow hourly variation: the annualised control, which has the same "
        f"annual totals as Method 2 but no temporal resolution, still has a MAE of {f1(C['mae'])}% ({rng(C)}%). Roughly "
        f"{(B['mae'] - C['mae']):.0f} percentage points of the batch error can therefore be attributed to boundary and "
        f"factor choices and the remaining {(C['mae'] - M2['mae']):.0f} points of the gap to Method 2 to temporal resolution.",
    "which combines event":
        f"Method 1, which combines event-level and monthly signals within a conservative, compliance-oriented framework, "
        f"reduces MAE to {f1(M1['mae'])}% ({rng(M1)}%). Its mean bias is small ({M1['bias']:+.1f}%), but individual workloads "
        f"deviate by {M1['annual_abs']:.1f}% in annual totals on average because provider reports carry their own systematic "
        f"error; its remaining hourly error reflects the uniform distribution of monthly compute, storage and CDN totals "
        f"across each month. Method 2 reduces MAE to {f1(M2['mae'])}% ({rng(M2)}%), a {B['mae'] / M2['mae']:.1f}-fold "
        f"reduction relative to conventional batch accounting, by attributing compute and CDN emissions hourly using "
        f"utilisation data, CDN logs and the hourly grid signal. Method 3, the full event-level model, achieves a MAE of "
        f"{f1(M3['mae'])}% ({rng(M3)}%). Its error is not small, because full telemetry does not remove systematic errors in "
        f"server power models, reported PUE, idle capacity and grid-intensity data, which Methods 2 and 3 share.",
    "The pattern across the four approaches confirms":
        "The pattern across the four approaches shows that hourly attribution performance improves with temporal resolution "
        "and boundary completeness, with sharply diminishing returns once compute and CDN are treated at event level: for "
        f"the platform profile studied here, the step from Method 2 to Method 3 reduces MAE by only "
        f"{M2['mae'] - M3['mae']:.1f} percentage points. The wide and right-skewed error ranges of Methods 2 and 3 show "
        "that, for an individual organisation, the realised error depends mainly on how well its compute energy model is "
        "calibrated.",

    # ---- 3.2
    "Beyond aggregate MAE, the analysis examines":
        "Beyond aggregate MAE, the analysis examines how attribution error varies across components of the transmission "
        "circuit (Figure 9). Under conventional batch accounting, CDN and device emissions are excluded entirely (100% "
        f"component error), storage is understated by the platform's per-gigabyte storage factor ({B['comp']['Storage']:.0f}% "
        f"error), and network emissions carry a {B['comp']['Network']:.0f}% error from the use of a static default intensity "
        f"and the omission of protocol overhead. Because compute represents {SH['Compute']:.0f}% of emissions, however, the "
        f"{B['comp']['Compute']:.0f}% error in compute dominates the aggregate. Under Method 1, residual error is concentrated "
        f"in compute ({M1['comp']['Compute']:.0f}%) and CDN ({M1['comp']['CDN']:.0f}%), whose monthly totals are temporally "
        f"flattened, while event-level treatment of data transfer keeps network error at {M1['comp']['Network']:.0f}%.",
    "hybrid design explicitly targets these":
        "Method 2's hybrid design targets the components that drive this residual: deterministic attribution of compute and "
        f"CDN emissions reduces their errors to {M2['comp']['Compute']:.0f}% and {M2['comp']['CDN']:.0f}% respectively; the "
        "CDN error that remains is set by the uncertainty of the CDN energy factor rather than by timing. Its largest "
        f"remaining component errors are for devices ({M2['comp']['Device']:.0f}%), network ({M2['comp']['Network']:.0f}%) "
        f"and storage ({M2['comp']['Storage']:.0f}%), which are allocated through daily proxies and nominal factors, but "
        f"these components together account for only {minor_share:.0f}% of emissions. Under Method 3, component errors range "
        f"from {min(M3['comp'].values()):.0f}% to {max(M3['comp'].values()):.0f}% and are determined by the assumed "
        "calibration and measurement errors rather than by structural limitations in system boundary or resolution.",

    # ---- 3.3
    "Temporal responsiveness is evaluated by comparing":
        "Temporal responsiveness is evaluated by comparing how each method represents emissions during periods of high load "
        "and periods of elevated grid carbon intensity. Batch methods, which aggregate activity and apply static emission "
        "factors, smooth emissions over time and fail to reproduce peaks that occur when high traffic coincides with "
        "carbon-intensive grid conditions (Figure 2). In the simulated workloads, the 10% of hours with the highest effective "
        f"grid intensity account for {peak['mean']:.1f}% of annual emissions ({peak['p5']:.1f}-{peak['p95']:.1f}%), whereas a "
        "time-invariant batch estimate assigns them exactly 10%. The concentration is moderate, because demand peaks and "
        "grid peaks only partly coincide, so the potential of load shifting for a site of this kind should not be overstated.",
    "All three proposed methods capture temporal variation":
        "All three proposed methods capture temporal variation to some extent, with the event-level approach providing the "
        "highest sensitivity to short-term fluctuations (Figure 10). Method 1 preserves high-frequency signals for sources "
        "where event data are available, while Method 2 goes further by aligning deterministic attribution of compute and CDN "
        "with time-resolved grid intensity, making peak emissions visible and actionable. Emissions time series show a tight "
        "coupling between grid carbon intensity and attributed emissions under Methods 2 and 3 (Figure 12); at daily "
        f"resolution their errors are {M2['daily_mae']:.1f}% and {M3['daily_mae']:.1f}%, compared with "
        f"{M1['daily_mae']:.1f}% for Method 1, {C['daily_mae']:.1f}% for the annualised control and {B['daily_mae']:.1f}% "
        "for conventional batch accounting. Most of the remaining daily error of Methods 2 and 3 is a persistent level "
        "offset from calibration error rather than a failure to follow the timing of emissions.",

    # ---- 3.4
    "The comparison between Method 2 and Method 3 reveals":
        "The comparison between Method 2 and Method 3 shows that marginal gains from full determinism are concentrated in "
        "components where routing paths, path-level grid intensity and device behaviour influence emissions, namely network "
        "transmission, storage and end-user devices. For a website whose emissions are dominated by compute, these "
        f"components are a small share of the total, so Method 2 captures {gain_share(M2):.0f}% of the achievable reduction "
        "in hourly error without the complexity and data requirements of Method 3. Both methods rely on the same compute "
        "energy model, so improving that model would benefit both, whereas adding telemetry for the minor components "
        "would not. For network-heavy services such as video streaming or large file transfer, the gap between the two "
        "methods would be expected to be larger.",

    # ---- 3.5
    "To move beyond aggregate error values, Table 1":
        "To move beyond aggregate error values, Table 1 expresses the performance of each method relative to conventional "
        f"batch accounting and to the full event-level benchmark. Method 2 reduces MAE by {red_pp(M2):.1f} percentage points "
        f"({red_rel(M2):.1f}%) relative to batch accounting, an error ratio of {B['mae'] / M2['mae']:.2f}, and closes "
        f"{gain_share(M2):.1f}% of the gap between batch accounting and Method 3. Method 1 closes {gain_share(M1):.0f}% of "
        "this gap despite not being optimised for fidelity. The final step from Method 2 to Method 3 yields a further "
        f"{M2['mae'] - M3['mae']:.1f} percentage points while requiring full telemetry for every component of the circuit. "
        "Figure 13 shows how this outcome depends on telemetry availability: the error of Method 2 falls as coverage of its "
        f"deterministic components increases, from {COV[0]['mae_m2']:.1f}% with no coverage to about "
        f"{min(c['mae_m2'] for c in COV):.1f}% at 80-90% coverage, and is flat within simulation noise beyond that point, "
        "because the residual is dominated by calibration error that more coverage does not remove.",
    "Expressed as proportional reductions between successive rungs":
        "Expressed as proportional reductions between successive rungs, the gains are uneven: the step from batch accounting "
        f"to Method 1 reduces the remaining error by {step(B, M1):.1f}%, Method 1 to Method 2 by {step(M1, M2):.1f}%, and "
        f"Method 2 to Method 3 by only {step(M2, M3):.1f}%. The diminishing returns at the top of the ladder reflect the fact "
        "that, once compute and CDN are treated deterministically, the remaining error is dominated by systematic "
        "calibration error and measurement noise shared by all high-resolution methods, which full determinism does not "
        "remove. Further investment is therefore better directed at calibrating the compute energy model and the energy "
        "intensities of network and CDN than at extending telemetry to minor components, except for services in which "
        "network and device emissions form a larger share of the total.",

    # ---- 3.6
    "The reported error ranges give a first indication":
        f"The bootstrap 95% confidence intervals for the MAE are {ci(B)} for conventional batch accounting, {ci(M1)} for "
        f"Method 1, {ci(M2)} for Method 2 and {ci(M3)} for Method 3. The intervals for the first three rungs are widely "
        "separated, and Wilcoxon signed-rank tests show that Method 2 has a lower error than batch accounting in "
        f"{T['Batch_vs_M2']['share_a_worse']:.0f}% of workloads and lower than Method 1 in "
        f"{T['M1_vs_M2']['share_a_worse']:.0f}% (both p < 0.001). With 200 workloads, even small differences become "
        "statistically detectable, so significance alone says little about practical relevance. The difference between "
        f"Method 2 and Method 3 is small but detectable (Wilcoxon p = {T['M2_vs_M3']['p']:.2f}; mean paired difference "
        f"{T['M2_vs_M3']['mean_diff']:+.2f} percentage points; Method 2 has the higher error in "
        f"{T['M2_vs_M3']['share_a_worse']:.0f}% of workloads). An equivalence test is therefore the appropriate check: the "
        f"90% bootstrap interval of the mean difference ({EQ['hourly']['ci90_lo']:+.2f} to {EQ['hourly']['ci90_hi']:+.2f} "
        f"percentage points) lies within the ±{EQ['hourly']['margin']:.0f} point margin, as does the interval for the "
        f"difference in annual-total error ({EQ['annual']['ci90_lo']:+.2f} to {EQ['annual']['ci90_hi']:+.2f}), so the two "
        "methods are practically equivalent for this platform class. The error distribution of Method 1 is narrow, because "
        "its error is dominated by monthly flattening that is similar across workloads, whereas the distributions of "
        "Methods 2 and 3 are wider and right-skewed, reflecting workload-specific calibration error.",

    # ---- 3.7
    "decomposes the error reduction achieved by the hybrid approach":
        "Figure 9 decomposes the error reduction achieved by the hybrid approach by component of the transmission circuit. "
        f"In relative terms, the largest reductions occur for storage ({comp_red('Storage'):.0f}%) and CDN "
        f"({comp_red('CDN'):.0f}%), followed by end-user devices ({comp_red('Device'):.0f}%), compute "
        f"({comp_red('Compute'):.0f}%) and network transmission ({comp_red('Network'):.0f}%). Because compute accounts for "
        f"{SH['Compute']:.0f}% of emissions, however, its reduction from {B['comp']['Compute']:.0f}% to "
        f"{M2['comp']['Compute']:.0f}% contributes most of the aggregate improvement. This is consistent with the design logic "
        "of Method 2: compute energy use is both variable, responding to load, caching behaviour and time of day, and well "
        "observed through utilisation metrics, so deterministic treatment yields the largest benefit (Figure 7). Network "
        "transmission shows the smallest relative improvement because backbone and access-network energy remain allocated "
        "through nominal factors and daily average intensity in the absence of routing-level telemetry. The importance of "
        "components that are often omitted is supported by production measurements of AI serving, in which idle provisioned "
        "capacity and facility overhead together accounted for about 18% of per-request energy and were excluded by "
        "narrower measurement boundaries (Elsworth et al., 2025).",

    # ---- 3.8
    "The practical consequence of attribution error can be illustrated":
        "The practical consequence of attribution error for reporting depends on whether it affects annual totals or only "
        "their distribution in time. For an organisation reporting annual internet-related emissions of 1,000 tCO₂e, the mean "
        f"absolute error in annual totals implies an expected deviation of approximately ±{tco2(B):.0f} tCO₂e under "
        f"conventional batch accounting, compared with ±{tco2(M1):.0f}, ±{tco2(M2):.0f} and ±{tco2(M3):.0f} tCO₂e under "
        f"Methods 1, 2 and 3. Against a materiality threshold of {MAT:.0f}%, which is commonly applied in greenhouse gas "
        f"verification, conventional batch accounting fails for every workload, but the proposed methods also exceed the "
        f"threshold for {M1['share_over_materiality']:.0f}%, {M2['share_over_materiality']:.0f}% and "
        f"{M3['share_over_materiality']:.0f}% of workloads respectively under the assumed calibration errors. Higher "
        "temporal resolution therefore does not by itself deliver materially accurate annual totals; that requires "
        "calibration of the energy model and emission factors, for example against metered data or provider-reported "
        "energy. For daily or hourly reporting, which carbon-aware operation requires, Methods 2 and 3 are clearly superior "
        f"(daily errors of {M2['daily_mae']:.1f}% and {M3['daily_mae']:.1f}%, against {M1['daily_mae']:.1f}% for Method 1). "
        "This reinforces the role of the provenance and assurance tagging built into Method 1, which makes the remaining "
        "uncertainty explicit to auditors rather than concealing it within a single annual figure.",
    "MAE does not, however, indicate whether batch accounting":
        "MAE does not indicate whether an approach systematically over- or under-estimates emissions. In the simulated "
        f"workloads, the mean signed error in annual totals is {B['bias']:+.1f}% for conventional batch accounting (5th-95th "
        f"percentile {B['bias_p5']:+.1f}% to {B['bias_p95']:+.1f}%), {M1['bias']:+.1f}% for Method 1, {M2['bias']:+.1f}% "
        f"for Method 2 and {M3['bias']:+.1f}% for Method 3, with 5th-95th percentiles of {M2['bias_p5']:+.0f}% to "
        f"{M2['bias_p95']:+.0f}% for Method 2. The batch bias is driven mainly by boundary omissions and by factors that "
        "understate storage and idle energy, rather than by temporal averaging; part of it stems from a platform storage "
        "factor that is far below a power-based estimate and should be corrected in the platform itself. The positive "
        "bias of Methods 2 and 3 arises mainly from the nominal idle floor, which is higher than that of many simulated "
        "servers. Temporal averaging introduces a further, profile-dependent bias: because batch methods apply annual "
        "average carbon intensity, they understate emissions when demand coincides with carbon-intensive grid periods and "
        f"overstate them when demand is concentrated in low-carbon periods (Miller et al., 2022). The 10% of hours with the "
        f"highest grid carbon intensity hold {peak['mean']:.1f}% of emissions, so a time-invariant factor understates the "
        f"emissions of these hours by about {(1 - 10 / peak['mean']) * 100:.0f}%. The direction of this bias depends on how "
        "an organisation's traffic profile aligns with grid conditions (Figure 12), which has direct implications for the "
        "credibility of reported reductions and for the design of demand-shifting strategies (Wiesner et al., 2021; "
        "Radovanović et al., 2023).",

    # ---- 3.9
    "Because the results are derived from synthetic datasets":
        "Because the results are derived from synthetic datasets, their robustness to the assumptions used to generate those "
        "datasets must be established. The key test is whether the advantage of Method 2 over conventional batch accounting "
        "is preserved across plausible ranges of the parameters that most influence attributed emissions (Table 2). Published "
        "estimates of network electricity intensity, for example, vary by orders of magnitude depending on boundary and "
        "reference year (Coroama and Hilty, 2014; Aslan et al., 2018), and grid carbon intensity varies substantially by hour "
        "and region (Hawkes, 2010; Siler-Evans et al., 2012). Each parameter was set to the lower and upper ends of its range "
        f"with all others held at baseline, on {R['n_sensitivity']} workloads; on the same workloads the baseline gives "
        f"MAEs of {SB['batch']:.1f}% (batch) and {SB['m2']:.1f}% (Method 2), an error ratio of {SB['ratio']:.1f}. Across "
        f"the five physical parameters, the ratio remains between {min(phys_ratios):.1f} and {max(phys_ratios):.1f}, so the "
        "advantage of the hybrid approach is not an artefact of any single physical assumption. Batch error is most "
        f"sensitive to network intensity ({SENS['network_kwh_per_gb']['runs'][0]['batch']:.1f}-"
        f"{SENS['network_kwh_per_gb']['runs'][1]['batch']:.1f}%) and the idle capacity share "
        f"({SENS['idle_share']['runs'][0]['batch']:.1f}-{SENS['idle_share']['runs'][1]['batch']:.1f}%), because both "
        "increase the share of energy that lies outside the batch boundary or is estimated with static factors. Two "
        "assumptions materially change the result. The first is the size of systematic errors: halving them lowers "
        f"Method 2 MAE to {sysr[0]['m2']:.1f}% (ratio {sysr[0]['ratio']:.1f}), while doubling them raises it to "
        f"{sysr[1]['m2']:.1f}% (ratio {sysr[1]['ratio']:.1f}) and its annual-total error to {sysr[1]['m2_annual_abs']:.0f}%. "
        f"The second is telemetry coverage: when only 25% of the deterministic components are covered, Method 2 MAE rises "
        f"to {cov25['m2']:.1f}% and the error ratio falls to {cov25['ratio']:.1f}.",
    "Table 2. Sensitivity of attribution error":
        f"Table 2. Sensitivity of attribution error to key modelling assumptions (one-at-a-time, {R['n_sensitivity']} "
        f"workloads; baseline MAE {SB['batch']:.1f}% batch and {SB['m2']:.1f}% Method 2). Each cell gives the value at the "
        "lower / upper end of the range tested; error ratio = MAE batch / MAE Method 2.",

    # ---- critical appraisal
    "Several features of the experimental design qualify":
        "Several features of the experimental design qualify the interpretation of these results. First, all errors are "
        "measured against a synthetic reference. To avoid a self-confirming evaluation, the reference differs from every "
        "estimator in structure (workload-specific idle floors, routing mixes, seasonal PUE and true energy intensities that "
        "depart from the nominal factors), and the estimators carry systematic calibration errors as well as hourly noise "
        "(Section 2.3). The absolute errors of Methods 2 and 3 nevertheless depend directly on the assumed size of these "
        f"errors, which is not calibrated against production data: Table 2 shows Method 2 MAE between {sysr[0]['m2']:.0f}% "
        f"and {sysr[1]['m2']:.0f}% when they are halved or doubled. The values should therefore be read as indicators of "
        "relative performance rather than as estimates of real-world accuracy. Second, part of the batch error arises from "
        "platform default factors, notably a per-gigabyte storage factor that understates storage energy relative to a "
        "power-based estimate; the annualised control shows that batch accounting with a complete boundary and calibrated "
        f"factors would have a much smaller annual bias, although its hourly error ({C['mae']:.0f}%) would remain. Third, "
        "network energy is modelled as proportional to transferred data. Power-based models attribute most network energy "
        "to fixed baseload, under which the marginal energy of additional data is small (Malmodin and Lundén, 2018); the "
        "network results describe an attributional allocation, not the consequence of changing traffic. Fourth, the "
        "analysis covers a single platform architecture and traffic profile and uses average (location-based) grid "
        "intensity; services dominated by video streaming, large file transfer or AI inference differ in the relative "
        "weight of network and compute components (Aslan et al., 2018; Elsworth et al., 2025), and marginal or "
        "market-based emission factors would change absolute results. Finally, the evaluation is limited to operational "
        "electricity-related emissions and does not consider the embodied emissions of network and end-user equipment, "
        "which can be material over the life cycle of digital services (Gupta et al., 2021). Validation against metered "
        "data from a production environment, as has recently been demonstrated for AI serving (Elsworth et al., 2025), is "
        "therefore the most important next step.",

    # ---- discussion
    "The expanded results confirm that attribution accuracy":
        "The results indicate that the temporal fidelity of internet emissions accounting is primarily a function of "
        "temporal resolution and system boundary completeness, and that hybrid approaches can capture most of the attainable "
        "gains. Annual accuracy is a different matter: once the boundary is complete, it is limited by the calibration of "
        "energy models and emission factors, which finer temporal resolution does not improve. By combining deterministic "
        "attribution for high-variance components with conservative batch treatment of structurally opaque elements, the "
        "hybrid deterministic-batch method substantially outperforms conventional batch accounting while remaining "
        "deployable at scale under current data availability. This mirrors evidence from production measurement of AI "
        "serving, where differences in measurement boundary alone account for order-of-magnitude variation in published "
        "per-request energy estimates, and a narrow boundary understated energy by a factor of 2.4 relative to a "
        "comprehensive boundary for the same workload (Elsworth et al., 2025).",
    "The study is limited by incomplete access to ISP-level":
        "The study is limited by incomplete access to ISP-level and backbone energy data, partial reliance on inferred "
        "routing paths, and the use of synthetic datasets rather than cross-provider empirical datasets. The size of the "
        "systematic calibration errors, the platform's grid-intensity averages and its storage factor are assumptions that "
        "require empirical confirmation. The wider literature on computing emissions shows that reported footprints are "
        "highly sensitive to measurement boundary, hardware utilisation and the treatment of embodied emissions (Strubell et "
        "al., 2019; Gupta et al., 2021; Patterson et al., 2021; Luccioni et al., 2023), underlining the need for empirical "
        "validation of the present framework. These limitations primarily affect the calibration of Methods 2 and 3 and "
        "the annual accuracy of all methods, while leaving the compliance-oriented design of Method 1 largely unaffected. "
        "In addition, the framework considers operational electricity-related emissions only; embodied hardware emissions, "
        "which can be included through amortised Scope 1 and Scope 3 contributions (Elsworth et al., 2025), and the choice "
        "between location-based and market-based emission factors should be addressed in future work.",

    # ---- conclusion
    "The second stage, the hybrid deterministic":
        "The second stage, the hybrid deterministic-batch approach, brings reported emissions closer to operational reality "
        "by treating high-variance, well-observed components deterministically and reserving batch allocation for "
        "low-variance or structurally opaque elements. Simulated results for a representative website indicate that this "
        f"design reduces hourly attribution error by about {red_rel(M2):.0f}% relative to conventional batch accounting, "
        f"and by about {(1 - cov25['m2'] / cov25['batch']) * 100:.0f}% when only a quarter of its deterministic components "
        "are covered by telemetry, performing within one percentage point of full event-level attribution. This enables "
        "higher-fidelity applications such as time-of-use emissions optimisation, carbon-aware workload shifting, and more "
        "robust product-level footprints for digital services, all without demanding universal, high-frequency telemetry "
        "across the entire circuit. Its annual totals, however, remain only as accurate as its calibration.",
    "The final stage full event-level deterministic attribution":
        "The final stage, full event-level deterministic attribution, serves primarily as a directional benchmark, "
        "clarifying the upper bound on attribution fidelity and indicating where expanded transparency (for example in "
        "compute, CDN, and routing data) would most improve accuracy. As infrastructure providers gradually expose richer "
        "energy and emissions signals, elements of this framework can be integrated into operational systems. Overall, the "
        "findings suggest that two challenges must be addressed together: methodological design, which determines temporal "
        "fidelity and boundary completeness, and calibration of energy and emission factors, which determines annual "
        "accuracy. By structuring accounting systems around a resolution ladder and calibrating them against measured data, "
        "policymakers and practitioners can drive continuous improvement in internet emissions reporting while ensuring "
        "that methods remain realistic, auditable, and aligned with decarbonisation goals.",

}

# figure captions appear twice (caption list and under each figure); replace every match
CAPTIONS = {
    "Figure 6 The resulting attribution error variability across workloads.":
        "Figure 6 The resulting attribution error variability across workloads. The grey control spreads the annual totals "
        "of Method 2 evenly over the year and isolates the effect of temporal resolution.",
    "Figure 13 highlights why the hybrid approach captures":
        "Figure 13 Method 2 error as a function of telemetry coverage of its deterministic components; reference lines show "
        "the other methods on the same workloads.",
    "Figure 14 Heatmap of data confidence across components":
        "Figure 14 Heatmap of assumed data confidence across components and signal types, as systematic (per-workload) and "
        "hourly uncertainty of the best available signal.",
    "Figure 9 the largest accuracy gains arise from deterministic":
        "Figure 9 the largest absolute accuracy gains arise from deterministic treatment of compute and",
}

# substring replacements inside a paragraph (keeps the rest of the paragraph as is)
INLINE = {
    "[which develops commercial carbon accounting products related to the methods described in this paper]":
        "which develops commercial carbon accounting products related to the methods described in this paper",
}


def table1_rows():
    rows = []
    for name, m in [("Conventional batch", B), ("Method 1: Operational hybrid", M1),
                    ("Method 2: Hybrid deterministic-batch", M2), ("Method 3: Full event-level", M3)]:
        if m is B:
            rows.append([name, f1(m["mae"]), rng(m), "-", "-", "1.00", "0"])
        else:
            rows.append([name, f1(m["mae"]), rng(m), f1(red_pp(m)), f1(red_rel(m)),
                         f"{B['mae'] / m['mae']:.2f}", f"{gain_share(m):.0f}"])
    return rows


def table2_rows():
    fmt_base = {"network_kwh_per_gb": "0.006", "grid_diurnal_amp": "±25%", "traffic_peak_to_mean": "2.0",
                "idle_share": "10%", "pue": "1.3", "systematic_scale": "1×", "telemetry_coverage": "100%"}
    fmt_range = {"network_kwh_per_gb": "0.002-0.06", "grid_diurnal_amp": "±10% to ±50%",
                 "traffic_peak_to_mean": "1.5-3.0", "idle_share": "5-20%", "pue": "1.1-1.6",
                 "systematic_scale": "0.5× to 2×", "telemetry_coverage": "25-100%"}
    rows = []
    for row in R["sensitivity"]:
        lo, hi = row["runs"]
        rows.append([row["label"], fmt_base[row["key"]], fmt_range[row["key"]],
                     f"{lo['batch']:.1f} / {hi['batch']:.1f}",
                     f"{lo['m2']:.1f} / {hi['m2']:.1f}", f"{lo['ratio']:.1f} / {hi['ratio']:.1f}"])
    return rows


# ---------------------------------------------------------------- XML helpers
P_RE = re.compile(r"<w:p[ >].*?</w:p>", re.S)


def para_text(p):
    p = p.replace("<w:noBreakHyphen/>", "<w:t>-</w:t>")
    return "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p))


def first_rpr(p):
    m = re.search(r"<w:r>\s*(<w:rPr>.*?</w:rPr>)", p, re.S) or re.search(r"<w:r [^>]*>\s*(<w:rPr>.*?</w:rPr>)", p, re.S)
    rpr = m.group(1) if m else ""
    return re.sub(r"<w:highlight [^>]*/>", "", rpr)


def run(rpr, text):
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def set_para(p, text):
    assert "<m:oMath" not in p and "<w:drawing" not in p, "refusing to rewrite math/drawing paragraph"
    head = re.match(r"(<w:p[ >].*?</w:pPr>|<w:p(?: [^>]*)?>)", p, re.S).group(1)
    return head + run(first_rpr(p), text) + "</w:p>"


def new_para(template_p, text):
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", template_p, re.S).group(0)
    return f"<w:p>{ppr}{run(first_rpr(template_p), text)}</w:p>"


def unhighlight_run_containing(xml, snippet):
    """Drop the placeholder highlight from the run whose text now holds the filled-in content."""
    for m in re.finditer(r"<w:r(?: [^>]*)?>(?:(?!</w:r>).)*</w:r>", xml, re.S):
        if snippet in m.group(0):
            fixed = re.sub(r"<w:highlight [^>]*/>", "", m.group(0))
            return xml[:m.start()] + fixed + xml[m.end():]
    raise AssertionError(f"run not found for {snippet!r}")


def find_unique(xml, key, exact=False):
    hits = [m for m in P_RE.finditer(xml) if (para_text(m.group(0)).strip() == key if exact else key in para_text(m.group(0)))]
    assert len(hits) == 1, f"{key!r}: {len(hits)} matches"
    return hits[0]


def replace_para(xml, key, text):
    m = find_unique(xml, key)
    return xml[:m.start()] + set_para(m.group(0), text) + xml[m.end():]


def replace_all_paras(xml, key, text):
    hits = [m for m in P_RE.finditer(xml) if key in para_text(m.group(0))]
    assert hits, f"{key!r}: no matches"
    for m in reversed(hits):
        xml = xml[:m.start()] + set_para(m.group(0), text) + xml[m.end():]
    return xml


def insert_after(xml, key, paras, template_key, exact=False):
    tmpl = find_unique(xml, template_key).group(0)
    m = find_unique(xml, key, exact)
    block = "".join(new_para(tmpl, t) for t in paras)
    return xml[:m.end()] + block + xml[m.end():]


def fill_table(xml, index, rows, first_col=0):
    tables = list(re.finditer(r"<w:tbl>.*?</w:tbl>", xml, re.S))
    t = tables[index]
    tbl = t.group(0)
    trs = re.findall(r"<w:tr[ >].*?</w:tr>", tbl, re.S)
    assert len(trs) <= len(rows) + 1, (len(trs), len(rows))
    while len(trs) < len(rows) + 1:          # add rows by cloning the last one
        tbl = tbl.replace(trs[-1], trs[-1] + trs[-1], 1)
        trs.append(trs[-1])
    new_tbl = tbl
    trs_iter = re.findall(r"<w:tr[ >].*?</w:tr>", tbl, re.S)
    assert len(trs_iter) == len(rows) + 1
    out_trs = []
    for tr, vals in zip(trs_iter[1:], rows):
        tcs = re.findall(r"<w:tc>.*?</w:tc>", tr, re.S)
        new_tr = tr
        for tc, val in zip(tcs[first_col:], vals):
            p = P_RE.search(tc).group(0)
            new_tc = tc.replace(p, set_para(p, val), 1)
            new_tr = new_tr.replace(tc, new_tc, 1)
        out_trs.append(new_tr)
    # rebuild row by row so identical cloned rows are filled independently
    head_end = new_tbl.index(trs_iter[1])
    tail_start = new_tbl.rindex(trs_iter[-1]) + len(trs_iter[-1])
    new_tbl = new_tbl[:head_end] + "".join(out_trs) + new_tbl[tail_start:]
    return xml[:t.start()] + new_tbl + xml[t.end():]


# ---------------------------------------------------------------- figures
def swap_figures(root: Path, xml: str) -> str:
    rels_p = root / "word/_rels/document.xml.rels"
    rels = rels_p.read_text(encoding="utf8")
    media = root / "word/media"
    drawings = list(re.finditer(r"<w:drawing>.*?</w:drawing>", xml, re.S))
    assert len(drawings) == 15
    out, pos = [], 0
    for n, d in enumerate(drawings, start=1):
        src = HERE / "figures" / f"fig{n:02d}.png"
        rid = re.search(r'r:embed="([^"]+)"', d.group(0)).group(1)
        old_target = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"', rels).group(1)
        (root / "word" / old_target).unlink(missing_ok=True)
        new_target = f"media/figure{n:02d}.png"
        shutil.copy(src, media / f"figure{n:02d}.png")
        rels = re.sub(rf'(Id="{rid}"[^>]*Target=")[^"]+(")', rf"\g<1>{new_target}\g<2>", rels)
        w, h = Image.open(src).size
        cx = int(FIG_WIDTH_IN * EMU_PER_IN)
        cy = int(cx * h / w)
        dx = re.sub(r'(<wp:extent cx=")\d+(" cy=")\d+(")', rf"\g<1>{cx}\g<2>{cy}\g<3>", d.group(0))
        dx = re.sub(r'(<a:ext cx=")\d+(" cy=")\d+(")', rf"\g<1>{cx}\g<2>{cy}\g<3>", dx)
        out.append(xml[pos:d.start()] + dx)
        pos = d.end()
    out.append(xml[pos:])
    rels_p.write_text(rels, encoding="utf8")
    ct_p = root / "[Content_Types].xml"
    ct = ct_p.read_text(encoding="utf8")
    if 'Extension="png"' not in ct:
        ct = ct.replace("<Types ", "<Types ", 1).replace(
            '<Default Extension="rels"', '<Default Extension="png" ContentType="image/png"/><Default Extension="rels"', 1)
    if not list(media.glob("*.emf")):
        ct = re.sub(r'<Default Extension="emf"[^>]*/>', "", ct)
    ct_p.write_text(ct, encoding="utf8")
    return "".join(out)


def main(root: Path):
    doc_p = root / "word/document.xml"
    xml = doc_p.read_text(encoding="utf8")
    for key, text in REPLACE.items():
        xml = replace_para(xml, key, text)
    for key, text in CAPTIONS.items():
        xml = replace_all_paras(xml, key, text)
    for old, new in INLINE.items():
        assert xml.count(escape(old)) == 1 or xml.count(old) == 1, old
        xml = xml.replace(escape(old), escape(new)).replace(old, escape(new))
        xml = unhighlight_run_containing(xml, escape(new)[:60])
    xml = insert_after(xml, "Data", DATA_PARAS, "This study develops a resolution-based", exact=True)
    xml = insert_after(xml, "Experimental evaluation focuses on comparing Method 2", SETUP_PARAS,
                       "Experimental evaluation focuses on comparing Method 2")
    xml = fill_table(xml, 0, table1_rows())
    xml = fill_table(xml, 1, table2_rows(), first_col=0)
    xml = swap_figures(root, xml)
    doc_p.write_text(xml, encoding="utf8")
    leftovers = [t for t in ["[ ]", "[To be completed", "[Clarify"] if t in xml]
    print("remaining placeholders:", leftovers)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
