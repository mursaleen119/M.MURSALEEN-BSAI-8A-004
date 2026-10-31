"""Adapt Weeks 4–6 to the repository's single Gapminder dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from solutions import ROOT, chart_path, load_data, run_single_week


COLORS = {
    "Africa": "#009E73",
    "Americas": "#CC79A7",
    "Asia": "#0072B2",
    "Europe": "#D55E00",
    "Oceania": "#E69F00",
}
SOURCE = "Source: data/gapminder.csv; 2007 panels use 142 countries; no source rows were deleted."

def chart_dir(week: int) -> Path:
    path = ROOT / f"weak-{week}" / "charts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(week: int, name: str, fig: plt.Figure) -> None:
    fig.text(.01, -.035, SOURCE, fontsize=7, color="#667085", ha="left", va="top")
    fig.savefig(chart_dir(week) / name, dpi=300, bbox_inches="tight")
    plt.close(fig)


def finish(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.7)
    ax.set_axisbelow(True)


def by_year(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("year", as_index=False).agg(
        lifeExp=("lifeExp", "mean"),
        population=("pop", "sum"),
        gdp=("gdp_total", "sum"),
    )


def week4(df: pd.DataFrame) -> None:
    """Time-series and composition adaptations, with unsupported claims named."""
    out = chart_dir(4)
    annual = by_year(df)
    continent = df.groupby(["year", "continent"], as_index=False).agg(
        lifeExp=("lifeExp", "mean"), population=("pop", "sum"),
        gdp=("gdp_total", "sum"))
    diagnoses: list[dict[str, object]] = []

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(annual.year, annual.lifeExp, marker="o", color="#0072B2")
    ax.set(title="Average life expectancy is shown in true calendar order",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    finish(ax)
    ax.text(.01, -.23, "Year strings and numeric years sort the same here; no false date order was found.",
            transform=ax.transAxes, fontsize=8)
    save(4, "week4_task01_dates.png", fig)
    diagnoses.append({"task": 1, "adaptation": "Calendar order; Gapminder uses numeric five-year steps, not malformed strings.",
                      "finding": "Lexical and numeric year order agree."})

    country = df[df.country == "Afghanistan"].sort_values("year")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(np.arange(len(country)), country.lifeExp, marker="o", color="#D55E00")
    axes[0].set(title="Row number hides the year units", xlabel="Recorded row", ylabel="Life expectancy (years)")
    axes[1].plot(country.year, country.lifeExp, marker="o", color="#0072B2")
    axes[1].set(title="Calendar axis keeps the five-year spacing", xlabel="Year", ylabel="Life expectancy (years)")
    for ax in axes:
        finish(ax)
    fig.suptitle("Country series: use the year, not the row index")
    save(4, "week4_task02_row_index.png", fig)
    diagnoses.append({"task": 2, "adaptation": "Compare row number with the actual year for one country's time series.",
                      "finding": "All steps are equally spaced, so the shape is unchanged; the year axis communicates the five-year unit."})

    continent_year = df.groupby(["year", "continent"])["pop"].agg(["sum", "mean"]).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for c, group in continent_year.groupby("continent"):
        axes[0].plot(group.year, group["sum"] / 1e6, marker="o", color=COLORS[c], label=c)
        axes[1].plot(group.year, group["mean"] / 1e6, marker="o", color=COLORS[c], label=c)
    axes[0].set(title="Summing population gives a continent total", xlabel="Year", ylabel="People (millions)")
    axes[1].set(title="Mean population answers a different question", xlabel="Year", ylabel="People per country (millions)")
    axes[0].legend(frameon=False, ncol=2)
    for ax in axes:
        finish(ax)
    fig.suptitle("Population is a stock: declare the aggregation")
    save(4, "week4_task03_stock_aggregation.png", fig)
    diagnoses.append({"task": 3, "adaptation": "Population is a stock, so show totals and per-country means separately.",
                      "finding": "A sum is a continent total, not a daily or monthly flow."})

    global_life = annual.set_index("year").lifeExp
    centered = global_life.rolling(3, center=True, min_periods=3).mean()
    trailing = global_life.rolling(3, min_periods=3).mean()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(global_life.index, global_life, marker="o", color="#AAB2BD", label="Observed")
    ax.plot(centered.index, centered, color="#0072B2", linewidth=2, label="Centered 3 observations")
    ax.plot(trailing.index, trailing, color="#D55E00", linewidth=2, label="Trailing 3 observations")
    ax.set(title="A trailing average uses only past observations", xlabel="Year", ylabel="Mean life expectancy (years)")
    ax.legend(frameon=False)
    finish(ax)
    save(4, "week4_task04_rolling_lag.png", fig)
    diagnoses.append({"task": 4, "adaptation": "Compare a centered and trailing 3-observation smoother.",
                      "finding": "The trailing curve ends later because it excludes future observations."})

    sensitivity: list[dict[str, object]] = []
    values = global_life.to_numpy()
    years = global_life.index.to_numpy()
    window_lengths = (3, 5, 7)
    for window in window_lengths:
        for start in range(len(values) - window + 1):
            slope = float(np.polyfit(years[start:start + window], values[start:start + window], 1)[0])
            sensitivity.append({"start_year": int(years[start]), "window_observations": window,
                                "slope_yearly": slope, "direction": "rising" if slope > 0 else "falling"})
    sens = pd.DataFrame(sensitivity)
    sens.to_csv(out / "week4_window_sensitivity.csv", index=False)
    counts = sens.direction.value_counts().to_dict()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(years, values, marker="o", color="#0072B2")
    ax.axvspan(1987, 2007, color="#E69F00", alpha=.18, label="Late window (shown for sensitivity)")
    ax.set(title="Changing the time window can change the fitted slope",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    ax.legend(frameon=False)
    finish(ax)
    save(4, "week4_task05_window_choice.png", fig)
    diagnoses.append({"task": 5, "adaptation": "Scan all available year starts and 3-, 5-, and 7-point windows.",
                      "finding": f"Window slopes: {counts.get('rising', 0)} rising, {counts.get('falling', 0)} falling."})

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for c, group in continent.groupby("continent"):
        ax.plot(group.year, group.population / 1e6, marker="o", color=COLORS[c], label=c)
    ax.set(title="Only recorded five-year observations are plotted",
           xlabel="Year", ylabel="Population (millions)")
    ax.legend(frameon=False, ncol=2)
    finish(ax)
    ax.text(.01, -.23, "No monthly extract or partial final month exists in this dataset.",
            transform=ax.transAxes, fontsize=8)
    save(4, "week4_task06_period_coverage.png", fig)
    diagnoses.append({"task": 6, "adaptation": "Check observed time coverage instead of inventing a partial month.",
                      "finding": "Gapminder records 12 five-year snapshots from 1952 to 2007."})

    wide_pop = continent.pivot(index="year", columns="continent", values="population")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.stackplot(wide_pop.index, *(wide_pop[c].to_numpy() / 1e6 for c in wide_pop.columns),
                 labels=wide_pop.columns, colors=[COLORS[c] for c in wide_pop.columns], alpha=.9)
    ax.set(title="Continent population is an exclusive composition of the world total",
           xlabel="Year", ylabel="Population (millions)")
    ax.legend(frameon=False, ncol=3, loc="upper left")
    save(4, "week4_task07_stacked_composition.png", fig)
    diagnoses.append({"task": 7, "adaptation": "Use continents as mutually exclusive population parts, not product lines.",
                      "finding": "The stacked total is world population; no volatility claim about products is made."})

    latest = df[df.year == df.year.max()].groupby("continent").gdp_total.sum().sort_values(ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    pie_parts = latest.nlargest(3).copy()
    pie_parts.loc["Other (2 continents)"] = latest.drop(index=pie_parts.index).sum()
    pie_colors = [COLORS[c] for c in pie_parts.index[:3]] + ["#9AA0A6"]
    axes[0].pie(pie_parts, labels=pie_parts.index, startangle=90, counterclock=False,
                colors=pie_colors)
    axes[0].set_title("Pie: four exclusive parts; Other is declared")
    latest.sort_values().plot.barh(ax=axes[1], color="#0072B2")
    axes[1].set(title="Bars: easier value comparisons", xlabel="GDP (current Gapminder units)", ylabel="")
    finish(axes[1])
    fig.suptitle("Continent GDP is exclusive; the bar is easier to compare")
    save(4, "week4_task08_pie_vs_bar.png", fig)
    diagnoses.append({"task": 8, "adaptation": "Compare legal continent GDP parts as a pie and sorted bars.",
                      "finding": "The five continent totals sum to the world total; bars improve ranking."})

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(annual.year, annual.gdp / 1e12, color="#0072B2", marker="o")
    axes[0].set(title="World GDP total", xlabel="Year", ylabel="GDP (trillion source units)")
    for c, group in continent.groupby("continent"):
        share = group.gdp / annual.set_index("year").gdp.reindex(group.year).to_numpy() * 100
        axes[1].plot(group.year, share, color=COLORS[c], label=c)
    axes[1].set(title="Continent shares of world GDP", xlabel="Year", ylabel="Share (%)")
    axes[1].legend(frameon=False, ncol=2)
    for ax in axes:
        finish(ax)
    fig.suptitle("A changing share is not the same as a falling total")
    save(4, "week4_task09_share_and_total.png", fig)
    diagnoses.append({"task": 9, "adaptation": "Show total GDP and continent GDP shares in separate panels.",
                      "finding": "Shares describe composition; the world total is not shown on a second axis."})

    chart_reasons = {
        1: "A line uses position on an ordered calendar axis to show a trend.",
        2: "Paired line panels isolate the same country series while making the x-axis units explicit.",
        3: "Two line panels separate total population from per-country mean; their units and questions differ.",
        4: "Observed values and rolling lines compare ordered time without hiding the window.",
        5: "A line shows the complete record; a computed window scan tests framing sensitivity.",
        6: "A line preserves the observed five-year sequence and makes absent monthly data explicit.",
        7: "A stacked area is legal because each country belongs to one continent and totals are additive.",
        8: "A four-slice pie shows the whole; sorted bars use length for precise ranking.",
        9: "Separate line panels avoid a dual axis while comparing world total and component shares.",
    }
    for row in diagnoses:
        row["chart_choice"] = chart_reasons[int(row["task"])]
    pd.DataFrame(diagnoses).to_csv(out / "week4_partA_diagnoses.csv", index=False)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].plot(annual.year, annual.lifeExp, marker="o", color="#AAB2BD")
    axes[0, 0].plot(annual.year, annual.lifeExp.rolling(3, center=True).mean(),
                    color="#0072B2", linewidth=2, label="Centered 3 observations")
    axes[0, 0].set(title="Global average life expectancy rises", xlabel="Year", ylabel="Years")
    axes[0, 0].legend(frameon=False)
    heat = continent.pivot(index="continent", columns="year", values="lifeExp")
    sns.heatmap(heat, ax=axes[0, 1], cmap="YlGnBu", cbar_kws={"label": "Mean life expectancy (years)"})
    axes[0, 1].set(title="The level differs by continent and year", xlabel="Year", ylabel="")
    shares = continent.pivot(index="year", columns="continent", values="gdp")
    shares = shares.div(shares.sum(axis=1), axis=0)
    axes[1, 0].stackplot(shares.index, *(shares[c].to_numpy() * 100 for c in shares.columns),
                         labels=shares.columns, colors=[COLORS[c] for c in shares.columns])
    axes[1, 0].set(title="Continent shares of world GDP", xlabel="Year", ylabel="Share (%)")
    axes[1, 0].legend(frameon=False, ncol=3, fontsize=7)
    latest_country = df[df.year == df.year.max()]
    sns.boxplot(data=latest_country, x="continent", y="lifeExp", hue="continent",
                palette=COLORS, legend=False, ax=axes[1, 1])
    axes[1, 1].set(title="Country life expectancy varies within continents",
                   xlabel="Continent", ylabel="Life expectancy (years)")
    for ax in (axes[0, 0], axes[1, 0]):
        finish(ax)
    fig.suptitle("Four questions from one country-year dataset", y=1.02)
    save(4, "week4_taskD_review_figure.png", fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for c, group in continent.groupby("continent"):
        ax.plot(group.year, group.lifeExp, marker="o", color=COLORS[c], label=c)
    ax.set(title="A cycle plot is not supported by 12 five-year snapshots",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    ax.legend(frameon=False, ncol=2)
    finish(ax)
    ax.text(.01, -.23, "Bonus adaptation: no monthly seasonal cycle or 18-month series is available.",
            transform=ax.transAxes, fontsize=8)
    save(4, "week4_taskF_cycle_limit.png", fig)

    (out / "week4_partE_justification.md").write_text(
        "# Week 4 written justification\n\n"
        "The chosen temporal unit is the recorded five-year observation. The source has no daily or hourly "
        "records, so the 3-observation smoother is declared as observations, not days. A centered window is "
        "for historical description; a live dashboard would require the trailing version and a lag warning. "
        "Continent totals are mutually exclusive parts of world totals. The treemap and product catalogue "
        "adaptation is not possible because Gapminder has no parent-child product hierarchy. No rows were "
        "removed. The optional cycle/decomposition task cannot meet its minimum monthly-history requirement.\n",
        encoding="utf-8")


def week5(df: pd.DataFrame) -> None:
    out = chart_dir(5)
    latest = df[df.year == df.year.max()].copy()
    latest["log_gdp"] = np.log10(latest.gdpPercap)
    diagnoses: list[dict[str, object]] = []

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    wrong_areas = .001 * (latest["pop"] / latest["pop"].min()) ** 2
    axes[0].scatter(latest.gdpPercap, latest.lifeExp, s=wrong_areas,
                    color="#0072B2", alpha=.65)
    axes[0].set_xscale("log")
    axes[0].set(title="Bad: population squared makes area explode", xlabel="GDP per capita (log scale)",
                ylabel="Life expectancy (years)")
    areas = latest["pop"] / latest["pop"].max() * 300
    axes[1].scatter(latest.gdpPercap, latest.lifeExp, s=areas,
                    color="#009E73", alpha=.65)
    axes[1].set_xscale("log")
    axes[1].set(title="Better: population is mapped to bounded area", xlabel="GDP per capita (log scale)",
                ylabel="Life expectancy (years)")
    for ax in axes:
        finish(ax)
    fig.suptitle("Population size belongs to area, not area squared")
    save(5, "week5_task01_bubble_area.png", fig)
    diagnoses.append({"task": 1, "adaptation": "GDP per capita, life expectancy and population replace health indicators.",
                      "finding": "Bubble area is bounded by an explicit size range; country population is not squared."})

    cont = latest.groupby("continent").agg(pop=("pop", "sum"), gdp_pc=("gdpPercap", "mean"))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    cont.sort_values("pop")["pop"].plot.barh(ax=axes[0], color="#0072B2")
    cont.sort_values("gdp_pc").gdp_pc.plot.barh(ax=axes[1], color="#D55E00")
    axes[0].set(title="Total population by continent", xlabel="People", ylabel="")
    axes[1].set(title="Mean GDP per person by continent", xlabel="GDP per capita", ylabel="")
    for ax in axes:
        finish(ax)
    fig.suptitle("Counts and per-person measures answer different questions")
    save(5, "week5_task02_count_vs_rate.png", fig)
    diagnoses.append({"task": 2, "adaptation": "Use population totals and GDP per capita; no outbreak count or district boundaries exist.",
                      "finding": "No choropleth or disease-rate claim can be made from this dataset."})

    mm = (latest.gdpPercap - latest.gdpPercap.min()) / (latest.gdpPercap.max() - latest.gdpPercap.min())
    rank = latest.gdpPercap.rank(pct=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].scatter(latest.gdpPercap, mm, color="#0072B2", alpha=.65)
    axes[0].set_xscale("log")
    axes[0].set(title="Min–max is compressed by the high-income tail", xlabel="GDP per capita (log scale)",
                ylabel="Min–max scaled GDP per capita")
    axes[1].scatter(latest.gdpPercap, rank, color="#D55E00", alpha=.65)
    axes[1].set_xscale("log")
    axes[1].set(title="Percentile rank preserves ordering", xlabel="GDP per capita (log scale)",
                ylabel="Percentile rank")
    for ax in axes:
        finish(ax)
    save(5, "week5_task03_scaling.png", fig)
    diagnoses.append({"task": 3, "adaptation": "Show GDP per capita scaling and the effect of a high outlier.",
                      "finding": f"Min–max median={mm.median():.3f}; percentile-rank median={rank.median():.3f}."})

    features = ["lifeExp", "pop", "gdpPercap", "gdp_total"]
    table = latest[features].copy()
    table["log_population"] = np.log10(table["pop"])
    table["log_gdp_per_capita"] = np.log10(table.gdpPercap)
    ordered = ["lifeExp", "gdpPercap", "pop", "gdp_total"]
    corr = table[ordered].corr().abs()
    chain = [ordered[0]]
    while len(chain) < len(ordered):
        chain.append(corr[chain[-1]].drop(labels=chain).idxmax())
    def pcp_order(cols: list[str], axis: plt.Axes, title: str) -> None:
        scaled = latest[cols].apply(lambda s: (s - s.min()) / (s.max() - s.min()))
        for row in scaled.to_numpy():
            axis.plot(range(len(cols)), row, color="#9AA0A6", alpha=.16, linewidth=.7)
        axis.set_xticks(range(len(cols)), cols, rotation=20)
        axis.set(title=title, ylabel="Min–max scaled values")
        finish(axis)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    pcp_order(ordered, axes[0], "File-inspired order separates associations")
    pcp_order(chain, axes[1], "Greedy correlation chain puts related axes together")
    fig.suptitle(f"Parallel coordinates; greedy order: {' → '.join(chain)}")
    save(5, "week5_task04_parallel_coordinates.png", fig)
    diagnoses.append({"task": 4, "adaptation": "Compare numeric-axis order in a parallel-coordinates chart.",
                      "finding": f"Greedy correlation order: {' -> '.join(chain)}."})

    cuts = latest.lifeExp.quantile([.2, .4, .6, .8]).to_numpy()
    latest["life_class"] = pd.cut(latest.lifeExp, [-np.inf, *cuts, np.inf],
                                  labels=["Q1", "Q2", "Q3", "Q4", "Q5"], include_lowest=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(latest.gdpPercap, latest.lifeExp,
               c=latest.lifeExp.rank(pct=True), cmap="YlGnBu", s=38)
    ax.set_xscale("log")
    ax.set(title="Quantile colours split countries even when values are close",
           xlabel="GDP per capita (log scale)", ylabel="Life expectancy (years)")
    fig.colorbar(ax.collections[0], ax=ax, label="Life expectancy percentile")
    finish(ax)
    save(5, "week5_task05_quantiles.png", fig)
    diagnoses.append({"task": 5, "adaptation": "Quantile-classify the observed life-expectancy values, not disease rates.",
                      "finding": f"Range={latest.lifeExp.min():.1f}–{latest.lifeExp.max():.1f} years; classes are not evidence of five natural groups."})

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(latest["pop"], latest.gdpPercap, color="#AAB2BD", alpha=.6)
    small = latest.nsmallest(10, "pop")
    ax.scatter(small["pop"], small.gdpPercap, color="#D55E00", label="10 smallest populations")
    for _, row in small.nlargest(3, "gdpPercap").iterrows():
        ax.annotate(row["country"], (row["pop"], row.gdpPercap), fontsize=7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set(title="Small population alone does not prove a rate is unstable",
           xlabel="Population (people, log scale)", ylabel="GDP per capita (log scale)")
    ax.legend(frameon=False)
    finish(ax)
    save(5, "week5_task06_denominator_caution.png", fig)
    diagnoses.append({"task": 6, "adaptation": "Use population size to discuss denominator caution, not a fabricated disease rate.",
                      "finding": "No case counts or Poisson rate estimates are available."})

    country_r = latest[["gdpPercap", "lifeExp"]].corr().iloc[0, 1]
    continent_latest = latest.groupby("continent")[["gdpPercap", "lifeExp"]].mean()
    continent_r = continent_latest.corr().iloc[0, 1]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    sns.regplot(data=latest, x="gdpPercap", y="lifeExp", ax=axes[0],
                scatter_kws={"alpha": .35, "s": 20}, line_kws={"color": "#D55E00"})
    axes[0].set_xscale("log")
    axes[0].set_title(f"Country level: r={country_r:.2f} (n={len(latest)})")
    continent_latest.plot.scatter(x="gdpPercap", y="lifeExp", ax=axes[1], color="#0072B2", s=60)
    axes[1].set_xscale("log")
    axes[1].set_title(f"Continent means: r={continent_r:.2f} (n={len(continent_latest)})")
    for ax in axes:
        finish(ax)
    fig.suptitle("Aggregation changes the unit of analysis")
    save(5, "week5_task07_scale_correlation.png", fig)
    diagnoses.append({"task": 7, "adaptation": "Compare country and continent-mean association of GDP and life expectancy.",
                      "finding": f"Country r={country_r:.3f}; continent-mean r={continent_r:.3f}."})

    fig, ax = plt.subplots(figsize=(8, 4.5))
    cont.sort_values("pop")["pop"].plot.barh(ax=ax, color="#0072B2")
    ax.set(title="Population by continent is not a map of land area",
           xlabel="People (latest year)", ylabel="Continent")
    finish(ax)
    ax.text(.01, -.23, "Gapminder has no country coordinates or polygon boundaries; no geographic map is inferred.",
            transform=ax.transAxes, fontsize=8)
    save(5, "week5_task08_no_geometry.png", fig)
    diagnoses.append({"task": 8, "adaptation": "Replace the land-area choropleth with a categorical population comparison.",
                      "finding": "No area share, map projection, or geographic hotspot can be computed."})

    profile = latest.groupby("continent").agg(
        lifeExp=("lifeExp", "mean"), lifeExp_median=("lifeExp", "median"),
        gdp=("gdpPercap", "mean"), gdp_median=("gdpPercap", "median"),
        population=("pop", "mean"), population_median=("pop", "median"))
    profile_scaled = (profile - profile.min()) / (profile.max() - profile.min()) * 100
    names = list(profile_scaled.columns)
    first, second = "Europe", "Africa"
    def radar_values(order: list[str]) -> tuple[list[float], list[float]]:
        return (profile_scaled.loc[first, order].tolist(), profile_scaled.loc[second, order].tolist())
    def polygon_area(values: list[float]) -> float:
        angle = np.linspace(0, 2 * np.pi, len(values), endpoint=False)
        x = np.asarray(values) * np.cos(angle)
        y = np.asarray(values) * np.sin(angle)
        return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)
    orders = [names, names[2:] + names[:2]]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), subplot_kw={"projection": "polar"})
    area_rows = []
    for ax, order in zip(axes, orders):
        angles = np.linspace(0, 2 * np.pi, len(order), endpoint=False).tolist()
        a, b = radar_values(order)
        for values, color, label in ((a, "#0072B2", first), (b, "#D55E00", second)):
            vals = values + [values[0]]
            ax.plot(angles + [angles[0]], vals, color=color, label=label)
            ax.fill(angles + [angles[0]], vals, color=color, alpha=.12)
        ax.set_xticks(angles, order, fontsize=7)
        ax.set_ylim(0, 100)
        ax.set_title("Order: " + ", ".join(order[:2]) + " …")
        area_rows.append({"axis_order": " | ".join(order),
                          "Europe_polygon_area": polygon_area(a),
                          "Africa_polygon_area": polygon_area(b)})
    axes[0].legend(frameon=False, loc="upper right", bbox_to_anchor=(1.35, 1.15))
    fig.suptitle("Radar area changes when the axis order changes")
    save(5, "week5_task09_radar_order.png", fig)
    pd.DataFrame(area_rows).to_csv(out / "week5_radar_area_by_order.csv", index=False)
    diagnoses.append({"task": 9, "adaptation": "Compare continent profiles on six normalized Gapminder indicators.",
                      "finding": "Radar polygon area depends on axis order; it is not a reliable overall score."})
    chart_reasons = {
        1: "Scatterplot position compares two numeric measures; population is the bubble area.",
        2: "Sorted horizontal bars compare continent categories without implying geographic shape.",
        3: "A scatterplot shows GDP per capita against its scaled value.",
        4: "Parallel coordinates show multiple numeric measures and make order effects visible.",
        5: "A sequential colour scale encodes ordered life-expectancy percentiles.",
        6: "A log-scaled scatter shows population and GDP per person without calling either a disease rate.",
        7: "Paired scatterplots keep country-level and continent-level associations distinct.",
        8: "A sorted bar chart compares categories because no spatial geometry is available.",
        9: "A radar chart is retained only to demonstrate its area/order limitation, not to rank regions.",
    }
    for row in diagnoses:
        row["chart_choice"] = chart_reasons[int(row["task"])]
    pd.DataFrame(diagnoses).to_csv(out / "week5_partA_diagnoses.csv", index=False)

    feature_cols = ["year", "lifeExp", "pop", "gdpPercap", "gdp_total"]
    matrix = df[feature_cols].copy()
    matrix["pop"] = np.log1p(matrix["pop"])
    matrix["gdpPercap"] = np.log1p(matrix["gdpPercap"])
    matrix["gdp_total"] = np.log1p(matrix["gdp_total"])
    standardized = (matrix - matrix.mean()) / matrix.std(ddof=0)
    _, singular, _ = np.linalg.svd(standardized.to_numpy(), full_matrices=False)
    variance = singular**2 / np.sum(singular**2)
    pd.DataFrame({"component": np.arange(1, len(variance) + 1),
                  "explained_variance": variance}).to_csv(out / "week5_pca_variance.csv", index=False)
    min_area = float(300 * latest["pop"].min() / latest["pop"].max())
    diameter_ratio = float(np.sqrt(latest["pop"].max() / latest["pop"].min()))
    gdp_z = (latest.gdpPercap - latest.gdpPercap.mean()) / latest.gdpPercap.std(ddof=0)
    (out / "week5_partB_decisions.md").write_text(
        "# Week 5 computed decisions\n\n"
        f"- Bubble area is directly proportional to population, with a maximum of 300 points squared and a minimum "
        f"area of {min_area:.2f}; the diameter ratio is `sqrt(max population / min population) = {diameter_ratio:.2f}`. "
        "Small marks are hard to read, so the companion bars are important.\n"
        "- Overplotting uses the 142 countries available in 2007 (alpha 0.22, hexbin gridsize 20, and a 2-D KDE). "
        "The brief's 9,000 points and planted 800-point cluster do not exist in this one dataset.\n"
        f"- For 2007 GDP per capita, min–max median={mm.median():.3f}, z-score median={gdp_z.median():.3f}, "
        f"and percentile-rank median={rank.median():.3f}.\n"
        f"- PCA uses five declared numeric features after log-transforming population and GDP columns; the first "
        f"two components explain {variance[:2].sum():.1%} of standardized variance.\n"
        "- District polygons, county rates, a small-area Poisson funnel and projected land areas cannot be "
        "computed without adding another dataset, so those results are not fabricated.\n",
        encoding="utf-8")

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    axes[0, 0].scatter(latest.gdpPercap, latest.lifeExp, color="#AAB2BD", alpha=.8, s=18)
    axes[0, 0].set_xscale("log")
    axes[0, 0].set(title="Opaque country marks", xlabel="GDP per capita (log)", ylabel="Life expectancy (years)")
    axes[0, 1].scatter(latest.gdpPercap, latest.lifeExp, color="#0072B2", alpha=.22, s=20)
    axes[0, 1].set_xscale("log")
    axes[0, 1].set(title="Transparency reveals density (alpha=.22)", xlabel="GDP per capita (log)", ylabel="Years")
    hb = axes[1, 0].hexbin(np.log10(latest.gdpPercap), latest.lifeExp, gridsize=20,
                           cmap="YlGnBu", mincnt=1)
    axes[1, 0].set(title="Hexbin (gridsize=20)", xlabel="log10 GDP per capita", ylabel="Years")
    fig.colorbar(hb, ax=axes[1, 0], label="Countries per hexagon")
    sns.kdeplot(x=np.log10(latest.gdpPercap), y=latest.lifeExp, fill=True, levels=8,
                cmap="YlGnBu", ax=axes[1, 1])
    axes[1, 1].set(title="2-D KDE: estimated density", xlabel="log10 GDP per capita", ylabel="Years")
    for ax in axes.flat:
        finish(ax)
    fig.suptitle("Overplotting methods on native Gapminder rows (n=142, not 9,000)")
    save(5, "week5_taskB_overplotting.png", fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    axes[0, 0].scatter(latest.gdpPercap, latest.lifeExp, s=areas, c="#0072B2", alpha=.55)
    axes[0, 0].set_xscale("log")
    axes[0, 0].set(title="Bubble chart: position first, area for population",
                   xlabel="GDP per capita (log scale)", ylabel="Life expectancy (years)")
    for population in [latest["pop"].min(), latest["pop"].median(), latest["pop"].max()]:
        marker_area = population / latest["pop"].max() * 300
        axes[0, 0].scatter([], [], s=marker_area, color="#0072B2", alpha=.55,
                           label=f"{population:.1f} million")
    axes[0, 0].legend(title="Population (area)", frameon=False, fontsize=7)
    pcp_order(chain, axes[0, 1], "Parallel coordinates: min–max; declared axis order")
    axes[1, 0].bar(["PC1", "PC2", "PC3", "PC4", "PC5"], variance, color="#009E73")
    axes[1, 0].set(title=f"Two components retain {variance[:2].sum():.1%}",
                   ylabel="Explained variance")
    finish(axes[1, 0])
    cont.sort_values("gdp_pc").gdp_pc.plot.barh(ax=axes[1, 1], color="#D55E00")
    axes[1, 1].set(title="Geography replaced: no boundary data", xlabel="Mean GDP per capita", ylabel="")
    finish(axes[1, 1])
    fig.suptitle("Three multivariate views and one honest geography limitation")
    save(5, "week5_taskD_three_figures.png", fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for c, group in latest.groupby("continent"):
        ax.scatter(group.gdpPercap, group.lifeExp,
                   s=group["pop"] / latest["pop"].max() * 300,
                   color=COLORS[c], alpha=.62, label=c)
    ax.set_xscale("log")
    ax.set(title="Higher income aligns with higher life expectancy across countries",
           xlabel="GDP per capita (log scale)", ylabel="Life expectancy (years)")
    for population in [latest["pop"].min(), latest["pop"].median(), latest["pop"].max()]:
        ax.scatter([], [], s=population / latest["pop"].max() * 300,
                   color="#667085", alpha=.55, label=f"{population:.1f} million")
    ax.legend(frameon=False, ncol=2, fontsize=7, title="Continent / population area")
    finish(ax)
    save(5, "week5_partD_bubble.png", fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    scaled = latest[chain].apply(lambda s: (s - s.min()) / (s.max() - s.min()))
    for index, row in latest.iterrows():
        values = scaled.loc[index]
        ax.plot(range(len(chain)), values, color="#AAB2BD", alpha=.18, linewidth=.7)
        if row.continent == "Asia":
            ax.plot(range(len(chain)), values, color=COLORS["Asia"], alpha=.75, linewidth=.8)
    ax.set_xticks(range(len(chain)), chain, rotation=15)
    ax.set(title="Asia is brushed over grey country context",
           xlabel=f"Min–max axes; order: {' → '.join(chain)}",
           ylabel="Scaled value (unitless)")
    finish(ax)
    save(5, "week5_partD_parallel_coordinates.png", fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    continent_gdp_pc = latest.groupby("continent").gdpPercap.mean().sort_values()
    continent_gdp_pc.plot.barh(ax=ax, color="#0072B2")
    ax.set(title="Continent comparison replaces a map when boundaries are absent",
           xlabel="Mean GDP per capita (source units)", ylabel="")
    finish(ax)
    ax.text(.01, -.23, "Categorical comparison only; no coordinates, polygons, or map projection are available.",
            transform=ax.transAxes, fontsize=8)
    save(5, "week5_partD_geography_adaptation.png", fig)

    (out / "week5_partE_justification.md").write_text(
        "# Week 5 written justification\n\n"
        "Position carries GDP per capita and life expectancy because those are the main comparisons; population "
        "uses bounded area with a visible legend note. Parallel-coordinate axes are min–max scaled and ordered "
        "by a greedy absolute-correlation chain; the order is printed above the plot. A geographic rate map, "
        "equal-area projection, district class breaks, land shares, county experiment and small-area funnel "
        "cannot be produced: this one-source repository contains no polygons, coordinates, disease counts or "
        "reader responses. Continent bars are explicitly categorical, not maps. No participant results are invented.\n",
        encoding="utf-8")


def week6(df: pd.DataFrame) -> None:
    out = chart_dir(6)
    raw = pd.read_csv(ROOT / "data" / "gapminder.csv")
    expected = {"country", "continent", "year", "lifeExp", "pop", "gdpPercap"}
    if set(raw.columns) != expected:
        raise ValueError(f"Unexpected Gapminder columns: {sorted(raw.columns)}")
    keys = raw[["country", "year"]]
    audit = [
        f"Rows: {len(raw)}",
        f"Columns: {', '.join(raw.columns)}",
        "Dtypes: " + "; ".join(f"{name}={kind}" for name, kind in raw.dtypes.items()),
        f"Duplicate country-year keys: {int(keys.duplicated().sum())}",
        f"Missing cells: {int(raw.isna().sum().sum())}",
        f"Unique countries: {raw.country.nunique()}",
        f"Years: {int(raw.year.min())}–{int(raw.year.max())}",
        f"Year steps: {sorted(raw.year.drop_duplicates().sort_values().diff().dropna().astype(int).unique().tolist())}",
        f"Sentinel values among numeric fields: {int(raw.select_dtypes('number').isin([-1, 999, 9999]).sum().sum())}",
        "Numeric ranges: " + "; ".join(
            f"{name}={raw[name].min()}..{raw[name].max()}"
            for name in raw.select_dtypes("number").columns
        ),
        "Join misses: not applicable (no geographic boundary or external table)",
        "Decision: no rows changed; source is complete and has one unique country-year record.",
    ]
    (out / "week6_audit.txt").write_text("\n".join(audit) + "\n", encoding="utf-8")
    year = by_year(df)
    continents = df.groupby(["year", "continent"], as_index=False).agg(
        lifeExp=("lifeExp", "mean"), pop=("pop", "sum"),
        gdp=("gdp_total", "sum"))
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    axes[0].plot(year.year, year.lifeExp, marker="o", color="#0072B2")
    axes[0].set(title="Trend: mean life expectancy rises", xlabel="Year", ylabel="Years")
    latest_cont = continents[continents.year == continents.year.max()].sort_values("gdp")
    axes[1].barh(latest_cont.continent, latest_cont.gdp / 1e12,
                 color=[COLORS[c] for c in latest_cont.continent])
    axes[1].set(title="Composition: GDP total by continent", xlabel="GDP (trillion source units)", ylabel="")
    axes[2].scatter(np.log10(df.gdpPercap), df.lifeExp, c=df.year,
                    cmap="viridis", s=18, alpha=.55)
    axes[2].set(title="Relationship: income and life expectancy", xlabel="GDP per capita (log10)", ylabel="Years")
    fig.colorbar(axes[2].collections[0], ax=axes[2], label="Year")
    for ax in axes[:2]:
        finish(ax)
    fig.suptitle("Three different questions from one audited dataset")
    save(6, "week6_taskB_three_questions.png", fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    for c, group in continents.groupby("continent"):
        ax.plot(group.year, group.lifeExp, marker="o", color=COLORS[c], label=c)
    ax.set(title="Every continent gained life expectancy in the long run",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    ax.legend(frameon=False, ncol=2)
    finish(ax)
    ax.text(.01, -.22, "Reader: public-health board. Historical global averages are not local forecasts.",
            transform=ax.transAxes, fontsize=8)
    save(6, "week6_taskC_board_figure.png", fig)

    (out / "week6_decisions.md").write_text(
        "# Week 6 decisions\n\n"
        "The data audit found no missing values, duplicate country-year keys, sentinel codes, or calendar "
        "irregularities. I kept all 1,704 rows and did not write a second CSV, so the repository still has "
        "exactly one copy of the source dataset. The instructor's district, meter, generation-mix and GeoJSON "
        "defects cannot be reproduced from Gapminder; I report the checks that apply and do not invent defects. "
        "The board figure answers the adapted question: how did average life expectancy change across continents? "
        "It is not a claim about electricity reliability or renewable generation.\n",
        encoding="utf-8")

    rows = []
    for c, group in continents.groupby("continent"):
        rows.append({"year": group.year.astype(int).tolist(),
                     "lifeExp": group.lifeExp.round(2).tolist(), "continent": c})
    html = """<!doctype html><meta charset="utf-8"><title>Gapminder interactive trends</title>
