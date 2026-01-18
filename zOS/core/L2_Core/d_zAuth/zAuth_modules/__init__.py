"""
zAuth Modules Package - Modular Three-Tier Authentication System (v1.5.4+)

PACKAGE OVERVIEW

This package contains the four core modules that implement zCLI's sophisticated
three-tier authentication system. Each module is designed with clear separation
of concerns and follows the Facade pattern, exposing clean APIs while hiding
implementation complexity.

MODULE ARCHITECTURE

The package follows a dependency hierarchy:

    Layer 1 (Foundation):
        auth_password_security.py
        └── Provides: bcrypt password hashing and verification
        └── Dependencies: None (foundation)
        └── Used by: auth_session_persistence

    Layer 2 (Persistence):
        auth_session_persistence.py
        └── Provides: SQLite-based persistent session management
        └── Dependencies: auth_password_security (for password hashing)
        └── Used by: auth_authentication (indirectly via zAuth facade)

    Layer 3 (Core Logic):
        auth_authentication.py (CORE)
        └── Provides: Three-tier authentication (zSession, Application, Dual)
        └── Dependencies: auth_password_security (indirectly), zConfig, zDisplay, zComm
        └── Used by: zAuth.py (facade)

        authzRBAC.py
        └── Provides: Context-aware Role-Based Access Control
        └── Dependencies: zConfig (for session/auth constants)
        └── Used by: zAuth.py (facade), zWizard (for access control)

MODULE DESCRIPTIONS

**auth_password_security.py** (PasswordSecurity class):
    Purpose:
        - Secure password hashing using bcrypt algorithm
        - Password verification with timing-safe comparison
        - Handles 72-byte bcrypt limit with truncation and logging
    
    Key Features:
        - Bcrypt with 12 rounds (2^12 = 4096 iterations)
        - Random salting (built into bcrypt)
        - Timing-safe comparison (prevents timing attacks)
        - Optional logging integration
    
    API:
        - hash_password(password: str) -> str
        - verify_password(password: str, hashed: str) -> bool

**auth_session_persistence.py** (SessionPersistence class):
    Purpose:
        - Persistent session storage using SQLite database
        - 7-day session expiry with automatic cleanup
        - Integration with zData subsystem for database operations
    
    Key Features:
        - Declarative zData operations (no raw SQL)
        - Session tokens generated with secrets.token_urlsafe()
        - Automatic password hashing via PasswordSecurity
        - Session cleanup on login/logout
    
    API:
        - ensure_sessions_db() -> bool
        - load_session(identifier: str, identifier_type: str) -> Optional[Dict]
        - save_session(auth_data: Dict, password: str) -> bool
        - cleanup_expired() -> int

**auth_authentication.py** (Authentication class) - CORE:
    Purpose:
        - CORE three-tier authentication implementation
        - zSession Auth (Internal zCLI/Zolo users)
        - Application Auth (External users of zCLI-built apps)
        - Dual-Mode Auth (Both contexts active simultaneously)
    
    Key Features:
        - Multi-app simultaneous authentication
        - Context-aware session management (active_context)
        - Local and remote authentication (via zComm)
        - Integration with zDisplay for all UI feedback
        - 100% SESSION_KEY_ZAUTH modernization (64 replacements)
    
    API:
        Layer 1 (zSession):
            - login(username, password, server_url, persist) -> Dict
            - logout(context, app_name, delete_persistent) -> Dict
            - status() -> Dict
            - is_authenticated() -> bool
            - get_credentials() -> Optional[Dict]
        
        Layer 2 (Application):
            - authenticate_app_user(app_name, token, config) -> Dict
            - switch_app(app_name) -> bool
            - get_app_user(app_name) -> Optional[Dict]
        
        Context Management:
            - set_active_context(context) -> bool
            - get_active_user() -> Optional[Dict]
        
        Remote:
            - authenticate_remote(username, password, server_url) -> Dict

**authzRBAC.py** (RBAC class):
    Purpose:
        - Context-aware Role-Based Access Control
        - Supports all three authentication tiers (zSession, Application, Dual)
        - Dynamic role/permission checks based on active_context
        - Dual-mode uses OR logic (either context can grant access)
    
    Key Features:
        - Context-aware role checks (_get_current_role helper)
        - Context-aware permission checks (_get_current_user_id helper)
        - Dual-mode OR logic (_check_role_match helper)
        - Persistent permissions in SQLite database (unified auth DB)
        - Integration with zData for permission storage
    
    API:
        - has_role(role: Union[str, List[str]]) -> bool
        - has_permission(permission: str) -> bool
        - grant_permission(user_id: str, permission: str, granted_by: str) -> bool
        - revoke_permission(user_id: str, permission: str) -> bool
        - ensure_permissions_db() -> bool

THREE-TIER AUTHENTICATION MODEL

This package implements zCLI's three-tier authentication model:

**Tier 1 - zSession Authentication (Internal Users):**
    - Authenticates zCLI/Zolo platform users
    - Used for premium features, plugins, cloud services
    - Session key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]

**Tier 2 - Application Authentication (External Users):**
    - Authenticates end-users of applications BUILT with zCLI
    - Each app maintains independent user database and credentials
    - Multi-app support: Multiple simultaneous authentications
    - Session key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]

**Tier 3 - Dual-Mode Authentication (Both Contexts):**
    - Both zSession AND application authenticated simultaneously
    - Example: Store owner analyzing their store (zCLI + store user)
    - RBAC uses OR logic: Either context can grant access
    - Session key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = True

INTEGRATION WITH ZCLI SUBSYSTEMS

**zConfig (config_session.py):**
    - Provides all session/auth constants:
      SESSION_KEY_ZAUTH, ZAUTH_KEY_*, CONTEXT_*
    - Maintains consistent session structure across subsystems
    - All modules import constants from zConfig (Week 6.2)

**zDisplay:**
    - All authentication feedback uses generic zDisplay events
    - Methods: success(), error(), warning(), text(), header()
    - Dual-mode compatible (Terminal + Bifrost)

**zComm (comm_http.py):**
    - Remote authentication uses zComm.http_post() for API calls
    - Secure HTTPS communication with Zolo authentication server

**zData (data_operations.py):**
    - Session persistence uses declarative zData operations
    - Permission storage uses zData for SQLite queries
    - No raw SQL - all operations go through zData subsystem

**zWizard (wizard.py):**
    - RBAC integration: _checkzRBAC_access() queries authzRBAC
    - Access control for all zVaF menu items
    - Supports require_auth, require_role, require_permission directives

USAGE EXAMPLE

    from zOS.L2_Core.d_zAuth.zAuth_modules import (
        PasswordSecurity,
        SessionPersistence,
        Authentication,
        RBAC
    )

    # Example 1: Password hashing
    pwd_security = PasswordSecurity(logger=zcli.logger)
    hashed = pwd_security.hash_password("my_password")
    is_valid = pwd_security.verify_password("my_password", hashed)

    # Example 2: Session persistence
    session_mgr = SessionPersistence(zcli, session_duration_days=7)
    session_mgr.ensure_sessions_db()
    session_data = session_mgr.load_session("user@example.com", "username")
    
    # Example 3: Three-tier authentication
    auth = Authentication(zcli)
    
    # zSession authentication (Tier 1)
    result = auth.login("user@zolo.com", "password")
    
    # Application authentication (Tier 2)
    result = auth.authenticate_app_user("my_store", "token", config)
    
    # Context switching
    auth.set_active_context("dual")  # Tier 3
    
    # Example 4: RBAC
    rbac = RBAC(zcli)
    
    if rbac.has_role("admin"):
        print("User is admin")
    
    if rbac.has_permission("data.delete"):
        print("User can delete data")

THREAD SAFETY

All modules operate on the zCLI session object, which is NOT thread-safe by design.
Each zCLI instance maintains a single session dictionary.

For multi-threaded applications:
- Each thread should use its own zCLI instance
- Multi-app authentication within a SINGLE session is fully supported and isolated
"""

