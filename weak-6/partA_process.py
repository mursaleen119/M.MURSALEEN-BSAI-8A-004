"""Audit, clean, and write Week 6's three raw tables without hand edits."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from week6_common import CLEAN_DIR, RAW_DIR, ROOT, ensure_source_files


def _format_range(series: pd.Series) -> str:
    usable = pd.to_numeric(series, errors="coerce").dropna()
    if usable.empty:
        return "no usable values"
    return f"{usable.min():,.3f} to {usable.max():,.3f}"


def process() -> dict[str, object]:
    """Create clean outputs, the audit, and the decision table."""
    ensure_source_files()
    districts_raw = pd.read_csv(RAW_DIR / "district_grid.csv", dtype={"code": "string"})
    daily_raw = pd.read_csv(RAW_DIR / "grid_daily.csv", dtype={"date": "string"})
    generation_raw = pd.read_csv(RAW_DIR / "generation_mix.csv", dtype={"month": "string"})
    with (RAW_DIR / "regions.geojson").open(encoding="utf-8") as file:
        geojson = json.load(file)

    region_names = {
        feature["properties"]["code"]: feature["properties"]["name"]
        for feature in geojson["features"]
    }
    audit: list[str] = [
        "Week 6 Task A — reproducible raw-data audit and cleaning",
        f"Source revision: {__import__('week6_common').SOURCE_REVISION}",
        "Raw inputs are fetched into ignored weak-6/data/ if absent; raw files are never modified.",
        "",
        "RAW FILE AUDITS",
    ]
    for name, frame, keys in (
        ("district_grid.csv", districts_raw, ["code"]),
        ("grid_daily.csv", daily_raw, ["date", "zone"]),
        ("generation_mix.csv", generation_raw, ["month", "source", "subsource"]),
    ):
        duplicates = int(frame.duplicated(keys).sum())
        audit.append(
            f"{name}: rows={len(frame):,}; dtypes={frame.dtypes.astype(str).to_dict()}; "
            f"key={keys}; unique={frame[keys].drop_duplicates().shape[0]:,}; "
            f"duplicate rows={duplicates}; missing cells={int(frame.isna().sum().sum())}"
        )
    audit.append(f"regions.geojson: features={len(geojson['features'])}; unique codes={len(region_names)}.")
    audit.append("")
    audit.append("DISTRICT REGISTER — FINDINGS AND REPAIRS")

    districts = districts_raw.copy()
    districts["code"] = districts["code"].str.strip().str.upper()
    duplicate_code_rows = districts[districts.duplicated("code", keep=False)].copy()
    duplicate_codes = sorted(duplicate_code_rows["code"].unique())
    dropped_districts = 0
    for code in duplicate_codes:
        group = districts.loc[districts["code"].eq(code)].copy()
        target_name = region_names.get(code)
        exact = group.loc[group["district"].str.casefold().eq(str(target_name).casefold())]
        if len(exact) != 1:
            raise ValueError(f"Cannot resolve duplicate district key {code} using GeoJSON name {target_name!r}.")
        keep_index = exact.index[0]
        dropped_districts += len(group) - 1
        districts = districts.drop(index=group.index.difference([keep_index]))
    audit.append(
        f"District duplicate codes={duplicate_codes}; GeoJSON exact-name match retained the "
        f"canonical row; duplicate rows dropped={dropped_districts}."
    )

    households_before = pd.to_numeric(districts["households"], errors="raise")
    pph_before = districts["population"] / households_before
    suspect_households = pph_before.gt(100)
    if int(suspect_households.sum()) != 1:
        raise ValueError("Expected exactly one implausible persons-per-household record.")
    repaired_code = districts.loc[suspect_households, "code"].iloc[0]
    original_households = int(districts.loc[suspect_households, "households"].iloc[0])
    if repaired_code != "D21" or original_households != 182:
        raise ValueError("The household-count anomaly did not match the audited D21 source value.")
    # The source record's hidden scale is recoverable from the expected aggregate
    # and the neighboring population-per-household range.
    repaired_households = 182_000
    districts.loc[suspect_households, "households"] = repaired_households
    audit.append(
        f"Household denominator anomaly: {repaired_code} had {original_households:,} households "
        f"(population/households={pph_before.loc[suspect_households].iloc[0]:,.1f}); "
        f"repaired to {repaired_households:,} using the evident thousand-unit scale."
    )

    raw_electrification = districts["electrification_pct"].astype("string")
    pct_suffix_rows = int(raw_electrification.str.contains("%", na=False).sum())
    districts["electrification_pct"] = pd.to_numeric(
        raw_electrification.str.replace("%", "", regex=False).str.strip(),
        errors="coerce",
    )
    missing_electrification = int(districts["electrification_pct"].isna().sum())
    outage_sentinels = districts["outage_minutes"].eq(-1)
    outage_sentinel_count = int(outage_sentinels.sum())
    districts.loc[outage_sentinels, "outage_minutes"] = np.nan
    audit.extend(
        [
            f"Electrification values with percent suffix parsed={pct_suffix_rows}; genuine missing values retained={missing_electrification}.",
            f"District outage_minutes=-1 operator sentinels set missing={outage_sentinel_count}.",
            f"District totals after cleaning: rows={len(districts)}, population={districts['population'].sum():,}, "
            f"households={districts['households'].sum():,}; people/household="
            f"{(districts['population'] / districts['households']).min():.2f}–"
            f"{(districts['population'] / districts['households']).max():.2f}.",
            f"Electrification range={_format_range(districts['electrification_pct'])}; "
            f"outage minutes per outage (usable districts)="
            f"{(districts['outage_minutes']/districts['outages']).dropna().min():.1f}–"
            f"{(districts['outage_minutes']/districts['outages']).dropna().max():.1f}.",
        ]
    )

    audit.append("")
    audit.append("DAILY RETURNS — FINDINGS AND REPAIRS")
    daily = daily_raw.copy()
    iso_dates = daily["date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    daily["date"] = pd.NaT
    daily.loc[iso_dates, "date"] = pd.to_datetime(
        daily_raw.loc[iso_dates, "date"], format="%Y-%m-%d", errors="raise"
    )
    daily.loc[~iso_dates, "date"] = pd.to_datetime(
        daily_raw.loc[~iso_dates, "date"], format="%d/%m/%Y", errors="raise"
    )
    alternate_dates = int((~iso_dates).sum())
    duplicate_mask = daily.duplicated(["date", "zone"], keep=False)
    duplicated_keys = daily.loc[duplicate_mask, ["date", "zone"]].drop_duplicates()
    duplicate_rows = int(daily.duplicated(["date", "zone"]).sum())
    conflict_keys = []
    conflicting_duplicate_rows = 0
    for key, group in daily.loc[duplicate_mask].groupby(["date", "zone"], sort=True):
        payloads = group[["cumulative_mwh", "peak_load_mw", "outage_minutes"]].drop_duplicates()
        if len(payloads) > 1:
            conflict_keys.append((str(key[0].date()), key[1]))
            conflicting_duplicate_rows += len(group) - 1
    exact_duplicate_rows = duplicate_rows - conflicting_duplicate_rows
    daily = daily.drop_duplicates(["date", "zone"], keep="first").copy()
    audit.append(
        f"Dates: ISO rows={int(iso_dates.sum()):,}; explicit day-first rows={alternate_dates:,}; "
        f"normalized duplicate date-zone keys={len(duplicated_keys)}; exact duplicate rows removed={exact_duplicate_rows}; "
        f"conflicting resubmission rows removed={conflicting_duplicate_rows}; "
        f"conflicting duplicate keys={conflict_keys}. First source row retained deterministically."
    )
    daily["peak_load_mw"] = pd.to_numeric(daily["peak_load_mw"], errors="raise")
    peak_sentinels = daily["peak_load_mw"].eq(-1)
    peak_sentinel_count = int(peak_sentinels.sum())
    daily.loc[peak_sentinels, "peak_load_mw"] = np.nan
    daily = daily.sort_values(["zone", "date"], kind="stable").reset_index(drop=True)
    previous_meter = daily.groupby("zone", sort=False)["cumulative_mwh"].shift()
    meter_drop = daily["cumulative_mwh"].lt(previous_meter)
    meter_drop_count = int(meter_drop.sum())
    if meter_drop_count != 1:
        raise ValueError(f"Expected one downward cumulative-meter reading, found {meter_drop_count}.")
    bad_meter_rows = daily.loc[meter_drop, ["date", "zone", "cumulative_mwh"]]
    daily.loc[meter_drop, "cumulative_mwh"] = np.nan
    dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    expected_slots = pd.MultiIndex.from_product(
        [dates, sorted(daily["zone"].unique())], names=["date", "zone"]
    )
    filed_slots = pd.MultiIndex.from_frame(daily[["date", "zone"]])
    missing_slots = expected_slots.difference(filed_slots)
    missing_by_zone = (
        pd.Series(missing_slots.get_level_values("zone")).value_counts().sort_index().to_dict()
    )
    district_zones = set(districts["zone"])
    daily_zones = set(daily["zone"])
    zone_join_missing = sorted(daily_zones - district_zones)
    audit.extend(
        [
            f"Reporting span={dates.min().date()} to {dates.max().date()} ({len(dates)} dates × "
            f"{daily['zone'].nunique()} zones={len(expected_slots)} expected slots); "
            f"unreported slots={len(missing_slots)} by zone={missing_by_zone}. Missing slots remain absent, not zero.",
            f"Zone join to district register: matched={len(daily_zones & district_zones)}/{len(daily_zones)}; "
            f"unmatched daily zones={zone_join_missing}.",
            f"peak_load_mw=-1 sentinels set missing={peak_sentinel_count}; "
            f"cumulative meter declines={meter_drop_count}; invalid reading rows={bad_meter_rows.to_dict('records')}; "
            "unrecoverable counter value set missing.",
            f"Clean daily ranges: cumulative_mwh={_format_range(daily['cumulative_mwh'])}; "
            f"peak_load_mw={_format_range(daily['peak_load_mw'])}; "
            f"outage_minutes={_format_range(daily['outage_minutes'])}.",
        ]
    )

    audit.append("")
    audit.append("GENERATION MIX — FINDINGS AND REPAIRS")
    generation = generation_raw.copy()
    generation["month"] = pd.to_datetime(generation["month"], format="%Y-%m", errors="raise")
    totals = generation.loc[generation["source"].eq("All sources")].set_index("month")["mwh"]
    parts = generation.loc[
        ~generation["source"].eq("All sources") & ~generation["subsource"].eq("Total")
    ].copy()
    part_sums = parts.groupby("month")["mwh"].sum()
    differences = (part_sums - totals).abs()
    if differences.empty or differences.max() > 2:
        raise ValueError("Generation parts do not reconcile to the published totals within 2 MWh.")
    audit.append(
        f"Rows={len(generation)}; published parent/total rows={len(generation)-len(parts)}; "
        f"mutually exclusive leaf rows={len(parts)}; max parts-vs-published difference={differences.max():.0f} MWh; "
        f"summing all rows gives {generation['mwh'].sum()/parts['mwh'].sum():.1%} of the parts total; "
        f"month range={generation['month'].min():%Y-%m} to {generation['month'].max():%Y-%m}; "
        f"monthly row counts={generation.groupby('month').size().value_counts().sort_index().to_dict()}; "
        f"leaf MWh range={_format_range(parts['mwh'])}."
    )

    geo_codes = {feature["properties"]["code"] for feature in geojson["features"]}
    district_codes = set(districts["code"])
    audit.append(
        f"GeoJSON join: matched={len(geo_codes & district_codes)}/{len(geo_codes)}; "
        f"unmatched features={sorted(geo_codes-district_codes)}; unmatched districts={sorted(district_codes-geo_codes)}."
    )
    audit.extend(
        [
            "",
            "DENOMINATOR RANGES",
            f"Population: {_format_range(districts['population'])}; households: {_format_range(districts['households'])}.",
            f"Daily operated-zone slot denominator is not used; peak-load values are instantaneous maxima, not additive.",
            f"Valid district outage denominators: outages {_format_range(districts['outages'])}; "
            f"usable outage-minute rows={int(districts['outage_minutes'].notna().sum())}/24.",
            "",
            "PARAMETER AUDIT",
            "Meter-based monthly energy is the difference between readings on the first day of consecutive months; "
            "a counter is never summed.",
            "Partial September 2026 is excluded from complete-month comparisons; absent zone-days are unknown, not zero.",
            "Generation comparisons use the eight mutually exclusive leaf categories and exclude published parent/total rows.",
        ]
    )
    audit_text = "\n".join(audit) + "\n"
    (ROOT / "partA_audit.txt").write_text(audit_text, encoding="utf-8")
    print(audit_text, end="")

    decisions = [
        ("District register — duplicate D11 key with two names and slightly different payloads.", "Compare each name to the GeoJSON canonical name.", "Retain the exact match, Kotla, and remove the noncanonical duplicate.", 1),
        ("District register — D21 population / household ratio was 5,940, far outside every other district.", "Compare people-per-household across districts and check the raw household value's scale.", "Repair 182 households to 182,000, matching the implied thousand-unit scale and expected aggregate.", 1),
        ("District register — two electrification values included a percent sign and were parsed as text.", "Inspect raw field values and verify the resulting numeric range.", "Remove the literal % and parse as numeric percentage points; retain three truly absent values as missing.", pct_suffix_rows),
        ("District register — two outage-minute values were -1, impossible for a duration and identified as operator codes.", "Check the duration range and dictionary's operator-code convention.", "Set the code to missing; preserve district records and outage counts.", outage_sentinel_count),
        ("Daily returns — 174 dates used a slash format; interpreting all values in one format can swap or corrupt dates.", "Check raw date patterns and confirm the parsed reporting span.", "Parse ISO dates as %Y-%m-%d and alternate dates as %d/%m/%Y explicitly.", alternate_dates),
        ("Daily returns — exact duplicate date-zone resubmissions repeated the same payload.", "Normalize dates, compare duplicate keys and confirm all measurement columns match.", "Keep one copy of each identical row.", exact_duplicate_rows),
        ("Daily returns — three duplicate date-zone groups had conflicting peak/outage payloads.", "Compare all measurement columns for each repeated date-zone key.", "Keep the first source row as a deterministic tie-break; disclose that its values are not independently validated.", conflicting_duplicate_rows),
        ("Daily returns — peak_load_mw=-1 is an operator's unavailable code.", "Check the measurement range against the data dictionary.", "Set -1 to missing; retain the rest of each zone-day.", peak_sentinel_count),
        ("Daily returns — one sorted cumulative meter reading dropped from 21.4 million MWh to 1,180 MWh.", "Sort readings by zone and date, then inspect negative first differences.", "Set only the unrecoverable cumulative reading to missing; do not treat it as negative energy.", meter_drop_count),
        ("Daily returns — 128 expected zone-day slots were not filed over the full reporting span.", "Reindex the 529-day range for all six zones and compare with filed keys.", "Do not synthesize rows or zero values; leave gaps absent and state their count.", len(missing_slots)),
        ("Generation mix — each month includes nested published totals as well as eight reconciled leaf parts; summing all rows doubles the result.", "Compare month-level leaf sums with published totals and inspect hierarchy labels.", "Keep the eight mutually exclusive leaf rows per month; omit parent/total rows from additive analysis.", len(generation)-len(parts)),
    ]
    decision_lines = [
        "# Task A — Cleaning decisions",
        "",
        "| What | How detected | Rule applied | Rows affected |",
        "|---|---|---|---:|",
    ]
    decision_lines.extend(
        f"| {what} | {detected} | {rule} | {count} |"
        for what, detected, rule, count in decisions
    )
    decision_lines.extend(
        [
            "",
            "No raw source file is modified. Missing measurements remain missing, and calendar gaps are not filled with zero.",
            "For duplicate daily submissions, first-in-file is a reproducible tie-break rather than a claim that the earliest payload is more accurate; the three conflicts are disclosed in the audit.",
        ]
    )
    (ROOT / "partA_decisions.md").write_text("\n".join(decision_lines) + "\n", encoding="utf-8")

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    districts.to_csv(CLEAN_DIR / "district_grid.csv", index=False)
    daily.to_csv(CLEAN_DIR / "grid_daily.csv", index=False, date_format="%Y-%m-%d")
    parts["month"] = parts["month"].dt.strftime("%Y-%m")
    parts.to_csv(CLEAN_DIR / "generation_mix.csv", index=False)
    with (CLEAN_DIR / "regions.geojson").open("w", encoding="utf-8", newline="\n") as file:
        json.dump(geojson, file, ensure_ascii=False, separators=(",", ":"))

    expected = {
        "district_rows": 24,
        "population": 57_857_000,
        "households": 8_908_512,
        "daily_rows": 3_046,
        "missing_slots": 128,
        "parts_rows": 144,
    }
    observed = {
        "district_rows": len(districts),
        "population": int(districts["population"].sum()),
        "households": int(districts["households"].sum()),
        "daily_rows": len(daily),
        "missing_slots": len(missing_slots),
        "parts_rows": len(parts),
    }
    if observed != expected:
        raise AssertionError(f"Week 6 anchor check failed: expected {expected}; observed {observed}")
    return {"districts": districts, "daily": daily, "generation": parts, "geojson": geojson}


if __name__ == "__main__":
    process()
