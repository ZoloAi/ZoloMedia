# zCLI/subsystems/zConfig/zConfig_modules/helpers/config_validator.py

"""
Configuration Validator - Fail Fast on Invalid Config
======================================================

Validates zSpark_obj configuration before initializing subsystems.
If anything is wrong, fails immediately with clear error messages.

Week 1.1 - Layer 0: Foundation
Week 6.2.9 - Moved to helpers/ (utility helper, not state module)
"""

from zOS import Path, Dict, List, Any

# Module Constants

# Logging and Messages
_LOG_PREFIX = "[CONFIG VALIDATION]"

# Valid Configuration Values
_VALID_MODES = ["Terminal", "zBifrost"]

# Configuration Keys
_KEY_ZSPACE = "zSpace"
_KEY_ZMODE = "zMode"
_KEY_WEBSOCKET = "websocket"
_KEY_HTTP_SERVER = "http_server"
_KEY_PLUGINS = "plugins"
_KEY_PORT = "port"
_KEY_HOST = "host"
_KEY_REQUIRE_AUTH = "require_auth"
_KEY_ALLOWED_ORIGINS = "allowed_origins"
_KEY_SERVE_PATH = "serve_path"
_KEY_ENABLED = "enabled"

# Port Validation
_PORT_MIN = 1
_PORT_MAX = 65535

# Error Message Templates
_ERROR_HEADER = "\n❌ Invalid zSpark configuration:\n\n"
_ERROR_FOOTER = "\n💡 Fix the above issues and try again.\n"
_ERROR_TYPE_MISMATCH = "{key}: Must be {expected_type}, got {actual_type}"
_ERROR_TYPE_MISMATCH_HINT = "{key}: Must be {expected_type}, got {actual_type} (hint: use {value} not '{value}')"
_ERROR_PATH_NOT_EXISTS = "{key}: Path '{path}' does not exist"
_ERROR_NOT_DIRECTORY = "{key}: '{path}' is not a directory"
_ERROR_INVALID_MODE = "zMode: Must be one of {valid_modes}, got '{mode}' (case-sensitive)"
_ERROR_PORT_RANGE = "{prefix}.port: Must be {min}-{max}, got {port}"
_ERROR_PORT_CONFLICT = "Port conflict: websocket and http_server both configured to use port {port}. They must use different ports."
_ERROR_LIST_ITEMS_TYPE = "{key}: All items must be {expected_type}"
_ERROR_INVALID_TYPE_OPTIONS = "{key}: Must be {option1} or {option2}, got {actual_type}"


class ConfigValidationError(Exception):
    """Raised when zSpark_obj configuration is invalid"""
    pass


