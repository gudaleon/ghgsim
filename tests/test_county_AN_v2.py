import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_county_AN_v2 as cc  # noqa: E402
import run_apsim_county_AN_v2 as rc  # noqa: E402


def test_cap_sat_caps_only_above_porosity_limit():
    node = {"Children": [{"$type": "Models.Soils.Physical, Models", "SAT": [0.53, 0.40], "BD": [1.27, 1.50]}]}
    caps = rc.cap_sat(node)
    assert node["Children"][0]["SAT"] == [0.520, 0.40]
    assert len(caps) == 1 and caps[0]["SAT_from_source"] == 0.53


def test_hargreaves_may_oct_plausible_and_ignores_other_months():
    days = {f"2001{m:02d}{d:02d}": None for m in range(1, 13) for d in range(1, 29)}
    par = {"PRECTOTCORR": {k: 2.0 for k in days}, "T2M_MAX": {k: 25.0 for k in days}, "T2M_MIN": {k: 13.0 for k in days}}
    p, pe = cc.hargreaves_may_oct({"properties": {"parameter": par}}, 42.0)
    assert p == 2.0 * 28 * 6
    assert 400 < pe < 900