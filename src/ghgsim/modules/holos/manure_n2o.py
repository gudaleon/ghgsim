"""
Holos Route A manure N2O (direct and indirect volatilisation).

Defaults are IPCC 2006 Vol 4 Ch 10:
- Direct: Equation 10.25
- Indirect volatilisation: Equations 10.26 and 10.27
- N excretion: Equation 10.30
Pasture N is returned as N_PRP_kg (Chapter 11), not manure EF3.
Leaching (Eq 10.28-10.29) is omitted: IPCC 2006 provides no default FracLeachMS.

The dairy-calf 0.078 kg N/head/day value is a labelled holos_as_coded fork
(UNVERIFIED). No Holos GPL code is copied.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import N2ON_TO_N2O, forks_from_inputs, option_is
from ghgsim.modules.holos.process_defs import (
    manure_n2o_direct_process,
    manure_n2o_indirect_vol_process,
)

_DIRECT = manure_n2o_direct_process()
_INDIRECT = manure_n2o_indirect_vol_process()

# system -> (EF3 key, FracGasMS key). Pasture is excluded from manure N2O.
SYSTEM_N2O_KEYS = {
    "liquid_nocrust": ("liquid_nocrust", "liquid_slurry"),
    "liquid_crust": ("liquid_crust", "liquid_slurry"),
    "lagoon": ("lagoon", "lagoon"),
    "solid_storage": ("solid_storage", "solid_storage"),
    "dry_lot": ("dry_lot", "dry_lot"),
    "daily_spread": ("daily_spread", "daily_spread"),
    "pasture": (None, None),
}


def _nex_kg_year(inputs: Mapping[str, Any], params: Mapping[str, Any], fork_settings: dict[str, str]) -> float:
    """Annual N excretion per animal (kg N / year)."""
    animal_class = str(inputs.get("animal_class", "adult"))
    if animal_class == "calf" and option_is("HOLOS.NEX.calf_nrate", "holos_as_coded", fork_settings):
        return float(params["calf_n_kg_head_day"]) * 365.0
    if inputs.get("Nex_kg_yr") not in (None, ""):
        return float(inputs["Nex_kg_yr"])
    animal = inputs["animal_type"]
    nrate = float(params[f"Nrate_{animal}_canada"])
    tam = float(params[f"TAM_{animal}_canada"])
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
    for name in candidates:
        if name in params:
            return float(params[name])
    raise ValueError(f"Missing FracGasMS for animal '{animal}' system '{fracgas_key}'")


class HolosManureN2O:
    """Manure N2O direct (Eq 10.25) and indirect volatilisation (Eq 10.26-10.27)."""

    id = "holos.manure_n2o"
    version = "1.0.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec("animal_type", "dimensionless", "Animal type (dairy/beef)", "scalar", True),
        "systems": VarSpec("systems", "dimensionless", "Dict of system -> fraction", "scalar", True),
        "Nex_kg_yr": VarSpec("Nex_kg_yr", "kg N / year", "Nitrogen excretion override per animal", "scalar", False),
        "animal_class": VarSpec("animal_class", "dimensionless", "adult or calf (calf Nrate fork)", "scalar", False),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
    }

    parameters = {
        "Nrate_dairy_canada": ParamRef("HOLOS.Nrate.dairy|canada", "N excretion rate dairy"),
        "Nrate_beef_canada": ParamRef("HOLOS.Nrate.beef|canada", "N excretion rate beef"),
        "TAM_dairy_canada": ParamRef("HOLOS.TAM.dairy_lactating|canada", "Typical animal mass dairy"),
        "TAM_beef_canada": ParamRef("HOLOS.TAM.beef_cow_lactating|canada", "Typical animal mass beef"),
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
        "EF4": ParamRef("IPCC2006.EF4.all", "EF4 volatilisation"),
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
    }

    outputs = {
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct manure N2O", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilisation", "scalar", True),
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Direct + indirect volatilisation N2O", "scalar", True),
        "N_PRP_kg": VarSpec("N_PRP_kg", "kg N / year", "Nitrogen to pasture/range/paddock", "scalar", True),
        "Nex_kg_head": VarSpec("Nex_kg_head", "kg N / year", "Nitrogen excretion per animal", "scalar", True),
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

        n_direct = 0.0
        n_vol = 0.0
        n_prp = 0.0
        for system, fraction in systems.items():
            if system not in SYSTEM_N2O_KEYS:
                raise ValueError(f"Unknown manure system '{system}'")
            ef3_key, fracgas_key = SYSTEM_N2O_KEYS[system]
            n_system = head * nex * float(fraction)
            if system == "pasture":
                n_prp += n_system
                continue
            n_direct += _DIRECT.compute_rate({"Nex_kg": n_system, "EF3": _ef3(params, ef3_key)})
            n_vol += _INDIRECT.compute_rate(
                {
                    "Nex_kg": n_system,
                    "FracGasMS": _fracgas(params, animal, fracgas_key),
                    "EF4": ef4,
                }
            )

        n2o_direct = n_direct * N2ON_TO_N2O
        n2o_vol = n_vol * N2ON_TO_N2O
        return {
            "N2O_direct": n2o_direct,
            "N2O_indirect_vol": n2o_vol,
            "N2O_total": n2o_direct + n2o_vol,
            "N_PRP_kg": n_prp,
            "Nex_kg_head": nex,
        }


errors = validate_module(HolosManureN2O())
if errors:
    raise ValueError(f"HolosManureN2O module validation failed: {errors}")
