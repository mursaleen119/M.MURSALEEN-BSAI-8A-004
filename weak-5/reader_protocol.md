# Week 5 Part C — real-reader capture protocol

The required five-reader study has not yet been run. `partC_reader_results.csv` intentionally contains only its header; do not treat it as data.

Recruit at least five real people, one at a time, and record anonymous IDs only. For each reader:

1. Show `charts/week5_partC_two_maps.png` with **Map A (count) only** visible; keep Map B covered. Ask: “Which three counties would you send extra police to, and why?” Record all three codes/names without prompting.
2. Reveal **Map B (rate)** and ask the same question. Record the three responses independently.
3. Do not allow the reader to revise the first answer after seeing Map B. Record the number of counties common to the two sets (0–3).
4. After five or more completed sessions, calculate the mean overlap and report it alongside the sample size and the order limitation. A small convenience sample does not establish a general effect.

**Fields:** `reader_id,mapA_top3_count,mapB_top3_rate,overlap_count,notes`. Use semicolons between names if storing each three-item list in one CSV cell. Never invent or back-fill participant responses.
