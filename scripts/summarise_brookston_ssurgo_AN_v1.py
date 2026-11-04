"""Summary of the SSURGO densic Brookston runs (AN_v1), FINDINGS_AN_v7. Consistency check, not validation.

Reuses compare_lake_erie_AN_v3 (read only) with the result folder and output names pointed at
results/apsim_brookston_ssurgo_[pond_][eo1440_]AN_v1. SSURGO wet-month top from the cosoilmoist rows in
data/apsim_site_lake_erie_AN_v3/ssurgo_brookston_densic_AN_v1.json. Adds EF and soybean-year share per tile case.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_lake_erie_AN_v3 as le  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAG = le.TAG
le.RES = ROOT / "results" / f"apsim_brookston_ssurgo_{TAG}AN_v1"
le.OUT_A = ROOT / "results" / f"apsim_brookston_ssurgo_{TAG}annual_AN_v1.csv"
le.OUT_S = ROOT / "results" / f"apsim_brookston_ssurgo_{TAG}summary_AN_v1.csv"
OUT_EF = ROOT / "results" / f"apsim_brookston_ssurgo_{TAG}ef_AN_v1.json"
J = json.loads((ROOT / "data" / "apsim_site_lake_erie_AN_v3" / "ssurgo_brookston_densic_AN_v1.json").read_text(encoding="utf-8"))
wet = [float(r["soimoistdept_r"]) for r in J.get("cosoilmoist", []) if r.get("soimoiststat") == "Wet" and r.get("soimoistdept_r") not in (None, "")]
le.SSURGO_WET_TOP_CM = {"essex_brookston_ssurgo": min(wet) if wet else None}


def main() -> None:
    if OUT_EF.exists():
        raise SystemExit(f"refusing to overwrite {OUT_EF}")
    le.main()
    rows = list(csv.DictReader(le.OUT_S.open(encoding="utf-8")))
    by = {(r["case"].replace("_0N", ""), float(r["corn_N"])): r for r in rows if not r.get("failed")}
    out = {"wet_months": sorted({r["month"] for r in J.get("cosoilmoist", []) if r.get("soimoiststat") == "Wet"}), "cases": {}}
    for case in sorted({k[0] for k in by}):
        f, z = by.get((case, 172.0)), by.get((case, 0.0))
        if not (f and z):
            continue
        g = lambda r, k: float(r[k])  # noqa: E731
        dm, ds = g(f, "N2O_N_maize_years") - g(z, "N2O_N_maize_years"), g(f, "N2O_N_soybean_years") - g(z, "N2O_N_soybean_years")
        d = g(f, "N2O_N_kg_ha") - g(z, "N2O_N_kg_ha")
        out["cases"][case] = {"EF_pct": 2 * d / 172 * 100, "EF_maize_years_only_pct": dm / 172 * 100,
                              "soybean_year_share": ds / (dm + ds) if dm + ds else None,
                              **{f"{k}_{n}": g(r, k) for n, r in (("172N", f), ("0N", z)) for k in
                                 ("N2O_N_kg_ha", "denitrification_N2_N_kg_ha", "tile_flow_mm", "NO3_N_tile_kg_ha",
                                  "base_drainage_mm", "NO3_N_leached_base_kg_ha", "wt_janapr_mean_cm", "wt_janapr_min_cm")}}
    OUT_EF.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()