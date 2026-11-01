# USDA NASS 2022 Census of Agriculture - county extract (AN_v1)
- Source: USDA NASS Quick Stats bulk file https://www.nass.usda.gov/datasets/qs.census2022.txt.gz (309,188,711 bytes; Last-Modified 2024-02-14 19:25:51 GMT). No API key needed for the bulk file; the Quick Stats API itself returned "unauthorized" without a key, so it was not used.
- Fetched 2026-10-31 12:51 ET with `scripts/fetch_nass_census2022.py` (streamed and filtered; the full file was never stored).
- Filter: AGG_LEVEL_DESC=COUNTY, DOMAIN_DESC=TOTAL, YEAR=2022, SHORT_DESC in: CATTLE, COWS, MILK - INVENTORY; CATTLE, COWS, BEEF - INVENTORY; CATTLE, INCL CALVES - INVENTORY; CORN, GRAIN / CORN, SILAGE / SOYBEANS / WHEAT / HAY & HAYLAGE - ACRES HARVESTED.
- Output: `nass_census2022_county_AN_v1.csv.gz` (20,754 rows, ~245 KB). Columns: STATE_ALPHA, STATE_FIPS_CODE, COUNTY_CODE, COUNTY_NAME, SHORT_DESC, VALUE, CV_%.
- "(D)" = withheld to avoid disclosing individual operations (share of rows: milk cows 36%, beef cows 29%, corn silage 26%, wheat 18%, soybeans 14%, corn grain 13%, all cattle 2%, hay 1%). The engine treats (D) as missing and flags it (`suppressed_D`); state sums therefore undercount.
- Crop areas are stored but not yet used: soil N2O needs N application rates, which are not in this extract (Phase 3).
