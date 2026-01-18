# zCLI/subsystems/zAuth/zAuth_modules/auth_login.py
"""
Built-in zLogin Action - Schema-Driven Authentication (v1.5.7+)

═══════════════════════════════════════════════════════════════════════════════
OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

This module provides a built-in zLogin action for declarative authentication
without requiring application-specific plugin code. It auto-discovers user table
structure from zSchema and automatically creates multi-app session structures.

Key Features:
    - Schema-driven: Auto-discovers table, fields, and hash type from zSchema
    - Zero configuration: No plugin code required
    - Multi-app support: Automatically creates/updates app sessions
    - Dual-mode aware: Detects and enables dual-mode if zSession exists
    - Declarative: Works in both Terminal and Bifrost modes

Usage:
    # In zUI.zLogin.yaml
    onSubmit:
        zLogin: "zCloud"  # App name (creates applications["zCloud"])
    
    # For Zolo platform authentication
    onSubmit:
        zLogin: "zolo"  # Reserved keyword for zSession authentication

Auto-Discovery from zSchema:
    - Table name: Extracted from model path (e.g., "@.models.zSchema.contacts" → "contacts")
    - Identity field: Auto-detects "email" or "username"
    - Password field: Always "password"
    - Hash type: Detects "zHash: bcrypt" from schema
    - Role field: Auto-detects "role" field
    - Additional fields: All non-password fields stored in session

═══════════════════════════════════════════════════════════════════════════════
"""

import bcrypt

from zOS import Any, Dict, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    SESSION_KEY_ZAUTH,
    SESSION_KEY_ZMODE,
    ZMODE_ZBIFROST,
    ZAUTH_KEY_APPLICATIONS,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_ACTIVE_APP,
    ZAUTH_KEY_DUAL_MODE,
    ZAUTH_KEY_AUTHENTICATED,
    ZAUTH_KEY_ID,
    ZAUTH_KEY_USERNAME,
    ZAUTH_KEY_ROLE,
    ZAUTH_KEY_ZSESSION,
    CONTEXT_APPLICATION,
    CONTEXT_ZSESSION,
    CONTEXT_DUAL
)
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SessionConfig

# Constants
# Import centralized constants
from .auth_constants import (
    # Public constants
    DEFAULT_IDENTITY_FIELDS,
    DEFAULT_PASSWORD_FIELD,
    DEFAULT_ROLE_FIELD,
    DEFAULT_ROLE,
    RESERVED_ZOLO_KEYWORD,
    # Internal constants (private)
    _LOG_PREFIX_LOGIN,
)

# Module uses _LOG_PREFIX_LOGIN as LOG_PREFIX for compatibility
LOG_PREFIX = _LOG_PREFIX_LOGIN


