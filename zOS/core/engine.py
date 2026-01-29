# zCLI/zCLI.py — Core zCLI Engine
# ═══════════════════════════════════════════════════════════════════════════════
"""
zCLI Core Engine - Top-Level Orchestrator

4-Layer Architecture (bottom-up):
    Layer 0: Foundation       → zConfig, zComm
    Layer 1: Core (9)         → zDisplay, zAuth, zDispatch, zNavigation, zParser, zLoader, zFunc, zDialog, zOpen
    Layer 2: Abstraction (4)  → zUtils, zWizard, zData, zShell
    Layer 3: Orchestration    → zWalker

Thread-safe via contextvars.ContextVar. Supports Terminal and zBifrost (WebSocket) modes.
Graceful shutdown via SIGINT/SIGTERM handlers (reverse initialization order).
"""

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS (Centralized from __init__.py per IMPORT_CENTRALIZATION_RULES.md)
# ═══════════════════════════════════════════════════════════════════════════════

from . import Any, Dict, Optional, contextvars, logging, signal, sys
from zSys.errors import ExceptionContext

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Session Keys (4) - Used in session dict
# ─────────────────────────────────────────────────────────────────────────────
SESSION_KEY_ZS_ID: str = "zS_id"
SESSION_KEY_ZMODE: str = "zMode"
SESSION_KEY_ZMACHINE: str = "zMachine"
SESSION_KEY_ZSPARK: str = "zSpark_obj"

# ─────────────────────────────────────────────────────────────────────────────
# Mode Constants (3) - zMode values
# ─────────────────────────────────────────────────────────────────────────────
MODE_TERMINAL: str = "Terminal"
MODE_ZBIFROST: str = "zBifrost"
MODE_WALKER: str = "Walker"

# ─────────────────────────────────────────────────────────────────────────────
# Signal Names (2) - For signal handler logging
# ─────────────────────────────────────────────────────────────────────────────
SIGNAL_INT: str = "SIGINT"
SIGNAL_TERM: str = "SIGTERM"

# ─────────────────────────────────────────────────────────────────────────────
# Shutdown Component Keys (4) - For status tracking dict
# ─────────────────────────────────────────────────────────────────────────────
SHUTDOWN_WEBSOCKET: str = "websocket"
SHUTDOWN_HTTP_SERVER: str = "http_server"
SHUTDOWN_DATABASE: str = "database"
SHUTDOWN_LOGGER: str = "logger"

# ─────────────────────────────────────────────────────────────────────────────
# Shutdown Status Symbols (2) - For status display
# ─────────────────────────────────────────────────────────────────────────────
SHUTDOWN_STATUS_SUCCESS: str = "✓"
SHUTDOWN_STATUS_FAIL: str = "✗"

# ─────────────────────────────────────────────────────────────────────────────
# Logger Messages - Info (10)
# ─────────────────────────────────────────────────────────────────────────────
LOG_INIT_COMPLETE: str = "zCLI Core initialized - Mode: %s"
LOG_MODE_TERMINAL: str = "Starting zCLI in Terminal mode..."
LOG_MODE_ZBIFROST: str = "Starting zCLI in zBifrost mode via zWalker..."
LOG_HTTP_START: str = "HTTP server auto-started at %s"
LOG_SESSION_INIT: str = "Session initialized:"
LOG_SESSION_ID_PREFIX: str = "  zS_id: %s"
LOG_SESSION_MODE_PREFIX: str = "  zMode: %s"
LOG_SESSION_MACHINE_PREFIX: str = "  zMachine hostname: %s"
LOG_SHUTDOWN_START: str = "[Shutdown] Initiating graceful shutdown..."
LOG_SHUTDOWN_COMPLETE: str = "[Shutdown] Graceful shutdown complete"

