"""IPCC Tier 1 components added for county-year runs (AN_v1).

* :mod:`.fsom` - N mineralised from soil organic matter loss (F_SOM), Eq 2.25 + Eq 11.8.
* :mod:`.forage_residue` - hay / haylage / silage residue N (2006 Table 11.2, 2019 Table 11.1a + 11.2).
* :mod:`.crop_n_removal` - N removed in harvested crops (USDA NRCS AWMFH Table 6-6) and soybean BNF.
* :mod:`.lime_urea` - Tier 1 lime / urea CO2 for both guideline versions (2019: "No refinement").
* :mod:`.n_budget` - soil-surface N budget with an explicit closing term.
* :mod:`.n_budget_closure` - extra N inputs (soybean full BNF, alfalfa BNF, deposition) and a budget-consistent leaching base.

Every numeric default is read from ``data/ipcc_params_AN_v11.csv`` (key, value, table, page). Nothing here
is calibrated or fitted.
"""
from .crop_n_removal import CROP_N_KEYS, crop_n_removal_kg, soybean_bnf_kg
from .forage_residue import forage_residue_n, silage_residue_n
from .fsom import fsom_kg_n, soc_stock_t, tillage_soc_change_t
from .lime_urea import lime_urea_co2_kg
from .n_budget import n_budget
from .n_budget_closure import (
    alfalfa_bnf_kg,
    deposition_n_kg,
    leach_budget_kg,
    n_budget_v2,
    soybean_bnf_full_kg,
    soybean_bnf_per_grain_kg,
)

__all__ = [
    "CROP_N_KEYS",
    "crop_n_removal_kg",
    "soybean_bnf_kg",
    "forage_residue_n",
    "silage_residue_n",
    "fsom_kg_n",
    "soc_stock_t",
    "tillage_soc_change_t",
    "lime_urea_co2_kg",
    "n_budget",
    "alfalfa_bnf_kg",
    "deposition_n_kg",
    "leach_budget_kg",
    "n_budget_v2",
    "soybean_bnf_full_kg",
    "soybean_bnf_per_grain_kg",
]
