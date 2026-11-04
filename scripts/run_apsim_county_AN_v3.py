"""Ontario county APSIM reruns with cited Ontario planting dates (AN_v3), FINDINGS_AN_v4.

v2 gave Ontario units the Michigan NASS window (1-may to 27-may) and the APSIM Maize example sowing rule
(MinESW 100 mm, MinRain 25 mm in 7 days, written for Dalby, Queensland). Diagnosis: the CanSIS 1 m profiles hold
less plant-available water than 100 mm at DUL (e.g. Essex Brookston: 0.20*250 + 0.05*400 + 0.02*350 = 77 mm), so the
rule could almost never fire (Essex sowed in 2 of 30 years). Changes, each from a cited source, no tuning:
- Start date: OMAFRA Agronomy Guide for Field Crops, Publication 811 (2022), Ch. 1 Corn, Planting: "plant as soil
  moisture conditions permit after April 26 in areas receiving greater than 3,000 CHU-M1 or May 1 in areas
  <3,000 CHU-M1". End date 15-may: same section, best yields from corn planted "in late April and the first half
  of May"; Table 1-10 indexes yield to planting before May 10.
- CHU class per unit from NASA POWER 1991-2020: CHU-M1 accumulated from May 1 (Pub. 811: "CHU-M1 because of the
  May 1 start date"; season end "when average temperature falls below 12 C or the first occurrence of -2 C",
  applied after July 31 with daily mean < 12 C read as a 7-day running mean, flagged), daily CHU =
  (Ymax + Ymin)/2, Ymax = 3.33(Tmax-10) - 0.084(Tmax-10)^2, Ymin = 1.8(Tmin-4.44) (Brown and Bootsma 1993, the
  basis of Pub. 811 Table 10-4), negative terms set to 0. Mean over 1991-2020 against the 3,000 threshold.
- Two variants: "rule" keeps the example MinESW/MinRain (date effect only); "omafra" sets MinESW = 0 and
  MinRain = 0, so the crop is sown on the OMAFRA start date (Pub. 811 gives a calendar/soil-fitness criterion, no
  stored-water criterion).
Everything else as run_apsim_county_AN_v2. Usage: python scripts/run_apsim_county_AN_v3.py. Resumable.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_apsim_county_AN_v2 as r2  # noqa: E402

ROOT = r2.ROOT
OUT = ROOT / "results" / "apsim_county_AN_v3"
VARIANTS = {"rule": {}, "omafra": {"MinESW": "0.0", "MinRain": "0.0"}}
END = "15-may"


def chu_m1(power: dict) -> dict[int, float]:
    par = power["properties"]["parameter"]
    tx, tn = par["T2M_MAX"], par["T2M_MIN"]
    out = {}
    for y in range(1991, 2021):
        tot, run = 0.0, []
        d = date(y, 5, 1)
        while d.year == y and d.month < 12:
            k = d.strftime("%Y%m%d")
            mx, mn = tx[k], tn[k]
            run = (run + [(mx + mn) / 2])[-7:]
            if d >= date(y, 8, 1) and (mn <= -2.0 or (len(run) == 7 and sum(run) / 7 < 12.0)):
                break
            ymax = max(0.0, 3.33 * (mx - 10) - 0.084 * (mx - 10) ** 2) if mx > 10 else 0.0
            ymin = max(0.0, 1.8 * (mn - 4.44))
            tot += (ymax + ymin) / 2
            d = date.fromordinal(d.toordinal() + 1)
        out[y] = round(tot, 1)
    return out


def main() -> None:
    apsim = Path(os.environ["GHGSIM_APSIM_DIR"])
    dotnet = os.environ.get("GHGSIM_DOTNET") or shutil.which("dotnet")
    models = apsim / "bin" / "Models.dll"
    example = json.loads((apsim / "Examples" / "Maize.apsimx").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=os.environ.get("GHGSIM_TMP")) as td:
        for u in [x for x in r2.units() if x["country"] == "CA"]:
            if (OUT / f"county_{u['id']}_run_AN_v3.json").exists():
                continue
            soil = u["soil"]()
            with gzip.open(u["power"](), "rt", encoding="utf-8") as fh:
                power, fills = r2.pf.fill_power(json.load(fh))
            chu = chu_m1(power)
            mean_chu = sum(chu.values()) / len(chu)
            start = "26-apr" if mean_chu > 3000 else "1-may"
            met = Path(td) / f"{u['id']}.met"
            metinfo = r2.v2.write_met(power, met, *soil["point_wgs84"])
            info = {"id": u["id"], "country": "CA", "chu_m1_mean_1991_2020": round(mean_chu, 1), "chu_m1_by_year": chu,
                    "sowing_window": {"StartDate": start, "EndDate": END}, "met": metinfo, "filled_missing": fills,
                    "soil": {k: soil["dominant"].get(k) for k in ("areaname", "mukey", "compname", "comppct_r", "drainagecl")}}
            for var, extra in VARIANTS.items():
                for tag, amount in r2.RUNS.items():
                    name = f"county_{u['id']}_{var}_{tag}_AN_v3"
                    m = r2.v1.build(example, apsim, tag, "AU_Dalby.met", amount)
                    next(r2.v1._find(m, "Models.Climate.Weather,"))["FileName"] = str(met)
                    next(r2.v1._find(m, "Models.Clock,")).update({"Start": "1991-01-01T00:00:00", "End": "2020-12-31T00:00:00"})
                    sw = {**r2.v2.SOW, "StartDate": start, "EndDate": END, **extra}
                    for p in next(r2.v1._find(m, "Models.Manager,", "Sow using a variable rule"))["Parameters"]:
                        p["Value"] = sw.get(p["Key"], p["Value"])
                    zone = next(r2.v1._find(m, "Models.Core.Zone,"))
                    i = next(q for q, ch in enumerate(zone["Children"]) if ch["$type"].startswith("Models.Soils.Soil,"))
                    zone["Children"][i] = r2.v2.build_soil(zone["Children"][i], soil)
                    info["sat_caps"] = r2.cap_sat(zone["Children"][i])
                    sim = Path(td) / f"{name}.apsimx"
                    sim.write_text(json.dumps(m), encoding="utf-8")
                    shutil.copyfile(sim, OUT / sim.name)
                    r = subprocess.run([dotnet, str(models), str(sim), "--csv"], capture_output=True, text=True)
                    if r.returncode != 0:
                        info.setdefault("failed", {})[f"{var}_{tag}"] = next((ln.strip() for ln in r.stdout.splitlines() if "Exception" in ln), r.stdout[-300:])
                        continue
                    for kind in ("Daily", "Report"):
                        src = Path(td) / f"{name}.{kind}.csv"
                        if not src.exists():
                            info.setdefault("missing_output", []).append(f"{var}_{tag}.{kind}")
                            continue
                        with src.open("rb") as fi, gzip.GzipFile(OUT / f"{name}.{kind}.csv.gz", "wb", mtime=0) as fo:
                            shutil.copyfileobj(fi, fo)
            (OUT / f"county_{u['id']}_run_AN_v3.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
            print("failed" if "failed" in info else "done", u["id"], start, round(mean_chu), flush=True)


if __name__ == "__main__":
    main()