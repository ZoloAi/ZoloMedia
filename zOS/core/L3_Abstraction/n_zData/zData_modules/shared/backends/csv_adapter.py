# zCLI/subsystems/zData/zData_modules/shared/backends/csv_adapter.py
"""
CSV database backend adapter with pandas-powered DataFrames and in-memory caching.

This module implements a sophisticated CSV adapter that uses pandas DataFrames for
powerful data manipulation, in-memory table caching for performance, multi-table
JOIN support, and comprehensive WHERE clause filtering. Perfect for lightweight
data storage, prototyping, and file-based databases.

Architecture Overview
--------------------
CSVAdapter sits at the concrete layer of the adapter hierarchy:

    BaseDataAdapter (ABC)
           ↓
    CSVAdapter (File-based with pandas DataFrames)

**Design Philosophy:**
- **Pandas-powered:** Uses DataFrames for efficient data manipulation
- **In-memory caching:** Tables cached in self.tables dict for performance
- **File-based persistence:** Each table stored as {table_name}.csv
- **Multi-table JOINs:** Merge multiple tables with auto-join detection
- **Type coercion:** Schema-based type enforcement via pandas dtypes
- **WHERE filtering:** Comprehensive operator support (eq, gt, lt, like, in, etc.)

CSV-Specific Features
---------------------
**1. Pandas DataFrames:**
All tables loaded as pandas DataFrames for powerful operations:
- Filtering, sorting, grouping via pandas API
- Type coercion (int, float, bool, datetime, str)
- Efficient column operations (add, drop, rename)
- to_csv() for persistence, read_csv() for loading

**2. In-Memory Table Caching:**
Tables cached in self.tables dict for performance:
```python
self.tables = {
    "users": DataFrame(...),
    "orders": DataFrame(...)
}
```
- Load once, access many times (no repeated file I/O)
- Automatic save on disconnect() flushes cache to disk
- Memory-efficient for small-to-medium datasets

**3. Multi-Table JOIN Support:**
Powerful _join_tables() method with pandas merge():
- Manual JOINs: Specify join conditions explicitly
- AUTO JOIN: Detects relationships from schema foreign keys
- Merge strategies: inner, left, right, outer
- Multi-table queries: join("users", "orders", "products")

**4. WHERE Clause Filtering:**
Comprehensive _create_where_mask() with operators:
- **Equality:** {"age": 25} → age == 25
- **Comparison:** {"age__gt": 18} → age > 18
- **LIKE:** {"name__like": "John%"} → name.str.startswith("John")
- **IN:** {"city__in": ["NYC", "LA"]} → city.isin(["NYC", "LA"])
- **IS NULL:** {"deleted__is_null": True} → deleted.isna()
- **OR conditions:** {"or": [{"city": "NYC"}, {"city": "LA"}]}

**5. Type Coercion:**
_apply_schema_types() enforces schema types:
```python
schema = {"age": {"type": "int"}, "price": {"type": "float"}}
df = df.astype({"age": "int64", "price": "float64"})
```

**6. UPSERT Support:**
Insert or update with conflict resolution:
- Merge new data with existing data on conflict_fields
- drop_duplicates(subset=conflict_fields, keep='last')

File Structure
-------------
Each table stored as a separate CSV file:
```
base_path/
    users.csv
    orders.csv
    products.csv
```

**CSV Format:**
- Header row with column names
- Pandas to_csv(index=False) - no row index
- UTF-8 encoding by default
- Comma delimiter (configurable)

Caching Strategy
---------------
**Load → Cache → Save cycle:**
1. **connect():** Ensure base_path exists
2. **_load_table():** Read CSV → DataFrame, cache in self.tables
3. **Operations:** Work with cached DataFrame (fast)
4. **_save_table():** Write DataFrame → CSV (on demand or disconnect)
5. **disconnect():** Flush all cached tables to disk

**Memory Management:**
- Tables stay in memory for session duration
- Large datasets: Consider chunking or database backend
- self.tables.clear() on disconnect frees memory

Usage Examples
-------------
Basic connection and CRUD:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.csv_adapter import CSVAdapter
    >>> config = {"path": "/data/myapp", "label": "csvdb"}
    >>> adapter = CSVAdapter(config, logger=logger)
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
    >>> # Insert (cached in memory)
    >>> row_id = adapter.insert("users", ["name", "age"], ["John", 30])
    >>> 
    >>> # Select with WHERE
    >>> rows = adapter.select("users", where={"age__gte": 18})
    >>> 
    >>> # Disconnect (saves all cached tables)
    >>> adapter.disconnect()

Multi-table JOINs:
    >>> # Manual JOIN
    >>> joins = [{"table": "orders", "on": "users.id == orders.user_id"}]
    >>> rows = adapter.select(["users", "orders"], joins=joins)
    >>> 
    >>> # AUTO JOIN (detects FK from schema)
    >>> rows = adapter.select(
    ...     ["users", "companies"],
    ...     auto_join=True,
    ...     schema=schema
    ... )

WHERE operators:
    >>> # Comparison
    >>> rows = adapter.select("users", where={"age__gt": 18, "age__lt": 65})
    >>> 
    >>> # LIKE pattern
    >>> rows = adapter.select("users", where={"name__like": "John%"})
    >>> 
    >>> # IN list
    >>> rows = adapter.select("users", where={"city__in": ["NYC", "LA"]})
    >>> 
    >>> # OR conditions
    >>> rows = adapter.select("users", where={
    ...     "status": "active",
    ...     "or": [{"city": "NYC"}, {"city": "LA"}]
    ... })

Dependencies
-----------
**Required:**
- pandas

**Installation:**
```bash
pip install pandas
# or
pip install zolo-zcli[csv]
```

Integration
----------
This adapter is used by:
- classical_data.py: CRUD orchestration
- data_operations.py: High-level operations
- quantum_data.py: Abstracted data structures (if CSV backend selected)

See Also
--------
- base_adapter.py: Abstract adapter interface
- sqlite_adapter.py: SQL-based file storage
- postgresql_adapter.py: SQL-based network storage
"""

from zOS import Dict, List, Optional, Any
from .base_adapter import BaseDataAdapter

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ============================================================
# Module Constants - File Extensions
# ============================================================

_CSV_EXTENSION = ".csv"
_CSV_GLOB_PATTERN = "*.csv"

# ============================================================
# Module Constants - Schema Keys
# ============================================================

_SCHEMA_KEY_PRIMARY_KEY = "primary_key"
_SCHEMA_KEY_INDEXES = "indexes"
_SCHEMA_KEY_TYPE = "type"
_SCHEMA_KEY_PK = "pk"
_SCHEMA_KEY_UNIQUE = "unique"
_SCHEMA_KEY_REQUIRED = "required"
_SCHEMA_KEY_DEFAULT = "default"

# ============================================================
# Module Constants - WHERE Operators
# ============================================================

_OP_SUFFIX_GT = "__gt"
_OP_SUFFIX_LT = "__lt"
_OP_SUFFIX_GTE = "__gte"
_OP_SUFFIX_LTE = "__lte"
_OP_SUFFIX_LIKE = "__like"
_OP_SUFFIX_IN = "__in"
_OP_SUFFIX_IS_NULL = "__is_null"
_OP_SUFFIX_IS_NOT_NULL = "__is_not_null"
_WHERE_KEY_OR = "or"

# ============================================================
# Module Constants - Merge Strategies
# ============================================================

_MERGE_INNER = "inner"
_MERGE_LEFT = "left"
_MERGE_RIGHT = "right"
_MERGE_OUTER = "outer"

# ============================================================
# Module Constants - Column Keys
# ============================================================

