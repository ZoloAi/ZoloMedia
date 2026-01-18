# zCLI/subsystems/zBifrost/zBifrost_modules/bifrost/server/modules/bridge_auth.py
"""
Authentication Module - Three-Tier WebSocket Authentication (v1.5.6+)

Orchestrates advanced WebSocket authentication using zComm primitives + zAuth integration.

Layer 0 (zComm): Basic WebSocket auth primitives (origin, token validation, connection limits)
Layer 2 (zBifrost): Three-tier authentication orchestration:
    - Layer 1 (zSession): Internal zCLI/Zolo users (no token required)
    - Layer 2 (Application): External app users with configurable user models
    - Layer 3 (Dual): Both zSession and application authenticated simultaneously

Features:
- Multi-app simultaneous authentication support (Scenario B)
- Concurrent user authentication (Scenario A - already working)
- Delegates basic auth to zComm (origin validation, token extraction)
- Adds three-tier authentication on top of zComm primitives
- Integrates with zAuth for application user validation
- Context-aware authentication results

Architecture:
    zComm (Layer 0) → Provides basic WebSocket security primitives
    zAuth (Layer 1) → Provides three-tier authentication logic
    zBifrost (Layer 2) → Orchestrates both for Walker-based WebSocket communication
"""

from zOS import Dict, Optional, Any
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_AUTHENTICATED,
    ZAUTH_KEY_ID,
    ZAUTH_KEY_USERNAME,
    ZAUTH_KEY_ROLE,
    ZAUTH_KEY_API_KEY
)

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Logging
_LOG_PREFIX = "[AuthManager]"
_LOG_AUTH_SUCCESS = "Authenticated"
_LOG_AUTH_FAIL = "Authentication failed"
_LOG_ZSESSION_AUTH = "Internal zCLI connection authenticated via session"
_LOG_APP_AUTH = "Application user authenticated"
_LOG_DUAL_AUTH = "Dual authentication (zSession + Application)"
_LOG_BLOCK = "BLOCK"
_LOG_WARN = "WARN"
_LOG_OK = "OK"
_LOG_ERROR = "ERROR"

# WebSocket Close Codes
_CLOSE_AUTH_REQUIRED = 1008  # Policy Violation
_CLOSE_INVALID_TOKEN = 1008  # Policy Violation
_CLOSE_AUTH_ERROR = 1011     # Internal Error
_CLOSE_INVALID_ORIGIN = 1008 # Policy Violation

# Close Reasons
_REASON_AUTH_REQUIRED = "Authentication required"
_REASON_INVALID_TOKEN = "Invalid token"
_REASON_AUTH_ERROR = "Authentication error"
_REASON_CONFIG_ERROR = "Server configuration error"
_REASON_INVALID_ORIGIN = "Invalid origin"

# Authentication Context Values (Three-Tier Authentication)
_CONTEXT_ZSESSION = "zSession"      # Layer 1: Internal zCLI users
_CONTEXT_APPLICATION = "application"  # Layer 2: External app users
_CONTEXT_DUAL = "dual"               # Layer 3: Both zSession + Application
_CONTEXT_NONE = "none"               # No authentication
_CONTEXT_GUEST = "guest"             # Guest access
_USER_ANONYMOUS = "anonymous"
_ROLE_GUEST = "guest"

# Default Auth Config
_DEFAULT_USER_MODEL = "@.zCloud.schemas.schema.zIndex.zUsers"
_DEFAULT_ID_FIELD = "id"
_DEFAULT_USERNAME_FIELD = "username"
_DEFAULT_ROLE_FIELD = "role"
_DEFAULT_API_KEY_FIELD = "api_key"

# Query Parameters
_QUERY_PARAM_TOKEN = "token"
_QUERY_PARAM_API_KEY = "api_key"
_QUERY_PARAM_APP_NAME = "app_name"  # For multi-app support

# Header Names
_HEADER_ORIGIN = "Origin"
_HEADER_AUTHORIZATION = "Authorization"
_AUTH_BEARER_PREFIX = "Bearer "

