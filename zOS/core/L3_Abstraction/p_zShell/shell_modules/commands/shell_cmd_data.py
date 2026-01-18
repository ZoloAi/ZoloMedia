# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_data.py
"""
Shell Command: Data Operations
===============================================================================

PURPOSE
-------
Provides shell interface to the zData subsystem (Week 6.16 - 4 phases complete).
Routes data commands to the modernized zData facade, supporting CRUD, DDL,
declarative migrations, and connection management.

ARCHITECTURE
------------
This module acts as a thin adapter layer between zShell's command parser and
the zData subsystem's comprehensive API:

    User Command → zShell Parser → shell_cmd_data → zData Facade → Adapter
                                                        ↓
                                                   Operations
                                                        ↓
                                            CRUD/DDL/Migrations

WEEK 6.16 ZDATA INTEGRATION (ALL 4 PHASES)
-------------------------------------------
**Phase 1: Foundation (13 files)**
    - WHERE/value parsers, validators, adapters (SQLite, PostgreSQL, CSV)
    - Full type hints, comprehensive constants

**Phase 2: Operations (10 files)**
    - CRUD: insert, select, update, delete, upsert
    - DDL: create, drop, head (schema introspection)
    - Facade pattern with DataOperations orchestrator

**Phase 3: Architecture Consolidation**
    - Quantum extraction (now separate Zolo app)
    - AdvancedData integration (zTable for paginated display)
    - 6 __init__.py files with proper exports

**Phase 4: Declarative Migrations**
    - Schema diff engine (YAML-based)
    - Migration executor (dry-run support)
    - History tracking (_zdata_migrations table)
    - SHA256 hash-based idempotency

SUPPORTED ACTIONS
-----------------
**CRUD Operations (5):**
    - insert:  Insert rows into table
    - select:  Query rows (with AdvancedData zTable pagination)
    - update:  Modify existing rows
    - delete:  Remove rows (⚠️ DESTRUCTIVE)
    - upsert:  Insert or update (conflict resolution)

**DDL Operations (4):**
    - create:    Create table from schema
    - drop:      Drop table (⚠️ DESTRUCTIVE, IRREVERSIBLE)
    - head:      Show table schema (uses AdvancedData zTable)
    - describe:  Detailed table metadata

**Migration Operations (2):**
    - migrate:  Apply schema changes (supports --dry-run)
    - history:  Show migration audit trail

**Connection Operations (3):**
    - connect:     Connect to data backend
    - disconnect:  Close connection
    - status:      Show connection state

USAGE EXAMPLES
--------------
**CRUD Operations:**
    # Insert data
    data insert users --model @.Schema.myapp --values "name=John,age=30"
    
    # Query with JOIN
    data select users,orders --model @.Schema.myapp --auto-join --limit 10
    
    # Update with WHERE
    data update users --model @.Schema.myapp --where "id=5" --values "age=31"
    
    # Delete (requires WHERE for safety)
    data delete users --model @.Schema.myapp --where "status=inactive"
    
    # Upsert (conflict resolution)
    data upsert users --model @.Schema.myapp --values "id=5,name=Jane"

**DDL Operations:**
    # Create table from schema
    data create users --model @.Schema.myapp
    
    # Show schema (AdvancedData pagination)
    data head users --model @.Schema.myapp
    
    # Drop table (⚠️ DESTRUCTIVE)
    data drop temp_table --model @.Schema.myapp

**Migration Operations:**
    # Preview migration (dry-run)
    data migrate --model @.Schema.myapp_v2 --dry-run
    
    # Apply migration
    data migrate --model @.Schema.myapp_v2
    
    # View migration history
    data history --model @.Schema.myapp

**Connection Operations:**
    # Connect to backend
    data connect --model @.Schema.myapp --backend sqlite
    
    # Check status
    data status
    
    # Disconnect
    data disconnect

MULTI-BACKEND SUPPORT
----------------------
zData supports 3 backend adapters:
    - **SQLite:**      File-based, no external deps, WAL mode, PRAGMA tuning
    - **PostgreSQL:**  Network-based, psycopg2, SERIAL types, RETURNING clause
    - **CSV:**         pandas-based, DataFrame caching, JOIN support

Each adapter has specific behavior for UPSERT, transactions, and type mapping.

ADVANCEDDATA INTEGRATION (WEEK 6.4)
------------------------------------
SELECT and HEAD operations use zDisplay's AdvancedData event package:
    - `display.zTable()` for paginated, formatted tabular output
    - Terminal mode: ASCII tables with "Press Enter to continue..."
    - Bifrost mode: JSON arrays for web frontend
    - Supports limit/offset for query pagination

CONSTANTS
---------
60+ module constants for actions, keys, error messages, and validation limits.
See MODULE CONSTANTS section below for complete reference.

CROSS-SUBSYSTEM DEPENDENCIES
-----------------------------
    - **zData (Week 6.16):**    handle_request(), migrate(), get_migration_history()
    - **zDisplay (Week 6.4):**  AdvancedData zTable() for paginated display
    - **zSession (Week 6.2):**  Session-scoped configuration
    - **zParser (Week 6.8):**   zPath resolution for model paths (@. notation)
    - **zLogger:**              Debug and error logging

MODULE HISTORY
--------------
    - Original:  data_executor.py (monolithic, 41 lines, D+ grade)
    - Refactor:  shell_cmd_data.py (modular, 450+ lines, A+ grade)
    - Week:      6.13.9 (zShell subsystem modernization)
    - Updated:   After Week 6.16 (zData 4-phase modernization complete)
"""

