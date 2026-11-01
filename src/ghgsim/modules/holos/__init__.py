"""Holos (Canada) agricultural GHG modules."""

from ghgsim.modules.holos.enteric import HolosEnteric
from ghgsim.modules.holos.fields import HolosFieldN
from ghgsim.modules.holos.lime_urea import HolosLimeUreaCO2
from ghgsim.modules.holos.manure import HolosManure
from ghgsim.modules.holos.manure_ch4 import HolosManureCH4
from ghgsim.modules.holos.manure_n2o import HolosManureN2O
from ghgsim.modules.holos.soil_n2o import HolosSoilN2O
from ghgsim.modules.holos.vs import HolosVolatileSolids

__all__ = [
    "HolosEnteric",
    "HolosFieldN",
    "HolosLimeUreaCO2",
    "HolosManure",
    "HolosManureCH4",
    "HolosManureN2O",
    "HolosSoilN2O",
    "HolosVolatileSolids",
]
