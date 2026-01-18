# zCLI/subsystems/zComm/zComm_modules/comm_websocket_auth.py
"""
WebSocket Authentication Primitive for zComm (Layer 0).

Provides industry-grade security for WebSocket connections:
- Origin validation (CORS/CSRF protection)
- Token-based authentication
- Connection limit enforcement
- Client registration and tracking

This is Layer 0 infrastructure - basic auth primitives.
For three-tier authentication (zSession, Application, Dual), see zBifrost (Layer 2).
"""

from zOS import Any, Optional, Dict
from zOS import WebSocketServerProtocol
from urllib.parse import urlparse, parse_qs
from .comm_constants import (
    WS_CLOSE_CODE_POLICY_VIOLATION,
    WS_CLOSE_CODE_INTERNAL_ERROR,
    WS_REASON_INVALID_ORIGIN,
    WS_REASON_AUTH_REQUIRED,
    WS_REASON_INVALID_TOKEN,
    WS_REASON_MAX_CONNECTIONS
)

# Module Constants

_LOG_PREFIX = "[WebSocketAuth]"

# Log Messages
_LOG_ORIGIN_VALID = f"{_LOG_PREFIX} Origin validated: {{origin}}"
_LOG_ORIGIN_INVALID = f"{_LOG_PREFIX} Origin rejected: {{origin}}"
_LOG_TOKEN_VALID = f"{_LOG_PREFIX} Token validated for {{addr}}"
_LOG_TOKEN_INVALID = f"{_LOG_PREFIX} Invalid token from {{addr}}"
_LOG_TOKEN_MISSING = f"{_LOG_PREFIX} Missing token from {{addr}}"
_LOG_CONNECTION_LIMIT = f"{_LOG_PREFIX} Connection limit reached ({{current}}/{{max}})"
_LOG_CLIENT_REGISTERED = f"{_LOG_PREFIX} Client registered: {{addr}}"
_LOG_CLIENT_UNREGISTERED = f"{_LOG_PREFIX} Client unregistered: {{addr}}"


