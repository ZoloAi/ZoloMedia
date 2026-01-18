# zCLI/subsystems/zConfig/zConfig_modules/config_logger.py
"""
Logger configuration and management as part of zConfig.

Uses unified logging format from zSys.logger for consistency
across all logging systems (bootstrap, framework, app).
"""

from zOS import Colors, logging, os, Path, Any, Dict, Optional
from zOS.utils import print_ready_message, validate_zcli_instance
from zSys.logger import UnifiedFormatter
from .config_session import SESSION_KEY_ZLOGGER

# Module Constants

# Logging
_LOG_PREFIX = "[LoggerConfig]"
_SUBSYSTEM_NAME = "LoggerConfig"
_READY_MESSAGE = "zLogger Ready"
_LOGGER_NAME = "zCLI"
_LOG_FILENAME = "zolo-zcli.log"  # Deprecated, kept for backward compatibility
_LOG_FILENAME_FRAMEWORK = "zcli-framework.log"
_LOG_FILENAME_APP = "zcli-app.log"

# Log Levels
_LOG_LEVEL_DEBUG = "DEBUG"
_LOG_LEVEL_SESSION = "SESSION"
_LOG_LEVEL_INFO = "INFO"
_LOG_LEVEL_WARNING = "WARNING"
_LOG_LEVEL_ERROR = "ERROR"
_LOG_LEVEL_CRITICAL = "CRITICAL"
# Import from zSys.logger (single source of truth)
from zSys.logger import LOG_LEVEL_SESSION, LOG_LEVEL_PROD as _LOG_LEVEL_PROD
_VALID_LOG_LEVELS = (_LOG_LEVEL_DEBUG, _LOG_LEVEL_SESSION, _LOG_LEVEL_INFO, _LOG_LEVEL_WARNING, _LOG_LEVEL_ERROR, _LOG_LEVEL_CRITICAL, _LOG_LEVEL_PROD)
_DEFAULT_LOG_LEVEL = _LOG_LEVEL_INFO

# Config Keys
_CONFIG_KEY_LOGGING = "logging"
_CONFIG_KEY_APP = "app"
_CONFIG_KEY_FRAMEWORK = "framework"
_CONFIG_KEY_FILE_ENABLED = "file_enabled"
_CONFIG_KEY_FORMAT = "format"
_CONFIG_KEY_FILE_PATH = "file_path"
_CONFIG_KEY_LEVEL = "level"

# Format Types
_FORMAT_JSON = "json"
_FORMAT_SIMPLE = "simple"
_FORMAT_DETAILED = "detailed"
_DEFAULT_FORMAT = _FORMAT_DETAILED

# Default Values
_DEFAULT_FILE_ENABLED = True

# Path Markers (for caller info detection)
_PATH_SUBSYSTEMS_MARKER = "zCLI/subsystems/"
_PATH_ZCLI_MARKER = "zCLI/"
_PATH_SUBSYSTEMS_DIR = "subsystems"
_PYTHON_EXTENSION = ".py"

