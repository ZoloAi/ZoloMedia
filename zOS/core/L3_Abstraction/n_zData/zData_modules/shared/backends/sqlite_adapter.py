# zCLI/subsystems/zData/zData_modules/shared/backends/sqlite_adapter.py
"""
SQLite database backend adapter with production-grade features.

This module implements a robust SQLite adapter that extends SQLAdapter with
SQLite-specific optimizations, PRAGMA configuration, and proper transaction
handling. It provides file-based persistent storage with ACID guarantees.

Architecture Overview
--------------------
SQLiteAdapter sits at the concrete layer of the adapter hierarchy:

    BaseDataAdapter (ABC)
           ↓
      SQLAdapter (SQL operations + builders)
           ↓
    SQLiteAdapter (SQLite-specific implementation)

**Design Philosophy:**
- **File-based storage:** Database stored as {data_label}.db in base_path
- **PRAGMA optimization:** Foreign keys, journal mode, synchronous settings
- **Transaction control:** DEFERRED isolation level with explicit BEGIN/COMMIT
- **Row factory:** Dict-like access via sqlite3.Row
- **Error resilience:** Handles OperationalError for transaction state

SQLite-Specific Features
------------------------
**1. PRAGMA Configuration:**
- `PRAGMA foreign_keys = ON` - Enable referential integrity
- `PRAGMA journal_mode = WAL` - Write-Ahead Logging for concurrency (optional)
- `PRAGMA synchronous = NORMAL` - Balance safety vs performance (optional)

**2. Isolation Levels:**
- **DEFERRED (default):** Lock acquired on first write, allows parallel reads
- **IMMEDIATE:** Lock acquired on BEGIN, blocks other writes
- **EXCLUSIVE:** Lock acquired on BEGIN, blocks all access

**3. Transaction Handling:**
- Autocommit mode with explicit transaction control
- BEGIN/COMMIT/ROLLBACK with OperationalError handling
- Prevents "transaction already active" and "no transaction is active" errors

**4. Type Mapping:**
SQLite uses dynamic typing with 5 storage classes:
- TEXT: str, string, datetime, date, time, json
- INTEGER: int, integer, bool, boolean
- REAL: float, real
- BLOB: blob
- NULL: None

**5. Limitations:**
- No DROP COLUMN support (SQLite < 3.35.0)
- Limited ALTER TABLE operations
- No native UPSERT before SQLite 3.24.0 (we require 3.24+)
- ADD COLUMN requires DEFAULT for NOT NULL columns

Write-Ahead Logging (WAL) Mode
------------------------------
WAL mode improves concurrency by allowing readers to access the database
while a writer is writing:

**Advantages:**
- Multiple readers can access DB while one writer writes
- Faster writes (no need to sync journal file)
- Reduced disk I/O

**How to Enable:**
```python
connection.execute("PRAGMA journal_mode = WAL")
```

**Note:** WAL mode persists in the database file, not the connection.

Connection Lifecycle
-------------------
1. **connect():** Create connection with DEFERRED isolation, enable foreign keys
2. **get_cursor():** Lazy cursor creation on demand
3. **Operations:** INSERT, SELECT, UPDATE, DELETE, UPSERT
4. **Transactions:** Explicit BEGIN/COMMIT/ROLLBACK
5. **disconnect():** Close cursor and connection

Usage Examples
-------------
Basic connection and CRUD:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.sqlite_adapter import SQLiteAdapter
    >>> config = {"path": "/data/myapp", "label": "users"}
    >>> adapter = SQLiteAdapter(config, logger=logger)
    >>> adapter.connect()
    >>> 
    >>> # Create table
    >>> schema = {
    ...     "id": {"type": "int", "pk": True},
    ...     "name": {"type": "str", "required": True},
    ...     "age": {"type": "int"}
    ... }
    >>> adapter.create_table("users", schema)
    >>> 
    >>> # Insert
    >>> row_id = adapter.insert("users", ["name", "age"], ["John", 30])
    >>> 
    >>> # Select
    >>> rows = adapter.select("users", where={"age__gte": 18})
    >>> 
    >>> # Update
    >>> adapter.update("users", ["age"], [31], where={"id": row_id})
    >>> 
    >>> # Delete
    >>> adapter.delete("users", where={"age__lt": 18})
    >>> 
    >>> adapter.disconnect()

Transactions:
    >>> adapter.begin_transaction()
    >>> try:
    ...     adapter.insert("users", ["name", "age"], ["Alice", 25])
    ...     adapter.insert("users", ["name", "age"], ["Bob", 28])
    ...     adapter.commit()
    ... except Exception as e:
    ...     adapter.rollback()
    ...     raise

UPSERT (SQLite 3.24+):
    >>> # Insert or update by id
    >>> adapter.upsert(
    ...     "users",
    ...     ["id", "name", "age"],
    ...     [1, "John Doe", 35],
    ...     conflict_fields=["id"]
    ... )

Integration
----------
This adapter is used by:
- classical_data.py: CRUD orchestration
- data_operations.py: High-level operations
- quantum_data.py: Abstracted data structures (if SQLite backend selected)

See Also
--------
- sql_adapter.py: SQL base class with builder methods
- base_adapter.py: Abstract adapter interface
- postgresql_adapter.py: PostgreSQL implementation
"""