class WebSocketAuth:
    """
    WebSocket authentication primitive for Layer 0.
    
    Provides basic security features:
    - Origin validation (CORS/CSRF protection)
    - Token authentication (via .zEnv, env vars, or zSpark)
    - Connection limit enforcement
    - Client tracking
    
    Configuration:
        All settings come from zConfig.websocket:
        - require_auth: bool
        - allowed_origins: List[str]
        - token: str (from .zEnv or env vars)
        - max_connections: int
    
    Usage:
        # In comm_websocket.py
        self.auth = WebSocketAuth(self.config, self.logger)
        
        # Validate client before accepting
        if not self.auth.validate_connection(websocket):
            await websocket.close(1008, "Authentication failed")
    """
    
    def __init__(self, config: Any, logger: Any) -> None:
        """
        Initialize WebSocket authentication.
        
        Args:
            config: WebSocketConfig from zConfig
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.authenticated_clients: Dict[Any, Dict[str, Any]] = {}
    
    def validate_origin(self, websocket: WebSocketServerProtocol) -> bool:
        """
        Validate Origin header against allowed_origins from zConfig.
        
        Provides CORS/CSRF protection by checking the Origin header
        against the whitelist in zConfig.websocket.allowed_origins.
        
        Args:
            websocket: Client connection
            
        Returns:
            bool: True if origin is allowed, False otherwise
            
        Rules:
            - If allowed_origins is empty: Only localhost/file:// allowed
            - If allowed_origins has entries: Must match one of them
            - Missing Origin header: Allowed (some clients don't send it)
        """
        # Get allowed origins from zConfig
        allowed_origins = self.config.allowed_origins or []
        
        # Extract Origin header (websockets 15.0+ uses websocket.request.headers)
        origin_header = None
        if hasattr(websocket, 'request') and websocket.request:
            origin_header = websocket.request.headers.get('Origin')
        elif hasattr(websocket, 'request_headers'):
            origin_header = websocket.request_headers.get('Origin')
        elif hasattr(websocket, 'origin'):
            origin_header = websocket.origin
        
        # No Origin header - allow (some WebSocket clients don't send it)
        if not origin_header:
            self.logger.framework.debug(f"{_LOG_PREFIX} No Origin header, allowing connection")
            return True
        
        # Empty allowed_origins = localhost only
        if not allowed_origins:
            is_local = any(local in origin_header for local in ['localhost', '127.0.0.1', 'file://'])
            if is_local:
                self.logger.framework.debug(_LOG_ORIGIN_VALID.format(origin=origin_header))
                return True
            else:
                self.logger.warning(_LOG_ORIGIN_INVALID.format(origin=origin_header))
                return False
        
        # Check against whitelist
        # Note: Browsers send "null" (string) for file:// origins, so accept both
        if origin_header in allowed_origins:
            self.logger.framework.debug(_LOG_ORIGIN_VALID.format(origin=origin_header))
            return True
        
        # Accept "null" origin if "file://" is in allowed_origins (local HTML files)
        if origin_header == "null" and "file://" in allowed_origins:
            self.logger.framework.debug(f"{_LOG_PREFIX} Accepting 'null' origin (file:// allowed)")
            return True
        
        self.logger.warning(_LOG_ORIGIN_INVALID.format(origin=origin_header))
        return False
    
    def extract_token(self, websocket: WebSocketServerProtocol) -> Optional[str]:
        """
        Extract authentication token from WebSocket connection.
        
        Checks (in order):
        1. Query params: ?token=xxx
        2. Headers: Authorization: Bearer xxx
        
        Args:
            websocket: Client connection
            
        Returns:
            str: Token if found, None otherwise
        """
        # 1. Try query params (websockets 15.0+ uses websocket.request.path)
        path = None
        if hasattr(websocket, 'request') and websocket.request:
            path = websocket.request.path
        elif hasattr(websocket, 'path'):
            path = websocket.path  # Fallback for older versions
        
        if path:
            parsed = urlparse(path)
            query_params = parse_qs(parsed.query)
            if 'token' in query_params:
                return query_params['token'][0]
        
        # 2. Try Authorization header
        headers = None
        if hasattr(websocket, 'request') and websocket.request:
            headers = websocket.request.headers
        elif hasattr(websocket, 'request_headers'):
            headers = websocket.request_headers  # Fallback for older versions
        
        if headers:
            auth_header = headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                return auth_header[7:]  # Remove "Bearer " prefix
        
        return None
    
    def validate_token(self, token: str) -> bool:
        """
        Validate token against zConfig value.
        
        Checks token against:
        1. WEBSOCKET_TOKEN env var (highest priority)
        2. websocket.token from .zEnv
        3. websocket.token from zConfig.environment.yaml
        
        Args:
            token: Token to validate
            
        Returns:
            bool: True if token matches expected value, False otherwise
        """
        expected_token = self.config.token
        
        # No token configured - reject all
        if not expected_token:
            self.logger.warning(f"{_LOG_PREFIX} Token validation requested but no WEBSOCKET_TOKEN configured")
            return False
        
        # Compare tokens
        return token == expected_token
    
    def check_connection_limit(self) -> bool:
        """
        Check if connection limit has been reached.
        
        Returns:
            bool: True if connection can be accepted, False if limit reached
        """
        max_connections = self.config.max_connections
        current_count = len(self.authenticated_clients)
        
        if current_count >= max_connections:
            self.logger.warning(_LOG_CONNECTION_LIMIT.format(
                current=current_count,
                max=max_connections
            ))
            return False
        
        return True
    
    def register_client(self, websocket: WebSocketServerProtocol, auth_info: Dict[str, Any]) -> None:
        """
        Register authenticated client.
        
        Args:
            websocket: Client connection
            auth_info: Authentication details (token, addr, etc.)
        """
        self.authenticated_clients[websocket] = auth_info
        client_addr = auth_info.get('addr', 'unknown')
        self.logger.framework.debug(_LOG_CLIENT_REGISTERED.format(addr=client_addr))
    
    def unregister_client(self, websocket: WebSocketServerProtocol) -> None:
        """
        Unregister client on disconnect.
        
        Args:
            websocket: Client connection
        """
        if websocket in self.authenticated_clients:
            auth_info = self.authenticated_clients.pop(websocket)
            client_addr = auth_info.get('addr', 'unknown')
            self.logger.framework.debug(_LOG_CLIENT_UNREGISTERED.format(addr=client_addr))
    
    def get_client_info(self, websocket: WebSocketServerProtocol) -> Optional[Dict[str, Any]]:
        """
        Get authentication info for registered client.
        
        Args:
            websocket: Client connection
            
        Returns:
            dict: Auth info if client is registered, None otherwise
        """
        return self.authenticated_clients.get(websocket)
    
    @property
    def client_count(self) -> int:
        """Get count of authenticated clients."""
        return len(self.authenticated_clients)

