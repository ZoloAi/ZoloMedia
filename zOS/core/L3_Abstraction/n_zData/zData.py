# zCLI/subsystems/zData/zData.py

"""
Unified Data Management System for zCLI.

This module provides the main entry point for all data operations in zCLI, supporting
relational databases (SQLite, PostgreSQL) and file-based data (CSV) through a unified
interface. It handles schema loading, adapter initialization, connection management, and
operation delegation to specialized handlers.

Architecture Overview:
    The zData subsystem uses a 2-tier architecture for simplicity and efficiency:
    
    1. zData Facade (this file):
       - Schema loading and validation
       - Adapter initialization via AdapterFactory
       - Connection lifecycle management (wizard mode vs one-shot mode)
       - Operation routing via DataOperations facade
       - zCLI subsystem integration (zLoader, zOpen, zDisplay, zFunc)
    
    2. Backend Adapters (SQLite, PostgreSQL, CSV):
       - Database-specific implementations
       - CRUD operation execution
       - DDL/DCL/TCL support (database-dependent)
       - Connection handling and query building

Supported Operations:
    CRUD (Create, Read, Update, Delete):
        - insert: Add new records
        - select: Query records with WHERE, JOIN, ORDER BY, LIMIT
        - update: Modify existing records
        - delete: Remove records
        - upsert: Insert or update (conflict resolution)
        - list_tables: List all tables in database
    
    DDL (Data Definition Language):
        - create_table: Create tables from schema
        - drop_table: Remove tables
        - alter_table: Modify table structure
        - table_exists: Check table existence
    
    DCL (Data Control Language - PostgreSQL/MySQL only):
        - grant: Grant privileges to users
        - revoke: Revoke privileges from users
        - list_privileges: List privileges for tables/users
    
    TCL (Transaction Control Language):
        - begin_transaction: Start transaction
        - commit: Commit transaction
        - rollback: Rollback transaction
    
    File Operations (zOpen integration):
        - open_schema: Open schema YAML in editor
        - open_csv: Open CSV data file in editor

Supported Backends:
    - SQLite: Embedded database, file-based, no external dependencies
    - PostgreSQL: Network database, requires psycopg2, project info YAML
    - CSV: File-based, requires pandas, DataFrame caching, multi-table JOINs

Integration Points:
    zSession:
        - wizard_mode: Connection reuse for multi-step workflows
        - schema_cache: Persistent connections across wizard steps
        - zAuth: Authentication context for secure data access
    
    zLoader:
        - Schema loading from zPath (@.zSchema.users, ~.zMachine.schemas/app.yaml)
        - pinned_cache: Cached schemas for faster initialization
    
    zParser:
        - Path resolution (zPath to absolute paths)
        - Data_Path resolution in schema Meta section
    
    zDisplay:
        - Mode-agnostic output (Terminal, Walker, Bifrost)
        - zDeclare for operation announcements
        - Table display via display.zTable() (AdvancedData for SQL/CSV results)
    
    zFunc:
        - Hook execution (onBeforeInsert, onAfterInsert, etc.)
        - Custom business logic for data operations
    
    zOpen:
        - File opening (schema YAML, CSV data files)
        - Editor integration

Connection Modes:
    Wizard Mode (wizard_mode=True):
        - Connection reuse: Same adapter instance across multiple operations
        - Schema cache: Stores connection per alias ($users, $products)
        - Lifecycle: Manual disconnect or wizard completion
        - Use case: Multi-step workflows, batch operations
    
    One-Shot Mode (wizard_mode=False):
        - New connection per operation
        - Auto-disconnect after operation completes
        - No persistent state
        - Use case: Single commands, terminal operations

Schema Structure:
    Meta Section (required):
        Data_Type: Backend type (sqlite, postgresql, csv)
        Data_Path: Path to database/CSV directory (~.zMachine.data/app.db)
        Data_Label: Human-readable label for logging
        Schema_Name: Optional schema name for error messages
        zVaFiles: Path to schema YAML file (for open_schema)
    
    Table Sections (one per table):
        field_name:
            type: Data type (TEXT, INTEGER, FLOAT, BOOLEAN, DATE)
            primary_key: Boolean (optional)
            required: Boolean (optional)
            unique: Boolean (optional)
            foreign_key: Foreign key spec (optional)
            default: Default value (optional)
            validators: List of validation rules (optional)

Usage Examples:
    # Example 1: One-shot mode (terminal command)
    zdata = zData(zcli)
    request = {
        "model": "@.zSchema.users",
        "action": "read",
        "options": {"where": "age > 25"}
    }
    result = zdata.handle_request(request)
    
    # Example 2: Wizard mode with connection reuse
    context = {
        "wizard_mode": True,
        "schema_cache": SchemaCache()
    }
    request1 = {
        "model": "@.zSchema.users",
        "action": "insert",
        "options": {"_alias_name": "users", "_schema_cached": schema}
    }
    zdata.handle_request(request1, context)
    # Connection stays open for next request...
    
    # Example 3: Direct adapter access (programmatic)
    zdata.load_schema(schema)
    rows = zdata.select("users", fields=["name", "email"], where={"active": True})
    zdata.insert("users", ["name", "email"], ["Alice", "alice@example.com"])
    zdata.disconnect()

Module Constants:
    This module defines 50+ constants to eliminate magic strings and improve
    maintainability across:
    - Schema keys (Meta, Data_Type, Data_Path, etc.)
    - Request keys (action, model, options, tables)
    - Option keys (_schema_cached, _alias_name, tables)
    - Context keys (wizard_mode, schema_cache)
    - Reserved keys (Meta, db_path)
    - Return values (error, success)
    - Error messages (10+ descriptive errors)
    - Log messages (8+ operation logs)

Type Hints:
    All methods in this module have 100% type hint coverage for improved
    code quality, IDE support, and runtime type checking.

See Also:
    - zCLI/subsystems/zData/zData_modules/shared/backends/: Adapter implementations
    - zCLI/subsystems/zData/zData_modules/shared/data_operations.py: Operation facade
    - zCLI/subsystems/zData/zData_modules/shared/validator.py: Data validation
    - zCLI/subsystems/zData/zData_modules/shared/parsers/: WHERE/value parsers
"""

from zOS import Any, Dict, List, Optional, os
from zSys.errors import SchemaNotFoundError, TableNotFoundError
from .zData_modules.shared.backends.adapter_factory import AdapterFactory
from .zData_modules.shared.validator import DataValidator
from .zData_modules.shared.data_operations import DataOperations


# ═══════════════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════════════

# Schema keys (Meta section)
_META_KEY = "zMeta"
_META_KEY_DATA_TYPE = "Data_Type"
_META_KEY_DATA_PATH = "Data_Path"
_META_KEY_DATA_SOURCE = "Data_Source"  # NEW v1.5.12: Environment variable reference (security best practice)
_META_KEY_DATA_LABEL = "Data_Label"
_META_KEY_SCHEMA_NAME = "Schema_Name"
_META_KEY_ZVAFILES = "zVaFiles"
_META_KEY_DATA_PARADIGM = "Data_Paradigm"
_META_DEFAULT_LABEL = "data"

# Migration keys (Meta section) - NEW v1.5.13: Opt-in declarative migrations
_META_KEY_ZMIGRATION = "zMigration"  # Enable migrations (opt-in for safety)
_META_KEY_ZMIGRATION_VERSION = "zMigrationVersion"  # Schema version tracking

# Environment variable naming convention (Flask-aligned)
_ENV_VAR_PREFIX = "ZDATA_"
_ENV_VAR_SUFFIX = "_URL"

# Request keys (handle_request parameters)
_REQUEST_KEY_ACTION = "action"
_REQUEST_KEY_MODEL = "model"
_REQUEST_KEY_OPTIONS = "options"
_REQUEST_KEY_TABLES = "tables"

# Option keys (request options)
_OPTION_KEY_SCHEMA_CACHED = "_schema_cached"
_OPTION_KEY_ALIAS_NAME = "_alias_name"
_OPTION_KEY_TABLES = "tables"
_OPTION_VALUE_ALL_TABLES = "all"

# Context keys (handle_request context parameter)
_CONTEXT_KEY_WIZARD_MODE = "wizard_mode"
_CONTEXT_KEY_SCHEMA_CACHE = "schema_cache"

# Reserved schema keys (excluded from table lists)
_RESERVED_KEY_META = "zMeta"
_RESERVED_KEY_DB_PATH = "db_path"

# Return values
_RESULT_ERROR = "error"
_RESULT_SUCCESS = "success"

# zDisplay color codes
_COLOR_ZDATA = "ZDATA"
_COLOR_ZCRUD = "ZCRUD"
_DISPLAY_STYLE_FULL = "full"

# zDeclare messages
_DECLARE_ZDATA_READY = "zData Ready"
_DECLARE_ZDATA_REQUEST = "zData Request"

# Error messages
_ERROR_NO_ZCLI_INSTANCE = "zData requires a zCLI instance"
_ERROR_NO_SESSION_ATTR = "Invalid zCLI instance: missing 'session' attribute"
_ERROR_NO_ADAPTER = "No adapter initialized"
_ERROR_NO_SCHEMA = "Cannot initialize adapter without schema"
_ERROR_FAILED_CONNECT = "Failed to connect to backend"
_ERROR_FAILED_INITIALIZE = "Failed to initialize adapter: {error}"
_ERROR_NO_HANDLER = "No handler initialized"
_ERROR_HANDLER_NO_ADAPTER = "Handler does not have an adapter"
_ERROR_NO_SCHEMA_PROVIDED = "No schema provided (model path or cached schema required)"
_ERROR_SCHEMA_LOAD_FAILED = "Failed to load schema from: {path}"
_ERROR_NO_CACHED_SCHEMA = "No cached schema for first-time connection: ${alias}"
_ERROR_NO_ZOPEN = "zOpen not available"
_ERROR_NO_SCHEMA_PATH = "No schema path available"
_ERROR_NO_TABLES = "No tables available"
_ERROR_CSV_NOT_SUPPORTED = "CSV operations not supported for this adapter"
_ERROR_MISSING_META_FIELD = "Schema Meta missing required field: '{field}'"
_ERROR_DCL_NOT_SUPPORTED = "{adapter} does not support {operation} operations. DCL is only supported by PostgreSQL and MySQL adapters."
_ERROR_NO_DATA_CONNECTION = "No database connection info found. Use Data_Source (env var) or Data_Path in schema Meta."

# Security warnings (v1.5.12)
_SECURITY_WARNING_DATA_PATH_IN_SCHEMA = "[SECURITY] Data_Path found in schema file. Move credentials to .zEnv using Data_Source pattern!"
_SECURITY_INFO_LOADED_FROM_ENV = "[SECURITY] Loaded Data_Path from environment: {env_var}"
_SECURITY_INFO_AUTO_CONVENTION = "[SECURITY] Auto-loaded connection from .zEnv using convention: {env_var}"

