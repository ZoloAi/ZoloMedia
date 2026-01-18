# zCLI/subsystems/zComm/zComm_modules/comm_ssl.py
"""
SSL/TLS Primitives for zComm (Layer 0).

Provides low-level SSL context creation for secure server infrastructure.
Used by both HTTP server and WebSocket server for consistent SSL handling.

Architecture:
    Layer 0 (zComm): SSL/TLS infrastructure primitives
    Consumers: WebSocketServer, zServer (via zComm)
"""

from zOS import ssl, Path, Optional, Any

# Module Constants

_LOG_PREFIX = "[SSL]"
_LOG_ENABLED = f"{_LOG_PREFIX} SSL enabled with cert: {{cert_path}}"
_LOG_CERT_NOT_PROVIDED = f"{_LOG_PREFIX} SSL enabled but cert/key not provided"
_LOG_CERT_NOT_FOUND = f"{_LOG_PREFIX} SSL cert not found: {{cert_path}}"
_LOG_KEY_NOT_FOUND = f"{_LOG_PREFIX} SSL key not found: {{key_path}}"
_LOG_CONTEXT_FAILED = f"{_LOG_PREFIX} Failed to create SSL context: {{error}}"


def create_ssl_context(
    ssl_enabled: bool,
    ssl_cert: Optional[str],
    ssl_key: Optional[str],
    logger: Any,
    log_prefix: str = _LOG_PREFIX
) -> Optional[ssl.SSLContext]:
    """
    Create SSL context for server-side TLS encryption (Layer 0 primitive).
    
    This is the canonical SSL context creation function for all zCLI servers
    (HTTP, WebSocket, etc.). Provides consistent SSL handling across the framework.
    
    Args:
        ssl_enabled: Whether SSL is enabled
        ssl_cert: Path to SSL certificate file (relative or absolute, supports ~)
        ssl_key: Path to SSL private key file (relative or absolute, supports ~)
        logger: Logger instance for diagnostics
        log_prefix: Optional custom log prefix (default: "[SSL]")
    
    Returns:
        ssl.SSLContext if SSL enabled and configured correctly, None otherwise
    
    Security:
        - Uses PROTOCOL_TLS_SERVER (TLS 1.2+ only, secure defaults)
        - Validates certificate/key files exist before loading
        - Resolves paths with ~ expansion and relative path handling
        - Comprehensive error logging for debugging
    
    Example:
        ```python
        from zOS.L1_Foundation.b_zComm.zComm_modules.comm_ssl import create_ssl_context
        
        ssl_context = create_ssl_context(
            ssl_enabled=True,
            ssl_cert="certs/server.cert",
            ssl_key="certs/server.key",
            logger=logger
        )
        
        if ssl_context:
            server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
        ```
    
    Note:
        This is a Layer 0 primitive. For higher-level orchestration,
        see zBifrost (Layer 2) or zServer (HTTP server).
    """
    # Check if SSL is enabled
    if not ssl_enabled:
        return None
    
    # Validate cert/key provided
    if not ssl_cert or not ssl_key:
        logger.warning(f"{log_prefix} SSL enabled but cert/key not provided")
        return None
    
    try:
        # Resolve paths (handle ~, relative paths)
        cert_path = Path(ssl_cert).expanduser().resolve()
        key_path = Path(ssl_key).expanduser().resolve()
        
        # Verify files exist
        if not cert_path.exists():
            logger.error(f"{log_prefix} SSL cert not found: {cert_path}")
            return None
        
        if not key_path.exists():
            logger.error(f"{log_prefix} SSL key not found: {key_path}")
            return None
        
        # Create SSL context for server (TLS 1.2+)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(str(cert_path), str(key_path))
        
        logger.info(f"{log_prefix} SSL enabled with cert: {cert_path}")
        return ssl_context
        
    except Exception as e:
        logger.error(f"{log_prefix} Failed to create SSL context: {e}")
        return None

