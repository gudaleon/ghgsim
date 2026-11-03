# Holos Code Audit Against Primary Sources — measured stylized-farm fork impacts

**Version:** AN_v3  
**Date:** 2026-11-01  
**Does not overwrite:** `docs/HOLOS_CODE_AUDIT_AN_v1.md` (equation findings) or `docs/HOLOS_CODE_AUDIT_AN_v2.md` (17-county measurements)  
**Branch:** `cursor/goal4-phase2-holos-forks-e537`

AN_v2 left seven registered forks as **MEASURED zero** on the 17-county mature-cow EPA dataset. This version runs those forks on stylized farms built to supply the missing inputs (calves, heifers, independent TDN and DE, high-grain UE disagreement, covered liquid). Values replace AN_v1/AN_v2 **ESTIMATE** rows where this run produced a number. Anything still not produced by running the modules is labelled **ESTIMATE**.

---

## How this was measured

**Command (also stored as the `command` column in the CSVs):**

```bash
python3 scripts/measure_holos_forks_stylized_AN_v1.py
```

**Inputs:** `data/stylized_farms_AN_v1.yaml`

**Outputs:**

- `data/holos_fork_deltas_stylized_AN_v1.csv` — 8 farms × (baseline + 8 single forks + combined)
- `data/holos_fork_deltas_stylized_summary_AN_v1.csv`
- `data/holos_fork_deltas_stylized_AN_v1.meta.json`

**Runner:** IPCC 2006 Eq 10.3 / 10.4 / 10.8 / 10.13 / 10.14 / 10.16 for NE and GE (no `GE_MJ_day` override); Eq 10.24 VS; Eq 10.23 / 10.25–10.27 manure; MCF = Table 10.17 15C; GWP AR5 CH4=28 N2O=265. Each fork is toggled alone, then all non-default options together (`COMBINED`).

**Farms (head counts ILLUSTRATIVE; diet TDN/DE pairings labelled ILLUSTRATIVE in the YAML):**

| Farm id | Animals | Diet | Liquid cover |
|---------|---------|------|--------------|
| `dairy_forage_uncovered` | 100 cows, 40 heifers, 20 calves | EPA A-139 DE 66.7 + NRC 2001 Table 14-3 TDN 68 | none |
| `dairy_forage_covered_crust` | same | same | `natural_crust` (Holos factor 0.4, UNVERIFIED) |
| `dairy_forage_covered_other` | same | same | `other_cover` (Holos factor 0.25, UNVERIFIED) |
| `dairy_high_grain_uncovered` | same | EPA A-139 feedlot DE 82.5 + NRC 2001 Table 14-4 TDN 78 / forage 48% | none |
| `dairy_high_grain_covered_crust` | same | same high-grain | `natural_crust` |
| `beef_cowcalf_uncovered` | 100 cows, 90 calves | EPA A-138 NE DE 62.5 + NRC 2001 Table 14-3 TDN 68 | none |
| `beef_cowcalf_covered_crust` | same | same | `natural_crust` |
| `beef_cowcalf_covered_other` | same | same | `other_cover` |

Masses: EPA 2025 Annex 3.11 Table A-128 year 2022 (cows 1,499 lb, dairy replacements 899 lb, calves 271 lb, beef cows 1,347 lb). Milk: Table A-132 Vermont 21,644 lb/cow/yr. Cow Nex: Table A-156 VT 153 / 74 kg N/yr. Heifer and calf Nex: IPCC 2006 Eq 10.30 with Table 10.19 North America Nrate (0.44 dairy / 0.31 other cattle) and A-128 mass. ASH = 8% (Eq 10.24 example). Dairy Ym default 5.6% (UNVERIFIED point value); beef Ym 6.5% (EPA Table A-138 Northeast).

The 17-county **MEASURED zeros** in AN_v2 remain true of that dataset. They are not estimates. This file adds a second measured dataset.

---

## Baseline (registered defaults), MEASURED

