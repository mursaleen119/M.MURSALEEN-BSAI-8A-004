"""Export the normalized district reliability map and its written counterfactual."""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Polygon as MplPolygon

from week6_common import CHART_DIR, ROOT, add_source_note, load_clean, project_laea, style_axes


def _polygon_area_km2(points: list[list[float]]) -> float:
    projected = np.asarray([project_laea(lon, lat) for lon, lat in points])
    return abs(
        np.dot(projected[:, 0], np.roll(projected[:, 1], 1))
        - np.dot(projected[:, 1], np.roll(projected[:, 0], 1))
    ) / 2 / 1_000_000


def make_figure() -> tuple[str, dict[str, object]]:
    data = load_clean()
    districts = data["districts"].copy()
    districts["interruptions_per_1000_households"] = districts["outages"] / districts["households"] * 1_000
    by_code = districts.set_index("code")
    values = by_code["interruptions_per_1000_households"]
    codes = [feature["properties"]["code"] for feature in data["geojson"]["features"]]
    unmatched = sorted(set(codes).symmetric_difference(values.index))
    if unmatched:
        raise ValueError(f"Cannot map unmatched district codes: {unmatched}")

    rate = values.to_numpy(dtype=float)
    breaks = np.unique(np.quantile(rate, np.linspace(0, 1, 6)))
    if len(breaks) != 6:
        raise ValueError(f"Expected five distinct quantile classes, got {len(breaks)-1}.")
    cmap = plt.get_cmap("viridis", len(breaks) - 1)
    norm = mcolors.BoundaryNorm(breaks, cmap.N, clip=True)

    style_axes()
    fig, (map_ax, bar_ax) = plt.subplots(
        1, 2, figsize=(12.2, 8.0), gridspec_kw={"width_ratios": [1.0, 1.15]}
    )
    map_ax.set_title("Outage burden varies after household normalization", loc="left", fontweight="bold")
    map_ax.set_axis_off()
    area_by_code: dict[str, float] = {}
    for feature in data["geojson"]["features"]:
        code = feature["properties"]["code"]
        ring = feature["geometry"]["coordinates"][0]
        points = [project_laea(lon, lat) for lon, lat in ring]
        polygon = MplPolygon(points, closed=True, edgecolor="white", linewidth=0.8)
        polygon.set_facecolor(cmap(norm(values.loc[code])))
        map_ax.add_patch(polygon)
        center = np.asarray(points[:-1]).mean(axis=0)
        map_ax.text(center[0], center[1], code[-2:], ha="center", va="center", fontsize=7, color="black")
        area_by_code[code] = _polygon_area_km2(ring)
    map_ax.autoscale_view()
    map_ax.set_aspect("equal", adjustable="datalim")
    scalar = ScalarMappable(norm=norm, cmap=cmap)
    scalar.set_array([])
    colorbar = fig.colorbar(
        scalar,
        ax=map_ax,
        fraction=0.048,
        pad=0.02,
        ticks=(breaks[:-1] + breaks[1:]) / 2,
    )
    colorbar.ax.set_yticklabels([f"{lo:.1f}–{hi:.1f}" for lo, hi in zip(breaks[:-1], breaks[1:])])
    colorbar.set_label("Annual interruptions per 1,000 households")

    ranked = districts.sort_values("interruptions_per_1000_households")
    colors = [
        "#0072B2" if code in {"D12", "D11", "D13"} else "#b8b8b8"
        for code in ranked["code"]
    ]
    bars = bar_ax.barh(
        ranked["code"],
        ranked["interruptions_per_1000_households"],
        color=colors,
        edgecolor="white",
    )
    pooled = districts["outages"].sum() / districts["households"].sum() * 1_000
    bar_ax.axvline(pooled, color="#333333", linestyle="--", linewidth=1, label=f"Pooled rate {pooled:.1f}")
    bar_ax.set_xlabel("Annual interruptions per 1,000 households")
    bar_ax.set_ylabel("District")
    bar_ax.set_title("Rates (all 24 districts; top three highlighted)", loc="left", fontweight="bold")
    bar_ax.legend(frameon=False, loc="lower right")
    bar_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    bar_ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=6)

    top_count = districts.nlargest(3, "outages")["code"].tolist()
    top_rate = districts.nlargest(3, "interruptions_per_1000_households")["code"].tolist()
    overlap = sorted(set(top_count) & set(top_rate))
    largest = districts.nlargest(5, "population")
    land_share = sum(area_by_code[code] for code in largest["code"]) / sum(area_by_code.values())
    people_share = largest["population"].sum() / districts["population"].sum()
    corr_count = districts["outages"].corr(districts["households"])
    corr_rate = districts["interruptions_per_1000_households"].corr(districts["households"])
    total_rate = districts["outages"].sum() / districts["households"].sum() * 1_000
    fig.suptitle(
        "Grid Authority budget screen: compare interruption rates, not raw district totals",
        x=0.055,
        y=0.98,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.925,
        f"Annual outages / billed households; 12-month register · raw count leaders {', '.join(top_count)} "
        f"vs rate leaders {', '.join(top_rate)}",
        fontsize=9,
        color="#444444",
    )
    add_source_note(
        fig,
        "Source: synthetic National Grid Authority district register and matching district boundaries, Week 6. "
        "Map projection: Lambert azimuthal equal-area, centered 70°E, 30°N.",
    )
    fig.tight_layout(rect=(0.02, 0.045, 0.98, 0.9))
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    destination = CHART_DIR / "partC_figure.png"
    fig.savefig(destination, dpi=300, bbox_inches="tight")
    plt.close(fig)

    metadata: dict[str, object] = {
        "breaks": [float(x) for x in breaks],
        "top_count": top_count,
        "top_rate": top_rate,
        "overlap": overlap,
        "pooled_rate": float(total_rate),
        "corr_count_households": float(corr_count),
        "corr_rate_households": float(corr_rate),
        "top_five_land_share": float(land_share),
        "top_five_population_share": float(people_share),
    }
    note = f"""# Task C — Reliability budget figure and counterfactual

**Reader and message.** For the National Grid Authority budget board: interruption frequency per billed household varies materially by district. The three highest normalized rates are {', '.join(top_rate)}; this is a screening result, not a complete outage-severity or service-equity measure.

**Measure and denominator.** Annual recorded supply interruptions divided by billed domestic households, multiplied by 1,000. The measure is interruptions per 1,000 households, not interruption minutes or population. The pooled national rate is {total_rate:.1f} interruptions per 1,000 households.

**Parameters.** The map uses five quantile classes with breaks {', '.join(f'{x:.2f}' for x in breaks)} (inclusive lower endpoints). District polygons are projected with Lambert azimuthal equal-area centered at 70°E, 30°N before drawing; this preserves area comparisons. The sorted bar panel uses the same normalized measure and a zero baseline. No district was suppressed or merged; all 24 are shown.

**Counterfactual and ethics.** Mapping raw interruption counts would point first to {', '.join(top_count)}, while the rate map points to {', '.join(top_rate)}; only {', '.join(overlap)} appears on both lists. A count-first allocation would direct attention toward the largest district totals and away from high-rate districts D12 and D11. Counts correlate with household totals at r={corr_count:+.3f}, while the normalized rate correlation is r={corr_rate:+.3f}. The five most populous districts contain {people_share:.1%} of residents on {land_share:.1%} of the land, so an area-colored map also gives these dense districts little visual area. No district is suppressed; the source data are synthetic, and this rate screen must be combined with duration, outage concentration, equity and local context before money is allocated.
"""
    (ROOT / "partC_note.md").write_text(note, encoding="utf-8")
    return str(destination), metadata


if __name__ == "__main__":
    path, metrics = make_figure()
    print(f"Wrote {path}")
    print(json.dumps(metrics, indent=2))
