# zCLI/subsystems/zAuth/__init__.py
"""
zAuth Subsystem - Three-Tier Authentication System (v1.5.4+)

═══════════════════════════════════════════════════════════════════════════════
PACKAGE OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

The zAuth subsystem provides comprehensive authentication and authorization for
the zCLI framework, implementing a sophisticated three-tier authentication model
that supports both internal platform users and external application users.

This is NOT a "session-only" authentication system. It's a complete three-tier
architecture designed to handle complex multi-user, multi-application scenarios.

═══════════════════════════════════════════════════════════════════════════════
THREE-TIER AUTHENTICATION MODEL
═══════════════════════════════════════════════════════════════════════════════

**Tier 1 - zSession Authentication (Internal Users):**
    Authenticates zCLI/Zolo platform users for access to:
    - Premium zCLI features
    - Plugin marketplace
    - Zolo cloud services
    - Administrative functions
    
    Session Key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]

**Tier 2 - Application Authentication (External Users - Multi-App):**
    Authenticates end-users of applications BUILT with zCLI. Key features:
    - Each app maintains independent user database and credentials
    - Multiple apps can be authenticated simultaneously
    - Each app has isolated authentication context
    - Example: Store customers, forum users, admin panel users
    
    Session Key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]

**Tier 3 - Dual-Mode Authentication (Both Contexts):**
    Both zSession AND application authenticated simultaneously:
    - Example: Store owner analyzing their store (zCLI user + store owner)
    - RBAC uses OR logic: Either context can grant access
    - Seamless context switching
    
    Session Key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = "dual"

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

**Facade Pattern:**
    zAuth.py acts as a unified facade, orchestrating four specialized modules:
    
    1. auth_password_security.py (PasswordSecurity)
       - bcrypt password hashing (12 rounds, 2^12 = 4096 iterations)
       - Random salting (built into bcrypt)
       - Timing-safe password verification
       - 72-byte truncation handling
    
    2. auth_session_persistence.py (SessionPersistence)
       - SQLite-based persistent session storage
       - 7-day session expiry with automatic cleanup
       - Declarative zData operations (no raw SQL)
       - Session tokens via secrets.token_urlsafe()
    
    3. auth_authentication.py (Authentication) - CORE
       - Three-tier authentication implementation
       - Multi-app simultaneous authentication
       - Context-aware session management
       - Local and remote authentication (via zComm)
       - 100% SESSION_KEY_ZAUTH modernization
    
    4. authzRBAC.py (RBAC)
       - Context-aware Role-Based Access Control
       - Supports all three authentication tiers
       - Dynamic role/permission checks based on active_context
       - Dual-mode uses OR logic (either context can grant access)
       - Persistent permissions in SQLite database

**Module Organization:**
    zCLI/subsystems/zAuth/
    ├── zAuth.py                  # Facade (orchestrates all modules)
    ├── __init__.py               # This file (package exports)
    └── zAuth_modules/            # Modular implementations
        ├── __init__.py           # Module exports (all 4 classes)
        ├── auth_password_security.py      # Layer 1: Password hashing
        ├── auth_session_persistence.py    # Layer 2: Session storage
        ├── auth_authentication.py         # Layer 3: CORE auth logic
        └── authzRBAC.py                   # Layer 3: RBAC
    
    Schema Location (v1.5.4+):
        zCLI/Schemas/zSchema.auth.yaml    # Centralized schemas directory
                                           # Contains sessions + permissions tables

═══════════════════════════════════════════════════════════════════════════════
KEY FEATURES
═══════════════════════════════════════════════════════════════════════════════

**Security:**
    - bcrypt password hashing (industry standard)
    - Timing-safe password verification (prevents timing attacks)
    - Persistent sessions with automatic expiry
    - CSRF protection via origin validation (zComm integration)
    - Secure token generation (secrets.token_urlsafe)

**Multi-App Support:**
    - Simultaneous authentication across multiple applications
    - Independent user identities per application
    - Isolated authentication contexts
    - Seamless context switching

**RBAC (Role-Based Access Control):**
    - Context-aware role checks
    - Granular permission system
    - Dual-mode OR logic (either context grants access)
    - Persistent permission storage

**Session Management:**
    - In-memory session (zCLI session dictionary)
    - Persistent session (SQLite, 7-day expiry)
    - Automatic session cleanup
    - Session tokens for API authentication

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION WITH ZCLI SUBSYSTEMS
═══════════════════════════════════════════════════════════════════════════════

**zConfig (config_session.py):**
    Provides all session/auth constants:
        SESSION_KEY_ZAUTH, ZAUTH_KEY_ZSESSION, ZAUTH_KEY_APPLICATIONS,
        ZAUTH_KEY_ACTIVE_CONTEXT, ZAUTH_KEY_DUAL_MODE, CONTEXT_*
    
    Maintains consistent session structure across all subsystems.

**zDisplay:**
    All authentication feedback uses generic zDisplay events:
        - success(), error(), warning(), text(), header()
        - zAuth composes these to create auth-specific UI
    
    Dual-mode compatible (Terminal + Bifrost WebSocket).

**zComm (bridge_auth.py):**
    - WebSocket connection authentication (token validation)
    - Remote authentication via HTTP POST (comm_http.py)
    - Origin validation for CSRF protection
    - zComm DELEGATES to zAuth for verification

**zData (data_operations.py):**
    - Session persistence uses declarative zData operations
    - Permission storage uses zData for SQLite queries
    - No raw SQL - all operations go through zData subsystem

**zWizard (wizard.py):**
    - RBAC integration: _checkzRBAC_access() queries authzRBAC
    - Access control for all zVaF menu items
    - Supports require_auth, require_role, require_permission directives

═══════════════════════════════════════════════════════════════════════════════
USAGE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Basic zSession Authentication:
    from zOS import zOS
    
    zcli = zCLI()
    
    # Login (prompts for credentials)
    result = zcli.auth.login()
    
    # Login with explicit credentials
    result = zcli.auth.login("user@zolo.com", "password", persist=True)
    
    # Check authentication
    if zcli.auth.is_authenticated():
        creds = zcli.auth.get_credentials()
        print(f"Logged in as: {creds['username']}")
    
    # RBAC check
    if zcli.auth.has_role("admin"):
        print("User has admin access")
    
    # Logout
    zcli.auth.logout()

Three-Tier Authentication:
    # 1. Login as Zolo user (zSession - Tier 1)
    zcli.auth.login("admin@zolo.com", "password")
    
    # 2. Authenticate as store owner (Application - Tier 2)
    zcli.auth.authenticate_app_user(
        app_name="my_store",
        token="owner_token_xyz",
        config={"auth_endpoint": "https://store.com/api/auth"}
    )
    
    # 3. Set dual-mode context (Tier 3)
    zcli.auth.set_active_context("dual")
    
    # RBAC now checks BOTH contexts with OR logic
    # Returns True if user has "admin" role in EITHER context
    if zcli.auth.has_role("admin"):
        print("Admin access granted (from zSession OR store)")
    
    # Get current active user
    user = zcli.auth.get_active_user()
    print(f"Active user: {user}")
    
    # Context-specific logout
    zcli.auth.logout(context="application", app_name="my_store")
    zcli.auth.logout(context="zSession")

Multi-App Authentication:
    # Authenticate with multiple apps simultaneously
    zcli.auth.authenticate_app_user("store", "token1", config1)
    zcli.auth.authenticate_app_user("forum", "token2", config2)
    zcli.auth.authenticate_app_user("admin_panel", "token3", config3)
    
    # Switch between apps
    zcli.auth.switch_app("store")
    store_user = zcli.auth.get_app_user("store")
    print(f"Store user: {store_user['user_id']}")
    
    zcli.auth.switch_app("forum")
    forum_user = zcli.auth.get_app_user("forum")
    print(f"Forum user: {forum_user['user_id']}")
    
    # Logout from specific app
    zcli.auth.logout(context="application", app_name="forum")
    
    # Logout from all apps
    zcli.auth.logout(context="all_apps")

═══════════════════════════════════════════════════════════════════════════════
THREAD SAFETY
═══════════════════════════════════════════════════════════════════════════════

All modules operate on the zCLI session object, which is NOT thread-safe by design.
Each zCLI instance maintains a single session dictionary.

For multi-threaded applications:
- Each thread should use its own zCLI instance
- Multi-app authentication within a SINGLE session is fully supported and isolated

═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════
# PACKAGE METADATA
# ═══════════════════════════════════════════════════════════════════════════

__version__ = "1.5.4"
__author__ = "Zolo"
__description__ = "Three-tier authentication subsystem for zCLI framework"

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

# Facade pattern: orchestrates PasswordSecurity, SessionPersistence, Authentication, RBAC
from .zAuth import zAuth  # noqa: F401 - zAuth imported for __all__ export

# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'zAuth'  # Main facade orchestrating 4 authentication modules (three-tier model)
]
