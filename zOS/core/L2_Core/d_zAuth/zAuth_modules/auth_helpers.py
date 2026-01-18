"""
Authentication Helper Utilities - Shared DRY utilities for session access

This module provides centralized helper functions to eliminate duplication in
session data access patterns across auth_authentication.py, authzRBAC.py, and
auth_session_persistence.py.

Purpose:
    - Reduce 55 DRY violations (44 direct + 11 chained session accesses)
    - Provide safe, consistent session data access with default fallbacks
    - Centralize session access patterns in one location

Usage:
    from .auth_helpers import get_auth_data, get_zsession_data
    
    auth_data = get_auth_data(self.session)
    zsession = get_zsession_data(self.session)
    apps = get_applications_data(self.session)
    context = get_active_context(self.session)
"""

from zOS import Dict, Optional, Any

# Import all session and auth constants from config_constants (Layer 1)
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_constants import (
    SESSION_KEY_ZAUTH,
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_APPLICATIONS,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_ACTIVE_APP,
    ZAUTH_KEY_DUAL_MODE,
    CONTEXT_ZSESSION,
)


# Session Data Access Helpers


def get_auth_data(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get auth data dict from session, with empty dict default.
    
    This helper eliminates the need for repeated:
        session.get(SESSION_KEY_ZAUTH, {})
    
    Args:
        session: Session dictionary
    
    Returns:
        Auth data dict (empty if not present)
    
    Example:
        auth_data = get_auth_data(self.session)
        if auth_data.get(ZAUTH_KEY_AUTHENTICATED):
            # ... authenticated logic
    """
    return session.get(SESSION_KEY_ZAUTH, {})


def get_zsession_data(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get zSession data dict, with empty dict default.
    
    This helper eliminates the need for repeated:
        session.get(SESSION_KEY_ZAUTH, {}).get(ZAUTH_KEY_ZSESSION, {})
        or
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
    
    Args:
        session: Session dictionary
    
    Returns:
        zSession data dict (empty if not present)
    
    Example:
        zsession = get_zsession_data(self.session)
        username = zsession.get(ZAUTH_KEY_USERNAME)
    """
    return get_auth_data(session).get(ZAUTH_KEY_ZSESSION, {})


def get_applications_data(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get applications data dict, with empty dict default.
    
    This helper eliminates the need for repeated:
        session.get(SESSION_KEY_ZAUTH, {}).get(ZAUTH_KEY_APPLICATIONS, {})
        or
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS]
    
    Args:
        session: Session dictionary
    
    Returns:
        Applications data dict (empty if not present)
    
    Example:
        apps = get_applications_data(self.session)
        ecommerce_user = apps.get("ecommerce_store", {})
    """
    return get_auth_data(session).get(ZAUTH_KEY_APPLICATIONS, {})


def get_active_context(session: Dict[str, Any]) -> str:
    """
    Get active authentication context.
    
    This helper eliminates the need for repeated:
        session.get(SESSION_KEY_ZAUTH, {}).get(ZAUTH_KEY_ACTIVE_CONTEXT, CONTEXT_ZSESSION)
        or
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT]
    
    Args:
        session: Session dictionary
    
    Returns:
        Active context (defaults to CONTEXT_ZSESSION)
    
    Example:
        context = get_active_context(self.session)
        if context == CONTEXT_ZSESSION:
            # ... zSession logic
    """
    return get_auth_data(session).get(ZAUTH_KEY_ACTIVE_CONTEXT, CONTEXT_ZSESSION)


def get_active_app(session: Dict[str, Any]) -> Optional[str]:
    """
    Get active application name.
    
    This helper eliminates the need for repeated:
        session.get(SESSION_KEY_ZAUTH, {}).get(ZAUTH_KEY_ACTIVE_APP)
        or
        session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_APP)
    
    Args:
        session: Session dictionary
    
    Returns:
        Active app name (None if not present)
    
    Example:
        app_name = get_active_app(self.session)
        if app_name:
            # ... app-specific logic
    """
    from .auth_constants import ZAUTH_KEY_ACTIVE_APP
    return get_auth_data(session).get(ZAUTH_KEY_ACTIVE_APP)


def get_dual_mode_enabled(session: Dict[str, Any]) -> bool:
    """
    Check if dual-mode authentication is enabled.
    
    This helper eliminates the need for repeated:
        session.get(SESSION_KEY_ZAUTH, {}).get(ZAUTH_KEY_DUAL_MODE, False)
        or
        session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_DUAL_MODE, False)
    
    Args:
        session: Session dictionary
    
    Returns:
        True if dual-mode enabled, False otherwise
    
    Example:
        if get_dual_mode_enabled(self.session):
            # ... dual-mode logic
    """
    from .auth_constants import ZAUTH_KEY_DUAL_MODE
    return get_auth_data(session).get(ZAUTH_KEY_DUAL_MODE, False)