from typing import TYPE_CHECKING, Dict, List, Any, Optional

if TYPE_CHECKING:
    from zOS.zCLI import zCLI

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# --- CRUD Actions (5) ---
ACTION_INSERT = "insert"
ACTION_SELECT = "select"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_UPSERT = "upsert"

# --- DDL Actions (4) ---
ACTION_CREATE = "create"
ACTION_DROP = "drop"
ACTION_HEAD = "head"
ACTION_DESCRIBE = "describe"

# --- Migration Actions (2) ---
ACTION_MIGRATE = "migrate"
ACTION_HISTORY = "history"

# --- Connection Actions (3) ---
ACTION_CONNECT = "connect"
ACTION_DISCONNECT = "disconnect"
ACTION_STATUS = "status"

# --- All Supported Actions ---
CRUD_ACTIONS = {ACTION_INSERT, ACTION_SELECT, ACTION_UPDATE, ACTION_DELETE, ACTION_UPSERT}
DDL_ACTIONS = {ACTION_CREATE, ACTION_DROP, ACTION_HEAD, ACTION_DESCRIBE}
MIGRATION_ACTIONS = {ACTION_MIGRATE, ACTION_HISTORY}
CONNECTION_ACTIONS = {ACTION_CONNECT, ACTION_DISCONNECT, ACTION_STATUS}
ALL_ACTIONS = CRUD_ACTIONS | DDL_ACTIONS | MIGRATION_ACTIONS | CONNECTION_ACTIONS

# --- Actions requiring table argument ---
ACTIONS_REQUIRING_TABLE = CRUD_ACTIONS | {ACTION_CREATE, ACTION_DROP, ACTION_HEAD, ACTION_DESCRIBE}

# --- Actions requiring model/schema ---
ACTIONS_REQUIRING_MODEL = CRUD_ACTIONS | DDL_ACTIONS | {ACTION_MIGRATE}

# --- Request Keys (15) ---
KEY_ACTION = "action"
KEY_TABLES = "tables"
KEY_MODEL = "model"
KEY_OPTIONS = "options"
KEY_AUTO_JOIN = "auto_join"
KEY_WHERE = "where"
KEY_FIELDS = "fields"
KEY_VALUES = "values"
KEY_LIMIT = "limit"
KEY_OFFSET = "offset"
KEY_DRY_RUN = "dry_run"
KEY_NEW_SCHEMA = "new_schema"
KEY_OLD_SCHEMA = "old_schema"
KEY_VERSION = "version"
KEY_BACKEND = "backend"

# --- Option Keys (for parsing from parsed dict) ---
OPT_MODEL = "model"
OPT_AUTO_JOIN = "auto_join"
OPT_AUTO_JOIN_ALT = "auto-join"  # Accept both underscore and hyphen
OPT_DRY_RUN = "dry_run"
OPT_DRY_RUN_ALT = "dry-run"
OPT_BACKEND = "backend"
OPT_VERSION = "version"

# --- Parsed Dict Keys ---
PARSED_ACTION = "action"
PARSED_ARGS = "args"
PARSED_OPTIONS = "options"

