import pytest, json, pathlib
SALib = pytest.importorskip("SALib")
from livingghg.params import ParamTable
from livingghg.forks import load_registry
from livingghg.sobol import sobol_indices

def test_sobol_tiny():
    legacy_root = pathlib.Path(__file__).parents[2] / "legacy" / "livingghg_AN_v3"
    farm = json.loads((legacy_root / "examples" / "example_farm_AN_v2.json").read_text())
    names, S1, ST, Y = sobol_indices(farm, "IPCC2019", ParamTable(), [("EF5", "all"), ("Ym", "dairy_medium")],
                                     load_registry(), ["F009"], n=8)
    assert len(names) == 3 and len(Y) == 8 * (3 + 2)
