"""
zSys - System Foundation (Layer 0)

Pre-boot system utilities shared by entry point (main.py) and framework (zCLI/).

This module provides foundational utilities that are needed before the full zCLI
framework is initialized. It is intentionally lightweight with no dependencies on
the zKernel framework itself.

Architecture:
    - Layer 0: System Foundation (this module)
    - Shared by both main.py (entry point) and zCLI/ (framework)
    - No circular dependencies
    - Pure utility functions and classes

Modules:
    - paths: Cross-platform path resolution for ecosystem
    - logger/: Unified logging system (bootstrap, console, formats)
    - install/: Installation detection and removal utilities
    - formatting/: Terminal colors and output utilities
    - errors/: Error handling (validation, exceptions, traceback)

Usage:
    from zOS.logger import BootstrapLogger, ConsoleLogger, UnifiedFormatter
    from zOS.install import detect_installation_type, cli_uninstall_complete
    from zOS.formatting import Colors, print_ready_message
    from zOS.errors import zKernelException, zTraceback, validate_zkernel_instance
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
    # Error handling subsystem
    "errors",
]

