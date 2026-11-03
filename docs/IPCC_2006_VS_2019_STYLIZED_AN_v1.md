# IPCC 2006 vs 2019 Refinement on the stylized farms (AN_v1)

- Script: `scripts/compare_ipcc_2006_2019_stylized_AN_v1.py`
- Results: `data/ipcc_2006_vs_2019_stylized_AN_v1.csv` (19 farms x 4 sources, kg gas and t CO2e, AR5 GWP100 from the spec)
- Figure: `docs/figures/ipcc_2006_vs_2019_stylized_AN_v1.png` (script `scripts/plot_ipcc_2006_vs_2019_stylized_AN_v1.py`)
- Test: `tests/test_ipcc_2006_vs_2019_stylized_AN_v1.py` (CSV reproduces exactly; direction checks)
- Inputs: `data/stylized_farms_AN_v6.yaml`, latest `data/ipcc_params_AN_v*.csv` (v7 at time of run), `allow_unverified=False`.

## Scope
Only ghgsim IPCC modules run: `ipcc2006.enteric/manure/soil_n2o` and `ipcc2019.enteric/manure/soil_n2o/crop_residue`.
No Holos parameters, Holos forks, or Holos MS2 data. Activity data are shared so only the method differs.

## Activity data (same for both versions)
- Cattle GE: IPCC 2006 Eq 10.16 from Eq 10.3/10.4/10.8/10.13 NE terms and REM Eq 10.14 (spec mass, milk, DE).
- Cattle VS: Eq 10.24, ASH 8%, UE 0.04 (0.02 if DE >= 80%, the repo's registered IPCC switch).
- Nex: EPA override where the spec has one (dairy cow 153, beef cow 74 kg N/yr); otherwise each module's own Nrate x TAM.
- Monogastric VS: spec `VS_kg_day`. Enteric: each version's Tier 1 EF.
- Soil: spec F_SN, F_SOM; F_CR from `ipcc2019.crop_residue` (Table 11.1a) for BOTH versions, because ghgsim has no 2006 Table 11.2 residue module. F_ON = manure N left after MMS losses from each version's own manure run (2019: module `N_MMS_Avb_kg`; 2006: managed N minus N2O-N direct and volatilised N backed out with EF4). F_PRP = each version's `N_PRP_kg`.
- MCF zone 15C; region north_america; field climate as in spec (wet).

## Ym mapping (assumption, needs Alex sign-off)
- 2006 Table 10.12: dairy 6.5, other cattle 6.5.
- 2019 Table 10.12 (Updated): lactating dairy with milk > 8,500 kg/yr (VT 21,644 lb = 9,818 kg) is high-producing. NDF is not in the spec, so forage share is the proxy: forage >= 50% -> `dairy_high_ndf_ge35` (6.0), else `dairy_high_ndf_le35` (5.7). Heifers, calves, beef: forage > 75% -> `nondairy_forage_gt75`, else `nondairy_mixed` (6.3).

## Headline (t CO2e/yr, 2019 vs 2006)
| Farm | 2006 | 2019 | % |
|---|---|---|---|
| dairy_forage (all covers) | 928.7 | 890.4 | -4.1 |
| dairy_high_grain (all covers) | 573.2 | 527.5 | -8.0 |
| beef_cowcalf (all covers, manure N2O missing) | 323.6 | 317.4 | -1.9 |
| broiler_litter | 29.8 | 36.5 | +22.5 |
| layer_litter / layer_highrise | 19.4 / 22.8 | 23.5 / 28.1 | +21.2 / +23.4 |
| turkey_litter | 32.1 | 32.1 | 0.0 |
| market_swine_liquid / breeding / farrow_to_finish | 295.7 / 104.1 / 398.5 | 297.0 / 104.1 / 399.7 | +0.5 / 0.0 / +0.3 |
| broiler_litter_field | 56.5 | 67.4 | +19.4 |
| market_swine_field | 320.8 | 321.0 | +0.1 |
| beef_pasture_field | 296.0 | 244.1 | -17.5 |
| crop_urea_lime | 9.3 | 11.0 | +19.3 |

By source:
- Enteric CH4: dairy -7.2% (forage) and -11.5% (high grain), beef -3.1% (Ym only). Monogastric unchanged.
- Manure CH4: 0% everywhere. ghgsim `ipcc2019.manure` keeps 2006 MCF, cattle B0, EF3 and cattle FracGasMS; the 2019 swine NA B0 (0.48) equals 2006. 2019 liquid MCFs by storage time and climate (e.g. `IPCC2019.MCF.liquid_12mo|cool_temperate_moist` = 0.31) are in the registry but not wired.
- Manure N2O: poultry +36 to +45% (2019 Nrate), market swine +9.5% (Nrate 0.46 and leaching), dairy 0% (module uses 2006 cattle Nrate/FracGasMS because Nex is the EPA override).
- Managed-soil N2O: crop_urea_lime +19.3% (EF1 wet synthetic 0.016), broiler field +16%, swine field -4.5% (EF1 wet other 0.006 vs 0.01, offset by more F_ON), beef pasture -52% (EF3PRP_CPP wet 0.006 vs 0.02).
- Cover variants (crust, solid) give identical IPCC results: IPCC methods have no cover factor for `liquid_nocrust`.

## Gaps (nothing invented)
1. Beef liquid manure N2O is NaN in both versions: 2006 Table 10.22 has no other-cattle liquid FracGasMS, and `ipcc2019.manure` still reads the 2006 key, although `IPCC2019.FracGasMS.other_cattle|liquid_nocrust` = 0.48 is registered.
2. `ipcc2019.manure` is a partial 2019 fork for cattle (MCF, B0, Nrate, FracGasMS still 2006). The manure CH4 "no change" result is a module gap, not an IPCC finding.
3. F_CR uses 2019 Table 11.1a for both versions.
