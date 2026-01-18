# zCLI/L2_Core/j_zDialog/dialog_modules/dialog_constants.py

"""
Constants for zDialog subsystem.

This module centralizes all constants used across the zDialog subsystem,
including keys, colors, error messages, log messages, and configuration values.

Organization:
    - Colors: Display and theming constants
    - Session Keys: Session storage keys
    - Data Keys: Dictionary keys for dialog data structures
    - Commands: Dispatch and operation commands
    - Events: Event type identifiers
    - Placeholders: Template placeholders
    - Separators: String parsing characters
    - Regular Expressions: Pattern matching
    - Configuration: Parsing and validation settings
    - Styles: Display styling constants
    - Indentation: Display indentation levels
    - Messages: User-facing messages
    - Log Messages: Debug and info logging
    - Error Messages: Error and warning messages

Layer Position:
    Layer 2, Position 10 (zDialog - Constants Module)
"""

from zOS import Any

# ============================================================================
# COLORS
# ============================================================================

COLOR_ZDIALOG: str = "ZDIALOG"
COLOR_DISPATCH: str = "DISPATCH"


# ============================================================================
# SESSION KEYS
# ============================================================================

_SESSION_VALUE_ZBIFROST: str = "zBifrost"


# ============================================================================
# DATA KEYS
# ============================================================================

KEY_ZDIALOG: str = "zDialog"
KEY_TITLE: str = "title"
KEY_MODEL: str = "model"
KEY_FIELDS: str = "fields"
KEY_ONSUBMIT: str = "onSubmit"
KEY_WEBSOCKET_DATA: str = "websocket_data"
KEY_DATA: str = "data"
KEY_ZCONV: str = "zConv"
KEY_ZCRUD: str = "zCRUD"
KEY_ZDATA: str = "zData"


# ============================================================================
# COMMANDS
# ============================================================================

_DISPATCH_CMD_SUBMIT: str = "submit"


# ============================================================================
# EVENTS
# ============================================================================

_EVENT_VALIDATION_ERROR: str = "validation_error"


# ============================================================================
# PLACEHOLDERS
# ============================================================================

_PLACEHOLDER_PREFIX: str = "zConv"
_PLACEHOLDER_FULL: str = "zConv"


# ============================================================================
# SEPARATORS & PARSING CHARACTERS
# ============================================================================

_SCHEMA_PATH_SEPARATOR: str = "."
_DOT_SEPARATOR: str = "."
_BRACKET_OPEN: str = "["
_BRACKET_CLOSE: str = "]"
_QUOTE_CHARS: str = "'\""


# ============================================================================
# REGULAR EXPRESSIONS
# ============================================================================

_REGEX_ZCONV_DOT_NOTATION: str = r'zConv\.(\w+)'  # noqa: W605


# ============================================================================
# CONFIGURATION
# ============================================================================

_EXPECTED_DOT_NOTATION_PARTS: int = 2


# ============================================================================
# STYLES
# ============================================================================

_STYLE_SINGLE: str = "single"
_STYLE_TILDE: str = "~"


# ============================================================================
# INDENTATION
# ============================================================================

_INDENT_DIALOG: int = 2
_INDENT_SUBMIT: int = 3


# ============================================================================
# MESSAGES
# ============================================================================

_MSG_ZDIALOG_READY: str = "zDialog Ready"
_MSG_ZDIALOG: str = "zDialog"
_MSG_ZDIALOG_RETURN_VALIDATION_FAILED: str = "zDialog Return (validation failed)"


# ============================================================================
# LOG MESSAGES - DEBUG
# ============================================================================

_DEBUG_SUBMIT_EXPR: str = "zSubmit_expr: %s"
_DEBUG_CONTEXT_KEYS: str = "zContext keys: %s | zConv: %s"
_DEBUG_DICT_PAYLOAD: str = "zSubmit detected dict payload; preparing for zLaunch"
_DEBUG_SUBMIT_RESULT: str = "zSubmit result: %s"
_DEBUG_CONTEXT_CREATED: str = "Created dialog context: %s"


