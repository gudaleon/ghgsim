"""
Holos Route A manure management facade (CH4 + N2O).

Delegates to HolosManureCH4 and HolosManureN2O so existing graphs that use
holos.manure keep working. Defaults are IPCC 2006; holos_as_coded forks are
on the child modules.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, VarSpec, validate_module
from ghgsim.modules.holos.manure_ch4 import HolosManureCH4
from ghgsim.modules.holos.manure_n2o import HolosManureN2O

_CH4 = HolosManureCH4()
_N2O = HolosManureN2O()


class HolosManure:
    """
    Combined manure CH4 and N2O.

    CH4: IPCC 2006 Eq 10.23
    N2O direct: Eq 10.25; indirect volatilisation: Eq 10.26-10.27
    """

    id = "holos.manure"
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
        "region": VarSpec("region", "dimensionless", "Region (canada/north_america)", "scalar", False),
        "climate_zone": VarSpec("climate_zone", "dimensionless", "Climate zone (cool/temperate)", "scalar", True),
        "systems": VarSpec("systems", "dimensionless", "Dict of system -> fraction", "scalar", True),
        "VS_kg_day": VarSpec("VS_kg_day", "kg / day", "Volatile solids override", "scalar", False),
        "Nex_kg_yr": VarSpec("Nex_kg_yr", "kg N / year", "Nitrogen excretion override", "scalar", False),
        "animal_class": VarSpec("animal_class", "dimensionless", "adult or calf", "scalar", False),
        "cover_type": VarSpec(
            "cover_type",
            "dimensionless",
            "none, natural_crust, or solid_cover (0.25 only for solid_cover)",
            "scalar",
            False,
        ),
        "include_leach": VarSpec(
            "include_leach",
            "dimensionless",
            "If true, apply IPCC 2019 FracLeachMS (2006 default is omit)",
            "scalar",
            False,
        ),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
    }

    parameters = {**_CH4.parameters, **_N2O.parameters}

    outputs = {
        "CH4": VarSpec("CH4", "kg CH4 / year", "Total CH4 emissions", "scalar", True),
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct N2O emissions", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilisation", "scalar", True),
        "N2O_indirect_leach": VarSpec(
            "N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True
        ),
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
        "N_PRP_kg": VarSpec("N_PRP_kg", "kg N / year", "Nitrogen to pasture", "scalar", True),
        "Nex_kg_head": VarSpec("Nex_kg_head", "kg N / year", "Nitrogen excretion per head", "scalar", True),
        "N_managed_kg": VarSpec("N_managed_kg", "kg N / year", "Managed manure N (non-PRP)", "scalar", True),
        "N_MMS_Avb_kg": VarSpec("N_MMS_Avb_kg", "kg N / year", "Manure N remaining for soils (Eq 10.34)", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 10",
            table="Tables 10.17, 10.21, 10.22",
            equation="Eq 10.23, 10.25, 10.26, 10.27, 10.30",
            page="10.53-10.59",
        ),
        Citation(
            source="Little et al. (2008). Holos v1.1.x Methodology. AAFC",
            table="Manure Management section",
            equation="IPCC 2006 Eq 10.23, 10.25-10.29",
            page="",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """Compute manure CH4 and N2O by delegating to the source-correct child modules."""
        ch4 = _CH4.compute(inputs, params)
        n2o = _N2O.compute(inputs, params)
        return {
            "CH4": ch4["CH4"],
            "N2O_direct": n2o["N2O_direct"],
            "N2O_indirect_vol": n2o["N2O_indirect_vol"],
            "N2O_indirect_leach": n2o["N2O_indirect_leach"],
            "N2O_total": n2o["N2O_total"],
            "N_PRP_kg": n2o["N_PRP_kg"],
            "Nex_kg_head": n2o["Nex_kg_head"],
            "N_managed_kg": n2o["N_managed_kg"],
            "N_MMS_Avb_kg": n2o["N_MMS_Avb_kg"],
        }


errors = validate_module(HolosManure())
if errors:
    raise ValueError(f"HolosManure module validation failed: {errors}")
