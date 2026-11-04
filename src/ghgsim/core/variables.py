"""
Variable system for AQUASIM-style OOP architecture.

Based on Reichert (1995) Environmental Software 10(3):199-210.
Four variable types: State, Input, Parameter, Program.
"""

import math
from abc import ABC, abstractmethod
from typing import Any


class Variable(ABC):
    """Base class for all variables (Reichert 1995 hierarchy)."""
    
    def __init__(self, name: str, units: str, description: str):
        self.name = name
        self.units = units
        self.description = description
        self.value: float | None = None
    
    @abstractmethod
    def get_type(self) -> str:
        """Return variable type (state/input/parameter/program)."""
        pass


class StateVariable(Variable):
    """State variable that evolves over time."""
    
    def __init__(self, name: str, units: str, description: str, initial_value: float):
        super().__init__(name, units, description)
        self.value = initial_value
        self.history = [initial_value]
    
    def update(self, new_value: float):
        """Update state and record history."""
        self.value = new_value
        self.history.append(new_value)
    
    def get_type(self) -> str:
        return "state"


class InputVariable(Variable):
    """External input/forcing variable."""
    
    def __init__(self, name: str, units: str, description: str, value: float | None = None):
        super().__init__(name, units, description)
        self.value = value
    
    def set_value(self, value: float):
        """Set input value."""
        self.value = value
    
    def get_type(self) -> str:
        return "input"


class ParameterVariable(Variable):
    """Parameter with optional uncertainty distribution."""
    
    def __init__(
        self, 
        name: str, 
        units: str, 
        description: str, 
        value: float, 
        distribution: str | None = None,
        dist_lower: float | None = None,
        dist_upper: float | None = None,
        source: str | None = None
    ):
        super().__init__(name, units, description)
        self.value = value
        self.distribution = distribution
        self.dist_lower = dist_lower
        self.dist_upper = dist_upper
        self.source = source
    
    def get_type(self) -> str:
        return "parameter"


class ProgramVariable(Variable):
    """Calculated/derived variable from equation."""
    
    def __init__(
        self, 
        name: str, 
        units: str, 
        description: str, 
        equation: str, 
        dependencies: list[str]
    ):
        super().__init__(name, units, description)
        self.equation = equation
        self.dependencies = dependencies
    
    def compute(self, context: dict[str, Any]) -> float:
        """Evaluate equation given context of other variables."""
        # Safe eval with only math operations and context vars
        safe_globals = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "min": min,
            "max": max,
        }
        safe_locals = dict(context)
        
        try:
            result = eval(self.equation, safe_globals, safe_locals)
            self.value = float(result)
            return self.value
        except Exception as e:
            raise ValueError(  # noqa: B904
                f"Error evaluating equation for {self.name}: {self.equation}\n"
                f"Context: {context}\n"
                f"Error: {e}"
            )
    
    def get_type(self) -> str:
        return "program"
