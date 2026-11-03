# County May-October P and PE for `holos_liang2020` (AN v1)

Builds `growing_season_precip_mm` and `growing_season_pe_mm` candidates per US county for the Holos EF1 option `holos_liang2020` (Holos V4 Sec 2.5, which uses May-October CanSIS 1980-2010 P and PE for Canada).

## Files
- `scripts/build_county_p_pe_AN_v1.py`: reproducible builder (standard library only). Refuses to overwrite existing `_AN_vX` outputs.
- `data/county_p_pe_may_oct_AN_v1.csv`: 3,141 counties; columns `fips, state, county, lat_intpt, n_years, period, growing_season_precip_mm, pe_hargreaves_mm, pe_thornthwaite_mm, p_over_pe_hargreaves, p_over_pe_thornthwaite`.
- `data/county_p_pe_manifest_AN_v1.json`: sources, versions, DOI, SHA-256 of inputs and output, issues.
- `tests/test_county_p_pe_AN_v1.py`.
- Raw inputs (about 123 MB) live on Bubble at `C:\ghgsim-data\climate\nclimdiv\`, not in git.

## Sources
- NOAA nClimDiv county monthly files `climdiv-pcpncy`, `climdiv-tmaxcy`, `climdiv-tmincy`, version `v1.0.0-20261006`, from https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/. County values are area-weighted means of the 5 km nClimGrid grid. Citation: Vose, R.S., Applequist, S., Squires, M., Durre, I., Menne, M.J., Williams, C.N. Jr., Fenimore, C., Gleason, K., Arndt, D. (2014). NOAA Monthly U.S. Climate Divisional Database (NClimDiv). NOAA National Climatic Data Center. doi:10.7289/V5M32STR.
- US Census Bureau 2020 Gazetteer counties (`INTPTLAT`) for latitude.

## Method
1. Parse county files (inches -> mm; deg F -> deg C; NCEI state codes mapped to FIPS).
2. For each year in the period (default 1980-2010 inclusive, 31 years), P = sum of May-Oct monthly precipitation.
3. PE, two documented, uncalibrated options from monthly Tmax/Tmin:
   - Hargreaves-Samani (1985), FAO-56 Eq 52: `0.0023 (Tmean+17.8) sqrt(Tmax-Tmin) 0.408 Ra`, Ra from FAO-56 Eqs 21-25 at mid-month day, times days in month.
   - Thornthwaite (1948), heat index from the same year's 12 monthly means; no correction above 26.5 C.
4. Average the yearly May-Oct sums over years with complete data (`n_years`).

Run: `python scripts/build_county_p_pe_AN_v1.py --version-date 20261006 --start 1980 --end 2010 --out <new path> --manifest <new path>`.

## Known issues
- Hawaii county data start in 1991, so HI rows have `n_years` = 20 for 1980-2010.
- FIPS 24511 (nClimDiv, Maryland) has no 2020 Gazetteer match and is dropped.
- Counties follow 2020 boundaries (e.g. pre-2022 Connecticut counties).
- The two PE methods differ a lot in arid regions (Fresno CA: Hargreaves 916 mm vs Thornthwaite 579 mm). Neither is the CanSIS PE used by Holos.

## Decisions for Alex
1. Which PE method feeds `growing_season_pe_mm`: Hargreaves (default recommendation, uses Tmax-Tmin) or Thornthwaite, or a Penman-Monteith grid such as TerraClimate/gridMET (heavier, needs zonal stats).
2. Period: 1980-2010 inclusive (literal Holos text) vs 1981-2010 normals vs 1991-2020.
3. Whether to wire the CSV into a county lookup in `soil_n2o.py` (not done in this PR).
