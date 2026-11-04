"""Paper B figures (AN_v7): Fig. 6 v2, four-way consistency check with APSIM on a US Corn Belt site, DECISIONS_AN_v24.

Panels a-c compare the farms each outside model could run (n/a = model not run there; nothing is
filled in). Panel d is APSIM's daily N2O on the fertilised crop farm at the main site (Boone County,
Iowa: SSURGO soil, NASA POWER weather 1991-2020); panel e the Dalby sensitivity run; both against the constant daily rate implied by ghgsim's
2019 annual direct N2O. Consistency check, not validation.
Writes figures/fig6_four_way_AN_v2.png and figures/paperB_figures_manifest_AN_v7.json. Refuses to overwrite.
Usage: python scripts/make_paperB_figures_AN_v6.py
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures")
FIG = os.path.join(OUT, "fig6_four_way_AN_v2.png")
MAN = os.path.join(OUT, "paperB_figures_manifest_AN_v7.json")
IN = {
    "ghgsim": os.path.join(ROOT, "data", "ipcc_2006_vs_2019_stylized_AN_v3.csv"),
    "gleam": os.path.join(ROOT, "results", "gleam_vs_ghgsim_stylized_AN_v3.csv"),
    "hestia": os.path.join(ROOT, "data", "hestia_matched_vs_ipcc_stylized_AN_v3.csv"),
    "apsim_cmp": os.path.join(ROOT, "results", "apsim_vs_ghgsim_hestia_crop_AN_v2.csv"),
    "apsim_iowa": os.path.join(ROOT, "results", "apsim_AN_v2", "crop_urea_lime_iowa_AN_v2.Daily.csv.gz"),
    "apsim_dalby": os.path.join(ROOT, "results", "apsim_AN_v1", "crop_urea_lime_dalby_AN_v1.Daily.csv.gz"),
}
C = {"ghgsim 2006": "#9ecae1", "ghgsim 2019": "#2b5c8a", "GLEAM": "#e6550d", "HESTIA": "#31a354", "APSIM": "#756bb1"}


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rows(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get(rs, **kw):
    return next(r for r in rs if all(r[k] == v for k, v in kw.items()))


def bars(ax, labels, vals, title, ylabel, err=None):
    x = range(len(labels))
    for i, (lab, v) in enumerate(zip(labels, vals, strict=True)):
        key = next(k for k in C if lab.startswith(k))
        if v is None:
            ax.text(i, 0, "n/a", ha="center", va="bottom", fontsize=8, color="0.4")
            continue
        ax.bar(i, v, color=C[key], width=0.7)
        if err and err[i]:
            ax.errorbar(i, v, yerr=[[v - err[i][0]], [err[i][1] - v]], color="k", capsize=3, lw=1)
        ax.text(i, v, f"{v:.1f}" if v >= 10 else f"{v:.2f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=7.5)
    ax.set_title(title, fontsize=9, loc="left")
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(axis="y", labelsize=7.5)


def daily(p):
    with gzip.open(p, "rt", encoding="utf-8") as f:
        rs = list(csv.DictReader(f))
    d = [date.fromisoformat(r["Clock.Today"][:10]) for r in rs]
    return d, [float(r["N2O_N_kgha"]) for r in rs], [float(r["Weather.Rain"]) for r in rs]


def main():
    for p in (FIG, MAN):
        if os.path.exists(p):
            raise SystemExit(f"refusing to overwrite {p}")
    g, gl, h, a = (rows(IN[k]) for k in ("ghgsim", "gleam", "hestia", "apsim_cmp"))
    checks = {}
    fig = plt.figure(figsize=(10, 7.6))
    gs = fig.add_gridspec(3, 3, height_ratios=[1.15, 0.85, 0.85], hspace=0.75, wspace=0.38)
    labs = ["ghgsim 2006", "ghgsim 2019", "GLEAM 2019", "HESTIA", "APSIM"]
    # a dairy forage manure N2O
    f = "dairy_forage_uncovered"
    v = [float(get(g, farm_id=f, source="manure_N2O")["ipcc2006_kg"]), float(get(g, farm_id=f, source="manure_N2O")["ipcc2019_kg"]),
         float(get(gl, farm_id=f, factor_set="IPCC2019", source="manure_N2O")["gleam_kg"]),
         float(get(h, farm_id=f, source="manure_N2O")["hestia_kg"]), None]
    bars(fig.add_subplot(gs[0, 0]), labs, v, "a  Dairy (forage), manure N2O", "kg N2O per farm per year")
    checks["a"] = v
    # b beef pasture N2O
    f = "beef_pasture_field"
    gpas = get(gl, farm_id=f, factor_set="IPCC2019", source="pasture_N2O_vs_soil_N2O")
    v = [float(get(g, farm_id=f, source="soil_N2O")["ipcc2006_kg"]), float(get(g, farm_id=f, source="soil_N2O")["ipcc2019_kg"]),
         float(gpas["gleam_kg"]), float(get(h, farm_id=f, source="soil_N2O")["hestia_kg"]), None]
    bars(fig.add_subplot(gs[0, 1]), labs, v, "b  Beef on pasture, pasture N2O", "kg N2O per farm per year")
    checks["b"] = v
    # c crop farm direct N2O per ha
    ad = get(a, model="APSIM NG 2026.11.8142.0", basis="sensitivity: APSoil 900, Dalby weather (example as shipped)")
    ah = get(a, model="APSIM NG 2026.11.8142.0", basis="sensitivity: APSoil 900, Hamilton weather (warm temperate moist)")
    ai = get(a, basis="main: Boone County IA, SSURGO Webster + NASA POWER 1991-2020")
    labs_c = ["ghgsim 2006", "ghgsim 2019", "GLEAM", "HESTIA", "APSIM Iowa", "APSIM Dalby*", "APSIM Hamilton*"]
    v = [float(get(a, model="ghgsim IPCC 2006")["direct_N2O_kg_ha"]), float(get(a, model="ghgsim IPCC 2019")["direct_N2O_kg_ha"]), None,
         float(get(a, model="HESTIA CE 7.1.0 (models 0.90.0)")["direct_N2O_kg_ha"]),
         float(ai["direct_N2O_kg_ha"]), float(ad["direct_N2O_kg_ha"]), float(ah["direct_N2O_kg_ha"])]
    err = [None] * 4 + [(float(r["direct_N2O_kg_ha_min_year"]), float(r["direct_N2O_kg_ha_max_year"])) for r in (ai, ad, ah)]
    bars(fig.add_subplot(gs[0, 2]), labs_c, v, "c  Maize, 100 kg N/ha urea: direct N2O", "kg N2O per ha per year", err)
    checks["c"] = v
    # d/e daily APSIM N2O with rain
    rate = float(get(a, model="ghgsim IPCC 2019")["direct_N2O_kg_ha"]) * 28.0 / 44.0 / 365.0
    for row, key, lab in ((1, "apsim_iowa", "d  APSIM daily N2O, Boone County, Iowa (SSURGO Webster soil, NASA POWER weather)"), (2, "apsim_dalby", "e  Sensitivity: APSIM daily N2O, APSoil 900 with Dalby weather")):
        ax = fig.add_subplot(gs[row, :])
        d, n, r = daily(IN[key])
        ax.plot(d, n, color=C["APSIM"], lw=0.7, label="APSIM N2O-N (100 kg N/ha urea)")
        ax.axhline(rate, color=C["ghgsim 2019"], lw=1.0, ls="--", label="ghgsim 2019 annual direct N2O-N spread evenly")
        ax.set_ylabel("kg N2O-N/ha/day", fontsize=8)
        ax.tick_params(labelsize=7.5)
        ax2 = ax.twinx()
        ax2.bar(d, r, color="0.6", width=1.0, alpha=0.6)
        ax2.set_ylim(max(r) * 3, 0)
        ax2.set_ylabel("rain, mm/day", fontsize=8, color="0.4")
        ax2.tick_params(labelsize=7.5, colors="0.4")
        ax.set_title(lab, fontsize=9, loc="left")
        if row == 1:
            ax.legend(fontsize=7, loc="upper left", frameon=False)
        checks[key] = {"max_day": max(n), "constant_rate": rate}
    fig.text(0.01, 0.005, "Consistency check, not validation. n/a: model not run on that farm (GLEAM: cattle only; APSIM: crop only). "
             "Error bars: lowest and highest year (Iowa 29 sown years; *sensitivity runs, 10 years).", fontsize=7, color="0.3")
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(FIG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    with open(MAN, "w") as fh:
        json.dump({"inputs_sha256": {os.path.relpath(p, ROOT).replace("\\", "/"): sha(p) for p in IN.values()},
                   "outputs": {"figures/fig6_four_way_AN_v2.png": sha(FIG)}, "checks": checks}, fh, indent=2)
    print(json.dumps(checks))


if __name__ == "__main__":
    main()
