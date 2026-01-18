# zCLI/subsystems/zLoader/loader_modules/loader_cache_plugin.py

"""
Plugin cache for dynamically loaded modules with collision detection and session injection.

This module provides a specialized caching layer for plugin modules within the zLoader
subsystem. Unlike other caches, the PluginCache uses filename-based keys (not full paths)
with collision detection, automatic mtime invalidation, and zCLI session injection for
every loaded plugin. It's the largest and most feature-rich cache implementation.

Purpose
-------
The PluginCache serves as Tier 2 (Cache Implementations) in the zLoader architecture,
providing plugin module caching with collision detection, LRU eviction, mtime-based
freshness checking, and automatic zCLI session injection. It sits alongside other cache
implementations but is the only one that caches executable code (modules).

Architecture
------------
**Tier 2 - Cache Implementations (Plugin Cache)**
    - Position: Cache tier for plugin modules
    - Dependencies: OrderedDict, time, os (from zCLI), Path, importlib.util, zConfig constants
    - Used By: CacheOrchestrator (line 23), zParser (plugin invocation via &PluginName.function)
    - Purpose: Plugin module caching + collision detection + session injection + LRU eviction

Key Features
------------
1. **Collision Detection**: Prevents loading plugins with duplicate filenames from different
   paths. If "test_plugin.py" exists in two directories, raises ValueError with hints.

2. **Filename-Based Keys**: Caches plugins by filename (stem), not full path. Ensures
   consistent access: &test_plugin.function works regardless of plugin location.

3. **Session Injection**: Injects `zcli` instance into module BEFORE executing it, enabling
   plugins to access zcli.logger, zcli.session, zcli.data in top-level code.

4. **Mtime Invalidation**: Automatic freshness checking on every get(). Compares file mtime
   vs cached mtime. Invalidates and reloads if file changed.

5. **LRU Eviction**: Uses OrderedDict with move_to_end() for proper LRU behavior. Evicts
   oldest plugins when max_size exceeded.

6. **Comprehensive Stats**: Tracks 6 metrics (hits, misses, loads, evictions, invalidations,
   collisions) for cache performance monitoring.

Design Decisions
----------------
1. **Filename-Based Keys**: Using Path.stem (filename without .py) as cache key ensures
   consistent plugin access. &test_plugin.function always works, regardless of where
   test_plugin.py is located.

2. **Collision Detection**: Critical safety feature. Two plugins with same filename from
   different paths would overwrite each other. Collision detection prevents this with
   clear error messages.

3. **Session Injection Timing**: Injecting zcli instance BEFORE exec_module() is critical.
   Allows plugins to use zcli in top-level code (imports, constants, decorators).

4. **OrderedDict for LRU**: Provides O(1) move_to_end() for efficient LRU tracking. Standard
   dict maintains insertion order but lacks move_to_end().

5. **Mtime Invalidation**: Ensures plugins reflect latest code changes during development.
   Without this, cached plugins would persist even after file modifications.

Cache Strategy
--------------
**When to Cache**:
    - User invokes plugin via &PluginName.function syntax
    - zParser calls load_and_cache() to load plugin module
    - Module stored with filename as key

**When to Invalidate**:
    - File mtime changed (developer modified plugin code)
    - User explicitly calls invalidate(plugin_name)
    - LRU eviction when max_size exceeded (default: 50 plugins)

**When to Hit**:
    - Same plugin invoked again (same filename)
    - File mtime unchanged (plugin code not modified)
    - Plugin moved to end of OrderedDict (most recently used)

External Usage
--------------
**Used By**:
    - zCLI/subsystems/zLoader/loader_modules/cache_orchestrator.py (Line 23)
      Usage: self.plugin_cache = PluginCache(session, logger, zcli)
      Purpose: Routes plugin cache requests (type="plugin")

    - zParser: Plugin invocation via &PluginName.function(args) syntax
      Usage: Calls load_and_cache() to load and cache plugin module
      Purpose: Provides fast plugin execution with caching

Usage Examples
--------------
**Load and Cache Plugin**:
    >>> session = {}
    >>> logger = get_logger()
    >>> zcli = get_zcli_instance()
    >>> cache = PluginCache(session, logger, zcli, max_size=50)
    >>> module = cache.load_and_cache("/path/to/test_plugin.py")
    >>> # Module cached as "test_plugin", zcli injected

**Get Cached Plugin**:
    >>> module = cache.get("test_plugin")
    >>> if module:
    ...     result = module.some_function(args)

**Collision Detection**:
    >>> cache.load_and_cache("/dir1/test_plugin.py")  # OK
    >>> cache.load_and_cache("/dir2/test_plugin.py")  # Raises ValueError with hints

**Invalidate Plugin**:
    >>> cache.invalidate("test_plugin")
    >>> # Plugin removed, will be reloaded on next access

**Clear Plugins by Pattern**:
    >>> cache.clear("test*")
    >>> # Removes all plugins starting with "test"

**Get Stats**:
    >>> stats = cache.get_stats()
    >>> print(f"Hit rate: {stats['hit_rate']}, Collisions: {stats['collisions']}")

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 2 Cache Implementations)
    - Tier 1: Foundation (loader_io.py - File I/O)
    - Tier 2: Cache Implementations ← THIS MODULE
        - SystemCache (UI/config files with LRU)
        - PinnedCache (User aliases, no eviction)
        - SchemaCache (DB connections + transactions)
        - PluginCache (Plugin modules + collision detection) ← THIS (LARGEST)
    - Tier 3: Cache Orchestrator (Routes cache requests)
    - Tier 4: Package Aggregator (loader_modules/__init__.py)
    - Tier 5: Facade (zLoader.py)
    - Tier 6: Package Root (__init__.py)

Dependencies
------------
Internal:
    - None (standalone cache implementation)

External:
    - zCLI imports: os, time, OrderedDict, Any, Dict, List, Optional
    - pathlib: Path (for filename extraction)
    - importlib.util: spec_from_file_location, module_from_spec (for dynamic loading)
    - zConfig constants: SESSION_KEY_ZCACHE, ZCACHE_KEY_PLUGIN

Performance Considerations
--------------------------
- **Memory**: Stores plugin modules in-memory. Typical usage: 5-20 plugins per session.
  Module objects vary by complexity (~10-100KB each).
- **LRU Overhead**: OrderedDict move_to_end() is O(1), minimal overhead.
- **Mtime Checking**: os.path.getmtime() on every get(), typically <1ms overhead.
- **Collision Detection**: Dict lookup is O(1), negligible overhead.
- **Eviction**: Evicts oldest plugin when max_size exceeded (default: 50).

Thread Safety
-------------
This class is NOT thread-safe. Both in-memory OrderedDict and session dict access are not
synchronized. If using zCLI in a multi-threaded environment, ensure proper locking around
plugin cache access.

See Also
--------
- cache_orchestrator.py: Routes cache requests to this class
- loader_cache_system.py: System cache with LRU eviction
- loader_cache_pinned.py: Pinned aliases cache (no eviction)
- loader_cache_schema.py: Schema cache (DB connections + transactions)
- zParser/parser_modules/parser_plugin.py: Plugin invocation logic

Version History
---------------
- v1.5.4: Industry-grade upgrade (type hints, constants, comprehensive docs,
          zConfig modernization, DRY refactoring, robust pattern matching)
- v1.5.3: Original implementation (344 lines, collision detection, session injection,
          mtime invalidation, LRU eviction)
"""

