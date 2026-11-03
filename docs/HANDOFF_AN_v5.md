# Goal 4: Holos Route A - Implementation Status

**Version:** AN_v5  
**Date:** 2026-11-01  
**Branch:** cursor/goal4-phase2-holos-forks-e537  
**Base:** cursor/goal4-holos-route-a-c98e  
**Status:** Phase 2 complete (source-correct defaults + holos_as_coded forks)

---

## Phase 2 completed

Modules (IPCC-correct default; labelled `holos_as_coded` forks in `data/holos_forks_AN_v1.json`):

1. Enteric CH4 (`holos.enteric`) — Eq 10.21; Eq 10.3 GE when NE+DE supplied
2. VS (`holos.vs`) — Eq 10.24
3. Manure CH4 (`holos.manure_ch4`) — Eq 10.23
4. Manure N2O (`holos.manure_n2o`) — Eq 10.25 and 10.26-10.27

Forks: `HOLOS.GE.digestibility`, `HOLOS.ENTERIC.calf_zero` (CE-06), `HOLOS.VS.digestibility`, `HOLOS.VS.urinary_energy`, `HOLOS.VS.calf_coeff` (CE-07), `HOLOS.CH4.cover_reduction` (CE-14), `HOLOS.NEX.calf_nrate`. Dairy Ym is a parameter refinement (`HOLOS.YM.dairy`), not a bug fork.

UE default follows IPCC 2006 p. 10.54 (0.04 typical, 0.02 when DE% > ~80%). See `docs/HOLOS_PHASE2_FORKS_AN_v1.md` for the correction to the audit's "reversal" sketch.

Parameters: `data/holos_params_canada_AN_v3.csv`, `data/holos_params_us_AN_v2.csv`. Holos file:line is never VERIFIED.

---

## Left for Phase 3

- Measure per-fork CH4, N2O, and CO2e on VT/DE (replace estimated ranges in the audit)
- Four-way comparison: IPCC 2006, IPCC 2019, Holos Canada, Holos US
- Confirm ECCC 2022 dairy Ym 5.6% against the NIR table
- Soil N2O remaining audit (CE-08 and related)
- Storage dynamics (CE-01, CE-11, CE-13) — not annual rate equations
- OOP compartments and links (design Phases 3-4)

---

## Documents

- `docs/HOLOS_PHASE2_FORKS_AN_v1.md` — forks and UE note
- `docs/HOLOS_SOURCES_AN_v2.md` — Phase 2 sources
- `docs/HOLOS_CODE_AUDIT_AN_v1.md` — unchanged (no measured impacts yet)
- `docs/HANDOFF_AN_v4.md` — Phase 1 handoff (not overwritten)

**Document:** docs/HANDOFF_AN_v5.md  
**Date:** 2026-11-01
