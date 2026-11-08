# Week 6 — National Grid Authority task
Install the listed packages with `python -m pip install -r weak-6\requirements.txt`.
Run `python weak-6\run_week6.py` from the repository root.
The first run downloads the pinned synthetic source files into the ignored `weak-6\data\` cache.
`partA_process.py` prints the audit and writes the decisions table and cleaned CSV/GeoJSON files.
The processor never edits raw inputs and leaves missing zone-days absent rather than filling zero.
`partB_charts.py` exports three 300-dpi charts for a meter trend, generation mix, and outage-rate comparison.
`partC_figure.py` exports the normalized board figure and writes its counterfactual and parameters in `partC_note.md`.
`partD_interactive.py` exports a self-contained Plotly HTML view; hover, zoom, and legend filtering expose each zone's monthly readings. A reader could also zoom to one unusual month and overstate a longer-term pattern.
The full runner writes all charts into `weak-6\charts\`; deleted or cleaned values are recorded in the audit.
