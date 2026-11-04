"""Paper B figures 1-5 (AN_v1).

Reads only committed result files; writes figures/*_AN_v1.png and
figures/paperB_figures_manifest_AN_v1.json (input SHA-256 per figure).
Run from repo root:  python scripts/make_paperB_figures_AN_v1.py
No numbers are typed in: every plotted value comes from the CSVs below.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures")
D = os.path.join(ROOT, "data")
STYL = os.path.join(D, "ipcc_2006_vs_2019_stylized_AN_v2.csv")
COUNTY = os.path.join(D, "us_county_2006_vs_2019_AN_v2.csv.gz")
NAT = os.path.join(D, "us_national_2006_vs_2019_vs_epa_AN_v2.csv")
ZONE = os.path.join(D, "us_county_zone_sensitivity_AN_v1.csv")
INV = sorted(glob.glob(os.path.join(D, "inventories_AN_v1", "*_recalc_AN_v1.csv")))
USREC = os.path.join(D, "inventories_US_AN_v1", "US_recalc_2024to2025_AN_v1.csv")
MANIFEST = os.path.join(ROOT, "results", "results_manifest_AN_v2.json")
COUNTY_VARIANT = "D_allocated"  # main-text variant (national 2019 total 341.4 Mt)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def save(fig, name, inputs, log):
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        raise SystemExit(f"refusing to overwrite {path}; bump the version")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log[name] = {os.path.relpath(p, ROOT).replace("\\", "/"): sha(p) for p in inputs}


def fig1(log):
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.axis("off")
    steps = ["Upstream sources\n(fingerprinted weekly)", "Versioned inputs", "ghgsim engine",
             "One-command recompute\n+ results manifest", "Diff report\n(why numbers moved)",
             "Readers: dashboard\n+ paper agent"]
    xs = np.linspace(0.08, 0.92, len(steps))
    for i, (x, s) in enumerate(zip(xs, steps, strict=True)):
        ax.text(x, 0.5, s, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.5", fc="#e8f0fa", ec="#2b5c8a"))
        if i:
            ax.annotate("", xy=(x - 0.065, 0.5), xytext=(xs[i - 1] + 0.065, 0.5),
                        arrowprops=dict(arrowstyle="->", color="#2b5c8a"))
    ax.set_title("Schematic (no data)", fontsize=8, loc="left", color="grey")
    save(fig, "fig1_architecture_AN_v1.png", [MANIFEST], log)


def fig2(log):
    d = pd.read_csv(STYL)
    by = d.pivot_table(index="farm_id", columns="source", values="diff_tCO2e_2019_minus_2006", aggfunc="sum")
    tot = d.groupby("farm_id")[["ipcc2006_tCO2e", "ipcc2019_tCO2e"]].sum()
    pct = 100 * (tot.ipcc2019_tCO2e - tot.ipcc2006_tCO2e) / tot.ipcc2006_tCO2e
    order = pct.sort_values().index
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 7), sharey=True)
    by.loc[order].plot.barh(stacked=True, ax=a, width=0.8)
    a.axvline(0, color="k", lw=0.6)
    a.set_xlabel("Change, 2019 âˆ’ 2006 (t CO$_2$e yr$^{-1}$, AR5)")
    a.set_ylabel("")
    a.set_title("a", loc="left", fontweight="bold")
    a.legend(fontsize=7, frameon=False)
    b.barh(range(len(order)), pct.loc[order], color=np.where(pct.loc[order] >= 0, "#c0392b", "#2471a3"))
    b.axvline(0, color="k", lw=0.6)
    b.set_xlabel("Change in farm total (%)")
    b.set_title("b", loc="left", fontweight="bold")
    save(fig, "fig2_stylized_2006_vs_2019_AN_v1.png", [STYL], log)
    return pct


def fig3(log):
    c = pd.read_csv(COUNTY, usecols=["variant", "fips", "t_co2e_2006", "t_co2e_2019"])
    c = c[c.variant == COUNTY_VARIANT].groupby("fips")[["t_co2e_2006", "t_co2e_2019"]].sum()
    c = c[c.t_co2e_2006 > 0]
    p = 100 * (c.t_co2e_2019 / c.t_co2e_2006 - 1)
    n = pd.read_csv(NAT, comment="#")
    n = n[(n.variant == COUNTY_VARIANT) & (n.category != "total_in_scope")]
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    a.hist(p.clip(-60, 60), bins=np.arange(-60, 62, 2), color="#7f8c8d")
    a.axvline(p.median(), color="#c0392b", lw=1, label=f"median {p.median():+.1f}% (n={len(p):,})")
    a.set_xlabel("County change in in-scope total, 2019 vs 2006 (%; clipped at Â±60)")
    a.set_ylabel("Counties")
    a.legend(frameon=False, fontsize=8)
    a.set_title("a  (distribution; county map pending: no boundary file in repo)", loc="left",
                fontsize=9, fontweight="bold")
    x = np.arange(len(n))
    w = 0.27
    b.bar(x - w, n.ghgsim_2006_MMT_CO2e, w, label="ghgsim IPCC 2006")
    b.bar(x, n.ghgsim_2019_MMT_CO2e, w, label="ghgsim IPCC 2019")
    b.bar(x + w, n["EPA_2025ed_Table5-1_2022_MMT_CO2e"], w, label="EPA 2025 ed., 2022", color="k")
    b.set_xticks(x, n.category.str.replace("_", " "))
    b.set_ylabel("Mt CO$_2$e (AR5)")
    b.legend(frameon=False, fontsize=8)
    b.set_title("b  (consistency check, not validation)", loc="left", fontsize=9, fontweight="bold")
    save(fig, "fig3_us_county_and_epa_AN_v1.png", [COUNTY, NAT], log)
    return {"n": int(len(p)), "median": float(p.median()), "up": int((p > 0).sum()), "down": int((p < 0).sum()),
            "p05": float(p.quantile(.05)), "p95": float(p.quantile(.95))}


def fig4(log):
    z = pd.read_csv(ZONE)
    z["group"] = np.where(z.source.str.startswith("soil"), "soil N2O",
                          np.where(z.source == "enteric", "enteric CH4",
                                   np.where(z.source == "manure_ch4", "manure CH4", "manure N2O")))
    t = z.pivot_table(index="zone_method", columns="group", values="ghgsim_2019_MMT_CO2e", aggfunc="sum")
    t = t.loc[["zone_primary", "zone_hargreaves", "zone_thornthwaite"]]
    t.index = ["IPCC 2019 map", "Hargreaves", "Thornthwaite"]
    fig, ax = plt.subplots(figsize=(7, 4))
    t.plot.bar(ax=ax, rot=0)
    ax.set_ylabel("2019-edition emissions, disclosed counties (Mt CO$_2$e)")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "fig4_zone_sensitivity_AN_v1.png", [ZONE], log)
    return t


def fig5(log):
    rows = []
    for f in INV:
        r = pd.read_csv(f)
        r = r[r.category.str.contains("Agriculture")]
        rows += [(x.iso, int(x.year), float(x.difference_pct)) for x in r.itertuples()]
    u = pd.read_csv(USREC)
    tot = u[u.key.str.lower().isin(["agriculture", "total agriculture", "total"])]
    if tot.empty:
        tot = u[~u.key.str.contains(":")].groupby("year")[["ed2024", "ed2025"]].sum().reset_index()
    else:
        tot = tot.groupby("year")[["ed2024", "ed2025"]].sum().reset_index()
    for x in tot.itertuples():
        rows.append(("USA*", int(x.year), 100 * (x.ed2025 - x.ed2024) / x.ed2024))
    r = pd.DataFrame(rows, columns=["iso", "year", "pct"]).pivot(index="iso", columns="year", values="pct")
    fig, ax = plt.subplots(figsize=(8, 4))
    r.plot.bar(ax=ax, rot=0)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("Agriculture: latest âˆ’ previous submission (%)")
    ax.set_xlabel("*USA: EPA 2025 vs 2024 editions (gases summed; years 1990, 2005, 2022)")
    ax.legend(title="Inventory year", frameon=False, fontsize=8)
    save(fig, "fig5_inventory_recalculations_AN_v1.png", INV + [USREC], log)
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    log = {}
    fig1(log)
    pct = fig2(log)
    s3 = fig3(log)
    t4 = fig4(log)
    r5 = fig5(log)
    checks = {"fig2_pct_range": [float(pct.min()), float(pct.max())], "fig3": s3,
              "fig4_soil_n2o": t4["soil N2O"].round(1).to_dict(), "fig5": r5.round(2).to_dict()}
    mp = os.path.join(OUT, "paperB_figures_manifest_AN_v1.json")
    if os.path.exists(mp):
        raise SystemExit(f"refusing to overwrite {mp}")
    json.dump({"inputs_sha256": log, "checks": checks}, open(mp, "w"), indent=2, default=str)
    print(json.dumps(checks, indent=1, default=str))


if __name__ == "__main__":
    main()
