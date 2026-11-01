"""Shared VT/DE farm assembly and Holos/IPCC runners for Phase 3 scripts.

County activity data come from the livingghg v3 trial CSVs and EPA Annex 3.11
assumptions JSON. No diet TDN, forage%, calf counts, or cover types are invented.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy" / "livingghg_AN_v3"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(LEGACY) not in sys.path:
    sys.path.insert(0, str(LEGACY))

from ghgsim.core.registry import ParameterRegistry, load_parameter_csv
from ghgsim.modules.holos import HolosEnteric, HolosManure, HolosSoilN2O, HolosVolatileSolids
from ghgsim.modules.holos.forks import get_holos_fork_registry

GWP_AR5 = {"CH4": 28.0, "N2O": 265.0}
ASH_IPCC_EXAMPLE_PCT = 8.0  # IPCC 2006 Eq 10.24 example text p. 10.54; SOURCE-TRACED
MCF_STEMS = (
    "liquid_nocrust",
    "liquid_crust",
    "lagoon",
    "solid_storage",
    "dry_lot",
    "daily_spread",
    "pasture",
)


def load_epa_assumptions() -> dict[str, Any]:
    path = LEGACY / "scripts" / "county_assumptions_AN_v3.json"
    with path.open() as f:
        return json.load(f)


def load_vt_de_counties() -> pd.DataFrame:
    frames = []
    for state in ("VT", "DE"):
        path = LEGACY / "results_TRIAL_AN_v3" / f"counties_{state}_AN_v3.csv"
        frames.append(pd.read_csv(path))
    return pd.concat(frames, ignore_index=True)


def load_registries() -> dict[str, ParameterRegistry]:
    return {
        "ipcc": load_parameter_csv(ROOT / "data" / "ipcc_params_AN_v4.csv", allow_unverified=False),
        "canada": load_parameter_csv(
            ROOT / "data" / "holos_params_canada_AN_v4.csv", allow_unverified=True
        ),
        "us": load_parameter_csv(ROOT / "data" / "holos_params_us_AN_v2.csv", allow_unverified=True),
    }


def v3_farm_from_row(row: pd.Series, epa: dict[str, Any]) -> dict[str, Any]:
    """v3 run_counties_AN_v3 farm: copy EPA dairy/beef dicts and attach head."""
    state = str(row["STATE_ALPHA"])
    state_cfg = epa["states"][state]
    herds = []
    for kind, col in (("dairy", "milk_cows"), ("beef", "beef_cows")):
        head = row.get(col)
        if head is not None and pd.notna(head) and float(head) > 0:
            herds.append(dict(state_cfg[kind], head=float(head)))
    soil = {"climate": epa["climate"], "F_SOM": 0.0, "F_PRP_CPP": 0.0}
    for key in ("F_SN", "F_ON", "F_CR"):
        value = row.get(key)
        soil[key] = 0.0 if value is None or pd.isna(value) else float(value)
    return {"soil": soil, "herds": herds}


def _reg_get(reg: ParameterRegistry, key: str) -> float:
    return float(reg.get_value(key))


def holos_compute_params(
    regs: dict[str, ParameterRegistry],
    *,
    mcf_set: str,
) -> dict[str, float]:
    """Parameter dict for Holos enteric/manure/soil/VS modules.

    mcf_set:
      - ipcc15C: IPCC 2006 Table 10.17 15C (source-correct; used for fork deltas)
      - holos_us: Holos US MCF overlay where present, else IPCC 15C
      - holos_canada: Holos Canada MCF (temperate/cool fallbacks), lagoon from IPCC
    """
    ipcc = regs["ipcc"]
    canada = regs["canada"]
    us = regs["us"]
    params: dict[str, float] = {
        "CH4_ENERGY": _reg_get(ipcc, "BOTH.CH4_ENERGY.all"),
        "CH4_M3_TO_KG": _reg_get(ipcc, "BOTH.CH4_M3_TO_KG.all"),
        "GE_PER_KG_DM": _reg_get(ipcc, "BOTH.GE_PER_KG_DM.all"),
        "Ym_dairy_canada": _reg_get(canada, "HOLOS.Ym.dairy_lactating|canada"),
        "Ym_dairy_ipcc2006": _reg_get(ipcc, "IPCC2006.Ym.dairy"),
        "Ym_beef_high_grain": _reg_get(canada, "HOLOS.Ym.beef_finisher_corn|canada"),
        "Ym_beef_medium": _reg_get(canada, "HOLOS.Ym.beef_backgrounder|canada"),
        "Ym_beef_low_grain": _reg_get(canada, "HOLOS.Ym.beef_cowcalf_low|canada"),
        "B0_dairy_canada": _reg_get(canada, "HOLOS.B0.dairy|canada"),
        "B0_beef_canada": _reg_get(canada, "HOLOS.B0.beef|canada"),
        "Nrate_dairy_canada": _reg_get(canada, "HOLOS.Nrate.dairy|canada"),
        "Nrate_beef_canada": _reg_get(canada, "HOLOS.Nrate.beef|canada"),
        "TAM_dairy_canada": _reg_get(canada, "HOLOS.TAM.dairy_lactating|canada"),
        "TAM_beef_canada": _reg_get(canada, "HOLOS.TAM.beef_cow_lactating|canada"),
        "calf_n_kg_head_day": _reg_get(canada, "HOLOS.Nrate.dairy_calves_kg_head_day|canada"),
        "calf_vs_coeff": _reg_get(canada, "HOLOS.VS.dairy_calves_coeff|canada"),
        "cover_crust_factor": _reg_get(canada, "HOLOS.COVER.natural_crust_factor"),
        "cover_other_factor": _reg_get(canada, "HOLOS.COVER.other_cover_factor"),
        "EF1": _reg_get(ipcc, "IPCC2006.EF1.all"),
        "EF3PRP_CPP": _reg_get(ipcc, "IPCC2006.EF3PRP_CPP.all"),
        "EF4": _reg_get(ipcc, "IPCC2006.EF4.all"),
        "EF5": _reg_get(ipcc, "IPCC2006.EF5.all"),
        "FracGASF": _reg_get(ipcc, "IPCC2006.FracGASF.all"),
        "FracGASM": _reg_get(ipcc, "IPCC2006.FracGASM.all"),
        "FracLEACH_wet": _reg_get(ipcc, "IPCC2006.FracLEACH.wet"),
        # IPCC 2006 CSV has no dry FracLEACH row. VT/DE climate is wet, so unused.
    }
    for system in ("liquid_nocrust", "liquid_crust", "lagoon", "solid_storage", "dry_lot", "daily_spread"):
        params[f"EF3_{system}"] = _reg_get(ipcc, f"IPCC2006.EF3.{system}")
    for animal, frac_animal in (("dairy", "dairy"), ("other_cattle", "other_cattle"), ("beef", "other_cattle")):
        for system in ("liquid_slurry", "solid_storage", "dry_lot", "daily_spread", "lagoon"):
            key = f"IPCC2006.FracGasMS.{frac_animal}|{system}"
            try:
                params[f"FracGasMS_{animal}_{system}"] = _reg_get(ipcc, key)
            except ValueError:
                params[f"FracGasMS_{animal}_{system}"] = _reg_get(
                    ipcc, f"IPCC2006.FracGasMS.dairy|{system}"
                )

    def put_mcf(stem: str, climate: str, key: str) -> None:
        params[f"MCF_{stem}_{climate}"] = _reg_get(ipcc, key)

    for stem in MCF_STEMS:
        zone = "le10C" if stem == "pasture" else "le10C"
        put_mcf(stem, "cool", f"IPCC2006.MCF.{stem}|{zone}")
        put_mcf(stem, "le10C", f"IPCC2006.MCF.{stem}|le10C" if stem != "pasture" else "IPCC2006.MCF.pasture|le10C")
        put_mcf(stem, "15C", f"IPCC2006.MCF.{stem}|15C")
        put_mcf(stem, "temperate", f"IPCC2006.MCF.{stem}|15C")

    if mcf_set == "holos_us":
        params["MCF_liquid_nocrust_15C"] = _reg_get(us, "HOLOS.MCF.liquid_nocrust|US")
        params["MCF_liquid_nocrust_temperate"] = params["MCF_liquid_nocrust_15C"]
        params["MCF_solid_storage_15C"] = _reg_get(us, "HOLOS.MCF.solid_storage|US")
        params["MCF_solid_storage_temperate"] = params["MCF_solid_storage_15C"]
        params["MCF_pasture_15C"] = _reg_get(us, "HOLOS.MCF.pasture|US")
        params["MCF_pasture_temperate"] = params["MCF_pasture_15C"]
        params["MCF_pasture_cool"] = params["MCF_pasture_15C"]
        params["MCF_daily_spread_15C"] = _reg_get(us, "HOLOS.MCF.daily_spread|US")
        params["MCF_daily_spread_temperate"] = params["MCF_daily_spread_15C"]
        params["MCF_lagoon_15C"] = _reg_get(us, "HOLOS.MCF.lagoon|US")
        params["MCF_lagoon_temperate"] = params["MCF_lagoon_15C"]
        params["B0_beef_canada"] = _reg_get(us, "HOLOS.B0.beef|VT")
    elif mcf_set == "holos_canada":
        params["MCF_liquid_nocrust_cool"] = _reg_get(canada, "HOLOS.MCF.liquid_nocrust|cool")
        params["MCF_liquid_nocrust_temperate"] = _reg_get(canada, "HOLOS.MCF.liquid_nocrust|temperate")
        params["MCF_solid_storage_cool"] = _reg_get(canada, "HOLOS.MCF.solid_storage|cool")
        params["MCF_solid_storage_temperate"] = _reg_get(canada, "HOLOS.MCF.solid_storage|temperate")
        params["MCF_pasture_cool"] = _reg_get(canada, "HOLOS.MCF.pasture|cool")
        params["MCF_daily_spread_cool"] = _reg_get(canada, "HOLOS.MCF.daily_spread|cool")
        # No Holos Canada lagoon row: IPCC Table 10.17 15C / le10C remain.
    elif mcf_set != "ipcc15C":
        raise ValueError(f"Unknown mcf_set '{mcf_set}'")
    return params


def _holos_animal(kind: str) -> str:
    return "dairy" if kind == "dairy" else "beef"


def _vs_for_herd(
    herd: dict[str, Any],
    forks: dict[str, str],
    params: dict[str, float],
    pathway: str,
    vs_module: HolosVolatileSolids,
) -> tuple[float | None, str]:
    """Return (VS_kg_day or None, vs_source). None means HolosManure uses its fallback."""
    manure = herd.get("manure") or {}
    epa_vs = manure.get("VS_kg_day", herd.get("VS_kg_day"))
    if pathway == "epa_vs":
        return (None if epa_vs is None else float(epa_vs), "EPA_VS_kg_day")
    if pathway != "eq1024_vs":
        raise ValueError(f"Unknown pathway '{pathway}'")
    ge = herd.get("GE_MJ_day")
    de = herd.get("DE_pct")
    if ge in (None, "") or de in (None, ""):
        return (None if epa_vs is None else float(epa_vs), "EPA_VS_fallback_missing_GE_or_DE")
    vs_in = {
        "GE_MJ_day": float(ge),
        "DE_percent": float(de),
        "ASH_percent": ASH_IPCC_EXAMPLE_PCT,
        "animal_class": str(herd.get("animal_class", "adult")),
        "forks": forks,
    }
    # TDN is not independently observed; equal to DE so the TDN fork cannot fire.
    vs_out = vs_module.compute(vs_in, params)
    return float(vs_out["VS_kg_day"]), "eq1024_EPA_GE_DE_ASH8_example"


def run_holos_farm(
    farm: dict[str, Any],
    params: dict[str, float],
    *,
    forks: dict[str, str] | None = None,
    pathway: str = "epa_vs",
    ym_dairy_mode: str = "fork_default",
    beef_ym: float | None = None,
    climate_zone: str = "15C",
) -> dict[str, float]:
    """Run Holos enteric + manure + soil on a v3-style farm.

    ym_dairy_mode:
      - fork_default: Ym_dairy_canada (5.6) unless HOLOS.YM.dairy is toggled
      - epa_state: pass EPA Ym_pct as Ym_dairy_canada (Holos US enteric)
    beef_ym: if set, used as Ym_beef_medium (EPA state Ym for US; Canada table otherwise).
    """
    fork_settings = dict(forks or {})
    enteric = HolosEnteric()
    manure = HolosManure()
    soil = HolosSoilN2O()
    vs_module = HolosVolatileSolids()
    run_params = dict(params)
    if beef_ym is not None:
        run_params["Ym_beef_medium"] = float(beef_ym)

    ch4_enteric = 0.0
    ch4_manure = 0.0
    n2o_manure = 0.0
    n_prp = 0.0
    for herd in farm["herds"]:
        animal_flag = (herd.get("manure") or {}).get("animal")
        if animal_flag == "dairy":
            animal = "dairy"
        elif animal_flag in ("other_cattle", "beef"):
            animal = "beef"
        else:
            ym_cat = herd.get("ym_category")
            if ym_cat == "dairy" or (isinstance(ym_cat, dict) and ym_cat.get("IPCC2006") == "dairy"):
                animal = "dairy"
            else:
                animal = "beef"
        herd_params = dict(run_params)
        if ym_dairy_mode == "epa_state" and animal == "dairy":
            herd_params["Ym_dairy_canada"] = float(herd["Ym_pct"])
        enteric_in: dict[str, Any] = {
            "head": float(herd["head"]),
            "animal_type": animal,
            "animal_class": str(herd.get("animal_class", "adult")),
            "GE_MJ_day": float(herd["GE_MJ_day"]),
            "forks": fork_settings,
        }
        ent = enteric.compute(enteric_in, herd_params)
        ch4_enteric += float(ent["CH4_total"])

        manure_cfg = herd.get("manure") or {}
        if not manure_cfg:
            continue
        vs_val, _vs_src = _vs_for_herd(herd, fork_settings, herd_params, pathway, vs_module)
        manure_in: dict[str, Any] = {
            "head": float(herd["head"]),
            "animal_type": animal,
            "climate_zone": climate_zone,
            "systems": manure_cfg["systems"],
            "animal_class": str(herd.get("animal_class", "adult")),
            "cover_type": str(herd.get("cover_type", "none")),
            "forks": fork_settings,
        }
        if vs_val is not None:
            manure_in["VS_kg_day"] = vs_val
        nex = manure_cfg.get("Nex_kg_yr", herd.get("Nex_kg_yr"))
        if nex not in (None, ""):
            manure_in["Nex_kg_yr"] = float(nex)
        man = manure.compute(manure_in, herd_params)
        ch4_manure += float(man["CH4"])
        n2o_manure += float(man["N2O_total"])
        n_prp += float(man["N_PRP_kg"])

    soil_in = {
        "F_SN": float(farm["soil"]["F_SN"]),
        "F_ON": float(farm["soil"]["F_ON"]),
        "F_CR": float(farm["soil"]["F_CR"]),
        "F_SOM": float(farm["soil"].get("F_SOM", 0.0)),
        "F_PRP_CPP": float(farm["soil"].get("F_PRP_CPP", 0.0)) + n_prp,
        "climate": farm["soil"]["climate"],
    }
    soil_out = soil.compute(soil_in, run_params)
    n2o_soil = float(soil_out["N2O_total"])
    ch4 = ch4_enteric + ch4_manure
    n2o = n2o_manure + n2o_soil
    co2e = (ch4 * GWP_AR5["CH4"] + n2o * GWP_AR5["N2O"]) / 1000.0
    return {
        "CH4_enteric_kg": ch4_enteric,
        "CH4_manure_kg": ch4_manure,
        "CH4_kg": ch4,
        "N2O_manure_kg": n2o_manure,
        "N2O_soil_kg": n2o_soil,
        "N2O_kg": n2o,
        "CO2e_t": co2e,
    }


def run_ipcc2006_v4(farm: dict[str, Any], ipcc: ParameterRegistry) -> dict[str, float]:
    """IPCC 2006 via v4 modules; EPA Ym/GE/VS/Nex when present (same as exact reproduction)."""
    from tests.test_exact_vt_de_reproduction import run_v4_farm_ipcc2006

    # Flatten v3 nested farm to the reproduction-test farm shape.
    flat = {
        "soil": dict(farm["soil"]),
        "herds": [],
    }
    for herd in farm["herds"]:
        manure = dict(herd.get("manure") or {})
        animal = manure.get("animal", "dairy")
        ym_cat = herd.get("ym_category")
        if isinstance(ym_cat, dict):
            ym2006 = ym_cat.get("IPCC2006", "dairy" if animal == "dairy" else "other_cattle")
            ym2019 = ym_cat.get("IPCC2019")
        else:
            ym2006 = ym_cat or ("dairy" if animal == "dairy" else "other_cattle")
            ym2019 = herd.get("ym_category_2019")
        mcf = manure.get("mcf_zone")
        if isinstance(mcf, dict):
            mcf2006 = mcf.get("IPCC2006", "15C")
        else:
            mcf2006 = mcf or "15C"
        flat_herd = {
            "head": float(herd["head"]),
            "GE_MJ_day": float(herd["GE_MJ_day"]),
            "Ym_pct": float(herd["Ym_pct"]),
            "ym_category": ym2006,
            "ym_category_2019": ym2019,
            "VS_kg_day": float(manure["VS_kg_day"]),
            "Nex_kg_yr": float(manure["Nex_kg_yr"]),
            "manure": {
                "animal": animal,
                "region": manure.get("region", "north_america"),
                "systems": manure["systems"],
                "mcf_zone": mcf2006,
            },
        }
        flat["herds"].append(flat_herd)
    result = run_v4_farm_ipcc2006(flat, ipcc)
    return {
        "CH4_kg": float(result["CH4_kg"]),
        "N2O_kg": float(result["N2O_kg"]),
        "CO2e_t": float(result["CO2e_t"]),
        "CH4_manure_kg": float(result["CH4_manure_kg"]),
        "N2O_manure_kg": float(result["N2O_manure_kg"]),
    }


def run_ipcc2019_v3(farm: dict[str, Any]):
    """IPCC 2019 full farm via livingghg v3 engine (v4 has no manure 2019 module)."""
    from livingghg.engine import run_farm
    from livingghg.params import ParamTable

    params = ParamTable()
    return run_farm(farm, "IPCC2019", params)


def alt_option(fork) -> str:
    """The non-default option (each Holos fork currently has exactly two options)."""
    others = [name for name in fork.options if name != fork.default]
    if len(others) != 1:
        raise ValueError(f"Fork {fork.id} does not have exactly one non-default option")
    return others[0]


def fork_catalog() -> list[dict[str, str]]:
    rows = []
    for fork in get_holos_fork_registry().list_forks(sort_by="id"):
        rows.append(
            {
                "fork_id": fork.id,
                "default": fork.default,
                "alt": alt_option(fork),
                "label": fork.label,
                "issue_ref": fork.issue_ref,
            }
        )
    return rows
