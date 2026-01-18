# zCLI/subsystems/zLoader/loader_modules/loader_cache_pinned.py

"""
Pinned cache for user-loaded aliases with no auto-eviction (highest priority).

This module provides a specialized caching layer for user-loaded aliases within
the zLoader subsystem. Unlike other caches, the pinned cache NEVER auto-evicts
entries, giving users complete control over cached aliases. This is the highest
priority cache tier, used exclusively for aliases loaded via `load --as` commands.

Purpose
-------
The PinnedCache serves as Tier 2 (Cache Implementations) in the zLoader architecture,
providing a session-based cache for user-loaded aliases. It sits alongside other
cache implementations (SystemCache, SchemaCache, PluginCache) but differs fundamentally
in that it never automatically removes entries - only explicit user actions can
remove pinned aliases.

Architecture
------------
**Tier 2 - Cache Implementations (Pinned Cache)**
    - Position: Cache tier for user-loaded aliases
    - Dependencies: time (from zCLI), zConfig constants
    - Used By: CacheOrchestrator (line 21)
    - Purpose: No-eviction cache for highest priority user-loaded resources

Key Features
------------
1. **No Auto-Eviction**: Entries remain cached until explicitly removed by user,
   ensuring aliases are always available once loaded.

2. **Highest Priority**: Pinned aliases take precedence over all other cached
   resources in the system.

3. **User-Controlled**: Only user actions (remove, clear) can delete entries,
   providing predictable and reliable caching behavior.

4. **Rich Metadata**: Each alias includes parsed schema data, zpath, type,
   loaded_at timestamp, and calculated age.

5. **Pattern-Based Management**: Supports wildcard patterns for bulk alias
   management (e.g., "db_*" to manage database aliases).

6. **Session Isolation**: Aliases stored in session dict under
   SESSION_KEY_ZCACHE/ZCACHE_KEY_PINNED namespace.

Design Decisions
----------------
1. **No Eviction Policy**: Unlike SystemCache (LRU eviction), pinned cache never
   evicts automatically. This design ensures user-loaded aliases remain available
   for the entire session duration.

2. **Session Storage**: Aliases stored in session dict rather than class attributes
   to support session persistence and isolation.

3. **Alias Key Format**: Uses "alias:{name}" prefix for keys to avoid collisions
   with other cache types and enable pattern-based operations.

4. **Metadata Tracking**: Each entry includes loaded_at timestamp and calculated
   age for debugging and user information.

5. **Schema Type Only**: Currently only supports parsed schemas (type="schema"),
   but architecture allows future expansion to other types.

Cache Strategy
--------------
**When to Cache**:
    - User executes `load --as ALIAS_NAME` command
    - Parsed schema loaded via load_alias()
    - Explicit user action only (never automatic)

**When to Invalidate**:
    - User executes explicit remove command (remove_alias)
    - User clears cache with pattern (clear pattern="db_*")
    - User clears entire cache (clear)
    - Session ends (cache destroyed with session)

**No Eviction**:
    - NEVER automatically evicts entries
    - No max_size limit (unlike SystemCache)
    - User has complete control

External Usage
--------------
**Used By**:
    - zCLI/subsystems/zLoader/loader_modules/cache_orchestrator.py (Line 21)
      Usage: self.pinned_cache = PinnedCache(session, logger)
      Purpose: Routes pinned cache requests (type="pinned")

    - User Commands:
      - `load --as myalias path/to/schema.yaml` → load_alias()
      - `unload myalias` or similar → remove_alias()
      - `cache clear pinned` → clear()

Usage Examples
--------------
**Load Alias**:
    >>> session = {}
    >>> logger = get_logger()
    >>> cache = PinnedCache(session, logger)
    >>> parsed_schema = {"table": "users", "fields": [...]}
    >>> cache.load_alias("users_db", parsed_schema, "~/db/users.yaml")
    >>> # Alias cached as $users_db, available until explicitly removed

**Get Alias**:
    >>> data = cache.get_alias("users_db")
    >>> print(data)
    {'table': 'users', 'fields': [...]}

**Check Existence**:
    >>> if cache.has_alias("users_db"):
    ...     print("Alias exists")

**List All Aliases**:
    >>> aliases = cache.list_aliases()
    >>> for alias in aliases:
    ...     print(f"${alias['name']} -> {alias['zpath']}")

**Get Alias Info**:
    >>> info = cache.get_info("users_db")
    >>> print(info)
    {'name': 'users_db', 'zpath': '~/db/users.yaml', 'type': 'schema',
     'loaded_at': 1699000000.0, 'age': 3600.5, 'size': 2048}

**Remove Alias**:
    >>> cache.remove_alias("users_db")
    >>> # Alias removed from cache

**Pattern-Based Clearing**:
    >>> cache.clear(pattern="db_*")  # Clears all db_* aliases
    >>> cache.clear(pattern="*_test")  # Clears all *_test aliases

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 2 Cache Implementations)
    - Tier 1: Foundation (loader_io.py - File I/O)
    - Tier 2: Cache Implementations ← THIS MODULE
        - SystemCache (UI/config files with LRU)
        - PinnedCache (User aliases, no eviction) ← THIS
        - SchemaCache (DB connections)
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
    - zConfig constants: SESSION_KEY_ZCACHE, ZCACHE_KEY_PINNED

Performance Considerations
--------------------------
- **Memory**: No size limit, grows with user-loaded aliases. Typical usage:
  1-20 aliases per session, ~1-10KB per alias = ~10-200KB total.
- **No Eviction Overhead**: Simpler than LRU caches, no move_to_end() calls.
- **Age Calculation**: Uses time.time() for age calculation, negligible overhead.
- **Pattern Matching**: List comprehension for pattern clearing, O(n) where n is
  number of aliases (typically small).

Thread Safety
-------------
This class is NOT thread-safe. Session dict access is not synchronized. If using
zCLI in a multi-threaded environment, ensure session dict access is protected
by locks or use thread-local storage.

See Also
--------
- cache_orchestrator.py: Routes cache requests to this class
- loader_cache_system.py: System cache with LRU eviction
- loader_cache_schema.py: Database connection cache
- loader_cache_plugin.py: Plugin instance cache

Version History
---------------
- v1.5.4: Industry-grade upgrade (type hints, constants, comprehensive docs,
          zConfig modernization, DRY refactoring, improved pattern matching)
- v1.5.3: Original implementation (156 lines, basic pinned cache)
"""

