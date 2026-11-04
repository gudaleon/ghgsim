"""Run APSIM Next Generation on the stylized crop farm crop_urea_lime (AN_v1, DECISIONS_AN_v23).

Consistency check, not validation. APSIM is run unmodified as outside software; no APSIM code is
copied into ghgsim. The simulation is APSIM's own shipped example Examples/Maize.apsimx (APSoil
No. 900 Black Vertosol, Norwin, Darling Downs, Qld; CSIRO Sustainable Ecosystems, Toowoomba, GRDC
project 2011; cultivar Dekalb_XL82, sowing rule, harvest manager) with only these changes:
- fertiliser at sowing: 100 kg N/ha as UreaN (crop_urea_lime: F_SN 1000 kg N on 10 ha) instead of
  160 kg N/ha NO3N; a 0 kg N/ha control is also run to isolate fertiliser-induced N2O;
- weather: the example's AU_Dalby.met (as shipped) and, as the climate-matched run, the shipped
  NZ_Hamilton.met (Ruakura; tav 13.8 C, ~1150 mm rain: IPCC warm temperate moist, like the
  stylized "wet" field). No soil or weather value is invented or edited;
- a daily report of N2O, N2, mineralisation, mineral N pools, NO3 leaching, rain and temperature.
Clock 1990-01-01..2000-12-31 as in the example.

Usage: python scripts/run_apsim_crop_AN_v1.py
Env: GHGSIM_APSIM_DIR (install root holding bin/Models.dll and Examples/),
     GHGSIM_DOTNET (dotnet executable for .NET 10). Writes results/apsim_AN_v1/ (refuses to overwrite).
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "apsim_AN_v1"
APSIM_VERSION = "2026.11.8142.0"
APSIM_COMMIT = "d1dca5e97aa4930a2015722362483b1216005037"
APSIM_PR = "https://github.com/APSIMInitiative/ApsimX/pull/11706"
RUNS = {
    "dalby": ("AU_Dalby.met", 100.0),
    "dalby_0N": ("AU_Dalby.met", 0.0),
    "hamilton": ("NZ_Hamilton.met", 100.0),
    "hamilton_0N": ("NZ_Hamilton.met", 0.0),
}
DAILY = [
    "[Clock].Today",
    "[Weather].Rain",
    "[Weather].MeanT",
    "sum([Nutrient].N2Oatm) as N2O_N_kgha",
    "sum([Nutrient].Natm) as N2_N_kgha",
    "sum([Nutrient].MineralisedN) as MinN_kgha",
    "sum([NO3].kgha) as NO3_kgha",
    "sum([NH4].kgha) as NH4_kgha",
    "sum([Urea].kgha) as Urea_kgha",
    "[SoilWater].LeachNO3 as LeachNO3_kgha",
    "[Maize].AboveGround.N as MaizeN_gm2",
    "sum([SoilWater].SWmm) as SW_mm",
    "[SoilWater].Drainage as Drain_mm",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _find(n, t, name=None):
    if n.get("$type", "").startswith(t) and (name is None or n.get("Name") == name):
        yield n
    for c in n.get("Children", []):
        yield from _find(c, t, name)


def build(example: dict, apsim: Path, site: str, met: str, amount: float) -> dict:
    m = copy.deepcopy(example)
    sim = next(_find(m, "Models.Core.Simulation,"))
    sim["Name"] = f"crop_urea_lime_{site}"
    next(_find(m, "Models.Climate.Weather,"))["FileName"] = str(apsim / "Examples" / "WeatherFiles" / met)
    fert = next(_find(m, "Models.Manager,", "Fertilise at sowing"))
    for p in fert["Parameters"]:
        if p["Key"] == "FertiliserType":
            p["Value"] = "UreaN"
        if p["Key"] == "Amount":
            p["Value"] = f"{amount:.1f}"
    rep = next(_find(m, "Models.Report,"))
    daily = copy.deepcopy(rep)
    daily["Name"] = "Daily"
    daily["VariableNames"] = DAILY
    daily["EventNames"] = ["[Clock].DoReport"]
    zone = next(_find(m, "Models.Core.Zone,"))
    zone["Children"].insert(zone["Children"].index(rep) + 1, daily)
    for g in list(_find(m, "Models.Graph,")):
        sim["Children"].remove(g)
    return m


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    example_path = apsim / "Examples" / "Maize.apsimx"
    example = json.loads(example_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True)
    files = {}
    with tempfile.TemporaryDirectory() as td:
        for site, (met, amount) in RUNS.items():
            name = f"crop_urea_lime_{site}_AN_v1"
            sim = Path(td) / f"{name}.apsimx"
            sim.write_text(json.dumps(build(example, apsim, site, met, amount), indent=1), encoding="utf-8")
            p = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
            if p.returncode != 0:
                raise SystemExit(f"APSIM failed for {site}:\n{p.stdout}\n{p.stderr}")
            txt = json.loads(sim.read_text(encoding="utf-8"))
            next(_find(txt, "Models.Climate.Weather,"))["FileName"] = f"%root%/Examples/WeatherFiles/{met}"
            (OUT / f"{name}.apsimx").write_text(json.dumps(txt, indent=1) + "\n", encoding="utf-8")
            for kind in ("Daily", "Report"):
                src = Path(td) / f"{name}.{kind}.csv"
                dst = OUT / f"{name}.{kind}.csv.gz"
                with src.open("rb") as fi, gzip.GzipFile(dst, "wb", mtime=0) as fo:
                    shutil.copyfileobj(fi, fo)
            files[site] = {"weather": met, "urea_N_kg_ha": amount}
    manifest = {
        "apsim": {
            "version": ver,
            "commit": APSIM_COMMIT,
            "pr": APSIM_PR,
            "licence": "APSIM General Use Licence / ApsimX repository licence (run unmodified, not redistributed)",
            "install": "portable: official build 8142 package contents in a user folder, .NET 10 user runtime",
            "models_dll_sha256": sha256(models),
        },
        "dotnet": subprocess.run([dotnet, "--version"], capture_output=True, text=True).stdout.strip()
        or "runtime only",
        "python": platform.python_version(),
        "example": {"file": "Examples/Maize.apsimx", "sha256": sha256(example_path)},
        "soil": "APSoil No. 900, Black Vertosol (Norwin, Darling Downs, Qld); CSIRO Sustainable Ecosystems,"
        " Toowoomba, GRDC project 'Doing it better, doing it smarter, managing soil water in Australian"
        " agriculture' (2011); as shipped in Examples/Maize.apsimx",
        "weather_sha256": {m: sha256(apsim / "Examples" / "WeatherFiles" / m) for m in ("AU_Dalby.met", "NZ_Hamilton.met")},
        "runs": files,
        "outputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in sorted(OUT.iterdir())},
        "note": "consistency check, not validation",
    }
    (OUT / "apsim_crop_manifest_AN_v1.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