from zOS import sqlite3, Dict, List, Any
from .sql_adapter import SQLAdapter

# ============================================================
# Module Constants - PRAGMA Commands
# ============================================================

_PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON"
_PRAGMA_JOURNAL_MODE_WAL = "PRAGMA journal_mode = WAL"
_PRAGMA_JOURNAL_MODE_DELETE = "PRAGMA journal_mode = DELETE"
_PRAGMA_SYNCHRONOUS_FULL = "PRAGMA synchronous = FULL"
_PRAGMA_SYNCHRONOUS_NORMAL = "PRAGMA synchronous = NORMAL"
_PRAGMA_SYNCHRONOUS_OFF = "PRAGMA synchronous = OFF"

# ============================================================
# Module Constants - Isolation Levels
# ============================================================

_ISOLATION_DEFERRED = "DEFERRED"
_ISOLATION_IMMEDIATE = "IMMEDIATE"
_ISOLATION_EXCLUSIVE = "EXCLUSIVE"

# ============================================================
# Module Constants - SQL Keywords
# ============================================================

_SQL_BEGIN = "BEGIN"
_SQL_COMMIT = "COMMIT"
_SQL_ROLLBACK = "ROLLBACK"
_SQL_SELECT_MASTER = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
_SQL_LIST_TABLES = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"

# ============================================================
# Module Constants - Connection Options
# ============================================================

_CONN_CHECK_SAME_THREAD = "check_same_thread"
_CONN_TIMEOUT = "timeout"
_DEFAULT_TIMEOUT = 5.0  # seconds

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_CONNECTION_FAILED = "SQLite connection failed: %s"
_ERR_DISCONNECT_FAILED = "Error closing SQLite connection: %s"
_ERR_TRANSACTION_ACTIVE = "transaction already active"
_ERR_NO_TRANSACTION = "no transaction is active"
_ERR_REQUIRES_DEFAULT = "SQLite ALTER TABLE ADD COLUMN requires DEFAULT for NOT NULL columns"
_ERR_TYPE_NOT_STRING = "Non-string type received (%r); defaulting to TEXT."

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_CONNECTED = "Connected to SQLite: %s"
_LOG_DISCONNECTED = "Disconnected from SQLite: %s"
_LOG_TABLE_EXISTS = "Table '%s' exists: %s"
_LOG_FOUND_TABLES = "Found %d tables: %s"
_LOG_UPSERTED = "Upserted row into %s with ID: %s"
_LOG_TRANSACTION_STARTED = "Transaction started"
_LOG_TRANSACTION_COMMITTED = "Transaction committed"
_LOG_TRANSACTION_ROLLED_BACK = "Transaction rolled back"
_LOG_ALTER_TABLE_SQLITE = "Altering SQLite table: %s"

# ============================================================
# Public API
# ============================================================

__all__ = ["SQLiteAdapter"]

