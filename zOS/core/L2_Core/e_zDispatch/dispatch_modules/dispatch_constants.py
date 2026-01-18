"""
Dispatch Constants - Centralized constants for zDispatch subsystem

This module provides all constants used across the zDispatch subsystem,
including command prefixes, dict keys, modifiers, labels, log messages,
mode values, and configuration defaults.

Organization:
    - Subsystem Identity
    - Command Prefixes & Dict Keys
    - Modifiers (^, ~, *, !)
    - Mode Values
    - Display Labels
    - Display Event Keys
    - Data Keys (Common dict keys)
    - Navigation
    - Plugins
    - Default Values
    - Styles & Indentation
    - Prompts & Input
    - Log Messages
    - Error Messages

Usage:
    from .dispatch_constants import (
        CMD_PREFIX_ZFUNC,
        KEY_ZFUNC,
        MOD_EXCLAMATION,
        MODE_BIFROST,
    )
"""

# ==============================================================================
# SUBSYSTEM IDENTITY
# ==============================================================================

SUBSYSTEM_NAME = "zDispatch"
SUBSYSTEM_COLOR = "DISPATCH"

# Display Messages (INTERNAL - used only within zDispatch)
_MSG_READY = "zDispatch Ready"
_MSG_HANDLE = "handle zDispatch"

# ==============================================================================
# COMMAND PREFIXES (String Format - for parsing)
# ==============================================================================

CMD_PREFIX_ZFUNC = "zFunc("
CMD_PREFIX_ZLINK = "zLink("
CMD_PREFIX_ZOPEN = "zOpen("
CMD_PREFIX_ZWIZARD = "zWizard("
CMD_PREFIX_ZREAD = "zRead("

# ==============================================================================
# DICT KEYS - Subsystem Commands
# ==============================================================================

KEY_ZFUNC = "zFunc"
KEY_ZLINK = "zLink"
KEY_ZDELTA = "zDelta"
KEY_ZOPEN = "zOpen"
KEY_ZWIZARD = "zWizard"
KEY_ZREAD = "zRead"
KEY_ZDATA = "zData"
KEY_ZDIALOG = "zDialog"
KEY_ZDISPLAY = "zDisplay"
KEY_ZLOGIN = "zLogin"
KEY_ZLOGOUT = "zLogout"

# ==============================================================================
# DICT KEYS - Context & Session
# ==============================================================================
# Note: Mode is now accessed via SESSION_KEY_ZMODE from zConfig (session-level)
# KEY_MODE removed - contexts should not contain mode (session is source of truth)

KEY_ZVAFILE = "zVaFile"
KEY_ZBLOCK = "zBlock"

# ==============================================================================
# DICT KEYS - Data Operations (zData integration)
# ==============================================================================

KEY_ACTION = "action"
KEY_MODEL = "model"
KEY_TABLE = "table"
KEY_TABLES = "tables"
KEY_FIELDS = "fields"
KEY_VALUES = "values"
KEY_FILTERS = "filters"
KEY_WHERE = "where"
KEY_ORDER_BY = "order_by"
KEY_LIMIT = "limit"
KEY_OFFSET = "offset"

# ==============================================================================
# DICT KEYS - Display & UI
# ==============================================================================

KEY_CONTENT = "content"
KEY_INDENT = "indent"
KEY_EVENT = "event"
KEY_LABEL = "label"
KEY_COLOR = "color"
KEY_STYLE = "style"
KEY_MESSAGE = "message"

# ==============================================================================
# MODIFIERS - Symbols
# ==============================================================================

MOD_CARET = "^"           # Bounce back: Execute action → return to menu
MOD_TILDE = "~"           # Anchor: Disable back navigation (used with *)
MOD_ASTERISK = "*"        # Menu: Create menu from horizontal data
MOD_EXCLAMATION = "!"     # Required: Retry until success

# Modifier Groups
PREFIX_MODIFIERS = [MOD_CARET, MOD_TILDE]
SUFFIX_MODIFIERS = [MOD_EXCLAMATION, MOD_ASTERISK]
ALL_MODIFIERS = PREFIX_MODIFIERS + SUFFIX_MODIFIERS

# ==============================================================================
# MODE VALUES
# ==============================================================================

MODE_BIFROST = "zBifrost"
MODE_TERMINAL = "Terminal"
MODE_WALKER = "Walker"

# ==============================================================================
# DISPLAY LABELS (zDeclare messages) - INTERNAL
# ==============================================================================