class ConfigValidator:
    """
    Validates zSpark_obj configuration dictionary.
    
    Validates:
    - zSpace: Path exists and is directory
    - zMode: Must be "Terminal" or "zBifrost"
    - websocket: Port, host, require_auth types
    - http_server: Port, host, serve_path, enabled types
    - Port conflicts: websocket and http_server can't use same port
    
    Usage:
        validator = ConfigValidator(zspark_obj, logger)
        validator.validate()  # Raises ConfigValidationError if invalid
    """
    
    def __init__(self, zspark_obj: Dict[str, Any], logger=None):
        """
        Initialize validator.
        
        Args:
            zspark_obj: Configuration dictionary to validate
            logger: Optional logger instance (if None, validation happens before logger exists)
        """
        self.config = zspark_obj or {}
        self.logger = logger
        self.errors: List[str] = []
    
    def validate(self) -> None:
        """
        Run all validations.
        
        Raises:
            ConfigValidationError: If any validation fails
        """
        # Run all validation checks
        self._validate_workspace()
        self._validate_mode()
        self._validate_websocket()
        self._validate_http_server()
        self._validate_port_conflicts()
        self._validate_plugins()
        
        # If any errors, raise with all messages
        if self.errors:
            error_msg = _ERROR_HEADER
            for i, error in enumerate(self.errors, 1):
                error_msg += f"  {i}. {error}\n"
            error_msg += _ERROR_FOOTER
            raise ConfigValidationError(error_msg)
    
    def _validate_workspace(self) -> None:
        """Validate zSpace path"""
        workspace = self.config.get(_KEY_ZSPACE)
        
        # Optional, but if provided must be valid
        if workspace is None:
            return
        
        # Must be string
        if not isinstance(workspace, str):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=_KEY_ZSPACE,
                    expected_type="string",
                    actual_type=type(workspace).__name__
                )
            )
            return
        
        # Path must exist
        path = Path(workspace).expanduser()
        if not path.exists():
            self.errors.append(
                _ERROR_PATH_NOT_EXISTS.format(key=_KEY_ZSPACE, path=workspace)
            )
            return
        
        # Must be directory
        if not path.is_dir():
            self.errors.append(
                _ERROR_NOT_DIRECTORY.format(key=_KEY_ZSPACE, path=workspace)
            )
    
    def _validate_mode(self) -> None:
        """Validate zMode"""
        mode = self.config.get(_KEY_ZMODE)
        
        if mode is None:
            return  # Optional, defaults to "Terminal"
        
        # Must be string
        if not isinstance(mode, str):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=_KEY_ZMODE,
                    expected_type="string",
                    actual_type=type(mode).__name__
                )
            )
            return
        
        # Must be valid mode
        if mode not in _VALID_MODES:
            self.errors.append(
                _ERROR_INVALID_MODE.format(valid_modes=_VALID_MODES, mode=mode)
            )
    
    def _validate_websocket(self) -> None:
        """Validate websocket configuration"""
        ws_config = self.config.get(_KEY_WEBSOCKET)
        
        if ws_config is None:
            return  # Optional
        
        # Must be dict
        if not isinstance(ws_config, dict):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=_KEY_WEBSOCKET,
                    expected_type="dict",
                    actual_type=type(ws_config).__name__
                )
            )
            return
        
        # Validate port
        self._validate_port(ws_config, _KEY_WEBSOCKET)
        
        # Validate host
        host = ws_config.get(_KEY_HOST)
        if host is not None and not isinstance(host, str):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=f"{_KEY_WEBSOCKET}.{_KEY_HOST}",
                    expected_type="string",
                    actual_type=type(host).__name__
                )
            )
        
        # Validate require_auth
        auth = ws_config.get(_KEY_REQUIRE_AUTH)
        if auth is not None and not isinstance(auth, bool):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=f"{_KEY_WEBSOCKET}.{_KEY_REQUIRE_AUTH}",
                    expected_type="boolean",
                    actual_type=type(auth).__name__
                )
            )
        
        # Validate allowed_origins
        origins = ws_config.get(_KEY_ALLOWED_ORIGINS)
        if origins is not None:
            if not isinstance(origins, list):
                self.errors.append(
                    _ERROR_TYPE_MISMATCH.format(
                        key=f"{_KEY_WEBSOCKET}.{_KEY_ALLOWED_ORIGINS}",
                        expected_type="list",
                        actual_type=type(origins).__name__
                    )
                )
            elif not all(isinstance(o, str) for o in origins):
                self.errors.append(
                    _ERROR_LIST_ITEMS_TYPE.format(
                        key=f"{_KEY_WEBSOCKET}.{_KEY_ALLOWED_ORIGINS}",
                        expected_type="strings"
                    )
                )
    
    def _validate_http_server(self) -> None:
        """Validate zServer configuration (backward compatible with 'http_server' key)"""
        # Try new 'zServer' key first, fallback to deprecated 'http_server' key
        http_config = self.config.get("zServer") or self.config.get(_KEY_HTTP_SERVER)
        
        if http_config is None:
            return  # Optional
        
        # Must be dict
        if not isinstance(http_config, dict):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=_KEY_HTTP_SERVER,
                    expected_type="dict",
                    actual_type=type(http_config).__name__
                )
            )
            return
        
        # Validate port
        self._validate_port(http_config, _KEY_HTTP_SERVER)
        
        # Validate host
        host = http_config.get(_KEY_HOST)
        if host is not None and not isinstance(host, str):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=f"{_KEY_HTTP_SERVER}.{_KEY_HOST}",
                    expected_type="string",
                    actual_type=type(host).__name__
                )
            )
        
        # Validate serve_path
        serve_path = http_config.get(_KEY_SERVE_PATH)
        if serve_path is not None:
            if not isinstance(serve_path, str):
                self.errors.append(
                    _ERROR_TYPE_MISMATCH.format(
                        key=f"{_KEY_HTTP_SERVER}.{_KEY_SERVE_PATH}",
                        expected_type="string",
                        actual_type=type(serve_path).__name__
                    )
                )
            else:
                path = Path(serve_path).expanduser()
                if not path.exists():
                    self.errors.append(
                        _ERROR_PATH_NOT_EXISTS.format(
                            key=f"{_KEY_HTTP_SERVER}.{_KEY_SERVE_PATH}",
                            path=serve_path
                        )
                    )
        
        # Validate enabled
        enabled = http_config.get(_KEY_ENABLED)
        if enabled is not None and not isinstance(enabled, bool):
            self.errors.append(
                _ERROR_TYPE_MISMATCH.format(
                    key=f"{_KEY_HTTP_SERVER}.{_KEY_ENABLED}",
                    expected_type="boolean",
                    actual_type=type(enabled).__name__
                )
            )
    
    def _validate_port(self, config: Dict[str, Any], prefix: str) -> None:
        """
        Validate port number in a config dict.
        
        Args:
            config: Dict containing 'port' key
            prefix: Config section name (e.g., "websocket", "http_server")
        """
        port = config.get(_KEY_PORT)
        
        if port is None:
            return  # Optional, has defaults
        
        # Must be integer
        if not isinstance(port, int):
            self.errors.append(
                _ERROR_TYPE_MISMATCH_HINT.format(
                    key=f"{prefix}.{_KEY_PORT}",
                    expected_type="integer",
                    actual_type=type(port).__name__,
                    value=port
                )
            )
            return
        
        # Must be in valid range
        if not (_PORT_MIN <= port <= _PORT_MAX):
            self.errors.append(
                _ERROR_PORT_RANGE.format(
                    prefix=prefix,
                    min=_PORT_MIN,
                    max=_PORT_MAX,
                    port=port
                )
            )
    
    def _validate_port_conflicts(self) -> None:
        """Ensure websocket and http_server don't use same port"""
        ws_config = self.config.get(_KEY_WEBSOCKET, {})
        http_config = self.config.get(_KEY_HTTP_SERVER, {})
        
        # Skip if either is not a dict (already reported error)
        if not isinstance(ws_config, dict) or not isinstance(http_config, dict):
            return
        
        ws_port = ws_config.get(_KEY_PORT)
        http_port = http_config.get(_KEY_PORT)
        
        # Skip if either is None or invalid type (already reported error)
        if ws_port is None or http_port is None:
            return
        if not isinstance(ws_port, int) or not isinstance(http_port, int):
            return
        
        # Check for conflict
        if ws_port == http_port:
            self.errors.append(
                _ERROR_PORT_CONFLICT.format(port=ws_port)
            )
    
    def _validate_plugins(self) -> None:
        """Validate plugins configuration"""
        plugins = self.config.get(_KEY_PLUGINS)
        
        if plugins is None:
            return  # Optional
        
        # Can be string or list
        if isinstance(plugins, str):
            return  # Single plugin path is OK
        
        if isinstance(plugins, list):
            # All items must be strings
            if not all(isinstance(p, str) for p in plugins):
                self.errors.append(
                    _ERROR_LIST_ITEMS_TYPE.format(
                        key=_KEY_PLUGINS,
                        expected_type="strings (file paths or module names)"
                    )
                )
        else:
            self.errors.append(
                _ERROR_INVALID_TYPE_OPTIONS.format(
                    key=_KEY_PLUGINS,
                    option1="string",
                    option2="list",
                    actual_type=type(plugins).__name__
                )
            )
