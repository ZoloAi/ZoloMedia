# zCLI/subsystems/zParser/parser_modules/parser_commands.py

"""
Command parsing functionality for shell commands within zParser subsystem.

This module provides comprehensive shell command parsing for the zCLI system,
supporting 20 different command types with structured argument and option extraction.

**⚠️ CRITICAL: This module is used externally by zShell for ALL shell command parsing.**

Key Functions
-------------
1. **parse_command**: Main command parser that routes commands to specialized parsers.
   CRITICAL function used externally by zShell (zShell_executor, wizard_step_executor).

2. **_split_command**: Helper that splits command strings while preserving quoted arguments.

3. **17 specialized parsers**: _parse_* functions for each command type (data, func, utils,
   session, walker, open, test, auth, export, config, load, comm, wizard, plugin,
   ls, cd, pwd, shortcut, where).

Architecture
------------
This module uses a **command router pattern**:
- parse_command() receives raw command string
- Routes to appropriate _parse_*() function based on command type
- Returns structured dict with {type, action, args, options} OR {error}

Command Router:
    parse_command() → command_type → _parse_*_command() → structured dict

Supported Command Types (18 Total):
    1. data     - Data operations (read, create, update, delete, etc.)
    2. func     - Function invocation
    3. utils    - Utility functions
    4. session  - Session management
    5. walker   - Walker operations
    6. open     - Open files/URLs
    7. test     - Test execution
    8. auth     - Authentication (login, logout, status)
    9. export   - Export configuration
    10. config  - Configuration management
    11. load    - Load files
    12. comm    - Communication services
    13. wizard  - Wizard operations
    14. plugin  - Plugin management
    15. ls      - List directory (list/dir aliases)
    16. cd      - Change directory
    17. cwd     - Current working directory (pwd alias)
    18. shortcut - Command shortcuts
    19. where   - Contextual prompt display
    20. help    - Shell command help

Return Structure
----------------
All parsers return Dict[str, Any] with one of two formats:

Success Format:
    {
        "type": str,              # Command type (e.g., "data", "func")
        "action": str,            # Action to perform (e.g., "read", "generate_id")
        "args": List[str],        # Positional arguments
        "options": Dict[str, Any] # Named options/flags
    }

Error Format:
    {
        "error": str              # Error message describing what went wrong
    }

External Usage (CRITICAL)
--------------------------
**parse_command** is used by:
    - zCLI/subsystems/zShell/zShell_modules/zShell_executor.py
      Purpose: Parse all shell commands entered by user
      Usage: parsed = self.zcli.zparser.parse_command(command)
      
    - zCLI/subsystems/zShell/zShell_modules/executor_commands/wizard_step_executor.py
      Purpose: Parse shell commands within wizard steps
      Usage: parsed = zcli.zparser.parse_command(step_value)

Signature must remain stable: parse_command(command, logger)

Quote Handling
--------------
The _split_command helper properly handles quoted strings:
- Single quotes ('...')
- Double quotes ("...")
- Preserves spaces within quotes
- Strips quotes from final tokens

Examples:
    'data read users'           → ["data", "read", "users"]
    'list -size'                → ["list", "-size"]
    "data insert users --name 'John Doe'" → ["data", "insert", "users", "--name", "John Doe"]

Usage Examples
--------------
**parse_command** - Main parser:
    >>> logger = get_logger()
    
    # Data command
    >>> parse_command("data read users --limit 10", logger)
    {'type': 'data', 'action': 'read', 'args': ['users'], 'options': {'limit': '10'}}
    
    # Function command
    >>> parse_command("func generate_id zU", logger)
    {'type': 'func', 'action': 'generate_id', 'args': ['zU'], 'options': {}}
    
    # Session command
    >>> parse_command("session info", logger)
    {'type': 'session', 'action': 'info', 'args': [], 'options': {}}
    
    # Error case
    >>> parse_command("unknown_cmd", logger)
    {'error': 'Unknown command: unknown_cmd'}

Layer Position
--------------
Layer 1, Position 5 (zParser - Tier 0 Foundation)
    - No internal dependencies
    - Used by: zShell (external - CRITICAL)
    - Provides: Shell command parsing

Dependencies
------------
Internal:
    - None (Tier 0 - Foundation)

External:
    - zCLI typing imports (Any, Dict, List)

See Also
--------
- zShell_executor.py: External usage for main shell command parsing
- wizard_step_executor.py: External usage for wizard command parsing
"""

from zOS import Any, Dict, List

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Import command types from centralized constants (private - internal use only)
from .parser_constants import (
    _CMD_TYPE_DATA as CMD_TYPE_DATA,
    _CMD_TYPE_FUNC as CMD_TYPE_FUNC,
    _CMD_TYPE_UTILS as CMD_TYPE_UTILS,
    _CMD_TYPE_SESSION as CMD_TYPE_SESSION,
    _CMD_TYPE_WALKER as CMD_TYPE_WALKER,
    _CMD_TYPE_OPEN as CMD_TYPE_OPEN,
    _CMD_TYPE_TEST as CMD_TYPE_TEST,
    _CMD_TYPE_AUTH as CMD_TYPE_AUTH,
    _CMD_TYPE_EXPORT as CMD_TYPE_EXPORT,
    _CMD_TYPE_CONFIG as CMD_TYPE_CONFIG,
    _CMD_TYPE_CONFIG_PERSISTENCE as CMD_TYPE_CONFIG_PERSISTENCE,
    _CMD_TYPE_LOAD as CMD_TYPE_LOAD,
    _CMD_TYPE_COMM as CMD_TYPE_COMM,
    _CMD_TYPE_WIZARD as CMD_TYPE_WIZARD,
    _CMD_TYPE_PLUGIN as CMD_TYPE_PLUGIN,
    _CMD_TYPE_LS as CMD_TYPE_LS,
    _CMD_TYPE_CD as CMD_TYPE_CD,
    _CMD_TYPE_CWD as CMD_TYPE_CWD,
    _CMD_TYPE_PWD as CMD_TYPE_PWD,
    _CMD_TYPE_SHORTCUT as CMD_TYPE_SHORTCUT,
    _CMD_TYPE_WHERE as CMD_TYPE_WHERE,
    _CMD_TYPE_HELP as CMD_TYPE_HELP,
)

