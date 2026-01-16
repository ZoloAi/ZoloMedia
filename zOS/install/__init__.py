# zSys/install/__init__.py
"""
Installation and uninstallation utilities for zolo-zcli.

This module provides both detection and removal functionality organized
into dedicated submodules for scalability and maintainability.
"""

# Detection utilities
from .detection import detect_installation_type

# Removal - Core functions (reusable, OS-level)
from .removal import (
    get_optional_dependencies,
    remove_package,
    remove_user_data,
    remove_dependencies,
)

# NOTE: CLI handlers (cli_uninstall_*) have been extracted to @temp_zKernel/cli/uninstall.py
# These were framework-level functions that required zDisplay and zKernel.zCLI
# They will be merged into zKernel when it joins the monorepo

__all__ = [
    # Detection
    "detect_installation_type",
    
    # Core removal functions (OS-level)
    "get_optional_dependencies",
    "remove_package",
    "remove_user_data",
    "remove_dependencies",
    
    # CLI handlers extracted to @temp_zKernel/cli/uninstall.py (framework-level)
    # "cli_uninstall_complete",
    # "cli_uninstall_package_only",
    # "cli_uninstall_data_only",
]

