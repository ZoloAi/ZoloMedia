# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_auth.py

"""
Authentication Commands for zCLI Three-Tier Auth System

This module provides shell commands for managing authentication in zCLI's three-tier
authentication architecture. It handles user authentication for both zSession (platform
users) and application-specific contexts (end users of apps built with zCLI).

Purpose:
    - User authentication (login, logout, status)
    - Three-tier auth integration (zSession, Application, Dual-mode)
    - Credential management and prompting
    - Session state management via zAuth subsystem
    - Mode-agnostic authentication UI (Terminal + Bifrost)

Commands:
    1. auth login [username] [password]  # Authenticate user (prompts if args missing)
    2. auth logout                       # Log out current user
    3. auth status                       # Show authentication status

Three-Tier Authentication:
    **Tier 1 - zSession Authentication:**
        Authenticates zCLI/Zolo platform users for premium features, plugins, cloud sync.
        Session stored in: session["zAuth"]["zSession"]
        
    **Tier 2 - Application Authentication:**
        Authenticates end-users of applications BUILT with zCLI. Each app maintains
        independent credentials. Multiple apps can be authenticated simultaneously.
        Session stored in: session["zAuth"]["applications"][app_name]
        
    **Tier 3 - Dual-Mode Authentication:**
        Both zSession AND application authenticated simultaneously. Example: Store owner
        using zCLI analytics (logged in as Zolo user + store owner).
        Context management: session["zAuth"]["active_context"]

Architecture:
    - Delegates all auth operations to zAuth subsystem (Week 6.5)
    - Uses zDisplay.zEvents.zAuth for all UI output (mode-agnostic)
    - Prompts for credentials if not provided as arguments
    - Validates zAuth availability before all operations
    - Returns None (UI Adapter Pattern) - all output via zDisplay
    - Uses zConfig session constants (SESSION_KEY_ZAUTH, etc.)

Constants:
    Actions: ACTION_LOGIN, ACTION_LOGOUT, ACTION_STATUS
    Error Messages: ERROR_NO_ZAUTH, ERROR_LOGIN_FAILED, ERROR_LOGOUT_FAILED
    Success Messages: MSG_LOGIN_SUCCESS, MSG_LOGOUT_SUCCESS, MSG_STATUS_SHOWN
    Usage Messages: USAGE_LOGIN, USAGE_LOGOUT, USAGE_STATUS
    Prompt Strings: PROMPT_USERNAME, PROMPT_PASSWORD, PROMPT_SERVER
    Three-Tier Constants: SESSION_KEY_ZAUTH, ZAUTH_KEY_ZSESSION, CONTEXT_*, etc.

Dependencies:
    - zAuth (Week 6.5): Three-tier authentication subsystem
    - zDisplay: Mode-agnostic UI output (Terminal + Bifrost)
    - zConfig (config_session.py): Session structure constants
    - getpass: Secure password input (hidden)

Example Usage:
    # Login with credentials
    >>> auth login myuser mypass
    [SUCCESS] Login successful
    Username: myuser
    Role: admin
    Context: zSession

    # Login with prompts
    >>> auth login
    Username: myuser
    Password: ********
    [SUCCESS] Login successful

    # Check status
    >>> auth status
    Authentication Status
    Authenticated: Yes
    Username: myuser
    Role: admin
    Context: zSession

    # Logout
    >>> auth logout
    [SUCCESS] Logout successful

Testing:
    All tests use mock login pattern (no real server required). Tests manipulate
    session structure directly following zAuth_Test.py pattern:
    
    mock_zcli.session = {
        "zMode": "Terminal",
        "zAuth": {
            "zSession": {"authenticated": False, "username": None, ...},
            "applications": {},
            "active_context": None,
            "dual_mode": False
        }
    }

Notes:
    - Credentials are never logged or displayed
    - Password input is hidden using getpass
    - All zAuth calls wrapped in try/except for robustness
    - Mode-agnostic output works in both Terminal and Bifrost modes
    - Session structure follows three-tier auth constants from zConfig

Author: zCLI Development Team
Version: 1.5.4+
Last Updated: Week 6.13
"""

# Type hints (centralized import from zCLI)
from zOS import Any, Dict, List, Optional, Tuple

# Three-tier auth constants from zConfig
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (  # pylint: disable=unused-import
    SESSION_KEY_ZAUTH,
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_APPLICATIONS,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_DUAL_MODE,
    CONTEXT_ZSESSION,
    CONTEXT_APPLICATION,
    CONTEXT_DUAL
)

# =============================================================================
# Module Constants
# =============================================================================

# Actions
ACTION_LOGIN = "login"
ACTION_LOGOUT = "logout"
ACTION_STATUS = "status"