# Dict Keys (for return structures)
DICT_KEY_ERROR: str = "error"
DICT_KEY_TYPE: str = "type"
DICT_KEY_ACTION: str = "action"
DICT_KEY_ARGS: str = "args"
DICT_KEY_OPTIONS: str = "options"

# Data Actions
ACTION_DATA_READ: str = "read"
ACTION_DATA_CREATE: str = "create"
ACTION_DATA_INSERT: str = "insert"
ACTION_DATA_UPDATE: str = "update"
ACTION_DATA_DELETE: str = "delete"
ACTION_DATA_DROP: str = "drop"
ACTION_DATA_HEAD: str = "head"
ACTION_DATA_SEARCH: str = "search"
ACTION_DATA_TABLES: str = "tables"

# Auth Actions
ACTION_AUTH_LOGIN: str = "login"
ACTION_AUTH_LOGOUT: str = "logout"
ACTION_AUTH_STATUS: str = "status"

# Export Targets
EXPORT_TARGET_MACHINE: str = "machine"
EXPORT_TARGET_CONFIG: str = "config"

# Config Actions
ACTION_CONFIG_CHECK: str = "check"
ACTION_CONFIG_SHOW: str = "show"
ACTION_CONFIG_GET: str = "get"
ACTION_CONFIG_SET: str = "set"
ACTION_CONFIG_RESET: str = "reset"
ACTION_CONFIG_LIST: str = "list"
ACTION_CONFIG_RELOAD: str = "reload"
ACTION_CONFIG_VALIDATE: str = "validate"
ACTION_CONFIG_MACHINE: str = "machine"
ACTION_CONFIG_CONFIG: str = "config"

# Comm Actions
ACTION_COMM_START: str = "start"
ACTION_COMM_STOP: str = "stop"
ACTION_COMM_STATUS: str = "status"
ACTION_COMM_RESTART: str = "restart"
ACTION_COMM_INFO: str = "info"
ACTION_COMM_INSTALL: str = "install"

# Default Actions
ACTION_DEFAULT_RUN: str = "run"
ACTION_DEFAULT_SHOW: str = "show"
ACTION_DEFAULT_LIST: str = "list"
ACTION_DEFAULT_CREATE: str = "create"
ACTION_DEFAULT_OPEN: str = "open"
ACTION_DEFAULT_LS: str = "ls"
ACTION_DEFAULT_CD: str = "cd"
ACTION_DEFAULT_PWD: str = "pwd"
ACTION_DEFAULT_STATUS: str = "status"
ACTION_DEFAULT_WIZARD: str = "wizard"
ACTION_DEFAULT_INFO: str = "info"

# Valid Actions Lists (for validation)
VALID_DATA_ACTIONS: List[str] = [
    ACTION_DATA_READ,
    ACTION_DATA_CREATE,
    ACTION_DATA_INSERT,
    ACTION_DATA_UPDATE,
    ACTION_DATA_DELETE,
    ACTION_DATA_DROP,
    ACTION_DATA_HEAD,
    ACTION_DATA_SEARCH,
    ACTION_DATA_TABLES
]

VALID_AUTH_ACTIONS: List[str] = [
    ACTION_AUTH_LOGIN,
    ACTION_AUTH_LOGOUT,
    ACTION_AUTH_STATUS
]

VALID_EXPORT_TARGETS: List[str] = [
    EXPORT_TARGET_MACHINE,
    EXPORT_TARGET_CONFIG
]

VALID_CONFIG_ACTIONS: List[str] = [
    ACTION_CONFIG_CHECK,
    ACTION_CONFIG_SHOW,
    ACTION_CONFIG_GET,
    ACTION_CONFIG_SET,
    ACTION_CONFIG_RESET,
    ACTION_CONFIG_LIST,
    ACTION_CONFIG_RELOAD,
    ACTION_CONFIG_VALIDATE,
    ACTION_CONFIG_MACHINE,
    ACTION_CONFIG_CONFIG
]

VALID_CONFIG_PERSISTENCE_TARGETS: List[str] = [
    EXPORT_TARGET_MACHINE,
    EXPORT_TARGET_CONFIG
]

VALID_COMM_ACTIONS: List[str] = [
    ACTION_COMM_START,
    ACTION_COMM_STOP,
    ACTION_COMM_STATUS,
    ACTION_COMM_RESTART,
    ACTION_COMM_INFO,
    ACTION_COMM_INSTALL
]

# Characters
CHAR_QUOTE_DOUBLE: str = '"'
CHAR_QUOTE_SINGLE: str = "'"
CHAR_SPACE: str = " "
CHAR_DASH_DOUBLE: str = "--"
CHAR_DASH_SINGLE: str = "-"

