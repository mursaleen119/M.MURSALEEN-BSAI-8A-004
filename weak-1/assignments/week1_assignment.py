from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "charts"
OUT.mkdir(exist_ok=True)
PALETTE = {"Africa": "#D55E00", "Americas": "#0072B2", "Asia": "#009E73", "Europe": "#CC79A7", "Oceania": "#E69F00"}
plt.rcParams.update({"figure.dpi": 120, "savefig.dpi": 300, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e8ec", "axes.axisbelow": True})


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def task1():
    d = pd.read_csv(DATA / "datasaurus.csv")
    stats = d.groupby("dataset").agg(n=("x", "size"), mean_x=("x", "mean"), mean_y=("y", "mean"), sd_x=("x", "std"), sd_y=("y", "std"), correlation=("x", lambda s: np.nan))
    stats["correlation"] = [g["x"].corr(g["y"]) for _, g in d.groupby("dataset")]
    stats.to_csv(OUT / "week1_task1_statistics.csv", float_format="%.4f")
    fig, ax = plt.subplots(figsize=(9, 5))
    stats[["mean_x", "mean_y", "sd_x", "sd_y", "correlation"]].plot(kind="bar", ax=ax, color=["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"])
    ax.set_title("All 13 datasets have nearly matching summaries", loc="left")
    ax.set_ylabel("Statistic (different units; compare columns only)")
    ax.set_xlabel("Dataset")
    ax.legend(ncol=3, fontsize=8)
    save(fig, "week1_task1_statistics.png")
    names = list(d.dataset.unique())
    fig, axes = plt.subplots(4, 4, figsize=(12, 10), sharex=True, sharey=True)
    for ax, name in zip(axes.flat, names):
        g = d[d.dataset == name]
        ax.scatter(g.x, g.y, s=12, color="#0072B2", alpha=.75, linewidths=0)
        ax.set_title(name, loc="left", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
        for side in ("top", "right", "bottom", "left"): ax.spines[side].set_visible(False)
    for ax in axes.flat[len(names):]: ax.set_visible(False)
    fig.suptitle("Identical-looking summaries hide 13 different point clouds", x=.08, ha="left", fontsize=14, fontweight="bold")
    fig.supxlabel("x"); fig.supylabel("y")
    save(fig, "week1_task1_datasaurus_grid.png")
    print(stats.round(3).to_string())
    print("Interpretation: the means, standard deviations and correlations are close, but shapes include curves, clusters, lines and a dinosaur. More points do not cure information loss: aggregation discards geometry, and the 13 plots remain essential.")


def task2():
    d = pd.read_csv(DATA / "gapminder.csv")
    fig, ax = plt.subplots(figsize=(12, 7))
    for country, g in d.groupby("country"):
        ax.plot(g.year, g.lifeExp, lw=.65, alpha=.65, label=country)
    ax.set_title("BAD EXAMPLE — 142 country lines hide the story", loc="left")
    ax.set_xlabel("Year"); ax.set_ylabel("Life expectancy (years)")
    ax.legend(ncol=8, fontsize=4, bbox_to_anchor=(1.02, 1), loc="upper left")
    save(fig, "week1_task2_bad_spaghetti.png")
    by_cont = d.groupby(["continent", "year"], as_index=False).lifeExp.mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    for cont, g in by_cont.groupby("continent"):
        ax.plot(g.year, g.lifeExp, marker="o", lw=2.2, color=PALETTE[cont], label=cont)
    ax.set_title("Life expectancy rose on every continent", loc="left")
    ax.set_xlabel("Year"); ax.set_ylabel("Mean life expectancy (years)"); ax.legend(title="Continent", ncol=3)
    save(fig, "week1_task2_continent_trends.png")
    picks = ["China", "Rwanda", "Japan"]
    colors = {"China": "#0072B2", "Rwanda": "#D55E00", "Japan": "#009E73"}
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for _, g in d.groupby("country"):
        ax.plot(g.year, g.lifeExp, color="#c9ced3", lw=.7, alpha=.55)
    for country in picks:
        g = d[d.country == country]
        ax.plot(g.year, g.lifeExp, color=colors[country], lw=2.6)
        ax.text(g.year.iloc[-1] + 1, g.lifeExp.iloc[-1], country, color=colors[country], va="center", fontsize=9)
    ax.set_title("Three countries reveal distinct paths through the global rise", loc="left")
    ax.set_xlabel("Year"); ax.set_ylabel("Life expectancy (years)"); ax.set_xlim(1952, 2016)
    ax.text(.01, .01, "142 countries; 3 highlighted, 139 shown in grey; no rows excluded", transform=ax.transAxes, fontsize=8)
    save(fig, "week1_task2_highlights.png")
    yr = d.groupby("year").gdpPercap.agg(richest="max", poorest="min").reset_index()
    yr["richest_to_poorest_ratio"] = yr.richest / yr.poorest
    yr.to_csv(OUT / "week1_task2_income_gap.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(yr.year, yr.richest_to_poorest_ratio, marker="o", color="#0072B2")
    ax.set_title("The richest-to-poorest income ratio did not steadily narrow", loc="left")
    ax.set_xlabel("Year"); ax.set_ylabel("Highest / lowest GDP per capita (ratio)")
    ax.text(.01, .02, "Country extremes by year; GDP per capita is highly skewed", transform=ax.transAxes, fontsize=8)
    save(fig, "week1_task2_income_gap.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(d.gdpPercap, bins=40, color="#0072B2", edgecolor="white"); axes[0].set_title("Linear: low incomes compressed", loc="left")
    axes[1].hist(d.gdpPercap, bins=np.logspace(np.log10(d.gdpPercap.min()), np.log10(d.gdpPercap.max()), 40), color="#D55E00", edgecolor="white"); axes[1].set_xscale("log"); axes[1].set_title("Log x: shape across income decades", loc="left")
    for ax in axes: ax.set_xlabel("GDP per capita (log x in right panel)"); ax.set_ylabel("Country-years")
    save(fig, "week1_task2_gdp_skew.png")
    print("(a) Continental averages reveal broad regional change, smoothing country variation. (b) Highlighting preserves individual paths and outliers, while grey context is still visually dense. The extreme-country ratio uses the same annual country set; it fluctuates and does not provide a simple steadily closing gap. The logarithm changes spacing to show multiplicative differences, not counts.")


def task3():
    d = pd.read_csv(DATA / "penguins.csv")
    meas = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"]
    missing_meas = d[meas].isna().all(axis=1)
    sex_missing = d.sex.isna()
    print(f"Rows={len(d)}; all four measurements missing={int(missing_meas.sum())}; missing sex={int(sex_missing.sum())} (overlap={int((missing_meas & sex_missing).sum())}). Measurement charts exclude all-measurement-missing rows; sex comparison also excludes rows with unknown sex.")
    valid = d.loc[~missing_meas].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(valid.body_mass_g.dropna(), bins=25, color="#0072B2", edgecolor="white")
    ax.set_title("Body mass is multi-peaked across a mixed-species sample", loc="left")
    ax.set_xlabel("Body mass (g)"); ax.set_ylabel("Penguins")
    ax.text(.01, .98, "342 with body-mass data; 2 all-measurement-missing rows excluded", transform=ax.transAxes, va="top", fontsize=8)
    save(fig, "week1_task3_distribution.png")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data=valid, x="body_mass_g", hue="species", bins=25, element="step", stat="count", common_bins=True, ax=ax)
    ax.set_title("Species separate the pooled body-mass humps", loc="left"); ax.set_xlabel("Body mass (g)"); ax.set_ylabel("Penguins")
    ax.text(.01, .98, "2 rows with all four measurements missing excluded", transform=ax.transAxes, va="top", fontsize=8)
    save(fig, "week1_task3_by_species.png")
    rel = valid.dropna(subset=["bill_length_mm", "bill_depth_mm"])
    pooled = rel.bill_length_mm.corr(rel.bill_depth_mm)
    rows = []
    fig, ax = plt.subplots(figsize=(8, 6))
    for species, g in rel.groupby("species"):
        ax.scatter(g.bill_length_mm, g.bill_depth_mm, s=30, alpha=.78, label=species)
        r = g.bill_length_mm.corr(g.bill_depth_mm)
        rows.append({"group": species, "n": len(g), "correlation": r})
    ax.set_title(f"Species mix reverses the pooled bill relationship (r={pooled:.2f})", loc="left")
    ax.set_xlabel("Bill length (mm)"); ax.set_ylabel("Bill depth (mm)"); ax.legend(title="Species")
    ax.text(.01, .01, "Complete bill measurements only; all-measurement missing rows excluded", transform=ax.transAxes, fontsize=8)
    save(fig, "week1_task3_relationship.png")
    rows.append({"group": "All species pooled", "n": len(rel), "correlation": pooled})
    pd.DataFrame(rows).to_csv(OUT / "week1_task3_group_correlations.csv", index=False)
    sex = valid.dropna(subset=["body_mass_g", "sex"])
    avg = sex.groupby(["species", "sex"], as_index=False).body_mass_g.mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=avg, x="species", y="body_mass_g", hue="sex", hue_order=["Female", "Male"], palette={"Female":"#0072B2", "Male":"#D55E00"}, errorbar=None, ax=ax)
    ax.set_title("Average mass differs by both species and sex", loc="left"); ax.set_xlabel("Species"); ax.set_ylabel("Mean body mass (g)")
    ax.text(.01, .98, f"n={len(sex)} known-sex penguins; missing sex excluded", transform=ax.transAxes, va="top", fontsize=8)
    save(fig, "week1_task3_species_sex.png")
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print("The pooled relationship is negative while each within-species correlation is positive: Simpson's paradox / aggregation reversal. Species is associated with both bill size ranges and masks the within-group trend. The sex comparison uses only known-sex records; no sex was imputed.")


def task4():
    d = pd.read_csv(DATA / "mpg.csv")
    colors = {"usa":"#0072B2", "europe":"#D55E00", "japan":"#009E73"}
    byyear = d.groupby("model_year", as_index=False).mpg.mean()
    fig, ax = plt.subplots(figsize=(8, 5)); ax.plot(byyear.model_year + 1900, byyear.mpg, marker="o", color="#0072B2")
    ax.set_title("Fleet fuel economy improved substantially over model years", loc="left"); ax.set_xlabel("Model year"); ax.set_ylabel("Mean fuel economy (mpg)")
    save(fig,"week1_task4_trend.png")
    fig, ax = plt.subplots(figsize=(8, 5)); sns.boxplot(data=d, x="origin", y="mpg", order=["usa","europe","japan"], color="#8bbbd3", ax=ax)
    ax.set_title("Japanese and European cars generally use less fuel", loc="left"); ax.set_xlabel("Origin"); ax.set_ylabel("Fuel economy (mpg)")
    save(fig,"week1_task4_comparison.png")
    fig, ax = plt.subplots(figsize=(8, 5)); ax.scatter(d.weight, d.mpg, c="#0072B2", alpha=.45, s=24, linewidths=0)
    ax.set_title("Heavier cars tend to have lower fuel economy", loc="left"); ax.set_xlabel("Weight (lb)"); ax.set_ylabel("Fuel economy (mpg)")
    save(fig,"week1_task4_relationship.png")
    counts = d.cylinders.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4)); ax.bar(counts.index.astype(str), counts.values, color="#0072B2")
    ax.set_title("Eight-cylinder cars are common, but six cylinders dominate", loc="left"); ax.set_xlabel("Cylinders"); ax.set_ylabel("Cars (count)"); ax.set_ylim(0, counts.max()*1.1)
    save(fig,"week1_task4_cylinders.png")
    mass = d.groupby("model_year", as_index=False).weight.mean()
    fig, ax = plt.subplots(figsize=(8, 5)); ax.plot(mass.model_year + 1900, mass.weight, marker="o", color="#D55E00")
    ax.set_title("Cars got lighter as fleet fuel economy improved", loc="left"); ax.set_xlabel("Model year"); ax.set_ylabel("Mean weight (lb)")
    save(fig,"week1_task4_mechanism.png")
    # Redraw the weakest chart as a direct, sorted horizontal count comparison.
    ordered = counts.sort_values()
    fig, ax = plt.subplots(figsize=(7, 4)); ax.barh(ordered.index.astype(str), ordered.values, color="#0072B2")
    for i, v in enumerate(ordered.values): ax.text(v + 2, i, str(v), va="center", fontsize=8)
    ax.set_title("A sorted count chart makes the dominant engine size clear", loc="left"); ax.set_xlabel("Cars (count; zero baseline)"); ax.set_ylabel("Cylinders"); ax.set_xlim(0, counts.max()*1.15)
    save(fig,"week1_task4_redesign.png")
    print(f"Cars={len(d)}; missing horsepower={int(d.horsepower.isna().sum())}. Horsepower is unused in these five charts, so no rows are excluded from them.")
    print("Chart choices: trend=line over ordered model year; origin comparison=box plot; weight–mpg relationship=scatter; cylinder distribution=bar count; explanatory question=mean weight over time. The redesign sorts and labels the cylinder count bars for easier comparison. Weight and MPG trend together, but this aggregate check does not prove weight alone caused the fleet change.")


def task5():
    d = pd.read_csv(DATA / "flights.csv")
    d["month"] = d.month.str[:3]
    d["month_num"] = pd.Categorical(d.month, categories=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], ordered=True).codes + 1
    d["date"] = pd.to_datetime(dict(year=d.year, month=d.month_num, day=1))
    fig, ax = plt.subplots(figsize=(10, 5)); ax.plot(d.date, d.passengers, color="#0072B2", lw=1.6)
    ax.set_title("Airline passenger totals climbed steadily from 1949 to 1960", loc="left"); ax.set_xlabel("Month"); ax.set_ylabel("Passengers (thousands)")
    save(fig,"week1_task5_time_series.png")
    fig, ax = plt.subplots(figsize=(10, 5))
    for year, g in d.groupby("year"): ax.plot(g.month_num, g.passengers, color="#9aa7b4", alpha=.65, lw=1)
    ax.set_xticks(range(1,13), ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
    ax.set_title("Seasonal shape repeats while the level rises", loc="left"); ax.set_xlabel("Month"); ax.set_ylabel("Passengers (thousands)")
    save(fig,"week1_task5_seasonal.png")
    month = d.groupby("month", as_index=False).passengers.mean().set_index("month").reindex(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]).reset_index()
    fig, ax = plt.subplots(figsize=(8, 4)); ax.bar(month.month, month.passengers, color="#0072B2")
    ax.set_title("July is consistently the busiest month on average", loc="left"); ax.set_xlabel("Month"); ax.set_ylabel("Mean passengers (thousands)"); ax.tick_params(axis="x", rotation=35)
    save(fig,"week1_task5_busiest_month.png")
    d["year_mean"] = d.groupby("year").passengers.transform("mean"); d["seasonal_index"] = d.passengers / d.year_mean
    fig, ax = plt.subplots(figsize=(10, 5))
    for year, g in d.groupby("year"): ax.plot(g.month_num, g.seasonal_index, color="#9aa7b4", alpha=.6, lw=1)
    ax.axhline(1, color="#D55E00", lw=1.8, label="Year's average month")
    ax.set_xticks(range(1,13), ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
    ax.set_title("Relative seasonal swing persists after dividing out annual growth", loc="left"); ax.set_xlabel("Month"); ax.set_ylabel("Monthly passengers / that year's mean"); ax.legend()
    save(fig,"week1_task5_relative_seasonality.png")
    print("Months were explicitly ordered and combined with year into a monthly date. The time series is the report chart; the year-by-month seasonal panel and busiest-month summary answer narrower, partly overlapping questions and should not be placed alongside it without a separate purpose. Normalizing each month by that year's mean separates relative seasonal amplitude from the airline's growing level.")

TASKS = {1: task1, 2: task2, 3: task3, 4: task4, 5: task5}
def run_task(number):
    return TASKS[number]()
def main():
    for n in TASKS: run_task(n)
if __name__ == "__main__": main()
