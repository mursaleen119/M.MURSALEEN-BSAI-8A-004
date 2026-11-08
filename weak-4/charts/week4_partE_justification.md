# Week 4 Part E — written justification

## The four panels and their questions

1. **Daily sessions:** how is traffic moving once the weekday cycle is separated? A time-series line uses position for sequence; the faint raw daily series remains under a named 7-day centred mean. The mean is retrospective; the live counterpart must be trailing and disclose its lag.
2. **Weekday × hour heatmap:** when is traffic typically concentrated? A sequential blue scale encodes an ordered mean; masked missing cells are not filled with zero.
3. **Treemap:** where is the net-revenue mass across category → sub-category? Area is appropriate for hierarchy overview, each parent category has a consistent identity hue, and values are printed because area ranks below position. Negative rows are shown as a separate return-credit issue, never as area.
4. **Sorted bars:** how much net revenue does each sub-category contribute? Common-baseline length gives more precise comparison than area or angle. No `Other` bucket was used: 0 sub-categories / PKR 0 are hidden; the cut is at the eight sub-category level.

## Time, parse and aggregation

The timestamp format is explicit by logger: `9,019` ISO strings use `%Y-%m-%d %H:%M:%S`; `3,651` slash strings use day-first `%d/%m/%Y %H:%M`. I checked the parsed min/max rather than trusting mixed-format success. The sorted, de-duplicated hourly index has `312` missing hours; `-1` is an invalid sessions sentinel. For daily flows, valid hourly session totals are divided by observed hours and multiplied by 24; this estimates a full-day total and assumes missing hours are not systematically different. Missing whole days remain NaN and form line breaks; the final 11-day September 2025 tail is omitted as incomplete. The heatmap uses mean observed sessions per hour. Daily totals use sum semantics (with transparent coverage correction), never a sum of an instantaneous level.

The 7-day window was fixed before inspection because the cycle it removes is weekly. The chart keeps raw values and names the window. A 28-day version and an exhaustive 12-start × 5-window slope scan are in the appendix. The annual decomposition is not identifiable from 518 days under `seasonal_decompose`'s two-cycle requirement; it is reported as unavailable instead of extrapolated.

## Row and hierarchy accounting

- Duplicate timestamp rows removed: **286**; all duplicate groups agree exactly on measures and normalized device.
- Invalid `sessions=-1` observations: **287** values excluded as missing.
- Missing hourly periods from the complete expected index: **312**; this includes **13** dates with no hourly data.
- Incomplete final month: **11** recorded September days removed from the complete-month analysis.
- Duplicate SKU rows removed: **1**. Negative net-revenue SKU rows excluded from area: **7**, net **-1.0693 PKR m**, retained as an explicit negative audit. Positive subcategory hierarchy total: **1,712.4508 PKR m**. The cut is category → sub-category; all eight sub-categories remain visible, so `Other` is empty.

The same fixed window and start date would be used if the result weakened the story. `partB` reports both rising and falling combinations, making the selection sensitivity visible rather than hiding rejected views.
