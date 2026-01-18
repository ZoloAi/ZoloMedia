# zCLI/subsystems/zComm/zComm_modules/comm_websocket.py
"""
WebSocket Server Primitives for zComm (Layer 0).

Provides low-level WebSocket server infrastructure - protocol, connections,
send/broadcast primitives. Used by zBifrost (Layer 2) for orchestration.

Architecture:
    Layer 0 (zComm): Raw WebSocket server infrastructure
    Layer 2 (zBifrost): Orchestration (display/auth/data coordination)
"""

from zOS import (
    asyncio, Any, Optional, Dict, Callable,
    ws_serve, WebSocketServerProtocol, logging
)
from typing import Set
from .comm_websocket_auth import WebSocketAuth
from .comm_ssl import create_ssl_context

# Module Constants

_LOG_PREFIX = "[WebSocketServer]"
_LOG_STARTED = f"{_LOG_PREFIX} Server started at {{protocol}}://{{host}}:{{port}}"
_LOG_CLIENT_CONNECTED = f"{_LOG_PREFIX} Client connected: {{client_addr}}"
_LOG_CLIENT_DISCONNECTED = f"{_LOG_PREFIX} Client disconnected: {{client_addr}}"
_LOG_BROADCAST = f"{_LOG_PREFIX} Broadcasting to {{count}} client(s)"
_LOG_SHUTDOWN = f"{_LOG_PREFIX} Shutting down..."
_LOG_SHUTDOWN_COMPLETE = f"{_LOG_PREFIX} Shutdown complete"


class WebSocketHandshakeFilter(logging.Filter):
    """
    Filter out benign handshake failures from websockets library (v1.5.10).
    
    The "zolo way": Graceful handling of noise we can't control.
    
    Context:
        External port probes, health checks, and network tools often connect
        to WebSocket ports and close immediately without sending HTTP headers.
        This causes the websockets library to log handshake errors that are
        actually benign - they're not bugs in our code, just normal network noise.
    
    Architecture:
        - Filters out "line without CRLF" errors (connection closed before sending data)
        - Filters out "did not receive a valid HTTP request" (invalid HTTP)
        - Keeps real WebSocket connection issues visible
        - Applied only to the 'websockets' logger (doesn't affect zCLI logging)
    
    Philosophy:
        We handle what we can (process_request for proper HTTP),
        and suppress what we can't (TCP connections that close immediately).
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record - return False to suppress, True to keep.
        
        Args:
            record: Log record from websockets library
            
        Returns:
            False if this is benign noise, True if it's a real issue
        """
        message = record.getMessage()
        
        # Suppress "line without CRLF" - connection closed before sending data
        if "line without CRLF" in message:
            return False
        
        # Suppress "did not receive a valid HTTP request" - port probe / health check
        if "did not receive a valid HTTP request" in message:
            return False
        
        # Suppress "opening handshake failed" - redundant header for above errors
        if "opening handshake failed" in message:
            return False
        
        # Suppress "connection closed while reading HTTP request line"
        if "connection closed while reading HTTP request line" in message:
            return False
        
        # Keep everything else (real WebSocket errors, connection issues, etc.)
        return True


