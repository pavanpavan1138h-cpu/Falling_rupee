# NEER/REER Value Matching Report

## Objective

Determine whether the local NEER/REER monthly file matches an official RBI series or only reflects the correct series definition.

## Local file

`data/raw/05_India_RBI_NEER_REER_40_Currency_Monthly.csv`

## Official evidence

- RBI article: <https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx?Id=20020>
- RBI Bulletin Table 36: <https://rbidocs.rbi.org.in/rdocs/Bulletin/PDFs/36T_2110202486AD6EB67C29453DA3D79C78E257CBB0.PDF>
- RBI Statistics / DBIE access page: <https://www.rbi.org.in/Scripts/Statistics.aspx>

## Verified facts

1. The local file includes the correct four series names: `Trade_NEER`, `Trade_REER`, `Export_NEER`, `Export_REER`.
2. The official RBI methodology confirms the 40-currency base and the 2015-16=100 index benchmark.
3. The 165 local observations are continuous and align with the expected monthly table structure.
4. The local file is not matched to a dated RBI DBIE export in this audit.

## Remaining gap

The local file contains the expected RBI variable names and a plausible historical span, but the actual value-by-value series was not compared to a dated official export. This means the local file is structurally consistent with the official methodology but is not a verified exact source match.

## Conclusion

The file is best classified as `SOURCE DEFINITION MATCH ONLY` rather than `EXACT MATCH`. This is sufficient to justify reading the dataset as a candidate NEER/REER input, but not sufficient to claim exact official historical matching or point-in-time vintage fidelity.
