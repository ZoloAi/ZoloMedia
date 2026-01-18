# zCLI/subsystems/zData/zData_modules/shared/operations/ddl_drop.py
"""
⚠️ DROP TABLE operation handler with CRITICAL safety warnings.

⚠️⚠️⚠️ IRREVERSIBLE OPERATION WARNING ⚠️⚠️⚠️
This module implements the DROP TABLE DDL operation for zData. DROP TABLE is
a PERMANENT, IRREVERSIBLE operation that deletes tables and ALL their data
with NO POSSIBILITY OF RECOVERY without backups.

Operation Overview
-----------------
The DROP TABLE operation permanently removes database tables including:
- Table structure (schema definition)
- ALL table data (every single row)
- Indexes on the table
- Constraints associated with the table

⚠️ CRITICAL: Once executed, data is GONE FOREVER (unless you have backups).

Key characteristics:
- ⚠️ IRREVERSIBLE: No undo, no rollback (on some adapters), no recovery
- ⚠️ PERMANENT: Tables and ALL data deleted forever
- Batch support: Can drop multiple tables in one call
- Graceful skip: Non-existent tables skipped (doesn't error)
- Partial success: Returns True if ANY tables dropped

⚠️ CRITICAL Safety Warnings
---------------------------
**1. DATA LOSS - PERMANENT AND IRREVERSIBLE:**
   - ALL table data deleted forever
   - Cannot be undone without backup
   - No "recycle bin" or recovery mechanism

**2. CASCADE DELETION:**
   - Foreign key constraints may CASCADE to dependent tables
   - Dropping one table may delete data in OTHER tables
   - CASCADE behavior is database-level, not application-level

**3. SCHEMA INTEGRITY:**
   - Dropping tables can BREAK your application
   - Missing tables → runtime errors in queries
   - Application code may expect tables that no longer exist

**4. TRANSACTION LIMITATIONS:**
   - DDL may NOT be transactional (adapter-specific)
   - SQLite: Auto-commits immediately (cannot rollback)
   - PostgreSQL: Transactional (can rollback if in transaction)
   - CSV: Immediate file/directory deletion (cannot rollback)

**5. NO HOOKS:**
   - Like DELETE operation, no onBeforeDrop/onAfterDrop
   - No application-level validation before drop
   - Reduces complexity but increases risk

Cascade Behavior
---------------
Foreign key constraints with CASCADE can cause data loss in dependent tables:

**Example Scenario:**
```yaml
orders:
  order_id: {type: int, pk: true}
  user_id: {type: int, fk: users.id, on_delete: CASCADE}

users:
  id: {type: int, pk: true}
  name: {type: str}
```

**Dropping users table:**
```python
request = {"tables": ["users"]}
handle_drop(request, ops)  # ⚠️ MAY ALSO DELETE ALL ORDERS (CASCADE)
```

The CASCADE deletion happens at the database level:
- SQLite: PRAGMA foreign_keys enforced
- PostgreSQL: ON DELETE CASCADE in schema
- CSV: No foreign keys (no cascades)

Batch Drop Support
-----------------
Multiple tables can be dropped in one call for efficiency:

**Single table drop:**
```python
request = {"tables": ["users"]}
result = handle_drop(request, ops)
```

**Batch drop (multiple tables):**
```python
request = {"tables": ["logs", "sessions", "cache"]}
result = handle_drop(request, ops)
# Drops all 3 tables in sequence
```

⚠️ WARNING: Batch drops are efficient but DANGEROUS - dropping the wrong
tables can destroy critical data. ALWAYS double-check table names!

Table Existence Check
--------------------
The handler gracefully skips non-existent tables without erroring:

**Behavior:**
1. Checks if table exists (adapter.table_exists())
2. If exists: Drops the table
3. If NOT exists: Logs warning, skips table, continues with others

**Example:**
```python
request = {"tables": ["users", "nonexistent", "logs"]}
result = handle_drop(request, ops)
# Drops: users, logs (2 tables)
# Skips: nonexistent (warning logged)
# Returns: True (partial success)
```

This prevents errors from breaking batch operations.

Partial Success Handling
------------------------
Returns True if ANY tables were dropped (even if some were skipped):

**Partial success example:**
```python
request = {"tables": ["users", "nonexistent1", "logs", "nonexistent2"]}
result = handle_drop(request, ops)
# Drops: users, logs (2 tables)
# Skips: nonexistent1, nonexistent2 (2 warnings)
# Returns: True (because 2 tables were dropped)
```

Returns False ONLY if NO tables were dropped:
- Empty tables list provided
- All tables in list don't exist

Backup Recommendations
---------------------
⚠️ CRITICAL: ALWAYS backup before DROP operations!

**Best Practices:**
1. **Test in dev environment first**
2. **Create backup before DROP:**
   - SQLite: Copy .db file
   - PostgreSQL: pg_dump before DROP
   - CSV: Copy directory/files
3. **Verify backup validity** (test restore)
4. **Document what you're dropping** (change log)
5. **Get approval** for production drops
6. **Have rollback plan** ready

Transaction Limitations
----------------------
DDL operations may not be transactional (depends on adapter):

**SQLite:**
- DDL auto-commits immediately
- Cannot rollback DROP TABLE
- Executes outside any transaction

**PostgreSQL:**
- DDL is transactional
- Can rollback DROP TABLE if in transaction
- BEGIN; DROP TABLE users; ROLLBACK; (works)

**CSV:**
- No transaction support
- File/directory deleted immediately
- Cannot rollback

Schema Integrity
---------------
Dropping tables can break your application if code expects them:

**Example:**
```python
# Application code
def get_user(user_id):
    return ops.adapter.select("users", {"id": user_id})

# After dropping users table
get_user(1)  # ⚠️ ERROR: Table 'users' doesn't exist
```

**Prevention:**
- Check application dependencies before DROP
- Update application code to handle missing tables
- Consider schema migrations instead of DROP
- Use feature flags to disable features using dropped tables

Adapter Differences
------------------
Different adapters implement DROP differently:

**SQLite:**
- Deletes table from .db file
- File size may not shrink (VACUUM needed)
- Immediate, auto-commit

**PostgreSQL:**
- Network DDL command
- Transactional (can rollback)
- Server-side execution

**CSV:**
- Deletes CSV file and/or directory
- Filesystem operation
- Immediate, permanent

No Hooks
--------
Like DELETE operation, DROP TABLE has NO hooks:
- No onBeforeDrop callback
- No onAfterDrop callback

**Rationale:**
- Reduce complexity (DDL is already risky)
- Increase safety (no custom logic to fail)
- Improve auditability (direct adapter calls)
- Application-level validation should happen BEFORE calling this handler

Return Value
-----------
Returns True/False based on operation success:
- **True**: At least one table was dropped successfully
- **False**: No tables were dropped (empty list OR all tables don't exist)

**Note:** Partial success returns True (some tables dropped, others skipped).

⚠️ 8 Safety Best Practices
---------------------------
1. **BACKUP FIRST**: Always backup before DROP (test restore)
2. **Test in dev**: Never test DROP in production first
3. **Verify table names**: Double-check spelling, use HEAD to confirm
4. **Check dependencies**: Review foreign keys, application code
5. **Consider alternatives**: Rename table instead? Archive data first?
6. **Document rationale**: Why are you dropping this table?
7. **Get approval**: Production drops require approval
8. **Monitor after drop**: Watch for application errors

Usage Examples
-------------
**⚠️ Dangerous - Single table drop:**
    >>> # ALWAYS backup first!
    >>> request = {"tables": ["users"]}
    >>> result = handle_drop(request, ops)
    [OK] Dropped table: users
    [OK] Dropped 1 table(s): users

**⚠️⚠️ VERY Dangerous - Batch drop:**
    >>> # ALWAYS backup first! Check for CASCADE!
    >>> request = {"tables": ["logs", "sessions", "cache"]}
    >>> result = handle_drop(request, ops)
    [OK] Dropped table: logs
    [OK] Dropped table: sessions
    [OK] Dropped table: cache
    [OK] Dropped 3 table(s): logs, sessions, cache

**Graceful skip for non-existent table:**
    >>> request = {"tables": ["nonexistent"]}
    >>> result = handle_drop(request, ops)
    Table 'nonexistent' does not exist, skipping
    No tables were dropped
    False  # No tables dropped

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm table drops
- quantum_data.py: Quantum paradigm table drops
- data_operations.py: DDL operation router
"""

