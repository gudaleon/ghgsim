#!/usr/bin/env python3
"""Measure per-fork CH4/N2O/CO2e on the newest stylized_farms_AN_vN.yaml.

Does not overwrite AN_v1–AN_v3 outputs. Writes delta_CO2e_pct so the
fork-diagram loader can attach MEASURED ranges, including HOLOS.N2O.ef1.

Usage (from repository root):
    python3 scripts/measure_holos_forks_stylized_AN_v4.py
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

from ghgsim.report.emissions_sankey import (  # noqa: E402
    combined_forks,
    compute_stylized_farm_flows,
    fork_catalog,
    gwp_from_spec,
    load_stylized_spec,
    stylized_params,
)
from ghgsim.report.fork_diagram import latest_versioned  # noqa: E402

COMMAND = "python3 scripts/measure_holos_forks_stylized_AN_v4.py"
FARMS_YAML = latest_versioned(ROOT / "data", "stylized_farms", ".yaml")
DETAIL_CSV = ROOT / "data" / "holos_fork_deltas_stylized_AN_v4.csv"
SUMMARY_CSV = ROOT / "data" / "holos_fork_deltas_stylized_summary_AN_v4.csv"
META_JSON = ROOT / "data" / "holos_fork_deltas_stylized_AN_v4.meta.json"


def _pct(delta: float, baseline: float) -> float:
    if baseline == 0.0:
        return 0.0 if delta == 0.0 else float("nan")
    return 100.0 * delta / baseline


def _row(farm: dict, fork_id: str, option: str, flows, baseline: dict[str, float] | None) -> dict:
    totals = {
        "CH4_enteric_kg": flows.ch4_enteric_kg,
        "CH4_manure_kg": flows.ch4_manure_kg,
        "CH4_kg": flows.ch4_kg,
        "N2O_kg": flows.n2o_kg,
        "CO2e_kg": flows.co2e_kg,
        "CO2e_t": flows.co2e_t,
    }
    if baseline is None:
        d_ch4 = d_n2o = d_co2e_kg = d_co2e_t = d_ent = d_man = 0.0
        base_ch4 = totals["CH4_kg"]
        base_n2o = totals["N2O_kg"]
        base_co2e_kg = totals["CO2e_kg"]
    else:
        d_ch4 = totals["CH4_kg"] - baseline["CH4_kg"]
        d_n2o = totals["N2O_kg"] - baseline["N2O_kg"]
        d_co2e_kg = totals["CO2e_kg"] - baseline["CO2e_kg"]
        d_co2e_t = totals["CO2e_t"] - baseline["CO2e_t"]
        d_ent = totals["CH4_enteric_kg"] - baseline["CH4_enteric_kg"]
        d_man = totals["CH4_manure_kg"] - baseline["CH4_manure_kg"]
        base_ch4 = baseline["CH4_kg"]
        base_n2o = baseline["N2O_kg"]
        base_co2e_kg = baseline["CO2e_kg"]
    return {
        "command": COMMAND,
        "farm_id": farm["id"],
        "farm_type": farm.get("farm_type"),
        "diet_id": farm.get("diet_id", ""),
        "manure_id": farm.get("manure_id"),
        "fork_id": fork_id,
        "option": option,
        "evidence": "MEASURED",
        **totals,
        "dCH4_kg": d_ch4,
        "dN2O_kg": d_n2o,
        "dCO2e_kg": d_co2e_kg,
        "delta_CH4_kg": d_ch4,
        "delta_N2O_kg": d_n2o,
        "delta_CO2e_t": d_co2e_t,
        "delta_CH4_pct": _pct(d_ch4, base_ch4),
        "delta_N2O_pct": _pct(d_n2o, base_n2o),
        "delta_CO2e_pct": _pct(d_co2e_kg, base_co2e_kg) if baseline is not None else 0.0,
        "delta_CH4_enteric_kg": d_ent,
        "delta_CH4_manure_kg": d_man,
    }


def main() -> None:
    spec = load_stylized_spec(FARMS_YAML)
    params = stylized_params(ROOT, spec)
    gwp = gwp_from_spec(spec)
    catalog = fork_catalog()
    combined = combined_forks()
    rows: list[dict] = []
    for farm in spec["farms"]:
        base_flows = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
        baseline = {
            "CH4_enteric_kg": base_flows.ch4_enteric_kg,
            "CH4_manure_kg": base_flows.ch4_manure_kg,
            "CH4_kg": base_flows.ch4_kg,
            "N2O_kg": base_flows.n2o_kg,
            "CO2e_kg": base_flows.co2e_kg,
            "CO2e_t": base_flows.co2e_t,
        }
        rows.append(_row(farm, "BASELINE", "registered_defaults", base_flows, None))
        for row in catalog:
            flows = compute_stylized_farm_flows(
                spec, farm, params, {row["fork_id"]: row["alt"]}, run=row["fork_id"]
            )
            rows.append(_row(farm, row["fork_id"], row["alt"], flows, baseline))
        all_alt = compute_stylized_farm_flows(spec, farm, params, combined, run="holos_as_coded")
        rows.append(_row(farm, "COMBINED", "all_non_default", all_alt, baseline))

    detail = pd.DataFrame(rows)
    detail.to_csv(DETAIL_CSV, index=False)
    summary = (
        detail.loc[~detail["fork_id"].isin(["BASELINE"])]
        .groupby(["farm_id", "fork_id"], as_index=False)[
            ["delta_CH4_kg", "delta_N2O_kg", "delta_CO2e_t", "delta_CO2e_pct"]
        ]
        .sum()
    )
    summary.to_csv(SUMMARY_CSV, index=False)
    META_JSON.write_text(
        json.dumps(
            {
                "command": COMMAND,
                "farms_yaml": FARMS_YAML.name,
                "gwp_ar5": gwp,
                "date": date.today().isoformat(),
                "n_farms": int(detail["farm_id"].nunique()),
                "n_forks": int(
                    detail.loc[~detail["fork_id"].isin(["BASELINE", "COMBINED"]), "fork_id"].nunique()
                ),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote {DETAIL_CSV}")
    print(f"wrote {SUMMARY_CSV}")
    turkey = detail[(detail["farm_id"] == "turkey_litter") & (detail["fork_id"] == "HOLOS.CH4.turkey_zero")]
    if not turkey.empty:
        print(
            f"turkey CE-10 dCH4_kg={turkey.iloc[0]['delta_CH4_kg']} "
            f"delta_CO2e_pct={turkey.iloc[0]['delta_CO2e_pct']}"
        )
    ef1 = detail[(detail["farm_id"] == "crop_urea_lime") & (detail["fork_id"] == "HOLOS.N2O.ef1")]
    if not ef1.empty:
        print(
            f"crop_urea_lime EF1 dN2O_kg={ef1.iloc[0]['delta_N2O_kg']} "
            f"delta_CO2e_pct={ef1.iloc[0]['delta_CO2e_pct']}"
        )


if __name__ == "__main__":
    main()
