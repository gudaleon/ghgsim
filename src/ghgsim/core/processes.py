"""
Process system for AQUASIM-style OOP architecture.

Based on Reichert (1995) Environmental Software 10(3):199-210.
User-definable rate expressions with stoichiometry.
"""

from typing import Any, Optional
import math


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
        sources: Optional[list[dict]] = None
    ):
        self.name = name
        self.description = description
        self.rate_equation = rate_equation
        self.stoichiometry = stoichiometry
        self.unit = unit
        self.sources = sources or []
    
    def add_source(self, doi_or_url: str, equation: str = "", page: str = "", notes: str = ""):
        """Add citation for traceability."""
        self.sources.append({
            "source": doi_or_url,
            "equation": equation,
            "page": page,
            "notes": notes
        })
    
    def compute_rate(self, variables: dict[str, Any]) -> float:
        """
        Evaluate rate equation given variable context.
        
        Args:
            variables: Dictionary of variable_name -> value
            
        Returns:
            Rate value (in self.unit)
        """
        safe_globals = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "min": min,
            "max": max,
        }
        safe_locals = dict(variables)
        
        try:
            rate = eval(self.rate_equation, safe_globals, safe_locals)
            return float(rate)
        except Exception as e:
            raise ValueError(
                f"Error evaluating rate for process {self.name}: {self.rate_equation}\n"
                f"Variables: {variables}\n"
                f"Error: {e}"
            )
    
    def apply_stoichiometry(self, rate: float, state_vars: dict[str, 'StateVariable']):
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


class ForkOption:
    """
    Alternative implementation of a process (e.g., Holos-as-coded vs IPCC-correct).
    
    Example:
        holos_fork = ForkOption(
            name="holos_vs_ipcc",
            description="Uses TDN instead of DE (Holos bug)",
            modified_equation="GE * (1.0 - TDN/100.0) + ...",
            issue_ref="CE-08"
        )
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        modified_equation: Optional[str] = None,
        modified_params: Optional[dict[str, float]] = None,
        issue_ref: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.modified_equation = modified_equation
        self.modified_params = modified_params or {}
        self.issue_ref = issue_ref
