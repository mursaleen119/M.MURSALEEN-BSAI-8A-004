# Task C — Interaction contract

**Default state:** the 2007 scatter shows all 142 countries, with GDP per capita on a log-scaled x-axis and life expectancy in years on the y-axis.

**Controls:** each continent checkbox hides or restores that continent's country points; it does not change the data, scale, year, or other continents. Multiple continents may be visible together. **Reset** restores all five groups. The default PNG is saved to `charts/partC_default.png` before the window opens.

**Wrong conclusion to guard against:** comparing filtered groups can invite a causal story about income and longevity. The view labels the association as descriptive, keeps the same log scale and year when filtering, and says that the points are countries—not individuals or a causal estimate. The exclusive continent categories do not overlap, and the control does not invite users to sum country counts into a transit-network total.

Run `python weak-7\week7_solution.py --interactive` from the repository root in an environment with a Matplotlib GUI backend. Headless checks and static exports use `python weak-7\week7_solution.py` without the flag.
