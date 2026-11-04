"""Compare APSIM on the Iowa SSURGO / NASA POWER site with ghgsim 2006/2019 and HESTIA (AN_v2, DECISIONS_AN_v24).

Consistency check, not validation. Reads results/apsim_AN_v2/ (Boone County, Iowa, 1991-2020, calendar
years, sowing in spring). Annual means and the fertiliser-induced EF use the years in which APSIM sowed
the crop (the sowing rule found no suitable day in 2000, so that year had no crop and no fertiliser);
pulse statistics use the full daily record. The Australian/NZ-weather runs (AN_v1) are carried over
unchanged as a sensitivity case. ghgsim and HESTIA terms come from compare_apsim_crop_AN_v1.

Writes (refuses to overwrite): results/apsim_crop_annual_AN_v2.csv, results/apsim_crop_pulses_AN_v2.csv,
results/apsim_vs_ghgsim_hestia_crop_AN_v2.csv
"""
from __future__ import annotations

import csv
import gzip
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_apsim_crop_AN_v1 as c1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "results" / "apsim_AN_v2"
F_ANN = ROOT / "results" / "apsim_crop_annual_AN_v2.csv"
F_PUL = ROOT / "results" / "apsim_crop_pulses_AN_v2.csv"
F_CMP = ROOT / "results" / "apsim_vs_ghgsim_hestia_crop_AN_v2.csv"
V1 = ROOT / "results" / "apsim_vs_ghgsim_hestia_crop_AN_v1.csv"
YEARS = range(1991, 2021)


def load(site: str, kind: str) -> list[dict]:
    with gzip.open(A / f"crop_urea_lime_{site}_AN_v2.{kind}.csv.gz", "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def daily(site: str) -> list[dict]:
    rows = load(site, "Daily")
    for r in rows:
        r["ay"] = int(r["Clock.Today"][:4])
        for k in list(r):
            if k.endswith("_kgha") or k == "Weather.Rain":
                r[k] = float(r[k])
    return [r for r in rows if r["ay"] in YEARS]


def main() -> None:
    sites = ("iowa", "iowa_0N")
    d = {s: daily(s) for s in sites}
    ann = {s: c1.annual(d[s]) for s in sites}
    sown = sorted({int(r["Clock.Today"][:4]) for r in load("iowa", "Report")})
    yld = {int(r["Clock.Today"][:4]): float(r["Yield"]) for r in load("iowa", "Report")}
    arow = [{"run": s, "year": y, "crop_sown": y in sown, **{k: c1.r4(v) for k, v in a.items()},
             "grain_yield_kg_ha": c1.r4(yld.get(y, math.nan)) if s == "iowa" else ""} for s in sites for y, a in sorted(ann[s].items())]
    prow = [{"run": s, **{k: c1.r4(v) if isinstance(v, float) else v for k, v in c1.pulses(d[s]).items()},
             "rain_event_mm": c1.RAIN_EVENT_MM, "window_days": c1.WINDOW_DAYS} for s in sites]
    with V1.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if r["model"].startswith("APSIM"):
            r["basis"] = "sensitivity: APSoil 900, " + r["basis"]
    f = [ann["iowa"][y]["N2O_N"] for y in sown]
    c = [ann["iowa_0N"][y]["N2O_N"] for y in sown]
    mf = sum(f) / len(f)
    rows.append({"farm_id": c1.FARM, "model": "APSIM NG 2026.11.8142.0",
                 "basis": "main: Boone County IA, SSURGO Webster + NASA POWER 1991-2020",
                 "direct_N2O_kg_ha": c1.r4(mf * c1.N2O_PER_N), "total_N2O_kg_ha": "nan",
                 "direct_N2O_kg_ha_min_year": c1.r4(min(f) * c1.N2O_PER_N), "direct_N2O_kg_ha_max_year": c1.r4(max(f) * c1.N2O_PER_N),
                 "fertiliser_induced_EF_pct": c1.r4(mf - sum(c) / len(c)),
                 "note": f"direct N2O only; mean of {len(sown)} sown calendar years 1991-2020; EF = (100 kg N/ha run - 0 N control) / 100"})
    c1.write(F_ANN, arow)
    c1.write(F_PUL, prow)
    c1.write(F_CMP, rows)
    print(rows[-1])
    for r in prow:
        print(r)
    print("sown", len(sown), "mean yield", round(sum(yld.values()) / len(yld)), "rain", round(sum(ann["iowa"][y]["Rain"] for y in YEARS) / 30),
          "N2", round(sum(ann["iowa"][y]["N2_N"] for y in sown) / len(sown), 2), "leach", round(sum(ann["iowa"][y]["LeachNO3"] for y in sown) / len(sown), 2),
          "minN", round(sum(ann["iowa"][y]["MinN"] for y in sown) / len(sown), 1))


if __name__ == "__main__":
    main()
