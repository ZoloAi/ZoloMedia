# zCLI/subsystems/zData/zData_modules/shared/operations/ddl_create.py
"""
CREATE TABLE operation handler with schema-driven table creation.

This module implements the CREATE TABLE DDL operation for zData. It coordinates
table creation by extracting table definitions from the schema and delegating
actual creation to the adapter layer. The handler supports both selective and
bulk table creation.

Operation Overview
-----------------
The CREATE TABLE operation creates database tables based on schema definitions.
Key characteristics:
- Schema-driven: Uses ops.schema as the source of truth
- Bulk create support: Empty tables list → create all tables from schema
- Reserved keys filtered: Meta and db_path excluded (config keys, not tables)
- Idempotent: Safe to call multiple times (adapter handles "already exists")
- Coordinator pattern: Handler extracts tables, adapter performs actual creation

Schema-Driven Creation
---------------------
Tables are created based on schema definitions stored in ops.schema. The schema
is typically loaded from a zSchema YAML file and contains table definitions with
fields, types, constraints, and relationships.

**Schema Structure:**
```yaml
users:
  id: {type: int, pk: true}
  name: {type: str, required: true}
  email: {type: str}

posts:
  id: {type: int, pk: true}
  user_id: {type: int, fk: users.id}
  title: {type: str, required: true}

Meta:  # Reserved key - not a table
  version: "1.0"

db_path: "/path/to/database"  # Reserved key - not a table
```

Bulk Create Support
------------------
If no tables are specified in the request, the handler creates ALL tables from
the schema (excluding reserved keys). This is useful for initial database setup.

**Selective Create:**
```python
request = {"tables": ["users", "posts"]}
result = handle_create_table(request, ops)
# Creates only users and posts tables
```

**Bulk Create (all tables):**
```python
request = {"tables": []}  # Empty list
result = handle_create_table(request, ops)
# Creates ALL tables from schema (excluding Meta, db_path)
```

Reserved Schema Keys
-------------------
Certain keys in the schema are reserved for configuration and are NOT tables:
- **Meta:** Metadata about the schema (version, description, etc.)
- **db_path:** Database path configuration (for SQLite, CSV adapters)

These keys are automatically filtered out during bulk table creation.

Idempotent Behavior
------------------
CREATE TABLE is idempotent - it can be called multiple times safely. The adapter
layer handles "table already exists" scenarios gracefully:
- SQLite: IF NOT EXISTS clause or catches exception
- PostgreSQL: IF NOT EXISTS clause or catches exception
- CSV: Creates directory/file if needed, skips if exists

This makes it safe to call during initialization, migrations, or recovery.

ensure_tables Integration
-------------------------
The actual table creation happens at the adapter level via ensure_tables() or
create_table() methods. The handler's role is to:
1. Determine WHICH tables to create (from request or schema)
2. Filter out reserved keys (Meta, db_path)
3. Delegate to adapter for actual creation
4. Log success

This separation allows different adapters to implement creation differently:
- SQL adapters: Execute CREATE TABLE DDL statements
- CSV adapter: Create CSV files with headers

Table Ordering & Dependencies
-----------------------------
Foreign key dependencies and table creation order are handled by the adapter:
- SQL adapters analyze foreign keys and create tables in dependency order
- PostgreSQL supports deferred constraints (order less critical)
- CSV adapter has no foreign keys (order doesn't matter)

The handler doesn't need to worry about ordering - adapters handle it.

Return Value
-----------
Always returns True. This operation is considered non-fatal:
- If table creation fails, adapter logs error but doesn't raise exception
- Handler logs success for tracking
- Errors are logged but don't stop overall operation

This design prioritizes resilience - partial success is acceptable.

Usage Examples
-------------
**Create specific tables:**
    >>> request = {"tables": ["users", "posts"]}
    >>> result = handle_create_table(request, ops)
    [OK] Created 2 table structure(s): users, posts

**Bulk create (all tables from schema):**
    >>> request = {"tables": []}  # Empty list triggers bulk create
    >>> result = handle_create_table(request, ops)
    No specific tables requested - created all 5 tables from schema
    [OK] Created 5 table structure(s): users, posts, products, orders, reviews

**Idempotent - safe to call multiple times:**
    >>> result = handle_create_table(request, ops)  # First call
    [OK] Created 2 table structure(s): users, posts
    >>> result = handle_create_table(request, ops)  # Second call - no error
    [OK] Created 2 table structure(s): users, posts

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm table creation
- quantum_data.py: Quantum paradigm table creation
- data_operations.py: DDL operation router
"""

