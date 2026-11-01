import math
from livingghg.params import ParamTable
from livingghg.manure import manure_emissions
P = ParamTable(); C = 44 / 28

def herd(systems, zone06="15C", zone19="cool_temperate_moist"):
    return {"head": 1, "manure": {"animal": "dairy", "region": "north_america", "systems": systems,
            "mcf_zone": {"IPCC2006": zone06, "IPCC2019": zone19}}}

def test_2006_dairy_solid_hand():
    nex = 0.44 * 604 / 1000 * 365            # Eq 10.30, Table 10.19 + 10A-4
    r = manure_emissions(herd({"solid_storage": 1.0}), "IPCC2006", P)
    assert math.isclose(r["Nex_kg_head"], nex)
    assert math.isclose(r["CH4"], 5.4 * 365 * 0.24 * 0.67 * 0.04)   # Eq 10.23
    assert math.isclose(r["N2O_direct"], nex * 0.005 * C)            # Eq 10.25, Table 10.21
    assert math.isclose(r["N2O_vol"], nex * 0.30 * 0.010 * C)        # Table 10.22, EF4 2006
    assert r["N2O_leach"] == 0

def test_2019_dairy_liquid_hand():
    h = herd({"liquid_nocrust": 1.0}); h["manure"]["TAM_kg"] = 600; h["manure"]["VS_kg_day"] = 5.0
    nex = 0.59 * 600 / 1000 * 365
    r = manure_emissions(h, "IPCC2019", P, soil_climate="wet")
    assert math.isclose(r["CH4"], 5.0 * 365 * 0.24 * 0.67 * 0.21)    # MCF 6-month CTM
    assert r["N2O_direct"] == 0
    assert math.isclose(r["N2O_vol"], nex * 0.48 * 0.014 * C)        # EF4 wet
    r12 = manure_emissions(h, "IPCC2019", P, {"liquid_retention": "12mo"})
    assert math.isclose(r12["CH4"], 5.0 * 365 * 0.24 * 0.67 * 0.31)

def test_2019_dry_lot_leach_hand():
    h = herd({"dry_lot": 1.0}); h["manure"].update(TAM_kg=600, VS_kg_day=5.0)
    nex = 0.59 * 600 / 1000 * 365
    r = manure_emissions(h, "IPCC2019", P, soil_climate="wet")
    assert math.isclose(r["N2O_direct"], nex * 0.02 * C)
    assert math.isclose(r["N2O_leach"], nex * 0.035 * 0.011 * C)
    assert math.isclose(r["CH4"], 5.0 * 365 * 0.24 * 0.67 * 0.01)    # dry lot, cool

def test_pasture_routes_to_prp():
    h = {"head": 1, "manure": {"animal": "other_cattle", "region": "north_america", "systems": {"pasture": 1.0},
         "mcf_zone": {"IPCC2006": "15C", "IPCC2019": "cool_temperate_moist"}}}
    r = manure_emissions(h, "IPCC2006", P)
    nex = 0.31 * 389 / 1000 * 365
    assert math.isclose(r["N_PRP_kg"], nex) and r["N2O_total"] == 0
    assert math.isclose(r["CH4"], 2.4 * 365 * 0.19 * 0.67 * 0.015)
