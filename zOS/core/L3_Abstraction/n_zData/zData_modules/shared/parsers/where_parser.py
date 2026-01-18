# zCLI/subsystems/zData/zData_modules/shared/parsers/where_parser.py
"""
WHERE clause parsing for zData query operations.

This module converts human-readable WHERE clause strings into adapter-compatible
dictionary formats. It supports multiple SQL-like operators and produces output
compatible with all backend adapters (SQLite, PostgreSQL, CSV).

Architecture Position
--------------------
- **Layer**: Tier 0 - Foundation
- **Dependencies**: value_parser.py (same package)
- **Used By**: CRUD read/update/delete operations, validator
- **Purpose**: Parse WHERE strings into structured filter dictionaries

Supported Operators
------------------
The parser supports a rich set of SQL-like comparison and logical operators:

**Logical Operators:**
- OR: Combines conditions with logical OR ("age > 18 OR status = admin")

**Comparison Operators:**
- =  : Equality ("name = John")
- != : Not equal ("status != inactive")
- >  : Greater than ("age > 18")
- <  : Less than ("age < 65")
- >= : Greater or equal ("score >= 90")
- <= : Less or equal ("score <= 100")

**Special Operators:**
- IS NULL     : Check for null ("email IS NULL")
- IS NOT NULL : Check for not null ("phone IS NOT NULL")
- LIKE        : Pattern matching ("name LIKE %John%")
- IN          : List membership ("status IN active,pending")

Output Format
------------
The parser produces dictionaries with special operator keys for non-equality:

Equality (no operator key):
    "name = John" → {"name": "John"}

Comparison operators (with $ prefix):
    "age > 18" → {"age": {"$gt": 18}}
    "score >= 90" → {"score": {"$gte": 90}}

Special operators:
    "email IS NULL" → {"email": None}
    "phone IS NOT NULL" → {"phone": {"$notnull": True}}
    "name LIKE %John%" → {"name": {"$like": "%John%"}}

Logical OR (with $or key):
    "age > 18 OR status = admin" → {"$or": [{"age": {"$gt": 18}}, {"status": "admin"}]}

Usage Examples
-------------
Basic equality:
    >>> parse_where_clause("name = John")
    {"name": "John"}

Comparison operators:
    >>> parse_where_clause("age >= 18")
    {"age": {"$gte": 18}}
    
    >>> parse_where_clause("score < 100")
    {"score": {"$lt": 100}}

NULL checks:
    >>> parse_where_clause("email IS NULL")
    {"email": None}
    
    >>> parse_where_clause("phone IS NOT NULL")
    {"phone": {"$notnull": True}}

LIKE pattern:
    >>> parse_where_clause("name LIKE %Smith%")
    {"name": {"$like": "%Smith%"}}

IN operator:
    >>> parse_where_clause("status IN active,pending")
    {"status": ["active", "pending"]}

OR conditions:
    >>> parse_where_clause("age > 18 OR status = admin")
    {"$or": [{"age": {"$gt": 18}}, {"status": "admin"}]}

Value Type Detection
-------------------
All values are automatically parsed to appropriate Python types via value_parser:
    "age = 42"     → {"age": 42}        (int)
    "price = 9.99" → {"price": 9.99}    (float)
    "active = true"→ {"active": True}   (bool)
    "name = John"  → {"name": "John"}   (str)

Security Notes
-------------
- Field names are passed through without sanitization (adapter responsibility)
- Values are type-converted but not SQL-escaped (adapter uses parameterized queries)
- No support for arbitrary SQL injection (limited operator set)

Limitations
----------
- No support for AND operator (all non-OR conditions are implicit AND)
- No support for parentheses or complex precedence
- No support for nested conditions beyond simple OR
- BETWEEN operator not implemented (use >= and <=)

Integration Points
-----------------
This parser is used by:
- crud_read.py: SELECT WHERE filtering
- crud_update.py: UPDATE WHERE conditions
- crud_delete.py: DELETE WHERE conditions
- DataValidator: Validation rule checking

See Also
--------
- value_parser.parse_value(): Type conversion for parsed values
- BaseDataAdapter: Backend adapter interface (uses parsed dictionaries)
"""

from zOS import Dict, Optional, Any, re

# Import from same directory
try:
    from .value_parser import parse_value
except ImportError:
    from value_parser import parse_value

# ============================================================
# Module Constants - SQL Keywords
# ============================================================

# Logical operator keywords
_KEYWORD_OR = " OR "
_KEYWORD_OR_UPPER = "OR"

