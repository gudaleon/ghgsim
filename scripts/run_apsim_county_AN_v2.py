"""APSIM daily runs on the expanded county sample (AN_v2), research questions (c) and (d), FINDINGS_AN_v2.

US: the 100-county sample of build_county_sample_AN_v2 (SSURGO soil, NASA POWER 1991-2020).
Ontario: upper-tier counties/regions and the rural single-tier municipalities south of 45.5 N (names beginning
"CITY OF", "TOWN OF" or "TOWNSHIP OF" are excluded as urban or island units), CanSIS soil of the dominant SLC
component at the municipality's representative point (fetch_ontario_soils_AN_v1), NASA POWER at that point.
Set-up as the pilot (run_apsim_county_pilot_AN_v1: Examples/Maize.apsimx, maize B_110, 100 kg N/ha urea at
sowing and 0 N, APSIM SoilWater, APSoil No. 900 borrowed fields), with three changes:
- sowing window = the state's USDA NASS (2010) Agricultural Handbook 628 "most active" corn planting dates
  (data/nass_corn_planting_2010_AN_v1.csv); Ontario uses Michigan's (nearest NASS state; a flagged proxy);
- NASA POWER -999 flags filled by linear interpolation (power_fill_AN_v1);
- where a source SAT exceeds the porosity implied by BD (1 - BD/2.65), APSIM rejects the soil; v1 dropped such
  counties, v2 sets SAT to that limit (floored to 0.001) and records each change.
Usage: python scripts/run_apsim_county_AN_v2.py [shard nshards]. Resumable; writes results/apsim_county_AN_v2/.
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f1  # noqa: E402
import power_fill_AN_v1 as pf  # noqa: E402
import run_apsim_crop_AN_v1 as v1  # noqa: E402
import run_apsim_crop_AN_v2 as v2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
US = ROOT / "data" / "apsim_county_v2_AN_v1"
ONT = ROOT / "data" / "ontario_soils_AN_v1" / "cansis_ontario_counties_AN_v1.json"
ONT_POWER = ROOT / "data" / "ontario_counties_power_AN_v1"
OUT = ROOT / "results" / "apsim_county_AN_v2"
RUNS = {"100N": 100.0, "0N": 0.0}
ST = {"AL": "Alabama", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
      "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
      "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
      "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
      "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
      "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
      "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
      "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}


def windows() -> dict[str, tuple[str, str]]:
    def dm(s: str) -> str:
        d = datetime.strptime(s + " 2001", "%b %d %Y")
        return f"{d.day}-{d.strftime('%b').lower()}"
    with (ROOT / "data" / "nass_corn_planting_2010_AN_v1.csv").open(encoding="utf-8") as fh:
        return {r["state"]: (dm(r["most_active_start"]), dm(r["most_active_end"])) for r in csv.DictReader(fh)}


def ontario_units() -> list[dict]:
    seen, out = set(), []
    for c in json.loads(ONT.read_text(encoding="utf-8"))["counties"]:
        if c["munid"] in seen or "skip" in c or c["municipality"].startswith(("CITY OF", "TOWN OF", "TOWNSHIP OF")):
            continue
        seen.add(c["munid"])
        out.append(c)
    return out


def ontario_power(c: dict) -> Path:
    p = ONT_POWER / f"{c['munid']}_nasa_power_daily_1991_2020_AN_v1.json.gz"
    if not p.exists():
        ONT_POWER.mkdir(parents=True, exist_ok=True)
        lat, lon = c["point_wgs84"]
        url = f1.POWER.replace(f"longitude={f1.LON}&latitude={f1.LAT}", f"longitude={lon}&latitude={lat}")
        raw = urllib.request.urlopen(url, timeout=300).read()
        with gzip.GzipFile(p, "wb", mtime=0) as fo:
            fo.write(raw)
        time.sleep(1)
    return p


def units() -> list[dict]:
    out = []
    with (US / "county_sample_AN_v2.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append({"id": r["fips"], "country": "US", "state": ST[r["state"]], "row": r,
                        "soil": lambda k=r["fips"]: json.loads((US / k / "ssurgo_point_AN_v1.json").read_text(encoding="utf-8")),
                        "power": lambda k=r["fips"]: US / k / "nasa_power_daily_1991_2020_AN_v1.json.gz"})
    for c in ontario_units():
        dom = {"muname": c["soilname"], "compname": c["soilname"], "areaname": c["municipality"], "areasymbol": f"SLC {c['slc_poly_id']}",
               "saverest": "CanSIS v2r20140203", "mukey": c["soil_id"], "cokey": c["soil_id"], "comppct_r": c["component_percent"],
               "drainagecl": c["drainage"], "hydgrp": None}
        out.append({"id": "ON" + c["munid"], "country": "CA", "state": "Michigan", "row": c,
                    "soil": lambda c=c, dom=dom: {"point_wgs84": c["point_wgs84"], "horizons": c["horizons"], "dominant": dom},
                    "power": lambda c=c: ontario_power(c)})
    return out


def cap_sat(soil_node: dict) -> list[dict]:
    phys = next(c for c in soil_node["Children"] if "Physical" in c["$type"])
    caps = []
    for k, (sat, bd) in enumerate(zip(phys["SAT"], phys["BD"], strict=True)):
        lim = int((1 - bd / 2.65) * 1000) / 1000
        if sat > lim:
            caps.append({"layer": k, "SAT_from_source": sat, "SAT_used": lim, "BD": bd})
            phys["SAT"][k] = lim
    return caps


def main() -> None:
    shard, nsh = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if v1.APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    example = json.loads((apsim / "Examples" / "Maize.apsimx").read_text(encoding="utf-8"))
    win = windows()
    OUT.mkdir(parents=True, exist_ok=True)
    us = units()
    with tempfile.TemporaryDirectory(dir=os.environ.get("GHGSIM_TMP")) as td:
        for j, u in enumerate(us):
            if j % nsh != shard or (OUT / f"county_{u['id']}_run_AN_v2.json").exists():
                continue
            ssurgo = u["soil"]()
            with gzip.open(u["power"](), "rt", encoding="utf-8") as fh:
                power, fills = pf.fill_power(json.load(fh))
            met = Path(td) / f"{u['id']}.met"
            metinfo = v2.write_met(power, met, *ssurgo["point_wgs84"])
            sw = dict(zip(("StartDate", "EndDate"), win[u["state"]], strict=True))
            info = {"id": u["id"], "country": u["country"], "sowing_window": sw, "window_state": u["state"], "met": metinfo,
                    "filled_missing": fills, "soil": {k: ssurgo["dominant"].get(k) for k in ("areaname", "mukey", "compname", "comppct_r", "drainagecl", "hydgrp")}}
            for tag, amount in RUNS.items():
                name = f"county_{u['id']}_{tag}_AN_v2"
                m = v1.build(example, apsim, tag, "AU_Dalby.met", amount)
                next(v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
                next(v1._find(m, "Models.Clock,")).update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
                for p in next(v1._find(m, "Models.Manager,", "Sow using a variable rule"))["Parameters"]:
                    p["Value"] = {**v2.SOW, **sw}.get(p["Key"], p["Value"])
                zone = next(v1._find(m, "Models.Core.Zone,"))
                i = next(q for q, ch in enumerate(zone["Children"]) if ch["$type"].startswith("Models.Soils.Soil,"))
                zone["Children"][i] = v2.build_soil(zone["Children"][i], ssurgo)
                info["sat_caps"] = cap_sat(zone["Children"][i])
                sim = Path(td) / f"{name}.apsimx"
                sim.write_text(json.dumps(m), encoding="utf-8")
                shutil.copyfile(sim, OUT / sim.name)
                r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
                if r.returncode != 0:
                    info.setdefault("failed", {})[tag] = next((ln.strip() for ln in r.stdout.splitlines() if "Exception" in ln), r.stdout[-300:])
                    continue
                for kind in ("Daily", "Report"):
                    if not (Path(td) / f"{name}.{kind}.csv").exists():  # no harvest rows -> APSIM writes no Report
                        info.setdefault("missing_output", []).append(f"{tag}.{kind}")
                        continue
                    with (Path(td) / f"{name}.{kind}.csv").open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                        shutil.copyfileobj(fi, fo)
            (OUT / f"county_{u['id']}_run_AN_v2.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
            print("failed" if "failed" in info else "done", u["id"], u["state"], flush=True)


if __name__ == "__main__":
    main()