# Error Messages
ERROR_NO_ZAUTH = "zAuth subsystem not available"
ERROR_LOGIN_FAILED = "Login failed"
ERROR_LOGOUT_FAILED = "Logout failed"
ERROR_STATUS_FAILED = "Failed to retrieve authentication status"
ERROR_UNKNOWN_ACTION = "Unknown auth action"
ERROR_INVALID_CREDENTIALS = "Invalid credentials"
ERROR_NO_USERNAME = "Username is required"
ERROR_NO_PASSWORD = "Password is required"

# Success Messages
MSG_LOGIN_SUCCESS = "Login successful"
MSG_LOGOUT_SUCCESS = "Logout successful"
MSG_STATUS_SHOWN = "Authentication status displayed"

# Usage Messages
USAGE_LOGIN = "Usage: auth login [username] [password]"
USAGE_LOGOUT = "Usage: auth logout"
USAGE_STATUS = "Usage: auth status"

# Prompt Strings
PROMPT_USERNAME = "Username"
PROMPT_PASSWORD = "Password"
PROMPT_SERVER = "Server URL (optional, press Enter to skip)"

# Display Labels
LABEL_USERNAME = "Username"
LABEL_ROLE = "Role"
LABEL_CONTEXT = "Context"
LABEL_AUTHENTICATED = "Authenticated"
LABEL_STATUS = "Status"
LABEL_APP = "Application"

# Status Values
STATUS_YES = "Yes"
STATUS_NO = "No"
STATUS_NOT_AUTHENTICATED = "Not authenticated"

# Header Strings
HEADER_AUTH_STATUS = "Authentication Status"
HEADER_LOGIN_SUCCESS = "Login Successful"


# =============================================================================
# Main Command Handler
# =============================================================================

