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
from ghgsim.modules.holos.liquid_tank import LIQUID_SYSTEMS, TANK_ANIMALS, run_liquid_tank
from ghgsim.modules.holos.process_defs import manure_ch4_process, turkey_manure_ch4_holos_process

_CH4 = manure_ch4_process()
_TURKEY_HOLOS = turkey_manure_ch4_holos_process()

# Map user system names to MCF parameter stem (IPCC 2006 Table 10.17).
SYSTEM_MCF_KEY = {
    "liquid_nocrust": "liquid_nocrust",
    "liquid_crust": "liquid_crust",
    "lagoon": "lagoon",
    "solid_storage": "solid_storage",
    "dry_lot": "dry_lot",
    "daily_spread": "daily_spread",
    "pasture": "pasture",
    "poultry_with_litter": "poultry_with_litter",
    "poultry_without_litter": "poultry_without_litter",
    "pit": "pit_gt1mo",
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


def _vs_for(animal: str, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> float:
    if inputs.get("VS_kg_day") not in (None, ""):
        return float(inputs["VS_kg_day"])
    for name in (f"VS_{animal}", f"VS_{animal}_canada"):
        if name in params:
            return float(params[name])
    raise ValueError(f"No VS parameter for animal_type '{animal}'")


def _b0_for(animal: str, params: Mapping[str, Any]) -> float:
    for name in (f"B0_{animal}", f"B0_{animal}_canada"):
        if name in params:
            return float(params[name])
    raise ValueError(f"No B0 parameter for animal_type '{animal}'")


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
    version = "1.1.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec(
            "animal_type",
            "dimensionless",
            "Animal type (dairy/beef/market_swine/breeding_swine/broilers/layers/turkeys)",
            "scalar",
            True,
        ),
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
        "temperatures_c": VarSpec(
            "temperatures_c",
            "degC",
            "Daily mean outdoor temperature for the Holos liquid tank (Eq 4.1.3-1). Required only for holos_v4_liquid_tank.",
            "scalar",
            False,
        ),
        "dates": VarSpec(
            "dates",
            "dimensionless",
            "ISO dates aligned with temperatures_c. Required for the 1 January VS reset fork.",
            "scalar",
            False,
        ),
        "removal_fractions": VarSpec(
            "removal_fractions",
            "fraction",
            "Fraction of stored manure removed on each day (Eq 4.1.3-6). Applied to the next day's carryover, capped at 0.95.",
            "scalar",
            False,
        ),
    }

    parameters = {
        "VS_dairy_canada": ParamRef("HOLOS.VS.dairy|canada", "Fallback VS for Canadian dairy"),
        "VS_beef_canada": ParamRef("HOLOS.VS.beef|canada", "Fallback VS for Canadian beef"),
        "B0_dairy_canada": ParamRef("HOLOS.B0.dairy|canada", "B0 for Canadian dairy"),
        "B0_beef_canada": ParamRef("HOLOS.B0.beef|canada", "B0 for Canadian beef"),
        "VS_market_swine": ParamRef("IPCC2006.VS.market_swine|north_america", "VS market swine NA"),
        "VS_breeding_swine": ParamRef("IPCC2006.VS.breeding_swine|north_america", "VS breeding swine NA"),
        "VS_broilers": ParamRef("IPCC2006.VS.broilers|north_america", "VS broilers"),
        "VS_layers": ParamRef("IPCC2006.VS.layers|north_america", "VS layers"),
        "VS_turkeys": ParamRef("IPCC2006.VS.turkeys|north_america", "VS turkeys"),
        "B0_market_swine": ParamRef("IPCC2006.B0.market_swine|north_america", "B0 market swine NA"),
        "B0_breeding_swine": ParamRef("IPCC2006.B0.breeding_swine|north_america", "B0 breeding swine NA"),
        "B0_broilers": ParamRef("IPCC2006.B0.broilers|north_america", "B0 broilers"),
        "B0_layers": ParamRef("IPCC2006.B0.layers|north_america", "B0 layers"),
        "B0_turkeys": ParamRef("IPCC2006.B0.turkeys|north_america", "B0 turkeys"),
        "MCF_liquid_nocrust_cool": ParamRef("HOLOS.MCF.liquid_nocrust|cool", "MCF liquid no crust, cool"),
        "MCF_liquid_nocrust_temperate": ParamRef("HOLOS.MCF.liquid_nocrust|temperate", "MCF liquid no crust, temperate"),
        "MCF_liquid_crust_cool": ParamRef("IPCC2006.MCF.liquid_crust|le10C", "MCF liquid with crust, cool"),
        "MCF_liquid_crust_temperate": ParamRef("IPCC2006.MCF.liquid_crust|15C", "MCF liquid with crust, temperate"),
        "MCF_solid_storage_cool": ParamRef("HOLOS.MCF.solid_storage|cool", "MCF solid storage, cool"),
        "MCF_solid_storage_temperate": ParamRef("HOLOS.MCF.solid_storage|temperate", "MCF solid storage, temperate"),
        "MCF_pasture_cool": ParamRef("HOLOS.MCF.pasture|cool", "MCF pasture, cool"),
        "MCF_daily_spread_cool": ParamRef("HOLOS.MCF.daily_spread|cool", "MCF daily spread, cool"),
        "MCF_poultry_with_litter_15C": ParamRef(
            "IPCC2006.MCF.poultry_with_litter|15C", "MCF poultry with litter 15C"
        ),
        "MCF_poultry_with_litter_le10C": ParamRef(
            "IPCC2006.MCF.poultry_with_litter|le10C", "MCF poultry with litter cool"
        ),
        "MCF_poultry_without_litter_15C": ParamRef(
            "IPCC2006.MCF.poultry_without_litter|15C", "MCF poultry without litter 15C"
        ),
        "MCF_poultry_without_litter_le10C": ParamRef(
            "IPCC2006.MCF.poultry_without_litter|le10C", "MCF poultry without litter cool"
        ),
        "MCF_pit_gt1mo_15C": ParamRef("IPCC2006.MCF.pit_gt1mo|15C", "MCF pit >1 month 15C"),
        "MCF_pit_gt1mo_le10C": ParamRef("IPCC2006.MCF.pit_gt1mo|le10C", "MCF pit >1 month cool"),
        "CH4_M3_TO_KG": ParamRef("BOTH.CH4_M3_TO_KG.all", "CH4 density kg/m3"),
        "cover_crust_reduction": ParamRef(
            "HOLOS.COVER.natural_crust_reduction",
            "Holos natural-crust CH4 reduction fraction 0.40 (CE-14); remaining = 0.60",
        ),
        "cover_solid_reduction": ParamRef(
            "HOLOS.COVER.solid_cover_reduction",
            "Holos solid-cover CH4 reduction fraction 0.25 (CE-14); remaining = 0.75",
        ),
        "TANK_T1_K": ParamRef("HOLOS.TANK.T1_K", "Eq 4.1.3-2 reference temperature 308.16 K"),
        "TANK_E_CAL": ParamRef("HOLOS.TANK.activation_energy_cal_mol", "Eq 4.1.3-2 activation energy 19347 cal/mol"),
        "TANK_R_CAL": ParamRef("HOLOS.TANK.ideal_gas_constant_cal", "Eq 4.1.3-2 gas constant 1.987 cal/K/mol"),
        "TANK_TEMP_FLOOR_C": ParamRef("HOLOS.TANK.temp_floor_C", "Eq 4.1.3-1 floor: Temp <= 1 C uses 1 C"),
        "TANK_KELVIN": ParamRef("HOLOS.TANK.kelvin_offset", "Eq 4.1.3-1 Celsius to Kelvin offset 273.15"),
        "TANK_WINDOW_MANUAL": ParamRef("HOLOS.TANK.window_days_manual", "Manual last-30-day temperature window"),
        "TANK_WINDOW_CODED": ParamRef("HOLOS.TANK.window_days_coded", "Coded inclusive date-30 window (31 days)"),
        "TANK_MDP": ParamRef("HOLOS.TANK.MDP", "Eq 4.1.3-4 management and design practice factor, default 1"),
        "TANK_MAX_REMOVAL": ParamRef("HOLOS.TANK.max_removal_fraction", "Eq 4.1.3-6 emptying cap 0.95"),
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
        "tank_applied": VarSpec(
            "tank_applied",
            "dimensionless",
            "True when CH4 came from the Holos V4 liquid tank",
            "scalar",
            True,
        ),
        "tank_status": VarSpec(
            "tank_status",
            "dimensionless",
            "not_selected, not_applicable, UNVERIFIED-input, or computed",
            "scalar",
            True,
        ),
        "CH4_ipcc_eq10_23": VarSpec(
            "CH4_ipcc_eq10_23",
            "kg CH4 / year",
            "IPCC Eq 10.23 value for the same inputs, including when the tank is used",
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
        Citation(
            source="Pogue et al. 2026, Holos Version 4.0 Algorithm Documentation (print PDF)",
            table="",
            equation="Equations 4.1.3-1 to 4.1.3-10",
            page="161-162",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute manure CH4.

        Default: IPCC 2006 Eq 10.23 with Table 10.17 MCF (crust is in MCF).
        Fork HOLOS.CH4.cover_reduction=holos_as_coded multiplies by
        (1 - reduction) and skips the IPCC with-crust MCF for that stream.

        HOLOS.CH4.liquid_tank=holos_v4_liquid_tank uses Holos V4 Eq 4.1.3-1..10
        for liquid dairy and swine when daily temperatures are supplied.
        Missing temperatures stay on Eq 10.23 with tank_status UNVERIFIED-input.
        """
        fork_settings = forks_from_inputs(inputs)
        head = float(inputs["head"])
        animal = inputs["animal_type"]
        systems = inputs["systems"]
        cover_type = str(inputs.get("cover_type", "none"))

        if animal == "turkeys" and option_is("HOLOS.CH4.turkey_zero", "holos_as_coded", fork_settings):
            _TURKEY_HOLOS.compute_rate(
                {"VS": 0.0, "B0": 0.0, "MCF": 0.0, "CH4_M3_TO_KG": 0.0},
                fork="holos_as_coded",
            )
            return _annotate_tank(
                {
                    "CH4": 0.0,
                    "MCF_weighted": 0.0,
                    "cover_reduction_fraction": 0.0,
                    "cover_remaining_used": 1.0,
                },
                applied=False,
                status="not_selected",
            )
        ipcc = _ipcc_manure_ch4(inputs, params, fork_settings)
        if not option_is("HOLOS.CH4.liquid_tank", "holos_v4_liquid_tank", fork_settings):
            return _annotate_tank(ipcc, applied=False, status="not_selected")
        if not _tank_eligible(animal, systems):
            return _annotate_tank(ipcc, applied=False, status="not_applicable")
        temperatures = inputs.get("temperatures_c")
        if not temperatures:
            return _annotate_tank(ipcc, applied=False, status="UNVERIFIED-input")
        reduction = _tank_cover_reduction(cover_type, params)
        tank = run_liquid_tank(
            head=head,
            vs_kg_day=_vs_for(animal, inputs, params),
            b0=_b0_for(animal, params),
            ch4_density=float(params["CH4_M3_TO_KG"]),
            cover_reduction=reduction,
            temperatures_c=temperatures,
            params=params,
            dates=inputs.get("dates"),
            removal_fractions=inputs.get("removal_fractions"),
            year_reset=option_is("HOLOS.STORAGE.year_reset", "holos_as_coded", fork_settings),
            coded_temp_window=option_is("HOLOS.STORAGE.temp_window", "holos_as_coded", fork_settings),
            ignore_removals=option_is("HOLOS.STORAGE.cli_no_drain", "holos_as_coded", fork_settings),
        )
        return {
            "CH4": tank["CH4"],
            "MCF_weighted": tank["MCF_implied"],
            "cover_reduction_fraction": reduction,
            "cover_remaining_used": 1.0 - reduction,
            "tank_applied": True,
            "tank_status": "computed",
            "CH4_ipcc_eq10_23": ipcc["CH4"],
        }


def _ipcc_manure_ch4(
    inputs: Mapping[str, Any], params: Mapping[str, Any], fork_settings: dict[str, str]
) -> dict[str, Any]:
    """IPCC 2006 Eq 10.23, including the CE-14 cover fork."""
    animal = inputs["animal_type"]
    climate = inputs["climate_zone"]
    systems = inputs["systems"]
    cover_type = str(inputs.get("cover_type", "none"))
    head = float(inputs["head"])
    vs = _vs_for(animal, inputs, params)
    b0 = _b0_for(animal, params)
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


def _annotate_tank(result: dict[str, Any], *, applied: bool, status: str) -> dict[str, Any]:
    return {
        **result,
        "tank_applied": applied,
        "tank_status": status,
        "CH4_ipcc_eq10_23": result["CH4"],
    }


def _tank_eligible(animal: str, systems: Mapping[str, float]) -> bool:
    """Manual Sec 4.1.3 limits the tank to liquid dairy and swine."""
    if animal not in TANK_ANIMALS:
        return False
    if not systems:
        return False
    return all(str(system) in LIQUID_SYSTEMS for system in systems)


def _tank_cover_reduction(cover_type: str, params: Mapping[str, Any]) -> float:
    """Eq 4.1.3-9 reduction, applied by the tank itself (not the annual CE-14 fork)."""
    key = _COVER_REDUCTION_PARAM.get(cover_type)
    if key is None:
        return 0.0
    return float(params[key])


errors = validate_module(HolosManureCH4())
if errors:
    raise ValueError(f"HolosManureCH4 module validation failed: {errors}")