from zOS import Any, Dict, List

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_DROP_TABLE = "DROP_TABLE"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_TABLES = "tables"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_NO_TABLES = "No tables specified for DROP operation"
_LOG_CHECK_EXISTS = "Checking if table exists: %s"
_LOG_TABLE_NOT_EXISTS = "Table '%s' does not exist, skipping"
_LOG_DROP_TABLE = "Dropping table: %s"
_LOG_DROP_SUCCESS = "[OK] Dropped table: %s"
_LOG_BATCH_DROP = "Batch dropping %d tables"
_LOG_PARTIAL_SUCCESS = "Partial success: dropped %d of %d tables"
_LOG_SUCCESS = "[OK] Dropped %d table(s): %s"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_TABLES = "No table specified for DROP"
_ERR_NO_TABLES_DROPPED = "No tables were dropped"
_ERR_DROP_FAILED = "Failed to drop table: %s"
_ERR_INVALID_TABLE = "Invalid table name: %s"
_ERR_CASCADE_ERROR = "CASCADE delete may affect dependent tables"
_ERR_ADAPTER_ERROR = "Adapter error during DROP: %s"

# ============================================================
# Module Constants - Safety Warnings
# ============================================================

_WARN_IRREVERSIBLE = "⚠️ DROP TABLE is IRREVERSIBLE - data will be lost permanently"
_WARN_DATA_LOSS = "⚠️ ALL table data will be deleted (no recovery without backup)"
_WARN_CASCADE = "⚠️ CASCADE may delete data in dependent tables"
_WARN_BACKUP = "⚠️ ALWAYS backup before DROP operations"
_WARN_TRANSACTION = "⚠️ DDL may not be transactional (adapter-specific)"
_WARN_SCHEMA_INTEGRITY = "⚠️ Dropping tables can break application (missing tables → errors)"

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_drop"]

