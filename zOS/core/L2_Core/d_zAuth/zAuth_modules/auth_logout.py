# zCLI/subsystems/zAuth/zAuth_modules/auth_logout.py
"""
Built-in zLogout Action - Declarative Logout (v1.6.0+)

═══════════════════════════════════════════════════════════════════════════════
OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

This module provides a built-in zLogout action for declarative logout
without requiring application-specific plugin code. It's the sister action
of zLogin and handles session cleanup and context switching.

Key Features:
    - Session cleanup: Removes app from session[zAuth][applications]
    - Context switching: Auto-switches to zSession if available, otherwise anonymous
    - Cache invalidation: Regenerates session_hash for frontend updates
    - Dual-mode aware: Handles transitions between contexts
    - Declarative: Works in both Terminal and Bifrost modes

Usage:
    # In zUI.logout.yaml
    Logout_Action!:
        - zLogout: "zCloud"  # App name to logout from

    Session Changes:
    Before:
        session[zAuth][applications] = {
            "zCloud": { authenticated: True, ... }
        }
        session[zAuth][active_context] = "application"
        session[zAuth][active_app] = "zCloud"
    
    After:
        session[zAuth][applications] = {}  # zCloud removed
        session[zAuth][active_context] = None  # Or "zsession" if available
        session[zAuth][active_app] = None

═══════════════════════════════════════════════════════════════════════════════
"""

from zOS import Any, Dict
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    SESSION_KEY_ZAUTH,
    SESSION_KEY_ZMODE,
    ZMODE_ZBIFROST,
    ZAUTH_KEY_APPLICATIONS,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_ACTIVE_APP,
    ZAUTH_KEY_DUAL_MODE,
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_AUTHENTICATED,
    CONTEXT_APPLICATION,
    CONTEXT_ZSESSION,
    CONTEXT_DUAL
)
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SessionConfig

# Constants
LOG_PREFIX = "[zLogout]"


def handle_zLogout(
    app_name: str,
    zConv: Dict[str, Any],
    zContext: Dict[str, Any],
    zcli: Any
) -> Dict[str, Any]:
    """
    Built-in zLogout handler - clears app session and switches context.
    
    This is the sister action of zLogin. It removes the specified app from
    the authenticated apps list and automatically switches to the appropriate
    context (zSession if available, otherwise anonymous).
    
    Args:
        app_name: Application name to logout from (e.g., "zCloud")
        zConv: Form data (not used for logout, but required for consistency)
        zContext: Dialog context (not used for logout, but required for consistency)
        zcli: zCLI instance (provides session, logger access)
    
    Returns:
        Dict[str, Any]: Response dict for gate completion
            - success (bool): True if logout successful
            - message (str): Success message for user feedback
    
    Examples:
        # Logout from zCloud app
        >>> result = handle_zLogout("zCloud", {}, {}, zcli)
        >>> # Removes: session[zAuth][applications]["zCloud"]
        >>> # Switches context to: "zsession" or "anonymous"
    
    Session Cleanup Process:
        1. Check if zAuth structure exists (graceful if missing)
        2. Remove app from session[zAuth][applications][app_name]
        3. Check if other apps are still authenticated
        4. If zSession is authenticated, switch to CONTEXT_ZSESSION
        5. If no zSession, set active_context to None (anonymous)
        6. Update dual_mode flag accordingly
        7. Clear active_app
        8. Regenerate session_hash for frontend cache invalidation
    
    Notes:
        - Gracefully handles logout from non-authenticated apps (success anyway)
        - Always regenerates session_hash to trigger frontend updates
        - Preserves zSession authentication if present
        - Works in both Terminal and Bifrost modes
    """
    logger = zcli.logger
    logger.info(f"{LOG_PREFIX} Logout request for app: {app_name}")
    
    # Initialize zAuth structure if not exists (graceful handling)
    if SESSION_KEY_ZAUTH not in zcli.session:
        logger.warning(f"{LOG_PREFIX} No zAuth session found (already logged out?)")
        zcli.session[SESSION_KEY_ZAUTH] = {}
    
    if ZAUTH_KEY_APPLICATIONS not in zcli.session[SESSION_KEY_ZAUTH]:
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS] = {}
    
    # Remove app from applications dict
    if app_name in zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS]:
        del zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]
        logger.info(f"{LOG_PREFIX} Removed {app_name} from applications")
    else:
        logger.debug(f"{LOG_PREFIX} App {app_name} was not authenticated (graceful)")
    
    # CONTEXT SWITCHING
    # Determine new context based on remaining authenticated sessions
    
    # Check if zSession is still authenticated
    zsession_data = zcli.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ZSESSION, {})
    zsession_authenticated = zsession_data.get(ZAUTH_KEY_AUTHENTICATED, False)
    
    # Check if any apps are still authenticated
    remaining_apps = zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS]
    has_remaining_apps = len(remaining_apps) > 0
    
    if zsession_authenticated and has_remaining_apps:
        # Both zSession and apps → DUAL mode
        new_context = CONTEXT_DUAL
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = True
        # Pick first remaining app as active
        first_app = list(remaining_apps.keys())[0]
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = first_app
        logger.info(f"{LOG_PREFIX} Switched to dual-mode (zSession + {first_app})")
    
    elif zsession_authenticated:
        # Only zSession → ZSESSION context
        new_context = CONTEXT_ZSESSION
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = None
        logger.info(f"{LOG_PREFIX} Switched to zSession context")
    
    elif has_remaining_apps:
        # Only apps → APPLICATION context
        new_context = CONTEXT_APPLICATION
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
        # Pick first remaining app as active
        first_app = list(remaining_apps.keys())[0]
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = first_app
        logger.info(f"{LOG_PREFIX} Switched to application context ({first_app})")
    
    else:
        # No sessions → Anonymous (context = None)
        new_context = None
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = None
        logger.info(f"{LOG_PREFIX} Switched to anonymous (no active context)")
    
    # Update active context
    zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = new_context
    logger.debug(f"{LOG_PREFIX} Active context: {new_context}")
    
    # v1.6.0: Regenerate session_hash for frontend cache invalidation
    new_hash = SessionConfig.regenerate_session_hash(zcli.session)
    logger.debug(f"{LOG_PREFIX} Session hash regenerated: {new_hash}")
    
    # Success! Display message and return
    success_msg = f"✓ You have been successfully logged out from {app_name}"
    logger.info(f"{LOG_PREFIX} Logout successful for {app_name}")
    
    if _is_bifrost_mode(zcli):
        return {"success": True, "message": success_msg, "app": app_name}
    
    # Terminal mode: Display success message and return truthy value for ! modifier
    zcli.display.success(success_msg)
    return True  # Return True (truthy) to indicate success for ! modifier


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _is_bifrost_mode(zcli: Any) -> bool:
    """
    Check if current mode is Bifrost (GUI).
    
    Args:
        zcli: zCLI instance
    
    Returns:
        bool: True if Bifrost mode, False if Terminal mode
    """
    return zcli.session.get(SESSION_KEY_ZMODE) == ZMODE_ZBIFROST

