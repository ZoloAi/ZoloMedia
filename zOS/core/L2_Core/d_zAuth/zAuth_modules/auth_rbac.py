"""
RBAC Module - Context-Aware Role-Based Access Control (v1.5.4+)

This module provides context-aware role and permission management for the zCLI
three-tier authentication system, enabling different RBAC rules for zSession,
application contexts, and dual-mode authentication.

Architecture
============

Context-Aware RBAC Design
--------------------------
Unlike traditional static RBAC systems, this module dynamically determines which
authentication context is active and applies role/permission checks accordingly.

Three-Tier Authentication Integration:

    Layer 1 (zSession):
        - Internal zCLI/Zolo users
        - Authenticated via zcli.auth.login()
        - Role stored in: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_ROLE]
        - Use case: Premium plugins, Zolo cloud access, zCLI features

    Layer 2 (Application - Multi-App):
        - External application users
        - Authenticated via zcli.auth.authenticate_app_user(app_name, token, config)
        - Role stored in: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name][ZAUTH_KEY_ROLE]
        - Use case: eCommerce store owners, analytics users, CRM users
        - Multiple apps can be authenticated simultaneously with independent roles

    Layer 3 (Dual):
        - Both zSession AND application authenticated
        - Role check uses OR logic: Either context can grant access
        - Use case: Store owner using zCLI analytics on their own store
        - Example: "admin" in eCommerce app but "user" in zSession → has_role("admin") = True

Active Context Determination
-----------------------------
The active context is stored in session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT]
and can be one of three values:

    CONTEXT_ZSESSION ("zSession"):
        - Only zSession authentication is active
        - Role/permission checks query zSession context only

    CONTEXT_APPLICATION ("application"):
        - Only application authentication is active
        - Role/permission checks query active application context
        - Active app determined by session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP]

    CONTEXT_DUAL ("dual"):
        - Both zSession AND application are active
        - Role/permission checks use OR logic (either grants access)
        - User must be authenticated in BOTH contexts (AND check)

Database Structure
------------------
Uses the unified auth database (zSchema.auth.yaml) which contains:

    sessions table:
        - session_id (primary key)
        - user_id, username, role
        - password_hash, token
        - created_at, expires_at, last_accessed

    user_permissions table:
        - user_id (foreign key to user)
        - permission (e.g., "users.delete", "system.shutdown")
        - granted_by (admin who granted permission)
        - granted_at (timestamp)

Permission Management
---------------------
Permissions are stored per user_id and checked against the current user's ID
from the active context. In dual-mode, permissions are checked for BOTH user IDs
(zSession and application) with OR logic.

Security Model
--------------
    - Permissions are explicitly granted by admins (whitelist approach)
    - No implicit permissions (even admins must be explicitly granted)
    - Public access supported via required_role=None
    - Admin operations (grant/revoke) require caller to check has_role("admin")

Usage Examples
==============

Basic Role Checks (zSession):
    >>> rbac = RBAC(zcli)
    >>> rbac.has_role("admin")  # Check zSession role
    True
    >>> rbac.has_role(["admin", "moderator"])  # Any of these (OR)
    True

Application Context Role Checks:
    >>> # User authenticated in eCommerce app as "admin"
    >>> # But authenticated in zSession as "user"
    >>> rbac.has_role("admin")  # Returns True (active_context = "application")
    True

Dual-Mode Role Checks:
    >>> # User: zSession="user", eCommerce="admin", active_context="dual"
    >>> rbac.has_role("admin")  # Returns True (eCommerce context has admin)
    True
    >>> rbac.has_role("user")  # Returns True (zSession context has user)
    True

Permission Checks:
    >>> rbac.has_permission("users.delete")  # Check single permission
    True
    >>> rbac.has_permission(["users.edit", "users.delete"])  # Any (OR)
    True

Admin Operations:
    >>> # Grant permission (admin-only, caller must verify)
    >>> if rbac.has_role("admin"):
    ...     rbac.grant_permission("user123", "users.delete", granted_by="admin")
    True

    >>> # Revoke permission (admin-only)
    >>> if rbac.has_role("admin"):
    ...     rbac.revoke_permission("user123", "users.delete")
    True

zCLI Integration
================
This module is deeply integrated with:
    - zConfig: Imports SESSION_KEY_ZAUTH and 12 ZAUTH_KEY_* constants
    - zData: Uses declarative operations for permission storage (no raw SQL)
    - zParser: Parses zSchema.auth.yaml for database schema
    - zAuth: Used by Authentication module for role/permission checks

Thread Safety
=============
This module reads from the zCLI session dictionary, which is NOT thread-safe.
If using zCLI in a multi-threaded environment, ensure proper session locking.

Module Constants
================
See MODULE CONSTANTS section below for all 38 defined constants:
    - Database: DB_LABEL_AUTH, TABLE_PERMISSIONS, TABLE_SESSIONS
    - Field Names: FIELD_USER_ID, FIELD_PERMISSION, FIELD_GRANTED_BY, FIELD_GRANTED_AT
    - Schema: SCHEMA_META_KEY, SCHEMA_LABEL_KEY, SCHEMA_FILE_NAME
    - Queries: QUERY_LIMIT_ONE, _QUERY_LEN_ZERO
    - Logging: LOG_PREFIX, _LOG_NOT_AUTHENTICATED, _LOG_NO_ROLE, etc. (20+ messages)
    - Defaults: DEFAULT_GRANTED_BY
"""

