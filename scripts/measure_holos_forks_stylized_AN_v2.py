#!/usr/bin/env python3
"""Measure per-fork CH4/N2O/CO2e on stylized farms (single forks + combined).

Farms are data/stylized_farms_AN_v2.yaml. Net-energy terms are computed from
IPCC 2006 Vol 4 Ch 10 equations using only YAML-cited primitives. GE_MJ_day is
never supplied, so HOLOS.GE.digestibility can fire. VS always uses Eq 10.24.

Does not overwrite AN_v1 outputs. Cover fork uses remaining = 1 - reduction.

Usage (from repository root):
    python3 scripts/measure_holos_forks_stylized_AN_v2.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from holos_vt_de_runner_AN_v1 import (  # noqa: E402
    GWP_AR5,
    fork_catalog,
    holos_compute_params,
    load_registries,
)
from ghgsim.modules.holos import HolosEnteric, HolosManure, HolosVolatileSolids  # noqa: E402

COMMAND = "python3 scripts/measure_holos_forks_stylized_AN_v2.py"
FARMS_YAML = ROOT / "data" / "stylized_farms_AN_v2.yaml"
DETAIL_CSV = ROOT / "data" / "holos_fork_deltas_stylized_AN_v2.csv"
SUMMARY_CSV = ROOT / "data" / "holos_fork_deltas_stylized_summary_AN_v2.csv"
META_JSON = ROOT / "data" / "holos_fork_deltas_stylized_AN_v2.meta.json"


def load_farms() -> dict[str, Any]:
    with FARMS_YAML.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _const(spec: dict[str, Any]) -> dict[str, float]:
    return {name: float(row["value"]) for name, row in spec["constants"].items() if "value" in row}


def rem_eq_10_14(de_percent: float) -> float:
    """IPCC 2006 Vol 4 Ch 10 Equation 10.14 p. 10.20."""
    de = float(de_percent)
    return 1.123 - (4.092e-3 * de) + (1.126e-5 * (de**2)) - (25.4 / de)


def weight_kg(spec: dict[str, Any], animal: dict[str, Any]) -> float:
    return float(animal["mass_lb"]["value"]) * float(spec["meta"]["lb_to_kg"])


def nex_kg_yr(spec: dict[str, Any], animal: dict[str, Any], constants: dict[str, float]) -> float:
    if "Nex_kg_yr_override" in animal:
        return float(animal["Nex_kg_yr_override"]["value"])
    nrate_key = "Nrate_dairy_na" if animal["animal_type"] == "dairy" else "Nrate_other_cattle_na"
    return constants[nrate_key] * weight_kg(spec, animal) / 1000.0 * 365.0


def milk_kg_day(spec: dict[str, Any], animal: dict[str, Any]) -> float:
    milk = animal.get("milk_lb_cow_yr")
    if not milk:
        return 0.0
    return float(milk["value"]) * float(spec["meta"]["lb_to_kg"]) / 365.0


def net_energy(
    spec: dict[str, Any],
    animal: dict[str, Any],
    constants: dict[str, float],
    de_percent: float,
) -> dict[str, float]:
    """NE_m / NE_a / NE_l / NE_p / RE_m from IPCC 2006 Eq 10.3, 10.4, 10.8, 10.13, 10.14."""
    cfi = constants[animal["Cfi_key"]]
    ca = constants[animal["Ca_key"]]
    mass = weight_kg(spec, animal)
    ne_m = cfi * (mass**0.75)
    ne_a = ca * ne_m
    ne_l = 0.0
    if animal.get("apply_lactation"):
        ne_l = milk_kg_day(spec, animal) * (1.47 + 0.40 * constants["milk_fat_pct"])
    ne_p = 0.0
    if animal.get("apply_pregnancy"):
        ne_p = constants["Cpregnancy_cattle"] * ne_m * constants["pregnant_fraction_na_dairy"]
    return {
        "NE_m": ne_m,
        "NE_a": ne_a,
        "NE_l": ne_l,
        "NE_work": 0.0,
        "NE_p": ne_p,
        "NE_g": 0.0,
        "RE_m": rem_eq_10_14(de_percent),
        "RE_g": 0.0,
        "weight_kg": mass,
    }


def herd_de_tdn(
    spec: dict[str, Any],
    farm: dict[str, Any],
    animal: dict[str, Any],
    diet: dict[str, Any],
) -> tuple[float, float, float]:
    """Return (DE%, TDN%, forage%). Farm high-grain diet overrides class DE."""
    tdn = float(diet["TDN_percent"]["value"])
    forage = float(diet["forage_percent"]["value"])
    if farm.get("diet_overrides_class_DE"):
        return float(diet["DE_percent"]["value"]), tdn, forage
    if "DE_percent" in animal and "value" in animal["DE_percent"]:
        return float(animal["DE_percent"]["value"]), tdn, forage
    return float(diet["DE_percent"]["value"]), tdn, forage


def run_stylized_farm(
    spec: dict[str, Any],
    farm: dict[str, Any],
    params: dict[str, float],
    forks: dict[str, str],
) -> dict[str, float]:
    constants = _const(spec)
    diet = spec["diets"][farm["diet_id"]]
    manure_cfg = spec["manure_variants"][farm["manure_id"]]
    enteric = HolosEnteric()
    vs_module = HolosVolatileSolids()
    manure = HolosManure()

    ch4_enteric = 0.0
    ch4_manure = 0.0
    n2o_manure = 0.0
    ge_sum = 0.0
    vs_sum = 0.0
    ue_values: list[float] = []
    head_total = 0.0

    for class_id in farm["herds"]:
        animal = spec["animal_classes"][class_id]
        de, tdn, forage = herd_de_tdn(spec, farm, animal, diet)
        energy = net_energy(spec, animal, constants, de)
        head = float(animal["head"]["value"])
        head_total += head
        enteric_in = {
            "head": head,
            "animal_type": animal["animal_type"],
            "animal_class": animal["animal_class"],
            "NE_m": energy["NE_m"],
            "NE_a": energy["NE_a"],
            "NE_l": energy["NE_l"],
            "NE_work": energy["NE_work"],
            "NE_p": energy["NE_p"],
            "NE_g": energy["NE_g"],
            "RE_m": energy["RE_m"],
            "RE_g": energy["RE_g"],
            "DE_percent": de,
            "TDN_percent": tdn,
            "forks": forks,
        }
        ent = enteric.compute(enteric_in, params)
        ge = float(ent["GE_used"])
        ch4_enteric += float(ent["CH4_total"])
        ge_sum += ge * head

        vs_in = {
            "GE_MJ_day": ge,
            "DE_percent": de,
            "TDN_percent": tdn,
            "ASH_percent": constants["ASH_percent"],
            "forage_percent": forage,
            "animal_class": animal["animal_class"],
            "weight_kg": energy["weight_kg"],
            "forks": forks,
        }
        vs_out = vs_module.compute(vs_in, params)
        vs = float(vs_out["VS_kg_day"])
        vs_sum += vs * head
        if vs_out["UE_used"] == vs_out["UE_used"]:  # not NaN (calf holos VS)
            ue_values.append(float(vs_out["UE_used"]))

        manure_in = {
            "head": head,
            "animal_type": animal["animal_type"],
            "climate_zone": spec["meta"]["climate_zone"],
            "systems": dict(manure_cfg["systems"]),
            "VS_kg_day": vs,
            "Nex_kg_yr": nex_kg_yr(spec, animal, constants),
            "animal_class": animal["animal_class"],
            "cover_type": str(manure_cfg["cover_type"]),
            "forks": forks,
        }
        man = manure.compute(manure_in, params)
        ch4_manure += float(man["CH4"])
        n2o_manure += float(man["N2O_total"])

    ch4 = ch4_enteric + ch4_manure
    n2o = n2o_manure
    co2e = (ch4 * GWP_AR5["CH4"] + n2o * GWP_AR5["N2O"]) / 1000.0
    return {
        "CH4_enteric_kg": ch4_enteric,
        "CH4_manure_kg": ch4_manure,
        "CH4_kg": ch4,
        "N2O_kg": n2o,
        "CO2e_t": co2e,
        "GE_sum_MJ_day": ge_sum,
        "VS_sum_kg_day": vs_sum,
        "UE_used": ue_values[0] if ue_values else float("nan"),
        "head_total": head_total,
    }


def _pct(delta: float, baseline: float) -> float:
    if baseline == 0.0:
        return 0.0 if delta == 0.0 else float("nan")
    return 100.0 * delta / baseline


def _row(
    farm: dict[str, Any],
    fork_id: str,
    option: str,
    result: dict[str, float],
    baseline: dict[str, float] | None,
) -> dict[str, Any]:
    if baseline is None:
        d_ch4 = d_n2o = d_co2e = d_ent = d_man = 0.0
    else:
        d_ch4 = result["CH4_kg"] - baseline["CH4_kg"]
        d_n2o = result["N2O_kg"] - baseline["N2O_kg"]
        d_co2e = result["CO2e_t"] - baseline["CO2e_t"]
        d_ent = result["CH4_enteric_kg"] - baseline["CH4_enteric_kg"]
        d_man = result["CH4_manure_kg"] - baseline["CH4_manure_kg"]
    return {
        "command": COMMAND,
        "farm_id": farm["id"],
        "farm_type": farm["farm_type"],
        "diet_id": farm["diet_id"],
        "manure_id": farm["manure_id"],
        "fork_id": fork_id,
        "option": option,
        "evidence": "MEASURED",
        **result,
        "delta_CH4_kg": d_ch4,
        "delta_N2O_kg": d_n2o,
        "delta_CO2e_t": d_co2e,
        "delta_CH4_pct": _pct(d_ch4, baseline["CH4_kg"] if baseline else result["CH4_kg"]),
        "delta_N2O_pct": _pct(d_n2o, baseline["N2O_kg"] if baseline else result["N2O_kg"]),
        "delta_CO2e_pct": _pct(d_co2e, baseline["CO2e_t"] if baseline else result["CO2e_t"]),
        "delta_CH4_enteric_kg": d_ent,
        "delta_CH4_manure_kg": d_man,
    }


def measure() -> tuple[pd.DataFrame, pd.DataFrame]:
    spec = load_farms()
    regs = load_registries()
    params = holos_compute_params(regs, mcf_set="ipcc15C")
    # Beef Ym is EPA Table A-138 Northeast 6.5 (held constant; not the dairy Ym fork).
    params = dict(params)
    params["Ym_beef_medium"] = float(spec["animal_classes"]["beef_cow"]["Ym_pct"]["value"])
    forks = fork_catalog()
    combined = {row["fork_id"]: row["alt"] for row in forks}
    rows: list[dict[str, Any]] = []

    for farm in spec["farms"]:
        baseline = run_stylized_farm(spec, farm, params, forks={})
        rows.append(_row(farm, "BASELINE", "registered_defaults", baseline, None))
        for fork in forks:
            alt = run_stylized_farm(spec, farm, params, forks={fork["fork_id"]: fork["alt"]})
            rows.append(_row(farm, fork["fork_id"], fork["alt"], alt, baseline))
        all_alt = run_stylized_farm(spec, farm, params, forks=combined)
        rows.append(_row(farm, "COMBINED", "all_non_default", all_alt, baseline))

    detail = pd.DataFrame(rows)
    summaries = []
    settings = [{"fork_id": f["fork_id"], "default": f["default"], "alt": f["alt"], "label": f["label"]} for f in forks]
    settings.append(
        {"fork_id": "COMBINED", "default": "registered_defaults", "alt": "all_non_default", "label": "combined"}
    )
    for farm in spec["farms"]:
        base = detail[(detail["farm_id"] == farm["id"]) & (detail["fork_id"] == "BASELINE")].iloc[0]
        for setting in settings:
            sub = detail[(detail["farm_id"] == farm["id"]) & (detail["fork_id"] == setting["fork_id"])].iloc[0]
            fired = bool(
                abs(sub["delta_CH4_kg"]) > 1e-9
                or abs(sub["delta_N2O_kg"]) > 1e-9
                or abs(sub["delta_CO2e_t"]) > 1e-9
            )
            summaries.append(
                {
                    "command": COMMAND,
                    "farm_id": farm["id"],
                    "farm_type": farm["farm_type"],
                    "diet_id": farm["diet_id"],
                    "manure_id": farm["manure_id"],
                    "fork_id": setting["fork_id"],
                    "default_option": setting["default"],
                    "alt_option": setting["alt"],
                    "label": setting["label"],
                    "evidence": "MEASURED",
                    "fork_fired": fired,
                    "baseline_CH4_kg": float(base["CH4_kg"]),
                    "delta_CH4_kg": float(sub["delta_CH4_kg"]),
                    "delta_CH4_pct": float(sub["delta_CH4_pct"]),
                    "delta_CH4_enteric_kg": float(sub["delta_CH4_enteric_kg"]),
                    "delta_CH4_manure_kg": float(sub["delta_CH4_manure_kg"]),
                    "baseline_N2O_kg": float(base["N2O_kg"]),
                    "delta_N2O_kg": float(sub["delta_N2O_kg"]),
                    "delta_N2O_pct": float(sub["delta_N2O_pct"]),
                    "baseline_CO2e_t": float(base["CO2e_t"]),
                    "delta_CO2e_t": float(sub["delta_CO2e_t"]),
                    "delta_CO2e_pct": float(sub["delta_CO2e_pct"]),
                    "UE_used_alt": float(sub["UE_used"]),
                    "GE_sum_MJ_day_alt": float(sub["GE_sum_MJ_day"]),
                    "VS_sum_kg_day_alt": float(sub["VS_sum_kg_day"]),
                }
            )
    return detail, pd.DataFrame(summaries)


def main() -> None:
    detail, summary = measure()
    DETAIL_CSV.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(DETAIL_CSV, index=False)
    summary.to_csv(SUMMARY_CSV, index=False)
    fired = summary[summary["fork_id"] != "COMBINED"].groupby("fork_id")["fork_fired"].any()
    meta = {
        "command": COMMAND,
        "date": date.today().isoformat(),
        "farms_yaml": str(FARMS_YAML.relative_to(ROOT)),
        "n_farms": int(detail["farm_id"].nunique()),
        "gwp": GWP_AR5,
        "baseline": (
            "Holos modules, registered fork defaults, IPCC 2006 Eq 10.3/10.4/10.8/"
            "10.13/10.14/10.16 NE+GE, Eq 10.24 VS, Eq 10.23/10.25-10.27 manure, "
            "MCF=IPCC 2006 Table 10.17 15C, dairy Ym_canada=5.6, beef Ym=6.5 EPA A-138"
        ),
        "forks_that_fired_on_any_farm": {k: bool(v) for k, v in fired.items()},
        "detail_csv": str(DETAIL_CSV.relative_to(ROOT)),
        "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
    }
    META_JSON.write_text(json.dumps(meta, indent=2) + "\n")
    print(COMMAND)
    print(f"farms: {detail['farm_id'].nunique()}")
    print(summary.to_string(index=False))
    print("forks that fired on any farm:")
    print(fired.to_string())
    print(f"wrote {DETAIL_CSV}")
    print(f"wrote {SUMMARY_CSV}")
    print(f"wrote {META_JSON}")


if __name__ == "__main__":
    main()
