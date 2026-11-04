"""Fetch the SSURGO Brookston component that carries a densic (restricting) layer, AN_v1.

Why: the CanSIS Essex Brookston profile (ONBKN, 0-100 cm) has KP33/KP1500 so close (Btg 0.36/0.31, Ckg 0.32/0.30)
that the SWIM K curve (HydraulicProperties.SetupKCurve: b = -ln(psiDUL/psiLL15)/ln(DUL/LL15), MicroP = 2b + 3)
gives MicroP ~ 120 and K(sat) ~ 2.6e10 mm/d below 65 cm, so no lower boundary can restrict drainage and Newton fails.
SSURGO's Brookston series (MI, the official-series source) has a densic Cd horizon (ksat 0.005 um/s) under Cg.
Proxy across the border, flagged. Same query set as the Hoytville v1 fetch.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
OUT = Path(__file__).resolve().parents[1] / "data" / "apsim_site_lake_erie_AN_v3" / "ssurgo_brookston_densic_AN_v1.json"
Q_COMP = """SELECT mu.mukey, mu.muname, mu.muacres, l.areaname, l.areasymbol, sc.saverest, c.cokey, c.compname,
c.comppct_r, c.majcompflag, c.taxclname, c.hydgrp, c.slope_r, c.drainagecl
FROM legend l JOIN mapunit mu ON mu.lkey = l.lkey JOIN sacatalog sc ON sc.areasymbol = l.areasymbol
JOIN component c ON c.mukey = mu.mukey JOIN corestrictions r ON r.cokey = c.cokey
WHERE c.compname = 'Brookston' AND c.majcompflag = 'Yes' AND r.reskind = 'Densic material'
ORDER BY mu.muacres DESC"""
Q_HZ = """SELECT hzname, hzdept_r, hzdepb_r, dbthirdbar_r, wthirdbar_r, wfifteenbar_r, wsatiated_r, ksat_r,
om_r, ph1to1h2o_r, claytotal_r, silttotal_r, sandtotal_r FROM chorizon WHERE cokey = '{cokey}' ORDER BY hzdept_r"""
Q_RES = "SELECT cokey, reskind, reshard, resdept_r, resdepb_r FROM corestrictions WHERE cokey = '{cokey}'"
Q_MO = ("SELECT cm.month, cs.soimoistdept_r, cs.soimoistdepb_r, cs.soimoiststat FROM comonth cm JOIN cosoilmoist cs "
        "ON cs.comonthkey = cm.comonthkey WHERE cm.cokey = '{cokey}' ORDER BY cm.monthseq, cs.soimoistdept_r")


def sda(sql: str) -> list[dict]:
    req = urllib.request.Request(URL, json.dumps({"format": "JSON+COLUMNNAME", "query": sql}).encode(), {"Content-Type": "application/json"})
    t = json.loads(urllib.request.urlopen(req, timeout=120).read()).get("Table", [])
    return [dict(zip(t[0], r, strict=True)) for r in t[1:]] if t else []


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    cands = sda(Q_COMP)
    dom = cands[0]
    ck = dom["cokey"]
    rec = {"source": "USDA-NRCS SSURGO via Soil Data Access", "url": URL, "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "point_wgs84": [42.1631, -82.7793], "point_note": "Essex Brookston point (CanSIS run); soil properties are the SSURGO series proxy",
           "queries": [Q_COMP, Q_HZ, Q_RES, Q_MO], "candidates": cands, "dominant": dom,
           "horizons": sda(Q_HZ.format(cokey=ck)), "restrictions": sda(Q_RES.format(cokey=ck)), "cosoilmoist": sda(Q_MO.format(cokey=ck))}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(dom, [(h["hzname"], h["hzdept_r"], h["hzdepb_r"], h["ksat_r"]) for h in rec["horizons"]], rec["restrictions"])


if __name__ == "__main__":
    main()