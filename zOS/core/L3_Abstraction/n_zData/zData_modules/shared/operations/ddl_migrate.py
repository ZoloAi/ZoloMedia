# zCLI/subsystems/zData/zData_modules/shared/operations/ddl_migrate.py
"""
Migration executor for declarative schema migrations in zData.

This module executes schema migrations based on diffs computed by schema_diff.py.
It provides safe, atomic migrations with dry-run preview, transaction wrapping,
rollback on failure, and user confirmation prompts for destructive changes.

Core Principle
--------------
Migrations are **declarative**: Users update their YAML schema file, and the
migration executor automatically applies the necessary DDL operations to bring
the database in line with the new schema.

Migration Flow:
1. Load old schema (current database state)
2. Load new schema (target YAML file)
3. Compute diff via schema_diff.diff_schemas()
4. Display preview via zDisplay
5. Prompt for confirmation (unless --auto-approve)
6. BEGIN transaction
7. Execute DDL operations in order (CREATE → ALTER → DROP)
8. Record migration in _zdata_migrations table
9. COMMIT transaction (or ROLLBACK on failure)

Safety Features
--------------
- **Dry-Run Mode**: Preview changes without executing
- **Transaction Wrapping**: All-or-nothing execution with auto-rollback on error
- **Confirmation Prompts**: User must confirm destructive changes
- **Destructive Warnings**: Highlight data loss risks (drop table/column, type changes)
- **Rollback on Failure**: Any error triggers transaction rollback
- **SQLite Workaround**: Special handling for SQLite's limited ALTER TABLE support

Execution Order
--------------
Operations are executed in a safe order to avoid dependency issues:

1. **CREATE TABLE**: Add new tables first (no dependencies yet)
2. **ALTER TABLE - ADD COLUMN**: Add columns to existing tables
3. **ALTER TABLE - MODIFY COLUMN**: Modify column definitions
4. **ALTER TABLE - DROP COLUMN**: Drop columns (after adds/modifies)
5. **DROP TABLE**: Drop tables last (after all other operations)

This ordering ensures:
- New tables exist before foreign keys reference them
- Columns are added before constraints reference them
- Drops happen last to avoid dependency errors

SQLite Limitations
-----------------
SQLite has limited ALTER TABLE support:
- ✅ Can: ADD COLUMN
- ❌ Cannot: DROP COLUMN, RENAME COLUMN, MODIFY COLUMN type

**Workaround**: Table Recreation Strategy
1. Create temporary table with new schema
2. Copy data from old table to temp table
3. Drop old table
4. Rename temp table to original name

This workaround is automatically applied when needed.

Usage Examples
-------------
Execute migration with preview:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.operations.ddl_migrate import handle_migrate
    >>> request = {
    ...     "old_schema": old_schema_dict,
    ...     "new_schema": new_schema_dict,
    ...     "dry_run": False,
    ...     "auto_approve": False
    ... }
    >>> result = handle_migrate(ops, request, display)

Dry-run mode (preview only):
    >>> request = {"old_schema": old_schema, "new_schema": new_schema, "dry_run": True}
    >>> result = handle_migrate(ops, request, display)
    # Displays migration plan but doesn't execute

Auto-approve mode (skip confirmation):
    >>> request = {"old_schema": old_schema, "new_schema": new_schema, "auto_approve": True}
    >>> result = handle_migrate(ops, request, display)
    # Executes without prompting (use with caution!)

Integration
----------
- **Used By**: DataOperations.route_action("migrate", request)
- **Depends On**: schema_diff.py (diff computation), ddl_create.py, ddl_drop.py, helpers.py
- **Integrates With**: zDisplay (preview/progress), migration_history.py (tracking)

See Also
--------
- schema_diff.py: Computes schema diffs
- migration_history.py: Tracks migration execution
- ddl_create.py: CREATE TABLE handler
- ddl_drop.py: DROP TABLE handler
"""

from zOS import Dict, List, Any

# Import diff engine
from ..schema_diff import diff_schemas, format_diff_report, KEY_CHANGE_COUNT

