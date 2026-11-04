"""Ontario county comparison with cited planting dates (AN_v3), FINDINGS_AN_v4. Consistency check, not validation.

Same per-unit metrics as compare_county_AN_v2 (APSIM fertiliser-induced EF at 100 kg N/ha vs 0 N over sown years,
Holos-style base EF from May-Oct P/PE), for the two v3 sowing variants of run_apsim_county_AN_v3 ("rule": OMAFRA
dates with the example MinESW/MinRain rule; "omafra": OMAFRA dates, sown on the start date), next to v2.
Outputs (refuse to overwrite): results/apsim_ontario_summary_AN_v3.csv, results/apsim_ontario_metrics_AN_v3.json
"""
from __future__ import annotations

import csv
import gzip
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_county_AN_v2 as k2  # noqa: E402
import run_apsim_county_AN_v2 as r2  # noqa: E402

ROOT = r2.ROOT
RES = ROOT / "results" / "apsim_county_AN_v3"
OUT = ROOT / "results" / "apsim_ontario_summary_AN_v3.csv"
MET = ROOT / "results" / "apsim_ontario_metrics_AN_v3.json"


def daily(name: str) -> list[dict]:
    with gzip.open(RES / f"{name}.Daily.csv.gz", "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["ay"] = int(r["Clock.Today"][:4])
        for k in list(r):
            if k.endswith(("_kgha", "_mm")) or k == "Weather.Rain":
                r[k] = float(r[k] or 0.0)
    return [r for r in rows if r["ay"] in k2.p1.YEARS]


def unit(uid: str, var: str) -> dict:
    f, c = f"county_{uid}_{var}_100N_AN_v3", f"county_{uid}_{var}_0N_AN_v3"
    if not (RES / f"{f}.Report.csv.gz").exists() or not (RES / f"{c}.Daily.csv.gz").exists():
        return {f"{var}_sown_years": 0}
    with gzip.open(RES / f"{f}.Report.csv.gz", "rt", encoding="utf-8") as fh:
        sown = sorted({int(r["Clock.Today"][:4]) for r in csv.DictReader(fh)})
    af, ac = k2.c1.annual(daily(f)), k2.c1.annual(daily(c))
    mf = sum(af[y]["N2O_N"] for y in sown) / len(sown)
    mc = sum(ac[y]["N2O_N"] for y in sown) / len(sown)
    return {f"{var}_sown_years": len(sown), f"{var}_apsim_N2O_kg_ha": mf * k2.c1.N2O_PER_N, f"{var}_apsim_EF_pct": mf - mc}


def main() -> None:
    for o in (OUT, MET):
        if o.exists():
            raise SystemExit(f"refusing to overwrite {o}")
    with (ROOT / "results" / "apsim_county_summary_AN_v2.csv").open(encoding="utf-8") as fh:
        v2 = {r["id"]: r for r in csv.DictReader(fh)}
    rows = []
    for u in [x for x in r2.units() if x["country"] == "CA"]:
        info = json.loads((RES / f"county_{u['id']}_run_AN_v3.json").read_text(encoding="utf-8"))
        c = u["row"]
        with gzip.open(u["power"](), "rt", encoding="utf-8") as fh:
            power, _ = k2.pf.fill_power(json.load(fh))
        p_mm, pe_mm = k2.hargreaves_may_oct(power, c["point_wgs84"][0])
        r = {"id": u["id"], "county": c["municipality"], "soil": c["soilname"], "drainage": c["drainage"],
             "chu_m1_mean": info["chu_m1_mean_1991_2020"], "start_date": info["sowing_window"]["StartDate"],
             "failed": ";".join(info.get("failed", {})), "holos_base_EF_pct": 100 * k2.p1.holos_base_ef(p_mm, pe_mm),
             "v2_sown_years": int(v2.get(u["id"], {}).get("sown_years") or 0),
             "v2_apsim_EF_pct": float(v2[u["id"]]["apsim_EF_pct"]) if v2.get(u["id"], {}).get("apsim_EF_pct") else None}
        for var in ("rule", "omafra"):
            r.update(unit(u["id"], var))
        rows.append(r)
    met = {"n_units": len(rows)}
    for var in ("v2", "rule", "omafra"):
        ok = [r for r in rows if r.get(f"{var}_sown_years", 0) >= 5]
        met[var] = {"n_ge5_sown": len(ok), "mean_sown_years": float(np.mean([r.get(f"{var}_sown_years", 0) for r in rows])),
                    "mean_apsim_EF_pct": float(np.mean([r[f"{var}_apsim_EF_pct"] for r in ok])) if ok else None,
                    "mean_holos_base_EF_pct_same_units": float(np.mean([r["holos_base_EF_pct"] for r in ok])) if ok else None,
                    "spearman_apsim_vs_holos": k2.p1.spearman([r[f"{var}_apsim_EF_pct"] for r in ok], [r["holos_base_EF_pct"] for r in ok]) if len(ok) > 2 else None}
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)
    MET.write_text(json.dumps(met, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(met, indent=1))


if __name__ == "__main__":
    main()