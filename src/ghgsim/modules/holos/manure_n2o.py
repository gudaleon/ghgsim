"""
Holos Route A manure N2O (direct and indirect volatilisation).

Defaults are IPCC 2006 Vol 4 Ch 10:
- Direct: Equation 10.25
- Indirect volatilisation: Equations 10.26 and 10.27
- N excretion: Equation 10.30
Pasture N is returned as N_PRP_kg (Chapter 11), not manure EF3.
Leaching (Eq 10.28-10.29) is omitted: IPCC 2006 provides no default FracLeachMS.

The dairy-calf 0.078 kg N/head/day value is a labelled holos_as_coded fork
(UNVERIFIED). Holos file:line citations are traceability only.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import N2ON_TO_N2O, forks_from_inputs, option_is
from ghgsim.modules.holos.process_defs import (
    manure_n2o_direct_process,
    manure_n2o_indirect_leach_process,
    manure_n2o_indirect_vol_process,
)
from ghgsim.modules.livestock_types import is_poultry, is_swine

_DIRECT = manure_n2o_direct_process()
_INDIRECT = manure_n2o_indirect_vol_process()
_LEACH = manure_n2o_indirect_leach_process()

# system -> (EF3 key, FracGasMS key). Pasture is excluded from manure N2O.
SYSTEM_N2O_KEYS = {
    "liquid_nocrust": ("liquid_nocrust", "liquid_slurry"),
    "liquid_crust": ("liquid_crust", "liquid_slurry"),
    "lagoon": ("lagoon", "lagoon"),
    "solid_storage": ("solid_storage", "solid_storage"),
    "dry_lot": ("dry_lot", "dry_lot"),
    "daily_spread": ("daily_spread", "daily_spread"),
    "pasture": (None, None),
    "poultry_with_litter": ("poultry_with_litter", "poultry_with_litter"),
    "poultry_without_litter": ("poultry_without_litter", "poultry_without_litter"),
    "pit": ("pit", "pit"),
}


def _nex_kg_year(inputs: Mapping[str, Any], params: Mapping[str, Any], fork_settings: dict[str, str]) -> float:
    """Annual N excretion per animal (kg N / year)."""
    animal_class = str(inputs.get("animal_class", "adult"))
    if animal_class == "calf" and option_is("HOLOS.NEX.calf_nrate", "holos_as_coded", fork_settings):
        return float(params["calf_n_kg_head_day"]) * 365.0
    if inputs.get("Nex_kg_yr") not in (None, ""):
        return float(inputs["Nex_kg_yr"])
    animal = inputs["animal_type"]
    nrate = None
    tam = None
    for nrate_name in (f"Nrate_{animal}", f"Nrate_{animal}_canada"):
        if nrate_name in params:
            nrate = float(params[nrate_name])
            break
    for tam_name in (f"TAM_{animal}", f"TAM_{animal}_canada"):
        if tam_name in params:
            tam = float(params[tam_name])
            break
    if nrate is None or tam is None:
        raise ValueError(f"Missing Nrate/TAM for animal_type '{animal}'")
    return nrate * tam / 1000.0 * 365.0


def _ef3(params: Mapping[str, Any], ef3_key: str) -> float:
    name = f"EF3_{ef3_key}"
    if name not in params:
        raise ValueError(f"Missing EF3 parameter '{name}'")
    return float(params[name])


def _fracgas(params: Mapping[str, Any], animal: str, fracgas_key: str) -> float:
    candidates = [f"FracGasMS_{animal}_{fracgas_key}"]
    if animal == "beef":
        candidates.append(f"FracGasMS_other_cattle_{fracgas_key}")
    elif animal == "other_cattle":
        candidates.append(f"FracGasMS_beef_{fracgas_key}")
    if is_swine(animal):
        candidates.append(f"FracGasMS_swine_{fracgas_key}")
        if fracgas_key == "liquid_slurry":
            candidates.append("FracGasMS_swine_liquid_nocrust")
    if is_poultry(animal):
        candidates.append(f"FracGasMS_poultry_{fracgas_key}")
    for name in candidates:
        if name in params:
            return float(params[name])
    raise ValueError(f"Missing FracGasMS for animal '{animal}' system '{fracgas_key}'")


def _fracleach(params: Mapping[str, Any], animal: str, fracgas_key: str) -> float:
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


class HolosManureN2O:
    """Manure N2O direct (Eq 10.25) and indirect volatilisation (Eq 10.26-10.27)."""

    id = "holos.manure_n2o"
    version = "1.0.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec(
            "animal_type",
            "dimensionless",
            "Animal type (dairy/beef/market_swine/breeding_swine/broilers/layers/turkeys)",
            "scalar",
            True,
        ),
        "systems": VarSpec("systems", "dimensionless", "Dict of system -> fraction", "scalar", True),
        "Nex_kg_yr": VarSpec("Nex_kg_yr", "kg N / year", "Nitrogen excretion override per animal", "scalar", False),
        "animal_class": VarSpec("animal_class", "dimensionless", "adult or calf (calf Nrate fork)", "scalar", False),
        "include_leach": VarSpec(
            "include_leach",
            "dimensionless",
            "If true, apply IPCC 2019 Table 10.22 FracLeachMS * EF5 (2006 has no default)",
            "scalar",
            False,
        ),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
    }

    parameters = {
        "Nrate_dairy_canada": ParamRef("HOLOS.Nrate.dairy|canada", "N excretion rate dairy"),
        "Nrate_beef_canada": ParamRef("HOLOS.Nrate.beef|canada", "N excretion rate beef"),
        "TAM_dairy_canada": ParamRef("HOLOS.TAM.dairy_lactating|canada", "Typical animal mass dairy"),
        "TAM_beef_canada": ParamRef("HOLOS.TAM.beef_cow_lactating|canada", "Typical animal mass beef"),
        "Nrate_market_swine": ParamRef("IPCC2006.Nrate.market_swine|north_america", "Nrate market swine"),
        "Nrate_breeding_swine": ParamRef("IPCC2006.Nrate.breeding_swine|north_america", "Nrate breeding swine"),
        "Nrate_broilers": ParamRef("IPCC2006.Nrate.broilers|north_america", "Nrate broilers"),
        "Nrate_layers": ParamRef("IPCC2006.Nrate.layers|north_america", "Nrate layers"),
        "Nrate_turkeys": ParamRef("IPCC2006.Nrate.turkeys|north_america", "Nrate turkeys"),
        "TAM_market_swine": ParamRef("IPCC2006.TAM.market_swine|north_america", "TAM market swine"),
        "TAM_breeding_swine": ParamRef("IPCC2006.TAM.breeding_swine|north_america", "TAM breeding swine"),
        "TAM_broilers": ParamRef("IPCC2006.TAM.broilers|north_america", "TAM broilers"),
        "TAM_layers": ParamRef("IPCC2006.TAM.layers|north_america", "TAM layers"),
        "TAM_turkeys": ParamRef("IPCC2006.TAM.turkeys|north_america", "TAM turkeys"),
        "calf_n_kg_head_day": ParamRef(
            "HOLOS.Nrate.dairy_calves_kg_head_day|canada",
            "Holos calf N excretion kg N/head/day; UNVERIFIED",
        ),
        "EF3_liquid_nocrust": ParamRef("IPCC2006.EF3.liquid_nocrust", "EF3 liquid no crust"),
        "EF3_liquid_crust": ParamRef("IPCC2006.EF3.liquid_crust", "EF3 liquid with crust"),
        "EF3_lagoon": ParamRef("IPCC2006.EF3.lagoon", "EF3 lagoon"),
        "EF3_solid_storage": ParamRef("IPCC2006.EF3.solid_storage", "EF3 solid storage"),
        "EF3_dry_lot": ParamRef("IPCC2006.EF3.dry_lot", "EF3 dry lot"),
        "EF3_daily_spread": ParamRef("IPCC2006.EF3.daily_spread", "EF3 daily spread"),
        "EF3_poultry_with_litter": ParamRef("IPCC2006.EF3.poultry_with_litter", "EF3 poultry with litter"),
        "EF3_poultry_without_litter": ParamRef(
            "IPCC2006.EF3.poultry_without_litter", "EF3 poultry without litter"
        ),
        "EF3_pit": ParamRef("IPCC2006.EF3.pit", "EF3 pit storage"),
        "EF4": ParamRef("IPCC2006.EF4.all", "EF4 volatilisation"),
        "EF5": ParamRef("IPCC2006.EF5.all", "EF5 leaching (used only when include_leach)"),
        "FracGasMS_dairy_liquid_slurry": ParamRef("IPCC2006.FracGasMS.dairy|liquid_slurry", "FracGasMS dairy liquid"),
        "FracGasMS_dairy_solid_storage": ParamRef("IPCC2006.FracGasMS.dairy|solid_storage", "FracGasMS dairy solid"),
        "FracGasMS_dairy_daily_spread": ParamRef("IPCC2006.FracGasMS.dairy|daily_spread", "FracGasMS dairy daily spread"),
        "FracGasMS_dairy_dry_lot": ParamRef("IPCC2006.FracGasMS.dairy|dry_lot", "FracGasMS dairy dry lot"),
        "FracGasMS_dairy_lagoon": ParamRef("IPCC2006.FracGasMS.dairy|lagoon", "FracGasMS dairy lagoon"),
        "FracGasMS_other_cattle_solid_storage": ParamRef(
            "IPCC2006.FracGasMS.other_cattle|solid_storage", "FracGasMS other cattle solid"
        ),
        "FracGasMS_other_cattle_dry_lot": ParamRef(
            "IPCC2006.FracGasMS.other_cattle|dry_lot", "FracGasMS other cattle dry lot"
        ),
        "FracGasMS_swine_liquid_slurry": ParamRef(
            "IPCC2006.FracGasMS.swine|liquid_slurry", "FracGasMS swine liquid/slurry"
        ),
        "FracGasMS_swine_pit": ParamRef("IPCC2006.FracGasMS.swine|pit", "FracGasMS swine pit"),
        "FracGasMS_swine_lagoon": ParamRef("IPCC2006.FracGasMS.swine|lagoon", "FracGasMS swine lagoon"),
        "FracGasMS_swine_solid_storage": ParamRef(
            "IPCC2006.FracGasMS.swine|solid_storage", "FracGasMS swine solid storage"
        ),
        "FracGasMS_poultry_poultry_with_litter": ParamRef(
            "IPCC2006.FracGasMS.poultry|poultry_with_litter", "FracGasMS poultry with litter"
        ),
        "FracGasMS_poultry_poultry_without_litter": ParamRef(
            "IPCC2006.FracGasMS.poultry|poultry_without_litter", "FracGasMS poultry without litter"
        ),
        "FracGasMS_poultry_lagoon": ParamRef("IPCC2006.FracGasMS.poultry|lagoon", "FracGasMS poultry lagoon"),
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
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct manure N2O", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilisation", "scalar", True),
        "N2O_indirect_leach": VarSpec(
            "N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching (0 unless include_leach)", "scalar", True
        ),
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Direct + indirect N2O", "scalar", True),
        "N_PRP_kg": VarSpec("N_PRP_kg", "kg N / year", "Nitrogen to pasture/range/paddock", "scalar", True),
        "Nex_kg_head": VarSpec("Nex_kg_head", "kg N / year", "Nitrogen excretion per animal", "scalar", True),
        "N_managed_kg": VarSpec("N_managed_kg", "kg N / year", "Managed manure N (non-PRP)", "scalar", True),
        "N_MMS_Avb_kg": VarSpec(
            "N_MMS_Avb_kg",
            "kg N / year",
            "Managed manure N remaining after FracGasMS (+ FracLeachMS if include_leach); Eq 10.34 without bedding",
            "scalar",
            True,
        ),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="Tables 10.19, 10.21, 10.22",
            equation="Equations 10.25, 10.26, 10.27, 10.30",
            page="10.55-10.59",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute manure N2O.

        Default: IPCC 2006 Eq 10.25 and 10.26-10.27 with Eq 10.30 Nex.
        Fork HOLOS.NEX.calf_nrate=holos_as_coded uses 0.078 kg N/head/day for calves.
        """
        fork_settings = forks_from_inputs(inputs)
        head = float(inputs["head"])
        animal = inputs["animal_type"]
        systems = inputs["systems"]
        nex = _nex_kg_year(inputs, params, fork_settings)
        ef4 = float(params["EF4"])
        include_leach = bool(inputs.get("include_leach", False))
        ef5 = float(params["EF5"]) if include_leach else 0.0

        n_direct = 0.0
        n_vol = 0.0
        n_leach = 0.0
        n_prp = 0.0
        n_managed = 0.0
        n_lost = 0.0
        for system, fraction in systems.items():
            if system not in SYSTEM_N2O_KEYS:
                raise ValueError(f"Unknown manure system '{system}'")
            ef3_key, fracgas_key = SYSTEM_N2O_KEYS[system]
            n_system = head * nex * float(fraction)
            if system == "pasture":
                n_prp += n_system
                continue
            n_managed += n_system
            fracgas = _fracgas(params, animal, fracgas_key)
            fracleach = _fracleach(params, animal, fracgas_key) if include_leach else 0.0
            n_direct += _DIRECT.compute_rate({"Nex_kg": n_system, "EF3": _ef3(params, ef3_key)})
            n_vol += _INDIRECT.compute_rate({"Nex_kg": n_system, "FracGasMS": fracgas, "EF4": ef4})
            if include_leach:
                n_leach += _LEACH.compute_rate({"Nex_kg": n_system, "FracLeachMS": fracleach, "EF5": ef5})
            n_lost += n_system * (fracgas + fracleach)

        n2o_direct = n_direct * N2ON_TO_N2O
        n2o_vol = n_vol * N2ON_TO_N2O
        n2o_leach = n_leach * N2ON_TO_N2O
        return {
            "N2O_direct": n2o_direct,
            "N2O_indirect_vol": n2o_vol,
            "N2O_indirect_leach": n2o_leach,
            "N2O_total": n2o_direct + n2o_vol + n2o_leach,
            "N_PRP_kg": n_prp,
            "Nex_kg_head": nex,
            "N_managed_kg": n_managed,
            "N_MMS_Avb_kg": n_managed - n_lost,
        }


errors = validate_module(HolosManureN2O())
if errors:
    raise ValueError(f"HolosManureN2O module validation failed: {errors}")