# Error Messages
ERROR_MSG_EMPTY_COMMAND: str = "Empty command"
ERROR_MSG_UNKNOWN_COMMAND: str = "Unknown command: {}"
ERROR_MSG_PARSE_ERROR: str = "Parse error: {}"
ERROR_MSG_DATA_NO_ACTION: str = "Data command requires action"
ERROR_MSG_DATA_INVALID_ACTION: str = "Invalid data action: {}"
ERROR_MSG_FUNC_NO_NAME: str = "Function command requires function name"
ERROR_MSG_UTILS_NO_NAME: str = "Utility command requires utility name"
ERROR_MSG_PLUGIN_NO_SUBCOMMAND: str = "Plugin command requires subcommand (exec, run, load, show, clear, reload)"
ERROR_MSG_SESSION_NO_ACTION: str = "Session command requires action"
ERROR_MSG_WALKER_NO_ACTION: str = "Walker command requires action"
ERROR_MSG_OPEN_NO_PATH: str = "Open command requires path"
ERROR_MSG_AUTH_NO_ACTION: str = "Auth command requires action (login, logout, status)"
ERROR_MSG_AUTH_INVALID_ACTION: str = "Invalid auth action: {}. Use: {}"
ERROR_MSG_EXPORT_NO_TARGET: str = "Export command requires target (machine, config)"
ERROR_MSG_EXPORT_INVALID_TARGET: str = "Invalid export target: {}. Use: {}"
ERROR_MSG_CONFIG_NO_ACTION: str = "Config command requires action (check, get, set, list, reload, validate, machine, config)"
ERROR_MSG_CONFIG_INVALID_ACTION: str = "Invalid config action: {}. Use: {}"
ERROR_MSG_CONFIG_PERSIST_NO_TARGET: str = "Config persistence command requires target (machine, config)"
ERROR_MSG_CONFIG_PERSIST_INVALID_TARGET: str = "Invalid config persistence target: {}. Use: {}"
ERROR_MSG_LOAD_NO_ARGS: str = "Load command requires arguments"
ERROR_MSG_COMM_NO_ACTION: str = "Comm command requires action (start, stop, status, restart, info, install)"
ERROR_MSG_COMM_INVALID_ACTION: str = "Invalid comm action: {}. Use: {}"
ERROR_MSG_WIZARD_NO_FLAGS: str = "Wizard command requires flags (--start, --stop, --run, --show, --clear)"

# Log Messages
LOG_MSG_PARSE_FAILED: str = "Command parsing failed: %s"

# Misc Constants
MIN_PARTS_SIMPLE_PARSER: int = 2
SLICE_START_ARGS: int = 2
SLICE_START_OPTIONS: int = 1


# ============================================================================
# COMMAND ROUTER (constant mapping)
# ============================================================================

# This will be populated after function definitions
COMMAND_ROUTER: Dict[str, Any] = {}


# ============================================================================
# FUNCTIONS
# ============================================================================

def parse_command(command: str, logger: Any) -> Dict[str, Any]:
    """
    Parse shell commands into structured format.
    
    ⚠️ CRITICAL: This function is used externally by zShell for ALL shell command parsing.
    Signature must remain stable.
    
    Main entry point for command parsing. Routes commands to specialized parsers based
    on command type (first word). Handles 20+ command types with uniform structure.
    
    Command Router Pattern:
        1. Strip and split command into parts
        2. Extract command type (first word, lowercase)
        3. Look up parser in COMMAND_ROUTER
        4. Delegate to specialized _parse_*() function
        5. Return structured dict or error dict
    
    Args:
        command: Raw command string from user (e.g., "data read users --limit 10")
        logger: Logger instance for error logging
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
        
        Success format:
            {
                "type": str,              # Command type
                "action": str,            # Action to perform
                "args": List[str],        # Positional arguments
                "options": Dict[str, Any] # Named options
            }
        
        Error format:
            {
                "error": str              # Error message
            }
    
    Raises:
        None: All exceptions are caught and returned as error dicts
    
    Examples:
        >>> logger = get_logger()
        
        # Data command
        >>> parse_command("data read users --limit 10", logger)
        {'type': 'data', 'action': 'read', 'args': ['users'], 'options': {'limit': '10'}}
        
        # Function command
        >>> parse_command("func generate_id zU", logger)
        {'type': 'func', 'action': 'generate_id', 'args': ['zU'], 'options': {}}
        
        # Auth command
        >>> parse_command("auth login admin", logger)
        {'type': 'auth', 'action': 'login', 'args': ['admin'], 'options': {}}
        
        # Empty command
        >>> parse_command("", logger)
        {'error': 'Empty command'}
        
        # Unknown command
        >>> parse_command("unknowncmd", logger)
        {'error': 'Unknown command: unknowncmd'}
    
    External Usage:
        zShell_executor.py:
            parsed = self.zcli.zparser.parse_command(command)
        Purpose: Parse user commands in main shell
        
        wizard_step_executor.py:
            parsed = zcli.zparser.parse_command(step_value)
        Purpose: Parse commands in wizard steps
    
    Notes:
        - Strips whitespace from command before parsing
        - Command type is case-insensitive (converted to lowercase)
        - Returns error dict on any exception (graceful degradation)
        - Logs errors via provided logger
        - Signature stability is CRITICAL for external usage
    
    See Also:
        - _split_command: Helper for splitting command with quote handling
        - All _parse_* functions: Specialized parsers for each command type
    """
    command = command.strip()

    # Split into parts using quote-aware splitting
    parts = _split_command(command)
    if not parts:
        return {DICT_KEY_ERROR: ERROR_MSG_EMPTY_COMMAND}

    # Extract command type (first word, lowercase)
    command_type = parts[0].lower()

    # Look up parser in command router
    if command_type not in COMMAND_ROUTER:
        return {DICT_KEY_ERROR: ERROR_MSG_UNKNOWN_COMMAND.format(command_type)}

    try:
        # Delegate to specialized parser
        return COMMAND_ROUTER[command_type](parts)
    except Exception as e:  # pylint: disable=broad-except
        logger.error(LOG_MSG_PARSE_FAILED, e)
        return {DICT_KEY_ERROR: ERROR_MSG_PARSE_ERROR.format(str(e))}


