"""APSIM soil, drainage and borrowed-parameter sensitivity runs at the Iowa site (AN_v3), DECISIONS_AN_v25.

Consistency check, not validation. Same site, weather (NASA POWER 1991-2020), management and mapping as
scripts/run_apsim_crop_AN_v2.py (main run, Webster, APSIM SoilWater, results/apsim_AN_v2, unchanged). Each
case below is run at 100 kg N/ha urea and with a 0 N control, so the fertiliser-induced EF is computed per case.
- webster_swim: Webster with APSIM's SWIM3 water model (Richards equation) and no drains, to separate the
  change of water model from the effect of drains. SWIM settings are those of APSIM's documented tutorial
  (Examples/Tutorials/SWIM.apsimx, "HowToAddTileDrainage"), except Salb and the runoff curve (CN2Bare, CNRed,
  CNCov), kept from the main run.
- webster_tile: as webster_swim plus SwimSubsurfaceDrain, the tutorial's documented tile-drain component, with
  DrainDepth 1200 mm and DrainSpacing 28500 mm from the tile-drained Iowa APSIM study of Malone et al. (2007,
  Geoderma 140, 310-322, Nashua, IA: drains at 1.2 m depth, 28.5 m spacing); Klat = SSURGO ksat of the horizon
  holding the drain (mm/d); ImpermDepth = bottom of the SSURGO profile (2000 mm; SSURGO lists no restrictive
  layer for the component); DrainRadius 150 mm as in the tutorial.
- webster_seep / webster_tile: the tile case is run over APSIM's documented "seepage" lower boundary
  (tutorial "HowToSetASeepageLowerBoundaryCondition", SWIM3_SetLowerBC), so that water can perch above the
  base of the profile, and webster_seep is its no-drain twin; webster_swim keeps SWIM's default
  unit-gradient (free) base. Numerical nodes: 100 mm LayerStructure (SWIM tutorial practice).
- webster_wt: undrained Webster with a fixed water table at 660 mm (APSIM's documented "potential" lower
  boundary, tutorial "HowToSetAWaterTableLowerBoundaryCondition"); 660 mm is the mean over the 12 months of
  the SSURGO cosoilmoist 'Wet' top depth for this Webster component (15-110 cm). An upper bound for an
  undrained Webster; a fixed-head base cannot be combined with drains (the base then feeds the drains
  without limit; tested: >1,400 mm/yr tile flow), so no tile case is run on it.
- clarion: SSURGO Clarion loam, Bemis moraine, 2-6% slopes (IA015; well drained), APSIM SoilWater, same
  mapping and borrowed APSoil No. 900 parameters (data/apsim_site_iowa_AN_v2).
- borrowed-parameter sensitivity on the main Webster run, one at a time: initial NO3 and NH4 x0.5 and x2;
  FBiom x0.5 and x1.5; FInert x0.75 and x1.25 (capped at 0.99).
Writes results/apsim_AN_v3/ (refuses to overwrite).
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "apsim_AN_v3"
CLARION = ROOT / "data" / "apsim_site_iowa_AN_v2" / "ssurgo_clarion_AN_v2.json"
LAYER_MM = 100.0
# SSURGO cosoilmoist 'Wet' top depth for the Webster component (cokey 28627783), mean of the 12 months, cm -> mm
WT_MM = 660.0
PROFILE_MM = 2000.0
TILE = {"DrainDepth": 1200.0, "DrainSpacing": 28500.0, "DrainRadius": 150.0, "ImpermDepth": 2000.0, "Open": True}
TILE_SOURCE = ("Malone, R. W. et al. Evaluating and predicting agricultural management effects under tile drainage "
               "using modified APSIM. Geoderma 140, 310-322 (2007), doi:10.1016/j.geoderma.2007.04.014 (Nashua, IA: 1.2 m depth, 28.5 m spacing)")
CASES = {
    "webster_swim": {"soil": "webster", "swim": True, "tile": False},
    "webster_seep": {"soil": "webster", "swim": True, "tile": False, "seepage": True},
    "webster_tile": {"soil": "webster", "swim": True, "tile": True, "seepage": True},
    "webster_wt": {"soil": "webster", "swim": True, "tile": False, "watertable_mm": WT_MM},
    "clarion": {"soil": "clarion"},
    "initN_x0.5": {"soil": "webster", "initN": 0.5},
    "initN_x2": {"soil": "webster", "initN": 2.0},
    "FBiom_x0.5": {"soil": "webster", "FBiom": 0.5},
    "FBiom_x1.5": {"soil": "webster", "FBiom": 1.5},
    "FInert_x0.75": {"soil": "webster", "FInert": 0.75},
    "FInert_x1.25": {"soil": "webster", "FInert": 1.25},
}


def find_swim(apsim: Path) -> dict:
    """Swim3 node and the solute transport settings (D0, Exco, FIP) of the documented tile-drain tutorial."""
    m = json.loads((apsim / "Examples" / "Tutorials" / "SWIM.apsimx").read_text(encoding="utf-8"))
    stack = [m]
    while stack:
        n = stack.pop()
        if n.get("Name") == "HowToAddTileDrainage":
            sw = copy.deepcopy(next(v1._find(n, "Models.Soils.Swim3,")))
            sol, st = {}, [n]
            while st:
                k = st.pop()
                if k["$type"].startswith("Models.Soils.Solute,"):
                    sol[k["Name"]] = {"D0": k["D0"], "Exco": k["Exco"][0], "FIP": k["FIP"][0]}
                st += k.get("Children", [])
            sw["_solutes"] = sol
            return sw
        stack += n.get("Children", [])
    raise SystemExit("SWIM tutorial node not found")


def find_seepage(apsim: Path) -> dict:
    """APSIM's documented SWIM3_SetLowerBC manager (tutorial "HowToSetASeepageLowerBoundaryCondition")."""
    m = json.loads((apsim / "Examples" / "Tutorials" / "SWIM.apsimx").read_text(encoding="utf-8"))
    stack = [m]
    while stack:
        n = stack.pop()
        if n.get("Name") == "HowToSetASeepageLowerBoundaryCondition":
            mg = copy.deepcopy(next(v1._find(n, "Models.Manager,", "SWIM3_SetLowerBC")))
            assert {p["Key"]: p["Value"] for p in mg["Parameters"]}["LowerBCType"] == "seepage"
            return mg
        stack += n.get("Children", [])
    raise SystemExit("SWIM seepage tutorial node not found")


