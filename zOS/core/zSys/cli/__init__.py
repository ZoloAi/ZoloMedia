# zSys/cli/__init__.py
"""
CLI command handlers for zolo entry point.

This module provides handler functions for all `zolo` CLI commands.
"""

from .cli_commands import (
    display_info,
    handle_shell_command,
    handle_config_command,
    handle_ztests_command,
    handle_migrate_command,
    handle_uninstall_command,
    handle_script_command,
    handle_zspark_command,
)

__all__ = [
    'display_info',
    'handle_shell_command',
    'handle_config_command',
    'handle_ztests_command',
    'handle_migrate_command',
    'handle_uninstall_command',
    'handle_script_command',
    'handle_zspark_command',
]
