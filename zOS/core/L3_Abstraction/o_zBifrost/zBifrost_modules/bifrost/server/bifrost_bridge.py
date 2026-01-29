# zCLI/subsystems/zComm/zComm_modules/bifrost/bifrost_bridge.py
"""
zBifrost WebSocket Bridge - Secure Real-Time Communication Server.

Provides a production-ready WebSocket server with modular architecture for
real-time bidirectional communication between Python backend and JavaScript
frontend clients. Features include event-driven message routing, client
authentication, schema caching, and graceful shutdown.

Architecture:
    - Event-Driven: Messages route through centralized event map to domain-specific handlers
    - Modular Components: CacheManager, AuthenticationManager, MessageHandler, ConnectionInfoManager
    - Async/Await: Full async support for non-blocking I/O and concurrent connections
    - Health Monitoring: Built-in health check API for service monitoring
    - Graceful Shutdown: Timeout-based shutdown with client notification

Key Responsibilities:
    - WebSocket server lifecycle (start, stop, health checks)
    - Client connection management (authentication, registration, cleanup)
    - Message routing and event dispatch
    - Broadcasting to multiple clients
    - Integration with zCLI configuration and logging systems
"""

from zOS import (
    asyncio, json, time,
    Optional, Dict, Any,
    ws_serve, WebSocketServerProtocol, ws_exceptions
)
from zOS.L1_Foundation.b_zComm.zComm_modules.comm_websocket_auth import WebSocketAuth
from .modules import (
    CacheManager,
    AuthenticationManager,
    MessageHandler,
    ConnectionInfoManager
)
from .modules.events import (
    ClientEvents,
    CacheEvents,
    DiscoveryEvents,
    DispatchEvents
)
# Phase 1: Output buffering for handling slow clients
from .buffered_connection import BufferedConnection
# Phase 1: Prometheus metrics (optional)
from .monitoring import get_metrics

# ═══════════════════════════════════════════════════════════
# Module-Level Constants
# ═══════════════════════════════════════════════════════════

# Default Configuration
_DEFAULT_PORT = 56891
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_REQUIRE_AUTH = True
_DEFAULT_ALLOWED_ORIGINS = []
_DEFAULT_QUERY_TTL = 60
_DEFAULT_SHUTDOWN_TIMEOUT = 5.0
# Phase 1: Buffering configuration
_DEFAULT_USE_BUFFERING = True  # Enable by default for Phase 1
_DEFAULT_BUFFER_SIZE = 1000  # Max messages per client

# Port Validation
_PORT_MIN = 1
_PORT_MAX = 65535

# Log Prefix
_LOG_PREFIX = "[zBifrost]"

