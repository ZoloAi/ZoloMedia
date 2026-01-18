# zCLI/subsystems/zLoader/loader_modules/loader_cache_system.py

"""
System cache for UI and config files with LRU eviction and mtime checking.

This module provides a sophisticated caching layer for UI and configuration files
within the zLoader subsystem. It implements Least Recently Used (LRU) eviction,
modification time (mtime) checking for cache freshness, and comprehensive statistics
tracking.

Purpose
-------
The SystemCache serves as Tier 2 (Cache Implementations) in the zLoader architecture,
providing a session-based cache for UI and config files. It sits between the raw
file I/O layer (loader_io.py) and the cache orchestration layer (cache_orchestrator.py),
offering intelligent caching with automatic invalidation when source files change.

Architecture
------------
**Tier 2 - Cache Implementations (System Cache)**
    - Position: Cache tier for UI/config files
    - Dependencies: OrderedDict (from zCLI), os, time, zConfig constants
    - Used By: CacheOrchestrator (line 20)
    - Purpose: LRU cache with mtime freshness checking

Key Features
------------
1. **LRU Eviction**: Uses OrderedDict.move_to_end() to maintain access order,
   automatically evicting least recently used entries when cache is full.

2. **Mtime Checking**: Validates cached files haven't changed on disk by comparing
   modification times, automatically invalidating stale entries.

3. **Statistics Tracking**: Comprehensive metrics including hits, misses, evictions,
   invalidations, and hit rate calculation.

4. **Session-Based Storage**: Cache data stored in session dict under
   SESSION_KEY_ZCACHE/ZCACHE_KEY_SYSTEM namespace for isolation.

5. **Pattern-Based Clearing**: Supports wildcard patterns for bulk cache invalidation
   (e.g., "ui_*" clears all UI files).

Design Decisions
----------------
1. **OrderedDict for LRU**: Python's OrderedDict with move_to_end() provides O(1)
   LRU operations without needing a custom data structure.

2. **Session Storage**: Cache stored in session dict rather than class attributes
   to support session isolation and persistence across zCLI operations.

3. **Mtime Freshness**: Checking file mtime on cache hit ensures cached data is
   always fresh, trading slight overhead for correctness.

4. **Entry Metadata**: Each cache entry includes cached_at, accessed_at, hits
   for debugging and cache behavior analysis.

5. **Graceful Degradation**: All operations wrapped in try-except, returning
   defaults on error to prevent cache failures from breaking application.

Cache Strategy
--------------
**When to Cache**:
    - UI files (zUI.*.yaml) after loading
    - Config files (zConfig.*.yaml) after parsing
    - Any file loaded via zLoader.handle()

**When to Invalidate**:
    - File mtime changes (detected on get())
    - Explicit invalidate() call
    - Pattern-based clear() (e.g., "ui_*")
    - LRU eviction when cache is full

**Eviction Policy**:
    - LRU (Least Recently Used) when cache exceeds max_size
    - Oldest entry (by access time) evicted first
    - Eviction logged with age and hit count for analysis

External Usage
--------------
**Used By**:
    - zCLI/subsystems/zLoader/loader_modules/cache_orchestrator.py (Line 20)
      Usage: self.system_cache = SystemCache(session, logger, max_size=100)
      Purpose: Routes system cache requests (type="system")

Usage Examples
--------------
**Basic Caching** (without mtime):
    >>> session = {}
    >>> logger = get_logger()
    >>> cache = SystemCache(session, logger, max_size=100)
    >>> cache.set("ui_main", {"zType": "zUI", "title": "Main"})
    >>> data = cache.get("ui_main")
    >>> print(data)
    {'zType': 'zUI', 'title': 'Main'}

**Caching with Mtime Checking**:
    >>> cache.set("ui_main", ui_data, filepath="/app/zUI.main.yaml")
    >>> # Later, if file changes, get() returns None and invalidates
    >>> data = cache.get("ui_main", filepath="/app/zUI.main.yaml")
    >>> # Returns None if file mtime changed

**Pattern-Based Clearing**:
    >>> cache.clear(pattern="ui_*")  # Clears all UI files
    >>> cache.clear(pattern="*_config")  # Clears all config files
    >>> cache.clear()  # Clears entire cache

**Statistics**:
    >>> stats = cache.get_stats()
    >>> print(stats)
    {'namespace': 'system_cache', 'size': 42, 'max_size': 100,
     'hits': 156, 'misses': 23, 'hit_rate': '87.2%',
     'evictions': 5, 'invalidations': 12}

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 2 Cache Implementations)
    - Tier 1: Foundation (loader_io.py - File I/O)
    - Tier 2: Cache Implementations ← THIS MODULE
        - SystemCache (UI/config files)
        - PinnedCache (aliases)
        - SchemaCache (DB connections)
        - PluginCache (plugin instances)
    - Tier 3: Cache Orchestrator (Routes cache requests)
    - Tier 4: Package Aggregator (loader_modules/__init__.py)
    - Tier 5: Facade (zLoader.py)
    - Tier 6: Package Root (__init__.py)

Dependencies
------------
Internal:
    - loader_io.py: Raw file loading (indirect, via zLoader facade)

External:
    - zCLI imports: os, time, OrderedDict, Any, Dict, Optional
    - zConfig constants: SESSION_KEY_ZCACHE, ZCACHE_KEY_SYSTEM

Performance Considerations
--------------------------
- **Memory**: Cache size limited by max_size (default 100 entries). Each entry
  stores file content + metadata (~1-10KB per entry).
- **LRU Overhead**: move_to_end() is O(1), making LRU operations very fast.
- **Mtime Checking**: os.path.getmtime() call on each cache hit adds ~0.1ms overhead.
- **Eviction**: Automatic eviction is O(1) using OrderedDict.popitem(last=False).

Thread Safety
-------------
This class is NOT thread-safe. Session dict access is not synchronized. If using
zCLI in a multi-threaded environment, ensure session dict access is protected
by locks or use thread-local storage.

See Also
--------
- cache_orchestrator.py: Routes cache requests to this class
- loader_cache_pinned.py: Pinned aliases cache
- loader_cache_schema.py: Database connection cache
- loader_cache_plugin.py: Plugin instance cache
- loader_io.py: Raw file I/O operations

Version History
---------------
- v1.5.4: Industry-grade upgrade (type hints, constants, comprehensive docs,
          zConfig modernization, DRY refactoring, improved pattern matching)
- v1.5.3: Original implementation (186 lines, basic LRU + mtime)
"""

