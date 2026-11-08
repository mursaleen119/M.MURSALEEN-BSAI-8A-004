"""Generate three Week 6 figures for trend, composition, and comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from week6_common import CHART_DIR, add_source_note, load_clean, month_boundary_energy, style_axes


def _save(fig: plt.Figure, name: str) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_DIR / name, dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_charts() -> list[str]:
    data = load_clean()
    style_axes()
    written = []

    daily = data["daily"]
    energy = month_boundary_energy(daily, "P1")
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.plot(energy.index.to_timestamp(), energy.values / 1_000, color="#0072B2", marker="o", linewidth=1.8)
    ax.set_title("P1 delivered about 1.2 million MWh in June 2026", loc="left", fontweight="bold")
    ax.set_xlabel("Month (meter change from the first day to the next month's first day)")
    ax.set_ylabel("Energy delivered (thousand MWh)")
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.text(
        0.01,
        0.97,
        "Counter differences only; intervals with a missing boundary meter reading are not estimated. "
        "Complete months Apr 2025–Aug 2026.",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        color="#444444",
    )
    add_source_note(fig, "Decision supported: identify changes in P1 energy deliveries without summing a cumulative meter. Source: synthetic Week 6 grid_daily.csv.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "partB_1_zone_energy_trend.png")
    written.append("partB_1_zone_energy_trend.png")

    generation = data["generation"].copy()
    generation["month"] = pd.PeriodIndex(generation["month"], freq="M")
    source_month = generation.groupby(["month", "source"], observed=True)["mwh"].sum().unstack()
    total = source_month.sum(axis=1)
    shares = source_month.div(total, axis=0).mul(100)
    fig, (ax_total, ax_share) = plt.subplots(
        2, 1, figsize=(10.5, 7.2), sharex=True, gridspec_kw={"height_ratios": [1, 1.15]}
    )
    dates = source_month.index.to_timestamp()
    ax_total.plot(dates, total / 1_000_000, color="#333333", marker="o", markersize=3.5, linewidth=1.6)
    ax_total.set_title("Total generation fell while solar's share rose", loc="left", fontweight="bold")
    ax_total.set_ylabel("Total generation (million MWh)")
    ax_total.grid(axis="y", color="#dddddd", linewidth=0.6)
    colors = {
        "Fossil": "#D55E00",
        "Hydro": "#0072B2",
        "Renewable": "#009E73",
        "Imported": "#999999",
    }
    order = [source for source in ["Fossil", "Hydro", "Renewable", "Imported"] if source in shares]
    ax_share.stackplot(
        dates,
        [shares[source].to_numpy() for source in order],
        labels=order,
        colors=[colors[source] for source in order],
        alpha=0.92,
    )
    ax_share.set_ylim(0, 100)
    ax_share.set_ylabel("Share of monthly generation (%)")
    ax_share.set_xlabel("Complete month (parent totals excluded; leaf categories sum to published total)")
    ax_share.legend(title="Generation source", loc="upper left", ncol=4, frameon=False)
    ax_share.grid(axis="y", color="white", linewidth=0.8)
    total_change = 100 * (total.iloc[-1] / total.iloc[0] - 1)
    solar_rows = generation.loc[generation["subsource"].eq("Solar")].set_index("month")["mwh"]
    solar_change = 100 * (solar_rows.iloc[-1] / solar_rows.iloc[0] - 1)
    ax_total.text(
        0.99,
        0.96,
        f"Total {total_change:+.1f}% | solar MWh {solar_change:+.1f}%\n"
        f"Solar share {solar_rows.iloc[0]/total.iloc[0]:.1%} → {solar_rows.iloc[-1]/total.iloc[-1]:.1%}",
        transform=ax_total.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85},
    )
    add_source_note(fig, "Decision supported: distinguish a change in total generation from a change in generation mix. Source: synthetic Week 6 generation_mix.csv.")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    _save(fig, "partB_2_generation_mix.png")
    written.append("partB_2_generation_mix.png")

    districts = data["districts"].copy()
    districts["interruptions_per_1000_households"] = districts["outages"] / districts["households"] * 1_000
    ranked = districts.nlargest(12, "interruptions_per_1000_households").sort_values(
        "interruptions_per_1000_households"
    )
    colors_top = ["#0072B2" if code in {"D12", "D11", "D13"} else "#b8b8b8" for code in ranked["code"]]
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    bars = ax.barh(
        ranked["code"],
        ranked["interruptions_per_1000_households"],
        color=colors_top,
        edgecolor="white",
    )
    pooled = districts["outages"].sum() / districts["households"].sum() * 1_000
    ax.axvline(pooled, color="#333333", linestyle="--", linewidth=1, label=f"National pooled rate: {pooled:.1f}")
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
    ax.set_xlim(0, max(ranked["interruptions_per_1000_households"]) * 1.2)
    ax.set_xlabel("Annual interruptions per 1,000 households")
    ax.set_ylabel("District (top 12 of 24)")
    ax.set_title("Household-normalized interruption rates identify different priorities", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    add_source_note(fig, "Decision supported: prioritize relative interruption burden, not the largest raw counts. Source: synthetic Week 6 district_grid.csv.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "partB_3_district_reliability.png")
    written.append("partB_3_district_reliability.png")

    if not np.isclose(energy.loc["2026-06"], 1_200_239, atol=1):
        raise AssertionError(f"P1 June 2026 meter difference should be about 1,200,239 MWh, got {energy.loc['2026-06']}")
    if not np.isclose(total.iloc[-1] / total.iloc[0] - 1, -0.05, atol=0.001):
        raise AssertionError("Generation total trend no longer matches the instructor's anchor.")
    return written


if __name__ == "__main__":
    for chart in make_charts():
        print(f"Wrote {chart}")
