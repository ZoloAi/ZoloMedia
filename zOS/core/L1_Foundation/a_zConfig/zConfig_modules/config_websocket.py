# zCLI/subsystems/zConfig/zConfig_modules/config_websocket.py
"""WebSocket configuration management as part of zConfig."""

from zOS import Colors, os, Any, Dict, List, Optional
from zOS.utils import print_ready_message, validate_zcli_instance

# Module Constants

# Logging
_LOG_PREFIX = "[WebSocketConfig]"
_SUBSYSTEM_NAME = "WebSocketConfig"
_READY_MESSAGE = "zSocket Ready"

# Config Section
_CONFIG_SECTION_KEY = "websocket"

# Environment Variables
_ENV_VAR_HOST = "WEBSOCKET_HOST"
_ENV_VAR_PORT = "WEBSOCKET_PORT"
_ENV_VAR_REQUIRE_AUTH = "WEBSOCKET_REQUIRE_AUTH"
_ENV_VAR_ALLOWED_ORIGINS = "WEBSOCKET_ALLOWED_ORIGINS"
_ENV_VAR_TOKEN = "WEBSOCKET_TOKEN"
_ENV_VAR_SSL_ENABLED = "WEBSOCKET_SSL_ENABLED"
_ENV_VAR_SSL_CERT = "WEBSOCKET_SSL_CERT"
_ENV_VAR_SSL_KEY = "WEBSOCKET_SSL_KEY"

# Config Keys
_KEY_HOST = "host"
_KEY_PORT = "port"
_KEY_REQUIRE_AUTH = "require_auth"
_KEY_ALLOWED_ORIGINS = "allowed_origins"
_KEY_TOKEN = "token"
_KEY_MAX_CONNECTIONS = "max_connections"
_KEY_PING_INTERVAL = "ping_interval"
_KEY_PING_TIMEOUT = "ping_timeout"
_KEY_SSL_ENABLED = "ssl_enabled"
_KEY_SSL_CERT = "ssl_cert"
_KEY_SSL_KEY = "ssl_key"

# Default Values
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765  # Standard WebSocket development port (matches zComm primitives)
_DEFAULT_REQUIRE_AUTH = False  # Security is opt-in, not opt-out (better UX for beginners)
_DEFAULT_ALLOWED_ORIGINS: List[str] = []
_DEFAULT_TOKEN = ""  # Empty by default - configure via .zEnv or env vars
_DEFAULT_MAX_CONNECTIONS = 100
_DEFAULT_PING_INTERVAL = 20
_DEFAULT_PING_TIMEOUT = 10
_DEFAULT_SSL_ENABLED = False  # SSL disabled by default for easier local development
_DEFAULT_SSL_CERT = None
_DEFAULT_SSL_KEY = None

# String Parsing
_TRUTHY_VALUES = ("true", "1", "yes")
_ORIGINS_DELIMITER = ","