from zOS import os, time, OrderedDict, Any, Dict, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZCACHE, ZCACHE_KEY_SYSTEM

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Log Prefixes
LOG_PREFIX_MISS: str = "[SystemCache MISS]"
LOG_PREFIX_HIT: str = "[SystemCache HIT]"
LOG_PREFIX_STALE: str = "[SystemCache STALE]"
LOG_PREFIX_INVALID: str = "[SystemCache INVALID]"
LOG_PREFIX_SET: str = "[SystemCache SET]"
LOG_PREFIX_EVICT: str = "[SystemCache EVICT]"
LOG_PREFIX_INVALIDATE: str = "[SystemCache INVALIDATE]"
LOG_PREFIX_CLEAR: str = "[SystemCache CLEAR]"
LOG_PREFIX_ERROR: str = "[SystemCache ERROR]"

# Statistics Keys
STAT_KEY_HITS: str = "hits"
STAT_KEY_MISSES: str = "misses"
STAT_KEY_EVICTIONS: str = "evictions"
STAT_KEY_INVALIDATIONS: str = "invalidations"
STAT_KEY_NAMESPACE: str = "namespace"
STAT_KEY_SIZE: str = "size"
STAT_KEY_MAX_SIZE: str = "max_size"
STAT_KEY_HIT_RATE: str = "hit_rate"

# Entry Keys (cache entry structure)
ENTRY_KEY_DATA: str = "data"
ENTRY_KEY_CACHED_AT: str = "cached_at"
ENTRY_KEY_ACCESSED_AT: str = "accessed_at"
ENTRY_KEY_HITS: str = "hits"
ENTRY_KEY_MTIME: str = "mtime"
ENTRY_KEY_FILEPATH: str = "filepath"

# Configuration
DEFAULT_MAX_SIZE: int = 100
WILDCARD_CHAR: str = "*"

# ============================================================================
# SYSTEMCACHE CLASS
# ============================================================================


