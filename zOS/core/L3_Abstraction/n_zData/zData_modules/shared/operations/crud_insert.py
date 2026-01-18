# zCLI/subsystems/zData/zData_modules/shared/operations/crud_insert.py
"""
INSERT operation handler with hooks, validation, and flexible data sources.

This module implements the INSERT operation for zData's CRUD system. It provides
a comprehensive handler for inserting rows into database tables with support for
multiple data sources, pre/post-insert hooks, and schema-based validation.

Operation Overview
-----------------
The INSERT operation adds a new row to an existing table. The handler supports:
- Multiple data sources (explicit fields/values, data dict, command-line options)
- Pre-insert hooks (onBeforeInsert) for data modification or abortion
- Schema-based validation (required fields, data types, patterns, format, plugins)
- Post-insert hooks (onAfterInsert) for side effects
- Integration with zDialog (form submissions)
- Flexible error handling and logging

Execution Flow
-------------
The INSERT operation follows a 6-phase execution flow:

    1. **Table Extraction:** Extract and validate table name from request
       ↓
    2. **Data Collection:** Gather field/value pairs from multiple sources
       ↓
    3. **onBeforeInsert Hook:** Execute pre-insert hook (optional)
       - Can modify data (return dict to update fields)
       - Can abort operation (return False)
       ↓
    4. **Validation:** Validate data against schema rules
       - Required fields check
       - Data type validation
       - Pattern matching (regex)
       - Format validation (email, url, etc.)
       - Plugin validators (custom business logic)
       ↓
    5. **Insert Execution:** Execute adapter's insert() method
       - Returns row_id (primary key or last insert ID)
       ↓
    6. **onAfterInsert Hook:** Execute post-insert hook (optional)
       - Receives inserted data + row_id
       - For side effects (notifications, logging, etc.)

Data Sources
-----------
The handler supports three data sources (checked in order):

**1. Data Dictionary (from zDialog):**
    request["data"] = {"name": "Alice", "age": 30}
    - Most common source for form submissions
    - Used by zDialog for interactive forms

**2. Explicit Fields/Values:**
    request["fields"] = ["name", "age"]
    request["values"] = ["Alice", 30]
    - Direct specification of columns and values
    - Used for programmatic inserts

**3. Command-Line Options:**
    request["name"] = "Alice"
    request["age"] = 30
    - Extracted by extract_field_values helper
    - Used for CLI commands

Hook Integration
---------------
**onBeforeInsert Hook:**
- Executed before validation
- Receives: {"zConv": data_dict, "table": table_name}
- Can modify data: Return dict to update/add fields
- Can abort: Return False to cancel insert
- Use cases: data enrichment, computed fields, business rules

**onAfterInsert Hook:**
- Executed after successful insert
- Receives: {"zConv": data_dict, "table": table_name, "row_id": insert_id}
- Return value ignored (side effects only)
- Use cases: notifications, audit logs, cascade operations

zConv Pattern
------------
"zConv" (zCLI Convention) is the standard key used to pass data dictionaries
in hook contexts. It represents the current conversation/transaction data and
is used consistently across zCLI subsystems (zDialog, zData, zWizard, zFunc).

Validation Integration
---------------------
Data validation is performed via ops.validator.validate_insert(), which enforces:
- Required fields (from schema)
- Data types (int, float, str, bool)
- Pattern matching (regex)
- Format validation (email, url, date, etc.)
- Plugin validators (custom business logic via zFunc)

If validation fails, errors are displayed via display_validation_errors() and
the operation is aborted.

Usage Examples
-------------
**Basic INSERT:**
    >>> request = {
    ...     "table": "users",
    ...     "data": {"name": "Alice", "email": "alice@example.com"}
    ... }
    >>> result = handle_insert(request, ops)
    [OK] Inserted row with ID: 1

**INSERT with onBeforeInsert Hook:**
    >>> # Schema with hook to add timestamp
    >>> schema = {
    ...     "users": {
    ...         "onBeforeInsert": "&add_timestamp"
    ...     }
    ... }
    >>> # Plugin function adds created_at field
    >>> result = handle_insert(request, ops)

**INSERT with Validation Errors:**
    >>> request = {"table": "users", "data": {"name": ""}}  # Empty name
    >>> result = handle_insert(request, ops)
    [ERROR] Validation failed for table 'users':
      - name: Field is required

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm INSERT operations
- quantum_data.py: Quantum paradigm INSERT operations
- data_operations.py: CRUD operation router
"""

