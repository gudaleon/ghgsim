"""Holos (Canada) agricultural GHG modules."""

from ghgsim.modules.holos.enteric import HolosEnteric
from ghgsim.modules.holos.manure import HolosManure
from ghgsim.modules.holos.soil_n2o import HolosSoilN2O

__all__ = ["HolosEnteric", "HolosManure", "HolosSoilN2O"]
