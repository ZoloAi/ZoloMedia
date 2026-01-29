# zCLI/subsystems/zData/zData_modules/shared/operations/helpers.py
"""
Shared Helper Utilities for zData Operations.

This module provides DRY (Don't Repeat Yourself) helper utilities used by ALL
zData operations (both CRUD and DDL). These functions eliminate code duplication
and ensure consistent behavior across operations for common tasks like table
extraction, WHERE clause parsing, field/value extraction, and validation error
display.

═══════════════════════════════════════════════════════════════════════════════
HELPER FUNCTIONS OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

1. extract_table_from_request()
   - Extracts and validates table name from request
   - 3-tier fallback logic: tables → table → model
   - Optional table existence check
   - Raises DatabaseNotInitializedError if table doesn't exist

2. extract_where_clause()
   - Extracts and parses WHERE clause from request
   - Dual-source extraction: top-level (YAML) + options (shell)
   - Quote stripping for command-line parsing artifacts
   - Optional warning if WHERE clause is missing (dangerous for UPDATE/DELETE)

3. extract_field_values()
   - Extracts field/value pairs from request options
   - Filters out reserved options (model, limit, where, order, offset, tables, joins)
   - Type conversion using parse_value() for values
   - Returns (fields: List[str], values: List[Any])

4. display_validation_errors()
   - Displays validation errors with actionable hints
   - Uses ValidationError exception for context-aware hints
   - zDisplay integration for user-friendly output
   - Logger integration for debug/error messages

═══════════════════════════════════════════════════════════════════════════════
3-TIER TABLE EXTRACTION LOGIC
═══════════════════════════════════════════════════════════════════════════════

The table extraction uses a 3-tier fallback to support multiple request formats:

1. Check "tables" key (list of table names - preferred)
2. Check "table" key (single table name or list)
3. Fallback to "model" key (extract last segment: "schema.table" → "table")

This flexibility ensures compatibility with:
- YAML-based requests (declarative operations)
- Shell command requests (command-line operations)
- Legacy model-based requests (backward compatibility)

═══════════════════════════════════════════════════════════════════════════════
DUAL-SOURCE WHERE EXTRACTION
═══════════════════════════════════════════════════════════════════════════════

WHERE clause extraction checks two locations:

1. Top-level "where" key (YAML-based requests)
   Example: {action: "read", where: "id > 5", ...}

2. Options "where" key (shell command requests)
   Example: {action: "read", options: {where: "id > 5"}, ...}

This dual-source approach supports both declarative (YAML) and imperative (shell)
operation modes. Quote stripping handles command-line parsing artifacts where
the shell passes WHERE strings with surrounding quotes.

═══════════════════════════════════════════════════════════════════════════════
RESERVED OPTIONS FILTERING
═══════════════════════════════════════════════════════════════════════════════

Reserved options are filtered out when extracting field/value pairs to prevent
conflicts with table field names:

Reserved: {model, limit, where, order, offset, tables, joins}

This ensures that options like "--limit 10" are not interpreted as setting a
"limit" field in the table, but rather as operation control parameters.

═══════════════════════════════════════════════════════════════════════════════
EXCEPTION INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

Helpers raise actionable exceptions with context-aware hints:

1. DatabaseNotInitializedError
   - Raised when table doesn't exist (extract_table_from_request)
   - Includes operation name, table name, schema name
   - Hint: "Please run 'Setup Database' first to create tables"

2. ValidationError
   - Raised for field validation failures (display_validation_errors)
   - Includes field, value, constraint, schema_name
   - Context-aware hints based on constraint type

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION WITH OTHER SUBSYSTEMS
═══════════════════════════════════════════════════════════════════════════════

- zDisplay: User-friendly error messages (mode-agnostic)
- zLogger: Debug/error/warning messages for operations
- Parsers: WHERE clause parsing (parse_where_clause) and value type conversion (parse_value)
- Exceptions: DatabaseNotInitializedError, ValidationError with actionable hints

═══════════════════════════════════════════════════════════════════════════════
USAGE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Example 1: Extract table with existence check
    table = extract_table_from_request(request, "INSERT", ops, check_exists=True)
    if not table:
        return False

Example 2: Extract WHERE clause with warning
    where = extract_where_clause(request, ops, warn_if_missing=True)

Example 3: Extract field/value pairs
    fields, values = extract_field_values(request, "UPDATE", ops)
    if not fields:
        return False

Example 4: Display validation errors
    if errors:
        display_validation_errors(table, errors, ops)
        return False

"""

