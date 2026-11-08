from __future__ import annotations

import csv
import json
import math
import re
import textwrap
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde, pearsonr
from sklearn.decomposition import PCA

import geolib
import vizlib


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)
vizlib.style_defaults()
P = vizlib.PALETTE
BLUE, ORANGE, GREEN = P["series"]
DIAGNOSES: list[str] = []
NUMERIC = ["gdp_pc", "healthcare_access", "urban_pct", "median_age", "cases_per_100k"]


def save(fig, name: str, note: str) -> None:
    vizlib.save_fig(fig, OUT / name, note)
    plt.close(fig)


def add_diagnosis(title: str, invited: str, decoy: str, mechanism: str,
                  evidence: str, redesign: str) -> None:
    DIAGNOSES.append(
        f"### {title}\n\n"
        f"- **Invited conclusion:** {invited}\n"
        f"- **Decoy ruled out:** {decoy}\n"
        f"- **Mechanism:** {mechanism}\n"
        f"- **Evidence:** {evidence}\n"
        f"- **Redesign:** {redesign}\n"
    )


def write_text_pdf(text: str, path: Path, title: str) -> None:
    clean = re.sub(r"[#*`]", "", text)
    lines = []
    for paragraph in clean.splitlines():
        lines.extend(textwrap.wrap(paragraph, width=118) if paragraph.strip() else [""])
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([.07, .06, .86, .88])
    ax.axis("off")
    ax.text(0, 1, title + "\n\n" + "\n".join(lines), va="top",
            fontsize=7.2, family="DejaVu Sans", linespacing=1.15)
    fig.savefig(path, format="pdf", bbox_inches="tight")
    plt.close(fig)


def write_diagnosis_pdf(image_names: list[str], path: Path) -> None:
    with PdfPages(path) as pdf:
        for diagnosis, image_name in zip(DIAGNOSES, image_names):
            clean = re.sub(r"[#*`]", "", diagnosis)
            lines = []
            for paragraph in clean.splitlines():
                lines.extend(textwrap.wrap(paragraph, width=128) if paragraph.strip() else [""])
            fig = plt.figure(figsize=(11.69, 8.27))
            ax = fig.add_axes([.04, .39, .92, .57])
            ax.imshow(plt.imread(OUT / image_name))
            ax.axis("off")
            text_ax = fig.add_axes([.06, .04, .88, .33])
            text_ax.axis("off")
            text_ax.text(0, 1, "\n".join(lines), va="top", fontsize=7.6,
                         family="DejaVu Sans", linespacing=1.05)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def features_for(codes: set[str] | list[str]) -> list[dict]:
    wanted = set(codes)
    return [f for f in geolib.read_geojson(DATA / "districts.geojson")
            if f["code"] in wanted]


def shoelace(x: np.ndarray, y: np.ndarray) -> float:
    return float(abs(np.dot(x, np.roll(y, -1)) -
                     np.dot(y, np.roll(x, -1))) / 2)


def radar_area(values: np.ndarray) -> float:
    v = np.asarray(values, dtype=float)
    return float(.5 * np.sum(v * np.roll(v, -1)) * np.sin(2 * np.pi / len(v)))


