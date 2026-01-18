# zCLI/subsystems/zData/zData_modules/shared/operations/crud_update.py
"""
UPDATE operation handler with hooks, validation, and WHERE clause safety.

This module implements the UPDATE operation for zData's CRUD system. It provides
a comprehensive handler for modifying existing rows in database tables with support
for partial updates, pre/post-update hooks, schema-based validation, and WHERE
clause safety warnings.

Operation Overview
-----------------
The UPDATE operation modifies existing rows in a table. The handler supports:
- Partial updates (update specific fields, not all columns)
- WHERE clause filtering (which rows to update)
- WHERE clause safety warning (warns if missing to prevent accidental full-table updates)
- Pre-update hooks (onBeforeUpdate) for data modification or abortion
- Schema-based validation (required fields, data types, patterns, format, plugins)
- Post-update hooks (onAfterUpdate) for side effects
- Returns boolean based on affected row count (count > 0)
- Hook receives WHERE clause for conditional logic

Execution Flow
-------------
The UPDATE operation follows a 6-phase execution flow:

    1. **Table Extraction:** Extract and validate table name from request
       ↓
    2. **Field/Value Extraction:** Extract field/value pairs to update
       ↓
    3. **WHERE Clause Extraction:** Extract WHERE clause (warns if missing)
       ↓
    4. **onBeforeUpdate Hook:** Execute pre-update hook (optional)
       - Can modify data (return dict to update fields)
       - Can abort operation (return False)
       - Receives WHERE clause for conditional logic
       ↓
    5. **Validation:** Validate data against schema rules
       - Data type validation
       - Pattern matching (regex)
       - Format validation (email, url, etc.)
       - Plugin validators (custom business logic)
       ↓
    6. **Update Execution:** Execute adapter's update() method
       - Returns count of affected rows
       ↓
    7. **onAfterUpdate Hook:** Execute post-update hook (optional)
       - Receives updated data + WHERE clause + count
       - For side effects (notifications, logging, etc.)

Partial Updates
--------------
UPDATE supports partial updates - you can update specific fields without providing
all columns:

    request = {"table": "users", "fields": ["email"], "values": ["new@example.com"], "where": "id = 1"}
    # Only updates email field, other fields unchanged

WHERE Clause Safety
------------------
**IMPORTANT:** UPDATE without a WHERE clause will update ALL rows in the table.

The handler provides safety by:
- Warning if WHERE clause is missing (warn_if_missing=True)
- Logging a warning message to alert the operator
- Still allowing the operation (but with clear warning)

**Best Practice:** Always provide a WHERE clause unless you intentionally want to
update all rows.

Hook Integration
---------------
**onBeforeUpdate Hook:**
- Executed before validation
- Receives: {"zConv": data_dict, "table": table_name, "where": where_clause}
- Can modify data: Return dict to update/add fields
- Can abort: Return False to cancel update
- WHERE clause available for conditional logic
- Use cases: data enrichment, computed fields, conditional updates

**onAfterUpdate Hook:**
- Executed after successful update
- Receives: {"zConv": data_dict, "table": table_name, "where": where_clause, "count": affected_rows}
- Return value ignored (side effects only)
- Use cases: notifications, audit logs, cascade operations

zConv Pattern
------------
"zConv" (zCLI Convention) is the standard key used to pass data dictionaries
in hook contexts. It represents the current conversation/transaction data and
is used consistently across zCLI subsystems (zDialog, zData, zWizard, zFunc).

Validation Integration
---------------------
Data validation is performed via ops.validator.validate_update(), which enforces:
- Data types (int, float, str, bool)
- Pattern matching (regex)
- Format validation (email, url, date, etc.)
- Plugin validators (custom business logic via zFunc)

Note: Required field validation is typically less strict for UPDATE than INSERT,
as partial updates are allowed.

Return Value
-----------
The handler returns a boolean based on affected row count:
- Returns count > 0 (True if at least one row was updated)
- Returns False if no rows were affected or if operation failed

This differs from INSERT (returns True on success) because UPDATE may legitimately
affect zero rows if WHERE clause matches nothing.

Usage Examples
-------------
**Basic UPDATE with WHERE:**
    >>> request = {
    ...     "table": "users",
    ...     "fields": ["status"],
    ...     "values": ["active"],
    ...     "where": "id = 1"
    ... }
    >>> result = handle_update(request, ops)
    [OK] Updated 1 row(s) in users

**UPDATE without WHERE (all rows - WARNING):**
    >>> request = {"table": "users", "fields": ["status"], "values": ["active"]}
    >>> result = handle_update(request, ops)
    [WARN] No WHERE clause provided for UPDATE on users (will update ALL rows)
    [OK] Updated 150 row(s) in users

**UPDATE with onBeforeUpdate Hook:**
    >>> # Schema with hook to add updated_at timestamp
    >>> schema = {
    ...     "users": {
    ...         "onBeforeUpdate": "&add_updated_timestamp"
    ...     }
    ... }
    >>> result = handle_update(request, ops)

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm UPDATE operations
- quantum_data.py: Quantum paradigm UPDATE operations
- data_operations.py: CRUD operation router
"""

