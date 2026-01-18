# zCLI/subsystems/zConfig/zConfig_modules/config_machine.py
"""Machine-level configuration management for system identity and preferences."""

from zOS import yaml, Any, Dict
from zOS.utils import print_ready_message
from .helpers import auto_detect_machine, create_user_machine_config, load_config_with_override
from .config_paths import zConfigPaths

# Module constants
LOG_PREFIX = "[MachineConfig]"
READY_MESSAGE = "zMachine Ready"
YAML_KEY = "zMachine"
SUBSYSTEM_NAME = "MachineConfig"

class MachineConfig:
    """Machine-level configuration for system identity and user preferences.
    
    Auto-detects capabilities (browser, IDE, shell, memory, CPU) and loads user 
    overrides from zConfig.machine.yaml. Persisted via config_persistence.py.
    """

    # Type hints for instance attributes
    paths: zConfigPaths
    machine: Dict[str, Any]

    def __init__(self, paths: zConfigPaths) -> None:
        """Initialize with auto-detection and load user preferences from zConfig.machine.yaml."""
        self.paths = paths

        # Auto-detect machine information with deployment-aware output
        self.machine = auto_detect_machine(log_level=paths._log_level, is_production=paths._is_production)
        
        # Add user_data_dir from paths (needed for zPath display formatting)
        self.machine["user_data_dir"] = str(paths.user_data_dir)

        # Load and override from config file (check exists, create if missing)
        load_config_with_override(
            self.paths,
            YAML_KEY,
            create_user_machine_config,
            self.machine,
            self.paths.ZMACHINE_USER_FILENAME,
            SUBSYSTEM_NAME,
            log_level=paths._log_level
        )

        # Print ready message (deployment-aware)
        print_ready_message(READY_MESSAGE, color="CONFIG", is_production=paths._is_production, is_testing=paths._is_testing)

    def get(self, key: str, default: Any = None) -> Any:
        """Get machine config value by key, returning default if not found."""
        return self.machine.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get complete machine configuration."""
        return self.machine.copy()

    def update(self, key: str, value: Any) -> None:
        """Update machine config value (runtime only)."""
        self.machine[key] = value

    def save_user_config(self) -> bool:
        """Save current machine config to user's zConfig.machine.yaml."""
        try:
            path = self.paths.user_zconfigs_dir / self.paths.ZMACHINE_USER_FILENAME
            path.parent.mkdir(parents=True, exist_ok=True)

            content = {YAML_KEY: self.machine}

            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, default_flow_style=False, sort_keys=False)

            print(f"{LOG_PREFIX} Saved machine config to: {path}")
            return True

        except Exception as e:
            print(f"{LOG_PREFIX} Failed to save machine config: {e}")
            return False
