# Data Definition and Methodology Review

This document records what official source material supports about the measures represented by POME EL's eight raw files. It does not prescribe preprocessing, validate a model, or authorize joining series. Accessed 2026-11-09.

## Exchange rates

The Federal Reserve's H.10 daily `DEXINUS` series is Indian rupees per U.S. dollar: daily noon buying rates in New York City for cable transfers, not seasonally adjusted. A missing daily numeric field in the local CSV may reflect a non-publication/non-trading day or a different issue; the source calendar and exact local extraction have not been reconciled.

The G.5 monthly `EXINUS` series uses the same quote and is the average of available daily observations. The Federal Reserve notes that an incomplete current month may be published as preliminary. The local monthly CSV is therefore not interchangeable with an end-of-month quote, nor is it a direct match for the local daily series without respecting the averaging and available-day conventions.

Sources: [Federal Reserve H.10 / DEXINUS](https://fred.stlouisfed.org/series/DEXINUS), [G.5 / EXINUS](https://fred.stlouisfed.org/series/EXINUS).

## Brent

The monthly source identifier `MCOILBRENTEU` is EIA's “Crude Oil Prices: Brent - Europe,” measured in dollars per barrel and not seasonally adjusted. It represents an international Brent spot-price benchmark, not an India-specific landed import cost or the price paid by a particular importer. The official series metadata reviewed here does not specify enough detail to assert the exact monthly aggregation formula. Preserve the published monthly value and its unit; do not infer a formula from the word “monthly.”

Sources: [FRED/EIA series metadata](https://fred.stlouisfed.org/series/MCOILBRENTEU), [EIA spot-price table](https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm), [EIA definitions](https://www.eia.gov/dnav/pet/TblDefs/pet_pri_spt_tbldef2.asp).

## RBI repo rate

The local CSV contains monthly `period,value` observations. Its values are consistent with the RBI policy repo rate in force at each month's end, but the file has no source identifier, unit, explicit month-end rule, or metadata. That interpretation is an inference, not an official verified definition of this file. It must not be described as a monthly average or an observed transaction rate. Obtain a dated RBI/DBIE extract and series metadata before fixing the operational meaning.

Official entry points: [RBI Statistics](https://www.rbi.org.in/Scripts/Statistics.aspx), [DBIE](https://data.rbi.org.in). Exact local series mapping: **PENDING VERIFICATION**.

## NEER and REER

RBI defines NEER as a weighted index of bilateral exchange rates with trading partners and REER as NEER adjusted for relative prices/costs. The 40-currency RBI series uses 2015–16=100 and provides trade- and export-weighted NEER and REER measures. The methodology describes geometric weighting based on the preceding three years of trade (or exports), normalization, and the change from an earlier 36-currency/2004–05-base series. Basket weights can vary across time. The RBI article explains its exchange-rate quotation so that an increase in the index represents rupee appreciation; interpretation should retain that convention.

These are index points, not exchange-rate quotes. The local four-column table's labels align with the RBI measures, but the local series values and later vintage are not independently validated. A rising REER can indicate real appreciation and weaker price-cost competitiveness, all else equal; that is an interpretation, not a causal result.

Sources: RBI, [“Effective Exchange Rate Indices of the Indian Rupee”](https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx?Id=20020); [Current Statistics Table 36](https://rbidocs.rbi.org.in/rdocs/Bulletin/PDFs/36T_2110202486AD6EB67C29453DA3D79C78E257CBB0.PDF).

## CPI

MoSPI's 2024-base CPI uses 2024=100 and weights drawn from HCES 2023–24. “CPI (General)” is the headline general index, while “Combined” identifies the rural/urban combined coverage. The January 2026 launch publication says the new series is accompanied by all-India combined general-index back data from January 2013 to December 2024. The linking factors use 2025 as an overlap year; the combined general-index factor is 0.5267. MoSPI limits direct linkage to the general index because classifications differ; detailed group/item series should not be presumed continuous across the old and new bases.

The official CPI FAQ defines year-over-year inflation as `(CPI_t - CPI_(t-12)) / CPI_(t-12) * 100`. An inflation column is a published rate, not a substitute for the index. The local workbooks' `inflation` fields are blank in some rows; preserve that state and do not silently calculate replacements. The source documents establish the official series design, not that these particular workbooks are authentic source downloads.

Sources: MoSPI, [2024-base launch release](https://www.mospi.gov.in/uploads/latestReleases/latest_release_1770891893893_6b458c0a-c327-4fef-a554-41131ea67273_Press_Relase_of_CPI_for_Jan26.pdf), [CPI 2024 FAQ](https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf).

## WPI

OEA defines WPI as an index of average price change for commodities sold at wholesale/early transaction stages. Its basket covers Primary Articles, Fuel & Power, and Manufactured Products, not services. The 2011–12 base-series FAQ describes weights based on base-year net traded value, with the noted crude-petroleum treatment. The April 2026 release reports Primary Articles 22.62%, Fuel & Power 13.15%, and Manufactured Products 64.23%; they sum to 100%. The separate Food Index has its own weight and is not an additional top-level component to be added to those three.

The local workbook's `COMM_WT` values and category names are consistent with this structure. The official source verifies base 2011–12=100 and weights as percentages. It does not define the meaning of the 505 numeric zeros observed in six detailed commodity rows. Those values remain numeric source values unless OEA provides a documented convention.

Sources: OEA, [WPI FAQ](https://eaindustry.nic.in/uploaded_files/FAQs_on_WPI.pdf), [metadata](https://eaindustry.nic.in/pdf_files/Metadata_WPI.pdf), [April 2026 release](https://eaindustry.nic.in/archive_data/wpi_press_release_201112/summary_apr_2026.doc), [2011–12 download page](https://eaindustry.nic.in/download_data_1112.asp).

## Cross-measure interpretation limits

- CPI and WPI are different price concepts, populations, transaction stages, baskets, and base periods; index levels cannot be compared directly.
- Brent is a global benchmark rather than an India-specific import-price index.
- Nominal FX, NEER/REER, repo, CPI, and WPI do not share a common unit or interpretation merely because they share monthly dates.
- A causal pass-through claim requires a documented specification and timing convention; no such model is implemented or authorized in this audit.
