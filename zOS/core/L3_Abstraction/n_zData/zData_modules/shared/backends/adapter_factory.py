# zCLI/subsystems/zData/zData_modules/shared/backends/adapter_factory.py
"""
Backend adapter factory with dynamic registration and instance creation.

This module implements the factory pattern for creating backend adapter instances
based on data type specifications. It works in tandem with adapter_registry.py to
provide a complete adapter management system for zData.

Architecture Overview
--------------------
The factory is the "creation" layer that builds adapter instances from the registry:

    adapter_registry.py (registers adapter classes)
           ↓
    adapter_factory.py (creates adapter instances from registered classes)
           ↓
    Adapter instances (SQLiteAdapter, CSVAdapter, PostgreSQLAdapter, custom)

**Design Philosophy:**
- **Factory Pattern:** Single class with static methods for adapter creation
- **Dynamic Registration:** Adapters registered at runtime (plugin-friendly)
- **Case-Insensitive:** Adapter types normalized to lowercase
- **Singleton Pattern:** Class-level state (_adapters dict, _logger)

Factory Pattern Workflow
------------------------
**1. Registration Phase (via adapter_registry):**
   - adapter_registry imports this module
   - Calls AdapterFactory.register_adapter("sqlite", SQLiteAdapter)
   - Adapter class stored in _adapters dict

**2. Logger Setup (via classical_data/quantum_data):**
   - AdapterFactory.set_logger(logger) called once at startup
   - Logger available to all created adapter instances

**3. Creation Phase (via classical_data/quantum_data):**
   - AdapterFactory.create_adapter("sqlite", config)
   - Factory looks up adapter class from _adapters dict
   - Instantiates adapter with config and logger
   - Returns adapter instance

**4. Validation Phase (optional):**
   - AdapterFactory.is_supported("mongodb") → False
   - AdapterFactory.list_adapters() → ["sqlite", "csv", "postgresql"]

Class Variables
--------------
**_adapters (dict):**
Class-level registry of adapter types → adapter classes:
```python
_adapters = {
    "sqlite": SQLiteAdapter,
    "csv": CSVAdapter,
    "postgresql": PostgreSQLAdapter
}
```

**_logger (logger instance):**
Shared logger instance passed to all created adapters. Set once via set_logger().

Plugin Support
-------------
Plugins can register custom adapters dynamically:
```python
from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.adapter_factory import AdapterFactory

class RedisAdapter(BaseDataAdapter):
    # ... implement adapter ...

AdapterFactory.register_adapter("redis", RedisAdapter)
# Now available via create_adapter("redis", config)
```

Case-Insensitive Lookup
-----------------------
All adapter types normalized to lowercase:
- register_adapter("SQLite", ...) → stored as "sqlite"
- create_adapter("SQLITE", ...) → looks up "sqlite"
- Provides consistent lookup regardless of case

Usage Examples
-------------
Basic adapter creation:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.adapter_factory import AdapterFactory
    >>> config = {"path": "/data/myapp", "label": "sqlite"}
    >>> adapter = AdapterFactory.create_adapter("sqlite", config)
    >>> adapter.connect()

Check adapter support:
    >>> AdapterFactory.is_supported("mongodb")
    False
    >>> AdapterFactory.list_adapters()
    ['sqlite', 'csv', 'postgresql']

Plugin registration:
    >>> AdapterFactory.register_adapter("mongodb", MongoDBAdapter)
    >>> AdapterFactory.is_supported("mongodb")
    True

Integration
----------
This module is used by:
- adapter_registry.py: Calls register_adapter() for built-in adapters
- classical_data.py: Calls create_adapter() to instantiate adapters
- quantum_data.py: Calls create_adapter() to instantiate adapters
- Plugin system: Calls register_adapter() for custom adapters
"""

from zOS import Any, Dict, List

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_UNSUPPORTED_TYPE = "Unsupported data type: %s. Available types: %s"
_ERR_NO_ADAPTERS = "No adapters registered"
_ERR_ADAPTER_NOT_FOUND = "Adapter not found for data type: %s"
_ERR_INVALID_CONFIG = "Invalid configuration provided"
_ERR_ADAPTER_CLASS_INVALID = "Adapter class must inherit from BaseDataAdapter"

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_SET_LOGGER = "Logger set for AdapterFactory"
_LOG_ADAPTER_REGISTERED = "Registered adapter for data type: %s"
_LOG_CREATING_ADAPTER = "Creating adapter for data type: %s"
_LOG_ADAPTER_CREATED = "Created %s adapter"
_LOG_LIST_ADAPTERS = "Listing %d registered adapters"
_LOG_CHECK_SUPPORT = "Checking support for data type: %s"
_LOG_SUPPORTED = "Data type '%s' is supported"
_LOG_NOT_SUPPORTED = "Data type '%s' is not supported"

