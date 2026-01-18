# zCLI/L2_Core/k_zOpen/open_modules/open_constants.py

"""
Constants for zOpen subsystem.

This module centralizes all constants used across the zOpen subsystem,
including path symbols, file extensions, error messages, log messages, and
configuration values.

Organization:
    - Command/Request Keys: zOpen command structure
    - zPath Symbols: zPath notation (@, ~, separators)
    - URL Schemes: HTTP/HTTPS schemes and prefixes
    - File Extensions: Supported file types
    - Return Values: Success/failure return codes
    - Machine Keys: Configuration keys for IDE/browser
    - IDE/Browser Configuration: Available editors and browsers
    - File Actions: User action choices
    - Colors: Display colors
    - Styles: Display styling
    - Indentation: Display indentation levels
    - Messages: User-facing success messages
    - Error Messages: Error and failure messages
    - Log Messages: Debug and info logging
    - Configuration: File handling, truncation, encoding

Layer Position:
    Layer 2, Position 11 (zOpen - Constants Module)
"""

from zOS import Any

# ============================================================================
# COMMAND/REQUEST KEYS (PUBLIC)
# ============================================================================

DICT_KEY_ZOPEN: str = "zOpen"
DICT_KEY_PATH: str = "path"
DICT_KEY_ON_SUCCESS: str = "onSuccess"
DICT_KEY_ON_FAIL: str = "onFail"


# ============================================================================
# ZPATH SYMBOLS (PUBLIC)
# ============================================================================

ZPATH_SYMBOL_WORKSPACE: str = "@"  # Workspace-relative path
ZPATH_SYMBOL_ABSOLUTE: str = "~"   # Absolute path from root
ZPATH_SEPARATOR: str = "."          # zPath component separator


# ============================================================================
# URL SCHEMES & PREFIXES (PUBLIC)
# ============================================================================

URL_SCHEME_HTTP: str = "http"
URL_SCHEME_HTTPS: str = "https"
URL_SCHEMES_SUPPORTED: tuple = (URL_SCHEME_HTTP, URL_SCHEME_HTTPS)
URL_PREFIX_WWW: str = "www."
URL_SCHEME_HTTPS_DEFAULT: str = "https://"


# ============================================================================
# FILE EXTENSIONS (PUBLIC)
# ============================================================================

EXTENSIONS_HTML: tuple = ('.html', '.htm')
EXTENSIONS_TEXT: tuple = ('.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml')


# ============================================================================
# RETURN VALUES (PUBLIC)
# ============================================================================

RETURN_ZBACK: str = "zBack"    # Success, return to previous screen
RETURN_STOP: str = "stop"       # Failure, stop execution


# ============================================================================
# MACHINE CONFIGURATION KEYS (PUBLIC)
# ============================================================================

ZMACHINE_KEY_IDE: str = "ide"
ZMACHINE_KEY_BROWSER: str = "browser"


# ============================================================================
# IDE/BROWSER CONFIGURATION (INTERNAL)
# ============================================================================

_DEFAULT_IDE: str = "nano"
_IDE_UNKNOWN: str = "unknown"
_AVAILABLE_IDES: list = ["cursor", "code", "nano", "vim"]
_BROWSERS_SKIP: tuple = ("unknown",)


# ============================================================================
# FILE ACTIONS (INTERNAL)
# ============================================================================

_FILE_ACTION_CREATE: str = "Create file"
_FILE_ACTION_CANCEL: str = "Cancel"
_FILE_ACTIONS: list = [_FILE_ACTION_CREATE, _FILE_ACTION_CANCEL]


# ============================================================================
# COLORS (PUBLIC - Display Integration)
# ============================================================================

COLOR_ZOPEN: str = "ZOPEN"
COLOR_SUCCESS: str = "GREEN"
COLOR_ERROR: str = "RED"
COLOR_INFO: str = "INFO"


# ============================================================================
# STYLES (INTERNAL)
# ============================================================================

_STYLE_FULL: str = "full"
_STYLE_SINGLE: str = "single"
_STYLE_SECTION: str = "~"


