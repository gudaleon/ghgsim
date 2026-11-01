# Phase A: poultry and swine (AN_v1)

Adds IPCC 2006 / 2019 and Holos Route A enteric and manure emissions for
US categories that map to USDA Census of Agriculture and EPA GHGI Annex 3.11:

| ghgsim `animal_type` | USDA Census | EPA Annex 3.11 |
|---|---|---|
| broilers | Broilers and other meat-type chickens | Broilers |
| layers | Layers 20 weeks old and older | Layers |
| turkeys | Turkeys | Turkeys |
| market_swine | Hogs and pigs, other (market) | Market swine |
| breeding_swine | Hogs and pigs, breeding | Breeding swine |

## Equations (AQUASIM ProcessDefs)

- Poultry enteric: `0` (IPCC 2006/2019 Table 10.9 method Not developed; Table 10.10 Insufficient data).
- Swine enteric: Tier 1 `EF = 1.5 kg CH4 head-1 yr-1` developed / high-productivity (Table 10.10).
- Manure CH4: IPCC Eq 10.23 `VS × 365 × B0 × 0.67 × Σ(MCF × MS)`.
- Direct N2O: Eq 10.25 `Nex × EF3`.
- Indirect vol: Eq 10.26-10.27 `Nex × FracGasMS × EF4`.
- Indirect leach: Eq 10.28-10.29 with **2019 Table 10.22 FracLeachMS** (2006 has no default; omitted unless `include_leach`).
- Managed N remaining for soils: Eq 10.34 without bedding (`N_MMS_Avb_kg`). Ready for Phase B so applied manure is counted once.

Holos defaults are those IPCC equations. Confirmed Holos discrepancies are labelled `holos_as_coded`.

## New fork

`HOLOS.CH4.turkey_zero` (CE-10): Holos CLI never populates the turkey daily manure CH4 rate, so yearly CH4 is 0. `source_correct` uses Eq 10.23.

Measured on stylized `turkey_litter` (5,000 turkeys, poultry with litter, 15C):

| Quantity | source_correct | holos_as_coded | delta |
|---|---:|---:|---:|
| Manure CH4 (kg) | 462.1995 | 0 | −462.1995 |
| N2O (kg) | 72.155 | 72.155 | 0 |
| CO2e (t) | 32.063 | 19.121 | −12.942 (−40.363%) |

Hand check: `5000 × 0.07 × 365 × 0.36 × 0.67 × 0.015 = 462.1995` (Table 10A-9 VS/B0, Table 10.17 MCF 1.5%).

Other poultry/swine farms have no Holos-as-coded delta: Holos uses the same IPCC equations there.

## Stylized farm baselines (AR5 GWP)

| farm | enteric CH4 kg | manure CH4 kg | N2O kg | CO2e t |
|---|---:|---:|---:|---:|
| broiler_litter | 0 | 528.228 | 56.784 | 29.838 |
| layer_litter | 0 | 286.124 | 42.846 | 19.366 |
| layer_highrise | 0 | 286.124 | 55.700 | 22.772 |
| turkey_litter | 0 | 462.200 | 72.155 | 32.063 |
| market_swine_liquid | 1500 | 8557.294 | 53.191 | 295.700 |
| breeding_swine_liquid | 300 | 3169.368 | 26.166 | 104.076 |
| farrow_to_finish | 1800 | 11726.662 | 74.397 | 398.462 |

Head counts are ILLUSTRATIVE. TAM/VS/B0/Nrate/MCF/EF cells are VERIFIED IPCC table values.

## Versioned files (never overwrite)

- `data/ipcc_params_AN_v5.csv`
- `data/holos_params_canada_AN_v6.csv`
- `data/holos_forks_AN_v4.json`
- `data/coefficient_trace_AN_v5.csv`
- `data/stylized_farms_AN_v3.yaml`
- `data/holos_fork_deltas_stylized_AN_v3.csv`
- `docs/figures/fork_diagram_AN_v3.{mmd,json,svg,png}`
- `docs/figures/sankey_{broiler_litter,layer_litter,layer_highrise,turkey_litter,market_swine_liquid,breeding_swine_liquid,farrow_to_finish}_AN_v1.*`

## Sources opened this run

- 2006 IPCC Vol 4 Ch 10 PDF
- 2019 Refinement Vol 4 Ch 10 PDF

No GPL Holos source was copied. Holos file:line citations are traceability only. A Holos-Canada-specific swine/poultry table was not opened; those Holos aliases are SOURCE-TRACED to the IPCC cells.

## Phase B (separate PR)

Crops/soils: EF1, residues, PRP, indirect, liming CO2, urea CO2, and manure N from animal modules counted once via `N_MMS_Avb_kg`.
