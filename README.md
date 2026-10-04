# M.MURSALEEN-BSAI-8A-004

## Weak One — Why Visualization & Choosing the Right Chart

This repository follows the official Week 1 assignment from the reference course repository: https://github.com/UsmarHaider/data-visualization

The official Week 1 task uses the `datasaurus.csv` dataset and focuses on proving that summary statistics alone can be misleading.

### What this task does

The task follows the official brief and does the following:

- computes the mean, standard deviation, and correlation for each dataset in `datasaurus.csv`
- saves the summary table as a CSV
- plots all 13 datasets in a grid of scatter plots
- demonstrates why the same summary statistics can hide very different shapes

### Key files

- [weak_one/weak_one.py](weak_one/weak_one.py) — official Week 1 implementation
- [data/datasaurus.csv](data/datasaurus.csv) — dataset from the official reference repo
- [weak_one/outputs/weak_one_summary_table.csv](weak_one/outputs/weak_one_summary_table.csv) — statistics table
- [weak_one/outputs/weak_one_datasaurus_grid.png](weak_one/outputs/weak_one_datasaurus_grid.png) — grid of scatter plots

### Run it

```bash
python -m pip install -r requirements.txt
python weak_one/weak_one.py
```

### Alignment with the official brief

This task matches the official Week 1 assignment guidance:

- 13 datasets in `datasaurus.csv`
- summary statistics for each dataset
- visual proof that statistics alone are not enough
- chart-based explanation of why plotting matters

---

## Weak Two — Week 2 Visual Perception

This repository also follows the official Week 2 visual-perception idea from the same reference course repository: https://github.com/UsmarHaider/data-visualization

The easy dataset used here is `tips.csv`, which is the simplest dataset suited to the Week 2 cognitive-load and data-ink task.

### What this task does

This task focuses on the official Week 2 principle that visual clutter increases cognitive load and reduces readability. The task demonstrates this by:

- creating a deliberately overloaded chart labelled `BAD EXAMPLE`
- showing the source of extraneous load
- removing clutter in stages
- producing a cleaner final chart
- explaining why the cleaner version is easier to read

### Key files

- [weak_two/](weak_two/) — task folder with script and outputs
- [data/](data/) — downloaded dataset folder
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
