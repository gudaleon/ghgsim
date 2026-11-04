"""GLEAM consistency check against ghgsim with climate-specific manure EF4 (AN_v3, DECISIONS_AN_v22).

Identical to run_gleam_stylized_AN_v2.py (same unmodified GLEAM v0.8.0-alpha, same R driver, same
mapping) except:
- the ghgsim reference is data/ipcc_2006_vs_2019_stylized_AN_v3.csv (ipcc2019.manure >= 2.1.0,
  climate-specific EF4, DECISIONS_AN_v21);
- for IPCC2019 managed manure systems the EF4 passed to GLEAM is the one ghgsim's manure module
  applies (IPCC2019Manure._ef4 with the stylized climate zone, ef4_mode="climate"), checked in
  results/gleam_stylized_factor_check_AN_v3.csv.
Consistency check, not validation. No GLEAM code is copied. Refuses to overwrite.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("rg_v2", ROOT / "scripts" / "run_gleam_stylized_AN_v2.py")
v2 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(v2)

from ghgsim.modules.ipcc2019.manure import IPCC2019Manure  # noqa: E402

TAG = "AN_v3"
v2.TAG = TAG
v2.GHGSIM_RESULTS = ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v3.csv"
for _n, _stem in (
    ("F_INPUT", "gleam_stylized_inputs"),
    ("F_FRAC", "gleam_stylized_mms_fraction"),
    ("F_FACT", "gleam_stylized_mms_factors"),
    ("F_RAW", "gleam_stylized_cohort_results"),
    ("F_CMP", "gleam_vs_ghgsim_stylized"),
    ("F_MAN", "gleam_stylized_manifest"),
    ("F_CHECK", "gleam_stylized_factor_check"),
):
    setattr(v2, _n, v2.OUT / f"{_stem}_{TAG}.{'json' if _n == 'F_MAN' else 'csv'}")

_orig = v2.ghgsim_n_factors


def ghgsim_n_factors(reg, ver, at, system, climate):
    g = _orig(reg, ver, at, system, climate)
    if ver == "IPCC2019" and system != "pasture":
        p = v2.cmp.resolve(v2.cmp.MODULES[ver][1], reg)
        ef4, basis = IPCC2019Manure._ef4(p, v2.cmp.CLIMATE_ZONE_2019, "climate")
        g["n2o_ef4"] = (ef4, f"EF4 via IPCC2019Manure._ef4 ({basis}, zone {v2.cmp.CLIMATE_ZONE_2019})")
    return g


v2.ghgsim_n_factors = ghgsim_n_factors

if __name__ == "__main__":
    v2.main()
