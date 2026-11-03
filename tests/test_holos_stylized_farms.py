"""Sanity checks for Phase 3b stylized farms and measured fork deltas."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data" / "stylized_farms_AN_v2.yaml"
CSV_PATH = ROOT / "data" / "holos_fork_deltas_stylized_AN_v2.csv"
COMMAND = "python3 scripts/measure_holos_forks_stylized_AN_v2.py"

ZERO_ON_COUNTY = {
    "HOLOS.GE.digestibility",
    "HOLOS.ENTERIC.calf_zero",
    "HOLOS.VS.digestibility",
    "HOLOS.VS.urinary_energy",
    "HOLOS.VS.calf_coeff",
    "HOLOS.CH4.cover_reduction",
    "HOLOS.NEX.calf_nrate",
}


@pytest.fixture(scope="module")
def spec():
    with YAML_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture(scope="module")
def deltas():
    if not CSV_PATH.exists():
        pytest.skip("stylized measurement CSV not generated yet")
    return pd.read_csv(CSV_PATH)


def test_yaml_has_dairy_classes_and_beef_cow_calf(spec):
    classes = spec["animal_classes"]
    assert classes["dairy_cow"]["animal_class"] == "adult"
    assert classes["dairy_heifer"]["animal_type"] == "dairy"
    assert classes["dairy_calf"]["animal_class"] == "calf"
    assert classes["beef_cow"]["animal_type"] == "beef"
    assert classes["beef_calf"]["animal_class"] == "calf"
    for name in ("dairy_cow", "dairy_heifer", "dairy_calf", "beef_cow", "beef_calf"):
        assert classes[name]["head"]["status"] == "ILLUSTRATIVE"


def test_yaml_diets_give_tdn_and_de_with_sources(spec):
    for diet_id, diet in spec["diets"].items():
        assert diet["DE_percent"]["value"] != diet["TDN_percent"]["value"], diet_id
        assert "Table" in diet["DE_percent"]["source"] or "A-" in diet["DE_percent"]["source"]
        assert "Table" in diet["TDN_percent"]["source"]
        assert diet["pairing"] == "ILLUSTRATIVE"


def test_high_grain_crosses_implemented_ue_switches(spec):
    diet = spec["diets"]["dairy_high_grain"]
    de = float(diet["DE_percent"]["value"])
    grain = float(diet["grain_percent"]["value"])
    assert de >= 80.0
    assert grain < 85.0


def test_each_farm_type_has_uncovered_and_covered(spec):
    dairy = [f for f in spec["farms"] if f["farm_type"] == "dairy"]
    beef = [f for f in spec["farms"] if f["farm_type"] == "beef_cowcalf"]
    assert any(f["manure_id"] == "liquid_uncovered" for f in dairy)
    assert any(f["manure_id"].startswith("liquid_covered") for f in dairy)
    assert any(f["manure_id"] == "liquid_uncovered" for f in beef)
    assert any(f["manure_id"].startswith("liquid_covered") for f in beef)
    dairy_forage = next(f for f in dairy if f["id"] == "dairy_forage_uncovered")
    assert set(dairy_forage["herds"]) == {"dairy_cow", "dairy_heifer", "dairy_calf"}
    beef_unc = next(f for f in beef if f["id"] == "beef_cowcalf_uncovered")
    assert set(beef_unc["herds"]) == {"beef_cow", "beef_calf"}


def test_measurement_csv_command_and_forks_fire(deltas):
    assert deltas["command"].nunique() == 1
    assert deltas["command"].iloc[0] == COMMAND
    assert (deltas["evidence"] == "MEASURED").all()
    assert "COMBINED" in set(deltas["fork_id"])
    for fork_id in ZERO_ON_COUNTY | {"HOLOS.YM.dairy"}:
        sub = deltas[deltas["fork_id"] == fork_id]
        fired = (
            sub["delta_CH4_kg"].abs().max() > 1e-6
            or sub["delta_N2O_kg"].abs().max() > 1e-6
            or sub["delta_CO2e_t"].abs().max() > 1e-6
        )
        assert fired, f"{fork_id} did not fire on any stylized farm"


def test_ue_fork_fires_only_on_high_grain(deltas):
    ue = deltas[deltas["fork_id"] == "HOLOS.VS.urinary_energy"]
    high = ue[ue["diet_id"] == "dairy_high_grain"]
    forage = ue[ue["diet_id"] != "dairy_high_grain"]
    assert (high["delta_CH4_kg"].abs() > 1.0).all()
    assert (forage["delta_CH4_kg"].abs() < 1e-6).all()


def test_cover_fork_fires_only_when_covered(deltas):
    cover = deltas[deltas["fork_id"] == "HOLOS.CH4.cover_reduction"]
    covered = cover[cover["manure_id"].str.startswith("liquid_covered")]
    uncovered = cover[cover["manure_id"] == "liquid_uncovered"]
    assert (covered["delta_CH4_kg"] < -1.0).all()
    assert (uncovered["delta_CH4_kg"].abs() < 1e-6).all()


def test_cover_remaining_is_0_6_crust_and_0_75_solid(deltas):
    cover = deltas[deltas["fork_id"] == "HOLOS.CH4.cover_reduction"]
    for _, row in cover.iterrows():
        if row["manure_id"] == "liquid_uncovered":
            continue
        remaining = (row["CH4_manure_kg"]) / (row["CH4_manure_kg"] - row["delta_CH4_manure_kg"])
        if row["manure_id"] == "liquid_covered_crust":
            assert remaining == pytest.approx(0.60, rel=1e-9)
        elif row["manure_id"] == "liquid_covered_solid":
            assert remaining == pytest.approx(0.75, rel=1e-9)
        else:
            raise AssertionError(f"unexpected manure_id {row['manure_id']}")
