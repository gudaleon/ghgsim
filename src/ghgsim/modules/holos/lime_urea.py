"""Holos lime/urea CO2: IPCC 2006 Eq 11.12 and 11.13. No holos_as_coded fork."""

from ghgsim.modules.ipcc2006.lime_urea import IPCC2006LimeUreaCO2


class HolosLimeUreaCO2(IPCC2006LimeUreaCO2):
    """Same published IPCC equations; Holos methodology cites IPCC 2006."""

    id = "holos.lime_urea_co2"
    version = "1.0.0"
