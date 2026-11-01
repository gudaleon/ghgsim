"""
Holos Route A enteric CH4.

Default equations are IPCC 2006 Vol 4 Ch 10 (Eq 10.21 daily/annual, Eq 10.3 GE).
Confirmed Holos discrepancies are labelled holos_as_coded forks, not defaults.

Holos file:line citations are traceability only and are not copied source.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import forks_from_inputs, option_is
from ghgsim.modules.holos.forks import resolve_option
from ghgsim.modules.holos.process_defs import (
    enteric_ch4_process,
    ge_intake_variable,
    ge_intake_variable_holos_tdn,
    poultry_enteric_process,
    swine_enteric_tier1_process,
)
from ghgsim.modules.livestock_types import is_poultry, is_swine

_ENTERIC = enteric_ch4_process()
_SWINE_ENTERIC = swine_enteric_tier1_process()
_POULTRY_ENTERIC = poultry_enteric_process()
_GE_IPCC = ge_intake_variable()
_GE_HOLOS = ge_intake_variable_holos_tdn()


def _compute_ge(inputs: Mapping[str, Any], params: Mapping[str, Any], fork_settings: dict[str, str]) -> float:
    """Return GE (MJ/day) from override, Eq 10.3, or animal-type fallback."""
    if inputs.get("GE_MJ_day") not in (None, ""):
        return float(inputs["GE_MJ_day"])

    has_ne = all(k in inputs for k in ("NE_m", "RE_m", "DE_percent"))
    if has_ne:
        context = {
            "NE_m": float(inputs["NE_m"]),
            "NE_a": float(inputs.get("NE_a", 0.0)),
            "NE_l": float(inputs.get("NE_l", 0.0)),
            "NE_work": float(inputs.get("NE_work", 0.0)),
            "NE_p": float(inputs.get("NE_p", 0.0)),
            "NE_g": float(inputs.get("NE_g", 0.0)),
            "RE_m": float(inputs["RE_m"]),
            "RE_g": float(inputs.get("RE_g", 0.0)),
            "DE_percent": float(inputs["DE_percent"]),
            "TDN_percent": float(inputs.get("TDN_percent", inputs["DE_percent"])),
        }
        if option_is("HOLOS.GE.digestibility", "holos_as_coded", fork_settings):
            return _GE_HOLOS.compute(context)
        return _GE_IPCC.compute(context)

    animal_type = inputs["animal_type"]
    if animal_type == "dairy":
        return float(params["GE_dairy_canada"])
    diet = inputs.get("diet_type", "medium")
    return float(params.get(f"GE_beef_{diet}", params["GE_beef_medium"]))


def _select_ym(inputs: Mapping[str, Any], params: Mapping[str, Any], fork_settings: dict[str, str]) -> float:
    """Select Ym (% of GE). Dairy Ym fork is a parameter refinement, not a Holos bug."""
    animal_type = inputs["animal_type"]
    if animal_type == "dairy":
        ym_option = resolve_option("HOLOS.YM.dairy", fork_settings)
        if ym_option == "ipcc2006_table_10_12":
            return float(params["Ym_dairy_ipcc2006"])
        return float(params["Ym_dairy_canada"])
    diet = inputs.get("diet_type", "medium")
    return float(params.get(f"Ym_beef_{diet}", params["Ym_beef_medium"]))


class HolosEnteric:
    """
    Enteric CH4 with IPCC-correct defaults and Holos-as-coded forks.

    CH4 (kg/head/year) = GE * (Ym/100) * 365 / 55.65
    IPCC 2006 Vol 4 Ch 10 Equation 10.21, p. 10.30.
    """

    id = "holos.enteric"
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
        "animal_class": VarSpec("animal_class", "dimensionless", "adult or calf (CE-06 fork)", "scalar", False),
        "diet_type": VarSpec("diet_type", "dimensionless", "Diet category (high_grain/medium/low)", "scalar", False),
        "GE_MJ_day": VarSpec("GE_MJ_day", "MJ / day", "Gross energy intake override", "scalar", False),
        "NE_m": VarSpec("NE_m", "MJ / day", "Net energy for maintenance", "scalar", False),
        "NE_a": VarSpec("NE_a", "MJ / day", "Net energy for activity", "scalar", False),
        "NE_l": VarSpec("NE_l", "MJ / day", "Net energy for lactation", "scalar", False),
        "NE_work": VarSpec("NE_work", "MJ / day", "Net energy for work", "scalar", False),
        "NE_p": VarSpec("NE_p", "MJ / day", "Net energy for pregnancy", "scalar", False),
        "NE_g": VarSpec("NE_g", "MJ / day", "Net energy for gain", "scalar", False),
        "RE_m": VarSpec("RE_m", "dimensionless", "NE available for maintenance / DE", "scalar", False),
        "RE_g": VarSpec("RE_g", "dimensionless", "NE available for gain / DE", "scalar", False),
        "DE_percent": VarSpec("DE_percent", "% GE", "Digestible energy as percent of GE", "scalar", False),
        "TDN_percent": VarSpec("TDN_percent", "%", "Total digestible nutrients (holos_as_coded GE fork)", "scalar", False),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
    }

    parameters = {
        "GE_dairy_canada": ParamRef("HOLOS.GE.dairy|canada", "Fallback GE for Canadian dairy (MJ/day)"),
        "Ym_dairy_canada": ParamRef("HOLOS.Ym.dairy_lactating|canada", "Ym for Canadian lactating dairy (% GE)"),
        "Ym_dairy_ipcc2006": ParamRef("IPCC2006.Ym.dairy", "Ym dairy IPCC 2006 Table 10.12 (% GE)"),
        "GE_beef_high_grain": ParamRef("HOLOS.GE.beef|high_grain", "Fallback GE for beef on high grain diet"),
        "GE_beef_medium": ParamRef("HOLOS.GE.beef|medium", "Fallback GE for beef on medium diet"),
        "GE_beef_low_grain": ParamRef("HOLOS.GE.beef|low_grain", "Fallback GE for beef on low grain diet"),
        "Ym_beef_high_grain": ParamRef("HOLOS.Ym.beef_finisher_corn|canada", "Ym for beef high grain (% GE)"),
        "Ym_beef_medium": ParamRef("HOLOS.Ym.beef_backgrounder|canada", "Ym for beef medium (% GE)"),
        "Ym_beef_low_grain": ParamRef("HOLOS.Ym.beef_cowcalf_low|canada", "Ym for beef low grain (% GE)"),
        "CH4_ENERGY": ParamRef("BOTH.CH4_ENERGY.all", "CH4 energy content (MJ/kg)"),
        "EF_enteric_swine": ParamRef(
            "IPCC2006.EF_enteric.swine|developed",
            "Swine enteric Tier 1 EF (developed / high-productivity), kg CH4/head/yr",
        ),
        "EF_enteric_poultry": ParamRef(
            "IPCC2006.EF_enteric.poultry",
            "Poultry enteric EF (0; IPCC Table 10.10 insufficient data)",
        ),
    }

    outputs = {
        "CH4_total": VarSpec("CH4_total", "kg CH4 / year", "Total enteric CH4 emissions", "scalar", True),
        "CH4_kg_head": VarSpec("CH4_kg_head", "kg CH4 / year", "Enteric CH4 per head", "scalar", True),
        "GE_used": VarSpec("GE_used", "MJ / day", "Gross energy used in calculation", "scalar", True),
        "Ym_used": VarSpec("Ym_used", "% GE", "Methane conversion factor used", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="Table 10.12",
            equation="Equation 10.21",
            page="10.30",
        ),
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="",
            equation="Equation 10.3",
            page="10.16",
            notes="GE from net energy and DE%",
        ),
        Citation(
            source="Little et al. (2008). Holos v1.1.x Methodology. Agriculture and Agri-Food Canada",
            table="Enteric fermentation section",
            equation="IPCC 2006 Eq 10.21 with Canadian parameters",
            page="",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute enteric CH4.

        Default: IPCC 2006 Eq 10.21. Optional Eq 10.3 GE when NE and DE are supplied.
        Forks (see data/holos_forks_AN_v3.json): HOLOS.GE.digestibility,
        HOLOS.ENTERIC.calf_zero, HOLOS.YM.dairy.
        """
        fork_settings = forks_from_inputs(inputs)
        head = float(inputs["head"])
        animal_type = str(inputs["animal_type"])
        if is_poultry(animal_type):
            ch4_kg_day = _POULTRY_ENTERIC.compute_rate({})
            return {
                "CH4_total": head * ch4_kg_day * 365.0,
                "CH4_kg_head": float(params.get("EF_enteric_poultry", 0.0)),
                "GE_used": 0.0,
                "Ym_used": 0.0,
            }
        if is_swine(animal_type):
            ef = float(params["EF_enteric_swine"])
            ch4_kg_day = _SWINE_ENTERIC.compute_rate({"EF_enteric_kg_head_yr": ef})
            return {
                "CH4_total": head * ch4_kg_day * 365.0,
                "CH4_kg_head": ef,
                "GE_used": 0.0,
                "Ym_used": 0.0,
            }
        animal_class = str(inputs.get("animal_class", "adult"))
        ge_mj_day = _compute_ge(inputs, params, fork_settings)
        ym_pct = _select_ym(inputs, params, fork_settings)
        ch4_energy = float(params["CH4_ENERGY"])

        rate_vars = {
            "GE": ge_mj_day,
            "Ym_percent": ym_pct,
            "CH4_ENERGY": ch4_energy,
            "animal_class": animal_class,
        }
        calf_option = resolve_option("HOLOS.ENTERIC.calf_zero", fork_settings)
        process_fork = "holos_as_coded" if calf_option == "holos_as_coded" else None
        ch4_kg_day = _ENTERIC.compute_rate(rate_vars, fork=process_fork)
        ch4_kg_head = ch4_kg_day * 365.0

        return {
            "CH4_total": head * ch4_kg_head,
            "CH4_kg_head": ch4_kg_head,
            "GE_used": ge_mj_day,
            "Ym_used": ym_pct,
        }


errors = validate_module(HolosEnteric())
if errors:
    raise ValueError(f"HolosEnteric module validation failed: {errors}")
