# zCLI/subsystems/zData/zData_modules/shared/operations/__init__.py
"""
Data operation handlers for CRUD, DDL, and helper utilities.

This package provides individual handler modules for each data operation supported
by the zData subsystem. Each handler is responsible for a single operation type,
following the Single Responsibility Principle for clean separation of concerns.

Package Contents
---------------
**CRUD Operations (5 handlers):**
- **crud_insert.py**: INSERT operations with validation and hooks (onBeforeInsert, onAfterInsert)
- **crud_read.py**: SELECT operations with JOINs, WHERE filtering, ORDER BY, LIMIT + OFFSET pagination
- **crud_update.py**: UPDATE operations with partial updates, WHERE conditions, hooks (onBeforeUpdate, onAfterUpdate)
- **crud_delete.py**: DELETE operations with WHERE safety, no hooks (irreversible by design)
- **crud_upsert.py**: UPSERT operations with adapter-specific conflict resolution (SQLite: OR REPLACE, PostgreSQL: ON CONFLICT)

**Aggregation Operations (1 handler):**
- **agg_aggregate.py**: AGGREGATE operations for statistical functions (COUNT, SUM, AVG, MIN, MAX) with WHERE filtering and GROUP BY

**DDL Operations (3 handlers):**
- **ddl_create.py**: CREATE TABLE operations from schema definitions, bulk creation, idempotent
- **ddl_head.py**: HEAD operations for schema introspection, displays table structure (columns, types, nullable, defaults)
- **ddl_drop.py**: DROP TABLE operations with critical safety warnings, cascade handling, irreversible

**Helper Utilities (4 functions):**
- **helpers.py**: Shared DRY utilities used across all operations (table extraction, WHERE parsing, validation display)

Architecture Position
--------------------
- **Layer**: Tier 1 - Operation Handlers (depends on: parsers, validator, backends)
- **Used By**: DataOperations facade (data_operations.py) routes actions to these handlers
- **Purpose**: Execute single data operations with validation, hooks, and mode-aware display

Operation Flow
-------------
All operation handlers follow a consistent execution pattern:

1. **Extract Request Data**: Parse table name, fields, values, options from request dict
2. **Validate Schema**: Check table exists, validate field names against schema
3. **Execute Hooks** (CRUD only): onBefore* hooks via zFunc integration
4. **Delegate to Adapter**: Call backend adapter method (SQLite/PostgreSQL/CSV)
5. **Execute Hooks** (CRUD only): onAfter* hooks with operation results
6. **Display Results**: Mode-aware output via zDisplay (Terminal vs Bifrost)
7. **Return Results**: Return data (zBifrost) or success indicator (Terminal)

Usage Examples
-------------
Handlers are called by DataOperations facade, not directly by users:

INSERT operation:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.operations import handle_insert
    >>> request = {"table": "users", "fields": ["name", "age"], "values": ["Alice", 30]}
    >>> result = handle_insert(ops, request, display)

READ operation with pagination:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.operations import handle_read
    >>> request = {"table": "users", "where": "age >= 18", "limit": 20, "offset": 40}
    >>> result = handle_read(ops, request, display)

DROP TABLE with safety:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.operations import handle_drop
    >>> request = {"tables": ["temp_table"], "if_exists": True}
    >>> result = handle_drop(ops, request, display)

Exported Functions
-----------------
**CRUD Handlers (5):**
- **handle_insert(ops, request, display)**: Insert rows with validation and hooks
- **handle_read(ops, request, display)**: Select rows with JOINs, filtering, pagination
- **handle_update(ops, request, display)**: Update rows with WHERE conditions and hooks
- **handle_delete(ops, request, display)**: Delete rows with WHERE safety (no hooks)
- **handle_upsert(ops, request, display)**: Insert-or-update with conflict resolution

**DDL Handlers (3):**
- **handle_create_table(ops, request, display)**: Create tables from schema definitions
- **handle_head(ops, request, display)**: Display table schema (columns, types, defaults)
- **handle_drop(ops, request, display)**: Drop tables with safety warnings

**Helper Functions (4):**
- **extract_table_from_request(request, ops)**: Extract table name from request (3-tier fallback: table → tables[0] → model)
- **extract_where_clause(request, ops)**: Extract WHERE clause from request or options (dual-source support)
- **extract_field_values(request)**: Extract fields and values from request with validation
- **display_validation_errors(errors, display)**: Display validation errors via zDisplay with color coding

Integration
----------
These operation handlers are the execution layer of zData's architecture:

- **DataOperations (data_operations.py)**: Routes actions to handlers via action_map
- **Parsers (parsers/)**: WHERE clause and value type parsing for handlers
- **Validator (validator.py)**: Schema validation before operation execution
- **Backends (backends/)**: SQLite/PostgreSQL/CSV adapters execute database operations
- **zFunc**: Hook execution (onBeforeInsert, onAfterInsert, onBeforeUpdate, onAfterUpdate)
- **zDisplay**: Mode-aware output (Terminal ASCII tables vs Bifrost JSON events)

See Also
--------
- data_operations.py: DataOperations facade that routes to these handlers
- helpers.py: Shared DRY utilities used across all operations
- ../parsers/: WHERE clause and value type parsing
- ../validator.py: Schema validation and plugin validators
- ../backends/: Database adapters (SQLite, PostgreSQL, CSV)
"""

from .crud_insert import handle_insert
from .crud_read import handle_read
from .crud_update import handle_update
from .crud_delete import handle_delete
from .crud_upsert import handle_upsert
from .agg_aggregate import handle_aggregate
from .ddl_create import handle_create_table
from .ddl_drop import handle_drop
from .ddl_head import handle_head
from .helpers import (
    extract_table_from_request,
    extract_where_clause,
    extract_field_values,
    display_validation_errors
)

__all__ = [
    # CRUD operations
    "handle_insert",
    "handle_read",
    "handle_update",
    "handle_delete",
    "handle_upsert",
    
    # Aggregation operations
    "handle_aggregate",
    
    # DDL operations
    "handle_create_table",
    "handle_drop",
    "handle_head",
    
    # Helpers
    "extract_table_from_request",
    "extract_where_clause",
    "extract_field_values",
    "display_validation_errors",
]

