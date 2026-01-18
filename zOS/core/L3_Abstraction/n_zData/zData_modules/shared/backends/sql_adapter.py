# zCLI/subsystems/zData/zData_modules/shared/backends/sql_adapter.py
"""
SQL base adapter providing shared operations for all SQL-based backends.

This module implements a powerful SQL adapter that extends BaseDataAdapter with
comprehensive SQL-building capabilities, including WHERE clause parsing, JOIN support,
and automatic relationship detection. It serves as the foundation for SQLite,
PostgreSQL, and other SQL-based backends.

Architecture Overview
--------------------
SQLAdapter sits between BaseDataAdapter and specific SQL implementations:

    BaseDataAdapter (ABC)
           ↓
      SQLAdapter (SQL operations + builders)
           ↓
    ┌──────┴──────┐
    ↓             ↓
SQLiteAdapter  PostgreSQLAdapter

**Design Philosophy:**
- **SQL Builder System:** Converts Python dicts to parameterized SQL
- **Dialect Agnostic:** Uses placeholders (?, %s) via hooks for different backends
- **AUTO JOIN Feature:** Detects relationships from schema foreign keys
- **Comprehensive WHERE:** Supports =, >, <, >=, <=, LIKE, IN, IS NULL, OR operators
- **Multi-table Queries:** JOIN, LEFT JOIN, INNER JOIN with manual or auto-detection

SQL Builder System
-----------------
The adapter provides 11 SQL builder methods that construct safe, parameterized queries:

**WHERE Clause Builder:**
- Converts dict to WHERE clause: {"age": 25} → "age = ?"
- Supports operators: {"age__gte": 18} → "age >= ?"
- Supports OR conditions: {"or": [{"city": "NYC"}, {"city": "LA"}]}
- Supports IN: {"city__in": ["NYC", "LA"]} → "city IN (?, ?)"
- Supports NULL checks: {"deleted__is_null": True} → "deleted IS NULL"

**JOIN Clause Builder:**
- Manual joins: joins=[{"table": "orders", "on": "users.id = orders.user_id"}]
- AUTO JOIN: Detects FK relationships from schema (forward and reverse)
- Supports INNER JOIN, LEFT JOIN, RIGHT JOIN

**Other Builders:**
- ORDER BY: order="age" or order=["-created_at", "name"]
- SELECT: Multi-table with table.field qualification
- Foreign Keys: ON DELETE CASCADE, ON UPDATE CASCADE

WHERE Clause Operators
---------------------
Supported operator suffixes in WHERE dict keys:

- **No suffix:** Equality (age: 25 → age = ?)
- **__gt:** Greater than (age__gt: 18 → age > ?)
- **__lt:** Less than (age__lt: 65 → age < ?)
- **__gte:** Greater or equal (age__gte: 18 → age >= ?)
- **__lte:** Less or equal (age__lte: 65 → age <= ?)
- **__like:** LIKE pattern (name__like: "John%" → name LIKE ?)
- **__in:** IN list (city__in: ["NYC", "LA"] → city IN (?, ?))
- **__is_null:** IS NULL check (deleted__is_null: True → deleted IS NULL)
- **__is_not_null:** IS NOT NULL check (active__is_not_null: True → active IS NOT NULL)

**OR Conditions:**
Use special "or" key with list of condition dicts:
```python
where = {
    "status": "active",
    "or": [
        {"city": "NYC"},
        {"city": "LA"}
    ]
}
# → status = ? AND (city = ? OR city = ?)
```

AUTO JOIN Feature
----------------
The adapter can automatically detect table relationships from schema foreign keys:

**Forward JOIN (FK in source table):**
```
users.company_id → companies.id
→ INNER JOIN companies ON users.company_id = companies.id
```

**Reverse JOIN (FK in target table):**
```
companies.id ← orders.company_id
→ INNER JOIN orders ON companies.id = orders.company_id
```

Enable with: `select(["users", "companies"], auto_join=True, schema=schema)`

Dialect Hooks
------------
Subclasses override these hooks for backend-specific SQL syntax:

- **_get_placeholders(count):** Return "?, ?, ?" (SQLite) or "%s, %s, %s" (PostgreSQL)
- **_get_single_placeholder():** Return "?" (SQLite) or "%s" (PostgreSQL)
- **_get_last_insert_id(cursor):** Return cursor.lastrowid (SQLite) or use RETURNING (PostgreSQL)

Usage Examples
-------------
Basic CRUD:
    >>> adapter = SQLiteAdapter(config, logger)
    >>> adapter.connect()
    
    >>> # Insert
    >>> row_id = adapter.insert("users", ["name", "age"], ["John", 30])
    
    >>> # Select with WHERE
    >>> rows = adapter.select("users", where={"age__gte": 18})
    
    >>> # Update
    >>> adapter.update("users", ["age"], [31], where={"id": row_id})
    
    >>> # Delete
    >>> adapter.delete("users", where={"age__lt": 18})

Multi-table queries:
    >>> # Manual JOIN
    >>> joins = [{"table": "orders", "on": "users.id = orders.user_id"}]
    >>> rows = adapter.select(["users", "orders"], joins=joins)
    
    >>> # AUTO JOIN (requires schema)
    >>> rows = adapter.select(
    ...     ["users", "companies"],
    ...     auto_join=True,
    ...     schema=schema
    ... )

Integration
----------
This SQL adapter is extended by:
- sqlite_adapter.py: SQLite-specific implementation
- postgresql_adapter.py: PostgreSQL-specific implementation

Used by:
- classical_data.py: CRUD orchestration
- data_operations.py: High-level operations

See Also
--------
- base_adapter.py: Abstract base class
- sqlite_adapter.py: SQLite implementation
- postgresql_adapter.py: PostgreSQL implementation
"""

