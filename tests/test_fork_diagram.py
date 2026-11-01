"""Tests for the living-paper Holos fork decision diagram."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from ghgsim.api.cli import cli
from ghgsim.report.fork_diagram import (
    an_version,
    build_fork_diagram,
    build_from_data_dir,
    discover_inputs,
    fork_status_from_trace,
    latest_versioned,
    load_trace_table,
    mermaid_id,
    newest_status_column,
    normalize_trace_status,
    render_mermaid,
    weakest_status,
    write_fork_diagram,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "docs" / "figures"


def _fork_ids_from_mermaid(mermaid: str) -> list[str]:
    return re.findall(r'\{"(HOLOS\.[^"<]+)<br/>', mermaid)


def test_latest_versioned_picks_highest_an_version(tmp_path):
    (tmp_path / "holos_forks_AN_v2.json").write_text("[]\n")
    (tmp_path / "holos_forks_AN_v10.json").write_text("[]\n")
    (tmp_path / "holos_forks_AN_v3.json").write_text("[]\n")
    (tmp_path / "holos_forks_summary_AN_v99.json").write_text("[]\n")
    chosen = latest_versioned(tmp_path, "holos_forks", ".json")
    assert chosen.name == "holos_forks_AN_v10.json"
    assert an_version(chosen.name) == 10


def test_newest_coefficient_trace_is_picked(tmp_path):
    (tmp_path / "coefficient_trace_AN_v1.csv").write_text("param,status\n")
    (tmp_path / "coefficient_trace_AN_v3.csv").write_text("param,status\n")
    (tmp_path / "coefficient_trace_AN_v4.csv").write_text("param,status\n")
    (tmp_path / "coefficient_trace_summary_AN_v99.csv").write_text("param,status\n")
    chosen = latest_versioned(tmp_path, "coefficient_trace", ".csv")
    assert chosen.name == "coefficient_trace_AN_v4.csv"
    assert an_version(chosen.name) == 4


def test_discover_inputs_picks_repo_newest_trace():
    paths = discover_inputs(DATA)
    newest = latest_versioned(DATA, "coefficient_trace", ".csv")
    assert paths["coefficient_trace"] == newest
    assert newest == latest_versioned(DATA, "coefficient_trace", ".csv")
    assert an_version(newest.name) >= 5


def test_every_registry_fork_appears_exactly_once():
    payload = build_from_data_dir(DATA, output_version="AN_v1")
    mermaid = render_mermaid(payload)
    forks = json.loads(latest_versioned(DATA, "holos_forks", ".json").read_text())
    registry_ids = [row["id"] for row in forks]
    mermaid_ids = _fork_ids_from_mermaid(mermaid)
    json_ids = [node["id"] for node in payload["nodes"] if node["type"] == "fork"]
    assert sorted(mermaid_ids) == sorted(registry_ids)
    assert len(mermaid_ids) == len(set(mermaid_ids)) == len(registry_ids)
    assert json_ids == mermaid_ids
    for fork_id in registry_ids:
        assert mermaid.count(f'{{"{fork_id}<br/>') == 1
        assert mermaid_id(fork_id) in mermaid


def test_diagram_output_is_deterministic():
    first = build_from_data_dir(DATA, output_version="AN_v1")
    second = build_from_data_dir(DATA, output_version="AN_v1")
    assert render_mermaid(first) == render_mermaid(second)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_dummy_fork_adds_a_node():
    payload = build_from_data_dir(DATA, output_version="AN_v1")
    dummy = {
        "id": "HOLOS.DUMMY.unit_test",
        "description": "Injected fork for diagram tests",
        "affects": ["holos.manure"],
        "default": "source_correct",
        "options": {"source_correct": "default", "holos_as_coded": "alt"},
        "label": "holos_as_coded",
        "issue_ref": "TEST",
    }
    forks = json.loads(latest_versioned(DATA, "holos_forks", ".json").read_text()) + [dummy]
    observations = {key: value.get("observations", []) for key, value in payload["deltas"].items()}
    with_dummy = build_fork_diagram(
        forks,
        observations=observations,
        trace_status=payload["status"],
        output_version="AN_v1",
    )
    mermaid = render_mermaid(with_dummy)
    ids = [node["id"] for node in with_dummy["nodes"] if node["type"] == "fork"]
    assert ids.count("HOLOS.DUMMY.unit_test") == 1
    assert mermaid.count('{"HOLOS.DUMMY.unit_test<br/>') == 1
    base_ids = [node["id"] for node in payload["nodes"] if node["type"] == "fork"]
    assert len(ids) == len(base_ids) + 1


def test_write_refuses_overwrite(tmp_path):
    payload = build_fork_diagram(
        [
            {
                "id": "HOLOS.GE.digestibility",
                "description": "x",
                "affects": [],
                "default": "source_correct",
                "options": {"source_correct": "a", "holos_as_coded": "b"},
                "label": "holos_as_coded",
                "issue_ref": "X",
            }
        ],
        output_version="AN_v1",
    )
    mermaid = render_mermaid(payload)
    write_fork_diagram(payload, mermaid, tmp_path, version=1, render_svg=False)
    with pytest.raises(FileExistsError):
        write_fork_diagram(payload, mermaid, tmp_path, version=1, render_svg=False)


def test_cli_writes_next_version(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["fork-diagram", "--repo", str(ROOT), "--figures-dir", str(tmp_path), "--no-svg"],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "fork_diagram_AN_v1.mmd").exists()
    assert (tmp_path / "fork_diagram_AN_v1.json").exists()
    again = runner.invoke(
        cli,
        ["fork-diagram", "--repo", str(ROOT), "--figures-dir", str(tmp_path), "--no-svg"],
    )
    assert again.exit_code == 0, again.output
    assert (tmp_path / "fork_diagram_AN_v2.mmd").exists()
    assert not (tmp_path / "fork_diagram_AN_v1.svg").exists()


def test_committed_figure_matches_regeneration():
    committed_mmd = latest_versioned(FIGURES, "fork_diagram", ".mmd")
    committed_json = committed_mmd.with_suffix(".json")
    if not committed_mmd.exists():
        pytest.skip("committed diagram not written yet")
    version = an_version(committed_mmd.name)
    payload = build_from_data_dir(DATA, output_version=f"AN_v{version}")
    assert committed_mmd.read_text(encoding="utf-8") == render_mermaid(payload)
    committed = json.loads(committed_json.read_text(encoding="utf-8"))
    assert committed["nodes"] == payload["nodes"]
    assert committed["edges"] == payload["edges"]
    assert committed["status"] == payload["status"]


def test_newest_status_column_and_weakest_mapped_status(tmp_path):
    csv_path = tmp_path / "coefficient_trace_AN_v1.csv"
    csv_path.write_text(
        "param,where used,status,v2 status,v3 status\n"
        "HOLOS.CH4.cover_reduction,holos.manure_ch4,HOLOS-ONLY,HOLOS-ONLY,SOURCE-TRACED\n"
        "HOLOS.COVER.natural_crust_factor,uses HOLOS.CH4.cover_reduction,VERIFIED,VERIFIED,HOLOS-ONLY\n"
        "HOLOS.COVER.other_cover_factor,uses HOLOS.CH4.cover_reduction,VERIFIED,,VERIFIED\n"
        "HOLOS.ENTERIC.calf_zero,holos.enteric,HOLOS-ONLY,HOLOS-ONLY,VERIFIED (IPCC 2019 p.10.45)\n"
    )
    rows = load_trace_table(csv_path)
    by_param = {row["param"]: row["status"] for row in rows}
    assert by_param["HOLOS.CH4.cover_reduction"] == "SOURCE-TRACED"
    assert by_param["HOLOS.COVER.natural_crust_factor"] == "HOLOS-ONLY"
    assert by_param["HOLOS.ENTERIC.calf_zero"] == "VERIFIED"
    assert newest_status_column(["status", "v2 status", "v3 status"]) == "v3 status"
    assert normalize_trace_status("SOURCE-TRACED + MANUAL-vs-CODE MISMATCH") == "SOURCE-TRACED"
    assert weakest_status(["VERIFIED", "SOURCE-TRACED", "HOLOS-ONLY"]) == "HOLOS-ONLY"
    assert fork_status_from_trace("HOLOS.CH4.cover_reduction", rows) == "HOLOS-ONLY"
    assert fork_status_from_trace("HOLOS.ENTERIC.calf_zero", rows) == "VERIFIED"


def test_v4_trace_fork_statuses():
    payload = build_from_data_dir(DATA, output_version="AN_v2")
    assert payload["generated_from"]["coefficient_trace"].endswith("coefficient_trace_AN_v5.csv")
    assert payload["status"]["HOLOS.GE.digestibility"] == "HOLOS-ONLY"
    assert payload["status"]["HOLOS.ENTERIC.calf_zero"] == "VERIFIED"
    assert payload["status"]["HOLOS.YM.dairy"] == "HOLOS-ONLY"
    assert payload["status"]["HOLOS.VS.digestibility"] == "HOLOS-ONLY"
    assert payload["status"]["HOLOS.VS.urinary_energy"] == "VERIFIED"
    assert payload["status"]["HOLOS.VS.calf_coeff"] == "HOLOS-ONLY"
    assert payload["status"]["HOLOS.CH4.cover_reduction"] == "SOURCE-TRACED"
    assert payload["status"]["HOLOS.NEX.calf_nrate"] == "SOURCE-TRACED"
    assert payload["status"]["HOLOS.CH4.turkey_zero"] == "SOURCE-TRACED"