# Log Messages
_LOG_INITIALIZED = f"{_LOG_PREFIX} Initialized with event-driven architecture"
_LOG_NEW_CONNECTION = f"{_LOG_PREFIX} [INFO] New connection from {{remote_addr}}, path: {{path}}"
_LOG_BLOCK_INVALID_ORIGIN = f"{_LOG_PREFIX} [BLOCK] Connection rejected due to invalid origin"
_LOG_CLIENT_AUTHENTICATED = f"{_LOG_PREFIX} [OK] Client authenticated and connected: {{user}} ({{remote_addr}})"
_LOG_OK_SENT_CONNECTION_INFO = f"{_LOG_PREFIX} [OK] Sent connection info to {{user}}"
_LOG_WARN_FAILED_SEND_INFO = f"{_LOG_PREFIX} [WARN] Failed to send connection info: {{error}}"
_LOG_CLIENT_DISCONNECTED = f"{_LOG_PREFIX} Client disconnected normally"
_LOG_DISCONNECT_ERROR = f"{_LOG_PREFIX} [DISCONNECT] Client disconnected with error: {{error}}"
_LOG_USER_DISCONNECTED = f"{_LOG_PREFIX} [DISCONNECT] User {{user}} disconnected"
_LOG_ACTIVE_CLIENTS = f"{_LOG_PREFIX} [INFO] Active clients: {{count}}"
_LOG_RECEIVED = f"{_LOG_PREFIX} [RECV] Received: {{message}}"
_LOG_MISSING_EVENT = f"{_LOG_PREFIX} Message missing 'event' field and cannot be inferred"
_LOG_UNKNOWN_EVENT = f"{_LOG_PREFIX} Unknown event: {{event}}"
_LOG_ERROR_HANDLING_EVENT = f"{_LOG_PREFIX} Error handling event '{{event}}': {{error}}"
_LOG_BROADCASTING = f"{_LOG_PREFIX} [BROADCAST] Broadcasting to {{count}} other clients"
_LOG_SENT = f"{_LOG_PREFIX} [SENT] Sent to {{remote_addr}}"
_LOG_BROADCAST_SKIPPED = f"{_LOG_PREFIX} [BROADCAST] Skipped client (closed or error): {{error}}"
_LOG_LIVE_SOCKET = "[OK] LIVE zSocket loaded"
_LOG_SECURITY = "[SECURITY] Security: Auth={{auth}}, Origins={{origins}}"
_LOG_HANDLER = "[HANDLER] Handler = {{name}}, args = {{args}}"
_LOG_STARTED = f"{_LOG_PREFIX} [STARTED] WebSocket server started at {{bind_info}}{{security_note}}"
_LOG_ERROR_PORT_IN_USE = "[ERROR] Port {{port}} already in use. Try restarting the app or killing the stuck process."
_LOG_ERROR_START_FAILED = "[ERROR] Failed to start WebSocket server: {{error}}"
_LOG_SHUTDOWN_NOT_RUNNING = f"{_LOG_PREFIX} Server not running, nothing to shutdown"
_LOG_SHUTDOWN_INITIATING = f"{_LOG_PREFIX} Initiating graceful shutdown..."
_LOG_SHUTDOWN_CLOSING_CLIENTS = f"{_LOG_PREFIX} Closing {{count}} active connections..."
_LOG_SHUTDOWN_CLIENT_CLOSED = f"{_LOG_PREFIX} Closed client connection"
_LOG_SHUTDOWN_ERROR_CLOSING = f"{_LOG_PREFIX} Error closing client: {{error}}"
_LOG_SHUTDOWN_CLOSING_SERVER = f"{_LOG_PREFIX} Closing WebSocket server..."
_LOG_SHUTDOWN_SUCCESS = f"{_LOG_PREFIX} WebSocket server closed successfully"
_LOG_SHUTDOWN_TIMEOUT = f"{_LOG_PREFIX} Server shutdown timed out after {{timeout}}s"
_LOG_SHUTDOWN_ERROR = f"{_LOG_PREFIX} Error during shutdown: {{error}}"
_LOG_SHUTDOWN_COMPLETE = f"{_LOG_PREFIX} Shutdown complete"
_LOG_SYNC_SHUTDOWN = f"{_LOG_PREFIX} Synchronous shutdown (loop running)..."
_LOG_SYNC_FORCE_CLOSING = f"{_LOG_PREFIX} Forcefully closing {{count}} connections..."
_LOG_SYNC_CLOSED = f"{_LOG_PREFIX} Server closed (sync)"
_LOG_SYNC_ERROR = f"{_LOG_PREFIX} Sync close error: {{error}}"
_LOG_SYNC_COMPLETE = f"{_LOG_PREFIX} Sync shutdown complete"

# JSON Message Keys
_KEY_EVENT = "event"
_KEY_DATA = "data"
_KEY_ERROR = "error"
_KEY_MESSAGE = "message"
_KEY_AUTH = "auth"
_KEY_DETAILS = "details"
_KEY_ACTION = "action"
_KEY_ZKEY = "zKey"
_KEY_CMD = "cmd"
_KEY_USER = "user"

# Event Names
_EVENT_CONNECTION_INFO = "connection_info"
_EVENT_SERVER_SHUTDOWN = "server_shutdown"
_EVENT_INPUT_RESPONSE = "input_response"
_EVENT_BUTTON_ACTION = "button_action"
_EVENT_PAGE_UNLOAD = "page_unload"
_EVENT_GET_SCHEMA = "get_schema"
_EVENT_CLEAR_CACHE = "clear_cache"
_EVENT_CACHE_STATS = "cache_stats"
_EVENT_SET_CACHE_TTL = "set_cache_ttl"
_EVENT_DISCOVER = "discover"
_EVENT_INTROSPECT = "introspect"
_EVENT_DISPATCH = "dispatch"
_EVENT_EXECUTE_CODE = "execute_code"

# Health Check Keys
_HEALTH_RUNNING = "running"
_HEALTH_HOST = "host"
_HEALTH_PORT = "port"
_HEALTH_URL = "url"
_HEALTH_CLIENTS = "clients"
_HEALTH_AUTHENTICATED_CLIENTS = "authenticated_clients"
_HEALTH_REQUIRE_AUTH = "require_auth"
_HEALTH_UPTIME = "uptime"

