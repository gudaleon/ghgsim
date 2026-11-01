"""Unit tests: Holos manure CH4 default vs CE-14 holos_as_coded cover fork."""

import pytest

from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.modules.holos.manure_ch4 import HolosManureCH4

VS = 5.4
B0 = 0.24
DENSITY = 0.67
MCF_SOLID = 0.04
MCF_PASTURE = 0.015
HEAD = 10.0


def _params(**overrides):
    base = {
        "VS_dairy_canada": VS,
        "VS_beef_canada": 2.4,
        "B0_dairy_canada": B0,
        "B0_beef_canada": 0.19,
        "MCF_liquid_nocrust_cool": 0.17,
        "MCF_liquid_nocrust_temperate": 0.27,
        "MCF_liquid_crust_cool": 0.10,
        "MCF_liquid_crust_temperate": 0.17,
        "MCF_solid_storage_cool": 0.02,
        "MCF_solid_storage_temperate": MCF_SOLID,
        "MCF_pasture_cool": MCF_PASTURE,
        "MCF_daily_spread_cool": 0.001,
        "CH4_M3_TO_KG": DENSITY,
        "cover_crust_factor": 0.4,
        "cover_other_factor": 0.25,
    }
    base.update(overrides)
    return base


def _eq_10_23(head, vs, b0, mcf, reduction=1.0):
    return head * vs * 365.0 * b0 * DENSITY * mcf * reduction


def test_cover_fork_registered():
    fork = get_holos_fork_registry().get("HOLOS.CH4.cover_reduction")
    assert fork.default == "source_correct"
    assert fork.label == "holos_as_coded"
    assert fork.issue_ref == "CE-14"
    assert "holos_as_coded" in fork.options


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
    assert result["cover_reduction_used"] == 1.0
    assert result["CH4"] == pytest.approx(_eq_10_23(HEAD, VS, B0, mcf))


def test_cover_fork_matches_default_when_uncovered():
    module = HolosManureCH4()
    inputs = {
        "head": HEAD,
        "animal_type": "dairy",
        "climate_zone": "temperate",
        "systems": {"liquid_nocrust": 1.0},
        "cover_type": "none",
        "VS_kg_day": VS,
    }
    params = _params()
    default = module.compute(inputs, params)
    holos = module.compute(
        {**inputs, "forks": {"HOLOS.CH4.cover_reduction": "holos_as_coded"}},
        params,
    )
    assert default["CH4"] == pytest.approx(holos["CH4"])
    assert default["cover_reduction_used"] == holos["cover_reduction_used"] == 1.0


def test_cover_fork_applies_crust_and_other_factors():
    module = HolosManureCH4()
    params = _params()
    crust = {
        "head": HEAD,
        "animal_type": "dairy",
        "climate_zone": "temperate",
        "systems": {"liquid_crust": 1.0},
        "cover_type": "natural_crust",
        "VS_kg_day": VS,
    }
    default = module.compute(crust, params)
    holos = module.compute(
        {**crust, "forks": {"HOLOS.CH4.cover_reduction": "holos_as_coded"}},
        params,
    )
    mcf = 0.17
    assert default["CH4"] == pytest.approx(_eq_10_23(HEAD, VS, B0, mcf, 1.0))
    assert holos["CH4"] == pytest.approx(_eq_10_23(HEAD, VS, B0, mcf, 0.4))
    assert holos["cover_reduction_used"] == 0.4
    assert default["CH4"] != holos["CH4"]
    assert holos["CH4"] / default["CH4"] == pytest.approx(0.4)

    other = {**crust, "cover_type": "other_cover", "systems": {"liquid_nocrust": 1.0}}
    default_other = module.compute(other, params)
    holos_other = module.compute(
        {**other, "forks": {"HOLOS.CH4.cover_reduction": "holos_as_coded"}},
        params,
    )
    assert holos_other["cover_reduction_used"] == 0.25
    assert holos_other["CH4"] / default_other["CH4"] == pytest.approx(0.25)
    assert default_other["CH4"] != holos_other["CH4"]
