# M.MURSALEEN-BSAI-8A-004

## Weak Two — Week 2 Visual Perception

This repository follows the official Week 2 visual-perception brief from the reference course repository: https://github.com/UsmarHaider/data-visualization

The easiest dataset in the official assignment set has been used here: `tips.csv`.

### Official Week 2 goal

The assignment focuses on how the human brain processes visual information. In this task, the emphasis is on reducing cognitive load, removing extraneous marks, and improving the data-ink ratio so the real finding is easier for the reader to understand.

### What this repo contains

- a deliberately overloaded chart (`BAD EXAMPLE`)
- a five-step de-cluttering sequence
- a cleaner final chart
- a short written explanation of the design decisions

### Key locations

- [weak_two/](weak_two/) — task script and outputs
- [data/](data/) — dataset used for the task
- [weak_two/weak_two.py](weak_two/weak_two.py) — chart generation script
- [weak_two/weak_two_report.md](weak_two/weak_two_report.md) — written reasoning
- [weak_two/outputs/bad_example.png](weak_two/outputs/bad_example.png)
- [weak_two/outputs/five_panel.png](weak_two/outputs/five_panel.png)
- [weak_two/outputs/clean_example.png](weak_two/outputs/clean_example.png)

### Run the task

```bash
python -m pip install -r requirements.txt
python weak_two/weak_two.py
```

### Assignment alignment

This repository follows the official Week 2 idea using the easy dataset `tips.csv` and is designed around the Week 2 principles of:

- cognitive load
- data-ink ratio
- clutter reduction
- cleaner chart design
- clearer visual communication
