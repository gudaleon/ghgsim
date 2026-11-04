# HESTIA matched stylized farms, AN_v3 (D20.4): 2019 Nex

Consistency check, not validation. HESTIA CE 7.1.0 (models 0.90.0), local Docker, drafts route as in
HESTIA_MATCHED_AN_v1/v2. Run 2026-11-04 00:28 EST, draft `ghgsim-matched-an-v1-bdfec2`.

## What changed vs AN_v1
1. Excreta N given to HESTIA = head x the Nex that ghgsim's `ipcc2019.manure` uses (2019 Vol 4 Ch10
   Table 10.19 (Updated) Nrate x TAM; spec EPA Nex override where present, as before). AN_v1 used the
   override-or-2006 Nex, which caused the N-basis gaps in HESTIA_MATCHED_AN_v2 (dairy 5%, beef 4%, swine
   6-9%, poultry 27-31%). Changed herds: dairy heifer 65.5 -> 87.8, dairy calf 19.7 -> 26.5, beef calf
   13.9 -> 17.9, broilers 0.361 -> 0.522, layers 0.545 -> 0.742, market swine 7.05 -> 7.72 kg N/head/yr.
   Overrides (dairy cow 153, beef cow 74, breeding swine 17.3, turkeys 1.84) unchanged.
2. ghgsim columns from `data/ipcc_2006_vs_2019_stylized_AN_v3.csv` (climate EF4, DECISIONS_AN_v21).

Script `scripts/hestia_matched_stylized_AN_v2.py`; outputs `data/hestia_matched_*_AN_v3.*`.

## Results (kg/yr, ghgsim 2019 AN_v3 vs HESTIA AN_v3)
| farm (representative) | term | ghgsim 2019 | HESTIA v1 | HESTIA v3 | HESTIA vs 2019 |
|---|---|---|---|---|---|
| dairy (all 5) | manure N2O | 204.3 | 60.4 | 63.8 | -68.8% |
| beef cow-calf (3) | manure N2O | 95.2 | 34.6 | 36.0 | -62.2% |
| broiler litter | manure N2O | 108.3 | 34.2 | 49.4 | -54.4% |
| layer litter / high-rise | manure N2O | 77.0 / 90.1 | 25.8 | 35.1 | -54.4% / -61.0% |
| turkey litter | manure N2O | 95.2 | 63.9 | 63.9 | -32.9% |
| market swine liquid | manure N2O | 81.6 | 11.9 | 13.1 | -83.9% |
| breeding swine liquid | manure N2O | 36.6 | 5.9 | 5.9 | -84.0% |
| farrow to finish | manure N2O | 96.7 | 77.3 | 82.2 | -15.0% |
| beef pasture | soil (PRP) N2O | 164.1 | 81.6 | 85.0 | -48.2% |
| crop urea/lime | soil N2O | 41.6 | 39.7 | 39.7 | -4.7% |
| all farms | manure CH4 | = | = | = | 0.0% (layers -7.7%) |

Manure CH4 is unchanged (driven by VS, not N). HESTIA manure N2O rises 3-44% with the 2019 N basis, but the
gap to ghgsim widens because ghgsim's 2019 manure indirect N2O now uses EF4 wet 0.014 (AN_v21). The remaining
gaps are method differences already decomposed in HESTIA_MATCHED_AN_v2: HESTIA's NH3 (EMEP/EEA 2019) and NOx
(Daemmgen 2009) volatilisation fractions are far below IPCC FracGasMS (e.g. dairy 0.150 vs 0.48), and HESTIA
produced no PRP leaching N for the pasture farm. These are differences between models, not errors in either.
Enteric CH4 is not compared (HESTIA needs feed inputs; none are invented).
