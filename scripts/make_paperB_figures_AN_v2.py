"""Paper B figures (AN_v2): all five figures, Fig. 3a now a county choropleth.

Reuses the AN_v1 functions for data handling and replaces Fig. 3a with a map.
Boundary file (not in git): US Census cartographic boundary counties 2023, 1:20m
  URL    https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_20m.zip
  SHA256 479956f6e3cb1573705c1ceb35d17ca7cd1b5179f3947ee6adbaa274b7e931e4
Set GHGSIM_BOUNDARIES to its folder (default D:/ghgsim-data/boundaries).
Usage: python scripts/make_paperB_figures_AN_v2.py [fig ...]   (default: all)
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import TwoSlopeNorm  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("figs_v1", os.path.join(HERE, "make_paperB_figures_AN_v1.py"))
v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v1)

BDIR = os.environ.get("GHGSIM_BOUNDARIES", "D:/ghgsim-data/boundaries")
BZIP = os.path.join(BDIR, "cb_2023_us_county_20m.zip")
BSHA = "479956f6e3cb1573705c1ceb35d17ca7cd1b5179f3947ee6adbaa274b7e931e4"
EXCLUDE_STATEFP = {"60", "66", "69", "72", "78"}  # territories and Puerto Rico: not in the run
ALBERS = "EPSG:5070"
CLIP = 60


def county_pct():
    c = pd.read_csv(v1.COUNTY, usecols=["variant", "fips", "t_co2e_2006", "t_co2e_2019"])
    g = c.groupby(["variant", "fips"])[["t_co2e_2006", "t_co2e_2019"]].sum()
    a = g.loc[v1.COUNTY_VARIANT]
    dis = g.loc["disclosed"]
    a = a[a.t_co2e_2006 > 0]
    pct = 100 * (a.t_co2e_2019 / a.t_co2e_2006 - 1)
    # counties whose D_allocated total differs from the disclosed total got allocated withheld values
    alloc = (a.t_co2e_2019 - dis.reindex(a.index).t_co2e_2019.fillna(0)).abs() > 1e-6
    out = pd.DataFrame({"pct": pct, "allocated": alloc})
    out.index = out.index.map(lambda f: f"{int(f):05d}")
    return out


def draw(ax, gdf, norm, cmap):
    has = gdf[gdf.pct.notna()]
    has.plot(column=has.pct.clip(-CLIP, CLIP), cmap=cmap, norm=norm, ax=ax, linewidth=0.05, edgecolor="white")
    nod = gdf[gdf.pct.isna()]
    if len(nod):
        nod.plot(ax=ax, facecolor="#dddddd", edgecolor="#777777", hatch="////", linewidth=0.05)
    ax.set_axis_off()


def fig3_v2(log):
    if v1.sha(BZIP) != BSHA:
        raise SystemExit("boundary file hash mismatch")
    g = gpd.read_file(f"zip://{BZIP}")
    g = g[~g.STATEFP.isin(EXCLUDE_STATEFP)].copy()
    d = county_pct()
    g = g.merge(d, left_on="GEOID", right_index=True, how="left")
    g["allocated"] = g.allocated.fillna(False).astype(bool)
    cmap = plt.get_cmap("RdBu_r")
    norm = TwoSlopeNorm(vmin=-CLIP, vcenter=0, vmax=CLIP)
    fig = plt.figure(figsize=(12, 9))
    a = fig.add_axes([0.02, 0.42, 0.96, 0.56])
    l48 = g[~g.STATEFP.isin({"02", "15"})].to_crs(ALBERS)
    draw(a, l48, norm, cmap)
    fig.text(0.08, 0.97, "a", fontweight="bold", fontsize=11)
    ak = fig.add_axes([0.03, 0.43, 0.2, 0.15])
    draw(ak, g[g.STATEFP == "02"].to_crs("EPSG:3338"), norm, cmap)
    hi = fig.add_axes([0.24, 0.43, 0.1, 0.08])
    draw(hi, g[g.STATEFP == "15"].to_crs("ESRI:102007"), norm, cmap)
    cax = fig.add_axes([0.42, 0.44, 0.3, 0.015])
    cax.xaxis.set_label_position("top")
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal", extend="both")
    cb.set_label("Change in in-scope total, 2019 vs 2006 (%; clipped at ±60)", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    fig.legend(handles=[Patch(facecolor="#dddddd", edgecolor="#777777", hatch="////",
                              label="No estimate, or county code not in 2023 boundaries (e.g. Connecticut)")],
               loc="lower left", bbox_to_anchor=(0.40, 0.375), frameon=False, fontsize=8)
    n = pd.read_csv(v1.NAT, comment="#")
    n = n[(n.variant == v1.COUNTY_VARIANT) & (n.category != "total_in_scope")]
    b = fig.add_axes([0.08, 0.05, 0.86, 0.3])
    x = np.arange(len(n))
    w = 0.27
    b.bar(x - w, n.ghgsim_2006_MMT_CO2e, w, label="ghgsim, IPCC 2006", color="#95a5a6")
    b.bar(x, n.ghgsim_2019_MMT_CO2e, w, label="ghgsim, IPCC 2019", color="#2471a3")
    b.bar(x + w, n["EPA_2025ed_Table5-1_2022_MMT_CO2e"], w, label="EPA inventory (2025 ed.), 2022", color="k")
    labels = {"enteric_CH4": "Enteric CH$_4$", "manure_CH4": "Manure CH$_4$", "manure_N2O": "Manure N$_2$O",
              "soil_N2O": "Soil N$_2$O"}
    b.set_xticks(x, [labels.get(c, c) for c in n.category])
    b.set_ylabel("Mt CO$_2$e yr$^{-1}$ (AR5)")
    b.legend(frameon=False, fontsize=8)
    b.spines[["top", "right"]].set_visible(False)
    b.set_title("b  National sums vs EPA (consistency check, not validation)", loc="left", fontsize=10,
                fontweight="bold")
    path = os.path.join(v1.OUT, "fig3_us_county_and_epa_AN_v2.png")
    if os.path.exists(path):
        raise SystemExit(f"refusing to overwrite {path}")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    log["fig3_us_county_and_epa_AN_v2.png"] = {"data/us_county_2006_vs_2019_AN_v2.csv.gz": v1.sha(v1.COUNTY),
                                               "data/us_national_2006_vs_2019_vs_epa_AN_v2.csv": v1.sha(v1.NAT),
                                               "boundary:cb_2023_us_county_20m.zip": BSHA}
    return {"mapped": int(g.pct.notna().sum()), "no_estimate": int(g.pct.isna().sum()),
            "allocated": int(g.allocated.sum()), "median": float(d.pct.median())}


def save(fig, name, inputs, log):
    v1.save(fig, name, inputs, log)


def fig1_v2(log):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    steps = ["Upstream sources\n(fingerprinted weekly)", "Versioned inputs", "ghgsim engine",
             "One-command recompute\n+ results manifest", "Diff report\n(why numbers moved)",
             "Readers: dashboard\n+ paper agent"]
    pos = [(0.17, 0.72), (0.5, 0.72), (0.83, 0.72), (0.83, 0.28), (0.5, 0.28), (0.17, 0.28)]
    for (x, y), t in zip(pos, steps, strict=True):
        ax.text(x, y, t, ha="center", va="center", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.6", fc="#e8f0fa", ec="#2b5c8a"))
    for (x0, y0), (x1, y1) in zip(pos[:-1], pos[1:], strict=True):
        dx = 0.12 if x1 > x0 else (-0.12 if x1 < x0 else 0)
        dy = -0.1 if y1 < y0 else 0
        ax.annotate("", xy=(x1 - dx, y1 - dy), xytext=(x0 + dx, y0 + dy),
                    arrowprops=dict(arrowstyle="->", color="#2b5c8a", lw=1.5))
    ax.text(0, 1, "Schematic (no data)", fontsize=8, color="grey", va="top")
    save(fig, "fig1_architecture_AN_v2.png", [v1.MANIFEST], log)


LAB = {"enteric_CH4": "Enteric CH$_4$", "manure_CH4": "Manure CH$_4$", "manure_N2O": "Manure N$_2$O",
       "soil_N2O": "Soil N$_2$O"}


def fig2_v2(log):
    d = pd.read_csv(v1.STYL)
    by = d.pivot_table(index="farm_id", columns="source", values="diff_tCO2e_2019_minus_2006", aggfunc="sum")
    tot = d.groupby("farm_id")[["ipcc2006_tCO2e", "ipcc2019_tCO2e"]].sum()
    pct = 100 * (tot.ipcc2019_tCO2e - tot.ipcc2006_tCO2e) / tot.ipcc2006_tCO2e
    order = pct.sort_values().index
    by = by.loc[order].rename(columns=LAB)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 7), sharey=True)
    by.plot.barh(stacked=True, ax=a, width=0.8)
    a.set_yticks(range(len(order)), [o.replace("_", " ") for o in order])
    a.axvline(0, color="k", lw=0.6)
    a.set_xlabel("Change, 2019 − 2006 (t CO$_2$e yr$^{-1}$, AR5)")
    a.set_ylabel("")
    a.set_title("a", loc="left", fontweight="bold")
    a.legend(fontsize=8, frameon=False, loc="lower right")
    vals = pct.loc[order]
    b.barh(range(len(order)), vals, color=np.where(vals >= 0, "#c0392b", "#2471a3"))
    b.axvline(0, color="k", lw=0.6)
    b.set_xlabel("Change in farm total (%)")
    b.set_title("b", loc="left", fontweight="bold")
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "fig2_stylized_2006_vs_2019_AN_v2.png", [v1.STYL], log)
    return [float(pct.min()), float(pct.max())]


def fig4_v2(log):
    z = pd.read_csv(v1.ZONE)
    z["group"] = np.where(z.source.str.startswith("soil"), "Soil N$_2$O",
                          np.where(z.source == "enteric", "Enteric CH$_4$",
                                   np.where(z.source == "manure_ch4", "Manure CH$_4$", "Manure N$_2$O")))
    t = z.pivot_table(index="zone_method", columns="group", values="ghgsim_2019_MMT_CO2e", aggfunc="sum")
    t = t.loc[["zone_primary", "zone_hargreaves", "zone_thornthwaite"],
              ["Enteric CH$_4$", "Manure CH$_4$", "Manure N$_2$O", "Soil N$_2$O"]]
    t.index = ["IPCC 2019 map", "Hargreaves PET", "Thornthwaite PET"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    t.plot.bar(ax=ax, rot=0)
    ax.set_ylabel("Mt CO$_2$e yr$^{-1}$ (AR5)")
    ax.set_title("2019-edition emissions, disclosed counties, by climate-zone method", fontsize=10, loc="left")
    ax.set_ylim(0, 165)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "fig4_zone_sensitivity_AN_v2.png", [v1.ZONE], log)
    return t.round(1).to_dict()


def fig5_v2(log):
    rows = []
    for f in v1.INV:
        r = pd.read_csv(f)
        r = r[r.category.str.contains("Agriculture")]
        rows += [(x.iso, int(x.year), float(x.difference_pct)) for x in r.itertuples()]
    u = pd.read_csv(v1.USREC)
    u = u[~u.key.str.contains(":")].groupby("year")[["ed2024", "ed2025"]].sum()
    for y, x in u.iterrows():
        rows.append(("USA", int(y), float(100 * (x.ed2025 - x.ed2024) / x.ed2024)))
    r = pd.DataFrame(rows, columns=["iso", "year", "pct"])
    r["col"] = r.year.map(lambda y: str(y) if y in (1990, 2005) else "Latest year (2023; USA 2022)")
    p = r.pivot(index="iso", columns="col", values="pct")
    p = p[["1990", "2005", "Latest year (2023; USA 2022)"]]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    p.plot.bar(ax=ax, rot=0)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("Agriculture, latest − previous\nsubmission (%)")
    ax.set_xlabel("USA: EPA 2025 vs 2024 editions; others: 2026 vs 2025 CRT submissions")
    ax.legend(title="Inventory year", frameon=False, fontsize=8, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "fig5_inventory_recalculations_AN_v2.png", v1.INV + [v1.USREC], log)
    return p.round(2).to_dict()


FIGS = {"1": fig1_v2, "2": fig2_v2, "3": fig3_v2, "4": fig4_v2, "5": fig5_v2}


def main():
    want = sys.argv[1:] or ["1", "2", "3", "4", "5"]
    log, checks = {}, {}
    for k in want:
        checks[k] = FIGS[k](log)
    mp = os.path.join(v1.OUT, "paperB_figures_manifest_AN_v2.json")
    if os.path.exists(mp):
        raise SystemExit(f"refusing to overwrite {mp}")
    json.dump({"inputs_sha256": log, "checks": checks}, open(mp, "w"), indent=2)
    print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
