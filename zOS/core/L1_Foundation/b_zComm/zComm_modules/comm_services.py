# zCLI/subsystems/zComm/zComm_modules/comm_services.py
"""
Service Manager for local development services.

Manages the lifecycle of local services like PostgreSQL, Redis, and MongoDB.
Provides a unified interface for starting, stopping, restarting, and querying
the status of registered services.

Architecture:
    - Registry-based pattern: Services are registered in self.services dict
    - Service abstraction: Each service implements a common interface
    - Extensible: New services can be added via _register_services()
    
Example:
    >>> manager = ServiceManager(logger)
    >>> manager.start('postgresql', port=5432)
    >>> status = manager.status('postgresql')
    >>> info = manager.get_connection_info('postgresql')
    >>> manager.stop('postgresql')
"""

from zOS import Any, Dict, Optional
from .services.postgresql_service import PostgreSQLService
from .comm_constants import SERVICE_POSTGRESQL, STATUS_KEY_ERROR

# Module Constants

# Logging
_LOG_PREFIX = "[ServiceManager]"

# Future service identifiers:
# SERVICE_REDIS = "redis"
# SERVICE_MONGODB = "mongodb"

# Log Messages - Initialization
_LOG_INIT = "Initializing ServiceManager"
_LOG_INIT_COMPLETE = "ServiceManager initialized with {count} services"
_LOG_REGISTERING = "Registering available services"
_LOG_REGISTERED_SERVICE = "Registered {service} service"
_LOG_REGISTRATION_COMPLETE = "Service registration completed"

# Log Messages - Service Operations
_LOG_STARTING_SERVICE = "Starting service: {service}"
_LOG_SERVICE_STARTED = "Service '{service}' started successfully"
_LOG_STOPPING_SERVICE = "Stopping service: {service}"
_LOG_SERVICE_STOPPED = "Service '{service}' stopped successfully"
_LOG_RESTARTING_SERVICE = "Restarting service: {service}"
_LOG_SERVICE_RESTARTED = "Service '{service}' restarted successfully"

# Log Messages - Status & Info
_LOG_STATUS_SINGLE = "Getting status for service: {service}"
_LOG_STATUS_ALL = "Getting status for all services"
_LOG_STATUS_RESULT = "Service '{service}' status: {status}"
_LOG_STATUS_ALL_RESULT = "All services status: {status}"
_LOG_CONNECTION_INFO = "Getting connection info for service: {service}"
_LOG_CONNECTION_INFO_RESULT = "Service '{service}' connection info: {info}"

# Error Messages
_ERROR_UNKNOWN_SERVICE = "Unknown service: {service}"
_ERROR_START_FAILED = "Failed to start service '{service}'"
_ERROR_STOP_FAILED = "Failed to stop service '{service}'"
_ERROR_STOP_FAILED_RESTART = "Failed to stop service '{service}' during restart"
_ERROR_RESTART_FAILED = "Failed to restart service '{service}'"
_ERROR_INVALID_SERVICE_NAME = "Invalid service name: {service}"
_ERROR_SERVICE_NAME_EMPTY = "Service name cannot be empty or None"


