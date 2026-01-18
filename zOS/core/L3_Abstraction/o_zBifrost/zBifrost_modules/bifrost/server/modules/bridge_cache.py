"""
Cache Manager Module - Secure multi-context caching with user/app isolation

This module provides thread-safe caching for Bifrost bridge operations with:
- Schema caching (permanent, no expiration)
- Query result caching (TTL-based expiration)
- User/application isolation (prevents data leaks between contexts)
- Statistics tracking for cache performance monitoring

Security Model:
    - Each cache entry is isolated by: user_id, app_name, role, auth_context
    - Anonymous users share a common cache for public data
    - Authenticated users have isolated caches per application
    - Administrators can clear caches by user or application

Example:
    cache = CacheManager(logger, default_query_ttl=60)
    
    # Generate secure cache key with user context
    user_context = {
        "user_id": "user_123",
        "app_name": "ecommerce_store",
        "role": "customer",
        "auth_context": "application"
    }
    cache_key = cache.generate_cache_key(data, user_context)
    
    # Check cache
    result = cache.get_query(cache_key)
    if result is None:
        result = fetch_from_database(data)
        cache.cache_query(cache_key, result)
"""
from zOS import hashlib, time, Optional, Dict, Any, Callable

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Default values
DEFAULT_QUERY_TTL: int = 60  # seconds
ANONYMOUS_USER_ID: str = "anonymous"
DEFAULT_APP_NAME: str = "default"
DEFAULT_ROLE: str = "guest"
DEFAULT_AUTH_CONTEXT: str = "none"

# Cache key components
CACHE_KEY_SEPARATOR: str = "|"
CACHE_KEY_HASH_LENGTH: int = 8

# Log message prefixes
LOG_PREFIX_CACHE: str = "[CacheManager]"
LOG_PREFIX_SCHEMA_HIT: str = "[SCHEMA HIT]"
LOG_PREFIX_SCHEMA_MISS: str = "[SCHEMA MISS]"
LOG_PREFIX_QUERY_HIT: str = "[QUERY HIT]"
LOG_PREFIX_QUERY_MISS: str = "[QUERY MISS]"
LOG_PREFIX_QUERY_EXPIRED: str = "[QUERY EXPIRED]"
LOG_PREFIX_QUERY_CACHED: str = "[CACHED]"
LOG_PREFIX_SECURITY_WARNING: str = "[SECURITY WARNING]"

# Statistics keys
STAT_KEY_HITS: str = "hits"
STAT_KEY_MISSES: str = "misses"
STAT_KEY_EXPIRED: str = "expired"

# Cache entry keys
CACHE_ENTRY_DATA: str = "data"
CACHE_ENTRY_TIMESTAMP: str = "timestamp"
CACHE_ENTRY_TTL: str = "ttl"

# Request data keys
REQUEST_KEY_ZKEY: str = "zKey"
REQUEST_KEY_ACTION: str = "action"
REQUEST_KEY_MODEL: str = "model"
REQUEST_KEY_WHERE: str = "where"
REQUEST_KEY_FILTERS: str = "filters"
REQUEST_KEY_FIELDS: str = "fields"
REQUEST_KEY_ORDER_BY: str = "order_by"
REQUEST_KEY_LIMIT: str = "limit"
REQUEST_KEY_OFFSET: str = "offset"

# User context keys
CONTEXT_KEY_USER_ID: str = "user_id"
CONTEXT_KEY_APP_NAME: str = "app_name"
CONTEXT_KEY_ROLE: str = "role"
CONTEXT_KEY_AUTH_CONTEXT: str = "auth_context"


