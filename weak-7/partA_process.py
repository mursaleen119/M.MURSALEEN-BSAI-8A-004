"""Audit, clean, and document the instructor's four transit files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from week7_common import (
    CHART_DIR,
    CLEAN_DIR,
    MODE_COLORS,
    RAW_DIR,
    SOURCE_REVISION,
    channel_conflicts,
    cvd_report,
    ensure_source_files,
    project_laea,
)


WEEK_DIR = Path(__file__).resolve().parent
AUDIT_PATH = WEEK_DIR / "partA_audit.txt"
DECISIONS_PATH = WEEK_DIR / "partA_decisions.md"
DISTRICT_CODES = {f"D{number:02d}" for number in range(1, 25)}


def _read_sources() -> dict[str, pd.DataFrame]:
    ensure_source_files()
    return {
        "districts": pd.read_csv(RAW_DIR / "district_transit.csv", dtype={"code": str}),
        "routes": pd.read_csv(RAW_DIR / "routes.csv", dtype={"route_id": str}),
        "daily": pd.read_csv(RAW_DIR / "ridership_daily.csv", dtype={"date": str}),
        "fares": pd.read_csv(RAW_DIR / "fare_revenue.csv"),
    }


def _read_geojson() -> dict:
    with (RAW_DIR / "regions.geojson").open(encoding="utf-8") as file:
        geojson = json.load(file)
    if geojson.get("type") != "FeatureCollection":
        raise ValueError("regions.geojson must be a GeoJSON FeatureCollection.")
    return geojson


def _audit_frame(name: str, frame: pd.DataFrame, key: list[str]) -> list[str]:
    duplicates = int(frame.duplicated(key).sum())
    return [
        f"{name}: raw rows={len(frame):,}; dtypes="
        + ", ".join(f"{column}:{dtype}" for column, dtype in frame.dtypes.items()),
        f"  Key {key}: unique={int(frame[key].drop_duplicates().shape[0]):,}; duplicate rows={duplicates}",
        f"  Missing cells={int(frame.isna().sum().sum()):,}",
    ]


def process() -> dict[str, pd.DataFrame]:
    raw = _read_sources()
    geojson = _read_geojson()
    district_raw = raw["districts"].copy()
    routes_raw = raw["routes"].copy()
    daily_raw = raw["daily"].copy()
    fares_raw = raw["fares"].copy()

    feature_codes = {
        str(feature["properties"]["code"]).strip().upper()
        for feature in geojson.get("features", [])
    }
    if len(feature_codes) != 24 or feature_codes != DISTRICT_CODES:
        raise ValueError("Expected exactly the D01–D24 GeoJSON district features.")

    # District register: normalize join keys before comparing to GeoJSON.
    districts = district_raw.copy()
    districts["code"] = districts["code"].astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)
    raw_matches = int(district_raw["code"].isin(feature_codes).sum())
    repaired_matches = int(districts["code"].isin(feature_codes).sum())
    extra_mask = ~districts["code"].isin(feature_codes)
    if districts.loc[extra_mask, "code"].tolist() != ["D00"]:
        raise ValueError("Unexpected district rows outside the 24 GeoJSON features.")
    excluded_districts = int(extra_mask.sum())
    districts = districts.loc[~extra_mask].copy()
    if districts["code"].duplicated().any():
        raise ValueError("District key normalization produced duplicate codes.")

    low_boarding_mask = districts["boardings_annual"] / districts["population"] < 1
    repaired_boardings = int(low_boarding_mask.sum())
    districts.loc[low_boarding_mask, "boardings_annual"] *= 1000
    concession_mask = districts["fare_concession_pct"].between(0, 1, inclusive="neither")
    repaired_concession = int(concession_mask.sum())
    districts.loc[concession_mask, "fare_concession_pct"] *= 100
    invalid_road_mask = districts["road_km"] < 0
    invalid_roads = int(invalid_road_mask.sum())
    districts.loc[invalid_road_mask, "road_km"] = np.nan
    districts = districts.sort_values("code").reset_index(drop=True)

    # Routes: canonicalize aliases and treat impossible sentinels as missing.
    routes = routes_raw.copy()
    route_mode = routes["mode"].astype(str).str.strip()
    mode_map = {
        "metro": "Metro",
        "brt": "BRT",
        "bus rapid transit": "BRT",
        "bus": "Bus",
        "ferry": "Ferry",
    }
    canonical_modes = route_mode.str.casefold().map(mode_map)
    if canonical_modes.isna().any():
        raise ValueError(f"Unrecognized route modes: {sorted(route_mode[canonical_modes.isna()].unique())}")
    mode_repairs = int((route_mode != canonical_modes).sum())
    routes["mode"] = canonical_modes
    invalid_punctuality = routes["punctuality_pct"] > 100
    invalid_punctuality_rows = int(invalid_punctuality.sum())
    routes.loc[invalid_punctuality, "punctuality_pct"] = np.nan
    zero_cost_recovery = routes["cost_recovery_pct"] == 0
    invalid_cost_rows = int(zero_cost_recovery.sum())
    routes.loc[zero_cost_recovery, "cost_recovery_pct"] = np.nan

    # Daily returns: parse only the two observed, explicit formats.
    daily = daily_raw.copy()
    iso_mask = daily["date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
    alternate_mask = ~iso_mask
    parsed_dates = pd.Series(pd.NaT, index=daily.index, dtype="datetime64[ns]")
    parsed_dates.loc[iso_mask] = pd.to_datetime(
        daily.loc[iso_mask, "date"], format="%Y-%m-%d", errors="coerce"
    )
    parsed_dates.loc[alternate_mask] = pd.to_datetime(
        daily.loc[alternate_mask, "date"], format="%d/%m/%Y", errors="coerce"
    )
    if parsed_dates.isna().any():
        bad = daily.loc[parsed_dates.isna(), "date"].head(10).tolist()
        raise ValueError(f"Unparseable daily dates: {bad}")
    month_first_accepted = int(
        pd.to_datetime(
            daily.loc[alternate_mask, "date"], format="%m/%d/%Y", errors="coerce"
        ).notna().sum()
    )
    daily["date"] = parsed_dates

    daily_key = ["date", "mode"]
    duplicate_keys = daily.duplicated(daily_key, keep=False)
    duplicate_rows = int(daily.duplicated(daily_key).sum())
    payload_columns = [
        "trips_scheduled",
        "trips_operated",
        "trips_on_time",
        "boardings",
        "delay_minutes",
    ]
    conflicts = (
        daily.loc[duplicate_keys]
        .groupby(daily_key, dropna=False)[payload_columns]
        .nunique()
        .gt(1)
        .any(axis=1)
    )
    if conflicts.any():
        raise ValueError(f"Conflicting same-day, same-mode submissions: {conflicts[conflicts].index.tolist()[:5]}")
    daily = daily.drop_duplicates(daily_key, keep="first").copy()
    impossible_on_time = daily["trips_on_time"] > daily["trips_operated"]
    impossible_rows = int(impossible_on_time.sum())
    # Keep valid boardings from these filed days, but exclude the unknowable rate.
    daily.loc[impossible_on_time, "trips_on_time"] = np.nan

    start, end = daily["date"].min(), daily["date"].max()
    expected_slots = pd.MultiIndex.from_product(
        [pd.date_range(start, end, freq="D"), sorted(daily["mode"].unique())],
        names=daily_key,
    )
    filed_slots = pd.MultiIndex.from_frame(daily[daily_key].drop_duplicates())
    missing_slots = expected_slots.difference(filed_slots)
    missing_by_mode = pd.Series(missing_slots.get_level_values("mode")).value_counts().to_dict()
    longest_gap: tuple[int, str, str, str] | None = None
    for mode in sorted(daily["mode"].unique()):
        filed_dates = pd.DatetimeIndex(daily.loc[daily["mode"].eq(mode), "date"].unique()).sort_values()
        absent = pd.date_range(start, end, freq="D").difference(filed_dates)
        if len(absent):
            groups = (absent.to_series().diff().dt.days.ne(1)).cumsum()
            for _, block in absent.to_series().groupby(groups):
                length = len(block)
                candidate = (length, mode, block.iloc[0].strftime("%Y-%m-%d"), block.iloc[-1].strftime("%Y-%m-%d"))
                if longest_gap is None or candidate[0] > longest_gap[0]:
                    longest_gap = candidate
    late_filed_rows = int(daily["date"].ge(pd.Timestamp("2026-09-22")).sum())

    # Fare table: keep only mutually exclusive ticket products, reconcile totals first.
    fares = fares_raw.copy()
    all_ticket_rows = fares["ticket_type"].eq("All tickets")
    summary = fares.loc[all_ticket_rows].set_index(["month", "mode"]).sort_index()
    fare_parts = fares.loc[~all_ticket_rows].copy()
    parts_sums = fare_parts.groupby(["month", "mode"])[["trips", "revenue_pkr"]].sum().sort_index()
    if not parts_sums.equals(summary[["trips", "revenue_pkr"]]):
        difference = parts_sums.subtract(summary[["trips", "revenue_pkr"]])
        raise ValueError(f"Published fare totals do not reconcile with products:\n{difference[difference.ne(0).any(axis=1)]}")

    # All output is generated from the raw source files; nothing is hand-edited.
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    districts.to_csv(CLEAN_DIR / "district_transit.csv", index=False)
    routes.to_csv(CLEAN_DIR / "routes.csv", index=False)
    daily.to_csv(CLEAN_DIR / "ridership_daily.csv", index=False, date_format="%Y-%m-%d")
    fare_parts.to_csv(CLEAN_DIR / "fare_revenue.csv", index=False)
    shutil.copyfile(RAW_DIR / "regions.geojson", CLEAN_DIR / "regions.geojson")

    # Cross-file reconciliation and audit facts.
    district_boardings = int(districts["boardings_annual"].sum())
    route_boardings = int(routes["boardings_annual"].sum())
    attributed_route_boardings = 0
    route_parts = routes["districts_served"].str.split(";")
    for values, parts in zip(routes["boardings_annual"], route_parts):
        attributed_route_boardings += int(values) * len(parts)
    join_misses = sorted(set(routes["districts_served"].str.split(";").explode()) - feature_codes)
    geo_features = len(feature_codes)
    road_valid = int(districts["road_km"].notna().sum())
    pooled_rate = district_boardings / int(districts["population"].sum()) * 1000
    boardings_per_1000 = districts.assign(
        boardings_per_1000=districts["boardings_annual"] / districts["population"] * 1000
    )
    map_breaks = np.unique(
        np.quantile(boardings_per_1000["boardings_per_1000"], np.linspace(0, 1, 6))
    )
    daily_annual = daily.loc[
        daily["date"].between("2025-09-01", "2026-08-31"), "boardings"
    ].sum()
    daily_before_dedup = daily_raw.copy()
    raw_dates = pd.Series(pd.NaT, index=daily_before_dedup.index, dtype="datetime64[ns]")
    daily_iso_mask = daily_before_dedup["date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
    raw_dates.loc[daily_iso_mask] = pd.to_datetime(daily_before_dedup.loc[daily_iso_mask, "date"], format="%Y-%m-%d", errors="coerce")
    raw_dates.loc[~daily_iso_mask] = pd.to_datetime(daily_before_dedup.loc[~daily_iso_mask, "date"], format="%d/%m/%Y", errors="coerce")
    daily_before_dedup["parsed_date"] = raw_dates
    pre_dedup_window = daily_before_dedup.loc[
        daily_before_dedup["parsed_date"].between("2025-09-01", "2026-08-31"), "boardings"
    ].sum()
    return_pct = daily_annual / district_boardings * 100
    daily_slots = len(expected_slots)
    late_expected = 9 * 4
    boarding_journeys_ratio = daily["boardings"].sum() / fare_parts["trips"].sum()
    raw_join_count = int(district_raw["code"].isin(feature_codes).sum())

    audit_lines = [
        "Week 7 Task A — reproducible raw-data audit and cleaning",
        f"Source: UsmarHaider/data-visualization, week7/assignments/data, revision {SOURCE_REVISION}",
        "Raw source inputs are fetched into ignored weak-7/data/ when absent; raw inputs are never modified or committed.",
        "",
        "RAW FILE AUDITS",
    ]
    audit_lines += _audit_frame("district_transit.csv", district_raw, ["code"])
    audit_lines += _audit_frame("routes.csv", routes_raw, ["route_id"])
    audit_lines += _audit_frame("ridership_daily.csv", daily_raw, ["date", "mode"])
    audit_lines += _audit_frame("fare_revenue.csv", fares_raw, ["month", "mode", "ticket_type"])
    audit_lines += [
        f"regions.geojson: {geo_features} Polygon features; unique code keys={len(feature_codes)}.",
        "",
        "FINDINGS, REPAIRS, AND RECONCILIATION",
        f"District GeoJSON join matches as filed: {raw_join_count}/24; after key repair: {repaired_matches}/24.",
        f"Districts retained={len(districts)}; out-of-scope D00 removed={excluded_districts}. "
        f"Residents={int(districts.population.sum()):,}; households={int(districts.households.sum()):,}; "
        f"population including D00 would be {int(district_raw.population.sum()):,}.",
        f"District boardings before repair: {int(district_raw.boardings_annual.sum()):,}; after repair: {district_boardings:,}.",
        f"Boardings per 1,000 residents: {boardings_per_1000.boardings_per_1000.min():,.0f}–"
        f"{boardings_per_1000.boardings_per_1000.max():,.0f}; pooled denominator rate={pooled_rate:,.0f}.",
        f"Concession share repairs={repaired_concession}; valid range after repair="
        f"{districts.fare_concession_pct.min():.1f}–{districts.fare_concession_pct.max():.1f}%.",
        f"Usable road_km values={road_valid}/24; -1 codes are missing, not negative road length.",
        "District non-positive population, households, area, stops, annual boardings, or registered-vehicle counts: "
        + str(
            int(
                (
                    districts[
                        ["population", "households", "area_km2", "stops", "boardings_annual", "vehicles_registered"]
                    ]
                    <= 0
                )
                .any(axis=1)
                .sum()
            )
        ),
        f"Routes: modes as filed={routes_raw['mode'].nunique()}, after normalization={routes['mode'].nunique()}; "
        f"counts={routes['mode'].value_counts().sort_index().to_dict()}.",
        f"Route punctuality usable={int(routes.punctuality_pct.notna().sum())}/36; "
        f"valid range={routes.punctuality_pct.min():.1f}–{routes.punctuality_pct.max():.1f}%.",
        f"Cost recovery zero codes set missing={invalid_cost_rows}; routes with a valid rate="
        f"{int(routes.cost_recovery_pct.notna().sum())}/36.",
        "Route invalid ranges: non-positive length/stops/fleet="
        + str(
            int(
                (
                    (routes["length_km"] <= 0)
                    | (routes["stops"] <= 0)
                    | (routes["fleet"] <= 0)
                ).sum()
            )
        )
        + f"; crowding index range={routes['crowding_index'].min():.2f}–{routes['crowding_index'].max():.2f}.",
        f"Route boardings={route_boardings:,}; district register={district_boardings:,}; "
        f"difference={route_boardings - district_boardings:+,}.",
        f"Crediting route boardings to every served district gives {attributed_route_boardings:,} "
        f"({attributed_route_boardings / route_boardings:.3f}x); routes with >1 district="
        f"{int(route_parts.map(len).gt(1).sum())}/36; mean districts/route={route_parts.map(len).mean():.2f}; "
        f"max={route_parts.map(len).max()}.",
        f"Route district codes with no GeoJSON feature: {join_misses or 'none'}.",
        f"Daily date format: alternate-format rows={int(alternate_mask.sum())}; "
        f"month-first parser accepts {month_first_accepted} and fails {int(alternate_mask.sum()) - month_first_accepted}; "
        "dates are parsed using explicit ISO or day-first formats.",
        f"Exact resubmissions after date normalization={duplicate_rows}; rows retained after deduplication={len(daily)}.",
        f"Impossible on-time counts (trips_on_time > trips_operated)={impossible_rows}; "
        "these rows remain for valid boardings but are excluded from punctuality numerator and denominator.",
        "Other daily impossibilities: negative counts="
        + str(
            int(
                daily[
                    ["trips_scheduled", "trips_operated", "trips_on_time", "boardings", "delay_minutes"]
                ]
                .lt(0)
                .any(axis=1)
                .sum()
            )
        )
        + f"; operated > scheduled={int((daily['trips_operated'] > daily['trips_scheduled']).sum())}.",
        f"Filed daily span={start:%Y-%m-%d} to {end:%Y-%m-%d}; expected date×mode slots={daily_slots}; "
        f"unfiled slots={len(missing_slots)}; by mode={dict(sorted(missing_by_mode.items()))}.",
        f"Longest single-mode no-return streak={longest_gap[0]} days, {longest_gap[1]} "
        f"{longest_gap[2]} to {longest_gap[3]}.",
        f"Slots from 2026-09-22 to 2026-09-30: {late_filed_rows}/{late_expected}; "
        "two modes stop filing in the partial final period.",
        f"12-month boardings (2025-09-01–2026-08-31), deduplicated={int(daily_annual):,}; "
        f"with resubmissions={int(pre_dedup_window):,}; inflation={(pre_dedup_window / daily_annual - 1) * 100:.2f}%.",
        f"District annual boardings vs daily-return boardings: {district_boardings:,} vs {int(daily_annual):,}; "
        f"returns account for {return_pct:.1f}%; gaps are unknown, not zero.",
        f"Fare table rows={len(fares)}: parts={len(fare_parts)}, published totals={int(all_ticket_rows.sum())}. "
        f"Parts reconcile exactly with all {len(summary)} published month×mode totals.",
        f"Summing every fare row would equal {fares.trips.sum() / fare_parts.trips.sum() * 100:.1f}% "
        "of part journeys and "
        f"{fares.revenue_pkr.sum() / fare_parts.revenue_pkr.sum() * 100:.1f}% of part revenue.",
        f"Fare parts total={int(fare_parts.trips.sum()):,} journeys and "
        f"{int(fare_parts.revenue_pkr.sum()):,} PKR; mean fare={fare_parts.revenue_pkr.sum() / fare_parts.trips.sum():.1f} PKR/journey.",
        f"Boardings ÷ journeys={boarding_journeys_ratio:.3f}; these are different units and are never combined on one axis.",
        "",
        "DIVISION DENOMINATORS",
        f"District population: min={districts.population.min():,}, max={districts.population.max():,}; "
        "all positive before boardings-per-resident calculations.",
        f"Daily operated departures: min={daily.trips_operated.min():,}, "
        f"max={daily.trips_operated.max():,}; rate calculations use rows with valid on-time counts.",
        f"Fare journeys: min={fare_parts.trips.min():,}, max={fare_parts.trips.max():,}; all positive.",
        "",
        "DASHBOARD CHANNEL PLAN",
    ]
    panel_channels = [
        {"panel": "punctuality", "x": "quarter", "y": "network_on_time_pct"},
        {"panel": "mode_reversal", "x": "mode", "y": "punctuality_change_pp", "hue": "mode"},
        {"panel": "district_map", "lightness": "boardings_per_1000_residents"},
        {"panel": "fare_trend", "x": "month", "y": "indexed_financial_measure"},
    ]
    channel_report = channel_conflicts(panel_channels)
    audit_lines += [
        f"channel_conflicts output: {json.dumps(channel_report, sort_keys=True)}",
        f"cvd_report palette: {json.dumps(MODE_COLORS, sort_keys=True)}",
    ]
    cvd = cvd_report(MODE_COLORS)
    audit_lines += [
        f"cvd_report output: method={cvd['method']}; minimum simulated RGB distance="
        f"{cvd['minimum_rgb_distance']:.3f}; pairs below 0.12={cvd['pairs_below_0_12']}.",
        "",
        "PARAMETER AUDIT",
        "Punctuality is sum(trips_on_time)/sum(trips_operated), not an average of daily percentages.",
        "Fare endpoint comparison uses complete months 2025-04 through 2026-08; partial 2026-09 is excluded.",
        "District choropleth uses equal-area Lambert azimuthal projection centered at 70°E, 30°N; "
        "five quantile class breaks: " + ", ".join(f"{value:,.0f}" for value in map_breaks) + ".",
    ]
    AUDIT_PATH.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")
    print(AUDIT_PATH.read_text(encoding="utf-8"), end="")

    decisions = [
        ("District register", "D00 extra territory row", "Join against the 24 GeoJSON features and scope codes D01–D24.", "Exclude the non-feature D00 territory from district totals; do not infer geography.", excluded_districts),
        ("District register", "Two malformed join keys", "Compare raw keys with GeoJSON codes; `d13` and `D 20` fail exact joins.", "Trim spaces and uppercase before joining, yielding D13 and D20.", 2),
        ("District register", "Three boardings values under one per resident", "Annual boardings divided by population is <1 for D05, D15, and D23, unlike every other district.", "Multiply these values by 1,000; this produces plausible per-capita rates and the published network reconciliation.", repaired_boardings),
        ("District register", "Four concession proportions filed as fractions", "Values 0.326–0.426 conflict with other percentage values and the 0–100 percent unit.", "Multiply only values strictly between 0 and 1 by 100.", repaired_concession),
        ("District register", "Two negative road lengths are operator codes", "D06 and D16 have road_km=-1 although lengths cannot be negative.", "Convert -1 to missing; do not treat it as distance.", invalid_roads),
        ("Route table", "Three noncanonical BRT mode labels", "Mode value counts show `brt` and `Bus Rapid Transit` alongside BRT.", "Map case-insensitive BRT aliases to canonical BRT.", mode_repairs),
        ("Route table", "Three punctuality sentinels", "punctuality_pct=999 exceeds the valid percentage range.", "Set the code to missing; retain route rows and do not compute with it.", invalid_punctuality_rows),
        ("Route table", "Two zero cost-recovery codes", "Dictionary and route context identify the two zero entries as operator codes, not measured 0% recovery.", "Set those entries to missing; preserve the route records.", invalid_cost_rows),
        ("Daily returns", "385 dates in an alternate format", "Strict ISO parsing fails on 385 rows; explicit day-first parsing succeeds. A month-first parser accepts 155 rows ambiguously.", "Parse ISO `%Y-%m-%d` and alternate `%d/%m/%Y` explicitly; never infer month-first.", int(alternate_mask.sum())),
        ("Daily returns", "30 same-day/mode resubmissions", "After parsing, 30 rows duplicate a date×mode key; all numeric payloads agree.", "Retain the first identical payload per date and mode; preserve one return per slot.", duplicate_rows),
        ("Daily returns", "Seven impossible on-time counts", "trips_on_time exceeds trips_operated on seven filed returns.", "Keep their valid boardings, blank the invalid on-time numerator, and exclude those rows from both sides of punctuality rates.", impossible_rows),
        ("Daily returns", "63 unfiled date×mode slots", "Reindex each mode over the full 2025-04-01–2026-09-30 reporting span.", "Leave absent slots absent; do not manufacture zero service or zero boardings.", len(missing_slots)),
        ("Daily returns", "Incomplete reporting at the file end", "Only 18 of 36 expected mode-days were filed from 2026-09-22 through 2026-09-30.", "Do not extrapolate or treat the partial final period as complete; exclude 2026-09 from full-month comparisons.", late_expected - late_filed_rows),
        ("Fare table", "72 published totals repeat the product parts", "For all 72 month×mode keys, Daily+Monthly+Single equals the `All tickets` row exactly.", "Keep the reconciled product rows for analysis; exclude summary rows to avoid double counting.", int(all_ticket_rows.sum())),
    ]
    lines = [
        "# Task A — Cleaning decisions",
        "",
        "| File | What | How detected | Rule applied | Rows affected |",
        "|---|---|---|---|---:|",
    ]
    for file_name, what, detection, rule, count in decisions:
        lines.append(f"| {file_name} | {what} | {detection} | {rule} | {count} |")
    lines += [
        "",
        "The cleaned daily file retains filed boardings even where the punctuality numerator is invalid. The fare summary rows are accurate published totals, but are not additive parts. Cross-file differences are reported in the audit rather than reconciled away.",
    ]
    DECISIONS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"districts": districts, "routes": routes, "daily": daily, "fares": fare_parts}


def main() -> None:
    process()
    print(f"Cleaned tables written under {CLEAN_DIR}")
    print(f"Decisions written to {DECISIONS_PATH}")


if __name__ == "__main__":
    main()
