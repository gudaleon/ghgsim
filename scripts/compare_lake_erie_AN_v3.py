"""Annual and pulse summary of the Lake Erie v3 runs (AN_v3), FINDINGS_AN_v4. Consistency check, not validation.

One row per run and calendar year 1991-2020: direct N2O-N and N2O, denitrification N2-N, NO3-N in tile drain
flow (SWIM SubsurfaceDrainNO3), NO3-N leached at the profile base (SWIM LeachNO3), tile drain flow, base drainage,
rain, mean / minimum water-table depth (mm; equal to the profile depth means no saturated zone), crop (maize in
odd years, soybean in even). Plus one mean row per run with pulse statistics. Failed runs are listed with the
day they stopped. v3 adds the Jan-Apr mean and minimum water-table depth (cm) next to the SSURGO wet-month top
(Hoytville 15 cm Jan-Apr; Brookston, MI115 proxy, 0 cm Dec-May), a consistency check only. Arguments --pond / --eo1440 read the
ponding-surface runs. Writes results/apsim_lake_erie[_pond]_annual_AN_v3.csv and _summary_AN_v3.csv (no overwrite).
"""
from __future__ import annotations

import csv
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_apsim_crop_AN_v1 as c1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAG = ("pond_" if "--pond" in sys.argv else "") + ("eo1440_" if "--eo1440" in sys.argv else "")
RES = ROOT / "results" / f"apsim_lake_erie_{TAG}AN_v3"
SSURGO_WET_TOP_CM = {"maumee_hoytville": 15.0, "essex_brookston": 0.0}
OUT_A = ROOT / "results" / f"apsim_lake_erie_{TAG}annual_AN_v3.csv"
OUT_S = ROOT / "results" / f"apsim_lake_erie_{TAG}summary_AN_v3.csv"
COLS = {"N2O_N_kgha": "N2O_N_kg_ha", "N2_N_kgha": "denitrification_N2_N_kg_ha", "TileNO3_kgha": "NO3_N_tile_kg_ha",
        "SwimLeachNO3_kgha": "NO3_N_leached_base_kg_ha", "TileDrain_mm": "tile_flow_mm", "Drain_mm": "base_drainage_mm",
        "Weather.Rain": "rain_mm"}


def main() -> None:
    for o in (OUT_A, OUT_S):
        if o.exists():
            raise SystemExit(f"refusing to overwrite {o}")
    man = json.loads((RES / "apsim_lake_erie_manifest_AN_v3.json").read_text(encoding="utf-8"))
    annual, summ = [], []
    for run, info in man["runs"].items():
        with gzip.open(RES / f"lake_erie_{run}_AN_v3.Daily.csv.gz", "rt", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            r["ay"] = int(r["Clock.Today"][:4])
            for k in list(r):
                if k.endswith(("_kgha", "_mm", "_gm2")) or k == "Weather.Rain":
                    r[k] = float(r[k] or 0.0)
        if "failed" in info:
            summ.append({"run": run, "site": info["site"], "case": info["case"], "corn_N": info["corn_urea_N_kg_ha"],
                         "failed": info["failed"], "last_day": rows[-1]["Clock.Today"] if rows else None,
                         "tile_flow_mm_to_failure": sum(r["TileDrain_mm"] for r in rows),
                         "wt_min_cm_to_failure": min(r["WaterTable_mm"] for r in rows) / 10 if rows else None,
                         "wt_janapr_mean_cm_to_failure": (lambda ja: sum(ja) / len(ja) / 10 if ja else None)([r["WaterTable_mm"] for r in rows if int(r["Clock.Today"][5:7]) <= 4]),
                         "ssurgo_wet_top_cm": SSURGO_WET_TOP_CM.get(info["site"])})
            continue
        ys = []
        for y in sorted({r["ay"] for r in rows}):
            d = [r for r in rows if r["ay"] == y]
            a = {"run": run, "site": info["site"], "case": info["case"], "corn_N": info["corn_urea_N_kg_ha"], "year": y,
                 "crop": "maize" if y % 2 else "soybean", **{v: sum(r[k] for r in d) for k, v in COLS.items()}}
            a["N2O_kg_ha"] = a["N2O_N_kg_ha"] * c1.N2O_PER_N
            a["water_table_mean_mm"] = sum(r["WaterTable_mm"] for r in d) / len(d)
            a["water_table_min_mm"] = min(r["WaterTable_mm"] for r in d)
            ys.append(a)
        annual += ys
        num = [k for k in ys[0] if k not in ("run", "site", "case", "corn_N", "year", "crop")]
        s = {"run": run, "site": info["site"], "case": info["case"], "corn_N": info["corn_urea_N_kg_ha"], "years": len(ys),
             **{k: sum(a[k] for a in ys) / len(ys) for k in num}}
        for crop in ("maize", "soybean"):
            cy = [a for a in ys if a["crop"] == crop]
            s[f"N2O_N_{crop}_years"] = sum(a["N2O_N_kg_ha"] for a in cy) / len(cy)
        ja = [r["WaterTable_mm"] for r in rows if int(r["Clock.Today"][5:7]) <= 4]
        s["wt_janapr_mean_cm"] = sum(ja) / len(ja) / 10
        s["wt_janapr_min_cm"] = min(ja) / 10
        s["ssurgo_wet_top_cm"] = SSURGO_WET_TOP_CM.get(info["site"])
        s.update(c1.pulses(rows))
        summ.append(s)
    keys_s = list(dict.fromkeys(k for r in summ for k in r))
    for out, data, keys in ((OUT_A, annual, list(annual[0])), (OUT_S, summ, keys_s)):
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in data)


if __name__ == "__main__":
    main()