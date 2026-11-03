"""Tests for Reichert-style Variable and ProcessDef fork selection."""

import pytest

from ghgsim.core.processes import ForkOption, ProcessDef
from ghgsim.core.registry import ParameterRegistry, ParameterValue, VerificationStatus
from ghgsim.core.variables import ParameterVariable, ProgramVariable, StateVariable


def test_program_variable_evaluates_equation():
    ge = ProgramVariable(
        name="GE",
        units="MJ / day",
        description="test",
        equation="(NE_m + NE_l) / RE_m / (DE_percent / 100.0)",
        dependencies=["NE_m", "NE_l", "RE_m", "DE_percent"],
    )
    value = ge.compute({"NE_m": 40.0, "NE_l": 60.0, "RE_m": 0.5, "DE_percent": 70.0})
    assert value == pytest.approx((100.0 / 0.5) / 0.70)


def test_state_variable_records_history():
    weight = StateVariable("weight", "kg", "live weight", 100.0)
    weight.update(110.0)
    assert weight.value == 110.0
    assert weight.history == [100.0, 110.0]
    assert weight.get_type() == "state"


def test_parameter_variable_stores_source():
    ym = ParameterVariable(
        "Ym",
        "% GE",
        "methane conversion",
        6.5,
        source="IPCC 2006 Table 10.12 p. 10.30",
    )
    assert ym.get_type() == "parameter"
    assert ym.source.startswith("IPCC 2006")


def test_process_fork_changes_rate_only_when_selected():
    process = ProcessDef(
        name="demo",
        description="demo",
        rate_equation="GE * (1.0 - DE_percent / 100.0)",
        stoichiometry={"x": 1.0},
        unit="MJ",
        forks={
            "holos_as_coded": ForkOption(
                name="holos_as_coded",
                description="TDN",
                modified_equation="GE * (1.0 - TDN_percent / 100.0)",
                issue_ref="AUDIT-VS-TDN",
            )
        },
    )
    variables = {"GE": 100.0, "DE_percent": 70.0, "TDN_percent": 60.0}
    default = process.compute_rate(variables)
    fork = process.compute_rate(variables, fork="holos_as_coded")
    assert default == pytest.approx(30.0)
    assert fork == pytest.approx(40.0)
    assert default != fork
    same = process.compute_rate({"GE": 100.0, "DE_percent": 70.0, "TDN_percent": 70.0}, fork="holos_as_coded")
    assert same == pytest.approx(default)


def test_source_traced_refused_by_default_gate():
    registry = ParameterRegistry(allow_unverified=False)
    registry.register(
        ParameterValue(
            key="test.source_traced",
            value=1.0,
            units="dimensionless",
            status=VerificationStatus.SOURCE_TRACED,
        )
    )
    with pytest.raises(ValueError, match="SOURCE-TRACED"):
        registry.get("test.source_traced")
    open_registry = ParameterRegistry(allow_unverified=True)
    open_registry.register(
        ParameterValue(
            key="test.source_traced",
            value=1.0,
            units="dimensionless",
            status=VerificationStatus.SOURCE_TRACED,
        )
    )
    assert open_registry.get("test.source_traced").value == 1.0
