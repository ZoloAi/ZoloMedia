# zCLI/subsystems/zData/zData_modules/shared/operations/crud_upsert.py
"""
UPSERT operation handler with adapter-specific conflict resolution strategies.

This module implements the UPSERT operation for zData's CRUD system. UPSERT is a
hybrid operation that performs an INSERT if the row doesn't exist, or an UPDATE
if it does (based on conflict detection). The specific implementation varies by
adapter.

Operation Overview
-----------------
The UPSERT operation combines INSERT and UPDATE into a single atomic operation:
- Attempts to INSERT a new row
- If a conflict is detected (row already exists), UPDATE the existing row instead
- Conflict detection is based on `conflict_fields` (defaults to first field)
- Returns True on success (regardless of INSERT or UPDATE path)

**Key Characteristics:**
- Atomic operation (no race conditions)
- Adapter-specific implementation (SQLite, PostgreSQL, CSV differ)
- Smart defaults (conflict_fields defaults to first field)
- No existence check (table may not exist yet - adapter handles creation)
- Hook/validation decisions delegated to adapter (INSERT vs UPDATE path)

Conflict Resolution
------------------
The `conflict_fields` parameter determines what constitutes a conflict:

**Default Behavior:**
```python
request = {"table": "users", "fields": ["id", "name"], "values": [1, "Alice"]}
# conflict_fields defaults to ["id"] (first field)
# If row with id=1 exists → UPDATE, else → INSERT
```

**Custom Conflict Fields:**
```python
request = {
    "table": "users",
    "fields": ["id", "email", "name"],
    "values": [1, "alice@example.com", "Alice"],
    "conflict_fields": ["email"]  # Detect conflict on email instead of id
}
# If row with email="alice@example.com" exists → UPDATE, else → INSERT
```

**Multiple Conflict Fields (Composite Key):**
```python
request = {
    "table": "user_permissions",
    "fields": ["user_id", "resource_id", "permission"],
    "values": [1, 42, "read"],
    "conflict_fields": ["user_id", "resource_id"]  # Composite key
}
# If row with user_id=1 AND resource_id=42 exists → UPDATE, else → INSERT
```

Adapter-Specific Behavior
-------------------------
Each adapter implements UPSERT differently:

**SQLite Adapter:**
- Uses `INSERT OR REPLACE` syntax
- Simple and efficient for SQLite
- Deletes old row and inserts new one (PRIMARY KEY or UNIQUE constraint based)
- Example: `INSERT OR REPLACE INTO users (id, name) VALUES (1, 'Alice')`

**PostgreSQL Adapter:**
- Uses `INSERT ... ON CONFLICT ... DO UPDATE` syntax (PostgreSQL 9.5+)
- More sophisticated, allows partial updates
- Preserves existing row, updates only specified fields
- Example: `INSERT INTO users (id, name) VALUES (1, 'Alice') ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name`

**CSV Adapter:**
- Uses pandas DataFrame merge strategy
- In-memory merge of existing and new data
- Overwrites existing row with new data on conflict
- Persists merged DataFrame to CSV file

Hook Integration (Adapter-Level)
--------------------------------
Unlike INSERT/UPDATE operations where hooks are explicit, UPSERT delegates hook
execution to the adapter. The adapter decides whether to trigger INSERT hooks or
UPDATE hooks based on whether the operation performs an insert or update:

**If Row Doesn't Exist (INSERT path):**
- Adapter may trigger `onBeforeInsert` hook
- Adapter may trigger `onAfterInsert` hook

**If Row Exists (UPDATE path):**
- Adapter may trigger `onBeforeUpdate` hook
- Adapter may trigger `onAfterUpdate` hook

**Note:** Hook behavior is adapter-specific. Some adapters may not support hooks
for UPSERT operations, as the INSERT/UPDATE path is determined at execution time.

Validation Integration (Adapter-Level)
--------------------------------------
Similar to hooks, validation is delegated to the adapter:

**If Row Doesn't Exist (INSERT path):**
- Adapter may call `validator.validate_insert(table, data)`

**If Row Exists (UPDATE path):**
- Adapter may call `validator.validate_update(table, data)`

**Note:** Validation behavior is adapter-specific and may occur at execution time.

No Existence Check
-----------------
Unlike other CRUD operations, UPSERT uses `check_exists=False` when extracting
the table name. This is intentional:

**Rationale:**
- Table may not exist yet (first UPSERT creates it)
- Adapter handles table creation if needed
- Avoids unnecessary pre-flight checks
- Reduces race conditions in concurrent environments

Return Value
-----------
UPSERT returns `True` on success, regardless of whether an INSERT or UPDATE occurred.

**Comparison with other operations:**
- INSERT: Returns `True` on success
- UPDATE: Returns `count > 0` (boolean from comparison)
- DELETE: Returns `count > 0` (boolean from comparison)
- **UPSERT: Returns `True` on success** (consistent with INSERT)

This simplifies usage - caller doesn't need to know if INSERT or UPDATE happened.

Execution Flow
-------------
The UPSERT operation follows a 4-phase execution flow:

    1. **Table Extraction:** Extract and validate table name (no existence check)
       ↓
    2. **Field/Value Extraction:** Extract field/value pairs (explicit or from options)
       ↓
    3. **Conflict Fields Resolution:** Extract or default conflict_fields (first field)
       ↓
    4. **Upsert Execution:** Execute adapter's upsert() method
       - Adapter decides INSERT vs UPDATE
       - Adapter handles hooks/validation (if supported)
       - Returns row_id or True

Usage Examples
-------------
**Basic UPSERT (default conflict on first field):**
    >>> request = {"table": "users", "fields": ["id", "name"], "values": [1, "Alice"]}
    >>> result = handle_upsert(request, ops)
    [OK] Upserted row with ID: 1

**UPSERT with custom conflict_fields:**
    >>> request = {
    ...     "table": "users",
    ...     "fields": ["id", "email", "name"],
    ...     "values": [1, "alice@example.com", "Alice"],
    ...     "conflict_fields": ["email"]
    ... }
    >>> result = handle_upsert(request, ops)
    [OK] Upserted row with ID: 1

**UPSERT with composite key:**
    >>> request = {
    ...     "table": "user_permissions",
    ...     "fields": ["user_id", "resource_id", "permission"],
    ...     "values": [1, 42, "read"],
    ...     "conflict_fields": ["user_id", "resource_id"]
    ... }
    >>> result = handle_upsert(request, ops)
    [OK] Upserted row with ID: None  # Composite key, no single ID

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm UPSERT operations
- quantum_data.py: Quantum paradigm UPSERT operations
- data_operations.py: CRUD operation router
"""