class ServiceManager:
    """
    Manages local development services lifecycle.
    
    Provides a unified interface for managing local development services like
    PostgreSQL, Redis, and MongoDB. Uses a registry-based pattern where services
    are registered and accessed via a common interface.
    
    Architecture:
        - Services registered in self.services dict by name
        - Each service must implement: start(), stop(), status(), get_connection_info()
        - Extensible via _register_services() method
        
    Attributes:
        logger: Logger instance for debug/info/error output
        services: Dict mapping service names to service instances
        
    Example:
        >>> manager = ServiceManager(logger)
        >>> # Start PostgreSQL on custom port
        >>> success = manager.start('postgresql', port=5433)
        >>> # Check status
        >>> status = manager.status('postgresql')
        >>> # Get connection string
        >>> conn = manager.get_connection_info('postgresql')
        >>> # Stop service
        >>> manager.stop('postgresql')
    """

    def __init__(self, logger: Any) -> None:
        """
        Initialize ServiceManager with logger.
        
        Args:
            logger: Logger instance for output (required)
            
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger cannot be None")

        self.logger = logger
        self.services: Dict[str, Any] = {}

        self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_INIT}")
        self._register_services()
        self.logger.framework.debug(
            f"{_LOG_PREFIX} {_LOG_INIT_COMPLETE.format(count=len(self.services))}"
        )

    def _register_services(self) -> None:
        """
        Register available service handlers.
        
        This is where new services should be added. Each service should
        implement the common service interface: start(), stop(), status(),
        and get_connection_info().
        """
        self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_REGISTERING}")

        # Register PostgreSQL
        self.services[SERVICE_POSTGRESQL] = PostgreSQLService(self.logger)
        self.logger.framework.debug(
            f"{_LOG_PREFIX} {_LOG_REGISTERED_SERVICE.format(service='PostgreSQL')}"
        )

        # TODO: Add Redis service support
        # self.services[SERVICE_REDIS] = RedisService(self.logger)
        # self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_REGISTERED_SERVICE.format(service='Redis')}")

        # TODO: Add MongoDB service support
        # self.services[SERVICE_MONGODB] = MongoDBService(self.logger)
        # self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_REGISTERED_SERVICE.format(service='MongoDB')}")

        self.logger.framework.debug(f"{_LOG_PREFIX} {_LOG_REGISTRATION_COMPLETE}")

    def _validate_service_name(self, service_name: Any) -> None:
        """
        Validate service name parameter.
        
        Args:
            service_name: Service name to validate
            
        Raises:
            ValueError: If service_name is invalid (None, empty, not a string, whitespace-only)
        """
        if service_name is None or service_name == "":
            error_msg = _ERROR_SERVICE_NAME_EMPTY
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if not isinstance(service_name, str):
            error_msg = _ERROR_INVALID_SERVICE_NAME.format(service=service_name)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

        if service_name.strip() == "":
            error_msg = _ERROR_SERVICE_NAME_EMPTY
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            raise ValueError(error_msg)

    def _get_service(self, service_name: str) -> Optional[Any]:
        """
        Get service instance by name with validation.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance if found, None otherwise
            
        Note:
            Logs error if service is not found
        """
        if service_name not in self.services:
            error_msg = _ERROR_UNKNOWN_SERVICE.format(service=service_name)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return None
        return self.services[service_name]

    def _log_operation_result(self, action: str, service_name: str, success: bool) -> None:
        """
        Log the result of a service operation (DRY helper).
        
        Args:
            action: Operation name ('started', 'stopped', 'restarted')
            service_name: Name of the service
            success: Whether the operation succeeded
        """
        if success:
            if action == "started":
                msg = _LOG_SERVICE_STARTED.format(service=service_name)
            elif action == "stopped":
                msg = _LOG_SERVICE_STOPPED.format(service=service_name)
            elif action == "restarted":
                msg = _LOG_SERVICE_RESTARTED.format(service=service_name)
            else:
                msg = f"Service '{service_name}' {action} successfully"
            self.logger.info(f"{_LOG_PREFIX} {msg}")
        else:
            if action == "started":
                msg = _ERROR_START_FAILED.format(service=service_name)
            elif action == "stopped":
                msg = _ERROR_STOP_FAILED.format(service=service_name)
            elif action == "restarted":
                msg = _ERROR_RESTART_FAILED.format(service=service_name)
            else:
                msg = f"Failed to {action} service '{service_name}'"
            self.logger.error(f"{_LOG_PREFIX} {msg}")

    def start(self, service_name: str, **kwargs: Any) -> bool:
        """
        Start a service with optional configuration.
        
        Args:
            service_name: Name of the service to start (e.g., 'postgresql')
            **kwargs: Service-specific configuration options (e.g., port=5432)
            
        Returns:
            True if service started successfully, False otherwise
            
        Raises:
            ValueError: If service_name is invalid
            
        Example:
            >>> manager.start('postgresql', port=5433, data_dir='/custom/path')
            True
        """
        self._validate_service_name(service_name)
        self.logger.info(f"{_LOG_PREFIX} {_LOG_STARTING_SERVICE.format(service=service_name)}")

        service = self._get_service(service_name)
        if service is None:
            return False

        result = service.start(**kwargs)
        self._log_operation_result("started", service_name, result)
        return result

    def stop(self, service_name: str) -> bool:
        """
        Stop a running service.
        
        Args:
            service_name: Name of the service to stop
            
        Returns:
            True if service stopped successfully, False otherwise
            
        Raises:
            ValueError: If service_name is invalid
            
        Example:
            >>> manager.stop('postgresql')
            True
        """
        self._validate_service_name(service_name)
        self.logger.info(f"{_LOG_PREFIX} {_LOG_STOPPING_SERVICE.format(service=service_name)}")

        service = self._get_service(service_name)
        if service is None:
            return False

        result = service.stop()
        self._log_operation_result("stopped", service_name, result)
        return result

    def restart(self, service_name: str) -> bool:
        """
        Restart a service (stop then start).
        
        Args:
            service_name: Name of the service to restart
            
        Returns:
            True if service restarted successfully, False otherwise
            
        Raises:
            ValueError: If service_name is invalid
            
        Example:
            >>> manager.restart('postgresql')
            True
        """
        self._validate_service_name(service_name)
        self.logger.info(f"{_LOG_PREFIX} {_LOG_RESTARTING_SERVICE.format(service=service_name)}")

        stop_result = self.stop(service_name)
        if not stop_result:
            error_msg = _ERROR_STOP_FAILED_RESTART.format(service=service_name)
            self.logger.error(f"{_LOG_PREFIX} {error_msg}")
            return False

        start_result = self.start(service_name)
        self._log_operation_result("restarted", service_name, start_result)
        return start_result

    def status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get service status.
        
        Args:
            service_name: Name of specific service, or None for all services
            
        Returns:
            Status dict for specific service, or dict of all service statuses.
            Returns error dict with STATUS_KEY_ERROR key if service not found.
            
        Raises:
            ValueError: If service_name is invalid (but not None)
            
        Example:
            >>> # Single service
            >>> manager.status('postgresql')
            {'running': True, 'port': 5432, 'pid': 1234}
            
            >>> # All services
            >>> manager.status()
            {'postgresql': {'running': True}, 'redis': {'running': False}}
            
            >>> # Unknown service
            >>> manager.status('unknown')
            {'error': 'Unknown service: unknown'}
        """
        if service_name:
            self._validate_service_name(service_name)
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_STATUS_SINGLE.format(service=service_name)}"
            )
            
            service = self._get_service(service_name)
            if service is None:
                return {
                    STATUS_KEY_ERROR: _ERROR_UNKNOWN_SERVICE.format(service=service_name)
                }
                
            status = service.status()
            self.logger.debug(
                f"{_LOG_PREFIX} {_LOG_STATUS_RESULT.format(service=service_name, status=status)}"
            )
            return status

        # Return status for all services
        self.logger.debug(f"{_LOG_PREFIX} {_LOG_STATUS_ALL}")
        status = {
            name: service.status()
            for name, service in self.services.items()
        }
        self.logger.debug(
            f"{_LOG_PREFIX} {_LOG_STATUS_ALL_RESULT.format(status=status)}"
        )
        return status

    def get_connection_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get connection information for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dict with connection details (host, port, etc.) or None if service not found
            
        Raises:
            ValueError: If service_name is invalid
            
        Example:
            >>> manager.get_connection_info('postgresql')
            {'host': 'localhost', 'port': 5432, 'connection_string': '...'}
        """
        self._validate_service_name(service_name)
        self.logger.debug(
            f"{_LOG_PREFIX} {_LOG_CONNECTION_INFO.format(service=service_name)}"
        )

        service = self._get_service(service_name)
        if service is None:
            return None

        info = service.get_connection_info()
        self.logger.debug(
            f"{_LOG_PREFIX} {_LOG_CONNECTION_INFO_RESULT.format(service=service_name, info=info)}"
        )
        return info
