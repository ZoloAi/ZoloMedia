# zCLI/subsystems/zBifrost/zBifrost_modules/bridge_orchestrator.py
"""
zBifrost WebSocket Bridge Orchestrator (Layer 2)

Orchestrates Terminal↔Web communication by coordinating zCLI subsystems
over WebSocket infrastructure. Manages server lifecycle, client connections,
and message routing between display/auth/data subsystems.

Architecture:
    - Uses z.comm for low-level WebSocket server infrastructure
    - Coordinates z.display for rendering events to web clients
    - Integrates z.auth for three-tier client authentication
    - Manages z.data for CRUD operations from web UI
"""

from zOS import Any, Optional, Callable
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    SESSION_KEY_ZMODE,
    ZMODE_TERMINAL,
    ZMODE_ZBIFROST
)
from .bifrost.server.bifrost_bridge import zBifrost

# ═══════════════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════════════

_LOG_PREFIX = "[zBifrost]"

# Default Configuration
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 56891
_MSG_PREVIEW_LENGTH = 100
_MSG_TRUNCATION_SUFFIX = "..."

# Port Validation
_PORT_MIN = 1
_PORT_MAX = 65535

# Log Messages - Auto-start
_LOG_DETECTED_ZBIFROST_MODE = "zBifrost mode detected - initializing WebSocket bridge"
_LOG_INSTANCE_CREATED_ZBIFROST = "WebSocket bridge instance created for zBifrost mode"
_LOG_DETECTED_TERMINAL_MODE = "Terminal mode detected - WebSocket bridge will be created when needed"

# Log Messages - Create
_LOG_CREATING_FROM_CONFIG = "Creating WebSocket bridge from zCLI config: %s:%d"
_LOG_CREATING_WITH_DEFAULTS = "Creating WebSocket bridge with defaults: %s:%d"
_LOG_CONFIG_DEBUG = "Bridge config - walker=%s, port=%d, host=%s"
_LOG_INSTANCE_CREATED_SUCCESS = "WebSocket bridge instance created successfully"

# Log Messages - Start
_LOG_STARTING_SERVER = "Starting WebSocket bridge..."
_LOG_CREATING_INSTANCE = "Creating bridge instance with current configuration"
_LOG_CALLING_START = "Calling start_socket_server with socket_ready callback"
_LOG_STARTED_SUCCESS = "WebSocket bridge started successfully"

# Log Messages - Broadcast
_LOG_BROADCASTING = "Broadcasting message from sender: %s"
_LOG_MESSAGE_CONTENT = "Message content: %s"
_LOG_BROADCAST_COMPLETED = "Broadcast completed"

# Warning Messages
_WARN_AUTO_START_FAILED = "Failed to auto-start WebSocket bridge: %s"
_WARN_NO_WEBSOCKET_INSTANCE = "Cannot broadcast - no WebSocket bridge instance available"

# Error Messages
_ERROR_ZCLI_NONE = "zcli parameter cannot be None"
_ERROR_LOGGER_NONE = "logger parameter cannot be None"
_ERROR_SESSION_NONE = "session parameter cannot be None"
_ERROR_SOCKET_READY_REQUIRED = "socket_ready event is required"
_ERROR_INVALID_PORT = "Port must be an integer between {min} and {max}, got: {port}"

