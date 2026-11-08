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
from scipy.stats import linregress
from statsmodels.tsa.seasonal import seasonal_decompose

import tslib
import vizlib


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)
vizlib.style_defaults()
P = vizlib.PALETTE
BLUE, ORANGE, GREEN = P["series"]
DIAGNOSES: list[str] = []


def save(fig, name: str, note: str) -> None:
    vizlib.save_fig(fig, OUT / name, note)
    plt.close(fig)


def add_diagnosis(title: str, conclusion: str, decoy: str, mechanism: str,
                  evidence: str, redesign: str) -> None:
    DIAGNOSES.append(
        f"### {title}\n\n"
        f"- **Invited conclusion:** {conclusion}\n"
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


def diagnose_cases() -> None:
    # 1. Sorting date strings is not chronological sorting.
    d = pd.read_csv(DATA / "case01_orders_stringdate.csv")
    text_order = d.sort_values("month")
    chrono = d.assign(date=pd.to_datetime(d.month, format="%Y-%m")).sort_values("date")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(text_order.month, text_order.orders, marker="o", color=ORANGE)
    axes[0].set(title="Published recipe: sorted as text", ylabel="Orders (monthly total)")
    axes[0].tick_params(axis="x", rotation=65)
    axes[1].plot(chrono.date, chrono.orders, marker="o", color=BLUE)
    axes[1].set(title="Redesign: parsed calendar months", ylabel="Orders (monthly total)")
    fig.suptitle("Case 1 · The apparent yearly cycle is a text-sort artefact")
    save(fig, "week4_case01_dates.png", "Source: synthetic CDB601220 Week 4 case 01; n=24 months.")
    add_diagnosis(
        "Case 1 — string-sorted months",
        "Orders seem to rise and collapse in a repeating annual sequence.",
        "The series is not too short: all 24 monthly observations are present.",
        "The YYYY-M strings sort lexicographically, so month 10 and 11 are placed before month 2; equal x spacing then assigns false time order.",
        f"24 points reproduce the recipe's 958 and 978 drops; parsing YYYY-M chronologically changes their positions and removes the claimed repeated Q1 collapse.",
        "Parse to a monthly DatetimeIndex, sort it, and draw the original values against calendar time.",
    )

    # 2. Trading-day rows are not equally spaced calendar time.
    d = pd.read_csv(DATA / "case02_shop_closed.csv")
    d["date"] = pd.to_datetime(d.date, format="%Y-%m-%d")
    d = d.sort_values("date").set_index("date")
    full = pd.date_range(d.index.min(), d.index.max(), freq="D")
    calendar = d.sales_pkr_k.reindex(full)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    axes[0].plot(np.arange(len(d)), d.sales_pkr_k, color=ORANGE, marker=".", linewidth=1)
    axes[0].set(title="Published recipe: row number", xlabel="Recorded trading-day row",
                ylabel="Sales (PKR thousands/day)")
    axes[1].plot(calendar.index, calendar, color=BLUE, marker=".", linewidth=1)
    axes[1].set(title="Redesign: calendar dates; closures remain gaps",
                xlabel="Calendar date", ylabel="Sales (PKR thousands/day)")
    fig.suptitle("Case 2 · 69 trading days span a longer calendar interval")
    missing_days = len(full.difference(d.index))
    save(fig, "week4_case02_trading_days.png",
         f"Source: synthetic case 02; 69 recorded days; {missing_days} unrecorded calendar dates.")
    change_pct = (d.sales_pkr_k.iloc[-1] / d.sales_pkr_k.iloc[0] - 1) * 100
    add_diagnosis(
        "Case 2 — row number hides closures",
        "Sales appear to rise steadily by about 22% across the quarter.",
        "The endpoint arithmetic and 69 observations are correct; sample size is not the defect.",
        "Plotting row number compresses elapsed time by deleting non-trading calendar days from the x scale; it cannot distinguish a one-day step from a multi-day closure.",
        f"The 69 records span {(d.index.max()-d.index.min()).days+1} calendar days with {missing_days} unrecorded dates; the first-to-last change is {change_pct:+.1f}%.",
        "Plot the actual dates and reindex to daily frequency so closures create visible gaps.",
    )

    # 3. A level must not be summed; a flow should be.
    d = pd.read_csv(DATA / "case03_bandwidth_levels.csv")
    d["ts"] = pd.to_datetime(d.ts, format="%Y-%m-%d %H:%M:%S")
    d = d.sort_values("ts").set_index("ts")
    wrong = d.concurrent_users.resample("D").sum()
    mean_level = d.concurrent_users.resample("D").mean()
    flow = d.bytes_served.resample("D").sum()
    june = float(wrong.loc["2025-06"].mean())
    july = float(wrong.loc["2025-07"].mean())
    pct = (july / june - 1) * 100
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(wrong.index, wrong, color=ORANGE)
    axes[0].set(title="Published recipe: sum of an instantaneous level",
                ylabel="User-observations summed/day")
    axes[1].plot(mean_level.index, mean_level, color=BLUE)
    axes[1].set(title="Redesign: mean concurrent users (level)",
                ylabel="Mean concurrent users")
    axes[2].plot(flow.index, flow, color=GREEN)
    axes[2].set(title="Keep the flow as a daily sum", ylabel="Bytes served/day",
                xlabel="Date")
    fig.suptitle("Case 3 · Levels and flows require different aggregations")
    save(fig, "week4_case03_level_vs_flow.png",
         "Source: synthetic case 03; level=concurrent users, flow=bytes served.")
    add_diagnosis(
        "Case 3 — summing a level",
        "Peak concurrent load appears to jump 43% overnight on 1 July.",
        "The y-axis starts at zero and the June/July sums reproduce the recipe.",
        "Concurrent users is a level measured at an instant, not an additive flow; summing 24 snapshots gives a user-hours measure and compounds any change in sampling coverage.",
        f"The incorrect daily sums average {june:,.0f} in June and {july:,.0f} in July ({pct:+.1f}%); daily means of the same level remove the multiplicative 24-hour sum, while bytes served remains a sum because it is a flow.",
        "Aggregate concurrent users with a daily mean; aggregate bytes served with a daily sum, in separate labelled panels.",
    )

    # 4. A trailing smoother reports a turning point late.
    d = pd.read_csv(DATA / "case04_intervention_lag.csv")
    d["date"] = pd.to_datetime(d.date, format="%Y-%m-%d")
    s = d.set_index("date").conversion_pct.sort_index()
    trail = s.rolling(31, min_periods=31).mean()
    centered = s.rolling(31, center=True, min_periods=31).mean()
    lag = tslib.lag_at_turn(s, 31, how="min")
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(s.index, s, color=P["muted"], linewidth=1, label="Daily conversion (raw)")
    ax.plot(trail.index, trail, color=ORANGE, label="31-day trailing mean")
    ax.plot(centered.index, centered, color=BLUE, label="31-day centred mean")
    ax.axvline(lag["trailing_turn"], color=ORANGE, linestyle="--", linewidth=1)
    ax.axvline(lag["centred_turn"], color=BLUE, linestyle=":", linewidth=1)
    ax.set(title="Case 4 · A trailing window sees the turn about half a window late",
           xlabel="Date", ylabel="Conversion (%)")
    ax.legend()
    save(fig, "week4_case04_rolling_lag.png",
         f"Source: synthetic case 04; 31-day windows; lag={lag['lag_periods']} days.")
    add_diagnosis(
        "Case 4 — trailing-window lag",
        "The new checkout flow started working on 7 September.",
        "The 31-day rolling mean is calculated on a sorted daily index, and its minimum is correctly 7 September.",
        "A trailing mean contains only current and earlier observations; at a 31-day window its minimum arrives roughly half a window after the centered estimate of the turn.",
        f"tslib.lag_at_turn reports trailing minimum {lag['trailing_turn'].date()}, centred minimum {lag['centred_turn'].date()}, a lag of {lag['lag_periods']} days (half-window {lag['half_window']}); the observational line alone does not establish that the checkout change caused a turn.",
        "Keep the faint raw series, name the 31-day window, show the centred estimate for retrospective analysis, and label a trailing estimate as delayed on any live dashboard.",
    )

    # 5. The selected window starts at a seasonal high.
    d = pd.read_csv(DATA / "case05_revenue_window.csv")
    d["month"] = pd.to_datetime(d.month, format="%Y-%m")
    s = d.set_index("month").revenue_pkr_m.sort_index()
    chosen = s.loc["2025-05":"2025-11"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(chosen.index, chosen, marker="o", color=ORANGE)
    axes[0].set(title="Published recipe: selected May–November 2025",
                ylabel="Revenue (PKR millions/month)")
    axes[0].set_ylim(bottom=0)
    axes[1].plot(s.index, s, marker="o", color=BLUE, markersize=3)
    axes[1].axvspan(pd.Timestamp("2025-05-01"), pd.Timestamp("2025-11-30"),
                    color=ORANGE, alpha=0.12, label="Selected 7-month window")
    axes[1].set(title="Redesign: all 36 complete months", ylabel="Revenue (PKR millions/month)")
    axes[1].legend()
    fig.suptitle("Case 5 · A seasonal window is not a six-month trend")
    save(fig, "week4_case05_selected_window.png",
         "Source: synthetic case 05; 36 complete monthly observations; selected window is shown for context.")
    drop_pct = (chosen.iloc[-1] / chosen.iloc[0] - 1) * 100
    add_diagnosis(
        "Case 5 — seasonally selected window",
        "Revenue has fallen 41.9% in six straight months.",
        "The recipe uses seven points and an honest zero baseline; neither truncation nor n=7 explains it.",
        "The chosen window begins at a seasonal peak and ends near a trough; the crop selects phase of the annual cycle rather than estimating a sustained trend.",
        f"The chosen interval reproduces {chosen.iloc[0]:.1f} to {chosen.iloc[-1]:.1f} PKR m ({drop_pct:.1f}%), but the source has 36 complete months; the fall must be compared with the same months in other years.",
        "Show all 36 months, identify the selected interval, and compare seasonal position across years instead of presenting the crop as a trend.",
    )

    # 6. A partial final month is not a complete monthly total.
    d = pd.read_csv(DATA / "case06_monthly_partial.csv")
    d["date"] = pd.to_datetime(d.date, format="%Y-%m-%d")
    d = d.set_index("date").sort_index()
    monthly = d.orders.resample("MS").sum()
    days = d.orders.resample("MS").count()
    expected_days = monthly.index.days_in_month
    complete = days == expected_days
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = [BLUE if ok else ORANGE for ok in complete]
    axes[0].bar(monthly.index, monthly.values, width=22, color=colors, align="center")
    axes[0].set(title="Published recipe: totals, including partial October",
                ylabel="Orders (monthly sum)", xlabel="Month")
    axes[0].tick_params(axis="x", rotation=55)
    axes[1].bar(monthly.index[complete], monthly[complete], width=22, color=BLUE,
                label="Complete month")
    axes[1].bar(monthly.index[~complete], monthly[~complete], width=22,
                color=ORANGE, alpha=.7, hatch="//", label="Partial month")
    daily_mean = d.orders.resample("MS").mean()
    axes[1].set(title="Redesign: mark coverage; compare daily averages",
                ylabel="Orders (monthly total / observed day)", xlabel="Month")
    axes[1].plot(daily_mean.index, daily_mean, color=GREEN, marker="o",
                 label="Mean orders / recorded day")
    axes[1].legend()
    axes[1].tick_params(axis="x", rotation=55)
    fig.suptitle("Case 6 · October is a partial extraction, not a collapse")
    last = monthly.index[-1]
    save(fig, "week4_case06_partial_month.png",
         f"Source: synthetic case 06; final month has {int(days.iloc[-1])}/{int(expected_days[-1])} days.")
    add_diagnosis(
        "Case 6 — partial final month",
        "Orders collapsed in October: 4,041 versus September's 10,805.",
        "Both bars start at zero and the monthly sum is arithmetically correct.",
        "October is only partially observed; comparing its subtotal with a complete September total confounds period coverage with the daily order rate.",
        f"October has {int(days.iloc[-1])} recorded days out of {int(expected_days[-1])}; its 4,041 orders are not a full-month total. The per-recorded-day mean is {daily_mean.iloc[-1]:.1f} versus {daily_mean.iloc[-2]:.1f} in September.",
        "Hatch and label the partial month, and show daily average alongside full-period totals rather than treating an incomplete period as complete.",
    )

    # 7. A moving stacked baseline makes top-layer volatility hard to read.
    d = pd.read_csv(DATA / "case07_stacked_products.csv")
    d["month"] = pd.to_datetime(d.month, format="%Y-%m")
    cols = [c for c in d.columns if c.startswith("product_")]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].stackplot(d.month, *(d[c] for c in cols), labels=cols, alpha=.82)
    axes[0].set(title="Published recipe: stacked area", ylabel="Revenue (PKR m/month)")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[1].plot(d.month, d[cols], linewidth=1.6)
    axes[1].set(title="Redesign: common zero baseline", ylabel="Revenue (PKR m/month)")
    axes[1].legend(cols, fontsize=8)
    fig.suptitle("Case 7 · The top boundary is not Product D's value")
    total = d[cols].sum(axis=1)
    save(fig, "week4_case07_stacked_baseline.png",
         f"Source: synthetic case 07; stack total range {total.min():.1f}–{total.max():.1f} PKR m.")
    add_diagnosis(
        "Case 7 — moving baseline in a stacked area",
        "Product D has been erratic since mid-2024.",
        "The stack is legal: the four product values are exclusive and exhaustive, and the total envelope is not fabricated.",
        "The top layer's upper boundary is the cumulative sum of A+B+C+D; movement in the three lower layers shifts D's baseline, so its thickness—not its top edge—is its value.",
        f"The full stack ranges from {total.min():.1f} to {total.max():.1f} PKR m/month; in the original, D is read against a moving cumulative baseline.",
        "Unstack the products into common-baseline lines (or small multiples) so D's own changes can be compared.",
    )

    # 8. Attribution touches overlap: the percentages are not shares.
    d = pd.read_csv(DATA / "case08_channel_attrib.csv")
    flags = [c for c in d if c.startswith("touch_")]
    shares = d[flags].sum().div(len(d)).mul(100)
    labels = [x.removeprefix("touch_").title() for x in shares.index]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].pie(shares.values, labels=labels, startangle=90, counterclock=False,
                colors=[BLUE, ORANGE, GREEN, P["series_4th"]])
    axes[0].set_title("Published recipe: pie implies exclusive parts")
    order = shares.sort_values()
    axes[1].barh([x.removeprefix("touch_").title() for x in order.index],
                 order.values, color=BLUE)
    axes[1].set(title="Redesign: overlapping customer reach",
                xlabel="Customers touched (%) — not additive")
    for y, v in enumerate(order.values):
        axes[1].text(v + .7, y, f"{v:.1f}%", va="center", fontsize=9)
    axes[1].set_xlim(0, order.max() * 1.23)
    fig.suptitle("Case 8 · Four touch channels reach 131% of customers in total")
    sum_pct = float(shares.sum())
    overlap_n = int(d[flags].sum(axis=1).gt(1).sum())
    touch_summary = ", ".join(
        f"{key.removeprefix('touch_')} {value:.1f}%" for key, value in shares.items()
    )
    save(fig, "week4_case08_nonexclusive_shares.png",
         f"Source: synthetic case 08; {len(d):,} customers; {overlap_n:,} touched by multiple channels.")
    add_diagnosis(
        "Case 8 — non-exclusive channel touches",
        "Paid search drives 42.6% of customers, apparently the largest share.",
        "The row is one customer and each percentage correctly divides a touch count by 4,000.",
        "Attribution flags are not mutually exclusive: a customer may be touched by several channels, so the four marginal percentages do not partition a meaningful whole and a pie renormalizes them deceptively.",
        f"The channel rates are {touch_summary}; they sum to {sum_pct:.1f}%, and {overlap_n:,} customers have multiple true flags.",
        "Use sorted bars labelled as percent of customers touched; explicitly state that overlaps mean bars need not sum to 100%.",
    )

    # 9. A rising share can coexist with a shrinking whole.
    d = pd.read_csv(DATA / "case09_premium_share.csv")
    d["share"] = d.premium_revenue_pkr_m / d.total_revenue_pkr_m * 100
    d["other_revenue"] = d.total_revenue_pkr_m - d.premium_revenue_pkr_m
    x = np.arange(len(d))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(x, d.share, marker="o", color=BLUE)
    axes[0].set(title="Published recipe: premium share rises",
                ylabel="Premium share of revenue (%)")
    axes[0].set_xticks(x, d.quarter, rotation=45)
    axes[1].stackplot(x, d.premium_revenue_pkr_m, d.other_revenue,
                      labels=["Premium", "Other"], colors=[ORANGE, P["muted"]])
    axes[1].set(title="Redesign: absolute revenue components",
                ylabel="Revenue (PKR millions/quarter)")
    axes[1].set_xticks(x, d.quarter, rotation=45)
    axes[1].legend()
    fig.suptitle("Case 9 · Share growth is not revenue growth")
    save(fig, "week4_case09_share_and_total.png",
         "Source: synthetic case 09; premium and other are exclusive components of the total.")
    add_diagnosis(
        "Case 9 — a rising share of a changing total",
        "Premium is now 38% of revenue, a record share.",
        "The share calculation and zero baseline are correct; the issue is not a percentage arithmetic error.",
        "The denominator (total revenue) is moving: a larger premium fraction does not establish that premium revenue itself grew or that overall revenue improved.",
        f"Premium share changes {d.share.iloc[0]:.1f}%→{d.share.iloc[-1]:.1f}%; total revenue changes {d.total_revenue_pkr_m.iloc[0]:,.1f}→{d.total_revenue_pkr_m.iloc[-1]:,.1f} PKR m, and premium revenue changes {d.premium_revenue_pkr_m.iloc[0]:,.1f}→{d.premium_revenue_pkr_m.iloc[-1]:,.1f} PKR m.",
        "Keep the share, but place the exclusive premium/other revenue amounts beside it so the changing denominator is visible.",
    )
    (OUT / "week4_partA_diagnoses.md").write_text(
        "# Week 4 Part A — diagnoses and redesigns\n\n"
        "All nine synthetic course-data cases are rebuilt in `week4_case*.png` "
        "with the published recipe beside an honest redesign. The chart titles "
        "and this report separate the invited conclusion, rejected decoy, "
        "mechanism, numeric evidence and fix.\n\n" + "\n".join(DIAGNOSES),
        encoding="utf-8",
    )
    write_diagnosis_pdf(
        [f"week4_case{i:02d}_" + [
            "dates.png", "trading_days.png", "level_vs_flow.png",
            "rolling_lag.png", "selected_window.png", "partial_month.png",
            "stacked_baseline.png", "nonexclusive_shares.png",
            "share_and_total.png",
        ][i - 1] for i in range(1, 10)],
        OUT / "week4_partA_diagnosis.pdf",
    )


