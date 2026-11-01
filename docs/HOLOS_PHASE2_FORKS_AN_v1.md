# Holos Route A Phase 2 - Source-correct defaults and forks

**Version:** AN_v1  
**Date:** 2026-11-01  
**Branch:** cursor/goal4-phase2-holos-forks-e537  
**Scope:** Goal 4 Phase 2 only (no VT/DE fork-impact measurement)

---

## Policy

For each Holos process in this phase:

1. The **default** is the source-correct published equation (IPCC 2006 Vol 4 Ch 10).
2. Each **confirmed Holos discrepancy** is a labelled `holos_as_coded` option in the fork registry (`data/holos_forks_AN_v1.json`).
3. Parameters are labelled **VERIFIED** (primary published source with page/table), **SOURCE-TRACED** (Holos or other intermediate citation), or **UNVERIFIED**. A Holos file:line is never VERIFIED.

Registry: `ghgsim.modules.holos.forks.get_holos_fork_registry()`.

---

## Modules

| Module | ID | Default equation | Forks |
|--------|----|------------------|-------|
| Enteric CH4 | `holos.enteric` | IPCC 2006 Eq 10.21 p. 10.30; GE from Eq 10.3 p. 10.16 when NE+DE supplied | `HOLOS.GE.digestibility`, `HOLOS.ENTERIC.calf_zero` (CE-06), `HOLOS.YM.dairy` (refinement) |
| Volatile solids | `holos.vs` | IPCC 2006 Eq 10.24 p. 10.54 | `HOLOS.VS.digestibility`, `HOLOS.VS.urinary_energy`, `HOLOS.VS.calf_coeff` (CE-07) |
| Manure CH4 | `holos.manure_ch4` | IPCC 2006 Eq 10.23 p. 10.53 | `HOLOS.CH4.cover_reduction` (CE-14) |
| Manure N2O | `holos.manure_n2o` | IPCC 2006 Eq 10.25 and 10.26-10.27; Nex Eq 10.30 | `HOLOS.NEX.calf_nrate` |
| Facade | `holos.manure` | Delegates to CH4 + N2O | same as children |

`holos.soil_n2o` was not rewritten in Phase 2 (remaining audit item in `HOLOS_CODE_AUDIT_AN_v1.md`).

---

## Urinary energy (UE) note

`HOLOS_CODE_AUDIT_AN_v1.md` finding 2 described IPCC UE as 0.04 for high-grain and 0.02 otherwise, and called Holos "reversed". The IPCC quotation in that same file (Vol 4 Ch 10 p. 10.54) says:

- typical UE = **0.04** GE
- exception: high-concentrate diets with DE% greater than approximately **80%** may use UE = **0.02**

Holos (as described in the audit) uses UE = 0.02 when grain% >= 85, else 0.04. That is the **same direction** as IPCC. The implemented default follows the IPCC quotation, not the audit's inverted implementation sketch. The `holos_as_coded` fork switches on grain% rather than DE%. Tests in `tests/test_holos_vs.py` show the two options differ only when those switch criteria disagree.

This correction is recorded here rather than overwriting `HOLOS_CODE_AUDIT_AN_v1.md`. Measured VT/DE impacts remain Phase 3.

---

## Parameter files

- Canada: `data/holos_params_canada_AN_v3.csv` (v2 not overwritten)
- US: `data/holos_params_us_AN_v2.csv` (v1 not overwritten)

Canada v3 summary is produced by `tests/test_holos_param_status.py` (status vocabulary, VERIFIED gate, Holos file:line never VERIFIED).

---

## Not in Phase 2

- Measured per-fork CH4/N2O/CO2e on VT/DE
- Four-way IPCC 2006 / 2019 / Holos Canada / Holos US county comparison
- Independent confirmation of ECCC 2022 dairy Ym 5.6%
- Soil N2O CE-08 and remaining audit items
- Compartments and links (OOP Phases 3-4)