class WebSocketServer:
    """
    Low-level WebSocket server primitives for zComm.
    
    Provides basic server infrastructure:
    - Create WebSocket server
    - Track connected clients
    - Send to specific client
    - Broadcast to all clients
    - Clean shutdown
    
    This is Layer 0 infrastructure. For orchestration with display/auth/data,
    see zBifrost (Layer 2).
    """
    
    def __init__(self, logger: Any, config: Any) -> None:
        """
        Initialize WebSocket server with logger and config.
        
        Args:
            logger: Logger instance (from zCLI)
            config: WebSocketConfig instance from zConfig (provides host/port defaults)
        """
        self.logger = logger
        self.config = config  # zConfig WebSocketConfig instance
        self.auth = WebSocketAuth(config, logger)  # Authentication primitive
        self.server: Optional[Any] = None
        self.clients: Set[WebSocketServerProtocol] = set()
        self.handler: Optional[Callable] = None
        self._running = False
        
        # Configure websockets library logger (v1.5.10: Graceful handshake error handling)
        # The "zolo way": Filter benign noise (port probes) while keeping real errors visible
        ws_logger = logging.getLogger('websockets')
        ws_logger.addFilter(WebSocketHandshakeFilter())
        ws_logger.setLevel(logging.CRITICAL)  # Only show critical errors, not handshake noise
    
    def _create_ssl_context(self) -> Optional['ssl.SSLContext']:
        """
        Create SSL context from config if SSL is enabled.
        
        Delegates to zComm Layer 0 primitive for consistent SSL handling.
        
        Returns:
            ssl.SSLContext if SSL enabled and configured, None otherwise
        """
        return create_ssl_context(
            ssl_enabled=self.config.ssl_enabled,
            ssl_cert=self.config.ssl_cert,
            ssl_key=self.config.ssl_key,
            logger=self.logger,
            log_prefix=_LOG_PREFIX
        )
    
    async def _process_request(self, path: str, request_headers: Any) -> Optional[tuple]:
        """
        Process incoming requests before WebSocket handshake (v1.5.10).
        
        Gracefully rejects non-WebSocket connections (health checks, port probes).
        This prevents handshake errors from cluttering logs - the "zolo way".
        
        Architecture:
            - Intercepts connections at the HTTP layer (before WebSocket upgrade)
            - Validates WebSocket upgrade headers
            - Returns clean HTTP 400 for invalid requests
            - Allows valid WebSocket connections to proceed
        
        Args:
            path: Request path
            request_headers: HTTP request headers
            
        Returns:
            None to allow connection, or (status, headers, body) to reject
            
        Example rejection:
            Port probe → HTTP 400 "WebSocket connection required"
            Valid WS → None (proceed with handshake)
        
        Note:
            This eliminates "opening handshake failed" noise by handling
            the root cause (invalid connections) rather than symptoms.
        """
        # Check if it looks like a valid WebSocket upgrade request
        upgrade = request_headers.get("Upgrade", "").lower()
        connection = request_headers.get("Connection", "").lower()
        
        if "websocket" not in upgrade or "upgrade" not in connection:
            # This is a port probe, health check, or non-WebSocket HTTP request
            # Reject gracefully with HTTP 400 (no handshake error logged)
            self.logger.framework.debug(
                f"{_LOG_PREFIX} Rejected non-WebSocket request from {path} "
                f"(Upgrade: {upgrade or 'none'}, Connection: {connection or 'none'})"
            )
            return (400, [], b"WebSocket connection required\n")
        
        # Valid WebSocket upgrade request - allow handshake to proceed
        return None
    
    def _custom_exception_handler(self, loop: Any, context: Dict[str, Any]) -> None:
        """
        Custom asyncio exception handler for graceful WebSocket error handling (v1.5.10).
        
        The "zolo way": Suppress benign handshake failures while logging real issues.
        
        Context:
            The websockets library raises exceptions for port probes and incomplete
            connections. These get caught by asyncio's default exception handler,
            which prints full tracebacks. We intercept these to suppress the noise
            while keeping visibility into actual problems.
        
        Args:
            loop: Asyncio event loop
            context: Exception context dict with 'message', 'exception', etc.
        """
        exception = context.get('exception')
        message = context.get('message', '')
        
        # Suppress benign websocket handshake errors (port probes)
        if exception:
            exception_str = str(exception)
            if any(phrase in exception_str for phrase in [
                'did not receive a valid HTTP request',
                'line without CRLF',
                'connection closed while reading HTTP request line'
            ]):
                # This is a port probe or incomplete connection - suppress traceback
                self.logger.framework.debug(
                    f"{_LOG_PREFIX} Suppressed benign handshake error: {exception_str[:100]}"
                )
                return
        
        # For all other exceptions, log them properly (real errors)
        self.logger.error(f"{_LOG_PREFIX} Asyncio exception: {message}")
        if exception:
            self.logger.error(f"{_LOG_PREFIX} Exception details: {exception}")
    
    async def start_async(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        handler: Optional[Callable] = None
    ) -> None:
        """
        Start WebSocket server (async version for advanced usage).
        
        Uses zConfig defaults if not specified (respects 5-layer hierarchy).
        
        Args:
            host: Host address (default: from zConfig.websocket.host)
            port: Port number (default: from zConfig.websocket.port)
            handler: Optional custom message handler
        """
        # Fall back to zConfig if not explicitly provided
        actual_host = host if host is not None else self.config.host
        actual_port = port if port is not None else self.config.port
        
        self.handler = handler or self._default_handler
        
        # Create SSL context if enabled
        ssl_context = self._create_ssl_context()
        protocol = "wss" if ssl_context else "ws"
        
        # Set custom exception handler for graceful error handling (v1.5.10)
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self._custom_exception_handler)
        
        try:
            self.server = await ws_serve(
                self._handle_client, 
                actual_host, 
                actual_port,
                ssl=ssl_context,
                process_request=self._process_request  # v1.5.10: Graceful handshake error handling
            )
            self._running = True
            self.logger.info(_LOG_STARTED.format(protocol=protocol, host=actual_host, port=actual_port))
            await self.server.wait_closed()
        except OSError as e:
            self.logger.error(f"{_LOG_PREFIX} Failed to start: {e}")
            raise
        finally:
            self._running = False
    
    def start(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        handler: Optional[Callable] = None
    ) -> None:
        """
        Start WebSocket server (blocks until Ctrl+C).
        
        Uses zConfig defaults if not specified (respects 5-layer hierarchy).
        zCLI handles asyncio and graceful shutdown internally.
        Press Ctrl+C to stop cleanly.
        
        Args:
            host: Host address (default: from zConfig.websocket.host)
            port: Port number (default: from zConfig.websocket.port)
            handler: Optional custom message handler
        """
        import asyncio
        
        async def _run_with_cleanup():
            """Run server with graceful shutdown handling."""
            try:
                await self.start_async(host, port, handler)
            except KeyboardInterrupt:
                await self.shutdown()
        
        try:
            asyncio.run(_run_with_cleanup())
        except KeyboardInterrupt:
            pass  # Clean exit
    
    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """
        Handle individual client connection with authentication.
        
        Args:
            websocket: Client WebSocket connection
        """
        client_addr = websocket.remote_address
        
        # ═══════════════════════════════════════════════════════
        # Security Validation (if require_auth enabled)
        # ═══════════════════════════════════════════════════════
        if self.config.require_auth:
            # 1. Check connection limit
            if not self.auth.check_connection_limit():
                await websocket.close(code=1008, reason="Maximum connections reached")
                return
            
            # 2. Validate origin (CORS/CSRF protection)
            if not self.auth.validate_origin(websocket):
                await websocket.close(code=1008, reason="Invalid origin")
                return
            
            # 3. Validate token
            token = self.auth.extract_token(websocket)
            if not token:
                self.logger.warning(f"{_LOG_PREFIX} Missing token from {client_addr}")
                await websocket.close(code=1008, reason="Authentication required")
                return
            
            if not self.auth.validate_token(token):
                self.logger.warning(f"{_LOG_PREFIX} Invalid token from {client_addr}")
                await websocket.close(code=1008, reason="Invalid token")
                return
            
            # Register authenticated client
            self.auth.register_client(websocket, {"token": token, "addr": client_addr})
        
        # ═══════════════════════════════════════════════════════
        # Accept Client Connection
        # ═══════════════════════════════════════════════════════
        self.clients.add(websocket)
        self.logger.info(_LOG_CLIENT_CONNECTED.format(client_addr=client_addr))
        
        try:
            async for message in websocket:
                if self.handler:
                    await self.handler(websocket, message)
        except Exception as e:
            self.logger.error(f"{_LOG_PREFIX} Client error: {e}")
        finally:
            self.clients.discard(websocket)
            if self.config.require_auth:
                self.auth.unregister_client(websocket)
            self.logger.info(_LOG_CLIENT_DISCONNECTED.format(client_addr=client_addr))
    
    async def _default_handler(
        self,
        websocket: WebSocketServerProtocol,
        message: str
    ) -> None:
        """
        Default message handler (echo).
        
        Args:
            websocket: Client connection
            message: Received message
        """
        await websocket.send(f"Echo: {message}")
    
    async def send(self, client: WebSocketServerProtocol, message: str) -> bool:
        """
        Send message to specific client.
        
        Args:
            client: Target client connection
            message: Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            await client.send(message)
            return True
        except Exception as e:
            self.logger.error(f"{_LOG_PREFIX} Send failed: {e}")
            return False
    
    async def broadcast(self, message: str, exclude: Optional[WebSocketServerProtocol] = None) -> int:
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude: Optional client to exclude from broadcast
            
        Returns:
            int: Number of clients message was sent to
        """
        disconnected = set()
        sent_count = 0
        
        for client in self.clients:
            if client == exclude:
                continue
                
            try:
                await client.send(message)
                sent_count += 1
            except Exception:
                disconnected.add(client)
        
        # Clean up disconnected clients
        self.clients.difference_update(disconnected)
        
        if sent_count > 0:
            self.logger.debug(_LOG_BROADCAST.format(count=sent_count))
        
        return sent_count
    
    async def shutdown(self) -> None:
        """Gracefully shutdown server and close all connections."""
        self.logger.info(_LOG_SHUTDOWN)
        
        # Close all client connections
        for client in list(self.clients):
            try:
                await client.close()
            except Exception:
                pass
        
        self.clients.clear()
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self._running = False
        self.logger.info(_LOG_SHUTDOWN_COMPLETE)
    
    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
    
    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)

