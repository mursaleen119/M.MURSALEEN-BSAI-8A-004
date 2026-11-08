# Week 4 Part A — diagnoses and redesigns

All nine synthetic course-data cases are rebuilt in `week4_case*.png` with the published recipe beside an honest redesign. The chart titles and this report separate the invited conclusion, rejected decoy, mechanism, numeric evidence and fix.

### Case 1 — string-sorted months

- **Invited conclusion:** Orders seem to rise and collapse in a repeating annual sequence.
- **Decoy ruled out:** The series is not too short: all 24 monthly observations are present.
- **Mechanism:** The YYYY-M strings sort lexicographically, so month 10 and 11 are placed before month 2; equal x spacing then assigns false time order.
- **Evidence:** 24 points reproduce the recipe's 958 and 978 drops; parsing YYYY-M chronologically changes their positions and removes the claimed repeated Q1 collapse.
- **Redesign:** Parse to a monthly DatetimeIndex, sort it, and draw the original values against calendar time.

### Case 2 — row number hides closures

- **Invited conclusion:** Sales appear to rise steadily by about 22% across the quarter.
- **Decoy ruled out:** The endpoint arithmetic and 69 observations are correct; sample size is not the defect.
- **Mechanism:** Plotting row number compresses elapsed time by deleting non-trading calendar days from the x scale; it cannot distinguish a one-day step from a multi-day closure.
- **Evidence:** The 69 records span 90 calendar days with 21 unrecorded dates; the first-to-last change is +22.2%.
- **Redesign:** Plot the actual dates and reindex to daily frequency so closures create visible gaps.

### Case 3 — summing a level

- **Invited conclusion:** Peak concurrent load appears to jump 43% overnight on 1 July.
- **Decoy ruled out:** The y-axis starts at zero and the June/July sums reproduce the recipe.
- **Mechanism:** Concurrent users is a level measured at an instant, not an additive flow; summing 24 snapshots gives a user-hours measure and compounds any change in sampling coverage.
- **Evidence:** The incorrect daily sums average 8,782 in June and 12,543 in July (+42.8%); daily means of the same level remove the multiplicative 24-hour sum, while bytes served remains a sum because it is a flow.
- **Redesign:** Aggregate concurrent users with a daily mean; aggregate bytes served with a daily sum, in separate labelled panels.

### Case 4 — trailing-window lag

- **Invited conclusion:** The new checkout flow started working on 7 September.
- **Decoy ruled out:** The 31-day rolling mean is calculated on a sorted daily index, and its minimum is correctly 7 September.
- **Mechanism:** A trailing mean contains only current and earlier observations; at a 31-day window its minimum arrives roughly half a window after the centered estimate of the turn.
- **Evidence:** tslib.lag_at_turn reports trailing minimum 2025-09-07, centred minimum 2025-08-23, a lag of 15 days (half-window 15); the observational line alone does not establish that the checkout change caused a turn.
- **Redesign:** Keep the faint raw series, name the 31-day window, show the centred estimate for retrospective analysis, and label a trailing estimate as delayed on any live dashboard.

### Case 5 — seasonally selected window

- **Invited conclusion:** Revenue has fallen 41.9% in six straight months.
- **Decoy ruled out:** The recipe uses seven points and an honest zero baseline; neither truncation nor n=7 explains it.
- **Mechanism:** The chosen window begins at a seasonal peak and ends near a trough; the crop selects phase of the annual cycle rather than estimating a sustained trend.
- **Evidence:** The chosen interval reproduces 158.8 to 92.2 PKR m (-41.9%), but the source has 36 complete months; the fall must be compared with the same months in other years.
- **Redesign:** Show all 36 months, identify the selected interval, and compare seasonal position across years instead of presenting the crop as a trend.

### Case 6 — partial final month

- **Invited conclusion:** Orders collapsed in October: 4,041 versus September's 10,805.
- **Decoy ruled out:** Both bars start at zero and the monthly sum is arithmetically correct.
- **Mechanism:** October is only partially observed; comparing its subtotal with a complete September total confounds period coverage with the daily order rate.
- **Evidence:** October has 11 recorded days out of 31; its 4,041 orders are not a full-month total. The per-recorded-day mean is 367.4 versus 360.2 in September.
- **Redesign:** Hatch and label the partial month, and show daily average alongside full-period totals rather than treating an incomplete period as complete.

### Case 7 — moving baseline in a stacked area

- **Invited conclusion:** Product D has been erratic since mid-2024.
- **Decoy ruled out:** The stack is legal: the four product values are exclusive and exhaustive, and the total envelope is not fabricated.
- **Mechanism:** The top layer's upper boundary is the cumulative sum of A+B+C+D; movement in the three lower layers shifts D's baseline, so its thickness—not its top edge—is its value.
- **Evidence:** The full stack ranges from 548.3 to 708.7 PKR m/month; in the original, D is read against a moving cumulative baseline.
- **Redesign:** Unstack the products into common-baseline lines (or small multiples) so D's own changes can be compared.

### Case 8 — non-exclusive channel touches

- **Invited conclusion:** Paid search drives 42.6% of customers, apparently the largest share.
- **Decoy ruled out:** The row is one customer and each percentage correctly divides a touch count by 4,000.
- **Mechanism:** Attribution flags are not mutually exclusive: a customer may be touched by several channels, so the four marginal percentages do not partition a meaningful whole and a pie renormalizes them deceptively.
- **Evidence:** The channel rates are search 42.6%, social 32.3%, email 27.5%, direct 28.6%; they sum to 131.0%, and 1,105 customers have multiple true flags.
- **Redesign:** Use sorted bars labelled as percent of customers touched; explicitly state that overlaps mean bars need not sum to 100%.

### Case 9 — a rising share of a changing total

- **Invited conclusion:** Premium is now 38% of revenue, a record share.
- **Decoy ruled out:** The share calculation and zero baseline are correct; the issue is not a percentage arithmetic error.
- **Mechanism:** The denominator (total revenue) is moving: a larger premium fraction does not establish that premium revenue itself grew or that overall revenue improved.
- **Evidence:** Premium share changes 24.0%→38.0%; total revenue changes 1,000.0→600.0 PKR m, and premium revenue changes 240.0→228.0 PKR m.
- **Redesign:** Keep the share, but place the exclusive premium/other revenue amounts beside it so the changing denominator is visible.
