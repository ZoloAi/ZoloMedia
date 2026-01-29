# zCLI/subsystems/zData/zData_modules/shared/data_operations.py
"""
Data Operations Facade for zData Subsystem.

This module provides the DataOperations facade class that acts as the central
orchestrator for all zData operations (CRUD + DDL). It implements the Facade
design pattern by delegating to individual operation handler modules while
providing a unified interface for the classical and quantum data paradigms.

═══════════════════════════════════════════════════════════════════════════════
FACADE ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

The DataOperations class serves as a facade that:
1. Routes actions to appropriate operation handlers (9 operations)
2. Executes zFunc hooks (onBeforeInsert, onAfterInsert, etc.)
3. Delegates CRUD operations to the adapter (6 pass-through methods)
4. Manages table lifecycle (ensure_tables, create, drop)
5. Handles errors gracefully with logging and recovery

This separation of concerns enables:
- Modular operation handlers (one file per operation)
- Centralized routing and error handling
- Hook integration for custom business logic
- Consistent interface across paradigms (classical/quantum)

═══════════════════════════════════════════════════════════════════════════════
SUPPORTED OPERATIONS (9 Total)
═══════════════════════════════════════════════════════════════════════════════

CRUD Operations (5):
1. insert    - Insert new rows into a table
2. read      - Read/query rows from a table (with JOINs)
3. update    - Update existing rows in a table
4. delete    - Delete rows from a table
5. upsert    - Insert or update rows (conflict resolution)

DDL Operations (4):
6. create    - Create new table(s) from schema
7. drop      - Drop existing table(s)
8. head      - Show table schema/columns
9. list_tables - List all tables in the database

═══════════════════════════════════════════════════════════════════════════════
ACTION ROUTER
═══════════════════════════════════════════════════════════════════════════════

The route_action() method maps string actions to handler functions:

action_map = {
    "list_tables": lambda: self.list_tables(),
    "insert": lambda: handle_insert(request, self),
    "read": lambda: handle_read(request, self),
    "update": lambda: handle_update(request, self),
    "delete": lambda: handle_delete(request, self),
    "upsert": lambda: handle_upsert(request, self),
    "create": lambda: handle_create_table(request, self),
    "drop": lambda: handle_drop(request, self),
    "head": lambda: handle_head(request, self),
}

Routing includes:
- Unknown action detection
- Exception handling with logging
- Return value normalization (bool/"error")

═══════════════════════════════════════════════════════════════════════════════
HOOK EXECUTION (zFunc Integration)
═══════════════════════════════════════════════════════════════════════════════

The execute_hook() method integrates with zFunc for custom hooks:

Hook Types:
- onBeforeInsert / onAfterInsert
- onBeforeUpdate / onAfterUpdate
- (DELETE and UPSERT do not support hooks by design)

Hook Execution Flow:
1. Check if hook expression is provided
2. Check if zFunc is available (fallback: skip hook)
3. Execute hook via zcli.zfunc.handle(hook_expr, context)
4. Handle errors gracefully (log and return None)

═══════════════════════════════════════════════════════════════════════════════
ADAPTER DELEGATION
═══════════════════════════════════════════════════════════════════════════════

The facade provides 6 pass-through methods that directly delegate to the adapter:

1. insert(table, fields, values)
2. select(table, fields, **kwargs) - with auto-join support
3. update(table, fields, values, where)
4. delete(table, where)
5. upsert(table, fields, values, conflict_fields)
6. list_tables()

These methods:
- Validate adapter initialization (raise RuntimeError if missing)
- Pass arguments directly to adapter
- Return adapter results unchanged

═══════════════════════════════════════════════════════════════════════════════
ENSURE TABLES LOGIC
═══════════════════════════════════════════════════════════════════════════════

ensure_tables_for_action() filters actions that require table existence:

Actions that SKIP ensure_tables:
- list_tables: Lists all tables (no specific table required)
- insert: Creates table on-the-fly if missing (handled by adapter)
- drop: Drops table (doesn't need it to exist)
- head: Shows schema from YAML (not from database)

Actions that REQUIRE ensure_tables:
- read, update, delete, upsert, create: Need table to exist

ensure_tables() creates missing tables:
1. Filters out reserved keys ("zMeta", "db_path")
2. Checks if table exists (adapter.table_exists)
3. Creates missing tables (adapter.create_table)
4. Logs success/failure for each table

═══════════════════════════════════════════════════════════════════════════════
SCHEMA INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

Schema Filtering:
- Excludes "zMeta" key (schema metadata, not a table)
- Excludes "db_path" key (legacy, should be in zMeta)
- Used by select() for auto-join detection
- Used by ensure_tables() for table creation

Auto-Join Support:
The select() method passes schema to adapter for automatic JOIN detection:
- Forward FKs: user_id → users.id
- Reverse FKs: users.id ← posts.user_id

═══════════════════════════════════════════════════════════════════════════════
ERROR HANDLING
═══════════════════════════════════════════════════════════════════════════════

Error handling strategies:

1. Route Action:
   - Try/except around handler execution
   - Logs error with traceback
   - Returns "error" string (for backward compatibility)

2. Execute Hook:
   - Try/except around hook execution
   - Logs error with traceback
   - Returns None (allows operation to continue)

3. Adapter Methods:
   - Raises RuntimeError if adapter not initialized
   - Delegates error handling to adapter

═══════════════════════════════════════════════════════════════════════════════
USAGE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Example 1: Route an action
    ops = DataOperations(handler)
    result = ops.route_action("insert", request)

Example 2: Execute a hook
    context = {"table": "users", "data": {...}}
    ops.execute_hook("&MyPlugin.validate_user", context)

Example 3: Direct adapter delegation
    row_id = ops.insert("users", ["name", "email"], ["Alice", "alice@example.com"])

Example 4: Ensure tables exist
    ops.ensure_tables(["users", "posts"])  # Create if missing

"""

