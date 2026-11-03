# holos_liang2020 dry-county fallback (AN v1)

Decision by Alex, 2026-11-03: under `HOLOS.N2O.ef1 = holos_liang2020`, a site that is dry (growing-season P/PE < 1), not irrigated and has no `FR_Topo` uses the IPCC default EF1 instead of Holos Eq 2.5.2. The `EF1_status` output (provenance) is then `fallback-IPCC-default`.

## IPCC default EF1 (verified)
| Source | Table | EF1 (kg N2O-N / kg N) | Range |
|---|---|---|---|
| 2006 IPCC Guidelines, Vol 4 Ch 11 | Table 11.1 | 0.01 | 0.003-0.03 |
| 2019 Refinement, Vol 4 Ch 11 | Table 11.1 (Updated), aggregated | 0.010 | 0.002-0.018 |
| 2019 Refinement, same table, disaggregated | dry climates, all N inputs | 0.005 | 0.000-0.011 |

The fallback uses the module's `EF1` parameter (`IPCC2006.EF1.all` = 0.01 in `data/ipcc_params_AN_v*.csv`, status VERIFIED, Table 11.1 p. 11.11). The 2019 aggregated value is the same. The values were rechecked on 2026-11-03 against the 2019 Refinement Ch 11 PDF (https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch11_Soils_N2O_CO2.pdf) and the repo's verified parameter rows.

## Behaviour
| Case | EF1 used | EF1_status |
|---|---|---|
| P/PE > 1 or = 1, or irrigated | Holos Eq 2.5.1-2.5.4 | holos_liang2020 |
| P/PE < 1 with FR_Topo | Holos Eq 2.5.2 | holos_liang2020 |
| P/PE < 1, no FR_Topo, not irrigated | IPCC EF1 (0.01) | fallback-IPCC-default |
| P or PE missing, or PE = 0 | IPCC EF1 | UNVERIFIED-input (unchanged) |

With the county table (`data/county_p_pe_may_oct_AN_v2.csv`), 3,041 of 3,142 US counties are dry under Hargreaves PE, so most US runs with `county_fips` and no `FR_Topo` now get `fallback-IPCC-default`.

## Open question
Whether the dry fallback should use the 2019 disaggregated dry value (0.005) instead of the aggregated 0.01. That would halve direct N2O for these counties. Not implemented; the aggregated value is used, as decided.

Code: `src/ghgsim/modules/holos/soil_n2o.py` (`FALLBACK_IPCC_DEFAULT`, `_is_dry_without_topo`). Tests: `tests/test_crops_soils.py`.
