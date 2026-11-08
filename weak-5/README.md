# Week 5 — official assignment implementation

This folder implements the instructor's multivariate, spatial, reader and bonus tasks using the official synthetic datasets and the supplied Week 5 toolkit.

## Run

From this directory, install the listed dependencies and run:

```powershell
python download_inputs.py
python run_week5.py
```

`download_inputs.py` caches the official CSV/GeoJSON files under `data/`; the scoped `.gitignore` keeps those raw course datasets local and uncommitted. The run writes 300-dpi figures, numeric/audit reports, reader stimuli, and requested PDFs under `charts/`. `vizlib.py` is the supplied shared toolkit. `geolib.py` is the instructor toolkit with narrowly documented compatibility/extensions: a writable correlation matrix for current NumPy/Pandas, a declared linear marker-size range for a matching real-value legend, and country-level class breaks for multipart boundaries.

## Honest limitation

Week 5 Part C requires at least five real readers. The two maps and a header-only `partC_reader_results.csv` are supplied, but no real people were available in this non-interactive run. No participant responses, overlap counts or mean are fabricated. Use [`reader_protocol.md`](reader_protocol.md) to collect the required observations.

## Official sources

- [Instructor Week 5 assignment brief](https://raw.githubusercontent.com/UsmarHaider/data-visualization/main/week5/assignments/TASKS.md)
- [Instructor Week 5 README](https://github.com/UsmarHaider/data-visualization/blob/main/week5/README.md)
- [Week 5 data dictionary](https://raw.githubusercontent.com/UsmarHaider/data-visualization/main/week5/assignments/data/DATA_DICTIONARY.md)
- [Week 5 toolkit source](https://github.com/UsmarHaider/data-visualization/tree/main/week5/assignments)

No copy of the instructor brief or README is bundled here.