# Error/Reason Messages
_ERROR_INVALID_ORIGIN = "Invalid origin"
_ERROR_RATE_LIMIT = "Rate limit exceeded"
_ERROR_FAILED_HANDLE_EVENT = "Failed to handle event: {event}"
_ERROR_CLOSING_CLIENT = "Error closing client connection during shutdown"
_ERROR_SHUTDOWN = "Error during WebSocket server shutdown"

# Shutdown Messages
_MSG_SERVER_SHUTDOWN = "Server is shutting down"

# Security Notes
_SECURITY_LOCALHOST_ONLY = " ([LOCK] localhost only - use nginx proxy for external access)"

# WebSocket Close Codes
_WS_CLOSE_INVALID_ORIGIN = 1008

# Error Numbers (macOS/Linux)
_ERRNO_ADDRESS_IN_USE = 48

# Validation Error Messages
_ERROR_LOGGER_REQUIRED = "logger parameter is required and cannot be None"
_ERROR_PORT_RANGE = f"port must be between {_PORT_MIN} and {_PORT_MAX}, got: {{port}}"
_ERROR_TIMEOUT_POSITIVE = "timeout must be a positive number, got: {timeout}"


class zBifrost:
    """
    Secure WebSocket server with modular event-driven architecture.
    
    Provides production-ready WebSocket communication with authentication,
    caching, message routing, and graceful shutdown capabilities.
    
    Modules:
        CacheManager: Schema and query result caching with TTL support
        AuthenticationManager: Client authentication and origin validation
        MessageHandler: Message routing and command dispatch
        ConnectionInfoManager: Server metadata for client discovery
    
    Lifecycle:
        1. Initialize with logger (required) and optional walker/zcli
        2. Call start_socket_server() to start async WebSocket server
        3. Server authenticates clients and routes messages via event map
        4. Call shutdown() for graceful cleanup with client notification
    
    Health Monitoring:
        Use health_check() to get server status, connected clients, and config
    
    Args:
        logger: Logger instance (required)
        walker: Optional Walker instance for zCLI integration
        zcli: Optional zCLI instance (falls back to walker.zcli if not provided)
        port: WebSocket server port (defaults to config or 56891)
        host: WebSocket server host (defaults to config or 127.0.0.1)
    
    Raises:
        ValueError: If logger is None or port is out of range (1-65535)
    """

    def __init__(
        self,
        logger: Any,
        *,
        walker: Optional[Any] = None,
        zcli: Optional[Any] = None,
        port: Optional[int] = None,
        host: Optional[str] = None
    ) -> None:
        """
        Initialize zBifrost WebSocket bridge with validation.
        
        Args:
            logger: Logger instance (required, cannot be None)
            walker: Optional Walker instance
            zcli: Optional zCLI instance (or derived from walker)
            port: Server port (1-65535, defaults to config or 56891)
            host: Server host (defaults to config or 127.0.0.1)
        
        Raises:
            ValueError: If logger is None or port out of range
        """
        # Input validation
        if logger is None:
            raise ValueError(_ERROR_LOGGER_REQUIRED)

        if port is not None and (port < _PORT_MIN or port > _PORT_MAX):
            raise ValueError(_ERROR_PORT_RANGE.format(port=port))

        self.walker = walker
        self.zcli = zcli or (walker.zcli if walker else None)
        self.logger = logger

        # Load WebSocket configuration from zCLI config system
        if self.zcli and hasattr(self.zcli, 'config') and hasattr(self.zcli.config, 'websocket'):
            self.ws_config = self.zcli.config.websocket
            self.port = port or self.ws_config.port
            self.host = host or self.ws_config.host
            require_auth = self.ws_config.require_auth
            allowed_origins = self.ws_config.allowed_origins
        else:
            # Fallback to defaults if zCLI config not available
            self.port = port or _DEFAULT_PORT
            self.host = host or _DEFAULT_HOST
            require_auth = _DEFAULT_REQUIRE_AUTH
            allowed_origins = _DEFAULT_ALLOWED_ORIGINS

        self.clients = set()
        self._running = False  # Track server running state
        self._start_time = None  # Track server start time for uptime calculation
        self.server = None  # WebSocket server instance
        
        # Phase 1: Connection Indexing (O(1) user lookup)
        # Maps user_id -> set of WebSocket connections (supports multiple tabs/devices)
        from collections import defaultdict
        self.user_connections: Dict[str, set] = defaultdict(set)
        # Reverse lookup: WebSocket -> user_id (for cleanup)
        self.connection_users: Dict[WebSocketServerProtocol, str] = {}
        
        # Phase 1: Metrics (optional, gracefully degrades)
        self.metrics = get_metrics()

        # Initialize modular components
        self.cache = CacheManager(logger, default_query_ttl=_DEFAULT_QUERY_TTL)
        
        # Layer 0: Basic WebSocket auth (origin/token validation)
        self.ws_auth = WebSocketAuth(zcli.config.websocket, logger) if zcli else None
        
        # Layer 2: Three-tier authentication orchestrator
        self.auth = AuthenticationManager(logger, require_auth, allowed_origins)
        
        self.connection_info = ConnectionInfoManager(logger, self.cache, self.zcli, self.walker)
        self.message_handler = MessageHandler(
            logger, self.cache, self.zcli, self.walker,
            connection_info_manager=self.connection_info,
            auth_manager=self.auth
        )

        # Initialize event handlers (event-driven architecture)
        from .modules.events.bridge_event_menu import MenuEvents
        
        self.events = {
            'client': ClientEvents(self, auth_manager=self.auth),
            'cache': CacheEvents(self, auth_manager=self.auth),
            'discovery': DiscoveryEvents(self, auth_manager=self.auth),
            'dispatch': DispatchEvents(self, auth_manager=self.auth),
            'menu': MenuEvents(self)
        }

        # Event map - single registry for all events (like zDisplay)
        self._event_map = {
            # Client events
            _EVENT_INPUT_RESPONSE: self.events['client'].handle_input_response,
            _EVENT_BUTTON_ACTION: self.events['client'].handle_button_action,
            _EVENT_CONNECTION_INFO: self.events['client'].handle_connection_info,
            _EVENT_PAGE_UNLOAD: self.events['client'].handle_page_unload,
            _EVENT_EXECUTE_CODE: self.events['client'].handle_execute_code,

            # Cache events
            _EVENT_GET_SCHEMA: self.events['cache'].handle_get_schema,
            _EVENT_CLEAR_CACHE: self.events['cache'].handle_clear_cache,
            _EVENT_CACHE_STATS: self.events['cache'].handle_cache_stats,
            _EVENT_SET_CACHE_TTL: self.events['cache'].handle_set_cache_ttl,

            # Discovery events
            _EVENT_DISCOVER: self.events['discovery'].handle_discover,
            _EVENT_INTROSPECT: self.events['discovery'].handle_introspect,

            # Dispatch events (zDispatch commands)
            _EVENT_DISPATCH: self.events['dispatch'].handle_dispatch,
            
            # Menu events (menu navigation in Bifrost mode)
            'menu_selection': self.events['menu'].handle_menu_selection,
            
            # Walker execution events (declarative UI rendering)
            'execute_walker': self.message_handler._handle_walker_execution,
            'load_page': self.message_handler._handle_walker_execution,
            
            # Form submission events (async form handling)
            'form_submit': self.message_handler._handle_form_submit,
        }

        self.logger.info(_LOG_INITIALIZED)

    # ═══════════════════════════════════════════════════════════
    # Client Connection Handling
    # ═══════════════════════════════════════════════════════════

    async def handle_client(self, ws: WebSocketServerProtocol) -> None:
        """
        Handle WebSocket client connection with authentication and message processing.
        
        Manages the complete client lifecycle: origin validation, authentication,
        registration, message handling, and cleanup on disconnect.
        
        Args:
            ws: WebSocket connection protocol instance
        """
        # Get connection details
        path = getattr(ws, 'path', None) or getattr(ws.request, 'path', '/')
        remote_addr = getattr(ws, 'remote_address', None) or getattr(ws.remote_address, '__str__', lambda: 'N/A')()

        self.logger.info(_LOG_NEW_CONNECTION.format(remote_addr=remote_addr, path=path))

        # Validate origin (Layer 0 primitive)
        if self.ws_auth and not self.ws_auth.validate_origin(ws):
            self.logger.warning(_LOG_BLOCK_INVALID_ORIGIN)
            await ws.close(code=_WS_CLOSE_INVALID_ORIGIN, reason=_ERROR_INVALID_ORIGIN)
            return

        # Authenticate client
        auth_info = await self.auth.authenticate_client(ws, self.walker)
        if not auth_info:
            return  # Connection closed in authenticate_client

        # Generate Bifrost session ID (hierarchical: zS_xxx:zB_xxx)
        import secrets
        bifrost_session_id = f"zB_{secrets.token_hex(4)}"  # 8-char hex (matches zS_ format)
        zspark_id = self.zcli.session.get("zS_id", "zS_unknown") if self.zcli else "zS_unknown"
        full_session_id = f"{zspark_id}:{bifrost_session_id}"
        
        # Attach to WebSocket connection
        ws.session_id = bifrost_session_id
        ws.zspark_id = zspark_id
        ws.full_session_id = full_session_id
        
        # Store session metadata in auth_info for persistence
        auth_info["bifrost_session"] = {
            "session_id": bifrost_session_id,
            "zspark_id": zspark_id,
            "full_id": full_session_id,
            "created_at": time.time(),
            "persistent": auth_info.get("context") != "guest"
        }
        
        user = auth_info.get(_KEY_USER, "anonymous")
        self.logger.info(f"{_LOG_PREFIX} Generated session: {full_session_id} for user: {user}")

        # Register client
        self.auth.register_client(ws, auth_info)
        self.clients.add(ws)
        
        # Phase 1: Index connection by user_id for O(1) lookup
        user = auth_info.get(_KEY_USER)
        if user:
            self.user_connections[user].add(ws)
            self.connection_users[ws] = user
        
        # Phase 1: Metrics
        self.metrics.connection_opened()
        self.metrics.set_active_connections(len(self.clients))

        self.logger.info(_LOG_CLIENT_AUTHENTICATED.format(user=user, remote_addr=remote_addr))

        # Send connection info to client
        await self._send_connection_info(ws, auth_info)

        # Handle messages
        try:
            async for message in ws:
                # Mask passwords in logged messages
                try:
                    import json
                    from zOS.L2_Core.j_zDialog.dialog_modules.dialog_submit import _mask_passwords_in_dict
                    msg_dict = json.loads(message)
                    masked_msg = _mask_passwords_in_dict(msg_dict)
                    self.logger.info(_LOG_RECEIVED.format(message=json.dumps(masked_msg)))
                except:
                    # If parsing fails, log as-is
                    self.logger.info(_LOG_RECEIVED.format(message=message))
                
                await self.handle_message(ws, message)

        except ws_exceptions.ConnectionClosed:
            self.logger.info(_LOG_CLIENT_DISCONNECTED)
        except Exception as e:
            self.logger.warning(_LOG_DISCONNECT_ERROR.format(error=e))
        finally:
            await self._cleanup_client(ws)

    async def _send_connection_info(self, ws: WebSocketServerProtocol, auth_info: Dict[str, Any]) -> None:
        """
        Send connection info to newly connected client.
        
        Args:
            ws: WebSocket connection
            auth_info: Authentication information dict
        """
        try:
            connection_info = self.connection_info.get_connection_info()
            connection_info[_KEY_AUTH] = auth_info

            await ws.send(json.dumps({
                _KEY_EVENT: _EVENT_CONNECTION_INFO,
                _KEY_DATA: connection_info
            }))

            user = auth_info.get(_KEY_USER)
            self.logger.debug(_LOG_OK_SENT_CONNECTION_INFO.format(user=user))
        except Exception as e:
            self.logger.warning(_LOG_WARN_FAILED_SEND_INFO.format(error=e))

    async def _cleanup_client(self, ws: WebSocketServerProtocol) -> None:
        """
        Clean up client connection and remove from tracking.
        
        Args:
            ws: WebSocket connection to clean up
        """
        if ws in self.clients:
            self.clients.remove(ws)

        auth_info = self.auth.unregister_client(ws)
        
        # Phase 1: Remove from connection index
        if ws in self.connection_users:
            indexed_user = self.connection_users[ws]
            del self.connection_users[ws]
            
            # Remove from user_connections
            if indexed_user in self.user_connections:
                self.user_connections[indexed_user].discard(ws)
                # Clean up empty sets
                if not self.user_connections[indexed_user]:
                    del self.user_connections[indexed_user]
        
        if auth_info:
            user = auth_info.get(_KEY_USER, 'unknown')
            self.logger.info(_LOG_USER_DISCONNECTED.format(user=user))
        
        # Phase 1: Metrics
        self.metrics.connection_closed(reason='normal')
        self.metrics.set_active_connections(len(self.clients))
        
        # Clean up any paused generators for this connection
        ws_id = id(ws)
        if hasattr(self.message_handler, '_paused_generators') and ws_id in self.message_handler._paused_generators:
            del self.message_handler._paused_generators[ws_id]
            self.logger.debug(f"[Cleanup] Removed paused generator for disconnected ws={ws_id}")
        
        # Phase 1: Clean up schema cache (closes DB connections)
        if hasattr(self.message_handler, '_ws_schema_caches') and ws_id in self.message_handler._ws_schema_caches:
            schema_cache = self.message_handler._ws_schema_caches[ws_id]
            # Close all cached database connections
            try:
                schema_cache.clear()  # This disconnects all cached adapters
                del self.message_handler._ws_schema_caches[ws_id]
                self.logger.debug(f"[Phase1] Cleaned up schema cache for ws_id={ws_id} (DB connections closed)")
            except Exception as e:
                self.logger.warning(f"[Phase1] Error cleaning schema cache: {e}")

        self.logger.debug(_LOG_ACTIVE_CLIENTS.format(count=len(self.clients)))

    # ═══════════════════════════════════════════════════════════
    # Message Handling - Event-Driven Architecture
    # ═══════════════════════════════════════════════════════════

    async def handle_message(self, ws: WebSocketServerProtocol, message: str) -> None:
        """
        Single entry point for all messages (mirrors zDisplay.handle).
        
        Routes messages to appropriate event handlers based on event type.
        The 'event' field is REQUIRED in all messages for clarity and protocol consistency.
        
        Args:
            ws: WebSocket connection
            message: Raw message string (JSON or plain text)
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            # Fallback to simple broadcast if not JSON
            await self.broadcast(message, sender=ws)
            return

        # Get event type - REQUIRED (no more inference)
        event = data.get(_KEY_EVENT)

        if not event:
            # Modern protocol: event field is required
            self.logger.warning(_LOG_MISSING_EVENT)
            error_response = {
                _KEY_ERROR: "Invalid message format",
                _KEY_MESSAGE: "The 'event' field is required in all messages"
            }
            await ws.send(json.dumps(error_response))
            return

        # Phase 1: Metrics - record message received
        self.metrics.message_received(event_type=event)
        
        # Route to handler via event map
        handler = self._event_map.get(event)
        if not handler:
            self.logger.warning(_LOG_UNKNOWN_EVENT.format(event=event))
            await self.broadcast(json.dumps(data), sender=ws)
            return

        # Execute handler
        # For custom event handlers that may block on user input (like show_inputs),
        # we need to run them as background tasks to avoid blocking the message loop.
        # This prevents deadlock when handler awaits input_response that arrives later.
        try:
            # Check if this is a built-in event that should be awaited inline
            builtin_events = {
                _EVENT_INPUT_RESPONSE, _EVENT_CONNECTION_INFO, _EVENT_PAGE_UNLOAD, _EVENT_GET_SCHEMA, 
                _EVENT_CLEAR_CACHE, _EVENT_CACHE_STATS, _EVENT_SET_CACHE_TTL,
                _EVENT_DISCOVER, _EVENT_INTROSPECT, _EVENT_DISPATCH,
                'execute_walker', 'load_page', 'form_submit',  # Walker and form events need responses
                'menu_selection'  # Menu selection needs immediate response
            }
            
            if event in builtin_events:
                # Built-in events: await normally (they don't block on user input)
                await handler(ws, data)
            else:
                # Custom handlers: run as background task to avoid blocking message loop
                asyncio.create_task(handler(ws, data))
                self.logger.debug(f"[zBifrost] Created background task for event: {event}")
        except Exception as e:
            self.logger.error(_LOG_ERROR_HANDLING_EVENT.format(event=event, error=e), exc_info=True)
            error_response = {
                _KEY_ERROR: _ERROR_FAILED_HANDLE_EVENT.format(event=event),
                _KEY_DETAILS: str(e)
            }
            await ws.send(json.dumps(error_response))

    # ═══════════════════════════════════════════════════════════
    # Health Check
    # ═══════════════════════════════════════════════════════════

    def health_check(self) -> Dict[str, Any]:
        """
        Get health status of WebSocket server.
        
        Returns:
            Server health status dict with keys:
                - running (bool): Whether server is running
                - host (str): Server host address
                - port (int): Server port
                - url (str|None): Server WebSocket URL (None if not running)
                - clients (int): Number of connected clients
                - authenticated_clients (int): Number of authenticated clients
                - require_auth (bool): Whether authentication is required
                - uptime (float): Seconds since server start (0.0 if not running)
        """
        # Calculate uptime if server is running
        uptime = 0.0
        if self._running and self._start_time is not None:
            uptime = time.time() - self._start_time
        
        return {
            _HEALTH_RUNNING: self._running,
            _HEALTH_HOST: self.host,
            _HEALTH_PORT: self.port,
            _HEALTH_URL: f"ws://{self.host}:{self.port}" if self._running else None,
            _HEALTH_CLIENTS: len(self.clients),
            _HEALTH_AUTHENTICATED_CLIENTS: len(self.auth.authenticated_clients),
            _HEALTH_REQUIRE_AUTH: self.auth.require_auth,
            _HEALTH_UPTIME: uptime
        }

    # ═══════════════════════════════════════════════════════════
    # Broadcasting
    # ═══════════════════════════════════════════════════════════

    async def broadcast(self, message: str, sender: Optional[WebSocketServerProtocol] = None) -> None:
        """
        Phase 1: Non-blocking broadcast to all connected clients except sender.
        
        Uses asyncio.create_task() to prevent slow clients from blocking fast clients.
        
        Args:
            message: Message string to broadcast
            sender: Optional sender to exclude from broadcast
        """
        count = len(self.clients) - (1 if sender else 0)
        self.logger.debug(_LOG_BROADCASTING.format(count=count))

        # Phase 1: Create tasks for non-blocking sends
        tasks = []
        for client in self.clients:
            if client != sender:
                task = asyncio.create_task(self._send_to_client(client, message))
                tasks.append(task)
        
        # Don't await tasks - let them run in background
        # This prevents slow clients from blocking the broadcast
        self.logger.debug(f"{_LOG_PREFIX} [Phase1] Created {len(tasks)} non-blocking send tasks")
        
        # Phase 1: Metrics
        self.metrics.broadcast_sent()
    
    async def _send_to_client(self, client: WebSocketServerProtocol, message: str) -> None:
        """
        Phase 1: Helper for non-blocking client sends.
        
        Args:
            client: Client WebSocket connection
            message: Message to send
        """
        try:
            # Check if connection is open (compatible with all websockets versions)
            is_open = getattr(client, 'open', None) or (not getattr(client, 'closed', False))
            if is_open:
                await client.send(message)
                remote_addr = getattr(client, 'remote_address', 'N/A')
                self.logger.debug(_LOG_SENT.format(remote_addr=remote_addr))
        except Exception as e:
            self.logger.debug(_LOG_BROADCAST_SKIPPED.format(error=e))

    async def send_to_user(self, user_id: str, message: str) -> int:
        """
        Phase 1: Send message to all connections for a specific user (O(1) lookup + non-blocking).
        
        Supports multiple tabs/devices per user. Uses non-blocking sends.
        
        Args:
            user_id: User ID to send message to
            message: Message string to send
        
        Returns:
            Number of connections message was sent to (queued, not delivered)
        """
        if user_id not in self.user_connections:
            self.logger.debug(f"{_LOG_PREFIX} [O(1)] No connections for user: {user_id}")
            return 0
        
        # Phase 1: Non-blocking sends
        tasks = []
        for ws in self.user_connections[user_id]:
            task = asyncio.create_task(self._send_to_client(ws, message))
            tasks.append(task)
        
        self.logger.debug(f"{_LOG_PREFIX} [O(1)] Queued message to user '{user_id}' ({len(tasks)} connections)")
        return len(tasks)

    # ═══════════════════════════════════════════════════════════
    # Server Lifecycle
    # ═══════════════════════════════════════════════════════════

    async def start_socket_server(self, socket_ready: Any) -> None:
        """
        Start the WebSocket server and signal when ready.
        
        Args:
            socket_ready: Async event to signal when server is ready
        """
        self.logger.info(_LOG_LIVE_SOCKET)
        origins = self.auth.allowed_origins if self.auth.allowed_origins else 'localhost only'
        self.logger.info(_LOG_SECURITY.format(auth=self.auth.require_auth, origins=origins))
        self.logger.info(_LOG_HANDLER.format(
            name=self.handle_client.__name__,
            args=self.handle_client.__code__.co_varnames
        ))

        # Delegate to Layer 0 (zComm) for SSL context creation (respects zConfig)
        ssl_context = None
        if self.zcli and hasattr(self.zcli.comm, 'websocket'):
            ssl_context = self.zcli.comm.websocket._create_ssl_context()
        
        try:
            self.server = await ws_serve(self.handle_client, self.host, self.port, ssl=ssl_context)
        except OSError as e:
            if getattr(e, 'errno', None) == _ERRNO_ADDRESS_IN_USE:
                self.logger.error(_LOG_ERROR_PORT_IN_USE.format(port=self.port))
            else:
                self.logger.error(_LOG_ERROR_START_FAILED.format(error=e))
            return

        protocol = "wss" if ssl_context else "ws"
        bind_info = f"{protocol}://{self.host}:{self.port}"
        security_note = _SECURITY_LOCALHOST_ONLY if self.host == _DEFAULT_HOST else ""
        self.logger.info(_LOG_STARTED.format(bind_info=bind_info, security_note=security_note))
        self._running = True
        self._start_time = time.time()  # Record server start time for uptime tracking
        socket_ready.set()
        await self.server.wait_closed()
        self._running = False
        self._start_time = None  # Clear start time when server stops

    def _log_with_traceback(self, e: Exception, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log exception with zTraceback if available, otherwise use standard logging.
        
        DRY helper to eliminate duplicate zTraceback pattern throughout shutdown code.
        
        Args:
            e: Exception to log
            message: Log message describing the error
            context: Optional context dict for zTraceback
        """
        if self.zcli and hasattr(self.zcli, 'zTraceback'):
            self.zcli.zTraceback.log_exception(e, message=message, context=context)
        else:
            self.logger.error(f"{_LOG_PREFIX} {message}: {e}", exc_info=True)

    async def shutdown(self, timeout: float = _DEFAULT_SHUTDOWN_TIMEOUT) -> None:
        """
        Gracefully shutdown WebSocket server.
        
        Closes all active client connections and stops the server.
        Uses zTraceback for consistent error handling during cleanup.
        
        Args:
            timeout: Maximum time in seconds to wait for graceful shutdown (default: 5.0)
        
        Raises:
            ValueError: If timeout is not positive
        """
        # Input validation
        if timeout <= 0:
            raise ValueError(_ERROR_TIMEOUT_POSITIVE.format(timeout=timeout))

        if not self._running:
            self.logger.debug(_LOG_SHUTDOWN_NOT_RUNNING)
            return

        self.logger.info(_LOG_SHUTDOWN_INITIATING)

        try:
            # Close all client connections gracefully
            if self.clients:
                self.logger.info(_LOG_SHUTDOWN_CLOSING_CLIENTS.format(count=len(self.clients)))

                # Create a copy to avoid modification during iteration
                clients_copy = self.clients.copy()

                for client in clients_copy:
                    try:
                        # Send shutdown notification
                        await client.send(json.dumps({
                            _KEY_EVENT: _EVENT_SERVER_SHUTDOWN,
                            _KEY_MESSAGE: _MSG_SERVER_SHUTDOWN
                        }))
                        # Close connection
                        await client.close()
                        self.logger.debug(_LOG_SHUTDOWN_CLIENT_CLOSED)
                    except Exception as e:
                        # Use DRY helper for zTraceback integration
                        self._log_with_traceback(e, _ERROR_CLOSING_CLIENT, {'client': str(client)})

                # Clear the clients set
                self.clients.clear()
                self.auth.authenticated_clients.clear()
                # Phase 1: Clear connection indices
                self.user_connections.clear()
                self.connection_users.clear()

            # Close the server
            if self.server:
                try:
                    self.logger.info(_LOG_SHUTDOWN_CLOSING_SERVER)
                    self.server.close()

                    # Wait for server to close with timeout
                    await asyncio.wait_for(self.server.wait_closed(), timeout=timeout)

                    self.logger.info(_LOG_SHUTDOWN_SUCCESS)
                except asyncio.TimeoutError:
                    self.logger.warning(_LOG_SHUTDOWN_TIMEOUT.format(timeout=timeout))
                except Exception as e:
                    # Use DRY helper for zTraceback integration
                    self._log_with_traceback(e, _ERROR_SHUTDOWN)
                finally:
                    self.server = None

        finally:
            # Always mark as not running after shutdown attempt
            self._running = False
            self._start_time = None  # Clear start time on shutdown
            self.logger.info(_LOG_SHUTDOWN_COMPLETE)

    def _sync_shutdown(self) -> None:
        """
        Synchronous shutdown for when event loop is already running.
        
        This is called from zOS.shutdown() when the event loop is active
        and we can't use async/await. Does minimal cleanup to free the port.
        
        Note: This skips sending shutdown notifications to clients and just
        forcefully closes connections and releases the port.
        """
        if not self._running:
            return

        self.logger.info(_LOG_SYNC_SHUTDOWN)

        try:
            # Clear client lists (no async send needed)
            if self.clients:
                self.logger.info(_LOG_SYNC_FORCE_CLOSING.format(count=len(self.clients)))
                self.clients.clear()
                self.auth.authenticated_clients.clear()
                # Phase 1: Clear connection indices
                self.user_connections.clear()
                self.connection_users.clear()

            # Close server synchronously
            if self.server:
                try:
                    self.server.close()
                    self.logger.info(_LOG_SYNC_CLOSED)
                except Exception as e:
                    self.logger.warning(_LOG_SYNC_ERROR.format(error=e))
                finally:
                    self.server = None

        finally:
            self._running = False
            self.logger.info(_LOG_SYNC_COMPLETE)