class LoggerConfig:
    """Manages three-tier logging configuration: framework, session framework, and app logs."""

    # Type hints for instance attributes
    environment: Any  # EnvironmentConfig
    zcli: Any  # zCLI instance
    session_data: Dict[str, Any]
    log_level: str  # App log level (backward compatibility)
    _framework_logger: logging.Logger  # Pure framework logs (global, session-agnostic)
    _session_framework_logger: logging.Logger  # Session-specific framework logs (bootstrap, ready banners, flow)
    _app_logger: logging.Logger  # User application logs (optional)

    def __init__(self, environment_config: Any, zcli: Any, session_data: Dict[str, Any]) -> None:
        """Initialize three-tier logger system with framework, session framework, and application loggers.
        
        Creates three separate loggers:
        1. Framework logger: Pure zCLI internals → zcli-framework.log (global, minimal)
        2. Session framework logger: Session execution trace → {session}.framework.log (bootstrap, flow)
        3. Application logger: User code → {session}.log (optional, customizable)
        """
        # Validate required parameters
        validate_zcli_instance(zcli, _SUBSYSTEM_NAME, require_session=False)
        if session_data is None:
            raise ValueError("session_data parameter is required and cannot be None")

        self.environment = environment_config
        self.zcli = zcli
        self.session_data = session_data

        # Get logger configuration from session (which uses environment detection)
        self.log_level = self._get_log_level()

        # Initialize three-tier logging system
        self._setup_framework_logging()              # #1 Pure framework (global)
        self._setup_session_framework_logging()      # #2 Session framework (THIS execution)
        self._setup_app_logging()                    # #3 User app (optional)

        # Print ready message (deployment-aware)
        print_ready_message(_READY_MESSAGE, color="CONFIG", is_production=self.environment.is_production(), is_testing=self.environment.is_testing())
        
        # Log ready message to session framework
        self._session_framework_logger.info("zLogger Ready")

    def _normalize_log_level(self, level: Any) -> str:
        """Normalize log level to uppercase string."""
        return str(level).upper()

    def _validate_log_level(self, level: str) -> str:
        """
        Validate log level against valid levels.
        
        Args:
            level: Log level string (already normalized to uppercase)
        
        Returns:
            str: Valid log level or _DEFAULT_LOG_LEVEL if invalid
        """
        if level not in _VALID_LOG_LEVELS:
            print(f"{Colors.WARNING}{_LOG_PREFIX} Invalid log level '{level}', "
                  f"using '{_DEFAULT_LOG_LEVEL}'{Colors.RESET}")
            return _DEFAULT_LOG_LEVEL
        return level

    def _strip_py_extension(self, filename: str) -> str:
        """Strip .py extension from filename if present."""
        if filename.endswith(_PYTHON_EXTENSION):
            return filename[:-len(_PYTHON_EXTENSION)]
        return filename

    def _get_log_level(self) -> str:
        """
        Get log level from session data.
        Session has already processed the full hierarchy:
        zSpark → virtual env → system env → config file → default
        
        Returns:
            str: Valid log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        # Session data has already done all the hierarchy detection
        # Just get the final value from session data
        level = self.session_data.get(SESSION_KEY_ZLOGGER, _DEFAULT_LOG_LEVEL)
        
        # Normalize and validate
        level = self._normalize_log_level(level)
        return self._validate_log_level(level)
    def _resolve_logger_path(self, path_str: str) -> Path:
        """
        Resolve logger path with zPath notation support.
        
        Supports:
            - @.path → workspace-relative (zPath convention)
            - ~.path or ~/path → home-relative
            - ./path → current directory relative
            - path → absolute or relative
        
        Args:
            path_str: Path string to resolve
            
        Returns:
            Resolved Path object
        
        Examples:
            >>> _resolve_logger_path("@.logs")  # workspace/logs
            >>> _resolve_logger_path("./logs")  # cwd/logs
            >>> _resolve_logger_path("~/logs")  # home/logs
        """
        path_str = str(path_str).strip()
        
        # Handle zPath workspace-relative notation (@.path or @path)
        if path_str.startswith("@."):
            # Remove @. prefix
            relative_path = path_str[2:]
            # Get workspace directory from config paths
            if hasattr(self.zcli, 'config') and hasattr(self.zcli.config, 'sys_paths'):
                workspace = self.zcli.config.sys_paths.workspace_dir
                if workspace:
                    return Path(workspace) / relative_path
            # Fallback to current directory if workspace not available
            return Path.cwd() / relative_path
        
        elif path_str.startswith("@"):
            # Handle @path (without dot)
            relative_path = path_str[1:]
            if hasattr(self.zcli, 'config') and hasattr(self.zcli.config, 'sys_paths'):
                workspace = self.zcli.config.sys_paths.workspace_dir
                if workspace:
                    return Path(workspace) / relative_path
            return Path.cwd() / relative_path
        
        # Handle tilde notation (~.path or ~/path) and regular paths
        return Path(path_str).expanduser().resolve()
    
    def _get_caller_info(self, record: logging.LogRecord) -> str:
        """
        Extract caller file information from log record.
        
        Provides hierarchical naming for zCLI subsystems (e.g., 'zComm.http_server')
        and simple filenames for other modules.
        
        Args:
            record: Python logging record with pathname information
        
        Returns:
            str: Formatted caller name (subsystem.module or filename)
        """
        pathname = record.pathname
        
        # For zCLI subsystems, show hierarchical subsystem/module names
        if _PATH_SUBSYSTEMS_MARKER in pathname:
            # Extract subsystem name from path like: /path/to/zCLI/subsystems/zComm/zComm.py
            parts = pathname.split(_PATH_SUBSYSTEMS_MARKER)
            if len(parts) > 1:
                subsystem_part = parts[1]
                # Get the first directory after subsystems (e.g., zComm from zComm/zComm.py)
                subsystem_segments = subsystem_part.split('/')
                subsystem = subsystem_segments[0]

                # Determine module filename (if available)
                if len(subsystem_segments) > 1:
                    module_filename = subsystem_segments[-1]
                    module, _ = os.path.splitext(module_filename)

                    # If the module filename matches the subsystem, return subsystem only
                    if module == subsystem:
                        return subsystem

                    # Otherwise return hierarchical name subsystem.module
                    return f"{subsystem}.{module}"

                return subsystem
        
        # For zCLI core files, show the module name
        if _PATH_ZCLI_MARKER in pathname and _PATH_SUBSYSTEMS_DIR not in pathname:
            filename = os.path.basename(pathname)
            return self._strip_py_extension(filename)
                
        # For other files, just show the filename
        filename = os.path.basename(pathname)
        return self._strip_py_extension(filename)
    
    def _setup_framework_logging(self) -> None:
        """
        Setup PURE framework logger for global, session-agnostic operations.
        
        Pure framework logger characteristics:
            - Logger name: "zCLI.framework"
            - Purpose: Global zCLI concerns (NOT session-specific)
            - Use: System-level errors, import failures, critical bugs
            - Level: Always DEBUG (for rare cases when used)
            - File: zcli-framework.log (fixed path, shared across sessions)
            - Console: Disabled in Production/Testing, ERROR+ otherwise
            - Path: Non-configurable (always zCLI support folder)
        
        NOTE: Most logs should go to session_framework instead!
        This logger is MINIMAL and should rarely be used.
        """
        # Get logging configuration for format only
        logging_config = self.environment.get(_CONFIG_KEY_LOGGING, {})
        framework_config = logging_config.get(_CONFIG_KEY_FRAMEWORK, {})
        log_format = framework_config.get(_CONFIG_KEY_FORMAT, _DEFAULT_FORMAT)
        
        # Framework logger fixed to DEBUG level
        framework_level = _LOG_LEVEL_DEBUG
        
        # Check deployment mode for console output
        is_production = self.environment.is_production()
        is_testing = self.environment.is_testing()
        
        # Framework log file path (fixed to zCLI support folder)
        if hasattr(self.zcli, 'config') and hasattr(self.zcli.config, 'sys_paths'):
            logs_dir = self.zcli.config.sys_paths.user_logs_dir
            file_path = str(logs_dir / _LOG_FILENAME_FRAMEWORK)
        else:
            # Fallback if config not available yet
            home_path = Path.home()
            import platform
            if platform.system() == "Windows":
                logs_dir = home_path / "AppData" / "Local" / "zolo-zcli" / "logs"
            elif platform.system() == "Darwin":  # macOS
                logs_dir = home_path / "Library" / "Application Support" / "zolo-zcli" / "logs"
            else:  # Linux
                logs_dir = home_path / ".local" / "share" / "zolo-zcli" / "logs"
            file_path = str(logs_dir / _LOG_FILENAME_FRAMEWORK)
        
        # Create framework logger
        self._framework_logger = logging.getLogger("zCLI.framework")
        self._framework_logger.setLevel(getattr(logging, framework_level))
        
        # Clear existing handlers to avoid duplicates
        self._framework_logger.handlers.clear()
        
        # Use unified formatter from zSys (consistent with bootstrap logger)
        # Framework logger always uses detailed format with file/line info
        console_formatter = UnifiedFormatter("Framework", include_details=False)
        file_formatter = UnifiedFormatter("Framework", include_details=True)

        # Console handler for framework logs: Development (ERROR+), Debug (respects logger level)
        is_debug = self.environment.is_debug()
        if not (is_production or is_testing):
            console_handler = logging.StreamHandler()
            # Debug deployment: show all framework logs at user's logger level
            # Development deployment: show only errors (minimal)
            if is_debug:
                console_handler.setLevel(getattr(logging, self.log_level))  # Respect logger level
            else:
                console_handler.setLevel(logging.ERROR)  # Minimal (Development mode)
            console_handler.setFormatter(console_formatter)
            self._framework_logger.addHandler(console_handler)

        # File handler (always enabled for framework logs)
        try:
            # Ensure log directory exists
            log_file = Path(file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Create file handler
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setLevel(getattr(logging, framework_level))
            file_handler.setFormatter(file_formatter)
            self._framework_logger.addHandler(file_handler)
            
            # Silent setup (framework logs are transparent)
        except Exception as e:
            print(f"{Colors.ERROR}{_LOG_PREFIX} Failed to setup framework logging: {e}{Colors.RESET}")
    
    def _setup_session_framework_logging(self) -> None:
        """
        Setup session framework logger for THIS execution.
        
        Session framework logger characteristics:
            - Logger name: "zCLI.session.framework"
            - File: {session_title}.framework.log (e.g., zCloud.framework.log)
            - Location: Fixed at ~/Library/.../zolo-zcli/logs/ (no override)
            - Level: DEBUG (capture everything for this session)
            - Console: WARNING+ in Development only
            - Content: Bootstrap, Ready banners, SESSION logs, framework flow
        
        This logger contains the complete execution trace for THIS session,
        making it easy to audit and debug specific runs.
        """
        # Get session title for filename
        from .config_session import SESSION_KEY_TITLE
        session_title = self.session_data.get(SESSION_KEY_TITLE, "session")
        log_filename = f"{session_title}.framework.log"
        
        # Check deployment mode
        is_production = self.environment.is_production()
        is_testing = self.environment.is_testing()
        
        # Get fixed log directory (no override for session framework)
        if hasattr(self.zcli, 'config') and hasattr(self.zcli.config, 'sys_paths'):
            logs_dir = self.zcli.config.sys_paths.user_logs_dir
            file_path = str(logs_dir / log_filename)
        else:
            # Fallback if config not available yet
            home_path = Path.home()
            import platform
            if platform.system() == "Windows":
                logs_dir = home_path / "AppData" / "Local" / "zolo-zcli" / "logs"
            elif platform.system() == "Darwin":  # macOS
                logs_dir = home_path / "Library" / "Application Support" / "zolo-zcli" / "logs"
            else:  # Linux
                logs_dir = home_path / ".local" / "share" / "zolo-zcli" / "logs"
            file_path = str(logs_dir / log_filename)
        
        # Create session framework logger
        self._session_framework_logger = logging.getLogger("zCLI.session.framework")
        self._session_framework_logger.setLevel(logging.DEBUG)  # Capture everything
        
        # Clear existing handlers to avoid duplicates
        self._session_framework_logger.handlers.clear()
        
        # Use unified formatter from zSys (consistent with bootstrap and framework)
        console_formatter = UnifiedFormatter("SessionFramework", include_details=False)
        file_formatter = UnifiedFormatter("SessionFramework", include_details=True)
        
        # Console handler: Development (WARNING+), Debug (respects logger level)
        is_debug = self.environment.is_debug()
        if not (is_production or is_testing):
            console_handler = logging.StreamHandler()
            # Debug deployment: show all framework logs at user's logger level
            # Development deployment: show only warnings and errors (minimal)
            if is_debug:
                console_handler.setLevel(getattr(logging, self.log_level))  # Respect logger level
            else:
                console_handler.setLevel(logging.WARNING)  # Minimal (Development mode)
            console_handler.setFormatter(console_formatter)
            self._session_framework_logger.addHandler(console_handler)
        
        # File handler (always enabled for session framework logs)
        try:
            # Ensure log directory exists
            log_file = Path(file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setLevel(logging.DEBUG)  # Capture everything to file
            file_handler.setFormatter(file_formatter)
            self._session_framework_logger.addHandler(file_handler)
            
            # Log session framework initialization
            if not is_production:
                print(f"{_LOG_PREFIX} Session framework logging enabled: {log_filename}")
        except Exception as e:
            print(f"{Colors.ERROR}{_LOG_PREFIX} Failed to setup session framework logging: {e}{Colors.RESET}")
    
    def _setup_app_logging(self) -> None:
        """
        Setup application logger for user code.
        
        Application logger characteristics:
            - Logger name: "zCLI.app"
            - Level: Configurable (default: INFO, smart defaults per deployment)
            - File: zcli-app.log (customizable path)
            - Console: Always enabled (respects level)
            - Path: Defaults to zCLI support folder, user-configurable via config
        """
        # Get logging configuration
        logging_config = self.environment.get(_CONFIG_KEY_LOGGING, {})
        app_config = logging_config.get(_CONFIG_KEY_APP, {})
        
        # Check deployment mode
        is_production = self.environment.is_production()
        
        # File logging always enabled in Production, otherwise configurable
        file_enabled = is_production or app_config.get(_CONFIG_KEY_FILE_ENABLED, _DEFAULT_FILE_ENABLED)
        log_format = app_config.get(_CONFIG_KEY_FORMAT, _DEFAULT_FORMAT)
        
        # Get log file path - check zSpark first, then fall back to system default
        from .config_session import SESSION_KEY_TITLE, SESSION_KEY_LOGGER_PATH
        
        # Get session title for log filename
        session_title = self.session_data.get(SESSION_KEY_TITLE)
        log_filename = f"{session_title}.log" if session_title else _LOG_FILENAME_APP
        
        # Priority 1: Check for custom logger_path (directory) from zSpark
        custom_logger_path = self.session_data.get(SESSION_KEY_LOGGER_PATH)
        if custom_logger_path:
            # User specified custom directory - append title-based filename
            # Support zPath notation (@. for workspace-relative, ~. for home)
            logs_dir = self._resolve_logger_path(custom_logger_path)
            file_path = str(logs_dir / log_filename)
        else:
            # Priority 2: Use system support directory with session title
            # Use proper system support directory for logs
            if hasattr(self.zcli, 'config') and hasattr(self.zcli.config, 'sys_paths'):
                logs_dir = self.zcli.config.sys_paths.user_logs_dir
                file_path = str(logs_dir / log_filename)
            else:
                # Fallback if config not available yet
                home_path = Path.home()
                import platform
                if platform.system() == "Windows":
                    logs_dir = home_path / "AppData" / "Local" / "zolo-zcli" / "logs"
                elif platform.system() == "Darwin":  # macOS
                    logs_dir = home_path / "Library" / "Application Support" / "zolo-zcli" / "logs"
                else:  # Linux
                    logs_dir = home_path / ".local" / "share" / "zolo-zcli" / "logs"
                
                file_path = str(logs_dir / log_filename)
        
        # Use configured log level (from session detection)
        app_log_level = self.log_level
        
        # Create application logger
        # In PROD mode, set logger to DEBUG to capture everything, but disable console
        effective_log_level = _LOG_LEVEL_DEBUG if app_log_level == _LOG_LEVEL_PROD else app_log_level
        self._app_logger = logging.getLogger("zCLI.app")
        self._app_logger.setLevel(getattr(logging, effective_log_level))
        
        # Clear existing handlers to avoid duplicates
        self._app_logger.handlers.clear()
        
        # Use unified formatter from zSys (consistent with bootstrap and framework)
        # App logger uses simple format (no file/line for console readability)
        console_formatter = UnifiedFormatter("App", include_details=False)
        file_formatter = UnifiedFormatter("App", include_details=True)

        # Console handler (disabled in PROD mode for silent operation)
        if app_log_level != _LOG_LEVEL_PROD:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, app_log_level))
            console_handler.setFormatter(console_formatter)
            self._app_logger.addHandler(console_handler)

        # File handler (enabled based on config)
        if file_enabled:
            try:
                # Ensure log directory exists
                log_file = Path(file_path)
                log_file.parent.mkdir(parents=True, exist_ok=True)

                # Create file handler
                # In PROD mode, use DEBUG for file (capture everything) while console is silent
                file_log_level = _LOG_LEVEL_DEBUG if app_log_level == _LOG_LEVEL_PROD else app_log_level
                file_handler = logging.FileHandler(str(log_file))
                file_handler.setLevel(getattr(logging, file_log_level))
                file_handler.setFormatter(file_formatter)
                self._app_logger.addHandler(file_handler)
                
                # Only print file logging message if not in Production
                if not is_production:
                    print(f"{_LOG_PREFIX} App logging enabled: {file_path}")
            except Exception as e:
                print(f"{Colors.ERROR}{_LOG_PREFIX} Failed to setup app logging: {e}{Colors.RESET}")
    
    @property
    def logger(self) -> logging.Logger:
        """
        Get the application logger instance (user code).
        
        This is the logger for user application code. Returns the app logger
        for backward compatibility and primary API surface.
        
        Returns:
            logging.Logger: The application logger instance
        """
        return self._app_logger
    
    @property
    def framework(self) -> logging.Logger:
        """
        Get the pure framework logger (global, session-agnostic).
        
        This logger is for PURE zCLI framework internals that are NOT
        session-specific (e.g., import errors, system-level failures).
        
        Use sparingly - most logs should go to session_framework instead.
        
        File: zcli-framework.log (fixed, global)
        
        Returns:
            logging.Logger: The pure framework logger instance
        """
        return self._framework_logger
    
    @property
    def session_framework(self) -> logging.Logger:
        """
        Get the session framework logger (execution trace for THIS session).
        
        This logger contains the complete execution trace for THIS specific
        session, including bootstrap, ready banners, SESSION logs, and
        framework flow.
        
        Use for:
            - Bootstrap logs
            - Ready banners (zMachine, zEnv, zParser, etc.)
            - SESSION level logs (zSpark values, config)
            - Framework execution flow (dispatch, navigation)
        
        File: {session_title}.framework.log (e.g., zCloud.framework.log)
        
        Returns:
            logging.Logger: The session framework logger instance
        """
        return self._session_framework_logger
    
    def set_level(self, level: Any) -> None:
        """
        Set logger level dynamically.
        
        Args:
            level: Log level string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        
        Note:
            To control production behaviors (silent console, no banners),
            use deployment mode instead of log level.
        """
        level = self._normalize_log_level(level)
        
        # Handle deprecated PROD level
        if level == _LOG_LEVEL_PROD:
            print(f"{Colors.WARNING}{_LOG_PREFIX} 'PROD' log level is deprecated.{Colors.RESET}")
            print(f"{Colors.WARNING}{_LOG_PREFIX} Deployment and logger level are now separate!{Colors.RESET}")
            print(f"{Colors.WARNING}{_LOG_PREFIX} Use: deployment: 'Production' (clean UI) + logger: 'INFO' (reasonable logs){Colors.RESET}")
            print(f"{Colors.WARNING}{_LOG_PREFIX} Defaulting to INFO for now.{Colors.RESET}")
            level = _LOG_LEVEL_INFO
        
        if level in _VALID_LOG_LEVELS:
            self._app_logger.setLevel(getattr(logging, level))
            self.log_level = level
            
            # Update all handlers
            for handler in self._app_logger.handlers:
                handler.setLevel(getattr(logging, level))
        else:
            print(f"{Colors.WARNING}{_LOG_PREFIX} Invalid log level: {level}{Colors.RESET}")
    
    def get_level(self) -> str:
        """
        Get current logger level.
        
        Returns:
            str: Current log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        return self.log_level
    
    def should_show_sysmsg(self) -> bool:
        """
        Check if system messages should be displayed based on deployment mode.
        
        System messages (aesthetic "Ready" banners) are shown in Development
        but hidden in Testing and Production deployments. These are visual
        indicators only, not logged to file.
        
        Shown in: Development deployment
        Hidden in: Testing, Production deployments
        
        Returns:
            bool: True if sysmsg should be shown (Development mode only)
        """
        # Suppress in both Production AND Testing (only show in Development)
        return not (self.environment.is_production() or self.environment.is_testing())
    
    # ═══════════════════════════════════════════════════════════
    # Logging Interface (Semantic Routing)
    # ═══════════════════════════════════════════════════════════
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log debug message → framework logger ONLY.
        
        Routes to: framework logger (zcli-framework.log)
        Audience: zCLI developers debugging framework internals
        
        Use for:
            - Implementation details (path resolution, cache hits)
            - Performance metrics for optimization
            - Internal algorithm debugging
            - Framework bug diagnosis
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Examples:
            z.logger.debug("zParser path resolution: @.UI → /Users/.../UI")
            z.logger.debug("Cache hit: 3/5 files")
        """
        self._framework_logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log info message → session framework logger ONLY.
        
        Routes to: session framework logger ({title}.framework.log)
        Audience: Users debugging their application flow
        
        Use for:
            - User-facing events (zParser Ready, subsystem loaded)
            - High-level flow (loading zVaFile, processing request)
            - Ready banners (zMachine, zEnv, zParser)
            - Configuration summary (non-detailed)
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Examples:
            z.logger.info("zParser Ready")
            z.logger.info("Loading zVaFile: @.UI.zProducts")
        """
        self._session_framework_logger.info(message, *args, **kwargs)
    
    def session(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log session/environment/system information → session framework logger ONLY.
        
        Routes to: session framework logger ({title}.framework.log)
        Audience: Users understanding session configuration and context
        
        SESSION level (15) sits between INFO (20) and DEBUG (10).
        
        Use for:
            - Session initialization details (Python version, OS)
            - Configuration detection (zSpark values, deployment, mode)
            - Environment setup (installation type, paths)
            - Session-specific context (dry information)
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Examples:
            z.logger.session("Python %s on %s", version, platform)
            z.logger.session("zSpark configuration loaded: %d keys", len(config))
            z.logger.session("Deployment: %s, Mode: %s", deployment, mode)
        """
        self._session_framework_logger.log(logging.SESSION, message, *args, **kwargs)
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log warning message → BOTH framework and session framework loggers.
        
        Routes to: BOTH zcli-framework.log AND {title}.framework.log
        Audience: Both developers (might be bug) and users (needs attention)
        
        Use for:
            - Potential issues (file not found, deprecated usage)
            - Configuration problems (invalid setting, missing key)
            - Non-critical failures (fallback used, retry succeeded)
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Examples:
            z.logger.warning("zVaFile not found: @.UI.Missing")
            z.logger.warning("Deprecated usage: PROD log level")
        """
        self._framework_logger.warning(message, *args, **kwargs)
        self._session_framework_logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log error message → BOTH framework and session framework loggers.
        
        Routes to: BOTH zcli-framework.log AND {title}.framework.log
        Audience: Both developers (framework bug?) and users (what failed?)
        
        Use for:
            - Critical failures (initialization failed, cannot proceed)
            - Runtime errors (database connection failed, API error)
            - System-level problems (permission denied, disk full)
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Examples:
            z.logger.error("zParser initialization failed: %s", error)
            z.logger.error("Database connection failed")
        """
        self._framework_logger.error(message, *args, **kwargs)
        self._session_framework_logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log critical message → BOTH framework and session framework loggers.
        
        Routes to: BOTH zcli-framework.log AND {title}.framework.log
        Audience: Both developers (system failure) and users (cannot continue)
        
        Use for:
            - System-level failures (cannot load core subsystem)
            - Unrecoverable errors (corruption detected, out of memory)
            - Emergency shutdowns (data integrity at risk)
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Examples:
            z.logger.critical("Core subsystem failed to load")
            z.logger.critical("Data corruption detected in config")
        """
        self._framework_logger.critical(message, *args, **kwargs)
        self._session_framework_logger.critical(message, *args, **kwargs)
    
    def dev(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Development log - shown in development modes but hidden in Production.
        
        Use for development diagnostics and internal debugging messages that
        should not appear in production deployments.
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            z.logger.dev("Cache hit rate: %d%%", 87)
            z.logger.dev("Development diagnostic message")
        """
        if self.environment.is_production():
            return  # Suppressed in Production deployment
        
        # Show in development modes (application logger)
        self._app_logger.info(message, *args, **kwargs)
    
    def user(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        User application log - shown in ALL modes including PROD.
        
        Use for important application messages that should always be visible,
        even in production deployments. These go to both console and log file.
        
        Args:
            message: Log message (supports % formatting with args)
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            z.logger.user("Application started successfully")
            z.logger.user("Processing %d records...", 1247)
        """
        # Format message if args provided
        formatted_msg = message % args if args else message
        
        # Always print to console, even in PROD mode
        print(formatted_msg)
        
        # Also log to file (application logger)
        self._app_logger.info(message, *args, **kwargs)

