# zCLI/subsystems/zConfig/zConfig_modules/config_persistence.py
"""Configuration persistence for saving/loading zCLI config changes."""

from zOS import Colors, Any, Dict, List, Optional
from .config_session import SESSION_KEY_ZMACHINE

# Module Constants

# Display Markers
_MARKER_EDITABLE = "[EDIT] "
_MARKER_LOCKED = "[LOCK] "

# Category Names
_CATEGORY_IDENTITY = "Identity (Auto-detected)"
_CATEGORY_USER_PREFS = "User Preferences (Editable)"
_CATEGORY_SYSTEM_INFO = "System Info (Auto-detected)"

# Valid Configuration Values
_VALID_DEPLOYMENTS = ["Debug", "Development", "Testing", "Production"]
_DEPRECATED_DEPLOYMENTS = ["Info"]  # Mapped to Development
_VALID_ROLES = ["development", "production", "testing", "staging"]
_VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Machine Config Keys (Editable)
_EDITABLE_MACHINE_KEYS = [
    # User tool preferences
    "browser", "ide", "terminal", "shell",
    "image_viewer", "video_player", "audio_player",
    # Time/date preferences
    "time_format", "date_format", "datetime_format",
    # Resource allocation limits (optional)
    "cpu_cores_limit", "memory_gb_limit",
]

# Machine Config Keys (By Category) - DEPRECATED: Now using dynamic categorization
# Kept for backward compatibility only
_MACHINE_KEYS_IDENTITY = ["os", "hostname", "architecture", "python_version", "processor"]
_MACHINE_KEYS_USER_PREFS = ["browser", "ide", "terminal", "shell"]
_MACHINE_KEYS_SYSTEM_INFO = ["cpu_cores", "memory_gb", "os_version", "os_name"]

# Environment Config Keys (Editable)
_EDITABLE_ENVIRONMENT_KEYS = [
    # Basic environment settings
    "deployment", "role", "datacenter", "cluster", "node_id",
    # Network settings
    "network.host", "network.port", "network.external_host", "network.external_port",
    # Security settings
    "security.require_auth", "security.allow_anonymous", "security.ssl_enabled",
    # Logging settings
    "logging.level", "logging.format", "logging.file_enabled", "logging.file_path",
    # Performance settings
    "performance.max_workers", "performance.cache_size", "performance.cache_ttl", "performance.timeout",
]

# Error Messages
_ERROR_INVALID_KEY = "Invalid {config_type} config key: {key}"
_ERROR_EDITABLE_KEYS = "Editable keys: {keys}"
_ERROR_FAILED_TO_SAVE = "Failed to save {config_type} config"
_ERROR_MUST_BE_POSITIVE = "{key} must be positive"
_ERROR_MUST_BE_NUMBER = "{key} must be a number"
_ERROR_INVALID_DEPLOYMENT = "Invalid deployment: {value}. Must be one of: {valid_values}"
_ERROR_INVALID_ROLE = "Invalid role: {value}. Must be one of: {valid_values}"
_ERROR_INVALID_LOG_LEVEL = "Invalid log level: {value}. Must be one of: {valid_values}"
_ERROR_RESET_REQUIRES_CONFIRMATION = "Full reset requires explicit confirmation"
_ERROR_RESET_USE_KEY = "Use: config machine --reset [key] to reset specific key"
_ERROR_RESET_NOT_IMPLEMENTED = "{config_type} config reset not yet implemented"

# Success Messages
_SUCCESS_UPDATED = "Updated {config_type} config: {key}"
_SUCCESS_RESET = "Reset {config_type} config: {key}"
_SUCCESS_CHANGE_DETAIL = "{old_value} → {new_value}"
__SUCCESS_RESET_DETAIL = "{old_value} → {new_value} (auto-detected)"
_SUCCESS_SAVED_TO = "Saved to: {file_path}"

# Display Headers
_HEADER_SEPARATOR = "=" * 70
_HEADER_MACHINE_CONFIG = "Machine Configuration"
_HEADER_ENVIRONMENT_CONFIG = "Environment Configuration"
_HEADER_ZC_ENV_SETTINGS = "zCLI Environment Settings:"
_HEADER_CONFIG_FILE = "Config file: {file_path}"


