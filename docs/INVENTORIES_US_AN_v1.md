# U.S. national inventory recalculations for Paper B (AN_v1)

Checked 2026-11-03. Companion to `docs/INVENTORIES_AN_v1.md` (PR #25), same layout. Source: EPA,
*Inventory of U.S. Greenhouse Gas Emissions and Sinks* (the "GHGI"). Every number below is parsed by
`scripts/fetch_epa_ghgi_AN_v1.py` from the PDF text, or quoted from the report with a page number.
PDF URLs and SHA-256 hashes are in `data/inventories_US_manifest_AN_v1.json`; CSVs are in
`data/inventories_US_AN_v1/`.

| Edition | Coverage | Report no. | Where obtained |
|---|---|---|---|
| 2024 | 1990-2022 | EPA 430-R-24-004 | epa.gov main-text PDF |
| 2025 | 1990-2023 | EPA 430-R-25-003 | EPA NEPIS (Dockey P101EZHC) |
| 2026 | - | - | **None.** EPA's report archive lists no 1990-2024 edition. A non-EPA 1990-2024 inventory exists (Univ. of Maryland CGS "GHGIA", Desai et al. 2026, doi:10.13016/g1xw-qftw) but is *not* used here |

Glossary. *MMT CO2 Eq.* = million metric tonnes CO2-equivalent (= Mt CO2e; 1 MMT = 1,000 kt).
*Recalculation* = EPA revising earlier years in a new edition. *Data splicing* = EPA's statistical
extrapolation for recent years whose activity data are not yet available. *DayCent* = the Tier 3
process model EPA uses for soil N2O and rice CH4.

**GWP basis:** both editions use AR5 100-yr GWPs (CH4 28, N2O 265). 2025 edition: ES-3, Table ES-1
and p. 1-10; 2024 edition: ES-3. So no GWP switch sits between these two editions (the AR4-to-AR5
switch happened in the 2024 edition, vs the 2023 edition; not quantified here).

## 1. Agriculture, 2025 edition (MMT CO2 Eq., AR5; Table 5-1, p. 5-3)

| Year | Total ag | Enteric CH4 | Manure CH4 | Manure N2O | Soils N2O | Rice CH4 | Liming CO2 | Urea CO2 | Burning CH4 | Burning N2O |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1990 | 551.5 | 183.1 | 39.1 | 13.4 | 289.1 | 18.9 | 4.7 | 2.4 | 0.5 | 0.2 |
| 2005 | 582.5 | 188.2 | 55.0 | 15.2 | 294.7 | 20.6 | 4.4 | 3.5 | 0.6 | 0.2 |
| 2022 | 593.3 | 192.6 | 64.7 | 17.0 | 291.8 | 18.0 | 3.2 | 5.2 | 0.6 | 0.2 |
| 2023 | 595.4 | 187.1 | 65.1 | 16.8 | 296.3 | 18.7 | 5.3 | 5.3 | 0.6 | 0.2 |

The EPA agriculture total excludes LULUCF (cropland/grassland soil carbon) and agricultural energy use.

## 2. Recalculations, 2024 edition vs 2025 edition (MMT CO2 Eq.)

Latest common year = 2022. Differences from Table 5-1 of each edition (1-decimal rounding, so ±0.1
noise). EPA's own sector figure (2025 edition Table 9-2, p. 9-3) in the last row.

| Category | 1990 | 2005 | 2022 |
|---|---:|---:|---:|
| Enteric CH4 | 0.0 | 0.0 | 0.0 |
| Manure CH4 | 0.0 | 0.0 | 0.0 |
| Manure N2O | 0.0 | 0.0 | 0.0 |
| Ag soils N2O | +0.3 (+0.10%) | +0.6 (+0.20%) | +1.0 (+0.34%) |
| Rice CH4 | 0.0 | 0.0 | -0.9 (-4.76%) |
| Liming CO2 | 0.0 | 0.0 | -0.1 |
| Urea CO2 | 0.0 | 0.0 | -0.1 |
| Field burning CH4 / N2O | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| **Total (Table 5-1 diff)** | **+0.4 (+0.07%)** | **+0.7 (+0.12%)** | **-0.1 (-0.02%)** |
| **Total (EPA Table 9-2)** | **+0.3** | **+0.7** | **(0.1)** |

1990: +0.4 vs +0.3 is a rounding difference between the two methods. Table 9-4 (p. 9-7) agrees:
Enteric and Manure "NC" (no change), Rice (0.9) in 2022, Ag Soil Management +0.3/+0.7/+1.0.

## 3. EPA's stated causes (2025 edition)

| Category | Stated cause | Page |
|---|---|---|
| Agriculture overall | Ag Soil Management is the only agriculture item in the "Key Recalculations" table: "Accuracy. Use of updated time-series activity data and updated data splicing methods"; +1.0 MMT in 2022 (+0.2%), average +0.6 | Table 9-3, p. 9-4 |
| Ag soils N2O | (a) revised time series of manure N amendments and pasture/range/paddock manure N; (b) revised surrogate data for data splicing; (c) corrections to NRI activity-data uncertainty found by QA/QC. Average +0.6 MMT (+0.2%) 1990-2022 | p. 5-55 |
| Enteric CH4 | "No time-series recalculations were performed"; 1990-2022 retained; 2023 from a simplified approach (EFs + extrapolated populations) | p. 5-12 |
| Manure CH4/N2O | No time-series recalculations; same simplified 2023 approach | p. 5-24 |
| Rice CH4 | Correction of data splicing for 2021-2022 (rice yield/area covariates had been applied to swapped years); 2022 down 0.3 MMT or 1.8% per text | p. 5-33 |
| Liming CO2 | Updated USGS limestone/dolomite data (Willett 2018-2024) and QC revisions to 1993-2023; 2005 +0.3%, 2016 +3.9%, 2021 <0.1%; whole series <0.1% | p. 5-59 |
| Urea CO2 | Data splicing changed from 5-yr linear extrapolation to linear regression with ARMA errors for 2016-2023; average -0.1 MMT (-1.4%) for 2016-2022 | p. 5-62 |
| Field burning | Sugarcane 2021-2023 switched to ARMA regression; reported changes are to CO and NOx (precursors) only | p. 5-72 |

**Flag (rice):** the rice text says 2022 fell by 0.3 MMT (1.8%), but Table 5-1 (18.9 -> 18.0) and
Table 9-4 both show -0.9 in 2022. Not resolved; EPA's text may describe a different quantity.

## 4. 2019 Refinement adoption (2025 edition)
- Manure management: "IPCC (2019) Tier 1 default N2O emission factors and Methane conversion factors (MCFs) for dry systems" (p. 5-18); dry-system MCFs "set equal to default IPCC factors based on state climate ... (IPCC 2019)" (p. 5-19). Liquid/lagoon/deep-pit MCFs stay U.S.-specific.
- Enteric: IPCC 2019 decision tree and default uncertainty (pp. 5-10, 5-12); Tier 1 EFs for minor species cite Crutzen et al. via IPCC 2006/2019.
- Planned, not adopted: 2019 Refinement digester N2O EF, digester MCFs, liquid-system MCF method (p. 5-25).
- None of the 2024->2025 agriculture recalculations is attributed to the 2019 Refinement.

## 5. Gaps
1. No EPA 2026 edition (1990-2024); no third edition to compare. The U.S. CRT for 2025 was not fetched.
2. Values are from PDF text at 0.1 MMT precision. EPA's CSV data tables / Data Explorer (finer precision) were not fetched; recalcs of <0.05 MMT appear as 0.0.
3. Rice: text-vs-table conflict above.
4. The 2024 edition's own recalculations (vs 2023 edition, incl. the AR4->AR5 switch) are not extracted.
5. Separate direct vs indirect soil N2O split not extracted (Table 5-16 has it; add in v2 if needed).

## 6. Reproduce
```
pip install pymupdf
python scripts/fetch_epa_ghgi_AN_v1.py --pdf-dir C:/ghgsim-data/epa_ghgi --out data/inventories_US_AN_v1
```
The script downloads both PDFs if missing (about 17 MB each; keep them out of the repo), checks hashes
in the manifest it writes, and parses Table 5-1 (both editions) and Table 9-2 (2025).

## Citations (accessed 2026-11-03)
- EPA (2024). *Inventory of U.S. Greenhouse Gas Emissions and Sinks: 1990-2022.* EPA 430-R-24-004. https://www.epa.gov/system/files/documents/2024-04/us-ghg-inventory-2024-main-text_04-18-2024.pdf
- EPA (2025). *Inventory of U.S. Greenhouse Gas Emissions and Sinks: 1990-2023.* EPA 430-R-25-003. https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P101EZHC.txt
- EPA. U.S. Greenhouse Gas Inventory Report Archive. https://www.epa.gov/ghgemissions/us-greenhouse-gas-inventory-report-archive
