"""Holos V4 manure-storage carbon (Pogue et al. 2026 Eq 4.1.3-13..17)."""

import pytest

from ghgsim.modules.holos.forks import resolve_option
from ghgsim.modules.holos.liquid_tank import run_liquid_tank
from ghgsim.modules.holos.storage_carbon import (
    carbon_lost_as_methane,
    run_storage_carbon,
    step_storage_carbon,
    total_carbon_storage,
)

CH4 = [8.0, 4.0]
EXCRETED = [10.0, 10.0]
BEDDING = [2.0, 2.0]
REMOVALS = [0.4, 0.0]


def _hand(ch4, excreted, bedding, removals, apply_removal, cap=0.95):
    """Independent expansion of Eq 4.1.3-13, 4.1.3-14, 4.1.3-15 and 4.1.3-17."""
    stock = 0.0
    stocks = []
    for index, methane in enumerate(ch4):
        lost = methane * 12.0 / 16.0
        flow = excreted[index] + bedding[index] - lost
        if apply_removal and index > 0:
            fraction = min(max(removals[index - 1], 0.0), cap)
            stock = flow + stock * (1.0 - fraction)
        else:
            stock = flow + stock
        stocks.append(stock)
    return stocks


def test_equation_4_1_3_13_is_twelve_sixteenths():
    assert carbon_lost_as_methane(8.0) == pytest.approx(8.0 * 12.0 / 16.0)
    assert carbon_lost_as_methane(0.0) == 0.0


def test_no_removal_matches_plain_accumulation():
    result = step_storage_carbon(CH4, EXCRETED, BEDDING, REMOVALS, apply_removal=False)
    assert result["C_storage_kg"] == pytest.approx(_hand(CH4, EXCRETED, BEDDING, REMOVALS, False))
    assert result["C_lost_as_methane_total_kg"] == pytest.approx(sum(CH4) * 12.0 / 16.0)
    # Day 0 flow is 10 + 2 - 6 = 6. Day 1 flow is 10 + 2 - 3 = 9. Stock 6 then 15.
    assert result["C_storage_kg"] == pytest.approx([6.0, 15.0])


def test_printed_removal_reduces_only_the_carryover():
    result = step_storage_carbon(CH4, EXCRETED, BEDDING, REMOVALS, apply_removal=True)
    assert result["C_storage_kg"] == pytest.approx(_hand(CH4, EXCRETED, BEDDING, REMOVALS, True))
    # 9 + 6 * (1 - 0.4) = 12.6, against 15 when the removal is ignored.
    assert result["C_storage_kg"][1] == pytest.approx(12.6)
    coded = step_storage_carbon(CH4, EXCRETED, BEDDING, REMOVALS, apply_removal=False)
    assert result["C_storage_kg"][1] != pytest.approx(coded["C_storage_kg"][1])


def test_removal_fraction_is_capped_at_0_95():
    result = step_storage_carbon(CH4, EXCRETED, BEDDING, [1.5, 0.0], apply_removal=True)
    # Day-1 stock 6, then 9 + 6 * (1 - 0.95) = 9.3.
    assert result["C_storage_kg"][1] == pytest.approx(9.3)


def test_flow_may_be_negative_when_methane_carbon_exceeds_inputs():
    result = step_storage_carbon([32.0], [1.0], [1.0], apply_removal=True)
    # 1 + 1 - 32 * 12/16 = -22. The print subtracts and does not floor the flow.
    assert result["C_flow_kg_day"][0] == pytest.approx(-22.0)
    assert result["C_storage_kg"][0] == pytest.approx(-22.0)


def test_total_storage_is_the_sum_across_groups():
    one = step_storage_carbon(CH4, EXCRETED, BEDDING, apply_removal=True)["C_storage_kg"]
    two = step_storage_carbon([0.0, 0.0], [1.0, 1.0], [0.0, 0.0], apply_removal=True)["C_storage_kg"]
    assert total_carbon_storage([one, two]) == pytest.approx([one[0] + two[0], one[1] + two[1]])


def test_fork_default_is_the_printed_removal():
    assert resolve_option("HOLOS.STORAGE.carbon_removal") == "source_correct"
    printed = run_storage_carbon(CH4, EXCRETED, BEDDING, REMOVALS)
    coded = run_storage_carbon(
        CH4,
        EXCRETED,
        BEDDING,
        REMOVALS,
        fork_settings={"HOLOS.STORAGE.carbon_removal": "holos_as_coded"},
    )
    assert printed["carbon_removal_option"] == "source_correct"
    assert coded["carbon_removal_option"] == "holos_as_coded"
    assert printed["C_storage_kg"] == pytest.approx(_hand(CH4, EXCRETED, BEDDING, REMOVALS, True))
    assert coded["C_storage_kg"] == pytest.approx(_hand(CH4, EXCRETED, BEDDING, REMOVALS, False))


def test_tank_daily_methane_sums_to_the_annual_total():
    temps = [10.0, 10.0, 10.0]
    params = {
        "TANK_T1_K": 308.16,
        "TANK_E_CAL": 19347.0,
        "TANK_R_CAL": 1.987,
        "TANK_TEMP_FLOOR_C": 1.0,
        "TANK_KELVIN": 273.15,
        "TANK_WINDOW_MANUAL": 30,
        "TANK_WINDOW_CODED": 31,
        "TANK_MDP": 1.0,
        "TANK_MAX_REMOVAL": 0.95,
    }
    tank = run_liquid_tank(
        head=10.0,
        vs_kg_day=5.4,
        b0=0.24,
        ch4_density=0.67,
        cover_reduction=0.0,
        temperatures_c=temps,
        params=params,
    )
    assert sum(tank["CH4_daily"]) == pytest.approx(tank["CH4"])
    carbon = run_storage_carbon(tank["CH4_daily"], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0])
    assert carbon["C_lost_as_methane_total_kg"] == pytest.approx(tank["CH4"] * 12.0 / 16.0)


def test_series_length_is_checked():
    with pytest.raises(ValueError):
        step_storage_carbon(CH4, [1.0], BEDDING)
    with pytest.raises(ValueError):
        step_storage_carbon([], [], [])
