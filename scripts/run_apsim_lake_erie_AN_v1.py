"""Lake Erie basin tile-drainage experiment: drained vs undrained Hoytville clay loam, APSIM SWIM3 (AN_v1).

Consistency/process experiment, not validation (FINDINGS_AN_v1). Soil: SSURGO Hoytville clay loam 0-1 %
(OH173, Wood County OH; very poorly drained, Mollic Epiaqualf), data/apsim_site_lake_erie_AN_v1, mapped with
run_apsim_crop_AN_v2.build_soil and APSoil No. 900 borrowed fields exactly as for the Iowa runs. The impeding
layer is SSURGO's own: Cd horizon 145-203 cm, ksat_r 0.005 um/s (0.43 mm/d), recorded in corestrictions as
densic material at 145 cm. SWIM3 settings from APSIM's tutorial (run_apsim_crop_AN_v3.find_swim), default
seepage base at the SSURGO densic contact. Weather: NASA POWER 1991-2020 at 41.22 N 83.76 W (OSU Northwest
Agricultural Research Station, Hoytville OH, 41 13' N 83 45' W). Maize management as in the Iowa main run.
Cases, each at 100 kg N/ha urea and 0 N:
- erie_undrained: no drains.
- erie_tile_1956: drains 0.76 m deep, 12.2 m spacing (OSU Hoytville Northwestern Substation, 1956 study:
  5-inch tile at 40 ft spacing, average depth 30 in; Ohio State University Knowledge Bank, "Hoytville soils").
- erie_tile_lt: drains 1.2 m deep, 17 m spacing (OSU long-term tillage experiment, Hoytville: 10 cm tile at
  17 m spacing and 1.2-1.4 m depth, citing Dick et al. 1986; lower end of the depth range used).
Densic Cd horizon replaced by a seepage base at 1450 mm (see main()); 145 mm SWIM nodes. Klat = SSURGO ksat_r of the horizon at drain depth x 86.4 (mm/d); ImpermDepth = 1450 mm (SSURGO densic top).
Writes results/apsim_lake_erie_AN_v1/ (refuses to overwrite).
"""
from __future__ import annotations

