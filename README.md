# M.MURSALEEN-BSAI-8A-004

This repository contains the completed Week 2 weak task and the weekly project structure for the wider Data Visualization course.

## Weekly folders
- `week1/` — weak task 1 solution
- `week2/` — weak task 2 solution
- `week3/` — weak task 3 solution

## Weak Two — Week 2 Visual Perception

This repository contains a completed Week 2 task based on the easiest usable dataset from the official brief: `tips.csv`.

### What this task covers
The project follows the Week 2 visual-perception idea of reducing cognitive load and improving the data-ink ratio:

- overloaded chart labeled `BAD EXAMPLE`
- simplified five-step de-cluttering process
- final cleaner chart with a clearer message
- short written reasoning about clutter, load, and readability

### Official task intent
The Week 2 assignment focuses on how the human brain processes visual information. The goal is to reduce extraneous load and remove visual noise so the reader can understand the real finding quickly and accurately.

### Dataset
The task uses the easy dataset `tips.csv` from the Week 2 visual-perception brief.

### Key folders
- `weak_two/` — task script, report, and generated charts
- `data/` — dataset used for the task

### Run the task

```bash
python -m pip install -r requirements.txt
python weak_two/weak_two.py
```

### Generated outputs
- `weak_two/outputs/bad_example.png`
- `weak_two/outputs/five_panel.png`
- `weak_two/outputs/clean_example.png`

### Written summary
- `weak_two/weak_two_report.md`

### Assignment alignment
This implementation follows the Week 2 task logic for cognitive load and data-ink ratio:

- a deliberately overloaded chart labeled `BAD EXAMPLE`
- a clearer redesign with fewer visual tasks
- a short explanation of extraneous load and why the cleaner chart is easier to read