# ─────────────────────────────────────────────────────────────────────────────
# Logger Messages - Warning (5)
# ─────────────────────────────────────────────────────────────────────────────
LOG_WARN_PLUGIN_FAIL: str = "Failed to load plugins: %s"
LOG_WARN_SHUTDOWN_IN_PROGRESS: str = "[Shutdown] Shutdown already in progress"
LOG_WARN_WEBSOCKET_ERROR: str = "[Shutdown] WebSocket cleanup error: %s"
LOG_WARN_SIGNAL_DUPLICATE: str = "[%s] Shutdown already in progress..."
LOG_WARN_ASYNC_SHUTDOWN_SKIPPED: str = "[Shutdown] Async shutdown skipped (loop running)"

# ─────────────────────────────────────────────────────────────────────────────
# Logger Messages - Debug (9)
# ─────────────────────────────────────────────────────────────────────────────
LOG_DEBUG_SESSION_ID: str = "  zS_id: %s"
LOG_DEBUG_SESSION_MODE: str = "  zMode: %s"
LOG_DEBUG_SESSION_MACHINE: str = "  zMachine hostname: %s"
LOG_DEBUG_SIGNAL_HANDLERS: str = "Signal handlers registered (SIGINT, SIGTERM)"
LOG_DEBUG_WEBSOCKET_NOT_RUNNING: str = "[Shutdown] WebSocket server not running"
LOG_DEBUG_WEBSOCKET_NOT_INIT: str = "[Shutdown] WebSocket server not initialized"
LOG_DEBUG_HTTP_NOT_RUNNING: str = "[Shutdown] HTTP server not running"
LOG_DEBUG_HTTP_NOT_INIT: str = "[Shutdown] HTTP server not initialized"
LOG_DEBUG_DB_NOT_CONNECTED: str = "[Shutdown] No active database connections"
LOG_DEBUG_DB_NOT_INIT: str = "[Shutdown] Database subsystem not initialized"

# ─────────────────────────────────────────────────────────────────────────────
# Shutdown Messages (6)
# ─────────────────────────────────────────────────────────────────────────────
SHUTDOWN_MSG_WEBSOCKET_CLOSE: str = "[Shutdown] Closing WebSocket server..."
SHUTDOWN_MSG_HTTP_STOP: str = "[Shutdown] Stopping HTTP server..."
SHUTDOWN_MSG_DB_CLOSE: str = "[Shutdown] Closing database connections..."
SHUTDOWN_MSG_LOGGER_FLUSH: str = "[Shutdown] Flushing logger..."
SHUTDOWN_MSG_STATUS_REPORT: str = "[Shutdown] Cleanup Status:"
SHUTDOWN_MSG_COMPONENT_STATUS: str = "  %s %s"

# ─────────────────────────────────────────────────────────────────────────────
# Shutdown Separators (2)
# ─────────────────────────────────────────────────────────────────────────────
SHUTDOWN_SEPARATOR: str = "=" * 70
SHUTDOWN_OPERATION_PREFIX: str = "[Shutdown]"

# ─────────────────────────────────────────────────────────────────────────────
# Error Messages (6)
# ─────────────────────────────────────────────────────────────────────────────
ERROR_SHUTDOWN_SIGNAL: str = "Error during %s shutdown"
ERROR_WEBSOCKET_SHUTDOWN: str = "WebSocket shutdown"
ERROR_HTTP_SHUTDOWN: str = "HTTP server shutdown"
ERROR_DB_SHUTDOWN: str = "Database connection cleanup"
ERROR_LOGGER_SHUTDOWN: str = "Logger cleanup"
ERROR_SIGNAL_RECEIVED: str = "[%s] Received shutdown signal"

# ─────────────────────────────────────────────────────────────────────────────
# Layer Names (4) - For architecture documentation
# ─────────────────────────────────────────────────────────────────────────────
LAYER_0_FOUNDATION: str = "Layer 0: Foundation"
LAYER_1_CORE: str = "Layer 1: Core Subsystems"
LAYER_2_ABSTRACTION: str = "Layer 2: Core Abstraction"
LAYER_3_ORCHESTRATION: str = "Layer 3: Orchestration"

