"""Brookston (Essex, CanSIS) with APSIM SoilWater (cascading bucket) instead of SWIM, AN_v1.

Why: every sown Brookston SWIM run fails (FINDINGS_AN_v4 section 2). SoilWater has no tile drain, so this gives an
undrained, crash-free 1991-2020 Brookston N2O EF only (Holos also has no drainage term). Identical to
run_apsim_lake_erie_AN_v3.py (same soil, met, sowing change 5, 172 N) except the water module: SoilWater as built by
APSoil/CanSIS (v3.soil_for with swim False), no gradient boundary, no tile. Consistency check, not validation.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import power_fill_AN_v1 as pf  # noqa: E402
import run_apsim_crop_AN_v1 as v1  # noqa: E402
import run_apsim_crop_AN_v2 as v2  # noqa: E402
import run_apsim_crop_AN_v3 as v3  # noqa: E402
import run_apsim_lake_erie_AN_v3 as le  # noqa: E402

OUT = le.ROOT / "results" / "apsim_brookston_soilwater_AN_v1"
le.EXTRA = ["[SoilWater].Drainage as Drainage_mm", "[SoilWater].Runoff as Runoff_mm",
            "[Soybean].Grain.Wt*10 as SoyGrain_kgha", "[Soybean].AboveGround.N*10 as SoyAbovegroundN_kgha"]
_orig = v3.soil_for
v3.soil_for = lambda case, node, ssurgo, tpl: _orig({"swim": False, "tile": False}, node, ssurgo, tpl)


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    maize_ex = json.loads((apsim / "Examples" / "Maize.apsimx").read_text(encoding="utf-8"))
    soy_ex = json.loads((apsim / "Examples" / "Soybean.apsimx").read_text(encoding="utf-8"))
    swim_tpl, seep_tpl = v3.find_swim(apsim), v3.find_seepage(apsim)
    site = le.sites()["essex_brookston"]
    OUT.mkdir(parents=True)
    runs = {}
    with tempfile.TemporaryDirectory() as td:
        lat, lon = site["soil"]["point_wgs84"]
        pp = site.get("power") or le.power_for(lat, lon)
        with gzip.open(pp, "rt", encoding="utf-8") as fh:
            power, fills = pf.fill_power(json.load(fh))
        met = Path(td) / "essex_brookston.met"
        metinfo = {**v2.write_met(power, met, lat, lon), "power_file": str(pp.relative_to(le.ROOT)), "filled_missing": fills}
        for amount in (le.CORN_N, 0.0):
            name = "brookston_soilwater" + ("" if amount else "_0N") + "_AN_v1"
            m = le.build(apsim, maize_ex, soy_ex, site, None, amount, met, swim_tpl, seep_tpl)
            zone = next(v1._find(m, "Models.Core.Zone,"))
            zone["Children"] = [c for c in zone["Children"] if c.get("Name") != "SWIM3_SetLowerBC_gradient"]
            for mgr in ("Sow Maize", "Sow Soybean"):
                for prm in next(v1._find(m, "Models.Manager,", mgr))["Parameters"]:
                    if prm["Key"] in ("MinESW", "MinRain"):
                        prm["Value"] = "0.0"
            caps = m.pop("_sat_caps")
            sim = Path(td) / f"{name}.apsimx"
            sim.write_text(json.dumps(m, indent=1), encoding="utf-8")
            r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
            txt = json.loads(sim.read_text(encoding="utf-8"))
            next(v1._find(txt, "Models.Climate.Weather,"))["FileName"] = met.name
            (OUT / f"{name}.apsimx").write_text(json.dumps(txt, indent=1) + "\n", encoding="utf-8")
            for kind in ("Daily", "Report"):
                src = Path(td) / f"{name}.{kind}.csv"
                if src.exists():
                    with src.open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                        shutil.copyfileobj(fi, fo)
            info = {"corn_urea_N_kg_ha": amount, "sat_caps": caps, "returncode": r.returncode}
            if r.returncode:
                info["failed"] = next((ln for ln in r.stdout.splitlines() if "Exception" in ln), r.stdout[-300:]).strip()
            runs[name] = info
            print(name, info.get("failed", "done"), flush=True)
    man = {"apsim": {"version": ver, "models_dll_sha256": v1.sha256(models)}, "met": metinfo, "runs": runs,
           "outputs_sha256": {p.name: v1.sha256(p) for p in sorted(OUT.iterdir())}}
    (OUT / "manifest_AN_v1.json").write_text(json.dumps(man, indent=1, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()