# zCLI/subsystems/zDialog/dialog_modules/dialog_context.py

"""
Context management for zDialog - Handles context creation and placeholder injection.

This module provides the foundational Tier 1 components for the zDialog subsystem,
handling dialog context creation and sophisticated placeholder resolution.

Architecture Position
---------------------
**Tier 1: Foundation** (5-Tier Pattern)
    - Tier 1: Foundation (dialog_context.py) ← This module
    - Tier 2: Submit Handler (dialog_submit.py)
    - Tier 3: Package Aggregator (dialog_modules/__init__.py)
    - Tier 4: Facade (zDialog.py)
    - Tier 5: Package Root (__init__.py)

Key Functions
-------------
1. create_dialog_context(): Creates dialog context from model and fields
2. inject_placeholders(): Recursively resolves 5 types of placeholders in data structures

Placeholder Syntax (5 Types)
-----------------------------
This module supports sophisticated placeholder resolution for form data:

1. **Full zConv**: "zConv" → Returns entire zConv dictionary
   Example: {"data": "zConv"} → {"data": {"name": "John", "age": 30}}

2. **Dot Notation**: "zConv.field" → Returns specific field value
   Example: "zConv.username" → "john_doe"

3. **Bracket Notation**: "zConv['field']" or 'zConv["field"]' → Returns field value
   Example: "zConv['email']" → "john@example.com"

4. **Embedded Placeholders**: "WHERE id = zConv.user_id" → Replaces within string
   Example: "WHERE id = zConv.user_id" → "WHERE id = 123"
   Note: Automatically detects numeric values and formats appropriately (no quotes for numbers)

5. **Regex Pattern Matching**: Uses r'zConv\\.(\\w+)' to find all dot notation occurrences
   Example: "user_id = zConv.id AND name = zConv.name" → "user_id = 123 AND name = 'John'"

Integration Points
------------------
- Used by: zDialog.py (line 59 - context creation)
- Used by: dialog_submit.py (line 35 - placeholder injection)
- Dependencies: None (stdlib only: re module)

Usage Examples
--------------
Example 1 - Basic Context Creation:
    >>> context = create_dialog_context(
    ...     model="@.zSchema.users",
    ...     fields=[{"name": "username", "type": "text"}],
    ...     logger=logger
    ... )
    >>> # Returns: {"model": "@.zSchema.users", "fields": [...]}

Example 2 - Dot Notation Placeholder:
    >>> zContext = {"zConv": {"user_id": 123, "name": "John"}}
    >>> result = inject_placeholders("zConv.user_id", zContext, logger)
    >>> # Returns: 123

Example 3 - Embedded Placeholders:
    >>> zContext = {"zConv": {"user_id": 42, "status": "active"}}
    >>> query = "SELECT * FROM users WHERE id = zConv.user_id AND status = zConv.status"
    >>> result = inject_placeholders(query, zContext, logger)
    >>> # Returns: "SELECT * FROM users WHERE id = 42 AND status = 'active'"

Example 4 - Recursive Dictionary Resolution:
    >>> zContext = {"zConv": {"name": "Alice", "age": 25}}
    >>> data = {
    ...     "user": "zConv.name",
    ...     "info": {"years": "zConv.age"},
    ...     "query": "WHERE name = zConv.name"
    ... }
    >>> result = inject_placeholders(data, zContext, logger)
    >>> # Returns: {"user": "Alice", "info": {"years": 25}, "query": "WHERE name = 'Alice'"}

Version History
---------------
- v1.5.4: Industry-grade refactor (type hints, constants, comprehensive docstrings)
- v1.5.3: Added embedded placeholder support with smart value formatting
- v1.5.2: Initial implementation with basic placeholder resolution
"""

import re
from zOS import Any, Dict, List, Optional, Union
from .dialog_constants import (
    KEY_FIELDS,
    KEY_MODEL,
    KEY_ZCONV,
    _BRACKET_CLOSE,
    _BRACKET_OPEN,
    _DEBUG_CONTEXT_CREATED,
    _DOT_SEPARATOR,
    _ERROR_PARSE_EMBEDDED_FAILED,
    _ERROR_PARSE_PLACEHOLDER_FAILED,
    _EXPECTED_DOT_NOTATION_PARTS,
    _PLACEHOLDER_FULL,
    _PLACEHOLDER_PREFIX,
    _QUOTE_CHARS,
    _REGEX_ZCONV_DOT_NOTATION,
    _WARNING_FIELD_NOT_FOUND,
)

# ============================================================================
# Module-Level Constants
# ============================================================================

# Context Dictionary Keys

# Placeholder Constants

# Parsing Characters

# Regex Pattern

# Magic Numbers

# Debug/Error/Warning Messages

# Module Public API
__all__ = ["create_dialog_context", "inject_placeholders"]


# ============================================================================
# Public Functions
# ============================================================================

