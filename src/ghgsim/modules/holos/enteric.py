"""
Holos (Canada) enteric CH4 emissions model.

Re-implemented from published AAFC Holos technical documentation and 
peer-reviewed sources. Implementation is independent, based solely on 
published equations and parameters.

Sources:
- Little, S., Lindwall, W., Hooton, N., et al. (2008). Holos - A Tool to 
  Estimate and Reduce GHG Emissions from Farms: Methodology and Algorithms 
  for Version 1.1.x. Agriculture and Agri-Food Canada.
  
- Holos Technical Reference (public): 
  https://agriculture.canada.ca/en/agricultural-production/holos-software-program
  
- Benchaar et al. (2001). Methane production from beef cattle fed corn silage or 
  barley silage based diets. Can J Anim Sci. 81: 199-210.
  DOI: 10.4141/A00-079

The core approach uses IPCC Tier 2 (Equation 10.21) with region-specific 
parameters for Canadian conditions.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec


class HolosEnteric:
    """
    Holos enteric CH4 emissions (beef and dairy cattle).
    
    Uses IPCC 2006 Tier 2 methodology (Equation 10.21) with Canadian-specific
    parameters for GE and Ym based on Canadian feeding systems.
    
    Methodology documented in:
    Little et al. (2008) Holos v1.1.x Methodology
    """

    id = "holos.enteric"
    version = "1.0.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec("animal_type", "dimensionless", "Animal type (dairy/beef)", "scalar", True),
        "diet_type": VarSpec("diet_type", "dimensionless", "Diet category (high_grain/medium/low)", "scalar", False),
        "GE_MJ_day": VarSpec("GE_MJ_day", "MJ / day", "Gross energy intake (optional override)", "scalar", False),
    }

    parameters = {
        # Canadian dairy defaults (from Holos technical documentation)
        "GE_dairy_canada": ParamRef("HOLOS.GE.dairy|canada", "GE for Canadian dairy (MJ/day)"),
        "Ym_dairy_canada": ParamRef("HOLOS.Ym.dairy|canada", "Ym for Canadian dairy (% GE)"),
        
        # Canadian beef defaults by diet
        "GE_beef_high_grain": ParamRef("HOLOS.GE.beef|high_grain", "GE for beef on high grain diet"),
        "GE_beef_medium": ParamRef("HOLOS.GE.beef|medium", "GE for beef on medium diet"),
        "GE_beef_low_grain": ParamRef("HOLOS.GE.beef|low_grain", "GE for beef on low grain diet"),
        
        "Ym_beef_high_grain": ParamRef("HOLOS.Ym.beef|high_grain", "Ym for beef on high grain (% GE)"),
        "Ym_beef_medium": ParamRef("HOLOS.Ym.beef|medium", "Ym for beef on medium (% GE)"),
        "Ym_beef_low_grain": ParamRef("HOLOS.Ym.beef|low_grain", "Ym for beef on low grain (% GE)"),
        
        # Universal constant
        "CH4_ENERGY": ParamRef("BOTH.CH4_ENERGY.all", "CH4 energy content (MJ/kg)"),
    }

    outputs = {
        "CH4_total": VarSpec("CH4_total", "kg CH4 / year", "Total enteric CH4 emissions", "scalar", True),
        "GE_used": VarSpec("GE_used", "MJ / day", "Gross energy used in calculation", "scalar", True),
        "Ym_used": VarSpec("Ym_used", "% GE", "Methane conversion factor used", "scalar", True),
    }

    sources = [
        Citation(
            source="Little et al. (2008). Holos v1.1.x Methodology. Agriculture and Agri-Food Canada",
            table="Section on Enteric Fermentation",
            equation="Based on IPCC 2006 Eq 10.21 with Canadian parameters",
            page="",
        ),
        Citation(
            source="IPCC 2006 Guidelines Volume 4 Chapter 10",
            table="",
            equation="Equation 10.21",
            page="10.30",
        ),
        Citation(
            source="Benchaar et al. (2001). Can J Anim Sci. DOI: 10.4141/A00-079",
            table="",
            equation="",
            page="",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute enteric CH4 emissions using IPCC Tier 2 with Canadian parameters.
        
        CH4 (kg/yr) = (GE × Ym / 100 × 365) / (55.65 MJ/kg CH4)
        
        Args:
            inputs: head, animal_type, diet_type (optional), GE_MJ_day (optional)
            params: GE and Ym parameters by animal type and diet
            
        Returns:
            CH4_total, GE_used, Ym_used
        """
        head = inputs["head"]
        animal_type = inputs["animal_type"]
        
        # Determine GE and Ym
        if inputs.get("GE_MJ_day"):
            # User-provided GE override
            ge_mj_day = inputs["GE_MJ_day"]
            if animal_type == "dairy":
                ym_pct = params["Ym_dairy_canada"]
            else:
                # Default to medium for beef if not specified
                diet = inputs.get("diet_type", "medium")
                ym_pct = params.get(f"Ym_beef_{diet}", params["Ym_beef_medium"])
        else:
            # Use Canadian defaults
            if animal_type == "dairy":
                ge_mj_day = params["GE_dairy_canada"]
                ym_pct = params["Ym_dairy_canada"]
            else:  # beef
                diet = inputs.get("diet_type", "medium")
                ge_mj_day = params.get(f"GE_beef_{diet}", params["GE_beef_medium"])
                ym_pct = params.get(f"Ym_beef_{diet}", params["Ym_beef_medium"])
        
        ch4_energy = params["CH4_ENERGY"]
        
        # IPCC 2006 Equation 10.21
        ch4_kg_yr = (ge_mj_day * (ym_pct / 100.0) * 365.0) / ch4_energy
        ch4_total = head * ch4_kg_yr
        
        return {
            "CH4_total": ch4_total,
            "GE_used": ge_mj_day,
            "Ym_used": ym_pct,
        }


# Validate module on import
from ghgsim.core.module import validate_module

errors = validate_module(HolosEnteric())
if errors:
    raise ValueError(f"HolosEnteric module validation failed: {errors}")