| Farm | CH4 enteric kg | CH4 manure kg | CH4 kg | N2O kg | CO2e t |
|------|----------------:|--------------:|-------:|-------:|-------:|
| dairy_forage_uncovered | 16,288.04 | 13,173.40 | 29,461.44 | 115.12 | 855.43 |
| dairy_high_grain_uncovered | 12,264.59 | 5,145.25 | 17,409.84 | 115.12 | 517.98 |
| beef_cowcalf_uncovered | 7,208.83 | 3,891.49 | 11,100.32 | 54.38 | 325.22 |

Covered farms share the uncovered baseline because `source_correct` ignores `cover_type` and MCF stays Table 10.17 liquid_nocrust 15C (0.27).

---

## MEASURED single-fork deltas (alt minus default)

Every registered fork fired on at least one farm.

### Dairy forage, uncovered liquid (100 cows / 40 heifers / 20 calves)

| Fork | Fired? | Δ CH4 kg | Δ CH4 % | Δ enteric kg | Δ manure kg | Δ N2O kg | Δ N2O % | Δ CO2e t | Δ CO2e % |
|------|--------|----------:|--------:|-------------:|------------:|---------:|--------:|---------:|---------:|
| `HOLOS.YM.dairy` | yes | +2,617.72 | +8.885 | +2,617.72 | 0 | 0 | 0 | +73.30 | +8.568 |
| `HOLOS.GE.digestibility` | yes | −694.40 | −2.357 | −381.64 | −312.76 | 0 | 0 | −19.44 | −2.273 |
| `HOLOS.ENTERIC.calf_zero` | yes | −269.17 | −0.914 | −269.17 | 0 | 0 | 0 | −7.54 | −0.881 |
| `HOLOS.VS.digestibility` | yes | −558.32 | −1.895 | 0 | −558.32 | 0 | 0 | −15.63 | −1.828 |
| `HOLOS.VS.urinary_energy` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `HOLOS.VS.calf_coeff` | yes | +128.95 | +0.438 | 0 | +128.95 | 0 | 0 | +3.61 | +0.422 |
| `HOLOS.CH4.cover_reduction` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `HOLOS.NEX.calf_nrate` | yes | 0 | 0 | 0 | 0 | +1.10 | +0.953 | +0.29 | +0.034 |
| `COMBINED` | yes | +1,195.19 | +4.057 | +1,882.07 | −686.88 | +1.10 | +0.953 | +33.76 | +3.946 |

VS TDN vs DE on this pairing: **MEASURED −4.238% VS** (and the same percent manure CH4). GE TDN vs DE: **MEASURED −2.343% GE**.

UE is **MEASURED zero** here because DE 66.7 < 80 and grain 33% < 85, so both switches stay at 0.04. That is the same agreement AN_v2 measured on EPA VT/DE diets.

### Dairy high-grain, uncovered (UE switches disagree)

DE 82.5 ≥ 80 → implemented IPCC UE = 0.02. Grain 52% < 85 → Holos UE = 0.04.

| Fork | Fired? | Δ CH4 kg | Δ CH4 % | Δ enteric kg | Δ manure kg | Δ N2O kg | Δ CO2e t | Δ CO2e % |
|------|--------|----------:|--------:|-------------:|------------:|---------:|---------:|---------:|
| `HOLOS.VS.urinary_energy` | yes | +527.72 | +3.031 | 0 | +527.72 | 0 | +14.78 | +2.853 |
| `HOLOS.VS.digestibility` | yes | +1,187.36 | +6.820 | 0 | +1,187.36 | 0 | +33.25 | +6.418 |
| `HOLOS.GE.digestibility` | yes | +1,004.41 | +5.769 | +707.57 | +296.84 | 0 | +28.12 | +5.429 |
| `HOLOS.YM.dairy` | yes | +1,971.10 | +11.322 | +1,971.10 | 0 | 0 | +55.19 | +10.655 |
| `HOLOS.ENTERIC.calf_zero` | yes | −191.00 | −1.097 | −191.00 | 0 | 0 | −5.35 | −1.032 |
| `HOLOS.VS.calf_coeff` | yes | +282.19 | +1.621 | 0 | +282.19 | 0 | +7.90 | +1.525 |
| `HOLOS.NEX.calf_nrate` | yes | 0 | 0 | 0 | 0 | +1.10 | +0.29 | +0.056 |
| `COMBINED` | yes | +4,918.09 | +28.249 | +2,557.90 | +2,360.19 | +1.10 | +138.00 | +26.641 |

