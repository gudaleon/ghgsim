"""
Tests for module contract and graph system (Phase 2).

Acceptance tests:
- Test 3: User-defined module integration (stub)
- Test 9: Unit mismatch detection
"""

import pytest

from ghgsim.core.graph import ExecutionGraph, GraphNode
from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.core.units import check_compatible, check_units


class SimpleLinearModule:
    """Simple 2-parameter linear model for testing: y = a*x + b"""

    id = "test.linear"
    version = "1.0.0"
    inputs = {"x": VarSpec("x", "dimensionless", "Input value")}
    parameters = {
        "a": ParamRef("test.a", "Slope", fallback=1.0),
        "b": ParamRef("test.b", "Intercept", fallback=0.0),
    }
    outputs = {"y": VarSpec("y", "dimensionless", "Output value")}
    sources = [
        Citation(
            "Test linear model", equation="y = a*x + b", notes="For testing only"
        )
    ]

    def compute(self, inputs, params):
        x = inputs["x"]
        a = params["a"]
        b = params["b"]
        return {"y": a * x + b}


def test_module_validation():
    """Test module metadata validation."""
    module = SimpleLinearModule()
    errors = validate_module(module)
    assert len(errors) == 0, f"Valid module should have no errors: {errors}"


def test_module_validation_missing_fields():
    """Test that incomplete modules are rejected."""

    class IncompleteModule:
        id = ""
        version = "1.0.0"
        inputs = {}
        parameters = {}
        outputs = {}
        sources = []

        def compute(self, inputs, params):
            return {}

    errors = validate_module(IncompleteModule())
    assert len(errors) > 0, "Incomplete module should have validation errors"
    assert any("ID" in err for err in errors)


def test_unit_checking():
    """Test pint unit checking and conversion."""
    # Valid units
    q = check_units(100.0, "kg", "mass")
    assert q.magnitude == 100.0
    assert str(q.units) == "kilogram"

    # Compatible units
    assert check_compatible("kg", "gram")
    assert check_compatible("m", "kilometer")

    # Incompatible units
    assert not check_compatible("kg", "meter")
    assert not check_compatible("second", "kilogram")


def test_unit_mismatch_detection():
    """Test 9: Unit mismatch raises error at graph build."""

    class MassProducer:
        id = "test.mass_producer"
        version = "1.0.0"
        inputs = {}
        parameters = {}
        outputs = {"value": VarSpec("value", "kg", "Mass output")}
        sources = [Citation("Test")]

        def compute(self, inputs, params):
            return {"value": 100.0}

    class LengthConsumer:
        id = "test.length_consumer"
        version = "1.0.0"
        inputs = {"value": VarSpec("value", "m", "Length input", required=True)}
        parameters = {}
        outputs = {"result": VarSpec("result", "dimensionless", "Result")}
        sources = [Citation("Test")]

        def compute(self, inputs, params):
            return {"result": inputs["value"] * 2}

    # This should raise ValueError due to unit mismatch
    # Producer provides "value" in kg, but consumer expects "value" in m
    nodes = {
        "producer": GraphNode(
            module=MassProducer(),
            dependencies=[],
            provides={"value": "kg"},
        ),
        "consumer": GraphNode(
            module=LengthConsumer(),
            dependencies=["producer"],
            provides={"result": "dimensionless"},
        ),
    }

    # This should fail due to unit mismatch: kg vs m
    with pytest.raises(ValueError, match="Unit mismatch"):
        ExecutionGraph(nodes)


def test_cycle_detection():
    """Test that cycles in the graph are detected."""

    class PassThrough:
        id = "test.passthrough"
        version = "1.0.0"
        inputs = {"x": VarSpec("x", "dimensionless", "Input")}
        parameters = {}
        outputs = {"y": VarSpec("y", "dimensionless", "Output")}
        sources = [Citation("Test")]

        def compute(self, inputs, params):
            return {"y": inputs["x"]}

    nodes = {
        "node_a": GraphNode(
            module=PassThrough(),
            dependencies=["node_b"],
            provides={"y": "dimensionless"},
        ),
        "node_b": GraphNode(
            module=PassThrough(),
            dependencies=["node_a"],
            provides={"y": "dimensionless"},
        ),
    }

    with pytest.raises(ValueError, match="Cycle detected"):
        ExecutionGraph(nodes)


def test_simple_graph_execution():
    """Test that a simple graph can execute correctly."""
    module = SimpleLinearModule()

    nodes = {
        "linear": GraphNode(
            module=module, dependencies=[], provides={"y": "dimensionless"}
        )
    }

    graph = ExecutionGraph(nodes)

    # Execute with x=10, a=2, b=3 -> y = 2*10 + 3 = 23
    result = graph.execute(
        external_inputs={"x": 10.0}, parameters={"test.a": 2.0, "test.b": 3.0}
    )

    assert "y" in result
    assert result["y"] == 23.0


def test_user_defined_module_stub():
    """
    Test 3 (stub): User can add a module with only a module file + YAML.
    
    This is a stub test that will be expanded in Phase 5 with full
    Monte Carlo, Sobol, and estimation tests.
    """
    # Demonstrate that a user-defined module follows the protocol
    user_module = SimpleLinearModule()

    # Validate it
    errors = validate_module(user_module)
    assert len(errors) == 0

    # Create a graph with it
    nodes = {
        "user_model": GraphNode(
            module=user_module, dependencies=[], provides={"y": "dimensionless"}
        )
    }
    graph = ExecutionGraph(nodes)

    # Execute it
    result = graph.execute(
        external_inputs={"x": 5.0}, parameters={"test.a": 3.0, "test.b": 1.0}
    )
    assert result["y"] == 16.0  # 3*5 + 1

    # Note: Full test with MC, Sobol, and estimation will be in Phase 5
