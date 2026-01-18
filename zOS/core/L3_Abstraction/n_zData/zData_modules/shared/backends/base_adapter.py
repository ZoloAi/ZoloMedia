# zCLI/subsystems/zData/zData_modules/shared/backends/base_adapter.py
"""
Abstract base class defining the unified interface for all data backend adapters.

This module provides the foundational ABC (Abstract Base Class) that all backend
adapters must implement. It ensures consistency across different storage backends
(SQLite, PostgreSQL, CSV) while allowing backend-specific optimizations.

Architecture Overview
--------------------
The BaseDataAdapter uses the ABC pattern to define a complete database-like interface
that works across diverse backends:

**Design Philosophy:**
- **Unified Interface:** All backends expose identical CRUD/DDL/TCL operations
- **Backend Agnostic:** Client code doesn't need to know the underlying storage
- **Extensible:** New backends can be added by implementing the abstract methods
- **Type Safe:** Full type hints ensure correct usage across the codebase

**Adapter Categories:**
1. **SQL Adapters** (SQLite, PostgreSQL)
   - Extend via SQLAdapter intermediate class
   - Use native SQL with parameterized queries
   - Support transactions, indexes, foreign keys

2. **File Adapters** (CSV)
   - Extend BaseDataAdapter directly
   - Implement database semantics on file storage
   - Use file locking for concurrent access

Abstract Method Categories
--------------------------
The interface is organized into 4 logical groups:

**DDL (Data Definition Language) - 5 methods:**
- create_table(): Create new table with schema
- alter_table(): Modify existing table structure
- drop_table(): Delete table and all data
- table_exists(): Check table existence
- list_tables(): Enumerate all tables

**DML (Data Manipulation Language) - 5 methods:**
- insert(): Add new row
- select(): Query rows with filtering
- update(): Modify existing rows
- delete(): Remove rows
- upsert(): Insert or update (conflict resolution)

**TCL (Transaction Control Language) - 3 methods:**
- begin_transaction(): Start transaction
- commit(): Persist changes
- rollback(): Revert changes

**Metadata & Utilities - 4 methods:**
- connect(): Establish backend connection
- disconnect(): Close connection and cleanup
- get_cursor(): Get/create operation cursor
- map_type(): Map abstract types to backend types

Connection Lifecycle
-------------------
All adapters follow a consistent lifecycle:

1. **Initialization:** `adapter = SQLiteAdapter(config, logger)`
   - Config provides path, label, metadata
   - Logger is optional for debug output

2. **Connection:** `adapter.connect()`
   - Establish connection to backend
   - Initialize cursors/handles
   - Backend-specific setup

3. **Operations:** `adapter.insert()`, `adapter.select()`, etc.
   - All CRUD/DDL/TCL operations available
   - Automatic error handling
   - Transaction support

4. **Disconnection:** `adapter.disconnect()`
   - Close connections gracefully
   - Flush pending operations
   - Cleanup resources

Implementation Guide for Subclasses
-----------------------------------
To implement a new backend adapter:

1. **Inherit from BaseDataAdapter or SQLAdapter**
2. **Implement all @abstractmethod methods** (17 required)
3. **Call super().__init__()** to initialize base config
4. **Use self.logger for debug output** (if provided)
5. **Use module constants** for error messages and config keys
6. **Raise appropriate exceptions** on errors
7. **Test against zData test suite** (37 tests)

Example Implementation (SQLite):

```python
from .base_adapter import BaseDataAdapter

class SQLiteAdapter(BaseDataAdapter):
    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        if self.logger:
            self.logger.info(LOG_CONNECTED, "SQLite", self.db_path)
    
    def insert(self, table, fields, values):
        placeholders = ', '.join(['?'] * len(values))
        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.connection.commit()
        return self.cursor.lastrowid
```

Concrete Helper Methods
----------------------
BaseDataAdapter provides 3 concrete helper methods that subclasses can use:

- **_ensure_directory(path):** Create directory for data storage
- **is_connected():** Check connection status
- **get_connection_info():** Get debug info dict

These helpers don't need to be overridden.

Integration with zData
----------------------
This adapter interface is used by:

- **classical_data.py:** CRUD orchestration for classical paradigm
- **data_operations.py:** High-level operation routing
- **adapter_factory.py:** Dynamic adapter creation
- **adapter_registry.py:** Auto-registration mechanism

Type Mapping
-----------
Subclasses must implement map_type() to convert abstract schema types
to backend-specific types:

- Abstract: str, int, float, bool, datetime, json
- SQLite: TEXT, INTEGER, REAL, INTEGER, TEXT, TEXT
- PostgreSQL: VARCHAR, INTEGER, REAL, BOOLEAN, TIMESTAMP, JSONB
- CSV: stored as strings, parsed on read

See Also
--------
- sql_adapter.py: Intermediate SQL base class
- sqlite_adapter.py: SQLite implementation
- postgresql_adapter.py: PostgreSQL implementation
- csv_adapter.py: CSV file-based implementation
- adapter_factory.py: Factory for creating adapters
"""

