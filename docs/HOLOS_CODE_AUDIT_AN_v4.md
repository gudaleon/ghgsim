# Holos Code Audit Against Primary Sources — cover-reduction bugfix

**Version:** AN_v4  
**Date:** 2026-11-01  
**Does not overwrite:** `docs/HOLOS_CODE_AUDIT_AN_v1.md`, `AN_v2.md`, or `AN_v3.md`  
**Branch:** `cursor/goal4-phase2-holos-forks-e537`

AN_v3 reported cover-fork cuts of **26–32% total CH4 / CO2e** on 100% liquid stylized farms. That finding is **retracted**. It came from treating Holos 0.40 / 0.25 as remaining-emission multipliers. Direct read of holos-aafc/Holos @036f862 shows they are **reduction** fractions: remaining = 1 − reduction (0.60 crust, 0.75 solid cover). This version re-measures after that fix.

---

## Retraction (AN_v3 cover finding)

AN_v3 (`docs/HOLOS_CODE_AUDIT_AN_v3.md` covered-liquid table) reported:

| Farm (AN_v3 id) | AN_v3 Δ CH4 % | AN_v3 Δ CO2e % | Why wrong |
|-----------------|--------------:|---------------:|-----------|
| dairy_forage_covered_crust | −26.828 | −25.872 | multiplied manure CH4 by 0.40 remaining |
| dairy_forage_covered_other | −33.536 | −32.340 | multiplied by 0.25 remaining; 0.25 applied as “other cover” |
| beef_cowcalf_covered_crust | −21.034 | −20.102 | same 0.40 remaining error |
| beef_cowcalf_covered_other | −26.293 | −25.128 | same 0.25 remaining error |

Holos @036f862:

- `AnimalResultsServiceBase.cs:967-972` sets `reductionFactor = 0.4` for `LiquidWithNaturalCrust`, else `0.25`.
- `AnimalResultsServiceBase.cs:1279-1283` returns `manureMethane * (1 - emissionReductionFactor)`.
- `ManureStateTypeExtensions.cs:53-56` `IsCoveredSystem()` is true only for `LiquidWithNaturalCrust` and `LiquidWithSolidCover`.
- Holos’s covered path does **not** use IPCC MCF (daily VS-consumed tank).

The fork difference versus `source_correct` is that Holos covered storage is an **MCF-free tank model**, approximated here as uncovered IPCC Table 10.17 MCF × (1 − reduction). It is **not** a reduction/retention mix-up. IPCC 2006 Table 10.17 p. 10.44 footnote already builds the ~40% crust reduction into with-crust MCF; stacking that MCF on the Holos remaining factor would double-count. This fork remaps `liquid_crust` → `liquid_nocrust` whenever the cover reduction applies.

0.25 applies to **solid cover only**, not to every non-crust cover type.

---

## How this was measured

**Commands:**

```bash
python3 scripts/measure_holos_forks_stylized_AN_v2.py
python3 scripts/measure_holos_forks_vt_de_AN_v2.py
```

**Inputs:** `data/stylized_farms_AN_v2.yaml` (does not overwrite AN_v1). Solid-cover farms replace AN_v1 `other_cover`.

**Outputs (new files; AN_v1 CSVs not overwritten):**

- `data/holos_fork_deltas_stylized_AN_v2.csv`
- `data/holos_fork_deltas_stylized_summary_AN_v2.csv`
- `data/holos_fork_deltas_stylized_AN_v2.meta.json`
- `data/holos_fork_deltas_vt_de_AN_v2.csv`
- `data/holos_fork_deltas_vt_de_summary_AN_v2.csv`
- `data/holos_fork_deltas_vt_de_AN_v2.meta.json`

**Registry:** `data/holos_forks_AN_v3.json` (AN_v2 already existed from Phase 2; never overwritten). Cover params: `data/holos_params_canada_AN_v5.csv` (`HOLOS.COVER.natural_crust_reduction` = 0.40 SOURCE-TRACED to the IPCC 2006 Table 10.17 40% footnote; `HOLOS.COVER.solid_cover_reduction` = 0.25 UNVERIFIED as a table cell).

**Runner:** same IPCC 2006 Eq 10.3 / 10.4 / 10.8 / 10.13 / 10.14 / 10.16 / 10.24 / 10.23 / 10.25–10.27 path as AN_v3; MCF = Table 10.17 15C; GWP AR5 CH4=28 N2O=265.

---

## Baseline (registered defaults), MEASURED

Unchanged from AN_v3. Covered farms still share the uncovered baseline because `source_correct` ignores `cover_type` and MCF stays liquid_nocrust 15C (0.27).

| Farm | CH4 enteric kg | CH4 manure kg | CH4 kg | N2O kg | CO2e t |
|------|----------------:|--------------:|-------:|-------:|-------:|
| dairy_forage_uncovered | 16,288.04 | 13,173.40 | 29,461.44 | 115.12 | 855.43 |
| dairy_high_grain_uncovered | 12,264.59 | 5,145.25 | 17,409.84 | 115.12 | 517.98 |
| beef_cowcalf_uncovered | 7,208.83 | 3,891.49 | 11,100.32 | 54.38 | 325.22 |

---

## MEASURED cover fork after the fix

Manure CH4 remaining vs uncovered `source_correct` base: **0.60 crust**, **0.75 solid cover**, **1.00 uncovered**. Locked by `tests/test_holos_manure_ch4.py` and `tests/test_holos_stylized_farms.py`.

