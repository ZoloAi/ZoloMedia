# zCLI/subsystems/zData/zData_modules/shared/backends/adapter_registry.py
"""
Backend adapter registry with auto-registration and plugin support.

This module implements the adapter registry pattern for zData's backend adapters.
It automatically registers all built-in adapters (SQLite, CSV, PostgreSQL) when
imported, and provides a mechanism for plugins to register custom adapters.

Architecture Overview
--------------------
The registry acts as the "bootstrap" layer that ties the adapter system together:

    adapter_registry.py (auto-registers built-in adapters on import)
           ↓
    adapter_factory.py (creates adapter instances from registry)
           ↓
    Adapter instances (SQLiteAdapter, CSVAdapter, PostgreSQLAdapter, custom)

**Design Philosophy:**
- **Auto-registration:** Built-in adapters registered automatically on module import
- **Graceful degradation:** Optional dependencies fail gracefully (ImportError handling)
- **Extensibility:** Plugins can register custom adapters via register_custom_adapter()
- **Simplicity:** Two functions only - register_builtin_adapters(), register_custom_adapter()

Auto-Registration Mechanism
---------------------------
When this module is imported, `register_builtin_adapters()` is called automatically
(see bottom of file). This registers all built-in adapters with AdapterFactory:

**Registration Flow:**
1. Module imported → `register_builtin_adapters()` called at line 46
2. Try to import SQLiteAdapter → register if successful
3. Try to import CSVAdapter → register if successful (requires pandas)
4. Try to import PostgreSQLAdapter → register if successful (requires psycopg2)
5. Adapters now available via AdapterFactory.create_adapter()

**ImportError Handling:**
- SQLite: Standard library, should always succeed
- CSV: Requires pandas (optional dependency) - fails gracefully
- PostgreSQL: Requires psycopg2 (optional dependency) - fails gracefully

Built-In Adapters
----------------
**1. SQLite Adapter:**
- Type: "sqlite"
- Dependencies: None (Python standard library)
- Use case: File-based relational database

**2. CSV Adapter:**
- Type: "csv"
- Dependencies: pandas (optional)
- Use case: File-based flat files with pandas DataFrames

**3. PostgreSQL Adapter:**
- Type: "postgresql"
- Dependencies: psycopg2 (optional)
- Use case: Network-based relational database

Custom Adapter Registration
--------------------------
Plugins can register custom adapters using `register_custom_adapter()`:

    from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.adapter_registry import register_custom_adapter
    
    class MyCustomAdapter(BaseDataAdapter):
        # ... implement adapter ...
    
    register_custom_adapter("mycustom", MyCustomAdapter)

Usage Examples
-------------
Built-in adapters (auto-registered):
    >>> # Just import the module - adapters auto-register
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends import adapter_registry
    >>> # Adapters now available via AdapterFactory.create_adapter()
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.adapter_factory import AdapterFactory
    >>> adapter = AdapterFactory.create_adapter("sqlite", config, logger)

Custom adapter registration:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.adapter_registry import register_custom_adapter
    >>> register_custom_adapter("redis", RedisAdapter)
    >>> adapter = AdapterFactory.create_adapter("redis", config, logger)

Integration
----------
This module is used by:
- adapter_factory.py: Relies on registered adapters
- classical_data.py: Imports to trigger auto-registration
- quantum_data.py: Imports to trigger auto-registration
- Plugin system: Uses register_custom_adapter() for extensions

Note:
    This module has a circular import with adapter_factory.py (registry imports
    factory, factory imports registry). This is intentional and safe because the
    import happens at module level, not during function execution.
"""

import logging
from zOS import Any
from .adapter_factory import AdapterFactory

# ============================================================
# Module Constants - Adapter Names
# ============================================================

_ADAPTER_SQLITE = "sqlite"
_ADAPTER_CSV = "csv"
_ADAPTER_POSTGRESQL = "postgresql"

# ============================================================
# Module Constants - Logger
# ============================================================

_LOG_PREFIX = "[OK]"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_REGISTERED = "[OK] Registered %s adapter"
_LOG_REGISTERED_CUSTOM = "Registered custom adapter: %s"
_LOG_AUTO_REGISTRATION_START = "Auto-registering built-in adapters"
_LOG_SQLITE_REGISTERED = "[OK] Registered SQLite adapter"
_LOG_CSV_REGISTERED = "[OK] Registered CSV adapter"
_LOG_POSTGRESQL_REGISTERED = "[OK] Registered PostgreSQL adapter"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_IMPORT_FAILED = "Failed to register %s adapter: %s"
_ERR_SQLITE_IMPORT = "Failed to register SQLite adapter: %s"
_ERR_CSV_IMPORT = "Failed to register CSV adapter (pandas not installed): %s"
_ERR_POSTGRESQL_IMPORT = "PostgreSQL adapter not available (psycopg2 not installed): %s"
_ERR_PANDAS_MISSING = "pandas not installed"
_ERR_PSYCOPG2_MISSING = "psycopg2 not installed"

