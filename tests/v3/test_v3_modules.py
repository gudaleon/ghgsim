import numpy as np
import pandas as pd
import pytest
from livingghg import gapfill
from livingghg.crop_residue import f_cr
from livingghg.enteric import enteric_ch4
from livingghg.params import ParamTable


def test_class_range_and_finest():
    assert gapfill.class_range("INVENTORY OF COWS: (1 TO 9 HEAD)") == (1, 9)
    assert gapfill.class_range("INVENTORY OF COWS: (500 OR MORE HEAD)") == (500, np.inf)
    labs = ["X: (1 TO 9 HEAD)", "X: (500 TO 999 HEAD)", "X: (500 OR MORE HEAD)", "X: (1,000 OR MORE HEAD)"]
    assert set(gapfill.finest_classes(labs)) == {"X: (1 TO 9 HEAD)", "X: (500 TO 999 HEAD)", "X: (1,000 OR MORE HEAD)"}
    assert gapfill.class_midpoint(1000, np.inf) == 1500

def _toy():
    r = []
    def add(agg, cty, dom, cat, kind, v):
        r.append(dict(STATE_ALPHA="ZZ", STATE_FIPS_CODE="99", COUNTY_CODE=cty, COUNTY_NAME=f"C{cty}", AGG_LEVEL_DESC=agg,
                      DOMAIN_DESC=dom, DOMAINCAT_DESC=cat, VALUE=v,
                      SHORT_DESC="CATTLE, COWS, MILK - " + ("OPERATIONS WITH INVENTORY" if kind == "ops" else "INVENTORY")))
    A, B = "INVENTORY OF MILK COWS: (1 TO 9 HEAD)", "INVENTORY OF MILK COWS: (10 TO 99 HEAD)"
    add("STATE", None, "TOTAL", None, "inv", "1,000")
    add("STATE", None, "SIZE", A, "ops", "10"); add("STATE", None, "SIZE", A, "inv", "50")
    add("STATE", None, "SIZE", B, "ops", "20"); add("STATE", None, "SIZE", B, "inv", "950")
    add("COUNTY", "001", "TOTAL", None, "inv", "700"); add("COUNTY", "001", "TOTAL", None, "ops", "15")
    for c, opsA, opsB in (("002", "2", "1"), ("003", "1", "3")):
        add("COUNTY", c, "TOTAL", None, "inv", "(D)"); add("COUNTY", c, "TOTAL", None, "ops", str(int(opsA) + int(opsB)))
        add("COUNTY", c, "SIZE", A, "ops", opsA); add("COUNTY", c, "SIZE", A, "inv", "(D)")
        add("COUNTY", c, "SIZE", B, "ops", opsB); add("COUNTY", c, "SIZE", B, "inv", "(D)")
    return gapfill.prepare(pd.DataFrame(r))

def test_sizeclass_fill_hand_case():
    f, disc = gapfill.fill_state_sizeclass(_toy(), "ZZ", "milk")
    # residual 300; estimates: 002 = 2*5 + 1*47.5 = 57.5 ; 003 = 1*5 + 3*47.5 = 147.5
    e = f.set_index("fips")
    assert e.raw_estimate["99002"] == pytest.approx(57.5) and e.raw_estimate["99003"] == pytest.approx(147.5)
    assert e.filled_head.sum() == pytest.approx(300.0)
    assert e.filled_head["99002"] == pytest.approx(300 * 57.5 / 205)

def test_prior_census_takes_most_recent():
    w = pd.DataFrame(dict(STATE_ALPHA=["ZZ"] * 2, fips=["99002", "99003"], COUNTY_NAME=["a", "b"], animal=["milk"] * 2))
    p = pd.DataFrame(dict(YEAR=["2017", "2012", "2012"], AGG_LEVEL_DESC="COUNTY", STATE_FIPS_CODE="99",
                          COUNTY_CODE=["2", "2", "3"], SHORT_DESC="CATTLE, COWS, MILK - INVENTORY", VALUE=["(D)", "40", "(D)"]))
    o = gapfill.fill_prior_census(w, p).set_index("fips")
    assert o.filled_head["99002"] == 40 and o.fill_method["99002"].endswith("2012")
    assert np.isnan(o.filled_head["99003"]) and o.fill_method["99003"].endswith("none_found")

def test_crop_residue_maize_hand():
    p = dict(N_AG=0.006, N_BG=0.007, R_AG=1.0, RS=0.22, DRY=0.87)
    # 1 ha, 10,000 kg fresh: Crop=8700; AGDM=8700; AG N=52.2; BG=(17400)*0.22*0.007=26.796
    assert f_cr(1.0, 10000.0, p) == pytest.approx(52.2 + 26.796)
    assert f_cr(1.0, 10000.0, p, frac_remove=0.5) == pytest.approx(26.1 + 26.796)

def test_epa_ym_reproduces_epa_ef():
    P = ParamTable()
    h = dict(GE_MJ_day=401.2, Ym_pct=5.7, ym_category={"IPCC2006": "dairy", "IPCC2019": "dairy_medium"}, head=1)
    assert enteric_ch4(h, "IPCC2019", P)["EF_kg_head"] == pytest.approx(150.0, abs=0.1)   # EPA A-142 VT dairy 2022
    assert enteric_ch4(h, "IPCC2019", P, {"ym_source": "ipcc_default"})["EF_kg_head"] != pytest.approx(150.0, abs=0.1)

def test_assumptions_file_complete():
    import json
    import pathlib
    legacy_root = pathlib.Path(__file__).parents[2] / "legacy" / "livingghg_AN_v3"
    a = json.loads((legacy_root / "scripts" / "county_assumptions_AN_v3.json").read_text(encoding="utf-8"))
    assert len(a["states"]) == 50
    for s in a["states"].values():
        assert sum(s["dairy"]["manure"]["systems"].values()) == pytest.approx(1.0)
        assert s["provenance"]["status"].startswith("VERIFIED")
