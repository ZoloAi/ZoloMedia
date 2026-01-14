"""
Zolo Type Hint Processing

Handles type hint detection and conversion for .zolo files.
Type hints use parentheses notation: key_name(type): value
"""

import re
from typing import Any, Optional, Pattern

from ..constants import (
    TYPE_INT, TYPE_FLOAT, TYPE_BOOL, TYPE_STR,
    TYPE_LIST, TYPE_DICT, TYPE_RAW,
    TYPE_DATE, TYPE_TIME, TYPE_URL, TYPE_PATH,
    SUPPORTED_TYPES, BOOL_TRUE_VALUES
)
from ...exceptions import ZoloTypeError


# Compiled regex pattern for type hints: key_name(type)
TYPE_HINT_PATTERN: Pattern = re.compile(
    r'^(.+?)\((' + '|'.join(SUPPORTED_TYPES) + r')\)$'
)


def process_type_hints(data: Any, string_first: bool = True) -> Any:
    """
    Process type hints in parsed data recursively.
    
    Args:
        data: Parsed dict/list/value from YAML
        string_first: If True, convert scalars to strings (for .zolo files)
                     If False, preserve native types (for .yaml files)
    
    Returns:
        Same structure with type hints processed and keys cleaned
    
    Examples:
        >>> # String-first (.zolo behavior)
        >>> process_type_hints({"port": 8080}, string_first=True)
        {"port": "8080"}
        
        >>> # With type hint
        >>> process_type_hints({"port(int)": 8080}, string_first=True)
        {"port": 8080}
        
        >>> # Native types (.yaml behavior)
        >>> process_type_hints({"port": 8080}, string_first=False)
        {"port": 8080}
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Check if key has type hint
            match = TYPE_HINT_PATTERN.match(key)
            if match:
                clean_key = match.group(1)  # Key without type hint
                type_hint = match.group(2)  # Type hint
                
                # Convert value based on type hint
                converted_value = convert_value_by_type(value, type_hint, clean_key)
                
                # Recursively process only structures (dict/list), not scalars
                if isinstance(converted_value, (dict, list)):
                    result[clean_key] = process_type_hints(converted_value, string_first)
                else:
                    result[clean_key] = converted_value
            else:
                # No type hint - apply string-first if enabled
                if string_first and not isinstance(value, (dict, list)):
                    # String-first: Convert scalar to string
                    result[key] = str(value) if value is not None else None
                else:
                    # Native: Preserve type, recurse into structures
                    result[key] = process_type_hints(value, string_first)
        
        return result
    
    elif isinstance(data, list):
        # Recursively process list items
        return [process_type_hints(item, string_first) for item in data]
    
    else:
        # Scalar value - apply string-first if enabled
        if string_first:
            return str(data) if data is not None else None
        else:
            return data


def convert_value_by_type(value: Any, type_hint: str, key: str) -> Any:
    """
    Convert a value to the specified type.
    
    Args:
        value: Original value from YAML
        type_hint: Type to convert to (int, float, bool, etc.)
        key: Key name (for error messages)
    
    Returns:
        Converted value
    
    Raises:
        ZoloTypeError: If conversion fails
    """
    try:
        if type_hint == TYPE_INT:
            return int(value)
        
        elif type_hint == TYPE_FLOAT:
            return float(value)
        
        elif type_hint == TYPE_BOOL:
            # Handle various boolean representations
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in BOOL_TRUE_VALUES
            return bool(value)
        
        elif type_hint == TYPE_STR:
            return str(value)
        
        elif type_hint == TYPE_LIST:
            if isinstance(value, list):
                return value
            # Try to convert to list
            return [value]
        
        elif type_hint == TYPE_DICT:
            if isinstance(value, dict):
                return value
            raise ZoloTypeError(
                f"Cannot convert key '{key}' to dict: value is {type(value).__name__}"
            )
        
        # TYPE_NULL removed - null now auto-detects as an RFC 8259 primitive
        
        elif type_hint in (TYPE_RAW, TYPE_DATE, TYPE_TIME, TYPE_URL, TYPE_PATH):
            # These are string types with semantic meaning
            return str(value)
        
        else:
            raise ZoloTypeError(f"Unknown type hint '{type_hint}' for key '{key}'")
    
    except (ValueError, TypeError) as e:
        raise ZoloTypeError(
            f"Failed to convert key '{key}' to {type_hint}: {e}"
        ) from e


def has_type_hint(key: str) -> bool:
    """
    Check if a key has a type hint.
    
    Args:
        key: Key name to check
    
    Returns:
        True if key has type hint, False otherwise
    
    Examples:
        >>> has_type_hint("port(int)")
        True
        >>> has_type_hint("port")
        False
    """
    return TYPE_HINT_PATTERN.match(key) is not None


def extract_type_hint(key: str) -> tuple[str, Optional[str]]:
    """
    Extract type hint from a key.
    
    Args:
        key: Key name (may or may not have type hint)
    
    Returns:
        Tuple of (clean_key, type_hint)
        - clean_key: Key without type hint
        - type_hint: Type hint string, or None if no hint
    
    Examples:
        >>> extract_type_hint("port(int)")
        ("port", "int")
        >>> extract_type_hint("port")
        ("port", None)
    """
    match = TYPE_HINT_PATTERN.match(key)
    if match:
        return match.group(1), match.group(2)
    return key, None