import copy
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_apsim_crop_AN_v1 as v1  # noqa: E402
import run_apsim_crop_AN_v2 as v2  # noqa: E402
import run_apsim_crop_AN_v3 as v3  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "apsim_site_lake_erie_AN_v1"
OUT = ROOT / "results" / "apsim_lake_erie_AN_v1"
IMPERM_MM = 1450.0
CASES = {
    "erie_undrained": None,
    "erie_tile_1956": {"DrainDepth": 760.0, "DrainSpacing": 12200.0},
    "erie_tile_lt": {"DrainDepth": 1200.0, "DrainSpacing": 17000.0},
}
EXTRA = ["[SoilWater].SubsurfaceDrain as TileDrain_mm", "[SoilWater].WaterTable as WaterTable_mm"]


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if v1.APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    ssurgo = json.loads((DATA / "ssurgo_hoytville_AN_v1.json").read_text(encoding="utf-8"))
    with gzip.open(DATA / "nasa_power_daily_1991_2020_AN_v1.json.gz", "rt", encoding="utf-8") as fh:
        power = json.load(fh)
    example_path = apsim / "Examples" / "Maize.apsimx"
    example = json.loads(example_path.read_text(encoding="utf-8"))
    swim_tpl = v3.find_swim(apsim)
    # The SSURGO Cd horizon (145-203 cm, ksat_r 0.005 um/s = 0.43 mm/d) has Ksat below the tutorial SWIM KDul
    # (1 mm/d, conductivity at DUL), an inconsistent hydraulic function on which SWIM fails to converge (tested).
    # Without tuning either value, the densic layer is represented as the base of the simulated profile (0-1450 mm,
    # SSURGO resdept_r) with APSIM's documented "seepage" lower boundary: water leaves the base only once the
    # profile is saturated there, so a perched water table forms above the densic layer. 145 mm SWIM nodes
    # (10 nodes; 50 mm nodes gave a soil-temperature solver failure in the 0 N run, tested).
    assert ssurgo["horizons"][-1]["hzname"] == "Cd" and ssurgo["restrictions"][0]["resdept_r"] == "145"
    ssurgo["horizons"] = ssurgo["horizons"][:-1]
    v3.LAYER_MM = 145.0
    seep_tpl = v3.find_seepage(apsim)
    OUT.mkdir(parents=True)
    runs = {}
    with tempfile.TemporaryDirectory() as td:
        met = Path(td) / "hoytville_oh.met"
        metinfo = v2.write_met(power, met, *ssurgo["point_wgs84"])
        for cname, tile in CASES.items():
            v3.TILE.update({"ImpermDepth": IMPERM_MM, **(tile or {})})
            for amount in (100.0, 0.0):
                site = cname if amount else cname + "_0N"
                m = v1.build(example, apsim, site, "AU_Dalby.met", amount)
                next(v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
                next(v1._find(m, "Models.Clock,")).update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
                for p in next(v1._find(m, "Models.Manager,", "Sow using a variable rule"))["Parameters"]:
                    p["Value"] = v2.SOW.get(p["Key"], p["Value"])
                zone = next(v1._find(m, "Models.Core.Zone,"))
                i = next(k for k, c in enumerate(zone["Children"]) if c["$type"].startswith("Models.Soils.Soil,"))
                zone["Children"][i] = v3.soil_for({"swim": True, "tile": tile is not None}, zone["Children"][i], ssurgo, swim_tpl)
                zone["Children"].append(copy.deepcopy(seep_tpl))
                daily = next(c for c in zone["Children"] if c.get("Name") == "Daily")
                daily["VariableNames"] = list(daily["VariableNames"]) + EXTRA
                name = f"lake_erie_{site}_AN_v1"
                sim = Path(td) / f"{name}.apsimx"
                sim.write_text(json.dumps(m, indent=1), encoding="utf-8")
                r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
                if r.returncode != 0:
                    dl = Path(td) / f"{name}.Daily.csv"
                    tail = dl.read_text(encoding="utf-8").splitlines()[-2:] if dl.exists() else []
                    # recorded, not hidden: solver failures are reported in FINDINGS_AN_v1
                    err = next((ln for ln in r.stdout.splitlines() if "System.Exception" in ln), "unknown")
                    runs[site] = {"case": cname, "failed": err.strip(), "last_day": tail[-1].split(",")[4] if tail else None}
                    print("failed", site, runs[site], flush=True)
                    continue
                txt = json.loads(sim.read_text(encoding="utf-8"))
                next(v1._find(txt, "Models.Climate.Weather,"))["FileName"] = met.name
                (OUT / f"{name}.apsimx").write_text(json.dumps(txt, indent=1) + "\n", encoding="utf-8")
                for kind in ("Daily", "Report"):
                    with (Path(td) / f"{name}.{kind}.csv").open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                        shutil.copyfileobj(fi, fo)
                runs[site] = {"case": cname, "tile": dict(v3.TILE) if tile else None, "urea_N_kg_ha": amount}
                print("done", site, flush=True)
    man = {"apsim": {"version": ver, "commit": v1.APSIM_COMMIT, "models_dll_sha256": v1.sha256(models)},
           "soil": {k: ssurgo["dominant"][k] for k in ("areasymbol", "mukey", "muname", "muacres", "cokey", "compname", "comppct_r", "taxclname", "drainagecl", "hydgrp")},
           "restrictions": ssurgo["restrictions"], "met": metinfo, "runs": runs,
           "outputs_sha256": {p.name: v1.sha256(p) for p in sorted(OUT.iterdir())}}
    (OUT / "apsim_lake_erie_manifest_AN_v1.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