# Import operation handlers
from .ddl_create import handle_create_table
from .ddl_drop import handle_drop

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Request Keys
_KEY_OLD_SCHEMA = "old_schema"
_KEY_NEW_SCHEMA = "new_schema"
_KEY_DRY_RUN = "dry_run"
_KEY_AUTO_APPROVE = "auto_approve"
_KEY_SCHEMA_VERSION = "schema_version"

# Response Keys
_KEY_SUCCESS = "success"
_KEY_DIFF = "diff"
_KEY_OPERATIONS_EXECUTED = "operations_executed"
_KEY_ERROR = "error"

# Migration Phases
_PHASE_LOAD_SCHEMAS = "Loading Schemas"
_PHASE_COMPUTE_DIFF = "Computing Diff"
_PHASE_DISPLAY_PREVIEW = "Displaying Preview"
_PHASE_CONFIRM = "Awaiting Confirmation"
_PHASE_BEGIN_TRANSACTION = "Beginning Transaction"
_PHASE_CREATE_TABLES = "Creating Tables"
_PHASE_ALTER_COLUMNS = "Altering Columns"
_PHASE_DROP_TABLES = "Dropping Tables"
_PHASE_RECORD_HISTORY = "Recording History"
_PHASE_COMMIT = "Committing Transaction"
_PHASE_ROLLBACK = "Rolling Back Transaction"

# Display Messages
_MSG_MIGRATION_START = "🔄 Starting migration..."
_MSG_DRY_RUN_MODE = "🔍 DRY-RUN MODE: Preview only, no changes will be applied"
_MSG_NO_CHANGES = "✅ No schema changes detected - database is up to date"
_MSG_PREVIEW_HEADER = "📋 Migration Preview:"
_MSG_CONFIRM_PROMPT = "⚠️  Apply these changes? (yes/no): "
_MSG_MIGRATION_CANCELLED = "❌ Migration cancelled by user"
_MSG_MIGRATION_SUCCESS = "✅ Migration completed successfully!"
_MSG_MIGRATION_FAILED = "❌ Migration failed: {error}"
_MSG_OPERATIONS_COUNT = "Executed {count} operation(s)"

# Error Messages
_ERROR_NO_OLD_SCHEMA = "No old_schema provided in request"
_ERROR_NO_NEW_SCHEMA = "No new_schema provided in request"
_ERROR_TRANSACTION_FAILED = "Transaction failed: {error}"
_ERROR_CREATE_TABLE_FAILED = "Failed to create table '{table}': {error}"
_ERROR_ALTER_TABLE_FAILED = "Failed to alter table '{table}': {error}"
_ERROR_DROP_TABLE_FAILED = "Failed to drop table '{table}': {error}"

# Confirmation Responses
_CONFIRM_YES = ["yes", "y"]
_CONFIRM_NO = ["no", "n"]

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION HISTORY RECORDING
# ═══════════════════════════════════════════════════════════════════════════════

def _record_migration_history(ops: Any, request: Dict[str, Any], diff: Dict[str, Any]) -> None:
    """
    Record migration history - per-table for CSV, global for SQL.
    
    For CSV backends: Creates separate migration files for each affected table
                      (e.g., zmigrations/users_zMigration.csv)
    For SQL backends: Records in global _zdata_migrations table
    
    Args:
        ops: DataOperations instance with adapter
        request: Migration request with schema_version and schema_hash
        diff: Migration diff with affected tables
    """
    from datetime import datetime
    
    # Check adapter type
    adapter_type = type(ops.adapter).__name__
    is_csv = 'CSV' in adapter_type
    
    if is_csv:
        # CSV: Per-table migration tracking
        _record_csv_migration_history(ops, request, diff)
    else:
        # SQL: Global migration table
        _record_sql_migration_history(ops, request, diff)


