# zCLI/subsystems/zData/zData_modules/shared/backends/__init__.py
"""
Backend adapter package with factory pattern and auto-registration.

This package provides a complete adapter system for zData's backend data storage,
supporting multiple database types through a unified interface. It implements the
factory pattern with automatic adapter registration for seamless extensibility.

Architecture Overview
--------------------
The package follows a layered architecture with clear separation of concerns:

    BaseDataAdapter (Abstract Base Class)
           ↓
    ┌──────────────────┬──────────────────┬──────────────────┐
    ↓                  ↓                  ↓                  ↓
SQLiteAdapter    CSVAdapter    PostgreSQLAdapter    (Custom Adapters)
    ↓                  ↓                  ↓                  ↓
    └──────────────────┴──────────────────┴──────────────────┘
                              ↓
                    AdapterFactory (creates instances)
                              ↓
                    AdapterRegistry (auto-registers classes)

**Layer 1: Abstract Base** (base_adapter.py)
- BaseDataAdapter: ABC defining common interface for all adapters
- 17 abstract methods (DDL, DML, TCL, metadata, utility)
- 3 concrete helpers (logging, config access)

**Layer 2: Concrete Adapters** (sqlite_adapter.py, csv_adapter.py, postgresql_adapter.py)
- SQLiteAdapter: File-based SQLite3 database (embedded, zero-config)
- CSVAdapter: Pandas-based CSV storage (flat files, DataFrames)
- PostgreSQLAdapter: Network PostgreSQL database (client-server, production)

**Layer 3: Creation & Registry** (adapter_factory.py, adapter_registry.py)
- AdapterFactory: Factory pattern for creating adapter instances
- AdapterRegistry: Auto-registration mechanism for built-in + custom adapters

Auto-Registration Mechanism
---------------------------
When this package is imported, the adapter_registry module is automatically imported,
which triggers registration of all built-in adapters:

    1. Package import: from zData.backends import AdapterFactory
    2. __init__.py imports adapter_registry module
    3. adapter_registry.py calls register_builtin_adapters()
    4. Built-in adapters auto-registered: SQLite, CSV, PostgreSQL
    5. AdapterFactory ready to create adapter instances

This mechanism enables zero-configuration usage while supporting plugin extensions.

Public API
----------
This package exports 6 main items for external use:

**Abstract Base:**
- BaseDataAdapter: ABC for implementing custom adapters

**Factory:**
- AdapterFactory: Create adapter instances (recommended approach)

**Concrete Adapters (for direct use):**
- SQLiteAdapter: File-based SQLite database
- CSVAdapter: Pandas DataFrame CSV storage
- PostgreSQLAdapter: Network PostgreSQL database

**Plugin Support:**
- register_custom_adapter: Register custom adapters dynamically

Usage Examples
-------------
**1. Factory Pattern (Recommended):**
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends import AdapterFactory
    >>> config = {"path": "/data/myapp", "label": "sqlite"}
    >>> adapter = AdapterFactory.create_adapter("sqlite", config)
    >>> adapter.connect()

**2. Direct Adapter Import:**
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends import SQLiteAdapter
    >>> config = {"path": "/data/myapp", "label": "sqlite"}
    >>> adapter = SQLiteAdapter(config, logger=logger)
    >>> adapter.connect()

**3. Plugin Registration (Custom Adapters):**
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends import (
    ...     BaseDataAdapter, register_custom_adapter
    ... )
    >>> 
    >>> class MongoDBAdapter(BaseDataAdapter):
    ...     # ... implement abstract methods ...
    >>> 
    >>> register_custom_adapter("mongodb", MongoDBAdapter)
    >>> # Now available via AdapterFactory.create_adapter("mongodb", config)

Integration
----------
This package is used by:
- classical_data.py: Classical paradigm (CRUD operations)
- quantum_data.py: Quantum paradigm (abstract data structures)
- Plugin system: Custom adapter registration
"""

# ============================================================
# Imports - Abstract Base & Factory
# ============================================================

from .base_adapter import BaseDataAdapter
from .adapter_factory import AdapterFactory

# ============================================================
# Imports - Concrete Adapters
# ============================================================

from .sqlite_adapter import SQLiteAdapter
from .csv_adapter import CSVAdapter
from .postgresql_adapter import PostgreSQLAdapter

# ============================================================
# Imports - Registry Functions
# ============================================================

from .adapter_registry import register_custom_adapter

# ============================================================
# Auto-Registration Trigger
# ============================================================

# Import adapter_registry module to trigger auto-registration of built-in adapters.
# This import executes register_builtin_adapters() at module load time, which
# registers SQLiteAdapter, CSVAdapter, and PostgreSQLAdapter with AdapterFactory.
# Order matters: This must come after importing AdapterFactory.
from . import adapter_registry  # noqa: F401 (imported for side effects)

# ============================================================
# Public API
# ============================================================

__all__ = [
    # Abstract base class
    "BaseDataAdapter",
    # Factory (recommended for creating adapters)
    "AdapterFactory",
    # Concrete adapters (for direct use)
    "SQLiteAdapter",
    "CSVAdapter",
    "PostgreSQLAdapter",
    # Plugin support (custom adapter registration)
    "register_custom_adapter",
]