| Farm | Δ CH4 kg | Δ CH4 % | Δ manure kg | Δ CO2e t | Δ CO2e % |
|------|----------:|--------:|------------:|---------:|---------:|
| dairy_forage_covered_crust | −5,269.36 | −17.886 | −5,269.36 | −147.54 | −17.248 |
| dairy_forage_covered_solid | −3,293.35 | −11.179 | −3,293.35 | −92.21 | −10.780 |
| dairy_high_grain_covered_crust | −2,058.10 | −11.821 | −2,058.10 | −57.63 | −11.125 |
| beef_cowcalf_covered_crust | −1,556.60 | −14.023 | −1,556.60 | −43.58 | −13.402 |
| beef_cowcalf_covered_solid | −972.87 | −8.764 | −972.87 | −27.24 | −8.376 |

On 100% liquid these percents equal reduction × (manure CH4 / total CH4). They are **not** 17-county crust shares. 17-county `HOLOS.CH4.cover_reduction` remains **MEASURED zero** (`cover_type=none`).

---

## Other single-fork deltas (unchanged from AN_v3)

Uncovered-farm non-cover forks were not affected by the cover-equation fix. AN_v3 MEASURED values stand for:

- Dairy forage uncovered: YM +8.885% CH4; GE TDN −2.357%; calf enteric −0.914%; VS TDN −1.895%; calf VS +0.438%; calf N +0.953% N2O; UE 0; cover 0; COMBINED **+4.057% CH4 / +3.946% CO2e**.
- Dairy high-grain uncovered: UE +3.031% CH4; VS TDN +6.820%; GE TDN +5.769%; YM +11.322%; COMBINED **+28.249% CH4 / +26.641% CO2e**.
- Beef cow-calf uncovered: calf enteric −12.440%; GE TDN −7.533%; VS TDN −4.363%; calf VS +3.953%; calf N +15.147% N2O; COMBINED **−18.531% CH4 / −17.039% CO2e**.

---

## COMBINED (all non-default options), MEASURED

Covered COMBINED rows change because cover remaining is now 0.60 / 0.75 instead of 0.40 / 0.25.

| Farm | Δ CH4 kg | Δ CH4 % | Δ enteric kg | Δ manure kg | Δ CO2e t | Δ CO2e % |
|------|----------:|--------:|-------------:|------------:|---------:|---------:|
| dairy_forage_uncovered | +1,195.19 | +4.057 | +1,882.07 | −686.88 | +33.76 | +3.946 |
| dairy_forage_covered_crust | −3,799.42 | −12.896 | +1,882.07 | −5,681.49 | −106.09 | −12.402 |
| dairy_forage_covered_solid | −1,926.44 | −6.539 | +1,882.07 | −3,808.51 | −53.65 | −6.272 |
| dairy_high_grain_uncovered | +4,918.09 | +28.249 | +2,557.90 | +2,360.19 | +138.00 | +26.641 |
| dairy_high_grain_covered_crust | +1,915.91 | +11.005 | +2,557.90 | −641.99 | +53.94 | +10.413 |
| beef_cowcalf_uncovered | −2,057.05 | −18.531 | −1,852.22 | −204.83 | −55.41 | −17.039 |
| beef_cowcalf_covered_crust | −3,531.71 | −31.816 | −1,852.22 | −1,679.50 | −96.70 | −29.735 |
| beef_cowcalf_covered_solid | −2,978.71 | −26.834 | −1,852.22 | −1,126.50 | −81.22 | −24.974 |

---

## 17-county VT/DE (AN_v2 re-run)

Same firing pattern as AN_v2/AN_v3: only `HOLOS.YM.dairy` is non-zero. `epa_vs` 17-county total: **+7.807898% CH4 / +5.300570% CO2e** (identical to the AN_v1 county run). Cover remains MEASURED zero.

---

## Scan of other forks (same error class)

Checked for reduction-vs-remaining, inverted sign, and unit mix-ups. Locked in `tests/test_holos_fork_sign_units.py`.

| Fork | Finding |
|------|---------|
| `HOLOS.CH4.cover_reduction` | **Fixed.** Was remaining 0.40/0.25; now reduction 0.40/0.25, remaining 0.60/0.75; 0.25 solid-cover only; no IPCC crust-MCF stack. |
| `HOLOS.GE.digestibility` | TDN vs DE in the Eq 10.3 denominator. Same algebraic position. Not a 1−x error. |
| `HOLOS.VS.digestibility` | Both paths use `(1 − digestibility/100)`. Sign correct. |
| `HOLOS.VS.urinary_energy` | High-digestibility / high-grain lowers UE to 0.02 (not 0.04). Not reversed. |
| `HOLOS.ENTERIC.calf_zero` | Hard zero for calves. Not a remaining fraction. |
| `HOLOS.VS.calf_coeff` | `0.0093 * weight` (kg VS / kg / day). Not a reduction. |
| `HOLOS.NEX.calf_nrate` | `0.078` kg N/head/day. Units already clarified; not a 1−x factor. |
| `HOLOS.YM.dairy` | 5.6% vs 6.5% of GE. Parameter value, not a remaining/reduction pair. |

No other fork in this class needed a code change.

---

## Files

- This document: `docs/HOLOS_CODE_AUDIT_AN_v4.md`
- Prior audits: `docs/HOLOS_CODE_AUDIT_AN_v1.md`, `AN_v2.md`, `AN_v3.md`
- Forks: `data/holos_forks_AN_v3.json` (AN_v1 and AN_v2 not overwritten)
- Canada params: `data/holos_params_canada_AN_v5.csv`
- Farms: `data/stylized_farms_AN_v2.yaml`
- Scripts and CSVs listed above