_COL_INDEX = "index"
_COL_DEFAULT = "default"
_COL_TYPE = "type"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_PANDAS_MISSING = "pandas is required for CSV adapter. Install with: pip install pandas"
_ERR_TABLE_NOT_FOUND = "CSV table '%s' not found: %s"
_ERR_DIR_CREATE_FAILED = "Failed to create CSV directory: %s"
_ERR_TABLE_LOAD_FAILED = "Failed to load CSV table '%s': %s"
_ERR_TABLE_SAVE_FAILED = "Failed to save CSV table '%s': %s"
_ERR_JOIN_FAILED = "Failed to join tables: %s"
_ERR_WHERE_FILTER_FAILED = "Failed to apply WHERE filter: %s"
_ERR_TYPE_COERCION_FAILED = "Failed to apply type coercion for table '%s': %s"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_CONNECTED = "Connected to CSV backend: %s"
_LOG_DISCONNECTED = "Disconnected from CSV backend: %s"
_LOG_TABLE_CREATED = "CSV table created: %s"
_LOG_TABLE_LOADED = "Loaded CSV table: %s (%d rows)"
_LOG_TABLE_SAVED = "Saved CSV table: %s (%d rows)"
_LOG_TABLE_DROPPED = "Dropped CSV table: %s"
_LOG_TABLE_ALTERED = "Altered CSV table: %s"
_LOG_COLUMN_ADDED = "Added column '%s' to table '%s'"
_LOG_COLUMN_DROPPED = "Dropped column '%s' from table '%s'"
_LOG_ROW_INSERTED = "Inserted row into CSV table %s (row %d)"
_LOG_JOIN_MULTI_TABLE = "[JOIN] Multi-table CSV query: %s"
_LOG_TABLE_EXISTS = "CSV table '%s' exists: %s"
_LOG_FOUND_TABLES = "Found %d CSV tables: %s"

# ============================================================
# Public API
# ============================================================

__all__ = ["CSVAdapter"]


