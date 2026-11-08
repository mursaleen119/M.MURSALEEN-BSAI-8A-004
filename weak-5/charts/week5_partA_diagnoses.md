# Week 5 Part A — diagnoses and redesigns

All nine synthetic cases are rebuilt in `week5_case*.png`. Each image puts the published recipe beside an honest alternative. The report names the claim, rules out the decoy, identifies the channel/boundary mechanism, and gives data evidence.

### Case 1 — population squared into scatter area

- **Invited conclusion:** Population and healthcare access appear unrelated across the GDP range.
- **Decoy ruled out:** There are 60 marks, and GDP's log scale is correct; the issue is not missing countries or the x transform.
- **Mechanism:** Matplotlib's `s` already means area. Setting `s=pop_m**2` makes area quadratic in population and reduces small-country marks to near invisibility.
- **Evidence:** Population spans 0.6–353.4 M (589×); the supplied recipe implies an area ratio of 346,921× (589²), and 9 countries are below 2.0 M. The brief's stated 589× area check conflicts with its own `s=pop_m**2` recipe; the code/data imply 589², so this report preserves the mathematical result.
- **Redesign:** Use a bounded, declared linear mapping from population to marker area; keep log GDP, retain and label the outlier, and include a size legend with real population values.

### Case 2 — raw-count choropleth

- **Invited conclusion:** The three darkest/highest-count districts are the outbreak hotspots.
- **Decoy ruled out:** All 24 districts join and the count data are arithmetically correct.
- **Mechanism:** A choropleth's polygon area is part of the visual encoding, but the count is unnormalized; districts with more residents tend to have more cases even at equal incidence.
- **Evidence:** Count leaders: D17, D13, D09; rate leaders: D19, D20, D21. District counts correlate with population at r=+0.986; the count and rate top-three sets overlap 0 districts.
- **Redesign:** Map cases per 100,000 residents with equal-area geometry, print breaks and legend denominator, and pair the map with a count ranking.

### Case 3 — min–max flattening

- **Invited conclusion:** GDP per capita barely varies across the sample.
- **Decoy ruled out:** There are no missing countries; the 60 GDP values genuinely span a large range.
- **Mechanism:** Min–max scaling divides every gap by the full range; the single top value (9.2× the runner-up) stretches the range and compresses the other observations.
- **Evidence:** After min–max scaling, 58/60 countries lie below 0.10 and the median is 0.017; raw GDP runs $283–$120,219.
- **Redesign:** Use percentile ranks when the question is relative ordering (and label that magnitude is discarded), or show raw GDP on a log scale when absolute gaps matter.

### Case 4 — misleading axis order

- **Invited conclusion:** Healthcare access and case rate appear unrelated because no crossing is obvious.
- **Decoy ruled out:** The five axes and the min–max scaling are valid; no scale was omitted.
- **Mechanism:** Parallel-coordinate crossings depend on adjacent axis pairs; the file order inserts two unrelated variables between strongly related access and incidence axes.
- **Evidence:** File order: gdp_pc, healthcare_access, urban_pct, median_age, cases_per_100k; greedy chain: healthcare_access → cases_per_100k → urban_pct → median_age → gdp_pc. Healthcare access and cases_per_100k have r=-0.799 but are three positions apart in the published chart.
- **Redesign:** Order axes using the stated greedy absolute-correlation chain; the paired variables become adjacent and the crossing pattern can be read.

### Case 5 — quantile classes over a flat distribution

- **Invited conclusion:** A five-level incidence gradient is visible across the federation.
- **Decoy ruled out:** The calculations and quantile assignments are correct, and all 24 districts are included.
- **Mechanism:** Quantile classification forces equal-count bins even when the underlying range is substantively tiny; class contrast exaggerates differences.
- **Evidence:** Rates span 31.07–33.40 per 100,000, only 7.2% of the mean. The five quantile breaks are [31.07, 31.49, 32.07, 32.51, 32.94, 33.4].
- **Redesign:** Show the actual values on a common linear dot scale and state that the total spread is small; use quantiles only when equal-count ranking is the explicit purpose.

### Case 6 — unstable rate from a small denominator

- **Invited conclusion:** U32 is nearly five times the national rate and therefore a hotspot.
- **Decoy ruled out:** The division is correct; the defect is not arithmetic or a map projection.
- **Mechanism:** A rate based on a small population has high Poisson variability; treating a noisy small-area estimate as a stable signal overstates certainty.
- **Evidence:** Pooled rate 8.72/100,000; U32 is 40.9/100,000 from 9 cases among 22,000 people (4.7×); 1 of 40 units fall outside the 95% funnel.
- **Redesign:** Show exposure against rate with a widening Poisson funnel and report the small-area numerator and denominator; do not rank a noisy extreme as a proven hotspot.

### Case 7 — areal-scale dependence

- **Invited conclusion:** District income and incidence have only a weak negative relationship (r≈−0.31).
- **Decoy ruled out:** The district-level Pearson correlation is correctly computed across 24 complete records.
- **Mechanism:** A correlation is conditional on its areal units; grouping districts into zones changes within-zone variation and can produce the modifiable areal unit problem (MAUP).
- **Evidence:** District r=-0.308; reaggregated population-weighted zone income versus pooled zone incidence r=-0.746 across 6 zones. These are different estimands, not evidence that one correlation is universally true.
- **Redesign:** Show the district scatter and report zone aggregation as a sensitivity analysis, with the unit of analysis named.

### Case 8 — area-weighted visual impression

- **Invited conclusion:** The outbreak is rural because much of the map is dark.
- **Decoy ruled out:** The rate is normalized, the sequential scale is correct, and the map uses equal-area geometry.
- **Mechanism:** A choropleth gives every square kilometre visible area regardless of population; viewers infer prevalence from the amount of colored land instead of the share of residents affected.
- **Evidence:** The five most populous districts contain 59.9% of residents but only 12.6% of land area; dark-map area therefore does not measure people or the rural share.
- **Redesign:** Pair the rate map with population-weighted counts/rankings or proportional symbols; explicitly describe population rather than colored land area.

### Case 9 — radar area depends on order

- **Invited conclusion:** Region A has a visibly stronger profile because it encloses more area.
- **Decoy ruled out:** Both profiles use the same 0–100 scale and the same six indicators.
- **Mechanism:** Radar polygon area depends on the adjacency/order of axes; a rearrangement changes cross-products and enclosed area without changing any score.
- **Evidence:** Mean scores are 62.3 and 62.0 (difference 0.33); in supplied order their polygon areas are 9,933 and 9,433, a layout-dependent difference.
- **Redesign:** Use paired points or sorted dumbbell bars on a shared linear scale to compare each indicator; do not summarize a radar polygon's area as overall strength.