class WebSocketConfig:
    """Manages WebSocket configuration with hierarchical loading."""

    # Type hints for instance attributes
    environment: Any  # EnvironmentConfig
    zcli: Any  # zCLI instance
    logger: Any  # Logger instance
    config: Dict[str, Any]

    def __init__(self, environment_config: Any, zcli: Any, logger: Any) -> None:
        """
        Initialize WebSocket config with environment config and zcli instance.
        
        Args:
            environment_config: EnvironmentConfig instance with environment settings
            zcli: Main zCLI instance for accessing zSpark and other subsystems
            logger: Logger instance for configuration logging
        """
        # Validate required parameters
        validate_zcli_instance(zcli, _SUBSYSTEM_NAME, require_session=False)

        self.environment = environment_config
        self.zcli = zcli
        self.logger = logger

        # Get WebSocket configuration from environment (which uses hierarchy)
        self._load_websocket_config()

        # Print ready message (deployment-aware)
        # Use environment.is_production() directly since we have the environment object
        print_ready_message(_READY_MESSAGE, color="CONFIG", is_production=self.environment.is_production(), is_testing=self.environment.is_testing())

    def _load_websocket_config(self) -> None:
        """Load WebSocket configuration following hierarchy: zSpark > env > config file > defaults."""

        # Get base config from environment
        websocket_config: Dict[str, Any] = self.environment.get(_CONFIG_SECTION_KEY, {})

        # 1. Check environment variables (Layer 3/4 - .zEnv or system env)
        env_host = os.getenv(_ENV_VAR_HOST)
        env_port = os.getenv(_ENV_VAR_PORT)
        env_auth = os.getenv(_ENV_VAR_REQUIRE_AUTH)
        env_origins = os.getenv(_ENV_VAR_ALLOWED_ORIGINS)
        env_token = os.getenv(_ENV_VAR_TOKEN)
        env_ssl_enabled = os.getenv(_ENV_VAR_SSL_ENABLED)
        env_ssl_cert = os.getenv(_ENV_VAR_SSL_CERT)
        env_ssl_key = os.getenv(_ENV_VAR_SSL_KEY)

        if env_host:
            websocket_config[_KEY_HOST] = env_host
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket host from env: {env_host}")

        if env_port:
            try:
                websocket_config[_KEY_PORT] = int(env_port)
                self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket port from env: {env_port}")
            except ValueError:
                self.logger.framework.warning(f"{_LOG_PREFIX} Invalid {_ENV_VAR_PORT}: {env_port}")

        if env_auth:
            websocket_config[_KEY_REQUIRE_AUTH] = env_auth.lower() in _TRUTHY_VALUES
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket auth from env: {websocket_config[_KEY_REQUIRE_AUTH]}")

        if env_origins:
            origins_list = [origin.strip() for origin in env_origins.split(_ORIGINS_DELIMITER) if origin.strip()]
            websocket_config[_KEY_ALLOWED_ORIGINS] = origins_list
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket origins from env: {origins_list}")

        if env_token:
            websocket_config[_KEY_TOKEN] = env_token
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket token from env: {'*' * len(env_token)}")

        # SSL Configuration with deployment-aware defaults (v1.5.10)
        # Check deployment mode for auto-SSL behavior
        deployment = None
        if self.zcli.zspark_obj:
            for key in ["deployment", "Deployment", "DEPLOYMENT"]:
                if key in self.zcli.zspark_obj:
                    deployment = str(self.zcli.zspark_obj[key])
                    break
        
        # If not in zSpark, check env (from .zEnv)
        if not deployment:
            deployment = os.getenv('DEPLOYMENT', 'Development')
        
        is_production = deployment.lower() == 'production'
        
        # Deployment-aware SSL defaults:
        # - Explicit env var (WEBSOCKET_SSL_ENABLED) → highest priority
        # - Production + certs present → auto-enable WSS
        # - Development or no certs → disable WSS
        if env_ssl_enabled is not None:
            # Explicit env var takes precedence
            websocket_config[_KEY_SSL_ENABLED] = env_ssl_enabled.lower() in _TRUTHY_VALUES
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket SSL from env: {websocket_config[_KEY_SSL_ENABLED]}")
        elif is_production and env_ssl_cert and env_ssl_key:
            # Production + certs present = auto-enable SSL
            websocket_config[_KEY_SSL_ENABLED] = True
            self.logger.framework.debug(f"{_LOG_PREFIX} Production mode: WSS auto-enabled (certs detected)")
        
        if env_ssl_cert:
            websocket_config[_KEY_SSL_CERT] = env_ssl_cert
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket SSL cert from env: {env_ssl_cert}")

        if env_ssl_key:
            websocket_config[_KEY_SSL_KEY] = env_ssl_key
            self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket SSL key from env: {env_ssl_key}")

        # 2. Check zSpark_obj for WebSocket settings (Layer 5 - highest priority, overrides env)
        if self.zcli.zspark_obj:
            zspark_ws = self.zcli.zspark_obj.get(_CONFIG_SECTION_KEY, {})
            if zspark_ws:
                self.logger.framework.debug(f"{_LOG_PREFIX} WebSocket settings from zSpark: {list(zspark_ws.keys())}")
                websocket_config.update(zspark_ws)  # zSpark overrides everything else

        # 3. Apply defaults for any missing values
        self.config = {
            _KEY_HOST: websocket_config.get(_KEY_HOST, _DEFAULT_HOST),
            _KEY_PORT: websocket_config.get(_KEY_PORT, _DEFAULT_PORT),
            _KEY_REQUIRE_AUTH: websocket_config.get(_KEY_REQUIRE_AUTH, _DEFAULT_REQUIRE_AUTH),
            _KEY_ALLOWED_ORIGINS: websocket_config.get(_KEY_ALLOWED_ORIGINS, _DEFAULT_ALLOWED_ORIGINS),
            _KEY_TOKEN: websocket_config.get(_KEY_TOKEN, _DEFAULT_TOKEN),
            _KEY_MAX_CONNECTIONS: websocket_config.get(_KEY_MAX_CONNECTIONS, _DEFAULT_MAX_CONNECTIONS),
            _KEY_PING_INTERVAL: websocket_config.get(_KEY_PING_INTERVAL, _DEFAULT_PING_INTERVAL),
            _KEY_PING_TIMEOUT: websocket_config.get(_KEY_PING_TIMEOUT, _DEFAULT_PING_TIMEOUT),
            _KEY_SSL_ENABLED: websocket_config.get(_KEY_SSL_ENABLED, _DEFAULT_SSL_ENABLED),
            _KEY_SSL_CERT: websocket_config.get(_KEY_SSL_CERT, _DEFAULT_SSL_CERT),
            _KEY_SSL_KEY: websocket_config.get(_KEY_SSL_KEY, _DEFAULT_SSL_KEY),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get WebSocket config value by key."""
        return self.config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get complete WebSocket configuration."""
        return self.config.copy()

    def update(self, key: str, value: Any) -> None:
        """Update WebSocket config value (runtime only)."""
        self.config[key] = value

    # ═══════════════════════════════════════════════════════════
    # Convenience Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def host(self) -> str:
        """WebSocket bind address."""
        return self.config[_KEY_HOST]

    @property
    def port(self) -> int:
        """WebSocket port."""
        return self.config[_KEY_PORT]

    @property
    def require_auth(self) -> bool:
        """Whether authentication is required."""
        return self.config[_KEY_REQUIRE_AUTH]

    @property
    def allowed_origins(self) -> List[str]:
        """List of allowed origins."""
        return self.config[_KEY_ALLOWED_ORIGINS]

    @property
    def token(self) -> str:
        """Authentication token (from .zEnv or env vars)."""
        return self.config[_KEY_TOKEN]

    @property
    def ssl_enabled(self) -> bool:
        """Whether SSL/TLS is enabled for WSS connections."""
        return self.config[_KEY_SSL_ENABLED]

    @property
    def ssl_cert(self) -> Optional[str]:
        """Path to SSL certificate file."""
        return self.config[_KEY_SSL_CERT]

    @property
    def ssl_key(self) -> Optional[str]:
        """Path to SSL private key file."""
        return self.config[_KEY_SSL_KEY]

    @property
    def max_connections(self) -> int:
        """Maximum concurrent connections."""
        return self.config[_KEY_MAX_CONNECTIONS]

    @property
    def ping_interval(self) -> int:
        """Ping interval in seconds."""
        return self.config[_KEY_PING_INTERVAL]

    @property
    def ping_timeout(self) -> int:
        """Ping timeout in seconds."""
        return self.config[_KEY_PING_TIMEOUT]
