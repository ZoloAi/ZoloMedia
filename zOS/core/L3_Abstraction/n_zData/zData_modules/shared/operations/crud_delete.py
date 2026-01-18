# zCLI/subsystems/zData/zData_modules/shared/operations/crud_delete.py
"""
DELETE operation handler with CRITICAL safety warnings and WHERE clause validation.

⚠️ **WARNING: IRREVERSIBLE OPERATION** ⚠️

This module implements the DELETE operation for zData's CRUD system. DELETE is a
PERMANENT and IRREVERSIBLE operation that removes rows from database tables. This
handler emphasizes safety through comprehensive WHERE clause warnings and best
practice documentation.

Operation Overview
-----------------
The DELETE operation permanently removes rows from a table. The handler provides:
- WHERE clause filtering (which rows to delete)
- **CRITICAL safety warning if WHERE clause is missing** (prevents accidental full-table deletes)
- Returns boolean based on affected row count (count > 0)
- NO pre/post-delete hooks (by design for safety - reduces complexity)
- Simple, clean implementation (appropriate for destructive operation)

⚠️ **CRITICAL: WHERE Clause Safety** ⚠️
---------------------------------------
**DELETE without a WHERE clause will delete ALL rows in the table.**

This is often catastrophic and unintended. The handler provides safety by:
- **Warning if WHERE clause is missing** (warn_if_missing=True)
- Logging a CRITICAL warning message to alert the operator
- Still allowing the operation (but with very clear warning)

**BEST PRACTICE:** ALWAYS provide a WHERE clause unless you intentionally want to
delete all rows. Even then, consider using TRUNCATE or DROP/CREATE instead.

**RECOMMENDED: Test WHERE clause with SELECT first:**
```python
# STEP 1: Test your WHERE clause with SELECT to preview affected rows
request = {"table": "users", "where": "status = 'inactive'"}
rows = handle_read(request, ops)  # Preview which rows will be deleted
print(f"Would delete {len(rows)} rows")

# STEP 2: If satisfied, proceed with DELETE using the SAME WHERE clause
request = {"table": "users", "where": "status = 'inactive'"}
result = handle_delete(request, ops)
```

Execution Flow
-------------
The DELETE operation follows a simple 3-phase execution flow:

    1. **Table Extraction:** Extract and validate table name from request
       ↓
    2. **WHERE Clause Extraction:** Extract WHERE clause (WARNS if missing)
       ↓
    3. **Delete Execution:** Execute adapter's delete() method
       - Returns count of affected rows

No Hooks (By Design)
-------------------
Unlike INSERT and UPDATE operations, DELETE intentionally has NO hooks:
- No onBeforeDelete hook
- No onAfterDelete hook

**Rationale:** DELETE is a destructive, irreversible operation. Adding hooks would:
1. Increase complexity and potential for bugs
2. Create more opportunities for unintended side effects
3. Make the operation less predictable and harder to audit

Keeping DELETE simple and hook-free is a deliberate design choice for safety
and clarity. If you need side effects (audit logs, notifications), implement
them at the application layer AFTER successful DELETE.

Cascade Behavior
---------------
DELETE operations may trigger cascading deletes through foreign key constraints:

**Database-Level Cascades:**
- If a table has foreign key constraints with `ON DELETE CASCADE`
- Deleting a parent row will automatically delete related child rows
- This happens at the database level (SQLite, PostgreSQL)
- The returned count only reflects the primary table, not cascaded deletes

**Example:**
```python
# If users.id has foreign key from posts.user_id with ON DELETE CASCADE
request = {"table": "users", "where": "id = 1"}
result = handle_delete(request, ops)
# Deletes user with id=1 AND all posts by that user (cascade)
# But count only reflects 1 (the user row)
```

**CSV Adapter:** No cascade support (CSV has no foreign key constraints)

Return Value
-----------
The handler returns a boolean based on affected row count:
- Returns count > 0 (True if at least one row was deleted)
- Returns False if no rows were affected or if operation failed

This differs from INSERT (returns True on success) because DELETE may legitimately
affect zero rows if WHERE clause matches nothing (not necessarily an error).

Safety Best Practices
---------------------
1. **Test WHERE with SELECT first:** Preview affected rows before deleting
2. **Use transactions:** Wrap DELETE in a transaction for rollback capability
3. **Backup before mass deletes:** Create backups before large DELETE operations
4. **Avoid DELETE without WHERE:** Always specify which rows to delete
5. **Consider soft deletes:** Use UPDATE to set a "deleted" flag instead
6. **Understand cascades:** Know which related data will be cascade-deleted
7. **Use LIMIT carefully:** Some databases support DELETE ... LIMIT (be cautious)

Usage Examples
-------------
**Safe DELETE with WHERE (RECOMMENDED):**
    >>> request = {"table": "users", "where": "id = 1"}
    >>> result = handle_delete(request, ops)
    [OK] Deleted 1 row(s) from users

**DELETE without WHERE (DANGEROUS - ALL ROWS DELETED):**
    >>> request = {"table": "users"}
    >>> result = handle_delete(request, ops)
    [CRITICAL WARNING] No WHERE clause provided for DELETE on users (will delete ALL rows)
    [OK] Deleted 150 row(s) from users  # ALL rows deleted!

**Test with SELECT first (BEST PRACTICE):**
    >>> # Preview affected rows
    >>> preview = {"table": "users", "where": "last_login < '2020-01-01'"}
    >>> rows = handle_read(preview, ops)
    >>> print(f"Would delete {len(rows)} inactive users")
    >>> 
    >>> # If satisfied, delete
    >>> delete_req = {"table": "users", "where": "last_login < '2020-01-01'"}
    >>> result = handle_delete(delete_req, ops)

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm DELETE operations
- quantum_data.py: Quantum paradigm DELETE operations
- data_operations.py: CRUD operation router
"""