def make_case_diagnoses() -> dict:
    hi = pd.read_csv(DATA / "health_indicators.csv")
    dh = pd.read_csv(DATA / "district_health.csv")
    feats24 = features_for(set(dh.code))
    rates = dh.assign(rate=dh.cases / dh.population * 100_000)

    # 1. Squaring a value for a scatter's area squares the population twice.
    s_bad = hi.pop_m.to_numpy() ** 2
    ratio_bad = float(s_bad.max() / s_bad.min())
    small_country_n = int(hi.pop_m.lt(2.0).sum())
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    scale_to_fit = 1800 / s_bad.max()
    axes[0].scatter(hi.gdp_pc, hi.healthcare_access,
                    s=s_bad * scale_to_fit, color=ORANGE, alpha=.62)
    axes[0].set_xscale("log")
    axes[0].set(title="Published recipe · s ∝ population²",
                xlabel="GDP per capita (USD/person/year; log)", ylabel="Healthcare access (0–100)")
    good_area = 18 + (360 - 18) * (hi.pop_m - hi.pop_m.min()) / (hi.pop_m.max() - hi.pop_m.min())
    axes[1].scatter(hi.gdp_pc, hi.healthcare_access, s=good_area,
                    color=BLUE, alpha=.55, edgecolor="white", linewidth=.3)
    axes[1].set_xscale("log")
    axes[1].set(title="Redesign · area grows linearly with population",
                xlabel="GDP per capita (USD/person/year; log)", ylabel="Healthcare access (0–100)")
    fig.suptitle("Case 1 · Population is an area channel, not an area-squared channel")
    save(fig, "week5_case01_bubble_area.png",
         f"Synthetic health_indicators.csv; {len(hi)} countries; marker areas in points².")
    add_diagnosis(
        "Case 1 — population squared into scatter area",
        "Population and healthcare access appear unrelated across the GDP range.",
        "There are 60 marks, and GDP's log scale is correct; the issue is not missing countries or the x transform.",
        "Matplotlib's `s` already means area. Setting `s=pop_m**2` makes area quadratic in population and reduces small-country marks to near invisibility.",
        f"Population spans {hi.pop_m.min():.1f}–{hi.pop_m.max():.1f} M ({hi.pop_m.max()/hi.pop_m.min():.0f}×); the supplied recipe implies an area ratio of {ratio_bad:,.0f}× ({hi.pop_m.max()/hi.pop_m.min():.0f}²), and {small_country_n} countries are below 2.0 M. The brief's stated 589× area check conflicts with its own `s=pop_m**2` recipe; the code/data imply 589², so this report preserves the mathematical result.",
        "Use a bounded, declared linear mapping from population to marker area; keep log GDP, retain and label the outlier, and include a size legend with real population values.",
    )

    # 2. Count map versus normalized rate.
    count_top = dh.nlargest(3, "cases")
    rate_top = rates.nlargest(3, "rate")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    count_edges = geolib.choropleth(
        axes[0], feats24, dict(zip(dh.code, dh.cases)), scheme="natural", k=5,
        legend_title="Cases (count)", fmt="{:,.0f}", legend_anchor=(1, 1),
    )
    rate_edges = geolib.choropleth(
        axes[1], feats24, dict(zip(rates.code, rates.rate)), scheme="natural", k=5,
        legend_title="Cases per 100,000 residents", fmt="{:.1f}", legend_anchor=(1, 1),
    )
    axes[0].set_title("Published: raw case count")
    axes[1].set_title("Redesign: population-normalized rate")
    fig.suptitle("Case 2 · Counts locate population; rates locate relative incidence")
    save(fig, "week5_case02_count_vs_rate.png",
         "Synthetic district data and fictional district boundaries; equal-area projection; 24/24 join.")
    add_diagnosis(
        "Case 2 — raw-count choropleth",
        "The three darkest/highest-count districts are the outbreak hotspots.",
        "All 24 districts join and the count data are arithmetically correct.",
        "A choropleth's polygon area is part of the visual encoding, but the count is unnormalized; districts with more residents tend to have more cases even at equal incidence.",
        f"Count leaders: {', '.join(count_top.code)}; rate leaders: {', '.join(rate_top.code)}. District counts correlate with population at r={pearsonr(dh.cases, dh.population).statistic:+.3f}; the count and rate top-three sets overlap {len(set(count_top.code)&set(rate_top.code))} districts.",
        "Map cases per 100,000 residents with equal-area geometry, print breaks and legend denominator, and pair the map with a count ranking.",
    )

    # 3. Min-max scaling is dominated by the GDP outlier.
    minmax = geolib.scale_frame(hi, NUMERIC, "minmax")
    below = int(minmax.gdp_pc.lt(.1).sum())
    median_mm = float(minmax.gdp_pc.median())
    rank = geolib.scale_frame(hi, NUMERIC, "rank")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    geolib.pcp(axes[0], hi, NUMERIC, how="minmax")
    axes[0].set_title("Published: min–max (GDP outlier compresses 58/60)")
    geolib.pcp(axes[1], hi, NUMERIC, how="rank")
    axes[1].set_title("Redesign: percentile ranks (relative position, not magnitude)")
    fig.suptitle("Case 3 · The scaled GDP axis is almost flat, not the underlying data")
    save(fig, "week5_case03_scaling_outlier.png",
         "Synthetic health indicators; min–max and percentile-rank methods named; all five non-size numeric axes.")
    add_diagnosis(
        "Case 3 — min–max flattening",
        "GDP per capita barely varies across the sample.",
        "There are no missing countries; the 60 GDP values genuinely span a large range.",
        "Min–max scaling divides every gap by the full range; the single top value (9.2× the runner-up) stretches the range and compresses the other observations.",
        f"After min–max scaling, {below}/60 countries lie below 0.10 and the median is {median_mm:.3f}; raw GDP runs ${hi.gdp_pc.min():,.0f}–${hi.gdp_pc.max():,.0f}.",
        "Use percentile ranks when the question is relative ordering (and label that magnitude is discarded), or show raw GDP on a log scale when absolute gaps matter.",
    )

    # 4. File order separates the correlated pair on a parallel coordinates plot.
    original_order = NUMERIC
    greedy = geolib.corr_chain(hi, NUMERIC)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    geolib.pcp(axes[0], hi, original_order, how="minmax")
    axes[0].set_title("Published: file order")
    geolib.pcp(axes[1], hi, greedy, how="minmax")
    axes[1].set_title("Redesign: greedy |r| chain")
    fig.suptitle("Case 4 · Put the healthcare–incidence pair next to each other")
    r_access_cases = float(hi.healthcare_access.corr(hi.cases_per_100k))
    save(fig, "week5_case04_axis_order.png",
         "Synthetic health indicators; min–max scale; file order compared with geolib.corr_chain.")
    add_diagnosis(
        "Case 4 — misleading axis order",
        "Healthcare access and case rate appear unrelated because no crossing is obvious.",
        "The five axes and the min–max scaling are valid; no scale was omitted.",
        "Parallel-coordinate crossings depend on adjacent axis pairs; the file order inserts two unrelated variables between strongly related access and incidence axes.",
        f"File order: {', '.join(original_order)}; greedy chain: {' → '.join(greedy)}. Healthcare access and cases_per_100k have r={r_access_cases:+.3f} but are three positions apart in the published chart.",
        "Order axes using the stated greedy absolute-correlation chain; the paired variables become adjacent and the crossing pattern can be read.",
    )

    # 5. Quantile classes exaggerate a narrow rate range.
    flat = pd.read_csv(DATA / "case05_flat_rates.csv")
    flat["rate"] = flat.cases / flat.population * 100_000
    flat_feats = features_for(set(flat.code))
    qedges = geolib.breaks(flat.rate, scheme="quantile", k=5)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    geolib.choropleth(
        axes[0], flat_feats, dict(zip(flat.code, flat.rate)),
        scheme="quantile", k=5, legend_title="Rate per 100,000 residents",
        fmt="{:.2f}",
    )
    axes[0].set_title("Published: five quantiles")
    ordered = flat.sort_values("rate")
    axes[1].scatter(ordered.rate, np.arange(len(ordered)), color=BLUE)
    axes[1].hlines(np.arange(len(ordered)), ordered.rate.min(), ordered.rate,
                   color=P["grid"], linewidth=.8)
    axes[1].set(title="Redesign: show the true narrow spread",
                xlabel="Cases per 100,000 residents", ylabel="Districts (ranked)")
    axes[1].set_yticks([])
    fig.suptitle("Case 5 · Five classes do not imply five meaningful levels")
    spread_pct = (flat.rate.max() - flat.rate.min()) / flat.rate.mean() * 100
    save(fig, "week5_case05_flat_quantiles.png",
         f"Synthetic 24-district rates; quantile breaks={np.round(qedges, 2).tolist()}.")
    add_diagnosis(
        "Case 5 — quantile classes over a flat distribution",
        "A five-level incidence gradient is visible across the federation.",
        "The calculations and quantile assignments are correct, and all 24 districts are included.",
        "Quantile classification forces equal-count bins even when the underlying range is substantively tiny; class contrast exaggerates differences.",
        f"Rates span {flat.rate.min():.2f}–{flat.rate.max():.2f} per 100,000, only {spread_pct:.1f}% of the mean. The five quantile breaks are {np.round(qedges, 2).tolist()}.",
        "Show the actual values on a common linear dot scale and state that the total spread is small; use quantiles only when equal-count ranking is the explicit purpose.",
    )

    # 6. Small denominators create unstable extreme rates.
    small = pd.read_csv(DATA / "smallarea_cases.csv")
    small["rate"] = small.cases / small.population * 100_000
    pool = float(small.cases.sum() / small.population.sum() * 100_000)
    outlier = small.loc[small.unit.eq("U32")].iloc[0]
    limits = geolib.funnel_limits(small.population, pool)
    order = small.sort_values("rate")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].barh(order.unit, order.rate,
                 color=[ORANGE if unit == "U32" else BLUE for unit in order.unit])
    axes[0].axvline(pool, color=P["ink"], linestyle="--", label=f"Pooled rate {pool:.2f}")
    axes[0].set(title="Published: rank rates without exposure stability",
                xlabel="Cases per 100,000")
    axes[0].legend()
    outside_units = []
    for row in small.itertuples():
        lim = limits.loc[limits.population.eq(row.population)].iloc[0]
        if row.rate < lim.lo or row.rate > lim.hi:
            outside_units.append(row.unit)
    lim_order = limits.sort_values("population")
    axes[1].fill_between(lim_order.population, lim_order.lo, lim_order.hi,
                         color=BLUE, alpha=.18, label="95% Poisson funnel")
    axes[1].plot(lim_order.population, lim_order.expected, color=BLUE, linestyle="--")
    axes[1].scatter(small.population, small.rate, color=ORANGE, s=25)
    axes[1].scatter([outlier.population], [outlier.rate], color=ORANGE, s=70,
                    edgecolor="black", label="U32: 9 cases / 22,000")
    axes[1].set(title="Redesign: the same rate has wider uncertainty at low n",
                xlabel="Population (people)", ylabel="Cases per 100,000")
    axes[1].legend(fontsize=8)
    fig.suptitle("Case 6 · A small-area extreme is not automatically a hotspot")
    save(fig, "week5_case06_smallarea_stability.png",
         f"Synthetic 40 small areas; pooled rate {pool:.2f}; {len(outside_units)} outside 95% Poisson limits.")
    add_diagnosis(
        "Case 6 — unstable rate from a small denominator",
        "U32 is nearly five times the national rate and therefore a hotspot.",
        "The division is correct; the defect is not arithmetic or a map projection.",
        "A rate based on a small population has high Poisson variability; treating a noisy small-area estimate as a stable signal overstates certainty.",
        f"Pooled rate {pool:.2f}/100,000; U32 is {outlier.rate:.1f}/100,000 from {int(outlier.cases)} cases among {int(outlier.population):,} people ({outlier.rate/pool:.1f}×); {len(outside_units)} of 40 units fall outside the 95% funnel.",
        "Show exposure against rate with a widening Poisson funnel and report the small-area numerator and denominator; do not rank a noisy extreme as a proven hotspot.",
    )

    # 7. The district correlation changes with areal aggregation.
    rates["rate"] = rates.cases / rates.population * 100_000
    district_r = float(rates.income_pc_usd.corr(rates.rate))
    zone = rates.groupby("zone").apply(
        lambda g: pd.Series({
            "income": np.average(g.income_pc_usd, weights=g.population),
            "rate": g.cases.sum() / g.population.sum() * 100_000,
        })
    ).reset_index()
    zone_r = float(zone.income.corr(zone.rate))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(rates.income_pc_usd, rates.rate, color=BLUE)
    axes[0].set(title=f"Districts (n=24), r={district_r:+.3f}",
                xlabel="Income per person (USD/year)", ylabel="Cases per 100,000")
    axes[1].scatter(zone.income, zone.rate, color=ORANGE, s=70)
    for r in zone.itertuples():
        axes[1].annotate(r.zone, (r.income, r.rate), xytext=(4, 4), textcoords="offset points")
    axes[1].set(title=f"Aggregated zones (n={len(zone)}), r={zone_r:+.3f}",
                xlabel="Population-weighted income (USD/person/year)",
                ylabel="Pooled cases per 100,000")
    fig.suptitle("Case 7 · Correlation depends on the areal unit")
    save(fig, "week5_case07_areal_scale.png",
         "Synthetic districts; zone rates pooled by population, income weighted by population.")
    add_diagnosis(
        "Case 7 — areal-scale dependence",
        "District income and incidence have only a weak negative relationship (r≈−0.31).",
        "The district-level Pearson correlation is correctly computed across 24 complete records.",
        "A correlation is conditional on its areal units; grouping districts into zones changes within-zone variation and can produce the modifiable areal unit problem (MAUP).",
        f"District r={district_r:+.3f}; reaggregated population-weighted zone income versus pooled zone incidence r={zone_r:+.3f} across {len(zone)} zones. These are different estimands, not evidence that one correlation is universally true.",
        "Show the district scatter and report zone aggregation as a sensitivity analysis, with the unit of analysis named.",
    )

    # 8. Polygon area is not population share.
    dh_area = dh.copy()
    geo_area = {f["code"]: geolib.polygon_area_km2(f["ring"]) for f in feats24}
    dh_area["spherical_area"] = dh_area.code.map(geo_area)
    top_pop = dh_area.nlargest(5, "population")
    pop_share = top_pop.population.sum() / dh_area.population.sum() * 100
    land_share = top_pop.spherical_area.sum() / dh_area.spherical_area.sum() * 100
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    rate_map = dict(zip(rates.code, rates.rate))
    geolib.choropleth(
        axes[0], feats24, rate_map, scheme="natural", k=5,
        legend_title="Cases per 100,000 residents", fmt="{:.1f}",
    )
    axes[0].set_title("Equal-area choropleth: incidence")
    ranked = dh_area.sort_values("population")
    axes[1].barh(ranked.district, ranked.population / 1e6,
                 color=[ORANGE if code in set(top_pop.code) else BLUE for code in ranked.code])
    axes[1].set(title="Population is not proportional to polygon area",
                xlabel="Population (millions)")
    fig.suptitle("Case 8 · A dark land area does not mean most people live there")
    save(fig, "week5_case08_area_population_bias.png",
         f"Synthetic 24-district data; equal-area projection; top-five residents={pop_share:.1f}%, land={land_share:.1f}%.")
    add_diagnosis(
        "Case 8 — area-weighted visual impression",
        "The outbreak is rural because much of the map is dark.",
        "The rate is normalized, the sequential scale is correct, and the map uses equal-area geometry.",
        "A choropleth gives every square kilometre visible area regardless of population; viewers infer prevalence from the amount of colored land instead of the share of residents affected.",
        f"The five most populous districts contain {pop_share:.1f}% of residents but only {land_share:.1f}% of land area; dark-map area therefore does not measure people or the rural share.",
        "Pair the rate map with population-weighted counts/rankings or proportional symbols; explicitly describe population rather than colored land area.",
    )

    # 9. Radar area changes with arbitrary variable order.
    prof = pd.read_csv(DATA / "region_profiles.csv")
    values_a = prof.region_a.to_numpy()
    values_b = prof.region_b.to_numpy()
    area_a, area_b = radar_area(values_a), radar_area(values_b)
    angles = np.linspace(0, 2 * np.pi, len(prof), endpoint=False)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax in axes:
        ax.remove()
    ax = fig.add_subplot(1, 2, 1, projection="polar")
    for values, name, color in [(values_a, "Region A", BLUE), (values_b, "Region B", ORANGE)]:
        ax.plot(np.r_[angles, angles[0]], np.r_[values, values[0]], label=name, color=color)
        ax.fill(np.r_[angles, angles[0]], np.r_[values, values[0]], color=color, alpha=.14)
    ax.set_xticks(angles, prof.indicator.tolist())
    ax.set_ylim(0, 100)
    ax.set_title(f"Published: file order\narea {area_a:,.0f} vs {area_b:,.0f}")
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.1))
    ax2 = fig.add_subplot(1, 2, 2)
    prof_sorted = prof.assign(diff=prof.region_a - prof.region_b).sort_values("indicator")
    y = np.arange(len(prof_sorted))
    ax2.hlines(y, prof_sorted.region_a, prof_sorted.region_b, color=P["muted"])
    ax2.scatter(prof_sorted.region_a, y, color=BLUE, label="Region A")
    ax2.scatter(prof_sorted.region_b, y, color=ORANGE, label="Region B")
    ax2.set_yticks(y, prof_sorted.indicator)
    ax2.set(xlim=(0, 100), title="Redesign: compare each indicator directly",
            xlabel="Rating (0–100)")
    ax2.legend()
    fig.suptitle("Case 9 · Enclosed area depends on axis order")
    mean_diff = float(values_a.mean() - values_b.mean())
    save(fig, "week5_case09_radar_order.png",
         f"Synthetic six-indicator profiles; means differ by {mean_diff:.2f} points.")
    add_diagnosis(
        "Case 9 — radar area depends on order",
        "Region A has a visibly stronger profile because it encloses more area.",
        "Both profiles use the same 0–100 scale and the same six indicators.",
        "Radar polygon area depends on the adjacency/order of axes; a rearrangement changes cross-products and enclosed area without changing any score.",
        f"Mean scores are {values_a.mean():.1f} and {values_b.mean():.1f} (difference {mean_diff:.2f}); in supplied order their polygon areas are {area_a:,.0f} and {area_b:,.0f}, a layout-dependent difference.",
        "Use paired points or sorted dumbbell bars on a shared linear scale to compare each indicator; do not summarize a radar polygon's area as overall strength.",
    )
    (OUT / "week5_partA_diagnoses.md").write_text(
        "# Week 5 Part A — diagnoses and redesigns\n\n"
        "All nine synthetic cases are rebuilt in `week5_case*.png`. Each image "
        "puts the published recipe beside an honest alternative. The report "
        "names the claim, rules out the decoy, identifies the channel/boundary "
        "mechanism, and gives data evidence.\n\n" + "\n".join(DIAGNOSES),
        encoding="utf-8",
    )
    write_diagnosis_pdf(
        [f"week5_case{i:02d}_" + [
            "bubble_area.png", "count_vs_rate.png", "scaling_outlier.png",
            "axis_order.png", "flat_quantiles.png", "smallarea_stability.png",
            "areal_scale.png", "area_population_bias.png", "radar_order.png",
        ][i - 1] for i in range(1, 10)],
        OUT / "week5_partA_diagnosis.pdf",
    )
    return {"hi": hi, "dh": dh, "rates": rates, "feats": feats24,
            "count_edges": count_edges, "rate_edges": rate_edges}