from zOS import Any, Dict

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_UPSERT = "UPSERT"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_FIELDS = "fields"
_KEY_VALUES = "values"
_KEY_TABLE = "table"
_KEY_CONFLICT_FIELDS = "conflict_fields"
_KEY_OPTIONS = "options"

# ============================================================
# Module Constants - Conflict Strategies
# ============================================================

_CONFLICT_REPLACE = "REPLACE"  # SQLite: INSERT OR REPLACE
_CONFLICT_UPDATE = "UPDATE"    # PostgreSQL: ON CONFLICT DO UPDATE
_CONFLICT_MERGE = "MERGE"      # CSV: DataFrame merge

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_EXTRACT_TABLE = "Extracting table from request for %s operation"
_LOG_EXTRACT_FIELDS = "Extracting fields/values from request"
_LOG_EXTRACT_CONFLICT = "Extracting conflict_fields from request"
_LOG_UPSERT = "Executing upsert operation on table %s"
_LOG_SUCCESS = "[OK] Upserted row with ID: %s"
_LOG_INSERT_PATH = "UPSERT taking INSERT path (row doesn't exist)"
_LOG_UPDATE_PATH = "UPSERT taking UPDATE path (row exists)"
_LOG_DEFAULT_CONFLICT = "Using default conflict_fields: first field"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_TABLE = "No table specified for UPSERT operation"
_ERR_NO_FIELDS = "No fields specified for UPSERT operation"
_ERR_UPSERT_FAILED = "Upsert operation failed"
_ERR_VALIDATION_FAILED = "Validation failed"
_ERR_NO_CONFLICT_FIELDS = "No conflict_fields specified and no fields available"
_ERR_INVALID_DATA = "Invalid data format"
_ERR_ADAPTER_NOT_SUPPORT = "Adapter does not support UPSERT operation"

