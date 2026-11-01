"""
Holos Route A volatile solids excretion.

Default is IPCC 2006 Vol 4 Ch 10 Equation 10.24 (DE%, IPCC UE).
Confirmed Holos discrepancies are labelled holos_as_coded forks.

No Holos GPL code is copied. Holos file:line citations are traceability only.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import forks_from_inputs, option_is
from ghgsim.modules.holos.forks import resolve_option
from ghgsim.modules.holos.process_defs import (
    calf_vs_holos_process,
    urinary_energy_holos,
    urinary_energy_ipcc,
    volatile_solids_process,
)

_VS = volatile_solids_process()
_CALF_VS = calf_vs_holos_process()
_UE_IPCC = urinary_energy_ipcc()
_UE_HOLOS = urinary_energy_holos()


def _urinary_energy(de_percent: float, forage_percent: float, fork_settings: dict[str, str]) -> float:
    """UE as a fraction of GE. Default: IPCC 2006 p. 10.54. Fork: Holos grain switch."""
    if option_is("HOLOS.VS.urinary_energy", "holos_as_coded", fork_settings):
        return _UE_HOLOS.compute({"forage_percent": forage_percent})
    return _UE_IPCC.compute({"DE_percent": de_percent})


class HolosVolatileSolids:
    """
    Daily volatile solids excretion.

    VS = [GE * (1 - DE%/100) + UE * GE] * (1 - ASH/100) / 18.45
    IPCC 2006 Vol 4 Ch 10 Equation 10.24, p. 10.54.
    """

    id = "holos.vs"
    version = "1.0.0"

    inputs = {
        "GE_MJ_day": VarSpec("GE_MJ_day", "MJ / day", "Gross energy intake", "scalar", True),
        "DE_percent": VarSpec("DE_percent", "% GE", "Digestible energy as percent of GE", "scalar", True),
        "ASH_percent": VarSpec("ASH_percent", "% DM", "Ash content of manure / feed DM", "scalar", True),
        "forage_percent": VarSpec("forage_percent", "% diet", "Forage fraction of diet (Holos UE switch)", "scalar", False),
        "TDN_percent": VarSpec("TDN_percent", "%", "Total digestible nutrients (holos_as_coded VS fork)", "scalar", False),
        "animal_class": VarSpec("animal_class", "dimensionless", "adult or calf (CE-07 fork)", "scalar", False),
        "weight_kg": VarSpec("weight_kg", "kg", "Live weight (CE-07 holos_as_coded calf VS)", "scalar", False),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
    }

    parameters = {
        "GE_PER_KG_DM": ParamRef("BOTH.GE_PER_KG_DM.all", "Gross energy per kg dry matter (MJ/kg)"),
        "calf_vs_coeff": ParamRef(
            "HOLOS.VS.dairy_calves_coeff|canada",
            "Holos calf VS coefficient (kg VS / kg weight / day); UNVERIFIED",
        ),
    }

    outputs = {
        "VS_kg_day": VarSpec("VS_kg_day", "kg / day", "Volatile solids excretion per animal", "scalar", True),
        "UE_used": VarSpec("UE_used", "fraction of GE", "Urinary energy fraction used", "scalar", True),
        "digestibility_used": VarSpec("digestibility_used", "%", "DE% or TDN% used in Eq 10.24", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="",
            equation="Equation 10.24",
            page="10.54",
            notes="UE text on the same page: 0.04 typical; 0.02 when DE% > ~80%",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute daily VS.

        Default: IPCC 2006 Eq 10.24 with DE% and IPCC UE.
        Forks: HOLOS.VS.digestibility, HOLOS.VS.urinary_energy, HOLOS.VS.calf_coeff.
        """
        fork_settings = forks_from_inputs(inputs)
        animal_class = str(inputs.get("animal_class", "adult"))
        ge_per_kg = float(params["GE_PER_KG_DM"])

        if animal_class == "calf" and option_is("HOLOS.VS.calf_coeff", "holos_as_coded", fork_settings):
            weight = inputs.get("weight_kg")
            if weight in (None, ""):
                raise ValueError("weight_kg is required for HOLOS.VS.calf_coeff=holos_as_coded")
            vs = _CALF_VS.compute_rate(
                {"calf_vs_coeff": float(params["calf_vs_coeff"]), "weight_kg": float(weight)}
            )
            return {
                "VS_kg_day": vs,
                "UE_used": float("nan"),
                "digestibility_used": float("nan"),
            }

        ge = float(inputs["GE_MJ_day"])
        de_percent = float(inputs["DE_percent"])
        tdn_percent = float(inputs.get("TDN_percent", de_percent))
        ash_percent = float(inputs["ASH_percent"])
        forage_percent = float(inputs.get("forage_percent", 100.0))
        ue = _urinary_energy(de_percent, forage_percent, fork_settings)

        tdn_option = resolve_option("HOLOS.VS.digestibility", fork_settings)
        process_fork = "holos_as_coded" if tdn_option == "holos_as_coded" else None
        vs = _VS.compute_rate(
            {
                "GE": ge,
                "DE_percent": de_percent,
                "TDN_percent": tdn_percent,
                "UE": ue,
                "ASH_percent": ash_percent,
                "GE_PER_KG_DM": ge_per_kg,
            },
            fork=process_fork,
        )
        digestibility = tdn_percent if process_fork == "holos_as_coded" else de_percent
        return {
            "VS_kg_day": vs,
            "UE_used": ue,
            "digestibility_used": digestibility,
        }


errors = validate_module(HolosVolatileSolids())
if errors:
    raise ValueError(f"HolosVolatileSolids module validation failed: {errors}")
