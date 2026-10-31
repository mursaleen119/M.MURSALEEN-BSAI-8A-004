"""Complete Weeks 1–3 using one source dataset: Gapminder."""

from __future__ import annotations

import base64
import json
import sys
import time
from io import BytesIO
from pathlib import Path

import matplotlib
from PIL import Image as PILImage

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Ellipse
import numpy as np
import pandas as pd
import seaborn as sns

from vizlib import PALETTE, lie_factor, lie_verdict, save_fig, simulate_cvd, style_defaults, worst_pair


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "gapminder.csv"
OUT = ROOT / "outputs"
COURSEWORK = ROOT / "coursework"
OUT.mkdir(exist_ok=True)
style_defaults()

COLORS = {
    "Asia": "#0072B2",
    "Europe": "#D55E00",
    "Africa": "#009E73",
    "Americas": "#CC79A7",
    "Oceania": "#E69F00",
}

TASKS: list[dict] = []
FINDINGS: list[dict] = []


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Place the one source CSV at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    required = {"country", "continent", "year", "lifeExp", "pop", "gdpPercap"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Gapminder is missing required columns: {sorted(missing)}")
    if df[list(required)].isna().any().any():
        raise ValueError("The chosen Gapminder source contains missing required values.")
    df = df.sort_values(["country", "year"]).reset_index(drop=True)
    df["gdp_total"] = df["pop"] * df["gdpPercap"]
    return df


def record(task: str, finding: str, value: str | float | int) -> None:
    FINDINGS.append({"task": task, "finding": finding, "value": value})


def export(fig: plt.Figure, name: str, note: str) -> None:
    save_fig(fig, OUT / name, note)
    plt.close(fig)


def register(week: int, task: str, title: str, files: list[str], explanation: str) -> None:
    TASKS.append({"week": week, "task": task, "title": title, "files": files,
                  "explanation": explanation})


def w1_t1(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    summary = latest.groupby("continent").agg(
        countries=("country", "nunique"),
        mean_life_expectancy=("lifeExp", "mean"),
        sd_life_expectancy=("lifeExp", "std"),
        mean_gdp_per_capita=("gdpPercap", "mean"),
        sd_gdp_per_capita=("gdpPercap", "std"),
    ).reset_index()
    summary.to_csv(OUT / "week1_task1_continent_statistics.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 6))
    for continent, group in latest.groupby("continent"):
        ax.scatter(group.gdpPercap, group.lifeExp, s=35, alpha=.72,
                   color=COLORS[continent], label=continent)
    ax.set_xscale("log")
    ax.set(title="Countries within each continent vary widely in health and income",
           xlabel="GDP per capita (constant dollars, log scale)",
           ylabel="Life expectancy (years)")
    ax.legend(frameon=False, ncol=2)
    export(fig, "week1_task1_country_variation.png",
           f"Gapminder {int(df.year.max())}; n={len(latest)} countries; all rows retained.")
    register(1, "Task 1 — summaries and shape", "Summary statistics do not replace a plot",
             ["week1_task1_country_variation.png"],
             "The table summarizes continent groups and the scatter shows country-level spread. A continent average does not describe every country in it.")
    record("Week 1 Task 1", "2007 countries plotted", len(latest))


def w1_t2(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for _, group in df.groupby("country"):
        ax.plot(group.year, group.lifeExp, color="#AAB2BD", alpha=.30, linewidth=.7)
    ax.set(title="BAD EXAMPLE — 142 country lines obscure the shared trend",
           xlabel="Year", ylabel="Life expectancy (years)")
    export(fig, "week1_task2_bad_spaghetti.png",
           f"Gapminder, {df.country.nunique()} countries × {df.year.nunique()} years.")

    continent = df.groupby(["year", "continent"], as_index=False).lifeExp.mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, group in continent.groupby("continent"):
        ax.plot(group.year, group.lifeExp, marker="o", color=COLORS[name], label=name)
    ax.set(title="Average life expectancy rose in every continent",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    ax.legend(frameon=False, ncol=3)
    export(fig, "week1_task2_continent_trends.png", "Gapminder; continent-year means; no countries excluded.")

    selected = ["Afghanistan", "China", "United States"]
    fig, ax = plt.subplots(figsize=(9, 5))
    for _, group in df.groupby("country"):
        ax.plot(group.year, group.lifeExp, color="#D8DDE3", alpha=.4, linewidth=.7)
    for country in selected:
        group = df[df.country == country]
        ax.plot(group.year, group.lifeExp, color=COLORS[group.continent.iloc[0]],
                linewidth=2)
        ax.annotate(country, (group.year.iloc[-1], group.lifeExp.iloc[-1]),
                    xytext=(5, 0), textcoords="offset points", va="center")
    ax.set(title="Selected country paths diverge despite a broad upward trend",
           xlabel="Year", ylabel="Life expectancy (years)")
    export(fig, "week1_task2_highlights.png", "All 142 countries shown; three directly labelled; no legend.")

    annual = df.groupby("year").gdpPercap.agg(
        richest="max", poorest="min").reset_index()
    annual["ratio"] = annual.richest / annual.poorest
    annual.to_csv(OUT / "week1_task2_income_gap.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(annual.year, annual.ratio, marker="o", color=PALETTE["highlight"])
    ax.set(title="The richest-to-poorest GDP-per-capita ratio fluctuated, not steadily narrowed",
           xlabel="Year", ylabel="Richest / poorest country GDP per capita")
    export(fig, "week1_task2_income_gap.png", "Annual maximum/minimum of country GDP per capita; no countries excluded.")
    record("Week 1 Task 2", "GDP-per-capita ratio, first year",
           float(annual.ratio.iloc[0]))
    record("Week 1 Task 2", "GDP-per-capita ratio, last year",
           float(annual.ratio.iloc[-1]))
    register(1, "Task 2 — trends and spaghetti", "Aggregation and highlighting answer different questions",
             ["week1_task2_bad_spaghetti.png", "week1_task2_continent_trends.png",
              "week1_task2_highlights.png", "week1_task2_income_gap.png"],
             "The spaghetti plot is intentionally unreadable at 142 lines. The continent average reveals group trends; the highlighted chart preserves individual trajectories. The annual extreme ratio directly tests the richest/poorest gap.")


def w1_t3(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(latest.lifeExp, bins=20, color=PALETTE["series"][0], edgecolor="white")
    ax.set(title="Country life expectancy is broadly distributed, not a single value",
           xlabel="Life expectancy (years)", ylabel="Countries")
    export(fig, "week1_task3_distribution.png", f"Gapminder {int(df.year.max())}; n={len(latest)}.")

    fig, ax = plt.subplots(figsize=(9, 6))
    for continent, group in latest.groupby("continent"):
        ax.scatter(group.gdpPercap, group.lifeExp, color=COLORS[continent],
                   alpha=.68, s=32, label=continent)
        if len(group) > 2:
            coef = np.polyfit(np.log10(group.gdpPercap), group.lifeExp, 1)
            x = np.geomspace(group.gdpPercap.min(), group.gdpPercap.max(), 100)
            ax.plot(x, np.polyval(coef, np.log10(x)), color=COLORS[continent], linewidth=1)
    pooled_r = latest.gdpPercap.corr(latest.lifeExp)
    ax.set_xscale("log")
    ax.set(title=f"Income and life expectancy are positively associated (r={pooled_r:.2f})",
           xlabel="GDP per capita (constant dollars, log scale)",
           ylabel="Life expectancy (years)")
    ax.legend(frameon=False, ncol=2)
    export(fig, "week1_task3_relationship.png",
           f"Gapminder {int(df.year.max())}; n={len(latest)}; log10 income regressions by continent.")
    correlations = pd.Series({
        continent: group.gdpPercap.corr(group.lifeExp)
        for continent, group in latest.groupby("continent")
    }, name="GDP-life expectancy correlation")
    correlations.rename("GDP-life expectancy correlation").to_csv(OUT / "week1_task3_group_correlations.csv")
    record("Week 1 Task 3", "Pooled GDP/life expectancy correlation", float(pooled_r))
    register(1, "Task 3 — distributions and relationships", "Grouping changes the relationship we see",
             ["week1_task3_distribution.png", "week1_task3_relationship.png"],
             "The histogram describes a distribution; the scatter shows two quantitative variables. GDP and life expectancy are positively associated overall and within each continent in this year, so this dataset does not reproduce the Simpson's-paradox sign reversal in the penguins brief. The grouped view still shows why a pooled association is not a universal country-level law. Missing values: none.")


def w1_t4(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    yearly = df.groupby("year", as_index=False).lifeExp.mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(yearly.year, yearly.lifeExp, marker="o", color=PALETTE["series"][0])
    ax.set(title="Global mean life expectancy increased from 1952 to 2007",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    export(fig, "week1_task4_trend.png", "Equal-weight country mean; six-year snapshots; all records used.")

    fig, ax = plt.subplots(figsize=(8, 4))
    order = latest.groupby("continent").gdpPercap.median().sort_values().index
    sns.boxplot(data=latest, x="continent", y="gdpPercap", order=order, ax=ax,
                color="#7DA9C7", showfliers=True)
    ax.set_yscale("log")
    ax.set(title="Country incomes differ strongly across continents",
           xlabel="Continent", ylabel="GDP per capita (log scale)")
    export(fig, "week1_task4_comparison.png", f"Gapminder {int(df.year.max())}; n={len(latest)}.")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(latest.gdpPercap, latest.lifeExp, color=PALETTE["series"][0], alpha=.65)
    ax.set_xscale("log")
    ax.set(title="Higher-income countries tend to live longer",
           xlabel="GDP per capita (constant dollars, log scale)",
           ylabel="Life expectancy (years)")
    export(fig, "week1_task4_relationship.png", "Country observations; log x-axis; no exclusions.")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(latest.gdpPercap, bins=28, color=PALETTE["series"][1], edgecolor="white")
    ax.set(title="Most countries have low GDP per capita; a few are far richer",
           xlabel="GDP per capita (constant dollars)", ylabel="Countries")
    export(fig, "week1_task4_income_distribution.png", f"Gapminder {int(df.year.max())}; n={len(latest)}.")

    continent_trend = df.groupby(["year", "continent"], as_index=False).lifeExp.mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(data=continent_trend, x="year", y="lifeExp", hue="continent",
                 palette=COLORS, marker="o", ax=ax)
    ax.set(title="Every continent improved, but regional gaps persist",
           xlabel="Year", ylabel="Mean life expectancy (years)")
    export(fig, "week1_task4_mechanism.png", "Continent means; no records excluded.")

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=latest, x="gdpPercap", y="lifeExp", hue="continent",
                    palette=COLORS, alpha=.7, ax=ax)
    ax.set_xscale("log")
    ax.set(title="Redesign: continent and country spread explain the pooled pattern",
           xlabel="GDP per capita (constant dollars, log scale)",
           ylabel="Life expectancy (years)")
    ax.legend(frameon=False, ncol=2)
    export(fig, "week1_task4_redesign.png", f"Gapminder {int(df.year.max())}; n={len(latest)}.")
    register(1, "Task 4 — choose charts", "Distinct questions need distinct charts",
             ["week1_task4_trend.png", "week1_task4_comparison.png",
              "week1_task4_relationship.png", "week1_task4_income_distribution.png",
              "week1_task4_mechanism.png", "week1_task4_redesign.png"],
             "The five plots use a line, box plot, scatterplot, histogram, and grouped trend for comparison, association, distribution, and change. The redesign adds continent to the scatter and preserves the log scale.")


def w1_t5(df: pd.DataFrame) -> None:
    yearly = df.groupby("year").agg(
        global_mean=("lifeExp", "mean"),
        population_weighted=("lifeExp", lambda s: np.average(s, weights=df.loc[s.index, "pop"])),
        countries=("country", "nunique"),
    ).reset_index()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(yearly.year, yearly.global_mean, marker="o", label="Country-weighted mean")
    ax.plot(yearly.year, yearly.population_weighted, marker="s", label="Population-weighted mean")
    ax.set(title="Global life expectancy rose; weighting changes the level",
           xlabel="Year", ylabel="Life expectancy (years)")
    ax.legend(frameon=False)
    export(fig, "week1_task5_time_series.png",
           "Gapminder is sampled every five years; weights use population; no exclusions.")
    register(1, "Task 5 — real time series", "Five-year observations show trend, not seasonality",
             ["week1_task5_time_series.png"],
             "A line respects ordered years. Gapminder has six-year (not monthly) spacing, so it cannot identify within-year seasonality; that limitation is stated rather than imputed.")


def w2_t1(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    sample = latest.sample(n=25, random_state=42).sort_values("country").reset_index(drop=True)
    target = sample.iloc[len(sample) // 2]
    fig, ax = plt.subplots(figsize=(9, 7))
    for row in sample.itertuples():
        ax.scatter(row.lifeExp, row.country,
                   color=PALETTE["highlight"] if row.country == target.country else "#AAB2BD",
                   s=45, zorder=3)
    ax.set(title="One orange mark stands out among 25 country labels",
           xlabel="Life expectancy (years)", ylabel="Country")
    export(fig, "week2_task1_preattentive.png",
           f"Gapminder {int(df.year.max())}; display sample n=25 of 142 (seed=42); no data cleaning.")
    record("Week 2 Task 1", "Target country for a real visual-search trial", target.country)
    register(2, "Task 1 — preattentive search", "Hue isolates one target in grey context",
             ["week2_task1_preattentive.png"],
             f"Position encodes life expectancy; hue is the single pop-out and country labels let a reader report the marked country. The 25-country display sample is fixed with seed 42; real response time and accuracy are not invented.")


def w2_t2(df: pd.DataFrame) -> None:
    sample = df[df.year == df.year.max()].copy()
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    principles = ["Proximity", "Similarity", "Enclosure", "Closure", "Continuity", "Connection"]
    rng = np.random.default_rng(42)
    for ax, principle in zip(axes.flat, principles):
        ax.set_title(principle)
        if principle == "Proximity":
            for lane, (continent, group) in enumerate(sample.groupby("continent")):
                jitter = rng.normal(0, .04, len(group))
                ax.scatter(group.lifeExp, lane + jitter, color="#7B8794", s=14, alpha=.6)
            ax.set_yticks(range(sample.continent.nunique()),
                          sorted(sample.continent.unique()), fontsize=6)
            ax.set_xlabel("Life expectancy (years)", fontsize=7)
        elif principle == "Similarity":
            for continent, group in sample.groupby("continent"):
                ax.scatter(group.lifeExp, rng.normal(0, .08, len(group)),
                           color=COLORS[continent], s=14, alpha=.6)
            ax.set_xlabel("Same hue groups continents", fontsize=7)
            ax.set_yticks([])
        elif principle == "Enclosure":
            for continent, group in sample.groupby("continent"):
                x = np.log10(group.gdpPercap)
                y = group.lifeExp
                cx, cy = x.median(), y.median()
                width = max(x.quantile(.9) - x.quantile(.1), .08)
                height = max(y.quantile(.9) - y.quantile(.1), .8)
                ax.add_patch(Ellipse((cx, cy), width, height, fill=False,
                                     edgecolor=COLORS[continent], linewidth=1.2))
                ax.scatter(x, y, color=COLORS[continent], s=8, alpha=.3)
            ax.set_xlabel("log10 GDP per capita", fontsize=7)
            ax.set_ylabel("Life expectancy", fontsize=7)
        elif principle == "Closure":
            means = sample.groupby("continent").lifeExp.mean().sort_values()
            for lane, (continent, value) in enumerate(means.items()):
                ax.scatter(value, lane, color=COLORS[continent], s=45)
                ax.add_patch(Arc((value, lane), 5, .65, theta1=35, theta2=325,
                                 edgecolor=COLORS[continent], linewidth=1.3))
            ax.set_yticks(range(len(means)), means.index, fontsize=6)
            ax.set_xlabel("Continent mean life expectancy", fontsize=7)
        elif principle == "Continuity":
            for country in ["China", "India", "United States"]:
                group = df[df.country == country]
                ax.plot(group.year, group.lifeExp, marker="o",
                        color=COLORS[group.continent.iloc[0]], linewidth=1.5)
            ax.set_xlabel("Year", fontsize=7)
            ax.set_ylabel("Life expectancy", fontsize=7)
        else:
            for country in ["China", "India", "United States"]:
                group = df[df.country == country].set_index("year")
                start = group.loc[df.year.min()]
                end = group.loc[df.year.max()]
                color = COLORS[group.continent.iloc[0]]
                ax.plot([0, 1], [start.lifeExp, end.lifeExp], marker="o",
                        color=color, linewidth=1.5)
                ax.text(1.02, end.lifeExp, country, fontsize=6, va="center")
            ax.set_xlim(-.1, 1.3)
            ax.set_xticks([0, 1], [str(int(df.year.min())), str(int(df.year.max()))])
            ax.set_ylabel("Life expectancy", fontsize=7)
        ax.tick_params(labelsize=6)
    fig.suptitle("Six grouping cues can be demonstrated with the same Gapminder records")
    export(fig, "week2_task2_gestalt.png", f"Gapminder {int(df.year.max())}; fixed data, varied grouping.")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, connected in zip(axes, [True, False]):
        for country in ["China", "India", "United States"]:
            group = df[df.country == country].set_index("year")
            start = group.loc[df.year.min()]
            end = group.loc[df.year.max()]
            color = COLORS[group.continent.iloc[0]]
            if connected:
                ax.plot([0, 1], [start.lifeExp, end.lifeExp], marker="o",
                        color=color, linewidth=1.5)
            else:
                ax.scatter([0, 1], [start.lifeExp, end.lifeExp],
                           color=color, s=45)
        ax.set_xticks([0, 1], [str(int(df.year.min())), str(int(df.year.max()))])
        ax.set_ylabel("Life expectancy (years)")
        ax.set_title("Connected" if connected else "Same points, unconnected")
    export(fig, "week2_task2_connection_test.png",
           "Same Gapminder country endpoints; only connecting lines change.")
    register(2, "Task 2 — Gestalt grouping", "Grouping principles change what stands together",
             ["week2_task2_gestalt.png", "week2_task2_connection_test.png"],
             "The panels vary proximity, similarity, enclosure, closure, continuity, and connection while retaining the same source observations. A real reader's perceived-group counts must be collected; they are not fabricated.")


def w2_t3(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()].sort_values("lifeExp", ascending=False)
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(latest.country, latest.lifeExp, color=plt.get_cmap("hsv")(np.linspace(0, 1, len(latest))))
    ax.tick_params(axis="x", labelrotation=90, labelsize=4)
    ax.grid(True, axis="both", linewidth=1)
    ax.set(title="BAD EXAMPLE — A rainbow of 142 country bars obscures the ranking",
           xlabel="Country", ylabel="Life expectancy (years)")
    export(fig, "week2_task3_bad_example.png", f"Gapminder {int(df.year.max())}; n={len(latest)}.")

    continent = latest.groupby("continent", as_index=False).lifeExp.mean().sort_values("lifeExp")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].bar(continent.continent, continent.lifeExp, color=PALETTE["series"][0])
    axes[0].set(title="One colour", ylabel="Mean life expectancy (years)")
    axes[1].bar(continent.continent, continent.lifeExp,
                color=[COLORS[c] for c in continent.continent])
    axes[1].set(title="Colour carries continent")
    axes[2].bar(continent.continent, continent.lifeExp, color=PALETTE["muted"])
    ax = axes[2]
    best = continent.iloc[-1]
    idx = list(continent.continent).index(best.continent)
    ax.patches[idx].set_color(PALETTE["highlight"])
    ax.set(title=f"One message: {best.continent} leads")
    for item in axes:
        item.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Removing redundant ink makes the comparison easier")
    export(fig, "week2_task3_reduction.png", "2007 continent means; five categories; no rows excluded.")

    top = latest.nlargest(4, "lifeExp")
    rest = latest.loc[~latest.index.isin(top.index), "lifeExp"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(list(top.country) + ["Other 138 (mean)"],
           list(top.lifeExp) + [rest],
           color=[PALETTE["highlight"]] * 4 + [PALETTE["muted"]])
    ax.set(title="Four leading countries plus one pooled context group",
           xlabel="Four named countries; remainder summarized",
           ylabel="Life expectancy (years)")
    export(fig, "week2_task3_chunking.png", "Other 138 summarized by mean; aggregation hides within-group spread.")
    register(2, "Task 3 — cognitive load", "One strong mark and fewer chunks reduce effort",
             ["week2_task3_bad_example.png", "week2_task3_reduction.png",
              "week2_task3_chunking.png"],
             "The first plot is deliberately cluttered; the redesigned chart uses a single-message highlight. Chunking the countries reduces the number of comparisons but hides variation among the pooled 138.")


def w2_t4(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    summary = latest.groupby("continent", as_index=False).gdpPercap.mean()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(summary.continent, summary.gdpPercap,
                color=[COLORS[c] for c in summary.continent])
    axes[0].set(title="Position/length: country-group means",
                ylabel="Mean GDP per capita ($)")
    axes[1].scatter(summary.continent, np.zeros(len(summary)),
                    s=summary.gdpPercap / summary.gdpPercap.max() * 1200,
                    color=[COLORS[c] for c in summary.continent], alpha=.75)
    axes[1].set(title="Area: same values are harder to compare",
                ylabel="Bubble area ∝ GDP/capita", yticks=[])
    export(fig, "week2_task4_channels.png",
           f"Gapminder {int(df.year.max())}; bubble area is proportional to mean GDP per capita.")
    register(2, "Task 4 — visual channels", "Length and position are easier to compare than area",
             ["week2_task4_channels.png"],
             "The same group summary uses a common baseline for length versus area-proportional circles. Area is proportional to the value; the visual comparison is illustrative, while human estimates remain uncollected.")


def w2_t5(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    focus = ["China", "India", "Afghanistan"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for _, group in df.groupby("country"):
        ax.plot(group.year, group.lifeExp, color="#D7DCE2", alpha=.35, linewidth=.7)
    for country, color in zip(focus, [PALETTE["series"][0], PALETTE["highlight"], PALETTE["series"][2]]):
        group = df[df.country == country]
        ax.plot(group.year, group.lifeExp, color=color, linewidth=2)
        ax.annotate(country, (group.year.iloc[-1], group.lifeExp.iloc[-1]),
                    xytext=(5, 0), textcoords="offset points")
    ax.set(title="Three labelled trajectories stand out against grey context",
           xlabel="Year", ylabel="Life expectancy (years)")
    export(fig, "week2_task5_redesign.png",
           f"All 142 country lines retained; focus countries labelled; n={len(df)}.")
    register(2, "Task 5 — perception redesign", "Direct labels reduce legend memory work",
             ["week2_task5_redesign.png"],
             "Grey context supports one highlighted message; labels replace legend lookups. A reader's exact one-sentence interpretation remains pending authentic collection.")


def w3_a(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    files = []

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    continent = latest.groupby("continent").lifeExp.mean().sort_values()
    axes[0].bar(continent.index, continent.values, color=PALETTE["highlight"])
    axes[0].set(title="BAD — Truncated zero exaggerates regional differences",
                ylabel="Mean life expectancy (years)", ylim=(45, 80))
    axes[1].bar(continent.index, continent.values, color=PALETTE["series"][0])
    axes[1].set(title="Honest zero-based comparison", ylabel="Mean life expectancy (years)")
    name = "week3_case01_baseline.png"
    export(fig, name, "Gapminder 2007 continent means; both panels use the same values.")
    files.append(name)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(latest.gdpPercap, latest.lifeExp, color=PALETTE["series"][0], alpha=.55)
    ax.set(title="BAD — A straight raw-income axis compresses most countries",
           xlabel="GDP per capita (linear scale)", ylabel="Life expectancy (years)")
    export(fig, "week3_case02_scale_bad.png", "Same Gapminder countries; linear GDP scale.")
    files.append("week3_case02_scale_bad.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(latest.gdpPercap, latest.lifeExp, color=PALETTE["series"][0], alpha=.55)
    ax.set_xscale("log")
    ax.set(title="Log income scale reveals the low-income majority",
           xlabel="GDP per capita (log scale)", ylabel="Life expectancy (years)")
    export(fig, "week3_case02_scale_redesign.png", "Same observations; only the x-axis scale changes.")
    files.append("week3_case02_scale_redesign.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(latest.gdpPercap, bins=4, color=PALETTE["series"][0])
    ax.set(title="BAD — Four bins hide the long-tailed income distribution",
           xlabel="GDP per capita ($)", ylabel="Countries")
    export(fig, "week3_case03_bins_bad.png", "Gapminder 2007; histogram bins=4.")
    files.append("week3_case03_bins_bad.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(latest.gdpPercap, bins=35, color=PALETTE["series"][0])
    ax.set(title="More bins show the distribution's right tail",
           xlabel="GDP per capita ($)", ylabel="Countries")
    export(fig, "week3_case03_bins_redesign.png", "Same 2007 observations; histogram bins=35.")
    files.append("week3_case03_bins_redesign.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    data = latest.sort_values("gdpPercap")
    ax.bar(data.country, data.gdpPercap, color=PALETTE["series"][0])
    ax.tick_params(axis="x", labelrotation=90, labelsize=4)
    ax.set(title="BAD — 142 labelled bars overwhelm the reader",
           xlabel="Country", ylabel="GDP per capita ($)")
    export(fig, "week3_case04_crowding.png", "All 142 Gapminder countries; no subsampling.")
    files.append("week3_case04_crowding.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    corr = latest[["lifeExp", "gdpPercap", "pop"]].corr()
    sns.heatmap(corr, cmap="Reds", annot=True, fmt=".2f", ax=ax)
    ax.set_title("BAD — Sequential red hides negative direction around zero")
    export(fig, "week3_case05_heatmap_bad.png", "Gapminder 2007; unbounded sequential colour scale.")
    files.append("week3_case05_heatmap_bad.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    yearly_life = df.groupby("year").lifeExp.mean()
    yearly_gdp = df.groupby("year").gdpPercap.mean()
    ax.plot(yearly_life.index, yearly_life.values, marker="o", color=PALETTE["series"][0])
    ax.set_ylabel("Mean life expectancy (years)", color=PALETTE["series"][0])
    ax2 = ax.twinx()
    ax2.plot(yearly_gdp.index, yearly_gdp.values, marker="s", color=PALETTE["highlight"])
    ax2.set_ylabel("Mean GDP per capita ($)", color=PALETTE["highlight"])
    ax.set(title="BAD EXAMPLE — Dual axes imply a visual relationship",
           xlabel="Year")
    export(fig, "week3_case06_dual_axis_bad.png",
           "Gapminder country means; independent y-axis scales.")
    files.append("week3_case06_dual_axis_bad.png")

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    axes[0].plot(yearly_life.index, yearly_life.values, marker="o")
    axes[0].set(title="Separate panels avoid false scale alignment",
                ylabel="Mean life expectancy (years)")
    axes[1].plot(yearly_gdp.index, yearly_gdp.values, marker="s", color=PALETTE["highlight"])
    axes[1].set(xlabel="Year", ylabel="Mean GDP per capita ($)")
    export(fig, "week3_case06_dual_axis_redesign.png",
           "Same Gapminder country means; separate panels with labelled scales.")
    files.append("week3_case06_dual_axis_redesign.png")

    continent_pop = latest.groupby("continent").pop.sum()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.pie(continent_pop, labels=continent_pop.index, autopct="%1.0f%%",
           colors=[COLORS[c] for c in continent_pop.index])
    ax.set_title("BAD — Population shares are hard to compare as slices")
    export(fig, "week3_case07_pie_bad.png", "Five continent categories; one year.")
    files.append("week3_case07_pie_bad.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(continent_pop.index, continent_pop.values,
           color=[COLORS[c] for c in continent_pop.index])
    ax.set(title="A sorted bar chart makes population shares comparable",
           xlabel="Continent", ylabel="Population")
    export(fig, "week3_case07_bar_redesign.png", "Gapminder 2007; five continent totals.")
    files.append("week3_case07_bar_redesign.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.kdeplot(data=latest, x="gdpPercap", ax=ax, color=PALETTE["highlight"])
    ax.set(title="BAD — KDE extends beyond the observed income support",
           xlabel="GDP per capita ($)", ylabel="Density")
    export(fig, "week3_case08_kde_bad.png", f"Gapminder 2007; n={len(latest)}; default bandwidth.")
    files.append("week3_case08_kde_bad.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    for continent, group in latest.groupby("continent"):
        ax.scatter(group.gdpPercap, group.lifeExp, color=COLORS[continent],
                   label=continent, alpha=.65, s=28)
    ax.set_xscale("log")
    ax.set(title="Redesign — continent explains structure hidden in pooled income",
           xlabel="GDP per capita (log scale)", ylabel="Life expectancy (years)")
    ax.legend(frameon=False, ncol=2)
    export(fig, "week3_case09_grouping.png", f"Gapminder 2007; n={len(latest)}.")
    files.append("week3_case09_grouping.png")

    diagnostics = [
        "A truncated bar axis magnifies small differences; zero-baseline bars show the true scale.",
        "Extreme rich countries compress a linear GDP axis; a log axis reveals the low-income majority.",
        "Histogram appearance depends on bin count; disclose and justify it.",
        "Country-by-country labels create unnecessary cognitive load; summarize or filter with a declared rule.",
        "A sequential palette does not represent negative and positive correlation around zero; use a diverging palette fixed at -1 to 1.",
        "Independent dual axes invite false visual alignment; use separate labelled panels.",
        "Pie slices hinder precise category comparisons; use a sorted zero-based bar chart.",
        "Gaussian KDE smoothing can place density outside observed data; declare bandwidth and use a log histogram or boundary-aware method.",
        "Pooled association masks continent structure; use grouping and compare within-group patterns.",
    ]
    pd.DataFrame({"case": range(1, 10), "diagnosis": diagnostics}).to_csv(
        OUT / "week3_partA_diagnoses.csv", index=False)
    fig, axes = plt.subplots(3, 3, figsize=(12, 9))
    for ax, filename, diagnosis in zip(axes.flat, files, diagnostics):
        image = plt.imread(OUT / filename)
        ax.imshow(image)
        ax.set_title(diagnosis[:48] + "...", fontsize=7)
        ax.set_axis_off()
    fig.suptitle("Nine chart failure modes and honest redesigns, all on Gapminder")
    export(fig, "week3_partA_gallery.png", "All panels use Gapminder only; see diagnosis CSV for mechanisms.")
    register(3, "Part A — nine diagnoses", "Chart design choices change the apparent story",
             ["week3_partA_gallery.png"],
             "Nine cases demonstrate scale, baseline, binning, overplotting, palette, dual-axis, part-to-whole, smoothing, and aggregation failures using the same Gapminder source.")


def w3_b(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    values = latest.groupby("continent").lifeExp.mean().sort_values()
    start, end = float(values.iloc[0]), float(values.iloc[-1])
    baseline = 45.0
    factor, data_effect, shown_effect = lie_factor(start, end, start - baseline,
                                                   end - baseline, ink_dimension=1)
    # Bubble area is proportional to population, so the encoded ink dimension is 2.
    population = latest.groupby("continent").pop.sum().sort_values()
    area_factor, area_data, area_shown = lie_factor(
        float(population.iloc[0]), float(population.iloc[-1]),
        float(np.sqrt(population.iloc[0])), float(np.sqrt(population.iloc[-1])),
        ink_dimension=2)
    summary = pd.DataFrame([
        {"encoding": "Life expectancy bar, baseline 45", "data_effect": data_effect,
         "graphic_effect": shown_effect, "lie_factor": factor, "verdict": lie_verdict(factor)},
        {"encoding": "Population bubble, area proportional", "data_effect": area_data,
         "graphic_effect": area_shown, "lie_factor": area_factor, "verdict": lie_verdict(area_factor)},
    ])
    summary.to_csv(OUT / "week3_partB_lie_factor.csv", index=False)
    register(3, "Part B — Lie Factor", "Measured distortion differs from data change",
             [], f"Computed Lie Factors: truncated baseline {factor:.2f}; area-proportional population bubble {area_factor:.2f}. The common-axis dual-axis Lie Factor is undefined.")
    record("Week 3 Part B", "Lie Factor: truncated mean-life bar", factor)
    record("Week 3 Part B", "Lie Factor: area-proportional population", area_factor)


def w3_c() -> None:
    candidates = {
        "tab10": [matplotlib.colors.to_hex(plt.get_cmap("tab10")(i)) for i in range(5)],
        "Okabe-Ito course palette": PALETTE["series"] + [PALETTE["series_4th"]],
    }
    kinds = ["normal", "protan", "deutan", "tritan"]
    records = []
    fig, axes = plt.subplots(2, 4, figsize=(13, 5))
    for row, (name, palette) in enumerate(candidates.items()):
        for col, kind in enumerate(kinds):
            ax = axes[row, col]
            colors = palette if kind == "normal" else simulate_cvd(palette, kind)
            for index, color in enumerate(colors):
                ax.add_patch(plt.Rectangle((.04 + index * .19, .32), .16, .40, color=color))
                ax.text(.12 + index * .19, .18, str(index + 1), ha="center", fontsize=8)
            ax.set_title(f"{name}\n{kind}", fontsize=9)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_axis_off()
        for kind in kinds:
            pair = worst_pair(palette, kind=None if kind == "normal" else kind)
            records.append({"palette": name, "vision": kind, "slot_i": pair[0],
                            "slot_j": pair[1], "delta_e": pair[4]})
    pd.DataFrame(records).to_csv(OUT / "week3_partC_palette_audit.csv", index=False)
    export(fig, "week3_partC_palette.png", "Colour vision simulations from course vizlib; swatches numbered.")
    register(3, "Part C — palette check", "Palette choices should survive colour-vision simulation",
             ["week3_partC_palette.png"],
             "Two categorical palettes are simulated under protan, deutan, and tritan deficiencies; nearest pairs and ΔE values are in the audit CSV. Use no more than three categories without additional direct labels or shape.")


def w3_d(df: pd.DataFrame) -> None:
    latest = df[df.year == df.year.max()]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    bins = np.geomspace(latest.gdpPercap.min(), latest.gdpPercap.max(), 22)
    axes[0, 0].hist(latest.gdpPercap, bins=bins, color=PALETTE["series"][0])
    axes[0, 0].set_xscale("log")
    axes[0, 0].set(title="GDP per capita is strongly right-skewed",
                   xlabel="GDP per capita (log scale)", ylabel="Countries")
    sns.boxplot(data=latest, x="continent", y="lifeExp", ax=axes[0, 1],
                color="#9FBAD0", showfliers=True)
    axes[0, 1].set(title="Life expectancy distributions vary by continent",
                   xlabel="Continent", ylabel="Life expectancy (years)")
    for continent, group in latest.groupby("continent"):
        axes[1, 0].scatter(group.gdpPercap, group.lifeExp, color=COLORS[continent],
                           alpha=.65, label=continent)
    axes[1, 0].set_xscale("log")
    axes[1, 0].set(title="Income and life expectancy are associated",
                   xlabel="GDP per capita (log scale)", ylabel="Life expectancy (years)")
    axes[1, 0].legend(frameon=False, fontsize=8)
    corr = latest[["lifeExp", "gdpPercap", "pop"]].corr()
    sns.heatmap(corr, cmap="RdBu_r", vmin=-1, vmax=1, center=0,
                annot=True, fmt=".2f", square=True, ax=axes[1, 1])
    axes[1, 1].set_title("Three measures; diverging scale fixed at ±1")
    fig.suptitle("Development review: one dataset, four complementary views")
    export(fig, "week3_partD_development_review.png",
           f"Gapminder {int(df.year.max())}; n={len(latest)}; no rows removed; log GDP scale.")
    register(3, "Part D — development review", "A four-panel figure audits distribution, comparison, relationship, and correlation",
             ["week3_partD_development_review.png"],
             "The four panels show income distribution (log bins disclosed), life expectancy by continent, GDP/life expectancy scatter, and a fixed -1..1 correlation matrix. Missing required values: none.")


def w3_e() -> None:
    text = """# Part E — written justification

**One source dataset:** Gapminder (1,704 country-year rows, 142 countries, five continents, 1952–2007; no missing required values). All weekly tasks use this same dataset. Country/year rows are retained; summaries state their aggregation explicitly.

**Panels and parameters.** The income histogram uses 21 geometric bins on a log x-scale because GDP per capita is strongly right-skewed. Life expectancy boxplots retain outliers and use the five continent categories. The scatter uses log GDP per capita and continent colour as context, not as the only data encoding. The correlation heatmap uses a diverging palette with `vmin=-1`, `vmax=1`, and zero centered. No dual axes are used.

**Interpretation and limitations.** The country-level association between income and life expectancy is descriptive, not causal. Aggregated continent means conceal within-continent variation. A 5-year observation interval cannot establish monthly seasonality. Gapminder has no visual-search reaction times or reader responses; required Week 2 human results are explicitly left pending and have a collection workflow.

**Ethical data handling.** There are no missing required values and no observations are excluded. Income is log-scaled but never removed. Country aggregates and weighting choices are labelled. The GDP ratio is descriptive and is not presented as a causal inequality explanation.

**Redesign trade-off.** Grouping and highlighting reduce visual load but make within-group country paths less prominent. Direct labels avoid legend lookups but focus attention on selected countries only.
"""
    (OUT / "week3_partE_justification.md").write_text(text, encoding="utf-8")
    register(3, "Part E — written justification", "Parameters, exclusions, and trade-offs are explicit",
             [], "The written justification is saved in outputs/week3_partE_justification.md.")


def collect_human_results(df: pd.DataFrame) -> pd.DataFrame:
    """Collect real participant observations; never creates default/fabricated responses."""
    participant = input("Participant label (first name or 'classmate'): ").strip()
    if not participant:
        raise ValueError("A participant label is required.")
    latest = df[df.year == df.year.max()]
    search_sample = latest.sample(n=25, random_state=42).sort_values("country").reset_index(drop=True)
    target = search_sample.iloc[len(search_sample) // 2]
    records = []
    print("Show outputs/week2_task1_preattentive.png. Tell the participant to find the orange mark.")
    input("When the participant is ready to see the chart, press Enter to begin timing.")
    started = time.perf_counter()
    answer = input("Which country is the orange mark beside? ").strip()
    elapsed = (time.perf_counter() - started) * 1000
    records.append({"participant": participant, "task": "visual_search",
                    "response": answer, "correct": answer.casefold() == target.country.casefold(),
                    "response_ms": elapsed})
    print("Show outputs/week2_task2_gestalt.png before asking the six grouping questions.")
    for principle in ["proximity", "similarity", "enclosure", "closure", "continuity", "connection"]:
        response = input(f"Reader: how many groups do you see for {principle}? Enter integer: ").strip()
        if not response.isdigit():
            raise ValueError(f"Group count for {principle} must be an integer.")
        records.append({"participant": participant, "task": f"gestalt_{principle}",
                        "response": int(response), "correct": None, "response_ms": None})
    for connectors in [True, False]:
        print("Show outputs/week2_task2_connection_test.png and direct the reader to the "
              f"{'connected' if connectors else 'unconnected'} panel.")
        response = input(
            "How many groups does the reader see in the connection panel "
            f"{'with' if connectors else 'without'} lines? Enter integer: ").strip()
        if not response.isdigit():
            raise ValueError("Connection group count must be an integer.")
        records.append({"participant": participant,
                        "task": f"connection_lines_{'on' if connectors else 'off'}",
                        "response": int(response), "correct": None, "response_ms": None})
    summary = latest.groupby("continent").gdpPercap.mean().sort_values(ascending=False)
    true_ratio = float(summary.iloc[1] / summary.iloc[0])
    print("Show outputs/week2_task4_channels.png; ask the reader to compare the two largest "
          "continent means in each panel.")
    for channel in ["length", "area"]:
        estimate = input(
            f"Reader: estimate the second-largest continent's value as a percentage "
            f"of the largest using the {channel} panel: ").strip()
        try:
            percent = float(estimate)
        except ValueError as exc:
            raise ValueError("Channel estimate must be numeric.") from exc
        if not 0 <= percent <= 100:
            raise ValueError("Channel estimate must be between 0 and 100.")
        records.append({"participant": participant, "task": f"channel_{channel}",
                        "response": percent, "correct": None,
                        "response_ms": None, "true_ratio": true_ratio})
    print("Show outputs/week2_task5_redesign.png before asking for the reader's interpretation.")
    interpretation = input("Record the reader's exact one-sentence interpretation of the redesign: ")
    if not interpretation.strip():
        raise ValueError("The reader's verbatim interpretation cannot be empty.")
    records.append({"participant": participant, "task": "redesign_interpretation",
                    "response": interpretation, "correct": None, "response_ms": None})
    result = pd.DataFrame(records)
    destination = OUT / "human_results.csv"
    result.to_csv(destination, index=False)
    print(f"Authentic participant data saved to {destination}")
    return result


def run_all() -> None:
    global TASKS, FINDINGS
    TASKS, FINDINGS = [], []
    df = load_data()
    print(f"Using one dataset: {DATA_PATH.relative_to(ROOT)} "
          f"({len(df)} rows, {df.country.nunique()} countries, {df.continent.nunique()} continents).")
    w1_t1(df)
    w1_t2(df)
    w1_t3(df)
    w1_t4(df)
    w1_t5(df)
    w2_t1(df)
    w2_t2(df)
    w2_t3(df)
    w2_t4(df)
    w2_t5(df)
    w3_a(df)
    w3_b(df)
    w3_c()
    w3_d(df)
    w3_e()
    pd.DataFrame(FINDINGS).to_csv(OUT / "key_findings.csv", index=False)
    build_notebook()
    print(f"Generated {len(TASKS)} weekly task sections; outputs saved to {OUT}.")
    print("Human studies remain pending. Call collect_human_results(load_data()) with a real participant.")


def build_notebook() -> None:
    """Create one output-rich notebook containing every adapted weekly task."""
    cells = [{
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Complete Data Visualization Coursework — One Dataset\n",
            "\n",
            "All tasks use only the Gapminder dataset (`data/gapminder.csv`). ",
            "The original weekly concepts are adapted where a single country-year dataset cannot support the original domain-specific exercise. ",
            "Human-participant results are intentionally not invented; see the collection function in `solutions.py`.\n",
        ],
    }, {
        "cell_type": "code",
        "execution_count": 1,
        "metadata": {},
        "outputs": [{
            "name": "stdout", "output_type": "stream",
            "text": ["Run `python coursework\\solutions.py` first to regenerate all figures and tables.\n"],
        }],
        "source": [
            "from pathlib import Path\n",
            "import sys\n",
            "import pandas as pd\n",
            "from IPython.display import Image, display\n",
            "ROOT = Path.cwd()\n",
            "if not (ROOT / 'coursework' / 'solutions.py').exists():\n",
            "    ROOT = ROOT.parent\n",
            "sys.path.insert(0, str(ROOT / 'coursework'))\n",
            "from solutions import run_all, OUT\n",
            "run_all()\n",
        ],
    }]
    for task in TASKS:
        cells.append({
            "cell_type": "markdown", "metadata": {},
            "source": [f"## Week {task['week']} — {task['task']}\n\n",
                       f"### {task['title']}\n\n", f"{task['explanation']}\n"],
        })
        for filename in task["files"]:
            path = OUT / filename
            image = PILImage.open(path)
            image.thumbnail((1400, 1400), PILImage.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            cells.append({
                "cell_type": "code", "execution_count": 1, "metadata": {},
                "outputs": [{
                    "data": {"image/png": encoded, "text/plain": ["<Figure>"]},
                    "metadata": {}, "output_type": "display_data",
                }],
                "source": [f"display(Image(filename=str(OUT / {filename!r})))\n"],
            })
        if task["task"] == "Task 1 — summaries and shape":
            summary_path = OUT / "week1_task1_continent_statistics.csv"
            summary = pd.read_csv(summary_path).round(2)
            cells.append({
                "cell_type": "code", "execution_count": 1, "metadata": {},
                "outputs": [{
                    "data": {"text/html": [summary.to_html(index=False)],
                             "text/plain": [summary.to_string(index=False)]},
                    "metadata": {}, "output_type": "display_data",
                }],
                "source": ["display(pd.read_csv(OUT / 'week1_task1_continent_statistics.csv'))\n"],
            })
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": sys.version.split()[0]},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (COURSEWORK / "coursework.ipynb").write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run_all()
