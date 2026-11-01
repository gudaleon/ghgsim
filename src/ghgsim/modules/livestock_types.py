"""
US livestock categories used by IPCC/Holos poultry and swine modules.

Category names map to USDA Census of Agriculture inventory items and
EPA GHGI Annex 3.11 animal groups. Coefficients themselves are IPCC
table values, not EPA or USDA emission factors.
"""

from __future__ import annotations

# IPCC 2006 Vol 4 Ch 10 Table 10.10 p. 10.28: poultry enteric "Insufficient
# data for calculation"; Table 10.9 p. 10.27 method = "Not developed".
POULTRY_TYPES = frozenset({"broilers", "layers", "turkeys", "poultry"})

# IPCC 2006 Table 10.10 swine Tier 1 EF; market vs breeding only differs
# for manure (Tables 10A-7 / 10A-8), not enteric.
SWINE_TYPES = frozenset({"market_swine", "breeding_swine", "swine"})

MONOGASTRIC_TYPES = POULTRY_TYPES | SWINE_TYPES

# USDA Census of Agriculture item → ghgsim animal_type.
# Names follow USDA NASS Census livestock inventory wording.
USDA_CENSUS_MAP = {
    "broilers": "Broilers and other meat-type chickens",
    "layers": "Layers 20 weeks old and older",
    "turkeys": "Turkeys",
    "market_swine": "Hogs and pigs, other (market)",
    "breeding_swine": "Hogs and pigs, breeding",
}

# EPA Inventory of U.S. GHG Emissions and Sinks, Annex 3.11 groups.
EPA_ANNEX_3_11_MAP = {
    "broilers": "Broilers",
    "layers": "Layers",
    "turkeys": "Turkeys",
    "market_swine": "Market swine",
    "breeding_swine": "Breeding swine",
}

# Manure-system stems added for poultry/swine (plus existing cattle stems).
POULTRY_SYSTEMS = frozenset({"poultry_with_litter", "poultry_without_litter"})
SWINE_EXTRA_SYSTEMS = frozenset({"pit"})


def is_poultry(animal_type: str) -> bool:
    return str(animal_type) in POULTRY_TYPES


def is_swine(animal_type: str) -> bool:
    return str(animal_type) in SWINE_TYPES


def is_monogastric(animal_type: str) -> bool:
    return str(animal_type) in MONOGASTRIC_TYPES


def swine_fracgas_animal(animal_type: str) -> str:
    """FracGasMS Table 10.22 uses a single Swine row."""
    return "swine" if is_swine(animal_type) else str(animal_type)


def poultry_fracgas_animal(animal_type: str) -> str:
    """FracGasMS Table 10.22 uses a single Poultry row."""
    return "poultry" if is_poultry(animal_type) else str(animal_type)
