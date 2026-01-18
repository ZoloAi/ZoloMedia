"""
zSys - System Foundation (Layer 0)

Pre-boot system utilities shared by entry point (main.py) and framework (zCLI/).

This module provides foundational utilities that are needed before the full zCLI
framework is initialized. It is intentionally lightweight with no dependencies on
the zCLI framework itself.

Architecture:
    - Layer 0: System Foundation (this module)
    - Shared by both main.py (entry point) and zCLI/ (framework)
    - No circular dependencies
    - Pure utility functions and classes

Modules:
    - logger/: Unified logging system (bootstrap, console, formats)
    - install/: Installation detection and removal utilities
    - formatting/: Terminal colors and output utilities
    - errors/: Error handling (validation, exceptions, traceback)

Usage:
    from zSys.logger import BootstrapLogger, ConsoleLogger, UnifiedFormatter
    from zSys.install import detect_installation_type, cli_uninstall_complete
    from zSys.formatting import Colors, print_ready_message
    from zSys.errors import zCLIException, zTraceback, validate_zcli_instance
"""

# Export all public APIs
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

