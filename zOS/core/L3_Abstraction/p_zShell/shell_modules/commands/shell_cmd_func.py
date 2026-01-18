# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_func.py

"""
Shell Function Command Executor.

This module provides the shell command interface for executing external Python functions
via the zFunc subsystem. The func command enables dynamic loading and execution of Python
functions from workspace files, package modules, or zMachine directories with automatic
zcli and session injection.

OVERVIEW:
    The 'func' command provides a shell-level interface to zFunc, enabling users to execute
    external Python functions without writing custom scripts. Functions are dynamically loaded
    from resolved file paths, with automatic injection of zcli instance and session context
    when the function signature requires them.

COMMAND SYNTAX:
    func <function_path> [args...]
    
    Examples:
        func @.zCLI.version.get_version
        func @.zCLI.version.get_package_info
        func @.utils.helpers.process_data mydata
        func ~./Users/name/scripts/helper.py.custom_function arg1 arg2

PATH RESOLUTION:
    The func command supports full zPath notation for function resolution:
    
    • Workspace-relative (@.):
        func @.zCLI.version.get_version
        Resolves to: {workspace}/zCLI/version.py::get_version()
        
    • Absolute file path (~.):
        func ~./Users/name/scripts/helper.py.process
        Resolves to: /Users/name/scripts/helper.py::process()
        
    • zMachine directory (~zMachine):
        func ~zMachine.zPlugins.custom.function
        Resolves to: {user_data_dir}/zPlugins/custom.py::function()
        
    All path resolution is delegated to zParser via zFunc, ensuring consistent
    behavior across the framework.

ZFUNC INTEGRATION:
    The func command is a thin shell adapter over the zFunc subsystem. It performs
    validation and formats the function call as a zFunc expression, then delegates
    all execution to zFunc.handle().
    
    Delegation flow:
        1. Shell parses command: "func @.utils.helper arg1 arg2"
        2. func command validates parsed structure
        3. func command builds expression: "zFunc(@.utils.helper, arg1, arg2)"
        4. func command calls: zcli.zfunc.handle(expression)
        5. zFunc resolves path, loads function, parses args, executes
        6. Result returned to shell (or displayed by zFunc)
    
    The func command does NOT:
        • Resolve file paths (delegated to zParser via zFunc)
        • Parse function arguments (delegated to zFunc)
        • Load Python modules (delegated to zFunc)
        • Inject zcli/session (delegated to zFunc)
        • Display results (delegated to zFunc's zDeclare)
    
    This separation ensures the func command remains a pure UI adapter.

AUTO-INJECTION:
    zFunc automatically injects zcli and session parameters when the target function
    signature requires them. This is handled transparently by zFunc using inspect.signature().
    
    Example function signatures:
        # No injection needed
        def simple_function(arg1, arg2):
            return arg1 + arg2
        
        # zcli injected automatically
        def zcli_aware_function(zcli, arg1):
            zcli.logger.info("Processing: %s", arg1)
            return arg1
        
        # Both zcli and session injected
        def session_aware_function(zcli, session, arg1):
            workspace = session["zSpace"]
            return f"{workspace}/{arg1}"
    
    The func command does not need to know about injection - it simply passes
    arguments as-is to zFunc, which handles injection during execution.

ZSESSION AWARENESS:
    Functions executed via zFunc inherit the full session context from zcli.session.
    This means functions can access and mutate session state:
    
    Session read example:
        def get_workspace(zcli, session):
            return session["zSpace"]  # Current workspace directory
    
    Session mutation example:
        def set_custom_key(zcli, session, key, value):
            session[key] = value  # Persists after function exits
    
    Common session keys available:
        • SESSION_KEY_ZSPACE: Workspace root directory
        • SESSION_KEY_ZVAFILE: Active zVaFile name
        • SESSION_KEY_ZVAFOLDER: Folder containing zVaFile
        • SESSION_KEY_ZBLOCK: Current block name
        • SESSION_KEY_ZMODE: Terminal or zBifrost
        • SESSION_KEY_ZAUTH: Auth context (if authenticated)
    
    Session mutations persist after function execution - the func command does
    not snapshot or restore session state. This is intentional for stateful workflows.

ZAUTH AWARENESS:
    Functions can access authentication context via session["zAuth"] when present.
    The func command does not enforce RBAC - functions are responsible for their
    own permission checks if needed.
    
    Auth context structure (when authenticated):
        {
            "user_id": "admin",
            "role": "admin",
            "tier": 3,
            "authenticated": True,
            "timestamp": "2024-01-01T12:00:00"
        }
    
    Example auth-aware function:
        def admin_only_function(zcli, session):
            auth = session.get("zAuth", {})
            if auth.get("role") != "admin":
                raise PermissionError("Admin access required")
            # ... admin logic ...
    
    No auth validation at func command level - auth state flows through transparently
    to the target function. This allows functions to implement custom auth logic.

ZPARSER INTEGRATION:
    zFunc uses zcli.zparser for all path resolution and argument parsing:
    
    • parse_function_path(zHorizontal, zContext):
        Resolves function path from zPath notation to absolute file path
        Extracts function name from path
        Handles @., ~., and ~zMachine prefixes
    
    • parse_json_expr(arg):
        Parses argument strings to Python types
        Supports: strings, numbers, booleans, None, lists, dicts
        Provides safe evaluation without exec/eval
    
    The func command never directly calls zParser - all parsing is delegated
    to zFunc, which uses zParser internally.

ARCHITECTURE:
    Multi-layer delegation pattern:
    
    Layer 1 - Shell Command (this file):
        • Validate parsed command structure
        • Validate function name format
        • Build zFunc expression string
        • Delegate to zFunc subsystem
        • Handle subsystem errors
    
    Layer 2 - zFunc Subsystem:
        • Parse function path (via zParser)
        • Parse function arguments (via zParser)
        • Resolve callable (dynamic import)
        • Inject zcli/session (via inspect)
        • Execute function
        • Display result (via zDisplay)
    
    Layer 3 - zParser Subsystem:
        • Resolve zPath notation to file paths
        • Parse argument strings to Python types
        • Validate path security
    
    Layer 4 - Target Function:
        • User-defined logic
        • Optional zcli/session parameters
        • Return result to zFunc

UI ADAPTER PATTERN:
    This command follows the shell UI adapter pattern:
    • Returns function result on success (passed through from zFunc)
    • Returns error dict on validation failure (for shell_executor to display)
    • Does not use zDisplay directly (zFunc handles display via zDeclare)
    • Validation errors return immediately (no execution)
    • Execution errors caught and returned as error dicts

TYPE SAFETY:
    All functions include comprehensive type hints using types imported from
    the zCLI namespace for consistency across the framework. Helper functions
    return Optional[Dict[str, str]] for error cases, None for success.

ERROR HANDLING:
    Two-tier error handling approach:
    
    1. Pre-execution Validation (returns error dict):
        • Missing zFunc subsystem (AttributeError)
        • Invalid parsed command structure (KeyError)
        • Invalid function name format (ValueError)
        
    2. Execution Errors (caught and returned as dict):
        • Function not found (AttributeError from zFunc)
        • Module import errors (ImportError from zFunc)
        • Function execution errors (Exception from zFunc)
    
    All errors are logged with full context (function name, args, traceback)
    and returned as error dicts for shell_executor to display to the user.

CROSS-SUBSYSTEM DEPENDENCIES:
    • zFunc: Function loading/execution (primary dependency - dynamic import)
    • zParser: Path resolution and arg parsing (via zFunc)
    • zSession: Context inheritance (auth, workspace, config)
    • zConfig: Session constants (SESSION_KEY_*, imported for docs)
    • zDisplay: Result display (via zFunc's zDeclare, not direct)
    • zAuth: Authentication context (via session, no direct dependency)

RELATED COMMANDS:
    • load: Loads data files via zLoader (data, not code)
    • walker: Declarative stepped execution via zWalker (UI blocks)
    • wizard: Programmatic loop engine via zWizard (buffer-based)
    • comm: Execute zComm messages (communication, not functions)

FUTURE ENHANCEMENTS:
    • --dry-run flag: Validate function path without execution
    • --timeout flag: Set execution timeout (prevent infinite loops)
    • --inject flag: Force zcli/session injection even if not in signature
    • func list: Show available functions in workspace/package
    • zDisplay integration: User-friendly error messages (currently via logger)

Author: zOS Framework
Version: 1.5.4+
Module: zShell (Command Executors - Group C: zCLI Subsystem Integration)
"""

