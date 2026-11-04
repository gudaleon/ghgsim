"""IPCC 2006 vs 2019 stylized-farm comparison, AN_v3: climate-specific manure EF4 (DECISIONS_AN_v21).

Identical to compare_ipcc_2006_2019_stylized_AN_v2.py except that ipcc2019.manure >= 2.1.0 applies the
2019 Refinement Vol 4 Ch11 Table 11.3 (Updated) EF4 by climate (wet 0.014 / dry 0.005) to manure NH3+NOx
volatilisation, consistent with ipcc2019.soil_n2o. The stylized farms are warm_temperate_moist -> wet, 0.014.

  --ef4-mode climate     (default) -> data/ipcc_2006_vs_2019_stylized_AN_v3.csv
  --ef4-mode aggregated  (0.010 sensitivity) -> data/ipcc_2006_vs_2019_stylized_ef4agg_AN_v3.csv
Refuses to overwrite.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("cmp_v2", ROOT / "scripts" / "compare_ipcc_2006_2019_stylized_AN_v2.py")
v2 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(v2)

OUT = {"climate": ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v3.csv",
       "aggregated": ROOT / "data" / "ipcc_2006_vs_2019_stylized_ef4agg_AN_v3.csv"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ef4-mode", choices=sorted(OUT), default="climate")
    a = ap.parse_args()
    out = OUT[a.ef4_mode]
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    from ghgsim.modules.ipcc2019.manure import IPCC2019Manure
    orig = IPCC2019Manure.compute

    def compute(self, inputs, params):
        return orig(self, {**inputs, "ef4_mode": a.ef4_mode}, params)

    IPCC2019Manure.compute = compute
    v2.OUT_CSV = out
    v2.main()


if __name__ == "__main__":
    main()
