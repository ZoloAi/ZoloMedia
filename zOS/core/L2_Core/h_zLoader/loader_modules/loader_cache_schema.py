# zCLI/subsystems/zLoader/loader_modules/loader_cache_schema.py

"""
Schema cache for database connections and transaction management.

This module provides a specialized caching layer for database connections and
transaction management within the zLoader subsystem. Unlike other caches, the
SchemaCache uses a dual storage architecture: database connections are stored
in-memory (non-serializable), while connection metadata is stored in the session
dict (serializable). This design enables transaction support for zWizard and zData.

Purpose
-------
The SchemaCache serves as Tier 2 (Cache Implementations) in the zLoader architecture,
providing connection pooling and transaction management for database operations.
It sits alongside other cache implementations but differs fundamentally in its
dual storage approach and transaction lifecycle management.

Architecture
------------
**Tier 2 - Cache Implementations (Schema Cache)**
    - Position: Cache tier for database connections
    - Dependencies: time (from zCLI), zConfig constants
    - Used By: CacheOrchestrator (line 22), zWizard, zData
    - Purpose: Connection pooling + transaction management

Key Features
------------
1. **Dual Storage Architecture**: Connections stored in-memory (cannot be serialized),
   metadata stored in session dict (can be serialized and tracked).

2. **Transaction Support**: Full transaction lifecycle (begin/commit/rollback) for
   zWizard multi-step operations.

3. **Connection Pooling**: Reuse database connections across operations, reducing
   connection overhead.

4. **Transaction State Tracking**: Separate tracking of active transaction state
   per connection/alias.

5. **Backend Tracking**: Stores database backend type (SQLite, PostgreSQL, etc.)
   from schema metadata.

6. **Graceful Cleanup**: Comprehensive disconnect logic ensures both connection
   and metadata are cleaned up properly.

Design Decisions
----------------
1. **Dual Storage**: Connections cannot be pickled/serialized, so we store them
   in class attributes (in-memory only) while storing connection metadata in
   session dict for tracking and display.

2. **In-Memory Connections**: `self.connections = {}` stores actual handler instances
   that cannot be serialized to session.

3. **Session Metadata**: `session["zCache"]["schema_cache"]` stores serializable
   metadata (backend, connected_at, active flag) for tracking and display.

4. **Transaction Tracking**: Separate `self.transaction_active` dict tracks which
   connections have active transactions.

5. **No Auto-Disconnect**: Unlike other caches, we don't auto-disconnect on eviction.
   User explicitly manages connection lifecycle.

Cache Strategy
--------------
**When to Cache**:
    - User connects to database via zData/zWizard
    - Connection established via set_connection()
    - Stored with alias for quick access

**When to Invalidate**:
    - User explicitly disconnects (disconnect method)
    - Session ends (connections lost, metadata persists)
    - Application shutdown (clear method)

**No Eviction**:
    - No LRU eviction (unlike SystemCache)
    - No mtime checking (unlike PluginCache)
    - User controls connection lifecycle

Transaction Lifecycle
--------------------
**Begin Transaction**:
    1. User calls begin_transaction(alias)
    2. Calls handler.adapter.begin_transaction()
    3. Marks transaction as active in tracking dict
    4. Logs transaction start

**Commit Transaction**:
    1. User calls commit_transaction(alias)
    2. Calls handler.adapter.commit()
    3. Marks transaction as inactive
    4. Logs transaction success

**Rollback Transaction**:
    1. User calls rollback_transaction(alias)
    2. Calls handler.adapter.rollback()
    3. Marks transaction as inactive
    4. Logs rollback warning

External Usage
--------------
**Used By**:
    - zCLI/subsystems/zLoader/loader_modules/cache_orchestrator.py (Line 22)
      Usage: self.schema_cache = SchemaCache(session, logger)
      Purpose: Routes schema cache requests (type="schema")

    - zWizard: Multi-step operations with begin/commit/rollback
    - zData: Database operations with connection reuse

Usage Examples
--------------
**Connect to Database**:
    >>> session = {}
    >>> logger = get_logger()
    >>> cache = SchemaCache(session, logger)
    >>> handler = get_database_handler("sqlite:///mydb.db")
    >>> cache.set_connection("mydb", handler)
    >>> # Connection stored, metadata tracked

**Get Connection**:
    >>> handler = cache.get_connection("mydb")
    >>> if handler:
    ...     results = handler.query("SELECT * FROM users")

**Transaction Lifecycle**:
    >>> cache.begin_transaction("mydb")
    >>> # ... perform multiple operations ...
    >>> if success:
    ...     cache.commit_transaction("mydb")
    ... else:
    ...     cache.rollback_transaction("mydb")

**Disconnect**:
    >>> cache.disconnect("mydb")
    >>> # Connection closed, metadata removed, transaction state cleared

**List Connections**:
    >>> connections = cache.list_connections()
    >>> for conn in connections:
    ...     print(f"{conn['alias']}: {conn['backend']} ({conn['age']:.1f}s)")

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 2 Cache Implementations)
    - Tier 1: Foundation (loader_io.py - File I/O)
    - Tier 2: Cache Implementations ← THIS MODULE
        - SystemCache (UI/config files with LRU)
        - PinnedCache (User aliases, no eviction)
        - SchemaCache (DB connections + transactions) ← THIS
        - PluginCache (Plugin instances)
    - Tier 3: Cache Orchestrator (Routes cache requests)
    - Tier 4: Package Aggregator (loader_modules/__init__.py)
    - Tier 5: Facade (zLoader.py)
    - Tier 6: Package Root (__init__.py)

Dependencies
------------
Internal:
    - None (standalone cache implementation)

External:
    - zCLI imports: time, Any, Dict, List, Optional
    - zConfig constants: SESSION_KEY_ZCACHE, ZCACHE_KEY_SCHEMA

Performance Considerations
--------------------------
- **Memory**: Stores active connections in-memory. Typical usage: 1-5 connections
  per session. Connection objects vary by backend (~1-10KB each).
- **No Pooling Overhead**: Simple dict lookup, O(1) access time.
- **Transaction Overhead**: Transaction begin/commit/rollback delegated to adapter,
  performance depends on database backend.
- **Metadata Tracking**: Minimal overhead, only stores 3 keys per connection.

Thread Safety
-------------
This class is NOT thread-safe. Both in-memory connections and session dict access
are not synchronized. If using zCLI in a multi-threaded environment, ensure proper
locking around connection access and transaction operations.

See Also
--------
- cache_orchestrator.py: Routes cache requests to this class
- loader_cache_system.py: System cache with LRU eviction
- loader_cache_pinned.py: Pinned aliases cache (no eviction)
- loader_cache_plugin.py: Plugin instance cache

Version History
---------------
- v1.5.4: Industry-grade upgrade (type hints, constants, comprehensive docs,
          zConfig modernization, DRY refactoring, error handling for transactions)
- v1.5.3: Original implementation (126 lines, basic connection + transaction)
"""

