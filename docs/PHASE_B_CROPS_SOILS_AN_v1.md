# Phase B: crops and soils (AN_v1)

Adds IPCC 2006 Vol 4 Chapter 11 soil N2O and lime/urea CO2, and links
managed manure N from the Phase A animal modules so excreted N is counted
once.

No new `holos_as_coded` fork. Holos crop/soil paths use the published IPCC
2006 equations. A Holos-Canada-specific lime/urea or Rochette EF1 table was
not opened; Holos aliases are SOURCE-TRACED to the IPCC cells.

## Equations (AQUASIM ProcessDefs)

| Process | Equation | Notes |
|---|---|---|
| Direct soil N2O-N | Eq 11.1 `(F_SN + F_ON + F_CR + F_SOM) × EF1 + F_PRP × EF3PRP` | Table 11.1: EF1 = 0.01; EF3PRP-CPP = 0.02 |
| Indirect vol | Eq 11.9 `(F_SN × FracGASF + (F_ON + F_PRP) × FracGASM) × EF4` | Table 11.3 |
| Indirect leach | Eq 11.10 `(F_SN + F_ON + F_CR + F_SOM + F_PRP) × FracLEACH × EF5` | FracLEACH wet = 0.30 |
| FAM | Eq 11.4 `N_MMS_Avb × (1 − FracFEED − FracFUEL − FracCNST)` | Fractions 0 when unused-manure data are absent (p. 11.13) |
| F_PRP | Eq 11.5 | Urine/dung on pasture; not applied manure |
| Lime CO2-C | Eq 11.12 | EF limestone 0.12; dolomite 0.13 t C / t lime; × 44/12 |
| Urea CO2-C | Eq 11.13 | EF 0.20 t C / t urea; × 44/12 |

Residue Eq 11.6 is not expanded (crop N contents were not opened). `F_CR` is
user-supplied and labelled ILLUSTRATIVE.

## Once-only manure N

`HolosManure` returns `N_MMS_Avb_kg` (Eq 10.34 without bedding).
`HolosFieldN` sets `FAM = N_MMS_Avb` (Eq 11.4) and `F_ON = FAM + other organic`.
Storage volatilisation is not added again as soil-applied N.

Broiler check (20,000 head, TAM 0.9 kg, Nrate 1.10, FracGasMS litter 0.40):

`Nex = 1.10 × 0.9 / 1000 × 365 = 0.36135 kg N head⁻¹ yr⁻¹`
`N_MMS_Avb = 20000 × 0.36135 × (1 − 0.40) = 4336.2 kg N`
`F_ON = 4336.2` (not 7227).

## Stylized farms (`data/stylized_farms_AN_v4.yaml`)

| farm | purpose | source_correct CO2e t |
|---|---|---:|
| broiler_litter_field | Linked FAM + ILLUSTRATIVE residues | 56.590 |
| market_swine_field | Linked FAM + ILLUSTRATIVE F_SN and residues | 320.984 |
| beef_pasture_field | 100% PRP; isolates EF3PRP | 295.270 |
| crop_urea_lime | Empty herd; EF1 + Eq 11.12/11.13 | 9.138 |
| turkey_litter | Unchanged, no field (CE-10 isolation) | 32.063 |

Field-linked soil N2O (not in the animal-only twin):

| farm | soil N2O kg | lime+urea CO2 kg | vs animal-only twin ΔCO2e t |
|---|---:|---:|---:|
| broiler_litter_field | 100.950 | 0 | +26.752 vs broiler_litter |
| market_swine_field | 95.411 | 0 | +25.284 vs market_swine_liquid |
| crop_urea_lime | 26.596 | 2090.000 | n/a (no animal twin) |

Hand checks: lime `2×0.12 + 1×0.13` t C × 1000 × 44/12 = 1356.667 kg CO2; urea `1×0.20` × 1000 × 44/12 = 733.333 kg CO2. Broiler FAM = 4336.2 kg N (not raw Nex 7227).

Head counts, F_SN, F_CR, F_SOM, and lime/urea tonnes that are not published
cells are ILLUSTRATIVE. EF/Frac/lime/urea cells are VERIFIED from the opened
Chapter 11 PDF.

## New forks and measured deltas

None. Phase B adds no Holos-as-coded crop/soil fork. The turkey CE-10 delta
from Phase A is unchanged because `turkey_litter` has no field.

## Versioned files (never overwrite)

- `data/ipcc_params_AN_v6.csv`
- `data/holos_params_canada_AN_v7.csv`
- `data/coefficient_trace_AN_v6.csv`
- `data/stylized_farms_AN_v4.yaml`
- `docs/figures/sankey_{broiler_litter_field,market_swine_field,beef_pasture_field,crop_urea_lime}_AN_v1.*`

## Sources opened this run

- 2006 IPCC Vol 4 Ch 11 PDF
  (https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf)

No GPL Holos source was copied.
