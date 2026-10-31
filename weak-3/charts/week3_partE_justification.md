# Part E — written justification

**One source dataset:** Gapminder (1,704 country-year rows, 142 countries, five continents, 1952–2007; no missing required values). All weekly tasks use this same dataset. Country/year rows are retained; summaries state their aggregation explicitly.

**Panels and parameters.** The income histogram uses 21 geometric bins on a log x-scale because GDP per capita is strongly right-skewed. Life expectancy boxplots retain outliers and use the five continent categories. The scatter uses log GDP per capita and continent colour as context, not as the only data encoding. The correlation heatmap uses a diverging palette with `vmin=-1`, `vmax=1`, and zero centered. No dual axes are used.

**Interpretation and limitations.** The country-level association between income and life expectancy is descriptive, not causal. Aggregated continent means conceal within-continent variation. A 5-year observation interval cannot establish monthly seasonality. Gapminder has no visual-search reaction times or reader responses; required Week 2 human results are explicitly left pending and have a collection workflow.

**Ethical data handling.** There are no missing required values and no observations are excluded. Income is log-scaled but never removed. Country aggregates and weighting choices are labelled. The GDP ratio is descriptive and is not presented as a causal inequality explanation.

**Redesign trade-off.** Grouping and highlighting reduce visual load but make within-group country paths less prominent. Direct labels avoid legend lookups but focus attention on selected countries only.