UE Holos-as-coded vs IPCC-as-implemented: **MEASURED +10.256% VS** and **+10.256% manure CH4**. VS TDN vs DE (78 vs 82.5): **MEASURED +23.077% VS**. GE TDN vs DE: **MEASURED +5.769% GE**.

### Covered liquid (CE-14), same herds as the uncovered twin

Default MCF is still liquid_nocrust 15C. The fork multiplies manure CH4 by 0.4 (`natural_crust`) or 0.25 (`other_cover`). Coefficients remain **UNVERIFIED**; the emission deltas are **MEASURED**.

| Farm | Δ CH4 kg | Δ CH4 % | Δ manure kg | Δ CO2e t | Δ CO2e % |
|------|----------:|--------:|------------:|---------:|---------:|
| dairy_forage_covered_crust | −7,904.04 | −26.828 | −7,904.04 | −221.31 | −25.872 |
| dairy_forage_covered_other | −9,880.05 | −33.536 | −9,880.05 | −276.64 | −32.340 |
| beef_cowcalf_covered_crust | −2,334.89 | −21.034 | −2,334.89 | −65.38 | −20.102 |
| beef_cowcalf_covered_other | −2,918.62 | −26.293 | −2,918.62 | −81.72 | −25.128 |

On 100% liquid these percents equal (1 − factor) × (manure CH4 / total CH4). They are not 17-county crust shares.

### Beef cow-calf, uncovered liquid (100 cows / 90 calves)

| Fork | Fired? | Δ CH4 kg | Δ CH4 % | Δ enteric kg | Δ manure kg | Δ N2O kg | Δ N2O % | Δ CO2e t | Δ CO2e % |
|------|--------|----------:|--------:|-------------:|------------:|---------:|--------:|---------:|---------:|
| `HOLOS.ENTERIC.calf_zero` | yes | −1,380.83 | −12.440 | −1,380.83 | 0 | 0 | 0 | −38.66 | −11.888 |
| `HOLOS.GE.digestibility` | yes | −836.15 | −7.533 | −542.45 | −293.69 | 0 | 0 | −23.41 | −7.199 |
| `HOLOS.VS.digestibility` | yes | −484.29 | −4.363 | 0 | −484.29 | 0 | 0 | −13.56 | −4.169 |
| `HOLOS.VS.calf_coeff` | yes | +438.80 | +3.953 | 0 | +438.80 | 0 | 0 | +12.29 | +3.778 |
| `HOLOS.NEX.calf_nrate` | yes | 0 | 0 | 0 | 0 | +8.24 | +15.147 | +2.18 | +0.671 |
| `HOLOS.VS.urinary_energy` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `HOLOS.YM.dairy` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `HOLOS.CH4.cover_reduction` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `COMBINED` | yes | −2,057.05 | −18.531 | −1,852.22 | −204.83 | +8.24 | +15.147 | −55.41 | −17.039 |

VS TDN vs DE (68 vs 62.5): **MEASURED −12.445% VS**. `HOLOS.YM.dairy` is **MEASURED zero** on beef (dairy-only parameter). Calf enteric is a larger share of this farm than of the dairy forage farm because the stylized calf:cow ratio is 90:100.

---

## AN_v1 / AN_v2 estimates replaced by MEASURED values

