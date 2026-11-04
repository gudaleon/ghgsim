# DECISIONS_AN_v21: climate-specific EF4 in the IPCC 2019 manure module (D20.3 follow-up)

Date: 2026-11-04. Delegated routine technical decision (Alex delegates these to the agents).

## D21.1 ipcc2019.manure 2.1.0 uses Table 11.3 (Updated) EF4 by climate
- Problem (found in HESTIA_MATCHED_AN_v2 / D20.3): `IPCC2019Manure` applied the aggregated EF4 = 0.010
  (ParamRef `IPCC2006.EF4.all`) to manure NH3+NOx volatilisation (2019 Vol 4 Ch10 Eq 10.26/10.27), while
  `IPCC2019SoilN2O` already used the disaggregated 2019 Vol 4 Ch11 Table 11.3 (Updated) EF4
  (wet 0.014, dry 0.005). HESTIA (EF4 wet 0.014) does the same as the soil module.
- Change: new ParamRefs `IPCC2019.EF4.all|wet|dry`; new input `ef4_mode`:
  - `climate` (default): wet 0.014 when the 2019 climate zone ends in `_moist`/`_wet`, dry 0.005 when it
    ends in `_dry`; aggregated 0.010 when no climate zone is given or derivable.
  - `aggregated`: 0.010 everywhere (sensitivity; reproduces pre-v21 results exactly).
  New outputs `EF4_used`, `EF4_basis`. Only `N2O_indirect_vol` changes; CH4, direct N2O, leaching N2O and
  N_MMS_Avb are unchanged. Tests: `tests/test_manure_ef4_climate_AN_v1.py`.
- Wet/dry rule: Table 11.3 (Updated) wet/dry are the moisture regimes of Vol 4 Ch3 / Ch11 (wet: MAP/PET > 1
  in temperate/boreal; tropical moist and wet are wet), the same rule `climate_zone_2019()` already uses.

## D21.2 Reruns
- Stylized: `scripts/compare_ipcc_2006_2019_stylized_AN_v3.py` ->
  `data/ipcc_2006_vs_2019_stylized_AN_v3.csv` (climate, warm_temperate_moist -> 0.014) and
  `data/ipcc_2006_vs_2019_stylized_ef4agg_AN_v3.csv` (0.010 sensitivity; numerically identical to AN_v2).
  Manure N2O (2019) rises 22-40% on the 17 farm x manure rows with managed manure (e.g. dairy 145.9 -> 204.3
  kg N2O; beef cow-calf 68.0 -> 95.2). Pasture-only farm and crop farm unchanged.
- County: `scripts/run_us_county_2006_vs_2019_AN_v2.py` never used the module for manure N2O; it already
  applies `IPCC2019.EF4.wet|dry` from each county's climate zone (its line `ef4m = ...`). The county and
  national AN_v2 outputs are therefore already consistent with D21.1 and are not rerun (no new numbers).
- Unchanged by design: 2006 runs (2006 EF4 0.010 has no climate split).