from abc import abstractmethod
from zOS import Dict, List, Optional, Any
from .base_adapter import BaseDataAdapter

# ============================================================
# Module Constants - SQL Keywords
# ============================================================

_SQL_SELECT = "SELECT"
_SQL_INSERT = "INSERT"
_SQL_UPDATE = "UPDATE"
_SQL_DELETE = "DELETE"
_SQL_CREATE = "CREATE"
_SQL_ALTER = "ALTER"
_SQL_DROP = "DROP"
_SQL_WHERE = "WHERE"
_SQL_ORDER = "ORDER BY"
_SQL_LIMIT = "LIMIT"
_SQL_JOIN = "JOIN"
_SQL_INNER_JOIN = "INNER JOIN"
_SQL_LEFT_JOIN = "LEFT JOIN"
_SQL_FROM = "FROM"
_SQL_INTO = "INTO"
_SQL_VALUES = "VALUES"

# ============================================================
# Module Constants - SQL Operators
# ============================================================

_OP_EQ = "="
_OP_GT = ">"
_OP_LT = "<"
_OP_GTE = ">="
_OP_LTE = "<="
_OP_LIKE = "LIKE"
_OP_IN = "IN"
_OP_IS_NULL = "IS NULL"
_OP_IS_NOT_NULL = "IS NOT NULL"
_OP_AND = "AND"
_OP_OR = "OR"

# Operator suffixes for WHERE clause parsing
_SUFFIX_GT = "__gt"
_SUFFIX_LT = "__lt"
_SUFFIX_GTE = "__gte"
_SUFFIX_LTE = "__lte"
_SUFFIX_LIKE = "__like"
_SUFFIX_IN = "__in"
_SUFFIX_IS_NULL = "__is_null"
_SUFFIX_IS_NOT_NULL = "__is_not_null"

# ============================================================
# Module Constants - Constraints
# ============================================================

_CONSTRAINT_PRIMARY_KEY = "PRIMARY KEY"
_CONSTRAINT_FOREIGN_KEY = "FOREIGN KEY"
_CONSTRAINT_UNIQUE = "UNIQUE"
_CONSTRAINT_NOT_NULL = "NOT NULL"
_CONSTRAINT_DEFAULT = "DEFAULT"

# ============================================================
# Module Constants - Join Types
# ============================================================

_JOIN_INNER = "INNER"
_JOIN_LEFT = "LEFT"
_JOIN_RIGHT = "RIGHT"
_JOIN_FULL = "FULL"

# ============================================================
# Module Constants - Index Types
# ============================================================

_INDEX_SIMPLE = "simple"
_INDEX_UNIQUE = "unique"
_INDEX_COMPOSITE = "composite"

# ============================================================
# Module Constants - Schema Keys
# ============================================================

_SCHEMA_KEY_PRIMARY_KEY = "primary_key"
_SCHEMA_KEY_INDEXES = "indexes"
_SCHEMA_KEY_TYPE = "type"
_SCHEMA_KEY_PK = "pk"
_SCHEMA_KEY_UNIQUE = "unique"
_SCHEMA_KEY_REQUIRED = "required"
_SCHEMA_KEY_FK = "fk"
_SCHEMA_KEY_DEFAULT = "default"

# ============================================================
# Module Constants - WHERE Keys
# ============================================================

_WHERE_KEY_OR = "or"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_TABLE_NOT_FOUND = "Table '{table}' does not exist"
_ERR_COLUMN_NOT_FOUND = "Column '{column}' not found in table '{table}'"
_ERR_FK_INVALID = "Invalid foreign key format: {fk}"
_ERR_JOIN_MISSING_ON = "JOIN requires 'on' clause"
_ERR_DROP_COLUMN_UNSUPPORTED = "DROP COLUMN not supported by this SQL dialect"
_ERR_UPSERT_MISSING_CONFLICT = "UPSERT requires conflict_fields"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_CREATE_TABLE = "Creating table: %s"
_LOG_TABLE_CREATED = "Table created: %s"
_LOG_DROP_TABLE = "Dropping table: %s"
_LOG_ALTER_TABLE = "Executing ALTER TABLE: %s"
_LOG_ALTER_COMPLETE = "Altered table (%s): %s"
_LOG_INSERT_ROW = "Inserted row into %s with ID: %s"
_LOG_SELECT_ROWS = "Selected %d rows from %s"
_LOG_UPDATE_ROWS = "Updated %d rows in %s"
_LOG_DELETE_ROWS = "Deleted %d rows from %s"
_LOG_UPSERT_ROW = "Upserted row into %s with ID: %s"
_LOG_CREATE_INDEX = "Creating index: %s"
_LOG_JOIN_MULTI_TABLE = "[JOIN] Multi-table query: %s"
_LOG_JOIN_AUTO_FORWARD = "  Auto-detected (forward): %s"
_LOG_JOIN_AUTO_REVERSE = "  Auto-detected (reverse): %s"
_LOG_COMPOSITE_PK = "Composite primary key detected: %s"
_LOG_ADD_COMPOSITE_PK = "Adding composite PRIMARY KEY (%s)"