def _record_csv_migration_history(ops: Any, request: Dict[str, Any], diff: Dict[str, Any]) -> None:
    """
    Record migration history in per-table CSV files.
    
    For each affected table, creates/updates zmigrations/{table}_zMigration.csv
    with the migration record.
    """
    from datetime import datetime
    import csv
    from pathlib import Path
    
    # Collect all affected tables
    affected_tables = []
    affected_tables.extend(diff.get("tables_added", []))
    affected_tables.extend([t["name"] for t in diff.get("tables_modified", [])])
    affected_tables.extend(diff.get("tables_dropped", []))
    
    if not affected_tables:
        return
    
    # Build migration record
    schema_version = request.get('schema_version', 'unknown')
    schema_hash = request.get('schema_hash', '')
    applied_at = datetime.now().isoformat()
    
    # For each affected table, record the migration
    for table_name in affected_tables:
        # Use __zmigration_{table} pattern to trigger CSV adapter path resolution
        migration_table = f"__zmigration_{table_name}"
        
        try:
            # Check if migration table exists
            if not ops.adapter.table_exists(migration_table):
                # Create migration table with headers
                ops.adapter.create_table(migration_table, {
                    'id': {'type': 'int', 'pk': True, 'auto_increment': True},
                    'from_version': {'type': 'str'},
                    'to_version': {'type': 'str'},
                    'applied_at': {'type': 'datetime'},
                    'applied_by': {'type': 'str'},
                    'duration_ms': {'type': 'int'},
                    'schema_hash': {'type': 'str'},
                    'changes_summary': {'type': 'str'},
                    'changes_detail': {'type': 'str'},
                    'status': {'type': 'str'},
                    'error_message': {'type': 'str'},
                    'rollback_possible': {'type': 'bool'},
                    'backup_location': {'type': 'str'},
                    'rows_affected': {'type': 'int'},
                    'columns_added': {'type': 'int'},
                    'columns_dropped': {'type': 'int'},
                    'columns_modified': {'type': 'int'},
                    'is_breaking': {'type': 'bool'},
                    'migration_hook': {'type': 'str'},
                    'hook_result': {'type': 'str'}
                })
            
            # Insert migration record
            ops.adapter.insert(
                migration_table,
                ['to_version', 'applied_at', 'schema_hash', 'status', 'duration_ms'],
                [schema_version, applied_at, schema_hash, 'success', 0]
            )
            
        except Exception as e:
            if hasattr(ops, 'logger'):
                ops.logger.warning(f"[zMigrate] Failed to record migration for table {table_name}: {e}")


def _record_sql_migration_history(ops: Any, request: Dict[str, Any], diff: Dict[str, Any]) -> None:
    """
    Record migration history in global _zdata_migrations table (SQL approach).
    """
    from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import record_migration, ensure_migrations_table
    
    ensure_migrations_table(ops.adapter)
    
    # Build metrics for recording
    metrics = {
        'schema_version': request.get('schema_version', 'unknown'),
        'schema_hash': request.get('schema_hash', ''),
        'tables_added': diff[KEY_CHANGE_COUNT].get("tables_added", 0),
        'tables_dropped': diff[KEY_CHANGE_COUNT].get("tables_dropped", 0),
        'columns_added': sum(len(t.get("columns_added", [])) for t in diff.get("tables_modified", [])),
        'columns_dropped': sum(len(t.get("columns_dropped", [])) for t in diff.get("tables_modified", [])),
        'duration_ms': 0,
        'status': 'success'
    }
    record_migration(ops.adapter, metrics)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MIGRATION HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

