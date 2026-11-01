#!/usr/bin/env python3
"""Measure per-fork CH4/N2O/CO2e deltas on the 17 VT/DE counties.

Runs Holos modules on the livingghg v3 county farm assembly (EPA Annex 3.11
GE/VS/Nex/systems; mature cows only). Toggles each registered fork one at a
time against the registered default.

Does not invent TDN, forage%, calf counts, cover types, or net-energy diets.

Usage (from repository root):
    python3 scripts/measure_holos_forks_vt_de_AN_v1.py
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
    fork_catalog,
    holos_compute_params,
    load_epa_assumptions,
    load_registries,
    load_vt_de_counties,
    run_holos_farm,
    v3_farm_from_row,
)

COMMAND = "python3 scripts/measure_holos_forks_vt_de_AN_v1.py"
COUNTY_CSV = ROOT / "data" / "holos_fork_deltas_vt_de_AN_v1.csv"
SUMMARY_CSV = ROOT / "data" / "holos_fork_deltas_vt_de_summary_AN_v1.csv"
META_JSON = ROOT / "data" / "holos_fork_deltas_vt_de_AN_v1.meta.json"

# Dataset facts that make a fork inactive even when the option is toggled.
INACTIVE_REASON = {
    "HOLOS.GE.digestibility": (
        "MEASURED_ZERO: GE_MJ_day override is always supplied; Eq 10.3 TDN/DE "
        "denominator is not evaluated. County dataset has no NE inputs."
    ),
    "HOLOS.ENTERIC.calf_zero": (
        "MEASURED_ZERO: EPA assumptions scope is mature cows only (no calves)."
    ),
    "HOLOS.VS.digestibility": (
        "MEASURED_ZERO: epa_vs pathway uses EPA VS_kg_day override. eq1024_vs "
        "sets TDN=DE because TDN is not independently observed."
    ),
    "HOLOS.VS.urinary_energy": (
        "MEASURED_ZERO: epa_vs pathway uses EPA VS override. eq1024_vs uses EPA "
        "DE% 66.7 dairy / 62.5 beef (both <80%) and default forage 100% (grain 0%), "
        "so IPCC UE and Holos-grain UE are both 0.04."
    ),
    "HOLOS.VS.calf_coeff": (
        "MEASURED_ZERO: EPA assumptions scope is mature cows only (no calves)."
    ),
    "HOLOS.CH4.cover_reduction": (
        "MEASURED_ZERO: EPA liquid/slurry mapped to liquid_nocrust; cover_type=none. "
        "No natural_crust or other_cover in the county dataset."
    ),
    "HOLOS.NEX.calf_nrate": (
        "MEASURED_ZERO: EPA assumptions scope is mature cows only (no calves)."
    ),
}


def _pct(delta: float, baseline: float) -> float:
    if baseline == 0.0:
        return 0.0 if delta == 0.0 else float("nan")
    return 100.0 * delta / baseline


def measure() -> tuple[pd.DataFrame, pd.DataFrame]:
    epa = load_epa_assumptions()
    counties = load_vt_de_counties()
    regs = load_registries()
    params = holos_compute_params(regs, mcf_set="ipcc15C")
    forks = fork_catalog()
    pathways = ("epa_vs", "eq1024_vs")
    rows: list[dict] = []

    for _, row in counties.iterrows():
        farm = v3_farm_from_row(row, epa)
        state = str(row["STATE_ALPHA"])
        dairy_ym_epa = float(epa["states"][state]["dairy"]["Ym_pct"])
        beef_ym_epa = float(epa["states"][state]["beef"]["Ym_pct"])
        for pathway in pathways:
            baseline = run_holos_farm(
                farm,
                params,
                forks={},
                pathway=pathway,
                ym_dairy_mode="fork_default",
                beef_ym=beef_ym_epa,
                climate_zone="15C",
            )
            rows.append(
                {
                    "command": COMMAND,
                    "fips": row["fips"],
                    "state": state,
                    "county": row["COUNTY_NAME"],
                    "pathway": pathway,
                    "fork_id": "BASELINE",
                    "option": "registered_defaults",
                    "evidence": "MEASURED",
                    "inactive_reason": "",
                    "epa_dairy_Ym_pct": dairy_ym_epa,
                    "epa_beef_Ym_pct": beef_ym_epa,
                    **baseline,
                    "delta_CH4_kg": 0.0,
                    "delta_N2O_kg": 0.0,
                    "delta_CO2e_t": 0.0,
                    "delta_CH4_pct": 0.0,
                    "delta_N2O_pct": 0.0,
                    "delta_CO2e_pct": 0.0,
                    "delta_CH4_enteric_kg": 0.0,
                    "delta_CH4_manure_kg": 0.0,
                }
            )
            for fork in forks:
                alt = run_holos_farm(
                    farm,
                    params,
                    forks={fork["fork_id"]: fork["alt"]},
                    pathway=pathway,
                    ym_dairy_mode="fork_default",
                    beef_ym=beef_ym_epa,
                    climate_zone="15C",
                )
                d_ch4 = alt["CH4_kg"] - baseline["CH4_kg"]
                d_n2o = alt["N2O_kg"] - baseline["N2O_kg"]
                d_co2e = alt["CO2e_t"] - baseline["CO2e_t"]
                reason = INACTIVE_REASON.get(fork["fork_id"], "")
                if abs(d_ch4) > 1e-9 or abs(d_n2o) > 1e-9 or abs(d_co2e) > 1e-9:
                    reason = ""
                rows.append(
                    {
                        "command": COMMAND,
                        "fips": row["fips"],
                        "state": state,
                        "county": row["COUNTY_NAME"],
                        "pathway": pathway,
                        "fork_id": fork["fork_id"],
                        "option": fork["alt"],
                        "evidence": "MEASURED",
                        "inactive_reason": reason,
                        "epa_dairy_Ym_pct": dairy_ym_epa,
                        "epa_beef_Ym_pct": beef_ym_epa,
                        **alt,
                        "delta_CH4_kg": d_ch4,
                        "delta_N2O_kg": d_n2o,
                        "delta_CO2e_t": d_co2e,
                        "delta_CH4_pct": _pct(d_ch4, baseline["CH4_kg"]),
                        "delta_N2O_pct": _pct(d_n2o, baseline["N2O_kg"]),
                        "delta_CO2e_pct": _pct(d_co2e, baseline["CO2e_t"]),
                        "delta_CH4_enteric_kg": alt["CH4_enteric_kg"] - baseline["CH4_enteric_kg"],
                        "delta_CH4_manure_kg": alt["CH4_manure_kg"] - baseline["CH4_manure_kg"],
                    }
                )

    county_df = pd.DataFrame(rows)
    summaries = []
    for pathway in pathways:
        for fork in forks:
            sub = county_df[
                (county_df["pathway"] == pathway) & (county_df["fork_id"] == fork["fork_id"])
            ]
            base = county_df[
                (county_df["pathway"] == pathway) & (county_df["fork_id"] == "BASELINE")
            ]
            ch4_sum = float(sub["delta_CH4_kg"].sum())
            n2o_sum = float(sub["delta_N2O_kg"].sum())
            co2e_sum = float(sub["delta_CO2e_t"].sum())
            ch4_base = float(base["CH4_kg"].sum())
            n2o_base = float(base["N2O_kg"].sum())
            co2e_base = float(base["CO2e_t"].sum())
            enteric_sum = float(sub["delta_CH4_enteric_kg"].sum())
            manure_sum = float(sub["delta_CH4_manure_kg"].sum())
            enteric_base = float(base["CH4_enteric_kg"].sum())
            fired = bool(
                sub["delta_CH4_kg"].abs().max() > 1e-9
                or sub["delta_N2O_kg"].abs().max() > 1e-9
                or sub["delta_CO2e_t"].abs().max() > 1e-9
            )
            summaries.append(
                {
                    "command": COMMAND,
                    "pathway": pathway,
                    "fork_id": fork["fork_id"],
                    "default_option": fork["default"],
                    "alt_option": fork["alt"],
                    "label": fork["label"],
                    "issue_ref": fork["issue_ref"],
                    "n_counties": int(sub["fips"].nunique()),
                    "evidence": "MEASURED",
                    "fork_fired": fired,
                    "inactive_reason": "" if fired else INACTIVE_REASON.get(fork["fork_id"], ""),
                    "sum_baseline_CH4_kg": ch4_base,
                    "sum_delta_CH4_kg": ch4_sum,
                    "sum_delta_CH4_pct": _pct(ch4_sum, ch4_base),
                    "sum_delta_CH4_enteric_kg": enteric_sum,
                    "sum_delta_CH4_enteric_pct": _pct(enteric_sum, enteric_base),
                    "sum_delta_CH4_manure_kg": manure_sum,
                    "sum_baseline_N2O_kg": n2o_base,
                    "sum_delta_N2O_kg": n2o_sum,
                    "sum_delta_N2O_pct": _pct(n2o_sum, n2o_base),
                    "sum_baseline_CO2e_t": co2e_base,
                    "sum_delta_CO2e_t": co2e_sum,
                    "sum_delta_CO2e_pct": _pct(co2e_sum, co2e_base),
                    "max_abs_delta_CH4_pct": float(sub["delta_CH4_pct"].abs().max()),
                    "max_abs_delta_CO2e_pct": float(sub["delta_CO2e_pct"].abs().max()),
                }
            )
    summary_df = pd.DataFrame(summaries)
    return county_df, summary_df


def main() -> None:
    county_df, summary_df = measure()
    COUNTY_CSV.parent.mkdir(parents=True, exist_ok=True)
    county_df.to_csv(COUNTY_CSV, index=False)
    summary_df.to_csv(SUMMARY_CSV, index=False)
    meta = {
        "command": COMMAND,
        "date": date.today().isoformat(),
        "n_counties": int(county_df["fips"].nunique()),
        "gwp": GWP_AR5,
        "baseline": (
            "Holos modules, registered fork defaults, EPA GE/VS/Nex/systems, "
            "dairy Ym_canada=5.6, beef Ym=EPA state, MCF=IPCC 2006 15C"
        ),
        "pathways": {
            "epa_vs": "Manure CH4 uses EPA VS_kg_day override",
            "eq1024_vs": (
                "Manure CH4 uses IPCC Eq 10.24 VS from EPA GE and DE% with "
                "ASH=8% (IPCC example, SOURCE-TRACED); TDN set equal to DE"
            ),
        },
        "county_csv": str(COUNTY_CSV.relative_to(ROOT)),
        "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
    }
    META_JSON.write_text(json.dumps(meta, indent=2) + "\n")
    print(COMMAND)
    print(f"counties: {county_df['fips'].nunique()}")
    print(summary_df.to_string(index=False))
    print(f"wrote {COUNTY_CSV}")
    print(f"wrote {SUMMARY_CSV}")
    print(f"wrote {META_JSON}")


if __name__ == "__main__":
    main()
