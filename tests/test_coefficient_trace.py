"""Phase 3c: every UNVERIFIED/SOURCE-TRACED Holos coefficient is in the trace CSV."""

import csv
from pathlib import Path

from ghgsim.core.registry import VerificationStatus
from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.report.fork_diagram import latest_versioned

ROOT = Path(__file__).resolve().parents[1]
TRACE_V1 = ROOT / "data" / "coefficient_trace_AN_v1.csv"
TRACE = latest_versioned(ROOT / "data", "coefficient_trace", ".csv")
DOC = ROOT / "docs" / "COEFFICIENT_TRACE_AN_v1.md"
CANADA = latest_versioned(ROOT / "data", "holos_params_canada", ".csv")
US = ROOT / "data" / "holos_params_us_AN_v2.csv"

REQUIRED = {
    "param",
    "value",
    "units",
    "where used",
    "Holos file:line",
    "claimed source",
    "source checked Y/N",
    "found value",
    "status",
    "note",
}
TRACE_STATUSES = {"VERIFIED", "HOLOS-ONLY"}
OPENED_PENDING = {"UNVERIFIED", "SOURCE-TRACED"}


def _rows(path: Path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def test_trace_csv_has_required_columns():
    rows = _rows(TRACE_V1)
    assert rows
    assert REQUIRED <= set(rows[0].keys())
    newest = _rows(TRACE)
    assert newest
    assert REQUIRED <= set(newest[0].keys())


def test_every_unverified_or_source_traced_param_is_traced():
    traced = {row["param"] for row in _rows(TRACE)}
    missing = []
    for path in (CANADA, US):
        for row in _rows(path):
            if row["status"] in OPENED_PENDING and row["key"] not in traced:
                missing.append(row["key"])
    assert missing == [], f"params not in {TRACE.name}: {missing}"


def test_every_holos_fork_is_traced():
    traced = {row["param"] for row in _rows(TRACE)}
    missing = [
        fork.id
        for fork in get_holos_fork_registry().list_forks(sort_by="id")
        if fork.id not in traced
    ]
    assert missing == [], f"forks not in {TRACE.name}: {missing}"


def test_trace_status_and_opened_sources():
    for row in _rows(TRACE_V1):
        assert row["status"] in TRACE_STATUSES, f"{row['param']} status {row['status']}"
        assert row["source checked Y/N"] in {"Y", "N"}
        assert row["found value"].strip()
        if row["status"] == "VERIFIED":
            assert row["source checked Y/N"] == "Y"
            blob = " ".join([row["claimed source"], row["found value"], row["note"]]).lower()
            assert "ipcc" in blob


def test_questions_address_aaron_holos_team_not_unverified_surname():
    text = DOC.read_text()
    assert "Aaron (Holos team, AAFC)" in text
    assert "McPherson" not in text
    assert "HOLOS-ONLY" in text
    # Numbered questions for Holos-only items.
    for number in range(1, 15):
        assert f"{number}." in text.split("Questions for Aaron")[1]


def test_param_csv_status_enum_unchanged():
    allowed = {item.value for item in VerificationStatus}
    for path in (CANADA, US):
        for row in _rows(path):
            assert row["status"] in allowed
