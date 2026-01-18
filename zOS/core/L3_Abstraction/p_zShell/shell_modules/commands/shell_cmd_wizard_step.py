# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_wizard_step.py

"""
Shell-specific wizard step execution for zWizard workflows.

This module contains shell-specific command parsing and execution logic
used by zWizard when running in Shell mode. It handles:
  - zData operations with alias resolution
  - zFunc expressions
  - zDisplay events
  - Shell command parsing and routing

ARCHITECTURE NOTE:
  This file was moved from zWizard/zWizard_modules/ to zShell/zShell_modules/
  to properly separate generic loop logic (zWizard) from shell-specific
  execution logic (zShell). This prevents circular dependencies and clarifies
  the role of each subsystem.
  
  The separation is essential:
    - zWizard: Generic workflow loop, transaction management, WizardHat results
    - zShell: Shell-specific parsing, alias resolution, command routing
    - Callback Pattern: zWizard calls execute_wizard_step() for Shell mode

Module Constants:
    Step Keys:
        STEP_KEY_ZDATA: Key for zData operations in workflow steps
        STEP_KEY_ZFUNC: Key for zFunc operations in workflow steps
        STEP_KEY_ZDISPLAY: Key for zDisplay operations in workflow steps
    
    Config Keys:
        CONFIG_KEY_MODEL: Model/schema alias key in zData config
        CONFIG_KEY_ACTION: Action/operation key in zData config
        CONFIG_KEY_TABLES: Tables list key in zData config
        CONFIG_KEY_OPTIONS: Options dictionary key in zData config
        CONFIG_KEY_EVENT: Event type key in zDisplay config
        CONFIG_KEY_CONTENT: Content/message key in display events
        CONFIG_KEY_MESSAGE: Message key for display events
        CONFIG_KEY_DATA: Data key for JSON display events
    
    Display Events:
        EVENT_TEXT, EVENT_LINE: Text/line display events
        EVENT_HEADER: Header display event
        EVENT_BREAK: Line break event
        EVENT_ERROR, EVENT_WARNING, EVENT_SUCCESS, EVENT_INFO: Status events
        EVENT_JSON: JSON output event
    
    Command Types:
        CMD_TYPE_DATA: zData command type
        CMD_TYPE_FUNC: zFunc command type
        CMD_TYPE_LOAD: Load command type
    
    Alias/Cache Keys:
        OPTION_ALIAS_NAME: Alias name option key
        OPTION_SCHEMA_CACHED: Cached schema option key
        CACHE_KEY_SCHEMA: Schema cache key in context
    
    Defaults:
        DEFAULT_ACTION: Default zData action (read)
        ZFUNC_PREFIX: Prefix for zFunc string expressions
    
    Error Messages:
        ERROR_MSG_ZDATA_DICT: Error when zData value is not a dict
        ERROR_MSG_ZDISPLAY_DICT: Error when zDisplay value is not a dict
        ERROR_MSG_PARSE_FAILED: Error when shell command parsing fails
        ERROR_MSG_DATA_REQUEST: Error when data request fails
        ERROR_MSG_FUNC_HANDLE: Error when func handling fails
        ERROR_MSG_PARSE_COMMAND: Error when command parsing fails
        ERROR_MSG_IMPORT_FAILED: Error when dynamic import fails
        WARNING_MSG_UNKNOWN_EVENT: Warning for unknown display events
        WARNING_MSG_UNSUPPORTED_CMD: Warning for unsupported command types
        WARNING_MSG_ALIAS_NOT_FOUND: Warning when alias not found in cache
"""

from zOS import Dict, Any, Optional, Union

# ============================================================================
# STEP KEYS
# ============================================================================
STEP_KEY_ZDATA = "zData"
STEP_KEY_ZFUNC = "zFunc"
STEP_KEY_ZDISPLAY = "zDisplay"

# ============================================================================
# CONFIG KEYS
# ============================================================================
CONFIG_KEY_MODEL = "model"
CONFIG_KEY_ACTION = "action"
CONFIG_KEY_TABLES = "tables"
CONFIG_KEY_OPTIONS = "options"
CONFIG_KEY_EVENT = "event"
CONFIG_KEY_CONTENT = "content"
CONFIG_KEY_MESSAGE = "message"
CONFIG_KEY_DATA = "data"

