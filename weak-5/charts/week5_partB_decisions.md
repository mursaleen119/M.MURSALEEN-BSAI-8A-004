# Week 5 computed decisions

- Bubble area is directly proportional to population, with a maximum of 300 points squared and a minimum area of 0.05; the diameter ratio is `sqrt(max population / min population) = 81.29`. Small marks are hard to read, so the companion bars are important.
- Overplotting uses the 142 countries available in 2007 (alpha 0.22, hexbin gridsize 20, and a 2-D KDE). The brief's 9,000 points and planted 800-point cluster do not exist in this one dataset.
- For 2007 GDP per capita, min–max median=0.119, z-score median=-0.434, and percentile-rank median=0.504.
- PCA uses five declared numeric features after log-transforming population and GDP columns; the first two components explain 80.0% of standardized variance.
- District polygons, county rates, a small-area Poisson funnel and projected land areas cannot be computed without adding another dataset, so those results are not fabricated.