from zOS import Any, Dict, Optional, Tuple
from zSys.errors import DatabaseNotInitializedError
from ..parsers import parse_where_clause, parse_value

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────────────────────────────
# Request Keys
# ────────────────────────────────────────────────────────────────────────────
_KEY_TABLES = "tables"
_KEY_TABLE = "table"
_KEY_MODEL = "model"
_KEY_WHERE = "where"
_KEY_OPTIONS = "options"
_KEY_LIMIT = "limit"
_KEY_ORDER = "order"
_KEY_OFFSET = "offset"
_KEY_JOINS = "joins"
_KEY_META = "zMeta"
_KEY_SCHEMA_NAME = "Schema_Name"

# ────────────────────────────────────────────────────────────────────────────
# Reserved Options (Filtered from Field Extraction)
# ────────────────────────────────────────────────────────────────────────────
_RESERVED_MODEL = "model"
_RESERVED_LIMIT = "limit"
_RESERVED_WHERE = "where"
_RESERVED_ORDER = "order"
_RESERVED_OFFSET = "offset"
_RESERVED_TABLES = "tables"
_RESERVED_JOINS = "joins"

# ────────────────────────────────────────────────────────────────────────────
# Error Messages
# ────────────────────────────────────────────────────────────────────────────
_ERR_NO_TABLE = "No table specified for %s"
_ERR_TABLE_NOT_EXISTS = "Table '%s' does not exist. Please run 'Setup Database' first to create tables."
_ERR_TABLE_NOT_EXISTS_LOG = "[FAIL] Table '%s' does not exist"
_ERR_NO_FIELDS = "No fields provided for %s. Use --field_name value syntax"
_ERR_VALIDATION_FAILED_LOG = "[FAIL] Validation failed for table '%s' with %d error(s)"

# ────────────────────────────────────────────────────────────────────────────
# Log Messages
# ────────────────────────────────────────────────────────────────────────────
_LOG_WARN_NO_WHERE = "[WARN] No WHERE clause - operation will affect ALL rows!"
_LOG_VALIDATION_SUMMARY = "[FAIL] Validation summary: %d field(s) failed for table '%s'"

# ────────────────────────────────────────────────────────────────────────────
# Special Values
# ────────────────────────────────────────────────────────────────────────────
_VALUE_PLACEHOLDER = "<provided value>"  # Placeholder for ValidationError when actual value unavailable

# ────────────────────────────────────────────────────────────────────────────
# Success Messages
# ────────────────────────────────────────────────────────────────────────────
_MSG_SUCCESS = "✓ %s"  # Generic success message template

# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────
__all__ = [
    "extract_table_from_request",
    "extract_where_clause",
    "extract_field_values",
    "display_validation_errors",
    "execute_hook_if_defined",
    "display_success_message",
]


