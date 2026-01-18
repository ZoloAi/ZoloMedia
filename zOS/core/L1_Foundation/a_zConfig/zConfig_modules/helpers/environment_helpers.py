# zCLI/subsystems/zConfig/zConfig_modules/helpers/environment_helpers.py
"""Helper functions for environment configuration."""

from zOS import Path, Colors, Dict, Any

def create_default_env_config(path: Path, _env_data: Dict[str, Any]) -> None:
    """Create default environment config YAML file from template."""
    # Lazy import to avoid circular dependency (config_environment imports from helpers)
    from ..config_environment import LOG_PREFIX, YAML_KEY, KEY_DEPLOYMENT, DEFAULT_DEPLOYMENT
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        content = f"""
# zolo-zcli Environment Configuration
# This file was auto-generated on first run.
# You can edit this file to customize your environment-specific settings.

{YAML_KEY}:
  # Environment Settings (customize these to your environment!)
  {KEY_DEPLOYMENT}: "{DEFAULT_DEPLOYMENT}"  # Development, Testing, Production
  datacenter: "local"  # local, us-west-2, eu-central-1, etc.
  cluster: "single-node"  # single-node, multi-node, k8s-cluster
  node_id: "node-001"  # unique identifier for this node
  
  # Network Configuration
  network:
    host: "127.0.0.1"  # bind address
    port: 56891  # service port
    external_host: "localhost"  # external access hostname
    external_port: 56891  # external access port
  
  # WebSocket Configuration
  # WebSocket settings hierarchy: zSpark > system env (WEBSOCKET_*) > this file
  websocket:
    host: "127.0.0.1"  # WebSocket bind address (default: localhost for security)
    port: 8765  # WebSocket port (standard development port)
    require_auth: false  # authentication is opt-in (set to true for production)
    allowed_origins: []  # list of allowed origins (empty = localhost only)
    token: ""  # WebSocket authentication token (override via .zEnv or env vars)
    max_connections: 100  # maximum concurrent WebSocket connections
    ping_interval: 20  # ping interval in seconds
    ping_timeout: 10  # ping timeout in seconds
    ssl_enabled: false  # enable SSL/TLS for WSS (WebSocket Secure)
    ssl_cert: null  # path to SSL certificate file
    ssl_key: null  # path to SSL private key file
  
  # Security Settings
  security:
    require_auth: true  # require authentication
    allow_anonymous: false  # allow anonymous access
    ssl_enabled: false  # enable SSL/TLS
    ssl_cert_path: ""  # path to SSL certificate
    ssl_key_path: ""  # path to SSL private key
  
  # Logging Configuration (Dual Logger System)
  # Hierarchy: zSpark > virtual env (ZOLO_LOGGER) > system env (ZOLO_LOGGER) > this file
  logging:
    # Application Logs (your code) - customizable
    app:
    level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: "detailed"  # simple, detailed, json
    file_enabled: true  # enable file logging
      file_path: ""  # empty = use zCLI support folder (zcli-app.log)
    
    # Framework Logs (internal zCLI) - fixed path
    framework:
      level: "DEBUG"  # always DEBUG to capture all internal operations
      format: "detailed"  # simple, detailed, json
      # Note: framework logs always go to zcli-framework.log (non-configurable path)
  
  # Performance Settings
  performance:
    max_workers: 4  # max concurrent workers
    cache_size: 1000  # cache size limit
    cache_ttl: 3600  # cache time-to-live (seconds)
    timeout: 30  # default timeout (seconds)
  
  # Custom Fields (add your own as needed)
  custom_field_1: "value"
  custom_field_2: 42
  custom_field_3: ["item1", "item2"]
"""

        Path(path).write_text(content, encoding="utf-8")
        print(f"{Colors.CONFIG}{LOG_PREFIX} Created environment config: {path}{Colors.RESET}")
        print(f"{Colors.CONFIG}{LOG_PREFIX} You can edit this file to customize environment settings{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.ERROR}{LOG_PREFIX} Failed to create environment config: {e}{Colors.RESET}")

