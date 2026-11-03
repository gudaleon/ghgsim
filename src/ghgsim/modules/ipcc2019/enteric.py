"""
IPCC 2019 Refinement Tier 2 enteric methane with diet-specific Ym values.

Updates from 2006:
- Dairy cattle: Disaggregated by NDF (neutral detergent fiber) levels
- Non-dairy cattle: Disaggregated by forage content
- Feedlot: Disaggregated by grain vs silage/concentrate

Equation 10.21 remains the same: CH4 = GE × Ym% / 100 × 365 / 55.65

Source: 2019 Refinement to the 2006 IPCC Guidelines,
        Volume 4, Chapter 10 (Updated).
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec
from ghgsim.modules.livestock_types import is_poultry, is_swine


class IPCC2019Enteric:
    """
    IPCC 2019 Refinement Tier 2 enteric CH4 with updated Ym categories.
    
    Provides more detailed Ym values based on diet composition.
    """

    id = "ipcc2019.enteric"
    version = "1.0.0"

    inputs = {
        "GE_MJ_day": VarSpec("GE_MJ_day", "MJ / day", "Gross energy intake per animal (cattle Tier 2)", "scalar", False),
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec("animal_type", "dimensionless", "Alias of ym_category for monogastrics", "scalar", False),
        "ym_category": VarSpec(
            "ym_category",
            "dimensionless",
            "Ym category (cattle diet keys) or swine/poultry animal_type",
            "scalar",
            True,
        ),
    }

    parameters = {
        "Ym_dairy_high_ndf_le35": ParamRef(
            "IPCC2019.Ym.dairy_high_ndf_le35", "Ym for dairy high NDF diet <35% milk fat"
        ),
        "Ym_dairy_high_ndf_ge35": ParamRef(
            "IPCC2019.Ym.dairy_high_ndf_ge35", "Ym for dairy high NDF diet ≥35% milk fat"
        ),
        "Ym_dairy_medium": ParamRef("IPCC2019.Ym.dairy_medium", "Ym for dairy medium forage diet"),
        "Ym_dairy_low": ParamRef("IPCC2019.Ym.dairy_low", "Ym for dairy low forage diet"),
        "Ym_nondairy_forage_gt75": ParamRef(
            "IPCC2019.Ym.nondairy_forage_gt75", "Ym for non-dairy >75% forage diet"
        ),
        "Ym_nondairy_mixed": ParamRef("IPCC2019.Ym.nondairy_mixed", "Ym for non-dairy mixed diet"),
        "Ym_feedlot_grain": ParamRef("IPCC2019.Ym.feedlot_grain", "Ym for feedlot grain-based diet"),
        "Ym_feedlot_sfc": ParamRef("IPCC2019.Ym.feedlot_sfc", "Ym for feedlot silage/concentrate diet"),
        "CH4_ENERGY": ParamRef("BOTH.CH4_ENERGY.all", "Energy content of methane (MJ/kg CH4)"),
        "EF_enteric_swine": ParamRef(
            "IPCC2019.EF_enteric.swine|high_productivity",
            "Swine Tier 1 EF high-productivity systems",
        ),
        "EF_enteric_poultry": ParamRef("IPCC2019.EF_enteric.poultry", "Poultry enteric EF (0)"),
    }

    outputs = {
        "CH4_kg_head": VarSpec("CH4_kg_head", "kg CH4 / year", "CH4 emission factor per head", "scalar", True),
        "CH4_total": VarSpec("CH4_total", "kg CH4 / year", "Total CH4 emissions", "scalar", True),
    }

    sources = [
        Citation(
            source="2019 Refinement to the 2006 IPCC Guidelines, Volume 4, Chapter 10",
            table="Table 10.12 (Updated)",
            equation="Eq 10.21",
            page="10.46, 10.47",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute enteric CH4 emissions (IPCC 2019 Tier 2).
        
        Args:
            inputs: Dictionary with GE_MJ_day, head, ym_category
            params: Dictionary with Ym_* for each diet category, CH4_ENERGY
            
        Returns:
            Dictionary with CH4_kg_head, CH4_total
        """
        head = inputs["head"]
        category = str(inputs.get("ym_category") or inputs.get("animal_type") or "")
        if is_poultry(category):
            ef = float(params.get("EF_enteric_poultry", 0.0))
            return {"CH4_kg_head": ef, "CH4_total": ef * head}
        if is_swine(category):
            ef = float(params["EF_enteric_swine"])
            return {"CH4_kg_head": ef, "CH4_total": ef * head}

        ge = inputs["GE_MJ_day"]

        # Select Ym parameter based on diet category
        ym_key = f"Ym_{category}"
        if ym_key not in params:
            raise ValueError(f"Unknown ym_category: {category}")

        ym = params[ym_key]
        ch4_energy = params["CH4_ENERGY"]

        # Equation 10.21: EF = GE × Ym/100 × 365 / CH4_ENERGY
        ef_kg_head = ge * ym / 100.0 * 365.0 / ch4_energy

        return {
            "CH4_kg_head": ef_kg_head,
            "CH4_total": ef_kg_head * head,
        }


# Validate module on import
from ghgsim.core.module import validate_module

errors = validate_module(IPCC2019Enteric())
if errors:
    raise ValueError(f"IPCC2019Enteric module validation failed: {errors}")
