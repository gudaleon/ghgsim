"""Holos (Canada) agricultural GHG modules."""

from ghgsim.modules.holos.enteric import HolosEnteric
from ghgsim.modules.holos.manure import HolosManure
from ghgsim.modules.holos.manure_ch4 import HolosManureCH4
from ghgsim.modules.holos.soil_n2o import HolosSoilN2O
from ghgsim.modules.holos.vs import HolosVolatileSolids

__all__ = [
    "HolosEnteric",
    "HolosManure",
    "HolosManureCH4",
    "HolosSoilN2O",
    "HolosVolatileSolids",
]