# ============================================================================
# DISPLAY EVENTS
# ============================================================================
EVENT_TEXT = "text"
EVENT_LINE = "line"
EVENT_HEADER = "header"
EVENT_BREAK = "break"
EVENT_ERROR = "error"
EVENT_WARNING = "warning"
EVENT_SUCCESS = "success"
EVENT_INFO = "info"
EVENT_JSON = "json"

# ============================================================================
# COMMAND TYPES
# ============================================================================
CMD_TYPE_DATA = "data"
CMD_TYPE_FUNC = "func"
CMD_TYPE_LOAD = "load"

# ============================================================================
# ALIAS/CACHE KEYS
# ============================================================================
OPTION_ALIAS_NAME = "_alias_name"
OPTION_SCHEMA_CACHED = "_schema_cached"
CACHE_KEY_SCHEMA = "schema_cache"

# ============================================================================
# DEFAULTS
# ============================================================================
DEFAULT_ACTION = "read"
ZFUNC_PREFIX = "zFunc("

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_MSG_ZDATA_DICT = "zData value must be a dict"
ERROR_MSG_ZDISPLAY_DICT = "zDisplay value must be a dict"
ERROR_MSG_PARSE_FAILED = "Failed to parse shell command"
ERROR_MSG_DATA_REQUEST = "Error executing zData request"
ERROR_MSG_FUNC_HANDLE = "Error executing zFunc"
ERROR_MSG_PARSE_COMMAND = "Error parsing shell command"
ERROR_MSG_IMPORT_FAILED = "Error importing command executor"
WARNING_MSG_UNKNOWN_EVENT = "Unknown zDisplay event in wizard"
WARNING_MSG_UNSUPPORTED_CMD = "Unsupported command type in wizard"
WARNING_MSG_ALIAS_NOT_FOUND = "Alias not found in pinned_cache or schema_cache"

