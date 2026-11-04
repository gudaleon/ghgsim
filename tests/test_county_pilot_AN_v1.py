import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_county_pilot_AN_v1 as cp  # noqa: E402


def test_spearman_perfect_and_ties():
    assert abs(cp.spearman([1, 2, 3], [10, 20, 30]) - 1) < 1e-12
    assert abs(cp.spearman([1, 2, 3], [3, 2, 1]) + 1) < 1e-12
    assert cp.ranks([5, 5, 1]) == [2.5, 2.5, 1.0]


def test_top_share_and_efs():
    assert cp.top_share([1] * 9 + [11]) == 11 / 20
    assert cp.ipcc_ef("cool_temperate_moist", "2019") == 0.016
    assert cp.ipcc_ef("warm_temperate_dry", "2019") == 0.005
    assert cp.ipcc_ef("warm_temperate_dry", "2006") == 0.01
    assert abs(cp.holos_base_ef(500, 400) - 2.718281828 ** (0.00558 * 500 - 7.7)) < 1e-9
    assert abs(cp.holos_base_ef(300, 600) - 2.718281828 ** (0.00558 * 300 - 7.7)) < 1e-9
    assert cp.holos_base_ef(300, 600, 1.0) == cp.holos_base_ef(600, 300)