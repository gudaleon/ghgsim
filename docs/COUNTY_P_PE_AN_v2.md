# County May-October P and PE for `holos_liang2020` (AN v2)

Supersedes `COUNTY_P_PE_AN_v1.md` (v1 files kept). Decisions by Alex, 2026-11-03: PE = Hargreaves; period = 1991-2020 normals.

## Files
- `scripts/build_county_p_pe_AN_v2.py` (standard library only; refuses to overwrite `_AN_vX` outputs).
- `data/county_p_pe_may_oct_AN_v2.csv`: 3,142 counties, all with 30 complete years (Hawaii now complete). Columns: `fips, state, county, lat_intpt, n_years, period, growing_season_precip_mm, growing_season_pe_mm, pe_method, pe_hargreaves_mm, pe_thornthwaite_mm, p_over_pe_hargreaves, p_over_pe_thornthwaite`. `growing_season_pe_mm` = `pe_hargreaves_mm`; Thornthwaite is a sensitivity column.
- `data/county_p_pe_manifest_AN_v2.json`: sources, version, DOI, SHA-256 of all inputs and the output.
- `src/ghgsim/modules/holos/county_climate.py`: lookup `county_p_pe(fips)`.
- Tests: `tests/test_county_p_pe_AN_v2.py`, county tests in `tests/test_crops_soils.py`.
- Raw inputs on Bubble: `C:\ghgsim-data\climate\nclimdiv\`.

## Sources
- NOAA nClimDiv county files `climdiv-pcpncy`, `-tmaxcy`, `-tmincy`, version `v1.0.0-20261006`. Vose et al. (2014), NOAA Monthly U.S. Climate Divisional Database (NClimDiv), doi:10.7289/V5M32STR.
- NOAA `county-to-climdivs.txt` (same directory): county FIPS to nClimDiv code table.
- US Census 2020 Gazetteer counties (`INTPTLAT`).

## Method
Unchanged from v1 except the period (1991-2020 inclusive, 30 years) and the county code mapping. Per year: P = sum of May-Oct precipitation; PE = Hargreaves-Samani (1985) per FAO-56 Eq 52 with Ra from FAO-56 Eqs 21-25 at mid-month; Thornthwaite (1948) as sensitivity. Then the mean over years.

## FIPS 24511 fix (verified)
nClimDiv files the District of Columbia under Maryland: code `18511`, which the alphabetical state map turns into `24511` (not a real FIPS). NOAA's own `county-to-climdivs.txt` lists `11001 18511 1804`, i.e. FIPS 11001 (District of Columbia). v2 applies that NOAA table to every county code; 18511 -> 11001 is the only code that differs from the plain state mapping. DC is now in the file; 24511 is not. Baltimore city (24510 = nClimDiv 18510) was already correct.

## Wiring into `soil_n2o.py`
New optional input `county_fips` on `holos.soil_n2o`. When `HOLOS.N2O.ef1 = holos_liang2020` and `growing_season_precip_mm` or `growing_season_pe_mm` is missing, they are filled from the v2 CSV. Explicit inputs win. Unknown FIPS leave the status as `UNVERIFIED-input`. Dry counties (P < PE) still need `FR_Topo`; none is invented. `ipcc2006_ef1` is unaffected.

## Caveats
- PE is an uncalibrated temperature method, not the CanSIS PE that Holos uses for Canada.
- Most US counties are dry under Hargreaves (P/PE < 1), so `FR_Topo` is required for most of them. There is no US source for FR_Topo yet.
