"""Build the four-panel transit authority board dashboard."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from week7_common import (
    CHART_DIR,
    MODE_COLORS,
    MODES,
    add_district_choropleth,
    load_clean,
    load_geojson,
    style_axes,
)


ROOT = Path(__file__).resolve().parent
BEFORE = pd.Period("2025Q2", freq="Q")
AFTER = pd.Period("2026Q2", freq="Q")
FARE_MONTHS = pd.period_range("2025-04", "2026-08", freq="M").astype(str).tolist()


def _quarter_totals(daily: pd.DataFrame, quarter: pd.Period) -> pd.DataFrame:
    valid = daily.dropna(subset=["trips_on_time"]).copy()
    valid["quarter"] = valid["date"].dt.to_period("Q")
    return valid.loc[valid["quarter"].eq(quarter)].groupby("mode")[
        ["trips_on_time", "trips_operated"]
    ].sum().reindex(MODES)


def rate_decomposition(before: pd.DataFrame, after: pd.DataFrame) -> dict:
    """Split an aggregate rate change into exact within-group and mix terms."""
    first = before[["trips_on_time", "trips_operated"]].copy()
    second = after[["trips_on_time", "trips_operated"]].copy()
    if first.isna().any().any() or second.isna().any().any():
        raise ValueError("Rate decomposition requires complete valid mode totals.")
    rate_before = first["trips_on_time"] / first["trips_operated"]
    rate_after = second["trips_on_time"] / second["trips_operated"]
    weight_before = first["trips_operated"] / first["trips_operated"].sum()
    weight_after = second["trips_operated"] / second["trips_operated"].sum()
    within = float((((weight_before + weight_after) / 2) * (rate_after - rate_before)).sum() * 100)
    mix = float((((rate_before + rate_after) / 2) * (weight_after - weight_before)).sum() * 100)
    total_before = float(first["trips_on_time"].sum() / first["trips_operated"].sum() * 100)
    total_after = float(second["trips_on_time"].sum() / second["trips_operated"].sum() * 100)
    return {
        "before": total_before,
        "after": total_after,
        "change": total_after - total_before,
        "within": within,
        "mix": mix,
        "delta_by_mode": (rate_after - rate_before) * 100,
        "share_before": weight_before * 100,
        "share_after": weight_after * 100,
    }


def _indexed_fares(fares: pd.DataFrame) -> pd.DataFrame:
    monthly = fares.loc[fares["month"].isin(FARE_MONTHS)].groupby("month")[
        ["trips", "revenue_pkr"]
    ].sum().reindex(FARE_MONTHS)
    return monthly.div(monthly.iloc[0]).mul(100)


def make_dashboard() -> Path:
    style_axes()
    data = load_clean()
    district = data["districts"].set_index("code")
    daily = data["daily"]
    before = _quarter_totals(daily, BEFORE)
    after = _quarter_totals(daily, AFTER)
    decomposition = rate_decomposition(before, after)
    if not np.isclose(decomposition["within"] + decomposition["mix"], decomposition["change"], atol=1e-10):
        raise AssertionError("Rate decomposition must sum to the aggregate change.")

    fig, axes = plt.subplots(2, 2, figsize=(14, 9.5))
    fig.suptitle(
        f"Network punctuality rose {decomposition['change']:+.2f} points—while every mode worsened",
        x=0.055,
        y=0.985,
        ha="left",
        fontsize=16,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.944,
        "2025 Q2 → 2026 Q2 · on-time departures / operated departures · "
        "map: 12-month boardings to 2026-08-31 per 1,000 residents · fare series: journeys and PKR indexed separately "
        "(Apr 2025=100; complete months through Aug 2026)",
        fontsize=9,
        color="#444444",
    )

    # Panel 1: aggregate headline.
    ax = axes[0, 0]
    ax.axis("off")
    ax.text(0.03, 0.87, "NETWORK ON-TIME DEPARTURES", transform=ax.transAxes, fontsize=11, fontweight="bold", color="#444444")
    ax.text(0.02, 0.57, f"{decomposition['before']:.2f}%", transform=ax.transAxes, fontsize=25, fontweight="bold", color="#4d4d4d")
    ax.text(0.44, 0.60, "→", transform=ax.transAxes, fontsize=21, color="#777777")
    ax.text(0.57, 0.57, f"{decomposition['after']:.2f}%", transform=ax.transAxes, fontsize=25, fontweight="bold", color="#0072B2")
    ax.text(0.03, 0.37, f"Reported aggregate change: {decomposition['change']:+.2f} percentage points", transform=ax.transAxes, fontsize=11)
    ax.text(
        0.03,
        0.15,
        "Rate = sum of valid on-time departures ÷ sum of operated departures.\n"
        "The adjacent panel shows why this headline is not service improvement.",
        transform=ax.transAxes,
        fontsize=9,
        color="#444444",
    )
    ax.set_title("A better network headline hides a worse within-mode result", loc="left", fontweight="bold")

    # Panel 2: the reversal and exact decomposition.
    ax = axes[0, 1]
    delta = decomposition["delta_by_mode"].reindex(MODES)
    y = np.arange(len(MODES))
    ax.barh(y, delta.values, color=[MODE_COLORS[mode] for mode in MODES], height=0.62)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_yticks(y, MODES)
    ax.invert_yaxis()
    ax.set_ylim(len(MODES) - 0.5 + 0.8, -0.5)
    ax.set_xlabel("Change in on-time rate (percentage points)")
    ax.set_title("Every mode worsened; changing service mix lifted the aggregate", loc="left", fontweight="bold")
    for index, value in enumerate(delta.values):
        ax.text(value - 0.04, index, f"{value:.2f}", ha="right", va="center", color="white", fontsize=8, fontweight="bold")
    ax.text(
        0.02,
        0.02,
        f"Within {decomposition['within']:+.2f} pp | mix {decomposition['mix']:+.2f} pp | "
        f"net {decomposition['change']:+.2f} pp\n"
        f"Metro share {decomposition['share_before']['Metro']:.1f}% → {decomposition['share_after']['Metro']:.1f}% | "
        f"Bus {decomposition['share_before']['Bus']:.1f}% → {decomposition['share_after']['Bus']:.1f}%",
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88},
    )

    # Panel 3: equal-area normalized district map.
    ax = axes[1, 0]
    per_capita = district["boardings_annual"] / district["population"] * 1000
    breaks = np.unique(np.quantile(per_capita.to_numpy(), np.linspace(0, 1, 6)))
    add_district_choropleth(
        ax,
        load_geojson(),
        per_capita,
        title="Corridor screening: boardings per 1,000 residents",
        colorbar_label="Annual boardings / 1,000 residents",
        breaks=breaks,
    )

    # Panel 4: distinct units indexed separately, never a shared count axis.
    ax = axes[1, 1]
    indexed = _indexed_fares(data["fares"])
    x = np.arange(len(indexed))
    ax.plot(x, indexed["trips"], color="#0072B2", marker="o", markersize=3, linewidth=1.8, label="Journeys")
    ax.plot(x, indexed["revenue_pkr"], color="#D55E00", marker="s", markersize=3, linewidth=1.8, label="Fare revenue (PKR)")
    ax.axhline(100, color="#777777", linewidth=0.8, linestyle=":")
    ax.set_xticks(x[::3], [pd.Period(indexed.index[i]).strftime("%b\n%Y") for i in x[::3]])
    ax.set_ylabel("Index (Apr 2025 = 100; separate original units)")
    ax.set_xlabel("Complete month")
    journeys_change = (indexed["trips"].iloc[-1] - 100)
    revenue_change = (indexed["revenue_pkr"].iloc[-1] - 100)
    mean_fare = data["fares"].groupby("month")[["trips", "revenue_pkr"]].sum()
    blended_change = (
        mean_fare.loc["2026-08", "revenue_pkr"] / mean_fare.loc["2026-08", "trips"]
        / (mean_fare.loc["2025-04", "revenue_pkr"] / mean_fare.loc["2025-04", "trips"])
        - 1
    ) * 100
    ax.set_title(
        f"Revenue +{revenue_change:.1f}% vs journeys +{journeys_change:.1f}%; "
        f"blended PKR/journey +{blended_change:.1f}%",
        loc="left",
        fontweight="bold",
        fontsize=10,
    )
    ax.legend(frameon=False, loc="upper left")

    fig.text(
        0.055,
        0.022,
        textwrap.fill(
            "Reading order: the Secretary sees the aggregate first, the adjacent mode panel tests it, then the normalized map and fare trend answer siting and finance questions. "
            "Source: Federal Transit Authority synthetic returns and published fare table; district boundaries from the same package.",
            width=200,
        ),
        fontsize=8,
        color="#444444",
    )
    fig.tight_layout(rect=(0.035, 0.055, 0.98, 0.91))
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    target = CHART_DIR / "partD_screen.png"
    fig.savefig(target, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return target


def main() -> None:
    path = make_dashboard()
    print(f"Dashboard written to {path}")


if __name__ == "__main__":
    main()
