# zCLI/subsystems/zConfig/zConfig_modules/config_http_server.py
"""HTTP Server Configuration Module"""

from zOS import Any, Dict, Optional, os
from zOS.utils import print_ready_message

# Module Constants

# Logging
_LOG_PREFIX = "[HttpServerConfig]"
_SUBSYSTEM_NAME = "HttpServerConfig"
_READY_MESSAGE = "zServer Ready"

# Config Section (v1.5.7: Renamed from 'http_server' to match subsystem name)
_CONFIG_SECTION_KEY = "zServer"  # Supports both http.server (Dev) and WSGI/Gunicorn (Prod)

# Config Keys
_KEY_HOST = "host"
_KEY_PORT = "port"
_KEY_SERVE_PATH = "serve_path"
_KEY_ROUTES_FILE = "routes_file"
_KEY_ENABLED = "enabled"
KEY_ZSHELL = "zShell"  # v1.5.8: Drop into zShell REPL (default: False = silent blocking)

# Default Values
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_SERVE_PATH = "."
DEFAULT_ROUTES_FILE = None
DEFAULT_ENABLED = False
DEFAULT_ZSHELL = False  # v1.5.8: Default to silent blocking (standard server behavior)
DEFAULT_SSL_ENABLED = False  # v1.5.10: SSL disabled by default for local development
DEFAULT_SSL_CERT = None
DEFAULT_SSL_KEY = None

# Environment Variables
ENV_VAR_HTTP_SSL_ENABLED = "HTTP_SSL_ENABLED"
ENV_VAR_HTTP_SSL_CERT = "HTTP_SSL_CERT"
ENV_VAR_HTTP_SSL_KEY = "HTTP_SSL_KEY"
ENV_VAR_ZSERVER_MOUNTS = "ZSERVER_MOUNTS"  # v1.5.11: Static mount points

# Truthy values for boolean environment variables
TRUTHY_VALUES = {'true', '1', 'yes', 'on'}