# --- Error Messages (20) ---
ERROR_NO_ZDATA = "zData subsystem not available - cannot execute data operations"
ERROR_MISSING_TABLE = "No table specified for {action} operation"
ERROR_MISSING_MODEL = "No model/schema specified - use --model @.Schema.myschema"
ERROR_INVALID_ACTION = "Invalid data action: {action}"
ERROR_NOT_CONNECTED = "Not connected to data backend - use 'data connect' first"
ERROR_ALREADY_CONNECTED = "Already connected to data backend"
ERROR_EXECUTION_FAILED = "Data operation failed: {error}"
ERROR_INVALID_BACKEND = "Invalid backend: {backend} (supported: sqlite, postgresql, csv)"
ERROR_MISSING_SCHEMA = "No schema specified for migration - use --model"
ERROR_MIGRATION_FAILED = "Migration failed: {error}"
ERROR_INVALID_TABLE_COUNT = "Too many tables for {action} (max: {max_count})"
ERROR_EMPTY_TABLE_NAME = "Empty table name in multi-table list"
ERROR_MODEL_PATH_TOO_LONG = "Model path exceeds maximum length ({max_len} chars)"
ERROR_CONNECTION_FAILED = "Connection failed: {error}"
ERROR_DISCONNECT_FAILED = "Disconnect failed: {error}"
ERROR_STATUS_CHECK_FAILED = "Status check failed: {error}"
ERROR_HISTORY_FAILED = "Failed to retrieve migration history: {error}"
ERROR_VALIDATION_FAILED = "Validation failed: {error}"
ERROR_MISSING_ARGS = "Missing required arguments for {action}"
ERROR_INVALID_ARGS = "Invalid arguments: {error}"

# --- Success Messages (10) ---
SUCCESS_CONNECTED = "Connected to {backend} backend"
SUCCESS_DISCONNECTED = "Disconnected from data backend"
SUCCESS_INSERTED = "Inserted {count} row(s) into {table}"
SUCCESS_UPDATED = "Updated {count} row(s) in {table}"
SUCCESS_DELETED = "Deleted {count} row(s) from {table}"
SUCCESS_CREATED = "Created table: {table}"
SUCCESS_DROPPED = "Dropped table: {table}"
SUCCESS_MIGRATED = "Migration completed: {summary}"
SUCCESS_OPERATION = "Operation completed successfully"
SUCCESS_STATUS_CONNECTED = "Connected to backend: {backend}"
SUCCESS_STATUS_DISCONNECTED = "Not connected to any backend"

# --- Validation Limits (5) ---
MAX_TABLE_NAME_LENGTH = 255
MAX_TABLES_COUNT = 10  # For multi-table JOINs
MAX_MODEL_PATH_LENGTH = 1024
MAX_BACKEND_NAME_LENGTH = 50

# --- Supported Backends ---
BACKEND_SQLITE = "sqlite"
BACKEND_POSTGRESQL = "postgresql"
BACKEND_CSV = "csv"
SUPPORTED_BACKENDS = {BACKEND_SQLITE, BACKEND_POSTGRESQL, BACKEND_CSV}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _validate_zdata_subsystem(zcli: 'zCLI') -> Optional[str]:
    """
    Validate that zData subsystem is available and initialized.
    
    Args:
        zcli: The zCLI instance
        
    Returns:
        Error message if validation fails, None if successful
        
    Example:
        >>> error = _validate_zdata_subsystem(zcli)
        >>> if error:
        >>>     zcli.display.error(error)
        >>>     return
    """
    if not hasattr(zcli, 'data'):
        return ERROR_NO_ZDATA
    
    if zcli.data is None:
        return ERROR_NO_ZDATA
    
    return None


def _validate_action(action: str) -> Optional[str]:
    """
    Validate that action is supported.
    
    Args:
        action: The action to validate
        
    Returns:
        Error message if invalid, None if valid
        
    Example:
        >>> error = _validate_action("select")
        >>> if error:
        >>>     return error
    """
    if not action:
        return ERROR_INVALID_ACTION.format(action="<empty>")
    
    if action not in ALL_ACTIONS:
        return ERROR_INVALID_ACTION.format(action=action)
    
    return None