from zOS import Any, Dict, Optional, List


# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Error Messages
ERROR_NO_ZFUNC: str = "zFunc subsystem not available - cannot execute functions"
ERROR_INVALID_FUNCTION: str = "Invalid function name or path: {func_name}"
ERROR_EXECUTION_FAILED: str = "Function execution failed: {error}"
ERROR_MISSING_ACTION: str = "No function specified in parsed command"
ERROR_INVALID_ARGS: str = "Invalid arguments: {error}"
ERROR_INVALID_PARSED: str = "Invalid parsed command structure: {error}"
ERROR_FUNCTION_TOO_LONG: str = "Function name exceeds maximum length ({max_len}): {func_name}"
ERROR_TOO_MANY_ARGS: str = "Too many arguments ({count}), maximum allowed: {max_count}"
ERROR_EMPTY_FUNCTION_NAME: str = "Function name cannot be empty or whitespace-only"

# Dict Keys (for refactor-proof access)
KEY_ACTION: str = "action"
KEY_ARGS: str = "args"
KEY_OPTIONS: str = "options"

# Format Templates
TEMPLATE_FUNC_EXPR: str = "zFunc({func_name}{args_str})"
TEMPLATE_ARG_SEP: str = ", "

# Validation Limits
MAX_FUNCTION_NAME_LENGTH: int = 255
MAX_ARGS_COUNT: int = 50

