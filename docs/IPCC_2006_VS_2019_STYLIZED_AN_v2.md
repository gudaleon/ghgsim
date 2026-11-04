# IPCC 2006 vs 2019 Refinement – stylized farms (AN_v2)

Supersedes `IPCC_2006_VS_2019_STYLIZED_AN_v1.md` (kept unchanged). Outputs: `data/ipcc_2006_vs_2019_stylized_AN_v2.csv`, `docs/figures/ipcc_2006_vs_2019_stylized_AN_v2.png`; scripts `scripts/*_AN_v2.py`; parameters `data/ipcc_params_AN_v8.csv`.

## What changed vs v1
1. `ipcc2019.manure` 2.0.0 uses 2019 Refinement manure factors throughout:
   * MCF – Vol 4 Ch 10 Table 10.17 (Updated), 12-month storage row (`storage_months` = 6 also supported), climate zone from `climate_zone_2019` or derived from mean annual temperature + moisture ratio (2006 Vol 4 Ch 3 Annex 3A.5 zone scheme; tropical returns None -> 2006 MCF fallback, flagged in `MCF_basis`). Crust = liquid x (1-0.40) (Table 10.17 fn); PRP = 0.47 % paired with B0 0.19 (fn).
   * B0 and Nex rate – Table 10.16 / 10.19 (Updated); FracGasMS / FracLeachMS – Table 10.22 (Updated), which has an *other cattle* liquid cell (0.48) – this fills the v1 beef manure-N2O NaN for 2019.
   * Stylized farms run in `warm_temperate_moist` (spec: 15 C MAT, humid fields), 12-month storage.
   * cool_temperate_moist 12-month liquid MCF (31 %, Table 10.17 Updated p. 10.68) was already in the registry; nothing invented.
2. `ipcc2006.manure`: FracLossMS (2006 Vol 4 Ch 10 Table 10.23, p. 10.67) and Eq 10.34 `N_MMS_Avb`; manure N applied to fields now uses N after losses for both guidelines. Cells absent from Table 10.23 return NaN.
3. Soil N2O: optional `dry_fallback_ef1 = "ipcc2019_dry"` sensitivity (see `LIANG_DRY_FALLBACK_AN_v2.md`). Default unchanged (0.01).

## Results (t CO2e/yr, 2006 / 2019)
| Farm | Enteric CH4 06/19 | Manure CH4 06/19 | Manure N2O 06/19 | Soil N2O 06/19 | Total 06 | Total 19 | % |
|---|---|---|---|---|---|---|---|
| dairy_forage_uncovered | 529.4 / 491.0 | 368.9 / 751.4 | 30.5 / 38.7 | 0.0 / 0.0 | 928.7 | 1281.1 | +37.9 |
| dairy_forage_covered_crust | 529.4 / 491.0 | 368.9 / 751.4 | 30.5 / 38.7 | 0.0 / 0.0 | 928.7 | 1281.1 | +37.9 |
| dairy_forage_covered_solid | 529.4 / 491.0 | 368.9 / 751.4 | 30.5 / 38.7 | 0.0 / 0.0 | 928.7 | 1281.1 | +37.9 |
| dairy_high_grain_uncovered | 398.6 / 352.9 | 144.1 / 293.5 | 30.5 / 38.7 | 0.0 / 0.0 | 573.2 | 685.1 | +19.5 |
| dairy_high_grain_covered_crust | 398.6 / 352.9 | 144.1 / 293.5 | 30.5 / 38.7 | 0.0 / 0.0 | 573.2 | 685.1 | +19.5 |
| beef_cowcalf_uncovered | 201.8 / 195.6 | 121.8 / 248.1 | blank / 18.0 | 0.0 / 0.0 | 323.6* | 461.7 | +42.7* |
| beef_cowcalf_covered_crust | 201.8 / 195.6 | 121.8 / 248.1 | blank / 18.0 | 0.0 / 0.0 | 323.6* | 461.7 | +42.7* |
| beef_cowcalf_covered_solid | 201.8 / 195.6 | 121.8 / 248.1 | blank / 18.0 | 0.0 / 0.0 | 323.6* | 461.7 | +42.7* |
| broiler_litter | 0.0 / 0.0 | 14.8 / 14.8 | 15.0 / 21.8 | 0.0 / 0.0 | 29.8 | 36.5 | +22.5 |
| layer_litter | 0.0 / 0.0 | 8.0 / 8.0 | 11.4 / 15.5 | 0.0 / 0.0 | 19.4 | 23.5 | +21.2 |
| layer_highrise | 0.0 / 0.0 | 8.0 / 8.0 | 14.8 / 17.9 | 0.0 / 0.0 | 22.8 | 25.9 | +13.9 |
| turkey_litter | 0.0 / 0.0 | 12.9 / 12.9 | 19.1 / 19.1 | 0.0 / 0.0 | 32.1 | 32.1 | +0.0 |
| market_swine_liquid | 42.0 / 42.0 | 239.6 / 488.1 | 14.1 / 15.4 | 0.0 / 0.0 | 295.7 | 545.5 | +84.5 |
| breeding_swine_liquid | 8.4 / 8.4 | 88.7 / 180.8 | 6.9 / 6.9 | 0.0 / 0.0 | 104.1 | 196.1 | +88.4 |
| farrow_to_finish | 50.4 / 50.4 | 328.3 / 668.9 | 19.7 / 21.0 | 0.0 / 0.0 | 398.5 | 740.2 | +85.8 |
| broiler_litter_field | 0.0 / 0.0 | 14.8 / 14.8 | 15.0 / 21.8 | 22.4 / 30.9 | 52.2 | 67.4 | +29.1 |
| market_swine_field | 42.0 / 42.0 | 239.6 / 488.1 | 14.1 / 15.4 | 25.1 / 24.0 | 320.8 | 569.5 | +77.5 |
| beef_pasture_field | 201.8 / 195.6 | 6.8 / 2.1 | 0.0 / 0.0 | 87.4 / 43.5 | 296.0 | 241.2 | -18.5 |
| crop_urea_lime | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 9.3 / 11.0 | 9.3 | 11.0 | +19.3 |

\* 2006 total excludes manure N2O, which is blank.

## Values left blank (never invented)
* 2006 beef_cowcalf manure N2O – 2006 Table 10.22 has no other-cattle liquid FracGasMS.
* 2006 other-cattle liquid FracLossMS – no Table 10.23 cell (no effect on totals: beef_cowcalf farms have no field).
* County-derived 2019 climate zones are not wired: the repo's county climate file has May–Oct P/PE only, no annual MAT or MAP/PET.

## Notes
* Liquid-manure CH4 roughly doubles (MCF 0.55 vs 0.27) for cattle and swine; dairy manure N2O +26.7 %.
* beef_pasture_field falls (-18.5 %) because of 2019 EF3PRP and PRP MCF.
* The covered variants equal the uncovered ones, as in v1 (stylized spec cover inputs do not change the system fractions).
