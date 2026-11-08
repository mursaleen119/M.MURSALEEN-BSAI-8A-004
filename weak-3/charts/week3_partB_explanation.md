# Part B — Lie Factor

Computed with `vizlib.lie_factor()`; values in 0.95–1.05 are honest. C is the only honest chart. B and E encode area, so `ink_dimension=2` is required: ignoring the square makes a 1.5× width/height icon appear to be a 1.5× change instead of a 2.25× area change; a radius-scaled bubble compounds the error. D understates pollution growth, which benefits actors who want deterioration to look modest.

Chart F (the dual-axis rebuild) has no valid Lie Factor: each series has a separate arbitrary axis mapping and there is no shared data-to-ink baseline. In the actual data, revenue exceeds cost in all six months and margin grows from PKR 8m to PKR 25m.

chart_id                       subject  ink_dimension  data_effect  graphic_effect  lie_factor            verdict                                                       encoding
       A            Corporate tax rate              1        0.067           5.000       75.00 exaggerates 75.00x Bars drawn from a 29.6% baseline, so only the tips are visible
       B Federal health budget (Rs bn)              2        0.500           1.250        2.50  exaggerates 2.50x               A coin icon scaled 1.5x in BOTH height and width
       C        Export earnings ($ bn)              1        0.200           0.200        1.00             honest                             Bars from zero: 5.0 cm then 6.0 cm
       D           Air-pollution index              1        0.500           0.125        0.25 understates (0.25)                             Bars drawn 8.0 cm then 9.0 cm tall
       E    City population (millions)              2        3.000          15.000        5.00  exaggerates 5.00x        A bubble whose RADIUS was set proportional to the value
