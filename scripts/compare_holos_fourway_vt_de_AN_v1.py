#!/usr/bin/env python3
"""Four-way VT/DE comparison: IPCC 2006, IPCC 2019, Holos Canada, Holos US.

Holos Canada has no published adult GE/VS in holos_params_canada_AN_v3.csv.
This run therefore uses EPA Annex 3.11 county activity (GE, VS, Nex, systems,
head, soil N) with Canada Ym/B0/MCF. That hybrid is labelled in the output.

IPCC 2019 manure is run with livingghg v3 because ghgsim v4 has enteric and
soil 2019 only.

Usage (from repository root):
    python3 scripts/compare_holos_fourway_vt_de_AN_v1.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from holos_vt_de_runner_AN_v1 import (  # noqa: E402
    GWP_AR5,
    holos_compute_params,
    load_epa_assumptions,
    load_registries,
    load_vt_de_counties,
    run_holos_farm,
    run_ipcc2006_v4,
    run_ipcc2019_v3,
    v3_farm_from_row,
)

COMMAND = "python3 scripts/compare_holos_fourway_vt_de_AN_v1.py"
COUNTY_CSV = ROOT / "data" / "holos_fourway_vt_de_AN_v1.csv"
SUMMARY_CSV = ROOT / "data" / "holos_fourway_vt_de_summary_AN_v1.csv"
META_JSON = ROOT / "data" / "holos_fourway_vt_de_AN_v1.meta.json"
METHODS = ("IPCC2006", "IPCC2019", "HolosCanada", "HolosUS")


def _pct(a: float, b: float) -> float:
    if b == 0.0:
        return 0.0 if a == 0.0 else float("nan")
    return 100.0 * (a - b) / b


def compare() -> tuple[pd.DataFrame, pd.DataFrame]:
    epa = load_epa_assumptions()
    counties = load_vt_de_counties()
    regs = load_registries()
    params_canada = holos_compute_params(regs, mcf_set="holos_canada")
    params_us = holos_compute_params(regs, mcf_set="holos_us")
    rows = []
    for _, row in counties.iterrows():
        farm = v3_farm_from_row(row, epa)
        state = str(row["STATE_ALPHA"])
        beef_ym = float(epa["states"][state]["beef"]["Ym_pct"])
        ipcc2006 = run_ipcc2006_v4(farm, regs["ipcc"])
        ipcc2019 = run_ipcc2019_v3(farm)
        holos_ca = run_holos_farm(
            farm,
            params_canada,
            forks={},
            pathway="epa_vs",
            ym_dairy_mode="fork_default",
            beef_ym=None,
            climate_zone="temperate",
        )
        holos_us = run_holos_farm(
            farm,
            params_us,
            forks={},
            pathway="epa_vs",
            ym_dairy_mode="epa_state",
            beef_ym=beef_ym,
            climate_zone="15C",
        )
        rec = {
            "command": COMMAND,
            "fips": row["fips"],
            "state": state,
            "county": row["COUNTY_NAME"],
            "milk_cows": row["milk_cows"],
            "beef_cows": row["beef_cows"],
            "evidence": "MEASURED",
            "IPCC2006_CH4_kg": ipcc2006["CH4_kg"],
            "IPCC2006_N2O_kg": ipcc2006["N2O_kg"],
            "IPCC2006_CO2e_t": ipcc2006["CO2e_t"],
            "IPCC2019_CH4_kg": ipcc2019["CH4_kg"],
            "IPCC2019_N2O_kg": ipcc2019["N2O_kg"],
            "IPCC2019_CO2e_t": ipcc2019["CO2e_t"],
            "HolosCanada_CH4_kg": holos_ca["CH4_kg"],
            "HolosCanada_N2O_kg": holos_ca["N2O_kg"],
            "HolosCanada_CO2e_t": holos_ca["CO2e_t"],
            "HolosCanada_CH4_enteric_kg": holos_ca["CH4_enteric_kg"],
            "HolosCanada_CH4_manure_kg": holos_ca["CH4_manure_kg"],
            "HolosUS_CH4_kg": holos_us["CH4_kg"],
            "HolosUS_N2O_kg": holos_us["N2O_kg"],
            "HolosUS_CO2e_t": holos_us["CO2e_t"],
            "HolosUS_CH4_enteric_kg": holos_us["CH4_enteric_kg"],
            "HolosUS_CH4_manure_kg": holos_us["CH4_manure_kg"],
            "csv_IPCC2006_CO2e_t": row["IPCC2006_CO2e_t"],
            "csv_IPCC2019_CO2e_t": row["IPCC2019_CO2e_t"],
        }
        for method in ("IPCC2019", "HolosCanada", "HolosUS"):
            for gas, unit in (("CH4", "kg"), ("N2O", "kg"), ("CO2e", "t")):
                a = rec[f"{method}_{gas}_{unit}"]
                b = rec[f"IPCC2006_{gas}_{unit}"]
                rec[f"{method}_minus_IPCC2006_{gas}_pct"] = _pct(a, b)
        rec["IPCC2006_vs_csv_CO2e_rel"] = _pct(rec["IPCC2006_CO2e_t"], rec["csv_IPCC2006_CO2e_t"])
        rec["IPCC2019_vs_csv_CO2e_rel"] = _pct(rec["IPCC2019_CO2e_t"], rec["csv_IPCC2019_CO2e_t"])
        rows.append(rec)
    df = pd.DataFrame(rows)
    summary_rows = []
    for method in METHODS:
        ch4 = float(df[f"{method}_CH4_kg"].sum())
        n2o = float(df[f"{method}_N2O_kg"].sum())
        co2e = float(df[f"{method}_CO2e_t"].sum())
        row = {
            "command": COMMAND,
            "method": method,
            "n_counties": int(df["fips"].nunique()),
            "evidence": "MEASURED",
            "sum_CH4_kg": ch4,
            "sum_N2O_kg": n2o,
            "sum_CO2e_t": co2e,
        }
        if method != "IPCC2006":
            b_ch4 = float(df["IPCC2006_CH4_kg"].sum())
            b_n2o = float(df["IPCC2006_N2O_kg"].sum())
            b_co2e = float(df["IPCC2006_CO2e_t"].sum())
            row["minus_IPCC2006_CH4_pct"] = _pct(ch4, b_ch4)
            row["minus_IPCC2006_N2O_pct"] = _pct(n2o, b_n2o)
            row["minus_IPCC2006_CO2e_pct"] = _pct(co2e, b_co2e)
        else:
            row["minus_IPCC2006_CH4_pct"] = 0.0
            row["minus_IPCC2006_N2O_pct"] = 0.0
            row["minus_IPCC2006_CO2e_pct"] = 0.0
        summary_rows.append(row)
    return df, pd.DataFrame(summary_rows)


def main() -> None:
    df, summary = compare()
    COUNTY_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(COUNTY_CSV, index=False)
    summary.to_csv(SUMMARY_CSV, index=False)
    meta = {
        "command": COMMAND,
        "date": date.today().isoformat(),
        "n_counties": int(df["fips"].nunique()),
        "gwp": GWP_AR5,
        "methods": {
            "IPCC2006": "ghgsim v4 IPCC 2006 modules; EPA GE/Ym/VS/Nex (exact-reproduction farm)",
            "IPCC2019": "livingghg v3 engine IPCC2019 (v4 has no manure 2019 module)",
            "HolosCanada": (
                "Holos modules; EPA GE/VS/Nex/systems; Canada Ym dairy 5.6 and beef "
                "medium 6.3; Canada B0 and MCF (temperate with cool fallback). "
                "Hybrid: Canada file has no adult GE/VS."
            ),
            "HolosUS": (
                "Holos modules; EPA JSON GE/Ym/VS/Nex/systems; Holos US MCF/B0 overlay. "
                "Uses county_assumptions_AN_v3.json, not holos_params_us_AN_v2.csv DE GE/Ym "
                "where those two files disagree."
            ),
        },
        "max_IPCC2006_vs_csv_CO2e_rel": float(df["IPCC2006_vs_csv_CO2e_rel"].abs().max()),
        "max_IPCC2019_vs_csv_CO2e_rel": float(df["IPCC2019_vs_csv_CO2e_rel"].abs().max()),
        "county_csv": str(COUNTY_CSV.relative_to(ROOT)),
        "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
    }
    META_JSON.write_text(json.dumps(meta, indent=2) + "\n")
    print(COMMAND)
    print(summary.to_string(index=False))
    print("max IPCC2006 vs committed CSV CO2e rel %:", meta["max_IPCC2006_vs_csv_CO2e_rel"])
    print("max IPCC2019 vs committed CSV CO2e rel %:", meta["max_IPCC2019_vs_csv_CO2e_rel"])
    print(f"wrote {COUNTY_CSV}")
    print(f"wrote {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
