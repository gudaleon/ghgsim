# Phase B follow-up (AN_v1)

Four follow-ups on PR #15 / #16. This document is the Phase B (#16) record.
Phase A turkey CE-10 isolation is unchanged (`turkey_litter` stays field-free).

## 1. Fork diagram and Sankey

Newest figures are `docs/figures/fork_diagram_AN_v4` and per-farm
`sankey_<farm>_AN_vN` (new version; never overwritten).

The process Sankey now routes managed manure N as
`animal → field.applied_manure → process.soil_n2o` (kg CO2e of the F_ON
share of soil N2O). Pasture urine/dung uses `field.prp`. Synthetic N,
residues, and SOM are separate sources. The field node is an intermediate
(inflow = outflow).

Poultry and swine farms from Phase A remain on the diagram. Crop/soil
processes appear on the field farms.

## 2. IPCC 2019 residue Eq 11.6

Opened: 2019 Refinement Vol 4 Ch 11 Table 11.1a (New) p. 11.18.

`F_CR` is no longer a user-supplied ILLUSTRATIVE N mass. Coefficients are
VERIFIED Table 11.1a cells. Area and fresh yield may still be ILLUSTRATIVE;
`F_CR` is then DERIVED.

Maize 10 ha × 8000 kg fresh ha⁻¹:

`Crop = 6960`; `AGDM = 6960`; `AGR = 69600`; `BGR = 30624`; `F_CR = 631.968 kg N`.

NASS `WHEAT` uses Winter Wheat cells (`RS = 0.23`). Spring Wheat `RS = 0.28`
is stored but not applied to the NASS wheat column. Bushel masses are
56 lb (corn) / 60 lb (soy, wheat) × NIST 0.45359237; AH-697 was not
re-opened (SOURCE-TRACED).

## 3. Rochette 2008 EF1 fork

Opened: Rochette et al. (2008) *Can. J. Soil Sci.* 88:641–654,
DOI 10.4141/cjss07025. Holos docs cite SSSAJ DOI 10.2136/sssaj2007.0351;
that URL 404s.

Rochette `EFeco = 0.022 × (P/PE) − 0.0048`, clamped to [0.0016, 0.017].
At `P/PE = 1` (published humid clamp, not a VT weather observation)
`EFeco = 0.017`. RFtext (east fine 1.2 / medium 0.8 / coarse 0.8) and
lower-landscape `P/PE = 1` are applied only when the caller supplies them.
No county texture or topography map is invented.

`HOLOS.N2O.ef1`:

- `source_correct` = Rochette EFeco when `P_PE` is supplied
- `holos_as_coded` = IPCC 2006 Table 11.1 EF1 = 0.01 (what ghgsim HolosSoilN2O coded)

Holos C# / V4 algorithm soil N2O section was **not** opened
(`UNVERIFIED` as Holos-engine behaviour). Rochette numbers themselves are
VERIFIED from the opened CJSS PDF.

Rochette `Frac_leach = 0.3247 × (P/PE) − 0.0247` at `P/PE = 1` equals IPCC
0.30, so there is no measured leach delta without a county `P/PE`.

## 4. VT/DE county run

Script: `scripts/holos_vt_de_poultry_crops_AN_v1.py`.

Census gap: `nass_census2022_county_AN_v1.csv.gz` has cattle inventory only.
No poultry or swine heads are in the repo extract; none are invented.

Poultry/swine enter as Falcone 2021 excreted N (`Hogs_N_kg-2017`,
`Poultry_N_kg-2017`) as `F_ON_other`. That is excreted N, not `N_MMS_Avb`.

Crops enter as NASS 2022 acres + bushels through Eq 11.6.

Cattle leftover managed manure N is linked once as FAM.

See `data/holos_vt_de_poultry_crops_summary_AN_v1.csv` for the change in
county totals versus the current Holos VT/DE trial-soil baseline.

## Versioned files (never overwrite)

- `data/ipcc_params_AN_v7.csv`
- `data/holos_params_canada_AN_v8.csv`
- `data/holos_forks_AN_v5.json`
- `data/coefficient_trace_AN_v7.csv`
- `data/stylized_farms_AN_v5.yaml`
- `data/holos_fork_deltas_stylized_AN_v4.csv`
- `data/holos_vt_de_poultry_crops_AN_v1.csv`
- `docs/figures/fork_diagram_AN_v4.*`
- new `docs/figures/sankey_*_AN_vN.*`

No GPL Holos source was copied.
