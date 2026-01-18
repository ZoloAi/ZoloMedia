# zCLI/subsystems/zComm/zComm_modules/bifrost/bridge_modules/events/bridge_event_dispatch.py
"""
Command Dispatch Event Handlers for zBifrost WebSocket Bridge.

This module provides event handlers for executing zDispatch commands through
the zBifrost WebSocket bridge, with intelligent caching for read operations
and user-aware cache isolation for security.

Features:
    - zDispatch Command Execution: Routes commands to zDispatch subsystem
    - Cache-Aware Dispatch: Automatically caches read operations (list, get, search)
    - User Context Isolation: Each user/app gets isolated cache entries
    - Cache Hit/Miss Optimization: Returns cached results instantly when available
    - Broadcast Support: Sends results to all connected clients for real-time updates
    - User Context Awareness: Logs authentication context for all operations
    - Error Handling: Comprehensive exception handling for resilience

Architecture:
    DispatchEvents acts as the primary command execution layer for the Bifrost
    bridge, integrating with zDispatch for command processing and CacheManager
    for performance optimization. All operations are user-context aware, ensuring
    proper cache isolation and audit trails.

Caching Strategy:
    Read Operations (cacheable):
        - Commands starting with ^List, ^Get, ^Search
        - Commands with action="read"
        - Cached per user/app for isolation
        - TTL configurable per request or global default
        - Can be disabled with no_cache=True
    
    Write Operations (non-cacheable):
        - All other commands (create, update, delete)
        - Always executed fresh
        - Invalidate related cache entries (future enhancement)

Security Model:
    User context (user_id, app_name, role, auth_context) is extracted and logged
    for every command dispatch. Cache keys include user context to prevent
    cross-user data leakage. Three-tier authentication (zSession, application,
    dual) is fully supported.

Integration:
    - zDispatch: For command execution
    - CacheManager (bridge_cache.py): For caching with user isolation
    - AuthenticationManager (bridge_auth.py): For user context extraction
    - zSession/zAuth: For three-tier authentication context
    - Broadcast: For multi-client real-time updates

Example:
    ```python
    # Initialize with auth_manager for user context
    dispatch_events = DispatchEvents(bifrost, auth_manager=auth_manager)
    
    # Execute cached read command
    await dispatch_events.handle_dispatch(ws, {
        "zKey": "^ListUsers",
        "zHorizontal": "^ListUsers",
        "_requestId": "req-123"
    })
    
    # Execute write command (no cache)
    await dispatch_events.handle_dispatch(ws, {
        "zKey": "^CreateUser",
        "zHorizontal": "^CreateUser",
        "data": {"username": "john", "email": "john@example.com"}
    })
    
    # Override cache behavior
    await dispatch_events.handle_dispatch(ws, {
        "zKey": "^GetUser",
        "no_cache": True,  # Force fresh execution
        "cache_ttl": 300   # Or custom TTL
    })
    ```

Module Structure:
    - Constants: Data keys, response keys, command prefixes, log prefixes, messages
    - DispatchEvents class: Main event handler with caching and auth awareness
    - _is_cacheable_operation: Determines if command can be cached
    - _extract_user_context: Extracts authentication context from WebSocket
"""

from zOS import asyncio, json, Dict, Any, Optional
from .base_event_handler import BaseEventHandler

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Data Keys (incoming event data)
_KEY_ZKEY = "zKey"
_KEY_CMD = "cmd"  # Alternative to zKey
_KEY_ZHORIZONTAL = "zHorizontal"
_KEY_ACTION = "action"
_KEY_CACHE_TTL = "cache_ttl"
_KEY_NO_CACHE = "no_cache"
_KEY_REQUEST_ID = "_requestId"

# Response Keys (outgoing messages)
_KEY_RESULT = "result"
_KEY_ERROR = "error"
_KEY_CACHED = "_cached"

# Action Types
_ACTION_READ = "read"

# Command Prefixes (for cache detection)
_CMD_PREFIX_LIST = "^List"
_CMD_PREFIX_GET = "^Get"
_CMD_PREFIX_SEARCH = "^Search"

# zDispatch Context Keys
_CONTEXT_KEY_WEBSOCKET_DATA = "websocket_data"
_CONTEXT_KEY_MODE = "mode"

# Mode Values
_MODE_ZBIFROST = "zBifrost"

