"""N removed in harvested crops, and soybean biological N fixation (BNF).

Removal follows the worked example of USDA NRCS Agricultural Waste Management Field Handbook, Part 651, Chapter 6,
section 651.0605 (p. 6-18): removal (lb N) = yield (bu) * lb/bu * N % / 100, using Table 6-6 (pp. 6-19 to 6-22)
'average concentration of nutrients' in the harvested part. Silage percentages are on a dry-matter basis, so
silage green weight is multiplied by the dry-matter fraction in the row label (corn silage 35% dm).
A dry-matter-corrected variant (multiplying by IPCC DRY) is offered for sensitivity only.

Soybean BNF: Salvagiotti et al. (2008, Field Crops Res. 108:1-13, abstract): 'On an average, 50-60% of soybean N
demand was met by biological N2 fixation'. Here N demand = above-ground N (harvested seed N + above-ground residue
N); BNF_AG = Ndfa * that. The same abstract's 24% below-ground contribution is not added (reported as a note).
"""
from __future__ import annotations

from collections.abc import Mapping

LB_KG = 0.45359237
# NASS crop key -> NRCS Table 6-6 key
CROP_N_KEYS = {
    "corn_grain": "corn_grain", "soybeans": "soybeans", "wheat_winter": "wheat", "wheat_spring": "wheat",
    "wheat_durum": "wheat", "oats": "oats", "barley": "barley", "rye": "rye", "sorghum_grain": "sorghum_grain",
    "rice": "rice", "peanuts": "peanuts", "potatoes": "potatoes", "beans_dry": "beans_dry",
    "alfalfa_hay": "alfalfa_hay", "other_hay": "clover_grass_hay", "alfalfa_haylage": "alfalfa_haylage",
    "other_haylage": "clover_grass_hay", "corn_silage": "corn_silage",
}


def crop_n_removal_kg(p: Mapping[str, float], crop: str, weight_lb: float, dm_frac: float = 1.0,
                      nrcs_key: str | None = None) -> float:
    """kg N removed. ``weight_lb`` is reported production in lb (bu * lb/bu, tons * 2000, cwt * 100);
    ``dm_frac`` converts to the basis of the Table 6-6 percentage (1.0 when the table is applied as in its example)."""
    key = nrcs_key or CROP_N_KEYS.get(crop)
    if key is None:
        raise KeyError(f"no NRCS Table 6-6 mapping for {crop!r}")
    if weight_lb < 0 or not 0.0 < dm_frac <= 1.0:
        raise ValueError("weight must be >= 0 and dm_frac in (0, 1]")
    return weight_lb * dm_frac * p[f"NRCS.CROPN_pct.{key}"] / 100.0 * LB_KG


def soybean_bnf_kg(seed_n_kg: float, ag_residue_n_kg: float, ndfa: float) -> float:
    """Above-ground BNF (kg N) = Ndfa * (seed N + above-ground residue N)."""
    if not 0.0 <= ndfa <= 1.0:
        raise ValueError("Ndfa must be in [0, 1]")
    return ndfa * (seed_n_kg + ag_residue_n_kg)
