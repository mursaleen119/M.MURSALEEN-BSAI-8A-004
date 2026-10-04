# M.MURSALEEN-BSAI-8A-004

This repository contains the completed weak tasks for the Data Visualization course, organized by week, and it also includes the completed Week 2 weak-two task using the official `tips.csv` dataset.

## Weekly folders
- `week1/` — weak task 1 solution
- `week2/` — weak task 2 solution
- `week3/` — weak task 3 solution

## Weak Two — Week 2 Visual Perception

This repository follows the official Week 2 visual-perception idea from the reference course repository: https://github.com/UsmarHaider/data-visualization

The easy dataset used here is `tips.csv`, which is the simplest dataset suited to the Week 2 cognitive-load and data-ink task.

### Official Week 2 goal
The assignment focuses on how the human brain processes visual information. The emphasis is on reducing cognitive load, removing extraneous marks, and improving the data-ink ratio so the real finding is easier for the reader to understand.

### What this task covers
The project follows the Week 2 visual-perception idea of reducing cognitive load and improving the data-ink ratio:

- overloaded chart labeled `BAD EXAMPLE`
- simplified five-step de-cluttering process
- final cleaner chart with a clearer message
- short written reasoning about clutter, load, and readability

### What this repo contains
- a deliberately overloaded chart (`BAD EXAMPLE`)
- a five-step de-cluttering sequence
- a cleaner final chart
- a short written explanation of the design decisions

### Key locations
- `weak_two/` — task script, report, and generated charts
- `data/` — dataset used for the task
- `weak_two/weak_two.py` — chart generation script
- `weak_two/weak_two_report.md` — written reasoning
- `weak_two/outputs/bad_example.png` — bad example output
- `weak_two/outputs/five_panel.png` — de-cluttering process output
- `weak_two/outputs/clean_example.png` — final clean chart output

### Run it

```bash
python -m pip install -r requirements.txt
python weak_two/weak_two.py
```

### Assignment alignment
This repository follows the official Week 2 idea using the easy dataset `tips.csv` and is designed around the Week 2 principles of:

- cognitive load
- extraneous visual marks
- data-ink ratio
- reducing noise in chart design
- clearer communication through simpler encoding

It stays within the part of the brief that is directly supported by the easy `tips.csv` example and avoids adding unsupported tasks beyond the official guidance.
