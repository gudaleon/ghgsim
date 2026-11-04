"""Rain-driven N2O pulses and annual-averaging distortion from existing APSIM daily outputs (AN_v1), FINDINGS_AN_v8.

Consistency check, not validation. No new APSIM runs. Inputs (read only):
- US: results/apsim_county_AN_v2 (97 counties, 100 vs 0 kg N/ha), results/apsim_county_summary_AN_v2.csv
  (IPCC 2006 / 2019 Tier 1 EF, zone, synthetic N, drainage), SSURGO surface horizon for texture.
- Ontario: results/apsim_county_AN_v3 'omafra' variant (32 units), CanSIS surface horizon for texture.
- Lake Erie: results/apsim_lake_erie_AN_v3 (non-failed runs) and results/apsim_brookston_ssurgo_AN_v1.
- Iowa: results/apsim_AN_v2 (Webster) and results/apsim_AN_v3 (Clarion, Webster SWIM/tile/seep/wt variants).
Decisions (logged in FINDINGS_AN_v8):
- D1 rain event = calendar day with Weather.Rain >= 10 mm.
- D2 window k (1, 3, 7) = event day plus the next k-1 days (APSIM daily step puts same-day rain and N2O on one
  row); windows of nearby events are merged (union), so no day counts twice. The share of days covered is reported
  as the random-expectation baseline.
- D3 pulse metrics use the fertilised run, all days 1991-2020; annual share = pooled over years.
- D4 texture class from the USDA triangle on the surface horizon sand/clay; grouped coarse / medium / fine.
- D5 annual-factor methods use a single EF per county: IPCC 2006 (1 %), IPCC 2019 (wet 1.6 %, dry 0.5 %), and the
  Holos-style base EF exp(0.00558 P - 7.7) (P > PE; f_lower = 0) on May-Oct NASA POWER P and Hargreaves PE, both as
  a 30-yr mean (as in v2) and per year for the interannual comparison. Ontario IPCC 2019 uses the wet value,
  flagged: all 32 units have annual P > PE in IPCC's climate sense is an assumption, not tested here.
- D6 APSIM EF per year = (N2O-N 100N - N2O-N 0N) / 100 over sown years (Report rows), as v2/v3.
- D7 bootstrap: 2,000 county resamples, seed 20261104, percentile 95 % CI.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_county_pilot_AN_v1 as p1  # noqa: E402
import power_fill_AN_v1 as pf  # noqa: E402
import run_apsim_county_AN_v2 as r2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUTJ = R / "pulses_distortion_AN_v1.json"
OUTC = R / "pulses_distortion_units_AN_v1.csv"
FIG = ROOT / "docs" / "figures"
THR, WINS, TOPS, NB, SEED = 10.0, (1, 3, 7), (0.01, 0.05, 0.10), 2000, 20261104
YEARS = range(1991, 2021)


def texture(sand: float, clay: float) -> str:
    silt = 100 - sand - clay
    if clay >= 40 or (clay >= 35 and sand >= 45) or (clay >= 40 and silt >= 40):
        return "fine"
    if clay >= 27 and sand <= 45:
        return "fine"
    if (silt + 1.5 * clay < 15) or (silt + 1.5 * clay >= 15 and silt + 2 * clay < 30) or \
       (clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50 and sand > 43 and silt + 2 * clay >= 30):
        return "coarse"
    return "medium"


def load(path: Path) -> list[tuple[str, float, float]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        out = [(r["Clock.Today"][:10], float(r["Weather.Rain"] or 0), float(r["N2O_N_kgha"] or 0)) for r in csv.DictReader(fh)]
    return [o for o in out if int(o[0][:4]) in YEARS]


def sown(path: Path) -> list[int]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return sorted({int(r["Clock.Today"][:4]) for r in csv.DictReader(fh)} & set(YEARS))


def pulses(rows) -> dict:
    n = np.array([r[2] for r in rows])
    rain = np.array([r[1] for r in rows])
    tot = n.sum()
    ev = np.where(rain >= THR)[0]
    out = {"n_days": len(n), "n_events": int(len(ev)), "events_per_yr": len(ev) / (len(n) / 365.25)}
    for k in WINS:
        m = np.zeros(len(n), bool)
        for i in ev:
            m[i:i + k] = True
        out[f"share_{k}d"] = float(n[m].sum() / tot) if tot else math.nan
        out[f"days_{k}d"] = float(m.mean())
    s = np.sort(n)[::-1]
    for f in TOPS:
        out[f"share_top{int(f * 100)}pct_days"] = float(s[:max(1, int(round(f * len(s))))].sum() / tot) if tot else math.nan
    return out


def annual(rows) -> dict[int, float]:
    a: dict[int, float] = {}
    for d, _, n in rows:
        a[int(d[:4])] = a.get(int(d[:4]), 0.0) + n
    return a


def holos_by_year(power: dict, lat: float) -> dict[int, float]:
    par = power["properties"]["parameter"]
    phi = math.radians(lat)
    P: dict[int, float] = {}
    PE: dict[int, float] = {}
    for day, rain in par["PRECTOTCORR"].items():
        y, m = int(day[:4]), int(day[4:6])
        if not 5 <= m <= 10:
            continue
        j = dt.date(y, m, int(day[6:])).timetuple().tm_yday
        dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
        dl = 0.409 * math.sin(2 * math.pi * j / 365 - 1.39)
        ws = math.acos(-math.tan(phi) * math.tan(dl))
        ra = 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(dl) + math.cos(phi) * math.cos(dl) * math.sin(ws))
        tx, tn = par["T2M_MAX"][day], par["T2M_MIN"][day]
        PE[y] = PE.get(y, 0.0) + 0.0023 * ((tx + tn) / 2 + 17.8) * math.sqrt(max(tx - tn, 0.0)) * ra * 0.408
        P[y] = P.get(y, 0.0) + rain
    return {y: 100 * p1.holos_base_ef(P[y], PE[y]) for y in P}


def skew(v) -> float:
    v = np.asarray(v, float)
    s = v.std()
    return float(((v - v.mean()) ** 3).mean() / s ** 3) if s > 0 else 0.0


def spread(v) -> dict:
    v = np.asarray(v, float)
    return {"skew": skew(v), "cv": float(v.std(ddof=1) / v.mean()) if v.mean() else math.nan,
            "p90_over_p10": float(np.percentile(v, 90) / np.percentile(v, 10)) if np.percentile(v, 10) > 0 else math.nan}


def spearman(a, b) -> float:
    if np.std(a) == 0 or np.std(b) == 0:
        return math.nan
    return p1.spearman(list(a), list(b))


def top_overlap(a, b, frac=0.1) -> float:
    k = max(1, int(round(frac * len(a))))
    ta, tb = set(np.argsort(a)[::-1][:k]), set(np.argsort(b)[::-1][:k])
    if np.std(b) == 0:
        return math.nan
    return len(ta & tb) / k


def ci(fn, n, rng) -> list[float]:
    vals = []
    for _ in range(NB):
        v = fn([rng.randrange(n) for _ in range(n)])
        if not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if len(vals) < NB / 2:
        return [math.nan, math.nan]
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]


def units() -> list[dict]:
    with (R / "apsim_county_summary_AN_v2.csv").open(encoding="utf-8") as fh:
        s2 = {r["id"]: r for r in csv.DictReader(fh)}
    with (R / "apsim_ontario_summary_AN_v3.csv").open(encoding="utf-8") as fh:
        s3 = {r["id"]: r for r in csv.DictReader(fh)}
    out = []
    for u in r2.units():
        if u["country"] == "US":
            base, tag, v = R / "apsim_county_AN_v2", "", "AN_v2"
            row = s2[u["id"]]
            hz = u["soil"]()["horizons"][0]
            ef06, ef19, N, dr = float(row["ipcc2006_EF_pct"]), float(row["ipcc2019_EF_pct"]), float(row["synthetic_N_kg"]), row["drainage"]
        else:
            base, tag, v = R / "apsim_county_AN_v3", "omafra_", "AN_v3"
            hz = u["row"]["horizons"][0]
            ef06, ef19, N, dr = 1.0, 1.6, math.nan, {"W": "well", "R": "well", "I": "imperfect", "P": "poor"}[u["row"]["drainage"]]
            row = s3[u["id"]]
        f = base / f"county_{u['id']}_{tag}100N_{v}.Daily.csv.gz"
        c = base / f"county_{u['id']}_{tag}0N_{v}.Daily.csv.gz"
        rep = base / f"county_{u['id']}_{tag}100N_{v}.Report.csv.gz"
        if not (f.exists() and c.exists() and rep.exists()):
            continue
        out.append({"id": u["id"], "country": u["country"], "drainage": dr, "N": N, "ef06": ef06, "ef19": ef19,
                    "texture": texture(float(hz["sandtotal_r"]), float(hz["claytotal_r"])), "f": f, "c": c, "rep": rep,
                    "power": u["power"], "lat": (u["soil"]()["point_wgs84"][0] if u["country"] == "US" else u["row"]["point_wgs84"][0])})
    return out


def sites() -> list[dict]:
    out = []
    for folder, man in (("apsim_lake_erie_AN_v3", "apsim_lake_erie_manifest_AN_v3.json"), ("apsim_brookston_ssurgo_AN_v1", "apsim_lake_erie_manifest_AN_v3.json")):
        m = json.loads((R / folder / man).read_text(encoding="utf-8"))
        for run, info in m["runs"].items():
            if "failed" in info or info["corn_urea_N_kg_ha"] == 0:
                continue
            out.append({"id": f"{folder}:{run}", "group": "Lake Erie", "path": R / folder / f"lake_erie_{run}_AN_v3.Daily.csv.gz"})
    out.append({"id": "apsim_AN_v2:iowa_webster", "group": "Iowa", "path": R / "apsim_AN_v2" / "crop_urea_lime_iowa_AN_v2.Daily.csv.gz"})
    for p in sorted((R / "apsim_AN_v3").glob("crop_urea_lime_*_AN_v3.Daily.csv.gz")):
        if "_0N_" in p.name or "_x" in p.name:
            continue
        out.append({"id": "apsim_AN_v3:" + p.name.replace("crop_urea_lime_", "").replace("_AN_v3.Daily.csv.gz", ""), "group": "Iowa", "path": p})
    return out


def main() -> None:
    for o in (OUTJ, OUTC):
        if o.exists():
            raise SystemExit(f"refusing to overwrite {o}")
    rng = random.Random(SEED)
    rows = []
    for u in units():
        f, c = load(u["f"]), load(u["c"])
        sy = sown(u["rep"])
        if len(sy) < 5:
            continue
        af, ac = annual(f), annual(c)
        ef_y = {y: af.get(y, 0) - ac.get(y, 0) for y in sy}
        with gzip.open(u["power"](), "rt", encoding="utf-8") as fh:
            power, _ = pf.fill_power(json.load(fh))
        hy = holos_by_year(power, u["lat"])
        r = {k: u[k] for k in ("id", "country", "drainage", "texture", "N", "ef06", "ef19")}
        r.update(pulses(f))
        r["sown_years"] = len(sy)
        r["apsim_EF"] = float(np.mean(list(ef_y.values())))
        r["holos_EF"] = float(np.mean([hy[y] for y in sy]))
        r["apsim_EF_sd"] = float(np.std(list(ef_y.values()), ddof=1))
        r["holos_EF_sd"] = float(np.std([hy[y] for y in sy], ddof=1))
        r["ef_years"] = {y: (ef_y[y], hy[y]) for y in sy}
        rows.append(r)
    site_rows = []
    for s in sites():
        site_rows.append({"id": s["id"], "group": s["group"], **pulses(load(s["path"]))})
    res: dict = {"decisions": __doc__.split("Decisions (logged in FINDINGS_AN_v8):")[1].strip(), "n_bootstrap": NB, "seed": SEED}
    pk = [f"share_{k}d" for k in WINS] + [f"days_{k}d" for k in WINS] + [f"share_top{int(f * 100)}pct_days" for f in TOPS] + ["events_per_yr"]

    def grp(sel):
        g = {}
        for k in pk:
            v = [r[k] for r in sel]
            g[k] = {"mean": float(np.mean(v)), "ci95": ci(lambda i, v=v: float(np.mean([v[j] for j in i])), len(v), rng) if len(v) > 2 else None}
        g["n"] = len(sel)
        return g
    P = {}
    for ctry in ("US", "CA"):
        sel = [r for r in rows if r["country"] == ctry]
        P[ctry] = {"all": grp(sel)}
        for key in ("drainage", "texture"):
            for val in sorted({r[key] for r in sel}):
                ss = [r for r in sel if r[key] == val]
                if len(ss) >= 3:
                    P[ctry][f"{key}={val}"] = grp(ss)
    P["sites"] = site_rows
    res["pulses"] = P
    D = {}
    for ctry in ("US", "CA"):
        sel = [r for r in rows if r["country"] == ctry]
        n = len(sel)
        w = np.array([r["N"] for r in sel]) if ctry == "US" else np.full(n, 100.0)
        ef = {"apsim": np.array([r["apsim_EF"] for r in sel]), "ipcc2006": np.array([r["ef06"] for r in sel]),
              "ipcc2019": np.array([r["ef19"] for r in sel]), "holos": np.array([r["holos_EF"] for r in sel])}
        d = {"n": n, "weight": "county synthetic N (kg)" if ctry == "US" else "100 kg N/ha per unit (no county N for Ontario)"}
        for m in ("apsim", "ipcc2006", "ipcc2019", "holos"):
            tot = w * ef[m] / 100
            e = {"total_kgN2ON": float(tot.sum())}
            e.update(spread(tot))
            e["skew_ci95"] = ci(lambda i, t=tot: skew(t[i]), n, rng)
            e["cv_ci95"] = ci(lambda i, t=tot: float(t[i].std(ddof=1) / t[i].mean()), n, rng)
            if m != "apsim":
                ta = w * ef["apsim"] / 100
                e["total_error_vs_apsim"] = float(tot.sum() / ta.sum() - 1)
                e["total_error_ci95"] = ci(lambda i, t=tot, ta=ta: float(t[i].sum() / ta[i].sum() - 1), n, rng)
                e["spearman_totals"] = spearman(ta, tot)
                e["spearman_totals_ci95"] = ci(lambda i, t=tot, ta=ta: spearman(ta[i], t[i]), n, rng)
                e["spearman_EF"] = spearman(ef["apsim"], ef[m])
                e["top10_overlap_totals"] = top_overlap(ta, tot)
                e["top10_overlap_ci95"] = ci(lambda i, t=tot, ta=ta: top_overlap(ta[i], t[i]), n, rng)
                e["top10_overlap_EF"] = top_overlap(ef["apsim"], ef[m])
            d[m] = e
        sda, sdh = np.array([r["apsim_EF_sd"] for r in sel]), np.array([r["holos_EF_sd"] for r in sel])
        rat = sdh / np.where(sda > 0, sda, np.nan)
        d["interannual"] = {"apsim_EF_sd_median_pct": float(np.median(sda)), "holos_EF_sd_median_pct": float(np.median(sdh)),
                            "ipcc_EF_sd_pct": 0.0, "median_sd_ratio_holos_over_apsim": float(np.nanmedian(rat)),
                            "ratio_ci95": ci(lambda i: float(np.nanmedian(rat[i])), n, rng),
                            "apsim_cv_median": float(np.median(sda / np.abs(ef["apsim"]))),
                            "corr_yearly_apsim_vs_holos_median": float(np.nanmedian([np.corrcoef(*zip(*r["ef_years"].values()))[0, 1] if len(r["ef_years"]) > 2 else np.nan for r in sel]))}
        D[ctry] = d
    res["distortion"] = D
    OUTJ.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    keys = [k for k in rows[0] if k not in ("ef_years",)]
    with OUTC.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    figures(rows, site_rows, res)
    print(json.dumps({k: v for k, v in res.items() if k != "decisions"}, indent=1, default=float)[:20000])


def figures(rows, site_rows, res) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    out = {n: FIG / f"{n}_AN_v1.png" for n in ("pulse_share_by_group", "county_distribution_by_method", "hotspot_rank_apsim_vs_methods", "interannual_sd_apsim_vs_holos")}
    for p in out.values():
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    fig, ax = plt.subplots(figsize=(8, 4))
    labels, P = [], res["pulses"]
    for ctry in ("US", "CA"):
        for g, v in P[ctry].items():
            labels.append(f"{ctry} {g} (n={v['n']})")
    x = np.arange(len(labels))
    i = 0
    for ctry in ("US", "CA"):
        for g, v in P[ctry].items():
            for j, k in enumerate(WINS):
                m = v[f"share_{k}d"]
                ax.bar(i + (j - 1) * 0.27, m["mean"], 0.27, color=f"C{j}", label=f"{k}-d window" if i == 0 else None,
                       yerr=[[m["mean"] - m["ci95"][0]], [m["ci95"][1] - m["mean"]]] if m["ci95"] else None)
                ax.plot(i + (j - 1) * 0.27, v[f"days_{k}d"]["mean"], "k_", ms=10)
            i += 1
    ax.set_xticks(x, labels, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("share of N2O-N after rain >= 10 mm")
    ax.set_title("Bars: N2O share; black ticks: share of days in windows (APSIM, consistency check)", fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out["pulse_share_by_group"], dpi=200)
    plt.close(fig)
    us = [r for r in rows if r["country"] == "US"]
    w = np.array([r["N"] for r in us])
    T = {"APSIM": w * np.array([r["apsim_EF"] for r in us]) / 100, "IPCC 2006": w * np.array([r["ef06"] for r in us]) / 100,
         "IPCC 2019": w * np.array([r["ef19"] for r in us]) / 100, "Holos-style": w * np.array([r["holos_EF"] for r in us]) / 100}
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([v / 1000 for v in T.values()], tick_labels=list(T))
    ax.set_yscale("log")
    ax.set_ylabel("county fertiliser-induced N2O-N (t/yr)")
    ax.set_title("US counties, distribution by method", fontsize=9)
    fig.tight_layout()
    fig.savefig(out["county_distribution_by_method"], dpi=200)
    plt.close(fig)
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.4))
    ra = p1.ranks(list(T["APSIM"]))
    for a, m in zip(axs, ("IPCC 2006", "IPCC 2019", "Holos-style"), strict=True):
        a.scatter(ra, p1.ranks(list(T[m])), s=8)
        a.set_xlabel("APSIM rank")
        a.set_ylabel(f"{m} rank")
        a.set_title(m, fontsize=9)
    fig.tight_layout()
    fig.savefig(out["hotspot_rank_apsim_vs_methods"], dpi=200)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for ctry, col in (("US", "C0"), ("CA", "C3")):
        s = [r for r in rows if r["country"] == ctry]
        ax.scatter([r["apsim_EF_sd"] for r in s], [r["holos_EF_sd"] for r in s], s=10, c=col, label=ctry)
    lim = max(r["apsim_EF_sd"] for r in rows)
    ax.plot([0, lim], [0, lim], "k:")
    ax.set_xlabel("APSIM interannual SD of EF (%)")
    ax.set_ylabel("Holos-style interannual SD of EF (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out["interannual_sd_apsim_vs_holos"], dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()