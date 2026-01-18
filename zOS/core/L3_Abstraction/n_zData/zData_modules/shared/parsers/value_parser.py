# zCLI/subsystems/zData/zData_modules/shared/parsers/value_parser.py
"""
Value type parsing for zData WHERE clauses and data operations.

This module provides intelligent type detection and conversion for string values
encountered during data operations (WHERE clauses, INSERT values, etc.).

Architecture Position
--------------------
- **Layer**: Tier 0 - Foundation
- **Dependencies**: None (stdlib only)
- **Used By**: where_parser.py, CRUD operations, validators
- **Purpose**: Convert string representations to appropriate Python types

Type Detection Order
-------------------
The parser follows a strict precedence order to avoid ambiguity:

1. **Boolean Values**: "true", "yes", "1" → True | "false", "no", "0" → False
2. **Null Values**: "null", "none" → None
3. **Numeric Values**: Integer or float detection (uses decimal point check)
4. **String Values**: Everything else (with automatic quote stripping)

This precedence ensures deterministic parsing: "1" → bool(True), not int(1).

Supported Types
--------------
- **bool**: True/False (case-insensitive: "true", "TRUE", "True")
- **None**: Null values (case-insensitive: "null", "NULL", "none", "NONE")
- **int**: Integers without decimal points ("42", "-10")
- **float**: Numbers with decimal points ("3.14", "-0.5")
- **str**: All other values (quotes automatically stripped)

Quote Handling
-------------
String values can be quoted with single or double quotes. The parser automatically
strips matching quotes from the beginning and end:

    "hello"  → hello
    'world'  → world
    "test    → "test (unmatched quotes preserved)

Usage Examples
-------------
Boolean detection:
    >>> parse_value("true")
    True
    >>> parse_value("FALSE")
    False
    >>> parse_value("yes")
    True

Null detection:
    >>> parse_value("null")
    None
    >>> parse_value("NONE")
    None

Numeric detection:
    >>> parse_value("42")
    42
    >>> parse_value("3.14")
    3.14
    >>> parse_value("-10")
    -10

String detection:
    >>> parse_value('"hello world"')
    'hello world'
    >>> parse_value("'test'")
    'test'
    >>> parse_value("unquoted")
    'unquoted'

Integration
----------
This parser is used throughout zData for consistent type handling:
- WHERE clause parsing (where_parser.py)
- INSERT/UPDATE value normalization
- Schema validation
- Query result formatting
"""

from zOS import Union

# ============================================================
# Module Constants - Boolean Values
# ============================================================

# True boolean literals (case-insensitive comparison)
_BOOL_TRUE_VALUES = ("true", "yes", "1")

# False boolean literals (case-insensitive comparison)
_BOOL_FALSE_VALUES = ("false", "no", "0")

# ============================================================
# Module Constants - Null Values
# ============================================================

# Null/None literals (case-insensitive comparison)
_NULL_VALUES = ("null", "none")

# ============================================================
# Module Constants - String Processing
# ============================================================

# Quote characters for string detection
_QUOTE_DOUBLE = '"'
_QUOTE_SINGLE = "'"
_QUOTE_CHARS = (_QUOTE_DOUBLE, _QUOTE_SINGLE)

# Decimal point character for float detection
_DECIMAL_POINT = "."

# ============================================================
# Module Constants - Type Names (for logging/debugging)
# ============================================================

_TYPE_NAME_BOOL = "bool"
_TYPE_NAME_NULL = "null"
_TYPE_NAME_INT = "int"
_TYPE_NAME_FLOAT = "float"
_TYPE_NAME_STRING = "str"

# ============================================================
# Public API
# ============================================================

__all__ = ["parse_value"]


def parse_value(value_str: str) -> Union[int, float, bool, str, None]:
    """
    Parse a string value into its appropriate Python type.
    
    This function analyzes the input string and converts it to the most appropriate
    Python type based on its content. It follows a strict precedence order:
    bool → null → numeric (int/float) → string.
    
    Args:
        value_str: The string value to parse. Leading/trailing whitespace is stripped.
    
    Returns:
        One of the following types based on detection:
        - bool: For "true"/"false"/"yes"/"no"/"1"/"0" (case-insensitive)
        - None: For "null"/"none" (case-insensitive)
        - int: For numeric values without decimal points
        - float: For numeric values with decimal points
        - str: For all other values (quotes stripped if present)
    
    Type Detection Details:
        **Boolean Detection** (Highest Priority):
            - "true", "TRUE", "True" → True
            - "yes", "YES", "Yes" → True
            - "1" → True
            - "false", "FALSE", "False" → False
            - "no", "NO", "No" → False
            - "0" → False
        
        **Null Detection**:
            - "null", "NULL", "Null" → None
            - "none", "NONE", "None" → None
        
        **Numeric Detection**:
            - "42" → 42 (int)
            - "-10" → -10 (int)
            - "3.14" → 3.14 (float)
            - "-0.5" → -0.5 (float)
        
        **String Detection** (Lowest Priority):
            - '"hello"' → "hello" (quotes stripped)
            - "'world'" → "world" (quotes stripped)
            - "test" → "test" (no quotes)
    
    Examples:
        Boolean values:
            >>> parse_value("true")
            True
            >>> parse_value("FALSE")
            False
        
        Null values:
            >>> parse_value("null")
            None
            >>> parse_value("NONE")
            None
        
        Numeric values:
            >>> parse_value("42")
            42
            >>> parse_value("3.14")
            3.14
        
        String values:
            >>> parse_value('"hello world"')
            'hello world'
            >>> parse_value("test")
            'test'
    
    Notes:
        - Input is always stripped of leading/trailing whitespace
        - Boolean detection takes precedence over numeric (e.g., "1" → True, not int)
        - Only matching quotes are stripped (e.g., '"test' → '"test')
        - Empty strings return as empty strings, not None
    
    See Also:
        - where_parser.parse_where_clause(): Uses this for WHERE value parsing
        - DataValidator: Uses this for schema validation
    """
    value_str = value_str.strip()
    lower = value_str.lower()

    # Check for boolean/null first (fastest - exact match)
    if lower in _BOOL_TRUE_VALUES:
        return True
    if lower in _BOOL_FALSE_VALUES:
        return False
    if lower in _NULL_VALUES:
        return None

    # Try numeric conversion (int if no decimal, else float)
    try:
        return int(value_str) if _DECIMAL_POINT not in value_str else float(value_str)
    except ValueError:
        pass

    # Return as string (remove quotes if present and matching)
    if (value_str.startswith(_QUOTE_CHARS) and value_str.endswith(_QUOTE_CHARS)):
        return value_str[1:-1]

    return value_str
