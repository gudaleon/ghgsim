"""
IPCC 2006 Guidelines manure management emissions.

CH4 emissions (Equation 10.23):
CH4 = VS × 365 × B0 × 0.67 × Σ(MCFi × MSi)

N2O emissions:
- Direct (Equation 10.25): N × EF3
- Indirect via volatilization (Equations 10.26-10.27): N × FracGasMS × EF4
- Indirect via leaching (Equations 10.28-10.29): N × FracLeachMS × EF5

Note: IPCC 2006 does not provide default FracLeachMS values (country-specific),
so leaching is typically omitted unless regional data available.

Pasture/range/paddock (PRP) manure goes to Ch11 EF3PRP, not manure management.

Source: 2006 IPCC Guidelines for National Greenhouse Gas Inventories,
        Volume 4, Chapter 10.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec
from ghgsim.modules.livestock_types import is_poultry, is_swine

# Molecular weight conversion: N2O-N to N2O
N2ON_TO_N2O = 44.0 / 28.0

# Manure management system mappings for IPCC 2006
# Each system maps to (MCF_key, EF3_key, FracGasMS_key)
SYSTEM_MAP_2006 = {
    "liquid_nocrust": ("liquid_nocrust", "liquid_nocrust", "liquid_slurry"),
    "liquid_crust": ("liquid_crust", "liquid_crust", "liquid_slurry"),
    "lagoon": ("lagoon", "lagoon", "lagoon"),
    "solid_storage": ("solid_storage", "solid_storage", "solid_storage"),
    "dry_lot": ("dry_lot", "dry_lot", "dry_lot"),
    "daily_spread": ("daily_spread", "daily_spread", "daily_spread"),
    "pasture": ("pasture", None, None),  # PRP goes to Ch11
    "poultry_with_litter": ("poultry_with_litter", "poultry_with_litter", "poultry_with_litter"),
    "poultry_without_litter": ("poultry_without_litter", "poultry_without_litter", "poultry_without_litter"),
    "pit": ("pit_gt1mo", "pit", "pit"),
}


def _fracgas_ms(params: Mapping[str, Any], animal: str, fracgas_key: str) -> float:
    candidates = [f"FracGasMS_{animal}_{fracgas_key}"]
    if is_swine(animal):
        candidates.append(f"FracGasMS_swine_{fracgas_key}")
    if is_poultry(animal):
        candidates.append(f"FracGasMS_poultry_{fracgas_key}")
    for name in candidates:
        if name in params:
            return float(params[name])
    raise KeyError(f"Missing FracGasMS for animal '{animal}' system '{fracgas_key}'")


class IPCC2006Manure:
    """
    IPCC 2006 manure management CH4 and N2O emissions.
    
    Handles multiple manure management systems with weighted fractions.
    Pasture/range/paddock nitrogen is returned separately for soil N2O calculations.
    """

    id = "ipcc2006.manure"
    version = "1.0.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec(
            "animal_type",
            "dimensionless",
            "Animal type (dairy/other_cattle/market_swine/breeding_swine/broilers/layers/turkeys)",
            "scalar",
            True,
        ),
        "region": VarSpec("region", "dimensionless", "Region (north_america)", "scalar", True),
        "VS_kg_day": VarSpec("VS_kg_day", "kg / day", "Volatile solids excretion per animal", "scalar", False),
        "Nex_kg_yr": VarSpec("Nex_kg_yr", "kg N / year", "Nitrogen excretion per animal", "scalar", False),
        "TAM_kg": VarSpec("TAM_kg", "kg", "Typical animal mass", "scalar", False),
        "mcf_zone": VarSpec("mcf_zone", "dimensionless", "MCF climate zone (15C/le10C)", "scalar", True),
        "systems": VarSpec("systems", "dimensionless", "Dict of system -> fraction", "scalar", True),
    }

    parameters = {
        # VS and N excretion rates (fallback if not provided)
        "VS_dairy": ParamRef("IPCC2006.VS.dairy|north_america", "VS excretion for dairy"),
        "VS_other_cattle": ParamRef("IPCC2006.VS.other_cattle|north_america", "VS excretion for other cattle"),
        "Nrate_dairy": ParamRef("IPCC2006.Nrate.dairy|north_america", "N excretion rate for dairy"),
        "Nrate_other_cattle": ParamRef("IPCC2006.Nrate.other_cattle|north_america", "N excretion rate for other cattle"),
        "TAM_dairy": ParamRef("IPCC2006.TAM.dairy|north_america", "Typical animal mass for dairy"),
        "TAM_other_cattle": ParamRef("IPCC2006.TAM.other_cattle|north_america", "Typical animal mass for other cattle"),
        # CH4 parameters
        "B0_dairy": ParamRef("IPCC2006.B0.dairy|north_america", "Maximum methane producing capacity for dairy"),
        "B0_other_cattle": ParamRef("IPCC2006.B0.other_cattle|north_america", "Maximum methane producing capacity for other cattle"),
        "VS_market_swine": ParamRef("IPCC2006.VS.market_swine|north_america", "VS market swine"),
        "VS_breeding_swine": ParamRef("IPCC2006.VS.breeding_swine|north_america", "VS breeding swine"),
        "VS_broilers": ParamRef("IPCC2006.VS.broilers|north_america", "VS broilers"),
        "VS_layers": ParamRef("IPCC2006.VS.layers|north_america", "VS layers"),
        "VS_turkeys": ParamRef("IPCC2006.VS.turkeys|north_america", "VS turkeys"),
        "Nrate_market_swine": ParamRef("IPCC2006.Nrate.market_swine|north_america", "Nrate market swine"),
        "Nrate_breeding_swine": ParamRef("IPCC2006.Nrate.breeding_swine|north_america", "Nrate breeding swine"),
        "Nrate_broilers": ParamRef("IPCC2006.Nrate.broilers|north_america", "Nrate broilers"),
        "Nrate_layers": ParamRef("IPCC2006.Nrate.layers|north_america", "Nrate layers"),
        "Nrate_turkeys": ParamRef("IPCC2006.Nrate.turkeys|north_america", "Nrate turkeys"),
        "TAM_market_swine": ParamRef("IPCC2006.TAM.market_swine|north_america", "TAM market swine"),
        "TAM_breeding_swine": ParamRef("IPCC2006.TAM.breeding_swine|north_america", "TAM breeding swine"),
        "TAM_broilers": ParamRef("IPCC2006.TAM.broilers|north_america", "TAM broilers"),
        "TAM_layers": ParamRef("IPCC2006.TAM.layers|north_america", "TAM layers"),
        "TAM_turkeys": ParamRef("IPCC2006.TAM.turkeys|north_america", "TAM turkeys"),
        "B0_market_swine": ParamRef("IPCC2006.B0.market_swine|north_america", "B0 market swine"),
        "B0_breeding_swine": ParamRef("IPCC2006.B0.breeding_swine|north_america", "B0 breeding swine"),
        "B0_broilers": ParamRef("IPCC2006.B0.broilers|north_america", "B0 broilers"),
        "B0_layers": ParamRef("IPCC2006.B0.layers|north_america", "B0 layers"),
        "B0_turkeys": ParamRef("IPCC2006.B0.turkeys|north_america", "B0 turkeys"),
        "CH4_M3_TO_KG": ParamRef("BOTH.CH4_M3_TO_KG.all", "Methane density conversion"),
        # MCF values for each system and zone
        "MCF_liquid_nocrust_15C": ParamRef("IPCC2006.MCF.liquid_nocrust|15C", "MCF for liquid without crust"),
        "MCF_liquid_crust_15C": ParamRef("IPCC2006.MCF.liquid_crust|15C", "MCF for liquid with crust"),
        "MCF_lagoon_15C": ParamRef("IPCC2006.MCF.lagoon|15C", "MCF for lagoon"),
        "MCF_solid_storage_15C": ParamRef("IPCC2006.MCF.solid_storage|15C", "MCF for solid storage"),
        "MCF_dry_lot_15C": ParamRef("IPCC2006.MCF.dry_lot|15C", "MCF for dry lot"),
        "MCF_daily_spread_15C": ParamRef("IPCC2006.MCF.daily_spread|15C", "MCF for daily spread"),
        "MCF_pasture_15C": ParamRef("IPCC2006.MCF.pasture|15C", "MCF for pasture (15C)"),
        "MCF_pasture_le10C": ParamRef("IPCC2006.MCF.pasture|le10C", "MCF for pasture (≤10C)"),
        "MCF_poultry_with_litter_15C": ParamRef("IPCC2006.MCF.poultry_with_litter|15C", "MCF poultry with litter 15C"),
        "MCF_poultry_with_litter_le10C": ParamRef("IPCC2006.MCF.poultry_with_litter|le10C", "MCF poultry with litter cool"),
        "MCF_poultry_without_litter_15C": ParamRef(
            "IPCC2006.MCF.poultry_without_litter|15C", "MCF poultry without litter 15C"
        ),
        "MCF_poultry_without_litter_le10C": ParamRef(
            "IPCC2006.MCF.poultry_without_litter|le10C", "MCF poultry without litter cool"
        ),
        "MCF_pit_gt1mo_15C": ParamRef("IPCC2006.MCF.pit_gt1mo|15C", "MCF pit >1 month 15C"),
        "MCF_pit_gt1mo_le10C": ParamRef("IPCC2006.MCF.pit_gt1mo|le10C", "MCF pit >1 month cool"),
        # N2O emission factors
        "EF3_liquid_nocrust": ParamRef("IPCC2006.EF3.liquid_nocrust", "Direct N2O EF for liquid no crust"),
        "EF3_liquid_crust": ParamRef("IPCC2006.EF3.liquid_crust", "Direct N2O EF for liquid with crust"),
        "EF3_lagoon": ParamRef("IPCC2006.EF3.lagoon", "Direct N2O EF for lagoon"),
        "EF3_solid_storage": ParamRef("IPCC2006.EF3.solid_storage", "Direct N2O EF for solid storage"),
        "EF3_dry_lot": ParamRef("IPCC2006.EF3.dry_lot", "Direct N2O EF for dry lot"),
        "EF3_daily_spread": ParamRef("IPCC2006.EF3.daily_spread", "Direct N2O EF for daily spread"),
        "EF3_poultry_with_litter": ParamRef("IPCC2006.EF3.poultry_with_litter", "EF3 poultry with litter"),
        "EF3_poultry_without_litter": ParamRef("IPCC2006.EF3.poultry_without_litter", "EF3 poultry without litter"),
        "EF3_pit": ParamRef("IPCC2006.EF3.pit", "EF3 pit storage"),
        "EF4": ParamRef("IPCC2006.EF4.all", "Indirect N2O EF for volatilization"),
        # Volatilization fractions
        "FracGasMS_dairy_liquid_slurry": ParamRef("IPCC2006.FracGasMS.dairy|liquid_slurry", "Volatilization fraction for dairy liquid"),
        "FracGasMS_dairy_solid_storage": ParamRef("IPCC2006.FracGasMS.dairy|solid_storage", "Volatilization fraction for dairy solid"),
        "FracGasMS_dairy_dry_lot": ParamRef("IPCC2006.FracGasMS.dairy|dry_lot", "Volatilization fraction for dairy dry lot"),
        "FracGasMS_dairy_daily_spread": ParamRef("IPCC2006.FracGasMS.dairy|daily_spread", "Volatilization fraction for dairy daily spread"),
        "FracGasMS_dairy_lagoon": ParamRef("IPCC2006.FracGasMS.dairy|lagoon", "Volatilization fraction for dairy lagoon"),
        "FracGasMS_other_cattle_liquid_slurry": ParamRef("IPCC2006.FracGasMS.other_cattle|liquid_slurry", "Volatilization fraction for other cattle liquid"),
        "FracGasMS_other_cattle_solid_storage": ParamRef("IPCC2006.FracGasMS.other_cattle|solid_storage", "Volatilization fraction for other cattle solid"),
        "FracGasMS_other_cattle_dry_lot": ParamRef("IPCC2006.FracGasMS.other_cattle|dry_lot", "Volatilization fraction for other cattle dry lot"),
        "FracGasMS_other_cattle_daily_spread": ParamRef("IPCC2006.FracGasMS.other_cattle|daily_spread", "Volatilization fraction for other cattle daily spread"),
        "FracGasMS_other_cattle_lagoon": ParamRef("IPCC2006.FracGasMS.other_cattle|lagoon", "Volatilization fraction for other cattle lagoon"),
        "FracGasMS_swine_liquid_slurry": ParamRef("IPCC2006.FracGasMS.swine|liquid_slurry", "FracGasMS swine liquid"),
        "FracGasMS_swine_pit": ParamRef("IPCC2006.FracGasMS.swine|pit", "FracGasMS swine pit"),
        "FracGasMS_swine_lagoon": ParamRef("IPCC2006.FracGasMS.swine|lagoon", "FracGasMS swine lagoon"),
        "FracGasMS_swine_solid_storage": ParamRef("IPCC2006.FracGasMS.swine|solid_storage", "FracGasMS swine solid"),
        "FracGasMS_poultry_poultry_with_litter": ParamRef(
            "IPCC2006.FracGasMS.poultry|poultry_with_litter", "FracGasMS poultry with litter"
        ),
        "FracGasMS_poultry_poultry_without_litter": ParamRef(
            "IPCC2006.FracGasMS.poultry|poultry_without_litter", "FracGasMS poultry without litter"
        ),
        "FracGasMS_poultry_lagoon": ParamRef("IPCC2006.FracGasMS.poultry|lagoon", "FracGasMS poultry lagoon"),
    }

    outputs = {
        "CH4": VarSpec("CH4", "kg CH4 / year", "Total CH4 emissions", "scalar", True),
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct N2O emissions", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilization", "scalar", True),
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
        "N_PRP_kg": VarSpec("N_PRP_kg", "kg N / year", "Nitrogen from pasture/range/paddock (to Ch11)", "scalar", True),
        "Nex_kg_head": VarSpec("Nex_kg_head", "kg N / year", "Nitrogen excretion per head", "scalar", True),
        "N_managed_kg": VarSpec("N_managed_kg", "kg N / year", "Managed manure N (non-PRP)", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="Tables 10.17, 10.21, 10A-4, 10A-5, 10A-6, 10A-7",
            equation="Eq 10.23, 10.25, 10.26, 10.27",
            page="10.52-10.60, 10.77-10.82",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute manure management emissions (IPCC 2006).
        
        Args:
            inputs: head, animal_type, region, VS_kg_day, Nex_kg_yr, TAM_kg, mcf_zone, systems
            params: VS, Nrate, TAM, B0, MCF, EF3, EF4, FracGasMS for each system
            
        Returns:
            CH4, N2O_direct, N2O_indirect_vol, N2O_total, N_PRP_kg, Nex_kg_head
        """
        head = inputs["head"]
        animal = inputs["animal_type"]
        systems = inputs["systems"]
        mcf_zone = inputs["mcf_zone"]

        # Get VS, Nex, TAM (use input or fallback to parameters)
        if inputs.get("VS_kg_day"):
            vs = inputs["VS_kg_day"]
        else:
            vs = params[f"VS_{animal}"]

        if inputs.get("TAM_kg"):
            tam = inputs["TAM_kg"]
        else:
            tam = params[f"TAM_{animal}"]

        if inputs.get("Nex_kg_yr"):
            nex = inputs["Nex_kg_yr"]
        else:
            nrate = params[f"Nrate_{animal}"]
            nex = nrate * tam / 1000.0 * 365.0

        b0 = params[f"B0_{animal}"]
        ch4_density = params["CH4_M3_TO_KG"]
        ef4 = params["EF4"]

        # Calculate CH4 from each system
        ch4_sum_mcf = 0.0  # Weighted sum of MCF values
        n_direct = 0.0
        n_vol = 0.0
        n_prp = 0.0  # Pasture nitrogen (goes to Ch11 EF3PRP)
        n_managed = 0.0

        for system, fraction in systems.items():
            mcf_key, ef3_key, fracgas_key = SYSTEM_MAP_2006[system]

            # MCF: Special handling for pasture (zone-dependent)
            if system == "pasture":
                zone_suffix = "le10C" if mcf_zone == "le10C" else "15C"
                mcf = params[f"MCF_pasture_{zone_suffix}"]
                # Pasture N goes to Ch11, not manure management
                n_prp += head * nex * fraction
            else:
                # All other systems use the specified zone (typically 15C for US)
                mcf = params[f"MCF_{mcf_key}_{mcf_zone}"]
                n_managed += head * nex * fraction
                
                # N2O direct emissions
                ef3 = params[f"EF3_{ef3_key}"]
                n_direct += head * nex * fraction * ef3

                # Volatilization
                fracgas = _fracgas_ms(params, animal, fracgas_key)
                n_vol += head * nex * fraction * fracgas

            ch4_sum_mcf += mcf * fraction

        # Equation 10.23: CH4 = VS × 365 × B0 × 0.67 × Σ(MCFi × MSi)
        ch4 = head * vs * 365.0 * b0 * ch4_density * ch4_sum_mcf

        # N2O from volatilization (indirect)
        n2o_vol_n = n_vol * ef4

        # IPCC 2006 note: FracLeachMS is not provided (country-specific), so leaching omitted
        # n_leach = 0.0  # No default leaching fraction

        # Convert N2O-N to N2O
        n2o_direct = n_direct * N2ON_TO_N2O
        n2o_vol = n2o_vol_n * N2ON_TO_N2O

        return {
            "CH4": ch4,
            "N2O_direct": n2o_direct,
            "N2O_indirect_vol": n2o_vol,
            "N2O_total": n2o_direct + n2o_vol,
            "N_PRP_kg": n_prp,
            "Nex_kg_head": nex,
            "N_managed_kg": n_managed,
        }


# Validate module on import
from ghgsim.core.module import validate_module

errors = validate_module(IPCC2006Manure())
if errors:
    raise ValueError(f"IPCC2006Manure module validation failed: {errors}")
