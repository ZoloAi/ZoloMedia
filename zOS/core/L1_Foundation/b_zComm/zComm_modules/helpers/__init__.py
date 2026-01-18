# zCLI/subsystems/zComm/zComm_modules/helpers/__init__.py
"""
Helper Utilities for zComm Communication Subsystem.

This package contains utility functions and classes that support the core zComm
functionality, providing network-level operations and validation helpers.

Current Utilities:
    NetworkUtils: Cross-platform network and port management
        - Port availability checking (is_port_available)
        - Service readiness detection
        - Network diagnostics and validation
        - Platform-agnostic implementations

Architecture:
    Helper modules are stateless utility classes that accept a logger during
    initialization and provide focused, reusable functionality. They follow
    the Single Responsibility Principle and avoid external dependencies beyond
    standard library and logging.

Design Patterns:
    - Dependency Injection: Logger passed to __init__
    - Stateless Operations: Methods are idempotent
    - Cross-Platform: OS-specific logic abstracted
    - Type-Safe: Full type hint coverage

Usage:
    ```python
    from zOS.L1_Foundation.b_zComm.zComm_modules.helpers import NetworkUtils
    
    # Typically accessed via zComm
    utils = NetworkUtils(logger)
    if utils.is_port_available(5432):
        print("Port 5432 is free")
    ```

Future Additions:
    - ValidationHelpers: Input validation for communication parameters
    - RetryHelpers: Exponential backoff for network operations
    - TimeoutHelpers: Configurable timeout management

See Also:
    - network_utils.py: NetworkUtils implementation
    - Documentation/zComm_GUIDE.md: Complete helper documentation
"""

from .network_utils import NetworkUtils

__all__ = [
    "NetworkUtils",
]