# Data Action
_DATA_ACTION_READ = "read"

# Messages
_MSG_NO_WALKER = "Cannot validate: No walker available"
_MSG_NO_ORIGIN = "Connection without Origin header"
_MSG_NO_TOKEN = "No authentication token provided"
_MSG_INVALID_TOKEN = "Invalid authentication token"


# ═══════════════════════════════════════════════════════════
# Authentication Manager Class
# ═══════════════════════════════════════════════════════════

class AuthenticationManager:
    """
    Manages WebSocket client authentication with three-tier support.
    
    Supports three authentication layers:
    1. zSession Auth (Layer 1): Internal zCLI users (no token required)
    2. Application Auth (Layer 2): External app users (token-based, configurable)
    3. Dual Auth (Layer 3): Both zSession and application simultaneously
    
    Multi-App Support (Scenario B):
        - Multiple apps can be authenticated per user simultaneously
        - Each WebSocket can connect with different app identity
        - app_name in query params specifies which app to authenticate to
    
    Concurrent Users (Scenario A):
        - Multiple WebSocket connections = multiple authenticated users
        - Each connection tracked independently in self.authenticated_clients
        - Already working - no special implementation needed
    
    Features:
        - Origin validation (CSRF protection)
        - Token extraction (query params or headers)
        - Configurable user models per application
        - Context-aware authentication results
    
    Args:
        logger: Logger instance for auth events
        require_auth: If True, require authentication for all connections
        allowed_origins: List of allowed Origin header values (CORS)
        app_auth_config: Optional dict for application auth configuration:
            {
                "user_model": "@.store_users.users",
                "id_field": "id",
                "username_field": "email",
                "role_field": "role",
                "api_key_field": "api_key"
            }
    """
    
    def __init__(
        self,
        logger: Any,
        require_auth: bool = True,
        allowed_origins: Optional[list] = None,
        app_auth_config: Optional[Dict[str, str]] = None
    ):
        """Initialize authentication manager with three-tier support.
        
        Args:
            logger: Logger instance (required)
            require_auth: Whether to require authentication (default: True)
            allowed_origins: List of allowed origin headers for CORS
            app_auth_config: Configuration for application-level authentication
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger is required for AuthenticationManager")
        
        self.logger = logger
        self.require_auth = require_auth
        self.allowed_origins = allowed_origins or []
        
        # Application auth configuration
        self.app_auth_config = app_auth_config or {
            "user_model": _DEFAULT_USER_MODEL,
            "id_field": _DEFAULT_ID_FIELD,
            "username_field": _DEFAULT_USERNAME_FIELD,
            "role_field": _DEFAULT_ROLE_FIELD,
            "api_key_field": _DEFAULT_API_KEY_FIELD
        }
        
        # Tracks authenticated clients: ws -> auth_info
        # Scenario A (Concurrent Users): Each WebSocket = independent user
        self.authenticated_clients: Dict[Any, Dict[str, Any]] = {}
    
    # ═══════════════════════════════════════════════════════════
    # Public Authentication Methods
    # ═══════════════════════════════════════════════════════════
    
    async def authenticate_client(
        self,
        ws: Any,
        walker: Any,
        auth_config: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate WebSocket client with three-tier authentication support.
        
        Architecture:
            1. Delegate basic auth to zComm (origin validation, token extraction)
            2. Add three-tier zBifrost/zAuth logic (zSession, Application, Dual)
        
        Authentication Flow:
            0. Basic Auth (zComm Layer 0): Origin validation + token extraction
               - Delegates to walker.zcli.comm.websocket.auth primitives
            
            1. Check zSession (Layer 1): Internal zCLI connection?
               - If walker.zcli.session["zAuth"]["zSession"]["authenticated"]:
                 Return zSession user (no token required)
            
            2. Check Application Auth (Layer 2): External user with token?
               - Extract token via zComm primitive
               - Extract app_name from query params (for multi-app support)
               - Call walker.zcli.auth.authenticate_app_user(app_name, token, config)
               - Return application user
            
            3. Dual-Auth Detection (Layer 3): Both authenticated?
               - If zSession + token both present:
                 Authenticate application user and detect dual mode
                 Return both user contexts
        
        Args:
            ws: WebSocket connection
            walker: zCLI walker instance (provides access to zcli, session, auth, data)
            auth_config: Optional per-request auth config (overrides instance config)
        
        Returns:
            dict: Authentication result with context info:
                {
                    "authenticated": True,
                    "context": "zSession" | "application" | "dual",
                    "zSession": {...} or None,
                    "application": {...} or None,
                    "app_name": str (if application context),
                    "dual_mode": bool
                }
            None: If authentication failed (connection will be closed)
        
        Examples:
            # Scenario 1: Internal zCLI connection (no token)
            → Returns: {"context": "zSession", "zSession": {...}}
            
            # Scenario 2: External app user (with token)
            → Returns: {"context": "application", "application": {...}}
            
            # Scenario 3: zCLI user connecting with app token (dual-auth)
            → Returns: {"context": "dual", "zSession": {...}, "application": {...}}
        """
        if not self.require_auth:
            self.logger.debug(f"{_LOG_PREFIX} Authentication disabled by config")
            return {
                "authenticated": True,
                "context": _CONTEXT_GUEST,
                "user": _USER_ANONYMOUS,
                "role": _ROLE_GUEST
            }
        
        # Use provided auth config or instance default
        effective_config = auth_config or self.app_auth_config
        
        # ═══════════════════════════════════════════════════════════
        # Step 0: Basic WebSocket Auth (Delegate to zComm Layer 0)
        # ═══════════════════════════════════════════════════════════
        comm_auth = walker.zcli.comm.websocket.auth
        
        # Origin validation (CORS/CSRF protection)
        if not comm_auth.validate_origin(ws):
            self.logger.warning(f"{_LOG_PREFIX} [{_LOG_BLOCK}] {_REASON_INVALID_ORIGIN}")
            await ws.close(code=_CLOSE_INVALID_ORIGIN, reason=_REASON_INVALID_ORIGIN)
            return None
        
        # Extract token using zComm primitive
        token = comm_auth.extract_token(ws)
        
        # Extract app_name from query params (for multi-app support)
        path = self._get_ws_path(ws)
        app_name = self._extract_app_name(path)
        
        # ═══════════════════════════════════════════════════════════
        # Step 1: Check zSession authentication (Layer 1 - Internal zCLI)
        # ═══════════════════════════════════════════════════════════
        zsession_auth = None
        if walker and hasattr(walker, 'zcli') and walker.zcli.session:
            zsession = walker.zcli.session.get("zAuth", {}).get(ZAUTH_KEY_ZSESSION, {})
            if zsession.get(ZAUTH_KEY_AUTHENTICATED, False):
                zsession_auth = {
                    ZAUTH_KEY_AUTHENTICATED: True,
                    ZAUTH_KEY_ID: zsession.get(ZAUTH_KEY_ID),
                    ZAUTH_KEY_USERNAME: zsession.get(ZAUTH_KEY_USERNAME),
                    ZAUTH_KEY_ROLE: zsession.get(ZAUTH_KEY_ROLE),
                    ZAUTH_KEY_API_KEY: zsession.get(ZAUTH_KEY_API_KEY)
                }
                self.logger.info(
                    f"{_LOG_PREFIX} [{_LOG_OK}] {_LOG_ZSESSION_AUTH}: "
                    f"{zsession_auth[ZAUTH_KEY_USERNAME]} (role={zsession_auth[ZAUTH_KEY_ROLE]})"
                )
        
        # ═══════════════════════════════════════════════════════════
        # Step 2: Check application authentication (Layer 2 - External Users)
        # ═══════════════════════════════════════════════════════════
        application_auth = None
        if token:
            # Validate token - either via zAuth (if available) or direct database query
            if walker and hasattr(walker, 'zcli') and hasattr(walker.zcli, 'auth'):
                # Use new zAuth multi-app method (Week 6.3.6.6b)
                auth_result = walker.zcli.auth.authenticate_app_user(
                    app_name or "default_app",
                    token,
                    effective_config
                )
                
                if auth_result and auth_result.get("status") == "success":
                    application_auth = auth_result.get("user", {})
                    self.logger.info(
                        f"{_LOG_PREFIX} [{_LOG_OK}] {_LOG_APP_AUTH}: "
                        f"{application_auth.get(ZAUTH_KEY_USERNAME)} "
                        f"(app={auth_result.get('app_name')}, "
                        f"role={application_auth.get(ZAUTH_KEY_ROLE)})"
                    )
                else:
                    # Authentication failed
                    self.logger.warning(f"{_LOG_PREFIX} [{_LOG_BLOCK}] {_MSG_INVALID_TOKEN}")
                    await ws.close(code=_CLOSE_INVALID_TOKEN, reason=_REASON_INVALID_TOKEN)
                    return None
            else:
                # Fallback to direct database validation (legacy)
                application_auth = await self._validate_token_direct(ws, token, walker, effective_config)
                if not application_auth:
                    return None
        
        # ═══════════════════════════════════════════════════════════
        # Step 3: Determine authentication context and return result
        # ═══════════════════════════════════════════════════════════
        
        # Case 1: Both zSession and application authenticated (Dual-Auth - Layer 3)
        if zsession_auth and application_auth:
            self.logger.info(f"{_LOG_PREFIX} [{_LOG_OK}] {_LOG_DUAL_AUTH}")
            return {
                "authenticated": True,
                "context": _CONTEXT_DUAL,
                "zSession": zsession_auth,
                "application": application_auth,
                "app_name": app_name or "default_app",
                "dual_mode": True
            }
        
        # Case 2: Only zSession authenticated (Layer 1)
        if zsession_auth:
            return {
                "authenticated": True,
                "context": _CONTEXT_ZSESSION,
                "zSession": zsession_auth,
                "application": None,
                "dual_mode": False
            }
        
        # Case 3: Only application authenticated (Layer 2)
        if application_auth:
            return {
                "authenticated": True,
                "context": _CONTEXT_APPLICATION,
                "zSession": None,
                "application": application_auth,
                "app_name": app_name or "default_app",
                "dual_mode": False
            }
        
        # Case 4: No authentication provided but required
        self.logger.warning(f"{_LOG_PREFIX} [{_LOG_BLOCK}] {_MSG_NO_TOKEN}")
        await ws.close(code=_CLOSE_AUTH_REQUIRED, reason=_REASON_AUTH_REQUIRED)
        return None
    
    # Note: validate_origin() has been moved to zComm (Layer 0)
    # Use walker.zcli.comm.websocket.auth.validate_origin(ws) instead
    
    def register_client(self, ws: Any, auth_info: Dict[str, Any]) -> None:
        """
        Register an authenticated client.
        
        Scenario A (Concurrent Users): Each WebSocket is tracked independently.
        Scenario B (Multi-App): auth_info includes app_name and context.
        
        Args:
            ws: WebSocket connection
            auth_info: Authentication information (with context)
        """
        self.authenticated_clients[ws] = auth_info
    
    def unregister_client(self, ws: Any) -> Optional[Dict[str, Any]]:
        """
        Unregister a client on disconnection.
        
        Args:
            ws: WebSocket connection
        
        Returns:
            dict: Auth info of disconnected client, or None
        """
        if ws in self.authenticated_clients:
            auth_info = self.authenticated_clients[ws]
            del self.authenticated_clients[ws]
            return auth_info
        return None
    
    def get_client_info(self, ws: Any) -> Optional[Dict[str, Any]]:
        """
        Get authentication info for a client (with context).
        
        Args:
            ws: WebSocket connection
        
        Returns:
            dict: Auth info with context information:
                {
                    "context": "zSession" | "application" | "dual",
                    "zSession": {...} or None,
                    "application": {...} or None,
                    "app_name": str (if applicable),
                    "dual_mode": bool
                }
            None: If client not authenticated
        """
        return self.authenticated_clients.get(ws)
    
    # ═══════════════════════════════════════════════════════════
    # Private Helper Methods (DRY)
    # ═══════════════════════════════════════════════════════════
    
    def _get_ws_path(self, ws: Any) -> str:
        """
        Extract request path from WebSocket (handles old/new API).
        
        Args:
            ws: WebSocket connection
        
        Returns:
            str: Request path (default: "/")
        """
        return getattr(ws, 'path', None) or getattr(ws.request, 'path', '/')
    
    def _get_ws_headers(self, ws: Any) -> Dict[str, str]:
        """
        Extract request headers from WebSocket (handles old/new API).
        
        Args:
            ws: WebSocket connection
        
        Returns:
            dict: Request headers
        """
        return getattr(ws, 'request_headers', None) or getattr(ws.request, 'headers', {})
    
    # Note: _extract_token() has been moved to zComm (Layer 0)
    # Use walker.zcli.comm.websocket.auth.extract_token(ws) instead
    
    def _extract_app_name(self, path: str) -> Optional[str]:
        """
        Extract app_name from query parameters (for multi-app support).
        
        Args:
            path: Request path (may contain query parameters)
        
        Returns:
            str: App name, or None if not specified
        """
        query = path.split("?", 1)
        if len(query) > 1:
            try:
                params = dict(
                    param.split("=", 1) for param in query[1].split("&") if "=" in param
                )
                return params.get(_QUERY_PARAM_APP_NAME)
            except (ValueError, AttributeError):
                pass
        return None
    
    async def _validate_token_direct(
        self,
        ws: Any,
        token: str,
        walker: Any,
        config: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Validate token against database directly (fallback/legacy method).
        
        Used when zAuth.authenticate_app_user() is not available.
        
        Args:
            ws: WebSocket connection
            token: Authentication token
            walker: zCLI walker instance
            config: Auth configuration (user_model, field names, etc.)
        
        Returns:
            dict: User info if valid, None otherwise
        """
        try:
            if not walker:
                self.logger.error(f"{_LOG_PREFIX} {_MSG_NO_WALKER}")
                await ws.close(code=_CLOSE_AUTH_ERROR, reason=_REASON_CONFIG_ERROR)
                return None
            
            # Query user database using provided configuration
            result = walker.data.handle_request({
                "action": _DATA_ACTION_READ,
                "model": config["user_model"],
                "fields": [
                    config["id_field"],
                    config["username_field"],
                    config["role_field"]
                ],
                "filters": {config["api_key_field"]: token},
                "limit": 1
            })
            
            if result and len(result) > 0:
                user = result[0]
                self.logger.info(
                    f"{_LOG_PREFIX} [{_LOG_OK}] {_LOG_AUTH_SUCCESS}: "
                    f"{user.get(config['username_field'])} "
                    f"(role={user.get(config['role_field'])})"
                )
                
                # Return in standardized format
                return {
                    ZAUTH_KEY_AUTHENTICATED: True,
                    ZAUTH_KEY_ID: user.get(config["id_field"]),
                    ZAUTH_KEY_USERNAME: user.get(config["username_field"]),
                    ZAUTH_KEY_ROLE: user.get(config["role_field"]),
                    ZAUTH_KEY_API_KEY: token
                }
            
            self.logger.warning(f"{_LOG_PREFIX} [{_LOG_BLOCK}] {_MSG_INVALID_TOKEN}")
            await ws.close(code=_CLOSE_INVALID_TOKEN, reason=_REASON_INVALID_TOKEN)
            return None
        
        except Exception as e:
            self.logger.error(f"{_LOG_PREFIX} [{_LOG_ERROR}] {_LOG_AUTH_FAIL}: {e}")
            await ws.close(code=_CLOSE_AUTH_ERROR, reason=_REASON_AUTH_ERROR)
            return None