# Error Return Keys
KEY_ERROR: str = "error"
KEY_DETAILS: str = "details"


# ============================================================================
# HELPER FUNCTIONS - Validation
# ============================================================================

def _validate_zfunc_subsystem(zcli: Any) -> Optional[Dict[str, str]]:
    """
    Validate that zFunc subsystem is available in zcli instance.
    
    Defensive check to ensure zcli.zfunc exists and is accessible before
    attempting to call it. This prevents AttributeError crashes if zFunc
    was not initialized properly.
    
    Args:
        zcli: zCLI instance to validate
        
    Returns:
        Optional[Dict[str, str]]: Error dict if validation fails, None if valid
            Error dict contains: {"error": "message", "details": "context"}
            
    Example:
        >>> error = _validate_zfunc_subsystem(zcli)
        >>> if error:
        ...     return error  # Abort execution
    """
    if not hasattr(zcli, 'zfunc'):
        zcli.logger.error(ERROR_NO_ZFUNC)
        return {
            KEY_ERROR: ERROR_NO_ZFUNC,
            KEY_DETAILS: "zFunc subsystem not found in zcli instance"
        }
    
    if not hasattr(zcli.zfunc, 'handle'):
        zcli.logger.error("zFunc subsystem exists but missing handle() method")
        return {
            KEY_ERROR: ERROR_NO_ZFUNC,
            KEY_DETAILS: "zFunc.handle() method not found"
        }
    
    zcli.logger.debug("zFunc subsystem validation: OK")
    return None


