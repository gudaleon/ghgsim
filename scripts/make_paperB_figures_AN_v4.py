"""Paper B figures (AN_v4): Fig. 5 v3 with eight CRT inventories (six comparators + Russia and EU extras).

Inputs: data/inventories_AN_v2/*_recalc_AN_v2.csv (scripts/fetch_inventories_AN_v2.py) and the US EPA
edition comparison (data/inventories_US_AN_v1). The EU CRT Table 8s1 is empty, so the EU has no bar
(its sector totals are in EUA_table3_AN_v2.csv). Other figures stay at their AN_v2/AN_v3 versions.
Usage: python scripts/make_paperB_figures_AN_v4.py
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("figs_v1", os.path.join(HERE, "make_paperB_figures_AN_v1.py"))
v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v1)

INV2 = sorted(glob.glob(os.path.join(os.path.dirname(HERE), "data", "inventories_AN_v2", "*_recalc_AN_v2.csv")))
ORDER = ["AUS", "CAN", "DEU", "GBR", "IRL", "NZL", "RUS", "USA"]


def fig5_v3(log):
    rows = []
    for f in INV2:
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
    p = p.loc[[i for i in ORDER if i in p.index], ["1990", "2005", "Latest year (2023; USA 2022)"]]
    p.index = [i + "*" if i == "RUS" else i for i in p.index]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    p.plot.bar(ax=ax, rot=0)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("Agriculture, latest \u2212 previous\nsubmission (%)")
    ax.set_xlabel("USA: EPA 2025 vs 2024 editions; others: 2026 vs 2025 CRT submissions. "
                  "*extra comparison; EU: no Table 8 data")
    ax.legend(title="Inventory year", frameon=False, fontsize=8, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    v1.save(fig, "fig5_inventory_recalculations_AN_v3.png", INV2 + [v1.USREC], log)
    return p.round(2).to_dict()


def main():
    log = {}
    checks = {"5": fig5_v3(log)}
    mp = os.path.join(v1.OUT, "paperB_figures_manifest_AN_v4.json")
    if os.path.exists(mp):
        raise SystemExit(f"refusing to overwrite {mp}")
    json.dump({"inputs_sha256": log, "checks": checks}, open(mp, "w"), indent=2)
    print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
