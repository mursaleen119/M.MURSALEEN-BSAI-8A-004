# Week 5 Part B — computed decisions

## 1 · Bubble-size range

`lo=18`, `hi=360` points²; Matplotlib `s` encodes **area**, linearly mapped from population `0.6–353.4 M`. The resulting diameter ratio is `sqrt(hi/lo)=4.47:1`. The floor keeps the smallest country mark visible; the cap keeps the largest from covering its neighbours. The legend uses actual population values and the same mapping. A bounded area scale is a deliberate readability compromise; it is not radius scaling.

## 2 · Overplotting

Parameters: opaque alpha=1; transparent `alpha=0.16`; hexbin `gridsize=55`; 2-D Gaussian KDE on a 160×160 grid. The supplied 800-point cluster is **visible in all four** renderings: opaque scatter shows a compact saturated clump, transparency preserves the local density contrast, and both hexbin and KDE show a distinct secondary density peak. The radius-0.15 neighbourhood around its center contains `133` points; this is a local neighborhood count, not the cluster's full membership. All four are exported for direct comparison. The hexbin is recommended because it communicates counts per cell without a kernel-bandwidth assumption, with KDE as a smooth check. The center is indicated by a cross in all panels. `week5_partB_overplotting.png` is the diagnostic image.

## 3 · Scaling and PCA

The five multivariate axes exclude `pop_m`, which is reserved for bubble area. Methods and GDP summaries are in `week5_partB_scaling_metrics.csv`:

```
method   gdp_min  gdp_median  gdp_max  countries_below_0.10  gdp_std
minmax  0.000000    0.017372 1.000000                    58 0.127184
zscore -0.361632   -0.225045 7.500995                    50 1.000000
  rank  0.016667    0.508333 1.000000                     5 0.288635
```

PCA on z-scored columns: PC1 explains `0.675`, PC2 `0.162`; the two-axis view explains `83.7%` and omits `16.3%` of standardized variance. Full component ratios: `week5_partB_pca_variance.csv`.

## 4 · Projection before area

Four northernmost districts (`D21, D22, D19, D24`) account for `10.51%` of spherical area versus `11.08%` under raw degree-space shoelace. The largest per-district share distortion is `D04` (0.35 percentage points). Total Mercator polygon area is `1.340×` the spherical total. This inflation makes a map's polygon area depend on latitude, so use the toolkit's equal-area projection when area itself carries the visual weight.

## 5 · Small-area stability

Pooled rate `8.72` cases per 100,000; `1/40` observed units fall outside 95% Poisson limits. U32's extreme is a noisy small-denominator signal, not automatically a stable hotspot. Under a normal Poisson approximation, the 95% upper funnel around a reference rate of 9 falls below 18 at population **42,685**:

`n = ceil(1.96² × 9 × 100,000 / (18−9)²)`.

This is the threshold for distinguishing 18 from a reference of 9 using the reference-rate funnel; the exact Poisson interval will differ slightly. The small-area map/diagnosis must report numerator, denominator and the stability check.