<h1>Explore life expectancy by continent</h1>
<label>Show continent <select id="group"><option value="all">All</option></select></label>
<svg id="chart" viewBox="0 0 900 440" role="img" aria-label="Life expectancy over time"></svg>
<p>Hover a point for its year and value. Select one continent to focus the comparison.</p>
<script>
const data = DATA_PLACEHOLDER, svg=document.getElementById('chart'), select=document.getElementById('group');
const ns='http://www.w3.org/2000/svg', colors={Africa:'#009E73',Americas:'#CC79A7',Asia:'#0072B2',Europe:'#D55E00',Oceania:'#E69F00'};
data.forEach(d=>{const o=document.createElement('option');o.value=d.continent;o.textContent=d.continent;select.append(o)});
function draw(){svg.innerHTML='';const W=900,H=440,L=65,R=20,T=20,B=55,x0=1952,x1=2007,y0=20,y1=85;
const X=x=>L+(x-x0)/(x1-x0)*(W-L-R),Y=y=>H-B-(y-y0)/(y1-y0)*(H-T-B);
for(let y=20;y<=80;y+=10){const line=document.createElementNS(ns,'line');line.setAttribute('x1',L);line.setAttribute('x2',W-R);line.setAttribute('y1',Y(y));line.setAttribute('y2',Y(y));line.setAttribute('stroke','#ddd');svg.append(line)}
data.filter(d=>select.value==='all'||d.continent===select.value).forEach(d=>{const p=document.createElementNS(ns,'polyline');p.setAttribute('fill','none');p.setAttribute('stroke',colors[d.continent]);p.setAttribute('stroke-width','2.5');p.setAttribute('points',d.year.map((v,i)=>`${X(v)},${Y(d.lifeExp[i])}`).join(' '));svg.append(p);
d.year.forEach((v,i)=>{const c=document.createElementNS(ns,'circle');c.setAttribute('cx',X(v));c.setAttribute('cy',Y(d.lifeExp[i]));c.setAttribute('r','4');c.setAttribute('fill',colors[d.continent]);const t=document.createElementNS(ns,'title');t.textContent=`${d.continent}, ${v}: ${d.lifeExp[i]} years`;c.append(t);svg.append(c)})});
}
select.addEventListener('change',draw);draw();
</script>""".replace("DATA_PLACEHOLDER", json.dumps(rows, separators=(",", ":")))
    (out / "week6_interactive.html").write_text(html, encoding="utf-8")


WEEK_META: dict[int, dict[str, object]] = {
    1: {
        "tasks": [
            ("Task 1 — Summary and shape", "Gapminder has one real dataset rather than 13 matched-statistic datasets. Country variation and continent summaries are compared honestly.", ["week1_task1_country_variation.png", "week1_task1_continent_statistics.csv"]),
            ("Task 2 — Trends and spaghetti", "The 142-country plot is compared with continent averages and selected-country highlights; GDP per capita uses a log axis.", ["week1_task2_bad_spaghetti.png", "week1_task2_continent_trends.png", "week1_task2_highlights.png", "week1_task2_income_gap.png"]),
            ("Task 3 — Distribution and relationships", "Life expectancy and income distributions and relationships are shown by continent; no penguin fields or missing records are claimed.", ["week1_task3_distribution.png", "week1_task3_relationship.png"]),
            ("Task 4 — Five chart choices", "Five distinct questions use time, category, relationship, distribution and grouped comparisons, followed by a redesign.", ["week1_task4_trend.png", "week1_task4_comparison.png", "week1_task4_relationship.png", "week1_task4_income_distribution.png", "week1_task4_mechanism.png", "week1_task4_redesign.png"]),
            ("Task 5 — Time series", "Country-year records are correctly ordered; the notebook separates trend and repeated observation patterns.", ["week1_task5_time_series.png"]),
        ],
    },
    2: {
        "tasks": [
            ("Task 1 — Preattentive search", "A Gapminder-derived visual comparison is provided. Reaction times require a real reader and remain uncollected; see reader_protocol.md.", ["week2_task1_preattentive.png"]),
            ("Task 2 — Gestalt grouping", "Six grouping ideas and a connection-versus-similarity display are adapted; perceived group counts remain pending.", ["week2_task2_gestalt.png", "week2_task2_connection_test.png"]),
            ("Task 3 — Cognitive load", "A deliberately labelled bad example is compared with a less cluttered view and a chunked summary.", ["week2_task3_bad_example.png", "week2_task3_reduction.png", "week2_task3_chunking.png"]),
            ("Task 4 — Channel effectiveness", "Position, length and area are compared visually; reader estimates are not fabricated.", ["week2_task4_channels.png"]),
            ("Task 5 — Capstone redesign", "One message is highlighted with muted context and a perception audit; human interpretation remains pending.", ["week2_task5_redesign.png"]),
        ],
    },
    3: {
        "tasks": [
            ("Task 1 — Nine chart diagnoses", "Nine original case datasets are replaced with measurable Gapminder chart decisions; limitations and redesigns are recorded.", ["week3_partA_gallery.png", "week3_partA_diagnoses.csv", "week3_case01_baseline.png", "week3_case02_scale_bad.png", "week3_case02_scale_redesign.png", "week3_case03_bins_bad.png", "week3_case03_bins_redesign.png", "week3_case04_crowding.png", "week3_case05_heatmap_bad.png", "week3_case06_dual_axis_bad.png", "week3_case06_dual_axis_redesign.png", "week3_case07_bar_redesign.png", "week3_case07_pie_bad.png", "week3_case08_kde_bad.png", "week3_case09_grouping.png"]),
            ("Task 2 — Lie Factor", "Where a comparable geometric encoding exists, the calculation is shown; cases with no comparable baseline are identified.", ["week3_partB_lie_factor.csv"]),
            ("Task 3 — Palette audit", "The palette is simulated for common colour-vision deficiencies and measured for close pairs.", ["week3_partC_palette.png", "week3_partC_palette_audit.csv"]),
            ("Task 4 — Review figure", "A multi-panel country-year review figure is built with labeled units and no dual axes.", ["week3_partD_development_review.png"]),
            ("Task 5 — Written justification", "The design choices and the limits of adapting clinical variables to Gapminder are stated.", ["week3_partE_justification.md"]),
        ],
    },
    4: {
        "tasks": [
            ("Task 1 — Nine time and composition cases", "Nine adaptations use Gapminder's observed country-year timeline and continent compositions.", [f"week4_task{i:02d}_{name}.png" for i, name in [(1,"dates"),(2,"row_index"),(3,"stock_aggregation"),(4,"rolling_lag"),(5,"window_choice"),(6,"period_coverage"),(7,"stacked_composition"),(8,"pie_vs_bar"),(9,"share_and_total")]] + ["week4_partA_diagnoses.csv"]),
            ("Task 2 — Windows and trend sensitivity", "A computed scan compares possible windows and reports their slope directions; units are observations, not days.", ["week4_task05_window_choice.png", "week4_window_sensitivity.csv"]),
            ("Task 3 — Part-to-whole legality", "Continent GDP shares are checked as exclusive parts; the pie is compared with a sorted bar. Real-reader ranking remains pending; see reader_protocol.md.", ["week4_task08_pie_vs_bar.png"]),
            ("Task 4 — Four-panel review figure", "The adapted dashboard shows a time trend, continent-year heatmap, GDP composition, and country distribution.", ["week4_taskD_review_figure.png"]),
            ("Task 5 — Written justification", "Time decisions, the missing product hierarchy, and non-applicable exclusions are documented.", ["week4_partE_justification.md"]),
            ("Task 6 — Bonus cycle plot", "The notebook shows why 12 five-year snapshots cannot support an 18-month seasonal decomposition.", ["week4_taskF_cycle_limit.png"]),
        ],
    },
    5: {
        "tasks": [
            ("Task 1 — Nine multivariate diagnoses", "Nine adaptations use population, GDP per capita, life expectancy and continent; geography-specific claims are not fabricated.", [f"week5_task{i:02d}_{name}.png" for i, name in [(1,"bubble_area"),(2,"count_vs_rate"),(3,"scaling"),(4,"parallel_coordinates"),(5,"quantiles"),(6,"denominator_caution"),(7,"scale_correlation"),(8,"no_geometry"),(9,"radar_order")]] + ["week5_partA_diagnoses.csv"]),
            ("Task 2 — Five channel and spatial decisions", "Bubble area, overplotting, scaling and PCA are computed; projections and small-area funnels are marked unavailable without geometry or counts.", ["week5_taskB_overplotting.png", "week5_taskD_three_figures.png", "week5_partB_decisions.md", "week5_pca_variance.csv"]),
            ("Task 3 — Two-map reader activity", "A reader protocol is supplied, but no map or participant results are claimed because the dataset has no boundaries; see reader_protocol.md.", ["week5_task08_no_geometry.png"]),
            ("Task 4 — Three multivariate figures", "Bubble, parallel-coordinate and continent comparison views are built; the final panel is not mislabelled as a map.", ["week5_partD_bubble.png", "week5_partD_parallel_coordinates.png", "week5_partD_geography_adaptation.png"]),
            ("Task 5 — Written justification", "Encoding choices and the geography limitation are documented.", ["week5_partE_justification.md"]),
            ("Task 6 — Bonus normalized map", "A choropleth cannot be made from Gapminder without a second dataset, so the single-dataset rule is preserved.", ["week5_partE_justification.md"]),
        ],
    },
    6: {
        "tasks": [
            ("Task 1 — Audit the source", "Gapminder's actual keys, missingness, sentinels, date coverage and ranges are audited without modifying the sole source file.", ["week6_audit.txt"]),
            ("Task 2 — Three chart questions", "A trend, a composition comparison and a relationship are answered in a single figure.", ["week6_taskB_three_questions.png"]),
            ("Task 3 — Board figure", "A public-health audience sees how life expectancy changed across continents; it is not an electricity-grid claim.", ["week6_taskC_board_figure.png", "week6_decisions.md"]),
            ("Task 4 — Bonus interaction", "A local HTML chart supports filtering by continent and hovering over year-level values.", ["week6_interactive.html"]),
        ],
    },
}


def week_for(week: int, df: pd.DataFrame) -> None:
    if week <= 3:
        run_single_week(week)
    elif week == 4:
        week4(df)
    elif week == 5:
        week5(df)
    elif week == 6:
        week6(df)
    else:
        raise ValueError(f"Expected a week from 1 to 6, got {week}.")


def build_notebook(week: int) -> None:
    meta = WEEK_META[week]
    cells: list[dict[str, object]] = [{
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            f"# Week {week} — Gapminder solution\n\n",
            "Student: M. Mursaleen · BSAI 8A · Roll/ID 004\n\n",
            "This notebook uses the repository's one source dataset, `data/gapminder.csv`. "
            "Each task includes its adaptation and the figures are exported to this folder's `charts/`. "
            "Reader experiments are left pending until real people take part.\n",
        ],
    }, {
        "cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
        "source": [
            "from pathlib import Path\n",
            "import sys\n",
            "import pandas as pd\n",
            "from IPython.display import Image, display\n",
            "ROOT = Path.cwd()\n",
            "if not (ROOT / 'coursework' / 'weekly_coursework.py').exists(): ROOT = ROOT.parent\n",
            "sys.path.insert(0, str(ROOT / 'coursework'))\n",
            "from solutions import load_data\n",
            "from weekly_coursework import week_for\n",
            f"df = load_data()\nweek_for({week}, df)\n",
        ],
    }]
    for index, (title, description, files) in enumerate(meta["tasks"], start=1):
        cells.append({
            "cell_type": "markdown", "metadata": {},
            "source": [f"## Task {index} — {title}\n\n", f"{description}\n"],
        })
        if files:
            lines = ["from IPython.display import Image, display\n"]
            for file in files:
                target = chart_path(file) if week <= 3 else chart_dir(week) / file
                if target.suffix.lower() == ".png":
                    lines.append(f"display(Image(filename=str(ROOT / {f'weak-{week}'!r} / 'charts' / {file!r})))\n")
                elif target.suffix.lower() == ".csv":
                    lines.append(f"display(pd.read_csv(ROOT / {f'weak-{week}'!r} / 'charts' / {file!r}))\n")
                else:
                    lines.append(f"print((ROOT / {f'weak-{week}'!r} / 'charts' / {file!r}).read_text(encoding='utf-8'))\n")
            cells.append({
                "cell_type": "code", "execution_count": None, "metadata": {},
                "outputs": [], "source": lines,
            })
        else:
            cells.append({
                "cell_type": "code", "execution_count": None, "metadata": {},
                "outputs": [], "source": [
                    "print('Written notes are in this week folder. No participant response or unsupported map is invented.')\n",
                ],
            })
    path = ROOT / f"weak-{week}" / f"weak-{week}_solution.ipynb"
    path.parent.mkdir(parents=True, exist_ok=True)
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": sys.version.split()[0]},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def build_week_readme(week: int) -> None:
    tasks = WEEK_META[week]["tasks"]
    lines = [f"# Week {week} solution\n", "\n",
             "Dataset: [`../data/gapminder.csv`](../data/gapminder.csv). "
             "Task-specific dataset differences are noted in the notebook; no other source dataset is added.\n\n",
             f"Notebook: [`weak-{week}_solution.ipynb`](weak-{week}_solution.ipynb)\n\n",
             "## Tasks\n\n"]
    for index, (title, description, _files) in enumerate(tasks, start=1):
        lines.extend([f"{index}. **{title}** — {description}\n"])
    lines.extend(["\n## Charts and files\n\n",
                  "Figures and audit artifacts are saved under [`charts/`](charts/). "
                  "Human-participant tasks are not marked complete until real responses are collected.\n"])
    protocol = ROOT / f"weak-{week}" / "reader_protocol.md"
    if protocol.exists():
        lines.extend(["\nReader collection notes: [`reader_protocol.md`](reader_protocol.md).\n"])
    (ROOT / f"weak-{week}" / f"weak-{week}_README.md").write_text("".join(lines), encoding="utf-8")


def build_all() -> None:
    df = load_data()
    for week in range(1, 7):
        week_for(week, df)
        build_notebook(week)
        build_week_readme(week)
    print("Built adapted week folders 1–6 from the single Gapminder dataset.")


if __name__ == "__main__":
    build_all()
