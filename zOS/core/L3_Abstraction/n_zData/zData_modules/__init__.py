# zCLI/subsystems/zData/zData_modules/__init__.py
"""
Internal modules for the zData subsystem.

This package contains the internal implementation modules for zData's data
management functionality. It is organized as an integration layer that brings
together parsers, validators, operations, and database backends.

Package Structure
----------------
**shared/**:
The primary subpackage containing all zData infrastructure:

- **parsers/**: WHERE clause and value type parsing (foundation layer)
  - parse_where_clause(): SQL-like syntax → adapter dictionaries
  - parse_value(): String → Python type conversion

- **validator.py**: 5-layer validation architecture
  - String validation (type, required)
  - Numeric validation (min, max)
  - Pattern validation (regex)
  - Format validation (email, url, etc.)
  - Plugin validation (custom business logic)

- **operations/**: CRUD and DDL operation handlers
  - CRUD: INSERT, READ, UPDATE, DELETE, UPSERT
  - DDL: CREATE, HEAD, DROP
  - helpers.py: Shared DRY utilities

- **backends/**: Database adapters for multiple backends
  - BaseDataAdapter: Abstract base class
  - SQLAdapter: SQL base class (SQLite + PostgreSQL)
  - SQLiteAdapter: File-based SQL support
  - PostgreSQLAdapter: Network-based SQL support
  - CSVAdapter: pandas DataFrame-based CSV support
  - AdapterFactory: Creates appropriate adapter
  - AdapterRegistry: Registers custom adapters

- **data_operations.py**: Central facade that routes actions to handlers

Architecture History
-------------------
**Paradigm Removal (Week 6.16 - Phase 3.1):**
Previously, zData_modules/ contained a `paradigms/` folder with:
- classical/: ClassicalData handler (SQL/CSV databases)
- quantum/: QuantumData stub (for future quantum computing integration)

**Architectural Decision:**
- **Quantum extracted**: Quantum computing support moved to separate Zolo app
  (leverages zSession's multi-app authentication, separate repository)
- **Classical merged**: ClassicalData logic merged directly into zData.py main facade
- **Paradigm fork removed**: Eliminated the 3-tier architecture (zData → paradigm → operations)
  in favor of a simpler 2-tier architecture (zData → operations)

**Current Architecture (2-Tier):**
```
zData.py (main facade)
    ↓
shared/ (operations, validators, backends)
```

This simplification makes zData more maintainable and focuses it on classical
data management (SQL and CSV), while Quantum becomes a specialized Zolo application.

Usage Pattern
------------
The zData_modules package is internal infrastructure. External code should use
the zData.py facade, not import from zData_modules directly.

Correct usage (via facade):
    >>> from zOS import zOS
    >>> z = zCLI()
    >>> z.data.load_schema("myschema.yaml")
    >>> z.data.insert("users", {"name": "Alice", "age": 30})

Incorrect usage (direct import):
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared import DataOperations
    >>> # Don't do this - use zData facade instead

Integration
----------
zData_modules is used by:
- **zData.py**: Main facade that initializes adapter, validator, and operations
- **zLoader**: Schema loading and caching
- **zOpen**: Direct database file operations
- **zWizard**: Multi-step data collection workflows

See Also
--------
- zData.py: Main facade for data operations
- shared/: Implementation modules (parsers, validators, operations, backends)
- ../zData.py: Public API for zData subsystem
"""

__all__ = []
