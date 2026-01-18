# zSys/install/__init__.py
"""
Installation and uninstallation utilities for zolo-zcli.

This module provides both detection and removal functionality organized
into dedicated submodules for scalability and maintainability.
"""

# Detection utilities
from .detection import detect_installation_type

# Removal - Core functions (reusable)
from .removal import (
    get_optional_dependencies,
    remove_package,
    remove_user_data,
    remove_dependencies,
)

# Removal - CLI handlers (interactive)
from .removal import (
    cli_uninstall_complete,
    cli_uninstall_package_only,
    cli_uninstall_data_only,
)

__all__ = [
    # Detection
    "detect_installation_type",
    
    # Core removal functions
    "get_optional_dependencies",
    "remove_package",
    "remove_user_data",
    "remove_dependencies",
    
    # CLI handlers
    "cli_uninstall_complete",
    "cli_uninstall_package_only",
    "cli_uninstall_data_only",
]