from zOS import Any, Dict

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_UPDATE = "UPDATE"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_FIELDS = "fields"
_KEY_VALUES = "values"
_KEY_TABLE = "table"
_KEY_WHERE = "where"
_KEY_SCHEMA = "schema"
_KEY_COUNT = "count"

# ============================================================
# Module Constants - Hook Names
# ============================================================

_HOOK_BEFORE_UPDATE = "onBeforeUpdate"
_HOOK_AFTER_UPDATE = "onAfterUpdate"

# ============================================================
# Module Constants - zConv Key
# ============================================================

_ZCONV_KEY = "zConv"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_EXTRACT_TABLE = "Extracting table from request for %s operation"
_LOG_EXTRACT_FIELDS = "Extracting fields/values from request"
_LOG_EXTRACT_WHERE = "Extracting WHERE clause from request"
_LOG_HOOK_BEFORE = "Executing %s hook for %s"
_LOG_HOOK_AFTER = "Executing %s hook for %s"
_LOG_VALIDATE = "Validating data for %s operation on table %s"
_LOG_UPDATE = "Executing update operation on table %s"
_LOG_SUCCESS = "[OK] Updated %d row(s) in %s"
_LOG_HOOK_ABORT = "%s hook returned False, aborting %s operation"
_LOG_HOOK_MODIFY = "%s hook returned dict, updating data"
_LOG_VALIDATION_ERROR = "Validation failed for table %s"
_LOG_NO_ROWS = "No rows affected by UPDATE (WHERE clause matched nothing)"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_TABLE = "No table specified for UPDATE operation"
_ERR_NO_FIELDS = "No fields specified for UPDATE operation"
_ERR_HOOK_ABORT = "onBeforeUpdate hook aborted operation"
_ERR_VALIDATION_FAILED = "Validation failed"
_ERR_UPDATE_FAILED = "Update operation failed"
_ERR_NO_WHERE = "No WHERE clause provided (will update ALL rows)"
_ERR_INVALID_DATA = "Invalid data format"
_ERR_HOOK_ERROR = "Hook execution error"

# ============================================================
# Imports - Helper Functions
# ============================================================

try:
    from .helpers import (
        extract_table_from_request,
        extract_where_clause,
        extract_field_values,
        display_validation_errors
    )
except ImportError:
    from helpers import (
        extract_table_from_request,
        extract_where_clause,
        extract_field_values,
        display_validation_errors
    )

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_update"]

# ============================================================
# CRUD Operation - UPDATE
# ============================================================

