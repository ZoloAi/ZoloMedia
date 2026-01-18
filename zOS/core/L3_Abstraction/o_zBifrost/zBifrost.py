# zCLI/subsystems/zBifrost/zBifrost.py
"""
zBifrost - Terminal↔Web Bridge Orchestrator (Layer 2)

Coordinates Terminal↔Web communication by orchestrating zCLI subsystems:
- zDisplay: Broadcasts render events to web clients
- zAuth: Three-tier authentication for WebSocket clients
- zData: Handles CRUD operations from web UI
- zComm: Uses low-level WebSocket infrastructure

Initialized in Layer 2 (after zData, before zShell).

Architecture:
    Terminal Python App
           ↓
        zBifrost (Layer 2 Orchestrator)
           ↓
        z.comm WebSocket (Layer 0 Infrastructure)
           ↓
        WebSocket Protocol
           ↓
        JavaScript Client (Browser)

Usage:
    ```python
    from zOS import zOS
    
    # Initialize zCLI (zBifrost auto-initializes)
    z = zCLI()
    
    # Start WebSocket bridge
    z.bifrost.start()
    
    # Broadcast event to all clients
    z.bifrost.broadcast({"event": "update", "data": {...}})
    
    # Check health
    status = z.bifrost.health_check()
    ```

Auto-Start:
    If session zMode is "zBifrost", the bridge auto-starts during initialization.
"""

from zOS import Any, Optional
from .zBifrost_modules.bridge_orchestrator import BridgeOrchestrator

# Module Constants
_LOG_PREFIX = "[zBifrost]"
_LOG_INIT = "zBifrost orchestrator initialized (Layer 2)"
_LOG_AUTO_START = "Auto-starting WebSocket bridge (zMode: zBifrost)"
_LOG_READY = "zBifrost WebSocket bridge ready"

class zBifrost:
    """
    Layer 2 WebSocket bridge orchestrator.
    
    Coordinates display/auth/data subsystems over WebSocket infrastructure,
    enabling Terminal→Web GUI transformation.
    
    Attributes:
        zcli: zCLI instance
        logger: Logger instance
        orchestrator: BridgeOrchestrator instance
    """
    
    def __init__(self, zcli: Any) -> None:
        """
        Initialize zBifrost orchestrator.
        
        Args:
            zcli: zCLI instance (must have comm, display, auth, data initialized)
            
        Raises:
            ValueError: If zcli is None or missing required subsystems
        """
        if zcli is None:
            raise ValueError("zcli parameter cannot be None")
        
        # Validate required subsystems are initialized
        required_subsystems = ['comm', 'display', 'auth', 'data', 'logger', 'session']
        missing = [s for s in required_subsystems if not hasattr(zcli, s)]
        if missing:
            raise ValueError(f"zCLI missing required subsystems for zBifrost: {', '.join(missing)}")
        
        self.zcli = zcli
        self.logger = zcli.logger
        
        self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_INIT}")
        
        # Initialize orchestrator with all required subsystems
        self.orchestrator = BridgeOrchestrator(
            zcli=zcli,
            logger=self.logger,
            session=zcli.session
        )
        
        # Auto-start if in zBifrost mode
        self._auto_start()
        
        self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_READY}")
    
    def _auto_start(self) -> None:
        """
        Auto-start WebSocket bridge if session zMode is 'zBifrost'.
        
        Reads session['zMode'] and starts the bridge if mode is 'zBifrost'.
        In Terminal mode, bridge remains dormant until explicitly started.
        """
        zmode = self.zcli.session.get('zMode', 'Terminal')
        if zmode == 'zBifrost':
            self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_AUTO_START}")
            self.orchestrator.auto_start()
    
    @property
    def server(self) -> Optional[Any]:
        """
        Get WebSocket server instance (from orchestrator).
        
        Returns:
            WebSocket server instance or None if not started
        """
        return self.orchestrator.websocket
    
    def start(self, socket_ready: Optional[Any] = None) -> None:
        """
        Start WebSocket bridge explicitly.
        
        Args:
            socket_ready: Optional threading.Event for socket ready notification
        """
        self.orchestrator.start(socket_ready=socket_ready)
    
    def stop(self) -> None:
        """
        Stop WebSocket bridge gracefully.
        
        Closes all client connections and shuts down the server.
        Uses asyncio to run the async shutdown method.
        """
        if self.orchestrator.websocket:
            self.logger.info(f"{_LOG_PREFIX} Stopping WebSocket bridge")
            import asyncio
            try:
                # Run async shutdown in sync context
                asyncio.run(self.orchestrator.websocket.shutdown())
                self.logger.info(f"{_LOG_PREFIX} WebSocket bridge stopped successfully")
            except Exception as e:
                self.logger.error(f"{_LOG_PREFIX} Error stopping WebSocket bridge: {e}")
        else:
            self.logger.warning(f"{_LOG_PREFIX} Cannot stop - WebSocket bridge not running")
    
    def broadcast(self, message: dict, sender: str = "system") -> None:
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Dict with event data to broadcast
            sender: Optional sender identifier (default: "system")
        """
        self.orchestrator.broadcast(message, sender=sender)
    
    def health_check(self) -> dict:
        """
        Get health status of WebSocket bridge.
        
        Returns:
            Dict with:
                - running: bool (is server running)
                - host: str (server host address)
                - port: int (server port)
                - url: str|None (WebSocket URL, None if not running)
                - clients: int (number of connected clients)
                - authenticated_clients: int (number of authenticated clients)
                - require_auth: bool (whether authentication is required)
                - uptime: float (seconds since server start, 0.0 if not running)
        
        Note:
            If WebSocket bridge is not initialized, returns minimal status dict.
        """
        if self.orchestrator.websocket:
            # Delegate to WebSocket bridge's comprehensive health check
            return self.orchestrator.websocket.health_check()
        else:
            # Return minimal status if bridge not initialized
            return {
                "running": False,
                "host": "N/A",
                "port": 0,
                "url": None,
                "clients": 0,
                "authenticated_clients": 0,
                "require_auth": False,
                "uptime": 0.0
            }