# Package Metadata
__version__ = "1.5.4"
__author__ = "Zolo"
__description__ = "Modular three-tier authentication system for zCLI framework"

# Module Imports (Dependency Order)

# Layer 0: Constants (Foundation)
from .auth_constants import *  # Centralized constants for all auth modules

# Layer 0.5: Session Access Helpers (DRY utilities)
from .auth_helpers import (
    get_auth_data,
    get_zsession_data,
    get_applications_data,
    get_active_context,
    get_active_app,
    get_dual_mode_enabled,
)

# Layer 1: Foundation (Password Security)
from .auth_password_security import PasswordSecurity  # bcrypt hashing/verification

# Layer 2: Persistence (Session Management)
from .auth_session_persistence import SessionPersistence  # SQLite persistent sessions

# Layer 3: Core Logic (Authentication + RBAC)
from .auth_authentication import Authentication  # Three-tier auth (zSession, App, Dual)
from .auth_rbac import RBAC  # Context-aware Role-Based Access Control

# Layer 3: Built-in Actions (zLogin, zLogout)
from .auth_login import handle_zLogin    # Built-in declarative login action
from .auth_logout import handle_zLogout  # Built-in declarative logout action

# Public API Exports
__all__ = [
    'PasswordSecurity',      # Layer 1: bcrypt password hashing and verification
    'SessionPersistence',    # Layer 2: SQLite-based persistent session management
    'Authentication',        # Layer 3: CORE three-tier authentication implementation
    'RBAC',                  # Layer 3: Context-aware Role-Based Access Control
    'handle_zLogin',         # Layer 3: Built-in declarative login action
    'handle_zLogout'         # Layer 3: Built-in declarative logout action
]
