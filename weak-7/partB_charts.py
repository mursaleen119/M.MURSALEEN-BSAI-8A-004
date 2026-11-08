"""Create the four question-led static charts required by Week 7 Task B."""

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
CAPTION_SIZE = 8
COMPLETE_MONTHS = pd.period_range("2025-04", "2026-08", freq="M")


def _export(fig: plt.Figure, filename: str) -> Path:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    target = CHART_DIR / filename
    fig.savefig(target, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return target


def _caption(fig: plt.Figure, text: str) -> None:
    fig.text(
        0.02,
        0.015,
        textwrap.fill(text, width=135),
        ha="left",
        va="bottom",
        fontsize=CAPTION_SIZE,
        color="#333333",
    )


def _month_labels(index: pd.Index) -> list[str]:
    return [pd.Period(month, freq="M").strftime("%b\n%Y") for month in index]


def chart_daily_boardings(data: dict[str, pd.DataFrame]) -> Path:
    daily = data["daily"].copy()
    start, end = pd.Timestamp("2025-04-01"), pd.Timestamp("2026-08-31")
    daily = daily.loc[daily["date"].between(start, end)].copy()
    daily["month"] = daily["date"].dt.to_period("M").astype(str)
    monthly = daily.groupby(["month", "mode"], observed=True)["boardings"].sum().unstack()
    coverage = daily.groupby(["month", "mode"], observed=True)["boardings"].count().unstack()
    month_index = [str(month) for month in COMPLETE_MONTHS]
    monthly = monthly.reindex(month_index)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for mode in MODES:
        ax.plot(
            monthly.index,
            monthly[mode] / 1_000_000,
            color=MODE_COLORS[mode],
            marker={"Metro": "o", "BRT": "s", "Bus": "^", "Ferry": "D"}[mode],
            linewidth=1.8,
            markersize=4,
            label=mode,
        )
    ax.set_title("Reported monthly boardings show distinct mode scale and variation", loc="left", fontweight="bold")
    ax.set_ylabel("Boardings on filed return-days (millions)")
    ax.set_xlabel("Reporting month")
    positions = np.arange(len(monthly.index))
    ax.set_xticks(positions[::2], _month_labels(monthly.index)[::2], rotation=0)
    ax.set_xlim(-0.4, len(monthly.index) - 0.6)
    ax.legend(title="Mode", frameon=False, ncol=4, loc="upper left")
    minimum_days = int(coverage.min().min())
    caption = (
        "Decision: compare observed monthly boarding flows by mode. Sum of filed daily returns only; "
        "unfiled date×mode slots are not zero-filled. Window: 2025-04–2026-08; "
        f"minimum filed days in any month×mode cell={minimum_days}/31. 2026-09 excluded as partial. Source: FTA synthetic returns."
    )
    _caption(fig, caption)
    fig.subplots_adjust(bottom=0.29, top=0.88)
    return _export(fig, "partB_1_daily_boardings_trend.png")


def chart_fare_hierarchy(data: dict[str, pd.DataFrame]) -> Path:
    fares = data["fares"]
    month = "2026-08"
    latest = fares.loc[fares["month"].eq(month)].copy()
    if latest.empty:
        raise ValueError(f"Fare table is missing required complete month {month}.")
    product_totals = latest.pivot(index="mode", columns="ticket_type", values="revenue_pkr")
    product_totals = product_totals.reindex(MODES)
    products = [name for name in ("Single", "Daily", "Monthly") if name in product_totals.columns]
    shares = product_totals[products].div(product_totals[products].sum(axis=1), axis=0) * 100
    product_colors = {"Single": "#0072B2", "Daily": "#E69F00", "Monthly": "#009E73"}
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    x = np.arange(len(MODES))
    bottom = np.zeros(len(MODES))
    for product in products:
        values = shares[product].to_numpy()
        ax.bar(
            x,
            values,
            bottom=bottom,
            color=product_colors[product],
            width=0.62,
            edgecolor="white",
            linewidth=0.6,
            label=product,
        )
        bottom += values
    mode_revenue = product_totals[products].sum(axis=1)
    ax.set_xticks(x, [f"{mode}\n{mode_revenue[mode] / 1e9:.2f} bn PKR" for mode in MODES])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Share of each mode's fare revenue (%)")
    ax.set_xlabel("Mode (total 2026-08 revenue labelled below)")
    ax.set_title("August fare revenue is concentrated in single tickets", loc="left", fontweight="bold")
    ax.legend(title="Fare product", frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    _caption(
        fig,
        "Decision: inspect the fare-product hierarchy for the finance director. Each 100% bar is revenue within one mode; "
        "Single/Daily/Monthly are exclusive parts; `All tickets` summary rows excluded. Revenue, not journeys or boardings. "
        "Complete month 2026-08. Source: ministry fare table.",
    )
    fig.subplots_adjust(bottom=0.36, top=0.87)
    return _export(fig, "partB_2_fare_hierarchy.png")


def chart_normalized_district_map(data: dict[str, pd.DataFrame]) -> tuple[Path, np.ndarray]:
    districts = data["districts"].set_index("code")
    per_capita = districts["boardings_annual"] / districts["population"] * 1000
    geojson = load_geojson()
    values = per_capita.sort_index()
    breaks = np.unique(np.quantile(values.to_numpy(), np.linspace(0, 1, 6)))
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    add_district_choropleth(
        ax,
        geojson,
        values,
        title="D12 and D21 lead on annual boardings per resident",
        colorbar_label="Boardings per 1,000 residents",
        breaks=breaks,
    )
    ax.text(
        0.02,
        0.02,
        "Equal-area Lambert azimuthal projection · D00 excluded: no boundary feature",
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8},
    )
    _caption(
        fig,
        "Decision: compare annual transit intensity rather than population-sized raw counts. "
        "Denominator: resident population; numerator: 12-month attributed boardings; rate per 1,000 residents. "
        f"Five quantile class breaks: {', '.join(f'{value:,.0f}' for value in breaks)}. Source: FTA synthetic district register.",
    )
    fig.subplots_adjust(bottom=0.24, right=0.88, top=0.9)
    return _export(fig, "partB_3_normalized_district_map.png"), breaks


def chart_fare_relationship(data: dict[str, pd.DataFrame]) -> Path:
    fares = data["fares"].copy()
    fares = fares.loc[fares["month"].isin([str(month) for month in COMPLETE_MONTHS])]
    monthly = fares.groupby(["month", "mode"], as_index=False)[["trips", "revenue_pkr"]].sum()
    monthly["mean_fare"] = monthly["revenue_pkr"] / monthly["trips"]
    fig, ax = plt.subplots(figsize=(9, 5.7))
    markers = {"Metro": "o", "BRT": "s", "Bus": "^", "Ferry": "D"}
    for mode in MODES:
        group = monthly.loc[monthly["mode"].eq(mode)]
        ax.scatter(
            group["mean_fare"],
            group["trips"] / 1_000_000,
            color=MODE_COLORS[mode],
            marker=markers[mode],
            s=42,
            alpha=0.68,
            edgecolor="white",
            linewidth=0.4,
            label=mode,
        )
        endpoint = group.loc[group["month"].eq("2026-08")]
        if not endpoint.empty:
            row = endpoint.iloc[0]
            ax.annotate(mode, (row["mean_fare"], row["trips"] / 1_000_000), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Mean fare (PKR per journey)")
    ax.set_ylabel("Journeys sold per mode-month (millions)")
    ax.set_title("Revenue growth reflects both journey volume and blended fare", loc="left", fontweight="bold")
    ax.legend(title="Mode", frameon=False, ncol=4)
    _caption(
        fig,
        "Decision: distinguish journey volume from blended PKR per journey. One point per mode-month; "
        "complete months 2025-04–2026-08; `All tickets` totals excluded. The average fare also reflects product/mode mix, "
        "not just a posted-price change. Journeys are not boardings. Source: ministry fare table.",
    )
    fig.subplots_adjust(bottom=0.26, top=0.87)
    return _export(fig, "partB_4_fare_relationship.png")


def make_charts() -> tuple[list[Path], np.ndarray]:
    style_axes()
    data = load_clean()
    outputs = [
        chart_daily_boardings(data),
        chart_fare_hierarchy(data),
    ]
    map_path, breaks = chart_normalized_district_map(data)
    outputs += [map_path, chart_fare_relationship(data)]
    return outputs, breaks


def main() -> None:
    outputs, breaks = make_charts()
    print("Task B charts:")
    for path in outputs:
        print(f"  {path.relative_to(ROOT)}")
    print("Normalized-map breaks:", ", ".join(f"{value:.0f}" for value in breaks))


if __name__ == "__main__":
    main()
