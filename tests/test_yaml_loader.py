"""
Tests for YAML model loader.
"""

import tempfile
from pathlib import Path

import pytest

from ghgsim.core.loader import build_graph_from_yaml, load_model_yaml
from ghgsim.core.module import Citation, ParamRef, VarSpec


class DummyModule:
    """Dummy module for testing."""

    id = "test.dummy"
    version = "1.0.0"
    inputs = {"x": VarSpec("x", "dimensionless", "Input")}
    parameters = {"p": ParamRef("test.p", "Parameter", fallback=1.0)}
    outputs = {"y": VarSpec("y", "dimensionless", "Output")}
    sources = [Citation("Test")]

    def compute(self, inputs, params):
        return {"y": inputs["x"] * params["p"]}


def test_load_yaml():
    """Test YAML loading."""
    yaml_content = """
name: test_model
version: 1.0.0
nodes:
  node1:
    module: test.dummy
    depends_on: []
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    try:
        model_def = load_model_yaml(temp_path)
        assert "nodes" in model_def
        assert "node1" in model_def["nodes"]
        assert model_def["nodes"]["node1"]["module"] == "test.dummy"
    finally:
        temp_path.unlink()


def test_build_graph_from_yaml():
    """Test building execution graph from YAML definition."""
    model_def = {
        "nodes": {
            "compute": {
                "module": "test.dummy",
                "depends_on": [],
            }
        }
    }

    available_modules = {"test.dummy": DummyModule()}

    graph = build_graph_from_yaml(model_def, available_modules)
    assert "compute" in graph.nodes

    # Execute the graph
    result = graph.execute(
        external_inputs={"x": 5.0}, parameters={"test.p": 2.0}
    )
    assert result["y"] == 10.0


def test_yaml_missing_module():
    """Test that referencing a non-existent module raises error."""
    model_def = {
        "nodes": {
            "compute": {
                "module": "nonexistent.module",
            }
        }
    }

    with pytest.raises(ValueError, match="not found in available modules"):
        build_graph_from_yaml(model_def, {})


def test_yaml_dependency_chain():
    """Test a chain of dependent nodes."""

    class ProducerModule:
        id = "test.producer"
        version = "1.0.0"
        inputs = {}
        parameters = {}
        outputs = {"value": VarSpec("value", "dimensionless", "Value")}
        sources = [Citation("Test")]

        def compute(self, inputs, params):
            return {"value": 10.0}

    class ConsumerModule:
        id = "test.consumer"
        version = "1.0.0"
        inputs = {"value": VarSpec("value", "dimensionless", "Input value")}
        parameters = {}
        outputs = {"doubled": VarSpec("doubled", "dimensionless", "Doubled value")}
        sources = [Citation("Test")]

        def compute(self, inputs, params):
            return {"doubled": inputs["value"] * 2}

    model_def = {
        "nodes": {
            "producer": {"module": "test.producer", "depends_on": []},
            "consumer": {"module": "test.consumer", "depends_on": ["producer"]},
        }
    }

    available_modules = {
        "test.producer": ProducerModule(),
        "test.consumer": ConsumerModule(),
    }

    graph = build_graph_from_yaml(model_def, available_modules)
    result = graph.execute(external_inputs={}, parameters={})

    assert result["value"] == 10.0
    assert result["doubled"] == 20.0