class ConfigPersistence:
    """Manages configuration persistence to files - handles only editable zCLI config parts."""

    def __init__(self, machine_config: Any, environment_config: Any, paths: Any, zcli: Optional[Any] = None) -> None:
        """Initialize config persistence with dependencies."""
        self.machine = machine_config
        self.environment = environment_config
        self.paths = paths
        self.zcli = zcli
    
    # ═══════════════════════════════════════════════════════════
    # Machine Config Persistence (User Preferences Only)
    # ═══════════════════════════════════════════════════════════
    
    def persist_machine(self, key: Optional[str] = None, value: Optional[Any] = None, 
                       show: bool = False, reset: bool = False) -> bool:
        """
        Persist machine configuration changes to user's zConfig.machine.yaml.
        
        Only handles USER-EDITABLE preferences, not auto-detected characteristics.
        
        Args:
            key: Machine config key (e.g., 'browser', 'ide', 'terminal')
            value: New value
            show: If True, show current values
            reset: If True, reset to auto-detected defaults
            
        Returns:
            bool: Success status
        """
        # Reset to defaults
        if reset:
            return self._reset_machine_config(key)
        
        # Show current values
        if show or (key is None and value is None):
            return self.show_machine_config()
        
        # Validate key is user-editable
        if key not in _EDITABLE_MACHINE_KEYS:
            self._handle_error(
                _ERROR_INVALID_KEY.format(config_type="machine", key=key),
                _ERROR_EDITABLE_KEYS.format(keys=', '.join(_EDITABLE_MACHINE_KEYS))
            )
            return False
        
        # Get current value
        current_value = self.machine.get(key)
        
        # Validate value (if applicable)
        validation_result = self._validate_machine_value(key, value)
        if not validation_result["valid"]:
            self._handle_error(validation_result['error'])
            return False
        
        # Update runtime config
        self.machine.update(key, value)
        self._update_session_machine(key, value)
        
        # Persist to disk
        success = self.machine.save_user_config()
        
        if success:
            # Show success message
            user_config_path = self.paths.user_zconfigs_dir / self.paths.ZMACHINE_USER_FILENAME
            self._handle_success(
                _SUCCESS_UPDATED.format(config_type="machine", key=key),
                _SUCCESS_CHANGE_DETAIL.format(old_value=current_value, new_value=value),
                str(user_config_path)
            )
        else:
            self._handle_error(_ERROR_FAILED_TO_SAVE.format(config_type="machine"))
        
        return success

    # ═══════════════════════════════════════════════════════════
    # Environment Config Persistence (zCLI Environment Settings)
    # ═══════════════════════════════════════════════════════════
    
    def persist_environment(self, key: Optional[str] = None, value: Optional[Any] = None, 
                           show: bool = False, reset: bool = False) -> bool:
        """
        Persist environment configuration changes to user's zConfig.environment.yaml.
        
        Handles zCLI-specific environment settings (deployment, logging, etc.).
        Does NOT handle system environment variables or virtual environments.
        
        Args:
            key: Environment config key (e.g., 'deployment', 'logging.level')
            value: New value
            show: If True, show current values
            reset: If True, reset to defaults
            
        Returns:
            bool: Success status
        """
        # Reset to defaults
        if reset:
            return self._reset_environment_config(key)
        
        # Show current values
        if show or (key is None and value is None):
            return self.show_environment_config()
        
        # Validate key is user-editable
        if key not in _EDITABLE_ENVIRONMENT_KEYS:
            self._handle_error(
                _ERROR_INVALID_KEY.format(config_type="environment", key=key),
                _ERROR_EDITABLE_KEYS.format(keys=', '.join(_EDITABLE_ENVIRONMENT_KEYS))
            )
            return False
        
        # Get current value
        current_value = self.environment.get(key)
        
        # Validate value (if applicable)
        validation_result = self._validate_environment_value(key, value)
        if not validation_result["valid"]:
            self._handle_error(validation_result['error'])
            return False
        
        # Update runtime config
        self.environment.env[key] = value
        
        # Persist to disk
        success = self.environment.save_user_config()
        
        if success:
            # Show success message
            user_config_path = self.paths.user_zconfigs_dir / self.paths.ZENVIRONMENT_FILENAME
            self._handle_success(
                _SUCCESS_UPDATED.format(config_type="environment", key=key),
                _SUCCESS_CHANGE_DETAIL.format(old_value=current_value, new_value=value),
                str(user_config_path)
            )
        else:
            self._handle_error(_ERROR_FAILED_TO_SAVE.format(config_type="environment"))
        
        return success

    # ═══════════════════════════════════════════════════════════
    # Machine Config Helpers
    # ═══════════════════════════════════════════════════════════
    
    def _reset_machine_config(self, key: Optional[str] = None) -> bool:
        """
        Reset machine configuration to auto-detected defaults.
        
        Args:
            key: Specific key to reset, or None to reset all
            
        Returns:
            bool: Success status
        """
        from .helpers import auto_detect_machine
        
        # Get fresh auto-detected values
        auto_detected = auto_detect_machine()
        
        user_config_path = self.paths.user_zconfigs_dir / self.paths.ZMACHINE_USER_FILENAME
        
        if key:
            # Reset specific key
            if key not in _EDITABLE_MACHINE_KEYS:
                self._handle_error(_ERROR_INVALID_KEY.format(config_type="machine", key=key))
                return False
            
            current_value = self.machine.get(key)
            default_value = auto_detected.get(key)
            
            # Update runtime and persist
            self.machine.update(key, default_value)
            self._update_session_machine(key, default_value)
            success = self.machine.save_user_config()
            
            if success:
                self._handle_success(
                    _SUCCESS_RESET.format(config_type="machine", key=key),
                    _SUCCESS_RESET_DETAIL.format(old_value=current_value, new_value=default_value),
                    str(user_config_path)
                )
            else:
                self._handle_error(_ERROR_FAILED_TO_SAVE.format(config_type="machine"))
            
            return success
        else:
            # Reset ALL keys - require explicit confirmation
            self._handle_error(
                _ERROR_RESET_REQUIRES_CONFIRMATION,
                _ERROR_RESET_USE_KEY
            )
            return False

    def _categorize_machine_fields(self, machine: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Dynamically categorize machine config fields based on patterns.
        
        Auto-discovers all fields and groups them intelligently by:
        - Identity: os, hostname, architecture, python*, zcli*, username
        - User Tools: browser, ide, *_viewer, *_player, terminal, shell, *_format
        - Hardware: cpu_*, memory_*, gpu_*
        - Network: network_*
        - Paths: home, lang, timezone
        
        Args:
            machine: Machine configuration dictionary
            
        Returns:
            Dict mapping category names to lists of field keys
            
        Benefits:
            - Zero maintenance: New detector fields automatically appear
            - Complete visibility: Shows ALL fields, not just hardcoded subset
            - Smart grouping: Uses prefix patterns for logical organization
        """
        categories = {
            "Identity (Auto-detected)": [],
            "User Tools & Preferences (Editable)": [],
            "Hardware Capabilities (Auto-detected)": [],
            "Network Configuration (Auto-detected)": [],
            "Environment & Paths (Auto-detected)": [],
        }
        
        for key in sorted(machine.keys()):
            # Skip verbose/internal fields that clutter display
            if key in ['path', 'cwd', 'python_build', 'python_compiler', 'libc_ver']:
                continue
            
            # Categorize by prefix/suffix patterns
            if (key.startswith(('os', 'hostname', 'architecture', 'python', 'zcli', 'processor')) 
                or key == 'username'):
                categories["Identity (Auto-detected)"].append(key)
                
            elif (key in ['browser', 'ide', 'terminal', 'shell'] 
                  or key.endswith(('_viewer', '_player', '_format'))):
                categories["User Tools & Preferences (Editable)"].append(key)
                
            elif key.startswith(('cpu_', 'memory_', 'gpu_')):
                categories["Hardware Capabilities (Auto-detected)"].append(key)
                
            elif key.startswith('network_'):
                categories["Network Configuration (Auto-detected)"].append(key)
                
            elif key in ['home', 'lang', 'timezone']:
                categories["Environment & Paths (Auto-detected)"].append(key)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def show_machine_config(self) -> bool:
        """
        Display current machine configuration with dynamic field discovery.
        
        Uses pattern-based categorization to automatically show ALL detected fields,
        not just a hardcoded subset. New detector fields appear automatically.
        """
        machine = self.machine.get_all()
        
        # Layer 0: Always use print (zDisplay not available yet)
        print(f"\n{Colors.CONFIG}{_HEADER_SEPARATOR}{Colors.RESET}")
        print(f"{Colors.CONFIG}{_HEADER_MACHINE_CONFIG}{Colors.RESET}")
        print(f"{Colors.CONFIG}{_HEADER_SEPARATOR}{Colors.RESET}")
        
        # Dynamically categorize all fields
        categories = self._categorize_machine_fields(machine)
        
        for category, keys in categories.items():
            print(f"\n{Colors.CONFIG}{category}:{Colors.RESET}")
            for key in keys:
                value = machine.get(key, "N/A")
                editable = key in _EDITABLE_MACHINE_KEYS
                marker = _MARKER_EDITABLE if editable else _MARKER_LOCKED
                
                # Format value for readability
                if isinstance(value, bool):
                    value_str = "true" if value else "false"
                elif isinstance(value, list):
                    if not value:
                        value_str = "[]"
                    elif len(value) == 1:
                        value_str = str(value[0])
                    else:
                        value_str = ", ".join(str(v) for v in value)
                elif value is None:
                    value_str = "null"
                else:
                    value_str = str(value)
                
                print(f"  {marker}{key}: {value_str}")
        
        # Show file location
        user_config_path = self.paths.user_zconfigs_dir / self.paths.ZMACHINE_USER_FILENAME
        print(f"\n{Colors.CONFIG}{_HEADER_CONFIG_FILE.format(file_path=user_config_path)}{Colors.RESET}")
        print(f"{Colors.CONFIG}{_HEADER_SEPARATOR}{Colors.RESET}\n")
        
        return True

    def _get_editable_machine_keys(self) -> List[str]:
        """
        Get list of user-editable machine config keys.
        
        Only includes preferences that users can reasonably override.
        Excludes auto-detected characteristics like OS, hostname, etc.
        
        Returns:
            List of editable key names
        """
        return _EDITABLE_MACHINE_KEYS

    def _validate_machine_value(self, key: str, value: Any) -> Dict[str, Any]:
        """
        Validate machine config value.
        
        Args:
            key: Config key being validated
            value: Value to validate
            
        Returns:
            Dict with 'valid' (bool) and 'error' (str or None) keys
        """
        # Numeric validation
        if key in ["cpu_cores", "memory_gb"]:
            try:
                int_value = int(value)
                if int_value <= 0:
                    return {"valid": False, "error": _ERROR_MUST_BE_POSITIVE.format(key=key)}
            except ValueError:
                return {"valid": False, "error": _ERROR_MUST_BE_NUMBER.format(key=key)}
        
        # All validations passed
        return {"valid": True, "error": None}

    # ═══════════════════════════════════════════════════════════
    # Environment Config Helpers
    # ═══════════════════════════════════════════════════════════
    
    def _reset_environment_config(self, key: Optional[str] = None) -> bool:  # pylint: disable=unused-argument
        """
        Reset environment configuration to defaults.
        
        Args:
            key: Specific key to reset, or None to reset all
            
        Returns:
            bool: Success status
        """
        # TODO: Implement environment config reset
        self._handle_error(_ERROR_RESET_NOT_IMPLEMENTED.format(config_type="Environment"))
        return False

    def show_environment_config(self) -> bool:
        """Display current environment configuration."""
        env = self.environment.get_all()
        
        # Layer 0: Always use print (zDisplay not available yet)
        print(f"\n{Colors.CONFIG}{_HEADER_SEPARATOR}{Colors.RESET}")
        print(f"{Colors.CONFIG}{_HEADER_ENVIRONMENT_CONFIG}{Colors.RESET}")
        print(f"{Colors.CONFIG}{_HEADER_SEPARATOR}{Colors.RESET}")
        
        # Show environment settings
        print(f"\n{Colors.CONFIG}{_HEADER_ZC_ENV_SETTINGS}{Colors.RESET}")
        for key, value in env.items():
            print(f"  {_MARKER_EDITABLE}{key}: {value}")
        
        # Show file location
        user_config_path = self.paths.user_zconfigs_dir / self.paths.ZENVIRONMENT_FILENAME
        print(f"\n{Colors.CONFIG}{_HEADER_CONFIG_FILE.format(file_path=user_config_path)}{Colors.RESET}")
        print(f"{Colors.CONFIG}{_HEADER_SEPARATOR}{Colors.RESET}\n")
        
        return True

    def _get_editable_environment_keys(self) -> List[str]:
        """
        Get list of user-editable environment config keys.
        
        Returns:
            List of editable key names
        """
        return _EDITABLE_ENVIRONMENT_KEYS

    def _validate_environment_value(self, key: str, value: Any) -> Dict[str, Any]:
        """
        Validate environment config value.
        
        Args:
            key: Config key being validated
            value: Value to validate
            
        Returns:
            Dict with 'valid' (bool) and 'error' (str or None) keys
        """
        # Deployment validation
        if key == "deployment":
            if value not in _VALID_DEPLOYMENTS:
                return {
                    "valid": False,
                    "error": _ERROR_INVALID_DEPLOYMENT.format(
                        value=value,
                        valid_values=', '.join(_VALID_DEPLOYMENTS)
                    )
                }
        
        # Role validation
        elif key == "role":
            if value not in _VALID_ROLES:
                return {
                    "valid": False,
                    "error": _ERROR_INVALID_ROLE.format(
                        value=value,
                        valid_values=', '.join(_VALID_ROLES)
                    )
                }
        
        # Logging level validation
        elif key == "logging.level":
            if value.upper() not in _VALID_LOG_LEVELS:
                return {
                    "valid": False,
                    "error": _ERROR_INVALID_LOG_LEVEL.format(
                        value=value,
                        valid_values=', '.join(_VALID_LOG_LEVELS)
                    )
                }
        
        # Numeric validation for performance settings
        elif key in ["performance.max_workers", "performance.cache_size", "performance.cache_ttl", "performance.timeout"]:
            try:
                int_value = int(value)
                if int_value <= 0:
                    return {"valid": False, "error": _ERROR_MUST_BE_POSITIVE.format(key=key)}
            except ValueError:
                return {"valid": False, "error": _ERROR_MUST_BE_NUMBER.format(key=key)}
        
        # All validations passed
        return {"valid": True, "error": None}
    
    # ═══════════════════════════════════════════════════════════
    # Session Update Helper - Week 6.2.10
    # ═══════════════════════════════════════════════════════════
    
    def _update_session_machine(self, key: str, value: Any) -> None:
        """
        Update machine config in session dict if available.
        
        Args:
            key: Machine config key
            value: New value
        """
        if self.zcli and hasattr(self.zcli, 'session'):
            self.zcli.session[SESSION_KEY_ZMACHINE][key] = value
    
    # ═══════════════════════════════════════════════════════════
    # Utility Methods
    # ═══════════════════════════════════════════════════════════
    
    def _handle_error(self, message: str, details: Optional[str] = None) -> None:
        """
        Handle error messages.
        
        Args:
            message: Error message
            details: Optional details
        """
        # Layer 0: Always use print (zDisplay not available yet)
        print(f"\n{Colors.ERROR}[ERROR] {message}{Colors.RESET}")
        if details:
            print(f"   {details}")
        print()
    
    def _handle_success(self, message: str, details: Optional[str] = None, file_path: Optional[str] = None) -> None:
        """
        Handle success messages.
        
        Args:
            message: Success message
            details: Optional change details
            file_path: Optional file path where changes were saved
        """
        # Layer 0: Always use print (zDisplay not available yet)
        print(f"\n{Colors.CONFIG}[OK] {message}{Colors.RESET}")
        if details:
            print(f"   {details}")
        if file_path:
            print(f"   {_SUCCESS_SAVED_TO.format(file_path=file_path)}")
        print()
