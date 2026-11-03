"""
Unit checking and conversion using pint.

All module inputs and outputs are checked for dimensional consistency
at the module boundary.
"""

import pint

# Create a shared unit registry
ureg = pint.UnitRegistry()


def check_units(value: float, expected_units: str, context: str = "") -> pint.Quantity:
    """
    Check and convert a value to expected units.
    
    Args:
        value: Numeric value (assumed to be in expected units)
        expected_units: Expected units string (pint-compatible)
        context: Context for error messages
        
    Returns:
        pint.Quantity with the value and units
        
    Raises:
        ValueError: If units are invalid
        pint.DimensionalityError: If units don't match
    """
    try:
        return ureg.Quantity(value, expected_units)
    except Exception as e:
        msg = f"Invalid units '{expected_units}'"
        if context:
            msg += f" for {context}"
        raise ValueError(msg) from e


def convert_units(quantity: pint.Quantity, target_units: str, context: str = "") -> float:
    """
    Convert a quantity to target units and return the magnitude.
    
    Args:
        quantity: pint.Quantity to convert
        target_units: Target units string
        context: Context for error messages
        
    Returns:
        Magnitude in target units
        
    Raises:
        pint.DimensionalityError: If units are incompatible
    """
    try:
        converted = quantity.to(target_units)
        return converted.magnitude
    except pint.DimensionalityError as e:
        msg = f"Cannot convert {quantity.units} to {target_units}"
        if context:
            msg += f" for {context}"
        raise pint.DimensionalityError(
            quantity.units, target_units, extra_msg=msg
        ) from e


def check_compatible(units1: str, units2: str, context: str = "") -> bool:
    """
    Check if two unit strings are dimensionally compatible.
    
    Args:
        units1: First units string
        units2: Second units string
        context: Context for error messages
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        q1 = ureg.Quantity(1, units1)
        ureg.Quantity(1, units2)  # Validate units2 is valid
        q1.to(units2)
        return True
    except (ValueError, pint.DimensionalityError):
        return False