def create_dialog_context(
    model: Optional[str],
    fields: List[Dict[str, Any]],
    logger: Any,
    zConv: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create dialog context with model schema, fields, and optional form data.

    This function creates a standardized context dictionary for dialog operations,
    containing the schema model reference, field definitions, and optionally the
    collected form data (zConv).

    Parameters
    ----------
    model : Optional[str]
        Schema model reference (e.g., "@.zSchema.users"). Can be None for
        forms without schema validation. If starts with '@', enables auto-validation
        in zDialog.handle().
    fields : List[Dict[str, Any]]
        List of field definitions. Each field dict typically contains:
        - "name": Field identifier (str)
        - "type": Field type (text, number, email, etc.)
        - "label": Display label (optional)
        - "required": Whether field is required (optional, bool)
        - "default": Default value (optional)
    logger : Any
        Logger instance for debug output. Should have .debug() method.
    zConv : Optional[Dict[str, Any]], default=None
        Optional dictionary of collected form data. Keys are field names,
        values are user-provided data. If provided, will be included in
        the context under KEY_ZCONV ("zConv").

    Returns
    -------
    Dict[str, Any]
        Dialog context dictionary with structure:
        {
            "model": Optional[str],    # Schema model reference
            "fields": List[Dict],      # Field definitions
            "zConv": Optional[Dict]    # Form data (if provided)
        }

    Examples
    --------
    Example 1: Basic context without form data
        >>> context = create_dialog_context(
        ...     model="@.zSchema.users",
        ...     fields=[
        ...         {"name": "username", "type": "text", "required": True},
        ...         {"name": "email", "type": "email"}
        ...     ],
        ...     logger=logger
        ... )
        >>> # Returns: {"model": "@.zSchema.users", "fields": [...]}

    Example 2: Context with collected form data
        >>> form_data = {"username": "john_doe", "email": "john@example.com"}
        >>> context = create_dialog_context(
        ...     model="@.zSchema.users",
        ...     fields=[...],
        ...     logger=logger,
        ...     zConv=form_data
        ... )
        >>> # Returns: {"model": "...", "fields": [...], "zConv": {...}}

    Notes
    -----
    - The context dictionary uses constants (KEY_MODEL, KEY_FIELDS, KEY_ZCONV)
      for consistent key naming across the zDialog subsystem
    - Model path starting with '@' triggers auto-validation in zDialog.handle()
    - This function is pure data transformation with no side effects (except logging)
    """
    context = {
        KEY_MODEL: model,
        KEY_FIELDS: fields,
    }
    
    if zConv is not None:
        context[KEY_ZCONV] = zConv
    
    logger.debug(_DEBUG_CONTEXT_CREATED, context)
    return context


def inject_placeholders(
    obj: Union[Dict, List, str, Any],
    zContext: Dict[str, Any],
    logger: Any
) -> Union[Dict, List, str, Any]:
    """
    Recursively replace placeholder strings with actual values from zContext.

    This function performs sophisticated placeholder resolution, supporting 5 different
    placeholder syntaxes. It recursively processes nested data structures (dicts, lists)
    and intelligently formats values based on their types.

    Supported Placeholder Types
    ----------------------------
    1. Full zConv: "zConv" → Returns entire zConv dictionary
    2. Dot Notation: "zConv.field" → Returns field value (e.g., "zConv.username")
    3. Bracket Notation: "zConv['field']" or 'zConv["field"]' → Returns field value
    4. Embedded: "WHERE id = zConv.user_id" → Replaces within string
    5. Regex: Pattern r'zConv\\.(\\w+)' matches all dot notation occurrences

    Parameters
    ----------
    obj : Union[Dict, List, str, Any]
        The object to process for placeholder resolution. Can be:
        - Dict: Recursively processes all values
        - List: Recursively processes all items
        - str: Performs placeholder resolution
        - Other: Returns as-is (int, float, bool, None, etc.)
    zContext : Dict[str, Any]
        Context dictionary containing the zConv data. Expected structure:
        {
            "zConv": {
                "field1": value1,
                "field2": value2,
                ...
            }
        }
    logger : Any
        Logger instance for debug/error/warning output. Should have
        .debug(), .error(), and .warning() methods.

    Returns
    -------
    Union[Dict, List, str, Any]
        Processed object with placeholders resolved:
        - Dict: New dict with all values processed
        - List: New list with all items processed
        - str: String with placeholders replaced or original value
        - Other: Original value unchanged

    Raises
    ------
    ValueError
        If placeholder parsing fails due to malformed syntax
    KeyError
        If attempting to access missing keys in zContext
    IndexError
        If bracket notation has invalid indices

    Examples
    --------
    Example 1: Full zConv placeholder
        >>> zContext = {"zConv": {"name": "Alice", "age": 30}}
        >>> result = inject_placeholders("zConv", zContext, logger)
        >>> # Returns: {"name": "Alice", "age": 30}

    Example 2: Dot notation placeholder
        >>> zContext = {"zConv": {"user_id": 123}}
        >>> result = inject_placeholders("zConv.user_id", zContext, logger)
        >>> # Returns: 123

    Example 3: Bracket notation placeholder
        >>> zContext = {"zConv": {"email": "test@example.com"}}
        >>> result = inject_placeholders("zConv['email']", zContext, logger)
        >>> # Returns: "test@example.com"

    Example 4: Embedded placeholders with smart formatting
        >>> zContext = {"zConv": {"user_id": 42, "name": "Bob"}}
        >>> query = "SELECT * FROM users WHERE id = zConv.user_id AND name = zConv.name"
        >>> result = inject_placeholders(query, zContext, logger)
        >>> # Returns: "SELECT * FROM users WHERE id = 42 AND name = 'Bob'"
        >>> # Note: Numbers don't get quotes, strings do

    Example 5: Recursive dictionary processing
        >>> zContext = {"zConv": {"x": 10, "y": 20}}
        >>> data = {
        ...     "point": {"x": "zConv.x", "y": "zConv.y"},
        ...     "query": "WHERE x = zConv.x"
        ... }
        >>> result = inject_placeholders(data, zContext, logger)
        >>> # Returns: {"point": {"x": 10, "y": 20}, "query": "WHERE x = 10"}

    Example 6: List processing
        >>> zContext = {"zConv": {"status": "active"}}
        >>> data = ["zConv.status", "fixed_value", {"key": "zConv.status"}]
        >>> result = inject_placeholders(data, zContext, logger)
        >>> # Returns: ["active", "fixed_value", {"key": "active"}]

    Notes
    -----
    - Recursion handles arbitrarily nested data structures
    - Value formatting is intelligent:
      * Numeric strings (isdigit() == True): No quotes
      * int/float: No quotes
      * Other strings: Wrapped in single quotes
    - Missing fields log warnings but don't raise exceptions
    - Errors during parsing are caught and logged, returning original value
    - The function is pure for non-string types (no mutations)
    - For strings, embedded placeholder replacement creates new strings
    """
    # Handle recursive cases first
    if isinstance(obj, dict):
        return {k: inject_placeholders(v, zContext, logger) for k, v in obj.items()}
    
    if isinstance(obj, list):
        return [inject_placeholders(v, zContext, logger) for v in obj]
    
    # Only process strings for placeholder resolution
    if not isinstance(obj, str):
        return obj
    
    # Get zConv data once (DRY - avoid repeated dict access)
    zconv_data = zContext.get(KEY_ZCONV, {})
    
    # Type 1: Full zConv placeholder - "zConv" => return entire dict
    if obj == _PLACEHOLDER_FULL:
        return zContext.get(KEY_ZCONV)
    
    # Type 2 & 3: Single placeholder (dot or bracket notation)
    if obj.startswith(_PLACEHOLDER_PREFIX):
        try:
            # Type 2: Dot notation - "zConv.field"
            if _DOT_SEPARATOR in obj and len(obj.split(_DOT_SEPARATOR)) == _EXPECTED_DOT_NOTATION_PARTS:
                parts = obj.split(_DOT_SEPARATOR, 1)
                if parts[0] == _PLACEHOLDER_PREFIX:
                    return zconv_data.get(parts[1])
            
            # Type 3: Bracket notation - "zConv['field']" or 'zConv["field"]'
            if _BRACKET_OPEN in obj and _BRACKET_CLOSE in obj:
                start = obj.index(_BRACKET_OPEN) + 1
                end = obj.index(_BRACKET_CLOSE)
                field = obj[start:end].strip(_QUOTE_CHARS)
                return zconv_data.get(field)
                
        except (ValueError, KeyError, IndexError) as e:
            logger.error(_ERROR_PARSE_PLACEHOLDER_FAILED, obj, e)
            return obj
    
    # Type 4 & 5: Embedded placeholders - "WHERE id = zConv.user_id"
    if _PLACEHOLDER_PREFIX in obj:
        try:
            result = obj
            
            # Type 5: Use regex to find all zConv.field_name patterns
            matches = re.findall(_REGEX_ZCONV_DOT_NOTATION, result)
            
            for field in matches:
                value = zconv_data.get(field)
                if value is not None:
                    # Smart value formatting based on type
                    if isinstance(value, str) and value.isdigit():
                        replacement = value  # Numeric string, no quotes
                    elif isinstance(value, (int, float)):
                        replacement = str(value)  # True numbers, no quotes
                    else:
                        replacement = f"'{value}'"  # Text strings, add quotes
                    result = result.replace(f"{_PLACEHOLDER_PREFIX}{_DOT_SEPARATOR}{field}", replacement)
                else:
                    logger.warning(_WARNING_FIELD_NOT_FOUND, field)
            
            return result
            
        except (ValueError, KeyError, IndexError) as e:
            logger.error(_ERROR_PARSE_EMBEDDED_FAILED, obj, e)
            return obj
    
    # No placeholders found - return original string
    return obj
