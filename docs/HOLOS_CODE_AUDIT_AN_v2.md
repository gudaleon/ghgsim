# Holos Code Audit Against Primary Sources — measured VT/DE fork impacts

**Version:** AN_v2  
**Date:** 2026-11-01  
**Does not overwrite:** `docs/HOLOS_CODE_AUDIT_AN_v1.md` (equation findings, Holos file:line traceability)  
**Branch:** `cursor/goal4-phase2-holos-forks-e537`

Equation-level audit text remains in AN_v1. This version replaces the AN_v1 **estimated** VT/DE magnitudes with values from actually running the Holos modules on the 17 Vermont and Delaware counties. Anything not produced by that run is labelled **ESTIMATE**.

---

## How this was measured

**Command (also stored as the `command` column in the CSVs):**

```bash
python3 scripts/measure_holos_forks_vt_de_AN_v1.py
```

**Outputs:**

- `data/holos_fork_deltas_vt_de_AN_v1.csv` — 17 counties × 2 pathways × (baseline + 8 forks)
- `data/holos_fork_deltas_vt_de_summary_AN_v1.csv` — 17-county sums
- `data/holos_fork_deltas_vt_de_AN_v1.meta.json`

**Runner:** `scripts/holos_vt_de_runner_AN_v1.py`

**Farm assembly (not invented):**

- County cow counts, soil N, and committed IPCC totals: `legacy/livingghg_AN_v3/results_TRIAL_AN_v3/counties_{VT,DE}_AN_v3.csv` (14 VT + 3 DE = 17)
- Animal characteristics: `legacy/livingghg_AN_v3/scripts/county_assumptions_AN_v3.json` (EPA 2025 Annex 3.11). `_assumptions.scope` = mature cows only (no calves). Liquid/slurry mapped to `liquid_nocrust`.
- GWP: AR5 CH4 = 28, N2O = 265
- Baseline forks: registered defaults (`source_correct` for bug forks; `HOLOS.YM.dairy` = `eccc_2022_canada` = 5.6% GE)
- Dairy GE: EPA state GE (VT 401.2, DE 358.4 MJ/day)
- Beef Ym: EPA state (6.5% both states) — held constant so the dairy Ym fork is isolated
- MCF: IPCC 2006 Table 10.17, 15C zone (same zone assumption as the county dataset)
- Cover type: `none` (not in the dataset)
- Animal class: `adult`

**Two VS pathways (both MEASURED; TDN/forage/calves/cover still not invented):**

| Pathway | Manure VS used | Status of extra inputs |
|---------|----------------|------------------------|
| `epa_vs` (primary county assembly) | EPA `VS_kg_day` override | No Eq 10.24 |
| `eq1024_vs` | IPCC 2006 Eq 10.24 from EPA GE and DE% | ASH = 8% (IPCC Eq 10.24 example, SOURCE-TRACED); TDN set equal to DE because TDN is not independently observed; forage omitted (module default 100%) |

No net-energy diet (NE_m, RE_m, …) exists in the county files, so `HOLOS.GE.digestibility` cannot be evaluated.

---

## MEASURED 17-county totals (`epa_vs`)

Baseline (registered defaults) vs each fork toggled to its non-default option. Sums over 17 counties.

| Fork | Alt option | Fired? | Δ CH4 kg | Δ CH4 % of total | Δ enteric CH4 % | Δ N2O kg | Δ CO2e t | Δ CO2e % | Evidence |
|------|------------|--------|----------|------------------|-----------------|----------|----------|----------|----------|
| `HOLOS.YM.dairy` | `ipcc2006_table_10_12` (6.5%) | yes | +2,551,895 | +7.807898 | +14.683897 | 0 | +71,453.05 | +5.300570 | **MEASURED** |
| `HOLOS.GE.digestibility` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |
| `HOLOS.ENTERIC.calf_zero` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |
| `HOLOS.VS.digestibility` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |
| `HOLOS.VS.urinary_energy` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |
| `HOLOS.VS.calf_coeff` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |
| `HOLOS.CH4.cover_reduction` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |
| `HOLOS.NEX.calf_nrate` | `holos_as_coded` | no | 0 | 0 | 0 | 0 | 0 | 0 | **MEASURED zero** |

The `eq1024_vs` pathway produced the same firing pattern: only `HOLOS.YM.dairy` is non-zero (enteric-only; manure CH4 baseline is slightly different because VS is recomputed, so the total-CH4 percent is +7.800495 instead of +7.807898). VS TDN and UE forks remain **MEASURED zero** on Eq 10.24 because TDN was set equal to DE and EPA DE% (dairy 66.7, beef 62.5) is below ~80% while default forage is 100% (grain 0%), so both UE switches yield 0.04.

---

## `HOLOS.YM.dairy` (the only non-zero fork on this dataset)

Default = Canada lactating dairy Ym 5.6% GE. Alternative = IPCC 2006 Table 10.12 p. 10.30 dairy Ym 6.5% GE.

Algebra of Eq 10.21 on dairy GE only: 6.5/5.6 − 1 = **+16.0714% dairy enteric CH4**. Beef enteric does not change. The 17-county **total enteric** increase is **+14.683897%** because beef enteric dilutes the dairy-only ratio. Manure CH4 and all N2O are unchanged (**MEASURED** 0).

County total-CH4 percent (alt 6.5 minus default 5.6), `epa_vs`:

