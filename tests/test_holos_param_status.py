"""Parameter status labels: VERIFIED requires a primary published page/table."""

import csv
from pathlib import Path

import pytest

from ghgsim.core.registry import VerificationStatus, load_parameter_csv
from ghgsim.modules.holos.forks import get_holos_fork_registry, list_holos_as_coded_forks

ROOT = Path(__file__).resolve().parents[1]
CANADA = ROOT / "data" / "holos_params_canada_AN_v4.csv"
CANADA_V5 = ROOT / "data" / "holos_params_canada_AN_v5.csv"
CANADA_V6 = ROOT / "data" / "holos_params_canada_AN_v6.csv"
US = ROOT / "data" / "holos_params_us_AN_v2.csv"
ALLOWED = {item.value for item in VerificationStatus}

# A Holos implementation path is never sufficient for VERIFIED.
HOLOS_FILE_MARKERS = (".cs:", ".cs", "csv:")


def _rows(path: Path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize("path", [CANADA, CANADA_V5, CANADA_V6, US])
def test_status_values_are_known(path):
    rows = _rows(path)
    assert rows
    for row in rows:
        assert row["status"] in ALLOWED, f"{row['key']} has unknown status {row['status']}"


@pytest.mark.parametrize("path", [CANADA, US])
def test_verified_has_primary_page_and_table_or_equation(path):
    for row in _rows(path):
        if row["status"] != "VERIFIED":
            continue
        assert row["page"], f"{row['key']} VERIFIED but missing page"
        assert row["table"] or row["equation"], f"{row['key']} VERIFIED but missing table/equation"
        source = row["source_doi_or_url"].lower()
        assert "ipcc" in source or "epa" in source or source.startswith("http"), (
            f"{row['key']} VERIFIED source is not a primary published document: {row['source_doi_or_url']}"
        )


@pytest.mark.parametrize("path", [CANADA, US])
def test_verified_is_not_only_a_holos_file_line(path):
    for row in _rows(path):
        if row["status"] != "VERIFIED":
            continue
        blob = " ".join([row["source_doi_or_url"], row["table"], row["page"], row["notes"]]).lower()
        holos_only = "holos" in blob and "ipcc" not in blob and "epa" not in blob
        assert not holos_only, f"{row['key']} VERIFIED from Holos only"


def test_canada_v4_loads_with_allow_unverified():
    registry = load_parameter_csv(CANADA, allow_unverified=True)
    unverified = {p.key: p.status for p in registry.list_unverified()}
    assert unverified["HOLOS.VS.dairy_calves_coeff|canada"] == VerificationStatus.UNVERIFIED
    assert unverified["HOLOS.Ym.dairy_lactating|canada"] == VerificationStatus.UNVERIFIED
    assert registry.get("HOLOS.B0.dairy|canada").status == VerificationStatus.VERIFIED


def test_canada_v5_cover_params_are_reduction_fractions():
    registry = load_parameter_csv(CANADA_V5, allow_unverified=True)
    crust = registry.get("HOLOS.COVER.natural_crust_reduction")
    solid = registry.get("HOLOS.COVER.solid_cover_reduction")
    assert crust.value == 0.40
    assert solid.value == 0.25
    assert crust.units == "reduction fraction"
    assert solid.units == "reduction fraction"
    assert crust.status == VerificationStatus.SOURCE_TRACED
    assert solid.status == VerificationStatus.UNVERIFIED


def test_unverified_dairy_ym_refused_without_flag():
    registry = load_parameter_csv(CANADA, allow_unverified=False)
    with pytest.raises(ValueError, match="UNVERIFIED"):
        registry.get("HOLOS.Ym.dairy_lactating|canada")


def test_holos_as_coded_forks_are_registered():
    forks = list_holos_as_coded_forks()
    ids = {fork.id for fork in forks}
    expected = {
        "HOLOS.GE.digestibility",
        "HOLOS.ENTERIC.calf_zero",
        "HOLOS.VS.digestibility",
        "HOLOS.VS.urinary_energy",
        "HOLOS.VS.calf_coeff",
        "HOLOS.CH4.cover_reduction",
        "HOLOS.CH4.turkey_zero",
        "HOLOS.NEX.calf_nrate",
    }
    assert expected <= ids
    registry = get_holos_fork_registry()
    ym = registry.get("HOLOS.YM.dairy")
    assert ym.label == "parameter_refinement"
    assert ym.default == "eccc_2022_canada"
    for fork in forks:
        assert fork.default == "source_correct"
        assert "holos_as_coded" in fork.options