| AN_v1 / AN_v2 claim | Status after this run |
|---------------------|------------------------|
| TDN vs DE: typically 1–5% VS | **MEASURED** on these pairings: dairy forage −4.238% VS; beef forage −12.445% VS; high-grain +23.077% VS. The “typically 1–5%” range is **not** a measured universal band. |
| UE switch disagreement: ~5–10% VS | **MEASURED +10.256% VS** and **+3.031% total CH4** on `dairy_high_grain_uncovered`. **MEASURED zero** on forage diets (both switches 0.04), matching AN_v2. |
| Combined VS error 6–15%; manure CH4 8–20% | **Replaced** by farm-specific MEASURED rows above (not a single range). Dairy-forage combined manure CH4 −686.88 kg (−5.21% of that farm’s manure CH4). High-grain combined manure CH4 +2,360.19 kg (+45.87% of that farm’s manure CH4) because UE, TDN, and calf VS all raise VS. |
| GE Eq 10.3 TDN vs DE 1–5% | **MEASURED −2.343% GE** (dairy forage) and **+5.769% GE** (high-grain). |
| Calf enteric / VS / Nrate impact | **MEASURED** on these ILLUSTRATIVE head counts (tables above). 17-county calf impact remains unmeasured (no calf counts in the county files). |
| Cover/crust 0.4 and 0.25 county impact | **MEASURED** on 100% liquid stylized farms (tables above). 17-county crust-share impact remains unmeasured. Factors themselves stay **UNVERIFIED**. |
| Essex combined Holos-bug net +3–8% total CH4 | Still **ESTIMATE** for Essex. Stylized dairy-forage uncovered **COMBINED** is **MEASURED +4.057% CH4 / +3.946% CO2e**. That is not Essex. |

AN_v2 17-county `HOLOS.YM.dairy` figures are unchanged and still **MEASURED** on that dataset (+14.68% enteric, +7.81% total CH4, +5.30% CO2e, `epa_vs`).

---

## Still ESTIMATE (not produced by this run or the 17-county run)

| Claim | Why it stays ESTIMATE |
|-------|------------------------|
| 17-county totals for the seven forks that were zero in AN_v2 | County files still have no calves, independent TDN, NE diet, high-grain grain%, or crust/cover shares. AN_v2 zeros on that dataset stand. |
| Essex VT combined Holos-bug net +3–8% total CH4 | Essex was not re-run with invented calves/TDN/cover. |
| VS-derived N and the AN_v1 “N2O 6–15%” sketch | This run uses EPA / Eq 10.30 Nex, not VS-derived N. N2O moved only via `HOLOS.NEX.calf_nrate`. |
| “Typically 1–5% VS” as a general TDN–DE rule | Only three constructed pairings were measured. |
| Canada-only adult GE/VS farm (no EPA GE override) | Not assembled. |
| ECCC dairy Ym 5.6% as a table cell | Still **UNVERIFIED** (`docs/HOLOS_ECCC_YM_AN_v1.md`). |
| Holos calf VS 0.0093, calf N 0.078, cover 0.4 / 0.25 | Coefficients remain **UNVERIFIED**. Emission deltas that use them are MEASURED. |

---

## Urinary energy (carried from Phase 2, now measured on a crossing diet)

Implemented `source_correct` UE is 0.02 when `DE_percent >= 80`, else 0.04. Holos-as-coded is 0.02 when grain% ≥ 85, else 0.04. The IPCC 2006 PDF opened this run (Eq 10.24 notes) also mentions 85% or more grain; the registered default was not rewritten. The high-grain farm uses EPA Table A-139 feedlot DE 82.5 with the NRC 2001 Table 14-4 forage/grain split (48/52) so the two implemented switches disagree. IPCC 2006 Table 10.2 “>90% concentrate” was not used, because both switches would then be 0.02.

---

## Files

- This document: `docs/HOLOS_CODE_AUDIT_AN_v3.md`
- Prior: `docs/HOLOS_CODE_AUDIT_AN_v1.md`, `docs/HOLOS_CODE_AUDIT_AN_v2.md`
- Farms: `data/stylized_farms_AN_v1.yaml`
- Script: `scripts/measure_holos_forks_stylized_AN_v1.py`
- CSVs listed above
