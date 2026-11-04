"""FINDINGS v11: recompute soybean share and EFs on sowing-to-sowing crop years vs calendar years.
Existing daily outputs only. Crop onset = first day with crop N > 0 (APSIM reports crop N from emergence, so this is a proxy a few days after sowing).
Refuses to overwrite outputs."""
import os, sys, json, glob
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse_pulses_distortion_AN_v2 as A  # noqa: E402
OUT = Path("results/sowing_year_AN_v1")
if OUT.exists(): sys.exit("refusing to overwrite " + str(OUT))
def rd(p): return pd.read_csv(p, parse_dates=["Clock.Today"]).set_index("Clock.Today")
def onsets(s):  # first day per calendar year where series > 0 after a zero day
    on = s.gt(0) & ~s.shift(1, fill_value=0).gt(0)
    return list(s.index[on])
def spearman(a, b): return float(pd.Series(a).rank().corr(pd.Series(b).rank()))
OUT.mkdir(parents=True); res = {"sites": {}, "counties": {}}
# --- Lake Erie rotations and Iowa maize ---
pairs = []
for p in sorted(glob.glob("results/apsim_lake_erie_AN_v3/*_AN_v3.Daily.csv.gz") + glob.glob("results/apsim_brookston_ssurgo_AN_v1/*_AN_v3.Daily.csv.gz")
                + ["results/apsim_brookston_soilwater_AN_v1/brookston_soilwater_AN_v1.Daily.csv.gz"]
                + glob.glob("results/apsim_AN_v3/crop_urea_lime_*_AN_v3.Daily.csv.gz") + ["results/apsim_AN_v2/crop_urea_lime_iowa_AN_v2.Daily.csv.gz"]
                + glob.glob("results/apsim_webster_drains_*/*.Daily.csv.gz")):
    if "_0N" in p or "_x" in os.path.basename(p): continue
    z = p.replace("_AN_v3.Daily", "_0N_AN_v3.Daily").replace("_AN_v2.Daily", "_0N_AN_v2.Daily").replace("_AN_v1.Daily", "_0N_AN_v1.Daily")
    if os.path.exists(z): pairs.append((p, z))
for p, z in pairs:
    f, c = rd(p), rd(z); idx = f.index.intersection(c.index); f, c = f.loc[idx], c.loc[idx]
    d = (f.N2O_N_kgha - c.N2O_N_kgha); name = os.path.basename(p).replace(".Daily.csv.gz", "")
    if len(idx) < 3 * 365: res["sites"][name] = {"skipped": f"only {len(idx)} days (failed run)"}; continue
    mz = onsets(f.MaizeN_gm2); sy = onsets(f["SoyAbovegroundN_kgha"]) if "SoyAbovegroundN_kgha" in f else []
    starts = sorted([(t, "maize") for t in mz] + [(t, "soy") for t in sy])
    seg = [(a[0], b[0], a[1]) for a, b in zip(starts, starts[1:])]  # complete crop years only
    crop = {"maize": [], "soy": []}
    for a, b, k in seg: crop[k].append(d[(d.index >= a) & (d.index < b)].sum())
    yr = idx.year; full = [y for y in sorted(set(yr)) if (yr == y).sum() >= 365]
    cal = {y: d[yr == y].sum() for y in full}
    out = {"n_crop_years": {k: len(v) for k, v in crop.items()}}
    if sy:
        cm, cs = np.mean([v for y, v in cal.items() if y % 2]), np.mean([v for y, v in cal.items() if not y % 2])
        sm, ss = np.mean(crop["maize"]), np.mean(crop["soy"])
        out.update({"calendar_soy_share": round(cs / (cm + cs), 3), "sowing_year_soy_share": round(ss / (sm + ss), 3),
                    "calendar_EF_pct": round((cm + cs) / 172 * 100, 2), "sowing_year_EF_pct": round((sm + ss) / 172 * 100, 2),
                    "sowing_maize_dN2O": round(sm, 3), "sowing_soy_dN2O": round(ss, 3)})
    else:
        nN = f.Urea_kgha.groupby(yr).sum().max() if "Urea_kgha" in f else np.nan
        out.update({"calendar_mean_dN2O": round(np.mean(list(cal.values())), 3), "sowing_year_mean_dN2O": round(np.mean(crop["maize"]), 3),
                    "calendar_sd": round(np.std(list(cal.values()), ddof=1), 3), "sowing_year_sd": round(np.std(crop["maize"], ddof=1), 3)})
    res["sites"][name] = out
# --- 95 US counties and 32 Ontario units (continuous maize, 100 vs 0 N) ---
rows = []
for u in A.units():
    f, c = rd(u["f"]), rd(u["c"]); idx = f.index.intersection(c.index); f, c = f.loc[idx], c.loc[idx]
    d = (f.N2O_N_kgha - c.N2O_N_kgha) / 100 * 100  # % of 100 kg N
    sown = set(A.sown(u["rep"])); mz = onsets(f.MaizeN_gm2)
    cal = [d[idx.year == y].sum() for y in sorted(sown) if (idx.year == y).sum() >= 365]
    sw = [d[(d.index >= a) & (d.index < b)].sum() for a, b in zip(mz, mz[1:])]
    rows.append({"id": u["id"], "country": u["country"], "cal_EF": np.mean(cal), "sow_EF": np.mean(sw), "cal_sd": np.std(cal, ddof=1), "sow_sd": np.std(sw, ddof=1),
                 "n_cal": len(cal), "n_sow": len(sw)})
df = pd.DataFrame(rows); df.to_csv(OUT / "county_sowing_vs_calendar_AN_v1.csv", index=False)
for k, g in df.groupby("country"):
    n = len(g); top = max(1, round(0.1 * n))
    tc, ts = set(g.nlargest(top, "cal_EF").id), set(g.nlargest(top, "sow_EF").id)
    rel = (g.sow_EF / g.cal_EF - 1) * 100
    res["counties"][k] = {"n": n, "mean_cal_EF_pct": round(g.cal_EF.mean(), 3), "mean_sow_EF_pct": round(g.sow_EF.mean(), 3),
        "median_rel_change_pct": round(rel.median(), 1), "rel_change_range_pct": [round(rel.min(), 1), round(rel.max(), 1)],
        "spearman_cal_vs_sow": round(spearman(g.cal_EF, g.sow_EF), 3), "top10pct_overlap": f"{len(tc & ts)}/{top}",
        "median_sd_ratio_sow_over_cal": round((g.sow_sd / g.cal_sd).median(), 3)}
json.dump(res, open(OUT / "sowing_year_summary_AN_v1.json", "w"), indent=1); print(json.dumps(res, indent=1))