def _validate_parsed_command(zcli: Any, parsed: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Validate parsed command dictionary structure.
    
    Ensures all required keys exist and have valid types before attempting
    to extract function name and arguments.
    
    Args:
        zcli: zCLI instance for logging
        parsed: Parsed command dict to validate
        
    Returns:
        Optional[Dict[str, str]]: Error dict if validation fails, None if valid
        
    Validation checks:
        • 'action' key exists (function name/path)
        • 'args' key exists (argument list)
        • 'args' is a list type
        • 'action' is not empty
    """
    try:
        # Check required keys exist
        if KEY_ACTION not in parsed:
            zcli.logger.error(ERROR_MISSING_ACTION)
            return {
                KEY_ERROR: ERROR_MISSING_ACTION,
                KEY_DETAILS: f"Parsed command missing '{KEY_ACTION}' key"
            }
        
        if KEY_ARGS not in parsed:
            zcli.logger.error("Parsed command missing 'args' key")
            return {
                KEY_ERROR: ERROR_INVALID_PARSED.format(error="missing 'args' key"),
                KEY_DETAILS: "Command parser did not provide 'args' list"
            }
        
        # Validate types
        if not isinstance(parsed[KEY_ARGS], list):
            zcli.logger.error("'args' is not a list: %s", type(parsed[KEY_ARGS]))
            return {
                KEY_ERROR: ERROR_INVALID_PARSED.format(error="'args' must be a list"),
                KEY_DETAILS: f"Expected list, got {type(parsed[KEY_ARGS])}"
            }
        
        # Validate action is not empty
        func_name = parsed[KEY_ACTION]
        if not func_name or (isinstance(func_name, str) and not func_name.strip()):
            zcli.logger.error(ERROR_EMPTY_FUNCTION_NAME)
            return {
                KEY_ERROR: ERROR_EMPTY_FUNCTION_NAME,
                KEY_DETAILS: "Function name cannot be empty string or whitespace"
            }
        
        zcli.logger.debug("Parsed command validation: OK")
        return None
        
    except Exception as e:
        zcli.logger.error("Parsed command validation failed: %s", e, exc_info=True)
        return {
            KEY_ERROR: ERROR_INVALID_PARSED.format(error=str(e)),
            KEY_DETAILS: f"Unexpected validation error: {e}"
        }


def _validate_function_name(zcli: Any, func_name: str) -> Optional[str]:
    """
    Validate function name/path format and length.
    
    Performs basic validation on function name to catch obvious errors before
    delegating to zFunc. Does not validate path syntax (delegated to zParser).
    
    Args:
        zcli: zCLI instance for logging
        func_name: Function name or zPath to validate
        
    Returns:
        Optional[str]: Error message if invalid, None if valid
        
    Validation rules:
        • Not empty or whitespace-only
        • Length <= MAX_FUNCTION_NAME_LENGTH (255 chars)
        • Contains at least one non-whitespace character
        
    Note:
        Path syntax validation (@., ~., etc) is delegated to zParser.
        This function only checks basic format issues.
    """
    # Check empty/whitespace
    if not func_name or not func_name.strip():
        zcli.logger.warning(ERROR_EMPTY_FUNCTION_NAME)
        return ERROR_EMPTY_FUNCTION_NAME
    
    # Check length
    if len(func_name) > MAX_FUNCTION_NAME_LENGTH:
        error = ERROR_FUNCTION_TOO_LONG.format(
            max_len=MAX_FUNCTION_NAME_LENGTH,
            func_name=func_name[:50] + "..."
        )
        zcli.logger.warning(error)
        return error
    
    zcli.logger.debug("Function name validation: OK (%d chars)", len(func_name))
    return None


def _validate_args_count(zcli: Any, args: List[str]) -> Optional[str]:
    """
    Validate argument count does not exceed maximum.
    
    Prevents potential issues with extremely long argument lists that could
    cause performance problems or buffer overflows.
    
    Args:
        zcli: zCLI instance for logging
        args: Argument list to validate
        
    Returns:
        Optional[str]: Error message if too many args, None if valid
    """
    if len(args) > MAX_ARGS_COUNT:
        error = ERROR_TOO_MANY_ARGS.format(count=len(args), max_count=MAX_ARGS_COUNT)
        zcli.logger.warning(error)
        return error
    
    zcli.logger.debug("Argument count validation: OK (%d args)", len(args))
    return None


# ============================================================================
# HELPER FUNCTIONS - Formatting
# ============================================================================

def _format_args(zcli: Any, args: List[str]) -> str:
    """
    Format argument list for zFunc expression.
    
    Converts list of argument strings into comma-separated format suitable
    for inclusion in zFunc expression. Handles edge cases like empty lists,
    None values, and whitespace.
    
    Args:
        zcli: zCLI instance for logging
        args: List of argument strings from parsed command
        
    Returns:
        str: Formatted argument string (with leading comma if non-empty)
            Empty list -> ""
            ["arg1"] -> ", arg1"
            ["arg1", "arg2"] -> ", arg1, arg2"
            
    Example:
        >>> _format_args(zcli, ["data", "123"])
        ", data, 123"
        >>> _format_args(zcli, [])
        ""
    """
    if not args:
        zcli.logger.debug("No arguments to format")
        return ""
    
    # Filter out None and empty strings
    valid_args = [str(arg).strip() for arg in args if arg is not None and str(arg).strip()]
    
    if not valid_args:
        zcli.logger.debug("All arguments were None/empty, returning empty string")
        return ""
    
    args_str = TEMPLATE_ARG_SEP + TEMPLATE_ARG_SEP.join(valid_args)
    zcli.logger.debug("Formatted %d args: %s", len(valid_args), args_str)
    return args_str


def _build_func_expression(zcli: Any, func_name: str, args: List[str]) -> str:
    """
    Build complete zFunc expression from function name and arguments.
    
    Constructs the final zFunc expression string that will be passed to
    zcli.zfunc.handle(). Uses template for consistent formatting.
    
    Args:
        zcli: zCLI instance for logging
        func_name: Function name or zPath
        args: List of argument strings
        
    Returns:
        str: Complete zFunc expression
            Example: "zFunc(@.utils.helper, arg1, arg2)"
            
    Example:
        >>> _build_func_expression(zcli, "@.utils.helper", ["data"])
        "zFunc(@.utils.helper, data)"
    """
    args_str = _format_args(zcli, args)
    func_expr = TEMPLATE_FUNC_EXPR.format(func_name=func_name, args_str=args_str)
    zcli.logger.debug("Built zFunc expression: %s", func_expr)
    return func_expr


# ============================================================================
# HELPER FUNCTIONS - Error Handling
# ============================================================================

def _handle_execution_error(
    zcli: Any,
    error: Exception,
    func_name: str,
    func_expr: str
) -> Dict[str, str]:
    """
    Handle function execution errors with comprehensive logging.
    
    Centralizes error handling for zFunc execution failures. Logs full context
    including function name, expression, and traceback, then returns formatted
    error dict for shell_executor to display.
    
    Args:
        zcli: zCLI instance for logging
        error: Exception raised during execution
        func_name: Original function name/path
        func_expr: Complete zFunc expression that failed
        
    Returns:
        Dict[str, str]: Error dict with error message and details
            {"error": "message", "details": "context"}
            
    Error types handled:
        • AttributeError: Function not found in module
        • ImportError: Module import failed
        • FileNotFoundError: Python file not found
        • Exception: Any other execution error
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Log with full context
    zcli.logger.error(
        "Function execution failed: %s",
        func_name,
        exc_info=True
    )
    zcli.logger.error("Expression: %s", func_expr)
    zcli.logger.error("Error type: %s", error_type)
    zcli.logger.error("Error message: %s", error_msg)
    
    # Format user-friendly error message based on error type
    if isinstance(error, AttributeError):
        details = f"Function '{func_name}' not found in module"
    elif isinstance(error, ImportError):
        details = f"Failed to import module for '{func_name}'"
    elif isinstance(error, FileNotFoundError):
        details = f"Python file not found for '{func_name}'"
    else:
        details = f"{error_type}: {error_msg}"
    
    return {
        KEY_ERROR: ERROR_EXECUTION_FAILED.format(error=error_msg),
        KEY_DETAILS: details
    }


# ============================================================================
# PUBLIC API
# ============================================================================

def execute_func(zcli: Any, parsed: Dict[str, Any]) -> Any:
    """
    Execute external Python function via zFunc subsystem.
    
    Main entry point for the func shell command. Validates the parsed command,
    builds a zFunc expression, and delegates execution to zcli.zfunc.handle().
    
    This function is a UI adapter - it performs validation and formatting, then
    delegates all actual work (path resolution, loading, execution) to zFunc.
    
    Args:
        zcli: zCLI instance with zfunc subsystem, logger, and session
        parsed: Parsed command dict from shell parser with keys:
            - action: Function name or zPath (str)
            - args: List of argument strings (List[str])
            - options: Dict of command options (Dict[str, Any])
            
    Returns:
        Any: Function execution result (passed through from zFunc), or
            Dict[str, str]: Error dict if validation/execution fails
            
    Return types:
        • Success: Function return value (any type, depends on function)
        • Validation Error: {"error": "message", "details": "context"}
        • Execution Error: {"error": "message", "details": "context"}
        
    Execution flow:
        1. Validate zFunc subsystem exists
        2. Validate parsed command structure
        3. Extract function name and arguments
        4. Validate function name format
        5. Validate argument count
        6. Build zFunc expression
        7. Delegate to zcli.zfunc.handle()
        8. Return result or error dict
        
    Examples:
        Basic function call:
            >>> parsed = {
            ...     "action": "@.zCLI.version.get_version",
            ...     "args": [],
            ...     "options": {}
            ... }
            >>> result = execute_func(zcli, parsed)
            >>> # Returns: "1.5.4"
            
        Function with arguments:
            >>> parsed = {
            ...     "action": "@.utils.helpers.process",
            ...     "args": ["data", "123"],
            ...     "options": {}
            ... }
            >>> result = execute_func(zcli, parsed)
            >>> # Calls: process(zcli, session, "data", "123")
            
        Validation error:
            >>> parsed = {"action": "", "args": []}
            >>> result = execute_func(zcli, parsed)
            >>> # Returns: {"error": "Function name cannot be empty...", ...}
            
        Execution error:
            >>> parsed = {"action": "nonexistent_function", "args": []}
            >>> result = execute_func(zcli, parsed)
            >>> # Returns: {"error": "Function execution failed...", ...}
    
    Notes:
        • All path resolution delegated to zParser (via zFunc)
        • All argument parsing delegated to zFunc
        • All function loading delegated to zFunc
        • All zcli/session injection delegated to zFunc
        • All result display delegated to zFunc (via zDeclare)
        • This function only validates and formats
        
    Error Handling:
        Pre-execution validation errors return immediately without calling zFunc.
        Execution errors from zFunc are caught and returned as error dicts.
        All errors logged with full context for debugging.
    """
    # Step 1: Validate zFunc subsystem exists
    error = _validate_zfunc_subsystem(zcli)
    if error:
        return error
    
    # Step 2: Validate parsed command structure
    error = _validate_parsed_command(zcli, parsed)
    if error:
        return error
    
    # Step 3: Extract function name and arguments
    func_name = parsed[KEY_ACTION]
    args = parsed[KEY_ARGS]
    
    zcli.logger.debug("Executing function: %s", func_name)
    zcli.logger.debug("Arguments: %s", args)
    
    # Step 4: Validate function name format
    error_msg = _validate_function_name(zcli, func_name)
    if error_msg:
        return {
            KEY_ERROR: error_msg,
            KEY_DETAILS: f"Function name: {func_name}"
        }
    
    # Step 5: Validate argument count
    error_msg = _validate_args_count(zcli, args)
    if error_msg:
        return {
            KEY_ERROR: error_msg,
            KEY_DETAILS: f"Provided {len(args)} arguments"
        }
    
    # Step 6: Build zFunc expression
    func_expr = _build_func_expression(zcli, func_name, args)
    zcli.logger.info("Executing: %s", func_expr)
    
    # Step 7: Delegate to zFunc for execution
    try:
        result = zcli.zfunc.handle(func_expr)
        zcli.logger.debug("Function execution completed successfully")
        return result
        
    except AttributeError as e:
        # Function not found in module
        zcli.logger.error("AttributeError during function execution", exc_info=True)
        return _handle_execution_error(zcli, e, func_name, func_expr)
        
    except ImportError as e:
        # Module import failed
        zcli.logger.error("ImportError during function execution", exc_info=True)
        return _handle_execution_error(zcli, e, func_name, func_expr)
        
    except FileNotFoundError as e:
        # Python file not found
        zcli.logger.error("FileNotFoundError during function execution", exc_info=True)
        return _handle_execution_error(zcli, e, func_name, func_expr)
        
    except Exception as e:
        # Any other execution error
        zcli.logger.error("Unexpected error during function execution", exc_info=True)
        return _handle_execution_error(zcli, e, func_name, func_expr)
