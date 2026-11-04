"""Summarise the APSIM soil, drainage and borrowed-parameter sensitivity runs at the Iowa site (AN_v3).

Consistency check, not validation (DECISIONS_AN_v25). Reads results/apsim_AN_v3/ and, as the reference row,
the main Webster run in results/apsim_AN_v2/. For each case: mean direct N2O over the years in which APSIM
sowed the crop, the single-year range, the fertiliser-induced EF against the case's own 0 N control, the pulse
statistics of compare_apsim_crop_AN_v1, and annual means of N2, NO3 leaching, drainage, tile drainage and
grain yield.

Writes (refuses to overwrite): results/apsim_crop_sensitivity_AN_v3.csv
"""
from __future__ import annotations

import csv
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_apsim_crop_AN_v1 as c1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
A2 = ROOT / "results" / "apsim_AN_v2"
A3 = ROOT / "results" / "apsim_AN_v3"
OUT = ROOT / "results" / "apsim_crop_sensitivity_AN_v3.csv"
YEARS = range(1991, 2021)
CASES = {
    "main_webster": (A2, "iowa", "main: Webster, APSIM SoilWater, APSoil 900 organic parameters"),
    "webster_swim": (A3, "webster_swim", "Webster, SWIM3, free (unit-gradient) base, no drains"),
    "webster_seep": (A3, "webster_seep", "Webster, SWIM3, seepage base, no drains"),
    "webster_tile": (A3, "webster_tile", "Webster, SWIM3, seepage base, tile drains 1.2 m depth / 28.5 m spacing"),
    "webster_wt": (A3, "webster_wt", "Webster, SWIM3, undrained, fixed water table 660 mm (SSURGO)"),
    "clarion": (A3, "clarion", "Clarion (well drained), APSIM SoilWater"),
    "initN_x0.5": (A3, "initN_x0.5", "Webster, initial NO3/NH4 x0.5"),
    "initN_x2": (A3, "initN_x2", "Webster, initial NO3/NH4 x2"),
    "FBiom_x0.5": (A3, "FBiom_x0.5", "Webster, FBiom x0.5"),
    "FBiom_x1.5": (A3, "FBiom_x1.5", "Webster, FBiom x1.5"),
    "FInert_x0.75": (A3, "FInert_x0.75", "Webster, FInert x0.75"),
    "FInert_x1.25": (A3, "FInert_x1.25", "Webster, FInert x1.25 (cap 0.99)"),
}


def load(d: Path, tag: str, kind: str) -> list[dict]:
    v = "AN_v2" if d == A2 else "AN_v3"
    with gzip.open(d / f"crop_urea_lime_{tag}_{v}.{kind}.csv.gz", "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def daily(d: Path, tag: str) -> list[dict]:
    rows = load(d, tag, "Daily")
    for r in rows:
        r["ay"] = int(r["Clock.Today"][:4])
        for k in list(r):
            if k.endswith(("_kgha", "_mm")) or k == "Weather.Rain":
                r[k] = float(r[k] or 0.0)
    return [r for r in rows if r["ay"] in YEARS]


def summarise(d: Path, tag: str) -> dict:
    f, c = daily(d, tag), daily(d, tag + "_0N")
    rep = load(d, tag, "Report")
    sown = sorted({int(r["Clock.Today"][:4]) for r in rep})
    af, ac = c1.annual(f), c1.annual(c)
    nf = [af[y]["N2O_N"] for y in sown]
    nc = [ac[y]["N2O_N"] for y in sown]
    mf = sum(nf) / len(nf)

    def yr(k):
        return sum(r.get(k, 0.0) for r in f if r["ay"] in sown) / len(sown)

    p = c1.pulses(f)
    return {
        "sown_years": len(sown),
        "direct_N2O_kg_ha": mf * c1.N2O_PER_N,
        "direct_N2O_kg_ha_min_year": min(nf) * c1.N2O_PER_N,
        "direct_N2O_kg_ha_max_year": max(nf) * c1.N2O_PER_N,
        "fertiliser_induced_EF_pct": mf - sum(nc) / len(nc),
        "control_N2O_kg_ha": sum(nc) / len(nc) * c1.N2O_PER_N,
        "share_top5pct_days": p["share_top5pct_days"],
        "max_day_over_mean_day": p["max_day_over_mean_day"],
        "share_N2O_within_window_after_rain": p["share_N2O_within_window_after_rain"],
        "N2_N_kg_ha": yr("N2_N_kgha"),
        "leach_NO3_N_kg_ha": yr("LeachNO3_kgha"),
        "drainage_mm": yr("Drain_mm"),
        "tile_drainage_mm": yr("TileDrain_mm") if "TileDrain_mm" in f[0] else "",
        "grain_yield_kg_ha": sum(float(r["Yield"]) for r in rep) / len(rep),
    }


def main() -> None:
    rows = []
    for name, (d, tag, basis) in CASES.items():
        s = summarise(d, tag)
        rows.append({"case": name, "basis": basis, **{k: c1.r4(v) if isinstance(v, float) else v for k, v in s.items()}})
    c1.write(OUT, rows)
    for r in rows:
        print(r["case"], r["direct_N2O_kg_ha"], r["fertiliser_induced_EF_pct"], r["tile_drainage_mm"], r["drainage_mm"])


if __name__ == "__main__":
    main()