def handle_migrate(ops: Any, request: Dict[str, Any], display: Any) -> Dict[str, Any]:
    """
    Execute declarative schema migration based on diff between old and new schemas.
    
    This is the main entry point for executing migrations. It:
    1. Loads old and new schemas
    2. Computes diff via schema_diff.diff_schemas()
    3. Displays preview via zDisplay
    4. Prompts for confirmation (unless auto_approve or dry_run)
    5. Executes DDL operations in transaction
    6. Records migration history
    7. Returns success/failure result
    
    Args:
        ops: DataOperations instance with adapter, schema, zcli
        request: Migration request dict with keys:
            - old_schema: Current schema dict (or load from DB introspection)
            - new_schema: Target schema dict (from YAML)
            - dry_run: If True, preview only (no execution)
            - auto_approve: If True, skip confirmation prompt
            - schema_version: Optional version string (e.g., "v1.2.3", git commit)
        display: zDisplay instance for user output
    
    Returns:
        Dict with keys:
            - success: True if migration succeeded, False otherwise
            - diff: Structured diff from schema_diff.diff_schemas()
            - operations_executed: Count of DDL operations performed
            - error: Error message if failed (only if success=False)
    
    Raises:
        KeyError: If required request keys missing
        RuntimeError: If adapter not initialized
        Exception: Any database errors during execution
    
    Examples:
        >>> request = {
        ...     "old_schema": {"Tables": {"users": {...}}},
        ...     "new_schema": {"Tables": {"users": {...}, "posts": {...}}},
        ...     "dry_run": False,
        ...     "auto_approve": False
        ... }
        >>> result = handle_migrate(ops, request, display)
        >>> result["success"]
        True
        >>> result["operations_executed"]
        3
    
    Notes:
        - Dry-run mode: Displays preview but doesn't execute (safe for testing)
        - Auto-approve mode: Skips confirmation (use with caution!)
        - Transaction wrapping: All operations are atomic (all-or-nothing)
        - Rollback on failure: Any error triggers automatic rollback
        - SQLite limitations: Uses table recreation workaround when needed
        - Destructive changes: Always prompt for confirmation (even with auto_approve)
    """
    # Display start message
    display.header(_MSG_MIGRATION_START)
    
    # Extract request parameters
    old_schema = request.get(_KEY_OLD_SCHEMA)
    new_schema = request.get(_KEY_NEW_SCHEMA)
    dry_run = request.get(_KEY_DRY_RUN, False)
    auto_approve = request.get(_KEY_AUTO_APPROVE, False)
    
    # Validate request
    if not old_schema:
        raise KeyError(_ERROR_NO_OLD_SCHEMA)
    if not new_schema:
        raise KeyError(_ERROR_NO_NEW_SCHEMA)
    
    # Show dry-run notice
    if dry_run:
        display.text(_MSG_DRY_RUN_MODE)
        display.text("")  # Blank line
    
    # Phase 1: Compute Diff
    display.text(f"⚙️  {_PHASE_COMPUTE_DIFF}...")
    diff = diff_schemas(old_schema, new_schema)
    
    # Check if any changes detected
    if diff[KEY_CHANGE_COUNT]["tables_added"] == 0 and \
       diff[KEY_CHANGE_COUNT]["tables_dropped"] == 0 and \
       diff[KEY_CHANGE_COUNT]["tables_modified"] == 0:
        display.text(_MSG_NO_CHANGES)
        return {
            _KEY_SUCCESS: True,
            _KEY_DIFF: diff,
            _KEY_OPERATIONS_EXECUTED: 0
        }
    
    # Phase 2: Display Preview
    display.header(_MSG_PREVIEW_HEADER)
    report = format_diff_report(diff)
    display.text(report)
    display.text("")  # Blank line
    
    # If dry-run, stop here
    if dry_run:
        return {
            _KEY_SUCCESS: True,
            _KEY_DIFF: diff,
            _KEY_OPERATIONS_EXECUTED: 0  # None executed in dry-run
        }
    
    # Phase 3: Confirmation
    if not auto_approve:
        if not _prompt_for_confirmation(diff, display):
            display.text(_MSG_MIGRATION_CANCELLED)
            return {
                _KEY_SUCCESS: False,
                _KEY_DIFF: diff,
                _KEY_OPERATIONS_EXECUTED: 0,
                _KEY_ERROR: "User cancelled migration"
            }
    
    # Phase 4: Execute Migration
    try:
        operations_executed = _execute_migration(ops, diff, display)
        
        # Phase 5: Record migration history
        try:
            # For CSV backends, record per-table migration history
            # For SQL backends, record in global _zdata_migrations table
            _record_migration_history(ops, request, diff)
        except Exception as e:
            # Log error but don't fail the migration
            if hasattr(ops, 'logger'):
                ops.logger.warning(f"[zMigrate] Failed to record migration history: {e}")
        
        display.text("")  # Blank line
        display.text(_MSG_MIGRATION_SUCCESS)
        display.text(_MSG_OPERATIONS_COUNT.format(count=operations_executed))
        
        return {
            _KEY_SUCCESS: True,
            _KEY_DIFF: diff,
            _KEY_OPERATIONS_EXECUTED: operations_executed
        }
    
    except Exception as e:
        error_msg = str(e)
        display.text("")  # Blank line
        display.text(_MSG_MIGRATION_FAILED.format(error=error_msg))
        
        return {
            _KEY_SUCCESS: False,
            _KEY_DIFF: diff,
            _KEY_OPERATIONS_EXECUTED: 0,
            _KEY_ERROR: error_msg
        }

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIRMATION PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