# ============================================================
# Public API
# ============================================================

__all__ = ["SQLAdapter"]

class SQLAdapter(BaseDataAdapter):
    """
    SQL base adapter with comprehensive SQL-building and multi-table query support.
    
    This class extends BaseDataAdapter to provide concrete SQL operations for all
    SQL-based backends. It implements sophisticated SQL builders for WHERE clauses,
    JOINs, and multi-table queries with automatic relationship detection.
    
    Architecture
    -----------
    SQLAdapter provides:
    - **Abstract Methods (3):** connect(), disconnect(), get_cursor() - backend-specific
    - **Concrete DDL (5):** create_table(), drop_table(), alter_table(), table_exists(), list_tables()
    - **Concrete DML (5):** insert(), select(), update(), delete(), upsert()
    - **Concrete TCL (3):** begin_transaction(), commit(), rollback()
    - **SQL Builders (11):** WHERE, JOIN, ORDER, SELECT builders with operator support
    - **Dialect Hooks (3):** _get_placeholders(), _get_single_placeholder(), _get_last_insert_id()
    
    Key Features
    -----------
    **1. Comprehensive WHERE Builder:**
    - Equality: {"age": 25}
    - Comparison: {"age__gte": 18, "age__lt": 65}
    - LIKE: {"name__like": "John%"}
    - IN: {"city__in": ["NYC", "LA"]}
    - NULL checks: {"deleted__is_null": True}
    - OR conditions: {"or": [{"city": "NYC"}, {"city": "LA"}]}
    
    **2. AUTO JOIN Feature:**
    Detects table relationships from schema foreign keys:
    - Forward FK: users.company_id → companies.id
    - Reverse FK: companies.id ← orders.company_id
    
    **3. Multi-table Queries:**
    Supports manual JOINs and AUTO JOIN for complex queries:
    - select(["users", "orders"], joins=[...])
    - select(["users", "companies"], auto_join=True, schema=schema)
    
    **4. Composite Primary Keys:**
    Table-level PRIMARY KEY constraints for multi-column PKs
    
    **5. Foreign Key Support:**
    ON DELETE CASCADE, ON UPDATE CASCADE actions
    
    **6. Index Creation:**
    Simple, composite, and unique indexes
    
    Subclass Implementation Guide
    ----------------------------
    To create a new SQL backend (e.g., MySQL):
    
    1. **Inherit from SQLAdapter**
    2. **Implement 3 abstract methods:** connect(), disconnect(), get_cursor()
    3. **Override dialect hooks (optional):**
       - _get_placeholders(): Return "%s, %s" instead of "?, ?"
       - _get_last_insert_id(): Use backend-specific method
    4. **Override upsert() (optional):** Use backend-specific UPSERT syntax
    
    Attributes:
        db_path (Path): Full path to database file (for file-based backends)
        All BaseDataAdapter attributes (connection, cursor, config, logger, etc.)
    
    Example:
        >>> adapter = SQLiteAdapter(config, logger=logger)
        >>> adapter.connect()
        >>> rows = adapter.select("users", where={"age__gte": 18}, order="name")
    """

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[Any] = None
    ) -> None:
        """
        Initialize SQL adapter with configuration.
        
        Args:
            config: Configuration dict (see BaseDataAdapter)
            logger: Optional logger instance
        
        Attributes Set:
            db_path: Constructed from base_path + data_label + ".db"
        
        Example:
            >>> config = {"path": "/data", "label": "mydb"}
            >>> adapter = SQLiteAdapter(config, logger=logger)
            >>> # adapter.db_path = Path("/data/mydb.db")
        """
        super().__init__(config, logger)
        # Construct db_path from folder + label
        self.db_path = self.base_path / f"{self.data_label}.db"
    
    # ============================================================
    # Abstract Methods (Backend-Specific)
    # ============================================================

    @abstractmethod
    def connect(self) -> None:
        """
        Establish database connection (backend-specific).
        
        Subclasses must implement this to create backend-specific connections.
        See BaseDataAdapter.connect() for full documentation.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close database connection (backend-specific).
        
        Subclasses must implement this to close backend-specific connections.
        See BaseDataAdapter.disconnect() for full documentation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_cursor(self) -> Any:
        """
        Get or create cursor (backend-specific).
        
        Subclasses must implement this to return backend-specific cursor objects.
        See BaseDataAdapter.get_cursor() for full documentation.
        """
        raise NotImplementedError
    
    # ============================================================
    # DDL - Data Definition Language
    # ============================================================

    def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """Create table with given schema."""
        self._log('info', _LOG_CREATE_TABLE, table_name)

        cur = self.get_cursor()
        field_defs = []
        foreign_keys = []

        # Check for composite primary key
        composite_pk = None
        if _SCHEMA_KEY_PRIMARY_KEY in schema:
            pk_value = schema[_SCHEMA_KEY_PRIMARY_KEY]
            if isinstance(pk_value, list) and len(pk_value) > 0:
                composite_pk = pk_value
                self._log('info', LOG_COMPOSITE_PK, composite_pk)

        # Process each field
        for field_name, attrs in schema.items():
            if field_name in [_SCHEMA_KEY_PRIMARY_KEY, _SCHEMA_KEY_INDEXES]:
                continue

            if not isinstance(attrs, dict):
                continue

            # Map type
            field_type = self._map_field_type(attrs.get(SCHEMA_KEY_TYPE, "str"))
            column = f"{field_name} {field_type}"

            # Only add column-level PRIMARY KEY if no composite PK
            if attrs.get(_SCHEMA_KEY_PK) and not composite_pk:
                column += f" {_CONSTRAINT_PRIMARY_KEY}"
            if attrs.get(SCHEMA_KEY_UNIQUE):
                column += f" {CONSTRAINT_UNIQUE}"
            if attrs.get(SCHEMA_KEY_REQUIRED) is True:
                column += f" {CONSTRAINT_NOT_NULL}"

            field_defs.append(column)

            # Handle foreign keys
            if SCHEMA_KEY_FK in attrs:
                fk_clause = self._build_foreign_key_clause(field_name, attrs)
                if fk_clause:
                    foreign_keys.append(fk_clause)

        # Add composite primary key as table-level constraint
        table_constraints = []
        if composite_pk:
            pk_columns = ", ".join(composite_pk)
            table_constraints.append(f"{_CONSTRAINT_PRIMARY_KEY} ({pk_columns})")
            self._log('info', LOG_ADD_COMPOSITE_PK, pk_columns)

        # Build and execute DDL
        all_defs = field_defs + table_constraints + foreign_keys
        ddl = f"{SQL_CREATE} TABLE {table_name} ({', '.join(all_defs)});"

        self._log('info', "Executing DDL: %s", ddl)
        cur.execute(ddl)
        self.connection.commit()
        self._log('info', _LOG_TABLE_CREATED, table_name)

        # Create indexes if specified
        if SCHEMA_KEY_INDEXES in schema:
            self._create_indexes(table_name, schema[SCHEMA_KEY_INDEXES])

    def drop_table(self, table_name: str) -> None:
        """Drop table from database."""
        cur = self.get_cursor()
        sql = f"DROP TABLE IF EXISTS {table_name}"
        self._log('info', "Dropping table: %s", table_name)
        cur.execute(sql)
        self.connection.commit()

        # Hook for subclass-specific cleanup
        self._after_drop_table(table_name)

    def _after_drop_table(self, table_name):
        """Hook for subclass-specific cleanup after dropping table."""

    def alter_table(self, table_name, changes):
        """Alter table structure (add/drop columns)."""
        cur = self.get_cursor()

        # Handle ADD COLUMN
        if "add_columns" in changes:
            for column_name, column_def in changes["add_columns"].items():
                sql = self._build_add_column_sql(table_name, column_name, column_def)
                self._log('info', "Executing ALTER TABLE: %s", sql)
                cur.execute(sql)
            self.connection.commit()
            self._log('info', "Altered table (add columns): %s", table_name)

        # Handle DROP COLUMN (if supported by dialect)
        if "drop_columns" in changes:
            if self._supports_drop_column():
                for column_name in changes["drop_columns"]:
                    sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
                    self._log('info', "Executing ALTER TABLE: %s", sql)
                    cur.execute(sql)
                self.connection.commit()
                self._log('info', "Altered table (drop columns): %s", table_name)
            else:
                self._log('warning', "DROP COLUMN not supported by this SQL dialect")

        # Handle MODIFY COLUMN (if supported by dialect)
        if "modify_columns" in changes:
            if self._supports_modify_column():
                for column_name, new_def in changes["modify_columns"].items():
                    sql = self._build_modify_column_sql(table_name, column_name, new_def)
                    self._log('info', "Executing ALTER TABLE: %s", sql)
                    cur.execute(sql)
                self.connection.commit()
                self._log('info', "Altered table (modify columns): %s", table_name)
            else:
                self._log('warning', "MODIFY COLUMN not supported by this SQL dialect")

    def _build_add_column_sql(self, table_name, column_name, column_def):
        """Build ADD COLUMN SQL statement."""
        field_type = self._map_field_type(column_def.get("type", "str"))
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {field_type}"

        # Add DEFAULT if specified
        if column_def.get("default") is not None:
            default = column_def.get("default")
            sql += f" DEFAULT {default}"

        return sql

    def _supports_drop_column(self):
        """Check if SQL dialect supports DROP COLUMN."""
        return True  # Most SQL databases support DROP COLUMN

    def _supports_modify_column(self):
        """Check if SQL dialect supports MODIFY COLUMN."""
        return True  # Most SQL databases support MODIFY COLUMN

    def _build_modify_column_sql(self, table_name, column_name, new_def):
        """Build MODIFY COLUMN SQL statement."""
        # Build the new column definition
        col_def = self._build_column_definition(column_name, new_def)
        return f"ALTER TABLE {table_name} MODIFY COLUMN {col_def}"

    def table_exists(self, table_name):
        """Check if table exists (must be overridden)."""
        raise NotImplementedError("Subclass must implement table_exists()")

    def list_tables(self):
        """List all tables (must be overridden)."""
        raise NotImplementedError("Subclass must implement list_tables()")

    def insert(self, table, fields, values):
        """Insert row into table."""
        cur = self.get_cursor()
        placeholders = self._get_placeholders(len(fields))
        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"

        self._log('debug', "Executing INSERT: %s with values: %s", sql, values)
        cur.execute(sql, values)
        self.connection.commit()

        row_id = self._get_last_insert_id(cur)
        self._log('info', "Inserted row into %s with ID: %s", table, row_id)
        return row_id

    def select(self, table, fields=None, **kwargs):
        """Select rows from table(s) with optional JOIN support."""
        where = kwargs.get('where')
        joins = kwargs.get('joins')
        order = kwargs.get('order')
        limit = kwargs.get('limit')
        offset = kwargs.get('offset')
        auto_join = kwargs.get('auto_join', False)
        schema = kwargs.get('schema')

        cur = self.get_cursor()

        # Handle multi-table queries
        tables = [table] if isinstance(table, str) else table
        is_multi_table = len(tables) > 1 or joins

        if is_multi_table:
            # Build FROM clause with JOINs
            from_clause, _ = self._build_join_clause(
                tables, joins=joins, schema=schema, auto_join=auto_join
            )

            # Build SELECT clause with table qualifiers for multi-table
            select_clause = self._build_select_clause(fields, tables)

            self._log('info', "[JOIN] Multi-table query: %s", " + ".join(tables))
        else:
            # Single table query (existing logic)
            from_clause = table
            select_clause = "*" if not fields or fields == ["*"] else ", ".join(fields)

        sql = f"SELECT {select_clause} FROM {from_clause}"
        params = []

        # Build WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            sql += f" WHERE {where_clause}"
            params.extend(where_params)

        # Build ORDER BY clause
        if order:
            order_clause = self._build_order_clause(order)
            sql += f" ORDER BY {order_clause}"

        # Build LIMIT clause
        if limit:
            sql += f" LIMIT {limit}"
            # Add OFFSET clause (only applies if LIMIT is specified - SQL standard)
            if offset:
                sql += f" OFFSET {offset}"

        self._log('debug', "Executing SELECT: %s with params: %s", sql, params)
        cur.execute(sql, params)
        raw_rows = cur.fetchall()

        # Convert rows to dicts for consistent display across backends
        # Get column names from cursor description
        if raw_rows and cur.description:
            column_names = [desc[0] for desc in cur.description]
            rows = [dict(zip(column_names, row)) for row in raw_rows]
        else:
            rows = []

        table_name = " + ".join(tables) if is_multi_table else table
        self._log('info', "Selected %d rows from %s", len(rows), table_name)
        return rows

    def update(self, table, fields, values, where):
        """Update rows in table."""
        cur = self.get_cursor()

        # Build SET clause with dialect-specific placeholders
        placeholder = self._get_single_placeholder()
        set_clause = ", ".join([f"{field} = {placeholder}" for field in fields])
        sql = f"UPDATE {table} SET {set_clause}"
        params = list(values)

        # Build WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            sql += f" WHERE {where_clause}"
            params.extend(where_params)

        self._log('debug', "Executing UPDATE: %s with params: %s", sql, params)
        cur.execute(sql, params)
        self.connection.commit()

        rows_affected = cur.rowcount
        self._log('info', "Updated %d rows in %s", rows_affected, table)
        return rows_affected

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """Delete rows from table."""
        cur = self.get_cursor()

        sql = f"{SQL_DELETE} {SQL_FROM} {table}"
        params = []

        # Build WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            sql += f" {_SQL_WHERE} {where_clause}"
            params.extend(where_params)

        self._log('debug', "Executing DELETE: %s with params: %s", sql, params)
        cur.execute(sql, params)
        self.connection.commit()

        rows_affected = cur.rowcount
        self._log('info', LOG_DELETE_ROWS, rows_affected, table)
        return rows_affected

    def upsert(
        self,
        table: str,
        fields: List[str],
        values: List[Any],
        conflict_fields: List[str]
    ) -> Any:
        """
        Insert row or update if conflict on specified fields (UPSERT).
        
        This default implementation uses SQLite 3.24+ syntax (INSERT...ON CONFLICT).
        Subclasses should override for backend-specific UPSERT syntax.
        
        Args:
            table: Table name
            fields: List of field names
            values: List of values (must match fields)
            conflict_fields: Fields to check for conflicts (usually pk or unique fields)
        
        Returns:
            Row ID of inserted/updated row
        
        Raises:
            ValueError: If conflict_fields not provided
        
        Example:
            >>> # Insert or update by id
            >>> row_id = adapter.upsert(
            ...     "users",
            ...     ["id", "name", "age"],
            ...     [1, "John", 30],
            ...     conflict_fields=["id"]
            ... )
        
        Notes:
            - SQLite 3.24+ required for ON CONFLICT
            - PostgreSQL should override to use ON CONFLICT DO UPDATE
            - MySQL should override to use ON DUPLICATE KEY UPDATE
        """
        if not conflict_fields:
            raise ValueError(ERR_UPSERT_MISSING_CONFLICT)
        
        cur = self.get_cursor()
        
        # Build INSERT clause
        placeholders = self._get_placeholders(len(fields))
        field_list = ", ".join(fields)
        sql = f"{_SQL_INSERT} {_SQL_INTO} {table} ({field_list}) {_SQL_VALUES} ({placeholders})"
        
        # Build ON CONFLICT clause (SQLite 3.24+ syntax)
        conflict_list = ", ".join(conflict_fields)
        
        # Build UPDATE clause (exclude conflict fields from update)
        update_fields = [f for f in fields if f not in conflict_fields]
        if update_fields:
            update_clause = ", ".join([f"{f} = excluded.{f}" for f in update_fields])
            sql += f" ON CONFLICT({conflict_list}) DO UPDATE SET {update_clause}"
        else:
            # All fields are conflict fields, just ignore conflicts
            sql += f" ON CONFLICT({conflict_list}) DO NOTHING"
        
        self._log('debug', "Executing UPSERT: %s with values: %s", sql, values)
        cur.execute(sql, values)
        self.connection.commit()
        
        row_id = self._get_last_insert_id(cur)
        self._log('info', LOG_UPSERT_ROW, table, row_id)
        return row_id

    def aggregate(
        self,
        table: str,
        function: str,
        field: Optional[str] = None,
        where: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None
    ) -> Any:
        """
        Perform aggregation function on table data using SQL.
        
        Executes SQL aggregate functions (COUNT, SUM, AVG, MIN, MAX) with optional
        WHERE filtering and GROUP BY grouping. Returns scalar for simple aggregations
        or dict for grouped aggregations.
        
        Supported functions:
        - count: Count rows (field optional, defaults to *)
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
            - Uses parameterized queries for safety
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
        
        # Build aggregation expression
        if function_lower == "count":
            agg_expr = f"COUNT({field if field else '*'})"
        else:
            agg_expr = f"{function_lower.upper()}({field})"
        
        # Build SELECT clause
        if group_by:
            sql = f"SELECT {group_by}, {agg_expr} FROM {table}"
        else:
            sql = f"SELECT {agg_expr} FROM {table}"
        
        # Build WHERE clause if provided
        params = []
        if where:
            where_clause, where_params = self._build_where_clause(where)
            sql += f" WHERE {where_clause}"
            params.extend(where_params)
        
        # Add GROUP BY if provided
        if group_by:
            sql += f" GROUP BY {group_by}"
        
        self._log('debug', f"Executing aggregation: {sql} with params: {params}")
        
        # Execute query
        cur = self.get_cursor()
        try:
            cur.execute(sql, params)
            
            if group_by:
                # GROUP BY: return dict {group_value: aggregate_value}
                rows = cur.fetchall()
                result = {}
                for row in rows:
                    group_val = row[0]
                    agg_val = row[1]
                    result[group_val] = agg_val
                self._log('info', f"Aggregation {function}({field or '*'}) on {table} grouped by {group_by}: {len(result)} groups")
                return result
            else:
                # Simple aggregation: return scalar
                row = cur.fetchone()
                result = row[0] if row and row[0] is not None else (0 if function_lower == "count" else None)
                self._log('info', f"Aggregation {function}({field or '*'}) on {table}: {result}")
                return result
                
        except Exception as e:
            self._log('error', f"Aggregation failed: {e}")
            raise RuntimeError(f"Aggregation query failed: {e}")

    def map_type(self, abstract_type: str) -> str:
        """
        Map abstract schema type to SQL type (public interface).
        
        This method satisfies the BaseDataAdapter interface requirement.
        Delegates to _map_field_type() for actual mapping.
        
        Args:
            abstract_type: Abstract type (str, int, float, bool, datetime, json)
        
        Returns:
            SQL type string (TEXT, INTEGER, REAL, etc.)
        
        Example:
            >>> adapter.map_type("str")
            "TEXT"
            >>> adapter.map_type("int")
            "INTEGER"
        """
        return self._map_field_type(abstract_type)
    
    # ============================================================
    # TCL - Transaction Control Language
    # ============================================================

    def begin_transaction(self) -> None:
        """Begin transaction."""
        if self.connection:
            self.connection.execute("BEGIN")
            self._log('debug', "Transaction started")

    def commit(self):
        """Commit current transaction."""
        if self.connection:
            self.connection.commit()
            self._log('debug', "Transaction committed")

    def rollback(self):
        """Rollback current transaction."""
        if self.connection:
            self.connection.rollback()
            self._log('debug', "Transaction rolled back")

    def _build_foreign_key_clause(self, field_name, attrs):
        """Build FOREIGN KEY clause."""
        if "fk" not in attrs:
            return None

        ref_table, ref_col = attrs["fk"].split(".")
        fk_clause = f"FOREIGN KEY ({field_name}) REFERENCES {ref_table}({ref_col})"

        # Add ON DELETE action if specified
        on_delete = attrs.get("on_delete")
        if on_delete:
            valid_actions = ["CASCADE", "RESTRICT", "SET NULL", "SET DEFAULT", "NO ACTION"]
            on_delete_upper = on_delete.upper()
            if on_delete_upper in valid_actions:
                fk_clause += f" ON DELETE {on_delete_upper}"
            else:
                self._log('warning', "Invalid on_delete action '%s' for field '%s'",
                         on_delete, field_name)

        return fk_clause

    def _build_where_clause(self, where):
        """Build WHERE clause from dict or string with operator support."""
        conditions = []
        params = []
        
        # If where is a string, return it directly
        if isinstance(where, str):
            return where, []

        for field, value in where.items():
            # Handle OR conditions
            if field.upper() in ("$OR", "OR"):
                if isinstance(value, list) and value:
                    or_conditions, or_params = self._build_or_conditions(value)
                    if or_conditions:
                        conditions.append(f"({or_conditions})")
                        params.extend(or_params)
                continue

            # Handle IS NULL
            if value is None:
                conditions.append(f"{field} IS NULL")
                continue

            # Handle IN operator (list values)
            if isinstance(value, list):
                if value:
                    placeholders = ", ".join([self._get_single_placeholder() for _ in value])
                    conditions.append(f"{field} IN ({placeholders})")
                    params.extend(value)
                continue

            # Handle complex operators (dict values)
            if isinstance(value, dict):
                cond, cond_params = self._build_operator_condition(field, value)
                if cond:
                    conditions.append(cond)
                    params.extend(cond_params)
                continue

            # Simple equality
            conditions.append(f"{field} = {self._get_single_placeholder()}")
            params.append(value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

    def _build_operator_condition(self, field, value_dict):
        """Build condition from operator dict."""
        conditions = []
        params = []

        for op, val in value_dict.items():
            op_upper = op.upper()

            if op_upper in ("$LIKE", "LIKE"):
                conditions.append(f"{field} LIKE {self._get_single_placeholder()}")
                params.append(val)
            elif op_upper in ("$IN", "IN") and isinstance(val, list) and val:
                placeholders = ", ".join([self._get_single_placeholder() for _ in val])
                conditions.append(f"{field} IN ({placeholders})")
                params.extend(val)
            elif op_upper == "$NULL" or (op_upper == "IS" and val is None):
                conditions.append(f"{field} IS NULL")
            elif op_upper == "$NOTNULL" or (op_upper == "IS NOT" and val is None):
                conditions.append(f"{field} IS NOT NULL")
            else:
                sql_op = self._map_operator(op)
                conditions.append(f"{field} {sql_op} {self._get_single_placeholder()}")
                params.append(val)

        return " AND ".join(conditions), params

    def _build_or_conditions(self, or_list):
        """Build OR conditions from list of condition dicts."""
        or_conditions = []
        or_params = []

        for condition_dict in or_list:
            if not isinstance(condition_dict, dict):
                continue

            conds, cond_params = self._build_where_clause(condition_dict)
            if conds and conds != "1=1":
                or_conditions.append(conds)
                or_params.extend(cond_params)

        or_clause = " OR ".join(or_conditions)
        return or_clause, or_params

    def _map_operator(self, op):
        """Map operator to SQL."""
        operator_map = {
            "$eq": "=",
            "$ne": "!=",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$like": "LIKE",
            "$in": "IN",
        }
        return operator_map.get(op, "=")

    def _build_order_clause(self, order):
        """Build ORDER BY clause from dict or list."""
        if isinstance(order, str):
            return order
        elif isinstance(order, list):
            return ", ".join(order)
        elif isinstance(order, dict):
            parts = []
            for field, direction in order.items():
                dir_str = "DESC" if direction.upper() == "DESC" else "ASC"
                parts.append(f"{field} {dir_str}")
            return ", ".join(parts)
        return ""

    def _build_select_clause(self, fields, tables):
        """Build SELECT clause with table qualifiers for multi-table queries."""
        if not fields or fields == ["*"]:
            # For *, use table.* for each table to avoid ambiguity
            if len(tables) > 1:
                return ", ".join([f"{table}.*" for table in tables])
            return "*"

        # Fields may already have table prefixes, just join them
        return ", ".join(fields)

    def _build_join_clause(self, tables, joins=None, schema=None, auto_join=False):
        """Build JOIN clause for multi-table queries (manual or auto-detected)."""
        if not tables or len(tables) < 2:
            # Single table - no joins needed
            return tables[0] if tables else "", []

        base_table = tables[0]
        from_clause = base_table
        joined_tables = []

        if auto_join and schema:
            # Auto-detect joins from foreign key relationships
            self._log('info', "[JOIN] Auto-joining tables based on FK relationships")
            from_clause, joined_tables = self._build_auto_join(tables, schema, base_table)
        elif joins:
            # Manual join definitions
            self._log('info', "[JOIN] Building manual JOIN clauses")
            from_clause, joined_tables = self._build_manual_join(base_table, joins)
        else:
            # Multiple tables but no join specification - use CROSS JOIN
            self._log('warning', "[JOIN] Multiple tables without JOIN specification - using CROSS JOIN")
            join_parts = [f"CROSS JOIN {table}" for table in tables[1:]]
            from_clause = f"{base_table} {' '.join(join_parts)}"
            joined_tables = tables[1:]

        self._log('debug', "Built FROM clause: %s", from_clause)
        return from_clause, joined_tables

    def _build_manual_join(self, base_table, joins):
        """Build JOIN clause from manual join definitions."""
        from_clause = base_table
        joined_tables = []

        for join_def in joins:
            join_type = join_def.get("type", "INNER").upper()
            table = join_def.get("table")
            on_clause = join_def.get("on")

            if not table or not on_clause:
                self._log('warning', "[JOIN] Skipping invalid join definition: %s", join_def)
                continue

            # Validate join type
            valid_types = ["INNER", "LEFT", "RIGHT", "FULL", "CROSS"]
            if join_type not in valid_types:
                self._log('warning', "[JOIN] Invalid join type '%s', using INNER", join_type)
                join_type = "INNER"

            # Handle FULL OUTER JOIN
            if join_type == "FULL":
                join_type = "FULL OUTER"

            # Build join clause
            if join_type == "CROSS":
                from_clause += f" CROSS JOIN {table}"
            else:
                from_clause += f" {join_type} JOIN {table} ON {on_clause}"

            joined_tables.append(table)
            self._log('debug', "  Added %s JOIN %s", join_type, table)

        return from_clause, joined_tables

    def _build_auto_join(self, tables, schema, base_table):
        """Auto-detect and build JOIN clauses from FK relationships."""
        from_clause = base_table
        joined_tables = []
        remaining_tables = [t for t in tables if t != base_table]

        for table in remaining_tables:
            # Try forward join (table has FK to joined tables)
            join_clause = self._try_forward_join_sql(table, base_table, joined_tables, schema)

            # Try reverse join (joined table has FK to this table)
            if not join_clause:
                join_clause = self._try_reverse_join_sql(table, base_table, joined_tables, schema)

            if join_clause:
                from_clause += join_clause
                joined_tables.append(table)
            else:
                self._log('warning', "[JOIN] Could not auto-detect join for table: %s", table)

        return from_clause, joined_tables

    def _try_forward_join_sql(self, table, base_table, joined_tables, schema):
        """Try to join table that has FK to already-joined tables."""
        table_schema = schema.get(table, {})

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

            if ref_table == base_table or ref_table in joined_tables:
                on_clause = f"{table}.{field_name} = {ref_table}.{ref_column}"
                self._log('debug', "  Auto-detected: INNER JOIN %s ON %s", table, on_clause)
                return f" INNER JOIN {table} ON {on_clause}"

        return None

    def _try_reverse_join_sql(self, table, base_table, joined_tables, schema):
        """Try to join when already-joined table has FK to this table."""
        for already_joined in [base_table] + joined_tables:
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

                if ref_table == table:
                    on_clause = f"{already_joined}.{field_name} = {table}.{ref_column}"
                    self._log('debug', "  Auto-detected (reverse): INNER JOIN %s ON %s", table, on_clause)
                    return f" INNER JOIN {table} ON {on_clause}"

        return None

    def _map_field_type(self, raw_type):
        """Map field type string to SQL type."""
        raw_type = str(raw_type).strip()

        if raw_type.startswith("str"):
            return "TEXT"
        if raw_type.startswith("int"):
            return "INTEGER"
        if raw_type.startswith("float"):
            return "REAL"
        if raw_type.startswith("datetime"):
            return "TEXT"
        if raw_type.startswith("bool"):
            return "INTEGER"
        return self.map_type(raw_type)

    def _create_indexes(self, table_name, indexes):
        """Create indexes for table."""
        cur = self.get_cursor()

        for idx_spec in indexes:
            if isinstance(idx_spec, str):
                idx_name = f"idx_{table_name}_{idx_spec}"
                sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx_spec})"
            elif isinstance(idx_spec, dict):
                fields = idx_spec.get("fields", [])
                if isinstance(fields, str):
                    fields = [fields]

                idx_name = idx_spec.get("name", f"idx_{table_name}_{'_'.join(fields)}")
                unique = "UNIQUE " if idx_spec.get("unique") else ""

                sql = f"CREATE {unique}INDEX IF NOT EXISTS {idx_name} ON {table_name} ({', '.join(fields)})"
            else:
                self._log('warning', "Invalid index specification: %s", idx_spec)
                continue

            self._log('info', "Creating index: %s", sql)
            cur.execute(sql)

        self.connection.commit()

    def _get_placeholders(self, count):
        """Get parameter placeholders (?, ?, ? or %s, %s, %s)."""
        return ", ".join(["?" for _ in range(count)])

    def _get_single_placeholder(self):
        """Get single parameter placeholder (? or %s)."""
        return "?"

    def _get_last_insert_id(self, cursor):
        """Get last inserted row ID (override for PostgreSQL RETURNING)."""
        return cursor.lastrowid
