# Task 1 human visual-search protocol (not yet run)

Participant results are intentionally blank; do not treat templates as evidence. The brief says “18 trials” but also specifies one present and one absent trial for each 3 conditions × 5 set sizes, which requires 30 trials. This protocol follows the complete factorial specification (30 trials); ask the instructor if 18 is a strict cap.

1. Obtain informed consent; use one adult volunteer, participant code only. Explain one target before each condition block, not before each trial.
2. Use the supplied fixed-seed stimuli. For each of the 30 rows in `week2_task1_search_results_TEMPLATE.csv`, render that trial; start `time.perf_counter()` after the figure is ready, then accept Y/N keyboard response and stop the timer.
3. Record response, correctness and elapsed seconds immediately. Keep target-present and target-absent separate. Do not edit out slow/error trials.
4. Save the filled file as `search_results.csv`; then run `python week2_reader_analysis.py search_results.csv` (or analyze the CSV in the notebook) to calculate condition-specific target-present slopes.

The experiment runner below is usable in an interactive Matplotlib backend. The default script only renders sample trials and leaves the template empty.
