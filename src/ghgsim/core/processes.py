"""
Process system for AQUASIM-style OOP architecture.

Based on Reichert (1995) Environmental Software 10(3):199-210.
User-definable rate expressions with stoichiometry.
"""

from __future__ import annotations

import math
from typing import Any


class ForkOption:
    """
    Alternative implementation of a process (e.g., Holos-as-coded vs IPCC-correct).

    Example:
        holos_fork = ForkOption(
            name="holos_as_coded",
            description="Uses TDN instead of DE (Holos discrepancy)",
            modified_equation="GE * (1.0 - TDN_percent/100.0) + UE * GE",
            issue_ref="AUDIT-VS-TDN",
            label="holos_as_coded",
        )
    """

    def __init__(
        self,
        name: str,
        description: str,
        modified_equation: str | None = None,
        modified_params: dict[str, float] | None = None,
        issue_ref: str | None = None,
        label: str = "holos_as_coded",
    ):
        self.name = name
        self.description = description
        self.modified_equation = modified_equation
        self.modified_params = modified_params or {}
        self.issue_ref = issue_ref
        self.label = label


class ProcessDef:
    """
    User-definable process with rate expression and stoichiometry.

    Example:
        enteric_ch4 = ProcessDef(
            name="enteric_methane",
            description="Enteric CH4 from cattle",
            rate_equation="GE * (Ym / 100.0) / 55.65",
            stoichiometry={"CH4_kg_day": +1.0},
            unit="kg CH4/head/day"
        )
    """

    def __init__(
        self,
        name: str,
        description: str,
        rate_equation: str,
        stoichiometry: dict[str, float],
        unit: str,
        sources: list[dict] | None = None,
        forks: dict[str, ForkOption] | None = None,
    ):
        self.name = name
        self.description = description
        self.rate_equation = rate_equation
        self.stoichiometry = stoichiometry
        self.unit = unit
        self.sources = sources or []
        self.forks = forks or {}

    def add_source(self, doi_or_url: str, equation: str = "", page: str = "", notes: str = ""):
        """Add citation for traceability."""
        self.sources.append({
            "source": doi_or_url,
            "equation": equation,
            "page": page,
            "notes": notes,
        })

    def add_fork(self, option: ForkOption) -> None:
        """Register a labelled alternative implementation of this process."""
        self.forks[option.name] = option

    def rate_equation_for(self, fork: str | None = None) -> str:
        """Return the rate equation for the default or a named fork option."""
        if fork is None or fork == "source_correct":
            return self.rate_equation
        if fork not in self.forks:
            raise ValueError(
                f"Unknown fork '{fork}' for process {self.name}. "
                f"Available: {sorted(self.forks)}"
            )
        option = self.forks[fork]
        if option.modified_equation:
            return option.modified_equation
        return self.rate_equation

    def compute_rate(self, variables: dict[str, Any], fork: str | None = None) -> float:
        """
        Evaluate rate equation given variable context.

        Args:
            variables: Dictionary of variable_name -> value
            fork: Optional fork option name registered on this process

        Returns:
            Rate value (in self.unit)
        """
        equation = self.rate_equation_for(fork)
        safe_globals = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "min": min,
            "max": max,
        }
        safe_locals = dict(variables)
        if fork and fork in self.forks:
            safe_locals.update(self.forks[fork].modified_params)

        try:
            rate = eval(equation, safe_globals, safe_locals)
            return float(rate)
        except Exception as e:
            raise ValueError(
                f"Error evaluating rate for process {self.name}: {equation}\n"
                f"Variables: {variables}\n"
                f"Error: {e}"
            ) from e

    def apply_stoichiometry(self, rate: float, state_vars: dict[str, Any]):
        """
        Apply stoichiometric changes to state variables.

        Args:
            rate: Process rate (in self.unit)
            state_vars: Dictionary of state variables to update
        """
        for var_name, coeff in self.stoichiometry.items():
            if var_name in state_vars:
                current = state_vars[var_name].value
                new_value = current + (rate * coeff)
                state_vars[var_name].update(new_value)
