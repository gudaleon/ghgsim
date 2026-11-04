# County annual climate and IPCC climate zones (AN v1)

File: `data/county_climate_annual_AN_v1.csv` (3,142 counties), manifest
`data/county_climate_annual_manifest_AN_v1.json` (SHA-256 of inputs and output).
Script: `scripts/build_county_climate_annual_AN_v1.py` (standard library; reuses
`build_county_p_pe_AN_v2.py`). Raw inputs on Bubble: `C:\ghgsim-data\climate\nclimdiv\`
(nClimDiv v1.0.0-20261006, doi:10.7289/V5M32STR, Vose et al. 2014).

## Columns
- `mean_annual_temp_c`: mean of 12 monthly (Tmax+Tmin)/2, averaged over 1991-2020.
- `annual_precip_mm`, `annual_pe_hargreaves_mm`: 12-month sums; PE = Hargreaves-Samani
  (FAO-56 Eq 52), uncalibrated. `annual_p_over_pe` = ratio of the two means.
- `ipcc_zone`: IPCC 2006 Vol 4 Ch 3 Annex 3A.5 rule (boreal MAT <= 0; cool temperate
  0-10 C; warm temperate 10-18 C; moist if P/PE > 1). Blank when MAT > 18 C (tropical needs
  MAP/elevation classes; not derived).

Jargon: **MAT** = mean annual temperature; **P/PE** = precipitation / potential
evapotranspiration; **MCF** = methane conversion factor (share of manure methane potential
actually emitted in a storage system).

## Zone counts
| Zone | Counties |
|---|---|
| (blank: MAT > 18 C, tropical unresolved) | 478 |
| warm_temperate_moist | 797 |
| warm_temperate_dry | 928 |
| cool_temperate_moist | 242 |
| boreal_moist | 7 |
| boreal_dry | 5 |
| cool_temperate_dry | 685 |

## Use in ghgsim
`ipcc2019.manure` accepts `county_fips`. Precedence: `climate_zone_2019` > `mean_annual_temp_c`
+ `moisture_ratio` > `county_fips`. Tropical and boreal counties fall back to 2006 Table 10.17
(`MCF_basis` says so) because those 2019 cells are not in the parameter registry yet.

## Caveat
Uncalibrated Hargreaves overestimates PE in humid regions, so the moist/dry split leans dry
(e.g. Polk County IA: P 909 mm, PE 1,006 mm, P/PE 0.90). Thornthwaite or Penman-Monteith would
shift some Midwest counties to moist; a sensitivity is planned.

Rebuild: `python scripts/build_county_climate_annual_AN_v1.py --version-date 20261006`
(refuses to overwrite existing `_AN_v1` files).