from zOS import Any, Dict

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_INSERT = "INSERT"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_FIELDS = "fields"
_KEY_VALUES = "values"
_KEY_DATA = "data"
_KEY_TABLE = "table"
_KEY_SCHEMA = "schema"
_KEY_ROW_ID = "row_id"

# ============================================================
# Module Constants - Hook Names
# ============================================================

_HOOK_BEFORE_INSERT = "onBeforeInsert"
_HOOK_AFTER_INSERT = "onAfterInsert"

# ============================================================
# Module Constants - zConv Key
# ============================================================

_ZCONV_KEY = "zConv"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_EXTRACT_TABLE = "Extracting table from request for %s operation"
_LOG_EXTRACT_FIELDS = "Extracting fields/values from request"
_LOG_BUILD_DATA = "Building data dictionary from fields/values"
_LOG_HOOK_BEFORE = "Executing %s hook for %s"
_LOG_HOOK_AFTER = "Executing %s hook for %s"
_LOG_VALIDATE = "Validating data for %s operation on table %s"
_LOG_INSERT = "Executing insert operation on table %s"
_LOG_SUCCESS = "[OK] Inserted row with ID: %s"
_LOG_HOOK_ABORT = "%s hook returned False, aborting %s operation"
_LOG_HOOK_MODIFY = "%s hook returned dict, updating data"
_LOG_VALIDATION_ERROR = "Validation failed for table %s"
_LOG_INSERT_ERROR = "Insert operation failed for table %s"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_TABLE = "No table specified for INSERT operation"
_ERR_NO_FIELDS = "No fields specified for INSERT operation"
_ERR_HOOK_ABORT = "onBeforeInsert hook aborted operation"
_ERR_VALIDATION_FAILED = "Validation failed"
_ERR_INSERT_FAILED = "Insert operation failed"
_ERR_NO_DATA = "No data provided for INSERT operation"
_ERR_INVALID_DATA = "Invalid data format"
_ERR_HOOK_ERROR = "Hook execution error"

# ============================================================
# Imports - Helper Functions
# ============================================================

try:
    from .helpers import (
        extract_table_from_request,
        extract_field_values,
        display_validation_errors
    )
except ImportError:
    from helpers import (
        extract_table_from_request,
        extract_field_values,
        display_validation_errors
    )

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_insert"]



# ============================================================
# CRUD Operations - INSERT
# ============================================================

