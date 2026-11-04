"""Compare APSIM daily county N2O with annual emission factors, 20-county pilot (AN_v1), question (b)/(d).

Consistency check, not validation (FINDINGS_AN_v1). Per county: APSIM direct N2O at 100 kg N/ha over sown years,
fertiliser-induced EF against the 0 N control, pulse statistics (compare_apsim_crop_AN_v1.pulses); the IPCC
Tier 1 EF1 used by ghgsim (2006: 1.0 %; 2019 disaggregated synthetic N: 1.6 % wet, 0.5 % dry, by zone_primary);
and a Holos-style base ecodistrict EF re-derived from the published equation exp(0.00558 x - 7.7)
(Rochette et al. 2008; Holos V4.0 algorithm document eq. 2.5.1-1/2), x = May-Oct P when P > PE else PE,
in dry environments weighted by the lower-landscape fraction (0 in the main column, 1 in the upper bound),
without the Holos texture, tillage and other modifiers (no Canadian ecodistrict lookups for US counties).
County totals = county synthetic N x EF. Outputs (refuse to overwrite):
results/apsim_county_pilot_summary_AN_v1.csv and results/apsim_county_pilot_metrics_AN_v1.json
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_apsim_crop_AN_v1 as c1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "apsim_county_pilot_AN_v1"
RES = ROOT / "results" / "apsim_county_pilot_AN_v1"
OUT = ROOT / "results" / "apsim_county_pilot_summary_AN_v1.csv"
MET = ROOT / "results" / "apsim_county_pilot_metrics_AN_v1.json"
YEARS = range(1991, 2021)


def ipcc_ef(zone: str, version: str) -> float:
    if version == "2006":
        return 0.01
    return 0.016 if zone.endswith(("moist", "wet")) else 0.005


def holos_base_ef(p_mm: float, pe_mm: float, f_lower: float = 0.0) -> float:
    """Base EF: humid (P > PE) exp(0.00558 P - 7.7); dry: f_lower * EF(PE) + (1 - f_lower) * EF(P), f_lower =
    fraction of land in lower landscape positions (a Canadian ecodistrict lookup in Holos; unknown for US counties,
    so the main column uses 0 and an upper-bound column uses 1)."""
    ef_p, ef_pe = math.exp(0.00558 * p_mm - 7.7), math.exp(0.00558 * pe_mm - 7.7)
    if p_mm > pe_mm:
        return ef_p
    return f_lower * ef_pe + (1 - f_lower) * ef_p


def ranks(v: list[float]) -> list[float]:
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=True))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else float("nan")


def top_share(v: list[float], frac: float = 0.1) -> float:
    n = max(1, round(len(v) * frac))
    return sum(sorted(v, reverse=True)[:n]) / sum(v)


def daily(fips: str, tag: str) -> list[dict]:
    with gzip.open(RES / f"county_{fips}_{tag}_AN_v1.Daily.csv.gz", "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["ay"] = int(r["Clock.Today"][:4])
        for k in list(r):
            if k.endswith(("_kgha", "_mm")) or k == "Weather.Rain":
                r[k] = float(r[k] or 0.0)
    return [r for r in rows if r["ay"] in YEARS]


def county(fips: str) -> dict:
    if not (RES / f"county_{fips}_0N_AN_v1.Report.csv.gz").exists():
        return {"sown_years": 0, "note": "dropped: APSIM soil physical check failed on SSURGO values (no tuning)"}
    f, c = daily(fips, "100N"), daily(fips, "0N")
    with gzip.open(RES / f"county_{fips}_100N_AN_v1.Report.csv.gz", "rt", encoding="utf-8") as fh:
        sown = sorted({int(r["Clock.Today"][:4]) for r in csv.DictReader(fh)})
    af, ac = c1.annual(f), c1.annual(c)
    if not sown:
        return {"sown_years": 0}
    mf = sum(af[y]["N2O_N"] for y in sown) / len(sown)
    mc = sum(ac[y]["N2O_N"] for y in sown) / len(sown)
    p = c1.pulses(f)
    return {"sown_years": len(sown), "apsim_N2O_kg_ha": mf * c1.N2O_PER_N, "apsim_control_N2O_kg_ha": mc * c1.N2O_PER_N,
            "apsim_EF_pct": mf - mc, "share_top5pct_days": p["share_top5pct_days"],
            "max_day_over_mean_day": p["max_day_over_mean_day"],
            "share_N2O_within_window_after_rain": p["share_N2O_within_window_after_rain"]}


def main() -> None:
    for o in (OUT, MET):
        if o.exists():
            raise SystemExit(f"refusing to overwrite {o}")
    with (DATA / "county_pilot_sample_AN_v1.csv").open(encoding="utf-8") as fh:
        sample = list(csv.DictReader(fh))
    with (ROOT / "data" / "county_p_pe_may_oct_AN_v2.csv").open(encoding="utf-8") as fh:
        ppe = {r["fips"]: r for r in csv.DictReader(fh)}
    rows = []
    for s in sample:
        r = {k: s[k] for k in ("fips", "state", "county", "ppe_quintile", "drainage", "p_over_pe_may_oct", "zone_primary", "synthetic_N_kg")}
        r.update(county(s["fips"]))
        q = ppe[s["fips"]]
        r["holos_base_EF_pct"] = 100 * holos_base_ef(float(q["growing_season_precip_mm"]), float(q["growing_season_pe_mm"]))
        r["holos_base_EF_upper_pct"] = 100 * holos_base_ef(float(q["growing_season_precip_mm"]), float(q["growing_season_pe_mm"]), 1.0)
        r["ipcc2006_EF_pct"] = 100 * ipcc_ef(s["zone_primary"], "2006")
        r["ipcc2019_EF_pct"] = 100 * ipcc_ef(s["zone_primary"], "2019")
        rows.append(r)
    ok = [r for r in rows if r.get("sown_years")]
    n = [float(r["synthetic_N_kg"]) for r in ok]
    tot = {k: [ni * r[k] / 100 for ni, r in zip(n, ok, strict=True)] for k in ("apsim_EF_pct", "ipcc2006_EF_pct", "ipcc2019_EF_pct", "holos_base_EF_pct")}
    a = [r["apsim_EF_pct"] for r in ok]
    met = {"n_counties": len(ok),
           "spearman_EF_apsim_vs": {k: spearman(a, [r[k] for r in ok]) for k in ("ipcc2019_EF_pct", "holos_base_EF_pct", "p_over_pe_may_oct")},
           "spearman_total_apsim_vs": {k: spearman(tot["apsim_EF_pct"], tot[k]) for k in ("ipcc2006_EF_pct", "ipcc2019_EF_pct", "holos_base_EF_pct")},
           "top_decile_share_of_total": {k: top_share(v) for k, v in tot.items()},
           "sum_total_N2O_N_t": {k: sum(v) / 1000 for k, v in tot.items()},
           "mean_apsim_EF_pct_by_drainage": {d: sum(r["apsim_EF_pct"] for r in ok if r["drainage"] == d) / max(1, sum(r["drainage"] == d for r in ok)) for d in ("well", "poor")},
           "spearman_apsim_over_ipcc2019_vs_ppe": spearman([r["apsim_EF_pct"] / r["ipcc2019_EF_pct"] for r in ok], [float(r["p_over_pe_may_oct"]) for r in ok]),
           "mean_share_top5pct_days": sum(r["share_top5pct_days"] for r in ok) / len(ok),
           "n_counties_ge15_sown_years": sum(r["sown_years"] >= 15 for r in ok),
           "spearman_EF_apsim_vs_ppe_ge15_sown": spearman([r["apsim_EF_pct"] for r in ok if r["sown_years"] >= 15], [float(r["p_over_pe_may_oct"]) for r in ok if r["sown_years"] >= 15])}
    keys = list(rows[0])
    for r in rows:
        keys += [k for k in r if k not in keys]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)
    MET.write_text(json.dumps(met, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(met, indent=1))


if __name__ == "__main__":
    main()