# ─────────────────────────────────────────────────────────────────────────────
# Plugin Config Keys (1)
# ─────────────────────────────────────────────────────────────────────────────
ZSPARK_PLUGINS_KEY: str = "plugins"

# ─────────────────────────────────────────────────────────────────────────────
# Context Variable Name (1)
# ─────────────────────────────────────────────────────────────────────────────
CONTEXT_VAR_NAME: str = "current_zcli"

# Global context variable for current zCLI instance (thread-safe, async-safe)
# Follows Django/Flask/FastAPI pattern for request/application context
_current_zos: contextvars.ContextVar = contextvars.ContextVar(CONTEXT_VAR_NAME, default=None)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API - Context Access
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_zos() -> Optional['zCLI']:
    """
    Get current zCLI instance from thread-local context.
    
    Thread-safe access following Django/Flask/FastAPI patterns. Used by zExceptions
    for auto-registration. Returns None if not in a zCLI context.
    """
    return _current_zos.get()


# ═══════════════════════════════════════════════════════════════════════════════
# CORE CLASS - zCLI
# ═══════════════════════════════════════════════════════════════════════════════

class zOS:
    """
    Core zCLI Engine - orchestrates 17 subsystems across 4 layers.
    
    Attributes (Public):
        config, comm, display, auth, dispatch, navigation, zparser, loader, zfunc,
        dialog, open, utils, wizard, data, shell, walker, server (optional)
        
        logger, session, zTraceback (set by zConfig)
    
    Key Methods:
        run()          → Start Terminal or zBifrost mode
        run_shell()    → Explicit Terminal mode (REPL)
        run_command()  → Execute single command
        shutdown()     → Graceful cleanup (reverse init order)
    
    Thread-safe via contextvars. Supports context manager protocol.
    Signal handlers (SIGINT/SIGTERM) registered automatically.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Type Hints for Attributes Set by Subsystems
    # ─────────────────────────────────────────────────────────────────────────
    logger: logging.Logger          # Set by zConfig
    session: Dict[str, Any]         # Set by zConfig
    zTraceback: Any                 # Set by zConfig (zTraceback instance)

    def __init__(self, zSpark_obj: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize zCLI with all 17 subsystems in dependency order.
        
        Parameters
        ----------
        zSpark_obj : Optional[Dict[str, Any]]
            Config dict. Common keys: zMode ("Terminal"|"zBifrost"), plugins (List[str]),
            log_level, database, port. Defaults: Terminal mode, INFO logging.
        
        Side Effects: Registers in thread context, sets SIGINT/SIGTERM handlers,
        may auto-start HTTP server, creates session dict.
        """

        # Initialize zSpark_obj config dict
        self.zspark_obj = zSpark_obj or {}

        # Shutdown coordination
        self._shutdown_requested = False
        self._shutdown_in_progress = False

        # Register this instance as current context (thread-safe)
        # Enables automatic exception registration for zExceptions
        _current_zos.set(self)

        # ─────────────────────────────────────────────────────────────
        # Layer 0: Foundation
        # ─────────────────────────────────────────────────────────────
        # Initialize zConfig FIRST (provides machine config, environment config, session, logger, and traceback)
        # After this call, self.session, self.logger, and self.zTraceback are ready to use
        from .L1_Foundation.a_zConfig import zConfig
        self.config = zConfig(zcli=self, zSpark_obj=zSpark_obj)

        # Initialize zComm (Communication infrastructure for zBifrost and zData)
        from .L1_Foundation.b_zComm import zComm
        self.comm = zComm(self)

        # ─────────────────────────────────────────────────────────────
        # Layer 1: Core Subsystems
        # ─────────────────────────────────────────────────────────────
        # Initialize display subsystem
        from .L2_Core.c_zDisplay import zDisplay
        self.display = zDisplay(self)
        self.mycolor = "MAIN"

        # Initialize authentication subsystem
        from .L2_Core.d_zAuth import zAuth
        self.auth = zAuth(self)

        # Initialize dispatch subsystem
        from .L2_Core.e_zDispatch import zDispatch
        self.dispatch = zDispatch(self)

        # Initialize navigation subsystem
        from .L2_Core.f_zNavigation import zNavigation
        self.navigation = zNavigation(self)

        # Initialize parser subsystem
        from .L2_Core.g_zParser import zParser
        self.zparser = zParser(self)

        # Initialize loader subsystem
        from .L2_Core.h_zLoader import zLoader
        self.loader = zLoader(self)

        # Initialize function subsystem
        from .L2_Core.i_zFunc import zFunc
        self.zfunc = zFunc(self)

        # Initialize dialog subsystem
        from .L2_Core.j_zDialog import zDialog
        self.dialog = zDialog(self)

        # Initialize open subsystem
        from .L2_Core.k_zOpen import zOpen
        self.open = zOpen(self)


        # ─────────────────────────────────────────────────────────────
        # Layer 2: Core Abstraction
        # ─────────────────────────────────────────────────────────────
        # Initialize utility subsystem (provides plugin system for other subsystems)
        from .L3_Abstraction.l_zUtils import zUtils
        self.utils = zUtils(self)    # Plugin system - available to all Layer 2+ subsystems
        self._load_plugins()         # Load plugins immediately after plugin system is ready

        # Initialize wizard subsystem (loop engine - no upper dependencies)
        from .L3_Abstraction.m_zWizard import zWizard
        self.wizard = zWizard(self)

        # Initialize data subsystem (may use zWizard for interactive operations)
        from .L3_Abstraction.n_zData import zData
        self.data = zData(self)

        # Initialize zBifrost WebSocket bridge orchestrator (Layer 2)
        # Coordinates Terminal↔Web communication using z.comm infrastructure
        from .L3_Abstraction.o_zBifrost import zBifrost
        self.bifrost = zBifrost(self)

        # Initialize shell and command executor (depends on zUtils, zWizard, zData)
        from .L3_Abstraction.p_zShell import zShell
        self.shell = zShell(self)

        # Layer 3: Orchestration
        # Initialize walker subsystem
        from .L4_Orchestration.q_zWalker import zWalker
        self.walker = zWalker(self)  # Modern walker with unified navigation (can use plugins immediately)

        # Initialize zServer (HTTP/WSGI server subsystem) - Layer 1
        # v1.5.8: Independent subsystem (was factory method in zComm)
        from .L4_Orchestration.r_zServer import zServer
        self.server = zServer(
            logger=self.logger,
            zcli=self,
            config=self.config.http_server if hasattr(self.config, 'http_server') else None
        )
        
        # Auto-start if enabled in config
        if hasattr(self.config, 'http_server') and self.config.http_server.enabled:
            self.server.start()
            self.logger.info(LOG_HTTP_START, f"http://{self.server.host}:{self.server.port}")
            
            # v1.5.8: Auto-wait if configured (declarative lifecycle management)
            # Must happen AFTER signal handlers are registered but BEFORE returning to user code
            # Note: We defer the actual wait() call until after __init__ completes

        # Initialize session (sets zMode from zSpark_obj or defaults to Terminal)
        self._init_session()
        
        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()
        
        # Note: Constructor returns immediately. Call z.run() to start execution.
        # Note: zAuth database is workspace-relative (@), ensuring each zCLI instance
        # is fully isolated. Auth DB lazy-loads on first save_session() or grant_permission().
        # This preserves the "no global state" principle - the secret sauce of zCLI architecture.

        self.logger.framework.debug(LOG_INIT_COMPLETE, self.session.get(SESSION_KEY_ZMODE))

    def _load_plugins(self) -> None:
        """
        Load plugins from zSpark_obj["plugins"] via zUtils.
        
        Supports single string or list. Failures logged as warnings, don't halt init.
        Plugins can use get_current_zos() to access subsystems.
        """
        try:
            plugin_paths = self.zspark_obj.get(ZSPARK_PLUGINS_KEY) or []
            if isinstance(plugin_paths, (list, tuple)):
                self.utils.load_plugins(plugin_paths)
            elif isinstance(plugin_paths, str):
                self.utils.load_plugins([plugin_paths])
        except (ImportError, AttributeError, TypeError) as e:
            self.logger.warning(LOG_WARN_PLUGIN_FAIL, e)

    def _init_session(self) -> None:
        """
        Set session[zS_id] and log config. zMode already set by zConfig.
        """
        # Set session ID - always required
        self.session[SESSION_KEY_ZS_ID] = self.config.session.generate_id("zS")

        # zMode was already set by zConfig.session.detect_zMode() during session creation
        # It checks zSpark_obj.get("zMode") and defaults to "Terminal"
        # No need to override it here

        self.logger.framework.debug(LOG_SESSION_INIT)
        self.logger.framework.debug(LOG_DEBUG_SESSION_ID, self.session[SESSION_KEY_ZS_ID])
        self.logger.framework.debug(LOG_DEBUG_SESSION_MODE, self.session[SESSION_KEY_ZMODE])
        self.logger.framework.debug(LOG_DEBUG_SESSION_MACHINE, self.session[SESSION_KEY_ZMACHINE].get("hostname"))

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def run_command(self, command: str) -> Any:
        """
        Execute single command string via zShell.
        
        Returns command result (type varies). Output typically via zDisplay.
        """
        return self.shell.execute_command(command)

    def run_shell(self) -> None:
        """
        Start Terminal mode (interactive REPL). Blocks until exit.
        """
        return self.shell.run_shell()

    def run(self) -> Any:
        """
        Main entry point - centralized execution for all zCLI modes.
        
        Decision Priority:
        1. zServer running + zShell → REPL with HTTP in background
        2. zServer running (silent) → Block on server.wait()
        3. zVaFile specified → zWalker (handles Terminal/zBifrost internally)
        4. zMode: zBifrost → zWalker (WebSocket mode)
        5. zMode: Terminal (default) → zShell REPL
        
        Returns:
            Any: Result from the executed subsystem (walker, shell, or server)
        """
        # Priority 1 & 2: zServer lifecycle management
        if self.server and self.server._running:
            if hasattr(self.config, 'http_server') and self.config.http_server.zShell:
                # Interactive mode: REPL with HTTP server in background
                print("\n" + "="*70)
                print(f"  🌐 Server: http://{self.server.host}:{self.server.port}")
                print(f"  💻 Entering zShell REPL (type 'exit' to stop server)")
                print("="*70 + "\n")
                return self.run_shell()
            else:
                # Silent blocking mode: Just wait for Ctrl+C
                self.logger.framework.debug("[zCLI] Blocking on zServer (silent mode)")
                return self.server.wait()
        
        # Priority 3: zVaFile specified → Launch walker (auto-detects Terminal/zBifrost)
        if self.session.get("zVaFile"):
            self.logger.info("[zCLI] Launching zWalker (zVaFile detected)")
            return self.walker.run()
        
        # Priority 4 & 5: Mode detection for walker vs shell
        zmode = self.session.get(SESSION_KEY_ZMODE, MODE_TERMINAL)
        
        if zmode == MODE_ZBIFROST:
            self.logger.info(LOG_MODE_ZBIFROST)
            return self.walker.run()

        self.logger.info(LOG_MODE_TERMINAL)
        return self.run_shell()
    
    # ═══════════════════════════════════════════════════════════════════════
    # SIGNAL HANDLERS & GRACEFUL SHUTDOWN
    # ═══════════════════════════════════════════════════════════════════════
    
    def _register_signal_handlers(self) -> None:
        """
        Register SIGINT/SIGTERM handlers for graceful shutdown.
        
        Prevents duplicate attempts via _shutdown_in_progress flag.
        Exit codes: 0 (clean) | 1 (error).
        """
        def signal_handler(signum, frame):  # pylint: disable=unused-argument
            """Handle SIGINT (Ctrl+C) and SIGTERM gracefully"""
            signal_name = SIGNAL_INT if signum == signal.SIGINT else SIGNAL_TERM
            
            # Prevent multiple shutdown attempts
            if self._shutdown_in_progress:
                self.logger.warning(LOG_WARN_SIGNAL_DUPLICATE, signal_name)
                return
            
            self.logger.info(ERROR_SIGNAL_RECEIVED, signal_name)
            self._shutdown_requested = True
            
            # Call shutdown
            try:
                self.shutdown()
                sys.exit(0)
            except Exception as e:
                self.zTraceback.log_exception(
                    e,
                    message=ERROR_SHUTDOWN_SIGNAL % signal_name,
                    context={'signal': signum}
                )
                sys.exit(1)
        
        # Register handlers for SIGINT and SIGTERM
        # Only register if in main thread (signal handlers don't work in other threads)
        import threading
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            self.logger.framework.debug(LOG_DEBUG_SIGNAL_HANDLERS)
        else:
            self.logger.framework.debug("[zCLI] Skipping signal handlers (not main thread)")
    
    def shutdown(self) -> Optional[Dict[str, bool]]:
        """
        Gracefully shutdown all subsystems in reverse init order.
        
        Cleanup: WebSocket → HTTP → Database → Logger. Each wrapped in ExceptionContext
        (failures don't halt shutdown). Idempotent via _shutdown_in_progress flag.
        
        Returns Dict[str, bool] with component status, or None if already in progress.
        """
        if self._shutdown_in_progress:
            self.logger.warning(LOG_WARN_SHUTDOWN_IN_PROGRESS)
            return None
        
        self._shutdown_in_progress = True
        print("\n🔄 zCLI: Graceful shutdown initiated...")
        self.logger.framework.debug(LOG_SHUTDOWN_START)
        
        # Track cleanup success
        cleanup_status = {
            SHUTDOWN_WEBSOCKET: False,
            SHUTDOWN_HTTP_SERVER: False,
            SHUTDOWN_DATABASE: False,
            SHUTDOWN_LOGGER: False
        }
        
        # 1. Close WebSocket connections (zBifrost)
        with ExceptionContext(
            self.zTraceback,
            operation=ERROR_WEBSOCKET_SHUTDOWN,
            default_return=None
        ):
            if self.comm and hasattr(self.comm, 'websocket') and self.comm.websocket:
                if self.comm.websocket._running:  # pylint: disable=protected-access
                    print("   ✓ Closing WebSocket connections...")
                    self.logger.framework.debug(SHUTDOWN_MSG_WEBSOCKET_CLOSE)
                    
                    # For async shutdown, we need to handle it properly
                    import asyncio
                    try:
                        # Check if event loop is already running
                        try:
                            loop = asyncio.get_running_loop()
                            # Loop is running - we can't use run_until_complete
                            # Call the internal synchronous cleanup method instead
                            if hasattr(self.comm.websocket, '_sync_shutdown'):
                                self.comm.websocket._sync_shutdown()  # pylint: disable=protected-access
                            else:
                                # Fallback: schedule shutdown and continue
                                self.logger.warning(LOG_WARN_ASYNC_SHUTDOWN_SKIPPED)
                        except RuntimeError:
                            # No running loop - create one and run shutdown
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.comm.websocket.shutdown())
                            loop.close()
                        
                        cleanup_status[SHUTDOWN_WEBSOCKET] = True
                    except Exception as e:
                        self.logger.warning(LOG_WARN_WEBSOCKET_ERROR, e)
                else:
                    self.logger.debug(LOG_DEBUG_WEBSOCKET_NOT_RUNNING)
                    cleanup_status[SHUTDOWN_WEBSOCKET] = True
            else:
                self.logger.debug(LOG_DEBUG_WEBSOCKET_NOT_INIT)
                cleanup_status[SHUTDOWN_WEBSOCKET] = True
        
        # 2. Stop HTTP server (zServer)
        with ExceptionContext(
            self.zTraceback,
            operation=ERROR_HTTP_SHUTDOWN,
            default_return=None
        ):
            if self.server:
                if self.server._running:  # pylint: disable=protected-access
                    print("   ✓ Stopping HTTP server...")
                    self.logger.framework.debug(SHUTDOWN_MSG_HTTP_STOP)
                    self.server.stop()
                    cleanup_status[SHUTDOWN_HTTP_SERVER] = True
                else:
                    self.logger.debug(LOG_DEBUG_HTTP_NOT_RUNNING)
                    cleanup_status[SHUTDOWN_HTTP_SERVER] = True
            else:
                self.logger.debug(LOG_DEBUG_HTTP_NOT_INIT)
                cleanup_status[SHUTDOWN_HTTP_SERVER] = True
        
        # 3. Close database connections (zData)
        with ExceptionContext(
            self.zTraceback,
            operation=ERROR_DB_SHUTDOWN,
            default_return=None
        ):
            if hasattr(self, 'data') and self.data:
                if hasattr(self.data, 'adapter') and self.data.adapter:
                    print("   ✓ Closing database connections...")
                    self.logger.framework.debug(SHUTDOWN_MSG_DB_CLOSE)
                    if hasattr(self.data.adapter, 'disconnect'):
                        self.data.adapter.disconnect()
                    elif hasattr(self.data.adapter, 'close'):
                        self.data.adapter.close()
                    cleanup_status[SHUTDOWN_DATABASE] = True
                else:
                    self.logger.debug(LOG_DEBUG_DB_NOT_CONNECTED)
                    cleanup_status[SHUTDOWN_DATABASE] = True
            else:
                self.logger.debug(LOG_DEBUG_DB_NOT_INIT)
                cleanup_status[SHUTDOWN_DATABASE] = True
        
        # 4. Flush and close logger
        with ExceptionContext(
            self.zTraceback,
            operation=ERROR_LOGGER_SHUTDOWN,
            default_return=None
        ):
            if self.logger:
                print("   ✓ Flushing logs...")
                self.logger.framework.debug(SHUTDOWN_MSG_LOGGER_FLUSH)
                # Flush all handlers (both app and framework loggers)
                if hasattr(self.logger, 'logger'):  # LoggerConfig wrapper
                    for handler in self.logger.logger.handlers:
                        handler.flush()
                    if hasattr(self.logger, 'framework'):
                        for handler in self.logger.framework.handlers:
                            handler.flush()
                else:  # Direct logger instance (backward compatibility)
                    for handler in self.logger.handlers:
                        handler.flush()
                cleanup_status[SHUTDOWN_LOGGER] = True
        
        # 5. Uninstall exception hook if installed
        if hasattr(self, 'zTraceback') and self.zTraceback:
            self.zTraceback.uninstall_exception_hook()
        
        # Final status report (detailed status to framework logs only)
        self.logger.framework.debug(SHUTDOWN_SEPARATOR)
        self.logger.framework.debug(SHUTDOWN_MSG_STATUS_REPORT)
        for component, status in cleanup_status.items():
            status_str = SHUTDOWN_STATUS_SUCCESS if status else SHUTDOWN_STATUS_FAIL
            self.logger.framework.debug(SHUTDOWN_MSG_COMPONENT_STATUS, status_str, component)
        self.logger.framework.debug(SHUTDOWN_SEPARATOR)
        self.logger.framework.debug(LOG_SHUTDOWN_COMPLETE)
        
        # User-facing completion message (always visible)
        print("✓ Graceful shutdown complete\n")
        
        return cleanup_status
    
    def __enter__(self) -> 'zCLI':
        """Context manager entry - register in thread context."""
        _current_zos.set(self)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        Context manager exit - clear thread context.
        
        Does NOT call shutdown() automatically. Returns False (exceptions propagate).
        """
        _current_zos.set(None)
        return False  # Don't suppress exceptions
