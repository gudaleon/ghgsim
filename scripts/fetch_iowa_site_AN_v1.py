"""Fetch documented US Corn Belt site data for the APSIM crop run (AN_v1), DECISIONS_AN_v24.

Site: 42.020 N, 93.774 W (Boone County, Iowa; SSURGO survey area IA015).
- Soil: USDA-NRCS SSURGO via Soil Data Access (https://sdmdataaccess.sc.egov.usda.gov), map unit at
  the point, dominant component and its horizons (representative values, *_r). Raw response saved.
- Weather: NASA POWER daily API v2 (https://power.larc.nasa.gov), community AG, 1991-01-01 to
  2020-12-31: T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN. Raw JSON saved (gzip).
Writes data/apsim_site_iowa_AN_v1/ (refuses to overwrite). Usage: python scripts/fetch_iowa_site_AN_v1.py
"""
from __future__ import annotations

import gzip
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apsim_site_iowa_AN_v1"
LAT, LON = 42.020, -93.774
SDA = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
POWER = (
    "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR,"
    f"ALLSKY_SFC_SW_DWN&community=AG&longitude={LON}&latitude={LAT}&start=19910101&end=20201231&format=JSON"
)
Q_COMP = f"""SELECT mu.mukey, mu.muname, l.areaname, l.areasymbol, sc.saverest, c.cokey, c.compname, c.comppct_r,
c.majcompflag, c.taxclname, c.hydgrp, c.slope_r, c.drainagecl
FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('point({LON} {LAT})') k
JOIN mapunit mu ON mu.mukey = k.mukey JOIN legend l ON l.lkey = mu.lkey
JOIN sacatalog sc ON sc.areasymbol = l.areasymbol JOIN component c ON c.mukey = mu.mukey
ORDER BY c.comppct_r DESC"""
Q_HZ = """SELECT hzname, hzdept_r, hzdepb_r, dbthirdbar_r, wthirdbar_r, wfifteenbar_r, wsatiated_r, ksat_r,
om_r, ph1to1h2o_r, claytotal_r, silttotal_r, sandtotal_r FROM chorizon WHERE cokey = '{cokey}' ORDER BY hzdept_r"""


def sda(sql: str) -> list[dict]:
    req = urllib.request.Request(SDA, data=json.dumps({"query": sql, "format": "JSON+COLUMNNAME"}).encode(),
                                 headers={"Content-Type": "application/json"})
    t = json.load(urllib.request.urlopen(req, timeout=120))["Table"]
    return [dict(zip(t[0], r, strict=True)) for r in t[1:]]


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    comps = sda(Q_COMP)
    dom = comps[0]
    hz = sda(Q_HZ.format(cokey=dom["cokey"]))
    soil = {"source": "USDA-NRCS SSURGO via Soil Data Access", "url": SDA, "retrieved_utc": now,
            "point_wgs84": [LAT, LON], "queries": [Q_COMP, Q_HZ], "components": comps, "dominant": dom, "horizons": hz}
    (OUT / "ssurgo_point_AN_v1.json").write_text(json.dumps(soil, indent=1) + "\n", encoding="utf-8")
    raw = urllib.request.urlopen(POWER, timeout=300).read()
    with gzip.GzipFile(OUT / "nasa_power_daily_1991_2020_AN_v1.json.gz", "wb", mtime=0) as fo:
        fo.write(raw)
    man = {"retrieved_utc": now, "power_url": POWER,
           "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}}
    (OUT / "site_manifest_AN_v1.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    print(dom["compname"], dom["areaname"], len(hz), "horizons;", len(raw), "bytes POWER")


if __name__ == "__main__":
    main()