from zOS import datetime, Path, Optional, Any, Dict, Union, Tuple, List
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    # Session structure
    SESSION_KEY_ZAUTH,
    
    # Three-tier authentication keys
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_APPLICATIONS,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_ACTIVE_APP,
    
    # User data keys
    ZAUTH_KEY_ROLE,
    ZAUTH_KEY_ID,
    ZAUTH_KEY_USERNAME,
    ZAUTH_KEY_AUTHENTICATED,
    
    # Context constants
    CONTEXT_ZSESSION,
    CONTEXT_APPLICATION,
    CONTEXT_DUAL,
)


# =============================================================================
# MODULE CONSTANTS
# =============================================================================

# Import centralized constants
from .auth_constants import (
    # Public constants
    DB_LABEL_AUTH,
    TABLE_PERMISSIONS,
    TABLE_SESSIONS,
    FIELD_USER_ID,
    FIELD_PERMISSION,
    FIELD_GRANTED_BY,
    FIELD_GRANTED_AT,
    SCHEMAS_DIR,
    SCHEMA_META_KEY,
    SCHEMA_LABEL_KEY,
    SCHEMA_FILE_NAME,
    QUERY_LIMIT_ONE,
    DEFAULT_GRANTED_BY,
    # Internal constants (private)
    _QUERY_LEN_ZERO,
    _LOG_PREFIX_RBAC,
    _LOG_NOT_AUTHENTICATED,
    _LOG_NO_ROLE,
    _LOG_INVALID_ROLE_TYPE,
    _LOG_NO_USER_ID,
    _LOG_PERMISSION_CHECK_FAILED,
    _LOG_PERMISSION_GRANTED,
    _LOG_PERMISSION_ALREADY_GRANTED,
    _LOG_PERMISSION_REVOKED,
    _LOG_INVALID_PERMISSION_TYPE,
    _LOG_PERMISSION_ERROR,
    _LOG_GRANT_ERROR,
    _LOG_REVOKE_ERROR,
    _LOG_DB_INIT,
    _LOG_TABLE_CREATED,
    _LOG_SESSIONS_TABLE_CREATED,
    _LOG_SCHEMA_LOADED,
    _LOG_SCHEMA_NOT_FOUND,
    _LOG_SCHEMA_PARSE_FAILED,
    _LOG_HANDLER_FAILED,
    _LOG_WRONG_SCHEMA,
    _LOG_DB_ERROR,
    _LOG_CONTEXT_ZSESSION,
    _LOG_CONTEXT_APPLICATION,
    _LOG_CONTEXT_DUAL,
    _LOG_DUAL_ROLE_MATCH,
    _LOG_NO_ACTIVE_APP,
    _LOG_UNKNOWN_CONTEXT,
)

# Session Access Helpers (DRY utilities)
from .auth_helpers import (
    get_auth_data,
    get_zsession_data,
    get_applications_data,
    get_active_context,
)

# Module uses _LOG_PREFIX_RBAC as LOG_PREFIX for compatibility
LOG_PREFIX = _LOG_PREFIX_RBAC


# =============================================================================
# CONTEXT-AWARE RBAC CLASS
# =============================================================================

