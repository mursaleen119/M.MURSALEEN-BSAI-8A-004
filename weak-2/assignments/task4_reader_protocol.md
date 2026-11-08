# Task 4 participant protocol (not yet run)

Use the 30 rows in `charts/channel_results.csv` in the supplied randomized `trial_order`. For each row, use `draw_channel(ax, channel, value_large, value_small)` from `week2_assignment.py` to prepare a stimulus; do not show the true values or ratio. Ask one consenting reader “The smaller one is what percentage of the larger?” Enter their estimate from 0 to 100 and an anonymous participant code. Save the completed file as `channel_results.csv`. Then call `analyze_channel_results(path)` to compute absolute error, mean error by channel, and the sorted zero-baseline chart. The pre-filled values are trial stimuli only; all reader fields remain blank until real data are collected.

The 30 responses from one person and six ratios are descriptive only. Report errors/noisy outcomes honestly; do not claim population-level statistical power.
