import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import power_fill_AN_v1 as pf  # noqa: E402


def _p(vals):
    return {"properties": {"parameter": {"X": {f"2000010{i + 1}": v for i, v in enumerate(vals)}}}}


def test_interior_fill_is_linear():
    out, fills = pf.fill_power(_p([1.0, -999, -999, 4.0]))
    s = out["properties"]["parameter"]["X"]
    assert [s[k] for k in sorted(s)] == [1.0, 2.0, 3.0, 4.0]
    assert len(fills) == 2


def test_edges_take_nearest_and_input_untouched():
    p = _p([-999, 5.0, -999])
    out, _ = pf.fill_power(p)
    s = out["properties"]["parameter"]["X"]
    assert [s[k] for k in sorted(s)] == [5.0, 5.0, 5.0]
    assert p["properties"]["parameter"]["X"]["20000101"] == -999