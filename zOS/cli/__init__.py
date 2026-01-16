# zSys/cli/__init__.py
"""
CLI command handlers for zolo entry point.

This module provides handler functions for all `zolo` CLI commands.

Active handlers (OS-level):
- display_info
- handle_machine_command (+ edit, open, system, user)
- handle_open_command
- handle_script_command

Extracted to @temp_zKernel (framework-level):
- handle_zspark_command → @temp_zKernel/cli/zspark.py

Commented out (zKernel framework - to be refactored):
- handle_shell_command
- handle_ztests_command
- handle_migrate_command
- handle_uninstall_command
"""

from .cli_commands import (
    display_info,
    handle_machine_command,
    handle_machine_open_command,
    handle_machine_edit_command,
    handle_machine_system_command,
    handle_machine_user_command,
    handle_open_command,
    # handle_shell_command,
    # handle_ztests_command,
    # handle_migrate_command,
    # handle_install_command,
    # handle_uninstall_command,
    handle_script_command,
    # handle_zspark_command,  # Extracted to @temp_zKernel/cli/zspark.py
)

__all__ = [
    'display_info',
    'handle_machine_command',
    'handle_machine_open_command',
    'handle_machine_edit_command',
    'handle_machine_system_command',
    'handle_machine_user_command',
    'handle_open_command',
    # 'handle_shell_command',
    # 'handle_ztests_command',
    # 'handle_migrate_command',
    # 'handle_install_command',
    # 'handle_uninstall_command',
    'handle_script_command',
    # 'handle_zspark_command',  # Extracted to @temp_zKernel/cli/zspark.py
]
