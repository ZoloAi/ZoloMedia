# zCLI/L3_Abstraction/o_zBifrost/zBifrost_modules/bifrost/server/modules/events/base_event_handler.py
"""
Base Event Handler for zBifrost WebSocket Bridge.

This module provides a base class for all event handlers, eliminating code
duplication by centralizing common functionality such as user context extraction,
shared constants, and authentication integration.

DRY Improvement:
    Extracted from 4 event handler modules where identical code was duplicated:
    - bridge_event_cache.py (7 usages)
    - bridge_event_client.py (6 usages)
    - bridge_event_dispatch.py (4 usages)
    - bridge_event_discovery.py (5 usages)
    Total: 22 instances of user context extraction consolidated into 1 method.

Architecture:
    All event handlers inherit from BaseEventHandler and gain:
    - User context extraction (_extract_user_context)
    - Shared authentication constants
    - Consistent logging context patterns
    - Future: Additional shared utilities as patterns emerge

Usage:
    ```python
    from .base_event_handler import BaseEventHandler
    
    class MyEventHandler(BaseEventHandler):
        def __init__(self, bifrost, auth_manager=None):
            super().__init__(bifrost, auth_manager)
            # Your custom initialization
        
        async def handle_my_event(self, ws, data):
            # Extract user context using inherited method
            user_context = self._extract_user_context(ws)
            user_id = user_context[self._CONTEXT_KEY_USER_ID]
            # ... handle event
    ```
"""

from zOS import Dict, Any, Optional, Callable

# Import authentication context constants from bridge_auth (shared auth constants)
try:
    from ..bridge_auth import _CONTEXT_ZSESSION, _CONTEXT_APPLICATION, _CONTEXT_DUAL, _CONTEXT_NONE
except ImportError:
    # Fallback if relative import fails (shouldn't happen in normal usage)
    _CONTEXT_ZSESSION = "zSession"
    _CONTEXT_APPLICATION = "application"
    _CONTEXT_DUAL = "dual"
    _CONTEXT_NONE = "none"

# ═══════════════════════════════════════════════════════════
# Shared Constants - User Context
# ═══════════════════════════════════════════════════════════

# User Context Keys (for logging and cache isolation)
_CONTEXT_KEY_USER_ID = "user_id"
_CONTEXT_KEY_APP_NAME = "app_name"
_CONTEXT_KEY_ROLE = "role"
_CONTEXT_KEY_AUTH_CONTEXT = "auth_context"

# Default Values (safe fallbacks when auth info unavailable)
_DEFAULT_USER_ID = "anonymous"
_DEFAULT_APP_NAME = "unknown"
_DEFAULT_ROLE = "guest"
_DEFAULT_AUTH_CONTEXT = "none"


# ═══════════════════════════════════════════════════════════
# BaseEventHandler Class
# ═══════════════════════════════════════════════════════════