class HttpServerConfig:
    """
    Configuration for zServer (HTTP + WSGI/Gunicorn deployment).
    
    Manages zServer settings from zSpark configuration with sensible defaults.
    Supports both Development (http.server) and Production (Gunicorn/WSGI) modes.
    
    Configuration Key: 'zServer' (backward compatible with 'http_server')
    
    Attributes:
        host: Server host address
        port: Server port
        serve_path: Directory to serve files from
        routes_file: Optional routes configuration file (auto-detected if not specified)
        enabled: Whether zServer is enabled (if True, server ALWAYS waits)
        zShell: Whether to drop into zShell REPL (False = silent blocking)
    """
    
    # Type hints for instance attributes
    logger: Any
    host: str
    port: int
    serve_path: str
    routes_file: Optional[str]
    enabled: bool
    zShell: bool  # v1.5.8: Drop into zShell REPL (default: False)
    ssl_enabled: bool  # v1.5.10: HTTPS support
    ssl_cert: Optional[str]  # v1.5.10: SSL certificate path
    ssl_key: Optional[str]  # v1.5.10: SSL key path
    static_mounts: Dict[str, str]  # v1.5.11: Multi-mount support {url_prefix: fs_path}
    
    def __init__(self, zspark_obj: Dict[str, Any], logger: Any) -> None:
        """
        Initialize zServer configuration.
        
        Args:
            zspark_obj: zSpark configuration dictionary (looks for 'zServer' key)
            logger: Logger instance for configuration logging
        """
        self.logger = logger
        
        # Get zServer config from zSpark (v1.5.7: Supports 'zServer' key, backward compatible with 'http_server')
        http_config = zspark_obj.get(_CONFIG_SECTION_KEY, {})
        
        # Backward compatibility: Check for old 'http_server' key if 'zServer' not found
        if not http_config and "http_server" in zspark_obj:
            http_config = zspark_obj.get("http_server", {})
            self.logger.framework.debug("[HttpServerConfig] Using deprecated 'http_server' key (use 'zServer' instead)")
        
        # Set configuration with defaults
        self.host = http_config.get(_KEY_HOST, DEFAULT_HOST)
        self.port = http_config.get(_KEY_PORT, DEFAULT_PORT)
        self.serve_path = http_config.get(_KEY_SERVE_PATH, DEFAULT_SERVE_PATH)
        self.routes_file = http_config.get(_KEY_ROUTES_FILE, DEFAULT_ROUTES_FILE)
        self.enabled = http_config.get(_KEY_ENABLED, DEFAULT_ENABLED)
        self.zShell = http_config.get(KEY_ZSHELL, DEFAULT_ZSHELL)  # v1.5.8: Interactive mode
        
        # SSL Configuration (v1.5.10: HTTPS support with deployment-aware defaults)
        # Environment variables from .zEnv (base or deployment-specific)
        env_ssl_enabled = os.getenv(ENV_VAR_HTTP_SSL_ENABLED)
        env_ssl_cert = os.getenv(ENV_VAR_HTTP_SSL_CERT)
        env_ssl_key = os.getenv(ENV_VAR_HTTP_SSL_KEY)
        
        # Check deployment mode from zSpark (determines auto-SSL behavior)
        deployment = None
        for key in ["deployment", "Deployment", "DEPLOYMENT"]:
            if key in zspark_obj:
                deployment = str(zspark_obj[key])
                break
        
        # If not in zSpark, check env (from .zEnv)
        if not deployment:
            deployment = os.getenv('DEPLOYMENT', 'Development')
        
        is_production = deployment.lower() == 'production'
        
        # Deployment-aware SSL defaults (v1.5.10):
        # - Explicit env var (HTTP_SSL_ENABLED) → highest priority
        # - Production + certs present → auto-enable HTTPS
        # - Development or no certs → disable HTTPS
        if env_ssl_enabled is not None:
            # Explicit env var takes precedence
            self.ssl_enabled = env_ssl_enabled.lower() in TRUTHY_VALUES
        elif is_production and env_ssl_cert and env_ssl_key:
            # Production + certs present = auto-enable SSL
            self.ssl_enabled = True
            self.logger.framework.debug(
                f"{_LOG_PREFIX} Production mode: SSL auto-enabled (certs detected)"
            )
        else:
            # Development or no certs = disable SSL
            self.ssl_enabled = DEFAULT_SSL_ENABLED
        
        self.ssl_cert = env_ssl_cert if env_ssl_cert else DEFAULT_SSL_CERT
        self.ssl_key = env_ssl_key if env_ssl_key else DEFAULT_SSL_KEY
        
        if self.ssl_enabled:
            self.logger.framework.debug(f"{_LOG_PREFIX} SSL enabled: {self.ssl_enabled}")
            if self.ssl_cert:
                self.logger.framework.debug(f"{_LOG_PREFIX} SSL cert: {self.ssl_cert}")
            if self.ssl_key:
                self.logger.framework.debug(f"{_LOG_PREFIX} SSL key: {self.ssl_key}")
        
        # Static Mounts Configuration (v1.5.11: Multi-mount support)
        # Allows serving files from multiple directories at custom URL prefixes
        # Format: {"/url_prefix/": "/absolute/filesystem/path/"}
        # Priority: Environment variable (from .zEnv) → zSpark config
        mounts_config = os.getenv(ENV_VAR_ZSERVER_MOUNTS) or zspark_obj.get('ZSERVER_MOUNTS', {})
        self.static_mounts = self._parse_static_mounts(mounts_config)
        
        # Log configuration
        if self.enabled:
            self.logger.info(f"{_LOG_PREFIX} Enabled - {self.host}:{self.port}")
            self.logger.info(f"{_LOG_PREFIX} Serve path: {self.serve_path}")
            if self.routes_file:
                self.logger.info(f"{_LOG_PREFIX} Routes file: {self.routes_file}")
        else:
            self.logger.framework.debug(f"{_LOG_PREFIX} HTTP server disabled")
        
        # Check production mode for banner suppression (zSpark Layer 5)
        is_production = False
        if zspark_obj and isinstance(zspark_obj, dict):
            for key in ["deployment", "Deployment", "DEPLOYMENT"]:
                if key in zspark_obj:
                    is_production = str(zspark_obj[key]).lower() == "production"
                    break
        
        # Print ready message (deployment-aware)
        # Also check for Testing mode (use zspark_obj to check early, before full init)
        is_testing = False
        if zspark_obj and isinstance(zspark_obj, dict):
            deployment = str(zspark_obj.get('deployment', '')).lower()
            is_testing = deployment in ['testing', 'info']
        print_ready_message(_READY_MESSAGE, color="CONFIG", is_production=is_production, is_testing=is_testing)
    
    def _parse_static_mounts(self, mounts_config: Any) -> Dict[str, str]:
        """
        Parse and validate static mount configuration (v1.5.11).
        
        Allows users to mount any filesystem directory to a custom URL prefix.
        Example: {"/bifrost/": "/Users/gal/bifrost/"} → http://host/bifrost/file.js
        
        Args:
            mounts_config: Dict or JSON string of {url_prefix: filesystem_path}
        
        Returns:
            Dict of validated mounts {url_prefix: absolute_path}
        
        Security:
            - Each mount has its own directory traversal protection
            - URL prefixes must start and end with /
            - Filesystem paths are resolved to absolute paths
        """
        import json
        from pathlib import Path
        
        # Handle JSON string format (from .zEnv)
        if isinstance(mounts_config, str):
            try:
                mounts_config = json.loads(mounts_config)
            except json.JSONDecodeError:
                self.logger.warning(f"{_LOG_PREFIX} Invalid ZSERVER_MOUNTS format (not valid JSON), ignoring")
                return {}
        
        if not isinstance(mounts_config, dict):
            if mounts_config:  # Only warn if non-empty
                self.logger.warning(f"{_LOG_PREFIX} ZSERVER_MOUNTS must be a dict, got {type(mounts_config)}")
            return {}
        
        validated = {}
        for url_prefix, fs_path in mounts_config.items():
            # Validate URL prefix format
            if not url_prefix.startswith('/') or not url_prefix.endswith('/'):
                self.logger.warning(
                    f"{_LOG_PREFIX} Invalid mount prefix '{url_prefix}' "
                    "(must start and end with /), skipping"
                )
                continue
            
            # Resolve filesystem path to absolute
            try:
                resolved_path = str(Path(fs_path).resolve())
                
                # Check if path exists (warn but allow - might be created later)
                if not Path(resolved_path).exists():
                    self.logger.warning(
                        f"{_LOG_PREFIX} Mount path does not exist: {fs_path} "
                        "(will serve 404 until created)"
                    )
                
                validated[url_prefix] = resolved_path
                self.logger.info(f"{_LOG_PREFIX} Registered mount: {url_prefix} → {resolved_path}")
            
            except Exception as e:
                self.logger.error(
                    f"{_LOG_PREFIX} Error resolving mount path '{fs_path}': {e}, skipping"
                )
                continue
        
        return validated
    
    def __repr__(self) -> str:
        """Return string representation of HttpServerConfig instance."""
        return f"HttpServerConfig(host={self.host}, port={self.port}, enabled={self.enabled})"

