"""Compare APSIM daily N2O on crop_urea_lime with ghgsim IPCC 2006/2019 and HESTIA (AN_v1, DECISIONS_AN_v23).

Consistency check, not validation. Reads the committed APSIM outputs (results/apsim_AN_v1/), runs ghgsim's
own soil modules on the crop_urea_lime field exactly as compare_ipcc_2006_2019_stylized_AN_v3 does (term by
term), and reads HESTIA's matched run (data/hestia_matched_emissions_raw_AN_v3.csv). All values per ha
(the farm is 10 ha). APSIM agricultural year = 1 Jul..30 Jun (southern-hemisphere sites, sowing Nov),
1990/91..1999/2000 (10 crops). APSIM reports direct N2O only (nitrification + denitrification); it
has no NH3 volatilisation, so it is compared with the direct terms. ghgsim/HESTIA inputs include
residue and SOM N; APSIM simulates its own residue and mineralisation, so scopes differ.

Writes (refuses to overwrite):
  results/apsim_crop_annual_AN_v1.csv     per run x year N flows
  results/apsim_crop_pulses_AN_v1.csv     daily-pulse statistics per run
  results/apsim_vs_ghgsim_hestia_crop_AN_v1.csv   per-ha comparison table
"""
from __future__ import annotations

import csv
import gzip
import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
A = ROOT / "results" / "apsim_AN_v1"
F_ANN = ROOT / "results" / "apsim_crop_annual_AN_v1.csv"
F_PUL = ROOT / "results" / "apsim_crop_pulses_AN_v1.csv"
F_CMP = ROOT / "results" / "apsim_vs_ghgsim_hestia_crop_AN_v1.csv"
HESTIA = ROOT / "data" / "hestia_matched_emissions_raw_AN_v3.csv"
FARM = "crop_urea_lime"
AREA_HA = 10.0
N2O_PER_N = 44.0 / 28.0
YEARS = range(1990, 2000)
RAIN_EVENT_MM = 20.0
WINDOW_DAYS = 3