def handle_update(request: Dict[str, Any], ops: Any) -> bool:
    """
    Handle UPDATE operation to modify existing rows in a table.

    This function implements the complete UPDATE workflow including table/field extraction,
    WHERE clause safety, pre-update hooks, validation, update execution, and post-update
    hooks. It supports partial updates (update specific fields only) and provides safety
    warnings for missing WHERE clauses.

    Args:
        request (Dict[str, Any]): The UPDATE request with the following keys:
            - "table" (str): Name of the table to update
            - "fields" (List[str]): List of field names to update
            - "values" (List[Any]): List of values (same order as fields)
            - "where" (str, optional): SQL WHERE clause (e.g., "id = 1")
              WARNING: Missing WHERE clause will update ALL rows
        ops (Any): The operations object with the following attributes/methods:
            - schema (Dict): Schema dictionary with table definitions and hooks
            - logger: Logger instance for operation tracking
            - validator: Validator instance for data validation
            - execute_hook(hook_name, context): Execute a hook function
            - update(table, fields, values, where): Execute the UPDATE operation

    Returns:
        bool: True if at least one row was updated (count > 0), False if operation
              failed or no rows were affected. Note: This differs from INSERT which
              returns True on success, because UPDATE may legitimately affect zero
              rows if WHERE clause matches nothing.

    Raises:
        No explicit exceptions are raised. Errors are logged and False is returned.

    Examples:
        >>> # Basic UPDATE with WHERE clause
        >>> request = {
        ...     "table": "users",
        ...     "fields": ["email", "status"],
        ...     "values": ["newemail@example.com", "active"],
        ...     "where": "id = 1"
        ... }
        >>> result = handle_update(request, ops)
        [OK] Updated 1 row(s) in users

        >>> # UPDATE without WHERE (WARNING - updates ALL rows)
        >>> request = {"table": "users", "fields": ["status"], "values": ["active"]}
        >>> result = handle_update(request, ops)
        [WARN] No WHERE clause provided for UPDATE on users (will update ALL rows)
        [OK] Updated 150 row(s) in users

        >>> # UPDATE with onBeforeUpdate hook (adds updated_at timestamp)
        >>> # Schema: {"users": {"onBeforeUpdate": "&add_timestamp"}}
        >>> result = handle_update(request, ops)
        Executing onBeforeUpdate hook for users
        [OK] Updated 1 row(s) in users

    Note:
        - Partial updates are supported (update specific fields, not all columns)
        - WHERE clause is optional but strongly recommended (warns if missing)
        - onBeforeUpdate hook can modify data (return dict) or abort (return False)
        - Hook receives WHERE clause for conditional logic
        - onAfterUpdate hook receives count of affected rows
        - Returns boolean based on count > 0 (differs from INSERT)
    """
    # ============================================================
    # Phase 1: Table Extraction
    # ============================================================
    table = extract_table_from_request(request, _OP_UPDATE, ops, check_exists=True)
    if not table:
        return False

    # ============================================================
    # Phase 2: Field/Value Extraction
    # ============================================================
    # Check for explicit top-level fields/values first (consistent with UPSERT and documented API)
    fields = request.get("fields", [])
    values = request.get("values")

    # If no explicit values, extract from options dict (legacy support)
    if not values:
        fields, values = extract_field_values(request, _OP_UPDATE, ops)
        if not fields:
            return False
    elif not fields:
        # Values provided but no fields - error
        ops.logger.error("Values provided but no fields for UPDATE operation")
        return False

    # Build data dictionary for validation and hooks
    data = dict(zip(fields, values))

    # ============================================================
    # Phase 3: WHERE Clause Extraction (with safety warning)
    # ============================================================
    where = extract_where_clause(request, ops, warn_if_missing=True)

    # ============================================================
    # Phase 4: onBeforeUpdate Hook (data modification/abortion)
    # ============================================================
    table_schema = ops.schema.get(table, {})
    on_before_update = table_schema.get(_HOOK_BEFORE_UPDATE)
    if on_before_update:
        ops.logger.info(_LOG_HOOK_BEFORE, _HOOK_BEFORE_UPDATE, table)
        hook_result = ops.execute_hook(on_before_update, {
            _ZCONV_KEY: data,
            _KEY_TABLE: table,
            _KEY_WHERE: where
        })
        if hook_result is False:
            ops.logger.error(_LOG_HOOK_ABORT, _HOOK_BEFORE_UPDATE, _OP_UPDATE)
            return False
        # If hook returns a dict, use it to update data
        if isinstance(hook_result, dict):
            ops.logger.info(_LOG_HOOK_MODIFY, _HOOK_BEFORE_UPDATE)
            data.update(hook_result)
            fields = list(data.keys())
            values = list(data.values())

    # ============================================================
    # Phase 5: Validation
    # ============================================================
    is_valid, errors = ops.validator.validate_update(table, data)
    if not is_valid:
        ops.logger.error(_LOG_VALIDATION_ERROR, table)
        display_validation_errors(table, errors, ops)
        return False

    # ============================================================
    # Phase 6: Update Execution
    # ============================================================
    count = ops.update(table, fields, values, where)
    ops.logger.info(_LOG_SUCCESS, count, table)

    # ============================================================
    # Phase 7: onAfterUpdate Hook (side effects)
    # ============================================================
    on_after_update = table_schema.get(_HOOK_AFTER_UPDATE)
    if on_after_update:
        ops.logger.info(_LOG_HOOK_AFTER, _HOOK_AFTER_UPDATE, table)
        context = {
            _ZCONV_KEY: data,
            _KEY_TABLE: table,
            _KEY_WHERE: where,
            _KEY_COUNT: count
        }
        ops.execute_hook(on_after_update, context)

    # Return True if at least one row was updated (count > 0)
    return count > 0
