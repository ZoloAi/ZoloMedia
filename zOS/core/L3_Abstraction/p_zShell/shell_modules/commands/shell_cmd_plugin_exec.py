# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_plugin_exec.py

"""
Plugin function execution for zCLI shell.

This module provides plugin function execution via the zUtils subsystem. It serves as
a thin router that validates inputs, executes plugin functions loaded by zUtils, and
displays results via zDisplay. This module handles the "plugin exec" and "plugin run"
subcommands.

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

Execute plugin functions that have been loaded by the zUtils subsystem (boot-time plugins
from zSpark configuration or runtime-loaded plugins). This module provides a shell
interface to call plugin functions dynamically.

**Key Responsibilities**:
    1. Validate function name and arguments
    2. Validate zUtils subsystem availability
    3. Execute plugin functions via zcli.utils.function()
    4. Display results or errors via zDisplay
    5. Log execution for debugging

═══════════════════════════════════════════════════════════════════════════════
COMMAND SYNTAX
═══════════════════════════════════════════════════════════════════════════════

    plugin exec <function> [args...]    # Execute plugin function
    plugin run <function> [args...]     # Alternative syntax

**Examples**:
    plugin exec hash_password mypass123
    plugin run generate_id
    plugin exec calculate 10 20 30

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

**Integration with zUtils (Week 6.15)**:
    - zUtils loads plugins from zSpark["plugins"] during boot
    - zUtils delegates storage to zLoader.plugin_cache (unified cache)
    - zUtils exposes plugin functions as methods: zcli.utils.function()
    - This module simply routes to those exposed methods

**Execution Flow**:
    1. Validate args (needs function name)
    2. Validate zUtils subsystem exists (zcli.utils)
    3. Validate function exists (hasattr check)
    4. Execute function via getattr() with try/except
    5. Format and display result via zDisplay
    6. Log execution (debug + info)

**Error Handling**:
    - No function name: Display usage error
    - No zUtils subsystem: Display subsystem error
    - Function not found: Display function not found error
    - Execution error: Display execution error with exception details

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION POINTS
═══════════════════════════════════════════════════════════════════════════════

**Dependencies**:
    - zUtils (Week 6.15): Plugin execution subsystem (994 lines, A+ grade)
        - Phase 1: Type hints, constants, docstrings
        - Phase 2: Unified storage with zLoader.plugin_cache
        - Phase 3: Collision detection, stats/metrics, mtime auto-reload

**Used By**:
    - shell_cmd_plugin.py: Main router (routes "exec"/"run" actions here)

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

    # Hash a password using auth plugin
    plugin exec hash_password mypass123
    # Output: [OK] hash_password() executed successfully
    #         Result: $2b$12$...

    # Generate a unique ID using generator plugin
    plugin run generate_id
    # Output: [OK] generate_id() executed successfully
    #         Result: uuid-123-456-789

    # Calculate with multiple arguments
    plugin exec calculate 10 20 30
    # Output: [OK] calculate() executed successfully
    #         Result: 60

═══════════════════════════════════════════════════════════════════════════════
AUTHOR & VERSION
═══════════════════════════════════════════════════════════════════════════════

Author: zCLI Development Team
Version: 1.5.4
Last Updated: 2025-11-07
"""

from typing import Any, List

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Error Messages
ERROR_NO_ARGS: str = "Usage: plugin exec <function> [args...]\nExample: plugin exec hash_password mypass"
ERROR_NO_UTILS: str = "zUtils subsystem not available - plugins not loaded"
ERROR_NO_FUNCTION: str = "Function '{function}' not found in loaded plugins\nUse 'plugin show' to see available functions"
ERROR_EXEC_FAILED: str = "Failed to execute {function}(): {error}"

# Success Messages
MSG_EXECUTING: str = "Executing plugin function: {function}()"
MSG_SUCCESS: str = "[OK] {function}() executed successfully"
MSG_RESULT: str = "Result:"

# Log Messages
LOG_EXECUTING: str = "Executing plugin function: %s with args: %s"
LOG_SUCCESS: str = "Plugin function %s executed successfully"
LOG_ERROR: str = "Plugin function %s failed: %s"

# Dict Keys
KEY_FUNCTION: str = "function"
KEY_ARGS: str = "args"
KEY_RESULT: str = "result"


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_zutils(zcli: Any) -> bool:
    """
    Validate that zUtils subsystem is available.

    Parameters
    ----------
    zcli : Any
        zCLI instance to check for utils attribute

    Returns
    -------
    bool
        True if zUtils is available, False otherwise

    Notes
    -----
    Checks both attribute existence and that it's not None.
    """
    return hasattr(zcli, "utils") and zcli.utils is not None


