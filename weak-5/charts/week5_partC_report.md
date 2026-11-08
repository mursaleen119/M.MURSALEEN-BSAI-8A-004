# Week 5 Part C — maps and reader protocol

Map A and Map B use the same Natural/Jenks 5-class scheme, sequential Blues ramp, boundary layer and equal-area projection. The only data change is denominator: Map A maps counts; Map B maps crimes per 100,000 residents. Joined records: 20/20. Four unmatched boundary polygons are left out: D21, D22, D23, D24; unmatched crime records: 0.

Self-check from the synthetic file (not reader evidence): r(count,population)=+0.935; count top three: Dunmere, Pellbrook, Grimsby; rate top three: Hollowfield, Netherby, Elmsworth; ranking overlap=0. One map is a map of recorded crime volume, the other of per-resident rate.

**Real-reader data remain uncollected.** `partC_reader_results.csv` is a header-only capture template; no people were simulated and no mean overlap is claimed. Recruit at least five real readers and follow `reader_protocol.md`, showing A first, then B, with no revision. The results—not the self-check—must support the reported mean overlap.
