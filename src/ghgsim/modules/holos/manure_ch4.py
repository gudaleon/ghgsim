"""
Holos Route A manure CH4.

Default is IPCC 2006 Vol 4 Ch 10 Equation 10.23.
CE-14 cover/crust factors are a labelled holos_as_coded fork. Holos applies
them as reduction fractions (remaining = 1 - reduction), consistent with
its manual and with IPCC 2006/2019 Table 10.17 crust treatment. The fork
difference versus source_correct is the MCF-free tank approximation, not a
reduction/retention mix-up.

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

# Holos IsCoveredSystem is true only for LiquidWithNaturalCrust and
# LiquidWithSolidCover (ManureStateTypeExtensions.cs:53-56). 0.25 applies
# to solid cover only, not to every non-crust cover type.
_COVER_REDUCTION_PARAM = {
    "natural_crust": "cover_crust_reduction",
    "solid_cover": "cover_solid_reduction",
}


def _mcf_for_system(system: str, climate: str, params: Mapping[str, Any]) -> float:
    """Look up MCF for a system and climate zone; fall back to cool then 15C names."""
    stem = SYSTEM_MCF_KEY[system]
    for name in (f"MCF_{stem}_{climate}", f"MCF_{stem}_cool", f"MCF_{stem}_15C", f"MCF_{stem}_temperate"):
        if name in params:
            return float(params[name])
    raise ValueError(f"No MCF parameter for system '{system}' (climate '{climate}')")


def _systems_for_mcf(systems: Mapping[str, float], cover_applies: bool) -> dict[str, float]:
    """
    MCF lookup systems for this stream.

    When the Holos cover-reduction fork applies, do not also use the IPCC
    with-crust MCF. IPCC 2006 Table 10.17 p. 10.44 footnote already builds
    the ~40% crust reduction into with-crust MCF (cool 10% vs 17%; 15C 17%
    vs 27%). Holos's covered path is an MCF-free daily VS-consumed tank
    (AnimalResultsServiceBase.cs:1279-1283 applies remaining = 1 - reduction
    to tank CH4). This fork approximates that tank with the uncovered
    liquid_nocrust MCF times (1 - reduction). Stacking liquid_crust MCF on
    the Holos remaining factor would double-count the crust.
    """
    if not cover_applies:
        return {str(system): float(fraction) for system, fraction in systems.items()}
    remapped: dict[str, float] = {}
    for system, fraction in systems.items():
        key = "liquid_nocrust" if system == "liquid_crust" else str(system)
        remapped[key] = remapped.get(key, 0.0) + float(fraction)
    return remapped


def _weighted_mcf(systems: Mapping[str, float], climate: str, params: Mapping[str, Any]) -> float:
    return sum(_mcf_for_system(system, climate, params) * float(fraction) for system, fraction in systems.items())


def _cover_reduction_fraction(
    cover_type: str, params: Mapping[str, Any], fork_settings: dict[str, str]
) -> float:
    """Holos reduction fraction (0.40 crust, 0.25 solid cover) or 0.0."""
    if not option_is("HOLOS.CH4.cover_reduction", "holos_as_coded", fork_settings):
        return 0.0
    key = _COVER_REDUCTION_PARAM.get(cover_type)
    if key is None:
        return 0.0
    return float(params[key])


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
            "none, natural_crust, or solid_cover (CE-14 fork; 0.25 only for solid_cover)",
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
        "cover_crust_reduction": ParamRef(
            "HOLOS.COVER.natural_crust_reduction",
            "Holos natural-crust CH4 reduction fraction 0.40 (CE-14); remaining = 0.60",
        ),
        "cover_solid_reduction": ParamRef(
            "HOLOS.COVER.solid_cover_reduction",
            "Holos solid-cover CH4 reduction fraction 0.25 (CE-14); remaining = 0.75",
        ),
    }

    outputs = {
        "CH4": VarSpec("CH4", "kg CH4 / year", "Total manure CH4 emissions", "scalar", True),
        "MCF_weighted": VarSpec("MCF_weighted", "fraction", "Fraction-weighted MCF", "scalar", True),
        "cover_reduction_fraction": VarSpec(
            "cover_reduction_fraction",
            "fraction",
            "Holos cover reduction (0.40 crust / 0.25 solid / 0)",
            "scalar",
            True,
        ),
        "cover_remaining_used": VarSpec(
            "cover_remaining_used",
            "fraction",
            "Multiplier applied = 1 - cover_reduction_fraction",
            "scalar",
            True,
        ),
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

        Default: IPCC 2006 Eq 10.23 with Table 10.17 MCF (crust is in MCF).
        Fork HOLOS.CH4.cover_reduction=holos_as_coded multiplies by
        (1 - reduction) and skips the IPCC with-crust MCF for that stream.
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
        reduction = _cover_reduction_fraction(cover_type, params, fork_settings)
        remaining = 1.0 - reduction
        mcf = _weighted_mcf(_systems_for_mcf(systems, reduction > 0.0), climate, params)
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
            "cover_reduction_fraction": reduction,
            "cover_remaining_used": remaining,
        }


errors = validate_module(HolosManureCH4())
if errors:
    raise ValueError(f"HolosManureCH4 module validation failed: {errors}")
