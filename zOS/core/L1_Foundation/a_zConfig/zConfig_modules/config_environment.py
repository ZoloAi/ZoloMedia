# zCLI/subsystems/zConfig/zConfig_modules/config_environment.py
"""Environment-level configuration management for deployment and runtime settings."""

from zOS import os, sys, yaml, Any, Dict, Optional
from zOS.utils import print_ready_message
from .helpers import create_default_env_config, load_config_with_override
from .config_paths import zConfigPaths

# Module constants
LOG_PREFIX = "[EnvironmentConfig]"
READY_MESSAGE = "zEnv Ready"
YAML_KEY = "zEnv"
SUBSYSTEM_NAME = "EnvironmentConfig"

# Environment variable names
ENV_VAR_DEPLOYMENT = "ZOLO_DEPLOYMENT"
ENV_VAR_DEPLOYMENT_ALT = "ZOLO_ENV"

# Config keys
KEY_DEPLOYMENT = "deployment"
KEY_ROLE = "role"

# Default values
DEFAULT_DEPLOYMENT = "Production"  # Changed in v1.5.9: Clean UI for most users (Development is opt-in for demos)
DEFAULT_ROLE = "production"

# Deprecated deployment mode mappings (for backward compatibility)
DEPRECATED_DEPLOYMENTS = {
    "Debug": "Development",
    "Info": "Testing"
}