def _split_command(command: str) -> List[str]:
    """
    Split command into parts, handling quotes and special characters.
    
    Splits command string on spaces while preserving quoted strings as single tokens.
    Handles both single and double quotes properly, allowing spaces within quotes.
    
    Quote Handling Logic:
        1. Iterate through each character
        2. Track quote state (in_quotes, quote_char)
        3. Build current token character by character
        4. When space found outside quotes: finalize current token
        5. When quote found: toggle quote state and track quote character
        6. Strip whitespace from tokens before adding to results
    
    Args:
        command: Command string to split (may contain quotes)
    
    Returns:
        List[str]: List of command parts with quotes preserved in content
    
    Examples:
        >>> _split_command("data read users")
        ['data', 'read', 'users']
        
        >>> _split_command('echo "Hello World"')
        ['echo', '"Hello World"']
        
        >>> _split_command("data insert --name 'John Doe' --age 30")
        ['data', 'insert', '--name', "'John Doe'", '--age', '30']
        
        >>> _split_command("load '@.ui.file with spaces.yaml'")
        ['load', "'@.ui.file with spaces.yaml'"]
    
    Notes:
        - Handles both single (') and double (") quotes
        - Preserves spaces within quoted strings
        - Quotes are kept in the token (not stripped)
        - Empty tokens are filtered out
        - Whitespace trimmed from non-quoted tokens
    
    See Also:
        - parse_command: Uses this helper for initial command splitting
    """
    parts = []
    current = ""
    in_quotes = False
    quote_char = None

    for char in command:
        # Check if this is a quote character and we're not already in quotes
        if char in [CHAR_QUOTE_DOUBLE, CHAR_QUOTE_SINGLE] and not in_quotes:
            in_quotes = True
            quote_char = char
            current += char
        # Check if this is the closing quote
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            current += char
        # Check if this is a space outside of quotes (token separator)
        elif char == CHAR_SPACE and not in_quotes:
            if current.strip():
                parts.append(current.strip())
            current = ""
        # Regular character: add to current token
        else:
            current += char

    # Add final token if exists
    if current.strip():
        parts.append(current.strip())

    return parts