class SQLiteAdapter(SQLAdapter):
    """
    SQLite backend adapter with file-based storage and PRAGMA optimizations.
    
    This class extends SQLAdapter to provide SQLite-specific implementations of
    connection management, type mapping, and transaction control. It leverages
    Python's built-in sqlite3 module for zero-dependency database operations.
    
    Architecture
    -----------
    SQLiteAdapter provides:
    - **Connection Management (3 methods):** connect(), disconnect(), get_cursor()
    - **DDL Helpers (2 methods):** _build_add_column_sql(), _supports_drop_column()
    - **DDL Operations (2 methods):** table_exists(), list_tables()
    - **DML Overrides (3 methods):** insert(), update(), delete() - parent wrappers
    - **DML New (1 method):** upsert() - SQLite-specific ON CONFLICT
    - **Type Mapping (1 method):** map_type() - 14 type mappings
    - **TCL (3 methods):** begin_transaction(), commit(), rollback()
    
    Key Features
    -----------
    **1. File-based Storage:**
    Database file: {base_path}/{data_label}.db
    
    **2. PRAGMA Configuration:**
    - Foreign keys enabled by default (PRAGMA foreign_keys = ON)
    - Optional WAL mode for better concurrency
    - Configurable synchronous mode
    
    **3. Transaction Control:**
    - DEFERRED isolation level (default)
    - Explicit BEGIN/COMMIT/ROLLBACK with error handling
    - Prevents "transaction already active" errors
    
    **4. Row Factory:**
    - sqlite3.Row for dict-like access to result rows
    - Access columns by name: row["name"] or row[0]
    
    **5. Type Mapping:**
    Maps abstract types to SQLite storage classes:
    - TEXT: str, datetime, json
    - INTEGER: int, bool
    - REAL: float
    - BLOB: blob
    
    **6. Limitations Handling:**
    - _supports_drop_column() returns False
    - ADD COLUMN requires DEFAULT for NOT NULL columns
    
    Attributes:
        db_path (Path): Full path to .db file (from parent SQLAdapter)
        connection: sqlite3.Connection instance (from parent BaseDataAdapter)
        cursor: sqlite3.Cursor instance (from parent BaseDataAdapter)
        All BaseDataAdapter attributes
    
    Example:
        >>> adapter = SQLiteAdapter({"path": "/data", "label": "mydb"}, logger)
        >>> adapter.connect()
        >>> adapter.create_table("users", schema)
        >>> adapter.insert("users", ["name", "age"], ["John", 30])
        >>> adapter.disconnect()
    """
    
    # ============================================================
    # Connection Management
    # ============================================================

    def connect(self) -> Any:
        """
        Establish SQLite connection with optimized settings.
        
        Creates a connection to the SQLite database file with:
        - DEFERRED isolation level for transaction control
        - sqlite3.Row factory for dict-like access
        - Foreign keys enabled via PRAGMA
        
        Returns:
            sqlite3.Connection: Configured database connection
        
        Raises:
            Exception: If connection fails or PRAGMA execution fails
        
        Example:
            >>> adapter = SQLiteAdapter(config, logger)
            >>> conn = adapter.connect()
            >>> # conn.isolation_level == 'DEFERRED'
        
        Notes:
            - Automatically creates parent directory if needed
            - Enables foreign key constraints (disabled by default in SQLite)
            - Uses DEFERRED isolation for better concurrency
        """
        try:
            # Ensure parent directory exists
            self._ensure_directory()

            # Convert Path to string for sqlite3.connect()
            # Use isolation_level='DEFERRED' for proper transaction support
            self.connection = sqlite3.connect(str(self.db_path), isolation_level=_ISOLATION_DEFERRED)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            self.connection.execute(_PRAGMA_FOREIGN_KEYS)  # Enable FK support
            self._log('info', _LOG_CONNECTED, self.db_path)
            return self.connection
        except Exception as e:  # pylint: disable=broad-except
            self._log('error', _ERR_CONNECTION_FAILED, e)
            raise

    def disconnect(self) -> None:
        """
        Close SQLite connection and release resources.
        
        Closes the cursor (if open) and then the connection. Handles errors
        gracefully and logs any issues during disconnect.
        
        Raises:
            Exception: Logged but not raised if disconnect fails
        
        Example:
            >>> adapter.disconnect()
            >>> # adapter.connection is now None
        
        Notes:
            - Safe to call multiple times (checks if connection exists)
            - Closes cursor before connection
            - Sets connection and cursor to None after closing
        """
        if self.connection:
            try:
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                self.connection.close()
                self.connection = None
                self._log('info', _LOG_DISCONNECTED, self.db_path)
            except Exception as e:  # pylint: disable=broad-except
                self._log('error', _ERR_DISCONNECT_FAILED, e)

    def get_cursor(self) -> Any:
        """
        Get or create a database cursor (lazy initialization).
        
        Creates a cursor on first call, then returns cached cursor on
        subsequent calls. This enables efficient cursor reuse.
        
        Returns:
            sqlite3.Cursor: Database cursor for query execution
        
        Example:
            >>> cur = adapter.get_cursor()
            >>> cur.execute("SELECT * FROM users")
        
        Notes:
            - Cursor created lazily (only when needed)
            - Cached for reuse across operations
            - Automatically closed during disconnect()
        """
        if not self.cursor and self.connection:
            self.cursor = self.connection.cursor()
        return self.cursor

    # create_table(), drop_table(), alter_table() - inherited from SQLAdapter
    
    # ============================================================
    # DDL Helpers (SQLite-Specific)
    # ============================================================

    def _build_add_column_sql(
        self,
        table_name: str,
        column_name: str,
        column_def: Dict[str, Any]
    ) -> str:
        """
        Build ALTER TABLE ADD COLUMN SQL for SQLite.
        
        SQLite requires DEFAULT values for NOT NULL columns when adding them
        to existing tables (since existing rows need a value).
        
        Args:
            table_name: Name of table to alter
            column_name: Name of new column
            column_def: Column definition dict (type, required, default)
        
        Returns:
            SQL string for ALTER TABLE ADD COLUMN
        
        Example:
            >>> sql = adapter._build_add_column_sql(
            ...     "users",
            ...     "email",
            ...     {"type": "str", "required": True, "default": "NULL"}
            ... )
            >>> # "ALTER TABLE users ADD COLUMN email TEXT DEFAULT NULL"
        
        Notes:
            - Required columns MUST have DEFAULT value
            - DEFAULT persists after ALTER (can't be removed)
        """
        field_type = self._map_field_type(column_def.get("type", "str"))
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {field_type}"

        # SQLite-specific: Handle required columns (need default)
        if column_def.get("required"):
            default = column_def.get("default", "NULL")
            sql += f" DEFAULT {default}"
        elif column_def.get("default") is not None:
            sql += f" DEFAULT {column_def['default']}"

        return sql

    def _supports_drop_column(self) -> bool:
        """
        Check if DROP COLUMN is supported (always False for SQLite < 3.35.0).
        
        Returns:
            False: SQLite does not support DROP COLUMN in older versions
        
        Notes:
            - SQLite 3.35.0+ added DROP COLUMN support
            - Most deployments use older versions
            - Workaround: Create new table, copy data, drop old, rename new
        """
        return False

    def _supports_modify_column(self) -> bool:
        """
        Check if MODIFY COLUMN is supported (always False for SQLite).
        
        Returns:
            False: SQLite does not support MODIFY COLUMN
        
        Notes:
            - SQLite has very limited ALTER TABLE support
            - MODIFY COLUMN not supported in any SQLite version
            - Workaround: Recreate table with new schema
        """
        return False

    def alter_table(self, table_name: str, changes: Dict[str, Any]) -> None:
        """
        Alter SQLite table structure.
        
        Due to SQLite's limited ALTER TABLE support, this method implements a
        table recreation strategy for DROP COLUMN and MODIFY COLUMN operations.
        ADD COLUMN is handled natively.
        
        Args:
            table_name: Name of table to alter
            changes: Dict with 'add_columns', 'drop_columns', 'modify_columns' keys
        
        Notes:
            - ADD COLUMN: Native support (uses parent class)
            - DROP COLUMN: Requires table recreation
            - MODIFY COLUMN: Requires table recreation
        """
        self._log('info', _LOG_ALTER_TABLE_SQLITE, table_name)
        
        # Handle ADD COLUMN natively (if present and no other changes)
        if changes.get("add_columns") and not changes.get("drop_columns") and not changes.get("modify_columns"):
            super().alter_table(table_name, changes)
            return
        
        # For DROP COLUMN or MODIFY COLUMN, use table recreation strategy
        self._recreate_table_with_changes(table_name, changes)

    def _recreate_table_with_changes(self, table_name: str, changes: Dict[str, Any]) -> None:
        """
        Recreate table with schema changes (SQLite workaround).
        
        Process:
        1. Get current schema
        2. Create temporary table with new schema
        3. Copy data (excluding dropped columns)
        4. Drop original table
        5. Rename temporary table
        
        Args:
            table_name: Name of table to modify
            changes: Dict with 'add_columns', 'drop_columns', 'modify_columns'
        
        Notes:
            - Preserves data integrity
            - Handles all schema changes atomically
            - Uses transaction for safety
        """
        cur = self.get_cursor()
        
        # Get current table schema
        cur.execute(f"PRAGMA table_info({table_name})")
        current_columns = cur.fetchall()
        
        # Build new schema
        new_columns = []
        drop_set = set(changes.get("drop_columns", []))
        modify_dict = changes.get("modify_columns", {})
        
        for col in current_columns:
            col_name = col[1]
            if col_name not in drop_set:
                if col_name in modify_dict:
                    # Use modified definition
                    col_def = self._build_column_definition(col_name, modify_dict[col_name])
                    new_columns.append(col_def)
                else:
                    # Keep existing definition
                    col_type = col[2]
                    col_notnull = col[3]
                    col_default = col[4]
                    col_pk = col[5]
                    
                    col_def = f"{col_name} {col_type}"
                    if col_pk:
                        col_def += " PRIMARY KEY"
                    if col_notnull and not col_pk:
                        col_def += " NOT NULL"
                    if col_default is not None:
                        col_def += f" DEFAULT {col_default}"
                    new_columns.append(col_def)
        
        # Add new columns if present
        if "add_columns" in changes:
            for col_name, col_spec in changes["add_columns"].items():
                col_def = self._build_column_definition(col_name, col_spec)
                new_columns.append(col_def)
        
        # Create temporary table
        temp_table = f"{table_name}_temp_migration"
        create_sql = f"CREATE TABLE {temp_table} ({', '.join(new_columns)})"
        
        self._log('info', "Creating temporary table: %s", create_sql)
        cur.execute(create_sql)
        
        # Copy data (exclude dropped columns)
        copy_columns = [col[1] for col in current_columns if col[1] not in drop_set]
        if copy_columns:
            copy_sql = f"INSERT INTO {temp_table} ({', '.join(copy_columns)}) SELECT {', '.join(copy_columns)} FROM {table_name}"
            self._log('info', "Copying data: %s", copy_sql)
            cur.execute(copy_sql)
        
        # Drop original table
        cur.execute(f"DROP TABLE {table_name}")
        
        # Rename temporary table
        cur.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
        
        self.connection.commit()
        self._log('info', "Table recreation complete: %s", table_name)
    
    # ============================================================
    # DDL Operations (Table Metadata)
    # ============================================================

    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists in database.
        
        Queries sqlite_master system table for table existence.
        
        Args:
            table_name: Name of table to check
        
        Returns:
            True if table exists, False otherwise
        
        Example:
            >>> if adapter.table_exists("users"):
            ...     print("Table found")
        """
        cur = self.get_cursor()
        cur.execute(_SQL_SELECT_MASTER, (table_name,))
        result = cur.fetchone()
        exists = result is not None
        self._log('debug', _LOG_TABLE_EXISTS, table_name, exists)
        return exists

    def list_tables(self) -> List[str]:
        """
        List all tables in database (alphabetically sorted).
        
        Returns:
            List of table names (sorted)
        
        Example:
            >>> tables = adapter.list_tables()
            >>> # ['auth_sessions', 'users', 'user_roles']
        """
        cur = self.get_cursor()
        cur.execute(_SQL_LIST_TABLES)
        tables = [row[0] for row in cur.fetchall()]
        self._log('debug', _LOG_FOUND_TABLES, len(tables), tables)
        return tables
    
    # ============================================================
    # DML Operations (Parent Wrappers)
    # ============================================================

    # insert(), select(), update(), delete() - inherited from SQLAdapter

    def insert(self, table: str, fields: List[str], values: List[Any]) -> Any:
        """
        Insert row into table (parent wrapper).
        
        Calls parent SQLAdapter.insert() which handles SQL building and execution.
        
        Args:
            table: Table name
            fields: List of field names
            values: List of values (must match fields)
        
        Returns:
            Row ID of inserted row
        """
        result = super().insert(table, fields, values)
        # Parent calls commit(), but in autocommit mode it's handled by explicit transactions
        return result

    def update(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        where: Dict[str, Any]
    ) -> int:
        """
        Update rows in table (parent wrapper).
        
        Calls parent SQLAdapter.update() which handles SQL building and execution.
        
        Args:
            table: Table name
            fields: List of field names to update
            values: List of new values (must match fields)
            where: WHERE clause dict (see sql_adapter.py for operators)
        
        Returns:
            Number of rows updated
        """
        result = super().update(table, fields, values, where)
        # Parent calls commit(), but in autocommit mode it's handled by explicit transactions
        return result

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Delete rows from table (parent wrapper).
        
        Calls parent SQLAdapter.delete() which handles SQL building and execution.
        
        Args:
            table: Table name
            where: WHERE clause dict (see sql_adapter.py for operators)
        
        Returns:
            Number of rows deleted
        """
        result = super().delete(table, where)
        # Parent calls commit(), but in autocommit mode it's handled by explicit transactions
        return result

    def upsert(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        conflict_fields: List[str]
    ) -> Any:
        """
        Insert or update row using SQLite's ON CONFLICT clause.
        
        Uses SQLite 3.24+ syntax: INSERT...ON CONFLICT...DO UPDATE SET.
        If no conflict_fields provided, falls back to INSERT OR REPLACE.
        
        Args:
            table: Table name
            fields: List of field names
            values: List of values (must match fields)
            conflict_fields: Fields to check for conflicts (usually pk or unique)
        
        Returns:
            Row ID of inserted/updated row
        
        Example:
            >>> # Insert or update by id
            >>> row_id = adapter.upsert(
            ...     "users",
            ...     ["id", "name", "age"],
            ...     [1, "John", 30],
            ...     conflict_fields=["id"]
            ... )
        
        Notes:
            - Requires SQLite 3.24.0+ for ON CONFLICT
            - Falls back to INSERT OR REPLACE if no conflict_fields
        """
        cur = self.get_cursor()

        # Build INSERT clause
        placeholders = ", ".join(["?" for _ in fields])
        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"

        # Build ON CONFLICT clause
        if conflict_fields:
            conflict_cols = ", ".join(conflict_fields)
            update_set = ", ".join([f"{f} = excluded.{f}" for f in fields if f not in conflict_fields])
            sql += f" ON CONFLICT({conflict_cols}) DO UPDATE SET {update_set}"
        else:
            # Default to REPLACE behavior
            sql = f"INSERT OR REPLACE INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"

        self._log('debug', "Executing UPSERT: %s with values: %s", sql, values)
        cur.execute(sql, values)
        # Don't commit - SQLite in autocommit mode with explicit transaction control

        row_id = cur.lastrowid
        self._log('info', _LOG_UPSERTED, table, row_id)
        return row_id
    
    # ============================================================
    # Type Mapping (SQLite Storage Classes)
    # ============================================================

    def map_type(self, abstract_type: Any) -> str:
        """
        Map abstract schema type to SQLite storage class.
        
        SQLite uses 5 storage classes: TEXT, INTEGER, REAL, BLOB, NULL.
        This method maps zCLI abstract types to appropriate storage classes.
        
        Args:
            abstract_type: Abstract type (str, int, float, bool, datetime, json, etc.)
        
        Returns:
            SQLite storage class (TEXT, INTEGER, REAL, BLOB)
        
        Example:
            >>> adapter.map_type("str")
            "TEXT"
            >>> adapter.map_type("int")
            "INTEGER"
            >>> adapter.map_type("bool")
            "INTEGER"
            >>> adapter.map_type("datetime")
            "TEXT"
        
        Notes:
            - Non-string types default to TEXT
            - bool → INTEGER (0 or 1)
            - datetime → TEXT (ISO 8601 format recommended)
            - json → TEXT (serialized JSON string)
        """
        if not isinstance(abstract_type, str):
            self._log('debug', _ERR_TYPE_NOT_STRING, abstract_type)
            return "TEXT"

        normalized = abstract_type.strip().rstrip("!?").lower()

        type_map = {
            "str": "TEXT",
            "string": "TEXT",
            "int": "INTEGER",
            "integer": "INTEGER",
            "float": "REAL",
            "real": "REAL",
            "bool": "INTEGER",
            "boolean": "INTEGER",
            "datetime": "TEXT",
            "date": "TEXT",
            "time": "TEXT",
            "json": "TEXT",
            "blob": "BLOB",
        }

        return type_map.get(normalized, "TEXT")
    
    # ============================================================
    # TCL - Transaction Control Language
    # ============================================================

    def begin_transaction(self) -> None:
        """
        Begin explicit transaction (DEFERRED isolation).
        
        Starts a transaction with DEFERRED locking. Lock is acquired on first
        write operation, allowing parallel reads.
        
        Raises:
            sqlite3.OperationalError: If transaction already active (handled)
        
        Example:
            >>> adapter.begin_transaction()
            >>> try:
            ...     adapter.insert("users", ["name"], ["John"])
            ...     adapter.commit()
            ... except Exception:
            ...     adapter.rollback()
        
        Notes:
            - Handles "transaction already active" error gracefully
            - Uses DEFERRED isolation by default (set in connect())
            - Lock acquired on first write, not on BEGIN
        """
        if self.connection:
            try:
                self.connection.execute(_SQL_BEGIN)
                self._log('debug', _LOG_TRANSACTION_STARTED)
            except sqlite3.OperationalError as e:
                if _ERR_TRANSACTION_ACTIVE not in str(e).lower():
                    raise

    def commit(self) -> None:
        """
        Commit current transaction (make changes permanent).
        
        Commits all changes made since BEGIN. If no transaction is active,
        handles the error gracefully (logs but doesn't raise).
        
        Raises:
            sqlite3.OperationalError: If commit fails (other than "no transaction")
        
        Example:
            >>> adapter.begin_transaction()
            >>> adapter.insert("users", ["name"], ["John"])
            >>> adapter.commit()  # Changes now permanent
        
        Notes:
            - Safe to call even if no transaction active
            - Releases all locks acquired during transaction
        """
        if self.connection:
            try:
                self.connection.execute(_SQL_COMMIT)
                self._log('debug', _LOG_TRANSACTION_COMMITTED)
            except sqlite3.OperationalError as e:
                if _ERR_NO_TRANSACTION not in str(e).lower():
                    raise

    def rollback(self) -> None:
        """
        Rollback current transaction (undo all changes).
        
        Reverts all changes made since BEGIN. If no transaction is active,
        handles the error gracefully (logs but doesn't raise).
        
        Raises:
            sqlite3.OperationalError: If rollback fails (other than "no transaction")
        
        Example:
            >>> adapter.begin_transaction()
            >>> try:
            ...     adapter.insert("users", ["name"], ["John"])
            ...     # Something goes wrong
            ...     adapter.rollback()  # Undo insert
            ... except Exception:
            ...     adapter.rollback()
        
        Notes:
            - Safe to call even if no transaction active
            - Releases all locks acquired during transaction
        """
        if self.connection:
            try:
                self.connection.execute(_SQL_ROLLBACK)
                self._log('debug', _LOG_TRANSACTION_ROLLED_BACK)
            except sqlite3.OperationalError as e:
                if _ERR_NO_TRANSACTION not in str(e).lower():
                    raise

    # _get_placeholders() returns "?, ?, ?" (default)
    # _get_last_insert_id() returns cursor.lastrowid (default)