class BaseEventHandler:
    """
    Base class for all zBifrost event handlers.
    
    Provides shared functionality for event handlers including user context
    extraction, authentication integration, and common constants. All event
    handlers should inherit from this class to maintain consistency and
    eliminate code duplication.
    
    Attributes:
        bifrost: zBifrost instance (provides logger, zcli, cache, etc.)
        logger: Logger instance from bifrost
        auth: AuthenticationManager instance for user context extraction
        _CONTEXT_KEY_USER_ID: Constant for user_id key
        _CONTEXT_KEY_APP_NAME: Constant for app_name key
        _CONTEXT_KEY_ROLE: Constant for role key
        _CONTEXT_KEY_AUTH_CONTEXT: Constant for auth_context key
        _DEFAULT_USER_ID: Default user ID when not authenticated
        _DEFAULT_APP_NAME: Default app name when not available
        _DEFAULT_ROLE: Default role when not assigned
        _DEFAULT_AUTH_CONTEXT: Default auth context when not authenticated
    
    Methods:
        _extract_user_context(ws): Extract authentication context from WebSocket
        _safe_send(ws, payload, context, error_prefix): Safe WebSocket send with error handling
        _send_and_broadcast(ws, payload, broadcast_func, context, error_prefix): Send + broadcast pattern
        _log_error_with_context(error_prefix, error_message, context, exception): Structured error logging
    
    Design:
        This base class follows the DRY principle by extracting common patterns
        identified in the Step 4.4.3 DRY Audit. It provides a foundation for
        all event handlers while maintaining flexibility for handler-specific
        logic in subclasses.
    """
    
    # Expose constants as class attributes for easy access in subclasses
    _CONTEXT_KEY_USER_ID = _CONTEXT_KEY_USER_ID
    _CONTEXT_KEY_APP_NAME = _CONTEXT_KEY_APP_NAME
    _CONTEXT_KEY_ROLE = _CONTEXT_KEY_ROLE
    _CONTEXT_KEY_AUTH_CONTEXT = _CONTEXT_KEY_AUTH_CONTEXT
    _DEFAULT_USER_ID = _DEFAULT_USER_ID
    _DEFAULT_APP_NAME = _DEFAULT_APP_NAME
    _DEFAULT_ROLE = _DEFAULT_ROLE
    _DEFAULT_AUTH_CONTEXT = _DEFAULT_AUTH_CONTEXT
    
    def __init__(self, bifrost: Any, auth_manager: Optional[Any] = None) -> None:
        """
        Initialize base event handler.
        
        Args:
            bifrost: zBifrost instance providing logger, zcli, and other subsystems
            auth_manager: Optional AuthenticationManager for user context extraction
        
        Note:
            Subclasses should call super().__init__() in their constructors to
            ensure proper initialization of shared attributes.
        
        Example:
            ```python
            class CacheEvents(BaseEventHandler):
                def __init__(self, bifrost, auth_manager=None):
                    super().__init__(bifrost, auth_manager)
                    self.cache = bifrost.cache  # Additional initialization
            ```
        """
        self.bifrost = bifrost
        self.logger = bifrost.logger
        self.auth = auth_manager
    
    def _extract_user_context(self, ws: Any) -> Dict[str, str]:
        """
        Extract user authentication context from WebSocket connection.
        
        Retrieves user context from AuthenticationManager for logging and
        cache isolation. Handles zSession, application, and dual contexts,
        preferring application context when both are present (dual mode).
        
        This method is the core DRY improvement - it consolidates 22 identical
        implementations across 4 event handler modules into a single method.
        
        Args:
            ws: WebSocket connection
        
        Returns:
            Dict containing:
                - user_id: User identifier (username or app user ID)
                - app_name: Application name (for app context)
                - role: User role (admin, user, guest, etc.)
                - auth_context: Authentication type (zSession, application, dual, none)
        
        Security:
            Returns safe defaults (anonymous/unknown/guest/none) if no auth
            info is available, ensuring the system remains operational.
        
        Context Priority (Dual Mode):
            When both zSession and application auth are present (dual mode),
            this method prefers application context for consistency with
            application-scoped operations.
        
        Example:
            ```python
            # In an event handler
            context = self._extract_user_context(ws)
            user_id = context[self._CONTEXT_KEY_USER_ID]
            app_name = context[self._CONTEXT_KEY_APP_NAME]
            
            self.logger.info(f"User: {user_id} | App: {app_name}")
            ```
        
        Returns:
            Dict with keys: user_id, app_name, role, auth_context
        """
        # No auth manager available - return safe defaults
        if not self.auth:
            return {
                self._CONTEXT_KEY_USER_ID: self._DEFAULT_USER_ID,
                self._CONTEXT_KEY_APP_NAME: self._DEFAULT_APP_NAME,
                self._CONTEXT_KEY_ROLE: self._DEFAULT_ROLE,
                self._CONTEXT_KEY_AUTH_CONTEXT: self._DEFAULT_AUTH_CONTEXT
            }
        
        # Get auth info from auth manager
        auth_info = self.auth.get_client_info(ws)
        if not auth_info:
            return {
                self._CONTEXT_KEY_USER_ID: self._DEFAULT_USER_ID,
                self._CONTEXT_KEY_APP_NAME: self._DEFAULT_APP_NAME,
                self._CONTEXT_KEY_ROLE: self._DEFAULT_ROLE,
                self._CONTEXT_KEY_AUTH_CONTEXT: self._DEFAULT_AUTH_CONTEXT
            }
        
        context = auth_info.get("context", self._DEFAULT_AUTH_CONTEXT)
        
        # Handle dual authentication (both zSession and application)
        # Prefer application context for consistency
        if context == _CONTEXT_DUAL:
            app_user = auth_info.get("app_user", {})
            return {
                self._CONTEXT_KEY_USER_ID: app_user.get("username", app_user.get("id", self._DEFAULT_USER_ID)),
                self._CONTEXT_KEY_APP_NAME: app_user.get("app_name", self._DEFAULT_APP_NAME),
                self._CONTEXT_KEY_ROLE: app_user.get("role", self._DEFAULT_ROLE),
                self._CONTEXT_KEY_AUTH_CONTEXT: _CONTEXT_DUAL
            }
        
        # Handle application-only authentication
        elif context == _CONTEXT_APPLICATION:
            app_user = auth_info.get("app_user", {})
            return {
                self._CONTEXT_KEY_USER_ID: app_user.get("username", app_user.get("id", self._DEFAULT_USER_ID)),
                self._CONTEXT_KEY_APP_NAME: app_user.get("app_name", self._DEFAULT_APP_NAME),
                self._CONTEXT_KEY_ROLE: app_user.get("role", self._DEFAULT_ROLE),
                self._CONTEXT_KEY_AUTH_CONTEXT: _CONTEXT_APPLICATION
            }
        
        # Handle zSession-only authentication
        elif context == _CONTEXT_ZSESSION:
            zsession_user = auth_info.get("zsession_user", {})
            return {
                self._CONTEXT_KEY_USER_ID: zsession_user.get("username", self._DEFAULT_USER_ID),
                self._CONTEXT_KEY_APP_NAME: "zCLI",
                self._CONTEXT_KEY_ROLE: zsession_user.get("role", self._DEFAULT_ROLE),
                self._CONTEXT_KEY_AUTH_CONTEXT: _CONTEXT_ZSESSION
            }
        
        # Unknown or unauthenticated context
        else:
            return {
                self._CONTEXT_KEY_USER_ID: self._DEFAULT_USER_ID,
                self._CONTEXT_KEY_APP_NAME: self._DEFAULT_APP_NAME,
                self._CONTEXT_KEY_ROLE: self._DEFAULT_ROLE,
                self._CONTEXT_KEY_AUTH_CONTEXT: self._DEFAULT_AUTH_CONTEXT
            }
    
    async def _safe_send(
        self,
        ws: Any,
        payload: str,
        context: str = "",
        error_prefix: str = "[BaseEventHandler]"
    ) -> bool:
        """
        Safely send payload to WebSocket with automatic error handling.
        
        This method implements Pattern 2 from the DRY audit - WebSocket send
        with consistent error handling. It eliminates the need to wrap every
        ws.send() call in try/except blocks.
        
        Args:
            ws: WebSocket connection
            payload: JSON string or message to send
            context: Context information for error logging (e.g., "Command: ^ListUsers | User: admin")
            error_prefix: Log prefix for error messages
        
        Returns:
            bool: True if send succeeded, False if failed
        
        Example:
            ```python
            # Instead of:
            try:
                await ws.send(payload)
            except Exception as send_err:
                self.logger.error(f"{LOG_PREFIX} Send failed | {context} | Error: {str(send_err)}")
            
            # Use:
            await self._safe_send(ws, payload, context="Command: ^ListUsers", error_prefix=LOG_PREFIX)
            ```
        
        DRY Improvement:
            Eliminates 66 instances of identical try/except blocks around ws.send()
        """
        try:
            await ws.send(payload)
            return True
        except Exception as send_err:
            error_msg = f"{error_prefix} Failed to send response"
            if context:
                error_msg += f" | {context}"
            error_msg += f" | Error: {str(send_err)}"
            self.logger.error(error_msg)
            return False
    
    async def _send_and_broadcast(
        self,
        ws: Any,
        payload: str,
        broadcast_func: Callable,
        context: str = "",
        error_prefix: str = "[BaseEventHandler]"
    ) -> tuple[bool, bool]:
        """
        Send payload to originating client and broadcast to all others.
        
        This method implements Pattern 5 from the DRY audit - the common pattern
        of sending a response to the originating WebSocket and broadcasting to
        all other connected clients. Both operations have independent error handling.
        
        Args:
            ws: WebSocket connection (originating client)
            payload: JSON string or message to send
            broadcast_func: Async function to broadcast (e.g., self.bifrost.broadcast)
            context: Context information for error logging
            error_prefix: Log prefix for error messages
        
        Returns:
            tuple[bool, bool]: (send_success, broadcast_success)
        
        Example:
            ```python
            # Instead of:
            try:
                await ws.send(payload)
            except Exception as send_err:
                self.logger.error(f"{LOG_PREFIX} Send failed | Error: {str(send_err)}")
            
            try:
                await self.bifrost.broadcast(payload, sender=ws)
            except Exception as broadcast_err:
                self.logger.error(f"{LOG_PREFIX} Broadcast failed | Error: {str(broadcast_err)}")
            
            # Use:
            await self._send_and_broadcast(
                ws, payload, self.bifrost.broadcast,
                context="Command: ^ListUsers | User: admin",
                error_prefix=LOG_PREFIX
            )
            ```
        
        DRY Improvement:
            Eliminates ~15 instances of send + broadcast with dual error handling
        """
        # Send to originating client
        send_success = await self._safe_send(ws, payload, context, error_prefix)
        
        # Broadcast to all other clients
        try:
            await broadcast_func(payload, sender=ws)
            broadcast_success = True
        except Exception as broadcast_err:
            error_msg = f"{error_prefix} Failed to broadcast"
            if context:
                error_msg += f" | {context}"
            error_msg += f" | Error: {str(broadcast_err)}"
            self.logger.error(error_msg)
            broadcast_success = False
        
        return send_success, broadcast_success
    
    def _log_error_with_context(
        self,
        error_prefix: str,
        error_message: str,
        context: Dict[str, Any],
        exception: Optional[Exception] = None
    ) -> None:
        """
        Log error with structured context information.
        
        This method implements Pattern 4 from the DRY audit - structured exception
        logging with consistent formatting. It provides a clean way to log errors
        with contextual information in a standardized format.
        
        Args:
            error_prefix: Log prefix (e.g., "[CacheEvents:Clear]")
            error_message: Main error message (e.g., "Cache operation failed")
            context: Dictionary of context key-value pairs (e.g., {"Command": "^ListUsers", "User": "admin"})
            exception: Optional exception object to include error details
        
        Example:
            ```python
            # Instead of:
            self.logger.error(
                f"{LOG_PREFIX} {ERR_MESSAGE} | "
                f"Command: {zKey} | User: {user_id} | Error: {str(exc)}"
            )
            
            # Use:
            self._log_error_with_context(
                error_prefix=LOG_PREFIX,
                error_message=ERR_MESSAGE,
                context={"Command": zKey, "User": user_id},
                exception=exc
            )
            ```
        
        Format:
            {error_prefix} {error_message} | Key1: Value1 | Key2: Value2 | Error: exception
        
        DRY Improvement:
            Eliminates 27 instances of manual string formatting for error logs
        """
        log_parts = [error_prefix, error_message]
        
        # Add context key-value pairs
        for key, value in context.items():
            log_parts.append(f"{key}: {value}")
        
        # Add exception details if provided
        if exception:
            log_parts.append(f"Error: {str(exception)}")
        
        # Join with separator
        log_message = " | ".join(log_parts)
        self.logger.error(log_message)