def handle_zLogin(
    app_or_type: str,
    zConv: Dict[str, Any],
    zContext: Dict[str, Any],
    zcli: Any
) -> Dict[str, Any]:
    """
    Built-in zLogin handler - auto-discovers authentication from schema.
    
    This is the main entry point for declarative authentication in zCLI.
    It requires NO plugin code - everything is auto-discovered from the
    zSchema model specified in the zDialog.
    
    Args:
        app_or_type: Application name (e.g., "zCloud") or "zolo" for platform auth
        zConv: Form data collected from zDialog (e.g., {"email": "...", "password": "..."})
        zContext: Dialog context containing model path and schema info
        zcli: zCLI instance (provides data, loader, session, logger access)
    
    Returns:
        Dict[str, Any]: Response dict for form rendering
            - success (bool): True if authentication successful
            - message (str): Success/error message for user feedback
            - redirect (str): Optional redirect URL (future feature)
    
    Raises:
        ValueError: If model is not specified in zContext (required for auto-discovery)
        Exception: If database query or password verification fails
    
    Examples:
        # Application authentication (zCloud app)
        >>> result = handle_zLogin("zCloud", {"email": "user@example.com", "password": "pass"}, zContext, zcli)
        >>> # Creates: session[zAuth][applications]["zCloud"] = {...}
        
        # Zolo platform authentication (zSession)
        >>> result = handle_zLogin("zolo", {"username": "admin", "password": "pass"}, zContext, zcli)
        >>> # Creates: session[zAuth][zSession] = {...}
    
    Auto-Discovery Process:
        1. Extract model path from zContext (e.g., "@.models.zSchema.contacts")
        2. Load schema via zcli.loader.handle()
        3. Extract table name from model path → "contacts"
        4. Auto-detect identity field (email or username) from zConv keys
        5. Query user table: zcli.data.select(table, where={identity_field: value})
        6. Verify password using bcrypt.checkpw()
        7. Create/update app session structure in session[zAuth][applications][app_name]
        8. Set active_context and active_app
        9. Detect dual-mode if zSession also authenticated
    
    Session Structure Created:
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name] = {
            ZAUTH_KEY_AUTHENTICATED: True,
            ZAUTH_KEY_ID: user["id"],
            ZAUTH_KEY_USERNAME: user["name"] or user["email"],
            ZAUTH_KEY_ROLE: user["role"] or "zUser",
            ...additional_user_fields  # All non-password fields from user record
        }
    
    Notes:
        - Requires zDialog to specify 'model' starting with '@' (schema reference)
        - Password field is never stored in session (excluded automatically)
        - All other user fields are stored for app use (e.g., company, phone, etc.)
        - Multi-app: Multiple apps can be authenticated simultaneously
        - Dual-mode: Auto-detected if both zSession and app are authenticated
    """
    logger = zcli.logger
    logger.info(f"{LOG_PREFIX} Authentication request for: {app_or_type}")
    
    # Check for Zolo platform authentication (reserved keyword)
    if app_or_type.lower() == RESERVED_ZOLO_KEYWORD:
        # Future: Implement zSession (Zolo platform) authentication
        # For now, return error message
        error_msg = "Zolo platform authentication not yet implemented. Use application authentication."
        logger.warning(f"{LOG_PREFIX} {error_msg}")
        if _is_bifrost_mode(zcli):
            return {"success": False, "message": error_msg}
        zcli.display.error(error_msg)
        return {"success": False, "message": error_msg}
    
    # APPLICATION AUTHENTICATION
    app_name = app_or_type
    logger.debug(f"{LOG_PREFIX} Application authentication for: {app_name}")
    
    # Auto-discover schema model from zContext
    model = zContext.get("model")
    if not model:
        error_msg = "zLogin requires 'model' in zDialog for schema auto-discovery"
        logger.error(f"{LOG_PREFIX} {error_msg}")
        raise ValueError(error_msg)
    
    if not model.startswith('@'):
        error_msg = f"zLogin requires schema reference (model starting with '@'), got: {model}"
        logger.error(f"{LOG_PREFIX} {error_msg}")
        raise ValueError(error_msg)
    
    logger.debug(f"{LOG_PREFIX} Schema model: {model}")
    
    # Extract table name from model path
    # e.g., "@.models.zSchema.contacts" → "contacts"
    table_name = _extract_table_name(model)
    logger.debug(f"{LOG_PREFIX} Auto-detected table: {table_name}")
    
    # Auto-detect identity field (email or username)
    identity_field = None
    identity_value = None
    
    for field in DEFAULT_IDENTITY_FIELDS:
        if field in zConv:
            identity_field = field
            identity_value = zConv[field]
            break
    
    if not identity_field:
        error_msg = f"No identity field found in form data. Expected one of: {DEFAULT_IDENTITY_FIELDS}"
        logger.error(f"{LOG_PREFIX} {error_msg}")
        if _is_bifrost_mode(zcli):
            return {"success": False, "message": "Invalid login credentials"}
        zcli.display.error("Invalid login credentials")
        return None  # Return None (falsy) for Terminal retry logic
    
    logger.debug(f"{LOG_PREFIX} Identity field: {identity_field} = {identity_value}")
    
    # Get password from form data
    password = zConv.get(DEFAULT_PASSWORD_FIELD)
    if not password:
        error_msg = "Password field required"
        logger.error(f"{LOG_PREFIX} {error_msg}")
        if _is_bifrost_mode(zcli):
            return {"success": False, "message": "Invalid login credentials"}
        zcli.display.error("Invalid login credentials")
        return None  # Return None (falsy) for Terminal retry logic
    
    # Query user from database
    try:
        logger.debug(f"{LOG_PREFIX} Querying table '{table_name}' for {identity_field}={identity_value}")
        result = zcli.data.select(
            table_name,
            where={identity_field: identity_value}
        )
        
        if not result or len(result) == 0 or result == "error":
            logger.warning(f"{LOG_PREFIX} No user found for {identity_field}={identity_value}")
            error_msg = "Invalid login credentials"
            if _is_bifrost_mode(zcli):
                return {"success": False, "message": error_msg}
            zcli.display.error(error_msg)
            return None  # Return None (falsy) for Terminal retry logic
        
        user = result[0]  # First matching record
        logger.debug(f"{LOG_PREFIX} User found: ID={user.get('id')}")
        
    except Exception as e:
        logger.error(f"{LOG_PREFIX} Database query failed: {e}", exc_info=True)
        error_msg = "Authentication system error"
        if _is_bifrost_mode(zcli):
            return {"success": False, "message": error_msg}
        zcli.display.error(error_msg)
        return None  # Return None (falsy) for Terminal retry logic
    
    # Verify password (bcrypt)
    stored_hash = user.get(DEFAULT_PASSWORD_FIELD)
    if not stored_hash:
        logger.error(f"{LOG_PREFIX} No password hash found for user {identity_value}")
        error_msg = "Invalid login credentials"
        if _is_bifrost_mode(zcli):
            return {"success": False, "message": error_msg}
        zcli.display.error(error_msg)
        return None  # Return None (falsy) for Terminal retry logic
    
    try:
        # Ensure stored_hash is a string (from CSV it might be str already, but be safe)
        stored_hash_str = str(stored_hash)
        password_bytes = password.encode('utf-8')
        stored_hash_bytes = stored_hash_str.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
            logger.warning(f"{LOG_PREFIX} Password verification failed for {identity_value}")
            error_msg = "Invalid login credentials"
            if _is_bifrost_mode(zcli):
                return {"success": False, "message": error_msg}
            zcli.display.error(error_msg)
            return None  # Return None (falsy) for Terminal retry logic
        
        logger.info(f"{LOG_PREFIX} Password verified successfully for {identity_value}")
        
    except Exception as e:
        logger.error(f"{LOG_PREFIX} Password verification error: {e}", exc_info=True)
        error_msg = "Authentication system error"
        if _is_bifrost_mode(zcli):
            return {"success": False, "message": error_msg}
        zcli.display.error(error_msg)
        return None  # Return None (falsy) for Terminal retry logic
    
    # CREATE/UPDATE APP SESSION STRUCTURE
    logger.debug(f"{LOG_PREFIX} Creating session structure for app: {app_name}")
    
    # Initialize zAuth structure if not exists
    if SESSION_KEY_ZAUTH not in zcli.session:
        zcli.session[SESSION_KEY_ZAUTH] = {}
    
    if ZAUTH_KEY_APPLICATIONS not in zcli.session[SESSION_KEY_ZAUTH]:
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS] = {}
    
    # Build app session data (exclude password!)
    # v1.5.13: Role lookup for production schema (users → user_roles → roles)
    user_role = user.get(DEFAULT_ROLE_FIELD)  # Try direct role field first
    if not user_role:
        # No direct role field - try production schema lookup
        try:
            user_id = int(user.get("id"))
            # Query user_roles table
            user_roles_result = zcli.data.select("user_roles", where={"user_id": user_id})
            if user_roles_result and len(user_roles_result) > 0:
                role_id = int(user_roles_result[0].get("role_id"))
                # Query roles table
                roles_result = zcli.data.select("roles", where={"id": role_id})
                if roles_result and len(roles_result) > 0:
                    user_role = roles_result[0].get("name")
                    logger.debug(f"{LOG_PREFIX} Role lookup: user_id={user_id} → role_id={role_id} → role={user_role}")
        except Exception as e:
            logger.debug(f"{LOG_PREFIX} Role lookup failed: {e}, using default")
    
    # Fallback to default if still no role
    if not user_role:
        user_role = DEFAULT_ROLE
    
    app_session = {
        ZAUTH_KEY_AUTHENTICATED: True,
        ZAUTH_KEY_ID: user.get("id"),
        ZAUTH_KEY_USERNAME: user.get("name", user.get(identity_field)),
        ZAUTH_KEY_ROLE: user_role
    }
    
    # Add all other user fields (except password) for app use
    for key, value in user.items():
        if key not in [DEFAULT_PASSWORD_FIELD, ZAUTH_KEY_ID, "name", identity_field, DEFAULT_ROLE_FIELD]:
            app_session[key] = value
    
    # Store app session
    zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name] = app_session
    logger.debug(f"{LOG_PREFIX} App session created: {list(app_session.keys())}")
    
    # Set active context and active app
    zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_APPLICATION
    zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = app_name
    logger.debug(f"{LOG_PREFIX} Active context: {CONTEXT_APPLICATION}, Active app: {app_name}")
    
    # Check for dual-mode (is zSession also authenticated?)
    zsession_data = zcli.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ZSESSION, {})
    if zsession_data.get(ZAUTH_KEY_AUTHENTICATED):
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = True
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_DUAL
        logger.info(f"{LOG_PREFIX} Dual-mode enabled (zSession + {app_name})")
    else:
        zcli.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
        logger.debug(f"{LOG_PREFIX} Single-app mode ({app_name})")
    
    # v1.6.0: Regenerate session_hash for frontend cache invalidation
    new_hash = SessionConfig.regenerate_session_hash(zcli.session)
    logger.debug(f"{LOG_PREFIX} Session hash regenerated: {new_hash}")
    
    # Success! Display message and return
    username = app_session[ZAUTH_KEY_USERNAME]
    role = app_session[ZAUTH_KEY_ROLE]
    success_msg = f"✓ Welcome back, {username}! (Role: {role})"
    
    logger.info(f"{LOG_PREFIX} Authentication successful for {username} in app {app_name}")
    
    # Clear parsed UI file cache to force navbar re-injection with new RBAC rules
    # This ensures navbar items are re-evaluated for the newly authenticated user
    if hasattr(zcli, 'loader') and hasattr(zcli.loader, 'cache') and hasattr(zcli.loader.cache, 'system_cache'):
        try:
            # Access the internal OrderedDict cache via _cache property
            cache_dict = zcli.loader.cache.system_cache._cache
            cleared = 0
            for key in list(cache_dict.keys()):
                if key.startswith('parsed:') and ('.zUI.' in key or '/zUI/' in key or '/UI/' in key):
                    del cache_dict[key]
                    cleared += 1
            if cleared > 0:
                logger.debug(f"{LOG_PREFIX} Cleared {cleared} cached UI file(s) for RBAC re-evaluation")
        except Exception as e:
            logger.debug(f"{LOG_PREFIX} Could not clear UI cache: {e}")
    
    if _is_bifrost_mode(zcli):
        return {"success": True, "message": success_msg, "app": app_name}
    
    # Terminal mode: Display success message and return truthy value for ! modifier
    zcli.display.success(success_msg)
    return True  # Return True (truthy) to indicate success for ! modifier retry logic


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_table_name(model_path: str) -> str:
    """
    Extract table name from model path.
    
    Examples:
        "@.models.zSchema.contacts" → "contacts"
        "@.zSchema.users" → "users"
        "zSchema.products" → "products"
    
    Args:
        model_path: Schema model path (e.g., "@.models.zSchema.contacts")
    
    Returns:
        str: Table name (last component of path)
    """
    # Split by '.' and take last component
    parts = model_path.split('.')
    return parts[-1]


def _is_bifrost_mode(zcli: Any) -> bool:
    """
    Check if current mode is Bifrost (GUI).
    
    Args:
        zcli: zCLI instance
    
    Returns:
        bool: True if Bifrost mode, False if Terminal mode
    """
    return zcli.session.get(SESSION_KEY_ZMODE) == ZMODE_ZBIFROST