# ============================================================================
# LOG MESSAGES - INFO
# ============================================================================

_INFO_DISPATCH_DICT: str = "Dispatching dict onSubmit via zDispatch: %s"


# ============================================================================
# LOG MESSAGES - DIALOG FLOW
# ============================================================================

_LOG_RECEIVED_ZHORIZONTAL: str = "\nReceived zHorizontal: %s"
_LOG_MODEL_FIELDS_SUBMIT: str = "\n   |-- model: %s\n   |-- fields: %s\n   |-- on_submit: %s"
_LOG_ZCONTEXT: str = "\nzContext: %s"
_LOG_WEBSOCKET_DATA: str = "Using pre-provided data from WebSocket: %s"


# ============================================================================
# LOG MESSAGES - AUTO-VALIDATION
# ============================================================================

_LOG_AUTO_VALIDATION_ENABLED: str = "Auto-validation enabled (model: %s)"
_LOG_AUTO_VALIDATION_FAILED: str = "Auto-validation failed with %d error(s)"
_LOG_AUTO_VALIDATION_PASSED: str = "[OK] Auto-validation passed for %s"
_LOG_AUTO_VALIDATION_ERROR: str = "Auto-validation error (proceeding anyway): %s"
_LOG_AUTO_VALIDATION_SKIPPED_PREFIX: str = "Auto-validation skipped (model doesn't start with '@'): %s"
_LOG_AUTO_VALIDATION_SKIPPED_NO_MODEL: str = "Auto-validation skipped (no model specified)"


# ============================================================================
# LOG MESSAGES - SUBMIT HANDLING
# ============================================================================

_LOG_ONSUBMIT_EXECUTE: str = "Found onSubmit => Executing via handle_submit()"
_LOG_ONSUBMIT_FAILED: str = "zDialog onSubmit failed: %s"
_LOG_WEBSOCKET_BROADCAST_FAILED: str = "Failed to broadcast validation errors via WebSocket: %s"


# ============================================================================
# ERROR MESSAGES - INITIALIZATION
# ============================================================================

_ERROR_NO_ZCLI: str = "zDialog requires a zCLI instance"
_ERROR_INVALID_ZCLI: str = "Invalid zCLI instance: missing 'session' attribute"


# ============================================================================
# ERROR MESSAGES - VALIDATION & TYPE CHECKING
# ============================================================================

_ERROR_INVALID_TYPE_DIALOG: str = "Unsupported zDialog expression type: {type_name}"
_ERROR_INVALID_TYPE_SUBMIT: str = "zSubmit expression must be a dict, got: %s"


# ============================================================================
# ERROR MESSAGES - REQUIREMENTS
# ============================================================================

_ERROR_NO_ZCLI_OR_WALKER: str = "handle_zDialog requires either zcli or walker with zcli attribute"
_ERROR_NO_WALKER: str = "handle_submit requires a walker instance"


# ============================================================================
# ERROR MESSAGES - OPERATION FAILURES
# ============================================================================

_ERROR_DISPATCH_FAILED: str = "zDispatch failed for submission: %s"
_ERROR_PARSE_PLACEHOLDER_FAILED: str = "Failed to parse placeholder '%s': %s"
_ERROR_PARSE_EMBEDDED_FAILED: str = "Failed to parse placeholder in '%s': %s"


# ============================================================================
# WARNING MESSAGES
# ============================================================================

_WARNING_FIELD_NOT_FOUND: str = "Field '%s' not found in zConv data"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Colors (PUBLIC)
    "COLOR_ZDIALOG",
    "COLOR_DISPATCH",
    
    # Data Keys (PUBLIC)
    "KEY_ZDIALOG",
    "KEY_TITLE",
    "KEY_MODEL",
    "KEY_FIELDS",
    "KEY_ONSUBMIT",
    "KEY_WEBSOCKET_DATA",
    "KEY_DATA",
    "KEY_ZCONV",
    "KEY_ZCRUD",
    "KEY_ZDATA",
]
