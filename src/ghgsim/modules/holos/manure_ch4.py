"""
Holos Route A manure CH4.

Default is IPCC 2006 Vol 4 Ch 10 Equation 10.23.
CE-14 cover/crust multiplicative factors are a labelled holos_as_coded fork
(UNVERIFIED coefficients). Default uses Table 10.17 MCF by system instead.

Holos file:line citations are traceability only and are not copied source.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import forks_from_inputs, option_is
from ghgsim.modules.holos.process_defs import manure_ch4_process

_CH4 = manure_ch4_process()

# Map user system names to MCF parameter stem (IPCC 2006 Table 10.17).
SYSTEM_MCF_KEY = {
    "liquid_nocrust": "liquid_nocrust",
    "liquid_crust": "liquid_crust",
    "lagoon": "lagoon",
    "solid_storage": "solid_storage",
    "dry_lot": "dry_lot",
    "daily_spread": "daily_spread",
    "pasture": "pasture",
}


def _mcf_for_system(system: str, climate: str, params: Mapping[str, Any]) -> float:
    """Look up MCF for a system and climate zone; fall back to cool then 15C names."""
    stem = SYSTEM_MCF_KEY[system]
    for name in (f"MCF_{stem}_{climate}", f"MCF_{stem}_cool", f"MCF_{stem}_15C", f"MCF_{stem}_temperate"):
        if name in params:
            return float(params[name])
    raise ValueError(f"No MCF parameter for system '{system}' (climate '{climate}')")


def _weighted_mcf(systems: Mapping[str, float], climate: str, params: Mapping[str, Any]) -> float:
    return sum(_mcf_for_system(system, climate, params) * float(fraction) for system, fraction in systems.items())


def _cover_reduction(cover_type: str, params: Mapping[str, Any], fork_settings: dict[str, str]) -> float:
    if not option_is("HOLOS.CH4.cover_reduction", "holos_as_coded", fork_settings):
        return 1.0
    if cover_type == "natural_crust":
        return float(params["cover_crust_factor"])
    if cover_type == "other_cover":
        return float(params["cover_other_factor"])
    return 1.0


class HolosManureCH4:
    """
    Manure methane, IPCC 2006 Eq 10.23.

    CH4 (kg/year) = VS * 365 * B0 * 0.67 * Σ(MCF_i * MS_i)
    """

    id = "holos.manure_ch4"
    version = "1.0.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec("animal_type", "dimensionless", "Animal type (dairy/beef)", "scalar", True),
        "climate_zone": VarSpec("climate_zone", "dimensionless", "Climate zone for MCF (cool/temperate/15C)", "scalar", True),
        "systems": VarSpec("systems", "dimensionless", "Dict of system -> fraction", "scalar", True),
        "VS_kg_day": VarSpec("VS_kg_day", "kg / day", "Volatile solids excretion override", "scalar", False),
        "cover_type": VarSpec(
            "cover_type",
            "dimensionless",
            "none, natural_crust, or other_cover (CE-14 fork)",
            "scalar",
            False,
        ),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
    }

    parameters = {
        "VS_dairy_canada": ParamRef("HOLOS.VS.dairy|canada", "Fallback VS for Canadian dairy"),
        "VS_beef_canada": ParamRef("HOLOS.VS.beef|canada", "Fallback VS for Canadian beef"),
        "B0_dairy_canada": ParamRef("HOLOS.B0.dairy|canada", "B0 for Canadian dairy"),
        "B0_beef_canada": ParamRef("HOLOS.B0.beef|canada", "B0 for Canadian beef"),
        "MCF_liquid_nocrust_cool": ParamRef("HOLOS.MCF.liquid_nocrust|cool", "MCF liquid no crust, cool"),
        "MCF_liquid_nocrust_temperate": ParamRef("HOLOS.MCF.liquid_nocrust|temperate", "MCF liquid no crust, temperate"),
        "MCF_liquid_crust_cool": ParamRef("IPCC2006.MCF.liquid_crust|le10C", "MCF liquid with crust, cool"),
        "MCF_liquid_crust_temperate": ParamRef("IPCC2006.MCF.liquid_crust|15C", "MCF liquid with crust, temperate"),
        "MCF_solid_storage_cool": ParamRef("HOLOS.MCF.solid_storage|cool", "MCF solid storage, cool"),
        "MCF_solid_storage_temperate": ParamRef("HOLOS.MCF.solid_storage|temperate", "MCF solid storage, temperate"),
        "MCF_pasture_cool": ParamRef("HOLOS.MCF.pasture|cool", "MCF pasture, cool"),
        "MCF_daily_spread_cool": ParamRef("HOLOS.MCF.daily_spread|cool", "MCF daily spread, cool"),
        "CH4_M3_TO_KG": ParamRef("BOTH.CH4_M3_TO_KG.all", "CH4 density kg/m3"),
        "cover_crust_factor": ParamRef(
            "HOLOS.COVER.natural_crust_factor",
            "Holos natural-crust CH4 multiplier (CE-14); UNVERIFIED",
        ),
        "cover_other_factor": ParamRef(
            "HOLOS.COVER.other_cover_factor",
            "Holos other-cover CH4 multiplier (CE-14); UNVERIFIED",
        ),
    }

    outputs = {
        "CH4": VarSpec("CH4", "kg CH4 / year", "Total manure CH4 emissions", "scalar", True),
        "MCF_weighted": VarSpec("MCF_weighted", "fraction", "Fraction-weighted MCF", "scalar", True),
        "cover_reduction_used": VarSpec("cover_reduction_used", "fraction", "Cover multiplier applied", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="Table 10.17",
            equation="Equation 10.23",
            page="10.53",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute manure CH4.

        Default: IPCC 2006 Eq 10.23 with Table 10.17 MCF.
        Fork HOLOS.CH4.cover_reduction=holos_as_coded applies CE-14 factors.
        """
        fork_settings = forks_from_inputs(inputs)
        head = float(inputs["head"])
        animal = inputs["animal_type"]
        climate = inputs["climate_zone"]
        systems = inputs["systems"]
        cover_type = str(inputs.get("cover_type", "none"))

        if inputs.get("VS_kg_day") not in (None, ""):
            vs = float(inputs["VS_kg_day"])
        else:
            vs = float(params[f"VS_{animal}_canada"])
        b0 = float(params[f"B0_{animal}_canada"])
        density = float(params["CH4_M3_TO_KG"])
        mcf = _weighted_mcf(systems, climate, params)
        reduction = _cover_reduction(cover_type, params, fork_settings)
        process_fork = (
            "holos_as_coded"
            if option_is("HOLOS.CH4.cover_reduction", "holos_as_coded", fork_settings)
            else None
        )
        ch4_kg_day = _CH4.compute_rate(
            {
                "VS": vs,
                "B0": b0,
                "MCF": mcf,
                "CH4_M3_TO_KG": density,
                "cover_reduction": reduction,
            },
            fork=process_fork,
        )
        return {
            "CH4": head * ch4_kg_day * 365.0,
            "MCF_weighted": mcf,
            "cover_reduction_used": reduction,
        }


errors = validate_module(HolosManureCH4())
if errors:
    raise ValueError(f"HolosManureCH4 module validation failed: {errors}")
