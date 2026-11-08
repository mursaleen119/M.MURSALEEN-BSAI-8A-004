# Part E — written justification

**Panel 1 — heart-rate histogram.** The safety-review question concerns the shape of the valid resting-rate distribution. A histogram is appropriate for a continuous measure; 30 equal-width bins are explicit. Readings above 250 bpm were removed as device faults (n=29); zero bpm records (n=8) were also excluded as invalid. Mean heart rate moves from 78.83 to 78.05 bpm. The figure was also produced without exclusion; see `week3_partD_heart_rate_appendix.png`.

**Panel 2 — ward length of stay.** Box plots compare center and spread by ward after melting the intentionally wide file. Whiskers use 1.5×IQR and fliers remain visible. Median days: {'Cardiology': 1.69, 'Day Surgery': 0.25, 'General Medicine': 1.26, 'ICU': 3.48}.

**Panel 3 — blood pressure.** The scatter uses all 10,000 records, alpha=0.22 to reduce overplotting, and a fitted line; systolic/diastolic r=0.89. MAP is derived from these measures and is not an independent clinical variable.

**Panel 4 — correlation matrix.** Pearson r uses a diverging map fixed at −1…+1 with neutral zero and only the lower triangle. BMI 0 (n=84) and 999 (n=402) were set to missing (n=486 invalid BMI cells). No patient rows were removed from the other panels.

All data are synthetic course records, not real patients. Dates were parsed from the three observed source formats, ward aliases normalized, units labeled, fliers kept, and MAP excluded from the matrix. The cleaning rules are based on format/measurement validity, not desired findings; the raw appendix makes HR exclusions reversible and inspectable.
