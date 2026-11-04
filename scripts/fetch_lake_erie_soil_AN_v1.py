"""Fetch a representative Lake Erie basin poorly drained soil (Hoytville, Wood County OH, SSURGO OH173) (AN_v1).

Lake Erie tile-drainage experiment, FINDINGS_AN_v1. Largest-acreage map unit whose dominant component is
Hoytville in survey area OH173; horizons (incl. ksat_r), corestrictions and monthly cosoilmoist (wet-layer depth,
i.e. the SSURGO seasonal high water table) for that component; NASA POWER daily weather 1991-2020 at the
map-unit search point near the OSU Northwest Agricultural Research Station, Hoytville OH (41.22 N, 83.76 W,
approximate). Writes data/apsim_site_lake_erie_AN_v1/ (refuses to overwrite).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apsim_site_lake_erie_AN_v1"
LAT, LON = 41.22, -83.76
POWER = f1.POWER.replace(f"longitude={f1.LON}&latitude={f1.LAT}", f"longitude={LON}&latitude={LAT}")
Q_MU = """SELECT TOP 5 mu.mukey, mu.muname, mu.muacres, l.areaname, l.areasymbol, sc.saverest, c.cokey, c.compname,
c.comppct_r, c.majcompflag, c.taxclname, c.hydgrp, c.slope_r, c.drainagecl
FROM legend l JOIN mapunit mu ON mu.lkey = l.lkey JOIN sacatalog sc ON sc.areasymbol = l.areasymbol
JOIN component c ON c.mukey = mu.mukey
WHERE l.areasymbol = 'OH173' AND c.compname = 'Hoytville'
AND c.comppct_r = (SELECT MAX(c2.comppct_r) FROM component c2 WHERE c2.mukey = mu.mukey)
ORDER BY mu.muacres DESC"""
Q_RES = "SELECT cokey, reskind, reshard, resdept_r, resdepb_r FROM corestrictions WHERE cokey = '{cokey}'"
Q_WT = ("SELECT cm.month, cs.soimoistdept_r, cs.soimoistdepb_r, cs.soimoiststat FROM comonth cm "
        "JOIN cosoilmoist cs ON cs.comonthkey = cm.comonthkey WHERE cm.cokey = '{cokey}' ORDER BY cm.monthseq, cs.soimoistdept_r")


def sda(q: str) -> list[dict]:
    try:
        return f1.sda(q)
    except (KeyError, IndexError):
        return []


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cands = sda(Q_MU)
    dom = cands[0]
    k = dom["cokey"]
    hz, res, wt = sda(f1.Q_HZ.format(cokey=k)), sda(Q_RES.format(cokey=k)), sda(Q_WT.format(cokey=k))
    OUT.mkdir(parents=True)
    soil = {"source": "USDA-NRCS SSURGO via Soil Data Access", "url": f1.SDA, "retrieved_utc": now,
            "point_wgs84": [LAT, LON], "queries": [Q_MU, f1.Q_HZ, Q_RES, Q_WT], "candidates": cands, "dominant": dom,
            "horizons": hz, "restrictions": res, "cosoilmoist": wt}
    (OUT / "ssurgo_hoytville_AN_v1.json").write_text(json.dumps(soil, indent=1) + "\n", encoding="utf-8")
    raw = urllib.request.urlopen(POWER, timeout=300).read()
    with gzip.GzipFile(OUT / "nasa_power_daily_1991_2020_AN_v1.json.gz", "wb", mtime=0) as fo:
        fo.write(raw)
    man = {"retrieved_utc": now, "power_url": POWER,
           "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}}
    (OUT / "site_manifest_AN_v1.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    print(dom["muname"], dom["muacres"], dom["comppct_r"], dom["drainagecl"], dom["taxclname"])
    for h in hz:
        print({x: h[x] for x in ("hzname", "hzdept_r", "hzdepb_r", "ksat_r", "claytotal_r", "dbthirdbar_r", "wsatiated_r", "om_r")})
    print("restrictions:", res)
    print("wet:", [(w["month"], w["soimoistdept_r"], w["soimoistdepb_r"]) for w in wt if w["soimoiststat"] == "Wet"])


if __name__ == "__main__":
    main()