def execute_wizard_step(
    zcli: Any,
    step_key: str,
    step_value: Union[Dict[str, Any], str],
    logger: Any,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Execute a wizard step in shell mode with shell-specific command handling.
    
    This function serves as a callback for zWizard when running in Shell mode.
    It handles the shell-specific parsing and execution of wizard steps,
    including sophisticated alias resolution for transactional workflows and
    schema cache connection reuse for optimal performance.
    
    Args:
        zcli: The zCLI instance providing access to all subsystems
        step_key: The step identifier/name from the workflow
        step_value: The step configuration, either:
            - Dict: Structured step with keys like zData, zFunc, zDisplay
            - str: Shell command string or zFunc expression
        logger: Logger instance for debug/info/warning/error messages
        context: Optional context dictionary containing:
            - schema_cache: SchemaCache instance for connection reuse
            - Other workflow-specific metadata
    
    Returns:
        Any: The result of step execution (varies by step type):
            - zData: Query results, operation status, or None
            - zFunc: Function return value
            - zDisplay: None (UI adapter pattern)
            - Shell command: Command execution result
            - None: On errors or empty steps
    
    Step Types Handled:
        1. **zData Operations** (Dict with "zData" key):
           - Handles CRUD operations (create, read, update, delete, upsert)
           - Resolves $alias_name to cached schemas or connections
           - Reuses existing connections from schema_cache for transactions
           - Falls back to pinned_cache if connection not in schema_cache
           - Normalizes tables field (string → list)
           - Sets default action to "read" if not specified
        
        2. **zFunc Operations** (Dict with "zFunc" key or str starting with "zFunc("):
           - Delegates to zcli.funcs.handle() for function resolution
           - Supports both dict format and string expression format
        
        3. **zDisplay Operations** (Dict with "zDisplay" key):
           - Routes to appropriate zDisplay methods based on event type
           - Supported events: text, line, header, break, error, warning,
             success, info, json
           - Extracts content/message/data based on event type
        
        4. **Shell Commands** (str without "zFunc(" prefix):
           - Parses command using zcli.zparser.parse_command()
           - Routes to appropriate command executor (data, func, load)
           - Supports inline imports to avoid circular dependencies
        
        5. **Generic Dict** (Dict without recognized keys):
           - Treated as zData request
           - Passed to zcli.data.handle_request()
    
    Alias Resolution Process:
        1. Check if model starts with $ (e.g., "$my_db")
        2. Extract alias_name by removing $ prefix
        3. Check context.schema_cache.has_connection(alias_name):
           - If YES: Reuse existing connection (for transactions)
           - Set options._alias_name and clear model field
        4. If not in schema_cache, check pinned_cache.get_alias(alias_name):
           - If found: Use cached schema
           - Set options._schema_cached and _alias_name
        5. If not found anywhere: Log warning and let zData handle error
    
    Context Structure:
        {
            "schema_cache": SchemaCache,  # For connection reuse
            # Additional workflow metadata...
        }
    
    Examples:
        >>> # Example 1: zData operation with alias
        >>> step_value = {
        ...     "zData": {
        ...         "model": "$my_db",
        ...         "action": "read",
        ...         "tables": ["users"],
        ...         "where": {"active": True}
        ...     }
        ... }
        >>> result = execute_wizard_step(zcli, "get_users", step_value, logger, context)
        
        >>> # Example 2: zFunc expression
        >>> step_value = "zFunc(hash_password, 'mypass')"
        >>> result = execute_wizard_step(zcli, "hash_pw", step_value, logger)
        
        >>> # Example 3: zDisplay event
        >>> step_value = {
        ...     "zDisplay": {
        ...         "event": "success",
        ...         "message": "Operation complete!"
        ...     }
        ... }
        >>> execute_wizard_step(zcli, "notify", step_value, logger)
        
        >>> # Example 4: Shell command
        >>> step_value = "data read users where active=true"
        >>> result = execute_wizard_step(zcli, "query", step_value, logger)
    
    Raises:
        Exception: Propagates exceptions from subsystem calls (wrapped in try/except)
    
    Notes:
        - This function uses lazy imports (inline) to prevent circular dependencies
        - Architecture: Moved from zWizard to zShell to separate concerns
        - Connection reuse enables atomic multi-step transactions
        - All errors are logged before returning None
        - UI adapter pattern: Display operations return None
    """
    logger.debug("Executing wizard step in shell mode: %s", step_key)
    
    # Handle different step value types
    if isinstance(step_value, dict):
        # Dictionary step - check for known keys
        if STEP_KEY_ZDATA in step_value:
            # zData operation
            zdata_config = step_value[STEP_KEY_ZDATA]
            # Ensure it's a dict
            if isinstance(zdata_config, dict):
                zdata_config.setdefault(CONFIG_KEY_ACTION, DEFAULT_ACTION)
                
                # Normalize tables field (string => list)
                if CONFIG_KEY_TABLES in zdata_config:
                    tables = zdata_config[CONFIG_KEY_TABLES]
                    if isinstance(tables, str):
                        # Convert string to list
                        zdata_config[CONFIG_KEY_TABLES] = [tables]
                
                # Resolve alias if model starts with $
                model = zdata_config.get(CONFIG_KEY_MODEL)
                if model and isinstance(model, str) and model.startswith("$"):
                    alias_name = model[1:]
                    
                    # Check if connection already exists in schema_cache (reuse)
                    if context and context.get(CACHE_KEY_SCHEMA):
                        schema_cache = context[CACHE_KEY_SCHEMA]
                        if schema_cache.has_connection(alias_name):
                            logger.debug("Reusing existing connection for $%s", alias_name)
                            # Connection exists, zData will reuse it automatically
                            if CONFIG_KEY_OPTIONS not in zdata_config:
                                zdata_config[CONFIG_KEY_OPTIONS] = {}
                            zdata_config[CONFIG_KEY_OPTIONS][OPTION_ALIAS_NAME] = alias_name
                            zdata_config[CONFIG_KEY_MODEL] = None  # Clear model, use existing connection
                            try:
                                return zcli.data.handle_request(zdata_config, context=context)
                            except Exception as e:  # pylint: disable=broad-except
                                logger.error("%s: %s", ERROR_MSG_DATA_REQUEST, e)
                                return None
                    
                    # Check pinned_cache for schema data
                    cached_schema = zcli.loader.cache.pinned_cache.get_alias(alias_name)
                    if cached_schema:
                        # Add alias info to options
                        if CONFIG_KEY_OPTIONS not in zdata_config:
                            zdata_config[CONFIG_KEY_OPTIONS] = {}
                        zdata_config[CONFIG_KEY_OPTIONS][OPTION_SCHEMA_CACHED] = cached_schema
                        zdata_config[CONFIG_KEY_OPTIONS][OPTION_ALIAS_NAME] = alias_name
                        zdata_config[CONFIG_KEY_MODEL] = None  # Clear model, use cached schema
                        logger.debug("Resolved alias $%s from pinned_cache", alias_name)
                    else:
                        logger.warning("%s: $%s", WARNING_MSG_ALIAS_NOT_FOUND, alias_name)
                        # Let it fall through - zData will handle the error
                
                try:
                    return zcli.data.handle_request(zdata_config, context=context)
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("%s: %s", ERROR_MSG_DATA_REQUEST, e)
                    return None
            
            logger.error(ERROR_MSG_ZDATA_DICT)
            return None
        
        if STEP_KEY_ZFUNC in step_value:
            # zFunc operation
            func_expr = step_value[STEP_KEY_ZFUNC]
            try:
                return zcli.zfunc.handle(func_expr, zContext=context)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("%s: %s", ERROR_MSG_FUNC_HANDLE, e)
                return None
        
        if STEP_KEY_ZDISPLAY in step_value:
            # zDisplay operation - route through new architecture
            display_obj = step_value[STEP_KEY_ZDISPLAY]
            if isinstance(display_obj, dict):
                # Extract event type and parameters
                event = display_obj.get(CONFIG_KEY_EVENT)
                
                # Route to appropriate zDisplay method based on event type
                if event in [EVENT_TEXT, EVENT_LINE]:
                    content = display_obj.get(CONFIG_KEY_CONTENT, "")
                    return zcli.display.text(content)
                if event == EVENT_HEADER:
                    content = display_obj.get(CONFIG_KEY_CONTENT, "")
                    return zcli.display.header(content)
                if event == EVENT_BREAK:
                    return zcli.display.break_line()
                if event in [EVENT_ERROR, EVENT_WARNING, EVENT_SUCCESS, EVENT_INFO]:
                    message = display_obj.get(CONFIG_KEY_MESSAGE, "")
                    return getattr(zcli.display, event)(message)
                if event == EVENT_JSON:
                    data = display_obj.get(CONFIG_KEY_DATA, {})
                    return zcli.display.json(data)
                
                # For any other events, log a warning
                logger.warning("%s: %s", WARNING_MSG_UNKNOWN_EVENT, event)
                return None
            
            logger.error(ERROR_MSG_ZDISPLAY_DICT)
            return None
        
        # Generic dict - try as zData request
        try:
            return zcli.data.handle_request(step_value, context=context)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("%s: %s", ERROR_MSG_DATA_REQUEST, e)
            return None
    
    if isinstance(step_value, str):
        # String step - could be zFunc expression or shell command
        if step_value.startswith(ZFUNC_PREFIX):
            try:
                return zcli.funcs.handle(step_value)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("%s: %s", ERROR_MSG_FUNC_HANDLE, e)
                return None
        
        # Treat as shell command - parse and execute
        logger.debug("Executing shell command: %s", step_value)
        try:
            parsed = zcli.zparser.parse_command(step_value)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("%s: %s", ERROR_MSG_PARSE_COMMAND, e)
            return None
        
        if "error" in parsed:
            logger.error("%s: %s", ERROR_MSG_PARSE_FAILED, parsed["error"])
            return None
        
        # Execute the parsed command
        command_type = parsed.get("type")
        
        if command_type == CMD_TYPE_DATA:
            try:
                # Lazy import to avoid circular dependencies
                from . import execute_data  # pylint: disable=import-outside-toplevel
                return execute_data(zcli, parsed)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("%s (data): %s", ERROR_MSG_IMPORT_FAILED, e)
                return None
        
        if command_type == CMD_TYPE_FUNC:
            try:
                # Lazy import to avoid circular dependencies
                from . import execute_func  # pylint: disable=import-outside-toplevel
                return execute_func(zcli, parsed)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("%s (func): %s", ERROR_MSG_IMPORT_FAILED, e)
                return None
        
        if command_type == CMD_TYPE_LOAD:
            try:
                # Lazy import to avoid circular dependencies
                from . import execute_load  # pylint: disable=import-outside-toplevel
                return execute_load(zcli, parsed)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("%s (load): %s", ERROR_MSG_IMPORT_FAILED, e)
                return None
        
        logger.warning("%s: %s", WARNING_MSG_UNSUPPORTED_CMD, command_type)
        return None
    
    return None

