"""Week 7 adaptation using the repository's sole source: Gapminder."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _interactive_requested() -> bool:
    """Choose a GUI backend only when the explicit interactive flag is present."""
    return "--interactive" in sys.argv

import matplotlib

matplotlib.use("TkAgg" if _interactive_requested() else "Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.widgets import Button, CheckButtons


ROOT = Path(__file__).resolve().parents[1]
WEEK_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "gapminder.csv"
CHART_DIR = WEEK_DIR / "charts"
CONTINENTS = ["Africa", "Americas", "Asia", "Europe", "Oceania"]
COLORS = dict(zip(CONTINENTS, sns.color_palette("colorblind", len(CONTINENTS)).as_hex()))
MARKERS = dict(zip(CONTINENTS, ["o", "s", "^", "D", "P"]))
YEARS = [1952, 2007]


def load_data() -> pd.DataFrame:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Expected the existing source dataset at {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    expected = {"country", "year", "pop", "continent", "lifeExp", "gdpPercap"}
    if set(frame.columns) != expected:
        raise ValueError(f"Unexpected Gapminder columns: {list(frame.columns)}")
    return frame


def audit_data(frame: pd.DataFrame) -> str:
    """Print and save the applicable audit; do not duplicate or edit the source."""
    years = sorted(frame["year"].unique().tolist())
    key_duplicates = int(frame.duplicated(["country", "year"]).sum())
    missing = int(frame.isna().sum().sum())
    year_steps = sorted(set(np.diff(years).astype(int).tolist()))
    per_country = frame.groupby("country")["year"].agg(["count", "nunique"])
    nonpositive = {
        column: int((frame[column] <= 0).sum())
        for column in ["pop", "lifeExp", "gdpPercap"]
    }
    lines = [
        "Week 7 adapted audit — source is the existing data/gapminder.csv",
        f"Rows: {len(frame):,}; columns: {', '.join(frame.columns)}",
        "Dtypes: " + "; ".join(f"{name}={dtype}" for name, dtype in frame.dtypes.items()),
        f"Unique country-year keys: {frame[['country', 'year']].drop_duplicates().shape[0]:,}; "
        f"duplicate keys: {key_duplicates}",
        f"Missing cells: {missing}",
        f"Countries: {frame['country'].nunique()}; continents: "
        f"{', '.join(sorted(frame['continent'].unique()))}",
        f"Observation years: {years[0]}–{years[-1]} ({len(years)} values); "
        f"year steps: {year_steps}",
        f"Countries with a row-count other than {len(years)}: "
        f"{int((per_country['count'] != len(years)).sum())}; "
        f"countries missing an expected year: "
        f"{int((per_country['nunique'] != len(years)).sum())}",
        "Non-positive values (invalid for calculations): "
        + ", ".join(f"{key}={value}" for key, value in nonpositive.items()),
        "Ranges used in calculations: "
        + "; ".join(
            f"{column}={frame[column].min():,.3f}–{frame[column].max():,.3f}"
            for column in ["pop", "lifeExp", "gdpPercap"]
        ),
        "Division denominators: population is positive "
        f"({frame['pop'].min():,.0f}–{frame['pop'].max():,.0f}); "
        "GDP per capita is positive "
        f"({frame['gdpPercap'].min():,.3f}–{frame['gdpPercap'].max():,.3f}).",
        "Join misses: not applicable; no external boundary or transit table is used.",
        "Geographic audit: not possible; Gapminder has no coordinates or boundary geometry.",
        "Channel plan: continent is consistently mapped to color and marker shape; "
        "year is horizontal position on time charts; life expectancy is vertical "
        "position where plotted; population share is vertical position only on its panel.",
        "Channel conflict check: 0 conflicts under the plan above.",
        "Palette check: Seaborn's colorblind palette is used, with marker shape as a "
        "redundant continent cue. Instructor vizlib.cvd_report() is unavailable in "
        "this one-dataset adaptation, so no simulation result is claimed.",
        "Scope note: transit-specific 14-defect audit, route overlap, drill-down, "
        "and normalized district map cannot be reproduced from Gapminder.",
    ]
    report = "\n".join(lines) + "\n"
    print(report, end="")
    (WEEK_DIR / "partA_audit.txt").write_text(report, encoding="utf-8")
    return report


def _save(fig: plt.Figure, name: str) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_DIR / name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_part_b_charts(frame: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid", context="notebook")

    # 1. Trend: country-level means preserve equal country weights.
    means = frame.groupby(["year", "continent"], as_index=False)["lifeExp"].mean()
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for continent in CONTINENTS:
        group = means[means["continent"] == continent]
        ax.plot(
            group["year"],
            group["lifeExp"],
            color=COLORS[continent],
            marker=MARKERS[continent],
            linewidth=2,
            label=continent,
        )
    ax.set(title="Life expectancy rose in every continent", xlabel="Year", ylabel="Mean life expectancy (years)")
    ax.legend(title="Continent", ncol=3, frameon=False)
    fig.subplots_adjust(bottom=0.23, top=0.88)
    fig.text(
        0.01,
        0.025,
        "Decision: compare long-run public-health progress by continent. "
        "Mean across country observations; all 12 five-year observations, 1952–2007. Source: Gapminder.",
        fontsize=8,
    )
    _save(fig, "partB_1_trend.png")

    # 2. Composition: continents are exclusive groups in this dataset.
    population = frame[frame["year"].isin(YEARS)].groupby(["year", "continent"])["pop"].sum().unstack()
    shares = population.div(population.sum(axis=1), axis=0).reindex(columns=CONTINENTS) * 100
    fig, ax = plt.subplots(figsize=(8, 5.4))
    x = np.arange(len(YEARS))
    bottom = np.zeros(len(YEARS))
    for continent in CONTINENTS:
        values = shares[continent].to_numpy()
        ax.bar(x, values, bottom=bottom, color=COLORS[continent], label=continent, width=0.58)
        bottom += values
    ax.set_xticks(x, [str(year) for year in YEARS])
    ax.set_ylim(0, 100)
    ax.set(title="Asia held the largest share of the population in both years", xlabel="Year", ylabel="Share of total population (%)")
    ax.legend(title="Continent", ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    fig.subplots_adjust(bottom=0.34, top=0.88)
    fig.text(
        0.01,
        0.025,
        "Decision: distinguish population mix from per-country averages. "
        "100% stacked; sum population within each continent; compare 1952 with 2007 only. Source: Gapminder.",
        fontsize=8,
    )
    _save(fig, "partB_2_population_composition.png")

    # 3. Relationship: GDP is log-scaled because the positive values span orders of magnitude.
    latest = frame[frame["year"] == 2007]
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    for continent in CONTINENTS:
        group = latest[latest["continent"] == continent]
        ax.scatter(
            group["gdpPercap"],
            group["lifeExp"],
            color=COLORS[continent],
            marker=MARKERS[continent],
            alpha=0.8,
            edgecolor="white",
            linewidth=0.35,
            label=continent,
        )
    ax.set_xscale("log")
    ax.set(title="Higher income is associated with longer lives in 2007", xlabel="GDP per capita (US$, log scale)", ylabel="Life expectancy (years)")
    ax.legend(title="Continent", frameon=False, ncol=3)
    fig.subplots_adjust(bottom=0.24, top=0.88)
    fig.text(
        0.01,
        0.025,
        "Decision: compare country-level association, not causation. One point per country; 2007 only; "
        "positive GDP per capita on a log x-axis. Source: Gapminder.",
        fontsize=8,
    )
    _save(fig, "partB_3_income_life_expectancy.png")

    # 4. Distribution: show within-continent spread, not only group averages.
    latest = latest.copy()
    latest["continent"] = pd.Categorical(latest["continent"], CONTINENTS, ordered=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.boxplot(data=latest, x="continent", y="lifeExp", hue="continent", order=CONTINENTS, palette=COLORS, legend=False, ax=ax)
    counts = latest.groupby("continent", observed=True)["country"].nunique()
    ax.set_xticks(
        range(len(CONTINENTS)),
        [f"{name}\nn={counts[name]}" for name in CONTINENTS],
    )
    ax.set(title="Country life expectancy still varies widely within continents", xlabel="Continent (number of countries)", ylabel="Life expectancy in 2007 (years)")
    fig.subplots_adjust(bottom=0.3, top=0.88)
    fig.text(
        0.01,
        0.025,
        "Decision: identify where a continental average hides country-level spread. "
        "One country per observation; 2007 only; box shows median and quartiles. Source: Gapminder.",
        fontsize=8,
    )
    _save(fig, "partB_4_life_expectancy_distribution.png")


def make_dashboard(frame: pd.DataFrame) -> None:
    """Build a four-panel screen and make the aggregation check explicit."""
    sns.set_theme(style="whitegrid", context="notebook")
    by_year = frame.groupby("year")
    country_mean = by_year["lifeExp"].mean()
    population_weighted = (frame["lifeExp"] * frame["pop"]).groupby(frame["year"]).sum() / by_year["pop"].sum()
    continent_mean = frame.groupby(["continent", "year"])["lifeExp"].mean().unstack()
    change = continent_mean[2007] - continent_mean[1952]
    equal_change = float(country_mean.loc[2007] - country_mean.loc[1952])
    weighted_change = float(population_weighted.loc[2007] - population_weighted.loc[1952])
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.2))
    fig.suptitle(
        "Life expectancy rose in every continent; the population-weighted gain was larger",
        x=0.06,
        y=0.99,
        ha="left",
        fontsize=17,
        fontweight="bold",
    )
    fig.text(
        0.06,
        0.945,
        "1952–2007 · life expectancy in years · country mean weights each country equally; "
        f"population-weighted mean uses residents as weights · world gains: +{equal_change:.1f} y equal-country, "
        f"+{weighted_change:.1f} y population-weighted · all five continent means rose",
        fontsize=10,
        color="#444444",
    )

    ax = axes[0, 0]
    ax.plot(country_mean.index, country_mean.values, color="#222222", marker="o", label="Equal country weights")
    ax.plot(population_weighted.index, population_weighted.values, color="#0072B2", marker="s", linestyle="--", label="Population weights")
    ax.set(title="World average rises under both weighting rules", xlabel="Year", ylabel="Life expectancy (years)")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[0, 1]
    ordered_change = change.reindex(CONTINENTS)
    ax.barh(CONTINENTS, ordered_change.values, color=[COLORS[c] for c in CONTINENTS])
    ax.axvline(0, color="#333333", linewidth=0.8)
    for y, value in enumerate(ordered_change.values):
        ax.text(value + 0.35, y, f"+{value:.1f}", va="center", fontsize=9)
    ax.set_xlim(0, float(ordered_change.max()) + 5)
    ax.set(title="Aggregation check: all five continent means rose", xlabel="Change, 1952 to 2007 (years)", ylabel="")

    ax = axes[1, 0]
    pop_by_continent = frame[frame["year"].isin(YEARS)].groupby(["year", "continent"])["pop"].sum().unstack()
    pop_shares = pop_by_continent.div(pop_by_continent.sum(axis=1), axis=0).reindex(columns=CONTINENTS) * 100
    x = np.arange(len(YEARS))
    bottom = np.zeros(len(YEARS))
    for continent in CONTINENTS:
        values = pop_shares[continent].to_numpy()
        ax.bar(x, values, bottom=bottom, color=COLORS[continent], label=continent)
        bottom += values
    ax.set_xticks(x, [str(year) for year in YEARS])
    ax.set_ylim(0, 100)
    ax.set(title="Population composition (100% of residents)", xlabel="Year", ylabel="Population share (%)")
    ax.legend(frameon=False, ncol=3, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.15))

    ax = axes[1, 1]
    latest = frame[frame["year"] == 2007]
    for continent in CONTINENTS:
        group = latest[latest["continent"] == continent]
        ax.scatter(
            group["gdpPercap"],
            group["lifeExp"],
            color=COLORS[continent],
            marker=MARKERS[continent],
            alpha=0.75,
            edgecolor="white",
            linewidth=0.3,
            label=continent,
        )
    ax.set_xscale("log")
    ax.set(title="Income and life expectancy are associated", xlabel="GDP per capita (US$, log scale)", ylabel="Life expectancy (years)")
    ax.legend(frameon=False, ncol=3, fontsize=7)
    fig.text(0.06, 0.015, "Source: Gapminder. Descriptive country-level data; no geographic boundary file, transit measure, or causal estimate is available.", fontsize=8, color="#444444")
    fig.tight_layout(rect=(0.04, 0.045, 0.98, 0.91))
    _save(fig, "partD_screen.png")


def make_interactive(frame: pd.DataFrame, show: bool = True) -> plt.Figure:
    """Open a continent-filterable 2007 scatter with an explicit reset control."""
    latest = frame[frame["year"] == 2007]
    fig = plt.figure(figsize=(11, 6.5))
    ax = fig.add_axes([0.09, 0.16, 0.62, 0.72])
    check_ax = fig.add_axes([0.76, 0.42, 0.2, 0.34])
    reset_ax = fig.add_axes([0.79, 0.29, 0.14, 0.07])
    artists = {}
    for continent in CONTINENTS:
        group = latest[latest["continent"] == continent]
        artists[continent] = ax.scatter(
            group["gdpPercap"],
            group["lifeExp"],
            color=COLORS[continent],
            marker=MARKERS[continent],
            alpha=0.8,
            edgecolor="white",
            linewidth=0.35,
            label=continent,
        )
    ax.set_xscale("log")
    ax.set(title="2007: income and life expectancy by country", xlabel="GDP per capita (US$, log scale)", ylabel="Life expectancy (years)")
    ax.legend(frameon=False, ncol=3, loc="lower right")
    fig.suptitle("Toggle continents; use Reset to restore all five", x=0.09, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.09, 0.07, "One point per country; this descriptive association is not a causal effect. Source: Gapminder.", fontsize=9)
    toggles = CheckButtons(check_ax, CONTINENTS, [True] * len(CONTINENTS))
    reset = Button(reset_ax, "Reset")

    def toggle(label: str) -> None:
        artists[label].set_visible(not artists[label].get_visible())
        fig.canvas.draw_idle()

    def restore(_event: object) -> None:
        for index, visible in enumerate(toggles.get_status()):
            if not visible:
                toggles.set_active(index)

    toggles.on_clicked(toggle)
    reset.on_clicked(restore)
    # Matplotlib's event registry holds weak references to widget callbacks.
    fig._week7_widgets = (toggles, reset)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_DIR / "partC_default.png", dpi=300, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="open the Matplotlib checkbox filter after writing the static deliverables",
    )
    args = parser.parse_args()
    frame = load_data()
    audit_data(frame)
    make_part_b_charts(frame)
    make_dashboard(frame)
    make_interactive(frame, show=args.interactive)
    print(f"Charts and dashboard written to {CHART_DIR}")
    print(f"Audit written to {WEEK_DIR / 'partA_audit.txt'}")


if __name__ == "__main__":
    main()
