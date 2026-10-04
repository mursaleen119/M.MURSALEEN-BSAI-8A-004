# M.MURSALEEN-BSAI-8A-004

## Weak Two — Week 2 Visual Perception

This repository follows the Week 2 visual-perception idea from the reference course repository: https://github.com/UsmarHaider/data-visualization

The easy dataset used here is `tips.csv`, which is the simplest dataset suited to the Week 2 cognitive-load and data-ink task.

### What this task does

This repository focuses on the official Week 2 principle that visual clutter increases cognitive load and reduces readability. The task demonstrates this by:

- creating a deliberately overloaded chart labelled `BAD EXAMPLE`
- showing the source of extraneous load
- removing clutter in stages
- producing a cleaner final chart
- explaining why the cleaner version is easier to read

### Key files

- [weak_two/](weak_two/) — task folder with script and outputs
- [data/](data/) — downloaded dataset
- [weak_two/weak_two.py](weak_two/weak_two.py) — generates the before/after charts
- [weak_two/weak_two_report.md](weak_two/weak_two_report.md) — written reasoning
- [weak_two/outputs/bad_example.png](weak_two/outputs/bad_example.png)
- [weak_two/outputs/five_panel.png](weak_two/outputs/five_panel.png)
- [weak_two/outputs/clean_example.png](weak_two/outputs/clean_example.png)

### Run it

```bash
python -m pip install -r requirements.txt
python weak_two/weak_two.py
```

### Alignment with the official brief

This repo follows the official Week 2 guidance on:

- cognitive load
- extraneous visual marks
- data-ink ratio
- reducing noise in chart design
- clearer communication through simpler encoding

It stays within the part of the brief that is directly supported by the easy `tips.csv` example and avoids adding unsupported tasks beyond the official guidance.