class SystemCache:
    """
    System cache for UI and config files with LRU eviction and mtime checking.

    This class implements a sophisticated caching layer for UI and configuration files,
    providing LRU (Least Recently Used) eviction, modification time checking for cache
    freshness, and comprehensive statistics tracking.

    The cache is stored in the session dict under SESSION_KEY_ZCACHE/ZCACHE_KEY_SYSTEM
    namespace, using OrderedDict for efficient LRU operations. Each cache entry includes
    metadata (cached_at, accessed_at, hits, optional mtime) for debugging and analysis.

    Attributes:
        session (Dict[str, Any]): Session dictionary containing cache namespace
        logger (Any): Logger instance for debug/error messages
        max_size (int): Maximum number of entries before LRU eviction (default: 100)
        stats (Dict[str, int]): Statistics dict tracking hits, misses, evictions, invalidations

    Cache Strategy:
        - **LRU Eviction**: Oldest accessed entry evicted when cache exceeds max_size
        - **Mtime Checking**: Cached files validated against disk mtime on get()
        - **Automatic Invalidation**: Stale entries removed when mtime changes
        - **Pattern Clearing**: Wildcard patterns ("ui_*") for bulk invalidation

    Thread Safety:
        NOT thread-safe. Session dict access is not synchronized.
    """

    def __init__(self, session: Dict[str, Any], logger: Any, max_size: int = DEFAULT_MAX_SIZE) -> None:
        """
        Initialize system cache with session, logger, and max size.

        Args:
            session (Dict[str, Any]): Session dictionary to store cache data.
                Must be a mutable dict that persists across zCLI operations.
            logger (Any): Logger instance for debug/error messages. Typically
                from zConfig.logger.
            max_size (int, optional): Maximum number of cache entries before LRU
                eviction. Defaults to DEFAULT_MAX_SIZE (100).

        Notes:
            - Cache namespace created automatically if not present
            - Statistics initialized to zero
            - Session dict structure: session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM]
        """
        self.session = session
        self.max_size = max_size
        self.logger = logger

        # Statistics tracking
        self.stats = {
            STAT_KEY_HITS: 0,
            STAT_KEY_MISSES: 0,
            STAT_KEY_EVICTIONS: 0,
            STAT_KEY_INVALIDATIONS: 0
        }

        # Ensure namespace exists in session
        self._ensure_namespace()

    @property
    def _cache(self) -> OrderedDict:
        """
        Get cache OrderedDict from session (DRY helper property).

        Returns:
            OrderedDict: The cache OrderedDict from session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM]

        Notes:
            This property replaces repeated `self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM]`
            access throughout the class, following DRY (Don't Repeat Yourself) principle.
        """
        return self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM]

    def _ensure_namespace(self) -> None:
        """
        Ensure system_cache namespace exists in session with proper structure.

        Creates the cache namespace structure if not present:
            session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM] = OrderedDict()

        Also converts existing dict to OrderedDict if needed (for backward compatibility).

        Notes:
            - Called automatically during __init__
            - Safe to call multiple times (idempotent)
            - Ensures OrderedDict type for LRU operations
        """
        if SESSION_KEY_ZCACHE not in self.session:
            self.session[SESSION_KEY_ZCACHE] = {}

        if ZCACHE_KEY_SYSTEM not in self.session[SESSION_KEY_ZCACHE]:
            self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM] = OrderedDict()
        elif not isinstance(self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM], OrderedDict):
            # Convert existing dict to OrderedDict for backward compatibility
            self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM] = OrderedDict(
                self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_SYSTEM]
            )

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if key matches wildcard pattern with proper prefix/suffix handling.

        Supports three wildcard patterns:
            - "prefix_*": Matches keys starting with "prefix_"
            - "*_suffix": Matches keys ending with "_suffix"
            - "*substring*": Matches keys containing "substring"

        Args:
            key (str): Cache key to test against pattern
            pattern (str): Wildcard pattern (must contain "*")

        Returns:
            bool: True if key matches pattern, False otherwise

        Examples:
            >>> cache._matches_pattern("ui_main", "ui_*")
            True
            >>> cache._matches_pattern("test_ui_main", "ui_*")
            False  # Doesn't match (not a prefix)
            >>> cache._matches_pattern("db_config", "*_config")
            True
            >>> cache._matches_pattern("db_config_backup", "*_config")
            False  # Doesn't match (not a suffix)
            >>> cache._matches_pattern("my_test_file", "*test*")
            True
        """
        if WILDCARD_CHAR not in pattern:
            return key == pattern

        # Handle prefix pattern: "prefix_*"
        if pattern.endswith(WILDCARD_CHAR) and not pattern.startswith(WILDCARD_CHAR):
            prefix = pattern[:-1]  # Remove trailing "*"
            return key.startswith(prefix)

        # Handle suffix pattern: "*_suffix"
        if pattern.startswith(WILDCARD_CHAR) and not pattern.endswith(WILDCARD_CHAR):
            suffix = pattern[1:]  # Remove leading "*"
            return key.endswith(suffix)

        # Handle substring pattern: "*substring*"
        if pattern.startswith(WILDCARD_CHAR) and pattern.endswith(WILDCARD_CHAR):
            substring = pattern[1:-1]  # Remove both wildcards
            return substring in key

        # Fallback: Just check if substring is in key
        return pattern.replace(WILDCARD_CHAR, "") in key

    def get(self, key: str, filepath: Optional[str] = None, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get value from cache with optional mtime freshness check.

        Retrieves cached data for the given key. If filepath is provided, validates
        that the cached file hasn't changed on disk by comparing modification times.
        Automatically invalidates stale entries and tracks cache statistics.

        Args:
            key (str): Cache key to retrieve
            filepath (Optional[str], optional): File path for mtime freshness check.
                If provided and file mtime changed, cache entry is invalidated.
                Defaults to None (no freshness check).
            default (Optional[Any], optional): Value to return on cache miss or error.
                Defaults to None.

        Returns:
            Optional[Any]: Cached data on hit, default on miss/error/stale

        Examples:
            Get cached data without mtime check:
                >>> data = cache.get("ui_main")
                >>> print(data)
                {'zType': 'zUI', 'title': 'Main'}

            Get with mtime check (returns None if file changed):
                >>> data = cache.get("ui_main", filepath="/app/zUI.main.yaml")
                >>> print(data)
                None  # File mtime changed, entry invalidated

            Get with custom default:
                >>> data = cache.get("missing_key", default={})
                >>> print(data)
                {}
        """
        try:
            cache = self._cache

            if key not in cache:
                self.stats[STAT_KEY_MISSES] += 1
                self.logger.debug(LOG_PREFIX_MISS + " %s", key)
                return default

            entry = cache[key]

            # Check freshness if filepath provided
            if filepath and ENTRY_KEY_MTIME in entry:
                try:
                    current_mtime = os.path.getmtime(filepath)
                    cached_mtime = entry[ENTRY_KEY_MTIME]

                    if current_mtime != cached_mtime:
                        # File changed - invalidate
                        self.stats[STAT_KEY_INVALIDATIONS] += 1
                        self.logger.debug(
                            LOG_PREFIX_STALE + " %s (mtime: %s => %s)",
                            key, cached_mtime, current_mtime
                        )
                        del cache[key]
                        return default
                except OSError:
                    # File doesn't exist anymore - invalidate
                    self.stats[STAT_KEY_INVALIDATIONS] += 1
                    self.logger.debug(LOG_PREFIX_INVALID + " %s (file not found)", key)
                    del cache[key]
                    return default

            # Cache hit - move to end (most recent)
            cache.move_to_end(key)
            entry[ENTRY_KEY_ACCESSED_AT] = time.time()
            entry[ENTRY_KEY_HITS] = entry.get(ENTRY_KEY_HITS, 0) + 1

            self.stats[STAT_KEY_HITS] += 1
            self.logger.debug(LOG_PREFIX_HIT + " %s (hits: %d)", key, entry[ENTRY_KEY_HITS])

            return entry.get(ENTRY_KEY_DATA)

        except Exception as e:
            self.logger.debug(LOG_PREFIX_ERROR + " %s - %s", key, e)
            return default

    def set(self, key: str, value: Any, filepath: Optional[str] = None) -> Any:
        """
        Set value in cache with optional mtime tracking for freshness checks.

        Stores data in cache with metadata (cached_at, accessed_at, hits). If filepath
        is provided, stores file mtime for freshness validation on get(). Automatically
        evicts least recently used entries if cache exceeds max_size.

        Args:
            key (str): Cache key to store data under
            value (Any): Data to cache (typically dict, but can be any type)
            filepath (Optional[str], optional): File path for mtime tracking.
                If provided, file mtime is stored for freshness checks.
                Defaults to None (no mtime tracking).

        Returns:
            Any: The value that was stored (for chaining)

        Examples:
            Cache data without mtime:
                >>> cache.set("ui_main", {"zType": "zUI", "title": "Main"})
                >>> # Data cached, no freshness checking

            Cache with mtime tracking:
                >>> cache.set("ui_main", ui_data, filepath="/app/zUI.main.yaml")
                >>> # Data cached with mtime, will be invalidated if file changes
        """
        try:
            cache = self._cache

            # Create cache entry with metadata
            entry = {
                ENTRY_KEY_DATA: value,
                ENTRY_KEY_CACHED_AT: time.time(),
                ENTRY_KEY_ACCESSED_AT: time.time(),
                ENTRY_KEY_HITS: 0
            }

            # Add mtime if filepath provided
            if filepath:
                try:
                    entry[ENTRY_KEY_MTIME] = os.path.getmtime(filepath)
                    entry[ENTRY_KEY_FILEPATH] = filepath
                except OSError:
                    pass  # File doesn't exist, skip mtime tracking

            # Store entry and mark as most recent
            cache[key] = entry
            cache.move_to_end(key)

            self.logger.debug(LOG_PREFIX_SET + " %s", key)

            # Evict oldest entries if over limit (LRU)
            while len(cache) > self.max_size:
                evicted_key, evicted_entry = cache.popitem(last=False)
                self.stats[STAT_KEY_EVICTIONS] += 1
                self.logger.debug(
                    LOG_PREFIX_EVICT + " %s (age: %.1fs, hits: %d)",
                    evicted_key,
                    time.time() - evicted_entry[ENTRY_KEY_CACHED_AT],
                    evicted_entry.get(ENTRY_KEY_HITS, 0)
                )

        except Exception as e:
            self.logger.debug(LOG_PREFIX_ERROR + " %s - %s", key, e)

        return value

    def invalidate(self, key: str) -> None:
        """
        Remove specific key from cache (explicit invalidation).

        Args:
            key (str): Cache key to remove

        Examples:
            >>> cache.invalidate("ui_main")
            >>> # Entry removed from cache
        """
        try:
            cache = self._cache
            if key in cache:
                del cache[key]
                self.stats[STAT_KEY_INVALIDATIONS] += 1
                self.logger.debug(LOG_PREFIX_INVALIDATE + " %s", key)
        except Exception as e:
            self.logger.debug(LOG_PREFIX_ERROR + " %s - %s", key, e)

    def clear(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries, optionally filtering by wildcard pattern.

        Supports three wildcard patterns:
            - "prefix_*": Clears keys starting with "prefix_"
            - "*_suffix": Clears keys ending with "_suffix"
            - "*substring*": Clears keys containing "substring"

        If no pattern is provided, clears entire cache.

        Args:
            pattern (Optional[str], optional): Wildcard pattern to match keys.
                If None, clears all entries. Defaults to None.

        Examples:
            Clear all UI files:
                >>> cache.clear(pattern="ui_*")
                >>> # Only keys starting with "ui_" removed

            Clear all config files:
                >>> cache.clear(pattern="*_config")
                >>> # Only keys ending with "_config" removed

            Clear entire cache:
                >>> cache.clear()
                >>> # All entries removed
        """
        try:
            cache = self._cache

            if pattern:
                # Clear matching keys using improved pattern matching
                keys_to_delete = [k for k in cache.keys() if self._matches_pattern(k, pattern)]
                for key in keys_to_delete:
                    del cache[key]
                self.logger.debug(
                    LOG_PREFIX_CLEAR + " %d entries matching '%s'",
                    len(keys_to_delete), pattern
                )
            else:
                # Clear entire cache
                count = len(cache)
                cache.clear()
                self.logger.debug(LOG_PREFIX_CLEAR + " %d entries", count)

        except Exception as e:
            self.logger.debug(LOG_PREFIX_ERROR + " clear - %s", e)

    def get_stats(self) -> Dict[str, Any]:
        """
        Return comprehensive cache statistics.

        Returns:
            Dict[str, Any]: Statistics dictionary containing:
                - namespace (str): Cache namespace identifier ("system_cache")
                - size (int): Current number of cached entries
                - max_size (int): Maximum entries before eviction
                - hits (int): Total cache hits
                - misses (int): Total cache misses
                - hit_rate (str): Hit rate percentage (formatted as "87.2%")
                - evictions (int): Total LRU evictions
                - invalidations (int): Total explicit/automatic invalidations

        Examples:
            >>> stats = cache.get_stats()
            >>> print(stats)
            {'namespace': 'system_cache', 'size': 42, 'max_size': 100,
             'hits': 156, 'misses': 23, 'hit_rate': '87.2%',
             'evictions': 5, 'invalidations': 12}
        """
        try:
            cache = self._cache
            total_requests = self.stats[STAT_KEY_HITS] + self.stats[STAT_KEY_MISSES]
            hit_rate = (self.stats[STAT_KEY_HITS] / total_requests * 100) if total_requests > 0 else 0

            return {
                STAT_KEY_NAMESPACE: ZCACHE_KEY_SYSTEM,
                STAT_KEY_SIZE: len(cache),
                STAT_KEY_MAX_SIZE: self.max_size,
                STAT_KEY_HITS: self.stats[STAT_KEY_HITS],
                STAT_KEY_MISSES: self.stats[STAT_KEY_MISSES],
                STAT_KEY_HIT_RATE: f"{hit_rate:.1f}%",
                STAT_KEY_EVICTIONS: self.stats[STAT_KEY_EVICTIONS],
                STAT_KEY_INVALIDATIONS: self.stats[STAT_KEY_INVALIDATIONS]
            }
        except Exception:
            return {}


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = ["SystemCache"]