from zOS import Any, Dict

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_DELETE = "DELETE"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_TABLE = "table"
_KEY_WHERE = "where"
_KEY_COUNT = "count"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_EXTRACT_TABLE = "Extracting table from request for %s operation"
_LOG_EXTRACT_WHERE = "Extracting WHERE clause from request"
_LOG_DELETE = "Executing delete operation on table %s"
_LOG_SUCCESS = "[OK] Deleted %d row(s) from %s"
_LOG_NO_ROWS = "No rows affected by DELETE (WHERE clause matched nothing)"
_LOG_WARNING_NO_WHERE = "[CRITICAL WARNING] No WHERE clause - will delete ALL rows"
_LOG_CASCADE = "Foreign key cascade may delete related rows in other tables"
_LOG_PERMANENT = "DELETE is permanent and irreversible"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_TABLE = "No table specified for DELETE operation"
_ERR_DELETE_FAILED = "Delete operation failed"
_ERR_NO_WHERE = "No WHERE clause provided (will delete ALL rows)"
_ERR_TABLE_NOT_EXIST = "Table does not exist"
_ERR_CASCADE_FAILED = "Cascade delete failed on related tables"

# ============================================================
# Module Constants - Safety Warnings
# ============================================================

_WARN_NO_WHERE = "DELETE without WHERE clause will delete ALL rows"
_WARN_IRREVERSIBLE = "DELETE is permanent and cannot be undone without backups"
_WARN_CASCADE = "Foreign key constraints may cascade delete to related tables"
_WARN_TEST_SELECT = "Test WHERE clause with SELECT before DELETE"
_WARN_BACKUP = "Create backup before large DELETE operations"

# ============================================================
# Imports - Helper Functions
# ============================================================

try:
    from .helpers import extract_table_from_request, extract_where_clause
except ImportError:
    from helpers import extract_table_from_request, extract_where_clause

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_delete"]

# ============================================================
# CRUD Operation - DELETE
# ============================================================

def handle_delete(request: Dict[str, Any], ops: Any) -> bool:
    """
    Handle DELETE operation to permanently remove rows from a table.
    
    ⚠️ **WARNING:** DELETE is IRREVERSIBLE. Deleted data cannot be recovered without backups.
    
    This function implements the complete DELETE workflow including table extraction,
    WHERE clause safety validation, and delete execution. It emphasizes safety through
    critical warnings when WHERE clause is missing (which would delete ALL rows).

    Args:
        request (Dict[str, Any]): The DELETE request with the following keys:
            - "table" (str): Name of the table to delete from
            - "where" (str, optional): SQL WHERE clause (e.g., "id = 1")
              ⚠️ **CRITICAL:** Missing WHERE clause will delete ALL rows
        ops (Any): The operations object with the following attributes/methods:
            - logger: Logger instance for operation tracking
            - delete(table, where): Execute the DELETE operation

    Returns:
        bool: True if at least one row was deleted (count > 0), False if operation
              failed or no rows were affected. Note: Returning False for zero rows
              is not necessarily an error (WHERE clause may legitimately match nothing).

    Raises:
        No explicit exceptions are raised. Errors are logged and False is returned.

    Examples:
        >>> # Safe DELETE with WHERE clause (RECOMMENDED)
        >>> request = {"table": "users", "where": "id = 1"}
        >>> result = handle_delete(request, ops)
        [OK] Deleted 1 row(s) from users
        
        >>> # DANGEROUS: DELETE without WHERE (deletes ALL rows)
        >>> request = {"table": "users"}
        >>> result = handle_delete(request, ops)
        [CRITICAL WARNING] No WHERE clause provided for DELETE on users (will delete ALL rows)
        [OK] Deleted 150 row(s) from users  # ALL rows deleted!
        
        >>> # BEST PRACTICE: Test with SELECT first
        >>> preview = {"table": "users", "where": "last_login < '2020-01-01'"}
        >>> rows = handle_read(preview, ops)  # Preview affected rows
        >>> print(f"Would delete {len(rows)} rows")
        >>> # If satisfied, delete
        >>> result = handle_delete(preview, ops)

    Note:
        - DELETE is PERMANENT and IRREVERSIBLE
        - Test WHERE clause with SELECT first to preview affected rows
        - Use transactions for rollback capability
        - Understand foreign key cascades (may delete related rows)
        - No hooks by design (no onBeforeDelete/onAfterDelete for safety)
        - Returns boolean based on count > 0 (differs from INSERT)
    """
    # ============================================================
    # Phase 1: Table Extraction
    # ============================================================
    table = extract_table_from_request(request, _OP_DELETE, ops, check_exists=True)
    if not table:
        return False

    # ============================================================
    # Phase 2: WHERE Clause Extraction (CRITICAL safety warning if missing)
    # ============================================================
    where = extract_where_clause(request, ops, warn_if_missing=True)

    # ============================================================
    # Phase 3: Delete Execution (PERMANENT and IRREVERSIBLE)
    # ============================================================
    count = ops.delete(table, where)
    ops.logger.info(_LOG_SUCCESS, count, table)

    # Return True if at least one row was deleted (count > 0)
    return count > 0
