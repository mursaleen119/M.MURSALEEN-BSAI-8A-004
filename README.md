# Data Visualization Coursework

Weeks 1–3 are completed using **one source dataset only**: Gapminder.

## Dataset

- `data/gapminder.csv` — 1,704 country-year observations, 142 countries, five continents, 1952–2007.
- Required fields have no missing values.
- This is the single source dataset. Tables and charts in `outputs/` are derived results, not additional input datasets.
- Source: Gapminder data included with the [course repository](https://github.com/UsmarHaider/data-visualization).

## Run

```powershell
python -m pip install -r requirements.txt
python coursework\solutions.py
```

Open [`coursework/coursework.ipynb`](coursework/coursework.ipynb) to review the 15 task sections and embedded chart outputs. Run the script first to regenerate all figures and summary files.

## Coverage

| Week | Tasks completed with Gapminder |
|---|---|
| 1 | Summary versus shape; trend aggregation/highlights; distributions and relationships; chart selection/redesign; long-term time series |
| 2 | Preattentive highlighting; six grouping cues; cognitive-load redesign; position/length versus area; capstone redesign |
| 3 | Nine chart failure modes and redesigns; Lie Factor calculations; colour-vision palette simulation; four-panel development review; written justification |

The original course tasks use different datasets and, in Week 2, controlled stimuli. To honour the one-dataset requirement, this repository adapts the concepts to Gapminder rather than retaining conflicting source datasets or pretending that Gapminder contains those other measurements.

## Human-participant tasks

No human responses or reaction times are fabricated. To collect authentic observations, run:

```python
from coursework.solutions import collect_human_results, load_data
collect_human_results(load_data())
```

The function records visual-search response time, Gestalt group counts, channel estimates, and the reader's verbatim redesign interpretation in `outputs/human_results.csv`. These components remain pending until a real participant completes them.

## Outputs

- `outputs/` — generated figures, summary tables, diagnostics, and written Week 3 justification.
- `coursework/solutions.py` — reproducible pipeline for all 15 adapted tasks.
- `coursework/vizlib.py` — course palette, colour-vision simulation, and Lie Factor helpers.
