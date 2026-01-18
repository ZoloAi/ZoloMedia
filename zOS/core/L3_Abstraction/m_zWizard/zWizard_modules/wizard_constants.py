# zCLI/L3_Abstraction/m_zWizard/zWizard_modules/wizard_constants.py

"""
Centralized constants for the zWizard subsystem.

This module contains all constants used by the zWizard looper and its supporting
modules (RBAC, transactions, interpolation, exceptions, WizardHat).

Constants are organized into PUBLIC (exported API) and INTERNAL (implementation
details) sections.

PUBLIC Constants:
    - Subsystem metadata (SUBSYSTEM_NAME, SUBSYSTEM_COLOR)
    - Navigation signals (NAVIGATION_SIGNALS tuple)
    - RBAC access results (RBAC_ACCESS_*)

INTERNAL Constants:
    - Display messages (prefixed with _MSG_)
    - Log messages (prefixed with _LOG_MSG_)
    - Error messages (prefixed with _ERR_)
    - RBAC keys (prefixed with _RBAC_)
    - Transaction keys (prefixed with _TRANS_)
    - Interpolation patterns (prefixed with _INTERP_)
    - Context keys (prefixed with _CONTEXT_KEY_)
    - Callback keys (prefixed with _CALLBACK_)
    - Display styles and colors
    - Indent levels

Usage:
    >>> from zOS.L3_Abstraction.m_zWizard.zWizard_modules import SUBSYSTEM_NAME
    >>> from zOS.L3_Abstraction.m_zWizard.zWizard_modules.wizard_constants import _MSG_READY
"""

# Import dependencies
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_WIZARD_MODE

# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC CONSTANTS (API)
# ═══════════════════════════════════════════════════════════════════════════

# Subsystem Identity
SUBSYSTEM_NAME: str = "zWizard"
SUBSYSTEM_COLOR: str = "ZWIZARD"

# Navigation Signals (Public API - tuple for external checking)
_SIGNAL_ZBACK: str = "zBack"
_SIGNAL_EXIT: str = "exit"
_SIGNAL_STOP: str = "stop"
_SIGNAL_ERROR: str = "error"
_SIGNAL_EMPTY: str = ""
NAVIGATION_SIGNALS: tuple = (_SIGNAL_ZBACK, _SIGNAL_EXIT, _SIGNAL_STOP, _SIGNAL_ERROR, _SIGNAL_EMPTY)

# RBAC Access Results (Public API)
RBAC_ACCESS_GRANTED: str = "access_granted"
RBAC_ACCESS_DENIED: str = "access_denied"
RBAC_ACCESS_DENIED_ZGUEST: str = "access_denied_zguest"  # Friendly redirect (no pause needed)


# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL CONSTANTS (Implementation Details)
# ═══════════════════════════════════════════════════════════════════════════

# ------------------------------------------------------------------------------
# zWizard Main Facade Constants
# ------------------------------------------------------------------------------

# Subsystem Identity (Internal)
_MSG_READY: str = "zWizard Ready"

# Context Keys
_CONTEXT_KEY_WIZARD_MODE: str = SESSION_KEY_WIZARD_MODE  # Use zConfig constant
_CONTEXT_KEY_SCHEMA_CACHE: str = "schema_cache"
_CONTEXT_KEY_ZHAT: str = "zHat"

# Navigation Callback Keys
_CALLBACK_ON_BACK: str = "on_back"
_CALLBACK_ON_EXIT: str = "on_exit"
_CALLBACK_ON_STOP: str = "on_stop"
_CALLBACK_ON_ERROR: str = "on_error"

# Display Messages
_MSG_HANDLE_WIZARD: str = "Handle zWizard"
_MSG_WIZARD_STEP: str = "zWizard step: %s"
_MSG_ZKEY_DISPLAY: str = "zKey: %s"
_MSG_DISPATCH_ERROR: str = "Dispatch error for: %s"

# Display Styles
_STYLE_FULL: str = "full"
_STYLE_SINGLE: str = "single"
_COLOR_MAIN: str = "MAIN"
_COLOR_ERROR: str = "ERROR"

# Log Messages
_LOG_MSG_PROCESSING_KEY: str = "Processing key: %s"
_LOG_MSG_MENU_SELECTED: str = "Menu selected key: %s - jumping to it"
_LOG_MSG_DISPATCH_ERROR: str = "Error for key '%s': %s"

# Display Indentation Levels
_INDENT_LEVEL_0: int = 0
_INDENT_LEVEL_1: int = 1
_INDENT_LEVEL_2: int = 2

# ------------------------------------------------------------------------------
# wizard_rbac.py Constants
# ------------------------------------------------------------------------------

# RBAC Keys
_RBAC_KEY: str = "zRBAC"
_RBAC_REQUIRE_AUTH: str = "require_auth"
_RBAC_REQUIRE_ROLE: str = "require_role"
_RBAC_REQUIRE_PERMISSION: str = "require_permission"
_RBAC_ZGUEST: str = "zGuest"  # Guest-only access (unauthenticated users)