# ============================================================
# Imports - Helper Functions
# ============================================================

try:
    from .helpers import extract_table_from_request, extract_field_values
except ImportError:
    from helpers import extract_table_from_request, extract_field_values

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_upsert"]


# ============================================================
# CRUD Operation - UPSERT
# ============================================================

def handle_upsert(request: Dict[str, Any], ops: Any) -> bool:
    """
    Handle UPSERT operation to insert or update rows based on conflict detection.
    
    UPSERT combines INSERT and UPDATE into a single atomic operation. If the row
    doesn't exist (based on conflict_fields), it performs an INSERT. If the row
    exists, it performs an UPDATE. The specific implementation is adapter-dependent.

    Args:
        request (Dict[str, Any]): The UPSERT request with the following keys:
            - "table" (str): Name of the table to upsert into
            - "fields" (List[str]): List of field names
            - "values" (List[Any]): List of values (same order as fields)
            - "conflict_fields" (List[str], optional): Fields to check for conflicts
              Defaults to [fields[0]] (first field) if not specified
            - "options" (Dict, optional): Alternative way to provide field/value pairs
        ops (Any): The operations object with the following attributes/methods:
            - logger: Logger instance for operation tracking
            - upsert(table, fields, values, conflict_fields): Execute the UPSERT

    Returns:
        bool: True if upsert succeeded (regardless of INSERT or UPDATE path),
              False if operation failed.

    Raises:
        No explicit exceptions are raised. Errors are logged and False is returned.

    Examples:
        >>> # Basic UPSERT (conflict on first field - id)
        >>> request = {"table": "users", "fields": ["id", "name"], "values": [1, "Alice"]}
        >>> result = handle_upsert(request, ops)
        [OK] Upserted row with ID: 1
        
        >>> # UPSERT with custom conflict_fields (detect conflict on email)
        >>> request = {
        ...     "table": "users",
        ...     "fields": ["id", "email", "name"],
        ...     "values": [1, "alice@example.com", "Alice"],
        ...     "conflict_fields": ["email"]
        ... }
        >>> result = handle_upsert(request, ops)
        [OK] Upserted row with ID: 1
        
        >>> # UPSERT with composite key (multiple conflict fields)
        >>> request = {
        ...     "table": "user_permissions",
        ...     "fields": ["user_id", "resource_id", "permission"],
        ...     "values": [1, 42, "read"],
        ...     "conflict_fields": ["user_id", "resource_id"]
        ... }
        >>> result = handle_upsert(request, ops)
        [OK] Upserted row with ID: None

    Note:
        - conflict_fields defaults to first field if not specified
        - Adapter-specific: SQLite uses INSERT OR REPLACE, PostgreSQL uses ON CONFLICT
        - Hook/validation delegated to adapter (INSERT vs UPDATE path decided at runtime)
        - No existence check (check_exists=False) - table may not exist yet
        - Returns True on success (differs from UPDATE/DELETE which return count > 0)
    """
    # ============================================================
    # Phase 1: Table Extraction (no existence check)
    # ============================================================
    table = extract_table_from_request(request, _OP_UPSERT, ops, check_exists=False)
    if not table:
        return False

    # ============================================================
    # Phase 2: Field/Value Extraction (explicit or from options)
    # ============================================================
    fields = request.get(_KEY_FIELDS, [])
    values = request.get(_KEY_VALUES)

    # If no explicit values, extract from options
    if not values:
        fields, values = extract_field_values(request, _OP_UPSERT, ops)
        if not fields:
            return False

    # ============================================================
    # Phase 3: Conflict Fields Resolution (smart default)
    # ============================================================
    conflict_fields = request.get(_KEY_CONFLICT_FIELDS, [fields[0]] if fields else [])

    # ============================================================
    # Phase 4: Upsert Execution (adapter decides INSERT vs UPDATE)
    # ============================================================
    row_id = ops.upsert(table, fields, values, conflict_fields)
    ops.logger.info(_LOG_SUCCESS, row_id)
    
    return True
