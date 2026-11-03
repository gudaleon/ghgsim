"""IPCC 2019 Refinement modules for GHG calculations."""

from .soil_n2o import IPCC2019SoilN2O
from .enteric import IPCC2019Enteric

__all__ = [
    "IPCC2019SoilN2O",
    "IPCC2019Enteric",
]
