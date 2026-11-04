"""Matched-period drained vs undrained totals for Lake Erie v3 runs that failed part-way (AN_v3), FINDINGS_AN_v4.

When an undrained run stops early (SWIM no solution), the drained runs of the same site, N rate and output mode are
cut to the same last day, and totals over 1991-01-01..last day are compared. Consistency check, not validation.
Writes results/apsim_lake_erie_matched_AN_v3.csv (refuses to overwrite).
"""
from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "apsim_lake_erie_matched_AN_v3.csv"
MODES = ["apsim_lake_erie_AN_v3", "apsim_lake_erie_pond_AN_v3", "apsim_lake_erie_eo1440_AN_v3", "apsim_lake_erie_pond_eo1440_AN_v3"]
K = {"N2O_N_kgha": "N2O_N_kg_ha", "N2_N_kgha": "N2_N_kg_ha", "TileDrain_mm": "tile_flow_mm", "TileNO3_kgha": "tile_NO3_N_kg_ha",
     "SwimLeachNO3_kgha": "leached_NO3_N_kg_ha", "Drain_mm": "base_drainage_mm"}


def rows(res: Path, run: str) -> list[dict]:
    with gzip.open(res / f"lake_erie_{run}_AN_v3.Daily.csv.gz", "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    out = []
    for mode in MODES:
        res = ROOT / "results" / mode
        if not (res / "apsim_lake_erie_manifest_AN_v3.json").exists():
            continue
        runs = json.loads((res / "apsim_lake_erie_manifest_AN_v3.json").read_text(encoding="utf-8"))["runs"]
        for run, info in runs.items():
            if info["case"] != "undrained" or "failed" not in info:
                continue
            u = rows(res, run)
            if len(u) < 366:
                continue
            last = u[-2]["Clock.Today"]  # last complete day
            for other, oi in runs.items():
                if oi["site"] != info["site"] or oi["corn_urea_N_kg_ha"] != info["corn_urea_N_kg_ha"]:
                    continue
                d = [r for r in rows(res, other) if r["Clock.Today"] <= last]
                if d[-1]["Clock.Today"] != last:
                    continue
                o = {"mode": mode, "site": oi["site"], "case": oi["case"], "corn_N": oi["corn_urea_N_kg_ha"], "end": last[:10], "days": len(d)}
                o.update({v: round(sum(float(r[k] or 0) for r in d), 4) for k, v in K.items()})
                ja = [float(r["WaterTable_mm"]) for r in d if int(r["Clock.Today"][5:7]) <= 4]
                o["wt_janapr_mean_cm"] = round(sum(ja) / len(ja) / 10, 2)
                out.append(o)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for o in out:
        print(o)


if __name__ == "__main__":
    main()