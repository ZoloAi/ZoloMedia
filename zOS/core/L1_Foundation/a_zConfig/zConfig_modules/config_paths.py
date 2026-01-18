# zCLI/subsystems/zConfig/zConfig_modules/config_paths.py
"""Cross-platform configuration path resolution with platformdirs."""

import logging
from zOS import platform, Path, Colors, platformdirs, load_dotenv, Any, Dict, List, Optional, Tuple

# Module-level logger
logger = logging.getLogger(__name__)

class zConfigPaths:
    """Cross-platform path resolver for zolo-zcli configuration using native OS conventions."""

    # Class-level constants
    APP_NAME = "zolo-zcli"
    APP_AUTHOR = "zolo"
    VALID_OS_TYPES = ("Linux", "Darwin", "Windows")
    DOTENV_FILENAME = ".zEnv"
    ZCONFIGS_DIRNAME = "zConfigs"
    ZUIS_DIRNAME = "zUIs"
    ZCONFIG_FILENAME = "zConfig.yaml"
    ZMACHINE_FILENAME = "zMachine.yaml"  # System-level machine config
    ZMACHINE_USER_FILENAME = "zConfig.machine.yaml"  # User-level machine config
    ZENVIRONMENT_FILENAME = "zConfig.environment.yaml"  # User-level environment config
    ZCONFIG_DEFAULTS_FILENAME = "zConfig.defaults.yaml"
    
    # zEnv file extensions (priority order - consistent with zParser and config_zenv)
    ZENV_EXTENSIONS = [".zolo", ".yaml"]

    # Dotenv key aliases for zSpark configuration
    DOTENV_KEY_ALIASES = (
        "env_file",
        "envFile",
        "dotenv",
        "dotenv_file",
        "dotenvFile",
        "dotenv_path",
        "dotenvPath",
    )

    # Type hints for instance attributes
    app_name: str
    app_author: str
    os_type: str
    zSpark: Optional[Dict[str, Any]]
    workspace_dir: Optional[Path]
    _dotenv_path: Optional[Path]
    _log_level: Optional[str]
    _is_production: bool

    def __init__(self, zSpark_obj: Optional[Dict[str, Any]] = None) -> None:
        """Initialize cross-platform path resolver.
        
        Auto-detects OS type, validates platform support, and resolves
        workspace and dotenv paths for configuration hierarchy.
        
        Args:
            zSpark_obj: Optional configuration dictionary with path overrides
            
        Raises:
            UnsupportedOSError: If OS type is unsupported (Linux/Darwin/Windows only)
        """
        self.app_name = self.APP_NAME
        self.app_author = self.APP_AUTHOR
        self.os_type = platform.system()  # 'Linux', 'Darwin', 'Windows'
        self.zSpark = zSpark_obj if isinstance(zSpark_obj, dict) else None
        
        # Extract log level and deployment early for log-aware printing (before logger exists)
        from zOS.utils import get_log_level_from_zspark
        self._log_level = get_log_level_from_zspark(zSpark_obj)
        self._is_production = self._check_production_from_zspark(zSpark_obj)
        self._is_testing = self._check_testing_from_zspark(zSpark_obj)

        # Validate OS type
        if self.os_type not in self.VALID_OS_TYPES:
            # Import inline to avoid circular dependency
            from zSys.errors import UnsupportedOSError
            self._log_error(f"Unsupported OS type '{self.os_type}'")
            self._log_warning(f"Supported OS types: {', '.join(self.VALID_OS_TYPES)}")
            self._log_warning("Please report this issue or add support for your OS")
            raise UnsupportedOSError(self.os_type, self.VALID_OS_TYPES)

        logger.debug("[zConfigPaths] Initialized for OS: %s", self.os_type)

        # Detect workspace and dotenv path early for reuse across modules
        self.workspace_dir = self._detect_workspace_dir()
        self._dotenv_path = self._detect_dotenv_file()

        if self.workspace_dir:
            logger.debug("[zConfigPaths] Workspace directory: %s", self.workspace_dir)
        if self._dotenv_path:
            logger.debug("[zConfigPaths] Dotenv path resolved: %s", self._dotenv_path)

    # ═══════════════════════════════════════════════════════════
    # Logging Helpers (DRY) - Deployment-aware
    # ═══════════════════════════════════════════════════════════
    
    def _check_testing_from_zspark(self, zSpark_obj: Optional[Dict[str, Any]]) -> bool:
        """Early check if zSpark indicates Testing deployment (for suppressing banners)."""
        if not zSpark_obj:
            return False
        deployment = zSpark_obj.get("deployment", "")
        return str(deployment).lower() in ["testing", "info"]
    
    def _check_production_from_zspark(self, zSpark_obj: Optional[Dict[str, Any]]) -> bool:
        """Check if deployment mode is Production from zSpark (case-insensitive).
        
        This is called during __init__ before environment config exists,
        so we check zSpark directly for deployment mode.
        """
        if not zSpark_obj or not isinstance(zSpark_obj, dict):
            return False
        
        # Check for deployment in any case variation
        for key in ["deployment", "Deployment", "DEPLOYMENT"]:
            if key in zSpark_obj:
                value = str(zSpark_obj[key]).lower()
                return value == "production"
        
        return False

    def _log_info(self, message: str) -> None:
        """Log info message (suppressed in Production deployment)."""
        if not self._is_production:
            logger.info("[zConfigPaths] %s", message)

    def _log_warning(self, message: str) -> None:
        """Log warning message (suppressed in Production deployment)."""
        if not self._is_production:
            logger.warning("[zConfigPaths] %s", message)

    def _log_error(self, message: str) -> None:
        """Log error message (always shown, even in Production)."""
        logger.error("[zConfigPaths] ERROR: %s", message)

    # ═══════════════════════════════════════════════════════════
    # Workspace & dotenv detection helpers
    # ═══════════════════════════════════════════════════════════

    def _detect_workspace_dir(self) -> Optional[Path]:
        """Determine workspace directory using zSpark hint or current directory."""
        if self.zSpark:
            workspace = self.zSpark.get("zSpace")
            if workspace:
                try:
                    return Path(workspace).expanduser().resolve()
                except Exception:  # pragma: no cover - defensive fallback
                    self._log_warning(
                        f"Unable to resolve zSpace '{workspace}', defaulting to current directory"
                    )

        try:
            return Path.cwd()
        except Exception:  # pragma: no cover - defensive fallback
            return Path.home()

    def _resolve_explicit_dotenv_path(self) -> Optional[Path]:
        """Check zSpark configuration for explicitly provided dotenv path."""
        if not self.zSpark:
            return None

        for key in self.DOTENV_KEY_ALIASES:
            candidate = self.zSpark.get(key)
            if candidate:
                try:
                    return Path(candidate).expanduser().resolve()
                except Exception:  # pragma: no cover - defensive fallback
                    self._log_warning(f"Invalid dotenv path '{candidate}' from zSpark key '{key}'")
        return None

    def _detect_dotenv_file(self) -> Optional[Path]:
        """Determine dotenv file location from zSpark overrides or workspace.
        
        Detection priority:
        1. Explicit path from zSpark configuration (via DOTENV_KEY_ALIASES)
        2. .zEnv in workspace directory (primary convention)
        3. .env in workspace directory (backward compatibility)
        4. Returns .zEnv path even if neither exists (for potential creation)
        """
        explicit = self._resolve_explicit_dotenv_path()
        if explicit:
            return explicit

        if self.workspace_dir:
            # Check for .zEnv first (primary convention)
            zenv_path = self.workspace_dir / self.DOTENV_FILENAME
            if zenv_path.exists():
                return zenv_path

            # Fall back to .env for backward compatibility
            env_path = self.workspace_dir / ".env"
            if env_path.exists():
                self._log_info("Using .env file (consider migrating to .zEnv)")
                return env_path

            # Neither exists - return primary convention path for potential creation
            return zenv_path

        return None

    def get_dotenv_path(self) -> Optional[Path]:
        """Return resolved dotenv path (.zEnv or .env fallback).
        
        Returns:
            Path to dotenv file (may not exist), or None if no workspace
        """
        return self._dotenv_path

    def _find_zenv_files(self, deployment: str) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Find zEnv config files with extension auto-detection.
        
        This is the decision layer - it discovers which files exist.
        File loading is delegated to config_zenv.py (the execution layer).
        
        Args:
            deployment: Deployment environment (development, production, testing)
        
        Returns:
            tuple: (base_file_path, env_file_path) or (None, None)
        """
        base_file = None
        env_file = None
        
        # Find base file (try extensions in priority order)
        for ext in self.ZENV_EXTENSIONS:
            candidate = self.workspace_dir / f"zEnv.base{ext}"
            if candidate.exists():
                base_file = candidate
                break
        
        # Find environment file (try extensions in priority order)
        for ext in self.ZENV_EXTENSIONS:
            candidate = self.workspace_dir / f"zEnv.{deployment}{ext}"
            if candidate.exists():
                env_file = candidate
                break
        
        return base_file, env_file
    
    def load_dotenv(self, override: bool = True) -> Optional[Path]:
        """Load environment variables with STRICT zEnv priority over dotenv.
        
        THE zCLI WAY (v2.0): Priority-based loading with declarative-first guarantee:
        1. Try zEnv.base.{zolo|yaml} + zEnv.{deployment}.{zolo|yaml} (declarative, THE zCLI WAY)
        2. Fallback to .zEnv + .zEnv.{deployment} ONLY if NO config files exist
        
        IMPORTANT: If ANY zEnv config files exist (even if empty/malformed), 
        dotenv fallback is SKIPPED. This ensures declarative files always take precedence.
        
        This allows:
        - zEnv.base.zolo → declarative config (string-first, type hints, navbar, nested structures)
        - zEnv.development.zolo → dev overrides (no SSL)
        - zEnv.production.zolo → prod overrides (SSL + certs)
        - .zEnv (legacy) → backward compatibility (only if no config files)
        
        Args:
            override: Whether to override existing environment variables (default: True)
            
        Returns:
            Path to loaded file, or None if no file found/loaded
        
        Example (THE zCLI WAY):
            # zEnv.base.zolo
            ZNAVBAR:
              zVaF:
              zAccount:
                zRBAC:
                  require_role: [zAdmin]
            
            # zEnv.production.zolo (overrides)
            DEPLOYMENT: Production
            HTTP_SSL_ENABLED(bool): true
            HTTP_SSL_CERT: /etc/ssl/cert.pem
        """
        from zOS import os
        
        # ═══════════════════════════════════════════════════════════
        # PRIORITY 1: Try zEnv (ZOLO/YAML/JSON) - THE zCLI WAY
        # ═══════════════════════════════════════════════════════════
        
        # Determine deployment/environment
        deployment = "development"  # Default
        if self.zSpark:
            # Check zSpark first (highest priority)
            for key in ["deployment", "Deployment", "DEPLOYMENT", "environment", "Environment"]:
                if key in self.zSpark:
                    deployment = str(self.zSpark[key]).lower()
                    break
        
        if not deployment or deployment == "development":
            # Fallback to env var (from system or previous load)
            env_deployment = os.getenv('DEPLOYMENT') or os.getenv('ZOLO_DEPLOYMENT')
            if env_deployment:
                deployment = env_deployment.lower()
        
        # Find config files (decision layer - discovers which files exist)
        base_file, env_file = self._find_zenv_files(deployment)
        config_files_exist = base_file is not None or env_file is not None
        
        # Try loading zEnv config files
        if config_files_exist:
            try:
                from .config_zenv import zEnv
                
                workspace_dir = str(self.workspace_dir)
                zenv_loader = zEnv(workspace_dir, deployment, logger=None)  # Logger not available yet
                
                # Pass found files directly to loader (execution layer)
                loaded = zenv_loader.load_files(base_file, env_file)
                
                if loaded:
                    self._log_info(f"✅ Loaded zEnv (THE zCLI WAY) for {deployment} environment")
                    # Return whichever file was found (prefer env-specific)
                    return env_file if env_file else base_file
                else:
                    self._log_warning(f"⚠️  zEnv files exist but failed to load, skipping dotenv fallback")
                    return None
            
            except Exception as e:
                self._log_warning(f"⚠️  zEnv loading error: {e}, but config files exist - skipping dotenv fallback")
                return None
        
        # ═══════════════════════════════════════════════════════════
        # PRIORITY 2: Fallback to dotenv (legacy, backward compat)
        # Only reached if NO YAML files exist in workspace
        # ═══════════════════════════════════════════════════════════
        
        dotenv_path = self.get_dotenv_path()
        if not dotenv_path:
            self._log_info("No dotenv path resolved")
            return None

        if not dotenv_path.exists():
            self._log_warning(f"Dotenv file not found at: {dotenv_path}")
            return None

        # Load base .zEnv file
        loaded = load_dotenv(dotenv_path, override=override)
        if loaded:
            self._log_info(f"Loaded environment variables from: {dotenv_path}")
        else:
            self._log_warning(f"Dotenv file present but no variables loaded: {dotenv_path}")

        # Cascading .zEnv support (v1.5.10): Load deployment-specific overrides
        # Re-check deployment from environment (now includes .zEnv values) or zSpark
        deployment_check = None
        if self.zSpark:
            # Check zSpark first (highest priority)
            for key in ["deployment", "Deployment", "DEPLOYMENT"]:
                if key in self.zSpark:
                    deployment_check = str(self.zSpark[key])
                    break
        
        if not deployment_check:
            # Fallback to env var (from .zEnv or system)
            deployment_check = os.getenv('DEPLOYMENT')
        
        if deployment_check:
            # Try to load deployment-specific .zEnv file
            deployment_env_path = dotenv_path.parent / f".zEnv.{deployment_check.lower()}"
            
            if deployment_env_path.exists():
                deployment_loaded = load_dotenv(deployment_env_path, override=True)
                if deployment_loaded:
                    self._log_info(f"Loaded deployment-specific env: {deployment_env_path.name}")
                else:
                    self._log_warning(f"Deployment env file present but no variables loaded: {deployment_env_path.name}")

        return dotenv_path

    # ═══════════════════════════════════════════════════════════
    # Resolves standard OS locations for zolo system folders
    # ═══════════════════════════════════════════════════════════
    @property
    def system_config_dir(self) -> Path:
        r"""
        System config location (discovery only; not created).
        
        Linux/macOS: /etc/zolo-zcli
        Windows:     C:\\ProgramData\\zolo-zcli
        """
        if self.os_type in ("Linux", "Darwin"):
            # Unix-like systems use /etc for system config
            return Path(f"/etc/{self.APP_NAME}")

        # Windows: use platformdirs
        return Path(platformdirs.site_config_dir(self.app_name, self.app_author))

    @property
    def user_config_dir(self) -> Path:
        r"""
        User config location (unified with data for simplicity).

        Linux:   ~/.local/share/zolo-zcli
        macOS:   ~/Library/Application Support/zolo-zcli 
        Windows: %LOCALAPPDATA%\zolo-zcli
        
        Note: Returns same directory as user_data_dir to keep everything in one place.
        This simplifies backup, uninstall, and user management.
        """
        return Path(platformdirs.user_data_dir(self.app_name, self.app_author))

    @property
    def user_config_dir_legacy(self) -> Path:
        """
        Legacy dotfile configuration directory (backward compatibility).
        
        All OS: ~/.zolo-zcli
        
        Checked for backward compatibility with older installations.
        """
        return Path.home() / f".{self.APP_NAME}"

    @property
    def user_zconfigs_dir(self) -> Path:
        """
        User zConfigs directory for configuration files.
        
        Location: user_config_dir/zConfigs/
        Contains: zConfig.default.yaml, zConfig.dev.yaml, etc.
        """
        return self.user_config_dir / self.ZCONFIGS_DIRNAME

    @property
    def user_zuis_dir(self) -> Path:
        """
        User zUIs directory for UI definition files.
        
        Location: user_config_dir/zUIs/
        Contains: User-customized UI files for commands and walkers.
        """
        return self.user_config_dir / self.ZUIS_DIRNAME

    @property
    def user_zschemas_dir(self) -> Path:
        """
        User zSchemas directory for system schema files.
        
        Location: user_config_dir/zSchemas/
        Contains: System schema templates (e.g., zSchema.zMigration.yaml)
        """
        return self.user_config_dir / "zSchemas"

    @property
    def user_data_dir(self) -> Path:
        r"""
        User data directory (unified with config for simplicity).
        
        Linux:   ~/.local/share/zolo-zcli
        macOS:   ~/Library/Application Support/zolo-zcli
        Windows: %LOCALAPPDATA%\zolo-zcli
        
        Note: Returns same directory as user_config_dir to keep everything in one place.
        This simplifies backup, uninstall, and user management.
        """
        return Path(platformdirs.user_data_dir(self.app_name, self.app_author))

    @property
    def user_cache_dir(self) -> Path:
        r"""
        User cache directory (temporary data).
        
        Linux:   ~/.cache/zolo-zcli
        macOS:   ~/Library/Caches/zolo-zcli
        Windows: %LOCALAPPDATA%\zolo-zcli\Cache
        """
        return Path(platformdirs.user_cache_dir(self.app_name, self.app_author))

    @property
    def user_logs_dir(self) -> Path:
        r"""
        User logs directory for application logs.
        
        Linux:   ~/.local/share/zolo-zcli/logs
        macOS:   ~/Library/Application Support/zolo-zcli/logs
        Windows: %LOCALAPPDATA%\zolo-zcli\logs
        """
        return self.user_data_dir / "logs"

    # ═══════════════════════════════════════════════════════════
    # System Config Files
    # ═══════════════════════════════════════════════════════════

    @property
    def system_config_defaults(self) -> Path:
        """
        System default configuration file.
        
        Location: system_config_dir/zConfig.defaults.yaml
        Created on first run with base configuration.
        """
        return self.system_config_dir / self.ZCONFIG_DEFAULTS_FILENAME

    @property
    def system_machine_config(self) -> Path:
        """
        System machine configuration file (zMachine zVaFile).
        
        Location: system_config_dir/zMachine.yaml
        Contains machine identity and capabilities.
        """
        return self.system_config_dir / self.ZMACHINE_FILENAME

    # ═══════════════════════════════════════════════════════════
    # Config File Hierarchy
    # ═══════════════════════════════════════════════════════════

    def get_config_file_hierarchy(self) -> List[Tuple[Path, int, str]]:
        """
        Get list of config file paths to check, in priority order.
        
        Returns:
            List of (Path, priority, description) tuples
            
        Config Hierarchy (lowest to highest priority):
        1. System defaults (zConfig.defaults.yaml) - Base configuration
        2. User config (OS-native) - Per-user overrides
        3. User config (legacy) - Backward compatibility with ~/.zolo-zcli
        4. Environment variables (.zEnv or .env) - Workspace-specific runtime config
        5. Session runtime - In-memory overrides (handled by zSession subsystem)
        
        Note: Dotenv detection auto-discovers .zEnv (primary) or .env (compat).
        """
        configs = []

        # 1. System defaults (lowest priority - base config)
        if self.system_config_defaults.exists():
            configs.append((self.system_config_defaults, 1, "system-defaults"))

        # 2. User config (primary native path)
        user_config = self.user_config_dir / self.ZCONFIGS_DIRNAME / self.ZCONFIG_FILENAME
        if user_config.exists():
            configs.append((user_config, 2, "user"))

        # 3. User config (legacy dotfile path - backward compat)
        user_config_legacy = self.user_config_dir_legacy / self.ZCONFIG_FILENAME
        if user_config_legacy.exists():
            configs.append((user_config_legacy, 3, "user-legacy"))

        # 4. Environment variables / dotenv (highest priority before runtime overrides)
        dotenv_path = self.get_dotenv_path()
        if dotenv_path:
            if dotenv_path.exists():
                configs.append((dotenv_path, 4, "env-dotenv"))
            else:
                self._log_warning(f"Dotenv path resolved but file missing: {dotenv_path}")
        else:
            self._log_info("No dotenv path detected for hierarchy")

        # Note: Session runtime overrides (highest priority) are handled
        # in-memory by zSession subsystem, not in this file hierarchy

        # Sort by priority
        configs.sort(key=lambda x: x[1])

        return configs

    def ensure_user_config_dir(self) -> Path:
        """Ensure user config directory exists.
        
        Creates the directory if it doesn't exist.
        
        Returns:
            Path to the user config directory
        """
        config_dir = self.user_config_dir
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            self._log_info(f"Created user config directory: {config_dir}")

        return config_dir

    def get_app_path(self, app_name: str, subpath: str = "") -> Path:
        """
        Get path for app-specific storage.
        
        Args:
            app_name: Application name (e.g., "zCloud")
            subpath: Optional subpath within app directory (e.g., "storage/users")
        
        Returns:
            Path: ~/Library/Application Support/zolo-zcli/Apps/{app_name}/{subpath}
        
        Example:
            >>> paths.get_app_path("zCloud")
            Path("~/Library/Application Support/zolo-zcli/Apps/zCloud")
            
            >>> paths.get_app_path("zCloud", "storage/users")
            Path("~/Library/Application Support/zolo-zcli/Apps/zCloud/storage/users")
        
        Note:
            - Does NOT create directories (use ensure_app_directory for that)
            - Returns path even if directory doesn't exist
            - Used by app code to construct storage paths
        """
        app_root = self.user_data_dir / "Apps" / app_name
        if subpath:
            return app_root / subpath
        return app_root

    def get_info(self) -> Dict[str, str]:
        """
        Get path information for debugging.
        
        Returns:
            Dict with all path information
        """
        return {
            "os": self.os_type,
            "system_config_dir": str(self.system_config_dir),
            "system_config_defaults": str(self.system_config_defaults),
            "system_machine_config": str(self.system_machine_config),
            "user_config_dir": str(self.user_config_dir),
            "user_config_legacy": str(self.user_config_dir_legacy),
            "user_zconfigs_dir": str(self.user_zconfigs_dir),
            "user_zuis_dir": str(self.user_zuis_dir),
            "user_data_dir": str(self.user_data_dir),
            "user_cache_dir": str(self.user_cache_dir),
            "user_logs_dir": str(self.user_logs_dir),
        }
