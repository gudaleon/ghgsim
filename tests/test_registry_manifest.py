"""
Tests for parameter registry and manifest (Phase 3).

Acceptance tests:
- Test 6: Deterministic runs (same manifest -> same outputs)
- Test 7: VERIFIED parameter gate (refuses UNVERIFIED by default)
"""

import tempfile
from pathlib import Path

import pytest

from ghgsim.core.manifest import (
    create_manifest,
    hash_file,
    load_manifest,
    save_manifest,
)
from ghgsim.core.registry import (
    ParameterRegistry,
    ParameterValue,
    VerificationStatus,
    load_parameter_csv,
)


def test_parameter_registry_basic():
    """Test basic parameter registration and retrieval."""
    registry = ParameterRegistry(allow_unverified=True)

    param = ParameterValue(
        key="test.param.value",
        value=1.5,
        units="kg",
        status=VerificationStatus.VERIFIED,
    )

    registry.register(param)
    retrieved = registry.get("test.param.value")

    assert retrieved.value == 1.5
    assert retrieved.units == "kg"


def test_verified_gate_refuses_unverified():
    """Test 7: Default runs refuse UNVERIFIED parameters."""
    registry = ParameterRegistry(allow_unverified=False)

    unverified_param = ParameterValue(
        key="test.unverified",
        value=1.0,
        units="dimensionless",
        status=VerificationStatus.UNVERIFIED,
    )

    registry.register(unverified_param)

    # Should raise ValueError
    with pytest.raises(ValueError, match="Use --allow-unverified"):
        registry.get("test.unverified")


def test_verified_gate_allows_verified():
    """Test that VERIFIED parameters are always allowed."""
    registry = ParameterRegistry(allow_unverified=False)

    verified_param = ParameterValue(
        key="test.verified",
        value=2.0,
        units="kg",
        status=VerificationStatus.VERIFIED,
    )

    registry.register(verified_param)

    # Should succeed
    result = registry.get("test.verified")
    assert result.value == 2.0


def test_allow_unverified_flag():
    """Test that allow_unverified flag permits UNVERIFIED parameters."""
    registry = ParameterRegistry(allow_unverified=True)

    unverified_param = ParameterValue(
        key="test.unverified",
        value=1.0,
        units="dimensionless",
        status=VerificationStatus.UNVERIFIED,
    )

    registry.register(unverified_param)

    # Should succeed with flag
    result = registry.get("test.unverified")
    assert result.value == 1.0


def test_parameter_overlays():
    """Test parameter overlay system."""
    registry = ParameterRegistry(allow_unverified=True)

    base_param = ParameterValue(
        key="test.param",
        value=1.0,
        units="kg",
        status=VerificationStatus.VERIFIED,
    )

    regional_param = ParameterValue(
        key="test.param",
        value=2.0,
        units="kg",
        region="us",
        status=VerificationStatus.VERIFIED,
    )

    registry.register(base_param)
    registry.add_overlay({"test.param": regional_param})

    # Should get overlay value
    result = registry.get("test.param")
    assert result.value == 2.0
    assert result.region == "us"


def test_list_unverified():
    """Test listing non-VERIFIED parameters."""
    registry = ParameterRegistry(allow_unverified=True)

    verified = ParameterValue(
        key="test.verified", value=1.0, units="kg", status=VerificationStatus.VERIFIED
    )

    unverified = ParameterValue(
        key="test.unverified",
        value=2.0,
        units="kg",
        status=VerificationStatus.UNVERIFIED,
    )

    registry.register(verified)
    registry.register(unverified)

    unverified_list = registry.list_unverified()
    assert len(unverified_list) == 1
    assert unverified_list[0].key == "test.unverified"


def test_load_parameter_csv_v3_format():
    """Test loading v3 CSV format."""
    csv_content = """guideline,factor,disaggregation,units,default,lower,upper,range_basis,source,table,page,status
IPCC2006,EF1,all,kg N2O-N/kg N,0.01,0.003,0.03,as published,2006 IPCC GL Vol4 Ch11,Table 11.1,11.11,VERIFIED
IPCC2019,EF1,wet,kg N2O-N/kg N,0.016,0.013,0.019,95% CI,2019 Refinement Vol4 Ch11,Table 11.1,11.13,VERIFIED
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        f.write(csv_content)
        temp_path = Path(f.name)

    try:
        registry = load_parameter_csv(temp_path, allow_unverified=False)

        # Should be able to get VERIFIED parameters
        ef1_2006 = registry.get("IPCC2006.EF1.all")
        assert ef1_2006.value == 0.01
        assert ef1_2006.status == VerificationStatus.VERIFIED

        ef1_2019 = registry.get("IPCC2019.EF1.wet")
        assert ef1_2019.value == 0.016
    finally:
        temp_path.unlink()


def test_manifest_creation():
    """Test manifest creation with hashing."""
    manifest = create_manifest(
        package_version="0.4.0",
        fork_settings={"F001": "default"},
        rng_seed=42,
        allow_unverified=False,
    )

    assert manifest.package_version == "0.4.0"
    assert manifest.fork_settings == {"F001": "default"}
    assert manifest.rng_seed == 42
    assert manifest.allow_unverified is False
    assert len(manifest.run_id) == 64  # SHA-256 hex length


def test_manifest_determinism():
    """Test 6 (part 1): Same inputs produce same run_id."""
    manifest1 = create_manifest(
        package_version="0.4.0",
        fork_settings={"F001": "default"},
        rng_seed=42,
        allow_unverified=False,
    )

    manifest2 = create_manifest(
        package_version="0.4.0",
        fork_settings={"F001": "default"},
        rng_seed=42,
        allow_unverified=False,
    )

    # run_ids should be identical (timestamps excluded from hash)
    assert manifest1.run_id == manifest2.run_id


def test_manifest_changes_with_parameter():
    """Test 6 (part 2): Changing parameter changes run_id."""
    manifest1 = create_manifest(
        package_version="0.4.0",
        fork_settings={"F001": "default"},
        rng_seed=42,
        allow_unverified=False,
    )

    manifest2 = create_manifest(
        package_version="0.4.0",
        fork_settings={"F001": "alternate"},  # Changed
        rng_seed=42,
        allow_unverified=False,
    )

    # run_ids should be different
    assert manifest1.run_id != manifest2.run_id


def test_manifest_save_load():
    """Test manifest serialization round-trip."""
    original = create_manifest(
        package_version="0.4.0",
        fork_settings={"F001": "default"},
        rng_seed=42,
        allow_unverified=False,
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        temp_path = Path(f.name)

    try:
        save_manifest(original, temp_path)
        loaded = load_manifest(temp_path)

        assert loaded.run_id == original.run_id
        assert loaded.package_version == original.package_version
        assert loaded.fork_settings == original.fork_settings
        assert loaded.rng_seed == original.rng_seed
    finally:
        temp_path.unlink()


def test_file_hashing():
    """Test file hashing for reproducibility."""
    content = b"test content for hashing"

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        hash1 = hash_file(temp_path)
        hash2 = hash_file(temp_path)

        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    finally:
        temp_path.unlink()
