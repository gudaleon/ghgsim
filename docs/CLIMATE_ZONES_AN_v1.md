# County IPCC climate zones (AN_v1)

Script: `scripts/build_county_climate_zones_AN_v1.py`. Output: `data/county_climate_zones_AN_v1.csv` (3,142 counties) plus a manifest.

- **Primary (`zone_primary`).** The IPCC 2019 climate-zone raster recreated by Lewis (2022), Zenodo doi:10.5281/zenodo.7303808. It is 0.5° resolution, built from CRU TS3.25 (1985–2015), Penman-Monteith PET, frost days and ETOPO1 elevation. I sampled it at the 2020 Gazetteer county internal point; 2 coastal counties use the nearest valid cell. Raster md5: f4fa673bd3cb4e0992931b0aff555eb8.
- **Sensitivity columns.**
  - `zone_hargreaves`: nClimDiv 1991–2020 data with Hargreaves PE (the earlier AN_v1 rule).
  - `zone_thornthwaite`: the same data with Thornthwaite PE.
  - For both, MAT > 18 °C is reported as `tropical_unresolved`, because frost days and elevation are not available.
- **Counties by zone (IPCC map):**

  | Zone | Counties |
  |---|---|
  | Warm temperate moist | 1,232 |
  | Warm temperate dry | 898 |
  | Cool temperate dry | 612 |
  | Cool temperate moist | 288 |
  | Tropical moist | 62 |
  | Tropical dry | 30 |
  | Boreal dry | 11 |
  | Boreal moist | 5 |
  | Polar moist | 3 |
  | Polar dry | 1 |

- **Moist/dry agreement with the map, for the 2,664 resolvable counties.**
  - Hargreaves disagrees in 432 counties: 354 are too dry and 78 too wet.
  - Thornthwaite disagrees in 779 counties: 778 are too wet.
  - Example, Polk County, IA: the map says cool temperate dry and Hargreaves agrees; Thornthwaite says moist.

See DECISIONS_AN_v4 #2.