def extract_table_from_request(
    request: Dict[str, Any],
    operation_name: str,
    ops: Any,
    check_exists: bool = True
) -> Optional[str]:
    """
    Extract and validate table name from request using 3-tier fallback logic.
    
    This function extracts the table name from a request dictionary using a
    3-tier fallback strategy to support multiple request formats (YAML-based,
    shell command-based, and legacy model-based requests).
    
    3-Tier Fallback Logic:
        1. Check "tables" key (list of table names - preferred format)
        2. Check "table" key (single table name or list - alternate format)
        3. Fallback to "model" key (extract last segment: "schema.table" → "table")
    
    Table Existence Check:
        If check_exists=True, validates that the table exists in the database.
        If table doesn't exist, displays user-friendly error and raises
        DatabaseNotInitializedError with actionable hints.
    
    Args:
        request: Request dictionary containing table information in one of 3 formats:
                 - {"tables": ["table_name"]}
                 - {"table": "table_name"}
                 - {"model": "schema.table_name"}
        operation_name: Name of the operation (INSERT, READ, UPDATE, etc.) for error messages
        ops: Operations context with adapter, logger, display, schema
        check_exists: If True, validate that table exists in database (default: True)
    
    Returns:
        str: Extracted table name (first table if multiple)
        None: If no table could be extracted
    
    Raises:
        DatabaseNotInitializedError: If check_exists=True and table doesn't exist
    
    Examples:
        # Extract table with existence check
        table = extract_table_from_request(
            {"tables": ["users"]}, "INSERT", ops, check_exists=True
        )
        
        # Extract table without existence check (for CREATE TABLE)
        table = extract_table_from_request(
            {"table": "users"}, "CREATE TABLE", ops, check_exists=False
        )
        
        # Extract from model path (legacy format)
        table = extract_table_from_request(
            {"model": "auth.users"}, "READ", ops
        )  # Returns "users"
    
    Notes:
        - Returns first table if multiple tables provided (tables[0])
        - Supports both string and list formats for "table" key
        - Model path extraction uses last segment (split by '.')
        - Logs error if no table specified (returns None)
        - Displays user-friendly error before raising exception
    """
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: 3-Tier Fallback - Extract table from request
    # ─────────────────────────────────────────────────────────────────────────
    
    # Tier 1: Check "tables" key (list of table names - preferred)
    tables = request.get(_KEY_TABLES, [])
    
    # Tier 2: Check singular "table" parameter (alternate format)
    if not tables:
        table_param = request.get(_KEY_TABLE)
        if table_param:
            if isinstance(table_param, str):
                tables = [table_param]
            elif isinstance(table_param, list):
                tables = table_param
    
    # Tier 3: Fallback to extracting from model path (legacy format)
    if not tables:
        model = request.get(_KEY_MODEL)
        if isinstance(model, str):
            # Extract last segment: "schema.table" → "table"
            tables = [model.split(".")[-1]]

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Validation - Ensure table was extracted
    # ─────────────────────────────────────────────────────────────────────────
    if not tables:
        ops.logger.error(_ERR_NO_TABLE, operation_name)
        return None

    table = tables[0]  # Use first table if multiple provided

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: Existence Check - Verify table exists in database (if requested)
    # ─────────────────────────────────────────────────────────────────────────
    if check_exists and not ops.adapter.table_exists(table):
        ops.logger.error(_ERR_TABLE_NOT_EXISTS_LOG, table)
        
        # Display user-friendly error first (mode-agnostic via zDisplay)
        ops.display.error(_ERR_TABLE_NOT_EXISTS % table)
        
        # Then raise actionable exception with hints
        raise DatabaseNotInitializedError(operation=operation_name, table=table)

    return table