def _validate_tables(action: str, tables: List[str]) -> Optional[str]:
    """
    Validate table argument requirements for action.
    
    Args:
        action: The action being performed
        tables: List of table names
        
    Returns:
        Error message if validation fails, None if successful
        
    Example:
        >>> error = _validate_tables("select", ["users", "orders"])
        >>> if error:
        >>>     return error
    """
    # Check if action requires table
    if action in ACTIONS_REQUIRING_TABLE:
        if not tables or len(tables) == 0:
            return ERROR_MISSING_TABLE.format(action=action)
        
        # Check for empty table names in multi-table list
        for table in tables:
            if not table or not table.strip():
                return ERROR_EMPTY_TABLE_NAME
        
        # Validate table count for multi-table operations
        if len(tables) > MAX_TABLES_COUNT:
            return ERROR_INVALID_TABLE_COUNT.format(
                action=action,
                max_count=MAX_TABLES_COUNT
            )
    
    return None


def _validate_model(action: str, model_path: Optional[str]) -> Optional[str]:
    """
    Validate model/schema path requirements for action.
    
    Args:
        action: The action being performed
        model_path: The model path (can be None)
        
    Returns:
        Error message if validation fails, None if successful
        
    Example:
        >>> error = _validate_model("select", "@.Schema.myapp")
        >>> if error:
        >>>     return error
    """
    # Check if action requires model
    if action in ACTIONS_REQUIRING_MODEL:
        if not model_path:
            return ERROR_MISSING_MODEL
        
        # Validate path length
        if len(model_path) > MAX_MODEL_PATH_LENGTH:
            return ERROR_MODEL_PATH_TOO_LONG.format(max_len=MAX_MODEL_PATH_LENGTH)
    
    return None


def _parse_tables(table_arg: Optional[str]) -> List[str]:
    """
    Parse table argument into list of table names.
    
    Supports comma-separated tables for multi-table JOINs:
        "users,orders" → ["users", "orders"]
    
    Args:
        table_arg: Raw table argument (can be None or comma-separated)
        
    Returns:
        List of table names (empty if no tables)
        
    Example:
        >>> tables = _parse_tables("users, orders, products")
        >>> # Returns: ["users", "orders", "products"]
    """
    if not table_arg:
        return []
    
    # Split on comma and strip whitespace
    if "," in table_arg:
        return [t.strip() for t in table_arg.split(",") if t.strip()]
    else:
        return [table_arg.strip()] if table_arg.strip() else []