# ============================================================
# DDL Operation - DROP TABLE (IRREVERSIBLE)
# ============================================================

def handle_drop(request: Dict[str, Any], ops: Any) -> bool:
    """
    Handle DROP TABLE operation to permanently delete database tables.
    
    ⚠️⚠️⚠️ CRITICAL WARNING ⚠️⚠️⚠️
    This operation is IRREVERSIBLE and PERMANENT. It deletes tables and ALL
    their data with NO POSSIBILITY OF RECOVERY without backups. ALWAYS backup
    before using this operation. Test in dev environment first. Double-check
    table names. Consider CASCADE effects on dependent tables.
    
    This handler coordinates table dropping by validating table names, checking
    existence, and delegating actual deletion to the adapter layer. It supports
    batch drops (multiple tables) and gracefully skips non-existent tables.

    Args:
        request (Dict[str, Any]): The DROP TABLE request with the following keys:
            - "tables" (List[str]): List of table names to drop.
              ⚠️ CRITICAL: Double-check table names before calling!
              ⚠️ WARNING: ALL data in these tables will be PERMANENTLY deleted!
        ops (Any): The operations object with the following attributes:
            - adapter: Adapter instance with table_exists() and drop_table() methods
            - logger: Logger instance for operation tracking

    Returns:
        bool: True if at least one table was dropped, False if no tables dropped.
              Returns True for partial success (some tables dropped, others skipped).
              Returns False only if NO tables were dropped (empty list OR all
              tables don't exist).

    Raises:
        No explicit exceptions are raised. Errors are logged and False is returned.
        However, adapter.drop_table() may raise exceptions if DROP fails.

    Examples:
        >>> # ⚠️ Dangerous - Single table drop (ALWAYS backup first!)
        >>> request = {"tables": ["users"]}
        >>> result = handle_drop(request, ops)
        [OK] Dropped table: users
        [OK] Dropped 1 table(s): users
        True
        
        >>> # ⚠️⚠️ VERY Dangerous - Batch drop (ALWAYS backup first!)
        >>> request = {"tables": ["logs", "sessions", "cache"]}
        >>> result = handle_drop(request, ops)
        [OK] Dropped table: logs
        [OK] Dropped table: sessions
        [OK] Dropped table: cache
        [OK] Dropped 3 table(s): logs, sessions, cache
        True
        
        >>> # Graceful skip for non-existent table
        >>> request = {"tables": ["nonexistent"]}
        >>> result = handle_drop(request, ops)
        Table 'nonexistent' does not exist, skipping
        No tables were dropped
        False
        
        >>> # Partial success (some drop, others skip)
        >>> request = {"tables": ["users", "nonexistent", "logs"]}
        >>> result = handle_drop(request, ops)
        [OK] Dropped table: users
        Table 'nonexistent' does not exist, skipping
        [OK] Dropped table: logs
        [OK] Dropped 2 table(s): users, logs
        True  # Partial success (2 of 3 dropped)

    Note:
        - ⚠️ IRREVERSIBLE: Tables and ALL data deleted permanently (no undo)
        - ⚠️ CASCADE: Foreign key constraints may delete data in dependent tables
        - ⚠️ BACKUP CRITICAL: Always backup before DROP (test restore)
        - Batch drop support: Multiple tables in one call (efficient but dangerous)
        - Table existence check: Gracefully skips non-existent tables
        - Partial success: Returns True if ANY tables dropped (even if some skipped)
        - Transaction limitations: DDL may not be transactional (adapter-specific)
        - Schema integrity: Dropping tables can break application (missing tables)
        - Adapter differences: SQLite (file delete), PostgreSQL (network DDL), CSV (directory delete)
        - No hooks: Like DELETE, no onBeforeDrop/onAfterDrop (reduce complexity)
    """
    # ============================================================
    # Phase 1: Validate Tables List (Empty Check)
    # ============================================================
    tables: List[str] = request.get(_KEY_TABLES, [])

    if not tables:
        ops.logger.error(_ERR_NO_TABLES)
        return False

    # ============================================================
    # Phase 2: Drop Each Table (Check Existence, Drop, Track)
    # ============================================================
    # Drop each table, tracking successes
    dropped: List[str] = []
    for table in tables:
        # Check if table exists (graceful skip for non-existent)
        if not ops.adapter.table_exists(table):
            ops.logger.warning(_LOG_TABLE_NOT_EXISTS, table)
            continue

        # ⚠️ IRREVERSIBLE: Drop the table (PERMANENT deletion)
        ops.adapter.drop_table(table)
        dropped.append(table)
        ops.logger.info(_LOG_DROP_SUCCESS, table)

    # ============================================================
    # Phase 3: Check If Any Tables Were Dropped
    # ============================================================
    if not dropped:
        ops.logger.error(_ERR_NO_TABLES_DROPPED)
        return False

    # ============================================================
    # Phase 4: Log Success (Partial or Complete)
    # ============================================================
    ops.logger.info(_LOG_SUCCESS, len(dropped), ", ".join(dropped))
    return True
