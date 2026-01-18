# zCLI/subsystems/zComm/zComm_modules/services/__init__.py
"""
Service Management Implementations for Local Database Services.

This package contains concrete service implementations for managing local database
and cache services that zCLI applications may depend on. Each service follows a
common interface for lifecycle management and status reporting.

Current Services:
    PostgreSQLService: PostgreSQL database service management
        - Cross-platform start/stop/status operations
        - Homebrew integration (macOS)
        - systemctl integration (Linux)
        - Connection info and readiness checks
        - Default port: 5432

Service Interface (Common Pattern):
    All service implementations provide:
    - start() -> bool: Start the service
    - stop() -> bool: Stop the service
    - status() -> str: Get service status ("running", "stopped", "unknown")
    - get_connection_info() -> Dict: Get connection details (host, port, etc.)
    - Dependency Injection: Logger passed to __init__
    - Cross-Platform Support: OS-specific implementations abstracted

Planned Services (Deferred):
    - RedisService: Redis cache service management (port 6379)
    - MongoDBService: MongoDB database service management (port 27017)
    - MySQLService: MySQL database service management (port 3306)

Architecture:
    Services are managed by ServiceManager (comm_services.py) which provides:
    - Service registration and discovery
    - Unified start/stop/status interface
    - Multi-service orchestration
    - Error handling and logging

Usage:
    ```python
    from zOS.L1_Foundation.b_zComm.zComm_modules.services import PostgreSQLService
    
    # Typically accessed via ServiceManager
    service = PostgreSQLService(logger)
    service.start()
    info = service.get_connection_info()
    # info = {"host": "localhost", "port": 5432, "default_db": "postgres"}
    ```

Integration:
    - Used by: ServiceManager (comm_services.py)
    - Accessed via: zComm.services.start("postgresql")
    - Dependencies: subprocess, socket, logging

See Also:
    - postgresql_service.py: PostgreSQLService implementation
    - comm_services.py: ServiceManager orchestration
    - Documentation/zComm_GUIDE.md: Service management guide
"""

from .postgresql_service import PostgreSQLService

__all__ = ['PostgreSQLService']
