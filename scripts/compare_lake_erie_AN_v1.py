"""Annual and pulse summary of the Lake Erie drained vs undrained APSIM SWIM runs (AN_v1), FINDINGS_AN_v1.

One row per case and calendar year 1991-2020: direct N2O-N, denitrification N2-N, NO3-N leached at the profile
base (APSIM LeachNO3; SWIM does not report the NO3 carried by the tile drains separately in this version, so
tile NO3 is not given), tile drain flow, base drainage, rain, and mean / minimum water-table depth (mm; profile
depth 1450 means no saturated zone). Plus a per-case mean row with pulse statistics. Consistency check, not
validation. Writes (refuses to overwrite) results/apsim_lake_erie_annual_AN_v1.csv and _summary_AN_v1.csv.
"""
from __future__ import annotations

import csv
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_apsim_crop_AN_v1 as c1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "apsim_lake_erie_AN_v1"
OUT_A = ROOT / "results" / "apsim_lake_erie_annual_AN_v1.csv"
OUT_S = ROOT / "results" / "apsim_lake_erie_summary_AN_v1.csv"
CASES = ("erie_undrained", "erie_tile_1956", "erie_tile_lt")
COLS = {"N2O_N_kgha": "N2O_N_kg_ha", "N2_N_kgha": "N2_N_kg_ha", "LeachNO3_kgha": "NO3_N_leached_base_kg_ha",
        "TileDrain_mm": "tile_flow_mm", "Drain_mm": "base_drainage_mm", "Weather.Rain": "rain_mm"}


def main() -> None:
    for o in (OUT_A, OUT_S):
        if o.exists():
            raise SystemExit(f"refusing to overwrite {o}")
    annual, summ = [], []
    for case in CASES:
        with gzip.open(RES / f"lake_erie_{case}_AN_v1.Daily.csv.gz", "rt", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            r["ay"] = int(r["Clock.Today"][:4])
            for k in list(r):
                if k.endswith(("_kgha", "_mm")) or k == "Weather.Rain":
                    r[k] = float(r[k] or 0.0)
        years = sorted({r["ay"] for r in rows})
        for y in years:
            d = [r for r in rows if r["ay"] == y]
            a = {"case": case, "year": y, **{v: sum(r[k] for r in d) for k, v in COLS.items()}}
            a["N2O_kg_ha"] = a["N2O_N_kg_ha"] * c1.N2O_PER_N
            a["water_table_mean_mm"] = sum(r["WaterTable_mm"] for r in d) / len(d)
            a["water_table_min_mm"] = min(r["WaterTable_mm"] for r in d)
            annual.append(a)
        ys = [a for a in annual if a["case"] == case]
        m = {"case": case, "years": len(ys), **{k: sum(a[k] for a in ys) / len(ys) for k in ys[0] if k not in ("case", "year")}}
        m.update(c1.pulses(rows))
        summ.append(m)
    for out, data in ((OUT_A, annual), (OUT_S, summ)):
        keys = list(data[0])
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in data)


if __name__ == "__main__":
    main()