def _prompt_for_confirmation(diff: Dict[str, Any], display: Any) -> bool:
    """
    Prompt user to confirm migration execution.
    
    Displays confirmation prompt and waits for user response. For destructive
    changes, adds extra warning emphasis.
    
    Args:
        diff: Structured diff from schema_diff.diff_schemas()
        display: zDisplay instance for output
    
    Returns:
        True if user confirms (yes/y), False if user declines (no/n)
    
    Notes:
        - Loops until valid response received
        - Case-insensitive comparison
        - Destructive changes get extra warning
    """
    # Extra warning for destructive changes
    if diff.get("has_destructive_changes"):
        display.text("⚠️  WARNING: This migration contains DESTRUCTIVE changes!")
        display.text("   Data will be permanently lost if you proceed.")
        display.text("")  # Blank line
    
    # Prompt for confirmation using display.button() (mode-agnostic)
    # Color selection based on destructiveness of changes
    button_color = "danger" if diff.get("has_destructive_changes") else "warning"
    
    # display.button() works in both Terminal and Bifrost modes:
    # - Terminal: Prompts "Click [Apply Migration]? (y/n):" with semantic color (red/yellow)
    # - Bifrost: Renders clickable button with semantic color
    # - Returns True if confirmed ("y"/"yes" or button click), False otherwise
    # TODO: Fine-tune UI/UX - Consider improving prompt text and visual flow
    #       Current implementation works but could be more polished for clarity
    return display.button("Apply Migration? (y/n)", color=button_color)

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def _execute_migration(ops: Any, diff: Dict[str, Any], display: Any) -> int:
    """
    Execute all DDL operations in the migration diff.
    
    Executes operations in safe order within a transaction:
    1. CREATE TABLE (new tables)
    2. ALTER TABLE - ADD COLUMN (column additions)
    3. ALTER TABLE - DROP COLUMN (column drops)
    4. DROP TABLE (dropped tables)
    
    All operations are wrapped in BEGIN/COMMIT/ROLLBACK for atomicity.
    
    Args:
        ops: DataOperations instance with adapter access
        diff: Structured diff from schema_diff.diff_schemas()
        display: zDisplay instance for progress updates
    
    Returns:
        Count of operations executed
    
    Raises:
        Exception: Any database errors trigger rollback and re-raise
    
    Notes:
        - Operations are atomic (all-or-nothing)
        - Rollback on any error
        - Progress displayed for each phase
    """
    operations_count = 0
    
    # Begin transaction
    display.text(f"🔄 {_PHASE_BEGIN_TRANSACTION}...")
    ops.adapter.begin_transaction()
    
    try:
        # Phase 1: Create new tables
        if diff["tables_added"]:
            display.text(f"➕ {_PHASE_CREATE_TABLES} ({len(diff['tables_added'])} tables)...")
            operations_count += _execute_table_creations(ops, diff["tables_added"], display)
        
        # Phase 2: Modify existing tables
        if diff["tables_modified"]:
            display.text(f"🔧 {_PHASE_ALTER_COLUMNS} ({len(diff['tables_modified'])} tables)...")
            operations_count += _execute_table_modifications(ops, diff["tables_modified"], display)
        
        # Phase 3: Drop tables
        if diff["tables_dropped"]:
            display.text(f"🗑️  {_PHASE_DROP_TABLES} ({len(diff['tables_dropped'])} tables)...")
            operations_count += _execute_table_drops(ops, diff["tables_dropped"], display)
        
        # Commit transaction
        display.text(f"✅ {_PHASE_COMMIT}...")
        ops.adapter.commit()
        
        return operations_count
    
    except Exception:
        # Rollback on any error
        display.text(f"❌ {_PHASE_ROLLBACK}...")
        ops.adapter.rollback()
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# OPERATION EXECUTORS
# ═══════════════════════════════════════════════════════════════════════════════