# ============================================================================
# INDENTATION LEVELS (INTERNAL)
# ============================================================================

_INDENT_INIT: int = 0
_INDENT_HANDLE: int = 1
_INDENT_HOOK: int = 2
_INDENT_FILE_INFO: int = 1
_INDENT_URL_INFO: int = 1


# ============================================================================
# ZPATH CONFIGURATION (INTERNAL)
# ============================================================================

_ZPATH_MIN_PARTS: int = 2


# ============================================================================
# FILE HANDLING CONFIGURATION (INTERNAL)
# ============================================================================

_CONTENT_TRUNCATE_LIMIT: int = 1000  # Characters to show before truncation
_FILE_ENCODING: str = 'utf-8'


# ============================================================================
# OPERATING SYSTEM (INTERNAL)
# ============================================================================

_OS_WINDOWS: str = 'nt'


# ============================================================================
# DIALOG FIELDS (INTERNAL)
# ============================================================================

_DIALOG_FIELD_ACTION: str = "action"
_DIALOG_FIELD_IDE: str = "ide"


# ============================================================================
# MESSAGES - SUCCESS (INTERNAL)
# ============================================================================

_MSG_ZOPEN_READY: str = "zOpen Ready"
_MSG_HANDLE_ZOPEN: str = "Handle zOpen"
_MSG_HOOK_SUCCESS: str = "[HOOK] onSuccess"
_MSG_HOOK_FAIL: str = "[HOOK] onFail"
_MSG_CREATED_FILE: str = "Created {path}"
_MSG_OPENED_BROWSER: str = "Opened {filename} in browser"
_MSG_OPENED_BROWSER_URL: str = "Opened URL in {browser}"
_MSG_OPENED_DEFAULT: str = "Opened URL in default browser"
_MSG_OPENED_IDE: str = "Opened {filename} in {ide}"
_MSG_FILE_CONTENT_TITLE: str = "File Content: {filename}"
_MSG_CONTENT_TRUNCATED: str = "\n[Content truncated - showing first {limit} of {total} characters]"
_MSG_URL_INFO_TITLE: str = "URL Information"
_MSG_URL_MANUAL: str = "Unable to open in browser. Please copy and paste into your browser."
_MSG_UNSUPPORTED_TYPE: str = "Unsupported file type: {ext}"


# ============================================================================
# MESSAGES - FAILURE (INTERNAL)
# ============================================================================

_MSG_BROWSER_FAILED: str = "Browser failed to open HTML file"
_MSG_BROWSER_FAILED_URL: str = "Browser failed to open URL"
_MSG_BROWSER_ERROR: str = "Browser error: {error}"
_MSG_FAILED_IDE: str = "Failed to open with {ide}: {error}"


# ============================================================================
# ERROR MESSAGES - zPath Resolution (INTERNAL)
# ============================================================================

_ERR_NO_WORKSPACE: str = "No workspace set for relative path"
_ERR_INVALID_ZPATH: str = "Invalid zPath format"
_ERR_RESOLUTION_FAILED: str = "Failed to resolve zPath"


# ============================================================================
# ERROR MESSAGES - File Operations (INTERNAL)
# ============================================================================

_ERR_FILE_NOT_FOUND: str = "File not found: %s"
_ERR_DIALOG_FAILED: str = "Dialog fallback failed: %s"
_ERR_READ_FAILED: str = "Failed to read file: %s"
_ERR_UNSUPPORTED_TYPE: str = "Unsupported file type: %s"


# ============================================================================
# ERROR MESSAGES - Browser Operations (INTERNAL)
# ============================================================================

_ERR_BROWSER_FAILED: str = "Browser failed to open HTML file"
_ERR_BROWSER_FAILED_URL: str = "Browser failed to open URL"
_ERR_BROWSER_ERROR: str = "Browser error: %s"
_ERR_URL_OPEN_FAILED: str = "Unable to open URL. Displaying information instead."


