# Goal 4: Holos Route A - Implementation Status

**Version:** AN_v7  
**Date:** 2026-11-01  
**Branch:** cursor/goal4-phase2-holos-forks-e537  
**Base:** cursor/goal4-holos-route-a-c98e  
**Status:** Phase 3b complete (stylized farms; every previously-zero fork MEASURED)

Does not overwrite `docs/HANDOFF_AN_v6.md`.

---

## Phase 3b completed

Stylized farms in `data/stylized_farms_AN_v1.yaml` (cited IPCC / NRC / EPA Annex 3 cells; ILLUSTRATIVE head counts and TDN–DE pairings). Command: `python3 scripts/measure_holos_forks_stylized_AN_v1.py`. Audit: `docs/HOLOS_CODE_AUDIT_AN_v3.md` (v1/v2 not overwritten).

All eight registered forks fired on at least one farm. Combined (all non-default options) was also MEASURED.

---

## MEASURED vs ESTIMATE (explicit)

**MEASURED on stylized farms (this phase)**

- `HOLOS.GE.digestibility`: dairy forage −2.34% GE / −2.36% CH4; high-grain +5.77% GE / +5.77% CH4
- `HOLOS.VS.digestibility`: dairy forage −4.24% VS; beef −12.45% VS; high-grain +23.08% VS
- `HOLOS.VS.urinary_energy`: high-grain +10.26% VS / +3.03% total CH4; forage diets still 0
- `HOLOS.ENTERIC.calf_zero`, `HOLOS.VS.calf_coeff`, `HOLOS.NEX.calf_nrate`: non-zero on dairy and beef farms that include calves
- `HOLOS.CH4.cover_reduction`: 0.4 crust and 0.25 other-cover multipliers on 100% liquid (factors still UNVERIFIED)
- `HOLOS.YM.dairy`: still fires on dairy; zero on beef
- Combined dairy-forage uncovered: +4.06% CH4 / +3.95% CO2e

**Still ESTIMATE**

- 17-county totals for the seven AN_v2-zero forks (county files still lack those inputs)
- Essex combined +3–8% sketch
- VS-derived N / N2O 6–15%
- “Typically 1–5% VS” as a universal TDN–DE rule
- Canada-only adult GE/VS farm
- ECCC Ym 5.6% table cell (UNVERIFIED)