# RBAC Log Messages
_LOG_MSG_NO_AUTH_SUBSYSTEM: str = "[RBAC] No auth subsystem available, denying access"
_LOG_MSG_ACCESS_GRANTED: str = "[RBAC] Access granted for %s"
_LOG_MSG_ACCESS_DENIED: str = "[RBAC] Access denied for '%s': %s"

# RBAC Display Messages
_MSG_AUTH_REQUIRED: str = "Authentication required"
_MSG_ROLE_REQUIRED: str = "Role required: %s"
_MSG_PERMISSION_REQUIRED: str = "Permission required: %s"
_MSG_ZGUEST_ONLY: str = "You're already logged in!"
_MSG_ZGUEST_REDIRECT: str = "This page is for guests only. Redirecting..."
_MSG_ACCESS_DENIED_HEADER: str = "[ACCESS DENIED] %s"
_MSG_DENIAL_REASON: str = "Reason: %s"
_MSG_DENIAL_TIP: str = "Tip: Check your role/permissions or log in"

# RBAC Display Event Types
_EVENT_TEXT: str = "text"
_EVENT_ERROR: str = "error"

# RBAC Display Event Keys
_KEY_EVENT: str = "event"
_KEY_CONTENT: str = "content"
_KEY_INDENT: str = "indent"
_KEY_BREAK_AFTER: str = "break_after"

# RBAC Indentation Levels (for display)
# Note: zWizard also has _INDENT_LEVEL_* constants for its own use
# These are duplicates but kept for wizard_rbac.py compatibility

# RBAC Formatting
_FORMAT_ONE_OF: str = "one of %s"

# RBAC Display Styling
_RBAC_ERROR_COLOR: str = "ERROR"
_RBAC_INDENT_LEVEL: int = 1

# ------------------------------------------------------------------------------
# wizard_exceptions.py Constants
# ------------------------------------------------------------------------------

# Public Error Messages (used by zWizard.py)
ERR_MISSING_INSTANCE: str = "zWizard requires either zcli or walker instance"

# Initialization Errors (Internal)
_ERR_MISSING_DISPLAY: str = "Display subsystem required but not available"
_ERR_MISSING_LOGGER: str = "Logger instance required but not available"
_ERR_INVALID_CONFIG: str = "Invalid wizard configuration: %s"

# Execution Errors
_ERR_STEP_FAILED: str = "Step '%s' failed: %s"
_ERR_DISPATCH_FAILED: str = "Failed to dispatch step '%s': %s"
_ERR_INVALID_STEP: str = "Invalid step structure for key '%s': %s"
_ERR_TRANSACTION_FAILED: str = "Transaction failed for '%s': %s"

# RBAC Errors
_ERR_NOT_AUTHENTICATED: str = "Authentication required for '%s'"
_ERR_MISSING_ROLE: str = "Role required for '%s': %s"
_ERR_MISSING_PERMISSION: str = "Permission required for '%s': %s"
_ERR_ACCESS_DENIED: str = "Access denied for '%s': %s"

# ------------------------------------------------------------------------------
# wizard_transactions.py Constants
# ------------------------------------------------------------------------------

# Transaction Log Messages
_LOG_TXN_ENABLED: str = "[TXN] Transaction mode enabled for $%s"
_LOG_TXN_COMMITTED: str = "[OK] Transaction committed for $%s"
_LOG_TXN_ROLLBACK: str = "[ERROR] Error in zWizard, rolling back transaction for $%s: %s"

# Dictionary Keys
_KEY_ZDATA: str = "zData"
_KEY_MODEL: str = "model"

# Model Prefix
_PREFIX_TXN_MODEL: str = "$"
_PREFIX_INDEX: int = 1  # Index to strip $ prefix

# ------------------------------------------------------------------------------
# wizard_interpolation.py Constants
# ------------------------------------------------------------------------------

# Interpolation Pattern
# Matches: zHat[numeric] OR zHat["key"] OR zHat['key'] OR zHat[key]
_ZHAT_PATTERN: str = r"zHat\[(['\"]?\w+['\"]?)\]"

# Fallback Values
_ZHAT_FALLBACK: str = "None"

# Log Messages
_LOG_MSG_KEY_NOT_FOUND: str = "zHat key not found during interpolation: %s"

# String Processing
_STR_QUOTE_CHARS: str = "'\""

# ------------------------------------------------------------------------------
# wizard_hat.py Constants
# ------------------------------------------------------------------------------

# Error Messages
_ERR_KEY_NOT_FOUND: str = "zHat key not found: %s"
_ERR_INVALID_KEY_TYPE: str = "Invalid zHat key type: %s"

# Container Keys
_PRIVATE_LIST_KEY: str = "_list"
_PRIVATE_DICT_KEY: str = "_dict"


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Public API Constants
    'SUBSYSTEM_NAME',
    'SUBSYSTEM_COLOR',
    'NAVIGATION_SIGNALS',
    'RBAC_ACCESS_GRANTED',
    'RBAC_ACCESS_DENIED',
    'RBAC_ACCESS_DENIED_ZGUEST',
    'ERR_MISSING_INSTANCE',
]
