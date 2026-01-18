# zCLI/subsystems/zComm/zComm_modules/comm_http.py
"""
HTTP client for zComm subsystem.

Provides a complete HTTP client for making web requests (GET, POST, PUT, PATCH, DELETE).
This is a pure communication layer with no authentication logic - auth should be handled
by the caller (e.g., zAuth subsystem).
"""

from zOS import Any, Dict, Optional, requests
from .comm_constants import HTTP_DEFAULT_TIMEOUT

# Module Constants

# Logging
_LOG_PREFIX = "[HTTPClient]"

# Log Messages
_LOG_REQUEST = "Making HTTP {method} request to {url}"
_LOG_REQUEST_PAYLOAD = "Request payload: {data}"
_LOG_REQUEST_PARAMS = "Query parameters: {params}"
_LOG_RESPONSE_RECEIVED = "Response received [status={status}]"

# Error Messages
_ERROR_REQUEST_FAILED = "HTTP {method} request failed to {url}: {error}"
_ERROR_INVALID_URL = "Invalid URL provided: {url}"
_ERROR_INVALID_TIMEOUT = "Timeout must be positive, got: {timeout}"


class HTTPClient:
    """
    HTTP client for making web requests (GET, POST, PUT, PATCH, DELETE).
    
    This is a pure communication layer with no authentication logic.
    Authentication should be handled by the caller (e.g., zAuth subsystem).
    
    Example:
        >>> client = HTTPClient(logger)
        >>> response = client.get("https://api.example.com/users")
        >>> response = client.post("https://api.example.com/users", 
        ...                        data={"name": "Alice"}, 
        ...                        timeout=5)
        >>> if response:
        ...     print(f"Status: {response.status_code}")
    """

    def __init__(self, logger: Any) -> None:
        """
        Initialize HTTP client.
        
        Args:
            logger: Logger instance for debug/error output
        """
        self.logger = logger

    def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
             timeout: int = HTTP_DEFAULT_TIMEOUT) -> Optional[Any]:
        """
        Make HTTP POST request - pure communication, no auth logic.
        
        Args:
            url: Target URL (must start with http:// or https://)
            data: Optional JSON data payload (dict will be serialized to JSON)
            timeout: Request timeout in seconds (must be positive, default: 10)
            
        Returns:
            Response object on success, None on failure
            
        Raises:
            ValueError: If url is empty/invalid or timeout is not positive
            
        Example:
            >>> response = client.post(
            ...     "https://api.example.com/data",
            ...     data={"user_id": 123, "action": "update"},
            ...     timeout=5
            ... )
            >>> if response and response.status_code == 200:
            ...     result = response.json()
        """
        # Validate URL
        if not url or not isinstance(url, str):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if not url.startswith(("http://", "https://")):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Validate timeout
        if not isinstance(timeout, int) or timeout <= 0:
            error_msg = _ERROR_INVALID_TIMEOUT.format(timeout=timeout)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Log request
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST.format(method='POST', url=url)}")
        if data:
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST_PAYLOAD.format(data=data)}")

        try:
            response = requests.post(url, json=data, timeout=timeout)
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_RESPONSE_RECEIVED.format(status=response.status_code)}"
            )
            return response

        except requests.Timeout:
            # Specific timeout error
            error_msg = _ERROR_REQUEST_FAILED.format(method='POST', url=url, error=f"Timeout after {timeout}s")
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

        except requests.RequestException as e:
            # Other request-related errors (connection, DNS, etc.)
            error_msg = _ERROR_REQUEST_FAILED.format(method='POST', url=url, error=str(e))
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

    def get(self, url: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: int = HTTP_DEFAULT_TIMEOUT) -> Optional[Any]:
        """
        Make HTTP GET request - pure communication, no auth logic.
        
        Args:
            url: Target URL (must start with http:// or https://)
            params: Optional query parameters (dict will be URL-encoded)
            headers: Optional custom headers
            timeout: Request timeout in seconds (must be positive, default: 10)
            
        Returns:
            Response object on success, None on failure
            
        Example:
            >>> response = client.get(
            ...     "https://api.example.com/users",
            ...     params={"limit": 10, "offset": 0},
            ...     timeout=5
            ... )
            >>> if response and response.status_code == 200:
            ...     users = response.json()
        """
        # Validate URL
        if not url or not isinstance(url, str):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if not url.startswith(("http://", "https://")):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Validate timeout
        if not isinstance(timeout, int) or timeout <= 0:
            error_msg = _ERROR_INVALID_TIMEOUT.format(timeout=timeout)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Log request
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST.format(method='GET', url=url)}")
        if params:
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST_PARAMS.format(params=params)}")

        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_RESPONSE_RECEIVED.format(status=response.status_code)}"
            )
            return response

        except requests.Timeout:
            error_msg = _ERROR_REQUEST_FAILED.format(method='GET', url=url, error=f"Timeout after {timeout}s")
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

        except requests.RequestException as e:
            error_msg = _ERROR_REQUEST_FAILED.format(method='GET', url=url, error=str(e))
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

    def put(self, url: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: int = HTTP_DEFAULT_TIMEOUT) -> Optional[Any]:
        """
        Make HTTP PUT request - pure communication, no auth logic.
        
        Args:
            url: Target URL (must start with http:// or https://)
            data: Optional JSON data payload (dict will be serialized to JSON)
            headers: Optional custom headers
            timeout: Request timeout in seconds (must be positive, default: 10)
            
        Returns:
            Response object on success, None on failure
            
        Example:
            >>> response = client.put(
            ...     "https://api.example.com/users/123",
            ...     data={"name": "Alice", "email": "alice@example.com"},
            ...     timeout=5
            ... )
            >>> if response and response.status_code == 200:
            ...     updated_user = response.json()
        """
        # Validate URL
        if not url or not isinstance(url, str):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if not url.startswith(("http://", "https://")):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Validate timeout
        if not isinstance(timeout, int) or timeout <= 0:
            error_msg = _ERROR_INVALID_TIMEOUT.format(timeout=timeout)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Log request
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST.format(method='PUT', url=url)}")
        if data:
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST_PAYLOAD.format(data=data)}")

        try:
            response = requests.put(url, json=data, headers=headers, timeout=timeout)
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_RESPONSE_RECEIVED.format(status=response.status_code)}"
            )
            return response

        except requests.Timeout:
            error_msg = _ERROR_REQUEST_FAILED.format(method='PUT', url=url, error=f"Timeout after {timeout}s")
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

        except requests.RequestException as e:
            error_msg = _ERROR_REQUEST_FAILED.format(method='PUT', url=url, error=str(e))
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

    def patch(self, url: str, data: Optional[Dict[str, Any]] = None,
              headers: Optional[Dict[str, str]] = None,
              timeout: int = HTTP_DEFAULT_TIMEOUT) -> Optional[Any]:
        """
        Make HTTP PATCH request - pure communication, no auth logic.
        
        Args:
            url: Target URL (must start with http:// or https://)
            data: Optional JSON data payload (dict will be serialized to JSON)
            headers: Optional custom headers
            timeout: Request timeout in seconds (must be positive, default: 10)
            
        Returns:
            Response object on success, None on failure
            
        Example:
            >>> response = client.patch(
            ...     "https://api.example.com/users/123",
            ...     data={"email": "newemail@example.com"},
            ...     timeout=5
            ... )
            >>> if response and response.status_code == 200:
            ...     updated_user = response.json()
        """
        # Validate URL
        if not url or not isinstance(url, str):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if not url.startswith(("http://", "https://")):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Validate timeout
        if not isinstance(timeout, int) or timeout <= 0:
            error_msg = _ERROR_INVALID_TIMEOUT.format(timeout=timeout)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Log request
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST.format(method='PATCH', url=url)}")
        if data:
            self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST_PAYLOAD.format(data=data)}")

        try:
            response = requests.patch(url, json=data, headers=headers, timeout=timeout)
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_RESPONSE_RECEIVED.format(status=response.status_code)}"
            )
            return response

        except requests.Timeout:
            error_msg = _ERROR_REQUEST_FAILED.format(method='PATCH', url=url, error=f"Timeout after {timeout}s")
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

        except requests.RequestException as e:
            error_msg = _ERROR_REQUEST_FAILED.format(method='PATCH', url=url, error=str(e))
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None,
               timeout: int = HTTP_DEFAULT_TIMEOUT) -> Optional[Any]:
        """
        Make HTTP DELETE request - pure communication, no auth logic.
        
        Args:
            url: Target URL (must start with http:// or https://)
            headers: Optional custom headers
            timeout: Request timeout in seconds (must be positive, default: 10)
            
        Returns:
            Response object on success, None on failure
            
        Example:
            >>> response = client.delete(
            ...     "https://api.example.com/users/123",
            ...     timeout=5
            ... )
            >>> if response and response.status_code == 204:
            ...     print("User deleted successfully")
        """
        # Validate URL
        if not url or not isinstance(url, str):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if not url.startswith(("http://", "https://")):
            error_msg = _ERROR_INVALID_URL.format(url=url)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Validate timeout
        if not isinstance(timeout, int) or timeout <= 0:
            error_msg = _ERROR_INVALID_TIMEOUT.format(timeout=timeout)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        # Log request
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_REQUEST.format(method='DELETE', url=url)}")

        try:
            response = requests.delete(url, headers=headers, timeout=timeout)
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_RESPONSE_RECEIVED.format(status=response.status_code)}"
            )
            return response

        except requests.Timeout:
            error_msg = _ERROR_REQUEST_FAILED.format(method='DELETE', url=url, error=f"Timeout after {timeout}s")
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None

        except requests.RequestException as e:
            error_msg = _ERROR_REQUEST_FAILED.format(method='DELETE', url=url, error=str(e))
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None
