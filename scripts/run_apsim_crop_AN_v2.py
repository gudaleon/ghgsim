"""APSIM crop run on a documented US Corn Belt site (AN_v2), DECISIONS_AN_v24. Consistency check, not validation.

Site 42.020 N, 93.774 W, Boone County, Iowa (data/apsim_site_iowa_AN_v1, from scripts/fetch_iowa_site_AN_v1.py).
- Soil, from SSURGO (dominant component Webster, map unit 2835012), direct field mapping only:
  BD = dbthirdbar_r; DUL = wthirdbar_r/100; LL15 = wfifteenbar_r/100; SAT = wsatiated_r/100 (all volumetric);
  KS = ksat_r um/s x 86.4 (mm/d); Carbon = om_r / 1.724 (van Bemmelen factor, as used by NRCS);
  pH = ph1to1h2o_r; particle sizes = clay/silt/sandtotal_r. Horizons over 400 mm are split into equal
  layers with the horizon's values. AirDry = LL15 and maize LL = LL15 (APSIM convention when no
  measured crop lower limit exists).
- Parameters SSURGO does not provide are NOT invented: KL, XF, FBiom, FInert, SoilCNRatio, FOM, FOMCNRatio,
  SWCON, CN2Bare and initial NO3/NH4 are taken from APSoil No. 900 in APSIM's Examples/Maize.apsimx,
  matched by layer mid-depth, and listed in the manifest as borrowed.
- Weather: NASA POWER daily (MERRA-2 / CERES), 1991-2020, written as an APSIM .met; tav and amp from
  the monthly means of the same record.
- Management: the example's own rules, except sowing window 19-Apr to 26-May (USDA NASS 2010, Iowa
  corn usual planting begin and end) and cultivar B_110 (an APSIM maize cultivar, 110-day relative
  maturity); urea 100 kg N/ha at sowing, plus a 0 N control.
Usage: python scripts/run_apsim_crop_AN_v2.py  (env GHGSIM_APSIM_DIR, GHGSIM_DOTNET). Writes results/apsim_AN_v2/.
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
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_apsim_crop_AN_v1 as v1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "apsim_site_iowa_AN_v1"
OUT = ROOT / "results" / "apsim_AN_v2"
RUNS = {"iowa": 100.0, "iowa_0N": 0.0}
SOW = {"StartDate": "19-apr", "EndDate": "26-may", "CultivarName": "B_110"}
EX_BOUNDS = [150, 300, 600, 900, 1200, 1500, 1800]


def layers(hz):
    th, rows = [], []
    for h in hz:
        t = (float(h["hzdepb_r"]) - float(h["hzdept_r"])) * 10.0
        n = max(1, int(-(-t // 400)))
        parts = [round(t / n)] * n
        parts[-1] = t - sum(parts[:-1])
        th += parts
        rows += [h] * n
    return th, rows


def ex_index(th):
    out, top = [], 0.0
    for t in th:
        mid = top + t / 2
        out.append(next((i for i, b in enumerate(EX_BOUNDS) if mid <= b), len(EX_BOUNDS) - 1))
        top += t
    return out


def build_soil(soil_node: dict, ssurgo: dict) -> dict:
    s = copy.deepcopy(soil_node)
    th, hz = layers(ssurgo["horizons"])
    ix = ex_index(th)
    f = lambda k, sc=1.0: [round(float(h[k]) * sc, 4) for h in hz]  # noqa: E731
    pick = lambda arr: [arr[i] for i in ix]  # noqa: E731
    d = ssurgo["dominant"]
    s.update({"RecordNumber": 0, "ASCOrder": None, "ASCSubOrder": None, "SoilType": d["muname"],
              "LocalName": d["compname"], "Site": d["areaname"], "NearestTown": None, "Region": "US Corn Belt",
              "State": "Iowa", "Country": "USA", "NaturalVegetation": None, "ApsoilNumber": None,
              "Latitude": ssurgo["point_wgs84"][0], "Longitude": ssurgo["point_wgs84"][1], "LocationAccuracy": None,
              "YearOfSampling": None,
              "DataSource": f"USDA-NRCS SSURGO via Soil Data Access, survey {d['areasymbol']} (saverest {d['saverest']}), "
                            f"mukey {d['mukey']}, cokey {d['cokey']} ({d['compname']} {d['comppct_r']}%)",
              "Comments": "Physical, carbon and pH from SSURGO; KL, XF, FBiom, FInert, SoilCNRatio, FOM, SWCON, CN2Bare "
                          "and initial NO3/NH4 borrowed from APSoil No. 900 (APSIM Examples/Maize.apsimx)"})
    for c in s["Children"]:
        t = c["$type"]
        if "Physical" in t:
            ll = f("wfifteenbar_r", 0.01)
            c.update({"Thickness": th, "BD": f("dbthirdbar_r"), "LL15": ll, "AirDry": ll, "DUL": f("wthirdbar_r", 0.01),
                      "SAT": f("wsatiated_r", 0.01), "KS": f("ksat_r", 86.4), "ParticleSizeClay": f("claytotal_r"),
                      "ParticleSizeSilt": f("silttotal_r"), "ParticleSizeSand": f("sandtotal_r")})
            for sc in c["Children"]:
                sc.update({"LL": ll, "KL": pick(sc["KL"]), "XF": pick(sc["XF"])})
        elif "WaterBalance" in t:
            c.update({"Thickness": th, "SWCON": pick(c["SWCON"]), "SummerDate": "1-Apr", "WinterDate": "1-Nov"})
        elif "Organic" in t:
            c.update({"Thickness": th, "Carbon": f("om_r", 1 / 1.724), "SoilCNRatio": pick(c["SoilCNRatio"]),
                      "FBiom": pick(c["FBiom"]), "FInert": pick(c["FInert"]), "FOM": pick(c["FOM"])})
        elif "Chemical" in t:
            c.update({"Thickness": th, "PH": f("ph1to1h2o_r")})
        elif t.startswith("Models.Soils.Water,"):
            c.update({"Thickness": th, "InitialValues": f("wthirdbar_r", 0.01)})
            c.pop("InitialPAWmm", None)
        elif t.startswith("Models.Soils.Solute,"):
            c.update({"Thickness": th, "InitialValues": pick(c["InitialValues"])})
    return s


def write_met(power: dict, path: Path, lat: float, lon: float) -> dict:
    p = power["properties"]["parameter"]
    days = sorted(p["T2M_MAX"])
    mon = defaultdict(list)
    for k in days:
        mon[int(k[4:6])].append((p["T2M_MAX"][k] + p["T2M_MIN"][k]) / 2)
    mm = [sum(v) / len(v) for _, v in sorted(mon.items())]
    tav, amp = sum(mm) / 12, max(mm) - min(mm)
    lines = ["[weather.met.weatherdata]", "! NASA POWER daily API v2, community AG; " + power["header"]["api"]["version"],
             f"latitude = {lat:.3f} (DECIMAL DEGREES)", f"longitude = {lon:.3f} (DECIMAL DEGREES)",
             f"tav = {tav:.2f} (oC) ! annual average ambient temperature",
             f"amp = {amp:.2f} (oC) ! annual amplitude in mean monthly temperature",
             "year day radn maxt mint rain", "() () (MJ/m^2) (oC) (oC) (mm)"]
    for k in days:
        dd = date(int(k[:4]), int(k[4:6]), int(k[6:]))
        doy = (dd - date(dd.year, 1, 1) + timedelta(days=1)).days
        lines.append(f"{dd.year} {doy} {p['ALLSKY_SFC_SW_DWN'][k]:.2f} {p['T2M_MAX'][k]:.2f} {p['T2M_MIN'][k]:.2f} {p['PRECTOTCORR'][k]:.2f}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return {"tav": round(tav, 2), "amp": round(amp, 2), "days": len(days)}


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    models = apsim / "bin" / "Models.dll"
    ver = subprocess.run([dotnet, str(models), "--version"], capture_output=True, text=True).stdout.strip()
    if v1.APSIM_VERSION not in ver:
        raise SystemExit(f"unexpected APSIM version {ver!r}")
    ssurgo = json.loads((SITE / "ssurgo_point_AN_v1.json").read_text(encoding="utf-8"))
    with gzip.open(SITE / "nasa_power_daily_1991_2020_AN_v1.json.gz", "rt", encoding="utf-8") as fh:
        power = json.load(fh)
    example_path = apsim / "Examples" / "Maize.apsimx"
    example = json.loads(example_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True)
    met = OUT / "boone_ia_nasa_power_1991_2020_AN_v1.met"
    metinfo = write_met(power, met, *ssurgo["point_wgs84"])
    files = {}
    with tempfile.TemporaryDirectory() as td:
        for site, amount in RUNS.items():
            m = v1.build(example, apsim, site, "AU_Dalby.met", amount)
            next(v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
            clock = next(v1._find(m, "Models.Clock,"))
            clock.update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
            for p in next(v1._find(m, "Models.Manager,", "Sow using a variable rule"))["Parameters"]:
                p["Value"] = SOW.get(p["Key"], p["Value"])
            zone = next(v1._find(m, "Models.Core.Zone,"))
            i = next(k for k, c in enumerate(zone["Children"]) if c["$type"].startswith("Models.Soils.Soil,"))
            zone["Children"][i] = build_soil(zone["Children"][i], ssurgo)
            name = f"crop_urea_lime_{site}_AN_v2"
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
            files[site] = {"urea_N_kg_ha": amount}
    manifest = {
        "apsim": {"version": ver, "commit": v1.APSIM_COMMIT, "pr": v1.APSIM_PR, "models_dll_sha256": v1.sha256(models)},
        "example": {"file": "Examples/Maize.apsimx", "sha256": v1.sha256(example_path)},
        "site": {"point_wgs84": ssurgo["point_wgs84"], "soil": {k: ssurgo["dominant"][k] for k in ("areaname", "areasymbol", "saverest", "mukey", "muname", "cokey", "compname", "comppct_r", "taxclname", "drainagecl", "hydgrp")},
                 "soil_source": "USDA-NRCS Soil Survey Staff, SSURGO, via Soil Data Access", "weather_source": "NASA POWER daily API " + power["header"]["api"]["version"], "met": metinfo},
        "borrowed_from_APSoil_900": ["KL", "XF", "FBiom", "FInert", "SoilCNRatio", "FOM", "FOMCNRatio", "SWCON", "CN2Bare", "initial NO3", "initial NH4"],
        "management": {**SOW, "planting_source": "USDA NASS (2010) Field Crops Usual Planting and Harvesting Dates, Agricultural Handbook 628, Iowa corn for grain"},
        "runs": files,
        "outputs_sha256": {p.name: v1.sha256(p) for p in sorted(OUT.iterdir())},
    }
    (OUT / "apsim_crop_manifest_AN_v2.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(metinfo))


if __name__ == "__main__":
    main()
