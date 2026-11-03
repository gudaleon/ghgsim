"""Tests for per-farm emissions Sankey diagrams."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ghgsim.api.cli import cli
from ghgsim.report.emissions_sankey import (
    MASS_TOL_KG_CO2E,
    assert_mass_conserved,
    build_stylized_payload,
    combined_forks,
    compute_stylized_farm_flows,
    discover_sankey_payloads,
    load_stylized_spec,
    next_view_version,
    node_balances,
    stylized_params,
    view_image_paths,
    write_sankey,
)
from ghgsim.report.fork_diagram import latest_versioned, repo_root

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "docs" / "figures"


def _spec_and_params():
    yaml_path = latest_versioned(DATA, "stylized_farms", ".yaml")
    spec = load_stylized_spec(yaml_path)
    return yaml_path, spec, stylized_params(ROOT, spec)


def _measure_runner():
    path = ROOT / "scripts" / "measure_holos_forks_stylized_AN_v2.py"
    spec = importlib.util.spec_from_file_location("measure_stylized_v2", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def farm_payloads():
    yaml_path, spec, params = _spec_and_params()
    rel = yaml_path.relative_to(ROOT).as_posix()
    payloads = {}
    for farm in spec["farms"]:
        payloads[farm["id"]] = build_stylized_payload(
            spec, farm, params, inputs_file=rel, output_version="AN_v1"
        )
    return spec, payloads


def test_every_stylized_farm_gets_a_diagram(farm_payloads):
    spec, payloads = farm_payloads
    farm_ids = [farm["id"] for farm in spec["farms"]]
    assert farm_ids
    assert sorted(payloads) == sorted(farm_ids)
    for farm_id, payload in payloads.items():
        assert payload["farm_id"] == farm_id
        assert set(payload["views"]) == {"source_correct", "holos_as_coded", "fork_delta"}
        for view in payload["views"].values():
            assert view["nodes"]
            assert view["links"]


def test_flows_conserve_mass(farm_payloads):
    _, payloads = farm_payloads
    for payload in payloads.values():
        for view in payload["views"].values():
            assert_mass_conserved(view)
            balances = node_balances(view)
            for node in view["nodes"]:
                balance = balances[node["id"]]
                if node["kind"] in {"animal", "source_total", "fork_added", "soil", "amendment", "crop"}:
                    assert balance["inflow"] == pytest.approx(0.0, abs=MASS_TOL_KG_CO2E)
                    assert balance["outflow"] == pytest.approx(node["value"], abs=MASS_TOL_KG_CO2E)
                elif node["kind"] in {"sink", "fork_removed"}:
                    assert balance["outflow"] == pytest.approx(0.0, abs=MASS_TOL_KG_CO2E)
                    assert balance["inflow"] == pytest.approx(node["value"], abs=MASS_TOL_KG_CO2E)
                else:
                    assert balance["inflow"] == pytest.approx(balance["outflow"], abs=MASS_TOL_KG_CO2E)


def test_totals_match_engine_co2e():
    yaml_path, spec, params = _spec_and_params()
    measure = _measure_runner()
    farm = spec["farms"][0]
    source = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    holos = compute_stylized_farm_flows(spec, farm, params, combined_forks(), run="holos_as_coded")
    engine_base = measure.run_stylized_farm(spec, farm, params, forks={})
    engine_holos = measure.run_stylized_farm(spec, farm, params, forks=combined_forks())
    assert source.co2e_t == pytest.approx(engine_base["CO2e_t"], abs=1e-9)
    assert holos.co2e_t == pytest.approx(engine_holos["CO2e_t"], abs=1e-9)
    assert source.ch4_kg == pytest.approx(engine_base["CH4_kg"], abs=1e-9)
    assert source.n2o_kg == pytest.approx(engine_base["N2O_kg"], abs=1e-9)
    payload = build_stylized_payload(
        spec, farm, params, inputs_file=yaml_path.name, output_version="AN_v1"
    )
    sink = next(node for node in payload["views"]["source_correct"]["nodes"] if node["id"] == "sink.CO2e")
    assert sink["value"] / 1000.0 == pytest.approx(engine_base["CO2e_t"], abs=1e-9)


def test_output_is_deterministic(farm_payloads):
    yaml_path, spec, params = _spec_and_params()
    farm = spec["farms"][0]
    rel = yaml_path.relative_to(ROOT).as_posix()
    first = build_stylized_payload(spec, farm, params, inputs_file=rel, output_version="AN_v1")
    second = build_stylized_payload(spec, farm, params, inputs_file=rel, output_version="AN_v1")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_write_refuses_overwrite(tmp_path, farm_payloads):
    _, payloads = farm_payloads
    payload = next(iter(payloads.values()))
    write_sankey(payload, tmp_path, version=1, render_static=False)
    with pytest.raises(FileExistsError):
        write_sankey(payload, tmp_path, version=1, render_static=False)


def test_cli_writes_every_farm_next_version(tmp_path, farm_payloads):
    spec, _payloads = farm_payloads
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["sankey", "--repo", str(ROOT), "--figures-dir", str(tmp_path), "--no-static"],
    )
    assert result.exit_code == 0, result.output
    for farm in spec["farms"]:
        stem = f"sankey_{farm['id']}_AN_v1"
        assert (tmp_path / f"{stem}.html").exists()
        assert (tmp_path / f"{stem}.json").exists()
    again = runner.invoke(
        cli,
        [
            "sankey",
            "--repo",
            str(ROOT),
            "--figures-dir",
            str(tmp_path),
            "--farm",
            spec["farms"][0]["id"],
            "--no-static",
        ],
    )
    assert again.exit_code == 0, again.output
    assert (tmp_path / f"sankey_{spec['farms'][0]['id']}_AN_v2.json").exists()


def test_generate_uses_repo_root():
    assert repo_root(ROOT) == ROOT


def test_view_image_paths_are_versioned_and_distinct(tmp_path):
    svg, png = view_image_paths(tmp_path, "dairy_forage_uncovered", "source_correct", 1).values()
    assert svg.name == "sankey_dairy_forage_uncovered_source_correct_AN_v1.svg"
    assert png.name == "sankey_dairy_forage_uncovered_source_correct_AN_v1.png"
    (tmp_path / svg.name).write_text("x")
    assert next_view_version(tmp_path, "dairy_forage_uncovered", "source_correct") == 2


def test_discover_sankey_payloads_skips_view_stems(tmp_path):
    (tmp_path / "sankey_dairy_forage_uncovered_AN_v1.json").write_text("{}")
    (tmp_path / "sankey_dairy_forage_uncovered_source_correct_AN_v1.json").write_text("{}")
    (tmp_path / "sankey_dairy_forage_uncovered_AN_v2.json").write_text("{}")
    found = discover_sankey_payloads(tmp_path)
    assert [path.name for path in found] == ["sankey_dairy_forage_uncovered_AN_v2.json"]


def test_committed_sankeys_cover_every_farm():
    yaml_path = latest_versioned(DATA, "stylized_farms", ".yaml")
    spec = load_stylized_spec(yaml_path)
    newest = {path.name: path for path in discover_sankey_payloads(FIGURES)}
    missing = []
    for farm in spec["farms"]:
        hits = [path for name, path in newest.items() if name.startswith(f"sankey_{farm['id']}_AN_v")]
        if not hits:
            missing.append(farm["id"])
    if missing:
        pytest.skip(f"committed Sankeys not written yet: {missing}")
    for path in discover_sankey_payloads(FIGURES):
        payload = json.loads(path.read_text())
        assert_mass_conserved(payload["views"]["source_correct"])


def test_field_farm_sankey_has_barn_to_field_to_soil(farm_payloads):
    _, payloads = farm_payloads
    payload = payloads["broiler_litter_field"]
    view = payload["views"]["source_correct"]
    ids = {node["id"] for node in view["nodes"]}
    assert "field.applied_manure" in ids
    assert "process.soil_n2o" in ids
    assert "crop.residues" in ids
    kinds = {node["id"]: node["kind"] for node in view["nodes"]}
    assert kinds["field.applied_manure"] == "field"
    links = {(link["source"], link["target"]) for link in view["links"]}
    assert ("animal.broilers", "field.applied_manure") in links
    assert ("field.applied_manure", "process.soil_n2o") in links
    assert ("crop.residues", "process.soil_n2o") in links