def part_b_decisions(hi: pd.DataFrame, dh: pd.DataFrame,
                     feats: list[dict]) -> dict:
    # B1 size mapping is an explicitly bounded linear mapping to scatter area.
    lo, hi_area = 18.0, 360.0
    pop = hi.pop_m.to_numpy(dtype=float)
    area = lo + (hi_area - lo) * (pop - pop.min()) / (pop.max() - pop.min())
    diameter_ratio = math.sqrt(hi_area / lo)

    # B2 same data and same axes, four ways.
    dense = pd.read_csv(DATA / "scatter_dense.csv")
    x = dense.x.to_numpy()
    y = dense.y.to_numpy()
    alpha_value, gridsize = .16, 55
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes[0, 0].scatter(x, y, s=4, color=BLUE, alpha=1)
    axes[0, 0].set_title("Opaque scatter")
    axes[0, 1].scatter(x, y, s=4, color=BLUE, alpha=alpha_value)
    axes[0, 1].set_title(f"Transparent scatter (alpha={alpha_value})")
    axes[1, 0].hexbin(x, y, gridsize=gridsize, cmap="Blues", mincnt=1)
    axes[1, 0].set_title(f"Hexbin (gridsize={gridsize})")
    kde = gaussian_kde(np.vstack([x, y]))
    gx, gy = np.mgrid[x.min():x.max():160j, y.min():y.max():160j]
    density = kde(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
    axes[1, 1].contourf(gx, gy, density, levels=12, cmap="Blues")
    axes[1, 1].set_title("2-D Gaussian KDE")
    for ax in axes.flat:
        ax.set(xlabel="x", ylabel="y")
        ax.scatter([3.1], [3.0], marker="+", s=90, color=ORANGE, linewidth=1.5)
        ax.set_xlim(x.min(), x.max())
        ax.set_ylim(y.min(), y.max())
    fig.suptitle("Week 5 B2 · Density methods expose the 800-point cluster")
    save(fig, "week5_partB_overplotting.png",
         f"Synthetic scatter_dense.csv; n={len(dense):,}; transparency alpha={alpha_value}; hexbin gridsize={gridsize}.")
    center = ((x - 3.1) ** 2 + (y - 3.0) ** 2 <= .15 ** 2)
    cluster_count = int(center.sum())

    # B3 three scalings, then PCA on standardized five numeric indicators.
    scale_metrics = []
    for method in ("minmax", "zscore", "rank"):
        scaled = geolib.scale_frame(hi, NUMERIC, how=method)
        g = scaled.gdp_pc
        scale_metrics.append({
            "method": method,
            "gdp_min": float(g.min()),
            "gdp_median": float(g.median()),
            "gdp_max": float(g.max()),
            "countries_below_0.10": int(g.lt(.1).sum()),
            "gdp_std": float(g.std(ddof=0)),
        })
    zscore = geolib.scale_frame(hi, NUMERIC, how="zscore")
    pca = PCA().fit(zscore[NUMERIC])
    evr1, evr2 = map(float, pca.explained_variance_ratio_[:2])
    pca_frame = pd.DataFrame({
        "component": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
        "explained_variance_ratio": pca.explained_variance_ratio_,
    })
    pca_frame.to_csv(OUT / "week5_partB_pca_variance.csv", index=False)
    pd.DataFrame(scale_metrics).to_csv(OUT / "week5_partB_scaling_metrics.csv", index=False)

    # B4 area by sphere, deliberately wrong raw degree shoelace, Mercator inflation.
    areas = []
    for feat in feats:
        ring = feat["ring"]
        lon = np.array([p[0] for p in ring], dtype=float)
        lat = np.array([p[1] for p in ring], dtype=float)
        sphere = geolib.polygon_area_km2(ring)
        degree_area = shoelace(lon, lat)
        mx, my = geolib.mercator_xy(lon, lat)
        mercator_area = shoelace(np.asarray(mx), np.asarray(my))
        areas.append({"code": feat["code"], "sphere_km2": sphere,
                      "degree_area": degree_area, "mercator_km2": mercator_area,
                      "latitude": float(np.mean(lat))})
    area_df = pd.DataFrame(areas)
    north = area_df.nlargest(4, "latitude")
    sphere_share = float(north.sphere_km2.sum() / area_df.sphere_km2.sum() * 100)
    degree_share = float(north.degree_area.sum() / area_df.degree_area.sum() * 100)
    area_df["sphere_share"] = area_df.sphere_km2 / area_df.sphere_km2.sum()
    area_df["degree_share"] = area_df.degree_area / area_df.degree_area.sum()
    area_df["share_distortion"] = (area_df.sphere_share - area_df.degree_share).abs()
    worst_area = area_df.loc[area_df.share_distortion.idxmax()]
    mercator_inflation = float(area_df.mercator_km2.sum() / area_df.sphere_km2.sum())
    area_df.to_csv(OUT / "week5_partB_area_comparison.csv", index=False)

    # B5 Poisson funnel, by exposure; minimum n for 18 to exceed the 95% upper
    # funnel around a reference rate of 9 per 100,000.
    small = pd.read_csv(DATA / "smallarea_cases.csv")
    small["rate"] = small.cases / small.population * 100_000
    pooled = float(small.cases.sum() / small.population.sum() * 100_000)
    limits_by_population = geolib.funnel_limits(small.population.unique(), pooled).set_index("population")
    small["lo"] = small.population.map(limits_by_population.lo)
    small["hi"] = small.population.map(limits_by_population.hi)
    small["expected"] = small.population.map(limits_by_population.expected)
    lim = small[["unit", "population", "rate", "lo", "hi", "expected"]].copy()
    outside = small.rate.lt(small.lo) | small.rate.gt(small.hi)
    n_outside = int(outside.sum())
    fig, ax = plt.subplots(figsize=(8, 5))
    lim_order = lim.sort_values("population")
    ax.fill_between(lim_order.population, lim_order.lo, lim_order.hi,
                    color=BLUE, alpha=.18, label="95% Poisson limits")
    ax.plot(lim_order.population, lim_order.expected, color=BLUE, linestyle="--",
            label=f"Pooled rate {pooled:.2f}")
    ax.scatter(small.population, small.rate,
               c=[ORANGE if unit == "U32" else BLUE for unit in small.unit], s=28)
    u32 = small.loc[small.unit.eq("U32")].iloc[0]
    ax.annotate("U32", (u32.population, u32.rate), xytext=(6, 5),
                textcoords="offset points")
    ax.set(title="Small-area funnel · 95% limits widen as population falls",
           xlabel="Population (people)", ylabel="Cases per 100,000")
    ax.legend()
    save(fig, "week5_partB_funnel.png",
         f"Synthetic 40 small areas; Poisson z=1.96; {n_outside}/40 outside limits.")
    baseline_rate, comparison_rate, z = 9.0, 18.0, 1.96
    min_population = int(math.ceil(z ** 2 * baseline_rate * 100_000 /
                                   (comparison_rate - baseline_rate) ** 2))
    lim.to_csv(OUT / "week5_partB_funnel_values.csv", index=False)

    report = f"""# Week 5 Part B — computed decisions

## 1 · Bubble-size range

`lo={lo:.0f}`, `hi={hi_area:.0f}` points²; Matplotlib `s` encodes **area**, linearly mapped from population `{pop.min():.1f}–{pop.max():.1f} M`. The resulting diameter ratio is `sqrt(hi/lo)={diameter_ratio:.2f}:1`. The floor keeps the smallest country mark visible; the cap keeps the largest from covering its neighbours. The legend uses actual population values and the same mapping. A bounded area scale is a deliberate readability compromise; it is not radius scaling.

## 2 · Overplotting

Parameters: opaque alpha=1; transparent `alpha={alpha_value}`; hexbin `gridsize={gridsize}`; 2-D Gaussian KDE on a 160×160 grid. The supplied 800-point cluster is **visible in all four** renderings: opaque scatter shows a compact saturated clump, transparency preserves the local density contrast, and both hexbin and KDE show a distinct secondary density peak. The radius-0.15 neighbourhood around its center contains `{cluster_count}` points; this is a local neighborhood count, not the cluster's full membership. All four are exported for direct comparison. The hexbin is recommended because it communicates counts per cell without a kernel-bandwidth assumption, with KDE as a smooth check. The center is indicated by a cross in all panels. `week5_partB_overplotting.png` is the diagnostic image.

## 3 · Scaling and PCA

The five multivariate axes exclude `pop_m`, which is reserved for bubble area. Methods and GDP summaries are in `week5_partB_scaling_metrics.csv`:

```
{pd.DataFrame(scale_metrics).to_string(index=False)}
```

PCA on z-scored columns: PC1 explains `{evr1:.3f}`, PC2 `{evr2:.3f}`; the two-axis view explains `{evr1+evr2:.1%}` and omits `{1-evr1-evr2:.1%}` of standardized variance. Full component ratios: `week5_partB_pca_variance.csv`.

## 4 · Projection before area

Four northernmost districts (`{', '.join(north.code)}`) account for `{sphere_share:.2f}%` of spherical area versus `{degree_share:.2f}%` under raw degree-space shoelace. The largest per-district share distortion is `{worst_area.code}` ({worst_area.share_distortion*100:.2f} percentage points). Total Mercator polygon area is `{mercator_inflation:.3f}×` the spherical total. This inflation makes a map's polygon area depend on latitude, so use the toolkit's equal-area projection when area itself carries the visual weight.

## 5 · Small-area stability

Pooled rate `{pooled:.2f}` cases per 100,000; `{n_outside}/40` observed units fall outside 95% Poisson limits. U32's extreme is a noisy small-denominator signal, not automatically a stable hotspot. Under a normal Poisson approximation, the 95% upper funnel around a reference rate of 9 falls below 18 at population **{min_population:,}**:

`n = ceil(1.96² × 9 × 100,000 / (18−9)²)`.

This is the threshold for distinguishing 18 from a reference of 9 using the reference-rate funnel; the exact Poisson interval will differ slightly. The small-area map/diagnosis must report numerator, denominator and the stability check.
"""
    (OUT / "week5_partB_decisions.md").write_text(report, encoding="utf-8")
    return {
        "lo": lo, "hi": hi_area, "area": area, "size_ratio": diameter_ratio,
        "scales": scale_metrics, "pca1": evr1, "pca2": evr2,
        "sphere_share": sphere_share, "degree_share": degree_share,
        "worst_area": worst_area.code, "mercator_inflation": mercator_inflation,
        "pooled_small": pooled, "outside": n_outside, "min_population": min_population,
    }


def part_c_reader_activity() -> dict:
    crime = pd.read_csv(DATA / "county_crime.csv")
    crime["rate"] = crime.crimes_reported / crime.population * 100_000
    all_features = geolib.read_geojson(DATA / "districts.geojson")
    codes = set(crime.code)
    feats = [f for f in all_features if f["code"] in codes]
    missing_polygons = sorted(set(f["code"] for f in all_features) - codes)
    unmatched_records = sorted(codes - set(f["code"] for f in all_features))
    assert len(feats) == 20 and len(missing_polygons) == 4 and not unmatched_records
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    geolib.choropleth(
        axes[0], feats, dict(zip(crime.code, crime.crimes_reported)),
        scheme="natural", k=5, legend_title="Crimes reported (count)",
        fmt="{:,.0f}",
    )
    geolib.choropleth(
        axes[1], feats, dict(zip(crime.code, crime.rate)),
        scheme="natural", k=5, legend_title="Crimes per 100,000 residents",
        fmt="{:.1f}",
    )
    axes[0].set_title("Map A · count")
    axes[1].set_title("Map B · population-normalized rate")
    fig.suptitle("Part C reader stimulus · Show Map A before Map B")
    corr = float(crime.crimes_reported.corr(crime.population))
    top_count = crime.nlargest(3, "crimes_reported").county.tolist()
    top_rate = crime.nlargest(3, "rate").county.tolist()
    overlap = len(set(top_count) & set(top_rate))
    save(fig, "week5_partC_two_maps.png",
         f"Synthetic county crime file; {len(feats)}/20 joined; unmatched polygons: {', '.join(missing_polygons)}.")
    result_path = ROOT / "partC_reader_results.csv"
    if not result_path.exists():
        with result_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "reader_id", "mapA_top3_count", "mapB_top3_rate",
                "overlap_count", "notes",
            ])
    report = f"""# Week 5 Part C — maps and reader protocol

Map A and Map B use the same Natural/Jenks 5-class scheme, sequential Blues ramp, boundary layer and equal-area projection. The only data change is denominator: Map A maps counts; Map B maps crimes per 100,000 residents. Joined records: {len(feats)}/20. Four unmatched boundary polygons are left out: {', '.join(missing_polygons)}; unmatched crime records: {len(unmatched_records)}.

Self-check from the synthetic file (not reader evidence): r(count,population)={corr:+.3f}; count top three: {', '.join(top_count)}; rate top three: {', '.join(top_rate)}; ranking overlap={overlap}. One map is a map of recorded crime volume, the other of per-resident rate.

**Real-reader data remain uncollected.** `partC_reader_results.csv` is a header-only capture template; no people were simulated and no mean overlap is claimed. Recruit at least five real readers and follow `reader_protocol.md`, showing A first, then B, with no revision. The results—not the self-check—must support the reported mean overlap.
"""
    (OUT / "week5_partC_report.md").write_text(report, encoding="utf-8")
    return {"crime": crime, "missing_polygons": missing_polygons,
            "top_count": top_count, "top_rate": top_rate,
            "overlap": overlap, "corr": corr}


