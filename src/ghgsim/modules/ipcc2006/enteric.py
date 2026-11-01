"""
IPCC 2006 Guidelines Tier 2 enteric methane emissions from cattle.

Equation 10.21: CH4 (kg/head/yr) = GE × Ym% / 100 × 365 / 55.65

Where:
- GE = Gross energy intake (MJ/head/day)
- Ym = Methane conversion factor (% of GE)
- 55.65 = Energy content of CH4 (MJ/kg)

Source: 2006 IPCC Guidelines for National Greenhouse Gas Inventories,
        Volume 4, Chapter 10.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec


class IPCC2006Enteric:
    """
    IPCC 2006 Tier 2 enteric CH4 emissions from cattle.
    
    Calculates methane emissions per head based on gross energy intake
    and methane conversion factor (Ym).
    """

    id = "ipcc2006.enteric"
    version = "1.0.0"

    inputs = {
        "GE_MJ_day": VarSpec("GE_MJ_day", "MJ / day", "Gross energy intake per animal", "scalar", True),
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "ym_category": VarSpec("ym_category", "dimensionless", "Ym category (dairy/feedlot/other_cattle)", "scalar", True),
    }

    parameters = {
        "Ym_dairy": ParamRef("IPCC2006.Ym.dairy", "Methane conversion factor for dairy cattle"),
        "Ym_feedlot": ParamRef("IPCC2006.Ym.feedlot", "Methane conversion factor for feedlot cattle"),
        "Ym_other_cattle": ParamRef("IPCC2006.Ym.other_cattle", "Methane conversion factor for other cattle"),
        "CH4_ENERGY": ParamRef("BOTH.CH4_ENERGY.all", "Energy content of methane (MJ/kg CH4)"),
    }

    outputs = {
        "CH4_kg_head": VarSpec("CH4_kg_head", "kg CH4 / year", "CH4 emission factor per head", "scalar", True),
        "CH4_total": VarSpec("CH4_total", "kg CH4 / year", "Total CH4 emissions", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="Table 10.12",
            equation="Eq 10.21",
            page="10.30, 10.31",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute enteric CH4 emissions (IPCC 2006 Tier 2).
        
        Args:
            inputs: Dictionary with GE_MJ_day, head, ym_category
            params: Dictionary with Ym_* for each category, CH4_ENERGY
            
        Returns:
            Dictionary with CH4_kg_head, CH4_total
        """
        ge = inputs["GE_MJ_day"]
        head = inputs["head"]
        category = inputs["ym_category"]

        # Select Ym parameter based on category
        if category == "dairy":
            ym = params["Ym_dairy"]
        elif category == "feedlot":
            ym = params["Ym_feedlot"]
        elif category == "other_cattle":
            ym = params["Ym_other_cattle"]
        else:
            raise ValueError(f"Unknown ym_category: {category}")

        ch4_energy = params["CH4_ENERGY"]

        # Equation 10.21: EF = GE × Ym/100 × 365 / CH4_ENERGY
        ef_kg_head = ge * ym / 100.0 * 365.0 / ch4_energy

        return {
            "CH4_kg_head": ef_kg_head,
            "CH4_total": ef_kg_head * head,
        }


# Validate module on import
from ghgsim.core.module import validate_module

errors = validate_module(IPCC2006Enteric())
if errors:
    raise ValueError(f"IPCC2006Enteric module validation failed: {errors}")
