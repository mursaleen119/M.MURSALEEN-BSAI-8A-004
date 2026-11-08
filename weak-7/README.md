# Week 7 - Transit authority dashboard
Install packages with `python -m pip install -r weak-7\requirements.txt`.
Run `python weak-7\run_week7.py` from the repository root for the full pipeline.
The first run downloads pinned instructor inputs to ignored `weak-7\data\`.
`partA_process.py` audits raw files, writes decisions, and generates `weak-7\clean\`.
`partB_charts.py` exports four question-led, 300-dpi charts to `weak-7\charts\`.
`partC_interactive.py` writes the default PNG; `--interactive` opens mode filters and reset.
`partD_screen.py` exports the four-panel, 300-dpi board dashboard.
Run scripts A, B, C, then D separately to inspect each stage.
Cleaned files are script-generated; raw inputs stay unchanged and uncommitted. Task notes document limits and parameters.
