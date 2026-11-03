"""Holos V4 liquid-tank manure CH4 (Pogue et al. 2026 Eq 4.1.3-1..10)."""

import math
from datetime import date

import pytest

from ghgsim.modules.holos.liquid_tank import climate_factor, kelvin_temperature
from ghgsim.modules.holos.manure_ch4 import HolosManureCH4
from ghgsim.modules.holos.process_defs import liquid_tank_climate_factor_process

HEAD = 10.0
VS = 5.4
B0 = 0.24
DENSITY = 0.67
T1 = 308.16
E_ACT = 19347.0
GAS_R = 1.987
FLOOR_C = 1.0
KELVIN = 273.15
MDP = 1.0
MAX_REMOVAL = 0.95


def _tank_params(**overrides):
    base = {
        "VS_dairy_canada": VS,
        "VS_beef_canada": 2.4,
        "B0_dairy_canada": B0,
        "B0_beef_canada": 0.19,
        "VS_market_swine": 0.3,
        "B0_market_swine": 0.48,
        "MCF_liquid_nocrust_cool": 0.17,
        "MCF_liquid_nocrust_temperate": 0.27,
        "MCF_liquid_crust_cool": 0.10,
        "MCF_liquid_crust_temperate": 0.17,
        "MCF_solid_storage_cool": 0.02,
        "MCF_solid_storage_temperate": 0.04,
        "MCF_pasture_cool": 0.015,
        "MCF_daily_spread_cool": 0.001,
        "CH4_M3_TO_KG": DENSITY,
        "cover_crust_reduction": 0.40,
        "cover_solid_reduction": 0.25,
        "TANK_T1_K": T1,
        "TANK_E_CAL": E_ACT,
        "TANK_R_CAL": GAS_R,
        "TANK_TEMP_FLOOR_C": FLOOR_C,
        "TANK_KELVIN": KELVIN,
        "TANK_WINDOW_MANUAL": 30,
        "TANK_WINDOW_CODED": 31,
        "TANK_MDP": MDP,
        "TANK_MAX_REMOVAL": MAX_REMOVAL,
    }
    base.update(overrides)
    return base


def _inputs(**overrides):
    inputs = {
        "head": HEAD,
        "animal_type": "dairy",
        "climate_zone": "temperate",
        "systems": {"liquid_nocrust": 1.0},
        "cover_type": "none",
        "VS_kg_day": VS,
        "forks": {"HOLOS.CH4.liquid_tank": "holos_v4_liquid_tank"},
    }
    inputs.update(overrides)
    return inputs


def _spec_factor(temp_c: float) -> float:
    """Independent expansion of Eq 4.1.3-1 and 4.1.3-2 at a constant temperature."""
    celsius = FLOOR_C if temp_c <= FLOOR_C else temp_c
    t2 = celsius + KELVIN
    exponent = math.exp(E_ACT * (t2 - T1) / (GAS_R * T1 * t2))
    return 1.0 - (1.0 - exponent) ** (1.0 / 30.0)


def _spec_series(temps, removals=None, reset_on_jan1=False, dates=None, window=30, cover=0.0):
    """Day loop written from Eq 4.1.3-5..9, not from run_liquid_tank."""
    prev_available = 0.0
    prev_consumed = 0.0
    total = 0.0
    removals = removals or [0.0] * len(temps)
    for index, _temp in enumerate(temps):
        is_jan1 = bool(dates and dates[index].month == 1 and dates[index].day == 1)
        if reset_on_jan1 and is_jan1:
            prev_available = 0.0
            prev_consumed = 0.0
            removal = 0.0
        elif index == 0:
            removal = 0.0
        else:
            removal = min(max(removals[index - 1], 0.0), MAX_REMOVAL)
        start = max(0, index - (window - 1))
        window_temps = temps[start : index + 1]
        t2 = sum(
            (FLOOR_C if item <= FLOOR_C else item) + KELVIN for item in window_temps
        ) / len(window_temps)
        exponent = math.exp(E_ACT * (t2 - T1) / (GAS_R * T1 * t2))
        factor = 1.0 - (1.0 - exponent) ** (1.0 / 30.0)
        vs_loaded = VS * HEAD * MDP
        vs_available = vs_loaded + (prev_available - prev_consumed) * (1.0 - removal)
        vs_consumed = factor * vs_available
        total += vs_consumed * B0 * DENSITY * (1.0 - cover)
        prev_available = vs_available
        prev_consumed = vs_consumed
    return total


