# Week 4 Part F — bonus cycle analysis

**Source.** Seaborn data repository, [`flights.csv`](https://raw.githubusercontent.com/mwaskom/seaborn-data/master/flights.csv), downloaded 2026-11-09. It is the classic real monthly U.S. airline passenger series `AirPassengers` (1949–1960), with `month` as the within-year category. The raw source is saved as `data/partF_airpassengers_source.csv`; it has 144 observations.

**Index audit (`tslib.audit_index`, MS):** `{"dtype_ok": true, "monotonic": true, "n_rows": 144, "n_duplicated": 0, "n_missing": 0, "missing_dates": [], "span": ["1949-01-01 00:00:00", "1960-12-01 00:00:00"], "partial_tail": false, "tail_period": "1960", "tail_count": 12}`.

**Figure parameters.** Additive and multiplicative seasonal decompositions use period 12; cycle plot groups by calendar month. The banked-to-45° figure size is `10.00 × 1.91` inches. Figures are 300 dpi.

**Answer (two sentences).** The annual absolute swing grows as passenger volume grows, but its relative swing is 0.355 on average in 1949–1951 versus 0.502 in 1958–1960, so most of the widening is explained by scale rather than a steadily increasing seasonal fraction. The multiplicative residual standard deviation is 0.033 versus 19.3 passengers for the additive residual; the ratio-scale residual is the appropriate diagnostic for seasonality proportional to the rising trend, not proof that every year has identical seasonal shape.