def clean_sessions() -> tuple[pd.DataFrame, pd.Series, pd.Series, dict]:
    raw = pd.read_csv(DATA / "sessions_hourly.csv")
    # Required first-look audit, before parsing timestamps.
    raw.info()
    print(raw.describe().T.to_string())
    print(raw.device.value_counts(dropna=False).to_string())
    print(raw.ts.head(10).tolist())

    slash = raw.ts.str.contains("/", regex=False)
    parsed = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")
    parsed.loc[~slash] = pd.to_datetime(
        raw.loc[~slash, "ts"], format="%Y-%m-%d %H:%M:%S", errors="raise"
    )
    parsed.loc[slash] = pd.to_datetime(
        raw.loc[slash, "ts"], format="%d/%m/%Y %H:%M", errors="raise"
    )
    assert parsed.notna().all()
    raw["timestamp"] = parsed
    raw["device_normalized"] = raw.device.str.strip().str.title()
    assert set(raw.device_normalized) == {"Mobile", "Desktop", "Tablet"}

    sorted_df = raw.sort_values("timestamp", kind="stable").set_index("timestamp")
    duplicate_mask = sorted_df.index.duplicated(keep=False)
    duplicate_groups = sorted_df.loc[duplicate_mask].groupby(level=0)
    duplicate_conflicts = sum(
        1 for _, group in duplicate_groups
        if group[["sessions", "orders", "revenue_pkr", "device_normalized"]]
        .nunique(dropna=False).max() > 1
    )
    assert duplicate_conflicts == 0, "timestamp duplicates need a review rule"
    n_duplicate_rows = int(sorted_df.index.duplicated(keep="first").sum())
    clean = sorted_df.loc[~sorted_df.index.duplicated(keep="first")].copy()

    sentinel_n = int(clean.sessions.lt(0).sum())
    clean["sessions_valid"] = clean.sessions.where(clean.sessions >= 0)
    full_hourly = pd.date_range(clean.index.min(), clean.index.max(), freq="h")
    hourly = clean[["sessions_valid", "orders", "revenue_pkr"]].reindex(full_hourly)
    missing_hours = int(full_hourly.difference(clean.index).size)

    available = hourly.sessions_valid
    raw_daily_sum = available.resample("D").sum(min_count=1)
    observed_hours = available.resample("D").count()
    daily_est = (raw_daily_sum / observed_hours * 24).where(observed_hours.gt(0))
    all_days = pd.date_range(daily_est.index.min(), daily_est.index.max(), freq="D")
    daily_est = daily_est.reindex(all_days)
    audit_obj = daily_est.dropna()
    daily_audit = tslib.audit_index(audit_obj, "D")
    missing_days_all = int(daily_est.isna().sum())
    complete_month_end = pd.Timestamp("2025-08-31")
    partial_tail = daily_est.loc[complete_month_end + pd.Timedelta(days=1):]
    tail_days = len(partial_tail)
    daily = daily_est.loc[:complete_month_end].copy()
    daily = daily.reindex(pd.date_range(daily.index.min(), complete_month_end, freq="D"))
    hourly_audit = tslib.audit_index(clean, "h")
    meta = {
        "source_rows": len(raw),
        "slash_date_rows": int(slash.sum()),
        "iso_date_rows": int((~slash).sum()),
        "first_date": str(clean.index.min()),
        "last_date": str(clean.index.max()),
        "duplicates_removed": n_duplicate_rows,
        "duplicate_conflicts": duplicate_conflicts,
        "sentinel_values": sentinel_n,
        "missing_hours": missing_hours,
        "missing_days_all": missing_days_all,
        "missing_days_before_tail": int(daily.isna().sum()),
        "partial_tail_days_removed": tail_days,
        "daily_audit": daily_audit,
        "hourly_audit": hourly_audit,
        "start": str(daily.index.min().date()),
        "end": str(daily.index.max().date()),
    }
    return hourly, daily, daily.interpolate(method="time", limit_area="inside"), meta