def _format_result(result: Any) -> str:
    """
    Format function result for display.

    Parameters
    ----------
    result : Any
        Result from plugin function execution

    Returns
    -------
    str
        Formatted result string suitable for display

    Notes
    -----
    **Formatting Rules**:
        - None: "None"
        - str: Direct string
        - list/dict: Pretty-printed representation
        - Other: str() conversion

    **Examples**:
        >>> _format_result(None)
        'None'
        >>> _format_result("hello")
        'hello'
        >>> _format_result([1, 2, 3])
        '[1, 2, 3]'
    """
    if result is None:
        return "None"
    if isinstance(result, str):
        return result
    if isinstance(result, (list, dict)):
        return str(result)
    return str(result)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def execute_plugin_function(zcli: Any, args: List[str]) -> None:
    """
    Execute a plugin function via zUtils subsystem.

    This function serves as the main entry point for plugin function execution from
    the shell. It validates inputs, checks that the function exists in zUtils, executes
    it with the provided arguments, and displays the result or error.

    Parameters
    ----------
    zcli : Any
        zCLI instance providing access to:
            - utils: zUtils subsystem (plugin functions)
            - display: zDisplay for output
            - logger: Logger for debug/info logging
    args : List[str]
        Command arguments where:
            - args[0]: Function name
            - args[1:]: Function arguments

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Examples
    --------
    **Execute Function with No Arguments**:
        >>> execute_plugin_function(zcli, ["generate_id"])
        # Displays: [OK] generate_id() executed successfully
        #           Result: uuid-123-456

    **Execute Function with Arguments**:
        >>> execute_plugin_function(zcli, ["hash_password", "mypass123"])
        # Displays: [OK] hash_password() executed successfully
        #           Result: $2b$12$...

    **Function Not Found**:
        >>> execute_plugin_function(zcli, ["unknown_function"])
        # Displays: [ERROR] Function 'unknown_function' not found in loaded plugins
        #           Use 'plugin show' to see available functions

    Notes
    -----
    **Validation Steps**:
        1. Check args list has at least 1 item (function name)
        2. Check zUtils subsystem exists (zcli.utils)
        3. Check function exists in zUtils (hasattr)

    **Execution**:
        - Uses getattr() to dynamically call function
        - Passes remaining args (*args[1:])
        - Catches all exceptions and displays user-friendly errors

    **Display Output**:
        - Success: Header with function name, result with formatted value
        - Error: Error message with details and suggestions

    **Logging**:
        - Debug: Function name + args before execution
        - Info: Success message after execution
        - Error: Failure message with exception details
    """
    # Validate args (needs at least function name)
    if not args:
        zcli.display.error(ERROR_NO_ARGS)
        return

    # Extract function name and arguments
    function_name: str = args[0]
    function_args: List[str] = args[1:] if len(args) > 1 else []

    # Validate zUtils subsystem exists
    if not _validate_zutils(zcli):
        zcli.display.error(ERROR_NO_UTILS)
        zcli.logger.error("zUtils subsystem not available")
        return

    # Validate function exists in zUtils
    if not hasattr(zcli.utils, function_name):
        error_msg: str = ERROR_NO_FUNCTION.format(function=function_name)
        zcli.display.error(error_msg)
        zcli.logger.error("Function %s not found in zUtils", function_name)
        return

    # Execute plugin function
    try:
        zcli.logger.debug(LOG_EXECUTING, function_name, function_args)

        # Get function reference and execute
        plugin_function = getattr(zcli.utils, function_name)
        result: Any = plugin_function(*function_args)

        # Log success
        zcli.logger.info(LOG_SUCCESS, function_name)

        # Display success message
        success_msg: str = MSG_SUCCESS.format(function=function_name)
        zcli.display.success(success_msg)

        # Display result if not None
        if result is not None:
            formatted_result: str = _format_result(result)
            zcli.display.text(f"{MSG_RESULT} {formatted_result}")

    except Exception as e:  # pylint: disable=broad-except
        # Log error
        zcli.logger.error(LOG_ERROR, function_name, str(e))

        # Display error
        error_msg = ERROR_EXEC_FAILED.format(function=function_name, error=str(e))
        zcli.display.error(error_msg)