from abc import ABC, abstractmethod
from zOS import Dict, List, Optional, Any, Path, Callable

# ============================================================
# Module Constants - Config Keys
# ============================================================

# Configuration keys
_CONFIG_KEY_PATH = "path"
_CONFIG_KEY_LABEL = "label"
_CONFIG_KEY_META = "meta"
_CONFIG_KEY_BACKEND = "backend"
_CONFIG_KEY_OPTIONS = "options"

# Configuration defaults
_DEFAULT_PATH = "."
_DEFAULT_LABEL = "data"

# ============================================================
# Module Constants - Connection States
# ============================================================

_STATE_DISCONNECTED = "disconnected"
_STATE_CONNECTED = "connected"
_STATE_ERROR = "error"

# ============================================================
# Module Constants - Adapter Types
# ============================================================

_ADAPTER_TYPE_SQLITE = "sqlite"
_ADAPTER_TYPE_POSTGRESQL = "postgresql"
_ADAPTER_TYPE_CSV = "csv"

# ============================================================
# Module Constants - Info Keys
# ============================================================

_INFO_KEY_ADAPTER = "adapter"
_INFO_KEY_CONNECTED = "connected"
_INFO_KEY_PATH = "path"
_INFO_KEY_BACKEND = "backend"
_INFO_KEY_STATE = "state"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NOT_CONNECTED = "Adapter not connected to backend"
_ERR_ALREADY_CONNECTED = "Adapter already connected"
_ERR_CONNECTION_FAILED = "Failed to connect to backend: {error}"
_ERR_TABLE_NOT_FOUND = "Table '{table}' does not exist"
_ERR_TABLE_EXISTS = "Table '{table}' already exists"
_ERR_OPERATION_FAILED = "Operation failed: {operation}"
_ERR_TRANSACTION_FAILED = "Transaction operation failed: {operation}"
_ERR_INVALID_CONFIG = "Invalid adapter configuration: {error}"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_INIT_ADAPTER = "Initializing %s adapter with config: %s"
_LOG_BASE_PATH = "Base path: %s, Data label: %s"
_LOG_DIRECTORY_CREATED = "Ensured directory exists: %s"
_LOG_CONNECTED = "Connected to %s backend: %s"
_LOG_DISCONNECTED = "Disconnected from %s backend"
_LOG_CONNECTION_INFO = "Connection info: adapter=%s, connected=%s, path=%s"
_LOG_TABLE_CREATED = "Created table: %s"
_LOG_TABLE_DROPPED = "Dropped table: %s"
_LOG_TABLE_ALTERED = "Altered table: %s"
_LOG_OPERATION_COMPLETE = "Operation complete: %s"
_LOG_TRANSACTION_BEGIN = "Transaction started"
_LOG_TRANSACTION_COMMIT = "Transaction committed"
_LOG_TRANSACTION_ROLLBACK = "Transaction rolled back"

# ============================================================
# Public API
# ============================================================

__all__ = ["BaseDataAdapter"]

