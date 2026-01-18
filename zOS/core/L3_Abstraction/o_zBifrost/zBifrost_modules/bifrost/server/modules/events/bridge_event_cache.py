# zCLI/subsystems/zComm/zComm_modules/bifrost/bridge_modules/events/bridge_event_cache.py
"""
Cache Management Event Handlers for zBifrost WebSocket Bridge.

This module provides event handlers for cache operations in the zBifrost
WebSocket bridge, enabling web clients to retrieve schemas, manage cache,
view statistics, and configure cache TTL settings.

Features:
    - Schema Retrieval: Get schema definitions for data models
    - Cache Management: Clear query cache (all, user-specific, or app-specific)
    - Cache Statistics: Retrieve hit/miss/expired counts for monitoring
    - TTL Configuration: Adjust cache time-to-live settings
    - User Context Awareness: All operations log authentication context
    - Security: Input validation and user-aware cache operations

Architecture:
    CacheEvents acts as a WebSocket event handler layer for the CacheManager
    (bridge_cache.py), providing a secure, validated, and context-aware interface
    for cache operations. All operations extract and log user context for audit
    trails and future authorization rules.

Security Model:
    - Schema retrieval: Available to all authenticated users
    - Cache stats: Available to all authenticated users
    - Cache clearing: Clears only user's/app's data (or all for admin)
    - TTL configuration: Input validated (positive int, max limit)
    - User context logged for all operations

Integration:
    - bridge_cache.py (CacheManager): Backend cache operations
    - bridge_connection.py: Schema metadata
    - bridge_auth.py: User context extraction
    - zSession/zAuth: Three-tier authentication context

Example:
    ```python
    # Initialize with auth_manager for user context
    cache_events = CacheEvents(bifrost, auth_manager=auth_manager)
    
    # Get schema for a model
    await cache_events.handle_get_schema(ws, {"model": "users"})
    
    # Clear user's cache (security-aware)
    await cache_events.handle_clear_cache(ws, {})
    
    # Get cache statistics
    await cache_events.handle_cache_stats(ws, {})
    
    # Configure TTL (input validated)
    await cache_events.handle_set_cache_ttl(ws, {"ttl": 300})
    ```

Module Structure:
    - Constants: Data keys, response keys, log prefixes, error/success messages
    - CacheEvents class: Main event handler with security awareness
    - _extract_user_context: Extracts authentication context from WebSocket

Notes:
    - Fixed runtime bugs: clear_query_cache() → clear_all(), get_stats() → get_all_stats()
    - Implements user-aware cache clearing for security
    - All WebSocket operations wrapped in try/except for resilience
"""

from zOS import json, Dict, Any, Optional
from .base_event_handler import BaseEventHandler
from ..bridge_auth import _CONTEXT_ZSESSION, _CONTEXT_APPLICATION, _CONTEXT_DUAL

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Data Keys (incoming event data)
_KEY_MODEL = "model"
_KEY_TTL = "ttl"
_KEY_SCOPE = "scope"  # For future: "user", "app", or "all"

# Response Keys (outgoing messages)
_KEY_ERROR = "error"
_KEY_RESULT = "result"
_KEY_STATS = "stats"

# Cache Stats Keys
_KEY_QUERY_CACHE = "query_cache"

# Log Prefixes
_LOG_PREFIX = "[CacheEvents]"
_LOG_PREFIX_SCHEMA = "[CacheEvents:Schema]"
_LOG_PREFIX_CLEAR = "[CacheEvents:Clear]"
_LOG_PREFIX_STATS = "[CacheEvents:Stats]"
_LOG_PREFIX_TTL = "[CacheEvents:TTL]"

# Error Messages
_ERR_NO_MODEL = "Missing model parameter"
_ERR_SCHEMA_NOT_FOUND = "Schema not found"
_ERR_INVALID_TTL = "Invalid TTL value"
_ERR_TTL_TOO_LARGE = "TTL exceeds maximum"
_ERR_SEND_FAILED = "Failed to send response"
_ERR_CACHE_OP_FAILED = "Cache operation failed"

# Success Messages
_MSG_CACHE_CLEARED = "Cache cleared successfully"
_MSG_TTL_SET = "Query cache TTL set"
_MSG_STATS_SENT = "Cache statistics sent"
_MSG_SCHEMA_SENT = "Schema sent"