# Log messages
_LOG_ZDATA_READY = "zData Ready"
_LOG_LOADING_SCHEMA = "Loading schema from: %s"
_LOG_INITIALIZING_ADAPTER = "Initializing %s adapter for: %s (label: %s)"
_LOG_CONNECTED_BACKEND = "[OK] Connected to %s backend: %s"
_LOG_DISCONNECTED = "Disconnected from backend"
_LOG_DISCONNECTED_ONE_SHOT = "Disconnected (one-shot mode)"
_LOG_CONNECTION_KEPT_ALIVE = "Connection kept alive (wizard mode)"
_LOG_USING_CACHED_SCHEMA = "Using cached schema from alias: $%s"
_LOG_REUSING_CONNECTION = "[REUSE] Reusing connection for $%s"
_LOG_LOADING_FROM_PINNED = "[LOAD] Loading schema from pinned_cache: $%s"
_LOG_CREATED_PERSISTENT = "[CONNECT] Created persistent connection for $%s"
_LOG_ERROR_EXECUTING_REQUEST = "Error executing request: %s"

# Log hints
_HINT_USE_LOAD_COMMAND = "Hint: Use 'load @data.%s' or provide model path directly"

# Debug log messages (for DDL/DCL/TCL operations)
_DEBUG_CREATING_TABLE = "Creating table: %s"
_DEBUG_DROPPING_TABLE = "Dropping table: %s"
_DEBUG_ALTERING_TABLE = "Altering table: %s"
_DEBUG_GRANTING = "Granting %s on %s to %s"
_DEBUG_REVOKING = "Revoking %s on %s from %s"
_DEBUG_LISTING_PRIVILEGES = "Listing privileges (table=%s, user=%s)"
_DEBUG_BEGIN_TRANSACTION = "Beginning transaction"
_DEBUG_COMMIT_TRANSACTION = "Committing transaction"
_DEBUG_ROLLBACK_TRANSACTION = "Rolling back transaction"

# File operation log messages
_LOG_OPENING_SCHEMA = "Opening schema file: %s"
_LOG_OPENING_CSV = "Opening CSV file: %s"

# Misc constants
_SCHEMA_PATH_SEPARATOR = "."
_SCHEMA_NAME_FALLBACK = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════════════

__all__ = ["zData"]


# ═══════════════════════════════════════════════════════════════════════════════════════
# MAIN ZDATA CLASS
# ═══════════════════════════════════════════════════════════════════════════════════════