def soil_for(case: dict, node: dict, ssurgo: dict, swim_tpl: dict) -> dict:
    s = v2.build_soil(node, ssurgo)
    th = next(c for c in s["Children"] if "Physical" in c["$type"])["Thickness"]
    for c in s["Children"]:
        t = c["$type"]
        if "Organic" in t:
            if "FBiom" in case:
                c["FBiom"] = [round(x * case["FBiom"], 4) for x in c["FBiom"]]
            if "FInert" in case:
                c["FInert"] = [round(min(0.99, x * case["FInert"]), 4) for x in c["FInert"]]
        if t.startswith("Models.Soils.Solute,") and c["Name"] in ("NO3", "NH4") and "initN" in case:
            c["InitialValues"] = [round(x * case["initN"], 4) for x in c["InitialValues"]]
    if case.get("swim"):
        i = next(k for k, c in enumerate(s["Children"]) if "WaterBalance" in c["$type"])
        wb = s["Children"][i]
        sw = copy.deepcopy(swim_tpl)
        sol = sw.pop("_solutes")
        for c in s["Children"]:
            if c["$type"].startswith("Models.Soils.Solute,") and c["Name"] in sol:
                p = sol[c["Name"]]
                c.update({"D0": p["D0"], "Exco": [p["Exco"]] * len(th), "FIP": [p["FIP"]] * len(th)})
        sw.update({"Name": "SoilWater", "Salb": wb["Salb"], "CN2Bare": wb["CN2Bare"], "CNRed": wb["CNRed"], "CNCov": wb["CNCov"]})
        sw["Children"] = []
        if case.get("tile"):
            dr = next(c for c in swim_tpl["Children"] if "SwimSubsurfaceDrain" in c["$type"])
            dr = copy.deepcopy(dr)
            top, klat = 0.0, None
            hz = v2.layers(ssurgo["horizons"])[1]
            for t, h in zip(th, hz, strict=False):
                if top <= TILE["DrainDepth"] < top + t:
                    klat = round(float(h["ksat_r"]) * 86.4, 2)
                top += t
            dr.update({**TILE, "Klat": klat})
            sw["Children"] = [dr]
        s["Children"][i] = sw
        # SWIM solves Richards' equation on the soil nodes; the tutorial uses a fine LayerStructure. Map the
        # SSURGO layers onto 100 mm nodes (numerical resolution only; no soil property is changed).
        n = round(sum(th) / LAYER_MM)
        assert abs(n * LAYER_MM - sum(th)) < 1e-6
        s["Children"].append({"$type": "Models.Soils.LayerStructure, Models", "Thickness": [LAYER_MM] * n,
                              "Name": "LayerStructure", "ResourceName": None, "Children": [], "Enabled": True, "ReadOnly": False})
    return s


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if v1.APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    soils = {"webster": json.loads((v2.SITE / "ssurgo_point_AN_v1.json").read_text(encoding="utf-8")),
             "clarion": json.loads(CLARION.read_text(encoding="utf-8"))}
    met = v2.OUT / "boone_ia_nasa_power_1991_2020_AN_v1.met"
    example_path = apsim / "Examples" / "Maize.apsimx"
    example = json.loads(example_path.read_text(encoding="utf-8"))
    swim_tpl = find_swim(apsim)
    seep_tpl = find_seepage(apsim)
    OUT.mkdir(parents=True)
    runs = {}
    with tempfile.TemporaryDirectory() as td:
        for cname, case in CASES.items():
            for amount in (100.0, 0.0):
                site = cname if amount else cname + "_0N"
                m = v1.build(example, apsim, site, "AU_Dalby.met", amount)
                next(v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
                next(v1._find(m, "Models.Clock,")).update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
                for p in next(v1._find(m, "Models.Manager,", "Sow using a variable rule"))["Parameters"]:
                    p["Value"] = v2.SOW.get(p["Key"], p["Value"])
                zone = next(v1._find(m, "Models.Core.Zone,"))
                i = next(k for k, c in enumerate(zone["Children"]) if c["$type"].startswith("Models.Soils.Soil,"))
                zone["Children"][i] = soil_for(case, zone["Children"][i], soils[case["soil"]], swim_tpl)
                if case.get("seepage"):
                    zone["Children"].append(copy.deepcopy(seep_tpl))
                if case.get("watertable_mm"):
                    mg = copy.deepcopy(seep_tpl)
                    mg["Parameters"] = [{"Key": "LowerBCType", "Value": "potential"},
                                        {"Key": "LowerBCValue", "Value": str(PROFILE_MM - case["watertable_mm"])}]
                    zone["Children"].append(mg)
                if case.get("swim"):
                    daily = next(c for c in zone["Children"] if c.get("Name") == "Daily")
                    daily["VariableNames"] = list(daily["VariableNames"]) + ["[SoilWater].SubsurfaceDrain as TileDrain_mm", "[SoilWater].WaterTable as WaterTable_mm"]
                name = f"crop_urea_lime_{site}_AN_v3"
                sim = Path(td) / f"{name}.apsimx"
                sim.write_text(json.dumps(m, indent=1), encoding="utf-8")
                r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
                if r.returncode != 0:
                    raise SystemExit(f"APSIM failed for {site}:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
                txt = json.loads(sim.read_text(encoding="utf-8"))
                next(v1._find(txt, "Models.Climate.Weather,"))["FileName"] = met.name
                (OUT / f"{name}.apsimx").write_text(json.dumps(txt, indent=1) + "\n", encoding="utf-8")
                for kind in ("Daily", "Report"):
                    with (Path(td) / f"{name}.{kind}.csv").open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                        shutil.copyfileobj(fi, fo)
                runs[site] = {"case": cname, **{k: v for k, v in case.items()}, "urea_N_kg_ha": amount}
                print("done", site, flush=True)
    manifest = {
        "apsim": {"version": ver, "commit": v1.APSIM_COMMIT, "models_dll_sha256": v1.sha256(models)},
        "main_run": "results/apsim_AN_v2 (Webster, SoilWater; unchanged)",
        "weather": "results/apsim_AN_v2/boone_ia_nasa_power_1991_2020_AN_v1.met",
        "swim_template": "Examples/Tutorials/SWIM.apsimx, HowToAddTileDrainage (Swim3 + SwimSubsurfaceDrain)",
        "tile": {**TILE, "source": TILE_SOURCE, "Klat": "SSURGO ksat_r of the horizon at drain depth x 86.4 (mm/d)",
                 "ImpermDepth_basis": "bottom of SSURGO profile; no corestrictions record"},
        "clarion": {k: soils["clarion"]["dominant"][k] for k in ("areasymbol", "saverest", "mukey", "muname", "muacres", "cokey", "compname", "comppct_r", "taxclname", "drainagecl", "hydgrp")},
        "borrowed_sensitivity": "one at a time on Webster: initial NO3+NH4 x0.5, x2; FBiom x0.5, x1.5; FInert x0.75, x1.25 (cap 0.99)",
        "runs": runs,
        "outputs_sha256": {p.name: v1.sha256(p) for p in sorted(OUT.iterdir())},
    }
    (OUT / "apsim_crop_manifest_AN_v3.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()