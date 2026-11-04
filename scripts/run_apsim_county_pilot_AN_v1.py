"""Run APSIM daily on the 20-county pilot sample (AN_v1), research question (b), FINDINGS_AN_v1.

Same set-up as the Iowa main run (run_apsim_crop_AN_v2): APSIM NG 2026.11.8142.0 Examples/Maize.apsimx,
maize B_110 sown 19 Apr-26 May, 100 kg N/ha urea at sowing and a 0 N control, APSIM SoilWater, SSURGO soil
at the county internal point with APSoil No. 900 borrowed fields, NASA POWER daily weather 1991-2020.
Management is deliberately identical everywhere so that differences come from soil and weather only.
Reads data/apsim_county_pilot_AN_v1/; writes results/apsim_county_pilot_AN_v1/ (refuses to overwrite).
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_apsim_crop_AN_v1 as v1  # noqa: E402
import run_apsim_crop_AN_v2 as v2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "apsim_county_pilot_AN_v1"
OUT = ROOT / "results" / "apsim_county_pilot_AN_v1"
RUNS = {"100N": 100.0, "0N": 0.0}


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if (OUT / "apsim_county_pilot_manifest_AN_v1.json").exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if v1.APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    example_path = apsim / "Examples" / "Maize.apsimx"
    example = json.loads(example_path.read_text(encoding="utf-8"))
    with (DATA / "county_pilot_sample_AN_v1.csv").open(encoding="utf-8") as fh:
        sample = list(csv.DictReader(fh))
    OUT.mkdir(parents=True, exist_ok=True)  # resumable: finished county runs are kept, never rewritten
    runs, skipped = {}, {}
    with tempfile.TemporaryDirectory() as td:
        for c in sample:
            k = c["fips"]
            ssurgo = json.loads((DATA / k / "ssurgo_point_AN_v1.json").read_text(encoding="utf-8"))
            with gzip.open(DATA / k / "nasa_power_daily_1991_2020_AN_v1.json.gz", "rt", encoding="utf-8") as fh:
                power = json.load(fh)
            met = Path(td) / f"{k}.met"
            metinfo = v2.write_met(power, met, *ssurgo["point_wgs84"])
            err = None
            for tag, amount in RUNS.items():
                name = f"county_{k}_{tag}_AN_v1"
                if (OUT / f"{name}.Report.csv.gz").exists():
                    continue
                m = v1.build(example, apsim, tag, "AU_Dalby.met", amount)
                next(v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
                next(v1._find(m, "Models.Clock,")).update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
                for p in next(v1._find(m, "Models.Manager,", "Sow using a variable rule"))["Parameters"]:
                    p["Value"] = v2.SOW.get(p["Key"], p["Value"])
                zone = next(v1._find(m, "Models.Core.Zone,"))
                i = next(j for j, ch in enumerate(zone["Children"]) if ch["$type"].startswith("Models.Soils.Soil,"))
                zone["Children"][i] = v2.build_soil(zone["Children"][i], ssurgo)
                sim = Path(td) / f"{name}.apsimx"
                sim.write_text(json.dumps(m), encoding="utf-8")
                r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
                if r.returncode != 0 and "inconsistent with each other" in r.stdout:
                    # SSURGO bulk density / saturated water content inconsistent for APSIM; no tuning allowed,
                    # so the county is dropped and reported (FINDINGS_AN_v1).
                    err = "APSIM soil physical check: rock content, bulk density and saturated water content inconsistent"
                    break
                if r.returncode != 0:
                    raise SystemExit(f"APSIM failed for {name}:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
                for kind in ("Daily", "Report"):
                    with (Path(td) / f"{name}.{kind}.csv").open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                        shutil.copyfileobj(fi, fo)
            if err:
                skipped[k] = {"reason": err, "soil": ssurgo["dominant"]["compname"]}
                print("skipped", k, err, flush=True)
                continue
            runs[k] = {"met": metinfo, "soil": {x: ssurgo["dominant"][x] for x in ("areasymbol", "mukey", "muname", "cokey", "compname", "comppct_r", "drainagecl", "hydgrp")}}
            print("done", k, c["state"], c["county"], flush=True)
    man = {"apsim": {"version": ver, "commit": v1.APSIM_COMMIT, "models_dll_sha256": v1.sha256(models)},
           "example": {"file": "Examples/Maize.apsimx", "sha256": v1.sha256(example_path)},
           "management": {**v2.SOW, "urea_N_kg_ha": RUNS}, "runs": runs, "skipped": skipped,
           "outputs_sha256": {p.name: v1.sha256(p) for p in sorted(OUT.iterdir())}}
    (OUT / "apsim_county_pilot_manifest_AN_v1.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()