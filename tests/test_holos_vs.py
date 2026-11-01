"""Unit tests: Holos VS default vs holos_as_coded TDN, UE, and calf forks."""

import math

import pytest

from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.modules.holos.vs import HolosVolatileSolids

GE = 300.0
ASH = 8.0
GE_PER_KG = 18.45
CALF_COEFF = 0.0093


def _params():
    return {"GE_PER_KG_DM": GE_PER_KG, "calf_vs_coeff": CALF_COEFF}


def _ipcc_vs(ge, digest_pct, ue, ash=ASH):
    return (ge * (1.0 - digest_pct / 100.0) + ue * ge) * (1.0 - ash / 100.0) / GE_PER_KG


def test_vs_forks_registered():
    registry = get_holos_fork_registry()
    tdn = registry.get("HOLOS.VS.digestibility")
    ue = registry.get("HOLOS.VS.urinary_energy")
    calf = registry.get("HOLOS.VS.calf_coeff")
    assert tdn.default == ue.default == calf.default == "source_correct"
    assert tdn.label == ue.label == calf.label == "holos_as_coded"
    assert "holos_as_coded" in tdn.options
    assert ue.issue_ref == "AUDIT-VS-UE"
    assert calf.issue_ref == "CE-07"


def test_default_vs_matches_ipcc_10_24_typical_ue():
    module = HolosVolatileSolids()
    result = module.compute(
        {"GE_MJ_day": GE, "DE_percent": 70.0, "ASH_percent": ASH, "forage_percent": 80.0},
        _params(),
    )
    assert result["UE_used"] == pytest.approx(0.04)
    assert result["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 70.0, 0.04))


def test_default_vs_uses_ue_002_when_de_above_80():
    module = HolosVolatileSolids()
    result = module.compute(
        {"GE_MJ_day": GE, "DE_percent": 85.0, "ASH_percent": ASH, "forage_percent": 80.0},
        _params(),
    )
    assert result["UE_used"] == pytest.approx(0.02)
    assert result["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 85.0, 0.02))


def test_tdn_fork_differs_only_when_tdn_ne_de():
    module = HolosVolatileSolids()
    shared = {
        "GE_MJ_day": GE,
        "DE_percent": 70.0,
        "TDN_percent": 65.0,
        "ASH_percent": ASH,
        "forage_percent": 80.0,
    }
    default = module.compute(shared, _params())
    holos = module.compute(
        {**shared, "forks": {"HOLOS.VS.digestibility": "holos_as_coded"}},
        _params(),
    )
    assert default["UE_used"] == holos["UE_used"] == pytest.approx(0.04)
    assert default["digestibility_used"] == 70.0
    assert holos["digestibility_used"] == 65.0
    assert default["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 70.0, 0.04))
    assert holos["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 65.0, 0.04))
    assert default["VS_kg_day"] != holos["VS_kg_day"]

    same = {**shared, "TDN_percent": 70.0}
    default_same = module.compute(same, _params())
    holos_same = module.compute(
        {**same, "forks": {"HOLOS.VS.digestibility": "holos_as_coded"}},
        _params(),
    )
    assert default_same["VS_kg_day"] == pytest.approx(holos_same["VS_kg_day"])


def test_ue_fork_differs_only_when_grain_and_de_switches_disagree():
    """
    IPCC UE uses DE% > ~80. Holos UE uses grain% >= 85.
    The 0.02/0.04 pairing is the same direction; values differ only when
    the two switch criteria disagree.
    """
    module = HolosVolatileSolids()
    params = _params()

    # Both typical UE=0.04: moderate DE, high forage (low grain)
    agree_typical = {
        "GE_MJ_day": GE,
        "DE_percent": 70.0,
        "ASH_percent": ASH,
        "forage_percent": 90.0,
    }
    d0 = module.compute(agree_typical, params)
    h0 = module.compute(
        {**agree_typical, "forks": {"HOLOS.VS.urinary_energy": "holos_as_coded"}},
        params,
    )
    assert d0["UE_used"] == h0["UE_used"] == pytest.approx(0.04)
    assert d0["VS_kg_day"] == pytest.approx(h0["VS_kg_day"])

    # Both UE=0.02: high DE and high grain
    agree_high = {
        "GE_MJ_day": GE,
        "DE_percent": 85.0,
        "ASH_percent": ASH,
        "forage_percent": 10.0,
    }
    d1 = module.compute(agree_high, params)
    h1 = module.compute(
        {**agree_high, "forks": {"HOLOS.VS.urinary_energy": "holos_as_coded"}},
        params,
    )
    assert d1["UE_used"] == h1["UE_used"] == pytest.approx(0.02)
    assert d1["VS_kg_day"] == pytest.approx(h1["VS_kg_day"])

    # Disagree: high grain, moderate DE -> Holos 0.02, IPCC 0.04
    high_grain_mod_de = {
        "GE_MJ_day": GE,
        "DE_percent": 70.0,
        "ASH_percent": ASH,
        "forage_percent": 10.0,
    }
    d2 = module.compute(high_grain_mod_de, params)
    h2 = module.compute(
        {**high_grain_mod_de, "forks": {"HOLOS.VS.urinary_energy": "holos_as_coded"}},
        params,
    )
    assert d2["UE_used"] == pytest.approx(0.04)
    assert h2["UE_used"] == pytest.approx(0.02)
    assert d2["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 70.0, 0.04))
    assert h2["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 70.0, 0.02))
    assert d2["VS_kg_day"] != h2["VS_kg_day"]

    # Disagree: low grain, high DE -> Holos 0.04, IPCC 0.02
    low_grain_high_de = {
        "GE_MJ_day": GE,
        "DE_percent": 85.0,
        "ASH_percent": ASH,
        "forage_percent": 90.0,
    }
    d3 = module.compute(low_grain_high_de, params)
    h3 = module.compute(
        {**low_grain_high_de, "forks": {"HOLOS.VS.urinary_energy": "holos_as_coded"}},
        params,
    )
    assert d3["UE_used"] == pytest.approx(0.02)
    assert h3["UE_used"] == pytest.approx(0.04)
    assert d3["VS_kg_day"] != h3["VS_kg_day"]


def test_calf_coeff_fork_differs_from_eq_10_24():
    module = HolosVolatileSolids()
    weight = 86.0
    calf = {
        "GE_MJ_day": 50.0,
        "DE_percent": 80.0,
        "ASH_percent": ASH,
        "forage_percent": 100.0,
        "animal_class": "calf",
        "weight_kg": weight,
    }
    params = _params()
    default = module.compute(calf, params)
    holos = module.compute(
        {**calf, "forks": {"HOLOS.VS.calf_coeff": "holos_as_coded"}},
        params,
    )
    assert default["VS_kg_day"] == pytest.approx(_ipcc_vs(50.0, 80.0, 0.02))
    assert holos["VS_kg_day"] == pytest.approx(CALF_COEFF * weight)
    assert holos["VS_kg_day"] != default["VS_kg_day"]
    assert math.isnan(holos["UE_used"])

    adult = {**calf, "animal_class": "adult"}
    adult_default = module.compute(adult, params)
    adult_fork = module.compute(
        {**adult, "forks": {"HOLOS.VS.calf_coeff": "holos_as_coded"}},
        params,
    )
    assert adult_default["VS_kg_day"] == pytest.approx(adult_fork["VS_kg_day"])


def test_tdn_and_ue_forks_are_independent():
    module = HolosVolatileSolids()
    inputs = {
        "GE_MJ_day": GE,
        "DE_percent": 70.0,
        "TDN_percent": 65.0,
        "ASH_percent": ASH,
        "forage_percent": 10.0,
        "forks": {
            "HOLOS.VS.digestibility": "holos_as_coded",
            "HOLOS.VS.urinary_energy": "holos_as_coded",
        },
    }
    result = module.compute(inputs, _params())
    assert result["UE_used"] == pytest.approx(0.02)
    assert result["digestibility_used"] == 65.0
    assert result["VS_kg_day"] == pytest.approx(_ipcc_vs(GE, 65.0, 0.02))