from zOS import os, time, OrderedDict, Any, Dict, List, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZCACHE
from pathlib import Path
import importlib.util

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Session Keys
ZCACHE_KEY_PLUGIN: str = "plugin_cache"  # Plugin cache namespace key

# Default Values
DEFAULT_MAX_SIZE: int = 50  # Default maximum number of cached plugins
MODULE_NAME_UNKNOWN: str = "unknown"  # Default module name if __name__ not set

# Log Prefixes
LOG_PREFIX_MISS: str = "[PluginCache MISS]"
LOG_PREFIX_STALE: str = "[PluginCache STALE]"
LOG_PREFIX_INVALID: str = "[PluginCache INVALID]"
LOG_PREFIX_HIT: str = "[PluginCache HIT]"
LOG_PREFIX_LOAD: str = "[PluginCache LOAD]"
LOG_PREFIX_SET: str = "[PluginCache SET]"
LOG_PREFIX_EVICT: str = "[PluginCache EVICT]"
LOG_PREFIX_INVALIDATE: str = "[PluginCache INVALIDATE]"
LOG_PREFIX_CLEAR: str = "[PluginCache CLEAR]"
LOG_PREFIX_ERROR: str = "[PluginCache ERROR]"

# Stats Keys (internal tracking)
STAT_KEY_HITS: str = "hits"
STAT_KEY_MISSES: str = "misses"
STAT_KEY_EVICTIONS: str = "evictions"
STAT_KEY_INVALIDATIONS: str = "invalidations"
STAT_KEY_LOADS: str = "loads"
STAT_KEY_COLLISIONS: str = "collisions"

