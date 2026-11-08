# Week 5 Part F — bonus normalized map

- **Emissions and population:** World Bank Indicators API, indicator `EN.GHG.CO2.MT.CE.AR5` (CO₂ emissions, total excluding LULUCF, Mt CO₂e) and `SP.POP.TOTL`; year 2022; downloaded 2026-11-09. Rate is `Mt × 1,000,000 / people`, in tonnes CO₂e per resident.
- **Boundaries:** Natural Earth, 1:110m Admin 0 Countries, v5.1.2 (`nvkelso/natural-earth-vector`, GeoJSON), downloaded 2026-11-09. Multipart geometries were expanded into Polygon rings; class breaks are computed once per country (`break_values`) so island count does not reweight the quantiles.
- **Join:** 165 country rows represented; emissions/population records without a matched boundary: 82; boundary ISO3 codes without a 2022 value: 9. Values with missing emissions or population were excluded upstream by the World Bank API response; no small areas were suppressed.
- **Classification/projection:** five quantile classes; breaks `[0.05, 0.52, 1.8, 3.73, 6.94, 45.2]` printed in the legend; geolib Lambert cylindrical equal-area.
- **Counterfactual:** raw Mt CO₂e totals would emphasize countries with the largest populations/economies; per-resident emissions answer a different question about average territorial emissions per person.
- Source files used by the script are in `data/partF_worldbank_co2_population_2022.csv` and `data/partF_naturalearth_admin0_v5.1.2.geojson`.
