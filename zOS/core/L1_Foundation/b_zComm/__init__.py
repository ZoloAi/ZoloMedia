# zCLI/subsystems/zComm/__init__.py
"""
Communication & Service Management Subsystem for zCLI.

This package provides low-level communication infrastructure including HTTP client,
service management, and network utilities for zCLI applications.

Architecture:
    zComm is a Layer 0 subsystem (initialized before zDisplay) that provides the
    communication backbone for zCLI. It manages:
    
    - HTTP Communication: Synchronous HTTP requests via HTTPClient
    - Service Management: Local service lifecycle (PostgreSQL, Redis, MongoDB)
    - Network Utilities: Port checking, availability detection

Main Components:
    - zComm: Primary facade class providing unified interface to all communication features
    - ServiceManager: Manages local database/cache services
    - HTTPClient: Synchronous HTTP requests (GET, POST, PUT, PATCH, DELETE)
    - NetworkUtils: Network availability and port checking

Usage:
    ```python
    from zOS.L1_Foundation.b_zComm import zComm
    
    # Initialize zComm (done automatically by zCLI)
    comm = zComm(zcli_instance)
    
    # Access components
    comm.services.start("postgresql")
    response = comm.http_get("https://api.example.com")
    is_free = comm.check_port(8080)
    ```

Integration:
    - Depends on: zSession (via zcli.session), zLogger, zConfig
    - Used by: zBifrost (Layer 2), zDisplay, zData, zServer, user applications

Note:
    For WebSocket orchestration (Terminal↔Web bridge), see zBifrost subsystem (Layer 2).
    zBifrost coordinates display/auth/data subsystems over WebSocket infrastructure.

Exports:
    - zComm: Main subsystem facade (recommended entry point)

See Also:
    - Documentation/zComm_GUIDE.md: Complete usage guide
    - zComm_modules/: Individual module implementations
    - zBifrost: WebSocket bridge orchestrator (Layer 2)
"""

from .zComm import zComm

__all__ = ['zComm']
