# Goal 4: Holos Route A - Implementation Status

**Version:** AN_v6  
**Date:** 2026-11-01  
**Branch:** cursor/goal4-phase2-holos-forks-e537  
**Base:** cursor/goal4-holos-route-a-c98e  
**Status:** Phase 3 complete (measured fork deltas, four-way comparison, ECCC Ym check)

Does not overwrite `docs/HANDOFF_AN_v5.md`.

---

## Phase 3 completed

1. **Measured** per-fork CH4/N2O/CO2e on 17 VT/DE counties. Command: `python3 scripts/measure_holos_forks_vt_de_AN_v1.py`. Audit: `docs/HOLOS_CODE_AUDIT_AN_v2.md`.
2. **Four-way** IPCC 2006 / IPCC 2019 / Holos Canada / Holos US. Command: `python3 scripts/compare_holos_fourway_vt_de_AN_v1.py`. Route A: `docs/HOLOS_ROUTE_A_AN_v2.md` (v1 not overwritten).
3. **ECCC dairy Ym 5.6%:** no table/page lists 5.6%. Independently read ECCC 2024/2025 NIR Part 2 Annex 3.4 §A3.4.2.1 range 5.5–5.7%. Point value left **UNVERIFIED**. `docs/HOLOS_ECCC_YM_AN_v1.md`. Canada params `data/holos_params_canada_AN_v4.csv`. Forks `data/holos_forks_AN_v2.json`.

---

## MEASURED vs ESTIMATE (explicit)

**MEASURED**

- Only `HOLOS.YM.dairy` (5.6 vs 6.5) moves 17-county emissions on the EPA mature-cow dataset: +14.68% enteric CH4, +7.81% total CH4, 0% N2O, +5.30% CO2e (`epa_vs`).
- Seven other registered forks: **MEASURED zero** (GE override; no calves; no crust; EPA VS or TDN=DE; EPA DE% and default forage both yield UE=0.04).
- Four-way 17-county sums vs IPCC 2006: IPCC 2019 −5.00% CO2e; Holos Canada −0.69% CO2e (EPA activity + Canada Ym/B0/MCF hybrid); Holos US +0.10% CO2e. IPCC 2006/2019 match committed county CSVs.

**ESTIMATE** (not run; inputs not invented)

- TDN≠DE, high-grain UE disagreement, calf VS/Nrate/enteric, cover 0.4/0.25, AN_v1 6–15% VS / 8–20% manure CH4 ranges, Canada-only adult GE/VS farm.

---

## Remaining outside Phase 3

- Soil N2O remaining audit (CE-08)
- Storage dynamics (CE-01, CE-11, CE-13)
- OOP compartments and links
- ECCC 2022 edition PDF still not opened