_LABEL_LAUNCHER = "zLauncher"
_LABEL_HANDLE_ZFUNC = "[HANDLE] zFunc"
_LABEL_HANDLE_ZFUNC_DICT = "[HANDLE] zFunc (dict)"
_LABEL_HANDLE_ZLINK = "[HANDLE] zLink"
_LABEL_HANDLE_ZDELTA = "[HANDLE] zDelta"
_LABEL_HANDLE_ZOPEN = "[HANDLE] zOpen"
_LABEL_HANDLE_ZWIZARD = "[HANDLE] zWizard"
_LABEL_HANDLE_ZREAD_STRING = "[HANDLE] zRead (string)"
_LABEL_HANDLE_ZREAD_DICT = "[HANDLE] zRead (dict)"
_LABEL_HANDLE_ZDATA_DICT = "[HANDLE] zData (dict)"
_LABEL_HANDLE_CRUD_DICT = "[HANDLE] zCRUD (dict)"
_LABEL_HANDLE_ZLOGIN = "[HANDLE] zLogin"
_LABEL_HANDLE_ZLOGOUT = "[HANDLE] zLogout"
_LABEL_PROCESS_MODIFIERS = "Process Modifiers"
_LABEL_ZBOUNCE = "zBounce (execute then back)"
_LABEL_ZREQUIRED = "zRequired"
_LABEL_ZREQUIRED_RETURN = "zRequired Return"

# ==============================================================================
# DISPLAY EVENT KEYS (Legacy zDisplay format) - INTERNAL
# ==============================================================================

_EVENT_TEXT = "text"
_EVENT_SYSMSG = "sysmsg"
_EVENT_HEADER = "header"
_EVENT_SUCCESS = "success"
_EVENT_ERROR = "error"
_EVENT_WARNING = "warning"
_EVENT_INFO = "info"
_EVENT_LINE = "line"
_EVENT_LIST = "list"

# ==============================================================================
# NAVIGATION
# ==============================================================================

NAV_ZBACK = "zBack"

# ==============================================================================
# PLUGINS
# ==============================================================================

PLUGIN_PREFIX = "&"

# ==============================================================================
# DEFAULT VALUES - INTERNAL
# ==============================================================================

_DEFAULT_ACTION_READ = "read"
_DEFAULT_ZBLOCK = "root"
_DEFAULT_CONTENT = ""
_DEFAULT_INDENT = 0
_DEFAULT_INDENT_LAUNCHER = 4
_DEFAULT_INDENT_HANDLER = 5
_DEFAULT_INDENT_PROCESS = 2
_DEFAULT_INDENT_MODIFIER = 3
_DEFAULT_STYLE_SINGLE = "single"
_DEFAULT_LABEL = ""

# ==============================================================================
# STYLES & INDENTATION - INTERNAL
# ==============================================================================

_STYLE_FULL = "full"
_STYLE_SINGLE = "single"
_STYLE_WAVY = "~"

_INDENT_ROOT = 0
_INDENT_HANDLE = 1

# ==============================================================================
# PROMPTS & INPUT - INTERNAL
# ==============================================================================

_PROMPT_REQUIRED_CONTINUE = "Try again? (press Enter to retry, 'n' or 'stop' to go back): "

# Input Values
_INPUT_N = "n"
_INPUT_STOP = "stop"

# ==============================================================================
# LOG MESSAGES - zDispatch - INTERNAL
# ==============================================================================

_LOG_PREFIX = "[zDispatch]"
_LOG_MSG_READY = f"{_LOG_PREFIX} Command dispatch subsystem ready"
_LOG_MSG_HORIZONTAL = "zHorizontal: %s"
_LOG_MSG_HANDLE_KEY = "handle zDispatch for key: %s"
_LOG_MSG_PREFIX_MODS = "Prefix modifiers: %s"
_LOG_MSG_SUFFIX_MODS = "Suffix modifiers: %s"
_LOG_MSG_DETECTED_MODS = "Detected modifiers for %s: %s"
_LOG_MSG_MODIFIER_RESULT = "Modifier evaluation result: %s"
_LOG_MSG_DISPATCH_RESULT = "dispatch result: %s"
_LOG_MSG_COMPLETED = "Modifier evaluation completed for key: %s"

# ==============================================================================
# LOG MESSAGES - Modifiers - INTERNAL
# ==============================================================================