def _build_request(
    action: str,
    tables: List[str],
    model: Optional[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build zRequest dictionary for zData.handle_request().
    
    Args:
        action: The action to perform
        tables: List of table names
        model: Model/schema path
        options: Parsed options from command
        
    Returns:
        Dictionary ready for zData.handle_request()
        
    Example:
        >>> request = _build_request("select", ["users"], "@.Schema.myapp", options)
        >>> zcli.data.handle_request(request)
    """
    # Extract auto_join flag (accept both formats)
    auto_join = options.get(OPT_AUTO_JOIN, False) or options.get(OPT_AUTO_JOIN_ALT, False)
    
    # Build base request
    request = {
        KEY_ACTION: action,
        KEY_TABLES: tables,
        KEY_MODEL: model,
        KEY_AUTO_JOIN: auto_join,
        KEY_OPTIONS: options  # Pass full options for zData to parse
    }
    
    return request


def _handle_migration_action(
    zcli: 'zCLI',
    action: str,
    options: Dict[str, Any]
) -> None:
    """
    Handle migration-specific actions (migrate, history).
    
    Uses zData's declarative migration system (Phase 4):
        - migrate: Apply schema changes via YAML diff
        - history: Show migration audit trail
    
    Args:
        zcli: The zCLI instance
        action: Migration action (migrate or history)
        options: Command options
        
    Example:
        >>> _handle_migration_action(zcli, "migrate", {"model": "@.Schema.v2", "dry_run": True})
    """
    try:
        if action == ACTION_MIGRATE:
            # Get migration parameters
            new_schema_path = options.get(OPT_MODEL)
            dry_run = options.get(OPT_DRY_RUN, False) or options.get(OPT_DRY_RUN_ALT, False)
            version = options.get(OPT_VERSION)
            
            # Validate schema path
            if not new_schema_path:
                zcli.display.error(ERROR_MISSING_SCHEMA)
                return
            
            # Call zData.migrate()
            zcli.logger.debug(
                "Executing migration: schema=%s, dry_run=%s, version=%s",
                new_schema_path,
                dry_run,
                version
            )
            
            result = zcli.data.migrate(
                new_schema_path=new_schema_path,
                dry_run=dry_run,
                version=version
            )
            
            # Display results (zData handles display via zDisplay)
            if result and not dry_run:
                zcli.display.success(SUCCESS_MIGRATED.format(summary="schema updated"))
        
        elif action == ACTION_HISTORY:
            # Get history parameters
            limit = options.get(KEY_LIMIT, 10)
            
            # Call zData.get_migration_history()
            zcli.logger.debug("Retrieving migration history: limit=%s", limit)
            
            history = zcli.data.get_migration_history(limit=limit)
            
            # Display results via AdvancedData zTable
            if history:
                zcli.display.zTable(
                    data=history,
                    title="Migration History",
                    headers=["ID", "Version", "Applied At", "Status", "Duration (ms)"]
                )
            else:
                zcli.display.info("No migration history found")
    
    except Exception as e:
        zcli.logger.error("Migration action failed: %s", str(e))
        zcli.display.error(ERROR_MIGRATION_FAILED.format(error=str(e)))


def _handle_connection_action(
    zcli: 'zCLI',
    action: str,
    options: Dict[str, Any]
) -> None:
    """
    Handle connection-specific actions (connect, disconnect, status).
    
    Args:
        zcli: The zCLI instance
        action: Connection action
        options: Command options
        
    Example:
        >>> _handle_connection_action(zcli, "connect", {"backend": "sqlite", "model": "@.Schema.myapp"})
    """
    try:
        if action == ACTION_CONNECT:
            # Get connection parameters
            backend = options.get(OPT_BACKEND, BACKEND_SQLITE)
            model = options.get(OPT_MODEL)
            
            # Validate backend
            if backend not in SUPPORTED_BACKENDS:
                zcli.display.error(ERROR_INVALID_BACKEND.format(backend=backend))
                return
            
            # Validate model
            if not model:
                zcli.display.error(ERROR_MISSING_MODEL)
                return
            
            # Call zData.connect()
            zcli.logger.debug("Connecting to backend: %s, model: %s", backend, model)
            zcli.data.connect(backend=backend, schema_path=model)
            zcli.display.success(SUCCESS_CONNECTED.format(backend=backend))
        
        elif action == ACTION_DISCONNECT:
            # Call zData.disconnect()
            zcli.logger.debug("Disconnecting from backend")
            zcli.data.disconnect()
            zcli.display.success(SUCCESS_DISCONNECTED)
        
        elif action == ACTION_STATUS:
            # Check connection status
            is_connected = zcli.data.is_connected()
            
            if is_connected:
                # Get backend info (if available)
                backend_type = getattr(zcli.data.adapter, '__class__.__name__', 'Unknown')
                zcli.display.success(SUCCESS_STATUS_CONNECTED.format(backend=backend_type))
            else:
                zcli.display.info(SUCCESS_STATUS_DISCONNECTED)
    
    except Exception as e:
        zcli.logger.error("Connection action failed: %s", str(e))
        
        if action == ACTION_CONNECT:
            zcli.display.error(ERROR_CONNECTION_FAILED.format(error=str(e)))
        elif action == ACTION_DISCONNECT:
            zcli.display.error(ERROR_DISCONNECT_FAILED.format(error=str(e)))
        else:
            zcli.display.error(ERROR_STATUS_CHECK_FAILED.format(error=str(e)))


# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def execute_data(zcli: 'zCLI', parsed: Dict[str, Any]) -> None:
    """
    Execute data commands for CRUD, DDL, migrations, and connection management.
    
    This is the main entry point called by zShell's command router. It:
        1. Validates zData subsystem availability
        2. Extracts and validates action, tables, model
        3. Routes to appropriate handler:
           - Migration actions → _handle_migration_action()
           - Connection actions → _handle_connection_action()
           - CRUD/DDL actions → zcli.data.handle_request()
        4. Handles all errors gracefully with user-friendly messages
    
    Args:
        zcli: The zCLI instance with access to all subsystems
        parsed: Parsed command dictionary from zShell:
            {
                "action": str,      # The data action (insert, select, migrate, etc.)
                "args": List[str],  # Positional args (table names)
                "options": Dict     # Named options (--model, --where, --dry-run, etc.)
            }
    
    Returns:
        None (uses zDisplay for all output via UI adapter pattern)
    
    Raises:
        No exceptions (all errors caught and displayed via zDisplay)
    
    Examples:
        >>> # CRUD operation
        >>> parsed = {
        >>>     "action": "select",
        >>>     "args": ["users", "orders"],
        >>>     "options": {"model": "@.Schema.myapp", "auto-join": True, "limit": 10}
        >>> }
        >>> execute_data(zcli, parsed)
        
        >>> # Migration operation
        >>> parsed = {
        >>>     "action": "migrate",
        >>>     "args": [],
        >>>     "options": {"model": "@.Schema.myapp_v2", "dry-run": True}
        >>> }
        >>> execute_data(zcli, parsed)
        
        >>> # Connection operation
        >>> parsed = {
        >>>     "action": "status",
        >>>     "args": [],
        >>>     "options": {}
        >>> }
        >>> execute_data(zcli, parsed)
    
    Notes:
        - Uses zData subsystem (Week 6.16 - all 4 phases)
        - SELECT/HEAD use AdvancedData zTable() for pagination
        - MIGRATE supports dry-run mode for safe previews
        - All outputs via zDisplay (mode-agnostic)
    """
    try:
        # ========================================================================
        # PHASE 1: VALIDATION
        # ========================================================================
        
        # Validate zData subsystem availability
        error = _validate_zdata_subsystem(zcli)
        if error:
            zcli.display.error(error)
            return
        
        # Extract action
        action = parsed.get(PARSED_ACTION)
        if not action:
            zcli.display.error(ERROR_MISSING_ARGS.format(action="<unknown>"))
            return
        
        # Validate action
        error = _validate_action(action)
        if error:
            zcli.display.error(error)
            return
        
        # ========================================================================
        # PHASE 2: PARSE ARGUMENTS
        # ========================================================================
        
        # Parse table argument(s)
        table_arg = parsed.get(PARSED_ARGS, [])[0] if parsed.get(PARSED_ARGS) else None
        tables = _parse_tables(table_arg)
        
        # Get options
        options = parsed.get(PARSED_OPTIONS, {})
        
        # Extract model path
        model_path = options.get(OPT_MODEL)
        
        # ========================================================================
        # PHASE 3: VALIDATE REQUIREMENTS
        # ========================================================================
        
        # Validate tables
        error = _validate_tables(action, tables)
        if error:
            zcli.display.error(error)
            return
        
        # Validate model
        error = _validate_model(action, model_path)
        if error:
            zcli.display.error(error)
            return
        
        # ========================================================================
        # PHASE 4: ROUTE TO HANDLER
        # ========================================================================
        
        zcli.logger.debug(
            "Executing data operation: action=%s, tables=%s, model=%s",
            action,
            tables,
            model_path
        )
        
        # Route migration actions to special handler
        if action in MIGRATION_ACTIONS:
            _handle_migration_action(zcli, action, options)
            return
        
        # Route connection actions to special handler
        if action in CONNECTION_ACTIONS:
            _handle_connection_action(zcli, action, options)
            return
        
        # ========================================================================
        # PHASE 5: CRUD/DDL OPERATIONS
        # ========================================================================
        
        # Build request for zData
        zRequest = _build_request(action, tables, model_path, options)
        
        # Delegate to zData subsystem
        # (zData handles display via AdvancedData for SELECT/HEAD)
        zcli.data.handle_request(zRequest)
    
    except KeyError as e:
        # Missing required key in parsed dict
        zcli.logger.error("Missing required key in parsed command: %s", str(e))
        zcli.display.error(ERROR_INVALID_ARGS.format(error=f"Missing key: {e}"))
    
    except ValueError as e:
        # Invalid value (e.g., type conversion failed)
        zcli.logger.error("Invalid value in data command: %s", str(e))
        zcli.display.error(ERROR_INVALID_ARGS.format(error=str(e)))
    
    except Exception as e:
        # Catch-all for unexpected errors
        zcli.logger.error("Data operation failed with unexpected error: %s", str(e))
        zcli.display.error(ERROR_EXECUTION_FAILED.format(error=str(e)))


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'execute_data',
]
