"""Validation utilities for property values."""
import re
from typing import Any, Tuple, Optional

def get_property_type(prop_name: str) -> str:
    """
    Determine expected property type based on naming convention.

    Returns: 'number', 'boolean', 'string', 'integer'
    """
    prop_lower = prop_name.lower()

    # Boolean properties
    if prop_name.startswith('has_') or prop_name.startswith('is_'):
        return 'boolean'

    # Numeric properties with units
    numeric_suffixes = ['_mm', '_cm', '_m', '_g', '_kg', '_wh', '_mah', '_w', '_v', '_a', '_hz', '_mhz', '_ghz', '_mb', '_gb', '_tb']
    if any(prop_lower.endswith(suffix) for suffix in numeric_suffixes):
        return 'number'

    # Integer count properties
    if 'number_of' in prop_lower or prop_lower.endswith('_count') or prop_lower.startswith('count_'):
        return 'integer'

    # Numeric properties (speed, frequency, capacity, etc.)
    numeric_keywords = ['speed', 'frequency', 'capacity', 'cache', 'clock', 'rate', 'size', 'weight', 'height', 'width', 'depth', 'thickness', 'diameter', 'brightness', 'resolution', 'rpm', 'tdp', 'voltage', 'current', 'power']
    if any(keyword in prop_lower for keyword in numeric_keywords):
        return 'number'

    # Default to string
    return 'string'

def validate_value(prop_name: str, value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate a property value based on its expected type.

    Returns: (is_valid, error_message)
    """
    if value is None or value == '':
        # Empty values are generally allowed (optional fields)
        return True, None

    expected_type = get_property_type(prop_name)

    if expected_type == 'boolean':
        if isinstance(value, bool):
            return True, None
        if isinstance(value, str):
            if value.lower() in ['true', 'false', '1', '0', 'yes', 'no']:
                return True, None
        return False, f"{prop_name} must be a boolean value (true/false)"

    elif expected_type == 'integer':
        try:
            int_val = int(value)
            if int_val < 0:
                return False, f"{prop_name} must be a positive integer"
            return True, None
        except (ValueError, TypeError):
            return False, f"{prop_name} must be an integer"

    elif expected_type == 'number':
        try:
            float(value)
            return True, None
        except (ValueError, TypeError):
            return False, f"{prop_name} must be a number"

    elif expected_type == 'string':
        if not isinstance(value, str):
            # Try to convert to string
            try:
                str(value)
                return True, None
            except:
                return False, f"{prop_name} must be a string"
        return True, None

    return True, None

def convert_value(prop_name: str, value: Any) -> Any:
    """
    Convert a value to the appropriate type based on property name.

    Used for form inputs (which come as strings) to convert to proper types.
    """
    if value is None or value == '':
        return None

    expected_type = get_property_type(prop_name)

    try:
        if expected_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes', 'on']
            return bool(value)

        elif expected_type == 'integer':
            return int(value)

        elif expected_type == 'number':
            # Try int first, then float
            try:
                return int(value)
            except ValueError:
                return float(value)

        elif expected_type == 'string':
            return str(value)

    except (ValueError, TypeError):
        # If conversion fails, return original value
        return value

    return value

def get_input_type(prop_name: str) -> str:
    """
    Get HTML input type for a property.

    Returns: 'checkbox', 'number', 'text', etc.
    """
    prop_type = get_property_type(prop_name)

    if prop_type == 'boolean':
        return 'checkbox'
    elif prop_type in ['number', 'integer']:
        return 'number'
    else:
        return 'text'

def is_required_property(prop_name: str) -> bool:
    """
    Determine if a property is required.

    Only _id is strictly required for identification.
    """
    return prop_name == '_id'