_LOG_PREFIX_MODIFIERS = "[MODIFIERS]"
_LOG_MSG_PARSING_PREFIX = "Parsing prefix modifiers for key: %s"
_LOG_MSG_PARSING_SUFFIX = "Parsing suffix modifiers for key: %s"
_LOG_MSG_PRE_MODIFIERS = "pre_modifiers: %s"
_LOG_MSG_SUF_MODIFIERS = "suf_modifiers: %s"
_LOG_MSG_RESOLVED = "Resolved modifiers: %s on key: %s"
_LOG_MSG_MENU_DETECTED = "* Modifier detected for %s - invoking menu (anchor=%s)"
_LOG_MSG_ZBOUNCE_RESULT = "zBounce action result: %s"
_LOG_MSG_ZBOUNCE_CONTEXT = "zBounce context: %s"
_LOG_MSG_ZBOUNCE_MODE_CHECK = "zBounce mode check: context=%s, mode=%s"
_LOG_MSG_BIFROST_DETECTED = "zBifrost mode detected - returning actual result"
_LOG_MSG_REQUIRED_STEP = "Required step: %s"
_LOG_MSG_REQUIRED_RESULTS = "zRequired results: %s"
_LOG_MSG_REQUIREMENT_NOT_SATISFIED = "Requirement '%s' not satisfied. Retrying..."
_LOG_MSG_REQUIREMENT_SATISFIED = "Requirement '%s' satisfied."
_LOG_MSG_LOOKING_UP_KEY = f"{_LOG_PREFIX_MODIFIERS} Looking up key: '%s' in block_dict keys: %s"
_LOG_MSG_RESOLVED_KEY = f"{_LOG_PREFIX_MODIFIERS} Resolved ^key '%s' to horizontal value: %s"
_LOG_MSG_COULD_NOT_LOAD = "Could not load UI block %s from %s"
_LOG_MSG_NO_ZVAFILE = "No zVaFile in zspark_obj"
_LOG_MSG_CANNOT_RESOLVE = "Cannot resolve ^key without walker context"

# ==============================================================================
# ERROR MESSAGES
# ==============================================================================

ERR_NO_ZCLI = "zDispatch requires a zCLI instance"
ERR_NO_ZCLI_OR_WALKER = "handle_zDispatch requires either zcli or walker parameter"

# ==============================================================================
# PUBLIC API EXPORTS
# ==============================================================================
# Note: Only PUBLIC constants are exported. INTERNAL constants (prefixed with _)
# are implementation details and not accessible outside zDispatch subsystem.

__all__ = [
    # Subsystem Identity
    'SUBSYSTEM_NAME',
    'SUBSYSTEM_COLOR',
    
    # Command Prefixes (PUBLIC - used by parsers and external code)
    'CMD_PREFIX_ZFUNC',
    'CMD_PREFIX_ZLINK',
    'CMD_PREFIX_ZOPEN',
    'CMD_PREFIX_ZWIZARD',
    'CMD_PREFIX_ZREAD',
    
    # Dict Keys - Subsystem Commands (PUBLIC - used to build commands)
    'KEY_ZFUNC',
    'KEY_ZLINK',
    'KEY_ZDELTA',
    'KEY_ZOPEN',
    'KEY_ZWIZARD',
    'KEY_ZREAD',
    'KEY_ZDATA',
    'KEY_ZDIALOG',
    'KEY_ZDISPLAY',
    'KEY_ZLOGIN',
    'KEY_ZLOGOUT',
    
    # Dict Keys - Context & Session (PUBLIC - used by external callers)
    'KEY_ZVAFILE',
    'KEY_ZBLOCK',
    
    # Dict Keys - Data Operations (PUBLIC - used by zData consumers)
    'KEY_ACTION',
    'KEY_MODEL',
    'KEY_TABLE',
    'KEY_TABLES',
    'KEY_FIELDS',
    'KEY_VALUES',
    'KEY_FILTERS',
    'KEY_WHERE',
    'KEY_ORDER_BY',
    'KEY_LIMIT',
    'KEY_OFFSET',
    
    # Dict Keys - Display & UI (PUBLIC - used by external code)
    'KEY_CONTENT',
    'KEY_INDENT',
    'KEY_EVENT',
    'KEY_LABEL',
    'KEY_COLOR',
    'KEY_STYLE',
    'KEY_MESSAGE',
    
    # Modifiers (PUBLIC - used by external code to parse and build commands)
    'MOD_CARET',
    'MOD_TILDE',
    'MOD_ASTERISK',
    'MOD_EXCLAMATION',
    'PREFIX_MODIFIERS',
    'SUFFIX_MODIFIERS',
    'ALL_MODIFIERS',
    
    # Modes (PUBLIC - used by external code for mode detection)
    'MODE_BIFROST',
    'MODE_TERMINAL',
    'MODE_WALKER',
    
    # Navigation (PUBLIC - used by zWizard, zWalker, and navigation logic)
    'NAV_ZBACK',
    
    # Plugins (PUBLIC - used by zParser for plugin invocations)
    'PLUGIN_PREFIX',
    
    # Error Messages (PUBLIC - used by external error handlers)
    'ERR_NO_ZCLI',
    'ERR_NO_ZCLI_OR_WALKER',
]

# INTERNAL constants (not exported):
# - _MSG_READY, _MSG_HANDLE - display messages
# - _LABEL_* (17 constants) - internal display labels
# - _EVENT_* (9 constants) - legacy display event keys
# - _DEFAULT_* (10 constants) - implementation defaults
# - _STYLE_*, _INDENT_* (5 constants) - styling details
# - _PROMPT_*, _INPUT_* (3 constants) - input prompts
# - _LOG_* (32 constants) - internal logging messages
