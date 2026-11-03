"""
Tests for ghgsim services: Monte Carlo, Sobol, and Fork registry.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from ghgsim.core.registry import DistributionType, ParameterRegistry, ParameterValue, VerificationStatus
from ghgsim.services import Fork, ForkRegistry, MonteCarloService, SobolService


@pytest.fixture
def simple_registry():
    """Create a simple parameter registry for testing."""
    registry = ParameterRegistry(allow_unverified=False)
    
    # Add uniform parameters
    registry.register(ParameterValue(
        key="test.param1.all",
        value=10.0,
        units="dimensionless",
        dist=DistributionType.UNIFORM,
        dist_params={"lower": 5.0, "upper": 15.0},
        status=VerificationStatus.VERIFIED,
    ))
    
    registry.register(ParameterValue(
        key="test.param2.all",
        value=20.0,
        units="dimensionless",
        dist=DistributionType.UNIFORM,
        dist_params={"lower": 10.0, "upper": 30.0},
        status=VerificationStatus.VERIFIED,
    ))
    
    registry.register(ParameterValue(
        key="test.param3.all",
        value=5.0,
        units="dimensionless",
        dist=DistributionType.FIXED,
        status=VerificationStatus.VERIFIED,
    ))
    
    return registry


def test_montecarlo_lhs_sampling(simple_registry):
    """Test LHS sampling produces correct number of samples."""
    mc = MonteCarloService(seed=42)
    
    param_keys = ["test.param1.all", "test.param2.all"]
    samples = mc.sample_parameters(simple_registry, param_keys, n_samples=100)
    
    assert len(samples) == 100
    assert all(isinstance(s, dict) for s in samples)
    assert all(set(s.keys()) == set(param_keys) for s in samples)
    
    # Check samples are within bounds
    for sample in samples:
        assert 5.0 <= sample["test.param1.all"] <= 15.0
        assert 10.0 <= sample["test.param2.all"] <= 30.0


def test_montecarlo_fixed_parameter(simple_registry):
    """Test fixed parameters return constant value."""
    mc = MonteCarloService(seed=42)
    
    param_keys = ["test.param3.all"]
    samples = mc.sample_parameters(simple_registry, param_keys, n_samples=10)
    
    # All samples should have the same value for fixed parameter
    values = [s["test.param3.all"] for s in samples]
    assert all(v == 5.0 for v in values)


def test_montecarlo_determinism(simple_registry):
    """Test that same seed produces same samples."""
    mc1 = MonteCarloService(seed=42)
    mc2 = MonteCarloService(seed=42)
    
    param_keys = ["test.param1.all", "test.param2.all"]
    samples1 = mc1.sample_parameters(simple_registry, param_keys, n_samples=10)
    samples2 = mc2.sample_parameters(simple_registry, param_keys, n_samples=10)
    
    for s1, s2 in zip(samples1, samples2):
        for key in param_keys:
            assert abs(s1[key] - s2[key]) < 1e-10


def test_montecarlo_run_ensemble(simple_registry):
    """Test ensemble run with simple compute function."""
    mc = MonteCarloService(seed=42)
    
    # Simple compute function: output = param1 + param2
    def compute(inputs, params):
        return {"sum": params["test.param1.all"] + params["test.param2.all"]}
    
    param_keys = ["test.param1.all", "test.param2.all"]
    param_samples, output_samples = mc.run_ensemble(
        compute,
        {},  # No fixed inputs
        simple_registry,
        param_keys,
        n_samples=50,
    )
    
    assert len(param_samples) == 50
    assert len(output_samples) == 50
    
    # Verify outputs match computation
    for params, outputs in zip(param_samples, output_samples):
        expected = params["test.param1.all"] + params["test.param2.all"]
        assert abs(outputs["sum"] - expected) < 1e-10


def test_montecarlo_summarize_outputs(simple_registry):
    """Test output summary statistics."""
    mc = MonteCarloService(seed=42)
    
    def compute(inputs, params):
        return {"output": params["test.param1.all"] * 2}
    
    _, output_samples = mc.run_ensemble(
        compute,
        {},
        simple_registry,
        ["test.param1.all"],
        n_samples=100,
    )
    
    summary = mc.summarize_outputs(output_samples, ["output"])
    
    assert "output" in summary
    stats = summary["output"]
    
    assert "mean" in stats
    assert "median" in stats
    assert "std" in stats
    assert "cv" in stats
    assert "p2.5" in stats
    assert "p97.5" in stats
    assert "min" in stats
    assert "max" in stats
    
    # Output is param1 * 2, where param1 is uniform(5, 15)
    # So output should be uniform(10, 30)
    assert 10.0 <= stats["min"] <= 12.0  # Close to lower bound
    assert 28.0 <= stats["max"] <= 30.0  # Close to upper bound
    assert 18.0 <= stats["mean"] <= 22.0  # Around midpoint


def test_sobol_sampling(simple_registry):
    """Test Sobol sampling with Saltelli scheme."""
    sobol = SobolService(seed=42)
    
    param_keys = ["test.param1.all", "test.param2.all"]
    samples = sobol.sample_parameters(simple_registry, param_keys, n_samples=10)
    
    # Saltelli sampling: n * (2D + 2) samples
    # For 2 parameters: 10 * (2*2 + 2) = 10 * 6 = 60 samples
    assert len(samples) == 60


def test_sobol_analysis(simple_registry):
    """Test Sobol sensitivity analysis."""
    sobol = SobolService(seed=42)
    
    # Test with linear model: output = 3*param1 + 1*param2
    # param1 should have higher sensitivity
    param_keys = ["test.param1.all", "test.param2.all"]
    n_samples = 100
    
    param_samples = sobol.sample_parameters(simple_registry, param_keys, n_samples)
    
    # Compute outputs
    output_samples = []
    for sample in param_samples:
        output = 3.0 * sample["test.param1.all"] + 1.0 * sample["test.param2.all"]
        output_samples.append({"result": output})
    
    # Analyze
    indices = sobol.analyze(param_keys, param_samples, output_samples, "result", n_samples)
    
    # Check structure
    assert "S1" in indices
    assert "ST" in indices
    assert "S1_conf" in indices
    assert "ST_conf" in indices
    
    # param1 should have higher first-order index than param2
    assert indices["S1"]["test.param1.all"] > indices["S1"]["test.param2.all"]
    
    # Total-order indices should be similar to first-order for additive model
    assert abs(indices["ST"]["test.param1.all"] - indices["S1"]["test.param1.all"]) < 0.3


def test_sobol_rank_importance(simple_registry):
    """Test ranking parameters by importance."""
    sobol = SobolService(seed=42)
    
    param_keys = ["test.param1.all", "test.param2.all"]
    n_samples = 100
    param_samples = sobol.sample_parameters(simple_registry, param_keys, n_samples)
    
    # Linear model with different weights
    output_samples = []
    for sample in param_samples:
        output = 5.0 * sample["test.param1.all"] + 1.0 * sample["test.param2.all"]
        output_samples.append({"result": output})
    
    indices = sobol.analyze(param_keys, param_samples, output_samples, "result", n_samples)
    ranked = sobol.rank_importance(indices, metric="ST")
    
    # Should return list of (param_name, index) tuples
    assert len(ranked) == 2
    assert isinstance(ranked[0], tuple)
    assert len(ranked[0]) == 2
    
    # param1 should be ranked first (highest importance)
    assert ranked[0][0] == "test.param1.all"
    assert ranked[1][0] == "test.param2.all"


def test_fork_registry_basic():
    """Test basic fork registry operations."""
    registry = ForkRegistry()
    
    fork = Fork(
        id="F001",
        description="Test fork",
        affects=["test.param1.all"],
        default="option1",
        options={"option1": "First option", "option2": "Second option"},
    )
    
    registry.register(fork)
    
    # Get fork
    retrieved = registry.get("F001")
    assert retrieved.id == "F001"
    assert retrieved.default == "option1"
    
    # List forks
    forks = registry.list_forks(sort_by="none")
    assert len(forks) == 1
    assert forks[0].id == "F001"


def test_fork_registry_importance_ranking():
    """Test fork importance ranking."""
    registry = ForkRegistry()
    
    fork1 = Fork("F001", "Fork 1", ["param1"], "opt1", {"opt1": "A", "opt2": "B"}, importance=0.5)
    fork2 = Fork("F002", "Fork 2", ["param2"], "opt1", {"opt1": "A", "opt2": "B"}, importance=0.8)
    
    registry.register(fork1)
    registry.register(fork2)
    
    # List sorted by importance
    forks = registry.list_forks(sort_by="importance")
    assert len(forks) == 2
    assert forks[0].id == "F002"  # Higher importance first
    assert forks[1].id == "F001"


def test_fork_registry_sobol_ranking():
    """Test ranking forks by Sobol indices."""
    registry = ForkRegistry()
    
    fork1 = Fork("F001", "Fork 1", ["test.param1.all"], "opt1", {"opt1": "A"})
    fork2 = Fork("F002", "Fork 2", ["test.param2.all"], "opt1", {"opt1": "A"})
    
    registry.register(fork1)
    registry.register(fork2)
    
    # Mock Sobol results
    sobol_results = {
        "ST": {
            "test.param1.all": 0.7,
            "test.param2.all": 0.3,
        }
    }
    
    ranked = registry.rank_by_sobol(sobol_results)
    
    assert len(ranked) == 2
    assert ranked[0][0] == "F001"  # param1 has higher ST
    assert ranked[0][1] == 0.7
    assert ranked[1][0] == "F002"
    assert ranked[1][1] == 0.3


def test_fork_registry_json_io():
    """Test saving and loading fork registry from JSON."""
    registry = ForkRegistry()
    
    fork = Fork(
        id="F007",
        description="Ym category selection",
        affects=["IPCC2019.Ym.dairy_medium"],
        default="dairy_medium",
        options={
            "dairy_high_ndf_le35": "High NDF, <35% milk fat",
            "dairy_medium": "Medium forage diet",
        },
        importance=0.85,
    )
    
    registry.register(fork)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        registry.save_to_json(temp_path)
        
        # Load into new registry
        registry2 = ForkRegistry()
        registry2.load_from_json(temp_path)
        
        # Verify
        fork2 = registry2.get("F007")
        assert fork2.id == "F007"
        assert fork2.description == "Ym category selection"
        assert fork2.default == "dairy_medium"
        assert fork2.importance == 0.85
        assert len(fork2.options) == 2
    finally:
        temp_path.unlink()


def test_fork_registry_apply_forks():
    """Test applying fork settings to configuration."""
    registry = ForkRegistry()
    
    fork = Fork(
        id="F001",
        description="Test fork",
        affects=["param1"],
        default="opt1",
        options={"opt1": "Option 1", "opt2": "Option 2"},
    )
    
    registry.register(fork)
    
    base_config = {"param1": "default_value"}
    fork_settings = {"F001": "opt2"}
    
    new_config = registry.apply_forks(fork_settings, base_config)
    
    assert "forks" in new_config
    assert new_config["forks"]["F001"] == "opt2"


def test_fork_registry_invalid_option():
    """Test that invalid fork option raises error."""
    registry = ForkRegistry()
    
    fork = Fork(
        id="F001",
        description="Test",
        affects=["param1"],
        default="opt1",
        options={"opt1": "A"},
    )
    
    registry.register(fork)
    
    with pytest.raises(ValueError, match="Invalid option"):
        registry.apply_forks({"F001": "invalid"}, {})
