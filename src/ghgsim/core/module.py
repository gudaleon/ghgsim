"""
Module contract and types for ghgsim.

This defines the Protocol for modules (plugins) that implement GHG calculations.
Each module is a pure, deterministic, vectorized function with declared inputs,
parameters, outputs, and source citations.

Design inspired by AQUASIM's modular architecture (Reichert 1995).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Citation:
    """
    Source citation for equations, parameters, or data.
    
    Attributes:
        source: DOI, URL, or full citation string
        table: Table number/name if applicable
        equation: Equation number/name if applicable
        page: Page number if applicable
        notes: Additional notes
    """

    source: str
    table: str | None = None
    equation: str | None = None
    page: str | None = None
    notes: str | None = None

    def __str__(self) -> str:
        parts = [self.source]
        if self.table:
            parts.append(f"Table {self.table}")
        if self.equation:
            parts.append(f"Eq {self.equation}")
        if self.page:
            parts.append(f"p. {self.page}")
        return ", ".join(parts)


@dataclass(frozen=True)
class VarSpec:
    """
    Variable specification with units and metadata.
    
    Attributes:
        name: Variable name
        units: Units string (pint-compatible)
        description: Human-readable description
        dims: Dimensionality (e.g., "scalar", "vector", "N_herds")
        required: Whether this variable is required
    """

    name: str
    units: str
    description: str
    dims: str = "scalar"
    required: bool = True


@dataclass(frozen=True)
class ParamRef:
    """
    Reference to a parameter in the registry.
    
    Attributes:
        key: Parameter registry key
        description: Human-readable description
        fallback: Fallback value if not in registry (None = required)
    """

    key: str
    description: str
    fallback: Any = None


class Module(Protocol):
    """
    Protocol for GHG calculation modules.
    
    Each module must be pure (no I/O, no globals), deterministic, and vectorized.
    Modules are discovered through the entry point group 'ghgsim.modules'.
    
    Design principle: Users define equation modules, the framework provides
    simulation services. Inspired by AQUASIM (Reichert 1995, 1998).
    """

    id: str
    """Unique module ID (e.g., 'ipcc2019.enteric')"""

    version: str
    """Semantic version; any change in outputs requires version bump"""

    inputs: dict[str, VarSpec]
    """Input variables with units and metadata"""

    parameters: dict[str, ParamRef]
    """Parameters from the registry"""

    outputs: dict[str, VarSpec]
    """Output variables with units and metadata"""

    sources: list[Citation]
    """Source citations for this module"""

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Execute the module computation.
        
        Must be pure (no side effects), deterministic (same inputs -> same outputs),
        and vectorized (works with numpy arrays/pandas dataframes).
        
        Args:
            inputs: Input variables (must provide all required inputs)
            params: Parameter values from registry
            
        Returns:
            Dictionary of output variables
            
        Raises:
            ValueError: If required inputs or parameters are missing
            pint.DimensionalityError: If units don't match
        """
        ...


def validate_module(module: Module) -> list[str]:
    """
    Validate a module's metadata and interface.
    
    Args:
        module: Module to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not module.id:
        errors.append("Module ID is required")

    if not module.version:
        errors.append("Module version is required")

    if not module.inputs:
        errors.append("Module must declare at least one input")

    if not module.outputs:
        errors.append("Module must declare at least one output")

    if not module.sources:
        errors.append("Module must cite at least one source")

    # Check for duplicate names across inputs/outputs
    all_names = set(module.inputs.keys()) | set(module.outputs.keys())
    if len(all_names) < len(module.inputs) + len(module.outputs):
        errors.append("Duplicate names found in inputs/outputs")

    return errors