# Entry Keys (cache entry structure)
ENTRY_KEY_MODULE: str = "module"
ENTRY_KEY_FILEPATH: str = "filepath"
ENTRY_KEY_CACHED_AT: str = "cached_at"
ENTRY_KEY_ACCESSED_AT: str = "accessed_at"
ENTRY_KEY_HITS: str = "hits"
ENTRY_KEY_MTIME: str = "mtime"
ENTRY_KEY_MODULE_NAME: str = "module_name"

# Stats Return Keys (for get_stats() return dict)
STATS_KEY_NAMESPACE: str = "namespace"
STATS_KEY_SIZE: str = "size"
STATS_KEY_MAX_SIZE: str = "max_size"
STATS_KEY_HITS: str = "hits"
STATS_KEY_MISSES: str = "misses"
STATS_KEY_HIT_RATE: str = "hit_rate"
STATS_KEY_LOADS: str = "loads"
STATS_KEY_EVICTIONS: str = "evictions"
STATS_KEY_INVALIDATIONS: str = "invalidations"
STATS_KEY_COLLISIONS: str = "collisions"

# List Return Keys (for list_plugins() return dict)
LIST_KEY_NAME: str = "name"
LIST_KEY_FILEPATH: str = "filepath"
LIST_KEY_HITS: str = "hits"
LIST_KEY_CACHED_AT: str = "cached_at"

# Wildcard Character
WILDCARD_CHAR: str = "*"

# ============================================================================
# PLUGINCACHE CLASS
# ============================================================================


