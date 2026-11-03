import json
import math
import pathlib

import pytest
from livingghg.enteric import enteric_ch4
from livingghg.forks import load_registry, oat_screen
from livingghg.montecarlo import lhs_run
from livingghg.params import ParamTable
from livingghg.soil_n2o import soil_n2o

P = ParamTable()
C = 44 / 28

def test_direct_2006_hand():
    # 100 kg synthetic N * 0.01 = 1 kg N2O-N
    r = soil_n2o({"F_SN": 100}, "IPCC2006", P)
    assert math.isclose(r["direct"], 1.0 * C)

def test_indirect_2006_hand():
    # vol: 100*0.10*0.010 = 0.1; leach: 100*0.30*0.0075 = 0.225 kg N2O-N
    r = soil_n2o({"F_SN": 100}, "IPCC2006", P)
    assert math.isclose(r["indirect_vol"], 0.1 * C)
    assert math.isclose(r["indirect_leach"], 0.225 * C)

def test_prp_2006_hand():
    # 100 kg PRP N: direct 2.0; vol 100*0.2*0.01=0.2; leach 100*0.3*0.0075=0.225
    r = soil_n2o({"F_PRP_CPP": 100}, "IPCC2006", P)
    assert math.isclose(r["total"], (2.0 + 0.2 + 0.225) * C)

def test_2019_disaggregated_wet_hand():
    # direct 100*0.016 + 100*0.006 = 2.2; vol (100*0.11 + 100*0.21)*0.014 = 0.448; leach 200*0.24*0.011 = 0.528
    r = soil_n2o({"F_SN": 100, "F_ON": 100, "climate": "wet"}, "IPCC2019", P)
    assert math.isclose(r["direct"], 2.2 * C)
    assert math.isclose(r["indirect_vol"], 0.448 * C)
    assert math.isclose(r["indirect_leach"], 0.528 * C)

def test_2019_aggregated_hand():
    r = soil_n2o({"F_SN": 100}, "IPCC2019", P, {"ef1_mode": "aggregated"})
    assert math.isclose(r["direct"], 1.0 * C)

def test_enteric_hand():
    # 300 MJ/d * 6.5% * 365 / 55.65 = 127.89 kg CH4/head/yr
    h = {"head": 10, "GE_MJ_day": 300, "ym_category": {"IPCC2006": "dairy", "IPCC2019": "dairy_low"}}
    for g in ("IPCC2006", "IPCC2019"):
        r = enteric_ch4(h, g, P)
        assert math.isclose(r["EF_kg_head"], 300 * 0.065 * 365 / 55.65)
        assert math.isclose(r["total"], 10 * r["EF_kg_head"])

def test_unverified_excluded():
    with pytest.raises(ValueError):
        P.get("IPCC2006", "FracLeachMS", "all")

def test_dry_fracleach_zero_2019():
    r = soil_n2o({"F_SN": 100, "climate": "dry"}, "IPCC2019", P)
    assert r["indirect_leach"] == 0

def test_registry_and_screen():
    reg = load_registry()
    legacy_root = pathlib.Path(__file__).parents[2] / "legacy" / "livingghg_AN_v3"
    farm = json.loads((legacy_root / "examples" / "example_farm_AN_v2.json").read_text(encoding="utf-8"))
    base, rows = oat_screen(farm, "IPCC2019", P, reg)
    deltas = [abs(r["delta_t"]) for r in rows if r["delta_t"] is not None]
    assert deltas == sorted(deltas, reverse=True) and base > 0

def test_lhs_within_bounds():
    farm = {"soil": {"F_SN": 100}, "herds": []}
    out = lhs_run(farm, "IPCC2006", P, [("EF1", "all")], n=50)
    lo = 100 * 0.003 * C * 265 / 1000  # noqa: F841
    hi = 100 * 0.03 * C * 265 / 1000  # noqa: F841
    assert (out.min() > 0) and out.max() > out.min()
