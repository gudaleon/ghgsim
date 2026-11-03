# Benchmarks (AN v5)

Supersedes `BENCHMARKS_AN_v4.md` (adds N2O vs N2O-N unit check, 2026-11-03). Locations unchanged from v4. Manifest: `data/benchmarks_manifest_AN_v4.json` (SHA-256 per file).

## Provenance
- Source: downloaded by Alex via LandEngine/EDI portal on 2026-11-03.
- Originals (untouched): `G:\My Drive\Papers_To_Publish\Ratna\DATA`.
  - `DATA\GlobalN2O_edi877v1\` (formerly `GRACE`): extracted EDI files, `GLOBALNO2edi.877.1.zip`, `GLOBALNO2edi.877.1_unzipped\`.
  - `DATA\GRACEnet_adc1235557\` (formerly `GlobalNO2`): GRACEnet Figshare files, `GRACE.zip`, `GRACE_unzipped\`.
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
1. G: folder names and zips were swapped; fixed 2026-11-03 by rename + Move-Item (nothing deleted; 30 files before and after).
2. Country labels not harmonized (USA/US, UK/United Kingdom).
3. Site counts differ across tables (54-106).
4. Daily CO2 unit in EML is kg/ha/yr, unlike n2o/CH4 g/ha/day; likely metadata error.
5. Daily tillage and fertilizer columns are entirely empty.

## N2O vs N2O-N in DailyGHG_V1 `n2o` (checked 2026-11-03)
**Result: not determinable from the published sources checked. Do not assume either basis.**

- EDI EML `edi.877.1.xml`, table "daily GHG", attribute `n2o`: definition "measured nitrous oxide flux in sample", unit `gramsPerHectarePerDay`. No element/basis is given. The EML contains no "N2O-N" string anywhere (`n2osd`, `Annual.n2o`, `cumulative.n2o` likewise only give kg or g per ha).
- EML points to the paper: "Please check Dorich et al., 2020 (https://doi.org/10.1016/j.cosust.2020.04.006) for further scientific background and creation information related to the Global N2O Database."
- Paper (verified on ScienceDirect/doi.org): Dorich, C.D., Conant, R.T., Albanito, F., Butterbach-Bahl, K., Grace, P., Scheer, C., Snow, V.O., Vogeler, I., van der Weerden, T.J. (2020). Improving N2O emission estimates with the global N2O database. *Current Opinion in Environmental Sustainability* 47, 13-20. https://doi.org/10.1016/j.cosust.2020.04.006. Full text is paywalled; the publicly visible text does not state the unit basis. Not read in full.
- Dataset citation: Global N2O Database version 1.0, EDI, https://doi.org/10.6073/pasta/09a95cf44cd7835db002b0089ed5ffc3.
- Database site (https://ecoapps.nrel.colostate.edu/global_n2o/) returned HTTP 500 on 2026-11-03, so its "Field Data" upload template could not be checked.

Next steps: read the Dorich et al. full text (via institutional access) and/or the Field Data template, or ask the maintainers (global_n2o_database@lists.colostate.edu). Many contributing studies report g N2O-N/ha/day, but that is an assumption, not evidence for this DB.