# ============================================================
# Module Logger
# ============================================================

# Get logger for this module
logger = logging.getLogger("zCLI.zData")

# ============================================================
# Public API
# ============================================================

__all__ = ["register_builtin_adapters", "register_custom_adapter"]

def register_builtin_adapters() -> None:
    """
    Register all built-in adapters (SQLite, CSV, PostgreSQL) with AdapterFactory.

    This function is called automatically when the module is imported (see bottom
    of file). It attempts to import and register each built-in adapter, handling
    ImportErrors gracefully for adapters with optional dependencies.

    **Registration Process:**
    1. Try to import SQLiteAdapter → register as "sqlite"
    2. Try to import CSVAdapter → register as "csv" (requires pandas)
    3. Try to import PostgreSQLAdapter → register as "postgresql" (requires psycopg2)

    **ImportError Handling:**
    - SQLite: Should always succeed (standard library)
    - CSV: Fails gracefully if pandas not installed
    - PostgreSQL: Fails gracefully if psycopg2 not installed

    Returns:
        None

    Example:
        >>> # Auto-registration on module import
        >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends import adapter_registry
        >>> # SQLite, CSV (if pandas), PostgreSQL (if psycopg2) now registered

    Note:
        - This function is called automatically at module import time
        - Manual calls are safe (idempotent via AdapterFactory)
        - Optional dependencies logged as warnings, not errors
    """
    try:
        from .sqlite_adapter import SQLiteAdapter
        AdapterFactory.register_adapter(_ADAPTER_SQLITE, SQLiteAdapter)
        if logger:
            logger.debug(_LOG_SQLITE_REGISTERED)
    except ImportError as e:
        if logger:
            logger.warning(_ERR_SQLITE_IMPORT, e)

    try:
        from .csv_adapter import CSVAdapter
        AdapterFactory.register_adapter(_ADAPTER_CSV, CSVAdapter)
        if logger:
            logger.debug(_LOG_CSV_REGISTERED)
    except ImportError as e:
        if logger:
            logger.warning(_ERR_CSV_IMPORT, e)

    try:
        from .postgresql_adapter import PostgreSQLAdapter
        AdapterFactory.register_adapter(_ADAPTER_POSTGRESQL, PostgreSQLAdapter)
        if logger:
            logger.debug(_LOG_POSTGRESQL_REGISTERED)
    except ImportError as e:
        if logger:
            logger.warning(_ERR_POSTGRESQL_IMPORT, e)

def register_custom_adapter(data_type: str, adapter_class: Any) -> None:
    """
    Register a custom adapter for plugins/extensions.

    Allows plugins to register their own adapter implementations with the
    AdapterFactory. Custom adapters must inherit from BaseDataAdapter and
    implement all required abstract methods.

    Args:
        data_type: Unique type identifier for the adapter (e.g., "redis", "mongodb")
        adapter_class: Adapter class (must inherit from BaseDataAdapter)

    Returns:
        None

    Example:
        >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.base_adapter import BaseDataAdapter
        >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.adapter_registry import register_custom_adapter
        >>> 
        >>> class RedisAdapter(BaseDataAdapter):
        ...     def connect(self):
        ...         # ... implement Redis connection ...
        ...     # ... implement other required methods ...
        >>> 
        >>> register_custom_adapter("redis", RedisAdapter)
        >>> # Now available via AdapterFactory.create_adapter("redis", ...)

    Note:
        - data_type must be unique (overwrites existing if duplicate)
        - adapter_class must inherit from BaseDataAdapter
        - Registered adapters available immediately via AdapterFactory
    """
    AdapterFactory.register_adapter(data_type, adapter_class)
    if logger:
        logger.info(_LOG_REGISTERED_CUSTOM, data_type)

# ============================================================
# Auto-Registration
# ============================================================

# Auto-register built-in adapters when module is imported.
# This ensures SQLite, CSV, and PostgreSQL adapters are available
# to AdapterFactory without explicit registration calls.
register_builtin_adapters()
