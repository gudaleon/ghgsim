# Holos Route A — four-way VT/DE comparison

**Version:** AN_v2  
**Date:** 2026-11-01  
**Does not overwrite:** `docs/HOLOS_ROUTE_A_AN_v1.md` (Phase 1 implementation narrative)  
**Branch:** `cursor/goal4-phase2-holos-forks-e537`

AN_v1 left the numerical comparison blocked. This version runs IPCC 2006, IPCC 2019, Holos Canada defaults, and Holos US inputs on the same 17 Vermont and Delaware counties. No activity data were invented.

---

## Reproducible command

```bash
python3 scripts/compare_holos_fourway_vt_de_AN_v1.py
```

**Outputs:**

- `data/holos_fourway_vt_de_AN_v1.csv`
- `data/holos_fourway_vt_de_summary_AN_v1.csv`
- `data/holos_fourway_vt_de_AN_v1.meta.json`

Shared farm builder: `scripts/holos_vt_de_runner_AN_v1.py`  
GWP: AR5 CH4 = 28, N2O = 265  
Counties: 14 VT + 3 DE from `legacy/livingghg_AN_v3/results_TRIAL_AN_v3/counties_{VT,DE}_AN_v3.csv`  
Animal characteristics: `legacy/livingghg_AN_v3/scripts/county_assumptions_AN_v3.json` (EPA 2025 Annex 3.11; mature cows only)

---

## What each column is

| Method | Code path | Ym dairy | Ym beef | VS / Nex / GE / systems | MCF / B0 | Evidence |
|--------|-----------|----------|---------|-------------------------|----------|----------|
| IPCC 2006 | ghgsim v4 `IPCC2006Enteric` + `IPCC2006Manure` + `IPCC2006SoilN2O` | EPA state (VT 5.7, DE 5.7) | EPA 6.5 | EPA JSON | IPCC 2006 Table 10.17 15C; B0 dairy 0.24 Table 10A-4, other cattle 0.19 Table 10A-5 | **MEASURED** |
| IPCC 2019 | livingghg v3 `run_farm(..., "IPCC2019")` | EPA state (v3 default `ym_source=epa_state`) | EPA 6.5 | EPA JSON | IPCC 2019 Table 10.17 (Updated); liquid as 6-month | **MEASURED** |
| Holos Canada | `HolosEnteric` + `HolosManure` + `HolosSoilN2O`, fork defaults | 5.6 (`HOLOS.Ym.dairy_lactating\|canada`) | 6.3 (`HOLOS.Ym.beef_backgrounder\|canada`) | EPA JSON GE/VS/Nex/systems (**hybrid**) | Canada MCF (temperate, cool fallback); B0 dairy 0.24, beef 0.17 | **MEASURED** hybrid |
| Holos US | same Holos modules | EPA state Ym | EPA 6.5 | EPA JSON | Holos US MCF overlay (pasture 0.02 SOURCE-TRACED; daily spread 0.005; lagoon 0.74); B0 beef 0.17 SOURCE-TRACED | **MEASURED** |

**Holos Canada hybrid (not invented GE):** `data/holos_params_canada_AN_v3.csv` has no adult dairy/beef GE or VS. This comparison therefore applies Canada Ym, B0, and MCF to the US county activity already used for IPCC 2006/2019. That is documented, not a Canada farm survey.

**Holos US file vs EPA JSON:** `data/holos_params_us_AN_v2.csv` DE dairy GE 382.9 MJ/day and Ym 5.8 disagree with `county_assumptions_AN_v3.json` DE dairy GE 358.4 and Ym 5.7 (JSON GE is EF×55.65/(Ym×365) from the annex). This run uses the JSON, which is the exact-reproduction farm assembly.

**IPCC 2019 manure:** ghgsim v4 has no 2019 manure module. The 2019 column is livingghg v3, which reproduces the committed county CSV CO2e to 0 relative difference on these 17 rows. IPCC 2006 v4 matches the committed CSV CO2e to 1.45e-14 relative.

IPCC 2006 here is **not** Table 10.12 dairy Ym 6.5%; it is the EPA-state Ym used in Goals 1–3.

---

## 17-county sums (MEASURED)

| Method | CH4 kg | N2O kg | CO2e t | vs IPCC 2006 CH4 | vs IPCC 2006 N2O | vs IPCC 2006 CO2e |
|--------|--------|--------|--------|------------------|------------------|-------------------|
| IPCC 2006 | 32,972,420 | 1,633,539 | 1,356,115 | — | — | — |
| IPCC 2019 | 29,752,070 | 1,717,773 | 1,288,268 | **−9.766799%** | **+5.156552%** | **−5.003092%** |
| Holos Canada | 32,637,340 | 1,633,539 | 1,346,733 | **−1.016246%** | **0%** | **−0.691848%** |
| Holos US | 33,020,480 | 1,633,539 | 1,357,461 | **+0.145762%** | **0%** | **+0.099233%** |

Holos vs IPCC 2006 N2O is identically zero because both use EPA Nex, the same IPCC 2006 EF3/FracGasMS/soil factors, and the same soil N inputs. The CH4 gaps are Ym and manure CH4 (B0 × MCF), not N2O.

County CO2e vs IPCC 2006:

- IPCC 2019: mean −4.18%, max abs 8.31% (New Castle DE, where 2019 N2O increase outweighs CH4 decrease)
- Holos Canada: mean −0.79%, max abs 1.17%
- Holos US: mean +0.12%, max abs 0.19%

Essex VT (dairy-heavy, AN_v1 example):

| Method | CH4 kg | N2O kg | CO2e t |
|--------|--------|--------|--------|
| IPCC 2006 | 170,198.176 | 3,914.539 | 5,802.902 |
| IPCC 2019 | 153,535.697 | 5,130.285 | 5,658.525 |
| Holos Canada | 168,481.222 | 3,914.539 | 5,754.827 |
| Holos US | 170,444.180 | 3,914.539 | 5,809.790 |

---

## Why Holos Canada and Holos US differ from IPCC 2006 (MEASURED, not estimated)

**Holos Canada, −1.02% CH4:**

- Dairy Ym 5.6 vs EPA 5.7 (VT and DE JSON)
- Beef Ym 6.3 vs EPA 6.5
- Beef B0 0.17 (SOURCE-TRACED) vs IPCC other cattle 0.19 (Table 10A-5)
- Daily-spread MCF falls back to Holos Canada cool 0.001 vs IPCC 15C 0.005
- Pasture MCF Canada cool 0.015 equals IPCC 15C pasture 0.015

**Holos US, +0.15% CH4:**

- Enteric uses the same EPA Ym as IPCC 2006, so enteric matches that path
- Pasture MCF 0.02 (SOURCE-TRACED; IPCC 15C is 0.015)
- Beef B0 0.17 vs 0.19
- Beef in this dataset is 100% pasture, so manure CH4 scales with B0 × MCF_pasture

---

## Not in this comparison (ESTIMATE / not run)

- A Canada-only GE/VS farm. Adult GE and VS are absent from `holos_params_canada_AN_v3.csv` and were not invented.
- Independent TDN, forage%, calves, or crusted covers (see `docs/HOLOS_CODE_AUDIT_AN_v2.md`).
- `holos_params_us_AN_v2.csv` DE GE/Ym values that disagree with the EPA JSON.

---

## Implementation pointer

Clean-room Holos modules (IPCC 2006 defaults, `holos_as_coded` forks) live in `src/ghgsim/modules/holos/`. Phase 2 fork list: `docs/HOLOS_PHASE2_FORKS_AN_v1.md`. License: Apache-2.0; `python3 scripts/check_licenses.py`.