# NULL check keywords
_KEYWORD_IS_NOT_NULL = " IS NOT NULL"
_KEYWORD_IS_NULL = " IS NULL"

# Special operator keywords
_KEYWORD_IN = " IN "
_KEYWORD_LIKE = " LIKE "

# ============================================================
# Module Constants - Comparison Operators
# ============================================================

# Comparison operator symbols (order matters - check longer first!)
_OPERATOR_GTE = ">="
_OPERATOR_LTE = "<="
_OPERATOR_NE = "!="
_OPERATOR_GT = ">"
_OPERATOR_LT = "<"
_OPERATOR_EQ = "="

# All comparison operators in order (longest first to avoid partial matches)
_COMPARISON_OPERATORS = [
    _OPERATOR_GTE,
    _OPERATOR_LTE,
    _OPERATOR_NE,
    _OPERATOR_GT,
    _OPERATOR_LT,
    _OPERATOR_EQ,
]

# ============================================================
# Module Constants - Operator Keys (Output Format)
# ============================================================

# Operator keys for dictionary output (MongoDB-style $ prefix)
_KEY_OR = "$or"
_KEY_LIKE = "$like"
_KEY_NOTNULL = "$notnull"
_KEY_GTE = "$gte"
_KEY_LTE = "$lte"
_KEY_NE = "$ne"
_KEY_GT = "$gt"
_KEY_LT = "$lt"

# Mapping from SQL operators to output keys
_OPERATOR_KEY_MAP = {
    _OPERATOR_GTE: _KEY_GTE,
    _OPERATOR_LTE: _KEY_LTE,
    _OPERATOR_NE: _KEY_NE,
    _OPERATOR_GT: _KEY_GT,
    _OPERATOR_LT: _KEY_LT,
    _OPERATOR_EQ: None,  # Equality has no key (direct value)
}

# ============================================================
# Module Constants - Regex Patterns
# ============================================================

# Pattern for splitting OR conditions (case-insensitive)
_PATTERN_OR_SPLIT = r'\s+OR\s+'

# ============================================================
# Module Constants - Delimiters
# ============================================================

# Delimiter for IN operator value lists
_DELIMITER_IN_VALUES = ","

# ============================================================
# Public API
# ============================================================

__all__ = [
    "parse_where_clause",
    "parse_or_where",
    "parse_single_where",
]