class EnvironmentConfig:
    """Manages environment-specific settings and deployment configuration."""

    # Type hints for instance attributes
    paths: zConfigPaths
    env: Dict[str, Any]
    in_venv: bool
    venv_path: Optional[str]
    system_env: Dict[str, str]
    zSpark: Optional[Dict[str, Any]]

    def __init__(self, paths: zConfigPaths, zSpark_obj: Optional[Dict[str, Any]] = None) -> None:
        """Initialize environment configuration with paths and optional zSpark override.
        
        Args:
            paths: zConfigPaths instance for file resolution
            zSpark_obj: Optional zSpark configuration dict (highest priority)
        """
        self.paths = paths
        self.zSpark = zSpark_obj

        # Detect environment types
        self._detect_environments()

        # Get minimal defaults first
        self.env = self._get_defaults()

        # Load and override from config file (check exists, create if missing)
        load_config_with_override(
            self.paths,
            YAML_KEY,
            create_default_env_config,
            self.env,
            self.paths.ZENVIRONMENT_FILENAME,
            SUBSYSTEM_NAME,
            log_level=paths._log_level
        )
        
        # LAYER 5: zSpark override (highest priority in hierarchy)
        self._apply_zspark_overrides()

        print_ready_message(READY_MESSAGE, color="CONFIG", is_production=paths._is_production, is_testing=paths._is_testing)

    def _detect_environments(self) -> None:
        """Detect virtual environment and system environment."""
        # Check production mode from paths (which checked zSpark)
        is_production = self.paths._is_production
        
        # Load dotenv file (if available) before capturing environment snapshot
        dotenv_path = self.paths.load_dotenv()
        if dotenv_path and not is_production:
            print(f"{LOG_PREFIX} Dotenv loaded from: {dotenv_path}")

        # Detect if running in virtual environment
        self.in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )

        # Store environment info
        self.venv_path = sys.prefix if self.in_venv else None
        self.system_env = dict(os.environ)

        # Print detection results
        if not is_production:
            if self.in_venv:
                print(f"{LOG_PREFIX} Virtual environment detected: {self.venv_path}")
            else:
                print(f"{LOG_PREFIX} Running in system environment")

    def _get_defaults(self) -> Dict[str, Any]:
        """Get minimal hardcoded default environment values (first run fallback).
        
        Hierarchy (lowest to highest priority):
        1. Hardcoded defaults
        2. Environment variables (ZOLO_DEPLOYMENT, ZOLO_ENV)
        """
        is_production = self.paths._is_production
        
        if not is_production:
            print(f"{LOG_PREFIX} Loading environment defaults...")

        env = {
            # Minimal defaults - comprehensive config is in zConfig.environment.yaml
            KEY_DEPLOYMENT: os.getenv(ENV_VAR_DEPLOYMENT) or os.getenv(ENV_VAR_DEPLOYMENT_ALT) or DEFAULT_DEPLOYMENT,
            KEY_ROLE: DEFAULT_ROLE,
        }

        if not is_production:
            print(f"{LOG_PREFIX} Environment: {env[KEY_DEPLOYMENT]} ({env[KEY_ROLE]})")

        return env
    
    def _apply_zspark_overrides(self) -> None:
        """Apply zSpark overrides (Layer 5 - highest priority in hierarchy).
        
        Checks zSpark for deployment and other environment overrides.
        This is called AFTER loading from file, so zSpark has final say.
        """
        if not self.zSpark or not isinstance(self.zSpark, dict):
            return
        
        is_production = self.paths._is_production
        
        # Check for deployment override (case-insensitive)
        for key in ["deployment", "Deployment", "DEPLOYMENT"]:
            if key in self.zSpark:
                deployment_value = str(self.zSpark[key]) if self.zSpark[key] else None
                if deployment_value:
                    # Handle deprecated deployment modes with migration
                    if deployment_value in DEPRECATED_DEPLOYMENTS:
                        from zOS.utils import Colors
                        new_value = DEPRECATED_DEPLOYMENTS[deployment_value]
                        if not is_production:
                            print(f"{Colors.WARNING}⚠️  Deprecated deployment: '{deployment_value}' → Use '{new_value}' instead{Colors.RESET}")
                        deployment_value = new_value
                    
                    self.env[KEY_DEPLOYMENT] = deployment_value
                    if not is_production:
                        print(f"{LOG_PREFIX} Deployment overridden by zSpark: {deployment_value}")
                break

    def get(self, key: str, default: Any = None) -> Any:
        """Get environment config value by key, returning default if not found."""
        return self.env.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all environment configuration values."""
        return self.env.copy()

    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with fallback to default."""
        return self.system_env.get(key, default)

    def is_in_venv(self) -> bool:
        """Check if running in virtual environment."""
        return self.in_venv

    def get_venv_path(self) -> Optional[str]:
        """Get virtual environment path if running in venv."""
        return self.venv_path

    def is_production(self) -> bool:
        """Check if running in Production deployment mode.
        
        Returns:
            bool: True if deployment is "Production", False otherwise
        """
        deployment = self.env.get(KEY_DEPLOYMENT, "")
        return deployment.lower() == "production"
    
    def is_testing(self) -> bool:
        """Check if running in Testing deployment mode.
        
        Returns:
            bool: True if deployment is "Testing", False otherwise
        """
        deployment = self.env.get(KEY_DEPLOYMENT, "")
        return deployment.lower() in ["testing", "info"]  # Include deprecated "Info"
    
    def is_development(self) -> bool:
        """Check if running in Development or Testing deployment mode.
        
        Returns:
            bool: True if deployment is "Development" or "Testing", False otherwise
        """
        deployment = self.env.get(KEY_DEPLOYMENT, "")
        return deployment.lower() in ["development", "testing", "debug", "info"]  # Include deprecated modes

    def save_user_config(self) -> bool:
        """Save current environment config to user's zConfig.environment.yaml."""
        try:
            path = self.paths.user_zconfigs_dir / self.paths.ZENVIRONMENT_FILENAME
            path.parent.mkdir(parents=True, exist_ok=True)

            content = {YAML_KEY: self.env}

            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, default_flow_style=False, sort_keys=False)

            print(f"{LOG_PREFIX} Saved environment config to: {path}")
            return True

        except Exception as e:
            print(f"{LOG_PREFIX} Failed to save environment config: {e}")
            return False