def handle_insert(request: Dict[str, Any], ops: Any) -> bool:
    """
    Handle INSERT operation to insert a new row into an existing table.

    This function implements the complete INSERT workflow including table validation,
    data collection from multiple sources, pre-insert hooks, schema validation,
    insert execution, and post-insert hooks.

    Args:
        request: Request dictionary containing operation parameters
            - "table" (str): Table name to insert into
            - "data" (dict, optional): Data dictionary (from zDialog)
            - "fields" (list, optional): Field names
            - "values" (list, optional): Field values
            - Additional keys extracted as field/value pairs (command-line)
        ops: Operations object providing:
            - schema (dict): Table schemas with validation rules and hooks
            - validator: Validator instance for data validation
            - logger: Logger instance for diagnostic output
            - insert(table, fields, values): Insert method
            - execute_hook(hook, context): Hook execution method

    Returns:
        bool: True if insert succeeded, False if failed (validation, hook abort, etc.)

    Raises:
        None: All errors are logged and return False

    Examples:
        >>> # Basic INSERT with data dict
        >>> request = {"table": "users", "data": {"name": "Alice", "age": 30}}
        >>> result = handle_insert(request, ops)
        [OK] Inserted row with ID: 1

        >>> # INSERT with hook that adds timestamp
        >>> request = {"table": "logs", "data": {"message": "System started"}}
        >>> result = handle_insert(request, ops)
        Executing onBeforeInsert hook for logs
        [OK] Inserted row with ID: 42

    Notes:
        - Data sources checked in order: data dict, fields/values, command-line
        - onBeforeInsert hook can modify data or abort (return False)
        - Validation enforced via validator.validate_insert()
        - onAfterInsert hook for side effects (notifications, logging)
        - zConv key used to pass data in hook context
    """
    # Phase 1: Extract and validate table name
    table = extract_table_from_request(request, _OP_INSERT, ops, check_exists=True)
    if not table:
        return False

    # Phase 2: Extract field/value pairs from request
    fields = request.get(_KEY_FIELDS, [])
    values = request.get(_KEY_VALUES)
    
    # Check if data dictionary is provided (from zDialog/zData)
    data_dict = request.get(_KEY_DATA)
    if data_dict and isinstance(data_dict, dict):
        fields = list(data_dict.keys())
        values = list(data_dict.values())
    # If no explicit values, extract from command-line options
    elif not values:
        fields, values = extract_field_values(request, _OP_INSERT, ops)
        if not fields:
            return False

    # Build data dictionary for validation and hooks
    data = dict(zip(fields, values))

    # Phase 2.5: Auto-hash password fields (if zHash: bcrypt in schema)
    table_schema = ops.schema.get(table, {})
    hash_modified = False
    for field_name, field_value in list(data.items()):
        field_def = table_schema.get(field_name, {})
        if isinstance(field_def, dict) and field_def.get('zHash') == 'bcrypt':
            # Hash the password using zAuth
            if ops.zcli and hasattr(ops.zcli, 'auth'):
                try:
                    ops.logger.info(f"[zData] Auto-hashing field '{field_name}' with bcrypt (plaintext MASKED for security)")
                    hashed_value = ops.zcli.auth.hash_password(str(field_value))
                    data[field_name] = hashed_value
                    hash_modified = True
                    ops.logger.debug(f"[zData] Field '{field_name}' hashed successfully (hash length: {len(hashed_value)} chars)")
                except Exception as e:
                    ops.logger.error(f"[zData] Failed to hash field '{field_name}': {e}")
                    return False
            else:
                ops.logger.error(f"[zData] zHash: bcrypt specified for '{field_name}' but zAuth not available")
                return False
    
    # Rebuild fields/values from potentially modified data
    if hash_modified:
        fields = list(data.keys())
        values = list(data.values())

    # Phase 3: Execute onBeforeInsert hook (can modify data or abort)
    on_before_insert = table_schema.get(_HOOK_BEFORE_INSERT)
    if on_before_insert:
        ops.logger.info(_LOG_HOOK_BEFORE, _HOOK_BEFORE_INSERT, table)
        hook_result = ops.execute_hook(on_before_insert, {_ZCONV_KEY: data, _KEY_TABLE: table})
        if hook_result is False:
            ops.logger.error(_LOG_HOOK_ABORT, _HOOK_BEFORE_INSERT, _OP_INSERT)
            return False
        # If hook returns a dict, use it to update data
        if isinstance(hook_result, dict):
            ops.logger.debug(_LOG_HOOK_MODIFY, _HOOK_BEFORE_INSERT)
            data.update(hook_result)
            fields = list(data.keys())
            values = list(data.values())

    # Phase 4: Validate data before inserting
    is_valid, errors = ops.validator.validate_insert(table, data)
    if not is_valid:
        ops.logger.error(_LOG_VALIDATION_ERROR, table)
        display_validation_errors(table, errors, ops)
        return False

    # Phase 5: Execute insert using operations' insert method
    row_id = ops.insert(table, fields, values)
    ops.logger.info(_LOG_SUCCESS, row_id)

    # Phase 6: Execute onAfterInsert hook (for side effects)
    on_after_insert = table_schema.get(_HOOK_AFTER_INSERT)
    if on_after_insert:
        ops.logger.info(_LOG_HOOK_AFTER, _HOOK_AFTER_INSERT, table)
        context = {_ZCONV_KEY: data, _KEY_TABLE: table, _KEY_ROW_ID: row_id}
        ops.execute_hook(on_after_insert, context)

    return True
