"""Fetch SSURGO monthly 'Wet' soil-moisture depths (cosoilmoist) for the Webster and Clarion components (AN_v1).

Provenance for the undrained-Webster water-table case in run_apsim_crop_AN_v3 (WT_MM = mean over the 12
months of the Webster 'Wet' top depth). Source: USDA-NRCS Soil Data Access (same service as
fetch_iowa_site_AN_v1). Writes (refuses to overwrite): data/apsim_site_iowa_AN_v2/ssurgo_cosoilmoist_AN_v1.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
OUT = D / "apsim_site_iowa_AN_v2" / "ssurgo_cosoilmoist_AN_v1.json"
Q = ("SELECT cm.month, cs.soimoistdept_r, cs.soimoistdepb_r, cs.soimoiststat FROM comonth cm "
     "JOIN cosoilmoist cs ON cs.comonthkey = cm.comonthkey WHERE cm.cokey = '{cokey}' AND cs.soimoiststat = 'Wet'")


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    out = {"source": f.SDA, "query": Q, "components": {}}
    for name, p in (("webster", D / "apsim_site_iowa_AN_v1" / "ssurgo_point_AN_v1.json"),
                    ("clarion", D / "apsim_site_iowa_AN_v2" / "ssurgo_clarion_AN_v2.json")):
        dom = json.loads(p.read_text(encoding="utf-8"))["dominant"]
        rows = f.sda(Q.format(cokey=dom["cokey"]))
        tops = [float(r["soimoistdept_r"]) for r in rows]
        out["components"][name] = {"cokey": dom["cokey"], "compname": dom["compname"], "months": rows,
                                   "mean_wet_top_cm": round(sum(tops) / len(tops), 1)}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print({k: v["mean_wet_top_cm"] for k, v in out["components"].items()})


if __name__ == "__main__":
    main()