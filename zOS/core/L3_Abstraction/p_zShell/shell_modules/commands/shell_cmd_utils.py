# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_utils.py

"""
Utility command execution for zCLI (DEPRECATED).

⚠️ DEPRECATION WARNING ⚠️

This command is DEPRECATED as of v1.5.4 and will be removed in v1.6.0.
Please use 'plugin exec' or 'plugin run' instead.

**Migration Guide**:
    OLD: utils hash_password mypass
    NEW: plugin exec hash_password mypass
    NEW: plugin run hash_password mypass

This module now serves as a redirect to the unified plugin command for
backward compatibility. All functionality has been moved to:
    - shell_cmd_plugin_exec.py: Plugin function execution
    - shell_cmd_plugin.py: Main plugin command router

For more information, see: shell_cmd_plugin.py
"""

from typing import Any, Dict

# Deprecation message
DEPRECATION_WARNING: str = (
    "⚠️  DEPRECATION WARNING: The 'utils' command is deprecated.\n"
    "   Please use 'plugin exec' or 'plugin run' instead.\n"
    "   Example: plugin exec {function} [args...]\n"
    "   This command will be removed in v1.6.0."
)


def execute_utils(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute utility commands (DEPRECATED - redirects to plugin exec).

    This function is DEPRECATED and redirects to the unified plugin command.
    It displays a deprecation warning and then delegates to the plugin_exec
    module for actual execution.

    Parameters
    ----------
    zcli : Any
        zCLI instance
    parsed : Dict[str, Any]
        Parsed command dictionary with keys:
            - "action": Function name
            - "args": Function arguments

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Notes
    -----
    **Deprecation Schedule**:
        - v1.5.4: Command deprecated, warning displayed
        - v1.6.0: Command will be removed

    **Migration**:
        - OLD: utils hash_password mypass
        - NEW: plugin exec hash_password mypass
    """
    # Extract function name from action
    function_name: str = parsed.get("action", "")
    function_args: list = parsed.get("args", [])

    # Display deprecation warning
    warning_msg: str = DEPRECATION_WARNING.format(function=function_name)
    zcli.display.warning(warning_msg)

    # Redirect to plugin_exec module
    from .shell_cmd_plugin_exec import execute_plugin_function

    # Build args list: [function_name] + function_args
    exec_args: list = [function_name] + function_args

    # Delegate to plugin exec
    execute_plugin_function(zcli, exec_args)
