# DECISIONS_AN_v20: HESTIA vs ghgsim N2O, term by term

Date: 2026-11-04. Consistency check, not validation. No Holos MS2 data. Enteric CH4 is still not compared (no feed inventory, none invented).

Script: `scripts/decompose_hestia_n2o_AN_v1.py` (`fetch` reads the local HESTIA CE API; `build` is offline).
Output: `data/hestia_matched_vs_ipcc_stylized_AN_v2.csv` (one row per farm x source x term: direct, indirect_volatilisation,
indirect_leaching, with the N basis and factor each model used). The terms sum to the AN_v1 totals (`tests/test_hestia_n2o_decomp_AN_v1.py`).
HESTIA's factors were read from its own lookups (`data/hestia_n2o_lookups_AN_v1.json`, dumped by
`scripts/hestia_container/dump_n2o_lookups_AN_v1.py`, glossary 0.103.0, models 0.90.0) and from the recalculated cycle emissions
(`data/hestia_matched_nflows_AN_v1.csv`). IPCC values were re-checked on 2026-11-04 against the 2019 Refinement PDFs
(Vol 4 Ch10 `19R_V4_Ch10_Livestock.pdf`, Ch11 `19R_V4_Ch11_Soils_N2O_CO2.pdf`).

## IPCC 2019 values used (checked in the PDFs)
| Factor | Value | Table |
|---|---|---|
| EF3 liquid/slurry without natural crust | 0 | Ch10 Table 10.21 (Updated) |
| EF3 pit storage below confinements | 0.002 | Ch10 Table 10.21 (Updated) |
| EF3 poultry manure with / without litter | 0.001 / 0.001 | Ch10 Table 10.21 (Updated) |
| FracGasMS liquid without crust (swine, dairy, other cattle) | 0.48 | Ch10 Table 10.22 (Updated) |
| FracGasMS pit (swine) | 0.25 | Ch10 Table 10.22 (Updated) |
| FracGasMS poultry with / without litter | 0.40 / 0.48 | Ch10 Table 10.22 (Updated) |
| FracLeachMS liquid, pit, poultry litter | 0 | Ch10 Table 10.22 (Updated) |
| EF3PRP,CPP wet (cattle, poultry, pigs) | 0.006 (aggregated 0.004) | Ch11 Table 11.1 (Updated) |
| EF4 wet / aggregated | 0.014 / 0.010 | Ch11 Table 11.3 (Updated) |
| EF5 | 0.011 | Ch11 Table 11.3 (Updated) |
| FracGASM | 0.21 | Ch11 Table 11.3 (Updated) |
| FracLEACH-(H) wet | 0.24 | Ch11 Table 11.3 (Updated) |

## What HESTIA (ipcc2019 models, v0.90.0) does
- Direct manure N2O: `EF_N2O-N` lookup per excretaManagement term. Values match Table 10.21: liquid without crust 0, pit 0.002,
  poultry with/without litter 0.001. HESTIA's direct term equals ghgsim's whenever the N basis is the same (turkey: 14.4 vs 14.43).
- Indirect manure N2O: N2O = (NH3-N + NOx-N) x EF4 + NO3-N x EF5, with EF4 climate-specific (wet 0.014).
  **NH3 and NOx are not from IPCC FracGasMS.** HESTIA takes NH3 from EMEP/EEA 2019 (`emepEea2019`) and NOx from Daemmgen 2009
  (`dammgen2009`). The implied volatilised fraction is 0.08 (pig slurry), 0.15 (dairy slurry), 0.18 (beef slurry), 0.14 (poultry),
  0.19 (pig pit) and 0.25 (turkey), against IPCC 0.25-0.48.
  NO3 leaching uses `NO3_EF_2019`, which is 0 for every confined system used here, the same as Table 10.22.
- PRP (pasture) direct: EF3PRP,CPP wet 0.006, the same as Table 11.1.
- PRP indirect: **not produced.** `n2OToAirExcretaIndirect` needs nh3, nox **and** no3ToGroundwaterExcreta. NH3 (1071 kg) and NOx
  (11.1 kg) were computed, but no NO3 emission was returned for the pasture cycle. PRP leaching needs FracLEACH-H site inputs
  (from measurements we did not supply), so the whole indirect term is missing, not zero by method.

## Gap explained, by term
1. **Manure, direct.** Zero in both for liquid slurry (Table 10.21 EF3 = 0, which is correct for IPCC 2019). Where it is non-zero
   (poultry, pit) the EF3 is the same and the gap is only the N basis (point 4).
2. **Manure, indirect volatilisation.** This is the whole liquid-system gap. Dairy example: ghgsim 19,342 kg N x 0.48 x EF4 0.010
   x 44/28 = 145.9 kg; HESTIA 18,314 kg N x 0.150 x 0.014 x 44/28 = 60.4 kg. The ratio is 0.31 (fraction) x 1.4 (EF4) x 0.947
   (N basis) = 0.41. The NH3 fraction is the main cause, not EF3.
3. **Manure, indirect leaching.** 0 in both (FracLeachMS = 0 for these systems).
4. **N basis.** ghgsim's 2019 path computes Nex from Table 10.19 (Updated) Nrate; the HESTIA activity CSV (AN_v1) was given the
   2006-based Nex. This makes the HESTIA N 5% lower for dairy and 4% lower for beef, 6-9% lower for market and farrow-to-finish swine (breeding swine and turkeys are the same because their 2019 Nrate repeats 2006), and 27-31% lower for
   broilers and layers. This is a matching error in v1 inputs, not a model
   difference.
5. **Pasture.** ghgsim 164.05 = direct 85.00 + volatilisation 41.65 + leaching 37.40. HESTIA 81.6 = direct only. Direct differs by
   the N basis alone (9,015 vs 8,652 kg N, same EF3 0.006). The missing 79.05 kg is the indirect term HESTIA did not run.

## Decisions
- D20.1 Report the HESTIA manure N2O gap as a **methodological difference in NH3 volatilisation** (EMEP/EEA vs IPCC FracGasMS),
  not as a disagreement on EF3. Paper wording: "HESTIA's lower manure N2O comes from its EMEP/EEA NH3 fractions; direct EF3 agree."
- D20.2 Pasture: do not compare the HESTIA total with ghgsim's total. Compare direct only (81.6 vs 85.0) and state that HESTIA's
  indirect PRP term needs leaching inputs that were not supplied.
- D20.3 Flag, do not change yet: ghgsim's IPCC 2019 **manure** module uses aggregated EF4 = 0.010, while its 2019 **soil** module
  (and HESTIA) use the wet value 0.014 for this warm-temperate-moist site. Switching would raise ghgsim 2019 manure N2O by 40% on all
  farms and change published draft numbers, so it is queued as a separate PR with a test.
- D20.4 A v2 HESTIA run should supply the 2019 Nex (from Table 10.19 Updated) so the N basis matches; queued.