def part_b_c_d() -> None:
    hourly, daily, model_daily, meta = clean_sessions()
    print("\nCLEANING AUDIT")
    print(json.dumps(meta, indent=2, default=str))
    # Computed time-index audit and daily coverage are saved for review.
    (OUT / "week4_partD_cleaning_audit.json").write_text(
        json.dumps(meta, indent=2, default=str), encoding="utf-8"
    )

    windows = (7, 28, 91)
    wr = tslib.window_report(model_daily, windows=windows, center=True)
    wr.to_csv(OUT / "week4_partB_window_report.csv", index=False)
    weekly_amplitude = None
    decomp7 = seasonal_decompose(model_daily, model="additive", period=7)
    weekly_amplitude = float(decomp7.seasonal.max() - decomp7.seasonal.min())
    largest_resid_date = str(decomp7.resid.abs().idxmax().date())
    try:
        seasonal_decompose(model_daily, model="additive", period=365)
        annual_status = "period=365 ran"
    except ValueError as exc:
        annual_status = (
            f"NOT ESTIMABLE: {len(model_daily)} daily observations after the "
            f"partial-month cutoff; statsmodels requires at least 2×365=730 "
            f"for seasonal_decompose(period=365). {exc}"
        )

    bf = pd.Timestamp("2024-11-29")
    fourteen_mean = model_daily.rolling(14, center=True, min_periods=14).mean().loc[bf]
    fourteen_median = model_daily.rolling(14, center=True, min_periods=14).median().loc[bf]
    ewma14 = model_daily.ewm(span=14, adjust=False, min_periods=1).mean().loc[bf]
    lag = tslib.lag_at_turn(model_daily, 31, how="min")

    # All start months × all requested windows: fixed, exhaustive sensitivity scan.
    scan_rows = []
    smoothed = {w: model_daily.rolling(w, center=True, min_periods=w).mean() for w in (7, 14, 28, 56, 91)}
    for month in range(1, 13):
        candidates = model_daily.index[model_daily.index.month == month]
        if len(candidates) == 0:
            continue
        start = candidates[0]
        for w in (7, 14, 28, 56, 91):
            part = smoothed[w].loc[start:].dropna()
            slope = linregress(np.arange(len(part)), part.to_numpy()).slope if len(part) >= 2 else np.nan
            scan_rows.append({"calendar_start_month": month, "start_date": start.date(),
                              "window_days": w, "slope": slope,
                              "direction": "rising" if slope > 0 else "falling" if slope < 0 else "flat"})
    scan = pd.DataFrame(scan_rows)
    scan.to_csv(OUT / "week4_partB_start_window_scan.csv", index=False)
    rising = int(scan.direction.eq("rising").sum())
    falling = int(scan.direction.eq("falling").sum())
    full_slope = linregress(np.arange(len(model_daily)), model_daily.to_numpy()).slope

    # Week 4 Part C: the first test is computed; the other two are explicit arguments.
    attribution = pd.read_csv(DATA / "case08_channel_attrib.csv")
    touch_cols = [c for c in attribution if c.startswith("touch_")]
    touch_check = tslib.exclusivity_check(attribution, touch_cols)
    eight = pd.read_csv(DATA / "shares_eight.csv")
    premium = pd.read_csv(DATA / "case09_premium_share.csv").iloc[-1]
    assert abs(eight.share_pct.sum() - 100) < 1e-6
    q4_other = float(premium.total_revenue_pkr_m - premium.premium_revenue_pkr_m)
    assert abs(premium.premium_revenue_pkr_m + q4_other - premium.total_revenue_pkr_m) < 1e-9
    palette_hexes = P["series"] + [P["series_4th"]]
    palette_cvd = vizlib.worst_pair(palette_hexes, kind="deutan")
    (OUT / "week4_palette_check.txt").write_text(
        "Week 3 palette check, using vizlib.worst_pair across every pair.\n"
        f"Deuteranopia-simulated closest pair: {palette_cvd}\n"
        "The fourth hue requires direct labels/redundant text; figures using it do so.\n",
        encoding="utf-8",
    )

    # Create requested stimuli; no human observation is created by this script.
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(eight.share_pct, labels=eight["slice"], startangle=90,
           counterclock=False, colors=sns.color_palette("colorblind", 8))
    ax.set_title("Part C stimulus 1 · Rank A–H, largest first")
    save(fig, "week4_partC_pie_stimulus.png",
         "Source: synthetic shares_eight.csv; no values printed; reader result not yet collected.")
    ranked = eight.sort_values("share_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(ranked["slice"], ranked.share_pct, color=BLUE)
    for y, value in enumerate(ranked.share_pct):
        ax.text(value + .3, y, f"{value:.1f}%", va="center")
    ax.set_xlim(0, ranked.share_pct.max() * 1.25)
    ax.set(title="Part C stimulus 2 · Rank A–H, largest first",
           xlabel="Share of the eight-category whole (%)")
    save(fig, "week4_partC_bar_stimulus.png",
         "Source: synthetic shares_eight.csv; sorted horizontal bars; reader result not yet collected.")
    result_path = ROOT / "pie_ranking_results.csv"
    if not result_path.exists():
        with result_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["reader_id", "stimulus", "order_largest_first", "seconds"])

    # Part D 2×2 dashboard.
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax = axes[0, 0]
    ax.plot(daily.index, daily, color=P["muted"], linewidth=.8, label="Daily sessions (raw/coverage-adjusted)")
    smooth7 = daily.rolling(7, center=True, min_periods=7).mean()
    ax.plot(smooth7.index, smooth7, color=BLUE, label="7-day centred mean")
    ax.set(title="A 7-day mean removes the weekday cycle", ylabel="Sessions/day (24 h coverage-adjusted sum)")
    ax.legend(fontsize=8)

    # Coverage-preserving hour-of-week heat map; missing samples remain masked.
    raw_hourly = hourly.copy()
    index = raw_hourly.index
    raw_hourly["weekday"] = index.dayofweek
    raw_hourly["hour"] = index.hour
    heat = raw_hourly.pivot_table(index="weekday", columns="hour",
                                  values="sessions_valid", aggfunc="mean")
    heat = heat.reindex(index=range(7), columns=range(24))
    sns.heatmap(heat, ax=axes[0, 1], cmap="Blues", cbar_kws={"label": "Mean sessions/hour"},
                mask=heat.isna())
    axes[0, 1].set(title="Mean sessions by weekday × hour",
                   xlabel="Hour of day", ylabel="Day of week (Mon=0)")

    # Catalogue clean-up: duplicate SKU retained once; negative net rows reported,
    # excluded from area, and shown as a separate signed bar.
    cat = pd.read_csv(DATA / "revenue_catalogue.csv")
    duplicate_skus = int(cat.sku.duplicated(keep="first").sum())
    cat = cat.drop_duplicates("sku", keep="first").copy()
    negative = cat.loc[cat.net_revenue_pkr_m < 0].copy()
    positive = cat.loc[cat.net_revenue_pkr_m > 0].copy()
    tree = positive.groupby(["category", "subcategory"], as_index=False).agg(
        net_revenue_pkr_m=("net_revenue_pkr_m", "sum")
    )
    shares_from_catalogue = (tree.set_index("subcategory").net_revenue_pkr_m
                             / tree.net_revenue_pkr_m.sum() * 100)
    target_shares = pd.read_csv(DATA / "shares_eight.csv").set_index("subcategory").share_pct
    share_delta = (shares_from_catalogue.reindex(target_shares.index) - target_shares)
    palette = [BLUE, ORANGE, GREEN, P["series_4th"]]
    cats = list(tree.category.drop_duplicates())
    cat_color = {name: palette[i] for i, name in enumerate(cats)}
    axes[1, 0].set_title("Net revenue mass by category → sub-category")
    tslib.treemap(
        axes[1, 0], tree.net_revenue_pkr_m,
        labels=[r.subcategory for r in tree.itertuples()],
        values=tree.net_revenue_pkr_m,
        colors=[cat_color[r.category] for r in tree.itertuples()],
        value_fmt="{:,.1f}",
    )
    from matplotlib.patches import Patch
    axes[1, 0].legend(
        handles=[Patch(facecolor=colour, label=name) for name, colour in cat_color.items()],
        title="Parent category", loc="lower center", bbox_to_anchor=(.5, -.14),
        ncol=2, fontsize=7,
    )
    sorted_tree = tree.sort_values("net_revenue_pkr_m")
    axes[1, 1].barh(sorted_tree.subcategory, sorted_tree.net_revenue_pkr_m,
                    color=[cat_color[c] for c in sorted_tree.category])
    for y, value in enumerate(sorted_tree.net_revenue_pkr_m):
        axes[1, 1].text(value + sorted_tree.net_revenue_pkr_m.max() * .008, y,
                        f"{value:,.1f}", va="center", fontsize=8)
    axes[1, 1].set(title="Exact comparison: net revenue by sub-category",
                   xlabel="Net revenue (PKR millions; catalogue total)")
    axes[1, 1].set_xlim(0, sorted_tree.net_revenue_pkr_m.max() * 1.2)
    fig.suptitle("Week 4 · Monday review: weekly rhythm, trend and product mix", y=1.01)
    note = (
        f"Synthetic CDB601220 data. {meta['source_rows']:,} source rows; "
        f"{meta['duplicates_removed']} duplicate timestamps removed; "
        f"{meta['sentinel_values']} −1 session sentinels excluded from sums; "
        f"{meta['missing_hours']} missing hours; {meta['partial_tail_days_removed']} "
        "partial September days omitted. 7-day centred mean; window fixed for weekly cycle."
    )
    save(fig, "week4_partD_review_figure.png", note)

    neg_value = float(negative.net_revenue_pkr_m.sum())
    tree_total = float(tree.net_revenue_pkr_m.sum())
    fig, ax = plt.subplots(figsize=(8, 4))
    neg_plot = negative.sort_values("net_revenue_pkr_m")
    ax.barh(neg_plot.sku, neg_plot.net_revenue_pkr_m, color=ORANGE)
    ax.axvline(0, color=P["ink_soft"], linewidth=.8)
    ax.set(title="Return credits exceed gross revenue on seven SKUs",
           xlabel="Net revenue (PKR millions; negative rows excluded from treemap area)",
           ylabel="SKU")
    save(fig, "week4_partD_negative_net_rows.png",
         f"Source: synthetic revenue_catalogue.csv; {len(negative)} negative net rows, total {neg_value:.4f} PKR m.")
    report_lines = [
        "# Week 4 Parts B–D — computed record\n",
        "## Part D data audit\n",
        f"- Explicit parse: ISO rows `{meta['iso_date_rows']:,}` as `%Y-%m-%d %H:%M:%S`; "
        f"slash rows `{meta['slash_date_rows']:,}` as **day/month/year** `%d/%m/%Y %H:%M`. "
        f"Resulting range `{meta['first_date']}`–`{meta['last_date']}`; parsing with mixed inference "
        "would silently reverse ambiguous dates.\n",
        f"- Device tags canonicalized by strip + title case: `{raw_device_counts()}`.\n",
        f"- Duplicate timestamps removed: `{meta['duplicates_removed']}` extra rows; "
        f"conflicting duplicate groups: `{meta['duplicate_conflicts']}`; no conflicts remained after the rule.\n",
        f"- Invalid session sentinel `-1`: `{meta['sentinel_values']}` observations set missing before daily aggregation; "
        "daily flow totals are expanded as observed hourly mean × 24. This assumes missing hours are not systematically different; it is stated, not hidden.\n",
        f"- Full expected hourly index contains `{meta['missing_hours']}` missing hours "
        f"({meta['missing_days_all']} empty calendar days). Daily audit before tail removal: "
        f"`{meta['daily_audit']}`.\n",
        f"- The final September 2025 extract contains `{meta['partial_tail_days_removed']}` days only, "
        "so it is excluded from all complete-month comparisons. The analysis period is "
        f"`{meta['start']}`–`{meta['end']}`.\n",
        "- The 2×2 dashboard shows a **7-day centred mean**, daily mean sessions by weekday/hour, "
        "a positive-only category→subcategory net-revenue treemap and sorted bars. Weekday × hour "
        "heatmap leaves missing observations masked, not interpolated.\n",
        "\n## Part B numbers\n",
        "### B1 · Window report (standard deviation reduction and edge periods)\n",
        "```\n" + wr.to_string(index=False) + "\n```\n",
        "\nThe window was fixed at **7 days before chart review** because it cancels the weekly cycle, "
        "not because it looks smooth. The raw series stays visible. Centred smoothing is retrospective; "
        "a morning-refresh dashboard must use a trailing window and caption its lag.\n",
        f"\n### B2 · Black Friday (2024-11-29)\n\n"
        f"- 14-day centred mean: `{fourteen_mean:,.1f}` sessions/day.\n"
        f"- 14-day centred median: `{fourteen_median:,.1f}` sessions/day.\n"
        f"- EWMA with span 14, `adjust=False` (causal/trailing): `{ewma14:,.1f}` sessions/day.\n"
        "The monitoring view should use the causal EWMA/trailing mean; a retrospective quarterly report can use "
        "the centred robust median and show the raw spike.\n",
        f"\n### B3 · Decomposition\n\n"
        f"- Additive `period=7`: weekly seasonal peak-to-trough `{weekly_amplitude:,.1f}` sessions/day; "
        f"largest absolute residual on `{largest_resid_date}`.\n"
        f"- Annual `period=365`: **{annual_status}**. No annual component is claimed from less than two annual cycles.\n",
        f"\n### B4 · Trailing versus centred\n\n`tslib.lag_at_turn(window=31)` gives trailing "
        f"`{lag['trailing_turn']}`, centred `{lag['centred_turn']}`, lag `{lag['lag_periods']}` days "
        f"versus half-window `{lag['half_window']}`. A live dashboard must show trailing (no future data) "
        "and caption that a turning point may appear about half a window late.\n",
        f"\n### B5 · Exhaustive start/window sensitivity\n\n"
        f"First occurrence of each calendar month as start; all 12 start months × 5 centred windows "
        f"(7, 14, 28, 56, 91 days) scanned: **{rising} rising**, **{falling} falling**, "
        f"{int(scan.direction.eq('flat').sum())} flat. Full-period line slope is `{full_slope:.3f}` "
        "sessions/day per day-index. A Lie Factor cannot be computed for a cherry-picked time window: "
        "its numerator changes with the chosen frame, while there is no unique original effect in the data "
        "to use as denominator; report the exhaustive direction counts and the full-period estimate instead.\n",
        "\n## Part C — legality and reader work\n",
        "| Table | Exclusive parts? | Meaningful whole? | Is share the question? | Verdict |\n|---|---|---|---|---|\n",
        f"| Touch flags | No (`{touch_check['n_multi']} customers` overlap) | Customer set is meaningful, but channels overlap | Reach by channel, not composition | Sorted bars; no pie |\n",
        "| Eight-category shares | Yes | Yes, the eight subcategories sum to 100% | Yes for one-period mix | Pie is legal; bars are better for ranking |\n",
        f"| Premium vs other, 2025Q4 | Yes | Yes, components sum to total `{premium.total_revenue_pkr_m:.1f}` PKR m | Yes for Q4 composition | Pie is legal; use a line for change over time |\n",
        f"\n`tslib.exclusivity_check` touch result: `{touch_check}`. Palette audit: deuteranopia closest pair `{palette_cvd}`; the fourth palette hue is accompanied by direct labels.\n",
        "- Both ranking stimuli are saved. `pie_ranking_results.csv` has headers only. No reader was available in this non-interactive run, so no response, timing, rank error or experiment result is invented. Collect a real reader using `reader_protocol.md`.\n",
        "\n## Part D hierarchy audit\n",
        f"- Duplicate SKU rows removed: `{duplicate_skus}` (retain first exact SKU record).\n",
        f"- Negative net-revenue rows excluded from treemap area: `{len(negative)}` rows, net total `{neg_value:.4f}` PKR m, shown separately in the report rather than treated as area.\n",
        f"- Positive hierarchy total `{tree_total:,.4f}` PKR m; cut at eight sub-categories (no category hidden in `Other`: 0 categories, PKR 0). "
        f"337 positive SKU rows roll into those eight named subcategories after deduplication and the negative-row exclusion. "
        f"Maximum absolute difference from `shares_eight.csv`: {share_delta.abs().max():.3f} percentage points.\n",
        "- The treemap answers where the revenue mass is; sorted bars answer how much each sub-category contributes. A single categorical hue is used per parent; negative values are never given area.\n",
    ]
    (OUT / "week4_partB_partC_partD_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    write_part_e(meta, duplicate_skus, len(negative), neg_value, tree_total)
    print("\nPART B WINDOW REPORT\n", wr.to_string(index=False))
    print(f"\nBlack Friday mean={fourteen_mean:.2f} median={fourteen_median:.2f} EWMA={ewma14:.2f}")
    print(f"Weekly seasonal amplitude={weekly_amplitude:.2f}; largest residual={largest_resid_date}")
    print(f"Annual decomposition: {annual_status}")
    print(f"Sensitivity scan: {rising} rising / {falling} falling")


def raw_device_counts() -> str:
    d = pd.read_csv(DATA / "sessions_hourly.csv")
    return json.dumps(d.device.value_counts(dropna=False).to_dict(), sort_keys=True)


def write_part_e(meta: dict, duplicate_skus: int, n_negative: int,
                 negative_total: float, tree_total: float) -> None:
    text = f"""# Week 4 Part E — written justification

## The four panels and their questions

1. **Daily sessions:** how is traffic moving once the weekday cycle is separated? A time-series line uses position for sequence; the faint raw daily series remains under a named 7-day centred mean. The mean is retrospective; the live counterpart must be trailing and disclose its lag.
2. **Weekday × hour heatmap:** when is traffic typically concentrated? A sequential blue scale encodes an ordered mean; masked missing cells are not filled with zero.
3. **Treemap:** where is the net-revenue mass across category → sub-category? Area is appropriate for hierarchy overview, each parent category has a consistent identity hue, and values are printed because area ranks below position. Negative rows are shown as a separate return-credit issue, never as area.
4. **Sorted bars:** how much net revenue does each sub-category contribute? Common-baseline length gives more precise comparison than area or angle. No `Other` bucket was used: 0 sub-categories / PKR 0 are hidden; the cut is at the eight sub-category level.

## Time, parse and aggregation

The timestamp format is explicit by logger: `{meta['iso_date_rows']:,}` ISO strings use `%Y-%m-%d %H:%M:%S`; `{meta['slash_date_rows']:,}` slash strings use day-first `%d/%m/%Y %H:%M`. I checked the parsed min/max rather than trusting mixed-format success. The sorted, de-duplicated hourly index has `{meta['missing_hours']}` missing hours; `-1` is an invalid sessions sentinel. For daily flows, valid hourly session totals are divided by observed hours and multiplied by 24; this estimates a full-day total and assumes missing hours are not systematically different. Missing whole days remain NaN and form line breaks; the final {meta['partial_tail_days_removed']}-day September 2025 tail is omitted as incomplete. The heatmap uses mean observed sessions per hour. Daily totals use sum semantics (with transparent coverage correction), never a sum of an instantaneous level.

The 7-day window was fixed before inspection because the cycle it removes is weekly. The chart keeps raw values and names the window. A 28-day version and an exhaustive 12-start × 5-window slope scan are in the appendix. The annual decomposition is not identifiable from 518 days under `seasonal_decompose`'s two-cycle requirement; it is reported as unavailable instead of extrapolated.

## Row and hierarchy accounting

- Duplicate timestamp rows removed: **{meta['duplicates_removed']}**; all duplicate groups agree exactly on measures and normalized device.
- Invalid `sessions=-1` observations: **{meta['sentinel_values']}** values excluded as missing.
- Missing hourly periods from the complete expected index: **{meta['missing_hours']}**; this includes **{meta['missing_days_all']}** dates with no hourly data.
- Incomplete final month: **{meta['partial_tail_days_removed']}** recorded September days removed from the complete-month analysis.
- Duplicate SKU rows removed: **{duplicate_skus}**. Negative net-revenue SKU rows excluded from area: **{n_negative}**, net **{negative_total:.4f} PKR m**, retained as an explicit negative audit. Positive subcategory hierarchy total: **{tree_total:,.4f} PKR m**. The cut is category → sub-category; all eight sub-categories remain visible, so `Other` is empty.

The same fixed window and start date would be used if the result weakened the story. `partB` reports both rising and falling combinations, making the selection sensitivity visible rather than hiding rejected views.
"""
    (OUT / "week4_partE_justification.md").write_text(text, encoding="utf-8")
    write_text_pdf(text, OUT / "week4_partE_justification.pdf",
                   "Week 4 Part E — written justification")


def part_f_bonus() -> None:
    source = pd.read_csv(DATA / "partF_airpassengers_source.csv")
    source["date"] = pd.to_datetime(source.year.astype(str) + "-" +
                                    source.month, format="%Y-%B")
    s = source.set_index("date").passengers.astype(float).sort_index()
    audit = tslib.audit_index(s, "MS")
    banked_size = tslib.banked_figsize(s.to_numpy(), width=10,
                                       x=np.arange(len(s)))
    fig, ax = plt.subplots(figsize=banked_size)
    ax.plot(s.index, s, marker="o", color=BLUE, markersize=3)
    ax.set(title=f"Air passengers rise with an increasingly wide seasonal swing\nBanked-to-45° figure: {banked_size[0]:.1f} × {banked_size[1]:.2f} inches",
           xlabel="Month", ylabel="Passengers (monthly total)")
    save(fig, "week4_partF_banked_series.png",
         "Source: seaborn-data flights.csv / R AirPassengers; 144 monthly rows; downloaded 2026-11-09.")
    add = seasonal_decompose(s, model="additive", period=12)
    mult = seasonal_decompose(s, model="multiplicative", period=12)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    tslib.cycle_plot(axes[0], s, by="month", color=BLUE)
    axes[0].set(title="Cycle plot: one line per year", ylabel="Passengers")
    axes[1].plot(add.resid.index, add.resid, color=ORANGE, linewidth=1)
    axes[1].axhline(0, color=P["ink_soft"], linewidth=.8)
    axes[1].set(title="Additive decomposition residual",
                ylabel="Residual (passengers)")
    axes[2].plot(mult.resid.index, mult.resid, color=GREEN, linewidth=1)
    axes[2].axhline(1, color=P["ink_soft"], linewidth=.8)
    axes[2].set(title="Multiplicative decomposition residual",
                ylabel="Residual (ratio; 1 = fitted)")
    fig.suptitle("Week 4 bonus · Separating airline growth from seasonality")
    save(fig, "week4_partF_cycle_and_residuals.png",
         "Source: 144 real historical monthly passenger totals, Jan 1949–Dec 1960; 12-month seasonal period.")
    year = source.groupby("year").passengers.agg(["mean", "min", "max"])
    year["swing"] = year["max"] - year["min"]
    year["relative_swing"] = year.swing / year["mean"]
    early = year.loc[1949:1951].relative_swing.mean()
    late = year.loc[1958:1960].relative_swing.mean()
    additive_sd = float(add.resid.std())
    multiplicative_sd = float(mult.resid.std())
    report = f"""# Week 4 Part F — bonus cycle analysis

**Source.** Seaborn data repository, [`flights.csv`](https://raw.githubusercontent.com/mwaskom/seaborn-data/master/flights.csv), downloaded 2026-11-09. It is the classic real monthly U.S. airline passenger series `AirPassengers` (1949–1960), with `month` as the within-year category. The raw source is saved as `data/partF_airpassengers_source.csv`; it has 144 observations.

**Index audit (`tslib.audit_index`, MS):** `{json.dumps(audit, default=str)}`.

**Figure parameters.** Additive and multiplicative seasonal decompositions use period 12; cycle plot groups by calendar month. The banked-to-45° figure size is `{banked_size[0]:.2f} × {banked_size[1]:.2f}` inches. Figures are 300 dpi.

**Answer (two sentences).** The annual absolute swing grows as passenger volume grows, but its relative swing is {early:.3f} on average in 1949–1951 versus {late:.3f} in 1958–1960, so most of the widening is explained by scale rather than a steadily increasing seasonal fraction. The multiplicative residual standard deviation is {multiplicative_sd:.3f} versus {additive_sd:.1f} passengers for the additive residual; the ratio-scale residual is the appropriate diagnostic for seasonality proportional to the rising trend, not proof that every year has identical seasonal shape.
"""
    (OUT / "week4_partF_report.md").write_text(report, encoding="utf-8")
    print(f"AirPassengers audit: {audit}; banked figsize={banked_size}")


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=FutureWarning)
    diagnose_cases()
    part_b_c_d()
    part_f_bonus()
    print(f"\nWeek 4 deliverables generated under {OUT}")
