"""Lake Erie tile-drainage experiment v2: Essex County (Windsor area, ON) vs Maumee basin (Wood County, OH) (AN_v2).

Consistency/process experiment, not validation (FINDINGS_AN_v2).
Soils (no parameter invented; see the fetch scripts for mapping):
- essex_brookston: CanSIS ONBKN~~~~~A (Brookston, poorly drained, Orthic Humic Gleysol on clay-loam till), the
  dominant soil of Essex County by area in SLC v3.2 (41.7 % of the area-weighted SLC components in the county
  polygon; data/ontario_soils_AN_v1/cansis_essex_composition_AN_v1.json), 0-100 cm, CanSIS modal values.
- essex_berrien: CanSIS ONBRR~~~~~A (Berrien, imperfectly drained, sandy loam to sand over clay at 44 cm), the
  second soil by area (11.6 %), the lighter contrast. Both use NASA POWER at the representative point of SLC
  polygon 570007 (Brookston 80 %, Berrien 10 %), 42.16 N 82.78 W.
- maumee_hoytville: SSURGO Hoytville clay loam 0-1 % (OH173 Wood County, the county's dominant component,
  210,816 component-acres), as in AN_v1 (densic Cd replaced by a seepage base at 1450 mm), NASA POWER 41.22 N 83.76 W.
Water: SWIM3 (tutorial settings), APSIM's documented seepage lower boundary at the profile base (CanSIS
profiles end at 100 cm; nothing extrapolated), so a perched water table can form; drains via SwimSubsurfaceDrain.
Drain geometry: tile_1956 = 0.76 m deep, 12.2 m spacing (OSU Hoytville 1956 study) at every site; tile_lt =
1.2 m, 17 m (OSU long-term tillage, Dick et al. 1986) at Hoytville only (deeper than the CanSIS profiles).
SWIM PSIDul = -330 cm (DUL defined at 33 kPa in both sources). NASA POWER -999 flags are
filled by linear interpolation (power_fill_AN_v1). Klat = Ksat of the layer at drain depth x 86.4 (mm/d); ImpermDepth = profile base; DrainRadius 150 mm.
Rotation corn-soybean (corn in odd years, soybean in even years), APSIM example sowing rule with windows from
USDA NASS (2010) Agricultural Handbook 628 "most active" dates: Ohio corn 24-Apr..24-May, soybean 3-May..30-May;
Michigan (nearest NASS state, proxy for Essex) corn 1-May..27-May, soybean 11-May..9-Jun. Maize B_110;
soybean Generic_MG3 (assumption: maturity group typical of 41-42 N; flagged). Corn N: 172 kg N/ha urea at
sowing (OMAFRA Pub 811 worksheet, corn after soybean, clay soil; yield 170 bu/ac, 3400 CHU and the price ratio are
assumptions, flagged) and a 0 N control; soybean 0 N. Clock 1991-2020.
Writes D:/APSIM/lake_erie_drainage_AN_v2 style outputs to results/apsim_lake_erie_AN_v2/ (refuses to overwrite);
failed runs keep their partial Daily CSV for diagnosis.
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
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f1  # noqa: E402
import power_fill_AN_v1 as pf  # noqa: E402
import run_apsim_crop_AN_v1 as v1  # noqa: E402
import run_apsim_crop_AN_v2 as v2  # noqa: E402
import run_apsim_crop_AN_v3 as v3  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "apsim_site_lake_erie_AN_v2"
OUT = ROOT / "results" / "apsim_lake_erie_AN_v2"
CORN_N = 172.0
TILE_1956 = {"DrainDepth": 760.0, "DrainSpacing": 12200.0}
TILE_LT = {"DrainDepth": 1200.0, "DrainSpacing": 17000.0}
WINDOWS = {"OH": {"Maize": ("24-apr", "24-may"), "Soybean": ("3-may", "30-may")},
           "MI": {"Maize": ("1-may", "27-may"), "Soybean": ("11-may", "9-jun")}}
EXTRA = ["[SoilWater].SubsurfaceDrain as TileDrain_mm", "[SoilWater].WaterTable as WaterTable_mm",
         "[SoilWater].SubsurfaceDrainNO3 as TileNO3_kgha", "[SoilWater].LeachNO3 as SwimLeachNO3_kgha",
         "[Soybean].Grain.Wt*10 as SoyGrain_kgha", "[Soybean].AboveGround.N*10 as SoyAbovegroundN_kgha"]


def sites() -> dict:
    ont = json.loads((ROOT / "data/ontario_soils_AN_v1/cansis_essex_sites_AN_v1.json").read_text(encoding="utf-8"))
    hoyt = json.loads((ROOT / "data/apsim_site_lake_erie_AN_v1/ssurgo_hoytville_AN_v1.json").read_text(encoding="utf-8"))
    assert hoyt["horizons"][-1]["hzname"] == "Cd"
    hoyt["horizons"] = hoyt["horizons"][:-1]
    for k in ("ONBKN~~~~~A", "ONBRR~~~~~A"):
        o = ont[k]
        o["dominant"] = {"muname": o["soilname"].title(), "compname": o["soilname"].title(), "areaname": "Essex County, Ontario",
                         "areasymbol": f"SLC v3.2 polygon {o['slc_poly_id']}", "saverest": "CanSIS soil layer table v2r20140203",
                         "mukey": k, "cokey": k, "comppct_r": o["component_percent"]}
    return {"essex_brookston": {"soil": ont["ONBKN~~~~~A"], "state": "MI", "layer": 100.0, "tiles": {"tile_1956": TILE_1956}},
            "essex_berrien": {"soil": ont["ONBRR~~~~~A"], "state": "MI", "layer": 100.0, "tiles": {"tile_1956": TILE_1956}},
            "maumee_hoytville": {"soil": hoyt, "state": "OH", "layer": 145.0, "tiles": {"tile_1956": TILE_1956, "tile_lt": TILE_LT},
                                 "power": ROOT / "data/apsim_site_lake_erie_AN_v1/nasa_power_daily_1991_2020_AN_v1.json.gz"}}


def power_for(lat: float, lon: float) -> Path:
    p = DATA / f"nasa_power_daily_1991_2020_{lat:.4f}_{lon:.4f}_AN_v2.json.gz"
    if not p.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        url = f1.POWER.replace(f"longitude={f1.LON}&latitude={f1.LAT}", f"longitude={lon}&latitude={lat}")
        raw = urllib.request.urlopen(url, timeout=300).read()
        with gzip.GzipFile(p, "wb", mtime=0) as fo:
            fo.write(raw)
    return p


def sow_manager(tpl: dict, crop: str, window: tuple, parity: int, cultivar: str, pop: str, depth: str) -> dict:
    m = copy.deepcopy(tpl)
    m["Name"] = f"Sow {crop}"
    key = "if (DateUtilities.WithinDates(StartDate, Clock.Today, EndDate) &&"
    code = m["CodeArray"]
    i = next(k for k, ln in enumerate(code) if ln.strip() == key)
    code[i] = code[i].replace("if (", f"if (Clock.Today.Year % 2 == {parity} && ", 1)
    vals = {"Crop": crop, "StartDate": window[0], "EndDate": window[1], "CultivarName": cultivar, "Population": pop, "SowingDepth": depth}
    for p in m["Parameters"]:
        p["Value"] = vals.get(p["Key"], p["Value"])
    return m


def build(apsim: Path, maize_ex: dict, soy_ex: dict, site: dict, tile: dict | None, amount: float, met: Path, swim_tpl, seep_tpl) -> dict:
    m = v1.build(maize_ex, apsim, "x", "AU_Dalby.met", amount)
    next(v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
    next(v1._find(m, "Models.Clock,")).update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
    zone = next(v1._find(m, "Models.Core.Zone,"))
    soy_zone = next(v1._find(soy_ex, "Models.Core.Zone,"))
    soy = copy.deepcopy(next(c for c in soy_zone["Children"] if c.get("Name") == "Soybean"))
    w = WINDOWS[site["state"]]
    old = next(c for c in zone["Children"] if c.get("Name") == "Sow using a variable rule")
    pos = zone["Children"].index(old)
    zone["Children"][pos] = sow_manager(old, "Maize", w["Maize"], 1, v2.SOW["CultivarName"], "6.0", "30.0")
    soy_sow = next(c for c in soy_zone["Children"] if c.get("Name") == "Sow using a variable rule")
    sp = {p["Key"]: p["Value"] for p in soy_sow["Parameters"]}
    zone["Children"].insert(pos + 1, sow_manager(soy_sow, "Soybean", w["Soybean"], 0, "Generic_MG3", sp["Population"], sp["SowingDepth"]))
    hv = copy.deepcopy(next(c for c in zone["Children"] if c.get("Name") == "Harvest"))
    hv["Name"] = "Harvest Soybean"
    for p in hv["Parameters"]:
        p["Value"] = "Soybean"
    zone["Children"].insert(pos + 2, hv)
    maize = next(c for c in zone["Children"] if c.get("Name") == "Maize")
    zone["Children"].insert(zone["Children"].index(maize) + 1, soy)
    v3.TILE.update({"ImpermDepth": sum(float(h["hzdepb_r"]) - float(h["hzdept_r"]) for h in site["soil"]["horizons"]) * 10.0 + float(site["soil"]["horizons"][0]["hzdept_r"]) * 10.0,
                    "DrainRadius": 150.0, **(tile or {})})
    v3.LAYER_MM = site["layer"]
    i = next(k for k, c in enumerate(zone["Children"]) if c["$type"].startswith("Models.Soils.Soil,"))
    zone["Children"][i] = v3.soil_for({"swim": True, "tile": tile is not None}, zone["Children"][i], site["soil"], swim_tpl)
    phys = next(c for c in zone["Children"][i]["Children"] if "Physical" in c["$type"])
    mz = next(c for c in phys["Children"] if c.get("Name") == "MaizeSoil")
    sy = copy.deepcopy(mz)
    sy["Name"] = "SoybeanSoil"  # assumption (flagged): soybean uses the maize LL/KL/XF of the same soil
    phys["Children"].append(sy)
    # APSIM rejects SAT above the total porosity implied by BD (1 - BD/2.65). Where the CanSIS modal KP0 exceeds it,
    # SAT is set to that physical limit (floored to 0.001) and the change is recorded; no other value is altered.
    caps = []
    for k, (sat, bd) in enumerate(zip(phys["SAT"], phys["BD"], strict=True)):
        lim = int((1 - bd / 2.65) * 1000) / 1000
        if sat > lim:
            caps.append({"node": k, "SAT_from_source": sat, "SAT_used": lim, "BD": bd})
            phys["SAT"][k] = lim
    m["_sat_caps"] = caps
    if site["state"] == "MI":
        zone["Children"][i].update({"Region": "Essex County", "State": "Ontario", "Country": "Canada",
                                    "DataSource": "AAFC CanSIS soil layer table (Ontario v2r20140203, modal values) for "
                                    f"{site['soil']['soil_id']}, located with SLC v3.2 polygon {site['soil']['slc_poly_id']}",
                                    "Comments": "Physical, carbon and pH from CanSIS; other fields borrowed from APSoil No. 900 as for the US runs"})
    zone["Children"].append(copy.deepcopy(seep_tpl))
    daily = next(c for c in zone["Children"] if c.get("Name") == "Daily")
    daily["VariableNames"] = list(daily["VariableNames"]) + EXTRA
    return m


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if v1.APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    maize_ex = json.loads((apsim / "Examples" / "Maize.apsimx").read_text(encoding="utf-8"))
    soy_ex = json.loads((apsim / "Examples" / "Soybean.apsimx").read_text(encoding="utf-8"))
    swim_tpl, seep_tpl = v3.find_swim(apsim), v3.find_seepage(apsim)
    # DUL in both sources is the water content at 33 kPa (CanSIS KP33, SSURGO wthirdbar_r), i.e. a matric head of
    # -330 cm; the tutorial's PSIDul (-100 cm) is set to match the definition of the data (tested: with -100 cm SWIM
    # fails to converge on the Brookston profile within 66 days). No other SWIM setting is changed.
    swim_tpl["PSIDul"] = -330.0
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True)
    runs, mets = {}, {}
    with tempfile.TemporaryDirectory() as td:
        for sname, site in sites().items():
            lat, lon = site["soil"]["point_wgs84"]
            pp = site.get("power") or power_for(lat, lon)
            with gzip.open(pp, "rt", encoding="utf-8") as fh:
                power, fills = pf.fill_power(json.load(fh))
            met = Path(td) / f"{sname}.met"
            mets[sname] = {**v2.write_met(power, met, lat, lon), "power_file": str(pp.relative_to(ROOT)), "filled_missing": fills}
            for cname, tile in {"undrained": None, **site["tiles"]}.items():
                for amount in (CORN_N, 0.0):
                    run = f"{sname}_{cname}" + ("" if amount else "_0N")
                    if only and run not in only:
                        continue
                    name = f"lake_erie_{run}_AN_v2"
                    m = build(apsim, maize_ex, soy_ex, site, tile, amount, met, swim_tpl, seep_tpl)
                    sim = Path(td) / f"{name}.apsimx"
                    caps = m.pop("_sat_caps")
                    sim.write_text(json.dumps(m, indent=1), encoding="utf-8")
                    r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
                    info = {"site": sname, "case": cname, "corn_urea_N_kg_ha": amount, "tile": dict(v3.TILE) if tile else None, "sat_caps": caps}
                    txt = json.loads(sim.read_text(encoding="utf-8"))
                    next(v1._find(txt, "Models.Climate.Weather,"))["FileName"] = met.name
                    (OUT / f"{name}.apsimx").write_text(json.dumps(txt, indent=1) + "\n", encoding="utf-8")
                    for kind in ("Daily", "Report"):
                        src = Path(td) / f"{name}.{kind}.csv"
                        if src.exists():
                            with src.open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                                shutil.copyfileobj(fi, fo)
                    if r.returncode != 0:
                        err = next((ln for ln in r.stdout.splitlines() if "System.Exception" in ln), r.stdout[-300:])
                        info["failed"] = err.strip()
                    runs[run] = info
                    print("failed" if r.returncode else "done", run, info.get("failed", ""), flush=True)
    man = {"apsim": {"version": ver, "commit": v1.APSIM_COMMIT, "models_dll_sha256": v1.sha256(models)},
           "sites": {k: {kk: vv for kk, vv in s["soil"].items() if kk != "horizons"} | {"horizons": s["soil"]["horizons"]} for k, s in sites().items()},
           "met": mets, "runs": runs, "windows_NASS_2010": WINDOWS, "corn_N": CORN_N,
           "outputs_sha256": {p.name: v1.sha256(p) for p in sorted(OUT.iterdir())}}
    (OUT / "apsim_lake_erie_manifest_AN_v2.json").write_text(json.dumps(man, indent=1, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()