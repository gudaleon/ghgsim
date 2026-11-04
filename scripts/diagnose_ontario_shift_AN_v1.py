"""FINDINGS v12: cause of the Ontario sowing-year EF shift (FINDINGS v11). Existing daily outputs only. Refuses to overwrite."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse_pulses_distortion_AN_v2 as A  # noqa: E402
OUT = Path("results/ontario_shift_AN_v1")
if OUT.exists(): sys.exit("refusing to overwrite " + str(OUT))
def rd(p): return pd.read_csv(p, parse_dates=["Clock.Today"]).set_index("Clock.Today")
def onsets(s):
    on = s.gt(0) & ~s.shift(1, fill_value=0).gt(0); return list(s.index[on])
rows = []
for u in A.units():
    f, c = rd(u["f"]), rd(u["c"]); idx = f.index.intersection(c.index); f, c = f.loc[idx], c.loc[idx]
    d = f.N2O_N_kgha - c.N2O_N_kgha
    sown = sorted(set(A.sown(u["rep"]))); mz = onsets(f.MaizeN_gm2); ur = onsets(f.Urea_kgha) if "Urea_kgha" in f else []
    onset_years = sorted({t.year for t in mz}); urea_years = sorted({t.year for t in ur})
    seg = [(a, b) for a, b in zip(mz, mz[1:]) if (b - a).days <= 400]
    seg_years = [a.year for a, b in seg]
    cal_all = {y: d[idx.year == y].sum() for y in sorted(set(idx.year)) if (idx.year == y).sum() >= 365}
    sw = {a.year: d[(d.index >= a) & (d.index < b)].sum() for a, b in seg}
    common = [y for y in seg_years if y in sown and y in cal_all]
    # Jan-to-onset in each common year, and onset-to-Dec31
    pre = np.mean([d[(idx.year == y) & (d.index < next(t for t in mz if t.year == y))].sum() for y in common]) if common else np.nan
    rows.append({"id": u["id"], "country": u["country"], "n_sown_report": len(sown), "n_onset_years": len(onset_years), "n_urea_years": len(urea_years),
        "n_segments": len(seg), "sown_not_onset": len(set(sown) - set(onset_years)), "onset_not_sown": len(set(onset_years) - set(sown)),
        "cal_EF_sown": np.mean([cal_all[y] for y in sown if y in cal_all]), "cal_EF_allyears": np.mean(list(cal_all.values())),
        "sow_EF_all": np.mean(list(sw.values())) if sw else np.nan,
        "cal_EF_common": np.mean([cal_all[y] for y in common]) if common else np.nan, "sow_EF_common": np.mean([sw[y] for y in common]) if common else np.nan,
        "n_common": len(common), "pre_onset_dN2O_common": pre,
        "mean_onset_doy": np.mean([t.dayofyear for t in mz]) if mz else np.nan,
        "dN2O_unsown_years": np.mean([v for y, v in cal_all.items() if y not in sown]) if any(y not in sown for y in cal_all) else np.nan})
df = pd.DataFrame(rows); OUT.mkdir(parents=True); df.to_csv(OUT / "ontario_shift_units_AN_v1.csv", index=False)
res = {}
for k, g in df.groupby("country"):
    g = g[g.cal_EF_sown > 0]
    r = lambda a, b: round(float(((g[a] / g[b]) - 1).median() * 100), 1)
    res[k] = {"n": len(g), "median_n_sown_report": float(g.n_sown_report.median()), "median_n_onset_years": float(g.n_onset_years.median()),
        "median_n_segments": float(g.n_segments.median()), "units_with_onset_not_sown": int((g.onset_not_sown > 0).sum()), "units_with_sown_not_onset": int((g.sown_not_onset > 0).sum()),
        "median_change_reported_pct (sow_all vs cal_sown)": r("sow_EF_all", "cal_EF_sown"),
        "median_change_same_years_pct (sow vs cal, common years)": r("sow_EF_common", "cal_EF_common"),
        "median_change_cal_all_vs_cal_sown_pct": r("cal_EF_allyears", "cal_EF_sown"),
        "median_mean_onset_doy": float(g.mean_onset_doy.median()),
        "mean_dN2O_in_unsown_calendar_years_kgha": round(float(g.dN2O_unsown_years.mean()), 3) if g.dN2O_unsown_years.notna().any() else None}
json.dump(res, open(OUT / "ontario_shift_summary_AN_v1.json", "w"), indent=1); print(json.dumps(res, indent=1))