# Task A — Data decisions

| What | How detected | Rule applied | Rows affected |
|---|---|---|---:|
| No source-data corrections were warranted in `data/gapminder.csv`. | Checked 1,704 country-year keys, missing cells, country/year coverage, numeric validity, and value ranges; the audit is printed and saved in `partA_audit.txt`. | Keep all rows and use the original single source file. Do not write a duplicate “clean” CSV. | 0 changed; 1,704 retained |

The instructor's transit-specific defects, route overlap, fare-table hierarchy, and daily-return calendar cannot be detected from Gapminder; those files are not included or synthesized. The data contain no geographic coordinates or boundaries, so no spatial join or normalized map is claimed.