# Log Prefixes
_LOG_PREFIX = "[DispatchEvents]"
_LOG_PREFIX_DISPATCH = "[DispatchEvents:Dispatch]"
_LOG_PREFIX_CACHE_HIT = "[DispatchEvents:CacheHit]"
_LOG_PREFIX_CACHE_MISS = "[DispatchEvents:CacheMiss]"
_LOG_PREFIX_EXECUTE = "[DispatchEvents:Execute]"

# Error Messages
_ERR_NO_ZKEY = "Missing zKey parameter"
_ERR_DISPATCH_FAILED = "Command execution failed"
_ERR_SEND_FAILED = "Failed to send response"
_ERR_BROADCAST_FAILED = "Failed to broadcast response"

# Success Messages
_MSG_CACHE_HIT = "Cache hit"
_MSG_CACHE_MISS = "Cache miss - executing"
_MSG_COMMAND_EXECUTED = "Command executed"
_MSG_RESULT_SENT = "Result sent"

# Note: User Context Keys and Default Values now inherited from BaseEventHandler.
# Module-level constants kept for convenience (match base class values exactly).
from .base_event_handler import (
    _CONTEXT_KEY_USER_ID, _CONTEXT_KEY_APP_NAME, _CONTEXT_KEY_ROLE, _CONTEXT_KEY_AUTH_CONTEXT,
    _DEFAULT_USER_ID, _DEFAULT_APP_NAME, _DEFAULT_ROLE, _DEFAULT_AUTH_CONTEXT
)


# ═══════════════════════════════════════════════════════════
# DispatchEvents Class
# ═══════════════════════════════════════════════════════════

