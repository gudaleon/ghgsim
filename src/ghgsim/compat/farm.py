"""
Farm model wrapper for v3 compatibility.

Composes soil N2O, enteric CH4, and manure emissions modules
to reproduce v3 farm-level GHG calculations.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.registry import ParameterRegistry
from ghgsim.modules.ipcc2006 import IPCC2006Enteric, IPCC2006Manure, IPCC2006SoilN2O
from ghgsim.modules.ipcc2019 import IPCC2019Enteric, IPCC2019SoilN2O


class FarmModel:
    """
    Composite farm model: soil + herds (enteric + manure).
    
    Reproduces v3 run_farm() behavior through new Module architecture.
    """

    def __init__(self, guideline: str = "IPCC2006", gwp: dict[str, float] | None = None):
        """
        Initialize farm model.
        
        Args:
            guideline: "IPCC2006" or "IPCC2019"
            gwp: GWP100 values (default: CH4=28, N2O=265 from AR5)
        """
        self.guideline = guideline
        self.gwp = gwp or {"CH4": 28.0, "N2O": 265.0}
        
        # Select modules based on guideline
        if guideline == "IPCC2006":
            self.soil_module = IPCC2006SoilN2O()
            self.enteric_module = IPCC2006Enteric()
            self.manure_module = IPCC2006Manure()
        elif guideline == "IPCC2019":
            self.soil_module = IPCC2019SoilN2O()
            self.enteric_module = IPCC2019Enteric()
            # IPCC2019 uses same manure module as 2006 for now
            self.manure_module = IPCC2006Manure()
        else:
            raise ValueError(f"Unknown guideline: {guideline}")

    def run_farm(
        self,
        farm: dict[str, Any],
        param_registry: ParameterRegistry,
    ) -> dict[str, float]:
        """
        Run farm-level GHG calculations.
        
        Args:
            farm: Farm specification with soil and herds
            param_registry: Parameter registry
            
        Returns:
            Dict with N2O_kg, CH4_kg, CH4_manure_kg, N2O_manure_kg, CO2e_t
        """
        # Extract farm components
        soil = farm.get("soil", {})
        herds = farm.get("herds", [])
        
        # Initialize totals
        ch4_total = 0.0
        ch4_manure = 0.0
        n2o_manure_total = 0.0
        n_prp_total = 0.0  # Pasture N to add to soil
        
        # Process each herd
        for herd in herds:
            # Enteric CH4
            enteric_inputs = {
                "GE_MJ_day": herd["GE_MJ_day"],
                "head": herd["head"],
                "ym_category": herd["ym_category"],
            }
            
            enteric_params = self._get_enteric_params(herd, param_registry)
            enteric_result = self.enteric_module.compute(enteric_inputs, enteric_params)
            ch4_total += enteric_result["CH4_total"]
            
            # Manure emissions (if manure system specified)
            if "manure" in herd:
                manure_inputs = {
                    "head": herd["head"],
                    "animal_type": herd["manure"]["animal"],
                    "region": herd["manure"]["region"],
                    "mcf_zone": herd["manure"]["mcf_zone"][self.guideline],
                    "systems": herd["manure"]["systems"],
                }
                
                manure_params = self._get_manure_params(herd, param_registry)
                manure_result = self.manure_module.compute(manure_inputs, manure_params)
                
                ch4_manure += manure_result["CH4"]
                n2o_manure_total += manure_result["N2O_total"]
                n_prp_total += manure_result["N_PRP_kg"]
        
        ch4_total += ch4_manure
        
        # Soil N2O (add PRP N from manure)
        soil_inputs = {
            "F_SN": soil.get("F_SN", 0.0),
            "F_ON": soil.get("F_ON", 0.0),
            "F_CR": soil.get("F_CR", 0.0),
            "F_SOM": soil.get("F_SOM", 0.0),
            "F_PRP_CPP": soil.get("F_PRP_CPP", 0.0) + n_prp_total,
            "climate": soil.get("climate", "wet"),
        }
        
        soil_params = self._get_soil_params(param_registry)
        soil_result = self.soil_module.compute(soil_inputs, soil_params)
        
        n2o_total = soil_result["N2O_total"] + n2o_manure_total
        
        # Convert to CO2e
        co2e_t = (n2o_total * self.gwp["N2O"] + ch4_total * self.gwp["CH4"]) / 1000.0
        
        return {
            "N2O_kg": n2o_total,
            "CH4_kg": ch4_total,
            "CH4_manure_kg": ch4_manure,
            "N2O_manure_kg": n2o_manure_total,
            "CO2e_t": co2e_t,
        }

    def _get_soil_params(self, registry: ParameterRegistry) -> dict[str, float]:
        """Get soil N2O parameters from registry."""
        if self.guideline == "IPCC2006":
            return {
                "EF1": registry.get_value(f"{self.guideline}.EF1.all"),
                "EF3PRP_CPP": registry.get_value(f"{self.guideline}.EF3PRP_CPP.all"),
                "EF4": registry.get_value(f"{self.guideline}.EF4.all"),
                "EF5": registry.get_value(f"{self.guideline}.EF5.all"),
                "FracGASF": registry.get_value(f"{self.guideline}.FracGASF.all"),
                "FracGASM": registry.get_value(f"{self.guideline}.FracGASM.all"),
                "FracLEACH_wet": registry.get_value(f"{self.guideline}.FracLEACH.wet"),
            }
        else:  # IPCC2019
            return {
                "EF1_wet_synthetic": registry.get_value(f"{self.guideline}.EF1.wet_synthetic"),
                "EF1_wet_other": registry.get_value(f"{self.guideline}.EF1.wet_other"),
                "EF1_dry": registry.get_value(f"{self.guideline}.EF1.dry"),
                "EF3PRP_CPP_wet": registry.get_value(f"{self.guideline}.EF3PRP_CPP.wet"),
                "EF3PRP_CPP_dry": registry.get_value(f"{self.guideline}.EF3PRP_CPP.dry"),
                "EF4_wet": registry.get_value(f"{self.guideline}.EF4.wet"),
                "EF4_dry": registry.get_value(f"{self.guideline}.EF4.dry"),
                "EF5": registry.get_value(f"{self.guideline}.EF5.all"),
                "FracGASF": registry.get_value(f"{self.guideline}.FracGASF.all"),
                "FracGASM": registry.get_value(f"{self.guideline}.FracGASM.all"),
                "FracLEACH_wet": registry.get_value(f"{self.guideline}.FracLEACH.wet"),
                "FracLEACH_dry": registry.get_value(f"{self.guideline}.FracLEACH.dry"),
            }

    def _get_enteric_params(self, herd: dict, registry: ParameterRegistry) -> dict[str, float]:
        """Get enteric CH4 parameters from registry."""
        params = {"CH4_ENERGY": registry.get_value("BOTH.CH4_ENERGY.all")}
        
        if self.guideline == "IPCC2006":
            for cat in ["dairy", "feedlot", "other_cattle"]:
                params[f"Ym_{cat}"] = registry.get_value(f"{self.guideline}.Ym.{cat}")
        else:  # IPCC2019
            cats = [
                "dairy_high_ndf_le35", "dairy_high_ndf_ge35", "dairy_medium", "dairy_low",
                "nondairy_forage_gt75", "nondairy_mixed", "feedlot_grain", "feedlot_sfc"
            ]
            for cat in cats:
                params[f"Ym_{cat}"] = registry.get_value(f"{self.guideline}.Ym.{cat}")
        
        return params

    def _get_manure_params(self, herd: dict, registry: ParameterRegistry) -> dict[str, float]:
        """Get manure management parameters from registry."""
        animal = herd["manure"]["animal"]
        region = herd["manure"]["region"]
        zone = herd["manure"]["mcf_zone"][self.guideline]
        
        params = {
            "CH4_M3_TO_KG": registry.get_value("BOTH.CH4_M3_TO_KG.all"),
            "EF4": registry.get_value(f"{self.guideline}.EF4.all"),
        }
        
        # Animal characteristics
        # Note: VS, TAM, B0 use 2006 values for both guidelines (no updates in 2019)
        # Only Nrate was updated in 2019
        for a in ["dairy", "other_cattle"]:
            params[f"VS_{a}"] = registry.get_value(f"IPCC2006.VS.{a}|{region}")
            params[f"TAM_{a}"] = registry.get_value(f"IPCC2006.TAM.{a}|{region}")
            params[f"B0_{a}"] = registry.get_value(f"IPCC2006.B0.{a}|{region}")
            # Nrate was updated in 2019
            params[f"Nrate_{a}"] = registry.get_value(f"{self.guideline}.Nrate.{a}|{region}")
        
        # MCF values for all systems (use 2006 values for both guidelines - no updates in 2019)
        for system in ["liquid_nocrust", "liquid_crust", "lagoon", "solid_storage", "dry_lot", "daily_spread"]:
            params[f"MCF_{system}_{zone}"] = registry.get_value(f"IPCC2006.MCF.{system}|{zone}")
        
        # Pasture MCF (both zones)
        params[f"MCF_pasture_{zone}"] = registry.get_value(f"IPCC2006.MCF.pasture|{zone}")
        params["MCF_pasture_le10C"] = registry.get_value(f"IPCC2006.MCF.pasture|le10C")
        
        # EF3 values (use 2006 values for both guidelines - no updates in 2019)
        for system in ["liquid_nocrust", "liquid_crust", "lagoon", "solid_storage", "dry_lot", "daily_spread"]:
            params[f"EF3_{system}"] = registry.get_value(f"IPCC2006.EF3.{system}")
        
        # FracGasMS values (use 2006 values for both guidelines - no updates in 2019)
        for a in ["dairy", "other_cattle"]:
            for system in ["liquid_slurry", "solid_storage", "dry_lot", "daily_spread", "lagoon"]:
                try:
                    params[f"FracGasMS_{a}_{system}"] = registry.get_value(f"IPCC2006.FracGasMS.{a}|{system}")
                except ValueError:
                    # If not available, use dairy value as fallback
                    if a == "other_cattle":
                        params[f"FracGasMS_{a}_{system}"] = registry.get_value(f"IPCC2006.FracGasMS.dairy|{system}")
        
        return params
