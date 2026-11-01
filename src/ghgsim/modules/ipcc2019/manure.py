"""
IPCC 2019 Refinement manure management.

Same Eq 10.23 / 10.25 / 10.26-10.27 as 2006, plus default FracLeachMS
from Table 10.22 (Updated) and Eq 10.28-10.29. 2006 has no FracLeachMS default.

Poultry/swine animal types and systems are included. Cattle path is unchanged
when the caller still supplies dairy/other_cattle.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.ipcc2006.manure import SYSTEM_MAP_2006, IPCC2006Manure, _fracgas_ms
from ghgsim.modules.livestock_types import is_poultry, is_swine

N2ON_TO_N2O = 44.0 / 28.0


class IPCC2019Manure:
    """IPCC 2019 manure CH4 + direct/indirect N2O including leaching."""

    id = "ipcc2019.manure"
    version = "1.0.0"

    inputs = {
        **IPCC2006Manure.inputs,
        "include_leach": VarSpec(
            "include_leach",
            "dimensionless",
            "Apply Table 10.22 FracLeachMS (default true for 2019)",
            "scalar",
            False,
        ),
    }

    parameters = {
        **IPCC2006Manure.parameters,
        "Nrate_market_swine_2019": ParamRef(
            "IPCC2019.Nrate.market_swine|north_america", "2019 finishing swine Nrate NA"
        ),
        "Nrate_breeding_swine_2019": ParamRef(
            "IPCC2019.Nrate.breeding_swine|north_america", "2019 breeding swine Nrate NA"
        ),
        "Nrate_broilers_2019": ParamRef("IPCC2019.Nrate.broilers|north_america", "2019 broiler Nrate NA"),
        "Nrate_layers_2019": ParamRef("IPCC2019.Nrate.layers|north_america", "2019 layer Nrate NA"),
        "Nrate_turkeys_2019": ParamRef("IPCC2019.Nrate.turkeys|north_america", "2019 turkey Nrate"),
        "B0_swine_2019": ParamRef("IPCC2019.B0.swine|north_america", "2019 swine B0 NA"),
        "B0_layers_2019": ParamRef("IPCC2019.B0.layers|north_america", "2019 layer B0"),
        "B0_other_poultry_2019": ParamRef("IPCC2019.B0.other_poultry|north_america", "2019 other poultry B0"),
        "EF5": ParamRef("IPCC2019.EF5.all", "2019 EF5 leaching"),
        "FracLeachMS_swine_liquid_nocrust": ParamRef(
            "IPCC2019.FracLeachMS.swine|liquid_nocrust", "2019 FracLeachMS swine liquid"
        ),
        "FracLeachMS_swine_pit": ParamRef("IPCC2019.FracLeachMS.swine|pit", "2019 FracLeachMS swine pit"),
        "FracLeachMS_poultry_poultry_with_litter": ParamRef(
            "IPCC2019.FracLeachMS.poultry|poultry_with_litter", "2019 FracLeachMS poultry litter"
        ),
        "FracLeachMS_poultry_poultry_without_litter": ParamRef(
            "IPCC2019.FracLeachMS.poultry|poultry_without_litter", "2019 FracLeachMS poultry no litter"
        ),
    }

    outputs = {
        **IPCC2006Manure.outputs,
        "N2O_indirect_leach": VarSpec(
            "N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True
        ),
        "N_managed_kg": VarSpec("N_managed_kg", "kg N / year", "Managed manure N (non-PRP)", "scalar", True),
        "N_MMS_Avb_kg": VarSpec(
            "N_MMS_Avb_kg", "kg N / year", "Managed manure N after gas+leach loss (no bedding)", "scalar", True
        ),
    }

    sources = [
        Citation(
            source="2019 Refinement to the 2006 IPCC Guidelines, Volume 4, Chapter 10",
            table="Tables 10.16A, 10.19, 10.21, 10.22 (Updated)",
            equation="Eq 10.23, 10.25, 10.26, 10.27, 10.28, 10.29",
            page="10.64, 10.83, 10.91, 10.97-10.98",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        resolved = dict(params)
        animal = str(inputs["animal_type"])
        if is_swine(animal):
            if "Nrate_market_swine_2019" in resolved:
                resolved["Nrate_market_swine"] = resolved["Nrate_market_swine_2019"]
            if "Nrate_breeding_swine_2019" in resolved:
                resolved["Nrate_breeding_swine"] = resolved["Nrate_breeding_swine_2019"]
            if "B0_swine_2019" in resolved:
                resolved["B0_market_swine"] = resolved["B0_swine_2019"]
                resolved["B0_breeding_swine"] = resolved["B0_swine_2019"]
        if animal == "layers" and "B0_layers_2019" in resolved:
            resolved["B0_layers"] = resolved["B0_layers_2019"]
        if animal in ("broilers", "turkeys") and "B0_other_poultry_2019" in resolved:
            resolved[f"B0_{animal}"] = resolved["B0_other_poultry_2019"]
        if animal == "broilers" and "Nrate_broilers_2019" in resolved:
            resolved["Nrate_broilers"] = resolved["Nrate_broilers_2019"]
        if animal == "layers" and "Nrate_layers_2019" in resolved:
            resolved["Nrate_layers"] = resolved["Nrate_layers_2019"]
        if animal == "turkeys" and "Nrate_turkeys_2019" in resolved:
            resolved["Nrate_turkeys"] = resolved["Nrate_turkeys_2019"]

        base = IPCC2006Manure().compute(inputs, resolved)
        include_leach = bool(inputs.get("include_leach", True))
        n_leach = 0.0
        n_lost = 0.0
        head = float(inputs["head"])
        nex = float(base["Nex_kg_head"])
        ef5 = float(resolved["EF5"]) if include_leach else 0.0
        for system, fraction in inputs["systems"].items():
            if system == "pasture":
                continue
            _mcf_key, _ef3_key, fracgas_key = SYSTEM_MAP_2006[system]
            n_system = head * nex * float(fraction)
            fracgas = _fracgas_ms(resolved, animal, fracgas_key)
            fracleach = _fracleach_ms(resolved, animal, fracgas_key) if include_leach else 0.0
            if include_leach:
                n_leach += n_system * fracleach * ef5
            n_lost += n_system * (fracgas + fracleach)
        n2o_leach = n_leach * N2ON_TO_N2O
        n_managed = head * nex - float(base["N_PRP_kg"])
        return {
            **base,
            "N2O_indirect_leach": n2o_leach,
            "N2O_total": float(base["N2O_total"]) + n2o_leach,
            "N_managed_kg": n_managed,
            "N_MMS_Avb_kg": n_managed - n_lost,
        }


def _fracleach_ms(params: Mapping[str, Any], animal: str, fracgas_key: str) -> float:
    candidates = [f"FracLeachMS_{animal}_{fracgas_key}"]
    if is_swine(animal):
        candidates.append(f"FracLeachMS_swine_{fracgas_key}")
        if fracgas_key == "liquid_slurry":
            candidates.append("FracLeachMS_swine_liquid_nocrust")
    if is_poultry(animal):
        candidates.append(f"FracLeachMS_poultry_{fracgas_key}")
    for name in candidates:
        if name in params:
            return float(params[name])
    return 0.0


errors = validate_module(IPCC2019Manure())
if errors:
    raise ValueError(f"IPCC2019Manure module validation failed: {errors}")