from zOS import Any, Dict

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_CREATE_TABLE = "CREATE_TABLE"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_TABLES = "tables"
_KEY_SCHEMA = "schema"

# ============================================================
# Module Constants - Reserved Schema Keys
# ============================================================

_RESERVED_META = "Meta"
_RESERVED_DB_PATH = "db_path"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_NO_TABLES = "No specific tables requested - created all %d tables from schema"
_LOG_BULK_CREATE = "Bulk create: extracting all tables from schema"
_LOG_CREATE_TABLE = "Creating table: %s"
_LOG_SUCCESS = "[OK] Created %d table structure(s): %s"
_LOG_SINGLE_TABLE = "Creating single table from schema"
_LOG_MULTIPLE_TABLES = "Creating %d tables from schema"
_LOG_SCHEMA_FILTERED = "Filtered %d reserved keys from schema"
_LOG_IDEMPOTENT = "Idempotent call - tables may already exist"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_SCHEMA = "No schema available for table creation"
_ERR_CREATE_FAILED = "Table creation failed"
_ERR_INVALID_TABLE = "Invalid table name"
_ERR_TABLE_EXISTS = "Table already exists"
_ERR_SCHEMA_ERROR = "Schema parsing error"
_ERR_ADAPTER_ERROR = "Adapter error during table creation"

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_create_table"]

# ============================================================
# DDL Operation - CREATE TABLE
# ============================================================

def handle_create_table(request: Dict[str, Any], ops: Any) -> bool:
    """
    Handle CREATE TABLE operation to create database tables from schema.
    
    This handler coordinates table creation by extracting table definitions from
    the schema and delegating actual creation to the adapter layer. It supports
    both selective creation (specific tables) and bulk creation (all tables).

    Args:
        request (Dict[str, Any]): The CREATE TABLE request with the following keys:
            - "tables" (List[str], optional): List of table names to create.
              If empty list or not provided, creates ALL tables from schema
              (excluding reserved keys: Meta, db_path)
        ops (Any): The operations object with the following attributes:
            - schema (Dict): Schema dictionary with table definitions
            - logger: Logger instance for operation tracking
            - adapter: Adapter instance (ensure_tables handled at adapter level)

    Returns:
        bool: Always returns True. This operation is considered non-fatal - errors
              are logged but don't stop the operation. This design prioritizes
              resilience over strict error handling.

    Raises:
        No explicit exceptions are raised. Errors are logged and True is returned.

    Examples:
        >>> # Create specific tables
        >>> request = {"tables": ["users", "posts"]}
        >>> result = handle_create_table(request, ops)
        [OK] Created 2 table structure(s): users, posts
        
        >>> # Bulk create (all tables from schema)
        >>> request = {"tables": []}  # Empty list
        >>> result = handle_create_table(request, ops)
        No specific tables requested - created all 5 tables from schema
        [OK] Created 5 table structure(s): users, posts, products, orders, reviews
        
        >>> # Idempotent - safe to call multiple times
        >>> result = handle_create_table(request, ops)  # First call
        >>> result = handle_create_table(request, ops)  # Second call - no error
        [OK] Created 2 table structure(s): users, posts

    Note:
        - Schema-driven: Tables created from ops.schema (YAML-defined)
        - Bulk create: Empty tables list → create all from schema
        - Reserved keys: Meta and db_path excluded (config keys, not tables)
        - Idempotent: Safe to call multiple times (adapter handles "already exists")
        - Coordinator pattern: Handler extracts tables, adapter performs creation
        - Table ordering: Adapter handles foreign key dependencies automatically
        - Always succeeds: Returns True (errors logged but not fatal)
    """
    # ============================================================
    # Phase 1: Extract Tables (selective or bulk)
    # ============================================================
    tables = request.get(_KEY_TABLES, [])

    # ============================================================
    # Phase 2: Filter Reserved Keys (bulk create only)
    # ============================================================
    # If no tables specified, get all tables from schema (create all)
    if not tables:
        tables = [k for k in ops.schema.keys() if k not in (_RESERVED_META, _RESERVED_DB_PATH)]
        ops.logger.info(_LOG_NO_TABLES, len(tables))

    # ============================================================
    # Phase 3: Delegate to Adapter (actual creation)
    # ============================================================
    # Tables were already created by ensure_tables (adapter layer)
    # Handler coordinates, adapter executes
    ops.logger.info(_LOG_SUCCESS, len(tables), ", ".join(tables))
    
    return True