class PluginCache:
    """
    Cache for dynamically loaded plugin modules with collision detection and session injection.

    This class implements a specialized caching layer for plugin modules using filename-based
    keys (not full paths) with collision detection, automatic mtime invalidation, zCLI session
    injection, and LRU eviction.

    The PluginCache is the largest and most feature-rich cache implementation, providing:
    - Collision detection (prevents duplicate filenames from different paths)
    - Session injection (injects zcli instance before executing plugin)
    - Mtime invalidation (auto-reloads when plugin file changes)
    - LRU eviction (OrderedDict with move_to_end for proper LRU)
    - Comprehensive stats (6 metrics for performance monitoring)

    Attributes
    ----------
    session : Dict[str, Any]
        Session dictionary for storing cache (OrderedDict).
    logger : Any
        Logger instance for cache operation logging.
    zcli : Any
        zCLI instance for session injection into plugins.
    max_size : int
        Maximum number of cached plugins (default: 50).
    stats : Dict[str, int]
        Statistics dict tracking hits, misses, loads, evictions, invalidations, collisions.

    Notes
    -----
    **Collision Detection**:
        If two plugins with the same filename exist in different paths, raises ValueError
        with detailed error message and hints. This prevents silent overwrites.

    **Session Injection Timing**:
        zcli instance is injected AFTER exec_module() to overwrite any zcli = None
        placeholder in the plugin. This ensures the zcli instance is available in functions.

    **LRU Eviction**:
        Uses OrderedDict with move_to_end() for O(1) LRU tracking. When max_size exceeded,
        evicts oldest (least recently used) plugin.
    """

    def __init__(self, session: Dict[str, Any], logger: Any, zcli: Any, max_size: int = DEFAULT_MAX_SIZE) -> None:
        """
        Initialize plugin cache with collision detection and session injection.

        Parameters
        ----------
        session : Dict[str, Any]
            Session dictionary for storing cached plugins (OrderedDict).
        logger : Any
            Logger instance for cache operation logging.
        zcli : Any
            zCLI instance for session injection into plugins.
        max_size : int, optional
            Maximum number of cached plugins (default: DEFAULT_MAX_SIZE = 50).

        Notes
        -----
        **Initialization Process**:
            1. Store session, logger, zcli, max_size references
            2. Initialize stats dict (6 metrics: hits, misses, loads, evictions, invalidations, collisions)
            3. Ensure session namespace exists (creates OrderedDict if needed)

        **Stats Tracking**:
            - hits: Successful cache lookups
            - misses: Cache misses (plugin not found)
            - loads: Plugins loaded from disk
            - evictions: Plugins evicted due to LRU
            - invalidations: Plugins invalidated due to mtime or explicit invalidate()
            - collisions: Duplicate filename attempts from different paths

        **OrderedDict**:
            Cache is stored as OrderedDict for LRU tracking. If existing cache is regular dict,
            _ensure_namespace() converts it to OrderedDict.
        """
        self.session = session
        self.max_size = max_size
        self.logger = logger
        self.zcli = zcli

        # Statistics tracking
        self.stats: Dict[str, int] = {
            STAT_KEY_HITS: 0,
            STAT_KEY_MISSES: 0,
            STAT_KEY_EVICTIONS: 0,
            STAT_KEY_INVALIDATIONS: 0,
            STAT_KEY_LOADS: 0,
            STAT_KEY_COLLISIONS: 0
        }

        # Ensure namespace exists
        self._ensure_namespace()

    @property
    def _cache(self) -> OrderedDict:
        """
        Get session cache dict for plugin cache.

        Returns
        -------
        OrderedDict
            Session cache OrderedDict containing plugin entries.

        Notes
        -----
        This property encapsulates the session path for cache storage,
        reducing code duplication across methods (9 uses).
        """
        return self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PLUGIN]

    def _ensure_namespace(self) -> None:
        """
        Ensure plugin_cache namespace exists in session (OrderedDict).

        Notes
        -----
        **Creates Two-Level Namespace**:
            1. `session[SESSION_KEY_ZCACHE]` - Top-level cache namespace
            2. `session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PLUGIN]` - Plugin cache namespace

        **OrderedDict Conversion**:
            If existing cache is regular dict (from deserialization or legacy code),
            converts it to OrderedDict for LRU tracking. This ensures move_to_end()
            always works.

        **When Called**:
            - During __init__ to ensure namespace exists
            - Before any cache operations
        """
        try:
            if SESSION_KEY_ZCACHE not in self.session:
                self.session[SESSION_KEY_ZCACHE] = {}

            if ZCACHE_KEY_PLUGIN not in self.session[SESSION_KEY_ZCACHE]:
                self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PLUGIN] = OrderedDict()
            elif not isinstance(self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PLUGIN], OrderedDict):
                # Convert existing dict to OrderedDict for LRU support
                self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PLUGIN] = OrderedDict(
                    self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PLUGIN]
                )
        except Exception as e:
            self.logger.debug(f"{LOG_PREFIX_ERROR} _ensure_namespace - {e}")

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if key matches wildcard pattern (robust pattern matching).

        Parameters
        ----------
        key : str
            Plugin name to check (e.g., "test_plugin").
        pattern : str
            Pattern with optional wildcards (e.g., "test*", "*_plugin", "*test*").

        Returns
        -------
        bool
            True if key matches pattern, False otherwise.

        Notes
        -----
        **Pattern Types**:
            - Prefix: "test*" matches "test_plugin", "test_utils", "test123"
            - Suffix: "*_plugin" matches "test_plugin", "db_plugin", "auth_plugin"
            - Substring: "*test*" matches "test_plugin", "my_test", "unittest"
            - Exact: "test_plugin" matches only "test_plugin"

        **Wildcard Handling**:
            - Leading wildcard: startswith check
            - Trailing wildcard: endswith check
            - Both wildcards: substring check
            - No wildcards: exact match

        Examples
        --------
        >>> cache._matches_pattern("test_plugin", "test*")
        True
        >>> cache._matches_pattern("test_plugin", "*_plugin")
        True
        >>> cache._matches_pattern("test_plugin", "*test*")
        True
        >>> cache._matches_pattern("test_plugin", "db*")
        False
        """
        # Extract base pattern (remove wildcards)
        pattern_clean = pattern.replace(WILDCARD_CHAR, "")

        # Determine match type based on wildcard position
        if pattern.startswith(WILDCARD_CHAR) and pattern.endswith(WILDCARD_CHAR):
            # Substring match: "*test*"
            return pattern_clean in key
        elif pattern.startswith(WILDCARD_CHAR):
            # Suffix match: "*_plugin"
            return key.endswith(pattern_clean)
        elif pattern.endswith(WILDCARD_CHAR):
            # Prefix match: "test*"
            return key.startswith(pattern_clean)
        else:
            # Exact match: "test_plugin"
            return key == pattern

    def get(self, plugin_name: str, default: Any = None) -> Optional[Any]:
        """
        Get plugin module from cache by filename with automatic freshness checking.

        Parameters
        ----------
        plugin_name : str
            Plugin filename (without .py extension), e.g., "test_plugin".
        default : Any, optional
            Default value if plugin not found or invalidated (default: None).

        Returns
        -------
        Optional[Any]
            Cached module if found and fresh, default value otherwise.

        Examples
        --------
        >>> module = cache.get("test_plugin")
        >>> if module:
        ...     result = module.some_function(args)

        Notes
        -----
        **Freshness Checking**:
            On every get(), compares current file mtime vs cached mtime. If different,
            invalidates cache entry and returns default. This ensures plugins reflect
            latest code changes during development.

        **LRU Tracking**:
            On cache hit, moves plugin to end of OrderedDict (most recently used).
            This ensures proper LRU eviction when max_size exceeded.

        **Stats Tracking**:
            - Increments hits on cache hit
            - Increments misses on cache miss
            - Increments invalidations on stale or missing file

        **OSError Handling**:
            If file no longer exists, invalidates cache entry gracefully and returns default.
        """
        try:
            cache = self._cache

            if plugin_name not in cache:
                self.stats[STAT_KEY_MISSES] += 1
                self.logger.debug(f"{LOG_PREFIX_MISS} {plugin_name}")
                return default

            entry = cache[plugin_name]
            file_path = entry.get(ENTRY_KEY_FILEPATH)

            # Check freshness (mtime)
            if file_path:
                try:
                    current_mtime = os.path.getmtime(file_path)
                    cached_mtime = entry.get(ENTRY_KEY_MTIME, 0)

                    if current_mtime != cached_mtime:
                        # File changed - invalidate
                        self.stats[STAT_KEY_INVALIDATIONS] += 1
                        self.logger.debug(
                            f"{LOG_PREFIX_STALE} {plugin_name} (mtime: {cached_mtime} => {current_mtime})"
                        )
                        del cache[plugin_name]
                        return default
                except OSError:
                    # File doesn't exist anymore - invalidate
                    self.stats[STAT_KEY_INVALIDATIONS] += 1
                    self.logger.debug(f"{LOG_PREFIX_INVALID} {plugin_name} (file not found)")
                    del cache[plugin_name]
                    return default

            # Cache hit - move to end (most recent)
            cache.move_to_end(plugin_name)
            entry[ENTRY_KEY_ACCESSED_AT] = time.time()
            entry[ENTRY_KEY_HITS] = entry.get(ENTRY_KEY_HITS, 0) + 1

            self.stats[STAT_KEY_HITS] += 1
            self.logger.debug(f"{LOG_PREFIX_HIT} {plugin_name} (hits: {entry[ENTRY_KEY_HITS]})")

            return entry.get(ENTRY_KEY_MODULE)

        except Exception as e:
            self.logger.debug(f"{LOG_PREFIX_ERROR} {plugin_name} - {e}")
            return default

    def load_and_cache(self, file_path: str, plugin_name: Optional[str] = None) -> Any:
        """
        Load plugin module and cache it by filename with collision detection and session injection.

        Parameters
        ----------
        file_path : str
            Absolute path to plugin file (e.g., "/path/to/test_plugin.py").
        plugin_name : Optional[str], optional
            Plugin name override. If None, uses filename stem (default: None).

        Returns
        -------
        Any
            Loaded and cached module object with zcli instance injected.

        Raises
        ------
        ValueError
            If module cannot be loaded or filename collision detected.

        Examples
        --------
        >>> module = cache.load_and_cache("/path/to/test_plugin.py")
        >>> # Module cached as "test_plugin", accessible via zcli

        >>> module = cache.load_and_cache("/dir1/test_plugin.py")
        >>> module = cache.load_and_cache("/dir2/test_plugin.py")  # Raises ValueError

        Notes
        -----
        **Collision Detection**:
            If plugin with same filename already cached from different path, raises ValueError
            with detailed error message and hints. This prevents silent overwrites.

        **Collision Handling**:
            - Same filename, same path: Returns cached version (no reload)
            - Same filename, different path: Raises ValueError with collision details
            - New filename: Loads and caches normally

        **Session Injection Timing**:
            Critical: Injects zcli instance AFTER exec_module(). This overwrites any
            zcli = None placeholder and ensures functions have access to the instance.

            ```python
            spec.loader.exec_module(module)  # Execute first
            module.zcli = self.zcli  # Inject after (overwrites None)
            ```

        **Module Name**:
            Uses Path.stem to extract filename without extension:
            - "/path/to/test_plugin.py" → "test_plugin"
            - "/dir/IDGenerator.py" → "IDGenerator"

        **Stats Tracking**:
            - Increments loads on successful load
            - Increments collisions on collision detection
        """
        try:
            # Extract filename as plugin name
            if not plugin_name:
                plugin_name = Path(file_path).stem
            
            # Check for collision
            cache = self._cache
            if plugin_name in cache:
                existing_path = cache[plugin_name].get(ENTRY_KEY_FILEPATH)
                if existing_path != file_path:
                    self.stats[STAT_KEY_COLLISIONS] += 1
                    raise ValueError(
                        f"[ERROR] Plugin name collision: '{plugin_name}'\n"
                        f"   Already loaded from: {existing_path}\n"
                        f"   Attempted to load:   {file_path}\n"
                        f"   Hint: Rename one of the plugin files to avoid collision"
                    )
                # Same file - just return cached version
                return cache[plugin_name][ENTRY_KEY_MODULE]
            
            # Load the module
            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            if not spec or not spec.loader:
                raise ValueError(f"Failed to create module spec for: {file_path}")

            module = importlib.util.module_from_spec(spec)
            
            # Execute module first (which may define zcli = None)
            spec.loader.exec_module(module)
            
            # Inject CLI session AFTER executing module
            # This overwrites any zcli = None placeholder in the plugin
            # and gives plugins access to zcli.logger, zcli.session, zcli.data, etc.
            module.zcli = self.zcli
            
            self.stats[STAT_KEY_LOADS] += 1
            self.logger.debug(f"{LOG_PREFIX_LOAD} {plugin_name} => {file_path} (session injected)")

            # Cache it by filename
            self.set(plugin_name, module, file_path)
            
            return module

        except Exception as e:
            if "collision" in str(e):
                raise  # Re-raise collision errors as-is
            raise ValueError(
                f"Failed to load plugin module: {file_path}\n"
                f"Error: {e}\n"
                f"Hint: Ensure the file is valid Python code"
            ) from e

    def set(self, plugin_name: str, module: Any, file_path: str) -> Any:
        """
        Set plugin module in cache by filename with mtime tracking and LRU eviction.

        Parameters
        ----------
        plugin_name : str
            Plugin filename (cache key), e.g., "test_plugin".
        module : Any
            Loaded module object to cache.
        file_path : str
            Absolute path to plugin file for mtime tracking.

        Returns
        -------
        Any
            The cached module (same as input module parameter).

        Notes
        -----
        **Cache Entry Structure**:
            - module: Module object
            - filepath: Absolute path to plugin file
            - cached_at: Unix timestamp when cached
            - accessed_at: Unix timestamp of last access
            - hits: Number of cache hits (starts at 0)
            - mtime: File modification time for freshness checking
            - module_name: Module __name__ attribute (or "unknown")

        **LRU Eviction**:
            After storing entry, checks if cache size > max_size. If yes, evicts oldest
            (least recently used) plugin via OrderedDict.popitem(last=False).

        **Eviction Logging**:
            Logs evicted plugin details (name, age, hits) for debugging.

        **Mtime Handling**:
            Uses os.path.getmtime() to capture file modification time. If OSError (file
            doesn't exist), skips mtime (entry still cached but won't have freshness checking).
        """
        try:
            cache = self._cache

            # Create cache entry
            entry = {
                ENTRY_KEY_MODULE: module,
                ENTRY_KEY_FILEPATH: file_path,
                ENTRY_KEY_CACHED_AT: time.time(),
                ENTRY_KEY_ACCESSED_AT: time.time(),
                ENTRY_KEY_HITS: 0,
                ENTRY_KEY_MODULE_NAME: module.__name__ if hasattr(module, '__name__') else MODULE_NAME_UNKNOWN
            }

            # Add mtime
            try:
                entry[ENTRY_KEY_MTIME] = os.path.getmtime(file_path)
            except OSError:
                pass  # File doesn't exist, skip mtime

            # Store entry by plugin name
            cache[plugin_name] = entry
            cache.move_to_end(plugin_name)

            self.logger.debug(f"{LOG_PREFIX_SET} {plugin_name} <= {file_path}")

            # Evict oldest if over limit
            while len(cache) > self.max_size:
                evicted_key, evicted_entry = cache.popitem(last=False)
                self.stats[STAT_KEY_EVICTIONS] += 1
                self.logger.debug(
                    f"{LOG_PREFIX_EVICT} {evicted_key} (age: {time.time() - evicted_entry[ENTRY_KEY_CACHED_AT]:.1f}s, hits: {evicted_entry.get(ENTRY_KEY_HITS, 0)})"
                )

        except Exception as e:
            self.logger.debug(f"{LOG_PREFIX_ERROR} {plugin_name} - {e}")

        return module

    def invalidate(self, plugin_name: str) -> None:
        """
        Remove specific plugin from cache by name.

        Parameters
        ----------
        plugin_name : str
            Plugin filename (without .py extension), e.g., "test_plugin".

        Examples
        --------
        >>> cache.invalidate("test_plugin")
        >>> # Plugin removed, will be reloaded on next access

        Notes
        -----
        **When to Use**:
            - User explicitly requests plugin reload
            - Developer modified plugin and wants fresh load
            - Plugin cache entry corrupted

        **Stats Tracking**:
            Increments invalidations counter.
        """
        try:
            cache = self._cache
            if plugin_name in cache:
                del cache[plugin_name]
                self.stats[STAT_KEY_INVALIDATIONS] += 1
                self.logger.debug(f"{LOG_PREFIX_INVALIDATE} {plugin_name}")
        except Exception as e:
            self.logger.debug(f"{LOG_PREFIX_ERROR} {plugin_name} - {e}")

    def clear(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries (optionally by pattern with wildcard support).

        Parameters
        ----------
        pattern : Optional[str], optional
            Pattern with optional wildcards (e.g., "test*", "*_plugin", "*test*").
            If None, clears entire cache (default: None).

        Examples
        --------
        >>> cache.clear("test*")
        >>> # Removes test_plugin, test_utils, test123, etc.

        >>> cache.clear("*_plugin")
        >>> # Removes test_plugin, db_plugin, auth_plugin, etc.

        >>> cache.clear()
        >>> # Removes all plugins

        Notes
        -----
        **Pattern Matching**:
            Uses _matches_pattern() for robust wildcard support:
            - Prefix: "test*" matches plugins starting with "test"
            - Suffix: "*_plugin" matches plugins ending with "_plugin"
            - Substring: "*test*" matches plugins containing "test"
            - Exact: "test_plugin" matches only "test_plugin"

        **Performance**:
            Pattern matching iterates over all keys. For large caches, use specific
            patterns rather than "*everything*" wildcards.
        """
        try:
            cache = self._cache

            if pattern:
                # Clear matching keys using robust pattern matching
                keys_to_delete = [k for k in cache.keys() if self._matches_pattern(k, pattern)]
                for key in keys_to_delete:
                    del cache[key]
                self.logger.debug(f"{LOG_PREFIX_CLEAR} {len(keys_to_delete)} entries matching '{pattern}'")
            else:
                # Clear entire cache
                count = len(cache)
                cache.clear()
                self.logger.debug(f"{LOG_PREFIX_CLEAR} {count} entries")

        except Exception as e:
            self.logger.debug(f"{LOG_PREFIX_ERROR} clear - {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Return cache statistics with performance metrics.

        Returns
        -------
        Dict[str, Any]
            Cache statistics dictionary with keys:
                - namespace (str): Cache namespace ("plugin_cache")
                - size (int): Current number of cached plugins
                - max_size (int): Maximum cache size
                - hits (int): Number of cache hits
                - misses (int): Number of cache misses
                - hit_rate (str): Hit rate percentage (e.g., "85.5%")
                - loads (int): Number of plugins loaded from disk
                - evictions (int): Number of LRU evictions
                - invalidations (int): Number of cache invalidations
                - collisions (int): Number of filename collisions detected

        Examples
        --------
        >>> stats = cache.get_stats()
        >>> print(f"Hit rate: {stats['hit_rate']}")
        Hit rate: 85.5%
        >>> print(f"Collisions: {stats['collisions']}")
        Collisions: 2

        Notes
        -----
        **Hit Rate Calculation**:
            hit_rate = (hits / (hits + misses)) * 100
            Returns "0.0%" if no requests yet (avoid division by zero).

        **Error Handling**:
            Returns empty dict {} on any exception.
        """
        try:
            cache = self._cache
            total_requests = self.stats[STAT_KEY_HITS] + self.stats[STAT_KEY_MISSES]
            hit_rate = (self.stats[STAT_KEY_HITS] / total_requests * 100) if total_requests > 0 else 0

            return {
                STATS_KEY_NAMESPACE: ZCACHE_KEY_PLUGIN,
                STATS_KEY_SIZE: len(cache),
                STATS_KEY_MAX_SIZE: self.max_size,
                STATS_KEY_HITS: self.stats[STAT_KEY_HITS],
                STATS_KEY_MISSES: self.stats[STAT_KEY_MISSES],
                STATS_KEY_HIT_RATE: f"{hit_rate:.1f}%",
                STATS_KEY_LOADS: self.stats[STAT_KEY_LOADS],
                STATS_KEY_EVICTIONS: self.stats[STAT_KEY_EVICTIONS],
                STATS_KEY_INVALIDATIONS: self.stats[STAT_KEY_INVALIDATIONS],
                STATS_KEY_COLLISIONS: self.stats[STAT_KEY_COLLISIONS]
            }
        except Exception:
            return {}

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all cached plugins with metadata.

        Returns
        -------
        List[Dict[str, Any]]
            List of plugin dictionaries, each containing:
                - name (str): Plugin filename (e.g., "test_plugin")
                - filepath (str): Absolute path to plugin file
                - hits (int): Number of cache hits for this plugin
                - cached_at (float): Unix timestamp when cached

        Examples
        --------
        >>> plugins = cache.list_plugins()
        >>> for plugin in plugins:
        ...     print(f"{plugin['name']}: {plugin['hits']} hits")
        test_plugin: 5 hits
        IDGenerator: 12 hits

        >>> plugins = cache.list_plugins()
        >>> # [
        >>> #     {"name": "test_plugin", "filepath": "/path/to/test_plugin.py", "hits": 5, "cached_at": 1234567890.0},
        >>> #     {"name": "IDGenerator", "filepath": "/path/to/IDGenerator.py", "hits": 12, "cached_at": 1234567891.0}
        >>> # ]

        Notes
        -----
        **Plugin Order**:
            Plugins listed in OrderedDict iteration order (most recently used last).

        **Error Handling**:
            Returns empty list [] on any exception.

        **Missing Fields**:
            Uses "unknown" for filepath if entry missing ENTRY_KEY_FILEPATH.
            Uses 0 for hits/cached_at if entry missing those keys.
        """
        try:
            cache = self._cache
            return [
                {
                    LIST_KEY_NAME: name,
                    LIST_KEY_FILEPATH: entry.get(ENTRY_KEY_FILEPATH, MODULE_NAME_UNKNOWN),
                    LIST_KEY_HITS: entry.get(ENTRY_KEY_HITS, 0),
                    LIST_KEY_CACHED_AT: entry.get(ENTRY_KEY_CACHED_AT, 0)
                }
                for name, entry in cache.items()
            ]
        except Exception:
            return []


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = ["PluginCache"]

