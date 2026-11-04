"""County annual climate -> IPCC zone -> 2019 manure MCF (AN v1)."""
import csv

import pytest

from ghgsim.modules.county_climate_annual import COUNTY_CLIMATE_ANNUAL_FILE, county_climate_annual
from ghgsim.modules.ipcc2019.manure import IPCC2019Manure, climate_zone_2019
from test_manure_2019_upgrade_AN_v1 import BASE, P19

ROWS = list(csv.DictReader(open(COUNTY_CLIMATE_ANNUAL_FILE, encoding="utf-8")))


def test_file_shape_and_zone_rule():
    assert len(ROWS) == 3142
    assert len({r["fips"] for r in ROWS}) == 3142
    for r in ROWS:
        assert r["period"] == "1991-2020"
        t, pr = float(r["mean_annual_temp_c"]), float(r["annual_p_over_pe"])
        if min(abs(t - b) for b in (0, 10, 18)) < 0.006 or abs(pr - 1) < 0.0006:
            continue  # zone computed from unrounded values; rounded CSV values sit on a boundary
        assert (climate_zone_2019(t, pr) or "") == r["ipcc_zone"]
        assert abs(float(r["annual_precip_mm"]) / float(r["annual_pe_hargreaves_mm"]) - float(r["annual_p_over_pe"])) < 2e-3


def test_lookup_values():
    c = county_climate_annual("50007")  # Chittenden VT
    assert c["ipcc_zone"] == "cool_temperate_moist"
    assert c["mean_annual_temp_c"] == pytest.approx(6.92)
    assert county_climate_annual(6019)["ipcc_zone"] == "warm_temperate_dry"  # Fresno, int FIPS ok
    assert county_climate_annual("99999") is None
    with pytest.raises(ValueError):
        county_climate_annual("abc")


def _ch4(**kw):
    return IPCC2019Manure().compute({**BASE, "animal_type": "dairy", "systems": {"liquid_nocrust": 1.0},
                                     "storage_months": 12, **kw}, P19)


def test_county_fips_drives_mcf():
    vt = _ch4(county_fips="50007")
    assert vt["CH4"] == pytest.approx(_ch4(climate_zone_2019="cool_temperate_moist")["CH4"])
    assert "cool_temperate_moist" in vt["MCF_basis"]
    fresno = _ch4(county_fips="06019")
    assert fresno["CH4"] == pytest.approx(_ch4(climate_zone_2019="warm_temperate_dry")["CH4"])


def test_explicit_zone_wins_over_county():
    out = _ch4(county_fips="50007", climate_zone_2019="warm_temperate_moist")
    assert "warm_temperate_moist" in out["MCF_basis"]


def test_tropical_and_boreal_use_2019_columns():
    # AN_v9 params add Table 10.17 (Updated) boreal/tropical columns; zone from IPCC 2019 map (DECISIONS_AN_v4).
    from ghgsim.modules.county_climate_annual import county_zone_primary
    for fips in ("12086", "02090"):  # Miami-Dade, Fairbanks North Star
        z = county_zone_primary(fips)
        assert z.startswith(("tropical", "boreal"))
        out = _ch4(county_fips=fips)
        assert z in out["MCF_basis"]
        assert out["CH4"] == pytest.approx(_ch4(climate_zone_2019=z)["CH4"])


def test_polar_falls_back_to_2006():
    from ghgsim.modules.county_climate_annual import COUNTY_CLIMATE_ZONES_FILE
    polar = [r["fips"] for r in csv.DictReader(open(COUNTY_CLIMATE_ZONES_FILE, encoding="utf-8"))
             if r["zone_primary"].startswith("polar")]
    assert polar
    assert "IPCC2006" in _ch4(county_fips=polar[0])["MCF_basis"]


def test_unknown_county_raises():
    with pytest.raises(KeyError):
        _ch4(county_fips="99999")