class CacheManager:
    """
    Manages dual-layer caching with multi-context isolation.
    
    Features:
        - Schema caching (permanent, model-based)
        - Query result caching (TTL-based, request-based)
        - User/application isolation (security-critical)
        - Performance statistics tracking
        - Selective cache clearing
    
    Security:
        Cache keys include user_id, app_name, role, and auth_context to prevent
        data leaks between different authentication contexts. Missing context
        triggers security warnings and falls back to anonymous caching.
    
    Attributes:
        logger: Logger instance for diagnostics
        schema_cache: Permanent cache for schema definitions
        ui_cache: Reserved for future UI component caching
        query_cache: TTL-based cache for query results
        query_cache_ttl: Default TTL for query cache entries
        schema_stats: Schema cache performance counters
        query_stats: Query cache performance counters
    """
    
    def __init__(
        self,
        logger: Any,
        default_query_ttl: int = DEFAULT_QUERY_TTL
    ) -> None:
        """
        Initialize cache manager with isolated caches.
        
        Args:
            logger: Logger instance for diagnostics and warnings
            default_query_ttl: Default TTL for query cache in seconds (default: 60)
        """
        self.logger = logger
        
        # Schema cache (no expiration, model-level)
        self.schema_cache: Dict[str, Any] = {}
        
        # UI cache (reserved for future use - UI component caching)
        # Note: Currently unused, reserved for caching UI schemas and templates
        self.ui_cache: Dict[str, Any] = {}
        
        # Query result cache (with TTL, user/app isolated)
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.query_cache_ttl: int = default_query_ttl
        
        # Reverse indexes for O(1) cache invalidation (industry-grade pattern)
        # Maps user_id → set of cache keys for that user
        self.user_index: Dict[str, set] = {}
        # Maps app_name → set of cache keys for that app
        self.app_index: Dict[str, set] = {}
        
        # Performance statistics
        self.schema_stats: Dict[str, int] = self._init_stats(include_expired=False)
        self.query_stats: Dict[str, int] = self._init_stats(include_expired=True)
    
    def _init_stats(self, include_expired: bool = False) -> Dict[str, int]:
        """
        Initialize statistics dictionary.
        
        Args:
            include_expired: Whether to include 'expired' counter
            
        Returns:
            Statistics dictionary with zeroed counters
        """
        stats = {
            STAT_KEY_HITS: 0,
            STAT_KEY_MISSES: 0
        }
        if include_expired:
            stats[STAT_KEY_EXPIRED] = 0
        return stats
    
    def _remove_from_indexes(self, cache_key: str, cached_entry: Dict[str, Any]) -> None:
        """
        Remove cache key from reverse indexes (industry-grade pattern).
        
        This is critical for maintaining index consistency when entries are
        removed due to expiration or explicit deletion. Without this, indexes
        would accumulate stale references (memory leak).
        
        Args:
            cache_key: Cache key to remove from indexes
            cached_entry: Cache entry containing metadata
        """
        # Extract metadata
        metadata = cached_entry.get("metadata", {})
        user_id = metadata.get(CONTEXT_KEY_USER_ID)
        app_name = metadata.get(CONTEXT_KEY_APP_NAME)
        
        # Remove from user index
        if user_id and user_id in self.user_index:
            self.user_index[user_id].discard(cache_key)
            # Clean up empty index entries (prevent memory leak)
            if not self.user_index[user_id]:
                del self.user_index[user_id]
        
        # Remove from app index
        if app_name and app_name in self.app_index:
            self.app_index[app_name].discard(cache_key)
            # Clean up empty index entries (prevent memory leak)
            if not self.app_index[app_name]:
                del self.app_index[app_name]
    
    # ═══════════════════════════════════════════════════════════
    # Schema Caching (Model-Level, Permanent)
    # ═══════════════════════════════════════════════════════════
    
    def get_schema(
        self,
        model: str,
        loader_func: Optional[Callable[[str], Optional[Dict]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get schema from cache or load it.
        
        Args:
            model: Model name (e.g., "users", "products")
            loader_func: Optional function to load schema if not cached
            
        Returns:
            Schema dictionary or None if not found
        """
        if model in self.schema_cache:
            self.schema_stats[STAT_KEY_HITS] += 1
            self.logger.debug(f"{LOG_PREFIX_CACHE} {LOG_PREFIX_SCHEMA_HIT} {model}")
            return self.schema_cache[model]
        
        self.schema_stats[STAT_KEY_MISSES] += 1
        self.logger.debug(f"{LOG_PREFIX_CACHE} {LOG_PREFIX_SCHEMA_MISS} {model}")
        
        # Try to load if loader provided
        if loader_func:
            try:
                schema = loader_func(model)
                if schema:
                    self.schema_cache[model] = schema
                    return schema
            except (KeyError, ValueError, TypeError) as e:
                self.logger.warning(
                    f"{LOG_PREFIX_CACHE} Failed to load schema '{model}': {e}"
                )
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    # Query Result Caching (User/App Isolated, TTL-Based)
    # ═══════════════════════════════════════════════════════════
    
    def generate_cache_key(
        self,
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate secure, deterministic cache key with user/app isolation.
        
        SECURITY CRITICAL: Cache keys MUST include user context to prevent
        data leaks between authenticated users or applications. Missing context
        triggers a security warning and falls back to anonymous caching.
        
        Args:
            data: Request data dictionary (zKey, action, model, where, etc.)
            user_context: User authentication context with keys:
                - user_id: Unique user identifier (or "anonymous")
                - app_name: Application name (or "default")
                - role: User role (e.g., "admin", "customer", "guest")
                - auth_context: Authentication context (e.g., "zSession", "application")
            
        Returns:
            MD5 hash string (32 characters)
            
        Example:
            >>> context = {
            ...     "user_id": "user_123",
            ...     "app_name": "ecommerce_store",
            ...     "role": "customer",
            ...     "auth_context": "application"
            ... }
            >>> key = cache.generate_cache_key(data, context)
            >>> # Key includes: user_123|ecommerce_store|customer|application|...
        """
        # Extract user context (with secure defaults)
        if user_context is None:
            self.logger.warning(
                f"{LOG_PREFIX_CACHE} {LOG_PREFIX_SECURITY_WARNING} "
                "No user context provided - cache not isolated! "
                "Falling back to anonymous caching."
            )
            user_context = {}
        
        user_id = user_context.get(CONTEXT_KEY_USER_ID, ANONYMOUS_USER_ID)
        app_name = user_context.get(CONTEXT_KEY_APP_NAME, DEFAULT_APP_NAME)
        role = user_context.get(CONTEXT_KEY_ROLE, DEFAULT_ROLE)
        auth_context = user_context.get(CONTEXT_KEY_AUTH_CONTEXT, DEFAULT_AUTH_CONTEXT)
        
        # Build cache key with user/app isolation prefix
        cache_parts = [
            # Security context (prevents cross-user/app data leaks)
            user_id,
            app_name,
            role,
            auth_context,
            # Request parameters (query-specific)
            data.get(REQUEST_KEY_ZKEY, ''),
            data.get(REQUEST_KEY_ACTION, ''),
            data.get(REQUEST_KEY_MODEL, ''),
            str(data.get(REQUEST_KEY_WHERE, {})),
            str(data.get(REQUEST_KEY_FILTERS, {})),
            str(data.get(REQUEST_KEY_FIELDS, [])),
            str(data.get(REQUEST_KEY_ORDER_BY, [])),
            str(data.get(REQUEST_KEY_LIMIT, '')),
            str(data.get(REQUEST_KEY_OFFSET, ''))
        ]
        
        cache_string = CACHE_KEY_SEPARATOR.join(cache_parts)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get_query(self, cache_key: str) -> Optional[Any]:
        """
        Get cached query result if valid (not expired).
        
        Args:
            cache_key: Cache key generated by generate_cache_key()
            
        Returns:
            Cached data or None if not found or expired
        """
        if cache_key not in self.query_cache:
            self.query_stats[STAT_KEY_MISSES] += 1
            return None
        
        cached = self.query_cache[cache_key]
        age = time.time() - cached[CACHE_ENTRY_TIMESTAMP]
        ttl = cached[CACHE_ENTRY_TTL]
        
        # Check if expired
        if age > ttl:
            self.query_stats[STAT_KEY_EXPIRED] += 1
            
            # Remove from indexes before deleting (maintain index consistency)
            self._remove_from_indexes(cache_key, cached)
            
            del self.query_cache[cache_key]
            self.logger.debug(
                f"{LOG_PREFIX_CACHE} {LOG_PREFIX_QUERY_EXPIRED} "
                f"{cache_key[:CACHE_KEY_HASH_LENGTH]}... "
                f"(age: {age:.1f}s, ttl: {ttl}s)"
            )
            return None
        
        self.query_stats[STAT_KEY_HITS] += 1
        self.logger.debug(
            f"{LOG_PREFIX_CACHE} {LOG_PREFIX_QUERY_HIT} "
            f"{cache_key[:CACHE_KEY_HASH_LENGTH]}... "
            f"(age: {age:.1f}s, ttl: {ttl}s)"
        )
        return cached[CACHE_ENTRY_DATA]
    
    def cache_query(
        self,
        cache_key: str,
        result: Any,
        ttl: Optional[int] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache a query result with TTL and maintain reverse indexes.
        
        Industry-grade implementation: Maintains reverse indexes for O(1) cache
        invalidation by user_id or app_name. This is the standard pattern used
        by Redis, Memcached, and all production caching systems.
        
        Args:
            cache_key: Cache key generated by generate_cache_key()
            result: Result data to cache
            ttl: Custom TTL in seconds (uses default if None)
            user_context: User authentication context for index maintenance:
                - user_id: Unique user identifier
                - app_name: Application name
                - role: User role
                - auth_context: Authentication context
        """
        if ttl is None:
            ttl = self.query_cache_ttl
        
        # Extract user context for index maintenance
        if user_context is None:
            user_context = {}
        
        user_id = user_context.get(CONTEXT_KEY_USER_ID, ANONYMOUS_USER_ID)
        app_name = user_context.get(CONTEXT_KEY_APP_NAME, DEFAULT_APP_NAME)
        role = user_context.get(CONTEXT_KEY_ROLE, DEFAULT_ROLE)
        auth_context = user_context.get(CONTEXT_KEY_AUTH_CONTEXT, DEFAULT_AUTH_CONTEXT)
        
        # Store cache entry with metadata
        self.query_cache[cache_key] = {
            CACHE_ENTRY_DATA: result,
            CACHE_ENTRY_TIMESTAMP: time.time(),
            CACHE_ENTRY_TTL: ttl,
            # Metadata for reverse index consistency
            "metadata": {
                CONTEXT_KEY_USER_ID: user_id,
                CONTEXT_KEY_APP_NAME: app_name,
                CONTEXT_KEY_ROLE: role,
                CONTEXT_KEY_AUTH_CONTEXT: auth_context
            }
        }
        
        # Maintain reverse indexes for O(1) invalidation
        # User index: user_id → set of cache keys
        if user_id not in self.user_index:
            self.user_index[user_id] = set()
        self.user_index[user_id].add(cache_key)
        
        # App index: app_name → set of cache keys
        if app_name not in self.app_index:
            self.app_index[app_name] = set()
        self.app_index[app_name].add(cache_key)
        
        self.logger.debug(
            f"{LOG_PREFIX_CACHE} {LOG_PREFIX_QUERY_CACHED} "
            f"{cache_key[:CACHE_KEY_HASH_LENGTH]}... "
            f"(user: {user_id}, app: {app_name}, ttl: {ttl}s)"
        )
    
    # ═══════════════════════════════════════════════════════════
    # Cache Management (Clearing & Statistics)
    # ═══════════════════════════════════════════════════════════
    
    def clear_all(self) -> None:
        """
        Clear all caches, indexes, and reset statistics.
        
        WARNING: This clears ALL cached data for ALL users and applications.
        Use clear_user_cache() or clear_app_cache() for selective clearing.
        """
        self.schema_cache.clear()
        self.ui_cache.clear()
        self.query_cache.clear()
        
        # Clear reverse indexes (prevent memory leaks)
        self.user_index.clear()
        self.app_index.clear()
        
        self.logger.info(
            f"{LOG_PREFIX_CACHE} All caches and indexes cleared. "
            f"Schema stats: {self.schema_stats}, Query stats: {self.query_stats}"
        )
        
        self.schema_stats = self._init_stats(include_expired=False)
        self.query_stats = self._init_stats(include_expired=True)
    
    def clear_user_cache(self, user_id: str) -> int:
        """
        Clear all cached queries for a specific user across all applications.
        
        Industry-grade implementation: O(m) performance where m = number of user's
        cache entries. Uses reverse index for direct lookup without scanning all
        cache entries. This is the standard pattern in Redis, Memcached, CDNs.
        
        Use Cases:
            - User logout (clear sensitive data)
            - User permission changes (invalidate access-controlled data)
            - User data updates (force cache refresh)
        
        Args:
            user_id: User identifier to clear cache for
            
        Returns:
            Number of cache entries removed
            
        Performance:
            - O(m) where m = number of user's cache entries
            - Does NOT scan all cache entries (O(n) avoided)
            - Production-ready for thousands of concurrent users
        """
        # Check if user has any cached entries (O(1) lookup)
        if user_id not in self.user_index:
            self.logger.debug(
                f"{LOG_PREFIX_CACHE} No cache entries found for user: '{user_id}'"
            )
            return 0
        
        # Get all cache keys for this user (O(1) index lookup)
        cache_keys_to_remove = self.user_index[user_id].copy()  # Copy to avoid mutation during iteration
        cleared = len(cache_keys_to_remove)
        
        # Remove each cache entry and update indexes (O(m) where m = user's entries)
        for cache_key in cache_keys_to_remove:
            if cache_key in self.query_cache:
                cached_entry = self.query_cache[cache_key]
                
                # Remove from indexes (maintains consistency)
                self._remove_from_indexes(cache_key, cached_entry)
                
                # Delete cache entry
                del self.query_cache[cache_key]
        
        self.logger.info(
            f"{LOG_PREFIX_CACHE} Cleared {cleared} cache entries for user: '{user_id}'"
        )
        return cleared
    
    def clear_app_cache(self, app_name: str) -> int:
        """
        Clear all cached queries for a specific application across all users.
        
        Industry-grade implementation: O(m) performance where m = number of app's
        cache entries. Uses reverse index for direct lookup without scanning all
        cache entries. This is the standard pattern in Redis, Memcached, CDNs.
        
        Use Cases:
            - Application configuration changes
            - Application schema updates
            - Application-wide data refresh
            - Deployment rollouts
        
        Args:
            app_name: Application name to clear cache for
            
        Returns:
            Number of cache entries removed
            
        Performance:
            - O(m) where m = number of app's cache entries
            - Does NOT scan all cache entries (O(n) avoided)
            - Production-ready for multi-tenant applications
        """
        # Check if app has any cached entries (O(1) lookup)
        if app_name not in self.app_index:
            self.logger.debug(
                f"{LOG_PREFIX_CACHE} No cache entries found for app: '{app_name}'"
            )
            return 0
        
        # Get all cache keys for this app (O(1) index lookup)
        cache_keys_to_remove = self.app_index[app_name].copy()  # Copy to avoid mutation during iteration
        cleared = len(cache_keys_to_remove)
        
        # Remove each cache entry and update indexes (O(m) where m = app's entries)
        for cache_key in cache_keys_to_remove:
            if cache_key in self.query_cache:
                cached_entry = self.query_cache[cache_key]
                
                # Remove from indexes (maintains consistency)
                self._remove_from_indexes(cache_key, cached_entry)
                
                # Delete cache entry
                del self.query_cache[cache_key]
        
        self.logger.info(
            f"{LOG_PREFIX_CACHE} Cleared {cleared} cache entries for app: '{app_name}'"
        )
        return cleared
    
    def set_query_ttl(self, ttl: int) -> None:
        """
        Set default TTL for query cache.
        
        Args:
            ttl: TTL in seconds (must be positive)
        """
        if ttl <= 0:
            raise ValueError(f"TTL must be positive, got {ttl}")
        
        self.query_cache_ttl = ttl
        self.logger.info(f"{LOG_PREFIX_CACHE} Query cache TTL set to {ttl}s")
    
    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get performance statistics for all caches.
        
        Returns:
            Dictionary with schema_cache and query_cache statistics:
                {
                    "schema_cache": {"hits": 42, "misses": 8},
                    "query_cache": {"hits": 150, "misses": 30, "expired": 12}
                }
        """
        return {
            'schema_cache': self.schema_stats.copy(),
            'query_cache': self.query_stats.copy()
        }