def execute_auth(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute auth commands (login, logout, status).

    Main entry point for all authentication commands. Routes to appropriate
    handler based on action. Validates zAuth availability before delegation.

    Args:
        zcli: The zCLI instance
        parsed: Parsed command dictionary with keys:
            - action (str): The command action (login, logout, status)
            - args (List[str]): Command arguments (e.g., username, password)

    Returns:
        None (UI Adapter Pattern - uses zDisplay for all output)

    Examples:
        >>> execute_auth(zcli, {"action": "login", "args": ["user", "pass"]})
        # Logs in with provided credentials

        >>> execute_auth(zcli, {"action": "status", "args": []})
        # Shows authentication status

    Notes:
        - Validates zAuth subsystem availability
        - Routes to handler functions (_handle_login, _handle_logout, _handle_status)
        - All output via zDisplay (mode-agnostic)
        - Logs all operations via zcli.logger
    """
    action = parsed.get("action", "")
    args = parsed.get("args", [])

    zcli.logger.debug("Executing auth command: %s", action)

    # Validate zAuth availability
    if not _validate_zauth(zcli):
        return None

    # Action routing
    if action == ACTION_LOGIN:
        _handle_login(zcli, args)
    elif action == ACTION_LOGOUT:
        _handle_logout(zcli, args)
    elif action == ACTION_STATUS:
        _handle_status(zcli)
    else:
        # Unknown action
        zcli.display.error(f"{ERROR_UNKNOWN_ACTION}: {action}")
        zcli.logger.warning("Unknown auth action: %s", action)

    return None


# =============================================================================
# Action Handlers
# =============================================================================

def _handle_login(zcli: Any, args: List[str]) -> None:
    """
    Handle login command - Authenticate user.

    Authenticates user with provided credentials or prompts for them. Supports
    both command-line arguments and interactive prompting.

    Args:
        zcli: The zCLI instance
        args: Command arguments [username, password] (optional)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_login(zcli, ["myuser", "mypass"])
        # Logs in with provided credentials

        >>> _handle_login(zcli, [])
        # Prompts for username and password interactively

    Notes:
        - If username not provided, prompts for it
        - If password not provided, prompts for it (hidden input)
        - Delegates to zcli.auth.login()
        - Displays success via zDisplay on successful login
        - Displays error via zDisplay on failed login
        - Logs operation via zcli.logger
    """
    try:
        # Get or prompt for credentials
        if len(args) >= 2:
            username = args[0]
            password = args[1]
        else:
            username, password = _prompt_credentials(zcli, args)

        if not username:
            zcli.display.error(ERROR_NO_USERNAME)
            zcli.logger.warning("Login attempted without username")
            return None

        if not password:
            zcli.display.error(ERROR_NO_PASSWORD)
            zcli.logger.warning("Login attempted without password")
            return None

        zcli.logger.info("Attempting login for user: %s", username)

        # Delegate to zAuth subsystem
        # Note: zAuth.login() handles display internally via zDisplay.zEvents.zAuth
        result = zcli.auth.login(username, password)

        # Log result (zAuth already displayed to user)
        if result and result.get("success", False):
            zcli.logger.info("Login successful for user: %s", username)
        else:
            zcli.logger.warning("Login failed for user: %s", username)

    except Exception as e:
        zcli.display.error(f"{ERROR_LOGIN_FAILED}: {e}")
        zcli.logger.error("Login error: %s", e)

    return None


def _handle_logout(zcli: Any, args: List[str]) -> None:  # pylint: disable=unused-argument
    """
    Handle logout command - Log out current user.

    Logs out the current authenticated user and clears session state.

    Args:
        zcli: The zCLI instance
        args: Command arguments (unused, for signature consistency)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_logout(zcli, [])
        [SUCCESS] Logout successful

    Notes:
        - Delegates to zcli.auth.logout()
        - Clears session authentication state
        - Displays success/error via zDisplay
        - zAuth.logout() handles display internally via zDisplay.zEvents.zAuth
        - Logs operation via zcli.logger
    """
    try:
        zcli.logger.info("Attempting logout")

        # Delegate to zAuth subsystem
        # Note: zAuth.logout() handles display internally via zDisplay.zEvents.zAuth
        result = zcli.auth.logout()

        # Log result (zAuth already displayed to user)
        if result and result.get("success", False):
            zcli.logger.info("Logout successful")
        else:
            zcli.logger.warning("Logout completed with warnings")

    except Exception as e:
        zcli.display.error(f"{ERROR_LOGOUT_FAILED}: {e}")
        zcli.logger.error("Logout error: %s", e)

    return None


def _handle_status(zcli: Any) -> None:
    """
    Handle status command - Display authentication status.

    Shows current authentication status including username, role, context,
    and authentication state for all three tiers.

    Args:
        zcli: The zCLI instance

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_status(zcli)
        Authentication Status
        Authenticated: Yes
        Username: myuser
        Role: admin
        Context: zSession

    Notes:
        - Delegates to zcli.auth.status()
        - Displays three-tier auth status (zSession, applications, dual-mode)
        - Shows active context and authenticated apps
        - zAuth.status() handles display internally via zDisplay.zEvents.zAuth
        - Logs operation via zcli.logger
    """
    try:
        zcli.logger.debug("Retrieving authentication status")

        # Delegate to zAuth subsystem
        # Note: zAuth.status() handles display internally via zDisplay.zEvents.zAuth
        result = zcli.auth.status()

        # Log result (zAuth already displayed to user)
        if result:
            zcli.logger.debug("Authentication status retrieved successfully")
        else:
            zcli.logger.warning("Authentication status retrieval returned empty result")

    except Exception as e:
        zcli.display.error(f"{ERROR_STATUS_FAILED}: {e}")
        zcli.logger.error("Status error: %s", e)

    return None


# =============================================================================
# Helper Functions
# =============================================================================

def _validate_zauth(zcli: Any) -> bool:
    """
    Validate that zAuth subsystem is available.

    Checks if zcli.auth exists and is properly initialized before attempting
    any authentication operations.

    Args:
        zcli: The zCLI instance

    Returns:
        bool: True if zAuth is available, False otherwise

    Examples:
        >>> _validate_zauth(zcli)
        True  # zAuth is available

        >>> _validate_zauth(zcli_without_auth)
        False  # zAuth not available
        # Displays error: "zAuth subsystem not available"

    Notes:
        - Displays error via zDisplay if zAuth not available
        - Logs error via zcli.logger
        - Returns False to signal caller to abort operation
    """
    if not hasattr(zcli, 'auth') or zcli.auth is None:
        zcli.display.error(ERROR_NO_ZAUTH)
        zcli.logger.error("zAuth subsystem not available")
        return False

    return True


def _prompt_credentials(zcli: Any, args: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Prompt for username and password if not provided.

    Interactively prompts user for credentials using zDisplay for username
    and getpass for password (hidden input).

    Args:
        zcli: The zCLI instance
        args: Command arguments (may contain username as args[0])

    Returns:
        Tuple[Optional[str], Optional[str]]: (username, password)

    Examples:
        >>> _prompt_credentials(zcli, [])
        Username: myuser
        Password: ********
        ("myuser", "mypass")

        >>> _prompt_credentials(zcli, ["myuser"])
        Password: ********
        ("myuser", "mypass")

    Notes:
        - Uses input() for username (visible)
        - Uses getpass.getpass() for password (hidden)
        - Returns None for username/password if prompt cancelled (Ctrl+C)
        - Handles EOFError (piped input) and KeyboardInterrupt (Ctrl+C)
    """
    import getpass

    username = args[0] if len(args) >= 1 else None
    password = None

    try:
        # Prompt for username if not provided
        if not username:
            username = input(f"{PROMPT_USERNAME}: ").strip()

        # Prompt for password (always prompt, never provided as plain arg for security)
        if username:
            password = getpass.getpass(f"{PROMPT_PASSWORD}: ")

    except (EOFError, KeyboardInterrupt):
        # User cancelled input (Ctrl+C or Ctrl+D)
        zcli.logger.debug("Credential prompt cancelled by user")
        return None, None
    except Exception as e:
        zcli.logger.error("Error prompting for credentials: %s", e)
        return None, None

    return username, password