class BridgeOrchestrator:
    """
    Layer 2 orchestrator for Terminal↔Web WebSocket bridge.
    
    Manages WebSocket server lifecycle and coordinates zCLI subsystems
    (display, auth, data) for real-time web communication.
    
    Attributes:
        zcli: zCLI instance
        logger: Logger instance
        session: Session dict from zCLI
        websocket: WebSocket bridge instance (None until created)
    """

    def __init__(self, zcli: Any, logger: Any, session: dict) -> None:
        """
        Initialize Bridge Orchestrator.
        
        Args:
            zcli: zCLI instance (required)
            logger: Logger instance (required)
            session: Session dict from zCLI (required)
            
        Raises:
            ValueError: If zcli, logger, or session is None
        """
        if zcli is None:
            raise ValueError(_ERROR_ZCLI_NONE)
        if logger is None:
            raise ValueError(_ERROR_LOGGER_NONE)
        if session is None:
            raise ValueError(_ERROR_SESSION_NONE)

        self.zcli = zcli
        self.logger = logger
        self.session = session
        self.websocket: Optional[Any] = None

    def auto_start(self) -> None:
        """
        Auto-start WebSocket bridge if in zBifrost mode.
        
        Checks session zMode and initializes WebSocket bridge if needed.
        
        Raises:
            KeyError: If session access fails
            AttributeError: If config access fails
        """
        try:
            # Check the actual zMode setting (not inferred from filename)
            zmode = self.session.get(SESSION_KEY_ZMODE, ZMODE_TERMINAL)
            is_zbifrost_mode = zmode == ZMODE_ZBIFROST

            if is_zbifrost_mode:
                self.logger.info(f"{_LOG_PREFIX} {_LOG_DETECTED_ZBIFROST_MODE}")
                self.create(walker=None)
                self.logger.debug(f"{_LOG_PREFIX} {_LOG_INSTANCE_CREATED_ZBIFROST}")
                
                # Auto-start the WebSocket server in background thread
                if self.websocket:
                    import threading
                    import asyncio
                    
                    def run_websocket():
                        socket_ready = threading.Event()
                        asyncio.run(self.websocket.start_socket_server(socket_ready))
                    
                    ws_thread = threading.Thread(target=run_websocket, daemon=True, name="zBifrost-WebSocket")
                    ws_thread.start()
                    self.logger.info(f"{_LOG_PREFIX} WebSocket server started in background thread")
            else:
                self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_DETECTED_TERMINAL_MODE}")
        except (KeyError, AttributeError) as e:
            self.logger.warning(f"{_LOG_PREFIX} {_WARN_AUTO_START_FAILED}", e)

    def create(
        self,
        walker: Optional[Any] = None,
        port: Optional[int] = None,
        host: Optional[str] = None
    ) -> Any:
        """
        Create WebSocket bridge instance using zCLI configuration.
        
        Args:
            walker: Optional walker instance
            port: Optional port override (1-65535)
            host: Optional host override
            
        Returns:
            WebSocket bridge instance
            
        Raises:
            ValueError: If port is outside valid range
        """
        # Validate port if provided
        if port is not None:
            if not isinstance(port, int) or port < _PORT_MIN or port > _PORT_MAX:
                raise ValueError(_ERROR_INVALID_PORT.format(min=_PORT_MIN, max=_PORT_MAX, port=port))

        # Use zCLI config if available, otherwise use provided parameters or defaults
        try:
            config_host = host or self.zcli.config.websocket.host
            config_port = port or self.zcli.config.websocket.port
            self.logger.info(f"{_LOG_PREFIX} {_LOG_CREATING_FROM_CONFIG}", config_host, config_port)
        except (AttributeError, KeyError):
            config_host = host or _DEFAULT_HOST
            config_port = port or _DEFAULT_PORT
            self.logger.info(f"{_LOG_PREFIX} {_LOG_CREATING_WITH_DEFAULTS}", config_host, config_port)

        self.logger.debug(
            f"{_LOG_PREFIX} {_LOG_CONFIG_DEBUG}",
            walker is not None,
            config_port,
            config_host
        )

        self.websocket = zBifrost(
            self.logger,
            walker=walker,
            zcli=self.zcli,
            port=config_port,
            host=config_host
        )

        self.logger.info(f"{_LOG_PREFIX} {_LOG_INSTANCE_CREATED_SUCCESS}")
        return self.websocket

    async def start(self, socket_ready: Any, walker: Optional[Any] = None) -> None:
        """
        Start WebSocket bridge.
        
        Args:
            socket_ready: asyncio.Event to signal when server is ready (required)
            walker: Optional walker instance
            
        Raises:
            ValueError: If socket_ready is None
        """
        if socket_ready is None:
            raise ValueError(_ERROR_SOCKET_READY_REQUIRED)

        self.logger.info(f"{_LOG_PREFIX} {_LOG_STARTING_SERVER}")

        # Always create a new instance to ensure we have the latest config
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_CREATING_INSTANCE}")
        self.websocket = self.create(walker=walker)

        self.logger.debug(f"{_LOG_PREFIX} {_LOG_CALLING_START}")
        await self.websocket.start_socket_server(socket_ready)
        self.logger.info(f"{_LOG_PREFIX} {_LOG_STARTED_SUCCESS}")

    async def broadcast(self, message: Any, sender: Optional[str] = None) -> None:
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
            sender: Optional sender identifier
        """
        if self.websocket:
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_BROADCASTING}", sender)
            msg_str = str(message)
            if len(msg_str) > _MSG_PREVIEW_LENGTH:
                msg_preview = msg_str[:_MSG_PREVIEW_LENGTH] + _MSG_TRUNCATION_SUFFIX
            else:
                msg_preview = msg_str
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_MESSAGE_CONTENT}", msg_preview)
            await self.websocket.broadcast(message, sender=sender)
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_BROADCAST_COMPLETED}")
        else:
            self.logger.warning(f"{_LOG_PREFIX} {_WARN_NO_WEBSOCKET_INSTANCE}")