| State | County | Δ CH4 % | Δ CO2e % |
|-------|--------|---------|----------|
| VT | ADDISON | 8.033192 | 7.286694 |
| VT | FRANKLIN | 7.942020 | 7.110318 |
| VT | WASHINGTON | 7.905374 | 6.914640 |
| VT | ORLEANS | 7.895384 | 7.009960 |
| VT | WINDHAM | 7.835342 | 6.607695 |
| VT | ESSEX | 7.833216 | 6.422745 |
| VT | ORANGE | 7.782167 | 7.037538 |
| VT | GRAND ISLE | 7.777421 | 6.775426 |
| VT | CALEDONIA | 7.658862 | 6.720983 |
| VT | LAMOILLE | 7.475681 | 6.181153 |
| VT | CHITTENDEN | 7.334746 | 6.191033 |
| VT | BENNINGTON | 7.205641 | 6.057624 |
| VT | RUTLAND | 7.099642 | 5.930495 |
| VT | WINDSOR | 6.378890 | 5.174252 |
| DE | NEW CASTLE | 6.868593 | 1.159322 |
| DE | SUSSEX | 6.633055 | 0.309890 |
| DE | KENT | 6.500631 | 0.500201 |

AN_v1 estimated “14% reduction in dairy enteric CH4” and “~7% total enteric if 50% dairy.” The first is the dairy-only Eq 10.21 ratio (MEASURED 13.846% reduction of dairy enteric when using 5.6 vs 6.5, i.e. 1 − 5.6/6.5). The “50% dairy → ~7% total enteric” mix is **ESTIMATE** of a hypothetical farm; the 17-county measured total-enteric impact of the fork is +14.68% (alt vs default), and total CH4 (enteric+manure) is +7.81%.

Essex VT (AN_v1 worked example), `epa_vs` baseline: enteric 89,465 kg, manure 79,239 kg, total CH4 168,704 kg, N2O 3,914.5 kg, CO2e 5,761.1 t. Ym fork Δ CH4 = +13,215 kg (+7.833%), Δ CO2e = +370.0 t (+6.423%). AN_v1’s Essex “Holos bugs → +10–15% manure CH4; net +3–8% total CH4” combined sketch is **ESTIMATE** and is not this Ym-only measurement.

---

## Why seven forks are MEASURED zero (not ESTIMATE)

A measured zero means the code was run with the fork on and emissions did not change on this dataset. It does not prove the Holos discrepancy is zero on a farm that has calves, crusted tanks, independent TDN, high-grain diets, or NE-based GE.

| Fork | Why the 17-county run cannot move CH4/N2O/CO2e |
|------|-----------------------------------------------|
| `HOLOS.GE.digestibility` | `GE_MJ_day` override always present; Eq 10.3 TDN vs DE is skipped. No NE inputs. |
| `HOLOS.ENTERIC.calf_zero` (CE-06) | Mature cows only. |
| `HOLOS.VS.digestibility` | `epa_vs` uses EPA VS. `eq1024_vs` sets TDN = DE (TDN not observed). |
| `HOLOS.VS.urinary_energy` | `epa_vs` uses EPA VS. `eq1024_vs`: EPA DE% < 80 and default forage 100% → both UE = 0.04. Phase 2 also records that Holos grain% and IPCC DE% switches are the **same direction** (AN_v1 “UE reversal” sketch was inverted; see `docs/HOLOS_PHASE2_FORKS_AN_v1.md`). |
| `HOLOS.VS.calf_coeff` (CE-07) | Mature cows only. Coefficient 0.0093 remains **UNVERIFIED**. |
| `HOLOS.CH4.cover_reduction` (CE-14) | EPA mapping is `liquid_nocrust`; `cover_type=none`. Factors 0.4 / 0.25 remain **UNVERIFIED**. |
| `HOLOS.NEX.calf_nrate` | Mature cows only. 0.078 kg N/head/day remains **UNVERIFIED**. |

---

## Still ESTIMATE (not produced by the 17-county run)

These AN_v1 ranges are **not** replaced by measurements. They would require inputs the county files do not contain, which this phase does not invent.

| AN_v1 claim | Status |
|-------------|--------|
| TDN vs DE: typically 1–5% VS | **ESTIMATE** — no independent TDN |
| UE switch disagreement: ~5–10% VS | **ESTIMATE** on a high-grain or DE>~80% diet; **MEASURED zero** on EPA VT/DE DE% + default forage |
| Combined VS error 6–15%; manure CH4 8–20% | **ESTIMATE** |
| VS-based N / N2O 6–15% | **ESTIMATE** — this run uses EPA Nex, not VS-derived N |
| GE Eq 10.3 TDN vs DE 1–5% | **ESTIMATE** — GE override, no NE diet |
| Calf VS / enteric / Nrate county impact | **ESTIMATE** — no calf counts |
| Cover/crust 0.4 and 0.25 county impact | **ESTIMATE** — no crust/cover shares |
| Essex combined Holos-bug net +3–8% total CH4 | **ESTIMATE** |

---

## Urinary energy (carried from Phase 2)

AN_v1 finding 2 quoted IPCC 2006 Vol 4 Ch 10 p. 10.54 then described Holos as reversing 0.04/0.02. The quoted IPCC text is: typical UE = 0.04; exception UE = 0.02 when DE% is greater than approximately 80%. Holos (as audited) uses 0.02 when grain% ≥ 85. Same direction; different switch. Implemented default follows the IPCC quotation. On the 17-county EPA diets the two switches agree (**MEASURED**).

---

## Files

- This document: `docs/HOLOS_CODE_AUDIT_AN_v2.md`
- Prior equation audit (unchanged): `docs/HOLOS_CODE_AUDIT_AN_v1.md`
- Script: `scripts/measure_holos_forks_vt_de_AN_v1.py`
- Shared runner: `scripts/holos_vt_de_runner_AN_v1.py`
- CSVs listed above