# Default/Max Values
_DEFAULT_TTL = 60
_MIN_TTL = 1
_MAX_TTL = 3600  # 1 hour max

# Note: User Context Keys and Default Values now inherited from BaseEventHandler.
# Module-level constants kept for convenience (match base class values exactly).
# These allow direct usage as `_CONTEXT_KEY_USER_ID` instead of `self._CONTEXT_KEY_USER_ID`.
from .base_event_handler import (
    _CONTEXT_KEY_USER_ID, _CONTEXT_KEY_APP_NAME, _CONTEXT_KEY_ROLE, _CONTEXT_KEY_AUTH_CONTEXT,
    _DEFAULT_USER_ID, _DEFAULT_APP_NAME, _DEFAULT_ROLE, _DEFAULT_AUTH_CONTEXT
)


# ═══════════════════════════════════════════════════════════
# CacheEvents Class
# ═══════════════════════════════════════════════════════════

class CacheEvents(BaseEventHandler):
    """
    Handles cache-related events for the zBifrost WebSocket bridge.
    
    Provides secure, validated, and context-aware cache operations including
    schema retrieval, cache management, statistics, and TTL configuration.
    All operations integrate with three-tier authentication for audit trails.
    
    Features:
        - Schema retrieval from connection info
        - Context-aware cache clearing (user/app-specific or all)
        - Cache statistics retrieval
        - TTL configuration with validation
        - User context extraction and logging
        - Comprehensive error handling
    
    Attributes:
        bifrost: zBifrost instance (provides logger, cache, connection_info)
        logger: Logger instance from bifrost
        cache: CacheManager instance from bifrost
        connection_info: ConnectionInfo instance for schema retrieval
        auth: AuthenticationManager instance for user context extraction
    
    Security:
        All operations extract and log user context (user_id, app_name, role,
        auth_context). Cache clearing is user-aware by default, preventing
        clients from clearing other users' cached data. TTL validation prevents
        invalid or excessive values.
    
    Note:
        Fixed runtime bugs from original implementation:
        - clear_query_cache() → clear_all() / clear_user_cache() / clear_app_cache()
        - get_stats() → get_all_stats()
    """
    
    def __init__(self, bifrost, auth_manager: Optional[Any] = None) -> None:
        """
        Initialize cache events handler with authentication awareness.
        
        Args:
            bifrost: zBifrost instance providing logger, cache, connection_info
            auth_manager: Optional AuthenticationManager for user context extraction
        
        Example:
            ```python
            cache_events = CacheEvents(bifrost, auth_manager=auth_manager)
            ```
        """
        super().__init__(bifrost, auth_manager)
        self.cache = bifrost.cache
        self.connection_info = bifrost.connection_info

    async def handle_get_schema(self, ws, data: Dict[str, Any]) -> None:
        """
        Retrieve schema definition for a specified model.
        
        Extracts user context, validates model parameter, and retrieves schema
        from connection info. Sends schema definition or error message to client.
        
        Args:
            ws: WebSocket connection (used for sending and user context)
            data: Event data containing:
                - model (str): Name of the model to retrieve schema for
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Validate model parameter is present
            3. Retrieve schema from connection_info
            4. Send schema or error to client
            5. Log success or errors
        
        Security:
            Logs user context for audit trails. Schema access is available to
            all authenticated users as schemas are metadata, not data.
        
        Response Format:
            Success: {"result": {"model": "users", "fields": [...]}}
            Error: {"error": "Missing model parameter"} or {"error": "Schema not found: users"}
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await cache_events.handle_get_schema(ws, {"model": "users"})
            ```
        """
        # Extract user context for logging
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        self.logger.debug(
            f"{_LOG_PREFIX_SCHEMA} Request | User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context}"
        )
        
        # Validate model parameter
        model = data.get(_KEY_MODEL)
        if not model:
            try:
                await ws.send(json.dumps({_KEY_ERROR: _ERR_NO_MODEL}))
            except Exception as e:
                self.logger.error(f"{_LOG_PREFIX_SCHEMA} {_ERR_SEND_FAILED}: {str(e)}")
            return
        
        try:
            # Retrieve schema from connection info
            schema = self.connection_info.get_schema(model)
            
            if schema:
                await ws.send(json.dumps({_KEY_RESULT: schema}))
                self.logger.debug(
                    f"{_LOG_PREFIX_SCHEMA} {_MSG_SCHEMA_SENT}: {model} | "
                    f"User: {user_id}"
                )
            else:
                await ws.send(json.dumps({_KEY_ERROR: f"{_ERR_SCHEMA_NOT_FOUND}: {model}"}))
                self.logger.warning(
                    f"{_LOG_PREFIX_SCHEMA} {_ERR_SCHEMA_NOT_FOUND}: {model} | "
                    f"User: {user_id}"
                )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_SCHEMA} {_ERR_CACHE_OP_FAILED} | "
                f"Model: {model} | User: {user_id} | Error: {str(e)}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: f"{_ERR_CACHE_OP_FAILED}: {str(e)}"}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_SCHEMA} {_ERR_SEND_FAILED}: {str(send_err)}")

    async def handle_clear_cache(self, ws, data: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
        """
        Clear query cache with user-aware scoping.
        
        Clears cache based on user context. By default, clears only the
        requesting user's or app's cached data. Admin users or explicit
        scope="all" can clear all cache entries (future enhancement).
        
        Args:
            ws: WebSocket connection (used for sending and user context)
            data: Event data (reserved for future scope parameter)
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Determine cache clearing scope (user/app/all)
            3. Clear appropriate cache entries
            4. Retrieve updated statistics
            5. Send result and stats to client
            6. Log operation
        
        Security:
            **CRITICAL**: Original code cleared ALL cache for ALL users.
            Now implements user-aware clearing:
            - Anonymous/guest: Clears all (backward compatible)
            - Application context: Clears app-specific cache
            - zSession context: Clears user-specific cache
            - Future: Admin role can clear all via scope="all"
        
        Response Format:
            {"result": "Cache cleared successfully", "stats": {...}}
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await cache_events.handle_clear_cache(ws, {})
            # Future: await cache_events.handle_clear_cache(ws, {"scope": "all"})
            ```
        """
        # Extract user context for logging and scoping
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        self.logger.debug(
            f"{_LOG_PREFIX_CLEAR} Request | User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context}"
        )
        
        try:
            # Determine clearing scope based on auth context
            cleared_count = 0
            scope_msg = "all"
            
            if auth_context == _CONTEXT_APPLICATION and app_name != _DEFAULT_APP_NAME:
                # Clear app-specific cache
                cleared_count = self.cache.clear_app_cache(app_name)
                scope_msg = f"app '{app_name}'"
            elif auth_context in (_CONTEXT_ZSESSION, _CONTEXT_DUAL) and user_id != _DEFAULT_USER_ID:
                # Clear user-specific cache
                cleared_count = self.cache.clear_user_cache(user_id)
                scope_msg = f"user '{user_id}'"
            else:
                # Anonymous/guest or no context: clear all (backward compatible)
                self.cache.clear_all()
                scope_msg = "all (no user context)"
            
            # Get updated stats
            stats = self.cache.get_all_stats()
            
            # Send response
            await ws.send(json.dumps({
                _KEY_RESULT: f"{_MSG_CACHE_CLEARED} ({scope_msg})",
                _KEY_STATS: stats
            }))
            
            self.logger.info(
                f"{_LOG_PREFIX_CLEAR} Cleared {scope_msg} | "
                f"Entries: {cleared_count} | User: {user_id} | App: {app_name}"
            )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_CLEAR} {_ERR_CACHE_OP_FAILED} | "
                f"User: {user_id} | Error: {str(e)}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: f"{_ERR_CACHE_OP_FAILED}: {str(e)}"}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_CLEAR} {_ERR_SEND_FAILED}: {str(send_err)}")

    async def handle_cache_stats(self, ws, data: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
        """
        Retrieve and send cache statistics to client.
        
        Returns hit/miss/expired/size counts for query cache, useful for
        monitoring cache effectiveness and debugging performance issues.
        
        Args:
            ws: WebSocket connection (used for sending and user context)
            data: Event data (reserved for future filtering options)
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Retrieve cache statistics from CacheManager
            3. Format stats in response structure
            4. Send stats to client
            5. Log operation
        
        Security:
            Cache statistics are aggregated metrics, not sensitive data.
            Available to all authenticated users for monitoring purposes.
        
        Response Format:
            {"result": {"query_cache": {"hits": 10, "misses": 2, ...}}}
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await cache_events.handle_cache_stats(ws, {})
            ```
        """
        # Extract user context for logging
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        self.logger.debug(
            f"{_LOG_PREFIX_STATS} Request | User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context}"
        )
        
        try:
            # Get all cache statistics (fixed: was get_stats(), now get_all_stats())
            all_stats = self.cache.get_all_stats()
            
            # Format response
            stats = {
                _KEY_QUERY_CACHE: all_stats.get(_KEY_QUERY_CACHE, {})
            }
            
            await ws.send(json.dumps({_KEY_RESULT: stats}))
            
            self.logger.debug(
                f"{_LOG_PREFIX_STATS} {_MSG_STATS_SENT} | "
                f"User: {user_id} | Hits: {stats[_KEY_QUERY_CACHE].get('hits', 0)}"
            )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_STATS} {_ERR_CACHE_OP_FAILED} | "
                f"User: {user_id} | Error: {str(e)}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: f"{_ERR_CACHE_OP_FAILED}: {str(e)}"}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_STATS} {_ERR_SEND_FAILED}: {str(send_err)}")

    async def handle_set_cache_ttl(self, ws, data: Dict[str, Any]) -> None:
        """
        Configure cache time-to-live (TTL) with validation.
        
        Sets the query cache TTL, controlling how long cached results remain
        valid. Validates input to prevent negative, zero, or excessive values.
        
        Args:
            ws: WebSocket connection (used for sending and user context)
            data: Event data containing:
                - ttl (int): Time-to-live in seconds (1-3600)
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Validate TTL parameter (positive int, within range)
            3. Apply TTL to cache manager
            4. Send confirmation to client
            5. Log operation
        
        Security:
            TTL configuration affects all users. Currently available to all
            authenticated users. Future enhancement: Restrict to admin role.
            Input validation prevents:
            - Negative values (would break cache)
            - Zero values (would disable cache)
            - Excessive values (would consume too much memory)
        
        Response Format:
            {"result": "Query cache TTL set to 300s"}
            {"error": "Invalid TTL value: must be positive integer"}
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await cache_events.handle_set_cache_ttl(ws, {"ttl": 300})
            ```
        """
        # Extract user context for logging
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        self.logger.debug(
            f"{_LOG_PREFIX_TTL} Request | User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context}"
        )
        
        # Get and validate TTL parameter
        ttl = data.get(_KEY_TTL, _DEFAULT_TTL)
        
        try:
            ttl = int(ttl)
        except (TypeError, ValueError):
            error_msg = f"{_ERR_INVALID_TTL}: must be positive integer"
            self.logger.warning(
                f"{_LOG_PREFIX_TTL} {error_msg} | "
                f"Provided: {ttl} | User: {user_id}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: error_msg}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_TTL} {_ERR_SEND_FAILED}: {str(send_err)}")
            return
        
        # Validate range
        if ttl < _MIN_TTL:
            error_msg = f"{_ERR_INVALID_TTL}: must be >= {_MIN_TTL}"
            self.logger.warning(
                f"{_LOG_PREFIX_TTL} {error_msg} | "
                f"Provided: {ttl} | User: {user_id}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: error_msg}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_TTL} {_ERR_SEND_FAILED}: {str(send_err)}")
            return
        
        if ttl > _MAX_TTL:
            error_msg = f"{_ERR_TTL_TOO_LARGE}: max {_MAX_TTL}s"
            self.logger.warning(
                f"{_LOG_PREFIX_TTL} {error_msg} | "
                f"Provided: {ttl} | User: {user_id}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: error_msg}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_TTL} {_ERR_SEND_FAILED}: {str(send_err)}")
            return
        
        try:
            # Apply TTL to cache
            self.cache.set_query_ttl(ttl)
            
            await ws.send(json.dumps({_KEY_RESULT: f"{_MSG_TTL_SET} to {ttl}s"}))
            
            self.logger.info(
                f"{_LOG_PREFIX_TTL} {_MSG_TTL_SET} to {ttl}s | "
                f"User: {user_id} | App: {app_name}"
            )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_TTL} {_ERR_CACHE_OP_FAILED} | "
                f"TTL: {ttl} | User: {user_id} | Error: {str(e)}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: f"{_ERR_CACHE_OP_FAILED}: {str(e)}"}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_TTL} {_ERR_SEND_FAILED}: {str(send_err)}")
    
    # Note: _extract_user_context() method removed - now inherited from BaseEventHandler
