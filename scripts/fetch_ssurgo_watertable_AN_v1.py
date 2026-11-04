"""SSURGO seasonal wet-soil (water-table) depths by month for the Lake Erie soils (AN_v1).

Source: USDA-NRCS SSURGO via Soil Data Access, tables comonth/cosoilmoist (soimoiststat = 'Wet' marks the
saturated zone, i.e. the apparent/perched water table; soimoistdept_r is its representative top depth, cm).
- Hoytville: the dominant component of the AN_v1/AN_v2 Wood County OH point (cokey from ssurgo_hoytville_AN_v1).
- Brookston: the same named series (Typic Argiaquolls) is mapped in Michigan; the major Brookston components of the
  Monroe County MI survey (MI115, directly across Lake Erie's western basin from Essex) are listed with their
  monthly wet-layer tops. CanSIS gives only a water-table class for Brookston, so this cross-border series value is a
  flagged proxy, not an Ontario measurement.
Writes data/lake_erie_watertable_AN_v1/ssurgo_wet_months_AN_v1.json (refuses to overwrite).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "lake_erie_watertable_AN_v1" / "ssurgo_wet_months_AN_v1.json"
Q = ("SELECT c.cokey, c.compname, c.comppct_r, c.drainagecl, mu.muname, mu.mukey, l.areasymbol, m.month, m.monthseq, "
     "s.soimoistdept_r, s.soimoistdepb_r, s.soimoiststat FROM legend l JOIN mapunit mu ON mu.lkey = l.lkey "
     "JOIN component c ON c.mukey = mu.mukey JOIN comonth m ON m.cokey = c.cokey "
     "JOIN cosoilmoist s ON s.comonthkey = m.comonthkey WHERE {where} AND s.soimoiststat = 'Wet' "
     "ORDER BY c.cokey, m.monthseq, s.soimoistdept_r")


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    hoyt = json.loads((ROOT / "data" / "apsim_site_lake_erie_AN_v1" / "ssurgo_hoytville_AN_v1.json").read_text(encoding="utf-8"))
    qs = {"hoytville": Q.format(where=f"c.cokey = '{hoyt['dominant']['cokey']}'"),
          "brookston_MI115": Q.format(where="l.areasymbol = 'MI115' AND c.compname = 'Brookston' AND c.majcompflag = 'Yes'")}
    out = {"retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": f.SDA, "queries": qs, "rows": {}}
    for k, q in qs.items():
        try:
            out["rows"][k] = f.sda(q)
        except KeyError:
            out["rows"][k] = []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k, rows in out["rows"].items():
        print(k, len(rows))
        for r in rows:
            print(" ", r["areasymbol"], r["muname"][:40], r["cokey"], r["month"], r["soimoistdept_r"], r["soimoistdepb_r"])


if __name__ == "__main__":
    main()