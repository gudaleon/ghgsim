"""IPCC 2006 Guidelines modules for GHG calculations."""

from .soil_n2o import IPCC2006SoilN2O
from .enteric import IPCC2006Enteric
from .manure import IPCC2006Manure

__all__ = [
    "IPCC2006SoilN2O",
    "IPCC2006Enteric",
    "IPCC2006Manure",
]
