"""Paper B figures (AN_v5): Fig. 2 from data/ipcc_2006_vs_2019_stylized_AN_v3.csv (climate EF4, DECISIONS_AN_v21).

Reuses make_paperB_figures_AN_v3.fig2_v2 unchanged; only the input CSV and output names change.
Writes figures/fig2_stylized_2006_vs_2019_AN_v3.png and figures/paperB_figures_manifest_AN_v5.json. Refuses to overwrite.
Usage: python scripts/make_paperB_figures_AN_v5.py
"""
from __future__ import annotations

import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("figs_v3", os.path.join(HERE, "make_paperB_figures_AN_v3.py"))
v3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v3)
v3.v1.STYL = os.path.join(v3.v1.D, "ipcc_2006_vs_2019_stylized_AN_v3.csv")
FIG = "fig2_stylized_2006_vs_2019_AN_v3.png"
_save = v3.save


def save(fig, name, inputs, log):
    _save(fig, FIG if name.startswith("fig2_") else name, inputs, log)


v3.save = save


def main():
    for p in (os.path.join(v3.v1.OUT, FIG), os.path.join(v3.v1.OUT, "paperB_figures_manifest_AN_v5.json")):
        if os.path.exists(p):
            raise SystemExit(f"refusing to overwrite {p}")
    log = {}
    checks = {"2": v3.fig2_v2(log)}
    with open(os.path.join(v3.v1.OUT, "paperB_figures_manifest_AN_v5.json"), "w") as f:
        json.dump({"inputs_sha256": log, "checks": checks}, f, indent=2)
    print(json.dumps(checks))


if __name__ == "__main__":
    main()