from zOS import Any, Dict, List, Optional
from .operations import (
    handle_insert,
    handle_read,
    handle_update,
    handle_delete,
    handle_upsert,
    handle_aggregate,
    handle_create_table,
    handle_drop,
    handle_head,
)
from .operations.ddl_migrate import handle_migrate

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────────────────────────────
# Action Names (9 supported operations)
# ────────────────────────────────────────────────────────────────────────────
ACTION_LIST_TABLES = "list_tables"
ACTION_INSERT = "insert"
ACTION_READ = "read"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_UPSERT = "upsert"
ACTION_AGGREGATE = "aggregate"
ACTION_CREATE = "create"
ACTION_DROP = "drop"
ACTION_HEAD = "head"
ACTION_MIGRATE = "migrate"

# ────────────────────────────────────────────────────────────────────────────
# Reserved Schema Keys (Excluded from table operations)
# ────────────────────────────────────────────────────────────────────────────
RESERVED_META = "zMeta"
RESERVED_DB_PATH = "db_path"

# ────────────────────────────────────────────────────────────────────────────
# Return Values
# ────────────────────────────────────────────────────────────────────────────
RETURN_ERROR = "error"
RETURN_SUCCESS = True

# ────────────────────────────────────────────────────────────────────────────
# Error Messages
# ────────────────────────────────────────────────────────────────────────────
ERR_NO_ADAPTER = "No adapter initialized"
ERR_UNKNOWN_ACTION = "Unknown action: %s"
ERR_ACTION_FAILED = "Error executing %s: %s"
ERR_HOOK_FAILED = "Hook execution failed: %s"
ERR_ZFUNC_NOT_AVAILABLE = "zFunc not available, skipping hook: %s"
ERR_TABLE_NOT_IN_SCHEMA = "Table '%s' not found in schema"
ERR_CREATE_TABLE_FAILED = "Failed to create table '%s': %s"
ERR_RUNTIME_NO_ADAPTER = "No adapter initialized"

