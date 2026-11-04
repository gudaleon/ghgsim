"""Holos (stock, public inputs, run by the collaborating project) vs APSIM v3 Lake Erie direct fertiliser N2O EF (AN_v3).

EF = 2 x (mean annual N2O-N at 172 N - at 0 N) / 172 x 100 over 1991-2020 (N on maize every other year), the same
definition as the Holos EF_direct_rotation column. APSIM split by maize-year and soybean-year share of the extra N2O.
Only APSIM runs completing 1991-2020 are used. Holos CSV read only from D:/holos_lakeerie_AN_v1/results_AN_v1.
Writes results/holos_vs_apsim_lake_erie_AN_v3.csv (refuses to overwrite). Consistency check, not validation.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOLOS = Path("D:/holos_lakeerie_AN_v1/results_AN_v1/holos_lakeerie_ef_summary_AN_v1.csv")
OUT = ROOT / "results" / "holos_vs_apsim_lake_erie_AN_v3.csv"
MODES = ["", "pond_", "eo1440_", "pond_eo1440_"]


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    holos = {r["site"]: r for r in csv.DictReader(HOLOS.open(encoding="utf-8"))}
    out = []
    for mode in MODES:
        f = ROOT / "results" / f"apsim_lake_erie_{mode}annual_AN_v3.csv"
        ann = list(csv.DictReader(f.open(encoding="utf-8")))
        runs = {}
        for a in ann:
            runs.setdefault((a["site"], a["case"], float(a["corn_N"])), []).append(a)
        for (site, case, n), ys in runs.items():
            if n == 0 or len(ys) != 30 or (site, case, 0.0) not in runs or len(runs[(site, case, 0.0)]) != 30:
                continue
            zero = {a["year"]: float(a["N2O_N_kg_ha"]) for a in runs[(site, case, 0.0)]}
            d = {a["year"]: float(a["N2O_N_kg_ha"]) - zero[a["year"]] for a in ys}
            crop = {a["year"]: a["crop"] for a in ys}
            tot = sum(d.values())
            soy = sum(v for y, v in d.items() if crop[y] == "soybean")
            h = holos.get(site, {})
            out.append({"mode": mode.rstrip("_") or "cn_eo720", "site": site, "case": case,
                        "apsim_EF_pct": round(2 * tot / 30 / 172 * 100, 3),
                        "apsim_EF_maize_year_only_pct": round(2 * (tot - soy) / 30 / 172 * 100, 3),
                        "soybean_year_share_of_extra_N2O": round(soy / tot, 3) if tot else None,
                        "holos_EF_direct_pct": h.get("EF_direct_rotation_pct"), "holos_EF_corn_year_only_pct": h.get("EF_direct_corn_year_only_pct"),
                        "apsim_v2_EF_pct_from_holos_file": h.get("APSIM_v2_EF_pct")})
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for o in out:
        print(o)


if __name__ == "__main__":
    main()