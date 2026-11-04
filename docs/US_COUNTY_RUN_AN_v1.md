# US county run, IPCC 2006 vs 2019 Tier 1 (AN_v1)

Script: `scripts/run_us_county_2006_vs_2019_AN_v1.py`. Decisions: `docs/DECISIONS_AN_v4.md`.

## Inputs (versions and hashes in `data/us_county_run_manifest_AN_v1.json`)

| Input | Version | SHA256 |
|---|---|---|
| NASS Quick Stats bulk `qs.census2022.txt.gz` (2022 Census of Agriculture) | Last-Modified 2024-02-14, 309,188,711 B | eca0f82dea58e1b128b82ac15f54e8bfc70cfb097e3e87710b74e7e93877dbbd |
| EPA ROE "Commercial fertilizer purchased" page (AAPFCO state N, 1000 kg N) | fetched 2026-11-03, latest year 2017 | 021f09a6e2ff14a603e47c3469469aba2513e729ab14fff463dd17f783476923 |
| Census cartographic boundary `cb_2022_us_county_20m.zip` | 2022 | 337192bcf4348d278304ebfbe2fceaeb936b368cc476c2aba51b59bd9e0b2e13 |
| `data/ipcc_params_AN_v9.csv` | v9 | adcdf82141988f0927dd019a282afff1b34b990c4b15bfda03719dc458c86139 |
| `data/county_climate_zones_AN_v1.csv` (IPCC 2019 map, Zenodo 7303808) | v1 | 4fa15553b1869303f2d111387c23041480f5e865501935fa14f4bc9833da2a6c |

EPA reference: *Inventory of U.S. GHG Emissions and Sinks 1990–2023* (2025 edition), main text, Table 5-1, p. 5-3, 2022 column. The PDF SHA256 is 9B37BE9F…E4B5.

## Outputs
- `data/us_county_2006_vs_2019_AN_v1.csv` has one row per county × source × category × gas. It gives kg and t CO2e for each version, % change, `census_flags` and `param_gaps`.
- `data/us_national_2006_vs_2019_vs_epa_AN_v1.csv` gives the national totals, the EPA check and the (D)-imputed sensitivity.
- `data/us_county_zone_sensitivity_AN_v1.csv` gives national 2019 totals under each zone method.
- `docs/figures/us_county_pct_change_2006_2019_AN_v1.png` maps the county % change in in-scope CO2e for CONUS.

## Headline numbers (MMT CO2e, AR5; 2022 Census activity)

| Category | 2006 | 2019 | Change | EPA 2022 | 2019 / EPA | 2019 / EPA, (D) imputed |
|---|---|---|---|---|---|---|
| Enteric CH4 | 118.9 | 139.1 | +16.9% | 192.6 | 0.72 | 0.93 |
| Manure CH4 | 36.9 | 53.3 | +44.5% | 64.7 | 0.82 | 0.93 |
| Manure N2O | 8.8 | 11.8 | +34.7% | 17.0 | 0.69 | 0.87 |
| Soil N2O (partial scope) | 86.6 | 62.1 | −28.3% | 291.8 | 0.21 | 0.22 |
| In-scope total | 251.2 | 266.3 | +6.0% | 566.1 | 0.47 | — |

- Of 3,065 counties with emissions, 1,881 rise and 1,184 fall from 2006 to 2019. The median change is +11.0%, with a range of −49.5% to +59.7%.
- Increases come from the higher 2019 cattle EFs, the 2019 liquid and lagoon MCFs (12-month storage) and higher Nrates.
- Decreases are in dry counties dominated by fertilizer and PRP N. There, the 2019 dry EF1 (0.005) and EF3PRP (0.002) replace the 2006 values of 0.01 and 0.02.
- Zone sensitivity for the 2019 national soil N2O: 62.1 (IPCC map), 57.5 (Hargreaves) and 93.8 (Thornthwaite) MMT CO2e. Manure CH4 is 53.3, 53.1 and 48.7.

## Consistency check against EPA (not validation)
- **Livestock:** With (D) cells imputed, the livestock categories come to 87–93% of EPA. That is plausible for Tier 1 against EPA's Tier 2/3 model, with sheep, goats and horses excluded.
- **Soils:** Soil N2O is about 22% of EPA because the scope is partial. EPA soils use DayCent, and include crop residues, mineralisation, organic soils and other N inputs.

## Gaps
- **(D) cells:** dairy 850, turkeys 688, pullets 613, broilers 587, roosters 524, swine 515, layers 348, cattle total 48 and fertilizer expense 26 county cells are withheld. In 32 more counties, other cattle is NaN because the total cattle figure is withheld. Withheld cells are not imputed in the county CSV.
- **No climate zone:** 1 NASS county has no zone match.
- **Census inventory as population:** December 31 inventory is used as a proxy for average annual population, with no adjustment for broiler or turkey turnover.
- **Swine:** there is no breeding-herd split, so all swine are treated as market swine.
- **Fertilizer:** N is 2017 data allocated by 2022 expense, which includes lime.
- **Excluded sources:** sheep, goats and horses; crop residues and F_SOM; organic soils, rice, liming and urea CO2.
- **Unpublished 2006 FracGasMS cells:** other cattle on liquid and swine on dry lot.
- **2019 VS defaults are not used** (see DECISIONS_AN_v4 #6).

## Reproduce
`python scripts/build_county_climate_zones_AN_v1.py --raw <climate dir>` (see `docs/CLIMATE_ZONES_AN_v1.md`), then

`python scripts/run_us_county_2006_vs_2019_AN_v1.py --nass <qs.census2022.txt.gz> --fert <epa fert html> --shp <cb_2022_us_county_20m.zip>`

Requires pandas, lxml, geopandas and matplotlib. The script refuses to overwrite its outputs.
