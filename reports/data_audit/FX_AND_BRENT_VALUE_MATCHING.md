# FX and Brent Value Matching Report

## Official data sources

- USD/INR daily: <https://fred.stlouisfed.org/series/DEXINUS>
- USD/INR monthly: <https://fred.stlouisfed.org/series/EXINUS>
- Brent: <https://fred.stlouisfed.org/series/MCOILBRENTEU>
- Federal Reserve H.10 release: <https://www.federalreserve.gov/releases/h10/current/>
- Federal Reserve G.5 release: <https://www.federalreserve.gov/releases/g5/current/>

## Comparison summary

| Local file | Comparison result | Determination |
|---|---|---|
| `03_USD_INR_Exchange_Rate_Daily.csv` | Official daily FRED series shares the same dates and values on all comparable dates. Local missing values align with official missing dates. | EXACT MATCH |
| `03_USD_INR_Exchange_Rate_Monthly.csv` | Exact agreement with official monthly FRED series. | EXACT MATCH |
| `02_Brent_Crude_Oil_Spot_Price_Monthly_USD_per_Barrel.csv` | Exact agreement with official FRED series for the full monthly range. | EXACT MATCH |

## Important interpretation notes

### USD/INR daily

The local file is not missing data in a way that indicates corruption. The 552 missing numeric values correspond to official dates where the FRED series does not publish a value. This is consistent with the daily data definition and should not be treated as an erroneous omission.

### Monthly USD/INR

The local monthly USD/INR file is a direct match to the official monthly average series, not a month-end spot rate. The Federal Reserve G.5 notes that monthly values are averages of available daily figures and that current-month values may be preliminary.

### Brent

The local Brent monthly file is an exact official FRED match. It reflects the EIA monthly benchmark series, and the local file should be interpreted as a monthly price series with the official EIA/FRED definition, not as a chained or transformed import-cost series.

## Conclusion

The local FX and Brent series are value-matched to their official sources and are therefore the strongest-verified inputs in the project.