def test_climate_factor_matches_printed_equation_at_10c():
    expected = _spec_factor(10.0)
    assert climate_factor(kelvin_temperature(10.0, FLOOR_C, KELVIN), T1, E_ACT, GAS_R) == pytest.approx(expected)
    assert expected == pytest.approx(0.002108867328538766)
    equation = liquid_tank_climate_factor_process().rate_equation
    assert "1.0 / 30.0" in equation
    assert "math.exp" in equation


def test_floor_replaces_temperatures_at_or_below_1c():
    assert kelvin_temperature(1.0, FLOOR_C, KELVIN) == pytest.approx(274.15)
    assert kelvin_temperature(-20.0, FLOOR_C, KELVIN) == pytest.approx(274.15)
    assert kelvin_temperature(1.1, FLOOR_C, KELVIN) == pytest.approx(274.25)


def test_missing_temperature_is_unverified_input_and_keeps_ipcc():
    module = HolosManureCH4()
    params = _tank_params()
    ipcc = module.compute(_inputs(forks={}), params)
    tank = module.compute(_inputs(), params)
    assert tank["tank_status"] == "UNVERIFIED-input"
    assert tank["tank_applied"] is False
    assert tank["CH4"] == pytest.approx(ipcc["CH4"])
    assert tank["CH4_ipcc_eq10_23"] == pytest.approx(ipcc["CH4"])


def test_default_fork_does_not_run_the_tank():
    module = HolosManureCH4()
    params = _tank_params()
    result = module.compute(
        _inputs(forks={}, temperatures_c=[10.0, 10.0]),
        params,
    )
    assert result["tank_status"] == "not_selected"
    assert result["tank_applied"] is False


def test_beef_liquid_stays_on_equation_10_23():
    module = HolosManureCH4()
    params = _tank_params()
    result = module.compute(
        _inputs(animal_type="beef", temperatures_c=[10.0, 12.0]),
        params,
    )
    assert result["tank_status"] == "not_applicable"
    assert result["tank_applied"] is False
    assert result["CH4"] == pytest.approx(result["CH4_ipcc_eq10_23"])


def test_constant_temperature_series_matches_hand_expansion():
    temps = [10.0, 10.0, 10.0]
    module = HolosManureCH4()
    result = module.compute(_inputs(temperatures_c=temps), _tank_params())
    assert result["tank_status"] == "computed"
    assert result["tank_applied"] is True
    assert result["CH4"] == pytest.approx(_spec_series(temps))
    assert result["CH4"] != pytest.approx(result["CH4_ipcc_eq10_23"])


def test_cover_reduction_is_part_of_equation_4_1_3_9():
    temps = [10.0, 10.0]
    module = HolosManureCH4()
    params = _tank_params()
    uncovered = module.compute(_inputs(temperatures_c=temps), params)
    crust = module.compute(_inputs(temperatures_c=temps, cover_type="natural_crust"), params)
    assert crust["cover_reduction_fraction"] == pytest.approx(0.40)
    assert crust["CH4"] == pytest.approx(uncovered["CH4"] * 0.60)
    assert crust["CH4"] == pytest.approx(_spec_series(temps, cover=0.40))


