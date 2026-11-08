# Week 4 — official assignment implementation

This folder implements the instructor's time-series, proportions, hierarchy, reader and bonus tasks using the official synthetic datasets and the supplied Week 4 toolkit.

## Run

From this directory, install the listed dependencies and run:

```powershell
python download_inputs.py
python run_week4.py
```

`download_inputs.py` caches the official CSV inputs under `data/`; the scoped `.gitignore` keeps those raw course datasets local and uncommitted. The run writes 300-dpi figures, CSV/JSON audits, diagnosis and numeric reports, and the requested PDFs under `charts/`. `vizlib.py` and `tslib.py` are the instructor toolkits.

## Honest limitations

- Week 4 Part C needs a real reader. The pie/bar stimuli and a header-only `pie_ranking_results.csv` are supplied; no reader response, timing, rank error or result has been invented. Follow [`reader_protocol.md`](reader_protocol.md).
- The cleaned daily series spans 518 days after the partial September tail is removed. `seasonal_decompose(period=365)` requires two complete annual cycles, so the annual decomposition is reported as not estimable rather than fabricated. The weekly decomposition and remaining Part B computations do run.
- The bonus uses the historical monthly airline-passenger dataset, cites its source and keeps the source CSV in the deliverables.

## Official sources

- [Instructor Week 4 assignment brief](https://raw.githubusercontent.com/UsmarHaider/data-visualization/main/week4/assignments/TASKS.md)
- [Instructor Week 4 README](https://github.com/UsmarHaider/data-visualization/blob/main/week4/README.md)
- [Week 4 data dictionary](https://raw.githubusercontent.com/UsmarHaider/data-visualization/main/week4/assignments/data/DATA_DICTIONARY.md)
- [Week 4 toolkit source](https://github.com/UsmarHaider/data-visualization/tree/main/week4/assignments)

No copy of the instructor brief or README is bundled here.
