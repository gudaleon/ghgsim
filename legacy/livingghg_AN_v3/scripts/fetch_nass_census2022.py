"""Stream-filter the USDA NASS Quick Stats bulk file for the 2022 Census of Agriculture (no API key needed)
into a small county CSV (gzip). Nothing large is written to disk.
Source: https://www.nass.usda.gov/datasets/qs.census2022.txt.gz"""
import csv, gzip, io, sys, urllib.request, datetime
URL = "https://www.nass.usda.gov/datasets/qs.census2022.txt.gz"
KEEP = {"CATTLE, COWS, MILK - INVENTORY", "CATTLE, COWS, BEEF - INVENTORY", "CATTLE, INCL CALVES - INVENTORY",
        "CORN, GRAIN - ACRES HARVESTED", "CORN, SILAGE - ACRES HARVESTED", "SOYBEANS - ACRES HARVESTED",
        "WHEAT - ACRES HARVESTED", "HAY & HAYLAGE - ACRES HARVESTED"}
COLS = ["STATE_ALPHA", "STATE_FIPS_CODE", "COUNTY_CODE", "COUNTY_NAME", "SHORT_DESC", "VALUE", "CV_%"]

def main(out="data_nass/nass_census2022_county_AN_v1.csv.gz"):
    n = 0
    with urllib.request.urlopen(URL, timeout=600) as resp, gzip.open(out, "wt", newline="") as fo:
        rd = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=resp), encoding="utf-8", errors="replace"), delimiter="\t")
        w = csv.writer(fo); w.writerow(COLS)
        for r in rd:
            if r["AGG_LEVEL_DESC"] == "COUNTY" and r["DOMAIN_DESC"] == "TOTAL" and r["YEAR"] == "2022" and r["SHORT_DESC"] in KEEP:
                w.writerow([r[c] for c in COLS]); n += 1
    print(f"{n} rows -> {out} ({datetime.datetime.now().isoformat(timespec='minutes')})")

if __name__ == "__main__":
    main(*sys.argv[1:])