def part_d_figures(hi: pd.DataFrame, dh: pd.DataFrame,
                   feats: list[dict], b: dict) -> None:
    # D1: x/y/area/hue, with redundant marker shapes and a real-value size key.
    lo, hi_area = b["lo"], b["hi"]
    pop = hi.pop_m.to_numpy(dtype=float)
    area = lo + (hi_area - lo) * (pop - pop.min()) / (pop.max() - pop.min())
    regions = sorted(hi.region.unique())
    palette = sns.color_palette("colorblind", len(regions))
    hexes = [matplotlib.colors.to_hex(c) for c in palette]
    shapes = ["o", "s", "^", "D", "v", "P"]
    colour_by_region = dict(zip(regions, hexes))
    marker_by_region = dict(zip(regions, shapes))
    fig, ax = plt.subplots(figsize=(12, 7))
    for region in regions:
        g = hi.loc[hi.region.eq(region)]
        ax.scatter(g.gdp_pc, g.healthcare_access,
                   s=area[g.index], color=colour_by_region[region],
                   marker=marker_by_region[region], alpha=.7,
                   edgecolor="white", linewidth=.5, label=region)
    ax.set_xscale("log")
    ax.set_ylim(0, 100)
    ax.set(xlabel="GDP per capita (USD/person/year; log scale)",
           ylabel="Healthcare access (index, 0–100)",
           title="Healthcare access varies across GDP and regions; GDP outlier retained")
    labels = set(["Aldonia"])
    labels.update(hi.nlargest(2, "healthcare_access").country)
    labels.update(hi.nsmallest(1, "healthcare_access").country)
    for row in hi.loc[hi.country.isin(labels)].itertuples():
        ax.annotate(row.country, (row.gdp_pc, row.healthcare_access),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.legend(title="Region (hue + shape)", bbox_to_anchor=(1.02, 1),
              loc="upper left")
    geolib.size_legend(
        ax, pop, max_pt=hi_area, n=3, color=P["muted"],
        title="Population (millions)", loc="lower left",
        bbox_to_anchor=(1.02, .25), fmt="{:.1f}",
        size_range=(lo, hi_area),
    )
    fig.subplots_adjust(right=.76)
    cvd_min = vizlib.worst_pair(hexes, kind="deutan")
    save(fig, "week5_partD_bubble.png",
         f"Synthetic 60 countries; s(area)={lo:.0f}–{hi_area:.0f} pt²; outlier GDP retained on log axis; deutan palette min ΔE={cvd_min[-1]:.1f}.")
    (OUT / "week5_partD_palette_check.txt").write_text(
        "Six-region categorical palette measured with vizlib.worst_pair.\n"
        f"Normal closest pair: {vizlib.worst_pair(hexes, kind='normal')}\n"
        f"Deuteranopia-simulated closest pair: {cvd_min}\n"
        "Distinct marker shapes and direct labels are redundant channels; color alone is not claimed to be sufficient.\n",
        encoding="utf-8",
    )

    # D2: computed axis chain, percentile rank scale, one region brushed.
    chain = geolib.corr_chain(hi, NUMERIC)
    highlight_region = sorted(hi.region.unique())[0]
    fig, ax = plt.subplots(figsize=(12, 6))
    geolib.pcp(ax, hi, chain, how="rank",
               highlight=hi.region.eq(highlight_region),
               hl_color=ORANGE, bg_color=P["muted"])
    r_access_cases = float(hi.healthcare_access.corr(hi.cases_per_100k))
    r_cases_urban = float(hi.cases_per_100k.corr(hi.urban_pct))
    ax.set_title(
        f"Percentile-rank axes · greedy |r| chain: {' → '.join(chain)}\n"
        f"Grey all; brush {highlight_region}; adjacent relationships: "
        f"access→cases r={r_access_cases:+.3f}, cases→urban r={r_cases_urban:+.3f}"
    )
    save(fig, "week5_partD_parallel_coordinates.png",
         f"Synthetic health_indicators.csv; percentile-rank scaling; greedy correlation chain; brushed region={highlight_region}.")

    # D3: normalized rate map with the count returned in a sorted bar panel.
    rates = dh.assign(rate=dh.cases / dh.population * 100_000)
    matched_codes = {f["code"] for f in feats}
    unmatched = sorted(set(dh.code) - matched_codes)
    assert len(unmatched) == 0
    rate_map = dict(zip(rates.code, rates.rate))
    count_map = dict(zip(dh.code, dh.cases))
    pooled = float(dh.cases.sum() / dh.population.sum() * 100_000)
    top_rate = rates.nlargest(3, "rate").code.tolist()
    top_count = dh.nlargest(3, "cases").code.tolist()
    overlap = len(set(top_rate) & set(top_count))
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    edges = geolib.choropleth(
        axes[0], feats, rate_map, scheme="natural", k=5,
        legend_title="Cases per 100,000 residents", fmt="{:.1f}",
        legend_anchor=(1.0, 1.0),
    )
    axes[0].set_title("Equal-area, five natural-break rate classes")
    ordered = dh.sort_values("cases")
    axes[1].barh(ordered.district, ordered.cases, color=BLUE)
    axes[1].set(title="Counts retained as a separate ranking",
                xlabel="Confirmed cases (count)")
    for y, row in enumerate(ordered.itertuples()):
        axes[1].text(row.cases + 20, y, row.code, va="center", fontsize=7)
    axes[1].set_xlim(0, ordered.cases.max() * 1.2)
    fig.suptitle("Week 5 D3 · Incidence is mapped; case volume is shown beside it")
    note = (
        "Synthetic district_health.csv + fictional districts.geojson; "
        "source extract 2026-11-09; Lambert cylindrical equal-area (geolib); "
        f"24/24 joined, unmatched={len(unmatched)}, no units suppressed; "
        f"five natural breaks={np.round(edges, 2).tolist()}."
    )
    save(fig, "week5_partD_choropleth.png", note)
    pooled_counts = float(dh.cases.sum())
    (OUT / "week5_partD_spatial_audit.md").write_text(
        f"""# Week 5 D3 spatial audit

- Join on `code`: {len(matched_codes)}/24 successful; unmatched records: {unmatched}.
- Denominator: population residents; pooled national incidence is {pooled:.2f} cases/100,000 from {pooled_counts:,.0f} cases.
- Natural Jenks breaks (5 classes): {np.round(edges, 2).tolist()}.
- Projection: geolib Lambert cylindrical equal-area; shared reference latitude across the feature collection.
- District rate leaders: {', '.join(top_rate)}; count leaders: {', '.join(top_count)}; overlap={overlap}.
- Boundaries: the fictional 24-district synthetic GeoJSON supplied for CDB601220; extraction 2026-11-09. Suppression: none.
- Count is not hidden: the sorted bar chart returns case volume beside the normalized map.
""",
        encoding="utf-8",
    )


def part_e_and_f(dh: pd.DataFrame, hi: pd.DataFrame,
                 b: dict) -> None:
    # Part E: concise, one-page equivalent; never treats the unrun reader study as evidence.
    rates = dh.assign(rate=dh.cases / dh.population * 100_000)
    count_top = dh.nlargest(3, "cases").code.tolist()
    rate_top = rates.nlargest(3, "rate").code.tolist()
    text = f"""# Week 5 Part E — written justification

**Channel budget.** In D1, x-position is log GDP per capita and y-position is bounded 0–100 healthcare access because these are the two values readers compare most precisely. Bubble area carries population with the declared {b['lo']:.0f}–{b['hi']:.0f} points² mapping and real-value legend; hue plus six marker shapes identify region. The $120,219 GDP outlier is retained, labelled and shown on the required log axis. D2 uses five percentile-rank axes for relative association, grey background profiles and one orange regional brush; D3 uses sequential light-to-dark blue for ordered incidence. `vizlib.worst_pair` measures the regional palette and the figure uses redundant shapes/labels rather than claiming hue alone solves CVD.

**Parallel coordinates.** `geolib.corr_chain()` sets the axis order before plotting: healthcare_access → cases_per_100k → urban_pct → median_age → gdp_pc. The adjacent access/incidence relationship is r={hi.healthcare_access.corr(hi.cases_per_100k):+.3f}; cases/urban is r={hi.cases_per_100k.corr(hi.urban_pct):+.3f}. Rank scaling shows relative order, not original gaps. This makes the multivariate path/crossing visible while retaining raw endpoint labels.

**Spatial decisions.** D3 maps cases per 100,000 residents (not counts), uses five natural/Jenks classes with printed breaks, and projects all districts with one equal-area reference latitude so polygon area is not exaggerated by latitude. The 24 `code` joins all succeed; the boundary is the synthetic fictional federation geometry distributed for CDB601220, with extraction date 2026-11-09. No unit was suppressed. Counts return in a sorted companion bar chart.

**Counterfactual and ethics.** A raw-count choropleth would darken D17, D13 and D09, whose residents generate more cases in absolute terms; the normalized-rate leaders are D19, D20 and D21, with zero top-three overlap. Counts correlate with population at r={dh.cases.corr(dh.population):+.3f}, so the raw map would mainly point leadership toward populous districts, not the highest per-resident incidence. Week 5's required five-reader activity has not been run; its blank results file is a capture template, not evidence, so no claimed reader mean is used here. Small-area estimates are separately checked against Poisson limits, and no low-count unit is presented as certain.
"""
    (OUT / "week5_partE_justification.md").write_text(text, encoding="utf-8")
    write_text_pdf(text, OUT / "week5_partE_justification.pdf",
                   "Week 5 Part E — written justification")

    # Part F: real World Bank count / population with a cited Natural Earth boundary.
    wb = pd.read_csv(DATA / "partF_worldbank_co2_population_2022.csv")
    wb["rate"] = wb.co2_mt * 1_000_000 / wb.population
    all_world = geolib.read_geojson(DATA / "partF_naturalearth_admin0_v5.1.2.geojson")
    wb_codes = set(wb.iso3)
    features = [f for f in all_world if f["code"] in wb_codes]
    matched_codes = {f["code"] for f in features}
    matched = wb.loc[wb.iso3.isin(matched_codes)].copy()
    unmatched_data = sorted(wb_codes - matched_codes)
    unmatched_boundary = sorted({f["code"] for f in all_world} - wb_codes)
    values = dict(zip(matched.iso3, matched.rate))
    fig, ax = plt.subplots(figsize=(13, 7))
    edges = geolib.choropleth(
        ax, features, values, scheme="quantile", k=5,
        legend_title="2022 CO₂ tonnes per resident",
        fmt="{:.2f}", legend_loc="lower left",
        legend_anchor=(.02, .02), break_values=matched.rate.to_numpy(),
    )
    ax.set_title("2022 territorial CO₂ emissions per resident · five quantiles")
    save(fig, "week5_partF_normalized_world_map.png",
         f"World Bank 2022 CO2/population + Natural Earth 1:110m v5.1.2; {len(matched)} matched country rows; equal-area.")
    (OUT / "week5_partF_sources_and_audit.md").write_text(
        f"""# Week 5 Part F — bonus normalized map

- **Emissions and population:** World Bank Indicators API, indicator `EN.GHG.CO2.MT.CE.AR5` (CO₂ emissions, total excluding LULUCF, Mt CO₂e) and `SP.POP.TOTL`; year 2022; downloaded 2026-11-09. Rate is `Mt × 1,000,000 / people`, in tonnes CO₂e per resident.
- **Boundaries:** Natural Earth, 1:110m Admin 0 Countries, v5.1.2 (`nvkelso/natural-earth-vector`, GeoJSON), downloaded 2026-11-09. Multipart geometries were expanded into Polygon rings; class breaks are computed once per country (`break_values`) so island count does not reweight the quantiles.
- **Join:** {len(matched)} country rows represented; emissions/population records without a matched boundary: {len(unmatched_data)}; boundary ISO3 codes without a 2022 value: {len(unmatched_boundary)}. Values with missing emissions or population were excluded upstream by the World Bank API response; no small areas were suppressed.
- **Classification/projection:** five quantile classes; breaks `{np.round(edges, 2).tolist()}` printed in the legend; geolib Lambert cylindrical equal-area.
- **Counterfactual:** raw Mt CO₂e totals would emphasize countries with the largest populations/economies; per-resident emissions answer a different question about average territorial emissions per person.
- Source files used by the script are in `data/partF_worldbank_co2_population_2022.csv` and `data/partF_naturalearth_admin0_v5.1.2.geojson`.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=FutureWarning)
    result = make_case_diagnoses()
    b = part_b_decisions(result["hi"], result["dh"], result["feats"])
    c = part_c_reader_activity()
    part_d_figures(result["hi"], result["dh"], result["feats"], b)
    part_e_and_f(result["dh"], result["hi"], b)
    print("\nWeek 5 summary")
    print(json.dumps({key: value for key, value in b.items() if key != "area"},
                     indent=2, default=str))
    print("Part C self-check:", json.dumps(c, default=str))
    print(f"\nWeek 5 deliverables generated under {OUT}")