from zOS import time, Any, Dict, List, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZCACHE, ZCACHE_KEY_PINNED

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Log Prefixes
LOG_PREFIX_LOADED: str = "[PinnedCache]"
LOG_PREFIX_HIT: str = "[PinnedCache HIT]"
LOG_PREFIX_ERROR: str = "[PinnedCache ERROR]"

# Entry Keys (cache entry structure)
ENTRY_KEY_DATA: str = "data"
ENTRY_KEY_ZPATH: str = "zpath"
ENTRY_KEY_TYPE: str = "type"
ENTRY_KEY_LOADED_AT: str = "loaded_at"

# Alias Keys (returned in list/info)
ALIAS_KEY_NAME: str = "name"
ALIAS_KEY_AGE: str = "age"
ALIAS_KEY_SIZE: str = "size"

# Key Format
ALIAS_KEY_PREFIX: str = "alias:"
ALIAS_TYPE_SCHEMA: str = "schema"

# Wildcard
WILDCARD_CHAR: str = "*"

# ============================================================================
# PINNEDCACHE CLASS
# ============================================================================


class PinnedCache:
    """
    Pinned cache for user-loaded aliases with no auto-eviction (highest priority).

    This class implements a specialized caching layer for user-loaded aliases,
    providing permanent (session-lifetime) caching with no automatic eviction.
    Unlike SystemCache (LRU eviction) or PluginCache (mtime invalidation), the
    pinned cache only removes entries when explicitly requested by the user.

    The cache is stored in the session dict under SESSION_KEY_ZCACHE/ZCACHE_KEY_PINNED
    namespace. Each alias is identified by a unique name and includes metadata
    (zpath, type, loaded_at) for debugging and user information.

    Attributes:
        session (Dict[str, Any]): Session dictionary containing cache namespace
        logger (Any): Logger instance for info/debug/error messages

    No-Eviction Policy:
        - **No max_size limit**: Cache grows with user-loaded aliases
        - **No LRU eviction**: Entries never automatically removed
        - **User control**: Only explicit remove/clear operations delete entries
        - **Session lifetime**: Aliases persist for entire session duration

    Thread Safety:
        NOT thread-safe. Session dict access is not synchronized.
    """

    def __init__(self, session: Dict[str, Any], logger: Any) -> None:
        """
        Initialize pinned cache with session and logger.

        Args:
            session (Dict[str, Any]): Session dictionary to store cache data.
                Must be a mutable dict that persists across zCLI operations.
            logger (Any): Logger instance for info/debug/error messages. Typically
                from zConfig.logger.

        Notes:
            - Cache namespace created automatically if not present
            - Session dict structure: session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PINNED]
            - No size limit (unlike SystemCache with max_size)
        """
        self.session = session
        self.logger = logger
        self._ensure_namespace()

    @property
    def _cache(self) -> Dict[str, Any]:
        """
        Get cache dict from session (DRY helper property).

        Returns:
            Dict[str, Any]: The cache dict from session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PINNED]

        Notes:
            This property replaces repeated `self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PINNED]`
            access throughout the class, following DRY (Don't Repeat Yourself) principle.
        """
        return self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PINNED]

    def _make_alias_key(self, alias_name: str) -> str:
        """
        Create consistent alias key with prefix (DRY helper method).

        Args:
            alias_name (str): Alias name (e.g., "users_db")

        Returns:
            str: Formatted key with prefix (e.g., "alias:users_db")

        Notes:
            This method replaces repeated `f"alias:{alias_name}"` formatting,
            ensuring consistent key format across all methods.
        """
        return f"{ALIAS_KEY_PREFIX}{alias_name}"

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
            >>> cache._matches_pattern("alias:db_users", "alias:db_*")
            True
            >>> cache._matches_pattern("alias:test_db_users", "alias:db_*")
            False  # Doesn't match (not a prefix)
            >>> cache._matches_pattern("alias:users_config", "alias:*_config")
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

    def _ensure_namespace(self) -> None:
        """
        Ensure pinned_cache namespace exists in session with proper structure.

        Creates the cache namespace structure if not present:
            session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PINNED] = {}

        Notes:
            - Called automatically during __init__
            - Safe to call multiple times (idempotent)
            - Creates regular dict (not OrderedDict like SystemCache)
        """
        if SESSION_KEY_ZCACHE not in self.session:
            self.session[SESSION_KEY_ZCACHE] = {}

        if ZCACHE_KEY_PINNED not in self.session[SESSION_KEY_ZCACHE]:
            self.session[SESSION_KEY_ZCACHE][ZCACHE_KEY_PINNED] = {}

    def load_alias(self, alias_name: str, parsed_schema: Any, zpath: str) -> Any:
        """
        Load alias from `load --as` command (user action).

        Caches parsed schema under the given alias name. The alias will persist
        for the entire session duration and can only be removed by explicit user
        action (remove_alias or clear).

        Args:
            alias_name (str): Alias name for cached schema (e.g., "users_db").
                Users reference this as $users_db.
            parsed_schema (Any): Parsed schema data to cache (typically dict).
            zpath (str): File path where schema was loaded from (for user reference).

        Returns:
            Any: The parsed_schema that was cached (for chaining).

        Examples:
            >>> parsed_schema = {"table": "users", "fields": [...]}
            >>> cache.load_alias("users_db", parsed_schema, "~/db/users.yaml")
            >>> # User can now reference $users_db in commands

        Notes:
            - Uses .info() logging for user-visible actions
            - Entry includes metadata: data, zpath, type, loaded_at
            - No size limit, no eviction
        """
        try:
            cache = self._cache
            key = self._make_alias_key(alias_name)

            cache[key] = {
                ENTRY_KEY_DATA: parsed_schema,
                ENTRY_KEY_ZPATH: zpath,
                ENTRY_KEY_TYPE: ALIAS_TYPE_SCHEMA,
                ENTRY_KEY_LOADED_AT: time.time()
            }

            self.logger.framework.debug(LOG_PREFIX_LOADED + " Alias loaded: $%s => %s", alias_name, zpath)

        except Exception as e:
            self.logger.error(LOG_PREFIX_ERROR + " %s - %s", alias_name, e)

        return parsed_schema

    def get_alias(self, alias_name: str) -> Optional[Any]:
        """
        Get alias by name (cache lookup).

        Retrieves cached schema data for the given alias name. This is typically
        called when user references $alias_name in commands.

        Args:
            alias_name (str): Alias name to retrieve (e.g., "users_db")

        Returns:
            Optional[Any]: Cached schema data on hit, None on miss or error

        Examples:
            >>> data = cache.get_alias("users_db")
            >>> if data:
            ...     print(f"Schema: {data['table']}")
        """
        try:
            cache = self._cache
            key = self._make_alias_key(alias_name)

            if key in cache:
                entry = cache[key]
                self.logger.debug(LOG_PREFIX_HIT + " $%s", alias_name)
                return entry.get(ENTRY_KEY_DATA)

            return None

        except Exception as e:
            self.logger.debug(LOG_PREFIX_ERROR + " %s - %s", alias_name, e)
            return None

    def has_alias(self, alias_name: str) -> bool:
        """
        Check if alias exists in cache.

        Args:
            alias_name (str): Alias name to check (e.g., "users_db")

        Returns:
            bool: True if alias exists, False otherwise

        Examples:
            >>> if cache.has_alias("users_db"):
            ...     print("Alias exists")
        """
        try:
            key = self._make_alias_key(alias_name)
            return key in self._cache
        except Exception:
            return False

    def remove_alias(self, alias_name: str) -> bool:
        """
        Remove specific alias from cache (user action).

        Explicitly removes an alias from the cache. This is typically called
        when user executes an unload or remove command.

        Args:
            alias_name (str): Alias name to remove (e.g., "users_db")

        Returns:
            bool: True if alias was removed, False if not found or error

        Examples:
            >>> if cache.remove_alias("users_db"):
            ...     print("Alias removed")
            ... else:
            ...     print("Alias not found")

        Notes:
            - Uses .info() logging for user-visible actions
            - Returns False if alias doesn't exist (not an error)
        """
        try:
            cache = self._cache
            key = self._make_alias_key(alias_name)

            if key in cache:
                del cache[key]
                self.logger.framework.debug(LOG_PREFIX_LOADED + " Removed: $%s", alias_name)
                return True
            return False
        except Exception as e:
            self.logger.error(LOG_PREFIX_ERROR + " %s - %s", alias_name, e)
            return False

    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear pinned aliases, optionally filtering by wildcard pattern.

        Supports two pattern formats:
            1. Alias name pattern: "user*", "*_test" (without "alias:" prefix)
            2. Full key pattern: "alias:user*", "alias:*_test" (with "alias:" prefix)

        Wildcard patterns:
            - "prefix_*": Clears keys starting with "prefix_"
            - "*_suffix": Clears keys ending with "_suffix"
            - "*substring*": Clears keys containing "substring"

        If no pattern is provided, clears all aliases.

        Args:
            pattern (Optional[str], optional): Wildcard pattern to match keys.
                If None, clears all aliases. Defaults to None.
                Can be alias name pattern (e.g., "user*") or full key pattern (e.g., "alias:user*").

        Returns:
            int: Number of aliases removed

        Examples:
            Clear all user aliases (alias name pattern):
                >>> count = cache.clear(pattern="user*")
                >>> print(f"{count} aliases removed")

            Clear all database aliases (full key pattern):
                >>> count = cache.clear(pattern="alias:db_*")

            Clear all test aliases:
                >>> count = cache.clear(pattern="*_test")

            Clear all aliases:
                >>> count = cache.clear()

        Notes:
            - Uses .info() logging for user-visible actions
            - Pattern matching uses improved wildcard handling
            - Automatically adds "alias:" prefix if not present
        """
        try:
            cache = self._cache

            if pattern:
                # Add "alias:" prefix if not present for user convenience
                if not pattern.startswith(ALIAS_KEY_PREFIX):
                    pattern = ALIAS_KEY_PREFIX + pattern

                # Clear matching keys using improved pattern matching
                keys_to_delete = [k for k in cache.keys() if self._matches_pattern(k, pattern)]
                for key in keys_to_delete:
                    del cache[key]
                self.logger.framework.debug(
                    LOG_PREFIX_LOADED + " Removed %d aliases matching '%s'",
                    len(keys_to_delete), pattern
                )
                return len(keys_to_delete)

            # Clear all aliases
            count = len(cache)
            cache.clear()
            self.logger.framework.debug(LOG_PREFIX_LOADED + " Removed all %d aliases", count)
            return count

        except Exception as e:
            self.logger.error(LOG_PREFIX_ERROR + " clear - %s", e)
            return 0

    def list_aliases(self) -> List[Dict[str, Any]]:
        """
        List all cached aliases with metadata.

        Returns a list of dicts, each containing alias metadata:
            - name (str): Alias name
            - zpath (str): File path where schema was loaded from
            - type (str): Alias type (currently always "schema")
            - loaded_at (float): Unix timestamp when alias was loaded
            - age (float): Age in seconds since loaded_at

        Returns:
            List[Dict[str, Any]]: List of alias metadata dicts, empty list on error

        Examples:
            >>> aliases = cache.list_aliases()
            >>> for alias in aliases:
            ...     print(f"${alias['name']} ({alias['age']:.1f}s old)")
            $users_db (120.5s old)
            $products_db (45.2s old)

        Notes:
            - Only includes entries with "alias:" prefix
            - Calculates age dynamically (time.time() - loaded_at)
        """
        try:
            cache = self._cache

            aliases = []
            for key, entry in cache.items():
                if key.startswith(ALIAS_KEY_PREFIX):
                    alias_name = key.replace(ALIAS_KEY_PREFIX, "")
                    aliases.append({
                        ALIAS_KEY_NAME: alias_name,
                        ENTRY_KEY_ZPATH: entry.get(ENTRY_KEY_ZPATH),
                        ENTRY_KEY_TYPE: entry.get(ENTRY_KEY_TYPE),
                        ENTRY_KEY_LOADED_AT: entry.get(ENTRY_KEY_LOADED_AT),
                        ALIAS_KEY_AGE: time.time() - entry.get(ENTRY_KEY_LOADED_AT, time.time())
                    })

            return aliases

        except Exception as e:
            self.logger.error(LOG_PREFIX_ERROR + " list - %s", e)
            return []

    def get_info(self, alias_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metadata about a specific alias.

        Returns a dict containing alias metadata:
            - name (str): Alias name
            - zpath (str): File path where schema was loaded from
            - type (str): Alias type (currently always "schema")
            - loaded_at (float): Unix timestamp when alias was loaded
            - age (float): Age in seconds since loaded_at
            - size (int): Approximate size of cached data in bytes

        Args:
            alias_name (str): Alias name to get info for (e.g., "users_db")

        Returns:
            Optional[Dict[str, Any]]: Alias metadata dict on success, None if not found or error

        Examples:
            >>> info = cache.get_info("users_db")
            >>> if info:
            ...     print(f"${info['name']}: {info['size']} bytes, {info['age']:.1f}s old")
            $users_db: 2048 bytes, 120.5s old
        """
        try:
            cache = self._cache
            key = self._make_alias_key(alias_name)

            if key in cache:
                entry = cache[key]
                return {
                    ALIAS_KEY_NAME: alias_name,
                    ENTRY_KEY_ZPATH: entry.get(ENTRY_KEY_ZPATH),
                    ENTRY_KEY_TYPE: entry.get(ENTRY_KEY_TYPE),
                    ENTRY_KEY_LOADED_AT: entry.get(ENTRY_KEY_LOADED_AT),
                    ALIAS_KEY_AGE: time.time() - entry.get(ENTRY_KEY_LOADED_AT, time.time()),
                    ALIAS_KEY_SIZE: len(str(entry.get(ENTRY_KEY_DATA, "")))
                }

            return None

        except Exception as e:
            self.logger.error(LOG_PREFIX_ERROR + " get_info - %s", e)
            return None


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = ["PinnedCache"]
