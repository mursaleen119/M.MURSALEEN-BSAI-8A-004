# Week 4 Part C — real-reader capture protocol

The required reader session has not yet been run. `pie_ranking_results.csv` intentionally contains only its header; do not treat it as data.

1. Recruit one real participant; explain the voluntary ranking task and record only an anonymous reader ID.
2. Show `charts/week4_partC_pie_stimulus.png` first. Do not reveal the values. Start `time.perf_counter()` when the image appears; ask the reader to rank letters A–H, largest share first; stop the timer when they finish.
3. Then show `charts/week4_partC_bar_stimulus.png`, ask for the same ranking, and time it the same way.
4. Record two rows in `pie_ranking_results.csv`, one for each stimulus, with the participant ID, order, and elapsed seconds. Compare with the correct order computed from `data/shares_eight.csv`; record misplaced letters and their positions in the report.
5. State explicitly that n=1 cannot establish a population-level effect. Do not replace missing responses with a model answer or simulated reader.

**Fields:** `reader_id,stimulus,order_largest_first,seconds`. Valid `stimulus` values: `pie` and `bar`.