class DispatchEvents(BaseEventHandler):
    """
    Handles zDispatch command execution with intelligent caching and user isolation.
    
    Provides secure, cache-aware, and context-aware command dispatch operations.
    Integrates with zDispatch subsystem for command execution and CacheManager
    for performance optimization. All operations integrate with three-tier
    authentication for comprehensive audit trails and cache isolation.
    
    Features:
        - Command execution via zDispatch
        - Automatic caching for read operations
        - User-aware cache isolation
        - Cache hit/miss optimization
        - Broadcast to all connected clients
        - User context extraction and logging
        - Comprehensive error handling
        - Three-tier auth integration
    
    Attributes:
        bifrost: zBifrost instance (provides logger, cache, zcli, walker)
        logger: Logger instance from bifrost
        cache: CacheManager instance for caching
        zcli: zCLI instance for command execution
        walker: zWalker instance for data operations
        auth: AuthenticationManager instance for user context extraction
    
    Caching Behavior:
        Read operations (^List*, ^Get*, ^Search*, action="read") are automatically
        cached per user/app for isolation. Write operations always execute fresh.
        Cache can be bypassed with no_cache=True or custom TTL with cache_ttl.
    
    Security:
        All operations extract and log user context (user_id, app_name, role,
        auth_context) for audit trails. Cache keys include user context to prevent
        cross-user data leakage. Critical for multi-tenant security.
    """
    
    def __init__(self, bifrost, auth_manager: Optional[Any] = None) -> None:
        """
        Initialize dispatch events handler with authentication awareness.
        
        Args:
            bifrost: zBifrost instance providing logger, cache, zcli, walker
            auth_manager: Optional AuthenticationManager for user context extraction
        
        Example:
            ```python
            dispatch_events = DispatchEvents(bifrost, auth_manager=auth_manager)
            ```
        """
        super().__init__(bifrost, auth_manager)
        self.cache = bifrost.cache
        self.zcli = bifrost.zcli
        self.walker = bifrost.walker
    
    async def handle_dispatch(self, ws, data: Dict[str, Any]) -> None:
        """
        Execute zDispatch command with cache-aware routing.
        
        This is the primary command execution endpoint for the Bifrost bridge.
        It implements intelligent caching for read operations, user-aware cache
        isolation, and broadcast support for real-time multi-client updates.
        
        Args:
            ws: WebSocket connection (used for sending, broadcast, and user context)
            data: Event data containing:
                - zKey or cmd (str): Command to execute (required)
                - zHorizontal (str, optional): Horizontal context, defaults to zKey
                - action (str, optional): "read" for cacheable operations
                - cache_ttl (int, optional): Custom cache TTL in seconds
                - no_cache (bool, optional): Bypass cache even for read operations
                - _requestId (str, optional): Request ID for response correlation
                - ... (other command-specific parameters)
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Validate zKey parameter
            3. Determine if operation is cacheable
            4. Check cache for read operations (unless no_cache=True)
            5. Execute command via zDispatch if cache miss or non-cacheable
            6. Cache result if cacheable
            7. Send response to requesting client
            8. Broadcast result to all connected clients
            9. Log success or errors
        
        Security:
            Logs user context for all commands. Cache keys include user context
            to prevent cross-user data leakage. Critical for multi-tenant security.
        
        Caching:
            Read operations automatically cached per user/app with configurable TTL.
            Cache can be bypassed with no_cache=True or custom TTL with cache_ttl.
            Write operations always execute fresh and bypass cache.
        
        Response Format (cache hit):
            {"result": {...}, "_cached": true, "_requestId": "req-123"}
        
        Response Format (fresh execution):
            {"result": {...}, "_requestId": "req-123"}
        
        Response Format (error):
            {"error": "Command execution failed: ...", "_requestId": "req-123"}
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await dispatch_events.handle_dispatch(ws, {
                "zKey": "^ListUsers",
                "zHorizontal": "^ListUsers",
                "_requestId": "req-123"
            })
            ```
        """
        # Extract user context for logging and cache isolation
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        # Get and validate zKey
        zKey = data.get(_KEY_ZKEY) or data.get(_KEY_CMD)
        zHorizontal = data.get(_KEY_ZHORIZONTAL) or zKey
        
        if not zKey:
            self.logger.warning(
                f"{_LOG_PREFIX_DISPATCH} {_ERR_NO_ZKEY} | "
                f"User: {user_id} | App: {app_name}"
            )
            try:
                await ws.send(json.dumps({_KEY_ERROR: _ERR_NO_ZKEY}))
            except Exception as send_err:
                self.logger.error(f"{_LOG_PREFIX_DISPATCH} {_ERR_SEND_FAILED}: {str(send_err)}")
            return
        
        self.logger.debug(
            f"{_LOG_PREFIX_DISPATCH} Request | User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context} | Command: {zKey}"
        )
        
        # Check cache behavior
        is_cacheable = self._is_cacheable_operation(data, zKey)
        cache_ttl = data.get(_KEY_CACHE_TTL, None)
        disable_cache = data.get(_KEY_NO_CACHE, False)
        
        # Try cache for read operations
        if is_cacheable and not disable_cache:
            cache_key = self.cache.generate_cache_key(data, user_context)
            cached_result = self.cache.get_query(cache_key)
            
            if cached_result is not None:
                # Cache hit!
                self.logger.debug(
                    f"{_LOG_PREFIX_CACHE_HIT} {_MSG_CACHE_HIT} | "
                    f"Command: {zKey} | User: {user_id}"
                )
                
                response = {_KEY_RESULT: cached_result, _KEY_CACHED: True}
                if _KEY_REQUEST_ID in data:
                    response[_KEY_REQUEST_ID] = data[_KEY_REQUEST_ID]
                
                payload = json.dumps(response)
                
                try:
                    await ws.send(payload)
                    await self.bifrost.broadcast(payload, sender=ws)
                    self.logger.debug(
                        f"{_LOG_PREFIX_CACHE_HIT} {_MSG_RESULT_SENT} | "
                        f"Command: {zKey} | User: {user_id}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"{_LOG_PREFIX_CACHE_HIT} Send/broadcast failed | "
                        f"Command: {zKey} | User: {user_id} | Error: {str(e)}"
                    )
                return
        
        # Cache miss or not cacheable - execute command
        if is_cacheable and not disable_cache:
            self.logger.debug(
                f"{_LOG_PREFIX_CACHE_MISS} {_MSG_CACHE_MISS} | "
                f"Command: {zKey} | User: {user_id}"
            )
        else:
            self.logger.debug(
                f"{_LOG_PREFIX_EXECUTE} Non-cacheable command | "
                f"Command: {zKey} | User: {user_id}"
            )
        
        try:
            # Execute via zDispatch
            from zOS.L2_Core.e_zDispatch import handle_zDispatch
            
            context = {
                _CONTEXT_KEY_WEBSOCKET_DATA: data,
                _CONTEXT_KEY_MODE: _MODE_ZBIFROST
            }
            
            result = await asyncio.to_thread(
                handle_zDispatch, zKey, zHorizontal,
                zcli=self.zcli, walker=self.walker, context=context
            )
            
            # Check if result contains buffered events (new zBifrost capture pattern)
            actual_result = result
            buffered_events = None
            
            if isinstance(result, dict) and 'events' in result and 'result' in result:
                # New structure: {result: ..., events: [...]}
                actual_result = result['result']
                buffered_events = result['events']
                self.logger.debug(
                    f"{_LOG_PREFIX_EXECUTE} Captured {len(buffered_events)} display events | "
                    f"Command: {zKey} | User: {user_id}"
                )
            
            # Cache result if cacheable (cache only the actual result, not events)
            if is_cacheable and not disable_cache:
                cache_key = self.cache.generate_cache_key(data, user_context)
                self.cache.cache_query(cache_key, actual_result, ttl=cache_ttl, user_context=user_context)
                self.logger.debug(
                    f"{_LOG_PREFIX_EXECUTE} Result cached | "
                    f"Command: {zKey} | User: {user_id}"
                )
            
            # Build response
            response = {_KEY_RESULT: actual_result}
            if _KEY_REQUEST_ID in data:
                response[_KEY_REQUEST_ID] = data[_KEY_REQUEST_ID]
            
            payload = json.dumps(response)
            
            self.logger.debug(
                f"{_LOG_PREFIX_EXECUTE} {_MSG_COMMAND_EXECUTED} | "
                f"Command: {zKey} | User: {user_id}"
            )
        
        except Exception as exc:
            self.logger.error(
                f"{_LOG_PREFIX_EXECUTE} {_ERR_DISPATCH_FAILED} | "
                f"Command: {zKey} | User: {user_id} | Error: {str(exc)}"
            )
            response = {_KEY_ERROR: f"{_ERR_DISPATCH_FAILED}: {str(exc)}"}
            if _KEY_REQUEST_ID in data:
                response[_KEY_REQUEST_ID] = data[_KEY_REQUEST_ID]
            payload = json.dumps(response)
        
        # Send result back and broadcast
        try:
            await ws.send(payload)
        except Exception as send_err:
            self.logger.error(
                f"{_LOG_PREFIX_EXECUTE} {_ERR_SEND_FAILED} | "
                f"Command: {zKey} | User: {user_id} | Error: {str(send_err)}"
            )
        
        try:
            await self.bifrost.broadcast(payload, sender=ws)
        except Exception as broadcast_err:
            self.logger.error(
                f"{_LOG_PREFIX_EXECUTE} {_ERR_BROADCAST_FAILED} | "
                f"Command: {zKey} | User: {user_id} | Error: {str(broadcast_err)}"
            )
        
        # Send buffered display events if any (new zBifrost capture pattern)
        if 'buffered_events' in locals() and buffered_events:
            for event in buffered_events:
                try:
                    event_payload = json.dumps({
                        'event': 'display',
                        'data': event
                    })
                    await ws.send(event_payload)
                    self.logger.debug(
                        f"{_LOG_PREFIX_EXECUTE} Sent display event: {event.get('display_event')} | "
                        f"Command: {zKey}"
                    )
                except Exception as event_err:
                    self.logger.error(
                        f"{_LOG_PREFIX_EXECUTE} Failed to send display event | "
                        f"Command: {zKey} | Error: {str(event_err)}"
                    )
    
    def _is_cacheable_operation(self, data: Dict[str, Any], zKey: str) -> bool:
        """
        Determine if command is cacheable (read-only operation).
        
        Read operations are automatically cached for performance. Write operations
        (create, update, delete) always execute fresh to ensure data consistency.
        
        Args:
            data: Message data with potential action field
            zKey: Command key
        
        Returns:
            bool: True if operation can be cached, False otherwise
        
        Cacheable Operations:
            - action="read"
            - Commands starting with ^List
            - Commands starting with ^Get
            - Commands starting with ^Search
        
        Example:
            ```python
            is_cacheable = self._is_cacheable_operation(data, "^ListUsers")
            # Returns: True
            
            is_cacheable = self._is_cacheable_operation(data, "^CreateUser")
            # Returns: False
            ```
        """
        return (
            data.get(_KEY_ACTION) == _ACTION_READ or
            zKey.startswith(_CMD_PREFIX_LIST) or
            zKey.startswith(_CMD_PREFIX_GET) or
            zKey.startswith(_CMD_PREFIX_SEARCH)
        )
    
    # Note: _extract_user_context() method removed - now inherited from BaseEventHandler