class RBAC:
    """
    Context-Aware Role-Based Access Control with three-tier authentication support.
    
    This class provides dynamic RBAC that adapts to the active authentication context
    (zSession, Application, or Dual). It supports:
    
    Features:
        - Context-aware role checks (zSession/Application/Dual)
        - Multi-app RBAC (different roles per application)
        - Context-aware permission checks (database-backed)
        - Permission grant/revoke (admin operations)
        - Dual-mode OR logic (either context can grant access)
        - SQLite-backed permissions database
        - Integration with three-tier authentication (Week 6.3)
    
    Architecture:
        - Checks session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] to determine context
        - Uses context-specific helper methods (_get_current_role, _get_current_user_id)
        - Supports dual-mode with OR logic for role checks
        - Uses declarative zData operations (no raw SQL)
    
    Three-Tier Support:
        Layer 1 (zSession):
            - Internal zCLI/Zolo users
            - Role from: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_ROLE]
        
        Layer 2 (Application):
            - External app users
            - Role from: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name][ZAUTH_KEY_ROLE]
            - Multiple apps with independent roles
        
        Layer 3 (Dual):
            - Both zSession AND app authenticated
            - Role check uses OR logic (either context grants access)
    
    Usage:
        >>> rbac = RBAC(zcli)
        >>> rbac.has_role("admin")  # Context-aware role check
        True
        >>> rbac.has_permission("users.delete")  # Context-aware permission check
        True
        >>> rbac.grant_permission("user123", "users.delete", granted_by="admin")
        True
    """
    
    # Class-level type declarations
    zcli: Any
    session: Dict[str, Any]
    logger: Any
    _permissions_db_initialized: bool
    
    def __init__(self, zcli: Any) -> None:
        """
        Initialize RBAC module with context-aware support.
        
        Args:
            zcli: zCLI instance (provides access to session, data, loader, logger)
        
        Notes:
            - Stores references to zcli.session and zcli.logger for convenience
            - Permissions database is lazily initialized on first use
            - No authentication checks in __init__ (happens per-method)
        
        Example:
            >>> from zOS import zOS
            >>> zcli = zCLI()
            >>> rbac = RBAC(zcli)
        """
        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
        self._permissions_db_initialized = False
    
    # =========================================================================
    # CONTEXT-AWARE HELPER METHODS (Private)
    # =========================================================================
    
    def _get_active_context(self) -> str:
        """
        Get the current active authentication context.
        
        Returns:
            str: Active context ("zSession", "application", or "dual")
                 Defaults to "zSession" if not set
        
        Context Values:
            - CONTEXT_ZSESSION ("zSession"): Only zSession active
            - CONTEXT_APPLICATION ("application"): Only app active
            - CONTEXT_DUAL ("dual"): Both zSession and app active
        
        Example:
            >>> context = self._get_active_context()
            >>> if context == CONTEXT_DUAL:
            ...     # Use OR logic for role checks
        """
        if not self.session:
            return CONTEXT_ZSESSION
        
        return self.session.get(SESSION_KEY_ZAUTH, {}).get(
            ZAUTH_KEY_ACTIVE_CONTEXT, 
            CONTEXT_ZSESSION
        )
    
    def _get_current_role(self) -> Optional[Union[str, Tuple[str, str]]]:
        """
        Get the current user's role(s) from the active authentication context.
        
        Returns:
            Optional[Union[str, Tuple[str, str]]]:
                - str: Single role (zSession or Application context)
                - Tuple[str, str]: Two roles (Dual context - zsession_role, app_role)
                - None: No role assigned or not authenticated
        
        Context Behavior:
            CONTEXT_ZSESSION:
                - Returns role from session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_ROLE]
            
            CONTEXT_APPLICATION:
                - Returns role from session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name][ZAUTH_KEY_ROLE]
                - Requires ZAUTH_KEY_ACTIVE_APP to be set
            
            CONTEXT_DUAL:
                - Returns tuple (zsession_role, app_role)
                - Either can be None if not assigned
        
        Example:
            >>> role = self._get_current_role()
            >>> if isinstance(role, tuple):
            ...     # Dual context - check both roles
            ...     zsession_role, app_role = role
        """
        if not self.session:
            return None
        
        active_context = self._get_active_context()
        auth_data = get_auth_data(self.session)
        
        if active_context == CONTEXT_ZSESSION:
            # Layer 1: Check zSession role
            return auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_ROLE)
        
        elif active_context == CONTEXT_APPLICATION:
            # Layer 2: Check active application role
            active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
            if not active_app:
                self._log("debug", LOG_NO_ACTIVE_APP)
                return None
            
            return auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_ROLE)
        
        elif active_context == CONTEXT_DUAL:
            # Layer 3: Return BOTH roles as tuple
            zsession_role = auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_ROLE)
            active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
            app_role = None
            if active_app:
                app_role = auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_ROLE)
            
            return (zsession_role, app_role)
        
        else:
            self._log("warning", f"{LOG_UNKNOWN_CONTEXT}: {active_context}")
            return None
    
    def _get_current_user_id(self) -> Optional[Union[str, Tuple[Optional[str], Optional[str]]]]:
        """
        Get the current user's ID(s) from the active authentication context.
        
        Returns:
            Optional[Union[str, Tuple[Optional[str], Optional[str]]]]:
                - str: Single user ID (zSession or Application context)
                - Tuple[str, str]: Two user IDs (Dual context - zsession_id, app_id)
                - None: No user ID or not authenticated
        
        Context Behavior:
            CONTEXT_ZSESSION:
                - Returns ID from session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_ID]
            
            CONTEXT_APPLICATION:
                - Returns ID from session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name][ZAUTH_KEY_ID]
            
            CONTEXT_DUAL:
                - Returns tuple (zsession_id, app_id)
                - Used for OR logic in permission checks
        
        Example:
            >>> user_id = self._get_current_user_id()
            >>> if isinstance(user_id, tuple):
            ...     # Dual context - check permissions for both
            ...     zsession_id, app_id = user_id
        """
        if not self.session:
            return None
        
        active_context = self._get_active_context()
        auth_data = get_auth_data(self.session)
        
        if active_context == CONTEXT_ZSESSION:
            # Layer 1: Check zSession user ID
            return auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_ID)
        
        elif active_context == CONTEXT_APPLICATION:
            # Layer 2: Check active application user ID
            active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
            if not active_app:
                return None
            
            return auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_ID)
        
        elif active_context == CONTEXT_DUAL:
            # Layer 3: Return BOTH user IDs as tuple
            zsession_id = auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_ID)
            active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
            app_id = None
            if active_app:
                app_id = auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_ID)
            
            return (zsession_id, app_id)
        
        else:
            return None
    
    def _check_role_match(
        self, 
        user_role: Optional[Union[str, Tuple[Optional[str], Optional[str]]]], 
        required_role: Union[str, List[str]]
    ) -> bool:
        """
        Check if user's role(s) match the required role(s), with dual-mode OR logic.
        
        Args:
            user_role: User's role(s) - str (single) or Tuple[str, str] (dual context)
            required_role: Required role(s) - str (single) or List[str] (any of)
        
        Returns:
            bool: True if role matches, False otherwise
        
        Dual-Mode OR Logic:
            If user_role is a tuple (dual context), checks BOTH roles:
            - Returns True if EITHER role matches required_role
            - Example: user_role=("user", "admin"), required_role="admin" → True
        
        Example:
            >>> # Single role check
            >>> self._check_role_match("admin", "admin")  # True
            >>> self._check_role_match("user", "admin")  # False
            
            >>> # Dual role check (OR logic)
            >>> self._check_role_match(("user", "admin"), "admin")  # True
            >>> self._check_role_match(("user", "moderator"), ["admin", "moderator"])  # True
        """
        if not user_role:
            return False
        
        # Dual context: Check BOTH roles with OR logic (with hierarchy support)
        if isinstance(user_role, tuple):
            zsession_role, app_role = user_role
            
            # Check if required_role is a list (any of these roles)
            if isinstance(required_role, list):
                # OR logic: Either role must qualify for any required role (via hierarchy or exact)
                zsession_match = any(
                    self._check_role_hierarchy(zsession_role, req) for req in required_role
                ) if zsession_role else False
                app_match = any(
                    self._check_role_hierarchy(app_role, req) for req in required_role
                ) if app_role else False
                return zsession_match or app_match
            
            # Single required role: Check if either user role qualifies (via hierarchy or exact)
            if isinstance(required_role, str):
                zsession_match = self._check_role_hierarchy(zsession_role, required_role) if zsession_role else False
                app_match = self._check_role_hierarchy(app_role, required_role) if app_role else False
                if zsession_match or app_match:
                    self._log("debug", f"{LOG_DUAL_ROLE_MATCH}: {required_role}")
                return zsession_match or app_match
            
            return False
        
        # Single context: Hierarchical role check (with fallback to exact match)
        if isinstance(required_role, str):
            return self._check_role_hierarchy(user_role, required_role)
        
        # Multiple required roles (list): Check if user qualifies for ANY
        if isinstance(required_role, list):
            return any(self._check_role_hierarchy(user_role, req) for req in required_role)
        
        return False
    
    def _check_role_hierarchy(self, user_role_name: str, required_role_name: str) -> bool:
        """
        Check if user's role matches required role with optional hierarchical checking.
        
        This is an OPT-IN feature: If both roles have a 'level' field in the database,
        hierarchy is used (user_level >= required_level). Otherwise, falls back to
        exact name matching for backwards compatibility.
        
        Hierarchy Rules:
            - Higher level = more access (e.g., level 100 > level 10)
            - User with level 100 can access features requiring level 10
            - User with level 10 CANNOT access features requiring level 100
        
        Exact Match Fallback:
            - If levels not found for either role → exact name match
            - If role query fails → exact name match
            - Maintains backwards compatibility with apps not using levels
        
        Args:
            user_role_name: Name of user's role (e.g., "zAdmin", "Administrator")
            required_role_name: Name of required role (e.g., "zUser", "Subscriber")
        
        Returns:
            bool: True if user qualifies (via hierarchy or exact match), False otherwise
        
        Examples:
            >>> # With levels (hierarchy mode):
            >>> self._check_role_hierarchy("zAdmin", "zUser")  # level 100 >= 10 → True
            >>> self._check_role_hierarchy("zUser", "zAdmin")  # level 10 >= 100 → False
            
            >>> # Without levels (exact match mode):
            >>> self._check_role_hierarchy("admin", "user")  # "admin" == "user" → False
            >>> self._check_role_hierarchy("admin", "admin")  # "admin" == "admin" → True
        """
        try:
            # Try to get levels for both roles (OPT-IN detection)
            user_level = self._get_role_level(user_role_name)
            required_level = self._get_role_level(required_role_name)
            
            # HIERARCHY MODE: Both roles have levels defined
            if user_level is not None and required_level is not None:
                result = user_level >= required_level
                if result:
                    self._log(
                        "debug",
                        f"[RBAC Hierarchy] User '{user_role_name}' (level {user_level}) "
                        f"qualifies for '{required_role_name}' (level {required_level})"
                    )
                return result
            
            # EXACT MATCH MODE: No levels found (backwards compatible)
            self._log(
                "debug",
                f"[RBAC] No hierarchy for '{user_role_name}' or '{required_role_name}', "
                f"using exact match"
            )
            
        except Exception as e:
            # Fail gracefully - log and fall back to exact match
            self._log(
                "warning",
                f"[RBAC] Role hierarchy check failed: {e}, falling back to exact match"
            )
        
        # Fallback to exact name matching
        return user_role_name == required_role_name
    
    def _get_role_level(self, role_name: str) -> Optional[int]:
        """
        Get the hierarchical level of a role from the roles table.
        
        This method implements the OPT-IN mechanism for hierarchical roles:
        - Returns int if role has 'level' field in database
        - Returns None if role not found, level field missing, or query fails
        
        The None return triggers exact match mode in _check_role_hierarchy(),
        making hierarchy completely optional and backwards compatible.
        
        Caching Strategy:
            - Levels are cached in self._role_level_cache
            - Cache persists for session lifetime
            - Avoids repeated database queries
        
        Args:
            role_name: Name of the role to look up (e.g., "zAdmin", "zUser")
        
        Returns:
            Optional[int]: Role level (0-100) or None if not found/available
        
        Examples:
            >>> self._get_role_level("zAdmin")  # Returns 100
            >>> self._get_role_level("zUser")   # Returns 10
            >>> self._get_role_level("unknown") # Returns None
        """
        # Initialize cache on first use
        if not hasattr(self, '_role_level_cache'):
            self._role_level_cache = {}
        
        # Return cached value if available
        if role_name in self._role_level_cache:
            return self._role_level_cache[role_name]
        
        # Try to query roles table for level
        try:
            # Load roles schema
            roles_schema = self.zcli.loader.handle('@.models.zSchema.roles')
            self.zcli.data.load_schema(roles_schema)
            
            # Query for this specific role
            role_data = self.zcli.data.adapter.select(
                "roles",
                where={"name": role_name}
            )
            
            # Extract level if found
            if role_data and len(role_data) > 0:
                level = role_data[0].get('level')
                
                # Cache the result (even if None)
                self._role_level_cache[role_name] = level
                
                if level is not None:
                    self._log(
                        "debug",
                        f"[RBAC] Cached level for role '{role_name}': {level}"
                    )
                
                return level
                
        except Exception as e:
            # Silently fail - this is opt-in, not required
            # The None return will trigger exact match mode
            self._log(
                "debug",
                f"[RBAC] Could not query level for role '{role_name}': {e}"
            )
        
        # Cache None to avoid repeated failed queries
        self._role_level_cache[role_name] = None
        return None
    
    def _is_db_ready(self) -> bool:
        """
        Check if zData handler is ready and auth schema is loaded.
        
        Returns:
            bool: True if database is ready, False otherwise
        
        Checks:
            - zData handler exists (self.zcli.data.handler)
            - Auth schema is loaded (schema["zMeta"]["Data_Label"] == "auth")
        
        Example:
            >>> if self._is_db_ready():
            ...     # Perform database operations
        """
        return (
            self.zcli.data.handler is not None and 
            self.zcli.data.schema.get(SCHEMA_META_KEY, {}).get(SCHEMA_LABEL_KEY) == DB_LABEL_AUTH
        )
    
    def _log(self, level: str, message: str) -> None:
        """
        Centralized logging with LOG_PREFIX.
        
        Args:
            level: Log level ("debug", "info", "warning", "error")
            message: Log message (LOG_PREFIX will be prepended)
        
        Example:
            >>> self._log("info", LOG_PERMISSION_GRANTED)
            >>> self._log("error", f"{LOG_GRANT_ERROR}: {e}")
        """
        full_message = f"{LOG_PREFIX} {message}"
        
        if level == "debug":
            self.logger.debug(full_message)
        elif level == "info":
            self.logger.info(full_message)
        elif level == "warning":
            self.logger.warning(full_message)
        elif level == "error":
            self.logger.error(full_message)
    
    def _is_authenticated(self) -> bool:
        """
        Check if user is authenticated in the active context.
        
        Returns:
            bool: True if authenticated, False otherwise
        
        Context Behavior:
            CONTEXT_ZSESSION:
                - Checks session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_AUTHENTICATED]
            
            CONTEXT_APPLICATION:
                - Checks session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name][ZAUTH_KEY_AUTHENTICATED]
            
            CONTEXT_DUAL:
                - Checks BOTH contexts (AND logic - must be authenticated in BOTH)
                - If either is not authenticated, returns False
        
        Example:
            >>> if self._is_authenticated():
            ...     # User is authenticated in active context
        """
        if not self.session:
            return False
        
        active_context = self._get_active_context()
        auth_data = get_auth_data(self.session)
        
        if active_context == CONTEXT_ZSESSION:
            # Layer 1: Check zSession authentication
            return auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_AUTHENTICATED, False)
        
        elif active_context == CONTEXT_APPLICATION:
            # Layer 2: Check active application authentication
            active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
            if not active_app:
                return False
            
            return auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_AUTHENTICATED, False)
        
        elif active_context == CONTEXT_DUAL:
            # Layer 3: Check BOTH contexts (AND logic - must be authenticated in BOTH)
            zsession_auth = auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_AUTHENTICATED, False)
            active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
            app_auth = False
            if active_app:
                app_auth = auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_AUTHENTICATED, False)
            
            return zsession_auth and app_auth
        
        else:
            return False
    
    # =========================================================================
    # PUBLIC API - CONTEXT-AWARE ROLE & PERMISSION CHECKS
    # =========================================================================
    
    def has_role(self, required_role: Optional[Union[str, List[str]]]) -> bool:
        """
        Check if the current user has the required role (context-aware).
        
        Args:
            required_role: Role name (str), list of role names (list), or None
                - str: User must have this exact role
                - list: User must have ANY of these roles (OR logic)
                - None: Public access (always returns True)
        
        Returns:
            bool: True if user has the required role(s), False otherwise
        
        Context Behavior:
            CONTEXT_ZSESSION:
                - Checks role in session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
            
            CONTEXT_APPLICATION:
                - Checks role in session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]
            
            CONTEXT_DUAL:
                - Checks roles in BOTH contexts with OR logic
                - Returns True if EITHER context has the required role
                - Example: User is "admin" in app but "user" in zSession → has_role("admin") = True
        
        Examples:
            >>> rbac = RBAC(zcli)
            
            >>> # Single role check (context-aware)
            >>> rbac.has_role("admin")
            True
            
            >>> # Multiple roles (any of - OR logic)
            >>> rbac.has_role(["admin", "moderator"])
            True
            
            >>> # Public access (no authentication required)
            >>> rbac.has_role(None)
            True
            
            >>> # Dual context example:
            >>> # User: zSession="user", eCommerce="admin", active_context="dual"
            >>> rbac.has_role("admin")  # True (eCommerce has admin)
            >>> rbac.has_role("user")  # True (zSession has user)
        """
        # None = public access (override file-level restrictions)
        if required_role is None:
            return True
        
        # Check if user is authenticated first (context-aware)
        if not self._is_authenticated():
            self._log("debug", _LOG_NOT_AUTHENTICATED)
            return False
        
        # Get user's current role(s) from active context
        user_role = self._get_current_role()
        
        if not user_role:
            self._log("debug", _LOG_NO_ROLE)
            return False
        
        # Log active context for debugging
        active_context = self._get_active_context()
        if active_context == CONTEXT_ZSESSION:
            self._log("debug", _LOG_CONTEXT_ZSESSION)
        elif active_context == CONTEXT_APPLICATION:
            self._log("debug", _LOG_CONTEXT_APPLICATION)
        elif active_context == CONTEXT_DUAL:
            self._log("debug", _LOG_CONTEXT_DUAL)
        
        # Check role match (handles single/list required_role and dual-mode OR logic)
        if self._check_role_match(user_role, required_role):
            return True
        
        # Invalid role type check
        if not isinstance(required_role, (str, list)):
            self._log("warning", f"{_LOG_INVALID_ROLE_TYPE}: {type(required_role)}")
        
        return False
    
    def has_permission(self, required_permission: Union[str, List[str]]) -> bool:
        """
        Check if the current user has the required permission (context-aware).
        
        Args:
            required_permission: Permission name (str) or list of permissions (list)
                - str: User must have this exact permission
                - list: User must have ANY of these permissions (OR logic)
        
        Returns:
            bool: True if user has the required permission(s), False otherwise
        
        Context Behavior:
            CONTEXT_ZSESSION:
                - Checks permissions for session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_ID]
            
            CONTEXT_APPLICATION:
                - Checks permissions for session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name][ZAUTH_KEY_ID]
            
            CONTEXT_DUAL:
                - Checks permissions for BOTH user IDs with OR logic
                - Returns True if EITHER user ID has the required permission
        
        Implementation:
            Queries the user_permissions table from zSchema.auth.yaml
            to check if the user has been granted the specified permission.
        
        Examples:
            >>> rbac = RBAC(zcli)
            
            >>> # Single permission check (context-aware)
            >>> rbac.has_permission("users.delete")
            True
            
            >>> # Multiple permissions (any of - OR logic)
            >>> rbac.has_permission(["users.edit", "users.delete"])
            True
            
            >>> # Dual context example:
            >>> # zSession user_id="123", eCommerce user_id="456"
            >>> # Permission "users.delete" granted to user_id="456"
            >>> rbac.has_permission("users.delete")  # True (eCommerce user has it)
        """
        # Validate authentication and get user ID
        if not self._validate_permission_check():
            return False
        
        user_id = self._get_current_user_id()
        if not user_id:
            self._log("debug", LOG_NO_USER_ID)
            return False
        
        try:
            # Ensure permissions database is loaded
            self.ensure_permissions_db()
            
            # Handle dual context (tuple of two user IDs)
            if isinstance(user_id, tuple):
                return self._check_permission_dual_context(user_id, required_permission)
            
            # Handle single context (single user ID)
            return self._check_permission_single_context(user_id, required_permission)
            
        except Exception as e:
            self._log("error", f"{LOG_PERMISSION_ERROR}: {e}")
            return False
    
    def _validate_permission_check(self) -> bool:
        """Validate user is authenticated before permission check."""
        if not self._is_authenticated():
            self._log("debug", LOG_PERMISSION_CHECK_FAILED)
            return False
        return True
    
    def _check_permission_dual_context(
        self,
        user_ids: Tuple[Optional[str], Optional[str]],
        required_permission: Union[str, List[str]]
    ) -> bool:
        """Check permissions for dual context (OR logic across two user IDs)."""
        zsession_id, app_id = user_ids
        
        # Single permission check
        if isinstance(required_permission, str):
            return self._check_single_permission_dual(zsession_id, app_id, required_permission)
        
        # Multiple permissions check (OR logic)
        if isinstance(required_permission, list):
            return self._check_multiple_permissions_dual(zsession_id, app_id, required_permission)
        
        self._log("warning", f"{LOG_INVALID_PERMISSION_TYPE}: {type(required_permission)}")
        return False
    
    def _check_single_permission_dual(
        self,
        zsession_id: Optional[str],
        app_id: Optional[str],
        permission: str
    ) -> bool:
        """Check single permission across both user IDs in dual context."""
        # Check zSession user
        if zsession_id and self._user_has_permission(zsession_id, permission):
            return True
        
        # Check app user
        if app_id and self._user_has_permission(app_id, permission):
            return True
        
        return False
    
    def _check_multiple_permissions_dual(
        self,
        zsession_id: Optional[str],
        app_id: Optional[str],
        permissions: List[str]
    ) -> bool:
        """Check multiple permissions across both user IDs in dual context (OR logic)."""
        for perm in permissions:
            # Check zSession user
            if zsession_id and self._user_has_permission(zsession_id, perm):
                return True
            
            # Check app user
            if app_id and self._user_has_permission(app_id, perm):
                return True
        
        return False
    
    def _check_permission_single_context(
        self,
        user_id: str,
        required_permission: Union[str, List[str]]
    ) -> bool:
        """Check permissions for single context."""
        # Single permission check
        if isinstance(required_permission, str):
            return self._user_has_permission(user_id, required_permission)
        
        # Multiple permissions check (OR logic)
        if isinstance(required_permission, list):
            for perm in required_permission:
                if self._user_has_permission(user_id, perm):
                    return True
            return False
        
        self._log("warning", f"{LOG_INVALID_PERMISSION_TYPE}: {type(required_permission)}")
        return False
    
    def _user_has_permission(self, user_id: str, permission: str) -> bool:
        """Query database to check if user has specific permission."""
        results = self.zcli.data.select(
            table=TABLE_PERMISSIONS,
            where=f"{FIELD_USER_ID} = '{user_id}' AND {FIELD_PERMISSION} = '{permission}'",
            limit=QUERY_LIMIT_ONE
        )
        return results and len(results) > _QUERY_LEN_ZERO
    
    # =========================================================================
    # ADMIN OPERATIONS - PERMISSION MANAGEMENT
    # =========================================================================
    
    def grant_permission(
        self, 
        user_id: str, 
        permission: str, 
        granted_by: Optional[str] = None
    ) -> bool:
        """
        Grant a permission to a user (admin-only operation).
        
        Args:
            user_id: User ID to grant permission to
            permission: Permission name (e.g., "users.delete", "system.shutdown")
            granted_by: Optional admin username who granted this permission
                       Defaults to current user's username from active context
        
        Returns:
            bool: True if permission was granted successfully, False otherwise
        
        Context Awareness:
            - If granted_by is not provided, extracts username from active context
            - In dual context, uses zSession username (admin operation)
        
        Security:
            This should only be callable by users with admin role.
            The calling code MUST check `has_role("admin")` before calling.
        
        Examples:
            >>> rbac = RBAC(zcli)
            
            >>> # Grant permission (with explicit granted_by)
            >>> if rbac.has_role("admin"):
            ...     rbac.grant_permission("user123", "users.delete", granted_by="admin")
            True
            
            >>> # Grant permission (auto-detect current admin)
            >>> if rbac.has_role("admin"):
            ...     rbac.grant_permission("user123", "system.shutdown")
            True
        """
        try:
            # Ensure permissions database is loaded
            self.ensure_permissions_db()
            
            # Check if permission already exists
            existing = self.zcli.data.select(
                table=TABLE_PERMISSIONS,
                where=f"{FIELD_USER_ID} = '{user_id}' AND {FIELD_PERMISSION} = '{permission}'",
                limit=QUERY_LIMIT_ONE
            )
            
            if existing and len(existing) > _QUERY_LEN_ZERO:
                self._log("info", f"{LOG_PERMISSION_ALREADY_GRANTED} '{user_id}': {permission}")
                return True
            
            # Get current admin's username if not provided (context-aware)
            if not granted_by:
                auth_data = get_auth_data(self.session)
                active_context = self._get_active_context()
                
                # In dual context, use zSession username (admin operations are zSession-level)
                if active_context == CONTEXT_DUAL:
                    granted_by = auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_USERNAME, DEFAULT_GRANTED_BY)
                elif active_context == CONTEXT_ZSESSION:
                    granted_by = auth_data.get(ZAUTH_KEY_ZSESSION, {}).get(ZAUTH_KEY_USERNAME, DEFAULT_GRANTED_BY)
                elif active_context == CONTEXT_APPLICATION:
                    active_app = auth_data.get(ZAUTH_KEY_ACTIVE_APP)
                    if active_app:
                        granted_by = auth_data.get(ZAUTH_KEY_APPLICATIONS, {}).get(active_app, {}).get(ZAUTH_KEY_USERNAME, DEFAULT_GRANTED_BY)
                    else:
                        granted_by = DEFAULT_GRANTED_BY
                else:
                    granted_by = DEFAULT_GRANTED_BY
            
            # Insert new permission
            self.zcli.data.insert(
                table=TABLE_PERMISSIONS,
                fields=[FIELD_USER_ID, FIELD_PERMISSION, FIELD_GRANTED_BY, FIELD_GRANTED_AT],
                values=[user_id, permission, granted_by, datetime.now().isoformat()]
            )
            
            self._log("info", f"{LOG_PERMISSION_GRANTED} '{permission}' to user '{user_id}' by '{granted_by}'")
            return True
            
        except Exception as e:
            self._log("error", f"{LOG_GRANT_ERROR}: {e}")
            return False
    
    def revoke_permission(self, user_id: str, permission: str) -> bool:
        """
        Revoke a permission from a user (admin-only operation).
        
        Args:
            user_id: User ID to revoke permission from
            permission: Permission name to revoke
        
        Returns:
            bool: True if permission was revoked successfully, False otherwise
        
        Security:
            This should only be callable by users with admin role.
            The calling code MUST check `has_role("admin")` before calling.
        
        Examples:
            >>> rbac = RBAC(zcli)
            
            >>> # Revoke permission
            >>> if rbac.has_role("admin"):
            ...     rbac.revoke_permission("user123", "users.delete")
            True
        """
        try:
            # Ensure permissions database is loaded
            self.ensure_permissions_db()
            
            # Delete permission
            self.zcli.data.delete(
                table=TABLE_PERMISSIONS,
                where=f"{FIELD_USER_ID} = '{user_id}' AND {FIELD_PERMISSION} = '{permission}'"
            )
            
            self._log("info", f"{LOG_PERMISSION_REVOKED} '{permission}' from user '{user_id}'")
            return True
            
        except Exception as e:
            self._log("error", f"{LOG_REVOKE_ERROR}: {e}")
            return False
    
    # =========================================================================
    # DATABASE INITIALIZATION
    # =========================================================================
    
    def ensure_permissions_db(self) -> None:
        """
        Ensure the permissions database is initialized (internal helper).
        
        Uses the unified auth schema (zSchema.auth.yaml) which contains both
        sessions and user_permissions tables. This method should be called
        after SessionPersistence.ensure_sessions_db() has loaded the schema.
        
        Process:
            1. Check if already initialized (self._permissions_db_initialized)
            2. If auth DB already loaded, just ensure table exists
            3. If not loaded, load zSchema.auth.yaml using zParser
            4. Create both tables (sessions + user_permissions) if needed
        
        Schema Location:
            zCLI/subsystems/zAuth/zSchema.auth.yaml
        
        Error Handling:
            - Gracefully handles missing schema file (logs warning)
            - Gracefully handles parse errors (logs warning)
            - Gracefully handles handler creation errors (logs error)
        
        Example:
            >>> rbac = RBAC(zcli)
            >>> rbac.ensure_permissions_db()  # Lazy initialization
        """
        # Skip if already initialized
        if self._permissions_db_initialized:
            return
        
        try:
            # Check if auth database is already loaded
            if self._is_db_ready():
                # Auth schema already loaded - just ensure table exists
                if not self.zcli.data.table_exists(TABLE_PERMISSIONS):
                    self.zcli.data.create_table(TABLE_PERMISSIONS)
                    self._log("info", LOG_TABLE_CREATED)
                self._permissions_db_initialized = True
                return
            
            # If not loaded yet, load the unified auth schema
            # Get absolute path to zSchema.auth.yaml (centralized location)
            # Schema Location (v1.5.4+): Centralized in zCLI/Schemas/
            zcli_root = Path(__file__).parent.parent.parent.parent  # Navigate to zCLI root
            schema_path = zcli_root / SCHEMAS_DIR / SCHEMA_FILE_NAME
            
            if not schema_path.exists():
                self._log("warning", f"{LOG_SCHEMA_NOT_FOUND}: {schema_path}")
                return
            
            # Load schema directly using zParser (bypass zLoader for package-internal files)
            schema_content = schema_path.read_text(encoding="utf-8")
            parsed_schema = self.zcli.zparser.parse_file_content(schema_content, ".yaml")
            
            if not parsed_schema:
                self._log("warning", LOG_SCHEMA_PARSE_FAILED)
                return
            
            # Load into zData
            self.zcli.data.load_schema(parsed_schema)
            
            # Verify handler was created
            if not self.zcli.data.handler:
                self._log("error", LOG_HANDLER_FAILED)
                return
            
            # Verify correct schema is loaded
            loaded_label = self.zcli.data.schema.get(SCHEMA_META_KEY, {}).get(SCHEMA_LABEL_KEY)
            if loaded_label != DB_LABEL_AUTH:
                self._log("error", f"{LOG_WRONG_SCHEMA}: {loaded_label} (expected: {DB_LABEL_AUTH})")
                return
            
            # CREATE both tables if they don't exist (unified schema)
            if not self.zcli.data.table_exists(TABLE_SESSIONS):
                self.zcli.data.create_table(TABLE_SESSIONS)
                self._log("info", LOG_SESSIONS_TABLE_CREATED)
            
            if not self.zcli.data.table_exists(TABLE_PERMISSIONS):
                self.zcli.data.create_table(TABLE_PERMISSIONS)
                self._log("info", LOG_TABLE_CREATED)
            
            self._log("info", LOG_DB_INIT)
            self._permissions_db_initialized = True
            
        except Exception as e:
            self._log("error", f"{LOG_DB_ERROR}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
