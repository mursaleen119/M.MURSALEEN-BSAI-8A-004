# Task A — Cleaning decisions

| File | What | How detected | Rule applied | Rows affected |
|---|---|---|---|---:|
| District register | D00 extra territory row | Join against the 24 GeoJSON features and scope codes D01–D24. | Exclude the non-feature D00 territory from district totals; do not infer geography. | 1 |
| District register | Two malformed join keys | Compare raw keys with GeoJSON codes; `d13` and `D 20` fail exact joins. | Trim spaces and uppercase before joining, yielding D13 and D20. | 2 |
| District register | Three boardings values under one per resident | Annual boardings divided by population is <1 for D05, D15, and D23, unlike every other district. | Multiply these values by 1,000; this produces plausible per-capita rates and the published network reconciliation. | 3 |
| District register | Four concession proportions filed as fractions | Values 0.326–0.426 conflict with other percentage values and the 0–100 percent unit. | Multiply only values strictly between 0 and 1 by 100. | 4 |
| District register | Two negative road lengths are operator codes | D06 and D16 have road_km=-1 although lengths cannot be negative. | Convert -1 to missing; do not treat it as distance. | 2 |
| Route table | Three noncanonical BRT mode labels | Mode value counts show `brt` and `Bus Rapid Transit` alongside BRT. | Map case-insensitive BRT aliases to canonical BRT. | 3 |
| Route table | Three punctuality sentinels | punctuality_pct=999 exceeds the valid percentage range. | Set the code to missing; retain route rows and do not compute with it. | 3 |
| Route table | Two zero cost-recovery codes | Dictionary and route context identify the two zero entries as operator codes, not measured 0% recovery. | Set those entries to missing; preserve the route records. | 2 |
| Daily returns | 385 dates in an alternate format | Strict ISO parsing fails on 385 rows; explicit day-first parsing succeeds. A month-first parser accepts 155 rows ambiguously. | Parse ISO `%Y-%m-%d` and alternate `%d/%m/%Y` explicitly; never infer month-first. | 385 |
| Daily returns | 30 same-day/mode resubmissions | After parsing, 30 rows duplicate a date×mode key; all numeric payloads agree. | Retain the first identical payload per date and mode; preserve one return per slot. | 30 |
| Daily returns | Seven impossible on-time counts | trips_on_time exceeds trips_operated on seven filed returns. | Keep their valid boardings, blank the invalid on-time numerator, and exclude those rows from both sides of punctuality rates. | 7 |
| Daily returns | 63 unfiled date×mode slots | Reindex each mode over the full 2025-04-01–2026-09-30 reporting span. | Leave absent slots absent; do not manufacture zero service or zero boardings. | 63 |
| Daily returns | Incomplete reporting at the file end | Only 18 of 36 expected mode-days were filed from 2026-09-22 through 2026-09-30. | Do not extrapolate or treat the partial final period as complete; exclude 2026-09 from full-month comparisons. | 18 |
| Fare table | 72 published totals repeat the product parts | For all 72 month×mode keys, Daily+Monthly+Single equals the `All tickets` row exactly. | Keep the reconciled product rows for analysis; exclude summary rows to avoid double counting. | 72 |

The cleaned daily file retains filed boardings even where the punctuality numerator is invalid. The fare summary rows are accurate published totals, but are not additive parts. Cross-file differences are reported in the audit rather than reconciled away.
