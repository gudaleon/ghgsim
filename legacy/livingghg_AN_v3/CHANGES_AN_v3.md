# livingghg v3 (AN_v3) - changes from v2
1. livingghg/gapfill.py: fills NASS 2022 county cow counts withheld as (D). Fork F011: sizeclass (default), prior_census (USGS/Falcone 2021 method using NASS 2017/2012/2007/2002), or none. Includes the masking validation (reproduces the Phase 2 numbers: milk cows 21.5% median / 22.9% head-weighted abs error; beef cows 3.6% / 6.7%).
2. livingghg/crop_residue.py: IPCC 2019 Eq 11.6 (Updated) / Eq 11.7 crop residue N (F_CR) from NASS 2022 county corn grain, soybean and wheat harvested area and production.
3. enteric.py: uses the herd Ym_pct when present (fork F013 ym_source, default epa_state). Herds without Ym_pct behave as in v2.
4. data/forks_AN_v3.json = v2 forks + F013. data/forks_pipeline_AN_v3.json = F010 (REFRAMED: watershed-only unpermitted-facility sensitivity, not a census undercount), F011, F012 (manure-N basis).
5. scripts/county_assumptions_AN_v3.json (built by build_county_assumptions_AN_v3.py): per-state EPA 2025 Annex 3.11 values that replace the v1 placeholders.
6. scripts/run_counties_AN_v3.py: fill + EPA per-state inputs + soil N2O (F_SN, F_ON, F_CR). Refuses F010 != 1 unless --allow-watershed-factor is given.
7. run_heavy_AN_v2.bat: generic Windows launcher (install root as argument, workers = NUMBER_OF_PROCESSORS-2, 'trial' flag). NOT yet run.
8. data_us/ (EPA, USGS, IPCC residue table) and new data_nass/ files (2002-2017 cow censuses, 2022 crops).
Known limitations: covers mature cows only (no heifers, calves, bulls, steers or feedlot cattle). One MCF zone for all states. Applied managed cattle manure N is not in F_ON. Wheat uses the winter-wheat residue parameters. Counties with (D) crop data get F_CR = 0 (flagged). Falcone's N data are 2017, so they are a year mismatch with the 2022 census.
