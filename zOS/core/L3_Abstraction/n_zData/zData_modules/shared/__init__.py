# zCLI/subsystems/zData/zData_modules/shared/__init__.py
"""
Shared infrastructure for zData operations, validation, and backends.

This package provides the integration layer that connects parsers, validators,
operations, and backends into a cohesive data management system. It exports
the core utilities and facades used across the zData subsystem.

Package Contents
---------------
This package is organized into several subpackages:

**parsers/**:
- WHERE clause parsing (SQL-like syntax → adapter dictionaries)
- Value type parsing (string → Python types: int, float, bool, None, str)
- Foundation layer with no dependencies

**operations/**:
- CRUD operation handlers (INSERT, READ, UPDATE, DELETE, UPSERT)
- DDL operation handlers (CREATE, HEAD, DROP)
- Helper utilities (table extraction, WHERE parsing, validation display)

**backends/**:
- BaseDataAdapter: Abstract base class for all backends
- SQLAdapter: SQL base class (shared by SQLite and PostgreSQL)
- SQLiteAdapter: File-based SQL database support
- PostgreSQLAdapter: Network-based SQL database support
- CSVAdapter: pandas DataFrame-based CSV file support
- AdapterFactory: Creates appropriate adapter based on schema config
- AdapterRegistry: Registers custom adapters for plugins

**validator.py**:
- DataValidator: 5-layer validation architecture (string → numeric → pattern → format → plugin)
- Schema validation enforcement
- Plugin validator integration via zParser

**data_operations.py**:
- DataOperations: Central facade that routes actions to operation handlers
- Hook execution (onBefore*/onAfter* via zFunc)
- Schema filtering and ensure_tables logic

Architecture Position
--------------------
- **Layer**: Tier 1 - Integration Layer (connects Tier 0 parsers with Tier 2 operations)
- **Used By**: zData.py main facade
- **Purpose**: Provide unified access to data management infrastructure

Exported Components
------------------
**Parsers (2 functions):**
- **parse_where_clause(where_str)**: Convert SQL-like WHERE to adapter dict
- **parse_value(value_str)**: Convert string to Python type

**Validator (1 class):**
- **DataValidator(schema, zcli)**: 5-layer validation architecture

**Facade (1 class):**
- **DataOperations(zcli, schema, adapter)**: Central operation router

Integration Flow
---------------
The shared infrastructure enables this data flow:

1. **zData.py** loads schema and initializes adapter via AdapterFactory
2. **DataValidator** is created from schema for validation
3. **DataOperations** facade is created with adapter and validator
4. User requests are routed through DataOperations.route_action()
5. Operation handlers use **parsers** for WHERE/value parsing
6. Operation handlers use **validator** for schema validation
7. Operation handlers delegate to **backends** for database execution
8. Results flow back through operations → facade → zData.py

Usage Examples
-------------
Using parsers:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared import parse_where_clause, parse_value
    >>> parse_where_clause("age >= 18 AND status = active")
    {"age": {"$gte": 18}, "status": "active"}
    >>> parse_value("42")
    42

Using DataOperations facade:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared import DataOperations
    >>> ops = DataOperations(zcli, schema, adapter)
    >>> request = {"action": "read", "table": "users", "limit": 10}
    >>> result = ops.route_action("read", request)

See Also
--------
- parsers/: WHERE clause and value type parsing
- operations/: CRUD and DDL operation handlers
- backends/: Database adapters (SQLite, PostgreSQL, CSV)
- validator.py: 5-layer validation architecture
- data_operations.py: Central operation facade
"""

from .parsers import parse_where_clause, parse_value
from .validator import DataValidator
from .data_operations import DataOperations

__all__ = [
    "parse_where_clause",
    "parse_value",
    "DataValidator",
    "DataOperations",
]