def parse_where_clause(where_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parse a WHERE clause string into an adapter-compatible dictionary.
    
    This is the main entry point for WHERE clause parsing. It automatically detects
    OR conditions and delegates to the appropriate parser.
    
    Args:
        where_str: The WHERE clause string to parse (without "WHERE" keyword).
                  Can be None or empty string (returns None).
    
    Returns:
        Dictionary representation of the WHERE clause, or None if input is empty.
        
        Format depends on operators used:
        - Simple equality: {"field": value}
        - Comparison: {"field": {"$op": value}}
        - OR conditions: {"$or": [condition1, condition2, ...]}
    
    Supported Operators:
        - Logical: OR
        - Comparison: =, !=, >, <, >=, <=
        - Special: IS NULL, IS NOT NULL, LIKE, IN
    
    Examples:
        Empty input:
            >>> parse_where_clause(None)
            None
            >>> parse_where_clause("")
            None
        
        Simple equality:
            >>> parse_where_clause("name = John")
            {"name": "John"}
        
        Comparison:
            >>> parse_where_clause("age >= 18")
            {"age": {"$gte": 18}}
        
        OR condition:
            >>> parse_where_clause("age > 18 OR status = admin")
            {"$or": [{"age": {"$gt": 18}}, {"status": "admin"}]}
        
        NULL check:
            >>> parse_where_clause("email IS NULL")
            {"email": None}
        
        LIKE pattern:
            >>> parse_where_clause("name LIKE %Smith%")
            {"name": {"$like": "%Smith%"}}
        
        IN list:
            >>> parse_where_clause("status IN active,pending")
            {"status": ["active", "pending"]}
    
    Notes:
        - Input is automatically stripped of leading/trailing whitespace
        - OR detection is case-insensitive (or, OR, Or all work)
        - Field names are case-preserved as provided
        - Values are automatically type-converted via parse_value()
        - Returns None for unparseable clauses (no exceptions)
    
    See Also:
        - parse_or_where(): Handles OR conditions
        - parse_single_where(): Handles single conditions
        - parse_value(): Type conversion for values
    """
    if not where_str:
        return None

    condition = where_str.strip()

    # Handle OR conditions (case-insensitive detection)
    if _KEYWORD_OR in condition.upper():
        return parse_or_where(condition)

    # Parse single condition
    return parse_single_where(condition)

def parse_or_where(where_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse a WHERE clause containing OR conditions.
    
    This function splits a WHERE clause by the OR keyword and parses each part
    independently. It produces an output dictionary with a "$or" key containing
    an array of condition dictionaries.
    
    Args:
        where_str: The WHERE clause string containing OR operators.
                  Must be non-empty (caller should check).
    
    Returns:
        Dictionary with "$or" key containing list of parsed conditions.
        Returns None if no valid conditions could be parsed.
        
        If only one condition is valid, returns that condition directly
        (no $or wrapper needed).
    
    OR Logic:
        - Splits by " OR " (case-insensitive, with surrounding spaces)
        - Each part is parsed as a single condition
        - Empty parts are skipped
        - Invalid parts are skipped (no error thrown)
        - Recursion is avoided (only single conditions parsed)
    
    Examples:
        Two conditions:
            >>> parse_or_where("age > 18 OR status = admin")
            {"$or": [{"age": {"$gt": 18}}, {"status": "admin"}]}
        
        Multiple conditions:
            >>> parse_or_where("age < 13 OR age > 65 OR disabled = true")
            {"$or": [
                {"age": {"$lt": 13}},
                {"age": {"$gt": 65}},
                {"disabled": True}
            ]}
        
        Single valid condition (no $or wrapper):
            >>> parse_or_where("name = John OR ")
            {"name": "John"}
    
    Notes:
        - OR detection is case-insensitive (or, OR, Or all work)
        - Leading/trailing whitespace in each part is stripped
        - Nested OR conditions are not supported (flat list only)
        - Avoids infinite recursion by only calling parse_single_where()
    
    See Also:
        - parse_where_clause(): Main entry point
        - parse_single_where(): Parses individual conditions
    """
    # Split by OR (case-insensitive)
    or_parts = re.split(_PATTERN_OR_SPLIT, where_str, flags=re.IGNORECASE)

    or_conditions = []
    for part in or_parts:
        part = part.strip()
        # Only parse non-empty parts that don't contain nested OR
        if part and _KEYWORD_OR not in part.upper():
            # Parse each part (avoiding infinite recursion)
            parsed = parse_single_where(part)
            if parsed:
                or_conditions.append(parsed)

    if not or_conditions:
        return None

    # If only one condition, return it directly (no $or wrapper)
    if len(or_conditions) == 1:
        return or_conditions[0]

    # Multiple conditions - wrap in $or
    return {_KEY_OR: or_conditions}

def parse_single_where(condition: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single WHERE condition without OR operators.
    
    This function handles all non-OR operators: comparison (=, !=, >, <, >=, <=),
    NULL checks (IS NULL, IS NOT NULL), pattern matching (LIKE), and list
    membership (IN).
    
    Args:
        condition: A single WHERE condition string (no OR operators).
                  Must be non-empty (caller should check).
    
    Returns:
        Dictionary representation of the condition, or None if unparseable.
        
        Format varies by operator:
        - Equality: {"field": value}
        - Comparison: {"field": {"$op": value}}
        - IS NULL: {"field": None}
        - IS NOT NULL: {"field": {"$notnull": True}}
        - LIKE: {"field": {"$like": pattern}}
        - IN: {"field": [value1, value2, ...]}
    
    Operator Precedence:
        Operators are checked in this order:
        1. IS NOT NULL (before IS NULL to avoid partial match)
        2. IS NULL
        3. IN
        4. LIKE
        5. Comparison operators (>=, <=, !=, >, <, =)
    
    Examples:
        Equality:
            >>> parse_single_where("name = John")
            {"name": "John"}
        
        Comparison:
            >>> parse_single_where("age >= 18")
            {"age": {"$gte": 18}}
            
            >>> parse_single_where("score < 100")
            {"score": {"$lt": 100}}
        
        NULL checks:
            >>> parse_single_where("email IS NULL")
            {"email": None}
            
            >>> parse_single_where("phone IS NOT NULL")
            {"phone": {"$notnull": True}}
        
        LIKE pattern:
            >>> parse_single_where("name LIKE %Smith%")
            {"name": {"$like": "%Smith%"}}
        
        IN list:
            >>> parse_single_where("status IN active,pending,closed")
            {"status": ["active", "pending", "closed"]}
        
        Type conversion:
            >>> parse_single_where("age = 42")
            {"age": 42}  # int, not string
            
            >>> parse_single_where("active = true")
            {"active": True}  # bool, not string
    
    Notes:
        - All operators are case-insensitive (in, IN, In all work)
        - Field names preserve original casing (except IS NULL/IS NOT NULL)
        - IS NULL/IS NOT NULL lowercase the field name (legacy behavior)
        - Values are type-converted via parse_value()
        - IN operator splits values by comma (no escaping supported)
        - Returns None for unparseable conditions (no exceptions thrown)
    
    See Also:
        - _parse_comparison(): Handles comparison operators
        - parse_value(): Type conversion for values
    """
    condition = condition.strip()
    upper = condition.upper()

    # Handle IS NOT NULL (check before IS NULL to avoid partial match)
    if _KEYWORD_IS_NOT_NULL in upper:
        field = upper.replace(_KEYWORD_IS_NOT_NULL, "").strip()
        return {field.lower(): {_KEY_NOTNULL: True}}
    
    # Handle IS NULL
    if _KEYWORD_IS_NULL in upper:
        field = upper.replace(_KEYWORD_IS_NULL, "").strip()
        return {field.lower(): None}

    # Handle IN operator
    if _KEYWORD_IN in upper:
        parts = condition.split(_KEYWORD_IN, 1)
        if len(parts) == 2:
            field = parts[0].strip()
            # Split by comma and parse each value
            values = [
                parse_value(v.strip()) 
                for v in parts[1].strip().split(_DELIMITER_IN_VALUES)
            ]
            return {field: values}

    # Handle LIKE operator
    if _KEYWORD_LIKE in upper:
        parts = condition.split(_KEYWORD_LIKE, 1)
        if len(parts) == 2:
            return {parts[0].strip(): {_KEY_LIKE: parts[1].strip()}}

    # Parse comparison operators (=, !=, >, <, >=, <=)
    result = _parse_comparison(condition)
    if result:
        return result

    # Could not parse WHERE clause - return None (silent failure)
    return None

def _parse_comparison(condition: str) -> Optional[Dict[str, Any]]:
    """
    Parse comparison operators in a WHERE condition.
    
    This helper function handles all comparison operators: >=, <=, !=, >, <, =.
    Operators are checked in order from longest to shortest to avoid partial matches
    (e.g., checking ">=" before ">" prevents "age >= 18" matching ">").
    
    Args:
        condition: A single condition string containing a comparison operator.
    
    Returns:
        Dictionary with field and comparison, or None if no operator found.
        
        Format:
        - Equality (=): {"field": value}
        - Comparison: {"field": {"$op": value}}
    
    Operator Order:
        Operators are checked in this order (longest first):
        1. >= (greater or equal) → {"$gte": value}
        2. <= (less or equal) → {"$lte": value}
        3. != (not equal) → {"$ne": value}
        4. > (greater than) → {"$gt": value}
        5. < (less than) → {"$lt": value}
        6. = (equality) → value (no operator key)
    
    Examples:
        Greater or equal:
            >>> _parse_comparison("age >= 18")
            {"age": {"$gte": 18}}
        
        Less than:
            >>> _parse_comparison("score < 100")
            {"score": {"$lt": 100}}
        
        Not equal:
            >>> _parse_comparison("status != inactive")
            {"status": {"$ne": "inactive"}}
        
        Equality (no operator key):
            >>> _parse_comparison("name = John")
            {"name": "John"}
    
    Notes:
        - Only the first matching operator is used
        - Values are type-converted via parse_value()
        - Field names and values are stripped of whitespace
        - Returns None if no operator found (not an error)
    
    See Also:
        - parse_single_where(): Calls this for comparison parsing
        - parse_value(): Type conversion for values
        - _COMPARISON_OPERATORS: List of operators checked
        - _OPERATOR_KEY_MAP: Mapping from operators to output keys
    """
    # Check operators in order (longest first to avoid partial matches)
    for operator in _COMPARISON_OPERATORS:
        if operator in condition:
            # Split on first occurrence only
            field, value = condition.split(operator, 1)
            parsed_value = parse_value(value.strip())
            
            # Get operator key from map (None for equality)
            op_key = _OPERATOR_KEY_MAP[operator]
            
            # Format: {"field": {"$op": value}} or {"field": value}
            if op_key:
                return {field.strip(): {op_key: parsed_value}}
            else:
                return {field.strip(): parsed_value}

    return None