class BaseDataAdapter(ABC):  # pylint: disable=unnecessary-pass
    """
    Abstract base class defining unified interface for all data backend adapters.
    
    This ABC ensures all backend implementations (SQLite, PostgreSQL, CSV) provide
    a consistent interface for database-like operations. Subclasses must implement
    18 abstract methods covering DDL, DML, aggregations, TCL, and metadata operations.
    
    Design Pattern
    -------------
    BaseDataAdapter uses the Template Method pattern:
    - Defines the complete interface (abstract methods)
    - Provides concrete helper methods (directory, connection status)
    - Enforces implementation requirements on subclasses
    
    Abstract Methods Required (18 total)
    -----------------------------------
    **Connection & Metadata (4):**
    - connect(): Establish backend connection
    - disconnect(): Close connection
    - get_cursor(): Get/create operation cursor
    - map_type(): Map abstract types to backend types
    
    **DDL - Data Definition (5):**
    - create_table(): Create new table
    - alter_table(): Modify table structure
    - drop_table(): Delete table
    - table_exists(): Check table existence
    - list_tables(): Enumerate tables
    
    **DML - Data Manipulation (5):**
    - insert(): Add row
    - select(): Query rows
    - update(): Modify rows
    - delete(): Remove rows
    - upsert(): Insert or update
    
    **Aggregations (1):**
    - aggregate(): Perform aggregation (count, sum, avg, min, max)
    
    **TCL - Transaction Control (3):**
    - begin_transaction(): Start transaction
    - commit(): Persist changes
    - rollback(): Revert changes
    
    Concrete Helper Methods (3)
    ---------------------------
    BaseDataAdapter provides these ready-to-use methods:
    - _ensure_directory(path): Create directory for storage
    - is_connected(): Check connection status
    - get_connection_info(): Get debug info dict
    
    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dict with path, label, meta, options
    connection : Any
        Backend-specific connection object (set by subclass)
    cursor : Any
        Backend-specific cursor object (set by subclass)
    base_path : Path
        Base directory for data storage
    data_label : str
        Label for data organization (e.g., "users", "products")
    logger : Optional[Any]
        Logger instance for debug output
    
    Example Subclass Implementation
    -------------------------------
    ```python
    class SQLiteAdapter(BaseDataAdapter):
        def connect(self):
            db_path = self.base_path / f"{self.data_label}.db"
            self.connection = sqlite3.connect(db_path)
            self.cursor = self.connection.cursor()
        
        def insert(self, table, fields, values):
            placeholders = ', '.join(['?'] * len(values))
            sql = f"INSERT INTO {table} (...) VALUES ({placeholders})"
            self.cursor.execute(sql, values)
            self.connection.commit()
            return self.cursor.lastrowid
    ```
    
    See Also
    --------
    - sql_adapter.py: SQL base class extending this ABC
    - sqlite_adapter.py: SQLite implementation
    - postgresql_adapter.py: PostgreSQL implementation
    - csv_adapter.py: CSV file-based implementation
    """

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[Any] = None
    ) -> None:
        """
        Initialize BaseDataAdapter with configuration and optional logger.
        
        Args:
            config: Configuration dictionary with backend settings. Required keys:
                - path: Base directory for data storage (default: ".")
                - label: Data label for organization (default: "data")
                Optional keys:
                - meta: Additional metadata dict
                - backend: Backend type (sqlite, postgresql, csv)
                - options: Backend-specific options dict
            
            logger: Optional logger instance for debug output. If provided,
                   logs initialization details, connection events, and operations.
        
        Attributes Set:
            self.config: Stored config dict
            self.connection: Initialized to None (set by connect())
            self.cursor: Initialized to None (set by get_cursor())
            self.base_path: Path object from config['path']
            self.data_label: String from config['label']
            self.logger: Stored logger instance
        
        Example:
            Basic initialization:
                >>> config = {"path": "/data/db", "label": "users"}
                >>> adapter = SQLiteAdapter(config)
            
            With logger:
                >>> config = {"path": "/data/db", "label": "users"}
                >>> adapter = SQLiteAdapter(config, logger=my_logger)
                >>> # Logger will output debug messages for all operations
        
        Notes:
            - config['path'] defaults to "." if not provided
            - config['label'] defaults to "data" if not provided
            - Subclasses should call super().__init__(config, logger) first
            - Connection is NOT established during __init__ (call connect())
        """
        self.config = config
        self.connection = None
        self.cursor = None
        self.base_path = Path(config.get(_CONFIG_KEY_PATH, _DEFAULT_PATH))
        self.data_label = config.get(_CONFIG_KEY_LABEL, _DEFAULT_LABEL)
        self.logger = logger

        if self.logger:
            self.logger.debug(
                _LOG_INIT_ADAPTER,
                self.__class__.__name__, config
            )
            self.logger.debug(_LOG_BASE_PATH, self.base_path, self.data_label)
    
    # ============================================================
    # DRY Helper Methods (Reduce Duplication Across Adapters)
    # ============================================================
    
    def _log(self, level: str, message: str, *args) -> None:
        """
        Log message if logger is available (DRY helper).
        
        Eliminates 147 occurrences of "if self.logger:" checks across all adapters.
        
        Args:
            level: Log level ('debug', 'info', 'warning', 'error')
            message: Log message with format placeholders
            *args: Arguments for message formatting
        
        Example:
            >>> # Instead of:
            >>> if self.logger:
            >>>     self.logger.info("Connected to %s", backend)
            >>> 
            >>> # Use:
            >>> self._log('info', "Connected to %s", backend)
        
        Notes:
            - No-op if logger not available
            - Supports all standard log levels
            - Uses getattr for dynamic method lookup
        """
        if self.logger:
            getattr(self.logger, level)(message, *args)
    
    def _execute_with_error_handling(
        self,
        operation_name: str,
        operation_fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with standardized error handling (DRY helper).
        
        Eliminates 66 try-catch blocks across all adapters by providing
        a centralized error handling pattern with logging.
        
        Args:
            operation_name: Human-readable operation description (for logging)
            operation_fn: Function/method to execute
            *args: Positional arguments for operation_fn
            **kwargs: Keyword arguments for operation_fn
        
        Returns:
            Result from operation_fn, or None if exception occurs
        
        Example:
            >>> # Instead of:
            >>> try:
            >>>     result = self.cursor.execute(sql)
            >>>     return result
            >>> except Exception as e:
            >>>     if self.logger:
            >>>         self.logger.error("Query failed: %s", e)
            >>>     return None
            >>> 
            >>> # Use:
            >>> return self._execute_with_error_handling(
            >>>     "Query execution",
            >>>     self.cursor.execute,
            >>>     sql
            >>> )
        
        Notes:
            - Catches all exceptions
            - Logs errors automatically
            - Returns None on failure (caller handles)
            - Preserves stack traces in logs
        """
        try:
            return operation_fn(*args, **kwargs)
        except Exception as e:
            self._log('error', f"{operation_name} failed: %s", e)
            return None
    
    # ============================================================
    # Connection & Metadata (Abstract Methods)
    # ============================================================

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the backend storage.
        
        This method must initialize self.connection and self.cursor (if applicable)
        with backend-specific connection objects. Should be idempotent if already connected.
        
        Implementation Requirements:
            - Set self.connection to backend connection object
            - Set self.cursor to backend cursor (if applicable)
            - Perform backend-specific initialization (pragmas, settings)
            - Create necessary directories or files
            - Log connection status using self.logger
        
        Raises:
            ConnectionError: If connection fails
            FileNotFoundError: If path doesn't exist (file backends)
        
        Example (SQLite):
            >>> def connect(self):
            ...     db_path = self.base_path / f"{self.data_label}.db"
            ...     self._ensure_directory(self.base_path)
            ...     self.connection = sqlite3.connect(db_path)
            ...     self.cursor = self.connection.cursor()
        """

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the backend storage and cleanup resources.
        
        This method must gracefully close connections, commit pending transactions,
        and release any held resources. Should be idempotent if already disconnected.
        
        Implementation Requirements:
            - Commit any pending transactions (if applicable)
            - Close cursor objects
            - Close connection objects
            - Set self.connection and self.cursor to None
            - Log disconnection using self.logger
        
        Raises:
            RuntimeError: If disconnect fails (rare)
        
        Example (SQLite):
            >>> def disconnect(self):
            ...     if self.connection:
            ...         self.connection.commit()
            ...         self.connection.close()
            ...         self.connection = None
            ...         self.cursor = None
        """

    @abstractmethod
    def get_cursor(self) -> Any:
        """
        Get or create cursor for executing database operations.
        
        Returns an active cursor object for executing queries. For backends
        that don't use cursors (e.g., CSV), may return self or a handler object.
        
        Implementation Requirements:
            - Return active cursor object
            - Create new cursor if none exists
            - Ensure cursor is ready for operations
        
        Returns:
            Backend-specific cursor object (sqlite3.Cursor, psycopg2 cursor, etc.)
        
        Raises:
            RuntimeError: If not connected to backend
        
        Example (SQLite):
            >>> def get_cursor(self):
            ...     if not self.cursor:
            ...         self.cursor = self.connection.cursor()
            ...     return self.cursor
        """

    @abstractmethod
    def map_type(self, abstract_type: str) -> str:
        """
        Map abstract schema type to backend-specific type.
        
        Converts zCLI's abstract type system (str, int, float, bool, datetime, json)
        to backend-specific type definitions (TEXT, INTEGER, VARCHAR, etc.).
        
        Args:
            abstract_type: Abstract type from schema (str, int, float, bool, datetime, json)
        
        Returns:
            Backend-specific type string
        
        Implementation Requirements:
            - Support all abstract types: str, int, float, bool, datetime, json
            - Return backend's native type representation
            - Handle type-specific constraints (size, precision)
        
        Example (SQLite):
            >>> def map_type(self, abstract_type):
            ...     mapping = {
            ...         'str': 'TEXT', 'int': 'INTEGER', 'float': 'REAL',
            ...         'bool': 'INTEGER', 'datetime': 'TEXT', 'json': 'TEXT'
            ...     }
            ...     return mapping.get(abstract_type, 'TEXT')
        
        Example (PostgreSQL):
            >>> def map_type(self, abstract_type):
            ...     mapping = {
            ...         'str': 'VARCHAR(255)', 'int': 'INTEGER', 'float': 'REAL',
            ...         'bool': 'BOOLEAN', 'datetime': 'TIMESTAMP', 'json': 'JSONB'
            ...     }
            ...     return mapping.get(abstract_type, 'TEXT')
        """
    
    # ============================================================
    # DDL - Data Definition Language (Abstract Methods)
    # ============================================================

    @abstractmethod
    def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create new table with specified schema.
        
        Args:
            table_name: Name of table to create
            schema: Schema definition dict with field definitions:
                {
                    'field_name': {
                        'type': 'str',           # Abstract type
                        'required': True,        # NOT NULL constraint
                        'pk': False,             # Primary key
                        'default': None,         # Default value
                        'unique': False          # Unique constraint
                    }
                }
        
        Implementation Requirements:
            - Convert abstract types using map_type()
            - Apply constraints (NOT NULL, PRIMARY KEY, UNIQUE, DEFAULT)
            - Handle composite primary keys if multiple pk=True
            - Create indexes for pk and unique fields
            - Log table creation using self.logger
        
        Raises:
            ValueError: If table already exists
            RuntimeError: If creation fails
        
        Example (SQLite):
            >>> def create_table(self, table_name, schema):
            ...     fields = []
            ...     for name, props in schema.items():
            ...         sql_type = self.map_type(props['type'])
            ...         constraints = []
            ...         if props.get('pk'): constraints.append('PRIMARY KEY')
            ...         if props.get('required'): constraints.append('NOT NULL')
            ...         fields.append(f"{name} {sql_type} {' '.join(constraints)}")
            ...     sql = f"CREATE TABLE {table_name} ({', '.join(fields)})"
            ...     self.cursor.execute(sql)
        """

    @abstractmethod
    def alter_table(self, table_name: str, changes: Dict[str, Any]) -> None:
        """
        Alter existing table structure (add/drop/modify columns).
        
        Args:
            table_name: Name of table to alter
            changes: Dict describing structural changes:
                {
                    'add': {'field_name': {'type': 'str', 'required': False}},
                    'drop': ['field_name1', 'field_name2'],
                    'modify': {'field_name': {'type': 'int'}}
                }
        
        Implementation Requirements:
            - Support adding new columns (with defaults for existing rows)
            - Support dropping columns (if backend allows)
            - Support modifying column types (if backend allows)
            - Handle backend limitations gracefully (e.g., SQLite limited ALTER)
            - Log alterations using self.logger
        
        Raises:
            ValueError: If table doesn't exist
            RuntimeError: If alteration fails
            NotImplementedError: If backend doesn't support operation
        
        Notes:
            - Some backends (SQLite) have limited ALTER support
            - May require table recreation for complex changes
        """

    @abstractmethod
    def drop_table(self, table_name: str) -> None:
        """
        Drop table and all its data permanently.
        
        Args:
            table_name: Name of table to drop
        
        Implementation Requirements:
            - Remove table and all data permanently
            - Handle foreign key constraints (cascade if needed)
            - Succeed silently if table doesn't exist (or raise based on policy)
            - Log table drop using self.logger
        
        Raises:
            ValueError: If table doesn't exist (optional, backend-specific)
            RuntimeError: If drop fails
        
        Example (SQLite):
            >>> def drop_table(self, table_name):
            ...     sql = f"DROP TABLE IF EXISTS {table_name}"
            ...     self.cursor.execute(sql)
            ...     self.connection.commit()
        """

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists in backend.
        
        Args:
            table_name: Name of table to check
        
        Returns:
            True if table exists, False otherwise
        
        Implementation Requirements:
            - Query backend metadata for table existence
            - Case-sensitive or case-insensitive based on backend
            - Don't raise exceptions, return boolean
        
        Example (SQLite):
            >>> def table_exists(self, table_name):
            ...     sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            ...     result = self.cursor.execute(sql, (table_name,)).fetchone()
            ...     return result is not None
        """

    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        List all table names in backend.
        
        Returns:
            List of table name strings
        
        Implementation Requirements:
            - Query backend metadata for all tables
            - Exclude system tables
            - Return empty list if no tables exist
            - Sort table names alphabetically (optional)
        
        Example (SQLite):
            >>> def list_tables(self):
            ...     sql = "SELECT name FROM sqlite_master WHERE type='table'"
            ...     results = self.cursor.execute(sql).fetchall()
            ...     return [row[0] for row in results]
        """

    # ============================================================
    # DML - Data Manipulation Language (Abstract Methods)
    # ============================================================

    @abstractmethod
    def insert(
        self,
        table: str,
        fields: List[str],
        values: List[Any]
    ) -> Any:
        """
        Insert new row into table.
        
        Args:
            table: Name of table to insert into
            fields: List of field names (ordered)
            values: List of values (ordered, must match fields)
        
        Returns:
            Row ID of inserted row (int for SQL backends, dict for CSV)
        
        Implementation Requirements:
            - Insert single row with provided field/value pairs
            - Auto-increment primary keys if applicable
            - Validate field/value count match
            - Commit transaction (or buffer for batch)
            - Log insert operation using self.logger
        
        Raises:
            ValueError: If table doesn't exist or field mismatch
            RuntimeError: If insert fails
        
        Example (SQLite):
            >>> def insert(self, table, fields, values):
            ...     placeholders = ', '.join(['?'] * len(values))
            ...     field_list = ', '.join(fields)
            ...     sql = f"INSERT INTO {table} ({field_list}) VALUES ({placeholders})"
            ...     self.cursor.execute(sql, values)
            ...     self.connection.commit()
            ...     return self.cursor.lastrowid
        """

    @abstractmethod
    def select(
        self,
        table: str,
        fields: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Select rows from table with optional filtering.
        
        Args:
            table: Name of table to select from
            fields: List of field names to return (None = all fields)
            **kwargs: Query options:
                - where: WHERE clause dict (e.g., {"age": 25, "city": "NYC"})
                - order_by: Field name to sort by
                - limit: Maximum number of rows
                - offset: Number of rows to skip
        
        Returns:
            List of dicts, each dict representing one row:
            [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        
        Implementation Requirements:
            - Return all rows if no WHERE clause
            - Support filtering with WHERE dict (key=value pairs)
            - Support ORDER BY if provided
            - Support LIMIT and OFFSET for pagination
            - Return empty list if no matches
        
        Example (SQLite):
            >>> def select(self, table, fields=None, **kwargs):
            ...     field_list = ', '.join(fields) if fields else '*'
            ...     sql = f"SELECT {field_list} FROM {table}"
            ...     if 'where' in kwargs:
            ...         conditions = ' AND '.join([f"{k}=?" for k in kwargs['where'].keys()])
            ...         sql += f" WHERE {conditions}"
            ...     results = self.cursor.execute(sql, tuple(kwargs['where'].values()))
            ...     return [dict(row) for row in results.fetchall()]
        """

    @abstractmethod
    def update(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        where: Dict[str, Any]
    ) -> int:
        """
        Update existing rows in table.
        
        Args:
            table: Name of table to update
            fields: List of field names to update (ordered)
            values: List of new values (ordered, must match fields)
            where: WHERE clause dict for filtering (e.g., {"id": 5})
        
        Returns:
            Number of rows updated
        
        Implementation Requirements:
            - Update only rows matching WHERE clause
            - Support multiple field updates in single operation
            - Commit transaction after update
            - Return count of affected rows
            - Log update operation using self.logger
        
        Raises:
            ValueError: If table doesn't exist or no WHERE clause
            RuntimeError: If update fails
        
        Example (SQLite):
            >>> def update(self, table, fields, values, where):
            ...     set_clause = ', '.join([f"{f}=?" for f in fields])
            ...     where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
            ...     sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            ...     params = list(values) + list(where.values())
            ...     self.cursor.execute(sql, params)
            ...     self.connection.commit()
            ...     return self.cursor.rowcount
        """

    @abstractmethod
    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Delete rows from table.
        
        Args:
            table: Name of table to delete from
            where: WHERE clause dict for filtering (e.g., {"id": 5})
        
        Returns:
            Number of rows deleted
        
        Implementation Requirements:
            - Delete only rows matching WHERE clause
            - Require WHERE clause to prevent accidental full delete
            - Commit transaction after delete
            - Return count of deleted rows
            - Log delete operation using self.logger
        
        Raises:
            ValueError: If table doesn't exist or no WHERE clause
            RuntimeError: If delete fails
        
        Example (SQLite):
            >>> def delete(self, table, where):
            ...     where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
            ...     sql = f"DELETE FROM {table} WHERE {where_clause}"
            ...     self.cursor.execute(sql, tuple(where.values()))
            ...     self.connection.commit()
            ...     return self.cursor.rowcount
        """

    @abstractmethod
    def upsert(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        conflict_fields: List[str]
    ) -> Any:
        """
        Insert row or update if conflict on specified fields (UPSERT).
        
        Args:
            table: Name of table
            fields: List of field names (ordered)
            values: List of values (ordered, must match fields)
            conflict_fields: Fields to check for conflicts (usually pk or unique)
        
        Returns:
            Row ID of inserted/updated row
        
        Implementation Requirements:
            - Insert row if conflict_fields don't match existing row
            - Update row if conflict_fields match existing row
            - Handle backend-specific UPSERT syntax (INSERT...ON CONFLICT, REPLACE)
            - Commit transaction
            - Return row ID
        
        Raises:
            ValueError: If table doesn't exist
            RuntimeError: If operation fails
        
        Example (SQLite):
            >>> def upsert(self, table, fields, values, conflict_fields):
            ...     placeholders = ', '.join(['?'] * len(values))
            ...     field_list = ', '.join(fields)
            ...     conflict_list = ', '.join(conflict_fields)
            ...     update_clause = ', '.join([f"{f}=excluded.{f}" for f in fields])
            ...     sql = f"INSERT INTO {table} ({field_list}) VALUES ({placeholders})"
            ...     sql += f" ON CONFLICT({conflict_list}) DO UPDATE SET {update_clause}"
            ...     self.cursor.execute(sql, values)
            ...     self.connection.commit()
            ...     return self.cursor.lastrowid
        """

    @abstractmethod
    def aggregate(
        self,
        table: str,
        function: str,
        field: Optional[str] = None,
        where: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None
    ) -> Any:
        """
        Perform aggregation function on table data.
        
        Supported aggregate functions:
        - count: Count rows (field optional, defaults to *)
        - sum: Sum numeric field values
        - avg: Average numeric field values
        - min: Minimum field value
        - max: Maximum field value
        
        Args:
            table: Name of table
            function: Aggregation function (count, sum, avg, min, max)
            field: Field name to aggregate (required for sum/avg/min/max, optional for count)
            where: Optional WHERE clause dictionary for filtering
            group_by: Optional field name to group by
        
        Returns:
            Scalar value (int/float) for simple aggregation
            Dict for GROUP BY aggregation {group_value: aggregate_value}
        
        Implementation Requirements:
            - Validate function name (count/sum/avg/min/max)
            - Build backend-specific query (SQL: SELECT COUNT(*), CSV: df.count())
            - Apply WHERE filtering if provided
            - Handle GROUP BY if provided
            - Return scalar for simple aggregation, dict for grouped
            - Handle empty results gracefully (return 0 for count, None for others)
        
        Raises:
            ValueError: If invalid function or missing required field
            RuntimeError: If query execution fails
        
        Example (SQLite):
            >>> def aggregate(self, table, function, field=None, where=None, group_by=None):
            ...     agg_field = field if field else '*'
            ...     sql = f"SELECT {function.upper()}({agg_field}) FROM {table}"
            ...     if where:
            ...         sql += f" WHERE {self._build_where_clause(where)}"
            ...     result = self.cursor.execute(sql).fetchone()
            ...     return result[0] if result else 0
        
        Example (pandas):
            >>> def aggregate(self, table, function, field=None, where=None, group_by=None):
            ...     df = self._load_table(table)
            ...     if where:
            ...         df = df[self._create_where_mask(df, where)]
            ...     if function == 'count':
            ...         return len(df)
            ...     return df[field].sum()  # or .mean(), .min(), .max()
        """

    # ============================================================
    # TCL - Transaction Control Language (Abstract Methods)
    # ============================================================

    @abstractmethod
    def begin_transaction(self) -> None:
        """
        Begin new transaction.
        
        Implementation Requirements:
            - Start new transaction context
            - Disable auto-commit mode
            - Nest transactions if backend supports it
            - Log transaction start using self.logger
        
        Raises:
            RuntimeError: If transaction start fails
        
        Example (SQLite):
            >>> def begin_transaction(self):
            ...     self.cursor.execute("BEGIN TRANSACTION")
            ...     if self.logger:
            ...         self.logger.debug(LOG_TRANSACTION_BEGIN)
        
        Notes:
            - Must be followed by commit() or rollback()
            - Some backends auto-begin transactions
        """

    @abstractmethod
    def commit(self) -> None:
        """
        Commit current transaction (persist all changes).
        
        Implementation Requirements:
            - Persist all pending changes to storage
            - End current transaction context
            - Re-enable auto-commit mode (if applicable)
            - Log commit using self.logger
        
        Raises:
            RuntimeError: If commit fails
        
        Example (SQLite):
            >>> def commit(self):
            ...     self.connection.commit()
            ...     if self.logger:
            ...         self.logger.debug(LOG_TRANSACTION_COMMIT)
        
        Notes:
            - Should be called after successful operations
            - Some backends commit automatically
        """

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback current transaction (revert all changes).
        
        Implementation Requirements:
            - Revert all pending changes since begin_transaction()
            - End current transaction context
            - Re-enable auto-commit mode (if applicable)
            - Log rollback using self.logger
        
        Raises:
            RuntimeError: If rollback fails (rare)
        
        Example (SQLite):
            >>> def rollback(self):
            ...     self.connection.rollback()
            ...     if self.logger:
            ...         self.logger.debug(LOG_TRANSACTION_ROLLBACK)
        
        Notes:
            - Should be called on operation errors
            - Restores database to pre-transaction state
        """
    
    # ============================================================
    # Concrete Helper Methods
    # ============================================================

    def _ensure_directory(self, path: Optional[Path] = None) -> None:
        """
        Ensure directory exists for data storage (concrete helper).
        
        Creates directory and all parent directories if they don't exist.
        Safe to call multiple times (idempotent).
        
        Args:
            path: Directory path to create (default: self.base_path)
        
        Example:
            >>> self._ensure_directory()  # Creates self.base_path
            >>> self._ensure_directory(Path("/data/custom"))  # Creates custom path
        
        Notes:
            - Used by subclasses during connect()
            - Creates parent directories as needed
            - Logs directory creation if logger available
        """
        target_path = Path(path) if path else self.base_path
        target_path.mkdir(parents=True, exist_ok=True)
        if self.logger:
            self.logger.debug(_LOG_DIRECTORY_CREATED, target_path)

    def is_connected(self) -> bool:
        """
        Check if adapter is currently connected to backend (concrete helper).
        
        Returns:
            True if connected, False if disconnected
        
        Example:
            >>> adapter.is_connected()
            False
            >>> adapter.connect()
            >>> adapter.is_connected()
            True
        
        Notes:
            - Checks if self.connection is not None
            - Does not verify connection is actually active
            - Fast check for basic connection status
        """
        return self.connection is not None

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information dict for logging/debugging (concrete helper).
        
        Returns:
            Dict with connection details:
            {
                "adapter": "SQLiteAdapter",
                "connected": True,
                "path": "/data/db",
                "backend": "sqlite",
                "state": "connected"
            }
        
        Example:
            >>> info = adapter.get_connection_info()
            >>> print(f"Using {info['adapter']}, connected: {info['connected']}")
        
        Notes:
            - Useful for logging and debugging
            - Safe to call at any time
            - Returns current state snapshot
        """
        return {
            _INFO_KEY_ADAPTER: self.__class__.__name__,
            _INFO_KEY_CONNECTED: self.is_connected(),
            _INFO_KEY_PATH: self.config.get(_CONFIG_KEY_PATH),
            _INFO_KEY_BACKEND: self.config.get(_CONFIG_KEY_BACKEND),
            _INFO_KEY_STATE: _STATE_CONNECTED if self.is_connected() else _STATE_DISCONNECTED,
        }
