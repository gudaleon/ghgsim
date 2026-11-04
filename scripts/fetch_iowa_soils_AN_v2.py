"""Fetch a well-drained Clarion soil and restrictive-layer records for the Iowa APSIM sensitivity runs (AN_v2), DECISIONS_AN_v25.

Same county as the main site (Boone County, Iowa, SSURGO survey area IA015), USDA-NRCS SSURGO via Soil Data Access:
- Clarion: the IA015 map unit with the largest mapped acreage (mapunit.muacres) whose largest component is
  Clarion; its horizons (representative values, *_r) are saved. No point is needed because the weather is the
  same NASA POWER record (data/apsim_site_iowa_AN_v1).
- Restrictive layers (corestrictions) for the Webster component of the main site and for the Clarion component,
  used to set the depth to the impermeable layer in the tile-drain run (none recorded -> profile bottom).
Writes data/apsim_site_iowa_AN_v2/ (refuses to overwrite). Usage: python scripts/fetch_iowa_soils_AN_v2.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apsim_site_iowa_AN_v2"
V1 = ROOT / "data" / "apsim_site_iowa_AN_v1" / "ssurgo_point_AN_v1.json"
Q_CLARION = """SELECT TOP 5 mu.mukey, mu.muname, mu.muacres, l.areaname, l.areasymbol, sc.saverest, c.cokey, c.compname,
c.comppct_r, c.majcompflag, c.taxclname, c.hydgrp, c.slope_r, c.drainagecl
FROM legend l JOIN mapunit mu ON mu.lkey = l.lkey JOIN sacatalog sc ON sc.areasymbol = l.areasymbol
JOIN component c ON c.mukey = mu.mukey
WHERE l.areasymbol = 'IA015' AND c.compname = 'Clarion'
AND c.comppct_r = (SELECT MAX(c2.comppct_r) FROM component c2 WHERE c2.mukey = mu.mukey)
ORDER BY mu.muacres DESC"""
Q_RES = "SELECT cokey, reskind, resdept_r, resdepb_r FROM corestrictions WHERE cokey IN ({keys})"


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cands = f1.sda(Q_CLARION)
    dom = cands[0]
    hz = f1.sda(f1.Q_HZ.format(cokey=dom["cokey"]))
    web = json.loads(V1.read_text(encoding="utf-8"))["dominant"]
    try:
        res = f1.sda(Q_RES.format(keys=f"'{web['cokey']}','{dom['cokey']}'"))
    except (KeyError, IndexError):
        res = []
    soil = {"source": "USDA-NRCS SSURGO via Soil Data Access", "url": f1.SDA, "retrieved_utc": now,
            "point_wgs84": json.loads(V1.read_text(encoding="utf-8"))["point_wgs84"],
            "queries": [Q_CLARION, f1.Q_HZ, Q_RES], "candidates": cands, "dominant": dom, "horizons": hz,
            "restrictions": res}
    (OUT / "ssurgo_clarion_AN_v2.json").write_text(json.dumps(soil, indent=1) + "\n", encoding="utf-8")
    man = {"retrieved_utc": now, "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}}
    (OUT / "site_manifest_AN_v2.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    print(dom["muname"], dom["muacres"], dom["comppct_r"], dom["drainagecl"], len(hz), "horizons; restrictions:", res)
    for h in hz:
        print({k: h[k] for k in ("hzname", "hzdept_r", "hzdepb_r", "dbthirdbar_r", "wthirdbar_r", "wfifteenbar_r", "wsatiated_r", "ksat_r", "om_r", "ph1to1h2o_r")})


if __name__ == "__main__":
    main()