# ============================================================
# Module Constants - Format Strings
# ============================================================

_FMT_UNSUPPORTED_TYPE = "Unsupported data type: {data_type}"
_FMT_AVAILABLE_TYPES = "Available types: {types}"

# ============================================================
# Public API
# ============================================================

__all__ = ["AdapterFactory"]


class AdapterFactory:
    """
    Factory class for creating backend adapter instances with dynamic registration.

    AdapterFactory implements the factory pattern for zData's adapter system. It
    maintains a class-level registry of adapter types and provides methods to create,
    register, and query adapters.

    **Design Pattern:**
    - Factory Pattern: Creates adapter instances from registered classes
    - Singleton Pattern: Class-level state (all methods are @classmethod)
    - Registry Pattern: Maintains adapter type → class mapping

    Class Variables
    --------------
    **_adapters (Dict[str, Any]):**
    Registry mapping adapter type names (lowercase) to adapter classes:
        {"sqlite": SQLiteAdapter, "csv": CSVAdapter, "postgresql": PostgreSQLAdapter}

    **_logger (Optional[logger]):**
    Shared logger instance passed to all created adapters. Set via set_logger().

    Methods (5 total)
    -----------------
    **Configuration:**
    - set_logger: Set shared logger for factory and created adapters

    **Registration:**
    - register_adapter: Register adapter class for a data type (plugin support)

    **Creation:**
    - create_adapter: Create adapter instance for specified data type

    **Query:**
    - list_adapters: List all registered adapter types
    - is_supported: Check if data type is supported

    Features
    -------
    **1. Dynamic Registration:**
    Adapters registered at runtime via register_adapter(). Enables plugins to add
    custom adapters without modifying core code.

    **2. Case-Insensitive Lookup:**
    All data types normalized to lowercase for consistent lookup.

    **3. Shared Logger:**
    Logger set once via set_logger(), then passed to all created adapter instances.

    **4. Error Handling:**
    create_adapter() raises ValueError with helpful message listing available types.

    Usage Example
    ------------
        >>> # Set logger (optional, done once at startup)
        >>> AdapterFactory.set_logger(logger)
        >>> 
        >>> # Register custom adapter (optional, for plugins)
        >>> AdapterFactory.register_adapter("redis", RedisAdapter)
        >>> 
        >>> # Create adapter instance
        >>> config = {"path": "/data/myapp", "label": "sqlite"}
        >>> adapter = AdapterFactory.create_adapter("sqlite", config)
        >>> 
        >>> # Query registered adapters
        >>> AdapterFactory.list_adapters()
        ['sqlite', 'csv', 'postgresql', 'redis']
        >>> AdapterFactory.is_supported("mongodb")
        False
    """

    # Class-level registry: {adapter_type: adapter_class}
    _adapters: Dict[str, Any] = {}
    
    # Shared logger instance for factory and adapters
    _logger: Any = None

    @classmethod
    def set_logger(cls, logger: Any) -> None:
        """
        Set shared logger instance for factory and all created adapters.

        The logger is stored at class level and passed to every adapter instance
        created via create_adapter(). Typically called once at application startup.

        Args:
            logger: Logger instance (e.g., logging.Logger) for diagnostic output

        Returns:
            None

        Example:
            >>> import logging
            >>> logger = logging.getLogger("zCLI.zData")
            >>> AdapterFactory.set_logger(logger)
            >>> # Now all created adapters will use this logger

        Note:
            - Called once at startup by classical_data.py or quantum_data.py
            - Logger shared across all adapter instances
            - Can be called multiple times to change logger
        """
        cls._logger = logger
        if cls._logger:
            cls._logger.debug(_LOG_SET_LOGGER)

    @classmethod
    def register_adapter(cls, data_type: str, adapter_class: Any) -> None:
        """
        Register adapter class for a data type (enables plugin extensions).

        Adds adapter class to the factory's registry, making it available for creation
        via create_adapter(). Data type normalized to lowercase for case-insensitive
        lookup.

        Args:
            data_type: Adapter type identifier (e.g., "sqlite", "csv", "postgresql")
            adapter_class: Adapter class (must inherit from BaseDataAdapter)

        Returns:
            None

        Example:
            >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.backends.base_adapter import BaseDataAdapter
            >>> 
            >>> class RedisAdapter(BaseDataAdapter):
            ...     # ... implement adapter methods ...
            >>> 
            >>> AdapterFactory.register_adapter("redis", RedisAdapter)
            >>> # Now available via create_adapter("redis", config)

        Note:
            - data_type converted to lowercase: "SQLite" → "sqlite"
            - Overwrites existing registration if data_type already registered
            - Called automatically by adapter_registry.py for built-in adapters
            - Plugins can call this to register custom adapters
        """
        cls._adapters[data_type.lower()] = adapter_class
        if cls._logger:
            cls._logger.info(_LOG_ADAPTER_REGISTERED, data_type)

    @classmethod
    def create_adapter(cls, data_type: str, config: Dict[str, Any]) -> Any:
        """
        Create and return adapter instance for specified data type.

        Looks up adapter class in registry, instantiates it with config and logger,
        and returns the instance. Data type normalized to lowercase for case-insensitive
        lookup.

        Args:
            data_type: Adapter type identifier (e.g., "sqlite", "csv", "postgresql")
            config: Configuration dict for adapter (path, host, port, etc.)

        Returns:
            Adapter instance (SQLiteAdapter, CSVAdapter, PostgreSQLAdapter, or custom)

        Raises:
            ValueError: If data_type not registered (includes list of available types)

        Example:
            >>> config = {"path": "/data/myapp", "label": "sqlite"}
            >>> adapter = AdapterFactory.create_adapter("sqlite", config)
            >>> adapter.connect()
            >>> # Use adapter for database operations

        Note:
            - data_type converted to lowercase: "SQLITE" → "sqlite"
            - config passed to adapter's __init__(config, logger=cls._logger)
            - ValueError message lists all registered adapter types
            - Adapter must be registered first via register_adapter()
        """
        if cls._logger:
            cls._logger.debug(_LOG_CREATING_ADAPTER, data_type)

        adapter_class = cls._adapters.get(data_type.lower())

        if not adapter_class:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(_ERR_UNSUPPORTED_TYPE % (data_type, available))

        adapter = adapter_class(config, logger=cls._logger)
        if cls._logger:
            cls._logger.info(_LOG_ADAPTER_CREATED, adapter.__class__.__name__)
        return adapter

    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        List all registered adapter types.

        Returns list of adapter type names (lowercase) currently registered in the
        factory. Useful for debugging, UI dropdowns, or validation.

        Returns:
            List[str]: List of registered adapter type names (e.g., ["sqlite", "csv"])

        Example:
            >>> adapters = AdapterFactory.list_adapters()
            >>> print(f"Available adapters: {', '.join(adapters)}")
            Available adapters: sqlite, csv, postgresql

        Note:
            - Returns empty list if no adapters registered
            - All type names are lowercase
            - Built-in adapters: ["sqlite", "csv", "postgresql"]
        """
        if cls._logger:
            cls._logger.debug(_LOG_LIST_ADAPTERS, len(cls._adapters))
        return list(cls._adapters.keys())

    @classmethod
    def is_supported(cls, data_type: str) -> bool:
        """
        Check if data type is supported (adapter registered).

        Validates whether an adapter is available for the specified data type.
        Useful for validation before attempting to create an adapter.

        Args:
            data_type: Adapter type identifier to check (e.g., "mongodb")

        Returns:
            bool: True if adapter registered, False otherwise

        Example:
            >>> if AdapterFactory.is_supported("sqlite"):
            ...     adapter = AdapterFactory.create_adapter("sqlite", config)
            ... else:
            ...     print("SQLite adapter not available")

        Note:
            - data_type converted to lowercase: "SQLITE" → "sqlite"
            - Returns False for unregistered types
            - More efficient than catching ValueError from create_adapter()
        """
        supported = data_type.lower() in cls._adapters
        if cls._logger:
            if supported:
                cls._logger.debug(_LOG_SUPPORTED, data_type)
            else:
                cls._logger.debug(_LOG_NOT_SUPPORTED, data_type)
        return supported
