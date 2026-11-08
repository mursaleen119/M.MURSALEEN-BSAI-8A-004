# Task A — Cleaning decisions

| What | How detected | Rule applied | Rows affected |
|---|---|---|---:|
| District register — duplicate D11 key with two names and slightly different payloads. | Compare each name to the GeoJSON canonical name. | Retain the exact match, Kotla, and remove the noncanonical duplicate. | 1 |
| District register — D21 population / household ratio was 5,940, far outside every other district. | Compare people-per-household across districts and check the raw household value's scale. | Repair 182 households to 182,000, matching the implied thousand-unit scale and expected aggregate. | 1 |
| District register — two electrification values included a percent sign and were parsed as text. | Inspect raw field values and verify the resulting numeric range. | Remove the literal % and parse as numeric percentage points; retain three truly absent values as missing. | 2 |
| District register — two outage-minute values were -1, impossible for a duration and identified as operator codes. | Check the duration range and dictionary's operator-code convention. | Set the code to missing; preserve district records and outage counts. | 2 |
| Daily returns — 174 dates used a slash format; interpreting all values in one format can swap or corrupt dates. | Check raw date patterns and confirm the parsed reporting span. | Parse ISO dates as %Y-%m-%d and alternate dates as %d/%m/%Y explicitly. | 174 |
| Daily returns — exact duplicate date-zone resubmissions repeated the same payload. | Normalize dates, compare duplicate keys and confirm all measurement columns match. | Keep one copy of each identical row. | 12 |
| Daily returns — three duplicate date-zone groups had conflicting peak/outage payloads. | Compare all measurement columns for each repeated date-zone key. | Keep the first source row as a deterministic tie-break; disclose that its values are not independently validated. | 3 |
| Daily returns — peak_load_mw=-1 is an operator's unavailable code. | Check the measurement range against the data dictionary. | Set -1 to missing; retain the rest of each zone-day. | 46 |
| Daily returns — one sorted cumulative meter reading dropped from 21.4 million MWh to 1,180 MWh. | Sort readings by zone and date, then inspect negative first differences. | Set only the unrecoverable cumulative reading to missing; do not treat it as negative energy. | 1 |
| Daily returns — 128 expected zone-day slots were not filed over the full reporting span. | Reindex the 529-day range for all six zones and compare with filed keys. | Do not synthesize rows or zero values; leave gaps absent and state their count. | 128 |
| Generation mix — each month includes nested published totals as well as eight reconciled leaf parts; summing all rows doubles the result. | Compare month-level leaf sums with published totals and inspect hierarchy labels. | Keep the eight mutually exclusive leaf rows per month; omit parent/total rows from additive analysis. | 18 |

No raw source file is modified. Missing measurements remain missing, and calendar gaps are not filled with zero.
For duplicate daily submissions, first-in-file is a reproducible tie-break rather than a claim that the earliest payload is more accurate; the three conflicts are disclosed in the audit.