class zData:
    """
    Unified Data Management System for zCLI.
    
    This class provides a unified interface for all data operations in zCLI, supporting
    multiple backends (SQLite, PostgreSQL, CSV) through a common API. It handles schema
    loading, adapter initialization, connection management, and operation delegation.
    
    Architecture:
        The zData class acts as a facade that orchestrates:
        - Schema loading (via zLoader)
        - Adapter initialization (via AdapterFactory)
        - Data validation (via DataValidator)
        - Operation routing (via DataOperations)
        - Connection lifecycle (wizard mode vs one-shot mode)
    
    Lifecycle:
        1. Initialization: Create zData instance with zCLI reference
        2. Schema Loading: Load schema from zPath or use cached schema
        3. Adapter Init: Create backend adapter (SQLite/PostgreSQL/CSV)
        4. Connection: Establish database connection
        5. Operations: Execute CRUD/DDL/DCL/TCL operations
        6. Disconnection: Close connection (auto in one-shot, manual in wizard)
    
    Connection Modes:
        Wizard Mode:
            - wizard_mode=True in context
            - Connection reused across multiple operations
            - Schema cache stores connection per alias
            - Manual disconnect or wizard completion
        
        One-Shot Mode:
            - wizard_mode=False (default)
            - New connection per operation
            - Auto-disconnect after operation
    
    Attributes:
        zcli: zCLI core instance (provides access to all subsystems)
        logger: Logger instance for operation logging
        display: zDisplay instance for mode-agnostic output
        loader: zLoader instance for schema loading
        open: zOpen instance for file operations
        schema: Loaded schema dictionary (Meta + table definitions)
        adapter: Backend adapter instance (SQLite/PostgreSQL/CSV)
        validator: DataValidator instance for validation
        operations: DataOperations facade for operation routing
        mycolor: zDisplay color code for zData messages
        _connected: Connection state flag
    
    Usage:
        # One-shot mode
        zdata = zData(zcli)
        request = {"model": "@.zSchema.users", "action": "read"}
        result = zdata.handle_request(request)
        
        # Wizard mode
        context = {"wizard_mode": True, "schema_cache": cache}
        zdata.handle_request(request, context)
    
    Notes:
        - All CRUD/DDL/DCL/TCL methods require schema to be loaded first
        - Connection state is managed automatically based on mode
        - All methods return adapter results or "error" string
        - Type hints are enforced for all public methods
    """

    def __init__(self, zcli: Any) -> None:
        """
        Initialize zData instance with zCLI reference.
        
        This method validates the zCLI instance and stores references to required
        subsystems (logger, display, loader, open). It initializes the zData state
        (schema, adapter, validator, operations) to None, which will be populated
        when a schema is loaded via handle_request() or load_schema().
        
        Args:
            zcli: zCLI core instance with required attributes:
                  - session: Active session dictionary
                  - logger: Logger instance
                  - display: zDisplay instance
                  - loader: zLoader instance
                  - open: zOpen instance
                  - zparser: zParser instance (for path resolution)
        
        Returns:
            None
        
        Raises:
            ValueError: If zcli is None or missing 'session' attribute
        
        Examples:
            # Standard initialization
            zcli = zCLI()
            zdata = zData(zcli)
            
            # Initialization with validation
            if hasattr(zcli, 'session'):
                zdata = zData(zcli)
        
        Notes:
            - This method does NOT load a schema or initialize an adapter
            - Schema loading happens in handle_request() or load_schema()
            - zDeclare announces "zData Ready" to display
        """
        # PHASE 1: Validate zCLI instance
        if zcli is None:
            raise ValueError(_ERROR_NO_ZCLI_INSTANCE)

        if not hasattr(zcli, 'session'):
            raise ValueError(_ERROR_NO_SESSION_ATTR)

        # PHASE 2: Store zCLI instance and subsystem references
        self.zcli = zcli
        self.logger = zcli.logger
        self.display = zcli.display
        self.loader = zcli.loader
        self.open = zcli.open

        # PHASE 3: Initialize data state (populated on schema load)
        self.schema: Optional[Dict[str, Any]] = None
        self.adapter: Optional[Any] = None
        self.validator: Optional[DataValidator] = None
        self.operations: Optional[DataOperations] = None
        self._connected: bool = False

        # PHASE 4: Display configuration
        self.mycolor = _COLOR_ZDATA

        # PHASE 5: Announce readiness
        self.display.zDeclare(_DECLARE_ZDATA_READY, color=self.mycolor, indent=0, style=_DISPLAY_STYLE_FULL)

    # ═══════════════════════════════════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ═══════════════════════════════════════════════════════════════════════════════════

    def handle_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Main entry point for all data operations.
        
        This method handles the complete lifecycle of a data operation:
        1. Announces request to display
        2. Initializes schema and adapter (if not already loaded)
        3. Validates connection
        4. Delegates to operation handlers (via DataOperations)
        5. Manages connection lifecycle (wizard mode vs one-shot mode)
        
        The method supports two connection modes:
        - Wizard Mode: Connection stays open across multiple operations
        - One-Shot Mode: Connection auto-closes after operation completes
        
        Args:
            request: Request dictionary with keys:
                     - model: Schema path (e.g., "@.zSchema.users")
                     - action: Operation name ("insert", "read", "update", etc.)
                     - options: Operation options (where, fields, values, etc.)
                     - tables: Target tables (optional, for bulk operations)
            context: Optional context dictionary with keys:
                     - wizard_mode: Boolean (default: False)
                     - schema_cache: SchemaCache instance (for wizard mode)
        
        Returns:
            Operation result from adapter or "error" string on failure:
            - insert/update/delete/upsert: Number of affected rows or True
            - select: List of row dictionaries
            - create_table/drop_table: True/False
            - list_tables: List of table names
            - Error: "error" string
        
        Raises:
            Exception: Propagates exceptions from adapter initialization or operation execution
        
        Examples:
            # Example 1: Simple read operation (one-shot mode)
            request = {
                "model": "@.zSchema.users",
                "action": "read",
                "options": {"where": "age > 25"}
            }
            result = zdata.handle_request(request)
            
            # Example 2: Wizard mode with connection reuse
            context = {"wizard_mode": True, "schema_cache": cache}
            request1 = {"model": "@.zSchema.users", "action": "insert", ...}
            zdata.handle_request(request1, context)
            request2 = {"action": "read", ...}  # Reuses connection
            zdata.handle_request(request2, context)
            
            # Example 3: Cached schema (no model path needed)
            request = {
                "action": "update",
                "options": {
                    "_schema_cached": schema,
                    "_alias_name": "users"
                }
            }
            result = zdata.handle_request(request)
        
        Notes:
            - Wizard mode requires schema_cache in context
            - Connection reuse in wizard mode improves performance
            - One-shot mode auto-disconnects (no cleanup needed)
            - All exceptions are logged with full traceback
        """
        # PHASE 1: Announce request (skip if silent mode for background data fetching)
        silent = request.get("silent", False)
        if not silent:
            self.display.zDeclare(_DECLARE_ZDATA_REQUEST, color=_COLOR_ZCRUD, indent=1, style=_DISPLAY_STYLE_FULL)

        # PHASE 2: Extract wizard mode flag
        wizard_mode = context.get(_CONTEXT_KEY_WIZARD_MODE, False) if context else False

        # PHASE 3: Initialize schema and adapter
        if not self._initialize_handler(request, context):
            return _RESULT_ERROR

        # PHASE 4: Validate connection
        if not self.is_connected():
            self.logger.error(_ERROR_FAILED_CONNECT)
            return _RESULT_ERROR

        # PHASE 5: Preprocess request (parse tables option)
        self._preprocess_request(request)

        # PHASE 6: Ensure tables exist (for operations that require tables)
        action = request.get(_REQUEST_KEY_ACTION)
        tables = request.get(_REQUEST_KEY_TABLES, [])
        if not self.operations.ensure_tables_for_action(action, tables):
            return _RESULT_ERROR

        # PHASE 7: Delegate to operation handlers
        try:
            result = self.operations.route_action(action, request)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error(_LOG_ERROR_EXECUTING_REQUEST, e, exc_info=True)
            result = _RESULT_ERROR
        finally:
            # PHASE 8: Manage connection lifecycle
            if not wizard_mode:
                self.disconnect()
                self.logger.debug(_LOG_DISCONNECTED_ONE_SHOT)
            else:
                self.logger.debug(_LOG_CONNECTION_KEPT_ALIVE)

        return result

    # ═══════════════════════════════════════════════════════════════════════════════════
    # SCHEMA LOADING & ADAPTER INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════════════════

    def _initialize_handler(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """
        Initialize schema and adapter with connection reuse support.
        
        This method handles three initialization scenarios:
        1. Wizard mode with connection reuse (check cache first)
        2. One-shot mode with cached schema (from pinned_cache)
        3. Default mode with model path (load schema via zLoader)
        
        Args:
            request: Request dictionary with model/options
            context: Context dictionary with wizard_mode/schema_cache
        
        Returns:
            True if initialization succeeded, False otherwise
        
        Notes:
            - Wizard mode checks schema_cache for existing connection
            - Cached schema bypasses zLoader (faster initialization)
            - Model path triggers full schema load and adapter init
        """
        # PHASE 1: Extract context parameters
        schema_cache = context.get(_CONTEXT_KEY_SCHEMA_CACHE) if context else None
        wizard_mode = context.get(_CONTEXT_KEY_WIZARD_MODE, False) if context else False

        # PHASE 2: Extract request options
        options = request.get(_REQUEST_KEY_OPTIONS, {})
        cached_schema = options.get(_OPTION_KEY_SCHEMA_CACHED)
        alias_name = options.get(_OPTION_KEY_ALIAS_NAME)

        # PHASE 3: Wizard mode with connection reuse
        if wizard_mode and schema_cache and alias_name:
            return self._init_wizard_handler(schema_cache, alias_name, cached_schema)

        # PHASE 4: One-shot mode with cached schema (from pinned_cache)
        if cached_schema and alias_name:
            self.logger.info(_LOG_USING_CACHED_SCHEMA, alias_name)
            self.load_schema(cached_schema)
            return True

        # PHASE 5: Load schema from model path (default)
        return self._init_from_model(request.get(_REQUEST_KEY_MODEL))

    def _init_wizard_handler(self, schema_cache: Any, alias_name: str, cached_schema: Optional[Dict[str, Any]]) -> bool:
        """
        Initialize handler for wizard mode with connection reuse.
        
        This method implements the wizard mode connection reuse logic:
        1. Check if connection already exists in schema_cache
        2. If exists, reuse adapter/validator/operations from cache
        3. If not, load schema and store new connection in cache
        
        Args:
            schema_cache: SchemaCache instance (stores connections per alias)
            alias_name: Alias name for connection ($users, $products)
            cached_schema: Optional cached schema dictionary
        
        Returns:
            True if initialization succeeded, False otherwise
        
        Notes:
            - Connection reuse avoids repeated adapter initialization
            - Schema cache is managed by wizard context
            - First use in wizard requires cached_schema
        """
        # PHASE 1: Check if connection already exists (reuse)
        existing_handler = schema_cache.get_connection(alias_name)
        if existing_handler:
            # Reuse existing adapter/validator/operations
            self.adapter = existing_handler.adapter
            self.validator = existing_handler.validator
            self.operations = existing_handler.operations
            self.schema = existing_handler.schema
            self._connected = existing_handler._connected  # pylint: disable=protected-access
            self.logger.info(_LOG_REUSING_CONNECTION, alias_name)
            return True

        # PHASE 2: First use in wizard - create and store connection
        if not cached_schema:
            self.logger.error(_ERROR_NO_CACHED_SCHEMA.format(alias=alias_name))
            self.logger.error(_HINT_USE_LOAD_COMMAND, alias_name)
            return False

        # PHASE 3: Load schema and store new connection
        self.logger.info(_LOG_LOADING_FROM_PINNED, alias_name)
        self.load_schema(cached_schema)
        schema_cache.set_connection(alias_name, self)
        self.logger.info(_LOG_CREATED_PERSISTENT, alias_name)
        return True

    def _init_from_model(self, model_path: Optional[str]) -> bool:
        """
        Initialize handler by loading schema from model path.
        
        This method loads a schema from a zPath (e.g., @.zSchema.users) using
        zLoader, then initializes the adapter/validator/operations.
        
        Args:
            model_path: zPath to schema file (e.g., "@.zSchema.users")
        
        Returns:
            True if schema loaded and adapter initialized, False otherwise
        
        Raises:
            SchemaNotFoundError: If schema file not found or load failed
        
        Notes:
            - Model path is resolved via zLoader (handles zPath)
            - Schema name extracted from path for error messages
            - Adapter initialization happens in load_schema()
        """
        # PHASE 1: Validate model path
        if not model_path:
            self.logger.error(ERROR_NO_SCHEMA_PROVIDED)
            return False

        # PHASE 2: Load schema via zLoader
        self.logger.info(_LOG_LOADING_SCHEMA, model_path)
        schema = self.loader.handle(model_path)

        # PHASE 3: Validate schema load
        if schema == _RESULT_ERROR or not schema:
            self.logger.error(_ERROR_SCHEMA_LOAD_FAILED.format(path=model_path))
            # Extract schema name from zPath (e.g., '@.zSchema.users' -> 'users')
            schema_name = model_path.split(_SCHEMA_PATH_SEPARATOR)[-1] if model_path else _SCHEMA_NAME_FALLBACK
            raise SchemaNotFoundError(
                schema_name=schema_name,
                context_type="python",
                zpath=model_path
            )

        # PHASE 4: Load schema and initialize adapter
        self.load_schema(schema)
        return bool(self.adapter)

    def load_schema(self, schema: Dict[str, Any]) -> None:
        """
        Load schema and initialize adapter/validator/operations.
        
        This method performs the complete schema loading and adapter initialization:
        1. Store schema dictionary
        2. Initialize backend adapter (SQLite/PostgreSQL/CSV)
        3. Establish database connection
        4. Initialize validator with schema tables
        5. Initialize operations facade
        
        After this method completes, the zData instance is ready to execute operations.
        
        Args:
            schema: Schema dictionary with Meta section and table definitions
        
        Returns:
            None
        
        Raises:
            ValueError: If Meta section missing required fields
            Exception: If adapter initialization or connection fails
        
        Examples:
            # Load schema and execute operations
            schema = {
                "zMeta": {
                    "Data_Type": "sqlite",
                    "Data_Path": "~.zMachine.data/users.db",
                    "Data_Label": "users"
                },
                "users": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "name": {"type": "TEXT", "required": True}
                }
            }
            zdata.load_schema(schema)
            zdata.insert("users", ["name"], ["Alice"])
            zdata.disconnect()
        
        Notes:
            - This method MUST be called before any CRUD/DDL/DCL/TCL operations
            - Adapter initialization includes connection establishment
            - Validator excludes Meta section from validation
            - Operations facade receives reference to self (for adapter/validator access)
        """
        # PHASE 1: Store schema
        self.schema = schema

        # PHASE 2: Initialize adapter (establishes connection)
        self._initialize_adapter()

        # PHASE 3: Initialize validator with schema tables (exclude Meta)
        schema_tables = {k: v for k, v in schema.items() if k != _RESERVED_KEY_META}
        self.validator = DataValidator(schema_tables, logger=self.logger, zcli=self.zcli)

        # PHASE 4: Initialize operations facade (uses self.adapter/validator/schema)
        self.operations = DataOperations(self)

    def _initialize_adapter(self) -> None:
        """
        Initialize backend adapter based on schema Meta section.
        
        This method extracts configuration from the Meta section, resolves paths
        via zParser, creates the appropriate adapter via AdapterFactory, and
        establishes the database connection.
        
        The adapter type (SQLite/PostgreSQL/CSV) is determined by Meta.Data_Type.
        Path resolution handles zPath notation (~.zMachine.*, @.workspace paths).
        
        Returns:
            None
        
        Raises:
            ValueError: If schema is None or Meta missing required fields
            Exception: If adapter creation or connection fails
        
        Notes:
            - This method is called by load_schema()
            - Connection is established automatically (adapter.connect())
            - Logger is set for AdapterFactory before adapter creation
            - self._connected flag is set to True on success
        """
        # PHASE 1: Validate schema
        if not self.schema:
            self.logger.error(_ERROR_NO_SCHEMA)
            return

        # PHASE 2: Extract connection config from schema Meta
        meta = self.schema.get(_META_KEY, {})

        # PHASE 3: Validate required Meta fields
        if _META_KEY_DATA_TYPE not in meta:
            raise ValueError(_ERROR_MISSING_META_FIELD.format(field=_META_KEY_DATA_TYPE))
        
        # PHASE 3.5: SECURITY - Load Data_Path from environment (v1.5.12)
        # Priority order:
        #   1. Data_Source: Explicit env var reference (e.g., "ZDATA_CONTACTS_URL")
        #   2. Convention: Auto-detect from schema name (e.g., zSchema.contacts → ZDATA_CONTACTS_URL)
        #   3. Data_Path: Direct in schema (DEPRECATED - log security warning)
        data_path = None
        data_path_source = None  # Track where data_path came from for logging
        
        # Option 1: Check for Data_Source (explicit env var reference)
        if _META_KEY_DATA_SOURCE in meta:
            env_var_name = meta[_META_KEY_DATA_SOURCE]
            data_path_from_env = os.getenv(env_var_name)
            
            if data_path_from_env:
                data_path = data_path_from_env
                data_path_source = "env_explicit"
                self.logger.info(_SECURITY_INFO_LOADED_FROM_ENV.format(env_var=env_var_name))
            else:
                self.logger.warning(f"[zData] Environment variable not found: {env_var_name}")
        
        # Option 2: Try auto-convention (if no Data_Source and no Data_Path yet)
        if not data_path and _META_KEY_DATA_PATH not in meta:
            # Auto-detect: zSchema.contacts → ZDATA_CONTACTS_URL
            schema_name = meta.get(_META_KEY_SCHEMA_NAME, meta.get(_META_KEY_ZVAFILES, ""))
            if schema_name:
                # Extract: "zSchema.contacts.yaml" → "contacts"
                schema_key = schema_name.replace("zSchema.", "").replace(".yaml", "").split("/")[-1]
                env_var_name = f"{_ENV_VAR_PREFIX}{schema_key.upper()}{_ENV_VAR_SUFFIX}"
                data_path_from_env = os.getenv(env_var_name)
                
                if data_path_from_env:
                    data_path = data_path_from_env
                    data_path_source = "env_convention"
                    self.logger.info(_SECURITY_INFO_AUTO_CONVENTION.format(env_var=env_var_name))
        
        # Option 3: Fallback to Data_Path in schema (DEPRECATED)
        if not data_path:
            if _META_KEY_DATA_PATH in meta:
                data_path = meta[_META_KEY_DATA_PATH]
                data_path_source = "schema_file"
                self.logger.warning(_SECURITY_WARNING_DATA_PATH_IN_SCHEMA)
            else:
                # No connection info found anywhere
                raise ValueError(_ERROR_NO_DATA_CONNECTION)

        # PHASE 4: Extract Meta values
        data_type = meta[_META_KEY_DATA_TYPE]
        data_label = meta.get(_META_KEY_DATA_LABEL, _META_DEFAULT_LABEL)

        # PHASE 5: Resolve special paths via zParser (handles ~.zMachine.* and @ paths)
        data_path = self.zcli.zparser.resolve_data_path(data_path)
        self.logger.info(_LOG_INITIALIZING_ADAPTER, data_type, data_path, data_label)

        # PHASE 6: Set logger for factory
        AdapterFactory.set_logger(self.logger)

        # PHASE 7: Create appropriate adapter
        try:
            self.adapter = AdapterFactory.create_adapter(data_type, {
                "path": data_path,
                "label": data_label,
                "meta": meta
            })

            # PHASE 8: Connect
            self.adapter.connect()
            self._connected = True
            self.logger.info(_LOG_CONNECTED_BACKEND, data_type, data_path)

            # PHASE 9: Initialize storage quota manager (Phase 1.5)
            from zOS.L3_Abstraction.n_zData.zData_modules.shared.storage_quota import StorageQuotaManager
            self.storage_quota = StorageQuotaManager(self)

        except Exception as e:
            self.logger.error(_ERROR_FAILED_INITIALIZE.format(error=e))
            raise

    def _preprocess_request(self, request: Dict[str, Any]) -> None:
        """
        Preprocess request - parse tables option.
        
        This method parses the "tables" option in request.options:
        - "all": Expands to all tables in schema (excluding Meta, db_path)
        - Comma-separated list: Splits into list of table names
        
        The parsed table list is stored in request["tables"] for use by
        operations.ensure_tables_for_action().
        
        Args:
            request: Request dictionary (modified in-place)
        
        Returns:
            None
        
        Examples:
            # Example 1: All tables
            request = {"options": {"tables": "all"}}
            # Result: request["tables"] = ["users", "products", "orders"]
            
            # Example 2: Specific tables
            request = {"options": {"tables": "users, products"}}
            # Result: request["tables"] = ["users", "products"]
        
        Notes:
            - This method modifies request in-place
            - Reserved keys (Meta, db_path) are excluded from "all"
            - Comma-separated strings are split and stripped
        """
        # PHASE 1: Extract tables option
        tables_option = request.get(_REQUEST_KEY_OPTIONS, {}).get(_OPTION_KEY_TABLES)

        # PHASE 2: Parse tables option
        if tables_option and isinstance(tables_option, str):
            if tables_option.lower() == _OPTION_VALUE_ALL_TABLES:
                # Expand "all" to all tables (excluding reserved keys)
                request[_REQUEST_KEY_TABLES] = [
                    k for k in self.schema.keys()
                    if k not in (_RESERVED_KEY_META, _RESERVED_KEY_DB_PATH)
                ]
            else:
                # Split comma-separated list
                request[_REQUEST_KEY_TABLES] = [t.strip() for t in tables_option.split(",")]

    # ═══════════════════════════════════════════════════════════════════════════════════
    # CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════════════

    def is_connected(self) -> bool:
        """
        Check if adapter is connected to backend.
        
        This method validates connection state by checking:
        1. self._connected flag (set during initialization)
        2. Adapter instance exists
        3. Adapter.is_connected() returns True
        
        Returns:
            True if connected, False otherwise
        
        Examples:
            if zdata.is_connected():
                zdata.insert("users", ["name"], ["Alice"])
            else:
                print("Not connected!")
        
        Notes:
            - This method is called by handle_request() before operations
            - Connection state is managed automatically in wizard/one-shot modes
        """
        return self._connected and self.adapter and self.adapter.is_connected()

    def disconnect(self) -> None:
        """
        Disconnect from backend and close adapter connection.
        
        This method closes the database connection and resets the connection flag.
        It is called automatically in one-shot mode after each operation, or
        manually in wizard mode when operations are complete.
        
        Returns:
            None
        
        Examples:
            # Manual disconnect after operations
            zdata.load_schema(schema)
            zdata.insert("users", ["name"], ["Alice"])
            zdata.disconnect()
        
        Notes:
            - One-shot mode calls this automatically
            - Wizard mode requires manual disconnect
            - Safe to call multiple times (no-op if already disconnected)
        """
        if self.adapter:
            self.adapter.disconnect()
            self._connected = False
            self.logger.info(_LOG_DISCONNECTED)

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information from adapter.
        
        This method returns connection metadata from the adapter, typically including:
        - connected: Boolean connection state
        - adapter_type: Backend type (SQLite, PostgreSQL, CSV)
        - path: Database path or CSV directory
        - label: Human-readable label
        
        Returns:
            Dictionary with connection info, or {"connected": False} if not connected
        
        Examples:
            info = zdata.get_connection_info()
            print(f"Connected: {info['connected']}")
            print(f"Adapter: {info.get('adapter_type')}")
        
        Notes:
            - Structure varies by adapter type
            - Always includes "connected" key
        """
        if self.adapter:
            return self.adapter.get_connection_info()
        return {"connected": False}

    # ═══════════════════════════════════════════════════════════════════════════════════
    # CRUD OPERATIONS (Delegated to Adapter)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def insert(self, table: str, fields: List[str], values: List[Any]) -> Any:
        """
        Insert a new record into a table.
        
        This method delegates directly to the adapter's insert() method to add a new
        record to the specified table. The fields and values must match in length and
        order. The adapter handles database-specific INSERT SQL generation.
        
        Args:
            table: Target table name
            fields: List of field names to insert
            values: List of values corresponding to fields
        
        Returns:
            Number of affected rows (typically 1) or adapter-specific result
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Insert a single user
            zdata.insert("users", ["name", "email"], ["Alice", "alice@example.com"])
            
            # Insert with auto-increment ID (omit id field)
            zdata.insert("users", ["name"], ["Bob"])
        
        Notes:
            - Schema loading required before calling this method
            - Fields and values must match in length
            - Adapter handles type conversion and SQL escaping
            - Use handle_request() for validation and hooks
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        return self.adapter.insert(table, fields, values)

    def select(self, table: str, fields: Optional[List[str]] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Select records from a table.
        
        This method delegates to the adapter's select() method to query records with
        optional filtering (WHERE), ordering (ORDER BY), limiting (LIMIT), and joining
        (JOIN). The adapter handles database-specific SELECT SQL generation.
        
        Args:
            table: Target table name
            fields: Optional list of field names to select (None = all fields)
            **kwargs: Additional query parameters:
                      - where: WHERE clause (dict or string)
                      - joins: JOIN clauses (list of dicts)
                      - order: ORDER BY clause (string)
                      - limit: LIMIT clause (int)
        
        Returns:
            List of row dictionaries (one dict per row)
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Select all users
            rows = zdata.select("users")
            
            # Select specific fields with WHERE
            rows = zdata.select("users", fields=["name", "email"], where={"age": 25})
            
            # Select with ORDER BY and LIMIT
            rows = zdata.select("users", order="age DESC", limit=10)
        
        Notes:
            - Schema loading required before calling this method
            - WHERE clause can be dict (e.g., {"age": 25}) or string (e.g., "age > 25")
            - Adapter handles auto-join for foreign keys
            - Use handle_request() for complex queries with validation
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        return self.adapter.select(table, fields, **kwargs)

    def update(self, table: str, fields: List[str], values: List[Any], where: Any) -> Any:
        """
        Update existing records in a table.
        
        This method delegates to the adapter's update() method to modify records
        matching the WHERE clause. The fields and values must match in length and
        order. The adapter handles database-specific UPDATE SQL generation.
        
        Args:
            table: Target table name
            fields: List of field names to update
            values: List of values corresponding to fields
            where: WHERE clause (dict or string)
        
        Returns:
            Number of affected rows or adapter-specific result
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Update user email
            zdata.update("users", ["email"], ["new@example.com"], where={"id": 1})
            
            # Update multiple fields
            zdata.update("users", ["name", "age"], ["Alice", 30], where={"id": 1})
        
        Notes:
            - Schema loading required before calling this method
            - WHERE clause is required (use empty dict {} to update all rows)
            - Fields and values must match in length
            - Use handle_request() for validation and hooks
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        return self.adapter.update(table, fields, values, where)

    def delete(self, table: str, where: Any) -> Any:
        """
        Delete records from a table.
        
        This method delegates to the adapter's delete() method to remove records
        matching the WHERE clause. The adapter handles database-specific DELETE SQL
        generation. This operation is IRREVERSIBLE - use with caution.
        
        Args:
            table: Target table name
            where: WHERE clause (dict or string)
        
        Returns:
            Number of affected rows or adapter-specific result
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Delete specific user
            zdata.delete("users", where={"id": 1})
            
            # Delete users matching criteria
            zdata.delete("users", where={"age": {"<": 18}})
        
        Notes:
            - Schema loading required before calling this method
            - WHERE clause is required (use empty dict {} to delete all rows)
            - Operation is IRREVERSIBLE - backup before deleting
            - Cascade behavior depends on foreign key constraints
            - Use handle_request() for validation and safety checks
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        return self.adapter.delete(table, where)

    def upsert(self, table: str, fields: List[str], values: List[Any], conflict_fields: List[str]) -> Any:
        """
        Insert or update a record (UPSERT).
        
        This method delegates to the adapter's upsert() method to insert a new record
        or update an existing one if a conflict occurs on the specified fields. The
        adapter handles database-specific UPSERT SQL generation (INSERT OR REPLACE,
        ON CONFLICT DO UPDATE, or DataFrame merge).
        
        Args:
            table: Target table name
            fields: List of field names to insert/update
            values: List of values corresponding to fields
            conflict_fields: List of fields to check for conflicts (usually primary key)
        
        Returns:
            Number of affected rows or adapter-specific result
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Upsert user by ID (insert if not exists, update if exists)
            zdata.upsert("users", ["id", "name"], [1, "Alice"], conflict_fields=["id"])
            
            # Upsert by email (unique constraint)
            zdata.upsert("users", ["email", "name"], ["alice@example.com", "Alice"], conflict_fields=["email"])
        
        Notes:
            - Schema loading required before calling this method
            - Conflict fields typically include primary key or unique constraints
            - SQLite: Uses INSERT OR REPLACE
            - PostgreSQL: Uses ON CONFLICT DO UPDATE
            - CSV: Uses DataFrame merge
            - Use handle_request() for validation and hooks
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        return self.adapter.upsert(table, fields, values, conflict_fields)

    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        This method delegates to the adapter's list_tables() method to retrieve
        all table names from the backend. The result includes all user-created
        tables but excludes system tables (e.g., sqlite_sequence).
        
        Returns:
            List of table names
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            tables = zdata.list_tables()
            print(f"Available tables: {tables}")
        
        Notes:
            - Schema loading required before calling this method
            - System tables are typically excluded
            - CSV adapter returns list of CSV files
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        return self.adapter.list_tables()

    # ═══════════════════════════════════════════════════════════════════════════════════
    # DDL OPERATIONS (Data Definition Language)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def create_table(self, table_name: str, schema: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a new table in the database.
        
        This method delegates to the adapter's create_table() method to create a table
        from a schema definition. If schema is not provided, it is extracted from the
        loaded schema dictionary. The adapter handles database-specific CREATE TABLE
        SQL generation.
        
        Args:
            table_name: Name of table to create
            schema: Optional table schema definition (None = use loaded schema)
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
            TableNotFoundError: If schema not provided and table not in loaded schema
        
        Examples:
            # Create table from loaded schema
            zdata.create_table("users")
            
            # Create table with explicit schema
            schema = {
                "id": {"type": "INTEGER", "primary_key": True},
                "name": {"type": "TEXT", "required": True}
            }
            zdata.create_table("users", schema)
        
        Notes:
            - Schema loading required before calling this method
            - Table schema must define field types and constraints
            - Adapter handles database-specific type mapping
            - Use handle_request() for validation and idempotent creation
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        # If schema not provided, get from loaded schema
        if schema is None:
            if not self.schema or table_name not in self.schema:
                # Extract schema name if available (e.g., from Meta section)
                schema_name = self.schema.get(_META_KEY, {}).get(_META_KEY_SCHEMA_NAME) if self.schema else None
                raise TableNotFoundError(table_name, schema_name=schema_name)
            schema = self.schema[table_name]
        
        self.logger.debug(_DEBUG_CREATING_TABLE, table_name)
        return self.adapter.create_table(table_name, schema)

    def drop_table(self, table_name: str) -> Any:
        """
        Drop (delete) a table from the database.
        
        This method delegates to the adapter's drop_table() method to remove a table
        and all its data. This operation is IRREVERSIBLE - use with extreme caution.
        The adapter handles database-specific DROP TABLE SQL generation.
        
        Args:
            table_name: Name of table to drop
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Drop a table (IRREVERSIBLE!)
            zdata.drop_table("old_users")
        
        Notes:
            - Schema loading required before calling this method
            - Operation is IRREVERSIBLE - backup before dropping
            - Cascade behavior depends on foreign key constraints
            - Some adapters support IF EXISTS (no error if table doesn't exist)
            - Use handle_request() for validation and safety checks
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        self.logger.debug(_DEBUG_DROPPING_TABLE, table_name)
        return self.adapter.drop_table(table_name)

    def alter_table(self, table_name: str, changes: Dict[str, Any]) -> Any:
        """
        Alter table structure by adding or dropping columns.
        
        This method delegates to the adapter's alter_table() method to modify an
        existing table's structure. The adapter handles database-specific ALTER TABLE
        SQL generation.
        
        Args:
            table_name: Name of table to alter
            changes: Dictionary of changes (e.g., {"add": {"new_field": {...}}, "drop": ["old_field"]})
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Add a new column
            changes = {"add": {"age": {"type": "INTEGER"}}}
            zdata.alter_table("users", changes)
            
            # Drop a column (not supported by all adapters)
            changes = {"drop": ["old_field"]}
            zdata.alter_table("users", changes)
        
        Notes:
            - Schema loading required before calling this method
            - Not all adapters support all ALTER operations (e.g., SQLite limited)
            - Adding columns may require default values
            - Dropping columns may affect dependent objects (views, indexes)
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        self.logger.debug(_DEBUG_ALTERING_TABLE, table_name)
        return self.adapter.alter_table(table_name, changes)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        This method delegates to the adapter's table_exists() method to check if a
        table exists. The adapter queries database metadata to determine existence.
        
        Args:
            table_name: Name of table to check
        
        Returns:
            True if table exists, False otherwise
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            if zdata.table_exists("users"):
                print("Users table exists!")
            else:
                zdata.create_table("users")
        
        Notes:
            - Schema loading required before calling this method
            - Check is case-sensitive or case-insensitive depending on adapter
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        return self.adapter.table_exists(table_name)

    # ═══════════════════════════════════════════════════════════════════════════════════
    # DCL OPERATIONS (Data Control Language - PostgreSQL/MySQL only)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def grant(self, privileges: str, table_name: str, user: str) -> Any:
        """
        Grant privileges to a user (PostgreSQL/MySQL only).
        
        This method delegates to the adapter's grant() method to grant database
        privileges to a user. This operation is only supported by PostgreSQL and
        MySQL adapters.
        
        Args:
            privileges: Comma-separated list of privileges (e.g., "SELECT, INSERT")
            table_name: Target table name
            user: Username to grant privileges to
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
            NotImplementedError: If adapter does not support DCL operations
        
        Examples:
            # Grant SELECT and INSERT to user
            zdata.grant("SELECT, INSERT", "users", "app_user")
        
        Notes:
            - Schema loading required before calling this method
            - Only supported by PostgreSQL and MySQL adapters
            - Requires appropriate database permissions
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        # Check if adapter supports DCL
        if not hasattr(self.adapter, 'grant'):
            adapter_type = self.adapter.__class__.__name__
            raise NotImplementedError(
                _ERROR_DCL_NOT_SUPPORTED.format(adapter=adapter_type, operation="GRANT")
            )
        
        self.logger.debug(_DEBUG_GRANTING, privileges, table_name, user)
        return self.adapter.grant(privileges, table_name, user)

    def revoke(self, privileges: str, table_name: str, user: str) -> Any:
        """
        Revoke privileges from a user (PostgreSQL/MySQL only).
        
        This method delegates to the adapter's revoke() method to revoke database
        privileges from a user. This operation is only supported by PostgreSQL and
        MySQL adapters.
        
        Args:
            privileges: Comma-separated list of privileges (e.g., "SELECT, INSERT")
            table_name: Target table name
            user: Username to revoke privileges from
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
            NotImplementedError: If adapter does not support DCL operations
        
        Examples:
            # Revoke INSERT from user
            zdata.revoke("INSERT", "users", "app_user")
        
        Notes:
            - Schema loading required before calling this method
            - Only supported by PostgreSQL and MySQL adapters
            - Requires appropriate database permissions
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        # Check if adapter supports DCL
        if not hasattr(self.adapter, 'revoke'):
            adapter_type = self.adapter.__class__.__name__
            raise NotImplementedError(
                _ERROR_DCL_NOT_SUPPORTED.format(adapter=adapter_type, operation="REVOKE")
            )
        
        self.logger.debug(_DEBUG_REVOKING, privileges, table_name, user)
        return self.adapter.revoke(privileges, table_name, user)

    def list_privileges(self, table_name: Optional[str] = None, user: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List privileges for tables and users (PostgreSQL/MySQL only).
        
        This method delegates to the adapter's list_privileges() method to query
        database privileges. This operation is only supported by PostgreSQL and
        MySQL adapters.
        
        Args:
            table_name: Optional table name to filter by
            user: Optional username to filter by
        
        Returns:
            List of privilege dictionaries
        
        Raises:
            RuntimeError: If adapter not initialized
            NotImplementedError: If adapter does not support DCL operations
        
        Examples:
            # List all privileges
            privs = zdata.list_privileges()
            
            # List privileges for specific user
            privs = zdata.list_privileges(user="app_user")
        
        Notes:
            - Schema loading required before calling this method
            - Only supported by PostgreSQL and MySQL adapters
            - Requires appropriate database permissions
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        # Check if adapter supports DCL
        if not hasattr(self.adapter, 'list_privileges'):
            adapter_type = self.adapter.__class__.__name__
            raise NotImplementedError(
                _ERROR_DCL_NOT_SUPPORTED.format(adapter=adapter_type, operation="privilege listing")
            )
        
        self.logger.debug(_DEBUG_LISTING_PRIVILEGES, table_name, user)
        return self.adapter.list_privileges(table_name, user)

    # ═══════════════════════════════════════════════════════════════════════════════════
    # TCL OPERATIONS (Transaction Control Language)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def begin_transaction(self) -> Any:
        """
        Begin a new database transaction.
        
        This method delegates to the adapter's begin_transaction() method to start
        a transaction. Subsequent operations are part of the transaction until
        commit() or rollback() is called.
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Transaction workflow
            zdata.begin_transaction()
            try:
                zdata.insert("users", ["name"], ["Alice"])
                zdata.insert("profiles", ["user_id"], [1])
                zdata.commit()
            except Exception:
                zdata.rollback()
        
        Notes:
            - Schema loading required before calling this method
            - Not all adapters support transactions (e.g., CSV)
            - Transactions are not nested
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        self.logger.debug(_DEBUG_BEGIN_TRANSACTION)
        return self.adapter.begin_transaction()

    def commit(self) -> Any:
        """
        Commit the current transaction.
        
        This method delegates to the adapter's commit() method to commit all
        operations since begin_transaction() was called.
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            zdata.begin_transaction()
            zdata.insert("users", ["name"], ["Alice"])
            zdata.commit()
        
        Notes:
            - Schema loading required before calling this method
            - Must be called after begin_transaction()
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        self.logger.debug(_DEBUG_COMMIT_TRANSACTION)
        return self.adapter.commit()

    def rollback(self) -> Any:
        """
        Rollback the current transaction.
        
        This method delegates to the adapter's rollback() method to undo all
        operations since begin_transaction() was called.
        
        Returns:
            True on success, False or exception on failure
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            zdata.begin_transaction()
            try:
                zdata.insert("users", ["name"], ["Alice"])
                zdata.insert("profiles", ["user_id"], [1])
                zdata.commit()
            except Exception:
                zdata.rollback()  # Undo both inserts
        
        Notes:
            - Schema loading required before calling this method
            - Must be called after begin_transaction()
            - Use in exception handlers for error recovery
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        self.logger.debug(_DEBUG_ROLLBACK_TRANSACTION)
        return self.adapter.rollback()

    # ═══════════════════════════════════════════════════════════════════════════════════
    # MIGRATION OPERATIONS (Declarative Schema Migrations)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def _convert_zcli_to_diff_format(self, zcli_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert zCLI native schema format to schema_diff.py expected format.
        
        zCLI Format (native):
            {'zMeta': {...}, 'users': {'id': {...}, 'name': {...}}, ...}
        
        Diff Engine Format (expected):
            {'Tables': {'users': {'Columns': {'id': {...}, 'name': {...}}}, ...}}
        
        Args:
            zcli_schema: Schema in zCLI native format
        
        Returns:
            Schema in diff engine format
        """
        if not zcli_schema:
            return {'Tables': {}}
        
        # Extract tables (all keys except 'zMeta')
        tables = {}
        for key, value in zcli_schema.items():
            if key == _META_KEY:
                continue
            # Wrap table columns in 'Columns' key for diff engine
            tables[key] = {'Columns': value}
        
        return {'Tables': tables}

    def _introspect_database_schema(self) -> Dict[str, Any]:
        """
        Introspect current database state to get actual schema (database reality).
        
        This method queries the actual database/CSV files to determine what columns
        and tables currently exist, independent of what the YAML schema says.
        Critical for declarative migrations where we compare reality vs. target.
        
        Backend Support:
            - CSV: Uses pd.read_csv() to get column names and infer types
            - SQLite: Uses PRAGMA table_info() to get schema
            - PostgreSQL: Uses information_schema queries
        
        Returns:
            Dict[str, Any]: Schema dict in zCLI format matching self.schema structure:
            {
                'zMeta': {...},  # Copied from loaded schema
                'Tables': {
                    'users': {
                        'Columns': {
                            'id': {'type': 'int'},
                            'name': {'type': 'str'},
                            ...
                        }
                    },
                    ...
                }
            }
        
        Notes:
            - Returns empty dict if adapter not initialized
            - Falls back to loaded YAML schema if introspection not supported
            - Used by migrate() to get "old_schema" (current database state)
            - Does NOT include constraints/hooks (only columns and types)
        
        Example:
            >>> # After loading schema and connecting
            >>> actual_schema = z.data._introspect_database_schema()
            >>> # Returns what's ACTUALLY in the database, not what's in YAML
        """
        if not self.adapter:
            self.logger.warning("[zMigrate] No adapter - cannot introspect database")
            return {}
        
        # Check if adapter supports introspection
        if not hasattr(self.adapter, 'introspect_schema'):
            # Fallback: Use loaded YAML schema (old behavior for backwards compatibility)
            self.logger.debug("[zMigrate] Adapter doesn't support introspection - using loaded schema")
            return self.schema
        
        try:
            # CRITICAL: Only introspect tables that are defined in the loaded schema!
            # We don't want to detect "extra" tables in the database as candidates for dropping.
            # This ensures we only compare the schema-defined tables' reality vs. their YAML definition.
            
            # zCLI schema format: tables are top-level keys (excluding 'zMeta')
            # Example: {'zMeta': {...}, 'users': {...}, 'posts': {...}}
            tables = [key for key in self.schema.keys() if key != _META_KEY] if self.schema else []
            
            self.logger.debug(f"[zMigrate] Introspecting {len(tables)} schema-defined tables: {tables}")
            
            # Introspect each table
            introspected_tables = {}
            for table_name in tables:
                try:
                    table_schema = self.adapter.introspect_schema(table_name)
                    if table_schema:
                        # Store as top-level key (zCLI format), NOT nested under 'Tables'
                        # The table definition is just the columns dict
                        introspected_tables[table_name] = table_schema
                        self.logger.debug(f"[zMigrate] Introspected {table_name}: {len(table_schema)} columns")
                except Exception as e:
                    self.logger.warning(f"[zMigrate] Failed to introspect {table_name}: {e}")
                    continue
            
            # Build complete schema structure matching zCLI format
            # Tables are at top level, NOT nested under 'Tables' key
            introspected_schema = {
                _META_KEY: self.schema.get(_META_KEY, {}) if self.schema else {}
            }
            # Add each table as a top-level key
            introspected_schema.update(introspected_tables)
            
            self.logger.info(f"[zMigrate] Introspected database: {len(introspected_tables)} tables")
            return introspected_schema
            
        except Exception as e:
            self.logger.error(f"[zMigrate] Introspection failed: {e}")
            # Fallback to loaded schema
            return self.schema

    def migrate(self, new_schema_path: str, dry_run: bool = False, 
                auto_approve: bool = False, schema_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute declarative schema migration to new schema version.
        
        This method performs a declarative migration by comparing the current schema
        with a new target schema and automatically applying the necessary DDL operations
        (CREATE TABLE, ALTER TABLE, DROP TABLE) to bring the database in line with
        the new schema.
        
        Migration Flow:
        1. Load current schema (from self.schema)
        2. Load new schema from new_schema_path
        3. Compute diff via schema_diff.diff_schemas()
        4. Display preview via zDisplay
        5. Prompt for confirmation (unless dry_run or auto_approve)
        6. Execute DDL operations in transaction
        7. Record migration in _zdata_migrations table
        8. Return success/failure result
        
        Args:
            new_schema_path: Path to new schema YAML file (supports zPath: @., ~.)
            dry_run: If True, preview changes without executing (default False)
            auto_approve: If True, skip confirmation prompt (default False)
            schema_version: Optional version string (e.g., "v1.2.3", git commit)
        
        Returns:
            Dict with keys:
            - success: True if migration succeeded, False otherwise
            - diff: Structured diff from schema_diff.diff_schemas()
            - operations_executed: Count of DDL operations performed
            - error: Error message if failed (only if success=False)
        
        Raises:
            RuntimeError: If adapter not initialized or schema not loaded
            KeyError: If new schema path invalid
            Exception: Any database errors during execution
        
        Examples:
            # Dry-run (preview only)
            result = zdata.migrate("@myapp.users_v2.yaml", dry_run=True)
            
            # Execute migration with confirmation
            result = zdata.migrate("@myapp.users_v2.yaml")
            
            # Execute migration without confirmation (use with caution!)
            result = zdata.migrate("@myapp.users_v2.yaml", auto_approve=True)
            
            # Execute with version tracking
            result = zdata.migrate("@myapp.users_v2.yaml", schema_version="v1.2.3")
        
        Notes:
            - Dry-run mode: Safe for testing, displays preview without executing
            - Auto-approve mode: Use with caution! Skips confirmation prompts
            - Transaction wrapping: All operations are atomic (all-or-nothing)
            - Rollback on failure: Any error triggers automatic rollback
            - History tracking: Successful migrations recorded in _zdata_migrations
            - Idempotency: Re-running same schema is safe (no-op if no changes)
            - Schema must be loaded before calling migrate()
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        if not self.schema:
            raise RuntimeError("No schema loaded. Call load_schema() first.")
        
        # Load new schema from path
        from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import (
            get_current_schema_hash
        )
        
        # Parse new schema path via zParser
        new_schema = self.zcli.loader.handle(new_schema_path)
        
        # NEW v1.5.13: Check if migrations are enabled (opt-in for safety)
        # This prevents accidental schema changes and supports backend migrations
        if not new_schema:
            error_msg = f"❌ Failed to load schema: {new_schema_path}"
            self.logger.error(error_msg)
            return {"success": False, "error": "Schema load failed"}
        
        new_meta = new_schema.get(_META_KEY, {})
        migration_enabled = new_meta.get(_META_KEY_ZMIGRATION, False)
        
        if not migration_enabled:
            error_msg = (
                f"\n❌ Schema Migration Not Enabled!\n"
                f"   Schema: {new_schema_path}\n"
                f"   \n"
                f"   To enable migrations, add to Meta section:\n"
                f"   \n"
                f"   Meta:\n"
                f"     zMigration: true\n"
                f"     zMigrationVersion: \"v1.0.0\"\n"
                f"   \n"
                f"   This opt-in flag prevents accidental schema changes.\n"
            )
            self.logger.error(error_msg)
            
            # Display user-friendly error via zDisplay
            self.zcli.display.text("", indent=0)
            self.zcli.display.text("❌ Migration Blocked: zMigration not enabled", indent=0)
            self.zcli.display.text("", indent=0)
            self.zcli.display.text(f"Schema file: {new_schema_path}", indent=1)
            self.zcli.display.text("", indent=0)
            self.zcli.display.text("To enable migrations, add to Meta section:", indent=1)
            self.zcli.display.text("", indent=0)
            self.zcli.display.text("  Meta:", indent=1)
            self.zcli.display.text("    zMigration: true", indent=1)
            self.zcli.display.text("    zMigrationVersion: \"v1.0.0\"", indent=1)
            self.zcli.display.text("", indent=0)
            self.zcli.display.text("This opt-in flag prevents accidental schema changes.", indent=1)
            self.zcli.display.text("", indent=0)
            
            return {
                "success": False,
                "error": "zMigration not enabled in schema",
                "hint": "Add 'zMigration: true' to Meta section"
            }
        
        # Log migration version
        new_version = new_meta.get(META_KEY_ZMIGRATION_VERSION, "unknown")
        self.logger.info(f"[zMigrate] Schema version: {new_version}")
        
        # NEW v1.5.13: Check for backend changes (CSV → Postgres, etc.)
        old_meta = self.schema.get(_META_KEY, {})
        old_backend = old_meta.get(_META_KEY_DATA_TYPE)
        new_backend = new_meta.get(_META_KEY_DATA_TYPE)
        
        if old_backend and new_backend and old_backend != new_backend:
            self.logger.info(f"[zMigrate] Backend change detected: {old_backend} → {new_backend}")
            return self._handle_backend_migration(old_backend, new_backend, new_schema, dry_run)
        
        # Compute schema hash
        schema_hash = get_current_schema_hash(new_schema)
        
        # NEW v1.5.14: Introspect actual database state (not YAML)
        # This compares database REALITY vs. target YAML schema
        self.logger.info("[zMigrate] Introspecting current database state...")
        old_schema_zcli = self._introspect_database_schema()
        
        # Convert both schemas to diff engine format
        # schema_diff expects {'Tables': {'users': {'Columns': {...}}}}
        # but zCLI uses {'zMeta': {...}, 'users': {...}}
        self.logger.debug("[zMigrate] Converting schemas to diff engine format...")
        old_schema_diff = self._convert_zcli_to_diff_format(old_schema_zcli)
        new_schema_diff = self._convert_zcli_to_diff_format(new_schema)
        
        # Build migration request
        request = {
            "old_schema": old_schema_diff,  # Database reality (introspected + converted)
            "new_schema": new_schema_diff,  # Target YAML schema (converted)
            "dry_run": dry_run,
            "auto_approve": auto_approve,
            "schema_version": schema_version or "unknown",
            "schema_hash": schema_hash
        }
        
        # Execute migration via operations facade
        result = self.operations.route_action("migrate", request)
        
        return result

    def get_migration_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve migration execution history.
        
        Returns list of migration records from the _zdata_migrations table,
        ordered by applied_at (most recent first). Useful for displaying
        migration audit trail to users.
        
        Args:
            limit: Maximum number of records to return (default 100)
        
        Returns:
            List of migration record dicts, each with keys:
            - id: Migration ID
            - schema_version: Version string (e.g., "v1.2.3")
            - schema_hash: SHA256 hash of schema
            - applied_at: ISO 8601 timestamp when migration ran
            - duration_ms: Migration execution time in milliseconds
            - tables_added: Count of tables created
            - tables_dropped: Count of tables dropped
            - columns_added: Count of columns added
            - columns_dropped: Count of columns dropped
            - status: "success" or "failed"
            - error_message: Error details if failed
        
        Raises:
            RuntimeError: If adapter not initialized
        
        Examples:
            # Get recent migrations
            history = zdata.get_migration_history(limit=10)
            for record in history:
                print(f"{record['applied_at']}: {record['schema_version']} - {record['status']}")
            
            # Check if any migrations applied
            history = zdata.get_migration_history()
            if history:
                print(f"Last migration: {history[0]['applied_at']}")
            else:
                print("No migrations applied yet")
        
        Notes:
            - Returns empty list if no migrations or table doesn't exist
            - Results ordered by applied_at DESC (newest first)
            - Limit prevents loading huge history (default 100)
            - Shows both successful and failed migrations
        """
        if not self.adapter:
            raise RuntimeError(_ERROR_NO_ADAPTER)
        
        from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import (
            get_migration_history as _get_history
        )
        
        return _get_history(self.adapter, limit=limit)

    def discover_schemas(self) -> List[Dict[str, Any]]:
        """
        Discover all schemas with zMigration enabled from ZDATA_*_URL environment variables.
        
        Scans environment for ZDATA_*_URL patterns, loads corresponding schemas via zLoader,
        filters by zMigration: true, and returns metadata for each schema. This is the
        foundation for app-wide migration operations.
        
        Discovery Process:
            1. Scan z.config.environment.env for ZDATA_*_URL variables
            2. Extract table name from env var (ZDATA_USERS_URL → users)
            3. Construct schema path (@.models.zSchema.users)
            4. Load schema via z.loader.handle()
            5. Check Meta.zMigration flag (defaults to True)
            6. Return list of schema metadata dicts
        
        Returns:
            List[Dict[str, Any]]: List of discovered schemas, each dict contains:
                - name: Schema name (e.g., "zSchema.users")
                - env_var: Environment variable name (e.g., "ZDATA_USERS_URL")
                - data_type: Backend type (csv, sqlite, postgresql)
                - version: Current zMigrationVersion (e.g., "v1.0.0")
                - migration_enabled: Whether zMigration is enabled (bool)
                - schema: Full schema dictionary (for further processing)
        
        Examples:
            >>> schemas = z.data.discover_schemas()
            >>> for schema in schemas:
            >>>     if schema['migration_enabled']:
            >>>         print(f"{schema['name']} v{schema['version']} ({schema['data_type']})")
            
            >>> # Filter by backend type
            >>> csv_schemas = [s for s in z.data.discover_schemas() if s['data_type'] == 'csv']
            
            >>> # Get migration-enabled count
            >>> enabled = [s for s in z.data.discover_schemas() if s['migration_enabled']]
            >>> print(f"{len(enabled)} schemas ready for migration")
        
        Notes:
            - Automatically uses zConfig.environment.env (includes .zEnv)
            - Falls back to os.environ if no ZDATA_* vars found in zConfig
            - Schema loading errors are logged and skipped (not fatal)
            - Empty list returned if no ZDATA_*_URL variables found
            - zMigration defaults to True if not specified in schema Meta
            - Convention: ZDATA_USERS_URL → @.models.zSchema.users.yaml
        
        Architecture:
            This method implements the "Automatic Discovery" feature from zMigration guide,
            enabling zero-config migration workflows where schemas are discovered from
            environment without manual registration.
        """
        from zOS import os
        
        schemas = []
        
        # Get environment from zCLI (includes .zEnv from app directory)
        env = self.zcli.config.environment.env
        
        # Fallback to os.environ if zCLI env doesn't have ZDATA vars
        if not any(k.startswith('ZDATA_') for k in env.keys()):
            env = os.environ
            self.logger.debug("[discover_schemas] Using os.environ as fallback for ZDATA_* vars")
        
        # Scan environment for ZDATA_*_URL variables
        for key, value in env.items():
            if key.startswith('ZDATA_') and key.endswith('_URL'):
                # Extract schema name (e.g., ZDATA_USERS_URL → users)
                schema_name_upper = key[6:-4]  # Remove ZDATA_ prefix and _URL suffix
                schema_name = schema_name_upper.lower()
                
                try:
                    # Construct schema path following zCLI convention
                    # ZDATA_USERS_URL → @.models.zSchema.users
                    schema_path = f"@.models.zSchema.{schema_name}"
                    
                    # Load schema via zLoader (handles @ paths, YAML parsing, etc.)
                    schema = self.zcli.loader.handle(schema_path)
                    
                    if schema:
                        meta = schema.get(_META_KEY, {})
                        
                        # Get migration flag (defaults to True per zMigration guide)
                        migration_enabled = meta.get('zMigration', True)
                        
                        schemas.append({
                            'name': f"zSchema.{schema_name}",
                            'env_var': key,
                            'data_type': meta.get('Data_Type', 'unknown'),
                            'version': meta.get('zMigrationVersion', 'none'),
                            'migration_enabled': migration_enabled,
                            'schema': schema
                        })
                        
                        self.logger.debug(
                            f"[discover_schemas] Discovered: {schema_name} "
                            f"(v{meta.get('zMigrationVersion', 'none')}, "
                            f"migration={'enabled' if migration_enabled else 'disabled'})"
                        )
                    else:
                        self.logger.debug(f"[discover_schemas] Schema not found: {schema_path}")
                        
                except Exception as e:
                    # Schema not found or error loading - log and skip
                    self.logger.debug(f"[discover_schemas] Skipped {key}: {e}")
        
        self.logger.info(f"[discover_schemas] Found {len(schemas)} schema(s), "
                        f"{sum(1 for s in schemas if s['migration_enabled'])} migration-enabled")
        
        return schemas

    def migrate_app(self,
                    app_file: Optional[str] = None,
                    auto_approve: bool = False,
                    dry_run: bool = False,
                    specific_schema: Optional[str] = None,
                    force_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute migrations for all schemas in an application.
        
        High-level orchestration method for app-wide migrations. Discovers all schemas
        with zMigration enabled, executes migrations via self.migrate(), aggregates results,
        and provides summary statistics. This is the primary entry point for the
        "zolo migrate" CLI command.
        
        Migration Workflow:
            1. Call self.discover_schemas() to find all ZDATA_*_URL schemas
            2. Filter by zMigration: true (skip disabled schemas)
            3. Filter by specific_schema if provided
            4. For each schema:
                a. Construct schema path (@.models.{schema_name})
                b. Call self.migrate() with auto_approve/dry_run/version
                c. Track result (success/failed/up_to_date)
            5. Aggregate results and return summary dict
        
        Args:
            app_file: Optional app file path (for display/logging only, not used functionally)
            auto_approve: If True, skip confirmation prompts (for CI/CD)
            dry_run: If True, preview changes without executing (not yet implemented)
            specific_schema: If provided, migrate only this schema (e.g., "users")
            force_version: If provided, force this version for all migrations
        
        Returns:
            Dict[str, Any]: Migration results with keys:
                - success: Count of migrations that succeeded
                - failed: Count of migrations that failed
                - skipped: Count of schemas skipped (zMigration: false)
                - up_to_date: Count of schemas already up-to-date (no changes)
                - total: Total schemas processed
                - schemas: List of per-schema results (each has 'name', 'status', 'result')
        
        Examples:
            >>> # Migrate all schemas with confirmation prompts
            >>> result = z.data.migrate_app()
            >>> print(f"Success: {result['success']}, Failed: {result['failed']}")
            
            >>> # CI/CD: Auto-approve all migrations
            >>> result = z.data.migrate_app(auto_approve=True)
            >>> if result['failed'] > 0:
            >>>     raise Exception(f"{result['failed']} migrations failed")
            
            >>> # Migrate specific schema only
            >>> result = z.data.migrate_app(specific_schema="users")
            
            >>> # Force version for all schemas
            >>> result = z.data.migrate_app(force_version="v2.0.0")
        
        Notes:
            - Schemas with zMigration: false are counted in 'skipped', not processed
            - Each schema migration is independent (one failure doesn't stop others)
            - Results include detailed per-schema information for logging/debugging
            - app_file parameter is optional, used only for display (not required)
            - Uses self.migrate() for each schema (single source of truth)
            - Follows "zolo migrate" command pattern from zMigration guide
        
        Architecture:
            This method implements the app-wide orchestration layer described in the
            zMigration guide, providing a single entry point for migrating all schemas
            in an application without manual iteration in CLI layer (main.py).
        """
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'up_to_date': 0,
            'total': 0,
            'schemas': []
        }
        
        # Discover all schemas from environment
        discovered_schemas = self.discover_schemas()
        
        if not discovered_schemas:
            self.logger.warning("[migrate_app] No schemas found with ZDATA_*_URL environment variables")
            return results
        
        # Filter by zMigration: true
        migration_enabled_schemas = [s for s in discovered_schemas if s['migration_enabled']]
        
        if not migration_enabled_schemas:
            results['skipped'] = len(discovered_schemas)
            results['total'] = len(discovered_schemas)
            self.logger.info(f"[migrate_app] No schemas enabled for migration (zMigration: false)")
            return results
        
        # Filter by specific_schema if provided
        if specific_schema:
            migration_enabled_schemas = [
                s for s in migration_enabled_schemas 
                if s['name'].split('.')[-1].lower() == specific_schema.lower()
            ]
            if not migration_enabled_schemas:
                self.logger.warning(f"[migrate_app] Schema '{specific_schema}' not found or not migration-enabled")
                return results
        
        results['total'] = len(migration_enabled_schemas)
        results['skipped'] = len(discovered_schemas) - len(migration_enabled_schemas)
        
        self.logger.info(f"[migrate_app] Migrating {len(migration_enabled_schemas)} schema(s)")
        
        # Migrate each schema
        for schema_info in migration_enabled_schemas:
            schema_name = schema_info['name']
            schema_path = f"@.models.{schema_name}"
            current_version = schema_info['version']
            
            # Use force_version if provided, otherwise use schema's current version
            target_version = force_version if force_version else (current_version if current_version != 'none' else None)
            
            self.logger.info(f"[migrate_app] Migrating {schema_name} (v{current_version})")
            
            try:
                # Use zData.migrate() for single-schema migration
                # This is the Single Source of Truth for migration logic
                migration_result = self.migrate(
                    new_schema_path=schema_path,
                    auto_approve=auto_approve,
                    schema_version=target_version
                )
                
                # Track results
                schema_result = {
                    'name': schema_name,
                    'version': current_version,
                    'result': migration_result
                }
                
                if migration_result.get('success'):
                    ops_executed = migration_result.get('operations_executed', 0)
                    if ops_executed == 0:
                        results['up_to_date'] += 1
                        schema_result['status'] = 'up_to_date'
                        self.logger.info(f"[migrate_app] {schema_name}: Up to date (no changes)")
                    else:
                        results['success'] += 1
                        schema_result['status'] = 'success'
                        self.logger.info(f"[migrate_app] {schema_name}: Success ({ops_executed} operation(s))")
                else:
                    results['failed'] += 1
                    schema_result['status'] = 'failed'
                    error = migration_result.get('error', 'Unknown error')
                    self.logger.error(f"[migrate_app] {schema_name}: Failed - {error}")
                
                results['schemas'].append(schema_result)
                
            except Exception as e:
                results['failed'] += 1
                schema_result = {
                    'name': schema_name,
                    'version': current_version,
                    'status': 'failed',
                    'result': {'success': False, 'error': str(e)}
                }
                results['schemas'].append(schema_result)
                self.logger.error(f"[migrate_app] {schema_name}: Exception - {e}", exc_info=True)
        
        # Log summary
        self.logger.info(
            f"[migrate_app] Complete: {results['success']} success, "
            f"{results['failed']} failed, {results['up_to_date']} up-to-date, "
            f"{results['skipped']} skipped"
        )
        
        return results

    def cli_migrate(self,
                    app_file: Optional[str] = None,
                    auto_approve: bool = False,
                    dry_run: bool = False,
                    specific_schema: Optional[str] = None,
                    force_version: Optional[str] = None) -> int:
        """
        CLI entry point for migrations - provides full user experience with display.
        
        This is a wrapper around migrate_app() that adds:
        - Display banners and headers
        - Schema discovery display with status
        - Migration results formatting
        - User-friendly output formatting
        
        Designed for `zolo migrate` CLI command, delegating to this method keeps
        all migration UX logic in zData (single source of truth) rather than
        scattered in main.py.
        
        Args:
            app_file: Optional app file path (for display only)
            auto_approve: If True, skip confirmation prompts (for CI/CD)
            dry_run: If True, preview changes without executing
            specific_schema: If provided, migrate only this schema (e.g., "users")
            force_version: If provided, force this version for all migrations
        
        Returns:
            int: Exit code (0 = success, 1 = error)
        
        Examples:
            >>> # From main.py CLI handler
            >>> z = zCLI({'zMode': 'Terminal'})
            >>> exit_code = z.data.cli_migrate(app_file="app.py", auto_approve=False)
            
            >>> # Programmatic use
            >>> z = zCLI()
            >>> exit_code = z.data.cli_migrate(specific_schema="users", dry_run=True)
        
        Notes:
            - Returns exit code (0/1) suitable for CLI, unlike migrate_app() which returns dict
            - Handles all display formatting internally (no display logic in main.py)
            - Delegates actual migration work to migrate_app()
        """
        from pathlib import Path
        
        # Display banner
        self.display.text("\n" + "=" * 70)
        self.display.text("🔄 zMigration: Schema Evolution System")
        self.display.text("=" * 70)
        if app_file:
            app_path = Path(app_file).resolve()
            self.display.text(f"   App: {app_path.name}")
            self.display.text(f"   Directory: {app_path.parent}")
        self.display.text("=" * 70 + "\n")
        
        self.display.text("1️⃣ Initializing zCLI...")
        self.display.text("   ✅ zCLI initialized\n")
        
        # Discover schemas
        self.display.text("2️⃣ Discovering schemas...")
        schemas_discovered = self.discover_schemas()
        
        if not schemas_discovered:
            self.display.text("   ⚠️  No schemas found with ZDATA_*_URL environment variables")
            self.display.text("\n💡 Tip: Add ZDATA_USERS_URL=@.Data to your .zEnv file")
            self.display.text("=" * 70 + "\n")
            return 0
        
        # Display discovered schemas
        migration_enabled = [s for s in schemas_discovered if s['migration_enabled']]
        self.display.text(f"   ✅ Found {len(schemas_discovered)} schema(s), {len(migration_enabled)} migration-enabled\n")
        
        self.display.text("📊 Discovered Schemas:")
        self.display.text("-" * 70)
        for schema_info in schemas_discovered:
            status_icon = "✓" if schema_info['migration_enabled'] else "✗"
            status_text = "enabled" if schema_info['migration_enabled'] else "disabled"
            self.display.text(f"   {status_icon} {schema_info['name']}")
            self.display.text(f"      Data Type: {schema_info['data_type']}")
            self.display.text(f"      Version: {schema_info['version']}")
            self.display.text(f"      zMigration: {status_text}")
            if not schema_info['migration_enabled']:
                self.display.text("      → SKIPPED")
            self.display.text("")
        
        self.display.text("=" * 70)
        self.display.text("✅ Schema Discovery Complete")
        self.display.text("=" * 70 + "\n")
        
        if not migration_enabled:
            self.display.text("   No schemas enabled for migration (zMigration: false)\n")
            return 0
        
        # Execute migrations (delegate to migrate_app)
        self.display.text("3️⃣ Applying Migrations...")
        self.display.text(f"   📌 {len(migration_enabled)} schema(s) ready\n")
        self.display.text("=" * 70 + "\n")
        
        result = self.migrate_app(
            app_file=app_file,
            auto_approve=auto_approve,
            dry_run=dry_run,
            specific_schema=specific_schema,
            force_version=force_version
        )
        
        # Display results summary
        self.display.text("\n" + "=" * 70)
        self.display.text("📊 Migration Results")
        self.display.text("=" * 70 + "\n")
        
        if result['success']:
            self.display.text(f"   ✅ {result['success']} migration(s) applied successfully")
        if result['up_to_date']:
            self.display.text(f"   ℹ️  {result['up_to_date']} schema(s) already up to date")
        if result['failed']:
            self.display.text(f"   ❌ {result['failed']} migration(s) failed")
        if result['skipped']:
            self.display.text(f"   ⏭️  {result['skipped']} schema(s) skipped")
        
        self.display.text("\n" + "=" * 70)
        
        total_processed = result['success'] + result['up_to_date']
        if result['failed'] == 0 and total_processed > 0:
            self.display.text("✅ All schemas processed successfully!")
        elif result['failed'] > 0:
            self.display.text("⚠️  Some migrations failed. Check logs for details.")
        else:
            self.display.text("ℹ️  No migrations were applied.")
        
        self.display.text("=" * 70 + "\n")
        
        return 0 if result['failed'] == 0 else 1

    def _handle_backend_migration(self, old_backend: str, new_backend: str, 
                                   new_schema: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Handle migration between different backends (CSV → Postgres, etc.)
        
        This method orchestrates a complete backend migration by:
        1. Exporting all data from current backend
        2. Initializing new backend with new schema
        3. Importing data to new backend
        4. Creating backup of old data
        
        Args:
            old_backend: Current backend type (csv, sqlite, postgres)
            new_backend: Target backend type
            new_schema: New schema dictionary
            dry_run: If True, preview only (no execution)
        
        Returns:
            Dict with success status and migration details:
            - success: True if migration succeeded
            - backend_changed: True (indicates backend migration occurred)
            - old_backend: Previous backend type
            - new_backend: New backend type
            - backup_location: Path to exported data backup
            - tables_migrated: Count of tables migrated
            - error: Error message if failed
        
        Notes:
            - Creates timestamped backup directory in Data/backups/
            - All data exported to CSV for portability
            - Atomic operation: rolls back on failure
            - Preserves original data (never destructive)
        
        Examples:
            # Dry-run backend migration
            result = zdata._handle_backend_migration("csv", "postgres", new_schema, dry_run=True)
            
            # Execute backend migration
            result = zdata._handle_backend_migration("csv", "postgres", new_schema)
        """
        from datetime import datetime
        import os
        
        # Display migration plan
        self.zcli.display.text("", indent=0)
        self.zcli.display.text("=" * 80, indent=0)
        self.zcli.display.text("⚠️  BACKEND MIGRATION DETECTED", indent=0)
        self.zcli.display.text("=" * 80, indent=0)
        self.zcli.display.text("", indent=0)
        self.zcli.display.text(f"  Old Backend: {old_backend}", indent=0)
        self.zcli.display.text(f"  New Backend: {new_backend}", indent=0)
        self.zcli.display.text("", indent=0)
        self.zcli.display.text("Migration Steps:", indent=0)
        self.zcli.display.text("  1. Export all data from current backend", indent=0)
        self.zcli.display.text("  2. Initialize new backend", indent=0)
        self.zcli.display.text("  3. Import data to new backend", indent=0)
        self.zcli.display.text("  4. Backup old data", indent=0)
        self.zcli.display.text("", indent=0)
        
        if dry_run:
            self.zcli.display.text("🔍 DRY RUN - No changes will be applied", indent=0)
            self.zcli.display.text("", indent=0)
            return {
                "success": True,
                "dry_run": True,
                "backend_migration": True,
                "old_backend": old_backend,
                "new_backend": new_backend
            }
        
        # Confirm with user
        self.zcli.display.text("⚠️  This operation will:", indent=0)
        self.zcli.display.text("  - Export all data from current backend", indent=0)
        self.zcli.display.text("  - Initialize new backend", indent=0)
        self.zcli.display.text("  - Import data (may take time for large datasets)", indent=0)
        self.zcli.display.text("", indent=0)
        self.zcli.display.text("⏳ Starting backend migration...", indent=0)
        self.zcli.display.text("", indent=0)
        
        try:
            # Step 1: Export current data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_dir = f"Data/backups/{old_backend}_export_{timestamp}"
            
            self.zcli.display.text(f"📦 Exporting data from {old_backend}...", indent=1)
            
            # Create export directory
            os.makedirs(export_dir, exist_ok=True)
            
            # Get all tables from current schema
            current_tables = [k for k in self.schema.keys() if k not in [_META_KEY, _RESERVED_KEY_DB_PATH]]
            
            # Export each table
            exported_tables = []
            for table_name in current_tables:
                try:
                    # Read all rows from table
                    rows = self.adapter.select(table_name)
                    
                    if rows:
                        # Write to CSV in export directory
                        import csv
                        export_file = os.path.join(export_dir, f"{table_name}.csv")
                        
                        with open(export_file, 'w', newline='') as f:
                            if rows:
                                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                                writer.writeheader()
                                writer.writerows(rows)
                        
                        exported_tables.append(table_name)
                        self.zcli.display.text(f"  ✓ Exported {table_name} ({len(rows)} rows)", indent=1)
                except Exception as e:
                    self.logger.warning(f"Could not export table {table_name}: {e}")
            
            self.zcli.display.text(f"  ✓ Exported {len(exported_tables)} tables to {export_dir}", indent=1)
            self.zcli.display.text("", indent=0)
            
            # Step 2: Initialize new backend
            self.zcli.display.text(f"🔧 Initializing new backend ({new_backend})...", indent=1)
            
            # Disconnect from old backend
            if self._connected:
                self.adapter.disconnect()
                self._connected = False
            
            # Load new schema
            self.schema = new_schema
            self._initialize_adapter()
            
            self.zcli.display.text(f"  ✓ New backend initialized", indent=1)
            self.zcli.display.text("", indent=0)
            
            # Step 3: Import data to new backend
            self.zcli.display.text(f"📥 Importing data to {new_backend}...", indent=1)
            
            imported_tables = []
            for table_name in exported_tables:
                try:
                    import csv
                    export_file = os.path.join(export_dir, f"{table_name}.csv")
                    
                    with open(export_file, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    if rows:
                        # Insert into new backend
                        for row in rows:
                            self.adapter.insert(table_name, row)
                        
                        imported_tables.append(table_name)
                        self.zcli.display.text(f"  ✓ Imported {table_name} ({len(rows)} rows)", indent=1)
                except Exception as e:
                    self.logger.error(f"Failed to import table {table_name}: {e}")
            
            self.zcli.display.text(f"  ✓ Imported {len(imported_tables)} tables", indent=1)
            self.zcli.display.text("", indent=0)
            self.zcli.display.text("✅ Backend migration complete!", indent=0)
            self.zcli.display.text("", indent=0)
            self.zcli.display.text(f"📦 Backup location: {export_dir}", indent=1)
            self.zcli.display.text("", indent=0)
            
            return {
                "success": True,
                "backend_changed": True,
                "old_backend": old_backend,
                "new_backend": new_backend,
                "backup_location": export_dir,
                "tables_migrated": len(imported_tables)
            }
        
        except Exception as e:
            error_msg = f"Backend migration failed: {str(e)}"
            self.logger.error(error_msg)
            
            self.zcli.display.text("", indent=0)
            self.zcli.display.text(f"❌ Migration failed: {str(e)}", indent=0)
            self.zcli.display.text("", indent=0)
            
            return {
                "success": False,
                "error": error_msg,
                "backup_location": export_dir if 'export_dir' in locals() else None
            }

    # ═══════════════════════════════════════════════════════════════════════════════════
    # FILE OPERATIONS (zOpen Integration)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def open_schema(self, schema_path: Optional[str] = None) -> Any:
        """
        Open schema file in editor via zOpen.
        
        This method delegates to zOpen to open the schema YAML file in the configured
        editor. If schema_path is not provided, it is extracted from the Meta.zVaFiles
        field of the loaded schema.
        
        Args:
            schema_path: Optional path to schema file (None = use Meta.zVaFiles)
        
        Returns:
            Result from zOpen.handle() or "error" on failure
        
        Examples:
            # Open loaded schema in editor
            zdata.open_schema()
            
            # Open specific schema file
            zdata.open_schema("@.zSchema.users.yaml")
        
        Notes:
            - Requires zOpen subsystem
            - Schema loading required if schema_path not provided
            - Editor is configured in zSession or zMachine
        """
        if not self.open:
            self.logger.warning(_ERROR_NO_ZOPEN)
            return _RESULT_ERROR

        # Use current schema's path if not specified
        if not schema_path and self.schema:
            meta = self.schema.get(_META_KEY, {})
            schema_path = meta.get(_META_KEY_ZVAFILES)

        if not schema_path:
            self.logger.error(_ERROR_NO_SCHEMA_PATH)
            return _RESULT_ERROR

        self.logger.info(_LOG_OPENING_SCHEMA, schema_path)
        return self.open.handle({"zOpen": {"path": schema_path}})

    def open_csv(self, table_name: Optional[str] = None) -> Any:
        """
        Open CSV data file in editor via zOpen.
        
        This method delegates to zOpen to open a CSV data file in the configured
        editor. This operation is only supported by the CSV adapter. If table_name
        is not provided, the first table is used.
        
        Args:
            table_name: Optional table name (None = first table)
        
        Returns:
            Result from zOpen.handle() or "error" on failure
        
        Examples:
            # Open first table's CSV file
            zdata.open_csv()
            
            # Open specific table's CSV file
            zdata.open_csv("users")
        
        Notes:
            - Requires zOpen subsystem
            - Only supported by CSV adapter
            - Schema loading required before calling this method
            - CSV path is determined by adapter
        """
        if not self.open:
            self.logger.warning(_ERROR_NO_ZOPEN)
            return _RESULT_ERROR

        if not self.adapter:
            self.logger.error(_ERROR_NO_ADAPTER)
            return _RESULT_ERROR

        # Get CSV path from adapter
        if hasattr(self.adapter, '_get_csv_path'):
            if not table_name:
                # List available tables
                tables = self.list_tables()
                if not tables:
                    self.logger.error(_ERROR_NO_TABLES)
                    return _RESULT_ERROR
                table_name = tables[0]  # Default to first table

            csv_path = str(self.adapter._get_csv_path(table_name))  # pylint: disable=protected-access
            self.logger.info(_LOG_OPENING_CSV, csv_path)
            return self.open.handle({"zOpen": {"path": csv_path}})

        self.logger.error(_ERROR_CSV_NOT_SUPPORTED)
        return _RESULT_ERROR
