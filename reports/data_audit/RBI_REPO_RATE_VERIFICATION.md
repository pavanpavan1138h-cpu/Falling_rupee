# RBI Repo Rate Verification

## Objective

Determine whether the local repo-rate series is an exact RBI official series or an inferred approximation from the local file.

## Official sources consulted

- RBI Statistics and DBIE access: <https://www.rbi.org.in/Scripts/Statistics.aspx>
- RBI Data and Statistics portal: <https://data.rbi.org.in>
- Relevant policy-rate publications and historical rate announcements were reviewed in the project’s earlier audit materials.

## Local file under review

`data/raw/04_India_RBI_Policy_Repo_Rate_Monthly.csv`

## Current finding

The local file is not yet authenticated to an exact official RBI series or export.

The file contains only two columns: `period` and `value`, with monthly observations. The values behave consistently with a policy-repo-rate time series that is set at the policy level rather than a monthly average. However:

- the exact RBI series identifier is not included;
- the file contains no source URL, retrieval timestamp, or vintage marker;
- the file does not explain whether the value is a month-end rate, an average rate, or an announced policy action;
- the local date labels are month-start keys, while the values appear to correspond to policy settings that remain in force for part or all of the month.

## Why this matters

A policy repo rate and a monthly average repo rate are not interchangeable. The distinction determines the correct interpretation for any pass-through model or early-warning approach. In the absence of exact RBI metadata, the local file must be treated as a policy-rate proxy rather than an authenticated RBI data export.

## Recommended treatment

- Retain the series as an auxiliary input only.
- Obtain a dated RBI/DBIE export with series metadata before using it as a primary explanatory variable.
- Do not claim a precise month-end or monthly-average convention unless the official RBI source explicitly states it.

## Conclusion

The repo-rate file is currently classified as `UNVERIFIED` for source-to-file authenticity. It may reflect the official RBI policy repo rate, but that cannot be claimed without a matched RBI source export or a documented series identifier.