# ============================================================================
# ERROR MESSAGES - IDE Operations (INTERNAL)
# ============================================================================

_ERR_IDE_FAILED: str = "Failed to open with IDE %s: %s"


# ============================================================================
# LOG MESSAGES - zOpen Handler (INTERNAL)
# ============================================================================

_LOG_INCOMING_REQUEST: str = "Incoming zOpen request: %s"
_LOG_PARSED_PATH: str = "Parsed path: %s"
_LOG_EXEC_SUCCESS_HOOK: str = "Executing onSuccess hook: %s"
_LOG_EXEC_FAIL_HOOK: str = "Executing onFail hook: %s"


# ============================================================================
# LOG MESSAGES - zPath Resolution (INTERNAL)
# ============================================================================

_LOG_RESOLVING_ZPATH: str = "Resolving zPath: %s"
_LOG_RESOLVED_SUCCESS: str = "Resolved zPath '%s' to: %s"
_LOG_INVALID_FORMAT: str = "Invalid zPath format: %s"
_LOG_WORKSPACE_MISSING: str = "Workspace context missing for path: %s"


# ============================================================================
# LOG MESSAGES - File Operations (INTERNAL)
# ============================================================================

_LOG_RESOLVED_PATH: str = "Resolved path: %s"
_LOG_FILE_NOT_FOUND: str = "File not found: %s"
_LOG_PROMPTING_USER: str = "Prompting user for action on missing file"
_LOG_CREATED_FILE: str = "Created file: %s"
_LOG_OPENING_HTML: str = "Opening HTML file: %s"
_LOG_SUCCESS_HTML: str = "Successfully opened HTML file in browser"
_LOG_OPENING_TEXT: str = "Opening text file: %s"
_LOG_USING_IDE: str = "Using IDE: %s"
_LOG_SUCCESS_IDE: str = "Successfully opened file with %s"
_LOG_IDE_SELECTION_FAILED: str = "IDE selection dialog failed: %s"
_LOG_DISPLAYING_CONTENT: str = "Displaying text file content"


# ============================================================================
# LOG MESSAGES - URL Operations (INTERNAL)
# ============================================================================

_LOG_OPENING_URL: str = "Opening URL: %s"
_LOG_USING_BROWSER: str = "Using browser: %s"
_LOG_SUCCESS_SPECIFIC: str = "Successfully opened URL in %s"
_LOG_SUCCESS_DEFAULT: str = "Successfully opened URL in system default browser"
_LOG_BROWSER_FAILED: str = "Browser failed to open URL"
_LOG_BROWSER_ERROR: str = "Browser error: %s"


# ============================================================================
# COMMAND PREFIX (INTERNAL)
# ============================================================================

_CMD_PREFIX: str = "zOpen("


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Command/Request Keys (PUBLIC)
    "DICT_KEY_ZOPEN",
    "DICT_KEY_PATH",
    "DICT_KEY_ON_SUCCESS",
    "DICT_KEY_ON_FAIL",
    
    # zPath Symbols (PUBLIC)
    "ZPATH_SYMBOL_WORKSPACE",
    "ZPATH_SYMBOL_ABSOLUTE",
    "ZPATH_SEPARATOR",
    
    # URL Schemes (PUBLIC)
    "URL_SCHEME_HTTP",
    "URL_SCHEME_HTTPS",
    "URL_SCHEMES_SUPPORTED",
    "URL_PREFIX_WWW",
    "URL_SCHEME_HTTPS_DEFAULT",
    
    # File Extensions (PUBLIC)
    "EXTENSIONS_HTML",
    "EXTENSIONS_TEXT",
    
    # Return Values (PUBLIC)
    "RETURN_ZBACK",
    "RETURN_STOP",
    
    # Machine Keys (PUBLIC)
    "ZMACHINE_KEY_IDE",
    "ZMACHINE_KEY_BROWSER",
    
    # Colors (PUBLIC - Display Integration)
    "COLOR_ZOPEN",
    "COLOR_SUCCESS",
    "COLOR_ERROR",
    "COLOR_INFO",
]
