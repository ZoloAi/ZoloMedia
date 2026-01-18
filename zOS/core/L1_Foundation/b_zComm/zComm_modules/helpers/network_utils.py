# zCLI/subsystems/zComm/zComm_modules/network_utils.py
"""
Network utility functions for zComm subsystem.

Provides network-level utilities for port checking, availability testing,
and other low-level network operations needed by zComm services.
"""

from zOS import Any, socket
from ..comm_constants import PORT_MIN, PORT_MAX, DEFAULT_HOST, DEFAULT_TIMEOUT_SECONDS

# Module Constants

# Logging
_LOG_PREFIX = "[NetworkUtils]"

# Error Messages
_ERROR_INVALID_PORT = "Port must be between {min} and {max}, got: {port}"
_ERROR_PORT_CHECK_FAILED = "Failed to check port {port}"


class NetworkUtils:
    """
    Network utility functions for zComm subsystem.
    
    Provides low-level network operations including port availability
    checking, which is essential for service management and server initialization.
    """

    def __init__(self, logger: Any) -> None:
        """
        Initialize network utilities.
        
        Args:
            logger: Logger instance for debug/error output
        """
        self.logger = logger

    def check_port(self, port: int, host: str = DEFAULT_HOST) -> bool:
        """
        Check if a port is available for binding.
        
        Attempts to connect to the specified port. If connection fails,
        the port is considered available (nothing is listening on it).
        
        Args:
            port: Port number to check (1-65535)
            host: Host address to check (default: localhost)
            
        Returns:
            bool: True if port is available, False if in use
            
        Raises:
            ValueError: If port is outside valid range (1-65535)
            
        Example:
            >>> network_utils = NetworkUtils(logger)
            >>> if network_utils.check_port(8080):
            ...     print("Port 8080 is available")
        """
        # Validate port range
        if not isinstance(port, int) or port < PORT_MIN or port > PORT_MAX:
            error_msg = _ERROR_INVALID_PORT.format(
                min=PORT_MIN,
                max=PORT_MAX,
                port=port
            )
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        self.logger.debug(f"{_LOG_PREFIX} Checking port availability: {port} on {host}")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(DEFAULT_TIMEOUT_SECONDS)
            result = sock.connect_ex((host, port))
            sock.close()

            is_available = result != 0  # True if available, False if in use

            if is_available:
                self.logger.debug(f"{_LOG_PREFIX} Port {port} is available")
            else:
                self.logger.debug(f"{_LOG_PREFIX} Port {port} is in use")

            return is_available

        except (socket.error, OSError) as e:
            # Specific socket/OS errors
            error_msg = _ERROR_PORT_CHECK_FAILED.format(port=port)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}: {e}")
            return False
