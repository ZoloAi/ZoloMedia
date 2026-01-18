# zCLI/subsystems/zConfig/zConfig.py
"""Cross-platform configuration management with hierarchical loading and secret support."""

from zOS import sys, Any, Dict, Optional, Union
from zOS.utils import print_ready_message, validate_zcli_instance
from .zConfig_modules import (
    ConfigValidator,
    ConfigValidationError,
    zConfigPaths,
    MachineConfig,
    EnvironmentConfig,
    ConfigPersistence,
    SessionConfig,
    SESSION_KEY_LOGGER_INSTANCE,
    LoggerConfig,
    WebSocketConfig,
    HttpServerConfig,
)
from .zConfig_modules.config_resource_limits import ResourceLimits
from .zConfig_modules.helpers import (
    ensure_user_directories,
    ensure_app_directory,
    initialize_system_ui,
    initialize_system_migration_schema,
)

# Module Constants
SUBSYSTEM_NAME = "zConfig"
READY_MESSAGE = "zConfig Ready"
DEFAULT_COLOR = "CONFIG"

class zConfig:
    """Configuration management with hierarchical loading and cross-platform support."""

    # Type hints for instance attributes
    zcli: Any  # zCLI instance
    zSpark: Optional[Dict[str, Any]]
    sys_paths: zConfigPaths
    app_root: Optional[Any]  # App-specific storage root (Path or None)
    machine: MachineConfig
    environment: EnvironmentConfig
    session: SessionConfig
    websocket: WebSocketConfig
    http_server: HttpServerConfig
    _persistence: Optional[ConfigPersistence]
    resource_limits: ResourceLimits

    def __init__(self, zcli: Any, zSpark_obj: Optional[Dict[str, Any]] = None) -> None:
        """Initialize zConfig subsystem with hierarchical configuration loading.
        
        Initialization Order:
            1. Validate configuration (fail fast)
            2. Initialize path resolver
            3. Load machine config (static, per-machine)
            4. Load environment config (deployment, runtime)
            5. Initialize session (creates logger, zTraceback)
            6. Initialize WebSocket and HTTP server configs
        
        Args:
            zcli: zCLI instance
            zSpark_obj: Optional configuration dictionary from zSpark
        """

        # Validate zCLI instance, pre zSession creation
        validate_zcli_instance(zcli, SUBSYSTEM_NAME, require_session=False)
        self.zcli = zcli
        self.zSpark = zSpark_obj

        # ═══════════════════════════════════════════════════════════
        # STEP 0: VALIDATE CONFIGURATION (Fail Fast)
        # ═══════════════════════════════════════════════════════════
        # Week 1.1 - Layer 0: Foundation
        # Validate config BEFORE initializing anything else
        # If config is invalid, fail immediately with clear error
        try:
            validator = ConfigValidator(zSpark_obj, logger=None)  # Logger doesn't exist yet
            validator.validate()
        except ConfigValidationError as e:
            # Print error and exit - can't proceed with invalid config
            print(str(e), file=sys.stderr)
            sys.exit(1)

        # Initialize path resolver
        self.sys_paths = zConfigPaths(zSpark_obj=zSpark_obj)

        # Ensure user directories exist (zConfigs, zUIs)
        ensure_user_directories(self.sys_paths)
        
        # Create app-specific storage directory if enabled in zSpark
        self.app_root = ensure_app_directory(self.sys_paths, zSpark_obj)
        
        # Copy system UI file to user zUIs directory (on first run)
        initialize_system_ui(self.sys_paths)
        
        # Copy system migration schema to user zSchemas directory (on first run)
        initialize_system_migration_schema(self.sys_paths)

        # Load machine config FIRST (static, per-machine)
        self.machine = MachineConfig(self.sys_paths)
        
        # Apply resource limits (CPU and memory) if specified
        self.resource_limits = ResourceLimits(self.machine.machine)
        self.resource_limits.apply()

        # Load environment config SECOND (deployment, runtime settings)
        # Pass zSpark for Layer 5 overrides (highest priority)
        self.environment = EnvironmentConfig(self.sys_paths, zSpark_obj)

        # Initialize session THIRD (uses machine and environment config for session creation)
        # Pass self so SessionConfig can call back to create_logger()
        self.session = SessionConfig(self.machine, self.environment, zcli, zSpark_obj, zconfig=self)

        # Create session and attach to zcli instance
        session_data = self.session.create_session()
        zcli.session = session_data

        # Get logger from session (initialized during session creation)
        session_logger = session_data[SESSION_KEY_LOGGER_INSTANCE]

        # Store full LoggerConfig instance (provides helper methods like should_show_sysmsg())
        # The LoggerConfig class proxies all standard logging methods to the underlying Python logger
        zcli.logger = session_logger

        # Log initial message with configured level (framework logger for internal init)
        zcli.logger.framework.debug("Logger initialized at level: %s", session_logger.log_level)

        # Initialize centralized traceback utility
        # Import inline to avoid circular dependency (zTraceback imports zConfig types)
        from zSys.errors import zTraceback
        zcli.zTraceback = zTraceback(logger=zcli.logger, zcli=zcli)

        # Install automatic exception handler if zTraceback is enabled
        if zcli.session.get('zTraceback', False):
            zcli.zTraceback.install_exception_hook()

        # Initialize WebSocket configuration (uses environment config)
        self.websocket = WebSocketConfig(self.environment, zcli, zcli.logger)

        # Initialize HTTP Server configuration (optional feature)
        self.http_server = HttpServerConfig(zSpark_obj or {}, zcli.logger)

        # Initialize storage path manager (Phase 1.5: Storage Architecture)
        from .zConfig_modules.config_storage_paths import StoragePathManager
        self.paths = self.sys_paths  # Shortcut for convenience
        self.storage_paths = StoragePathManager(self)

        # Print styled ready message (before zDisplay is available, deployment-aware)
        is_production = self.environment.is_production()
        is_testing = self.environment.is_testing()
        print_ready_message(READY_MESSAGE, color=DEFAULT_COLOR, is_production=is_production, is_testing=is_testing)

    # ═══════════════════════════════════════════════════════════
    # Configuration Access Methods
    # ═══════════════════════════════════════════════════════════

    def get_machine(self, key: Optional[str] = None, default: Any = None) -> Union[Any, Dict[str, Any]]:
        """Get machine config value by key (or all values if key=None).
        
        Args:
            key: Configuration key to retrieve (None returns all config)
            default: Default value if key not found
            
        Returns:
            Single value if key provided, full config dict if key is None
        """
        if key is None:
            return self.machine.get_all()
        return self.machine.get(key, default)

    def get_environment(self, key: Optional[str] = None, default: Any = None) -> Union[Any, Dict[str, Any]]:
        """Get environment config value by key (or all values if key=None).
        
        Args:
            key: Configuration key to retrieve (None returns all config)
            default: Default value if key not found
            
        Returns:
            Single value if key provided, full config dict if key is None
        """
        if key is None:
            return self.environment.get_all()
        return self.environment.get(key, default)

    def is_production(self) -> bool:
        """Check if running in Production deployment mode.
        
        Convenience method that delegates to environment.is_production().
        
        Returns:
            bool: True if deployment is "Production", False otherwise
        """
        return self.environment.is_production()
    
    def get_cpu_limit(self) -> int:
        """Get effective CPU core limit for resource management.
        
        Returns user-specified limit if set, otherwise returns detected cores.
        Use this value to limit multiprocessing pools, thread pools, etc.
        
        Returns:
            int: Number of CPU cores to use
        """
        return self.resource_limits.get_cpu_limit()
    
    def get_memory_limit_gb(self) -> int:
        """Get effective memory limit in GB for resource management.
        
        Returns user-specified limit if set, otherwise returns detected memory.
        Use this value to limit cache sizes, buffer allocations, etc.
        
        Returns:
            int: Memory limit in GB
        """
        return self.resource_limits.get_memory_limit_gb()
    
    def get_resource_limits_status(self) -> Dict[str, Any]:
        """Get detailed resource limits status.
        
        Returns:
            Dict with current limits, availability info, and enforcement status
        """
        return self.resource_limits.get_status()

    def create_logger(self, session_data: Dict[str, Any]) -> LoggerConfig:
        """Create logger instance with session data.
        
        Args:
            session_data: Session dictionary containing logger configuration
            
        Returns:
            Configured LoggerConfig instance
        """
        return LoggerConfig(self.environment, self.zcli, session_data)

    def get_paths_info(self) -> Dict[str, str]:
        """Get path information for debugging/diagnostics.
        
        Returns dict with all config paths (system, user, data, cache, logs).
        Used by shell config check command for system diagnostics.
        
        Returns:
            Dict[str, str]: Dictionary with path information:
                - os: Operating system type
                - system_config_dir: System-level config directory
                - system_config_defaults: Default config files location
                - system_machine_config: System machine config file
                - user_config_dir: User config directory
                - user_config_legacy: Legacy user config directory (if exists)
                - user_zconfigs_dir: User zConfigs directory
                - user_data_dir: User data directory
                - user_cache_dir: User cache directory
                - user_logs_dir: User logs directory
        
        Example:
            paths = zcli.config.get_paths_info()
            print(f"User config: {paths['user_config_dir']}")
        
        Notes:
            - Delegates to sys_paths.get_info() for actual path resolution
            - All paths are returned as strings (converted from Path objects)
            - Used for config check command diagnostics
        """
        return self.sys_paths.get_info()

    def get_config_sources(self) -> list:
        """Get list of config sources that were loaded.
        
        Returns ordered list of source names that were successfully loaded during
        initialization. Used by config check command to verify loader functionality.
        
        Returns:
            List[str]: List of config source names, e.g.:
                ['machine', 'environment']
        
        Example:
            sources = zcli.config.get_config_sources()
            print(f"Config loaded from {len(sources)} sources: {', '.join(sources)}")
        
        Notes:
            - Sources are loaded in hierarchical order (machine, environment)
            - Empty list means no sources loaded (should not happen in normal operation)
            - Used for config check command to verify loader is working
        """
        sources = []
        if hasattr(self, 'machine') and self.machine:
            sources.append('machine')
        if hasattr(self, 'environment') and self.environment:
            sources.append('environment')
        return sources

    @property
    def persistence(self) -> ConfigPersistence:
        """Lazy-load persistence subsystem when needed for saving changes.
        
        Returns:
            ConfigPersistence instance for saving configuration changes
        """
        if not hasattr(self, '_persistence'):
            self._persistence = ConfigPersistence(self.machine, self.environment, self.sys_paths, self.zcli)  # pylint: disable=attribute-defined-outside-init
        return self._persistence
