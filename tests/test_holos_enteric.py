"""Unit tests: Holos enteric CH4 default vs holos_as_coded forks."""

import pytest

from ghgsim.modules.holos.enteric import HolosEnteric
from ghgsim.modules.holos.forks import get_holos_fork_registry, resolve_option

CH4_ENERGY = 55.65

# IPCC 2006 Eq 10.21 annual, dairy Ym 6.5% from Table 10.12 p. 10.30 (VERIFIED).
GE = 300.0
YM_ECCC = 5.6
YM_IPCC = 6.5


def _params(**overrides):
    base = {
        "GE_dairy_canada": 380.0,
        "Ym_dairy_canada": YM_ECCC,
        "Ym_dairy_ipcc2006": YM_IPCC,
        "GE_beef_high_grain": 200.0,
        "GE_beef_medium": 220.0,
        "GE_beef_low_grain": 180.0,
        "Ym_beef_high_grain": 3.0,
        "Ym_beef_medium": 6.3,
        "Ym_beef_low_grain": 7.0,
        "CH4_ENERGY": CH4_ENERGY,
    }
    base.update(overrides)
    return base


def _eq_10_21(ge, ym_pct):
    return ge * (ym_pct / 100.0) * 365.0 / CH4_ENERGY


def test_enteric_forks_registered_with_holos_as_coded_label():
    registry = get_holos_fork_registry()
    ge_fork = registry.get("HOLOS.GE.digestibility")
    calf_fork = registry.get("HOLOS.ENTERIC.calf_zero")
    assert ge_fork.default == "source_correct"
    assert "holos_as_coded" in ge_fork.options
    assert ge_fork.label == "holos_as_coded"
    assert calf_fork.issue_ref == "CE-06"
    assert resolve_option("HOLOS.GE.digestibility", {}) == "source_correct"


def test_default_enteric_matches_ipcc_10_21():
    module = HolosEnteric()
    result = module.compute(
        {"head": 10.0, "animal_type": "dairy", "GE_MJ_day": GE},
        _params(),
    )
    expected = 10.0 * _eq_10_21(GE, YM_ECCC)
    assert result["CH4_total"] == pytest.approx(expected)
    assert result["Ym_used"] == YM_ECCC


def test_dairy_ym_fork_changes_only_ym():
    module = HolosEnteric()
    inputs_default = {"head": 1.0, "animal_type": "dairy", "GE_MJ_day": GE}
    inputs_ipcc = {
        "head": 1.0,
        "animal_type": "dairy",
        "GE_MJ_day": GE,
        "forks": {"HOLOS.YM.dairy": "ipcc2006_table_10_12"},
    }
    default = module.compute(inputs_default, _params())
    ipcc = module.compute(inputs_ipcc, _params())
    assert default["GE_used"] == ipcc["GE_used"] == GE
    assert default["Ym_used"] == YM_ECCC
    assert ipcc["Ym_used"] == YM_IPCC
    assert ipcc["CH4_kg_head"] == pytest.approx(_eq_10_21(GE, YM_IPCC))
    assert default["CH4_kg_head"] / ipcc["CH4_kg_head"] == pytest.approx(YM_ECCC / YM_IPCC)
    assert default["CH4_kg_head"] != ipcc["CH4_kg_head"]


def test_calf_zero_fork_differs_only_for_calves():
    module = HolosEnteric()
    adult = {
        "head": 1.0,
        "animal_type": "dairy",
        "animal_class": "adult",
        "GE_MJ_day": GE,
    }
    calf = {
        "head": 1.0,
        "animal_type": "dairy",
        "animal_class": "calf",
        "GE_MJ_day": GE,
    }
    forks = {"forks": {"HOLOS.ENTERIC.calf_zero": "holos_as_coded"}}
    params = _params()

    adult_default = module.compute(adult, params)
    adult_fork = module.compute({**adult, **forks}, params)
    calf_default = module.compute(calf, params)
    calf_fork = module.compute({**calf, **forks}, params)

    assert adult_default["CH4_kg_head"] == pytest.approx(adult_fork["CH4_kg_head"])
    assert calf_default["CH4_kg_head"] == pytest.approx(_eq_10_21(GE, YM_ECCC))
    assert calf_fork["CH4_kg_head"] == 0.0
    assert calf_default["CH4_kg_head"] != calf_fork["CH4_kg_head"]


def test_ge_tdn_fork_differs_only_when_tdn_ne_de():
    module = HolosEnteric()
    ne_inputs = {
        "head": 1.0,
        "animal_type": "dairy",
        "NE_m": 40.0,
        "NE_a": 0.0,
        "NE_l": 60.0,
        "NE_work": 0.0,
        "NE_p": 0.0,
        "NE_g": 0.0,
        "RE_m": 0.5,
        "RE_g": 0.4,
        "DE_percent": 70.0,
        "TDN_percent": 65.0,
    }
    params = _params()
    default = module.compute(ne_inputs, params)
    holos = module.compute(
        {**ne_inputs, "forks": {"HOLOS.GE.digestibility": "holos_as_coded"}},
        params,
    )
    ge_de = ((40.0 + 60.0) / 0.5) / 0.70
    ge_tdn = ((40.0 + 60.0) / 0.5) / 0.65
    assert default["GE_used"] == pytest.approx(ge_de)
    assert holos["GE_used"] == pytest.approx(ge_tdn)
    assert default["CH4_kg_head"] == pytest.approx(_eq_10_21(ge_de, YM_ECCC))
    assert holos["CH4_kg_head"] == pytest.approx(_eq_10_21(ge_tdn, YM_ECCC))
    assert default["CH4_kg_head"] != holos["CH4_kg_head"]

    same = {**ne_inputs, "TDN_percent": 70.0}
    default_same = module.compute(same, params)
    holos_same = module.compute(
        {**same, "forks": {"HOLOS.GE.digestibility": "holos_as_coded"}},
        params,
    )
    assert default_same["CH4_kg_head"] == pytest.approx(holos_same["CH4_kg_head"])


def test_ge_tdn_fork_inactive_when_ge_override_supplied():
    module = HolosEnteric()
    inputs = {
        "head": 1.0,
        "animal_type": "dairy",
        "GE_MJ_day": GE,
        "DE_percent": 70.0,
        "TDN_percent": 50.0,
        "forks": {"HOLOS.GE.digestibility": "holos_as_coded"},
    }
    result = module.compute(inputs, _params())
    assert result["GE_used"] == GE
    assert result["CH4_kg_head"] == pytest.approx(_eq_10_21(GE, YM_ECCC))