def extract_where_clause(
    request: Dict[str, Any],
    ops: Any,
    warn_if_missing: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Extract and parse WHERE clause from request using dual-source extraction.
    
    This function extracts the WHERE clause from a request dictionary using a
    dual-source strategy to support both YAML-based (declarative) and shell
    command-based (imperative) request formats. It also strips surrounding
    quotes that are artifacts of command-line parsing.
    
    Dual-Source Extraction Logic:
        1. Check top-level "where" key (YAML-based requests - preferred)
           Example: {action: "read", where: "id > 5", ...}
        
        2. Check options "where" key (shell command requests - fallback)
           Example: {action: "read", options: {where: "id > 5"}, ...}
    
    Quote Stripping:
        Removes surrounding quotes (single or double) from WHERE strings.
        This handles shell command-line parsing artifacts where the shell
        passes WHERE strings with surrounding quotes.
        
        Example: '"id > 5"' → 'id > 5'
    
    Optional Warning:
        If warn_if_missing=True, logs a warning when WHERE clause is missing.
        This is useful for UPDATE/DELETE operations where missing WHERE clause
        means the operation will affect ALL rows (potentially dangerous).
    
    Args:
        request: Request dictionary with WHERE clause in one of 2 formats:
                 - {"where": "id > 5"}  (YAML-based)
                 - {"options": {"where": "id > 5"}}  (shell-based)
        ops: Operations context with logger
        warn_if_missing: If True, log warning when WHERE clause is missing (default: False)
    
    Returns:
        Dict[str, Any]: Parsed WHERE clause dictionary (from parse_where_clause)
                        Example: {"id": {"$gt": 5}}
        None: If no WHERE clause found
    
    Examples:
        # Extract WHERE from YAML-based request
        where = extract_where_clause(
            {"where": "id > 5"}, ops
        )  # Returns {"id": {"$gt": 5}}
        
        # Extract WHERE from shell command request
        where = extract_where_clause(
            {"options": {"where": '"id > 5"'}}, ops
        )  # Returns {"id": {"$gt": 5}} (quotes stripped)
        
        # Extract with warning for dangerous operations
        where = extract_where_clause(
            {"options": {}}, ops, warn_if_missing=True
        )  # Logs: "[WARN] No WHERE clause - operation will affect ALL rows!"
    
    Notes:
        - Top-level "where" takes precedence over options "where"
        - Quote stripping handles both single (') and double (") quotes
        - Uses parse_where_clause() for WHERE string parsing
        - Warning is logged to ops.logger (not displayed to user)
    """
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: Dual-Source Extraction - Get WHERE string from request
    # ─────────────────────────────────────────────────────────────────────────
    
    # Source 1: Check top-level "where" key (YAML-based requests - preferred)
    where_str = request.get(_KEY_WHERE)
    
    # Source 2: Check options "where" key (shell command requests - fallback)
    if not where_str:
        options = request.get(_KEY_OPTIONS, {})
        where_str = options.get(_KEY_WHERE)

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Dict Passthrough - If already a dict, skip string processing
    # ─────────────────────────────────────────────────────────────────────────
    if where_str and isinstance(where_str, dict):
        # WHERE clause is already in dict format (e.g., from auto-query)
        where = where_str
    else:
        # ─────────────────────────────────────────────────────────────────────────
        # Phase 3: Quote Stripping - Remove surrounding quotes (shell artifact)
        # ─────────────────────────────────────────────────────────────────────────
        if where_str:
            where_str = where_str.strip()
            # Strip surrounding quotes (single or double)
            if (where_str.startswith('"') and where_str.endswith('"')) or \
               (where_str.startswith("'") and where_str.endswith("'")):
                where_str = where_str[1:-1]

        # ─────────────────────────────────────────────────────────────────────────
        # Phase 4: Parsing - Convert WHERE string to dictionary
        # ─────────────────────────────────────────────────────────────────────────
        where = parse_where_clause(where_str) if where_str else None

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 4: Optional Warning - Alert if WHERE clause is missing
    # ─────────────────────────────────────────────────────────────────────────
    if warn_if_missing and not where:
        ops.logger.warning(_LOG_WARN_NO_WHERE)

    return where

def extract_field_values(
    request: Dict[str, Any],
    operation_name: str,
    ops: Any
) -> Tuple[Optional[list], Optional[list]]:
    """
    Extract field/value pairs from request options with reserved options filtering.
    
    This function extracts field/value pairs from the request's options dictionary,
    filtering out reserved option names that control operation behavior rather than
    representing table fields. Values are parsed using parse_value() for automatic
    type conversion (int, float, bool, str, None).
    
    Reserved Options Filtering:
        The following option names are reserved for operation control and are NOT
        interpreted as table field names:
        
        - model: Table/model path specification
        - limit: Result limit for READ operations
        - where: WHERE clause filter
        - order: Sort order for READ operations
        - offset: Pagination offset for READ operations
        - tables: Table name(s) specification
        - joins: JOIN specifications for READ operations
    
    Type Conversion:
        Values are converted from strings to appropriate Python types using
        parse_value():
        - "123" → 123 (int)
        - "3.14" → 3.14 (float)
        - "true" → True (bool)
        - "None" → None
        - "text" → "text" (str)
    
    Args:
        request: Request dictionary with options containing field/value pairs
                 Example: {"options": {"name": "Alice", "age": "30", "limit": "10"}}
        operation_name: Name of the operation (INSERT, UPDATE, etc.) for error messages
        ops: Operations context with logger
    
    Returns:
        Tuple[list, list]: (fields, values) where:
            - fields: List of field names (strings)
            - values: List of parsed values (typed)
        Tuple[None, None]: If no fields provided (logs error)
    
    Examples:
        # Extract field/value pairs with reserved options filtering
        fields, values = extract_field_values(
            {"options": {"name": "Alice", "age": "30", "limit": "10"}},
            "INSERT",
            ops
        )
        # Returns: (["name", "age"], ["Alice", 30])
        # Note: "limit" is filtered out as reserved option
        
        # No fields provided (only reserved options)
        fields, values = extract_field_values(
            {"options": {"limit": "10", "where": "id > 5"}},
            "UPDATE",
            ops
        )
        # Returns: (None, None)
        # Logs: "No fields provided for UPDATE. Use --field_name value syntax"
    
    Notes:
        - Reserved options are filtered to prevent field name conflicts
        - Values are converted to Python types (not kept as strings)
        - Returns (None, None) if no field/value pairs after filtering
        - Error is logged but no exception is raised
    """
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: Extract Options - Get options dictionary from request
    # ─────────────────────────────────────────────────────────────────────────
    options = request.get(_KEY_OPTIONS, {})

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Reserved Options Filtering - Build reserved options set
    # ─────────────────────────────────────────────────────────────────────────
    reserved_options = {
        _RESERVED_MODEL,
        _RESERVED_LIMIT,
        _RESERVED_WHERE,
        _RESERVED_ORDER,
        _RESERVED_OFFSET,
        _RESERVED_TABLES,
        _RESERVED_JOINS
    }

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: Field/Value Extraction - Filter out reserved options
    # ─────────────────────────────────────────────────────────────────────────
    fields_dict = {k: v for k, v in options.items() if k not in reserved_options}

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 4: Validation - Ensure at least one field provided
    # ─────────────────────────────────────────────────────────────────────────
    if not fields_dict:
        ops.logger.error(_ERR_NO_FIELDS, operation_name)
        return None, None

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 5: Type Conversion - Parse values to Python types
    # ─────────────────────────────────────────────────────────────────────────
    fields = list(fields_dict.keys())
    values = [parse_value(str(v)) for v in fields_dict.values()]

    return fields, values

def display_validation_errors(
    table: str,
    errors: Dict[str, str],
    ops: Any
) -> None:
    """
    Display validation errors with actionable hints using ValidationError exception.
    
    This function displays field validation errors to the user with context-aware
    actionable hints by leveraging the ValidationError exception. Each error is
    raised and caught to generate formatted error messages with hints, then
    displayed using zDisplay for mode-agnostic output.
    
    ValidationError Integration:
        Each field error is raised as a ValidationError exception to generate:
        - Formatted error message with field, value, and constraint
        - Context-aware actionable hint based on constraint type
        - Schema name for context
    
    Display Integration:
        Errors are displayed using ops.zcli.display.write_line() for mode-agnostic
        output (works in Terminal, Walker, and Bifrost modes). Each error is
        displayed with blank lines for readability.
    
    Logger Integration:
        - Error level: Summary of total errors
        - Debug level: Detailed validation summary
    
    Args:
        table: Table name where validation failed (used for schema_name context)
        errors: Dictionary mapping field names to error messages
                Example: {"email": "Pattern mismatch", "age": "Value out of range"}
        ops: Operations context with logger and zcli.display
    
    Returns:
        None: Displays errors and logs summary (no return value)
    
    Examples:
        # Display validation errors for multiple fields
        errors = {
            "email": "Pattern mismatch: must match email format",
            "age": "Value out of range: must be >= 18"
        }
        display_validation_errors("users", errors, ops)
        
        # Logs:
        # [FAIL] Validation failed for table 'users' with 2 error(s)
        # [FAIL] Validation summary: 2 field(s) failed for table 'users'
        
        # Displays:
        # 
        # [ValidationError] Field 'email' validation failed: Pattern mismatch
        # Hint: Check the field format requirements in the schema
        # 
        # 
        # [ValidationError] Field 'age' validation failed: Value out of range
        # Hint: Check the numeric range constraints in the schema
        # 
    
    Notes:
        - Uses ValidationError exception for formatted error messages
        - Value placeholder "<provided value>" used (actual value not available)
        - Each error displayed with blank lines for readability
        - Logger used for error/debug messages (not displayed to user)
        - zDisplay integration ensures mode-agnostic output
    """
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: Import - Get ValidationError exception
    # ─────────────────────────────────────────────────────────────────────────
    from zSys.errors import ValidationError
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Log Summary - Record validation failure
    # ─────────────────────────────────────────────────────────────────────────
    ops.logger.error(_ERR_VALIDATION_FAILED_LOG, table, len(errors))

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: Display Errors - Show each error with actionable hints
    # ─────────────────────────────────────────────────────────────────────────
    for field, message in errors.items():
        try:
            # Raise ValidationError to get actionable hints
            raise ValidationError(
                field=field,
                value=_VALUE_PLACEHOLDER,  # Actual value not available here
                constraint=message,
                schema_name=table
            )
        except ValidationError as e:
            # Display the formatted error with hint (mode-agnostic via zDisplay)
            ops.zcli.display.write_line("")
            ops.zcli.display.write_line(str(e))
            ops.zcli.display.write_line("")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 4: Log Details - Record validation summary for debugging
    # ─────────────────────────────────────────────────────────────────────────
    ops.logger.debug(_LOG_VALIDATION_SUMMARY, len(errors), table)

def execute_hook_if_defined(
    adapter: Any,
    hook_name: str,
    *args,
    **kwargs
) -> None:
    """
    Execute adapter hook method if it exists (DRY helper).
    
    Eliminates 4 occurrences of "if hasattr(adapter, hook_name)" checks across
    CRUD operations by providing a centralized hook execution pattern.
    
    Args:
        adapter: Backend adapter instance
        hook_name: Name of the hook method to execute (e.g., "after_insert")
        *args: Positional arguments to pass to the hook
        **kwargs: Keyword arguments to pass to the hook
    
    Examples:
        >>> # Instead of:
        >>> if hasattr(adapter, "after_insert"):
        >>>     adapter.after_insert(table, row_id)
        >>> 
        >>> # Use:
        >>> execute_hook_if_defined(adapter, "after_insert", table, row_id)
    
    Notes:
        - No-op if hook doesn't exist (safe to call)
        - Uses getattr with hasattr for safe method lookup
        - Supports both args and kwargs forwarding
    """
    if hasattr(adapter, hook_name):
        hook = getattr(adapter, hook_name)
        hook(*args, **kwargs)

def display_success_message(
    message: str,
    ops: Any
) -> None:
    """
    Display success message in mode-agnostic way (DRY helper).
    
    Eliminates 11 occurrences of "ops.display.success()" or "ops.zcli.display.success()"
    checks across CRUD operations by providing a centralized success display pattern.
    
    Args:
        message: Success message to display
        ops: Operations context with display
    
    Examples:
        >>> # Instead of:
        >>> ops.display.success(f"✓ Inserted row into {table} with ID: {row_id}")
        >>> 
        >>> # Use:
        >>> display_success_message(f"Inserted row into {table} with ID: {row_id}", ops)
    
    Notes:
        - Uses ops.display.success() for mode-agnostic output
        - Automatically prefixes message with checkmark (✓) if not present
        - Works in Terminal, Walker, and Bifrost modes
    """
    # Add checkmark prefix if not present
    if not message.startswith("✓"):
        message = _MSG_SUCCESS % message
    ops.display.success(message)
