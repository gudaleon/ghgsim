"""Compare APSIM daily county N2O with annual EFs on the expanded sample (AN_v2), questions (c) and (d).

Consistency check, not validation (FINDINGS_AN_v2). Per-county metrics as compare_county_pilot_AN_v1 (APSIM
fertiliser-induced EF at 100 kg N/ha vs 0 N over sown years, IPCC 2006/2019 Tier 1, Holos-style base EF).
(d) Is the error of a single annual EF systematic? For the US sample: the county ratio APSIM EF / IPCC 2019 EF,
an OLS fit of log(ratio) on May-Oct P/PE and a poor-drainage indicator, and the aggregation error of the summed
county totals (sum N x EF_tier1 / sum N x EF_APSIM - 1) with a 2,000-draw county bootstrap 95 % interval.
(c) Ontario: APSIM EF vs the Holos-style base EF with May-Oct P from NASA POWER and PE by Hargreaves (FAO-56
eq. 52, Ra from FAO-56 eq. 21) from the same POWER series; no county N input is used for Ontario.
Outputs (refuse to overwrite): results/apsim_county_summary_AN_v2.csv, results/apsim_county_metrics_AN_v2.json
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_apsim_crop_AN_v1 as c1  # noqa: E402
import compare_county_pilot_AN_v1 as p1  # noqa: E402
import power_fill_AN_v1 as pf  # noqa: E402
import run_apsim_county_AN_v2 as r2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "apsim_county_AN_v2"
OUT = ROOT / "results" / "apsim_county_summary_AN_v2.csv"
MET = ROOT / "results" / "apsim_county_metrics_AN_v2.json"


def daily(uid: str, tag: str) -> list[dict]:
    with gzip.open(RES / f"county_{uid}_{tag}_AN_v2.Daily.csv.gz", "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["ay"] = int(r["Clock.Today"][:4])
        for k in list(r):
            if k.endswith(("_kgha", "_mm")) or k == "Weather.Rain":
                r[k] = float(r[k] or 0.0)
    return [r for r in rows if r["ay"] in p1.YEARS]


def county(uid: str) -> dict:
    if not (RES / f"county_{uid}_0N_AN_v2.Report.csv.gz").exists() or not (RES / f"county_{uid}_100N_AN_v2.Report.csv.gz").exists():
        return {"sown_years": 0, "note": "run failed or missing"}
    f, c = daily(uid, "100N"), daily(uid, "0N")
    with gzip.open(RES / f"county_{uid}_100N_AN_v2.Report.csv.gz", "rt", encoding="utf-8") as fh:
        sown = sorted({int(r["Clock.Today"][:4]) for r in csv.DictReader(fh)})
    if not sown:
        return {"sown_years": 0}
    af, ac = c1.annual(f), c1.annual(c)
    mf = sum(af[y]["N2O_N"] for y in sown) / len(sown)
    mc = sum(ac[y]["N2O_N"] for y in sown) / len(sown)
    p = c1.pulses(f)
    return {"sown_years": len(sown), "apsim_N2O_kg_ha": mf * c1.N2O_PER_N, "apsim_EF_pct": mf - mc,
            "share_top5pct_days": p["share_top5pct_days"], "max_day_over_mean_day": p["max_day_over_mean_day"]}


def hargreaves_may_oct(power: dict, lat: float) -> tuple[float, float]:
    par = power["properties"]["parameter"]
    p_tot, pe_tot, ny = 0.0, 0.0, 0
    phi = math.radians(lat)
    for day, rain in par["PRECTOTCORR"].items():
        m = int(day[4:6])
        if not 5 <= m <= 10:
            continue
        j = int(__import__("datetime").date(int(day[:4]), m, int(day[6:])).strftime("%j"))
        dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
        dl = 0.409 * math.sin(2 * math.pi * j / 365 - 1.39)
        ws = math.acos(-math.tan(phi) * math.tan(dl))
        ra = 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(dl) + math.cos(phi) * math.cos(dl) * math.sin(ws))
        tx, tn = par["T2M_MAX"][day], par["T2M_MIN"][day]
        pe_tot += 0.0023 * ((tx + tn) / 2 + 17.8) * math.sqrt(max(tx - tn, 0.0)) * ra * 0.408
        p_tot += rain
    ny = len({d[:4] for d in par["PRECTOTCORR"]})
    return p_tot / ny, pe_tot / ny


def main() -> None:
    for o in (OUT, MET):
        if o.exists():
            raise SystemExit(f"refusing to overwrite {o}")
    with (ROOT / "data" / "county_p_pe_may_oct_AN_v2.csv").open(encoding="utf-8") as fh:
        ppe = {r["fips"]: r for r in csv.DictReader(fh)}
    rows = []
    for u in r2.units():
        info = json.loads((RES / f"county_{u['id']}_run_AN_v2.json").read_text(encoding="utf-8")) if (RES / f"county_{u['id']}_run_AN_v2.json").exists() else {}
        r = {"id": u["id"], "country": u["country"], "sat_caps": len(info.get("sat_caps", [])), "filled_missing": len(info.get("filled_missing", []))}
        if u["country"] == "US":
            s = u["row"]
            r.update({k: s[k] for k in ("state", "county", "ppe_quintile", "drainage", "p_over_pe_may_oct", "zone_primary", "synthetic_N_kg")})
            q = ppe[s["fips"]]
            p_mm, pe_mm = float(q["growing_season_precip_mm"]), float(q["growing_season_pe_mm"])
            r["ipcc2006_EF_pct"] = 100 * p1.ipcc_ef(s["zone_primary"], "2006")
            r["ipcc2019_EF_pct"] = 100 * p1.ipcc_ef(s["zone_primary"], "2019")
        else:
            c = u["row"]
            with gzip.open(u["power"](), "rt", encoding="utf-8") as fh:
                power, _ = pf.fill_power(json.load(fh))
            p_mm, pe_mm = hargreaves_may_oct(power, c["point_wgs84"][0])
            r.update({"state": "ON", "county": c["municipality"], "drainage": c["drainage"], "soil": c["soilname"],
                      "p_over_pe_may_oct": p_mm / pe_mm})
        r["may_oct_P_mm"], r["may_oct_PE_mm"] = p_mm, pe_mm
        r["holos_base_EF_pct"] = 100 * p1.holos_base_ef(p_mm, pe_mm)
        r.update(county(u["id"]))
        rows.append(r)
    us = [r for r in rows if r["country"] == "US" and r.get("sown_years", 0) >= 5]
    on = [r for r in rows if r["country"] == "CA" and r.get("sown_years", 0) >= 5]
    a = [r["apsim_EF_pct"] for r in us]
    n = [float(r["synthetic_N_kg"]) for r in us]
    ratio = [r["apsim_EF_pct"] / r["ipcc2019_EF_pct"] for r in us]
    pos = [i for i, x in enumerate(ratio) if x > 0]
    X = np.column_stack([np.ones(len(pos)), [float(us[i]["p_over_pe_may_oct"]) for i in pos], [us[i]["drainage"] == "poor" for i in pos]])
    y = np.log([ratio[i] for i in pos])
    beta, res, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    s2 = float(resid @ resid) / (len(y) - 3)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    r2_ = 1 - float(resid @ resid) / float(((y - y.mean()) ** 2).sum())

    def agg(idx: list[int], k: str) -> float:
        ap = sum(n[i] * a[i] for i in idx)
        return sum(n[i] * us[i][k] for i in idx) / ap - 1

    rng = random.Random(20261104)
    boot = {k: sorted(agg([rng.randrange(len(us)) for _ in us], k) for _ in range(2000)) for k in ("ipcc2006_EF_pct", "ipcc2019_EF_pct", "holos_base_EF_pct")}
    allidx = list(range(len(us)))
    met = {"n_us": len(us), "n_ontario": len(on), "n_us_failed_or_lt5_sown": sum(r["country"] == "US" for r in rows) - len(us),
           "n_ontario_failed_or_lt5_sown": sum(r["country"] == "CA" for r in rows) - len(on),
           "us_spearman_EF_apsim_vs": {k: p1.spearman(a, [float(r[k]) for r in us]) for k in ("ipcc2019_EF_pct", "holos_base_EF_pct", "p_over_pe_may_oct")},
           "us_mean_apsim_EF_pct_by_drainage": {d: float(np.mean([r["apsim_EF_pct"] for r in us if r["drainage"] == d])) for d in ("well", "poor")},
           "us_mean_apsim_EF_pct_by_ppe_quintile": {q: float(np.mean([r["apsim_EF_pct"] for r in us if r["ppe_quintile"] == q])) for q in sorted({r["ppe_quintile"] for r in us})},
           "us_log_ratio_ols": {"terms": ["intercept", "p_over_pe", "poor_drainage"], "beta": beta.tolist(), "se": se.tolist(), "r2": r2_,
                                "n": len(y), "n_dropped_nonpositive_ratio": len(us) - len(pos)},
           "us_aggregation_error_vs_apsim": {k: {"point": agg(allidx, k), "boot95": [boot[k][49], boot[k][1949]]} for k in boot},
           "us_top_decile_share_of_total": {k: p1.top_share([ni * float(r[k]) / 100 for ni, r in zip(n, us, strict=True)]) for k in ("apsim_EF_pct", "ipcc2019_EF_pct", "holos_base_EF_pct")},
           "us_mean_share_top5pct_days": float(np.mean([r["share_top5pct_days"] for r in us])),
           "ontario_spearman_EF_apsim_vs_holos": p1.spearman([r["apsim_EF_pct"] for r in on], [r["holos_base_EF_pct"] for r in on]) if len(on) > 2 else None,
           "ontario_mean_EF_pct": {"apsim": float(np.mean([r["apsim_EF_pct"] for r in on])) if on else None,
                                   "holos_base": float(np.mean([r["holos_base_EF_pct"] for r in on])) if on else None},
           "ontario_mean_share_top5pct_days": float(np.mean([r["share_top5pct_days"] for r in on])) if on else None,
           "sat_caps_units": sum(r["sat_caps"] > 0 for r in rows), "filled_missing_units": sum(r["filled_missing"] > 0 for r in rows)}
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)
    MET.write_text(json.dumps(met, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(met, indent=1))


if __name__ == "__main__":
    main()