from zOS import time, Any, Dict, List, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZCACHE, ZCACHE_KEY_SCHEMA

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Log Prefixes
LOG_PREFIX_CACHE: str = "[SchemaCache]"
LOG_PREFIX_TXN: str = "[TXN]"
LOG_PREFIX_OK: str = "[OK]"
LOG_PREFIX_ROLLBACK: str = "[ROLLBACK]"

# Metadata Keys (stored in session)
META_KEY_ACTIVE: str = "active"
META_KEY_CONNECTED_AT: str = "connected_at"
META_KEY_BACKEND: str = "backend"

# List Keys (returned by list_connections)
LIST_KEY_ALIAS: str = "alias"
LIST_KEY_BACKEND: str = "backend"
LIST_KEY_CONNECTED_AT: str = "connected_at"
LIST_KEY_AGE: str = "age"
LIST_KEY_TXN_ACTIVE: str = "transaction_active"

# Schema Keys (for backend extraction)
SCHEMA_KEY_META: str = "zMeta"
SCHEMA_KEY_DATA_TYPE: str = "Data_Type"
BACKEND_UNKNOWN: str = "unknown"

# ============================================================================
# SCHEMACACHE CLASS
# ============================================================================


class SchemaCache:
    """
    Active database connection cache for zWizard with transaction support.

    This class implements a specialized caching layer for database connections
    using a dual storage architecture: connections are stored in-memory (cannot
    be serialized), while connection metadata is stored in the session dict
    (can be serialized and tracked).

    The SchemaCache provides connection pooling and full transaction lifecycle
    management (begin/commit/rollback) for zWizard multi-step operations and
    zData database queries.

    Attributes
    ----------
    session : Dict[str, Any]
        Session dictionary for storing connection metadata (serializable).
    logger : Any
        Logger instance for connection and transaction logging.
    connections : Dict[str, Any]
        In-memory storage for active database connections (non-serializable).
        Maps alias_name → handler_instance.
    transaction_active : Dict[str, bool]
        Tracks active transaction state per connection.
        Maps alias_name → bool (True if transaction active).

    Notes
    -----
    **Dual Storage Architecture**:
        - Connections: Stored in `self.connections` (in-memory, non-serializable)
        - Metadata: Stored in `session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SCHEMA]` (serializable)

    **Why Dual Storage?**
        Database connection objects cannot be pickled/serialized, so we store them
        in class attributes (memory-only). Connection metadata (backend, connected_at)
        is stored in session dict for persistence and display.
    """

    def __init__(self, session: Dict[str, Any], logger: Any) -> None:
        """
        Initialize schema cache with dual storage architecture.

        Parameters
        ----------
        session : Dict[str, Any]
            Session dictionary for storing connection metadata.
        logger : Any
            Logger instance for connection and transaction logging.

        Notes
        -----
        **Initialization Process**:
            1. Store session and logger references
            2. Initialize in-memory connections dict
            3. Initialize transaction state tracking dict
            4. Ensure session namespace exists for metadata storage

        **Dual Storage Setup**:
            - `self.connections` stores actual handler instances (in-memory only)
            - `session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SCHEMA]` stores metadata (serializable)
        """
        self.session = session
        self.logger = logger

        # In-memory connection storage (NOT in session)
        # Connections cannot be serialized, so we keep them in memory only
        self.connections: Dict[str, Any] = {}  # {alias_name: handler_instance}
        self.transaction_active: Dict[str, bool] = {}  # {alias_name: bool}

        # Ensure namespace exists (for metadata only)
        self._ensure_namespace()

    @property
    def _metadata(self) -> Dict[str, Any]:
        """
        Get session metadata dict for schema cache.

        Returns
        -------
        Dict[str, Any]
            Session metadata dict containing connection info.

        Notes
        -----
        This property encapsulates the session path for metadata storage,
        reducing code duplication across methods.
        """
        return self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SCHEMA]

    def _ensure_namespace(self) -> None:
        """
        Ensure schema_cache namespace exists in session (for metadata).

        Notes
        -----
        **Creates Two-Level Namespace**:
            1. `session[SESSION_KEY_ZCACHE]` - Top-level cache namespace
            2. `session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SCHEMA]` - Schema cache namespace

        **What's Stored**:
            - Metadata only (active, connected_at, backend)
            - NOT connections (they're stored in self.connections)

        **When Called**:
            - During __init__ to ensure namespace exists
            - Before any metadata operations
        """
        if SESSION_KEY_ZCACHE not in self.session:
            self.session[SESSION_KEY_ZCACHE] = {}

        if ZCACHE_KEY_SCHEMA not in self.session[SESSION_KEY_ZCACHE]:
            self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SCHEMA] = {}

    def _cleanup_alias(self, alias_name: str) -> None:
        """
        Clean up all tracking for an alias (DRY helper).

        Parameters
        ----------
        alias_name : str
            Database connection alias to clean up.

        Notes
        -----
        **Cleanup Operations**:
            1. Remove from in-memory connections dict
            2. Remove from transaction state tracking
            3. Remove from session metadata

        **When Called**:
            - After disconnect completes (graceful or error)
            - Ensures consistent cleanup across all storage locations
        """
        # Remove from in-memory tracking
        if alias_name in self.connections:
            del self.connections[alias_name]

        if alias_name in self.transaction_active:
            del self.transaction_active[alias_name]

        # Remove from session metadata
        if alias_name in self._metadata:
            del self._metadata[alias_name]

    def get_connection(self, alias_name: str) -> Optional[Any]:
        """
        Get active connection for alias.

        Parameters
        ----------
        alias_name : str
            Database connection alias (e.g., "mydb", "production").

        Returns
        -------
        Optional[Any]
            Handler instance if connection exists, None otherwise.

        Examples
        --------
        >>> handler = cache.get_connection("mydb")
        >>> if handler:
        ...     results = handler.query("SELECT * FROM users")
        """
        connection = self.connections.get(alias_name)
        if connection:
            self.logger.debug(f"{LOG_PREFIX_CACHE} Found connection for ${alias_name}")
        return connection

    def set_connection(self, alias_name: str, handler: Any) -> None:
        """
        Store active connection (in-memory) and metadata (session).

        Parameters
        ----------
        alias_name : str
            Database connection alias (e.g., "mydb", "production").
        handler : Any
            Database handler instance (e.g., SQLiteHandler, PostgreSQLHandler).

        Notes
        -----
        **Dual Storage**:
            1. Store handler in `self.connections` (in-memory, non-serializable)
            2. Store metadata in session (serializable):
                - active: True
                - connected_at: Unix timestamp
                - backend: Database type from schema metadata

        **Backend Detection**:
            Extracts backend from `handler.schema["zMeta"]["Data_Type"]`,
            defaults to "unknown" if not found.
        """
        self.connections[alias_name] = handler

        # Store metadata in session (not the connection itself)
        self._metadata[alias_name] = {
            META_KEY_ACTIVE: True,
            META_KEY_CONNECTED_AT: time.time(),
            META_KEY_BACKEND: handler.schema.get(SCHEMA_KEY_META, {}).get(SCHEMA_KEY_DATA_TYPE, BACKEND_UNKNOWN)
        }

        self.logger.debug(f"{LOG_PREFIX_CACHE} Stored connection for ${alias_name}")

    def has_connection(self, alias_name: str) -> bool:
        """
        Check if connection exists for alias.

        Parameters
        ----------
        alias_name : str
            Database connection alias.

        Returns
        -------
        bool
            True if connection exists, False otherwise.

        Examples
        --------
        >>> if cache.has_connection("mydb"):
        ...     handler = cache.get_connection("mydb")
        """
        return alias_name in self.connections

    def begin_transaction(self, alias_name: str) -> None:
        """
        Begin transaction for alias.

        Parameters
        ----------
        alias_name : str
            Database connection alias.

        Notes
        -----
        **Transaction Start**:
            1. Check if connection exists
            2. Call handler.adapter.begin_transaction()
            3. Mark transaction as active in tracking dict
            4. Log transaction start

        **Error Handling**:
            - Logs warning if connection doesn't exist
            - Logs warning if adapter.begin_transaction() raises exception
            - Transaction state NOT marked active if error occurs

        **Used By**:
            - zWizard: Multi-step operations requiring atomic commits
            - zData: Complex queries requiring transaction isolation
        """
        if alias_name in self.connections:
            try:
                handler = self.connections[alias_name]
                handler.adapter.begin_transaction()
                self.transaction_active[alias_name] = True
                self.logger.framework.debug(f"{LOG_PREFIX_TXN} Transaction started for ${alias_name}")
            except Exception as e:
                self.logger.warning(f"{LOG_PREFIX_TXN} Error starting transaction for ${alias_name}: {e}")
        else:
            self.logger.warning(f"{LOG_PREFIX_TXN} Cannot begin transaction - no connection for ${alias_name}")

    def commit_transaction(self, alias_name: str) -> None:
        """
        Commit transaction for alias.

        Parameters
        ----------
        alias_name : str
            Database connection alias.

        Notes
        -----
        **Transaction Commit**:
            1. Check if connection exists
            2. Call handler.adapter.commit()
            3. Mark transaction as inactive in tracking dict
            4. Log transaction success

        **Error Handling**:
            - Logs warning if connection doesn't exist
            - Logs warning if adapter.commit() raises exception
            - Transaction state marked inactive even if error occurs (cleanup)

        **Guarantees**:
            - After commit (success or failure), transaction is marked inactive
        """
        if alias_name in self.connections:
            try:
                handler = self.connections[alias_name]
                handler.adapter.commit()
                self.transaction_active[alias_name] = False
                self.logger.framework.debug(f"{LOG_PREFIX_OK} Transaction committed for ${alias_name}")
            except Exception as e:
                self.transaction_active[alias_name] = False  # Clean up even on error
                self.logger.warning(f"{LOG_PREFIX_OK} Error committing transaction for ${alias_name}: {e}")
        else:
            self.logger.warning(f"{LOG_PREFIX_OK} Cannot commit transaction - no connection for ${alias_name}")

    def rollback_transaction(self, alias_name: str) -> None:
        """
        Rollback transaction for alias.

        Parameters
        ----------
        alias_name : str
            Database connection alias.

        Notes
        -----
        **Transaction Rollback**:
            1. Check if connection exists
            2. Call handler.adapter.rollback()
            3. Mark transaction as inactive in tracking dict
            4. Log rollback warning

        **Error Handling**:
            - Logs warning if connection doesn't exist
            - Logs warning if adapter.rollback() raises exception
            - Transaction state marked inactive even if error occurs (cleanup)

        **When Called**:
            - zWizard: Multi-step operation encounters error
            - zData: Query error requires rollback
            - User explicitly calls rollback

        **Guarantees**:
            - After rollback (success or failure), transaction is marked inactive
        """
        if alias_name in self.connections:
            try:
                handler = self.connections[alias_name]
                handler.adapter.rollback()
                self.transaction_active[alias_name] = False
                self.logger.warning(f"{LOG_PREFIX_ROLLBACK} Transaction rolled back for ${alias_name}")
            except Exception as e:
                self.transaction_active[alias_name] = False  # Clean up even on error
                self.logger.warning(f"{LOG_PREFIX_ROLLBACK} Error rolling back transaction for ${alias_name}: {e}")
        else:
            self.logger.warning(f"{LOG_PREFIX_ROLLBACK} Cannot rollback transaction - no connection for ${alias_name}")

    def is_transaction_active(self, alias_name: str) -> bool:
        """
        Check if transaction is active for alias.

        Parameters
        ----------
        alias_name : str
            Database connection alias.

        Returns
        -------
        bool
            True if transaction is active, False otherwise.

        Examples
        --------
        >>> cache.begin_transaction("mydb")
        >>> if cache.is_transaction_active("mydb"):
        ...     # Transaction in progress
        ...     cache.commit_transaction("mydb")
        """
        return self.transaction_active.get(alias_name, False)

    def disconnect(self, alias_name: str) -> None:
        """
        Disconnect specific connection.

        Parameters
        ----------
        alias_name : str
            Database connection alias to disconnect.

        Notes
        -----
        **Disconnect Process**:
            1. Check if connection exists
            2. Call handler.disconnect() to close connection
            3. Use _cleanup_alias() to remove from all tracking
            4. Log disconnect success or error

        **Error Handling**:
            - Try-except around handler.disconnect() call
            - Finally block ensures cleanup always happens
            - Uses _cleanup_alias() helper for consistent cleanup

        **What's Cleaned Up**:
            1. In-memory connection (self.connections)
            2. Transaction state (self.transaction_active)
            3. Session metadata (session[...][ZCACHE_KEY_SCHEMA])

        **Graceful Degradation**:
            Even if handler.disconnect() raises exception, we still clean up
            all tracking to avoid memory leaks.
        """
        if alias_name in self.connections:
            try:
                handler = self.connections[alias_name]
                handler.disconnect()
                self.logger.debug(f"{LOG_PREFIX_CACHE} Disconnected ${alias_name}")
            except Exception as e:
                self.logger.warning(f"{LOG_PREFIX_CACHE} Error disconnecting ${alias_name}: {e}")
            finally:
                # Always remove from tracking (graceful cleanup)
                self._cleanup_alias(alias_name)

    def clear(self) -> None:
        """
        Disconnect all connections and clear cache.

        Notes
        -----
        **Clear Process**:
            1. Iterate over all connections (using list() for safe iteration)
            2. Call disconnect() for each connection
            3. Log clear operation

        **Safe Iteration**:
            Uses `list(self.connections.keys())` to avoid "dictionary changed
            size during iteration" error, since disconnect() modifies the dict.

        **When Called**:
            - Application shutdown
            - Session cleanup
            - User explicitly calls clear

        **Result**:
            - All connections closed
            - All metadata removed
            - All transaction state cleared
        """
        for alias_name in list(self.connections.keys()):
            self.disconnect(alias_name)

        self.logger.debug(f"{LOG_PREFIX_CACHE} Cleared all connections")

    def list_connections(self) -> List[Dict[str, Any]]:
        """
        List all active connections with metadata.

        Returns
        -------
        List[Dict[str, Any]]
            List of connection dictionaries, each containing:
                - alias (str): Connection alias name
                - backend (str): Database backend type
                - connected_at (float): Unix timestamp of connection
                - age (float): Connection age in seconds
                - transaction_active (bool): Transaction state

        Examples
        --------
        >>> connections = cache.list_connections()
        >>> for conn in connections:
        ...     print(f"{conn['alias']}: {conn['backend']} ({conn['age']:.1f}s)")
        mydb: sqlite (45.3s)
        production: postgresql (120.7s)

        Notes
        -----
        **Data Source**:
            - Reads from session metadata (not in-memory connections)
            - Session metadata is serializable and persists across requests

        **Age Calculation**:
            - Dynamic: `time.time() - connected_at`
            - Reflects actual connection age at call time

        **Transaction State**:
            - Calls is_transaction_active() for each connection
            - Provides real-time transaction state
        """
        connections = []
        for alias_name, metadata in self._metadata.items():
            connections.append({
                LIST_KEY_ALIAS: alias_name,
                LIST_KEY_BACKEND: metadata.get(META_KEY_BACKEND),
                LIST_KEY_CONNECTED_AT: metadata.get(META_KEY_CONNECTED_AT),
                LIST_KEY_AGE: time.time() - metadata.get(META_KEY_CONNECTED_AT, time.time()),
                LIST_KEY_TXN_ACTIVE: self.is_transaction_active(alias_name)
            })
        return connections


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = ["SchemaCache"]
