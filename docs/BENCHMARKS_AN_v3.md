# Benchmarks (AN v3)

Supersedes `BENCHMARKS_AN_v2.md` (fixes dataset ID heading; G: folders renamed 2026-11-03). Manifest: `data/benchmarks_manifest_AN_v3.json` (SHA-256 per file).

## Provenance
- Source: downloaded by Alex via LandEngine/EDI portal on 2026-11-03.
- Originals (untouched): `G:\My Drive\Papers_To_Publish\Ratna\DATA`.
  - `DATA\GlobalN2O_edi877v1\` (formerly `GRACE`): extracted EDI files, plus `GRACE.zip` (GRACEnet) and its `GRACE_unzipped\`.
  - `DATA\GRACEnet_adc1235557\` (formerly `GlobalNO2`): GRACEnet Figshare files, plus `GLOBALNO2edi.877.1.zip` (EDI) and its `GLOBALNO2edi.877.1_unzipped\`.
  - The two zips still sit in the opposite-named folder (renamed folders only; no files moved).
- Working copies: `C:\ghgsim-data\benchmarks\global_n2o_edi877v1\` (9 files, 118.7 MB) and `...\gracenet_adc1235557\` (6 files, 37.2 MB).
- GRACEnet download is byte-identical to the Figshare API download (article 24660216 v1). No "33 CSV / 378 MB" GRACEnet set exists in either download.

## Global N2O DB (EDI edi.877.1) profile
| Table | Rows x cols |
|---|---|
| Sitelibrary_V1 | 438 x 24 |
| Summary_V1 | 993 x 49 |
| cumulativeN2O_V1 | 1,085 x 20 |
| CropYield_V1 | 893 x 39 |
| DailyGHG_V1 | 549,454 x 58 (85,176 non-null n2o) |

Units (from EML): daily `n2o`, `n2osd`, `CH4` g/ha/day; `Annual.n2o` kg/ha/yr; `cumulative.n2o` kg/ha; `Avg_Fert_N_Rate_kgNha` kg N/ha; `soilC_perc` % (SOC as %C, 63% non-null in Summary). EML does not say whether N2O is N2O or N2O-N; check before use.

Sites (unique SiteID): Summary 106, cumulativeN2O 105, DailyGHG 71, Sitelibrary 54.
By country (Summary): USA 41 + "US" 2 = **43 US**, **Canada 7**, Australia 15, China 6, Panama 5, others 1-2.
- Lat/lon: present; 18 of 106 Summary sites lack them.
- Crop: present (86% non-null). N rate: present (82%). Tillage: `soil_tillage` 34% non-null (nt/ct/st/yes/CT/n, not harmonized); daily `Tillage.type`/`Fertilizer.kgN.ha` are empty.
- Years: StudyYear 1991-2019; daily 1991-2018; cumulative 1993-2016.

## Oddities
1. G: folder names were swapped; renamed 2026-11-03 (zips still cross-filed, above).
2. Country labels not harmonized (USA/US, UK/United Kingdom).
3. Site counts differ across tables (54-106).
4. Daily CO2 unit in EML is kg/ha/yr, unlike n2o/CH4 g/ha/day; likely metadata error.
5. Daily tillage and fertilizer columns are entirely empty.
