# zOS/machine/config.py
"""Machine configuration for Zolo ecosystem."""
from typing import Any, Dict, Optional
from pathlib import Path
import logging

from zOS.paths import get_ecosystem_root
from .detectors import auto_detect_machine, create_user_machine_config

# Module-level logger
logger = logging.getLogger("zolo.os.machine")


class zMachine:
    """
    Machine-level configuration (OS-wide singleton).
    
    Auto-detects system capabilities and user preferences.
    Used by all Zolo products (zKernel, zLSP, etc.)
    
    Example:
        >>> machine = zMachine()
        >>> print(machine.get('os'))
        'Darwin'
        >>> print(machine.get('cpu_cores'))
        10
    """
    
    _instance = None
    _config: Dict[str, Any] = None
    
    def __new__(cls):
        """Singleton - only detect once per session."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize machine config (lazy - only on first access)."""
        if self._config is None:
            self._config = self._load_or_detect()
    
    def _load_or_detect(self) -> Dict[str, Any]:
        """Load from file or auto-detect."""
        config_path = get_ecosystem_root() / "zConfig.machine.zolo"
        
        # Try to load existing config
        if config_path.exists():
            try:
                logger.debug("[zMachine] Loading config from %s", config_path)
                # Use zlsp parser for .zolo files
                try:
                    from core.parser import load
                    data = load(str(config_path))
                    if data and 'zMachine' in data:
                        # Flatten nested structure for backward compatibility
                        zmachine = data['zMachine']
                        flat_config = {}
                        
                        # Flatten machine_identity
                        if 'machine_identity' in zmachine:
                            flat_config.update(zmachine['machine_identity'])
                        
                        # Flatten python_runtime
                        if 'python_runtime' in zmachine:
                            runtime = zmachine['python_runtime']
                            flat_config['python_version'] = runtime.get('version')
                            flat_config['python_impl'] = runtime.get('implementation')
                            flat_config['python_build'] = runtime.get('build')
                            flat_config['python_compiler'] = runtime.get('compiler')
                            flat_config['libc_ver'] = runtime.get('libc_ver')
                            flat_config['python_executable'] = runtime.get('executable')
                        
                        # Flatten user_preferences
                        if 'user_preferences' in zmachine:
                            flat_config.update(zmachine['user_preferences'])
                        
                        # Flatten time_date_formatting
                        if 'time_date_formatting' in zmachine:
                            flat_config.update(zmachine['time_date_formatting'])
                        
                        # Flatten user_paths
                        if 'user_paths' in zmachine:
                            flat_config.update(zmachine['user_paths'])
                        
                        # Flatten cpu
                        if 'cpu' in zmachine:
                            cpu = zmachine['cpu']
                            flat_config['processor'] = cpu.get('processor')
                            flat_config['cpu_cores'] = cpu.get('cores_total')
                            flat_config['cpu_physical'] = cpu.get('cores_physical')
                            flat_config['cpu_logical'] = cpu.get('cores_logical')
                            flat_config['cpu_performance'] = cpu.get('cores_performance')
                            flat_config['cpu_efficiency'] = cpu.get('cores_efficiency')
                        
                        # Flatten memory
                        if 'memory' in zmachine:
                            flat_config['memory_gb'] = zmachine['memory'].get('total_gb')
                        
                        # Flatten gpu
                        if 'gpu' in zmachine:
                            gpu = zmachine['gpu']
                            flat_config['gpu_available'] = gpu.get('available')
                            flat_config['gpu_type'] = gpu.get('type')
                            flat_config['gpu_vendor'] = gpu.get('vendor')
                            flat_config['gpu_memory_gb'] = gpu.get('memory_gb')
                            flat_config['gpu_compute'] = gpu.get('compute', [])
                        
                        # Flatten network
                        if 'network' in zmachine:
                            network = zmachine['network']
                            flat_config['network_interfaces'] = network.get('interfaces', [])
                            flat_config['network_primary'] = network.get('primary')
                            flat_config['network_ip_local'] = network.get('ip_local')
                            flat_config['network_mac_address'] = network.get('mac_address')
                            flat_config['network_gateway'] = network.get('gateway')
                            flat_config['network_ip_public'] = network.get('ip_public')
                        
                        # Add launch_commands if present (optional)
                        if 'launch_commands' in zmachine:
                            flat_config['launch_commands'] = zmachine['launch_commands']
                        
                        # Add custom if present (optional)
                        if 'custom' in zmachine:
                            flat_config['custom'] = zmachine['custom']
                        
                        return flat_config
                except ImportError:
                    # Fallback to yaml if zolo not available
                    logger.warning("[zMachine] zolo parser not available, falling back to yaml")
                    import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'zMachine' in data:
                        return data['zMachine']
            except Exception as e:
                logger.warning("[zMachine] Failed to load config: %s, will auto-detect", e)
        
        # Auto-detect and create config
        logger.info("[zMachine] Auto-detecting system capabilities...")
        machine_info = auto_detect_machine(is_production=False)
        self._save_config(config_path, machine_info)
        return machine_info
    
    def _save_config(self, path: Path, config: Dict[str, Any]) -> None:
        """Save config to .zolo file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use the detectors module to generate properly formatted .zolo with comments
            create_user_machine_config(path, config)
            
            logger.info("[zMachine] Saved config to %s", path)
        except Exception as e:
            logger.error("[zMachine] Failed to save config: %s", e)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get machine config value."""
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete machine config."""
        return self._config.copy()
    
    def refresh(self) -> None:
        """Force re-detection (useful for testing or config changes)."""
        logger.info("[zMachine] Forcing re-detection...")
        self._config = None
        self._config = self._load_or_detect()


# Convenience function
def get_machine_info() -> zMachine:
    """Get machine config instance (singleton)."""
    return zMachine()
