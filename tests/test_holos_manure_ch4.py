"""Unit tests: Holos manure CH4 default vs CE-14 cover reduction fork.

Locks the Phase 3d fix: Holos cover factors are REDUCTION fractions
(0.40 crust, 0.25 solid cover only), applied as remaining = 1 - reduction.
When the cover fork applies, IPCC with-crust MCF is not also used.
"""

import pytest

from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.modules.holos.manure_ch4 import HolosManureCH4
from ghgsim.modules.holos.process_defs import manure_ch4_process

VS = 5.4
B0 = 0.24
DENSITY = 0.67
MCF_SOLID = 0.04
MCF_PASTURE = 0.015
MCF_NOCRUST = 0.27
MCF_CRUST = 0.17
HEAD = 10.0
CRUST_REDUCTION = 0.40
SOLID_REDUCTION = 0.25


def _params(**overrides):
    base = {
        "VS_dairy_canada": VS,
        "VS_beef_canada": 2.4,
        "B0_dairy_canada": B0,
        "B0_beef_canada": 0.19,
        "MCF_liquid_nocrust_cool": 0.17,
        "MCF_liquid_nocrust_temperate": MCF_NOCRUST,
        "MCF_liquid_crust_cool": 0.10,
        "MCF_liquid_crust_temperate": MCF_CRUST,
        "MCF_solid_storage_cool": 0.02,
        "MCF_solid_storage_temperate": MCF_SOLID,
        "MCF_pasture_cool": MCF_PASTURE,
        "MCF_daily_spread_cool": 0.001,
        "CH4_M3_TO_KG": DENSITY,
        "cover_crust_reduction": CRUST_REDUCTION,
        "cover_solid_reduction": SOLID_REDUCTION,
    }
    base.update(overrides)
    return base


def _eq_10_23(head, vs, b0, mcf, remaining=1.0):
    return head * vs * 365.0 * b0 * DENSITY * mcf * remaining


def _base_inputs(**overrides):
    inputs = {
        "head": HEAD,
        "animal_type": "dairy",
        "climate_zone": "temperate",
        "systems": {"liquid_nocrust": 1.0},
        "cover_type": "none",
        "VS_kg_day": VS,
    }
    inputs.update(overrides)
    return inputs


def _holos(inputs):
    return {**inputs, "forks": {"HOLOS.CH4.cover_reduction": "holos_as_coded"}}


def test_cover_fork_registered():
    fork = get_holos_fork_registry().get("HOLOS.CH4.cover_reduction")
    assert fork.default == "source_correct"
    assert fork.label == "holos_as_coded"
    assert fork.issue_ref == "CE-14"
    assert "holos_as_coded" in fork.options
    assert "1 - reduction" in fork.description or "1 − reduction" in fork.description or "remaining = 1" in fork.description


def test_process_equation_multiplies_by_one_minus_reduction():
    process = manure_ch4_process()
    equation = process.rate_equation_for("holos_as_coded")
    assert "(1.0 - cover_reduction)" in equation
    assert equation.count("cover_reduction") == 1


def test_default_manure_ch4_matches_ipcc_10_23():
    module = HolosManureCH4()
    result = module.compute(
        {
            "head": HEAD,
            "animal_type": "dairy",
            "climate_zone": "temperate",
            "systems": {"solid_storage": 0.7, "pasture": 0.3},
        },
        _params(),
    )
    mcf = 0.7 * MCF_SOLID + 0.3 * MCF_PASTURE
    assert result["MCF_weighted"] == pytest.approx(mcf)
    assert result["cover_remaining_used"] == 1.0
    assert result["cover_reduction_fraction"] == 0.0
    assert result["CH4"] == pytest.approx(_eq_10_23(HEAD, VS, B0, mcf))


def test_uncovered_is_1x_base():
    module = HolosManureCH4()
    params = _params()
    inputs = _base_inputs()
    default = module.compute(inputs, params)
    holos = module.compute(_holos(inputs), params)
    assert default["CH4"] == pytest.approx(holos["CH4"])
    assert default["cover_remaining_used"] == holos["cover_remaining_used"] == 1.0
    assert holos["cover_reduction_fraction"] == 0.0
    assert holos["CH4"] / default["CH4"] == pytest.approx(1.0)


def test_crust_is_0_6x_uncovered_base():
    module = HolosManureCH4()
    params = _params()
    base = module.compute(_base_inputs(), params)
    holos = module.compute(_holos(_base_inputs(cover_type="natural_crust")), params)
    assert holos["cover_reduction_fraction"] == pytest.approx(CRUST_REDUCTION)
    assert holos["cover_remaining_used"] == pytest.approx(0.60)
    assert holos["MCF_weighted"] == pytest.approx(MCF_NOCRUST)
    assert holos["CH4"] == pytest.approx(_eq_10_23(HEAD, VS, B0, MCF_NOCRUST, 0.60))
    assert holos["CH4"] / base["CH4"] == pytest.approx(0.60)


def test_solid_cover_is_0_75x_uncovered_base():
    module = HolosManureCH4()
    params = _params()
    base = module.compute(_base_inputs(), params)
    holos = module.compute(_holos(_base_inputs(cover_type="solid_cover")), params)
    assert holos["cover_reduction_fraction"] == pytest.approx(SOLID_REDUCTION)
    assert holos["cover_remaining_used"] == pytest.approx(0.75)
    assert holos["CH4"] == pytest.approx(_eq_10_23(HEAD, VS, B0, MCF_NOCRUST, 0.75))
    assert holos["CH4"] / base["CH4"] == pytest.approx(0.75)


def test_other_cover_does_not_get_solid_cover_reduction():
    """0.25 applies only to solid_cover, not to all non-crust covers."""
    module = HolosManureCH4()
    params = _params()
    base = module.compute(_base_inputs(), params)
    holos = module.compute(_holos(_base_inputs(cover_type="other_cover")), params)
    assert holos["cover_reduction_fraction"] == 0.0
    assert holos["cover_remaining_used"] == 1.0
    assert holos["CH4"] / base["CH4"] == pytest.approx(1.0)


def test_no_double_count_of_ipcc_crust_mcf():
    """Covered Holos path must not stack IPCC with-crust MCF on (1 - 0.40)."""
    module = HolosManureCH4()
    params = _params()
    base = module.compute(_base_inputs(), params)
    holos_nocrust = module.compute(_holos(_base_inputs(cover_type="natural_crust")), params)
    holos_crust_system = module.compute(
        _holos(_base_inputs(cover_type="natural_crust", systems={"liquid_crust": 1.0})),
        params,
    )
    source_crust = module.compute(_base_inputs(systems={"liquid_crust": 1.0}), params)

    assert holos_nocrust["CH4"] == pytest.approx(holos_crust_system["CH4"])
    assert holos_crust_system["MCF_weighted"] == pytest.approx(MCF_NOCRUST)
    assert holos_crust_system["CH4"] / base["CH4"] == pytest.approx(0.60)
    # Double-count would be crust MCF * 0.60, not nocrust MCF * 0.60.
    double_count = source_crust["CH4"] * 0.60
    assert holos_crust_system["CH4"] != pytest.approx(double_count)
    assert source_crust["CH4"] / base["CH4"] == pytest.approx(MCF_CRUST / MCF_NOCRUST)
    assert source_crust["cover_remaining_used"] == 1.0
