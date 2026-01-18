# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_plugin.py

"""
Unified plugin command router for zCLI shell.

This module provides the main entry point for all plugin-related commands in the zCLI
shell, routing requests to either execution (plugin_exec.py) or management (plugin_mgmt.py)
submodules based on the requested action. It implements a clean separation between
plugin function execution and plugin cache management.

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

The plugin command provides a unified interface for all plugin operations:
    - **Execution**: Run plugin functions loaded by zUtils (plugin exec/run)
    - **Management**: Load, show, clear, reload plugins in cache (plugin load/show/clear/reload)

This architecture ensures clear separation of concerns and keeps the main router thin
while delegate complexity is handled by specialized submodules.

═══════════════════════════════════════════════════════════════════════════════
COMMAND SYNTAX
═══════════════════════════════════════════════════════════════════════════════

**Plugin Execution**:
    plugin exec <function> [args...]    # Execute plugin function
    plugin run <function> [args...]     # Alternative syntax

**Plugin Management**:
    plugin load <zPath>                 # Load plugin from zPath
    plugin show                         # Show loaded plugins
    plugin show cache                   # Show cache statistics
    plugin clear [pattern]              # Clear plugin cache
    plugin reload <zPath>               # Reload plugin (clear + load)

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

**Routing Strategy**:
    execute_plugin() (main router)
        ├─→ plugin exec/run → shell_cmd_plugin_exec.execute_plugin_function()
        └─→ plugin load/show/clear/reload → shell_cmd_plugin_mgmt functions

**File Organization**:
    - shell_cmd_plugin.py: Main router (THIS FILE)
    - shell_cmd_plugin_exec.py: Execution logic (thin router to zUtils)
    - shell_cmd_plugin_mgmt.py: Management logic (cache operations via zLoader)

**Design Benefits**:
    - Single command namespace for users (plugin)
    - Modular code organization (separate files by concern)
    - Easy to extend (add new subcommands)
    - Clear separation of execution vs management

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION POINTS
═══════════════════════════════════════════════════════════════════════════════

**Dependencies**:
    - zUtils (Week 6.15): Plugin execution subsystem (zcli.utils.function())
    - zLoader (Week 6.9): Plugin cache management (zcli.loader.cache.plugin_cache)
    - shell_cmd_plugin_exec: Execution submodule
    - shell_cmd_plugin_mgmt: Management submodule

**Used By**:
    - zShell command dispatcher (shell_router.py or similar)
    - Parses: {"action": "exec|run|load|show|clear|reload", "args": [...]}

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

    # Execute a plugin function
    plugin exec hash_password mypass123
    # Routes to: plugin_exec.execute_plugin_function(zcli, ["hash_password", "mypass123"])

    # Load a plugin
    plugin load @.plugins.auth
    # Routes to: plugin_mgmt.load_plugin(zcli, ["@.plugins.auth"])

    # Show loaded plugins
    plugin show
    # Routes to: plugin_mgmt.show_plugins(zcli, [])

    # Show cache statistics
    plugin show cache
    # Routes to: plugin_mgmt.show_plugins(zcli, ["cache"])

    # Clear plugin cache
    plugin clear auth
    # Routes to: plugin_mgmt.clear_plugins(zcli, ["auth"])

    # Reload a plugin
    plugin reload @.plugins.auth
    # Routes to: plugin_mgmt.reload_plugin(zcli, ["@.plugins.auth"])

═══════════════════════════════════════════════════════════════════════════════
AUTHOR & VERSION
═══════════════════════════════════════════════════════════════════════════════

Author: zCLI Development Team
Version: 1.5.4
Last Updated: 2025-11-07
"""

from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Action Constants
ACTION_EXEC: str = "exec"
ACTION_RUN: str = "run"
ACTION_LOAD: str = "load"
ACTION_SHOW: str = "show"
ACTION_CLEAR: str = "clear"
ACTION_RELOAD: str = "reload"

# Error Messages
ERROR_NO_ACTION: str = "Usage: plugin <command> [args]\nCommands: exec, run, load, show, clear, reload"
ERROR_UNKNOWN_ACTION: str = "Unknown plugin command: {action}"

# Dict Keys
KEY_ACTION: str = "action"
KEY_ARGS: str = "args"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def execute_plugin(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Route plugin commands to appropriate submodule (exec or mgmt).

    This is the main entry point for all plugin commands in zShell. It extracts
    the action and arguments from the parsed command dict and routes the request
    to either the execution submodule (plugin_exec.py) or the management submodule
    (plugin_mgmt.py) based on the requested action.

    Parameters
    ----------
    zcli : Any
        zCLI instance providing access to subsystems (utils, loader, display, logger)
    parsed : Dict[str, Any]
        Parsed command dictionary with keys:
            - "action": Command action (exec, run, load, show, clear, reload)
            - "args": List of command arguments

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Examples
    --------
    **Execute Plugin Function**:
        >>> parsed = {"action": "exec", "args": ["hash_password", "mypass123"]}
        >>> execute_plugin(zcli, parsed)
        # Routes to: plugin_exec.execute_plugin_function(zcli, ["hash_password", "mypass123"])

    **Load Plugin**:
        >>> parsed = {"action": "load", "args": ["@.plugins.auth"]}
        >>> execute_plugin(zcli, parsed)
        # Routes to: plugin_mgmt.load_plugin(zcli, ["@.plugins.auth"])

    **Show Plugins**:
        >>> parsed = {"action": "show", "args": []}
        >>> execute_plugin(zcli, parsed)
        # Routes to: plugin_mgmt.show_plugins(zcli, [])

    Notes
    -----
    **Routing Logic**:
        - exec/run → shell_cmd_plugin_exec.execute_plugin_function()
        - load/show/clear/reload → shell_cmd_plugin_mgmt functions

    **Error Handling**:
        - No action: Display usage message
        - Unknown action: Display error with unknown action name

    **UI Adapter Pattern**:
        Returns None - all output via zDisplay (supports Terminal + Bifrost modes)
    """
    # Extract action and args from parsed dict
    action: Optional[str] = parsed.get(KEY_ACTION)
    args: List[str] = parsed.get(KEY_ARGS, [])

    # Validate action exists
    if not action:
        zcli.display.error(ERROR_NO_ACTION)
        return

    # Route to execution submodule (plugin exec/run)
    if action in (ACTION_EXEC, ACTION_RUN):
        from .shell_cmd_plugin_exec import execute_plugin_function
        execute_plugin_function(zcli, args)
        return

    # Route to management submodule (plugin load/show/clear/reload)
    if action in (ACTION_LOAD, ACTION_SHOW, ACTION_CLEAR, ACTION_RELOAD):
        from .shell_cmd_plugin_mgmt import (
            load_plugin, show_plugins, clear_plugins, reload_plugin
        )
        if action == ACTION_LOAD:
            load_plugin(zcli, args)
        elif action == ACTION_SHOW:
            show_plugins(zcli, args)
        elif action == ACTION_CLEAR:
            clear_plugins(zcli, args)
        elif action == ACTION_RELOAD:
            reload_plugin(zcli, args)
        return

    # Unknown action
    error_msg: str = ERROR_UNKNOWN_ACTION.format(action=action)
    zcli.display.error(error_msg)
