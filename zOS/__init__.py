"""
zOS - System Foundation (OS Primitives Layer)

Standalone OS utilities for Zolo applications with NO framework dependencies.

This module provides foundational OS-level utilities that can be used by any
Zolo application (zlsp, zOS CLI, zKernel framework, standalone tools, etc.).

Architecture:
    - Layer: OS Primitives (standalone, no zKernel dependency)
    - Used by: zlsp, zKernel, user applications
    - Dependencies: Only standard library + platformdirs, PyYAML

Modules:
    - paths: Cross-platform path resolution (platformdirs)
    - logger/: Unified logging system (bootstrap, console, formats)
    - install/: Installation detection and removal utilities
    - formatting/: Terminal colors and output utilities
    - errors/: OS-level exceptions (zMachinePathError, UnsupportedOSError)
    - machine/: Machine detection and zConfig.machine.zolo generation
    - utils/: File opening, OS primitives
    - cli/: zolo command-line interface

Public API:
    Import from package root for stable API:
        from zOS import BootstrapLogger, ConsoleLogger
        from zOS import get_ecosystem_root, get_product_logs
        from zOS.machine import get_machine_info
        from zOS.utils.open import open_file, open_url

Usage:
    from zOS.logger import BootstrapLogger, ConsoleLogger, UnifiedFormatter
    from zOS.install import detect_installation_type
    from zOS.formatting import Colors
    from zOS.errors import zMachinePathError, UnsupportedOSError
    from zOS.machine import get_machine_info
    from zOS.utils.open import open_file, open_url
"""

# Export all public APIs
from .paths import (
    get_ecosystem_root,
    get_product_root,
    get_ecosystem_logs,
    get_product_logs,
    get_ecosystem_cache,
)
from .logger import (
    BootstrapLogger,
    ConsoleLogger,
    UnifiedFormatter,
    format_log_message,
    format_bootstrap_verbose,
)
from . import install
from . import formatting
from . import errors

__all__ = [
    # Paths (ecosystem)
    "get_ecosystem_root",
    "get_product_root",
    "get_ecosystem_logs",
    "get_product_logs",
    "get_ecosystem_cache",
    # Logger (unified)
    "BootstrapLogger",
    "ConsoleLogger",
    "UnifiedFormatter",
    "format_log_message",
    "format_bootstrap_verbose",
    # Installation subsystem
    "install",
    # Formatting subsystem
    "formatting",
    # Error handling subsystem (OS-level only)
    "errors",
]