def _parse_data_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse data commands like 'data read users --limit 10' or 'data insert users --name Alice'.
    
    Data commands handle database/data operations with various actions (read, create, insert,
    update, delete, drop, head, search, tables). Supports positional args and named options.
    
    Args:
        parts: Command parts from _split_command (e.g., ['data', 'read', 'users', '--limit', '10'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
        
        Success:
            {
                "type": "data",
                "action": str (read/create/insert/update/delete/drop/head/search/tables),
                "args": List[str] (e.g., ["users"]),
                "options": Dict[str, Any] (e.g., {"limit": "10"})
            }
        
        Error:
            {"error": str}
    
    Examples:
        >>> _parse_data_command(['data', 'read', 'users', '--limit', '10'])
        {'type': 'data', 'action': 'read', 'args': ['users'], 'options': {'limit': '10'}}
        
        >>> _parse_data_command(['data', 'insert', 'users', '--name', 'Alice', '--age', '30'])
        {'type': 'data', 'action': 'insert', 'args': ['users'], 'options': {'name': 'Alice', 'age': '30'}}
        
        >>> _parse_data_command(['data'])
        {'error': 'Data command requires action'}
    
    Notes:
        - Requires at least 2 parts (data + action)
        - Action must be in VALID_DATA_ACTIONS
        - Options start with -- (e.g., --limit 10)
        - Boolean options: --flag (no value)
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_DATA_NO_ACTION}

    action = parts[1].lower()

    if action not in VALID_DATA_ACTIONS:
        return {DICT_KEY_ERROR: ERROR_MSG_DATA_INVALID_ACTION.format(action)}

    # Extract arguments and options
    args, options = _extract_args_and_options(parts, SLICE_START_ARGS)

    return {
        DICT_KEY_TYPE: CMD_TYPE_DATA,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_func_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse function commands like 'func generate_id zU'.
    
    Function commands invoke zFunc functions with positional arguments.
    
    Args:
        parts: Command parts (e.g., ['func', 'generate_id', 'zU'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_func_command(['func', 'generate_id', 'zU'])
        {'type': 'func', 'action': 'generate_id', 'args': ['zU'], 'options': {}}
        
        >>> _parse_func_command(['func', 'hash_password', 'secret123'])
        {'type': 'func', 'action': 'hash_password', 'args': ['secret123'], 'options': {}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_FUNC_NO_NAME}

    func_name = parts[1]
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_FUNC,
        DICT_KEY_ACTION: func_name,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_utils_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse utility commands like 'utils hash_password mypass'.
    
    Utility commands invoke utility functions with positional arguments.
    
    Args:
        parts: Command parts (e.g., ['utils', 'hash_password', 'mypass'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_utils_command(['utils', 'hash_password', 'secret'])
        {'type': 'utils', 'action': 'hash_password', 'args': ['secret'], 'options': {}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_UTILS_NO_NAME}

    util_name = parts[1]
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_UTILS,
        DICT_KEY_ACTION: util_name,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_plugin_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse plugin commands like 'plugin exec', 'plugin load', or 'plugin show'.
    
    Plugin commands handle both plugin execution (exec/run) and plugin cache
    management (load/show/clear/reload).
    
    Args:
        parts: Command parts (e.g., ['plugin', 'exec', 'hash_password', 'arg1'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_plugin_command(['plugin', 'exec', 'hash_password', 'mypass'])
        {'type': 'plugin', 'action': 'exec', 'args': ['hash_password', 'mypass'], 'options': {}}
        
        >>> _parse_plugin_command(['plugin', 'load', '@.utils.my_plugin'])
        {'type': 'plugin', 'action': 'load', 'args': ['@.utils.my_plugin'], 'options': {}}
        
        >>> _parse_plugin_command(['plugin', 'show'])
        {'type': 'plugin', 'action': 'show', 'args': [], 'options': {}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_PLUGIN_NO_SUBCOMMAND}

    action = parts[1]
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_PLUGIN,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_session_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse session commands like 'session' or 'session set mode zGUI'.
    
    Session commands manage session state and configuration. If no action is
    provided, defaults to 'info' action (display session state).
    
    Args:
        parts: Command parts (e.g., ['session'] or ['session', 'set', 'mode', 'zGUI'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_session_command(['session'])
        {'type': 'session', 'action': 'info', 'args': [], 'options': {}}
        
        >>> _parse_session_command(['session', 'info'])
        {'type': 'session', 'action': 'info', 'args': [], 'options': {}}
        
        >>> _parse_session_command(['session', 'set', 'mode', 'zGUI'])
        {'type': 'session', 'action': 'set', 'args': ['mode', 'zGUI'], 'options': {}}
        
        >>> _parse_session_command(['session', 'get', 'zMode'])
        {'type': 'session', 'action': 'get', 'args': ['zMode'], 'options': {}}
    
    Notes:
        - Default action is 'info' if no action provided
        - Most common use case is viewing session state
    """
    # Default to "info" action if no action provided
    action = ACTION_DEFAULT_INFO if len(parts) < MIN_PARTS_SIMPLE_PARSER else parts[1]
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_SESSION,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_walker_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse walker commands like 'walker load ui.zCloud.yaml'.
    
    Walker commands manage UI file loading and navigation.
    
    Args:
        parts: Command parts (e.g., ['walker', 'load', 'ui.zCloud.yaml'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_walker_command(['walker', 'load', 'ui.zCloud.yaml'])
        {'type': 'walker', 'action': 'load', 'args': ['ui.zCloud.yaml'], 'options': {}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_WALKER_NO_ACTION}

    action = parts[1]
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_WALKER,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_open_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse open commands like 'open @.zProducts.zTimer.index.html' or 'open https://example.com'.
    
    Open commands open files, directories, or URLs in appropriate applications.
    Path is rejoined if split (preserves spaces in paths).
    
    Args:
        parts: Command parts (e.g., ['open', '@.zProducts.zTimer.index.html'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_open_command(['open', '@.zProducts.zTimer.index.html'])
        {'type': 'open', 'action': 'open', 'args': ['@.zProducts.zTimer.index.html'], 'options': {}}
        
        >>> _parse_open_command(['open', 'https://example.com'])
        {'type': 'open', 'action': 'open', 'args': ['https://example.com'], 'options': {}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_OPEN_NO_PATH}

    # The path is everything after "open", rejoined if it was split
    path = CHAR_SPACE.join(parts[1:])

    return {
        DICT_KEY_TYPE: CMD_TYPE_OPEN,
        DICT_KEY_ACTION: ACTION_DEFAULT_OPEN,
        DICT_KEY_ARGS: [path],
        DICT_KEY_OPTIONS: {}
    }


def _parse_test_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse test commands like 'test run' or 'test session'.
    
    Test commands execute test suites. Default action is "run" if not specified.
    
    Args:
        parts: Command parts (e.g., ['test', 'run'] or ['test'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_test_command(['test', 'run'])
        {'type': 'test', 'action': 'run', 'args': [], 'options': {}}
        
        >>> _parse_test_command(['test'])
        {'type': 'test', 'action': 'run', 'args': [], 'options': {}}
        
        >>> _parse_test_command(['test', 'session'])
        {'type': 'test', 'action': 'session', 'args': [], 'options': {}}
    """
    action = ACTION_DEFAULT_RUN if len(parts) < MIN_PARTS_SIMPLE_PARSER else parts[1]
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_TEST,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_auth_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse auth commands like 'auth login', 'auth logout', 'auth status'.
    
    Auth commands manage authentication state. Validates action against VALID_AUTH_ACTIONS.
    
    Args:
        parts: Command parts (e.g., ['auth', 'login', 'admin'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_auth_command(['auth', 'login', 'admin'])
        {'type': 'auth', 'action': 'login', 'args': ['admin'], 'options': {}}
        
        >>> _parse_auth_command(['auth', 'logout'])
        {'type': 'auth', 'action': 'logout', 'args': [], 'options': {}}
        
        >>> _parse_auth_command(['auth', 'invalid'])
        {'error': 'Invalid auth action: invalid. Use: login, logout, status'}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_AUTH_NO_ACTION}

    action = parts[1].lower()

    if action not in VALID_AUTH_ACTIONS:
        valid_list = ", ".join(VALID_AUTH_ACTIONS)
        return {DICT_KEY_ERROR: ERROR_MSG_AUTH_INVALID_ACTION.format(action, valid_list)}

    # Extract any additional arguments (e.g., username, server URL)
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []

    return {
        DICT_KEY_TYPE: CMD_TYPE_AUTH,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_export_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse export commands like 'export machine text_editor cursor'.
    
    Export commands export configuration to persistent storage. Validates target
    against VALID_EXPORT_TARGETS. Supports flags (--show, --reset).
    
    Args:
        parts: Command parts (e.g., ['export', 'machine', 'text_editor', 'cursor', '--show'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_export_command(['export', 'machine', 'text_editor', 'cursor'])
        {'type': 'export', 'action': 'machine', 'args': ['text_editor', 'cursor'], 'options': {}}
        
        >>> _parse_export_command(['export', 'config', '--show'])
        {'type': 'export', 'action': 'config', 'args': [], 'options': {'show': True}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_EXPORT_NO_TARGET}

    target = parts[1].lower()

    if target not in VALID_EXPORT_TARGETS:
        valid_list = ", ".join(VALID_EXPORT_TARGETS)
        return {DICT_KEY_ERROR: ERROR_MSG_EXPORT_INVALID_TARGET.format(target, valid_list)}

    # Check for flags (--show, --reset)
    options = {}
    args = []

    for part in parts[SLICE_START_ARGS:]:
        if part.startswith(CHAR_DASH_DOUBLE):
            flag = part[2:]
            options[flag] = True
        else:
            args.append(part)

    return {
        DICT_KEY_TYPE: CMD_TYPE_EXPORT,
        DICT_KEY_ACTION: target,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_config_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse config commands (unified config system).
    
    Supports:
        - Diagnostics: 'config check', 'config show'
        - Get: 'config get machine text_editor', 'config get env deployment'
        - Set: 'config set machine text_editor cursor', 'config set env deployment prod'
        - Reset: 'config reset machine text_editor', 'config reset env deployment'
    
    Config commands manage configuration state. Validates action against VALID_CONFIG_ACTIONS.
    Delegates to _parse_config_persistence_command for legacy machine/config actions.
    
    Args:
        parts: Command parts (e.g., ['config', 'check'], ['config', 'set', 'machine', 'browser', 'Chrome'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_config_command(['config', 'check'])
        {'type': 'config', 'action': 'check', 'args': [], 'options': {}}
        
        >>> _parse_config_command(['config', 'get', 'machine', 'text_editor'])
        {'type': 'config', 'action': 'get', 'args': ['machine', 'text_editor'], 'options': {}}
        
        >>> _parse_config_command(['config', 'set', 'machine', 'text_editor', 'cursor'])
        {'type': 'config', 'action': 'set', 'args': ['machine', 'text_editor', 'cursor'], 'options': {}}
        
        >>> _parse_config_command(['config', 'reset', 'env', 'deployment'])
        {'type': 'config', 'action': 'reset', 'args': ['env', 'deployment'], 'options': {}}
        
        >>> _parse_config_command(['config', 'machine', 'browser', 'Chrome'])
        {'type': 'config_persistence', 'action': 'machine', 'args': ['browser', 'Chrome'], 'options': {}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_CONFIG_NO_ACTION}

    action = parts[1].lower()

    if action not in VALID_CONFIG_ACTIONS:
        valid_list = ", ".join(VALID_CONFIG_ACTIONS)
        return {DICT_KEY_ERROR: ERROR_MSG_CONFIG_INVALID_ACTION.format(action, valid_list)}

    # Handle persistence commands (machine, config)
    if action in [ACTION_CONFIG_MACHINE, ACTION_CONFIG_CONFIG]:
        return _parse_config_persistence_command(parts)

    # Extract arguments and options for other commands
    args = parts[SLICE_START_ARGS:] if len(parts) > SLICE_START_ARGS else []
    options = {}

    return {
        DICT_KEY_TYPE: CMD_TYPE_CONFIG,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_config_persistence_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse config persistence commands like 'config machine browser Chrome' or 'config machine --reset browser'.
    
    Config persistence commands save configuration to disk. Validates target against
    VALID_CONFIG_PERSISTENCE_TARGETS. Supports flags (--show, --reset).
    
    Args:
        parts: Command parts (e.g., ['config', 'machine', 'browser', 'Chrome', '--reset'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_config_persistence_command(['config', 'machine', 'browser', 'Chrome'])
        {'type': 'config_persistence', 'action': 'machine', 'args': ['browser', 'Chrome'], 'options': {}}
        
        >>> _parse_config_persistence_command(['config', 'machine', '--reset', 'browser'])
        {'type': 'config_persistence', 'action': 'machine', 'args': ['browser'], 'options': {'reset': True}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_CONFIG_PERSIST_NO_TARGET}

    target = parts[1].lower()

    if target not in VALID_CONFIG_PERSISTENCE_TARGETS:
        valid_list = ", ".join(VALID_CONFIG_PERSISTENCE_TARGETS)
        return {DICT_KEY_ERROR: ERROR_MSG_CONFIG_PERSIST_INVALID_TARGET.format(target, valid_list)}

    # Check for flags (--show, --reset)
    options = {}
    args = []

    for part in parts[SLICE_START_ARGS:]:
        if part.startswith(CHAR_DASH_DOUBLE):
            flag = part[2:]
            options[flag] = True
        else:
            args.append(part)

    return {
        DICT_KEY_TYPE: CMD_TYPE_CONFIG_PERSISTENCE,
        DICT_KEY_ACTION: target,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_load_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse load commands like 'load @.zUI.manual' or 'load @.zSchema.demo --as my_schema'.
    
    Load commands load files with optional named options (--as, etc.).
    
    Args:
        parts: Command parts (e.g., ['load', '@.zUI.manual', '--as', 'myui'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_load_command(['load', '@.zUI.manual'])
        {'type': 'load', 'action': 'load', 'args': ['@.zUI.manual'], 'options': {}}
        
        >>> _parse_load_command(['load', '@.zSchema.demo', '--as', 'my_schema'])
        {'type': 'load', 'action': 'load', 'args': ['@.zSchema.demo'], 'options': {'as': 'my_schema'}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_LOAD_NO_ARGS}

    # Extract arguments and options
    args, options = _extract_args_and_options(parts, SLICE_START_OPTIONS)

    return {
        DICT_KEY_TYPE: CMD_TYPE_LOAD,
        DICT_KEY_ACTION: ACTION_DEFAULT_OPEN,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_comm_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse comm commands like 'comm start postgresql', 'comm status'.
    
    Comm commands manage communication services (databases, servers, etc.).
    Validates action against VALID_COMM_ACTIONS. Supports args and options.
    
    Args:
        parts: Command parts (e.g., ['comm', 'start', 'postgresql', '--port', '5432'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_comm_command(['comm', 'start', 'postgresql'])
        {'type': 'comm', 'action': 'start', 'args': ['postgresql'], 'options': {}}
        
        >>> _parse_comm_command(['comm', 'start', 'postgresql', '--port', '5432'])
        {'type': 'comm', 'action': 'start', 'args': ['postgresql'], 'options': {'port': '5432'}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_COMM_NO_ACTION}

    action = parts[1].lower()

    if action not in VALID_COMM_ACTIONS:
        valid_list = ", ".join(VALID_COMM_ACTIONS)
        return {DICT_KEY_ERROR: ERROR_MSG_COMM_INVALID_ACTION.format(action, valid_list)}

    # Extract arguments and options
    args, options = _extract_args_and_options(parts, SLICE_START_ARGS)

    return {
        DICT_KEY_TYPE: CMD_TYPE_COMM,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_wizard_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse wizard commands with flags like 'wizard --start', 'wizard --run myfile'.
    
    Wizard commands manage wizard execution. Requires at least one flag
    (--start, --stop, --run, --show, --clear).
    
    Args:
        parts: Command parts (e.g., ['wizard', '--start', '--run', 'myfile'])
    
    Returns:
        Dict[str, Any]: Structured command dict or error dict
    
    Examples:
        >>> _parse_wizard_command(['wizard', '--start'])
        {'type': 'wizard', 'action': 'wizard', 'args': [], 'options': {'start': True}}
        
        >>> _parse_wizard_command(['wizard', '--run', 'myfile'])
        {'type': 'wizard', 'action': 'wizard', 'args': ['myfile'], 'options': {'run': True}}
    """
    if len(parts) < MIN_PARTS_SIMPLE_PARSER:
        return {DICT_KEY_ERROR: ERROR_MSG_WIZARD_NO_FLAGS}

    # Extract options
    options = {}
    args = []

    for part in parts[1:]:
        if part.startswith(CHAR_DASH_DOUBLE):
            flag = part[2:]
            options[flag] = True
        else:
            args.append(part)

    return {
        DICT_KEY_TYPE: CMD_TYPE_WIZARD,
        DICT_KEY_ACTION: ACTION_DEFAULT_WIZARD,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_ls_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse list/ls/dir commands like 'list', 'ls @.path', 'list --sizes'.
    
    List directory commands show directory contents. Supports flags (-l, --recursive, etc.).
    
    Args:
        parts: Command parts (e.g., ['ls', '@.path', '--recursive', '-l'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_ls_command(['ls'])
        {'type': 'ls', 'action': 'ls', 'args': [], 'options': {}}
        
        >>> _parse_ls_command(['ls', '@.path', '--recursive'])
        {'type': 'ls', 'action': 'ls', 'args': ['@.path'], 'options': {'recursive': True}}
    """
    args = []
    options = {}
    
    for part in parts[1:]:
        if part.startswith(CHAR_DASH_DOUBLE) or part.startswith(CHAR_DASH_SINGLE):
            flag = part.lstrip(CHAR_DASH_SINGLE)
            options[flag] = True
        else:
            args.append(part)
    
    return {
        DICT_KEY_TYPE: CMD_TYPE_LS,
        DICT_KEY_ACTION: ACTION_DEFAULT_LS,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_cd_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse cd commands like 'cd @.path' or 'cd ~'.
    
    Change directory commands change current working directory.
    
    Args:
        parts: Command parts (e.g., ['cd', '@.path'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_cd_command(['cd', '@.path'])
        {'type': 'cd', 'action': 'cd', 'args': ['@.path'], 'options': {}}
        
        >>> _parse_cd_command(['cd', '~'])
        {'type': 'cd', 'action': 'cd', 'args': ['~'], 'options': {}}
    """
    args = parts[1:] if len(parts) > 1 else []
    
    return {
        DICT_KEY_TYPE: CMD_TYPE_CD,
        DICT_KEY_ACTION: ACTION_DEFAULT_CD,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_pwd_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse cwd/pwd command (current/print working directory).
    
    Shows current working directory. Both 'cwd' (primary) and 'pwd' (alias) are supported.
    Takes no arguments.
    
    Args:
        parts: Command parts (e.g., ['cwd'] or ['pwd'])
    
    Returns:
        Dict[str, Any]: Structured command dict with appropriate type
    
    Examples:
        >>> _parse_pwd_command(['cwd'])
        {'type': 'cwd', 'action': 'pwd', 'args': [], 'options': {}}
        
        >>> _parse_pwd_command(['pwd'])
        {'type': 'pwd', 'action': 'pwd', 'args': [], 'options': {}}
    
    Note:
        Both commands execute the same function (execute_pwd), but return their
        respective type for logging/debugging purposes.
    """
    # Determine which command was used (cwd is primary, pwd is alias)
    command_type = CMD_TYPE_CWD if parts[0] == "cwd" else CMD_TYPE_PWD
    
    return {
        DICT_KEY_TYPE: command_type,
        DICT_KEY_ACTION: ACTION_DEFAULT_PWD,
        DICT_KEY_ARGS: [],
        DICT_KEY_OPTIONS: {}
    }


def _parse_shortcut_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse shortcut commands like 'shortcut', 'shortcut name="command"', 'shortcut --remove name'.
    
    Shortcut commands manage command shortcuts. Default action is "list" if no args/options.
    
    Args:
        parts: Command parts (e.g., ['shortcut', 'name="command"'] or ['shortcut', '--remove', 'name'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_shortcut_command(['shortcut'])
        {'type': 'shortcut', 'action': 'list', 'args': [], 'options': {}}
        
        >>> _parse_shortcut_command(['shortcut', 'gs="git status"'])
        {'type': 'shortcut', 'action': 'create', 'args': ['gs="git status"'], 'options': {}}
        
        >>> _parse_shortcut_command(['shortcut', '--remove', 'gs'])
        {'type': 'shortcut', 'action': 'create', 'args': ['gs'], 'options': {'remove': True}}
    """
    # Extract options and args
    options = {}
    args = []
    
    for part in parts[1:]:
        if part.startswith(CHAR_DASH_DOUBLE):
            flag = part[2:]
            options[flag] = True
        else:
            args.append(part)
    
    action = ACTION_DEFAULT_LIST if not args and not options else ACTION_DEFAULT_CREATE
    
    return {
        DICT_KEY_TYPE: CMD_TYPE_SHORTCUT,
        DICT_KEY_ACTION: action,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: options
    }


def _parse_where_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse where commands like 'where', 'where on', 'where off', 'where toggle'.
    
    Where commands manage contextual prompt display. Default action is "status" if no args.
    
    Args:
        parts: Command parts (e.g., ['where'], ['where', 'on'], ['where', 'toggle'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_where_command(['where'])
        {'type': 'where', 'action': 'status', 'args': [], 'options': {}}
        
        >>> _parse_where_command(['where', 'on'])
        {'type': 'where', 'action': 'status', 'args': ['on'], 'options': {}}
        
        >>> _parse_where_command(['where', 'toggle'])
        {'type': 'where', 'action': 'status', 'args': ['toggle'], 'options': {}}
        
        >>> _parse_where_command(['where', 'off'])
        {'type': 'where', 'action': 'status', 'args': ['off'], 'options': {}}
    """
    # Extract args (no options needed for where command)
    args = parts[1:] if len(parts) > 1 else []
    
    return {
        DICT_KEY_TYPE: CMD_TYPE_WHERE,
        DICT_KEY_ACTION: ACTION_DEFAULT_STATUS,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


def _parse_help_command(parts: List[str]) -> Dict[str, Any]:
    """
    Parse help commands like 'help', 'help ls', 'help shortcut'.
    
    Help commands show shell terminal command documentation. Optional argument
    specifies which command to show help for.
    
    Args:
        parts: Command parts (e.g., ['help'], ['help', 'ls'], ['help', 'shortcut'])
    
    Returns:
        Dict[str, Any]: Structured command dict
    
    Examples:
        >>> _parse_help_command(['help'])
        {'type': 'help', 'action': 'show', 'args': [], 'options': {}}
        
        >>> _parse_help_command(['help', 'ls'])
        {'type': 'help', 'action': 'show', 'args': ['ls'], 'options': {}}
        
        >>> _parse_help_command(['help', 'shortcut'])
        {'type': 'help', 'action': 'show', 'args': ['shortcut'], 'options': {}}
    """
    # Extract args (command name to show help for)
    args = parts[1:] if len(parts) > 1 else []
    
    return {
        DICT_KEY_TYPE: CMD_TYPE_HELP,
        DICT_KEY_ACTION: ACTION_DEFAULT_SHOW,
        DICT_KEY_ARGS: args,
        DICT_KEY_OPTIONS: {}
    }


# ============================================================================
# DRY HELPER FUNCTIONS
# ============================================================================

def _extract_args_and_options(parts: List[str], start_idx: int) -> tuple:
    """
    DRY helper: Extract arguments and options from command parts.
    
    Extracts positional arguments and named options (--key value or --flag) from
    command parts starting at specified index. Used by multiple parsers to avoid
    code duplication.
    
    Args:
        parts: Full command parts list
        start_idx: Index to start extraction (typically 1 or 2)
    
    Returns:
        tuple: (args: List[str], options: Dict[str, Any])
            - args: Positional arguments
            - options: Named options (--key value) or flags (--flag)
    
    Examples:
        >>> _extract_args_and_options(['cmd', 'action', 'arg1', '--key', 'val', '--flag'], 2)
        (['arg1'], {'key': 'val', 'flag': True})
    """
    args = []
    options = {}

    i = start_idx
    while i < len(parts):
        part = parts[i]

        if part.startswith(CHAR_DASH_DOUBLE):
            # Option
            opt_name = part[2:]
            if i + 1 < len(parts) and not parts[i + 1].startswith(CHAR_DASH_DOUBLE):
                options[opt_name] = parts[i + 1]
                i += 2
            else:
                options[opt_name] = True
                i += 1
        else:
            # Argument
            args.append(part)
            i += 1

    return args, options


# ============================================================================
# INITIALIZE COMMAND ROUTER
# ============================================================================

# Populate command router after all functions are defined
COMMAND_ROUTER = {
    CMD_TYPE_DATA: _parse_data_command,
    CMD_TYPE_FUNC: _parse_func_command,
    CMD_TYPE_UTILS: _parse_utils_command,
    CMD_TYPE_SESSION: _parse_session_command,
    CMD_TYPE_WALKER: _parse_walker_command,
    CMD_TYPE_OPEN: _parse_open_command,
    CMD_TYPE_TEST: _parse_test_command,
    CMD_TYPE_AUTH: _parse_auth_command,
    CMD_TYPE_EXPORT: _parse_export_command,
    CMD_TYPE_CONFIG: _parse_config_command,
    CMD_TYPE_LOAD: _parse_load_command,
    CMD_TYPE_COMM: _parse_comm_command,
    CMD_TYPE_WIZARD: _parse_wizard_command,
    CMD_TYPE_PLUGIN: _parse_plugin_command,
    CMD_TYPE_LS: _parse_ls_command,
    "list": _parse_ls_command,  # Modern alias for ls (beginner-friendly)
    "dir": _parse_ls_command,   # Windows alias for ls
    CMD_TYPE_CD: _parse_cd_command,
    CMD_TYPE_CWD: _parse_pwd_command,  # Primary: Current Working Directory
    CMD_TYPE_PWD: _parse_pwd_command,  # Alias: Unix compatibility (Print Working Directory)
    CMD_TYPE_SHORTCUT: _parse_shortcut_command,
    CMD_TYPE_WHERE: _parse_where_command,
    CMD_TYPE_HELP: _parse_help_command,
}