class CSVAdapter(BaseDataAdapter):
    """
    CSV backend adapter with pandas DataFrames, in-memory caching, and multi-table JOINs.

    CSVAdapter provides a powerful file-based database using CSV files with pandas
    DataFrames for efficient data manipulation. Each table is a separate CSV file,
    loaded into memory as a DataFrame for fast operations, then saved back to disk.

    Architecture
    -----------
    **Inheritance Chain:**
    BaseDataAdapter (ABC) → CSVAdapter

    **Key Components:**
    - **self.tables (dict):** In-memory cache of DataFrames {table_name: DataFrame}
    - **self.schemas (dict):** Schema definitions {table_name: schema_dict}
    - **base_path (Path):** Directory where CSV files are stored
    - **pandas (library):** DataFrame engine for data operations

    Key Features
    -----------
    **1. Pandas-Powered DataFrames:**
    All table operations use pandas DataFrames:
    - Efficient filtering, sorting, grouping
    - Type coercion (int, float, bool, datetime, str)
    - Column operations (add, drop, rename)
    - to_csv() persistence, read_csv() loading

    **2. In-Memory Table Caching:**
    Tables cached for performance:
    - Load once via _load_table() → cache in self.tables
    - All operations work with cached DataFrame (no file I/O)
    - Save on demand via _save_table() or disconnect()
    - Memory-efficient for small-to-medium datasets

    **3. Multi-Table JOINs:**
    Sophisticated _join_tables() with pandas merge():
    - Manual JOINs: Explicit join conditions
    - AUTO JOIN: Detect relationships from schema FKs
    - Merge strategies: inner, left, right, outer
    - Multi-table support: join 3+ tables

    **4. WHERE Clause Filtering:**
    Comprehensive _create_where_mask() with operators:
    - Equality, comparison (gt, lt, gte, lte)
    - LIKE patterns (startswith, endswith, contains)
    - IN lists, IS NULL checks
    - OR conditions for complex logic

    **5. Type Coercion:**
    Schema-based type enforcement via _apply_schema_types():
    - int → int64, float → float64, bool → bool
    - Ensures data integrity on load/save

    **6. UPSERT Support:**
    Insert or update with conflict resolution:
    - Merge new + existing data on conflict_fields
    - drop_duplicates() with keep='last'

    Methods (24 total)
    -----------------
    **Initialization:**
    - __init__: Initialize with pandas check, cache dicts

    **Connection Management:**
    - connect: Ensure base_path directory exists
    - disconnect: Flush all cached tables to disk, clear memory
    - get_cursor: Return self (no cursor concept for CSV)

    **DDL Operations:**
    - create_table: Create CSV with headers from schema
    - alter_table: Add/drop columns
    - drop_table: Delete CSV file
    - table_exists: Check if CSV file exists
    - list_tables: List all CSV files in base_path

    **DML Operations:**
    - insert: Add row to DataFrame, save to CSV
    - select: Query with WHERE, JOINs, ORDER BY, LIMIT
    - update: Modify rows matching WHERE
    - delete: Remove rows matching WHERE
    - upsert: Insert or update on conflict

    **Type Mapping:**
    - map_type: Convert abstract types to pandas dtypes

    **TCL Operations:**
    - begin_transaction: No-op (CSV has no transactions)
    - commit: No-op
    - rollback: No-op

    **Internal Helpers:**
    - _get_csv_path: Build file path for table
    - _append_row_to_df: Add row to DataFrame
    - _load_table: Read CSV → DataFrame, cache
    - _save_table: Write DataFrame → CSV
    - _apply_schema_types: Enforce schema type coercion
    - _create_where_mask: Build pandas boolean mask for WHERE
    - _join_tables: Multi-table JOIN with merge
    - _resolve_field_names: Resolve ambiguous column names
    - _apply_where_filter: Apply WHERE mask to DataFrame

    CSV-Specific Details
    -------------------
    **File Format:**
    - Each table: {table_name}.csv
    - Header row with column names
    - to_csv(index=False) - no row index
    - UTF-8 encoding

    **Memory Management:**
    - Tables stay in self.tables for session duration
    - disconnect() flushes cache and clears memory
    - Large datasets: Consider chunking or SQL backend

    **Limitations:**
    - No ACID transactions (file-based)
    - No concurrent write access (file locking needed)
    - Memory-bound by dataset size
    - No indexes (full table scan for queries)

    Usage Example
    ------------
        >>> config = {"path": "/data/myapp", "label": "csvdb"}
        >>> adapter = CSVAdapter(config, logger=logger)
        >>> adapter.connect()
        >>> 
        >>> schema = {"id": {"type": "int"}, "name": {"type": "str"}}
        >>> adapter.create_table("users", schema)
        >>> adapter.insert("users", ["id", "name"], [1, "Alice"])
        >>> 
        >>> rows = adapter.select("users", where={"id": 1})
        >>> adapter.disconnect()  # Saves all cached tables
    """

    # ============================================================
    # Initialization
    # ============================================================

    def __init__(self, config: Dict[str, Any], logger=None) -> None:
        """
        Initialize CSV adapter with pandas check and in-memory caching.

        Validates pandas availability, initializes the base adapter (sets base_path,
        logger), and creates empty cache dicts for tables and schemas.

        Args:
            config: Configuration dict with:
                - path (str): Base directory for CSV files
                - label (str): Adapter label
            logger: Optional logger instance for diagnostic output

        Raises:
            ImportError: If pandas is not installed

        Example:
            >>> config = {"path": "/data/myapp", "label": "csvdb"}
            >>> adapter = CSVAdapter(config, logger=logger)
            >>> # adapter.tables = {}  (empty cache)
            >>> # adapter.schemas = {}  (empty schema tracking)

        Note:
            - pandas must be installed: pip install pandas
            - self.tables dict caches DataFrames for performance
            - self.schemas dict tracks schema definitions per table
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(ERR_PANDAS_MISSING)

        super().__init__(config, logger)
        self.tables: Dict[str, Any] = {}  # Cache: {table_name: DataFrame}
        self.schemas: Dict[str, Dict] = {}  # Schema: {table_name: schema_dict}

    # ============================================================
    # Connection Management
    # ============================================================

    def connect(self) -> bool:
        """
        Establish CSV backend connection by ensuring base directory exists.

        Creates the base_path directory if it doesn't exist, enabling CSV file
        storage. Sets self.connection = True to mark connection as active.

        Returns:
            bool: True on successful connection

        Raises:
            Exception: If directory creation fails (permissions, disk full, etc.)

        Example:
            >>> adapter = CSVAdapter(config, logger=logger)
            >>> adapter.connect()
            True
            >>> # base_path directory now exists

        Note:
            - CSV "connection" is just directory validation
            - No network connection or database server needed
            - Idempotent: safe to call multiple times
        """
        try:
            self._ensure_directory()
            self._log('info', _LOG_CONNECTED, self.base_path)
            self.connection = True
            return True
        except Exception as e:
            self._log('error', _ERR_DIR_CREATE_FAILED, e)
            raise

    def disconnect(self) -> None:
        """
        Disconnect from CSV backend by flushing all cached tables to disk.

        Saves all cached DataFrames in self.tables to their respective CSV files,
        then clears the cache to free memory. Essential for data persistence.

        Raises:
            Exception: If any table save operation fails

        Example:
            >>> adapter.disconnect()
            >>> # All tables in self.tables saved to CSV
            >>> # self.tables = {} (cleared)
            >>> # self.connection = None

        Note:
            - **CRITICAL:** Always call disconnect() to persist changes
            - Without disconnect(), in-memory changes are lost
            - Automatically saves all tables (no manual save needed)
            - Clears self.tables cache to free memory
        """
        if self.tables:
            for table_name, df in self.tables.items():
                self._save_table(table_name, df)
            self.tables.clear()
            self._log('info', LOG_DISCONNECTED, self.base_path)
        self.connection = None

    def get_cursor(self):
        """
        Return self as cursor (CSV has no cursor concept).

        CSV adapter doesn't use cursors like SQL databases. This method exists
        for BaseDataAdapter interface compatibility and simply returns self.

        Returns:
            CSVAdapter: self instance

        Example:
            >>> cursor = adapter.get_cursor()
            >>> # cursor is adapter (same object)

        Note:
            - No cursor object needed for CSV operations
            - All operations called directly on adapter instance
        """
        return self

    # ============================================================
    # DDL Operations (Schema Management)
    # ============================================================

    def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create CSV table file with headers based on schema definition.

        Parses schema to extract column names, creates an empty pandas DataFrame
        with those columns, saves it as a CSV file, and caches in self.tables.

        Args:
            table_name: Name of the table (becomes filename {table_name}.csv)
            schema: Schema dict with field definitions:
                {"field": {"type": "str", "required": True}, ...}
                or {"field": "str", ...}

        Example:
            >>> schema = {
            ...     "id": {"type": "int", "pk": True},
            ...     "name": {"type": "str"},
            ...     "primary_key": ["id"]  # Ignored (metadata)
            ... }
            >>> adapter.create_table("users", schema)
            >>> # Creates: base_path/users.csv with headers: id,name

        Note:
            - Skips metadata keys: "primary_key", "indexes"
            - Supports both dict attrs and str shorthand
            - Creates empty DataFrame (0 rows, just headers)
            - Saves immediately to CSV file
            - Caches DataFrame in self.tables
        """
        self._log('info', "Creating CSV table: %s", table_name)

        columns = []
        self.schemas[table_name] = {}

        for field_name, attrs in schema.items():
            if field_name in [_SCHEMA_KEY_PRIMARY_KEY, _SCHEMA_KEY_INDEXES]:
                continue

            if isinstance(attrs, dict):
                columns.append(field_name)
                self.schemas[table_name][field_name] = attrs
            elif isinstance(attrs, str):
                columns.append(field_name)
                self.schemas[table_name][field_name] = {_SCHEMA_KEY_TYPE: attrs}

        df = pd.DataFrame(columns=columns)
        csv_file = self._get_csv_path(table_name)
        df.to_csv(csv_file, index=False)
        self.tables[table_name] = df

        self._log('info', _LOG_TABLE_CREATED, csv_file)

    def alter_table(self, table_name: str, changes: Dict[str, Any]) -> None:
        """
        Alter CSV table structure by adding or dropping columns.

        Loads table, applies column changes, saves back to CSV.

        Args:
            table_name: Name of the table to alter
            changes: Dict with operations:
                {"add_columns": {"col": {"type": "str", "default": None}}, ...}
                {"drop_columns": ["col1", "col2"], ...}

        Example:
            >>> changes = {
            ...     "add_columns": {"age": {"type": "int", "default": 0}},
            ...     "drop_columns": ["temp_field"]
            ... }
            >>> adapter.alter_table("users", changes)
            >>> # CSV updated with new columns, old columns removed

        Note:
            - add_columns: Adds new columns with default values
            - drop_columns: Removes columns if they exist
            - Changes applied in order: add first, then drop
            - Saves immediately to CSV file
        """
        df = self._load_table(table_name)

        if "add_columns" in changes:
            for column_name, column_def in changes["add_columns"].items():
                default = column_def.get(COL_DEFAULT, None)
                df[column_name] = default
                self._log('info', LOG_COLUMN_ADDED, column_name, table_name)

        if "drop_columns" in changes:
            for column_name in changes["drop_columns"]:
                if column_name in df.columns:
                    df = df.drop(columns=[column_name])
                    self._log('info', LOG_COLUMN_DROPPED, column_name, table_name)

        self._save_table(table_name, df)
        self.tables[table_name] = df
        self._log('info', LOG_TABLE_ALTERED, table_name)

    def drop_table(self, table_name: str) -> None:
        """
        Drop CSV table by deleting the file and clearing cache.

        Args:
            table_name: Name of the table to drop

        Example:
            >>> adapter.drop_table("users")
            >>> # Deletes: base_path/users.csv
            >>> # Clears: self.tables["users"], self.schemas["users"]

        Note:
            - Deletes CSV file from disk (permanent)
            - Removes from self.tables cache
            - Removes from self.schemas
            - Safe to call if table doesn't exist (no error)
        """
        csv_file = self._get_csv_path(table_name)
        if csv_file.exists():
            csv_file.unlink()
            self._log('info', LOG_TABLE_DROPPED, table_name)

        if table_name in self.tables:
            del self.tables[table_name]
        if table_name in self.schemas:
            del self.schemas[table_name]

    def table_exists(self, table_name: str) -> bool:
        """
        Check if CSV table exists by verifying file existence.

        Args:
            table_name: Name of the table to check

        Returns:
            bool: True if CSV file exists, False otherwise

        Example:
            >>> if adapter.table_exists("users"):
            ...     print("Table exists")

        Note:
            - Checks file system, not cache
            - Does not verify CSV is valid (just checks file exists)
        """
        csv_file = self._get_csv_path(table_name)
        exists = csv_file.exists()
        self._log('debug', LOG_TABLE_EXISTS, table_name, exists)
        return exists

    def list_tables(self) -> List[str]:
        """
        List all CSV tables in base_path directory.

        Returns:
            List[str]: List of table names (without .csv extension)

        Example:
            >>> tables = adapter.list_tables()
            >>> # ["users", "orders", "products"]

        Note:
            - Scans base_path for *.csv files
            - Returns table names (stem), not full paths
            - Sorted alphabetically
        """
        csv_files = list(self.base_path.glob(_CSV_GLOB_PATTERN))
        tables = [f.stem for f in csv_files]
        self._log('debug', LOG_FOUND_TABLES, len(tables), tables)
        return tables

    def introspect_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Introspect CSV file to get actual columns and infer types.
        
        This method reads the CSV file and uses pandas to infer the schema
        from the actual data. Critical for declarative migrations where we
        need to compare database reality vs. YAML target schema.
        
        Args:
            table_name: Name of the table to introspect
        
        Returns:
            Dict[str, Any]: Schema dict in zCLI format:
            {
                'column_name': {'type': 'int'|'float'|'str'|'bool'|'datetime'},
                ...
            }
        
        Example:
            >>> schema = adapter.introspect_schema("users")
            >>> # {'id': {'type': 'int'}, 'name': {'type': 'str'}, ...}
        
        Notes:
            - Reads only first 10 rows for performance (type inference)
            - Uses pandas dtype inference (int64 → int, object → str)
            - Returns empty dict if table doesn't exist
            - Does NOT include constraints (pk, unique, etc.) - only columns and types
            - Used by zData.migrate() to detect schema drift
        
        Type Mapping:
            - int64, int32 → 'int'
            - float64, float32 → 'float'
            - bool → 'bool'
            - datetime64 → 'datetime'
            - object, string → 'str'
        """
        csv_file = self._get_csv_path(table_name)
        
        # Return empty schema if table doesn't exist
        if not csv_file.exists():
            self._log('warning', f"Cannot introspect non-existent table: {table_name}")
            return {}
        
        try:
            # Read just header + 10 rows for type inference (performance optimization)
            df = pd.read_csv(csv_file, nrows=10)
            
            schema = {}
            for col in df.columns:
                col_def = {'type': 'str'}  # Default to string
                
                # Infer type from pandas dtype
                dtype_str = str(df[col].dtype)
                
                if 'int' in dtype_str:
                    col_def['type'] = 'int'
                elif 'float' in dtype_str:
                    col_def['type'] = 'float'
                elif 'bool' in dtype_str:
                    col_def['type'] = 'bool'
                elif 'datetime' in dtype_str:
                    col_def['type'] = 'datetime'
                else:
                    # object, string, or unknown → str
                    col_def['type'] = 'str'
                
                schema[col] = col_def
            
            self._log('debug', f"Introspected schema for {table_name}: {len(schema)} columns")
            
            return schema
            
        except Exception as e:
            self._log('error', f"Failed to introspect table {table_name}: {e}")
            return {}

    # ============================================================
    # DML Operations (Data Manipulation)
    # ============================================================

    def insert(self, table: str, fields: List[str], values: List[Any]) -> int:
        """
        Insert a row into CSV table and save to disk.

        Loads table, appends new row, saves back to CSV.
        Handles auto_increment for ID fields by calculating max(id) + 1.

        Args:
            table: Table name
            fields: List of field names
            values: List of values (same order as fields)

        Returns:
            int: Auto-generated ID if pk with auto_increment, else row count

        Example:
            >>> row_id = adapter.insert("users", ["name", "age"], ["Alice", 30])
            >>> # Returns auto-incremented ID if 'id' field has auto_increment: true

        Note:
            - Creates field→value dict via zip(fields, values)
            - Auto-generates ID if schema has pk=True, auto_increment=True
            - Appends row to DataFrame
            - Saves immediately to CSV (no explicit commit needed)
        """
        df = self._load_table(table)

        if values is None:
            values = []
        if fields is None:
            fields = []

        new_row = {field: value for field, value in zip(fields, values)}
        
        # Handle auto_increment for primary key fields
        # Try schema first, then fallback to convention-based detection
        schema = self.schemas.get(table, {})
        auto_id_field = None
        
        # Check schema for explicit auto_increment field
        for field_name, field_def in schema.items():
            if isinstance(field_def, dict):
                is_pk = field_def.get('pk', False) or field_def.get('primary_key', False)
                is_auto = field_def.get('auto_increment', False) or field_def.get('autoincrement', False)
                if is_pk and is_auto:
                    auto_id_field = field_name
                    break
        
        # Fallback: If no schema, check for 'id' column in DataFrame (convention-based)
        if not auto_id_field and 'id' in df.columns and 'id' not in new_row:
            auto_id_field = 'id'
        
        # If auto_increment field found and not provided (or empty) in insert
        if auto_id_field and (auto_id_field not in new_row or not new_row.get(auto_id_field)):
            # Calculate next ID: max(existing_ids) + 1, or 1 if table is empty
            if len(df) > 0 and auto_id_field in df.columns:
                try:
                    max_id = df[auto_id_field].max()
                    # Handle NaN or None
                    next_id = int(max_id) + 1 if pd.notna(max_id) else 1
                except (ValueError, TypeError):
                    next_id = len(df) + 1
            else:
                next_id = 1
            
            new_row[auto_id_field] = next_id
            row_id = next_id
            self._log('info', f"Auto-generated ID for {table}: {next_id}")
        else:
            row_id = len(df) + 1
        
        df = self._append_row_to_df(df, new_row)

        self._save_table(table, df)
        self.tables[table] = df

        self._log('info', LOG_ROW_INSERTED, table, row_id)
        return row_id

    def select(self, table, fields: Optional[List[str]] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Select rows from CSV table(s) with WHERE, JOINs, ORDER BY, LIMIT.

        Powerful query method supporting:
        - Single table queries with WHERE filtering
        - Multi-table JOINs (manual or AUTO)
        - ORDER BY sorting
        - LIMIT + OFFSET pagination

        Args:
            table: Table name (str) or list of tables for JOINs
            fields: List of field names or ["*"] for all (default: all)
            **kwargs:
                - where (dict): WHERE conditions
                - joins (list): Manual JOIN conditions
                - auto_join (bool): Auto-detect JOINs from schema FKs
                - schema (dict): Schema for AUTO JOIN detection
                - order (list): ORDER BY clauses [("field", "asc"), ...]
                - limit (int): Max rows to return
                - offset (int): Number of rows to skip (default: 0)

        Returns:
            List[Dict[str, Any]]: List of row dicts

        Example - Single table:
            >>> rows = adapter.select("users", where={"age__gte": 18})
            >>> # [{"id": 1, "name": "Alice", "age": 30}, ...]

        Example - Multi-table JOIN:
            >>> joins = [{"table": "orders", "on": "users.id == orders.user_id"}]
            >>> rows = adapter.select(["users", "orders"], joins=joins)

        Example - AUTO JOIN:
            >>> rows = adapter.select(
            ...     ["users", "companies"],
            ...     auto_join=True,
            ...     schema=schema
            ... )

        Example - ORDER BY and LIMIT:
            >>> rows = adapter.select(
            ...     "users",
            ...     where={"status": "active"},
            ...     order=[("created_at", "desc")],
            ...     limit=10
            ... )

        Note:
            - Multi-table detected by: len(tables) > 1 or joins is set
            - AUTO JOIN uses schema FKs to infer relationships
            - WHERE filtering via _create_where_mask() (operators: gt, lt, like, in, etc.)
            - ORDER BY uses pandas sort_values()
            - Returns list of dicts (row-wise)
        """
        where = kwargs.get('where')
        joins = kwargs.get('joins')
        order = kwargs.get('order')
        limit = kwargs.get('limit')
        offset = kwargs.get('offset', 0)  # Default to 0 (no offset)
        auto_join = kwargs.get('auto_join', False)
        schema = kwargs.get('schema')

        tables = [table] if isinstance(table, str) else table
        is_multi_table = len(tables) > 1 or joins

        if is_multi_table:
            self._log('info', LOG_JOIN_MULTI_TABLE, " + ".join(tables))
            df = self._join_tables(tables, joins=joins, schema=schema, auto_join=auto_join)

            if fields and fields != ["*"]:
                fields = self._resolve_field_names(fields, df.columns.tolist())
        else:
            df = self._load_table(table)

        if where:
            df = self._apply_where_filter(df, where)

        if fields and fields != ["*"]:
            available_fields = [f for f in fields if f in df.columns]
            if available_fields:
                df = df[available_fields]

        if order:
            df = self._apply_order(df, order)

        # Apply LIMIT + OFFSET pagination using DataFrame slicing
        if limit is not None:
            # Calculate slice boundaries: [offset:offset+limit]
            end = offset + limit
            df = df.iloc[offset:end]
        elif offset > 0:
            # Only offset, no limit: skip first N rows, return rest
            df = df.iloc[offset:]

        rows = df.to_dict('records')

        table_name = " + ".join(tables) if is_multi_table else table
        self._log('info', "Selected %d rows from %s", len(rows), table_name)
        return rows

    def update(self, table: str, fields: List[str], values: List[Any], where: Dict[str, Any]) -> int:
        """
        Update rows in CSV table matching WHERE condition.

        Args:
            table: Table name
            fields: List of fields to update
            values: List of new values (same order as fields)
            where: WHERE condition dict

        Returns:
            int: Number of rows updated

        Example:
            >>> count = adapter.update("users", ["age"], [31], {"name": "Alice"})
            >>> # Updates age to 31 for all rows where name='Alice'

        Note:
            - Uses _create_where_mask() to filter rows
            - If where=None, updates ALL rows
            - Saves immediately to CSV
        """
        df = self._load_table(table)

        if where:
            mask = self._create_where_mask(df, where)
        else:
            mask = pd.Series([True] * len(df), index=df.index)

        for field, value in zip(fields, values):
            if field in df.columns:
                df.loc[mask, field] = value

        rows_affected = mask.sum()

        self._save_table(table, df)
        self.tables[table] = df

        self._log('info', "Updated %d rows in CSV table %s", rows_affected, table)
        return int(rows_affected)

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Delete rows from CSV table matching WHERE condition.

        Args:
            table: Table name
            where: WHERE condition dict

        Returns:
            int: Number of rows deleted

        Example:
            >>> count = adapter.delete("users", {"age__lt": 18})
            >>> # Deletes all rows where age < 18

        Note:
            - Uses _create_where_mask() to filter rows
            - If where=None, deletes ALL rows (clears table)
            - Saves immediately to CSV
        """
        df = self._load_table(table)
        original_count = len(df)

        if where:
            mask = self._create_where_mask(df, where)
            df = df.loc[~mask]
        else:
            df = pd.DataFrame(columns=df.columns)

        rows_deleted = original_count - len(df)

        self._save_table(table, df)
        self.tables[table] = df

        self._log('info', "Deleted %d rows from CSV table %s", rows_deleted, table)
        return rows_deleted

    def upsert(self, table: str, fields: List[str], values: List[Any], conflict_fields: List[str]) -> int:
        """
        Insert or update row with conflict resolution.

        If row exists matching conflict_fields, updates it. Otherwise, inserts new row.

        Args:
            table: Table name
            fields: List of fields
            values: List of values
            conflict_fields: Fields to check for conflicts (e.g., ["id"])

        Returns:
            int: Row ID (index + 1)

        Example:
            >>> row_id = adapter.upsert(
            ...     "users",
            ...     ["id", "name", "age"],
            ...     [1, "Alice", 31],
            ...     conflict_fields=["id"]
            ... )
            >>> # If id=1 exists: updates name and age
            >>> # If id=1 missing: inserts new row

        Note:
            - Checks conflict_fields for existing row
            - If match found: updates (UPDATE)
            - If no match: inserts (INSERT)
            - Saves immediately to CSV
        """
        df = self._load_table(table)
        new_row = {field: value for field, value in zip(fields, values)}

        if conflict_fields and len(df) > 0:
            mask = pd.Series([True] * len(df), index=df.index)
            for conflict_field in conflict_fields:
                if conflict_field in new_row and conflict_field in df.columns:
                    mask = mask & (df[conflict_field] == new_row[conflict_field])

            if mask.any():
                for field, value in zip(fields, values):
                    if field in df.columns:
                        df.loc[mask, field] = value
                self._log('info', "Updated existing row in CSV table %s", table)
                row_id = int(df[mask].index[0]) + 1
            else:
                df = self._append_row_to_df(df, new_row)
                row_id = len(df)
                self._log('info', "Inserted new row into CSV table %s", table)
        else:
            df = self._append_row_to_df(df, new_row)
            row_id = len(df)
            self._log('info', "Inserted new row into CSV table %s", table)

        self._save_table(table, df)
        self.tables[table] = df

        return int(row_id)

    def aggregate(
        self,
        table: str,
        function: str,
        field: Optional[str] = None,
        where: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None
    ) -> Any:
        """
        Perform aggregation function on table data using pandas.
        
        Executes pandas aggregate functions (count, sum, mean, min, max) with optional
        WHERE filtering and GROUP BY grouping. Returns scalar for simple aggregations
        or dict for grouped aggregations.
        
        Supported functions:
        - count: Count rows (field optional, counts non-null if field provided)
        - sum: Sum numeric field values (field required)
        - avg: Average numeric field values (field required)
        - min: Minimum field value (field required)
        - max: Maximum field value (field required)
        
        Args:
            table: Table name
            function: Aggregation function (count, sum, avg, min, max)
            field: Field name to aggregate (required for sum/avg/min/max, optional for count)
            where: Optional WHERE clause dictionary for filtering
            group_by: Optional field name to group by
        
        Returns:
            Scalar value (int/float) for simple aggregation
            Dict {group_value: aggregate_value} for GROUP BY aggregation
        
        Raises:
            ValueError: If invalid function or missing required field
            RuntimeError: If query execution fails
        
        Examples:
            >>> # Count all users
            >>> count = adapter.aggregate("users", "count")
            >>> # 12
            
            >>> # Count active users
            >>> count = adapter.aggregate("users", "count", where={"status": "active"})
            >>> # 10
            
            >>> # Sum storage usage
            >>> total = adapter.aggregate("user_storage", "sum", field="used_mb")
            >>> # 34200
            
            >>> # Count users by role
            >>> counts = adapter.aggregate("user_roles", "count", group_by="role_id")
            >>> # {1: 1, 2: 3, 3: 8}
        
        Notes:
            - Uses pandas DataFrame operations for efficiency
            - Returns 0 for count on empty result
            - Returns None for sum/avg/min/max on empty result
            - GROUP BY returns dict with group values as keys
        """
        # Validate function
        valid_functions = ["count", "sum", "avg", "min", "max"]
        function_lower = function.lower()
        if function_lower not in valid_functions:
            raise ValueError(f"Invalid aggregate function '{function}'. Must be one of: {valid_functions}")
        
        # Validate field requirement
        if function_lower != "count" and not field:
            raise ValueError(f"Aggregate function '{function}' requires a field name")
        
        # Load table
        try:
            df = self._load_table(table)
        except Exception as e:
            self._log('error', f"Failed to load table {table}: {e}")
            raise RuntimeError(f"Failed to load table {table}: {e}")
        
        # Apply WHERE filter if provided
        if where:
            try:
                mask = self._create_where_mask(df, where)
                df = df[mask].copy()
            except Exception as e:
                self._log('error', f"WHERE clause filtering failed: {e}")
                raise RuntimeError(f"WHERE clause filtering failed: {e}")
        
        # Perform aggregation
        try:
            if group_by:
                # GROUP BY aggregation
                if group_by not in df.columns:
                    raise ValueError(f"GROUP BY field '{group_by}' not found in table")
                
                if function_lower == "count":
                    # Count rows per group
                    if field and field in df.columns:
                        result_series = df.groupby(group_by)[field].count()
                    else:
                        result_series = df.groupby(group_by).size()
                elif function_lower == "sum":
                    result_series = df.groupby(group_by)[field].sum()
                elif function_lower == "avg":
                    result_series = df.groupby(group_by)[field].mean()
                elif function_lower == "min":
                    result_series = df.groupby(group_by)[field].min()
                elif function_lower == "max":
                    result_series = df.groupby(group_by)[field].max()
                
                # Convert Series to dict
                result = result_series.to_dict()
                
                self._log('info', f"Aggregation {function}({field or '*'}) on {table} grouped by {group_by}: {len(result)} groups")
                return result
            else:
                # Simple aggregation (scalar result)
                if function_lower == "count":
                    if field and field in df.columns:
                        result = int(df[field].count())  # Count non-null values
                    else:
                        result = len(df)  # Count all rows
                elif function_lower == "sum":
                    if field not in df.columns:
                        raise ValueError(f"Field '{field}' not found in table")
                    result = df[field].sum()
                    # Convert numpy types to Python types
                    result = int(result) if pd.api.types.is_integer_dtype(df[field]) else float(result)
                elif function_lower == "avg":
                    if field not in df.columns:
                        raise ValueError(f"Field '{field}' not found in table")
                    result = float(df[field].mean()) if len(df) > 0 else None
                elif function_lower == "min":
                    if field not in df.columns:
                        raise ValueError(f"Field '{field}' not found in table")
                    result = df[field].min() if len(df) > 0 else None
                elif function_lower == "max":
                    if field not in df.columns:
                        raise ValueError(f"Field '{field}' not found in table")
                    result = df[field].max() if len(df) > 0 else None
                
                # Handle empty results
                if result is None or (isinstance(result, float) and pd.isna(result)):
                    result = 0 if function_lower == "count" else None
                
                self._log('info', f"Aggregation {function}({field or '*'}) on {table}: {result}")
                return result
                
        except Exception as e:
            self._log('error', f"Aggregation failed: {e}")
            raise RuntimeError(f"Aggregation query failed: {e}")

    # ============================================================
    # Type Mapping
    # ============================================================

    def map_type(self, abstract_type: str) -> str:
        """
        Map abstract schema type to pandas dtype.

        Args:
            abstract_type: Abstract type (str, int, float, bool, datetime, etc.)

        Returns:
            str: Pandas dtype ("object", "Int64", "float64", "boolean")

        Example:
            >>> adapter.map_type("int")
            'Int64'
            >>> adapter.map_type("str!")  # Strips '!' required marker
            'object'

        Note:
            - Strips whitespace and required markers (!?)
            - Case-insensitive matching
            - Returns "object" for unknown types
        """
        if not isinstance(abstract_type, str):
            return "object"

        normalized = abstract_type.strip().rstrip("!?").lower()

        type_map = {
            "str": "object",
            "string": "object",
            "int": "Int64",
            "integer": "Int64",
            "float": "float64",
            "real": "float64",
            "bool": "boolean",
            "boolean": "boolean",
            "datetime": "object",
            "date": "object",
            "json": "object",
        }

        return type_map.get(normalized, "object")

    # ============================================================
    # Transaction Control (No-ops for CSV)
    # ============================================================

    def begin_transaction(self) -> None:
        """
        Begin transaction (no-op for CSV - no transaction support).

        Note:
            CSV is file-based with no ACID transactions.
            This method exists for BaseDataAdapter interface compatibility.
        """
        self._log('debug', "CSV adapter: begin_transaction (no-op)")

    def commit(self) -> None:
        """
        Commit transaction by saving all cached tables to CSV files.

        Note:
            Unlike SQL databases, CSV saves happen immediately on each operation.
            This method explicitly flushes all cached tables to disk.
        """
        for table_name, df in self.tables.items():
            self._save_table(table_name, df)
        self._log('debug', "CSV adapter: commit (saved all tables)")

    def rollback(self) -> None:
        """
        Rollback transaction by reloading tables from disk (best-effort).

        Note:
            CSV has no true rollback. This clears cache, forcing reload on next access.
            Changes already saved to CSV files cannot be undone.
        """
        self._log('warning', "CSV adapter: rollback (reloading from disk)")
        self.tables.clear()

    # ============================================================
    # Internal Helpers
    # ============================================================

    def _get_csv_path(self, table_name: str):
        """
        Get CSV file path for table.
        
        For migration tables, uses zmigrations/ subfolder to keep Data/ directory clean.
        For regular tables, uses base_path/{table}.csv
        """
        # Check if this is a migration table for a specific data table
        # Pattern: __zmigration_{table_name} → zmigrations/{table_name}_zMigration.csv
        if table_name.startswith("__zmigration_"):
            actual_table = table_name.replace("__zmigration_", "")
            migration_dir = self.base_path / "zmigrations"
            migration_dir.mkdir(parents=True, exist_ok=True)
            return migration_dir / f"{actual_table}_zMigration{_CSV_EXTENSION}"
        
        # For the global _zdata_migrations table, redirect to zmigrations/ as well
        # This keeps the Data/ directory clean while accepting CSV's file-per-table approach
        if table_name == "_zdata_migrations":
            migration_dir = self.base_path / "zmigrations"
            migration_dir.mkdir(parents=True, exist_ok=True)
            return migration_dir / f"{table_name}{_CSV_EXTENSION}"
        
        # Regular tables use base_path
        return self.base_path / f"{table_name}{_CSV_EXTENSION}"

    def _append_row_to_df(self, df, new_row):
        """Safely append row to DataFrame (avoids FutureWarning)."""
        # Ensure all columns present in new row
        for col in df.columns:
            if col not in new_row:
                new_row[col] = None

        new_df = pd.DataFrame([new_row], columns=df.columns)

        # If original is empty, return new one (avoids pandas FutureWarning)
        if len(df) == 0:
            return new_df

        return pd.concat([df, new_df], ignore_index=True, sort=False)

    def _load_table(self, table_name):
        """Load table from CSV file (with caching)."""
        # Check cache first
        if table_name in self.tables:
            return self.tables[table_name]

        csv_file = self._get_csv_path(table_name)

        if not csv_file.exists():
            self._log('error', "CSV table does not exist: %s", table_name)
            raise FileNotFoundError(f"Table '{table_name}' not found")

        try:
            df = pd.read_csv(csv_file)

            # Apply schema types if available
            if table_name in self.schemas:
                df = self._apply_schema_types(df, self.schemas[table_name])

            # Cache for reuse
            self.tables[table_name] = df

            self._log('debug', "Loaded CSV table %s (%d rows)", table_name, len(df))
            return df

        except Exception as e:
            self._log('error', "Failed to load CSV table %s: %s", table_name, e)
            raise

    def _save_table(self, table_name, df):
        """Save DataFrame to CSV file."""
        csv_file = self._get_csv_path(table_name)

        try:
            df.to_csv(csv_file, index=False)
            self._log('debug', "Saved CSV table %s (%d rows)", table_name, len(df))
        except Exception as e:
            self._log('error', "Failed to save CSV table %s: %s", table_name, e)
            raise

    def _apply_schema_types(self, df, schema):
        """Apply type conversions based on schema."""
        for field_name, field_def in schema.items():
            if field_name not in df.columns:
                continue

            field_type = field_def.get("type", "str")

            try:
                if field_type in ["int", "integer"]:
                    df[field_name] = pd.to_numeric(df[field_name], errors='coerce').astype('Int64')
                elif field_type in ["float", "real"]:
                    df[field_name] = pd.to_numeric(df[field_name], errors='coerce')
                elif field_type in ["bool", "boolean"]:
                    df[field_name] = df[field_name].astype('boolean')
                elif field_type in ["datetime", "date"]:
                    df[field_name] = pd.to_datetime(df[field_name], errors='coerce')
            except Exception as e:
                self._log('warning', "Failed to convert column '%s' to type '%s': %s",
                             field_name, field_type, e)

        return df

    def _create_where_mask(self, df, where):
        """Create boolean mask for WHERE clause with operator support."""
        if not where or len(df) == 0:
            return pd.Series([True] * len(df), index=df.index)

        # Handle string WHERE clauses (simple equality only)
        if isinstance(where, str):
            self._log('warning', "String WHERE clauses not fully supported in CSV adapter. Use dict format for complex queries.")
            # Parse simple "field = 'value'" format
            if " = " in where:
                field, value = where.split(" = ", 1)
                field = field.strip()
                value = value.strip().strip("'\"")
                where = {field: value}
            else:
                self._log('error', "Cannot parse WHERE clause: %s", where)
                return pd.Series([True] * len(df), index=df.index)

        mask = pd.Series([True] * len(df), index=df.index)

        for field, condition in where.items():
            # Handle OR conditions
            if field.upper() in ("$OR", "OR"):
                if isinstance(condition, list) and condition:
                    or_mask = self._create_or_mask(df, condition)
                    mask = mask & or_mask
                continue

            if field not in df.columns:
                self._log('warning', "Field '%s' not in table columns", field)
                continue

            # Handle IS NULL
            if condition is None:
                mask = mask & df[field].isna()
                continue

            # Handle IN operator (list values) with type coercion
            if isinstance(condition, list):
                # Fix: Ensure condition values match column dtype
                try:
                    col_dtype = df[field].dtype
                    if col_dtype == 'object':  # String column
                        # Convert all list values to strings
                        coerced_list = [str(v) for v in condition]
                        mask = mask & df[field].astype(str).isin(coerced_list)
                    else:
                        mask = mask & df[field].isin(condition)
                except (ValueError, TypeError):
                    # Fallback: convert to strings
                    coerced_list = [str(v) for v in condition]
                    mask = mask & df[field].astype(str).isin(coerced_list)
                continue

            # Handle complex operators (dict values)
            if isinstance(condition, dict):
                mask = self._apply_operator_conditions(df, field, condition, mask)
                continue

            # Simple equality with type coercion
            # Fix: CSV stores everything as strings, but WHERE may use ints/floats
            try:
                # Try to match the column's dtype
                col_dtype = df[field].dtype
                if col_dtype == 'object':  # String column
                    # Convert condition to string for comparison
                    mask = mask & (df[field].astype(str) == str(condition))
                else:
                    # Numeric column - try to convert condition to same type
                    mask = mask & (df[field] == condition)
            except (ValueError, TypeError):
                # Fallback: convert both to strings and compare
                mask = mask & (df[field].astype(str) == str(condition))

        return mask

    def _apply_operator_conditions(self, df, field, condition, mask):
        """Apply complex operator conditions to mask with type coercion."""
        for op, value in condition.items():
            op_upper = op.upper()

            # Special case: LIKE requires pattern conversion
            if op_upper in ("$LIKE", "LIKE"):
                pattern = value.replace("%", ".*").replace("_", ".")
                mask = mask & df[field].astype(str).str.match(pattern, na=False)
                continue

            # Special case: IN requires list check with type coercion
            if op_upper in ("$IN", "IN") and isinstance(value, list):
                try:
                    col_dtype = df[field].dtype
                    if col_dtype == 'object':  # String column
                        coerced_list = [str(v) for v in value]
                        mask = mask & df[field].astype(str).isin(coerced_list)
                    else:
                        mask = mask & df[field].isin(value)
                except (ValueError, TypeError):
                    coerced_list = [str(v) for v in value]
                    mask = mask & df[field].astype(str).isin(coerced_list)
                continue

            # Helper to apply operator with type coercion
            def apply_op(field, op_func_str, value):
                try:
                    col_dtype = df[field].dtype
                    if col_dtype == 'object':  # String column
                        # For comparison ops on strings, convert value to string
                        if op_func_str in ['==', '!=']:
                            return eval(f"df[field].astype(str) {op_func_str} str(value)")
                        else:
                            # For >, <, >=, <= on strings, use lexicographic comparison
                            return eval(f"df[field].astype(str) {op_func_str} str(value)")
                    else:
                        # Numeric column - use as-is
                        return eval(f"df[field] {op_func_str} value")
                except (ValueError, TypeError):
                    # Fallback: string comparison
                    return eval(f"df[field].astype(str) {op_func_str} str(value)")

            # Standard operators map with type coercion
            op_map = {
                "$EQ": lambda f, v: apply_op(f, '==', v),
                "=": lambda f, v: apply_op(f, '==', v),
                "$NE": lambda f, v: apply_op(f, '!=', v),
                "!=": lambda f, v: apply_op(f, '!=', v),
                "$GT": lambda f, v: apply_op(f, '>', v),
                ">": lambda f, v: apply_op(f, '>', v),
                "$GTE": lambda f, v: apply_op(f, '>=', v),
                ">=": lambda f, v: apply_op(f, '>=', v),
                "$LT": lambda f, v: apply_op(f, '<', v),
                "<": lambda f, v: apply_op(f, '<', v),
                "$LTE": lambda f, v: apply_op(f, '<=', v),
                "<=": lambda f, v: apply_op(f, '<=', v),
                "$NULL": lambda f, v: df[f].isna(),
                "$NOTNULL": lambda f, v: df[f].notna(),
            }

            op_func = op_map.get(op_upper)
            if op_func:
                mask = mask & op_func(field, value)
            else:
                self._log('warning', "Unsupported operator: %s", op)

        return mask

    def _create_or_mask(self, df, or_list):
        """Create OR mask from list of condition dicts."""
        or_mask = pd.Series([False] * len(df), index=df.index)

        for condition_dict in or_list:
            if not isinstance(condition_dict, dict):
                continue

            cond_mask = self._create_where_mask(df, condition_dict)
            or_mask = or_mask | cond_mask

        return or_mask

    def _apply_where_filter(self, df, where):
        """Apply WHERE clause filtering to DataFrame."""
        mask = self._create_where_mask(df, where)
        # Use .loc to avoid index alignment issues
        return df.loc[mask]

    def _apply_order(self, df, order):
        """Apply ORDER BY to DataFrame."""
        if isinstance(order, str):
            return self._apply_order_string(df, order)
        if isinstance(order, list):
            return self._apply_order_list(df, order)
        if isinstance(order, dict):
            return self._apply_order_dict(df, order)
        return df

    def _apply_order_string(self, df, order):
        """Apply ORDER BY from string format."""
        parts = order.split()
        field = parts[0]
        ascending = len(parts) == 1 or parts[1].upper() == "ASC"
        if field in df.columns:
            return df.sort_values(by=field, ascending=ascending)
        return df

    def _apply_order_list(self, df, order):
        """Apply ORDER BY from list format."""
        sort_fields = []
        sort_ascending = []

        for item in order:
            if isinstance(item, str):
                parts = item.split()
                field = parts[0]
                ascending = len(parts) == 1 or parts[1].upper() == "ASC"
                if field in df.columns:
                    sort_fields.append(field)
                    sort_ascending.append(ascending)
            elif isinstance(item, dict):
                for field, direction in item.items():
                    if field in df.columns:
                        sort_fields.append(field)
                        sort_ascending.append(direction.upper() != "DESC")

        if sort_fields:
            return df.sort_values(by=sort_fields, ascending=sort_ascending)
        return df

    def _apply_order_dict(self, df, order):
        """Apply ORDER BY from dict format."""
        sort_fields = []
        sort_ascending = []

        for field, direction in order.items():
            if field in df.columns:
                sort_fields.append(field)
                sort_ascending.append(direction.upper() != "DESC")

        if sort_fields:
            return df.sort_values(by=sort_fields, ascending=sort_ascending)
        return df

    def _join_tables(self, tables, joins=None, schema=None, auto_join=False):
        """Join multiple CSV tables using pandas merge."""
        if not tables or len(tables) < 2:
            return self._load_table(tables[0]) if tables else pd.DataFrame()

        # Load base table
        base_table = tables[0]
        result_df = self._load_table(base_table)

        # Add table prefix to columns to avoid conflicts
        result_df.columns = [f"{base_table}.{col}" for col in result_df.columns]

        remaining_tables = tables[1:]

        if auto_join and schema:
            # Auto-detect joins from FK relationships
            self._log('info', "[JOIN] Auto-joining CSV tables based on FK relationships")
            result_df = self._auto_join_csv(result_df, base_table, remaining_tables, schema)
        elif joins:
            # Manual join definitions
            self._log('info', "[JOIN] Building manual JOINs for CSV")
            result_df = self._manual_join_csv(result_df, base_table, joins)
        else:
            # Cross join (Cartesian product)
            self._log('warning', "[JOIN] Multiple tables without JOIN specification - using CROSS JOIN")
            for table_name in remaining_tables:
                right_df = self._load_table(table_name)
                right_df.columns = [f"{table_name}.{col}" for col in right_df.columns]
                result_df['_join_key'] = 1
                right_df['_join_key'] = 1
                result_df = result_df.merge(right_df, on='_join_key', how='outer')
                result_df = result_df.drop('_join_key', axis=1)

        return result_df

    def _auto_join_csv(self, base_df, base_table, remaining_tables, schema):
        """Auto-join CSV tables based on FK relationships."""
        result_df = base_df
        joined_tables = [base_table]

        for table_name in remaining_tables:
            right_df = self._load_table(table_name)
            right_df.columns = [f"{table_name}.{col}" for col in right_df.columns]

            ctx = {"right_df": right_df, "joined_tables": joined_tables, "schema": schema}

            # Try forward join (this table has FK to joined table)
            result_df, join_found = self._try_forward_join(result_df, table_name, ctx)

            # Try reverse join (joined table has FK to this table)
            if not join_found:
                result_df, join_found = self._try_reverse_join(result_df, table_name, ctx)

            if join_found:
                joined_tables.append(table_name)
            else:
                self._log('warning', "[JOIN] Could not auto-detect join for CSV table: %s", table_name)

        return result_df

    def _try_forward_join(self, result_df, table_name, ctx):
        """Try to join table that has FK to already-joined tables."""
        right_df = ctx["right_df"]
        joined_tables = ctx["joined_tables"]
        schema = ctx["schema"]
        table_schema = schema.get(table_name, {})

        for field_name, field_def in table_schema.items():
            if not isinstance(field_def, dict):
                continue

            fk = field_def.get("fk")
            if not fk:
                continue

            try:
                ref_table, ref_column = fk.split(".", 1)
            except ValueError:
                continue

            if ref_table in joined_tables:
                left_on = f"{ref_table}.{ref_column}"
                right_on = f"{table_name}.{field_name}"

                if left_on in result_df.columns and right_on in right_df.columns:
                    result_df = result_df.merge(
                        right_df, left_on=left_on, right_on=right_on, how='inner'
                    )
                    self._log('debug', "  Auto-detected CSV JOIN: %s.%s = %s.%s",
                               ref_table, ref_column, table_name, field_name)
                    return result_df, True

        return result_df, False

    def _try_reverse_join(self, result_df, table_name, ctx):
        """Try to join when already-joined table has FK to this table."""
        right_df = ctx["right_df"]
        joined_tables = ctx["joined_tables"]
        schema = ctx["schema"]

        for already_joined in joined_tables[:]:
            joined_schema = schema.get(already_joined, {})

            for field_name, field_def in joined_schema.items():
                if not isinstance(field_def, dict):
                    continue

                fk = field_def.get("fk")
                if not fk:
                    continue

                try:
                    ref_table, ref_column = fk.split(".", 1)
                except ValueError:
                    continue

                if ref_table == table_name:
                    left_on = f"{already_joined}.{field_name}"
                    right_on = f"{table_name}.{ref_column}"

                    if left_on in result_df.columns and right_on in right_df.columns:
                        result_df = result_df.merge(
                            right_df, left_on=left_on, right_on=right_on, how='inner'
                        )
                        self._log('debug', "  Auto-detected CSV JOIN (reverse): %s.%s = %s.%s",
                                   already_joined, field_name, table_name, ref_column)
                        return result_df, True

        return result_df, False

    def _manual_join_csv(self, base_df, base_table, joins):  # pylint: disable=unused-argument
        """Perform manual joins on CSV tables."""
        result_df = base_df

        for join_def in joins:
            join_type = join_def.get("type", "INNER").lower()
            table_name = join_def.get("table")
            on_clause = join_def.get("on")

            if not table_name or not on_clause:
                self._log('warning', "[JOIN] Skipping invalid CSV join: %s", join_def)
                continue

            right_df = self._load_table(table_name)
            right_df.columns = [f"{table_name}.{col}" for col in right_df.columns]

            # Parse ON clause: "users.id = posts.user_id"
            try:
                left_part, right_part = on_clause.split("=", 1)
                left_on = left_part.strip()
                right_on = right_part.strip()

                # Map SQL join types to pandas how parameter
                how_map = {
                    "inner": "inner",
                    "left": "left",
                    "right": "right",
                    "full": "outer",
                    "cross": "cross"
                }
                how = how_map.get(join_type, "inner")

                if how == "cross":
                    result_df['_join_key'] = 1
                    right_df['_join_key'] = 1
                    result_df = result_df.merge(right_df, on='_join_key', how='outer')
                    result_df = result_df.drop('_join_key', axis=1)
                else:
                    result_df = result_df.merge(
                        right_df,
                        left_on=left_on,
                        right_on=right_on,
                        how=how
                    )

                self._log('debug', "  Added CSV %s JOIN %s", join_type.upper(), table_name)
            except Exception as e:
                self._log('error', "Failed to parse CSV join ON clause '%s': %s", on_clause, e)

        return result_df

    def _resolve_field_names(self, fields, available_columns):
        """Resolve field names for multi-table queries."""
        resolved = []
        for field in fields:
            if field in available_columns:
                resolved.append(field)
            else:
                # Try to find a match with table prefix
                matches = [col for col in available_columns if col.endswith(f".{field}")]
                if matches:
                    resolved.append(matches[0])
                else:
                    self._log('warning', "Field '%s' not found in available columns", field)
        return resolved

    def get_connection_info(self):
        """Get connection information for CSV adapter."""
        return {
            "adapter": "CSVAdapter",
            "connected": self.is_connected(),
            "path": str(self.base_path),
            "tables_cached": len(self.tables),
            "tables_available": len(self.list_tables()) if self.base_path.exists() else 0,
        }