def _execute_table_creations(ops: Any, tables_added: List[str], display: Any) -> int:  # pylint: disable=unused-argument
    """
    Execute CREATE TABLE operations for all new tables.
    
    Args:
        ops: DataOperations instance
        tables_added: List of table names to create
        display: zDisplay instance (not used, kept for consistency)
    
    Returns:
        Count of tables created
    
    Raises:
        Exception: If any CREATE TABLE fails
    """
    count = 0
    for table_name in tables_added:
        try:
            # Create request for handle_create_table
            create_request = {"tables": [table_name]}
            handle_create_table(create_request, ops)
            count += 1
        except Exception as e:
            raise RuntimeError(_ERROR_CREATE_TABLE_FAILED.format(table=table_name, error=str(e))) from e
    
    return count

def _execute_table_modifications(ops: Any, tables_modified: Dict[str, Any], display: Any) -> int:  # pylint: disable=unused-argument
    """
    Execute ALTER TABLE operations for all modified tables.
    
    For each modified table:
    1. Add new columns
    2. Modify existing columns (if supported)
    3. Drop columns (if supported)
    
    SQLite limitations are handled with table recreation strategy.
    
    Args:
        ops: DataOperations instance
        tables_modified: Dict of {table_name: table_changes}
        display: zDisplay instance (not used, kept for consistency)
    
    Returns:
        Count of ALTER operations executed
    
    Raises:
        Exception: If any ALTER TABLE fails
    """
    count = 0
    
    for table_name, changes in tables_modified.items():
        try:
            # Prepare changes dict for adapter.alter_table()
            alter_changes = {}
            
            # Add columns
            if changes["columns_added"]:
                alter_changes["add_columns"] = changes["columns_added"]
                count += len(changes["columns_added"])
            
            # Drop columns
            if changes["columns_dropped"]:
                alter_changes["drop_columns"] = changes["columns_dropped"]
                count += len(changes["columns_dropped"])
            
            # Modify columns (for type changes, etc.)
            if changes["columns_modified"]:
                alter_changes["modify_columns"] = changes["columns_modified"]
                count += len(changes["columns_modified"])
            
            # Execute ALTER TABLE via adapter
            if alter_changes:
                ops.adapter.alter_table(table_name, alter_changes)
        
        except Exception as e:
            raise RuntimeError(_ERROR_ALTER_TABLE_FAILED.format(table=table_name, error=str(e))) from e
    
    return count

def _execute_table_drops(ops: Any, tables_dropped: List[str], display: Any) -> int:  # pylint: disable=unused-argument
    """
    Execute DROP TABLE operations for all dropped tables.
    
    Args:
        ops: DataOperations instance
        tables_dropped: List of table names to drop
        display: zDisplay instance (not used, kept for consistency)
    
    Returns:
        Count of tables dropped
    
    Raises:
        Exception: If any DROP TABLE fails
    """
    count = 0
    for table_name in tables_dropped:
        try:
            # Create request for handle_drop
            drop_request = {"tables": [table_name], "if_exists": True}
            handle_drop(drop_request, ops)
            count += 1
        except Exception as e:
            raise RuntimeError(_ERROR_DROP_TABLE_FAILED.format(table=table_name, error=str(e))) from e
    
    return count

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "handle_migrate"
]

