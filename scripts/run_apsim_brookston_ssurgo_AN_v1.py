"""Brookston with a SSURGO densic restricting layer and SWIM tile drains, AN_v1 (FINDINGS_AN_v7).

Reuses run_apsim_lake_erie_AN_v3.py unchanged (SpaceWeightingFactor 0.5, PSIDul -330 cm, MinESW/MinRain 0,
gradient lower boundary, flags --pond / --eo1440) with one site replaced:
* soil: SSURGO Brookston loam, dense substratum (MI155 mukey 2393950, cokey 27985665; series proxy for Essex, flagged:
  fine-loamy, clay 23-28 %, vs CanSIS Essex Brookston clay 37-51 %), horizons Ap/Btg/Cg 0-127 cm;
* lower boundary: gr = Ksat(Cd 127-203 cm) / Ksat(Cg) - 1 = 0.005 / 0.55 - 1 (same rule as Hoytville, now from
  Brookston's own restricting layer, no transfer);
* weather, sowing windows and tile cases as for essex_brookston in v3 (tile_1956 OSU depth/spacing; tile_2rod Essex
  Report 11 spacing at 0.76 m; both flagged as in v3). ImpermDepth = profile base (1270 mm).
Reason the CanSIS profile is not used: see scripts/fetch_ssurgo_brookston_AN_v1.py (SWIM K(sat) blow-up).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_apsim_lake_erie_AN_v3 as le  # noqa: E402

SOIL = le.ROOT / "data" / "apsim_site_lake_erie_AN_v3" / "ssurgo_brookston_densic_AN_v1.json"
le.OUT = le.ROOT / "results" / ("apsim_brookston_ssurgo_" + ("pond_" if "--pond" in sys.argv else "") + ("eo1440_" if "--eo1440" in sys.argv else "") + "AN_v1")
le.WINDOWS["MI_SSURGO"] = le.WINDOWS["MI"]


def sites() -> dict:
    s = json.loads(SOIL.read_text(encoding="utf-8"))
    cd = s["horizons"][-1]
    assert cd["hzname"] == "Cd" and s["restrictions"][0]["reskind"] == "Densic material"
    s["horizons"] = s["horizons"][:-1]
    gr = float(cd["ksat_r"]) / float(s["horizons"][-1]["ksat_r"]) - 1.0
    return {"essex_brookston_ssurgo": {"soil": s, "state": "MI_SSURGO", "layer": 127.0, "tiles": {"tile_1956": le.TILE_1956, "tile_2rod": le.TILE_2ROD}, "gr": gr,
                                       "power": le.power_for(42.1631, -82.7793)}}


le.sites = sites
le.GR = {"brookston_ssurgo": sites()["essex_brookston_ssurgo"]["gr"]}

if __name__ == "__main__":
    le.main()