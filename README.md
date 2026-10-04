# M.MURSALEEN-BSAI-8A-004

This repository contains the completed Week 2 task, named "Weak Two".

## Task selected

The assignment uses the easy dataset `tips.csv` from the Week 2 visual-perception brief. This dataset is simple and readable, and it suits the Week 2 goal of showing how cognitive load, clutter, and data-ink decisions change the reader's experience.

## Task folder

- `weak_two/` — Week 2 task files and generated outputs

## Run the task

```bash
python -m pip install -r requirements.txt
python weak_two/weak_two.py
```

The script downloads the dataset if needed and saves the before/after charts in the `weak_two/outputs/` folder.

## Assignment alignment

This implementation follows the Week 2 task logic for cognitive load and data-ink ratio:

- a deliberately overloaded chart labeled `BAD EXAMPLE`
- a clearer redesign with fewer visual tasks
- a short explanation of extraneous load and why the cleaner chart is easier to read
