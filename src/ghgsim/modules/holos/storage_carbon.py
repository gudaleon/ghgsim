"""
Manure-storage carbon (Holos V4 Section 4.1.3.1-4.1.3.3).

Eq 4.1.3-13 through 4.1.3-17 from the opened print (Pogue et al. 2026,
pages 163-164; PDF commit 913bc8c). This is not a translation of the GPL
sources. File:line notes are traceability for the one place the opened C#
does not follow that print.

Carbon lost as methane (Eq 4.1.3-13), every animal group:

    C_manureCH4 = CH4_manure * 12/16

Flow into storage (Eq 4.1.3-14):

    C_flow(t) = C_excretion(t) + C_bedding(t) - C_manureCH4(t)

C_excretion and C_bedding are inputs. They are not calculated here.

The print then both accumulates the stock (Eq 4.1.3-15) and, on the day
after a removal, replaces it (Eq 4.1.3-17). The volatile-solids equation in
the same section (Eq 4.1.3-6) resolves that pair by adding today's inflow in
full and multiplying only yesterday's carryover. source_correct uses that
resolution for carbon:

    C(t) = C_flow(t) + C(t-1) * (1 - fraction(t-1))

fraction is Volume_removed(t-1) / (Total_Volume_landmanure(t-1) * 1000),
the ratio Eq 4.1.3-17 writes. Its bounds, 0 to 0.95, are stated under
Eq 4.1.3-6. Day 0 has no previous removal.

holos_as_coded does not apply that reduction. CalculateAmountOfCarbonInStorageOnCurrentDay
(AnimalResultsServiceBase.cs:1363-1367, Holos commit 53401a022f6c, 2026-11-13)
is C(t) = C_flow(t) + C(t-1). The comment at lines 1129-1134 says carbon is
intended to follow the net-of-removals pattern, and lines 1156-1158 say the
daily storage advance still carries volume only.

Eq 4.1.3-18, a separate liquid-VS stock after removal, is marked in the print
as not implemented in the Holos code. Methane already reduces VSavailable
through Eq 4.1.3-6, so this stepper does not add a second VS stock.

The same C# method zeros storage carbon when housing is pasture (lines
1320-1326). Section 4.1.3 does not say that, and this stepper does not apply it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ghgsim.modules.holos.forks import resolve_option
from ghgsim.modules.holos.process_defs import (
    manure_carbon_from_methane_process,
    storage_carbon_flow_process,
)

_LOST = manure_carbon_from_methane_process()
_FLOW = storage_carbon_flow_process()

FORK_ID = "HOLOS.STORAGE.carbon_removal"


def carbon_lost_as_methane(ch4_kg: float) -> float:
    """Eq 4.1.3-13."""
    return _LOST.compute_rate({"CH4": float(ch4_kg)})


def _clamp_removal(fraction: float, maximum: float) -> float:
    if fraction < 0.0:
        return 0.0
    if fraction > maximum:
        return maximum
    return fraction


def step_storage_carbon(
    ch4_kg_day: Sequence[float],
    carbon_excreted_kg_day: Sequence[float],
    carbon_bedding_kg_day: Sequence[float],
    removal_fractions: Sequence[float] | None = None,
    *,
    apply_removal: bool = True,
    max_removal: float = 0.95,
    carbon_storage_initial: float = 0.0,
) -> dict[str, Any]:
    """
    Step Eq 4.1.3-13 through 4.1.3-15, and Eq 4.1.3-17 when apply_removal is set.

    `removal_fractions[i]` is the fraction removed on day i. It reduces the
    carbon carryover into day i+1. The caller supplies the Eq 4.1.3-17 ratio;
    this function does not convert a manure volume.
    """
    ch4 = [float(value) for value in ch4_kg_day]
    excreted = [float(value) for value in carbon_excreted_kg_day]
    bedding = [float(value) for value in carbon_bedding_kg_day]
    if not ch4:
        raise ValueError("ch4_kg_day is empty")
    if len(excreted) != len(ch4) or len(bedding) != len(ch4):
        raise ValueError("carbon input series must match ch4_kg_day")
    if not 0.0 <= max_removal <= 1.0:
        raise ValueError("max_removal must be between 0 and 1")
    removals = [0.0] * len(ch4)
    if removal_fractions is not None:
        removals = [float(value) for value in removal_fractions]
        if len(removals) != len(ch4):
            raise ValueError("removal_fractions must match ch4_kg_day")

    stock = float(carbon_storage_initial)
    lost_daily: list[float] = []
    flow_daily: list[float] = []
    stock_daily: list[float] = []
    for index, ch4_kg in enumerate(ch4):
        lost = carbon_lost_as_methane(ch4_kg)
        flow = _FLOW.compute_rate(
            {"C_excreted": excreted[index], "C_bedding": bedding[index], "C_as_methane": lost}
        )
        if apply_removal and index > 0:
            fraction = _clamp_removal(removals[index - 1], max_removal)
            stock = flow + stock * (1.0 - fraction)
        else:
            stock = flow + stock
        lost_daily.append(lost)
        flow_daily.append(flow)
        stock_daily.append(stock)
    return {
        "C_lost_as_methane_kg": lost_daily,
        "C_flow_kg_day": flow_daily,
        "C_storage_kg": stock_daily,
        "C_lost_as_methane_total_kg": sum(lost_daily),
        "days": len(ch4),
        "removal_applied": apply_removal,
    }


def total_carbon_storage(group_stocks: Sequence[Sequence[float]]) -> list[float]:
    """Eq 4.1.3-16. Sum C_storage across animal groups on each day."""
    if not group_stocks:
        raise ValueError("group_stocks is empty")
    width = len(group_stocks[0])
    if width == 0 or any(len(series) != width for series in group_stocks):
        raise ValueError("animal-group carbon series must be non-empty and the same length")
    return [sum(series[index] for series in group_stocks) for index in range(width)]


def run_storage_carbon(
    ch4_kg_day: Sequence[float],
    carbon_excreted_kg_day: Sequence[float],
    carbon_bedding_kg_day: Sequence[float],
    removal_fractions: Sequence[float] | None = None,
    *,
    fork_settings: dict[str, str] | None = None,
    max_removal: float = 0.95,
    carbon_storage_initial: float = 0.0,
) -> dict[str, Any]:
    """Apply HOLOS.STORAGE.carbon_removal. Default is the printed removal."""
    option = resolve_option(FORK_ID, fork_settings)
    result = step_storage_carbon(
        ch4_kg_day,
        carbon_excreted_kg_day,
        carbon_bedding_kg_day,
        removal_fractions,
        apply_removal=option == "source_correct",
        max_removal=max_removal,
        carbon_storage_initial=carbon_storage_initial,
    )
    result["carbon_removal_option"] = option
    return result