# ────────────────────────────────────────────────────────────────────────────
# Log Messages
# ────────────────────────────────────────────────────────────────────────────
LOG_HOOK_EXECUTE = "Executing hook: %s"
LOG_TABLE_CREATE = "Table '%s' does not exist, creating..."
LOG_TABLE_EXISTS = "Table '%s' already exists"
LOG_TABLE_NOT_IN_SCHEMA = "Table '%s' not found in schema"
LOG_CREATED_TABLE_SUCCESS = "[OK] Created table: %s"

# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────
__all__ = ["DataOperations"]

class DataOperations:
    """
    Data Operations Facade - Central orchestrator for all zData operations.
    
    This class implements the Facade design pattern to provide a unified interface
    for all zData operations (CRUD + DDL). It delegates to individual operation
    handler modules while managing routing, hooks, adapter delegation, and error
    handling.
    
    Architecture:
        The facade separates concerns into three layers:
        
        1. Routing Layer (route_action):
           - Maps action strings to handler functions
           - Validates actions and handles errors
           - Returns normalized results (bool/"error")
        
        2. Hook Layer (execute_hook):
           - Integrates with zFunc for custom hooks
           - Executes onBeforeInsert, onAfterInsert, etc.
           - Handles errors gracefully (allows operation to continue)
        
        3. Delegation Layer (insert, select, update, delete, upsert, list_tables):
           - Pass-through methods to adapter
           - Validates adapter initialization
           - Returns adapter results unchanged
    
    Responsibilities:
        - Route 9 operations to their handlers (insert, read, update, delete, upsert, create, drop, head, list_tables)
        - Execute zFunc hooks for custom business logic
        - Delegate CRUD operations to adapter
        - Manage table lifecycle (ensure_tables, create, drop)
        - Handle errors with logging and recovery
        - Filter schema (exclude Meta, db_path)
        - Support auto-join for SELECT operations
    
    Integration Points:
        - Operation Handlers: Imports from .operations (handle_insert, handle_read, etc.)
        - zFunc: Executes hooks via zcli.zfunc.handle()
        - Adapter: Delegates CRUD operations via self.adapter
        - Validator: Available for operation handlers via self.validator
        - Schema: Filters and passes to adapter for auto-join
        - Logger: Logs routing, hooks, and errors
        - Display: Available via @property display() for operation handlers
    
    Usage:
        # Initialize (typically done by classical_data.py or quantum_data.py)
        ops = DataOperations(handler)
        
        # Route an action
        result = ops.route_action("insert", request)
        
        # Execute a hook
        ops.execute_hook("&MyPlugin.validate_user", context)
        
        # Direct adapter delegation
        ops.insert("users", ["name"], ["Alice"])
        
        # Ensure tables exist
        ops.ensure_tables(["users", "posts"])
    
    Attributes:
        handler: Reference to parent handler (classical_data or quantum_data)
        adapter: Database adapter instance (SQLite, PostgreSQL, CSV)
        validator: Data validator instance
        schema: Schema dictionary (tables + Meta)
        logger: Logger instance
        zcli: zCLI core instance
    
    Notes:
        - This class is instantiated by classical_data.py and quantum_data.py
        - All operation handlers receive `ops` (self) as a parameter
        - Operation handlers return None and use ops.display for output
        - Hook execution errors are logged but don't block operations
        - Adapter delegation methods raise RuntimeError if adapter is None
    """

    def __init__(self, handler: Any) -> None:
        """
        Initialize DataOperations facade with handler reference.
        
        This method stores references to the parent handler and its dependencies
        (adapter, validator, schema, logger, zcli) for use by operation handlers
        and delegation methods.
        
        Args:
            handler: Parent handler instance (ClassicalData or QuantumData) with attributes:
                     - adapter: Database adapter (SQLite, PostgreSQL, CSV)
                     - validator: Data validator instance
                     - schema: Schema dictionary (tables + Meta)
                     - logger: Logger instance
                     - zcli: zCLI core instance
        
        Returns:
            None
        
        Examples:
            # Typically called by classical_data.py or quantum_data.py
            ops = DataOperations(self)  # self is ClassicalData or QuantumData
        
        Notes:
            - All attributes are references to handler's attributes
            - No deep copying is performed (shares handler's state)
            - Display is accessed via @property display() (added separately)
        """
        self.handler = handler
        self.adapter = handler.adapter
        self.validator = handler.validator
        self.schema = handler.schema
        self.logger = handler.logger
        self.zcli = handler.zcli

    @property
    def display(self) -> Any:
        """
        Get display instance for mode-agnostic output.
        
        This property provides access to zDisplay for operation handlers that need
        to output data (handle_insert, handle_read, handle_update, handle_delete,
        handle_upsert, handle_create_table, handle_drop, handle_head).
        
        Returns:
            Any: zDisplay instance from zcli.display
        
        Examples:
            # Used by operation handlers
            ops.display.header("Operation Results")
            ops.display.list(rows, style="table")
        
        Notes:
            - This property is required by all operation handlers
            - Returns self.zcli.display (zDisplay facade)
            - Mode-agnostic (works in Terminal, Walker, Bifrost modes)
        """
        return self.zcli.display

    # ═══════════════════════════════════════════════════════════════════════════
    # Hook Execution (zFunc Integration)
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_hook(
        self,
        hook_expr: Optional[str],
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a zFunc hook if available (onBeforeInsert, onAfterInsert, etc.).
        
        This method integrates with zCLI's zFunc subsystem to execute custom hooks
        for data operations. Hooks enable custom business logic before/after INSERT
        and UPDATE operations.
        
        Hook Execution Flow:
            1. Check if hook_expr is provided (empty string or None = skip)
            2. Check if zFunc is available (zcli.zfunc exists)
            3. Execute hook via zcli.zfunc.handle(hook_expr, context)
            4. Return result or None on error (operation continues)
        
        Error Handling:
            - If hook_expr is empty: Returns None (no hook to execute)
            - If zFunc not available: Logs warning, returns None (graceful degradation)
            - If hook raises exception: Logs error with traceback, returns None (allows operation to continue)
        
        Args:
            hook_expr: Hook expression string (e.g., "&MyPlugin.validate_user")
                       - Empty string or None = skip hook execution
                       - Must start with & (plugin reference)
            context: Context dictionary passed to hook with operation data
                     - Typically includes: table, data, fields, values, etc.
                     - Hook can read/modify context (modifications may affect operation)
        
        Returns:
            Any: Hook result (typically None or modified context)
            None: If hook skipped, zFunc unavailable, or error occurred
        
        Raises:
            None: All exceptions are caught and logged (graceful error handling)
        
        Examples:
            # Execute a validation hook
            context = {"table": "users", "data": {"email": "alice@example.com"}}
            result = ops.execute_hook("&Validators.check_email", context)
            
            # Hook not provided (skip execution)
            result = ops.execute_hook(None, context)  # Returns None
            
            # Hook with error (logs but continues)
            result = ops.execute_hook("&BadPlugin.broken", context)  # Returns None, logs error
        
        Notes:
            - Used by handle_insert (onBeforeInsert, onAfterInsert)
            - Used by handle_update (onBeforeUpdate, onAfterUpdate)
            - DELETE and UPSERT do not support hooks by design
            - Hook errors do not block operations (graceful degradation)
            - Broad exception catch (Exception) is intentional for resilience
        """
        # ─────────────────────────────────────────────────────────────────────────
        # Phase 1: Check if hook expression provided
        # ─────────────────────────────────────────────────────────────────────────
        if not hook_expr:
            return None

        # ─────────────────────────────────────────────────────────────────────────
        # Phase 2: Check if zFunc available
        # ─────────────────────────────────────────────────────────────────────────
        if not self.zcli.zfunc:
            self.logger.warning(ERR_ZFUNC_NOT_AVAILABLE, hook_expr)
            return None

        # ─────────────────────────────────────────────────────────────────────────
        # Phase 3: Execute hook via zFunc (with error handling)
        # ─────────────────────────────────────────────────────────────────────────
        try:
            self.logger.debug(LOG_HOOK_EXECUTE, hook_expr)
            result = self.zcli.zfunc.handle(hook_expr, context)
            return result
        except Exception as e:  # pylint: disable=broad-except
            # Broad except is intentional: hook errors should not block operations
            self.logger.error(ERR_HOOK_FAILED, e, exc_info=True)
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # Action Router
    # ═══════════════════════════════════════════════════════════════════════════

    def route_action(
        self,
        action: str,
        request: Dict[str, Any]
    ) -> Any:
        """
        Route action string to appropriate operation handler module.
        
        This method implements the routing layer of the facade pattern by mapping
        action strings (e.g., "insert", "read") to their corresponding handler
        functions. It handles unknown actions and exceptions gracefully.
        
        Action Map (11 operations):
            - "list_tables": self.list_tables() (adapter delegation)
            - "insert": handle_insert(request, self) (CRUD operation)
            - "read": handle_read(request, self) (CRUD operation)
            - "update": handle_update(request, self) (CRUD operation)
            - "delete": handle_delete(request, self) (CRUD operation)
            - "upsert": handle_upsert(request, self) (CRUD operation)
            - "aggregate": handle_aggregate(request, self) (Aggregation operation)
            - "create": handle_create_table(request, self) (DDL operation)
            - "drop": handle_drop(request, self) (DDL operation)
            - "head": handle_head(request, self) (DDL operation)
            - "migrate": handle_migrate(self, request, display) (DDL operation)
        
        Error Handling:
            - Unknown action: Logs error, returns "error" string
            - Handler exception: Logs error with traceback, returns "error" string
            - Broad exception catch is intentional for resilience
        
        Args:
            action: Action string identifying the operation to execute
                    Must be one of: list_tables, insert, read, update, delete, upsert, create, drop, head, migrate
            request: Request dictionary containing operation parameters
                     - Format depends on action (table, fields, values, where, etc.)
                     - Passed to operation handler for processing
        
        Returns:
            Any: Result from operation handler (typically bool for success/failure)
            str: "error" if action unknown or handler raises exception
        
        Examples:
            # Route an INSERT operation
            request = {"table": "users", "options": {"name": "Alice"}}
            result = ops.route_action("insert", request)
            
            # Route a READ operation
            request = {"table": "users", "where": "id > 5"}
            result = ops.route_action("read", request)
            
            # Unknown action (logs error, returns "error")
            result = ops.route_action("invalid", request)  # Returns "error"
        
        Notes:
            - Operation handlers return None and use ops.display for output
            - Return value "error" is for backward compatibility (should be bool)
            - Broad exception catch (Exception) is intentional for resilience
            - All errors are logged with traceback for debugging
        """
        # ─────────────────────────────────────────────────────────────────────────
        # Phase 1: Build Action Map (11 operations)
        # ─────────────────────────────────────────────────────────────────────────
        action_map = {
            ACTION_LIST_TABLES: lambda: self.list_tables(),
            ACTION_INSERT: lambda: handle_insert(request, self),
            ACTION_READ: lambda: handle_read(request, self),
            ACTION_UPDATE: lambda: handle_update(request, self),
            ACTION_DELETE: lambda: handle_delete(request, self),
            ACTION_UPSERT: lambda: handle_upsert(request, self),
            ACTION_AGGREGATE: lambda: handle_aggregate(request, self),
            ACTION_CREATE: lambda: handle_create_table(request, self),
            ACTION_DROP: lambda: handle_drop(request, self),
            ACTION_HEAD: lambda: handle_head(request, self),
            ACTION_MIGRATE: lambda: handle_migrate(self, request, self.zcli.display),
        }

        # ─────────────────────────────────────────────────────────────────────────
        # Phase 2: Route Action to Handler (with error handling)
        # ─────────────────────────────────────────────────────────────────────────
        try:
            handler_func = action_map.get(action)
            if handler_func:
                return handler_func()

            # Unknown action (not in action_map)
            self.logger.error(ERR_UNKNOWN_ACTION, action)
            return RETURN_ERROR
        except Exception as e:  # pylint: disable=broad-except
            # Broad except is intentional: handler errors should not crash the system
            self.logger.error(ERR_ACTION_FAILED, action, e, exc_info=True)
            return RETURN_ERROR

    def ensure_tables_for_action(
        self,
        action: str,
        tables: Optional[List[str]]
    ) -> bool:
        """
        Ensure tables exist for actions that require it (action filtering).
        
        This method filters actions that require table existence checks before
        execution. Actions like list_tables, insert, drop, and head do not require
        ensure_tables, while read, update, delete, upsert, and create do.
        
        Action Filtering Logic:
            Actions that SKIP ensure_tables:
            - list_tables: Lists all tables (no specific table required)
            - insert: Creates table on-the-fly if missing (handled by adapter)
            - drop: Drops table (doesn't need it to exist)
            - head: Shows schema from YAML (not from database)
            
            Actions that REQUIRE ensure_tables:
            - create: Explicitly creates tables from schema
            - read: Requires table to exist for querying
            - update: Requires table to exist for updating
            - delete: Requires table to exist for deleting
            - upsert: Requires table to exist for upserting
        
        Args:
            action: Action string identifying the operation
                    One of: list_tables, insert, read, update, delete, upsert, create, drop, head
            tables: List of table names to ensure exist
                    - None = ensure all tables from schema
                    - Empty list = ensure all tables from schema
                    - Specific list = ensure only those tables
        
        Returns:
            bool: True if tables ensured successfully or action skips ensure_tables
                  False if table creation failed
        
        Examples:
            # Action that requires ensure_tables (create, read, update, delete, upsert)
            result = ops.ensure_tables_for_action("read", ["users"])  # Calls ensure_tables
            
            # Action that skips ensure_tables (list_tables, insert, drop, head)
            result = ops.ensure_tables_for_action("list_tables", None)  # Returns True (skip)
        
        Notes:
            - This method is called by classical_data.py before route_action
            - Filtering reduces unnecessary table creation checks
            - insert action handles table creation internally (adapter responsibility)
        """
        # ─────────────────────────────────────────────────────────────────────────
        # Phase 1: Check if action requires ensure_tables
        # ─────────────────────────────────────────────────────────────────────────
        
        # CREATE action explicitly ensures tables
        if action == ACTION_CREATE:
            return self.ensure_tables(tables if tables else None)
        
        # Actions that SKIP ensure_tables (do not need tables to exist)
        if action not in [ACTION_LIST_TABLES, ACTION_INSERT, ACTION_DROP, ACTION_HEAD]:
            # All other actions (read, update, delete, upsert) REQUIRE ensure_tables
            return self.ensure_tables(tables if tables else None)

        # Action skips ensure_tables (list_tables, insert, drop, head)
        return RETURN_SUCCESS

    # ═══════════════════════════════════════════════════════════════════════════
    # DDL Operations (Shared)
    # ═══════════════════════════════════════════════════════════════════════════

    def ensure_tables(
        self,
        tables: Optional[List[str]] = None
    ) -> bool:
        """
        Ensure tables exist in database, create missing tables from schema.
        
        This method checks if specified tables (or all tables from schema) exist
        in the database and creates missing tables using adapter.create_table().
        It filters out reserved schema keys ("zMeta", "db_path") and logs all
        operations.
        
        Table Selection:
            - tables=None or empty list: Ensure ALL tables from schema (excluding Meta, db_path)
            - tables=[specific list]: Ensure only those tables
        
        Schema Filtering:
            Excluded keys (not tables):
            - "zMeta": Schema metadata (schema name, version, etc.)
            - "db_path": Legacy key (should be in zMeta)
        
        Error Handling:
            - Adapter not initialized: Logs error, returns False
            - Table not in schema: Logs warning, continues, sets all_ok=False
            - Table creation fails: Logs error, continues, sets all_ok=False
            - Partial success possible (some tables created, some failed)
        
        Args:
            tables: List of table names to ensure exist
                    - None = ensure all tables from schema (default)
                    - Empty list = ensure all tables from schema
                    - Specific list = ensure only those tables
        
        Returns:
            bool: True if all tables ensured successfully
                  False if adapter missing, table not in schema, or creation failed
        
        Examples:
            # Ensure all tables from schema
            success = ops.ensure_tables()  # Creates all missing tables
            
            # Ensure specific tables only
            success = ops.ensure_tables(["users", "posts"])  # Creates if missing
            
            # Adapter not initialized (returns False)
            ops.adapter = None
            success = ops.ensure_tables()  # Returns False, logs error
        
        Notes:
            - Called by ensure_tables_for_action() for action filtering
            - Logs info/warning/error for each table operation
            - Partial success possible (returns False but some tables created)
            - Does NOT drop or alter existing tables (idempotent)
        """
        # ─────────────────────────────────────────────────────────────────────────
        # Phase 1: Validate adapter initialized
        # ─────────────────────────────────────────────────────────────────────────
        if not self.adapter:
            self.logger.error(ERR_NO_ADAPTER)
            return False

        # ─────────────────────────────────────────────────────────────────────────
        # Phase 2: Determine tables to check (filter reserved keys)
        # ─────────────────────────────────────────────────────────────────────────
        if tables is None:
            # Ensure all tables from schema (excluding reserved keys)
            tables_to_check = [
                k for k in self.schema.keys()
                if k not in (RESERVED_META, RESERVED_DB_PATH)
            ]
        else:
            tables_to_check = tables

        # ─────────────────────────────────────────────────────────────────────────
        # Phase 3: Check each table and create if missing
        # ─────────────────────────────────────────────────────────────────────────
        all_ok = True
        for table_name in tables_to_check:
            # Check if table in schema
            if table_name not in self.schema:
                self.logger.warning(LOG_TABLE_NOT_IN_SCHEMA, table_name)
                all_ok = False
                continue

            # Check if table exists in database
            if not self.adapter.table_exists(table_name):
                self.logger.info(LOG_TABLE_CREATE, table_name)
                try:
                    # Create table from schema
                    self.adapter.create_table(table_name, self.schema[table_name])
                    self.logger.info(LOG_CREATED_TABLE_SUCCESS, table_name)
                except Exception as e:  # pylint: disable=broad-except
                    # Log error but continue (partial success possible)
                    self.logger.error(ERR_CREATE_TABLE_FAILED, table_name, e)
                    all_ok = False
            else:
                self.logger.debug(LOG_TABLE_EXISTS, table_name)

        return all_ok

    # ═══════════════════════════════════════════════════════════════════════════
    # CRUD Operations (Shared Adapter Delegates)
    # ═══════════════════════════════════════════════════════════════════════════

    def insert(
        self,
        table: str,
        fields: List[str],
        values: List[Any]
    ) -> Any:
        """
        Insert a row into table (adapter delegation).
        
        Pass-through method that delegates INSERT operations to the adapter.
        Returns the inserted row ID or raises RuntimeError if adapter not initialized.
        
        Args:
            table: Table name to insert into
            fields: List of field names
            values: List of values (must match fields order)
        
        Returns:
            Any: Inserted row ID (adapter-specific type)
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            row_id = ops.insert("users", ["name", "email"], ["Alice", "alice@example.com"])
        """
        if not self.adapter:
            raise RuntimeError(ERR_RUNTIME_NO_ADAPTER)
        return self.adapter.insert(table, fields, values)

    def select(
        self,
        table: str,
        fields: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[Any]:
        """
        Select rows from table with optional JOINs (adapter delegation).
        
        Pass-through method that delegates SELECT operations to the adapter with
        auto-join support. Filters schema to exclude "zMeta" key before passing
        to adapter for automatic JOIN detection.
        
        Schema Filtering:
            - Excludes "zMeta" key (schema metadata)
            - Passes remaining tables to adapter for auto-join detection
        
        Args:
            table: Table name to select from
            fields: List of field names (None = all fields)
            **kwargs: Additional query parameters:
                      - where: WHERE clause dictionary
                      - joins: JOIN specifications
                      - order: ORDER BY clause
                      - limit: Result limit
                      - auto_join: Enable automatic JOIN detection (default: False)
        
        Returns:
            List[Any]: List of rows (adapter-specific format)
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Select all rows
            rows = ops.select("users")
            
            # Select with WHERE and auto-join
            rows = ops.select("users", where={"id": 5}, auto_join=True)
        """
        if not self.adapter:
            raise RuntimeError(ERR_RUNTIME_NO_ADAPTER)

        # Filter schema: exclude "zMeta" key for auto-join detection
        schema_tables = {k: v for k, v in self.schema.items() if k != RESERVED_META}
        return self.adapter.select(
            table,
            fields=fields,
            where=kwargs.get("where"),
            joins=kwargs.get("joins"),
            order=kwargs.get("order"),
            limit=kwargs.get("limit"),
            auto_join=kwargs.get("auto_join", False),
            schema=schema_tables
        )

    def update(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        where: Optional[Dict[str, Any]]
    ) -> int:
        """
        Update rows in table (adapter delegation).
        
        Pass-through method that delegates UPDATE operations to the adapter.
        Returns the number of rows updated or raises RuntimeError if adapter not initialized.
        
        Args:
            table: Table name to update
            fields: List of field names to update
            values: List of new values (must match fields order)
            where: WHERE clause dictionary (None = update all rows - dangerous!)
        
        Returns:
            int: Number of rows updated
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            count = ops.update("users", ["status"], ["active"], {"id": 5})
        """
        if not self.adapter:
            raise RuntimeError(ERR_RUNTIME_NO_ADAPTER)
        return self.adapter.update(table, fields, values, where)

    def delete(
        self,
        table: str,
        where: Optional[Dict[str, Any]]
    ) -> int:
        """
        Delete rows from table (adapter delegation).
        
        Pass-through method that delegates DELETE operations to the adapter.
        Returns the number of rows deleted or raises RuntimeError if adapter not initialized.
        
        Args:
            table: Table name to delete from
            where: WHERE clause dictionary (None = delete all rows - dangerous!)
        
        Returns:
            int: Number of rows deleted
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            count = ops.delete("users", {"status": "inactive"})
        """
        if not self.adapter:
            raise RuntimeError(ERR_RUNTIME_NO_ADAPTER)
        return self.adapter.delete(table, where)

    def upsert(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        conflict_fields: List[str]
    ) -> Any:
        """
        Upsert (insert or update) a row in table (adapter delegation).
        
        Pass-through method that delegates UPSERT operations to the adapter.
        Returns the row ID or raises RuntimeError if adapter not initialized.
        
        Args:
            table: Table name to upsert into
            fields: List of field names
            values: List of values (must match fields order)
            conflict_fields: List of fields to check for conflicts (typically primary key)
        
        Returns:
            Any: Inserted/updated row ID (adapter-specific type)
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            row_id = ops.upsert("users", ["id", "name"], [1, "Alice"], ["id"])
        """
        if not self.adapter:
            raise RuntimeError(ERR_RUNTIME_NO_ADAPTER)
        return self.adapter.upsert(table, fields, values, conflict_fields)

    def list_tables(self) -> List[str]:
        """
        List all tables in database (adapter delegation).
        
        Pass-through method that delegates list_tables operations to the adapter.
        Returns a list of table names or raises RuntimeError if adapter not initialized.
        
        Returns:
            List[str]: List of table names
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            tables = ops.list_tables()  # Returns ["users", "posts", "products"]
        """
        if not self.adapter:
            raise RuntimeError(ERR_RUNTIME_NO_ADAPTER)
        return self.adapter.list_tables()
