"""
Liquid dairy and swine manure CH4 tank (Holos V4 Section 4.1.3).

The default manure-CH4 path stays IPCC 2006 Equation 10.23. This stepper is
the model-version alternative printed in Pogue et al. 2026, pages 161-162
(Eq 4.1.3-1 through 4.1.3-10). It is not a translation of the GPL sources.
File:line notes below are traceability for forks where the opened C# does
not follow that print.

State update (Eq 4.1.3-5, and Eq 4.1.3-6 when manure was removed yesterday):

    VSavailable(d) = VSloaded(d)
        + (VSavailable(d-1) - VSconsumed(d-1)) * (1 - removal_fraction(d-1))

removal_fraction is clamped to [0, 0.95] (95% emptying efficiency, Eq 4.1.3-6
note). ghgsim takes that fraction as unitless. The print's "× 1000" converts
Eq 4.5.3-3 totals that are stored per 1000 L; it is not applied again here.

The manual carries volatile solids across 1 January. The opened C# discards
the previous day on 1 January (AnimalResultsServiceBase.cs:124-127 and
:881-884). That reset is the holos_as_coded option of HOLOS.STORAGE.year_reset.

The manual averages the last 30 days. The opened C# averages date-30 through
date inclusive, which is 31 days (CalculateDegreesKelvinOverLast30Days,
AnimalResultsServiceBase.cs:986-1007, ClimateData.cs:521). That window is
HOLOS.STORAGE.temp_window.

CLI field applications never set AnimalType, so IsImportedManure() is true
(ManureApplicationViewItem.cs:148-150; FieldSystemInputConverter.cs:270-285)
and ManureService.cs:240-242 skips them. HOLOS.STORAGE.cli_no_drain forces
the removal fraction to 0.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from ghgsim.modules.holos.process_defs import (
    liquid_tank_ch4_process,
    liquid_tank_climate_factor_process,
    liquid_tank_vs_consumed_process,
)

TANK_ANIMALS = frozenset({"dairy", "market_swine", "breeding_swine"})
LIQUID_SYSTEMS = frozenset({"liquid_nocrust", "liquid_crust"})

_CLIMATE = liquid_tank_climate_factor_process()
_CONSUMED = liquid_tank_vs_consumed_process()
_CH4 = liquid_tank_ch4_process()

# Printed Eq 4.1.3-2. Above T1 the (1 - exp) term is negative and the
# 1/30 power is undefined in real arithmetic (the C# Math.Pow path as well).
_T2_ABOVE_T1 = "T2 exceeds T1; Eq 4.1.3-2 is undefined for that temperature"


def kelvin_temperature(temp_c: float, floor_c: float, offset: float) -> float:
    """Eq 4.1.3-1. Temperatures at or below the floor are replaced by the floor."""
    celsius = floor_c if temp_c <= floor_c else temp_c
    return celsius + offset


def climate_factor(t2_k: float, t1_k: float, activation_energy: float, gas_constant: float) -> float:
    """Eq 4.1.3-2 via the registered ProcessDef."""
    if t2_k <= 0.0 or t1_k <= 0.0:
        raise ValueError("Kelvin temperatures must be positive")
    if t2_k > t1_k:
        raise ValueError(f"{_T2_ABOVE_T1} (T2={t2_k}, T1={t1_k})")
    return _CLIMATE.compute_rate(
        {"E": activation_energy, "T2": t2_k, "T1": t1_k, "R": gas_constant}
    )


def _parse_day(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _mean_kelvin(temps_c: Sequence[float], index: int, window_days: int, floor_c: float, offset: float) -> float:
    start = max(0, index - (window_days - 1))
    window = temps_c[start : index + 1]
    if not window:
        raise ValueError("temperature window is empty")
    total = sum(kelvin_temperature(float(temp), floor_c, offset) for temp in window)
    return total / len(window)


def _clamp_removal(fraction: float, maximum: float) -> float:
    if fraction < 0.0:
        return 0.0
    if fraction > maximum:
        return maximum
    return fraction


def run_liquid_tank(
    *,
    head: float,
    vs_kg_day: float,
    b0: float,
    ch4_density: float,
    cover_reduction: float,
    temperatures_c: Sequence[float],
    params: Mapping[str, Any],
    dates: Sequence[Any] | None = None,
    removal_fractions: Sequence[float] | None = None,
    year_reset: bool = False,
    coded_temp_window: bool = False,
    ignore_removals: bool = False,
    vs_available_initial: float = 0.0,
    vs_consumed_initial: float = 0.0,
) -> dict[str, Any]:
    """
    Step Eq 4.1.3-1..10 for one animal group.

    `removal_fractions[i]` is the fraction removed on day i. It reduces the
    volatile-solids carryover into day i+1. Day 0 has no previous removal.
    """
    temps = [float(temp) for temp in temperatures_c]
    if not temps:
        raise ValueError("temperatures_c is empty")
    n = len(temps)
    parsed_dates: list[date] | None = None
    if dates is not None:
        parsed_dates = [_parse_day(value) for value in dates]
        if len(parsed_dates) != n:
            raise ValueError("dates and temperatures_c must have the same length")
    if year_reset and parsed_dates is None:
        raise ValueError("HOLOS.STORAGE.year_reset requires dates so 1 January can be identified")
    removals = [0.0] * n
    if removal_fractions is not None:
        removals = [float(value) for value in removal_fractions]
        if len(removals) != n:
            raise ValueError("removal_fractions and temperatures_c must have the same length")

    t1 = float(params["TANK_T1_K"])
    activation = float(params["TANK_E_CAL"])
    gas_r = float(params["TANK_R_CAL"])
    floor_c = float(params["TANK_TEMP_FLOOR_C"])
    offset = float(params["TANK_KELVIN"])
    window_days = int(params["TANK_WINDOW_CODED"] if coded_temp_window else params["TANK_WINDOW_MANUAL"])
    mdp = float(params["TANK_MDP"])
    max_removal = float(params["TANK_MAX_REMOVAL"])
    if window_days < 1:
        raise ValueError("temperature window must be at least 1 day")
    if not 0.0 <= max_removal <= 1.0:
        raise ValueError("TANK_MAX_REMOVAL must be between 0 and 1")

    prev_available = float(vs_available_initial)
    prev_consumed = float(vs_consumed_initial)
    ch4_total = 0.0
    vs_produced_total = 0.0
    for index, _temp in enumerate(temps):
        is_new_year = bool(
            parsed_dates is not None
            and parsed_dates[index].month == 1
            and parsed_dates[index].day == 1
        )
        if year_reset and is_new_year:
            prev_available = 0.0
            prev_consumed = 0.0
            removal = 0.0
        elif index == 0 or ignore_removals:
            removal = 0.0
        else:
            removal = _clamp_removal(removals[index - 1], max_removal)

        t2 = _mean_kelvin(temps, index, window_days, floor_c, offset)
        factor = climate_factor(t2, t1, activation, gas_r)
        vs_produced = float(vs_kg_day) * float(head)
        vs_loaded = vs_produced * mdp
        carry = prev_available - prev_consumed
        vs_available = vs_loaded + carry * (1.0 - removal)
        vs_consumed = _CONSUMED.compute_rate({"f": factor, "VS_available": vs_available})
        day_ch4 = _CH4.compute_rate(
            {
                "VS_consumed": vs_consumed,
                "B0": b0,
                "CH4_M3_TO_KG": ch4_density,
                "cover_reduction": cover_reduction,
            }
        )
        if not math.isfinite(day_ch4):
            raise ValueError(f"non-finite tank CH4 on day index {index}")
        ch4_total += day_ch4
        vs_produced_total += vs_produced
        prev_available = vs_available
        prev_consumed = vs_consumed

    if vs_produced_total <= 0.0 or b0 == 0.0 or ch4_density == 0.0:
        mcf = 0.0
    else:
        # Eq 4.1.3-12.
        mcf = ch4_total / (ch4_density * b0 * vs_produced_total)
    return {
        "CH4": ch4_total,
        "MCF_implied": mcf,
        "VS_produced_kg": vs_produced_total,
        "days": n,
        "window_days": window_days,
    }