def load_daily(site: str) -> list[dict]:
    with gzip.open(A / f"crop_urea_lime_{site}_AN_v1.Daily.csv.gz", "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        y, m, _d = (int(x) for x in r["Clock.Today"][:10].split("-"))
        r["ay"] = y if m >= 7 else y - 1
        for k in list(r):
            if k.endswith("_kgha") or k in ("Weather.Rain",):
                r[k] = float(r[k])
    return [r for r in rows if r["ay"] in YEARS]


def annual(rows):
    out = {}
    for r in rows:
        d = out.setdefault(r["ay"], {"N2O_N": 0.0, "N2_N": 0.0, "MinN": 0.0, "LeachNO3": 0.0, "Rain": 0.0})
        d["N2O_N"] += r["N2O_N_kgha"]
        d["N2_N"] += r["N2_N_kgha"]
        d["MinN"] += r["MinN_kgha"]
        d["LeachNO3"] += r["LeachNO3_kgha"]
        d["Rain"] += r["Weather.Rain"]
    return out


def pulses(rows):
    n = [r["N2O_N_kgha"] for r in rows]
    tot = sum(n)
    srt = sorted(n, reverse=True)
    k = max(1, round(0.05 * len(n)))
    after = set()
    for i, r in enumerate(rows):
        if r["Weather.Rain"] >= RAIN_EVENT_MM:
            after.update(range(i, min(len(rows), i + WINDOW_DAYS + 1)))
    mean_day = tot / len(n)
    return {
        "days": len(n),
        "total_N2O_N_kgha": tot,
        "share_top5pct_days": sum(srt[:k]) / tot,
        "max_day_N2O_N_kgha": srt[0],
        "max_day_over_mean_day": srt[0] / mean_day,
        "share_days": len(after) / len(n),
        "share_N2O_within_window_after_rain": sum(n[i] for i in after) / tot,
    }


def ghgsim_terms() -> dict[str, dict[str, float]]:
    s = importlib.util.spec_from_file_location("cmp3", ROOT / "scripts" / "compare_ipcc_2006_2019_stylized_AN_v2.py")
    cmp = importlib.util.module_from_spec(s)
    s.loader.exec_module(cmp)
    from ghgsim.core.registry import load_parameter_csv
    from ghgsim.report.emissions_sankey import _const, load_stylized_spec

    spec = load_stylized_spec(cmp.SPEC)
    reg = load_parameter_csv(cmp.latest_versioned(ROOT / "data", "ipcc_params", ".csv"), allow_unverified=False)
    farm = next(f for f in spec["farms"] if f["id"] == FARM)
    out = {}
    for ver in ("IPCC2006", "IPCC2019"):
        soil_m = cmp.MODULES[ver][2]
        cap = {}
        orig = soil_m.compute

        def wrap(inputs, params, _o=orig, cap=cap):
            r = _o(inputs, params)
            cap.update({"in": dict(inputs), "out": dict(r)})
            return r

        soil_m.compute = wrap
        try:
            cmp.run_version(ver, spec, farm, reg, _const(spec))
        finally:
            soil_m.compute = orig
        o, i = cap["out"], cap["in"]
        out[ver] = {
            "N2O_direct": float(o["N2O_direct"]),
            "N2O_indirect": float(o["N2O_indirect_vol"]) + float(o["N2O_indirect_leach"]),
            "N2O_total": float(o["N2O_total"]),
            "N_inputs": sum(float(i[k]) for k in ("F_SN", "F_ON", "F_CR", "F_SOM", "F_PRP_CPP")),
            "F_SN": float(i["F_SN"]),
        }
    return out


def hestia_terms() -> dict[str, float]:
    d = {"direct": 0.0, "indirect": 0.0}
    with HESTIA.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = r["hestia_term"]
            if r["farm_id"] != FARM or not t.startswith("n2OToAir") or "Burning" in t:
                continue
            v = float(r["value_kg"] or 0)
            d["direct" if t.endswith("Direct") else "indirect"] += v
    return d


def write(path, rows):
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def r4(x):
    return round(x, 4) if isinstance(x, float) and not math.isnan(x) else x


def main() -> None:
    sites = ("dalby", "dalby_0N", "hamilton", "hamilton_0N")
    daily = {s: load_daily(s) for s in sites}
    ann = {s: annual(daily[s]) for s in sites}
    arow = [{"run": s, "ag_year": f"{y}/{y + 1}", **{k: r4(v) for k, v in d.items()}} for s in sites for y, d in sorted(ann[s].items())]
    prow = [{"run": s, **{k: r4(v) if isinstance(v, float) else v for k, v in pulses(daily[s]).items()},
             "rain_event_mm": RAIN_EVENT_MM, "window_days": WINDOW_DAYS} for s in sites]
    g = ghgsim_terms()
    h = hestia_terms()
    rows = []

    def add(model, basis, direct_n2o_ha, total_n2o_ha, lo=math.nan, hi=math.nan, ef=math.nan, note=""):
        rows.append({"farm_id": FARM, "model": model, "basis": basis,
                     "direct_N2O_kg_ha": r4(direct_n2o_ha), "total_N2O_kg_ha": r4(total_n2o_ha),
                     "direct_N2O_kg_ha_min_year": r4(lo), "direct_N2O_kg_ha_max_year": r4(hi),
                     "fertiliser_induced_EF_pct": r4(ef), "note": note or "consistency check, not validation"})

    for ver, lab in (("IPCC2006", "ghgsim IPCC 2006"), ("IPCC2019", "ghgsim IPCC 2019")):
        t = g[ver]
        add(lab, "Tier 1 annual EF, wet climate", t["N2O_direct"] / AREA_HA, t["N2O_total"] / AREA_HA,
            note=f"N inputs {t['N_inputs'] / AREA_HA:.1f} kg N/ha (synthetic {t['F_SN'] / AREA_HA:.0f}, residue, SOM)")
    add("HESTIA CE 7.1.0 (models 0.90.0)", "IPCC 2019 Tier 1 as implemented in HESTIA", h["direct"] / AREA_HA,
        (h["direct"] + h["indirect"]) / AREA_HA)
    for s, lab in (("dalby", "Dalby weather (example as shipped)"), ("hamilton", "Hamilton weather (warm temperate moist)")):
        f = [ann[s][y]["N2O_N"] for y in YEARS]
        c = [ann[s + "_0N"][y]["N2O_N"] for y in YEARS]
        mean_f = sum(f) / len(f)
        ef = (mean_f - sum(c) / len(c)) / 100.0 * 100.0
        add(f"APSIM {APSIM_LABEL}", lab, mean_f * N2O_PER_N, math.nan, min(f) * N2O_PER_N, max(f) * N2O_PER_N, ef,
            "daily process model; direct N2O only; 10-crop mean (Jul-Jun years 1990/91-1999/2000); "
            "EF = (100 kg N/ha run - 0 N control) / 100")
    write(F_ANN, arow)
    write(F_PUL, prow)
    write(F_CMP, rows)
    for r in rows:
        print(r["model"], r["basis"], r["direct_N2O_kg_ha"], r["total_N2O_kg_ha"], r["fertiliser_induced_EF_pct"])
    for r in prow:
        print(r)


APSIM_LABEL = "NG 2026.11.8142.0"

if __name__ == "__main__":
    main()