def test_removal_cap_leaves_five_percent_and_cli_fork_ignores_it():
    temps = [10.0, 10.0]
    removals = [1.0, 0.0]
    module = HolosManureCH4()
    params = _tank_params()
    capped = module.compute(_inputs(temperatures_c=temps, removal_fractions=removals), params)
    untouched = module.compute(_inputs(temperatures_c=temps), params)
    cli = module.compute(
        _inputs(
            temperatures_c=temps,
            removal_fractions=removals,
            forks={
                "HOLOS.CH4.liquid_tank": "holos_v4_liquid_tank",
                "HOLOS.STORAGE.cli_no_drain": "holos_as_coded",
            },
        ),
        params,
    )
    assert capped["CH4"] == pytest.approx(_spec_series(temps, removals))
    assert capped["CH4"] < untouched["CH4"]
    assert cli["CH4"] == pytest.approx(untouched["CH4"])
    assert cli["CH4"] == pytest.approx(_spec_series(temps))


def test_january_reset_drops_carryover_only_when_fork_is_on():
    temps = [10.0, 10.0, 10.0]
    dates = [date(2023, 12, 31), date(2024, 1, 1), date(2024, 1, 2)]
    module = HolosManureCH4()
    params = _tank_params()
    carried = module.compute(_inputs(temperatures_c=temps, dates=dates), params)
    reset = module.compute(
        _inputs(
            temperatures_c=temps,
            dates=dates,
            forks={
                "HOLOS.CH4.liquid_tank": "holos_v4_liquid_tank",
                "HOLOS.STORAGE.year_reset": "holos_as_coded",
            },
        ),
        params,
    )
    assert carried["CH4"] == pytest.approx(_spec_series(temps, dates=dates))
    assert reset["CH4"] == pytest.approx(_spec_series(temps, dates=dates, reset_on_jan1=True))
    assert reset["CH4"] < carried["CH4"]


def test_year_reset_without_dates_raises():
    module = HolosManureCH4()
    with pytest.raises(ValueError, match="dates"):
        module.compute(
            _inputs(
                temperatures_c=[10.0, 10.0],
                forks={
                    "HOLOS.CH4.liquid_tank": "holos_v4_liquid_tank",
                    "HOLOS.STORAGE.year_reset": "holos_as_coded",
                },
            ),
            _tank_params(),
        )


def test_coded_window_differs_only_when_the_extra_day_differs():
    module = HolosManureCH4()
    params = _tank_params()
    flat = [10.0] * 31
    varied = [20.0] + [10.0] * 30
    forks = {
        "HOLOS.CH4.liquid_tank": "holos_v4_liquid_tank",
        "HOLOS.STORAGE.temp_window": "holos_as_coded",
    }
    flat_manual = module.compute(_inputs(temperatures_c=flat), params)
    flat_coded = module.compute(_inputs(temperatures_c=flat, forks=forks), params)
    varied_manual = module.compute(_inputs(temperatures_c=varied), params)
    varied_coded = module.compute(_inputs(temperatures_c=varied, forks=forks), params)
    assert flat_coded["CH4"] == pytest.approx(flat_manual["CH4"])
    assert varied_coded["CH4"] == pytest.approx(_spec_series(varied, window=31))
    assert varied_manual["CH4"] == pytest.approx(_spec_series(varied, window=30))
    assert varied_coded["CH4"] != pytest.approx(varied_manual["CH4"])


def test_storage_forks_do_not_change_the_ipcc_default():
    module = HolosManureCH4()
    params = _tank_params()
    base = module.compute(_inputs(forks={}), params)
    coded = module.compute(
        _inputs(
            forks={
                "HOLOS.STORAGE.year_reset": "holos_as_coded",
                "HOLOS.STORAGE.temp_window": "holos_as_coded",
                "HOLOS.STORAGE.cli_no_drain": "holos_as_coded",
            },
            temperatures_c=[10.0, 10.0],
            dates=[date(2024, 1, 1), date(2024, 1, 2)],
            removal_fractions=[1.0, 0.0],
        ),
        params,
    )
    assert coded["tank_status"] == "not_selected"
    assert coded["CH4"] == pytest.approx(base["CH4"])
