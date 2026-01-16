# @temp_zKernel/cli/__init__.py
"""
Framework CLI handlers extracted from zOS.

STAGING AREA - DO NOT USE IN PRODUCTION

This module contains framework-specific CLI command handlers that were extracted
from zOS (OS primitives layer) to maintain clean separation.

These will be merged into zKernel when it joins the monorepo.

See @temp_zKernel/README.md for merge instructions.
"""

from .uninstall import (
    cli_uninstall_complete,
    cli_uninstall_package_only,
    cli_uninstall_data_only,
)

from .zspark import (
    handle_zspark_command,
)

__all__ = [
    # Uninstall CLI handlers
    "cli_uninstall_complete",
    "cli_uninstall_package_only",
    "cli_uninstall_data_only",
    # zSpark bootstrapping command
    "handle_zspark_command",
]
