"""Tests for scripts/build_county_p_pe_AN_v2.py (county May-Oct P and PE, v2)."""
import csv
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bpp", ROOT / "scripts" / "build_county_p_pe_AN_v2.py")
bpp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bpp)  # noqa: E702
DATA = ROOT / "data" / "county_p_pe_may_oct_AN_v2.csv"


def test_ra_fao56_example8():
    # FAO-56 Example 8: 20 deg S, 3 September (J=246) -> Ra = 32.2 MJ m-2 d-1
    assert bpp.ra_mj(-20.0, 246) == pytest.approx(32.2, abs=0.1)


def test_daylength_fao56_example9():
    # FAO-56 Example 9: 20 deg S, 3 September -> N = 11.7 h
    assert bpp.daylength_h(-20.0, 246) == pytest.approx(11.7, abs=0.1)


def test_hargreaves_zero_range_is_zero():
    assert bpp.hargreaves_month_mm(20.0, 20.0, 40.0, 7) == 0.0


def test_thornthwaite_cold_year_zero():
    assert bpp.thornthwaite_year_mm([-5.0] * 12, 45.0) == [0.0] * 12


def test_parse_climdiv_units_and_fips():
    # NCEI state 43 = Vermont (FIPS 50); county 007; element 01; 1.00 in -> 25.4 mm
    line = "43007011990" + "".join(f"{v:7.2f}" for v in [1.0] * 11 + [-9.99])
    out = bpp.parse_climdiv(line, "01")
    vals = out[("50007", 1990)]
    assert vals[0] == pytest.approx(25.4) and vals[11] is None
    t = bpp.parse_climdiv("43007271990" + "".join(f"{v:7.2f}" for v in [32.0] * 12), "27")
    assert t[("50007", 1990)][0] == pytest.approx(0.0)


def test_parse_rejects_wrong_element():
    with pytest.raises(ValueError):
        bpp.parse_climdiv("43007021990" + "   1.00" * 12, "01")


def test_state_map_complete():
    assert sorted(bpp.NCEI_TO_FIPS) == list(range(1, 51))
    assert len(set(bpp.NCEI_TO_FIPS.values())) == 50


@pytest.mark.skipif(not DATA.exists(), reason="data file not built")
def test_data_file_sane():
    rows = list(csv.DictReader(open(DATA, encoding="utf-8")))
    assert len(rows) > 3000
    for r in rows:
        p, h, t = (float(r[k]) for k in ("growing_season_precip_mm", "pe_hargreaves_mm", "pe_thornthwaite_mm"))
        assert 0 <= p < 4000 and 0 < h < 2000 and 0 <= t < 2000
        assert len(r["fips"]) == 5


def test_county_map_parses_dc(tmp_path):
    f = tmp_path / "c2d.txt"
    f.write_text("header line\n11001 18511 1804\n24510 18510 1806\n", encoding="utf-8")
    m = bpp.load_county_map(f)
    assert m == {"18511": "11001", "18510": "24510"}
    line = "18511011995" + "   1.00" * 12
    assert ("11001", 1995) in bpp.parse_climdiv(line, "01", m)


@pytest.mark.skipif(not DATA.exists(), reason="data file not built")
def test_v2_pe_default_is_hargreaves_and_complete():
    rows = list(csv.DictReader(open(DATA, encoding="utf-8")))
    assert all(r["growing_season_pe_mm"] == r["pe_hargreaves_mm"] for r in rows)
    assert all(r["n_years"] == "30" and r["period"] == "1991-2020" for r in rows)
    assert any(r["fips"] == "11001" for r in rows)
