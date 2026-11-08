# Week 4 Parts B–D — computed record

## Part D data audit

- Explicit parse: ISO rows `9,019` as `%Y-%m-%d %H:%M:%S`; slash rows `3,651` as **day/month/year** `%d/%m/%Y %H:%M`. Resulting range `2024-04-01 00:00:00`–`2025-09-11 23:00:00`; parsing with mixed inference would silently reverse ambiguous dates.

- Device tags canonicalized by strip + title case: `{"Desktop": 3452, "MOBILE ": 246, "Mobile": 6994, "Tablet": 777, "desktop": 318, "mobile": 883}`.

- Duplicate timestamps removed: `286` extra rows; conflicting duplicate groups: `0`; no conflicts remained after the rule.

- Invalid session sentinel `-1`: `287` observations set missing before daily aggregation; daily flow totals are expanded as observed hourly mean × 24. This assumes missing hours are not systematically different; it is stated, not hidden.

- Full expected hourly index contains `312` missing hours (13 empty calendar days). Daily audit before tail removal: `{'dtype_ok': True, 'monotonic': True, 'n_rows': 516, 'n_duplicated': 0, 'n_missing': 13, 'missing_dates': ['2024-05-18 00:00:00', '2024-07-02 00:00:00', '2024-07-03 00:00:00', '2024-09-27 00:00:00', '2024-11-11 00:00:00', '2024-12-25 00:00:00', '2025-01-01 00:00:00', '2025-02-14 00:00:00', '2025-03-30 00:00:00', '2025-03-31 00:00:00', '2025-06-07 00:00:00', '2025-07-19 00:00:00'], 'span': ('2024-04-01 00:00:00', '2025-09-11 00:00:00'), 'partial_tail': True, 'tail_period': '2025-09', 'tail_count': 11}`.

- The final September 2025 extract contains `11` days only, so it is excluded from all complete-month comparisons. The analysis period is `2024-04-01`–`2025-08-31`.

- The 2×2 dashboard shows a **7-day centred mean**, daily mean sessions by weekday/hour, a positive-only category→subcategory net-revenue treemap and sorted bars. Weekday × hour heatmap leaves missing observations masked, not interpolated.


## Part B numbers

### B1 · Window report (standard deviation reduction and edge periods)

```
 window    raw_sd  smoothed_sd  variation_removed_pct  periods_lost_each_end
      7 6779.7666    4653.6271                   31.4                      3
     28 6779.7666    4435.6225                   34.6                     14
     91 6779.7666    4158.9950                   38.7                     45
```


The window was fixed at **7 days before chart review** because it cancels the weekly cycle, not because it looks smooth. The raw series stays visible. Centred smoothing is retrospective; a morning-refresh dashboard must use a trailing window and caption its lag.


### B2 · Black Friday (2024-11-29)

- 14-day centred mean: `33,382.4` sessions/day.
- 14-day centred median: `24,780.5` sessions/day.
- EWMA with span 14, `adjust=False` (causal/trailing): `38,131.8` sessions/day.
The monitoring view should use the causal EWMA/trailing mean; a retrospective quarterly report can use the centred robust median and show the raw spike.


### B3 · Decomposition

- Additive `period=7`: weekly seasonal peak-to-trough `7,568.7` sessions/day; largest absolute residual on `2024-11-29`.
- Annual `period=365`: **NOT ESTIMABLE: 518 daily observations after the partial-month cutoff; statsmodels requires at least 2×365=730 for seasonal_decompose(period=365). x must have 2 complete cycles requires 730 observations. x only has 518 observation(s)**. No annual component is claimed from less than two annual cycles.


### B4 · Trailing versus centred

`tslib.lag_at_turn(window=31)` gives trailing `2024-05-23 00:00:00`, centred `2024-05-08 00:00:00`, lag `15` days versus half-window `15`. A live dashboard must show trailing (no future data) and caption that a turning point may appear about half a window late.


### B5 · Exhaustive start/window sensitivity

First occurrence of each calendar month as start; all 12 start months × 5 centred windows (7, 14, 28, 56, 91 days) scanned: **33 rising**, **27 falling**, 0 flat. Full-period line slope is `21.320` sessions/day per day-index. A Lie Factor cannot be computed for a cherry-picked time window: its numerator changes with the chosen frame, while there is no unique original effect in the data to use as denominator; report the exhaustive direction counts and the full-period estimate instead.


## Part C — legality and reader work

| Table | Exclusive parts? | Meaningful whole? | Is share the question? | Verdict |
|---|---|---|---|---|

| Touch flags | No (`1105 customers` overlap) | Customer set is meaningful, but channels overlap | Reach by channel, not composition | Sorted bars; no pie |

| Eight-category shares | Yes | Yes, the eight subcategories sum to 100% | Yes for one-period mix | Pie is legal; bars are better for ranking |

| Premium vs other, 2025Q4 | Yes | Yes, components sum to total `600.0` PKR m | Yes for Q4 composition | Pie is legal; use a line for change over time |


`tslib.exclusivity_check` touch result: `{'n': 4000, 'shares_pct': {'touch_search': 42.62, 'touch_social': 32.3, 'touch_email': 27.48, 'touch_direct': 28.58}, 'sum_pct': 130.98, 'exclusive': False, 'n_multi': 1105, 'pct_multi': 27.62, 'n_zero': 0}`. Palette audit: deuteranopia closest pair `(3, 4, '#009E73', '#CC79A7', 7.546637952916592)`; the fourth palette hue is accompanied by direct labels.

- Both ranking stimuli are saved. `pie_ranking_results.csv` has headers only. No reader was available in this non-interactive run, so no response, timing, rank error or experiment result is invented. Collect a real reader using `reader_protocol.md`.


## Part D hierarchy audit

- Duplicate SKU rows removed: `1` (retain first exact SKU record).

- Negative net-revenue rows excluded from treemap area: `7` rows, net total `-1.0693` PKR m, shown separately in the report rather than treated as area.

- Positive hierarchy total `1,712.4508` PKR m; cut at eight sub-categories (no category hidden in `Other`: 0 categories, PKR 0). 337 positive SKU rows roll into those eight named subcategories after deduplication and the negative-row exclusion. Maximum absolute difference from `shares_eight.csv`: 0.228 percentage points.

- The treemap answers where the revenue mass is; sorted bars answer how much each sub-category contributes. A single categorical hue is used per parent; negative values are never given area.
