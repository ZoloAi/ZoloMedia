# zCLI/subsystems/zAuth/zAuth.py
"""
zAuth Subsystem - Three-Tier Authentication Facade (v1.5.4+)

ARCHITECTURE OVERVIEW

This module implements the **Facade Pattern** for zCLI's authentication subsystem.
It orchestrates four modular components to provide a unified, developer-friendly API
while maintaining clean separation of concerns internally.

The facade coordinates:
1. PasswordSecurity - bcrypt password hashing and verification
2. SessionPersistence - SQLite-based persistent session storage
3. Authentication - Three-tier authentication logic (zSession, Application, Dual)
4. RBAC - Context-aware Role-Based Access Control

THREE-TIER AUTHENTICATION MODEL

**Tier 1 - zSession Authentication (Internal Users):**
    Authenticates zCLI/Zolo platform users for premium features, plugins, cloud.
    
    Methods:
        - login(username, password, server_url, persist)
        - logout(context="zSession", app_name=None, delete_persistent=True)
        - is_authenticated() → bool
        - get_credentials() → Optional[Dict]
        - status() → Dict
    
    Session Storage:
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION] = {
            "username": str,
            "user_id": str,
            "role": str,
            "server_url": str (optional)
        }

**Tier 2 - Application Authentication (External Users - Multi-App):**
    Authenticates end-users of applications BUILT with zCLI. Each app maintains
    independent credentials and user identities. Multiple apps can be authenticated
    simultaneously within the same zCLI session.
    
    Methods:
        - authenticate_app_user(app_name, token, config) → Dict
        - switch_app(app_name) → bool
        - get_app_user(app_name) → Optional[Dict]
        - logout(context="application", app_name="store", delete_persistent=True)
    
    Session Storage:
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS] = {
            "store": {"user_id": "123", "role": "customer", ...},
            "admin_panel": {"user_id": "456", "role": "admin", ...}
        }

**Tier 3 - Dual-Mode Authentication (Both Contexts):**
    Both zSession AND application authenticated simultaneously. Example: Store owner
    using zCLI analytics on their store (logged in as Zolo user + store owner).
    
    Context Management:
        - set_active_context(context) → bool  # "zSession", "application", "dual"
        - get_active_user() → Optional[Dict]  # Returns user based on active_context
        - RBAC uses OR logic in dual mode (either context can grant access)
    
    Session Storage:
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = "dual"
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = True

DELEGATION MAPPING (Facade → Modules)

Password Security Methods:
    hash_password(plain_password)         → password_security.hash_password()
    verify_password(plain, hashed)        → password_security.verify_password()

Layer 1 (zSession) Methods:
    login(username, password, ...)        → authentication.login()
    logout(context, app_name, ...)        → authentication.logout()
    is_authenticated()                     → authentication.is_authenticated()
    get_credentials()                      → authentication.get_credentials()
    status()                               → authentication.status()

Layer 2 (Application) Methods:
    authenticate_app_user(app, token, ...) → authentication.authenticate_app_user()
    switch_app(app_name)                   → authentication.switch_app()
    get_app_user(app_name)                 → authentication.get_app_user()

Context Management:
    set_active_context(context)            → authentication.set_active_context()
    get_active_user()                      → authentication.get_active_user()

RBAC Methods (Context-Aware):
    has_role(required_role)                → rbac.has_role()
    has_permission(required_permission)    → rbac.has_permission()
    grant_permission(user_id, perm, by)    → rbac.grant_permission()
    revoke_permission(user_id, perm)       → rbac.revoke_permission()

MODULE RESPONSIBILITIES

**PasswordSecurity (auth_password_security.py):**
    - bcrypt password hashing (12 rounds, 2^12 = 4096 iterations)
    - Random salting (built into bcrypt)
    - Timing-safe password verification
    - 72-byte truncation with logging

**SessionPersistence (auth_session_persistence.py):**
    - SQLite-based persistent session storage (sessions.db)
    - 7-day session expiry with automatic cleanup
    - Declarative zData operations (no raw SQL)
    - Session tokens via secrets.token_urlsafe()

**Authentication (auth_authentication.py - CORE):**
    - Three-tier authentication implementation
    - Multi-app simultaneous authentication
    - Context-aware session management (active_context)
    - Local and remote authentication (via zComm HTTP)
    - Integration with zDisplay for all UI feedback

**RBAC (authzRBAC.py):**
    - Context-aware Role-Based Access Control
    - Supports all three authentication tiers
    - Dynamic role/permission checks based on active_context
    - Dual-mode uses OR logic (either context can grant access)
    - Persistent permissions in SQLite (unified auth DB)

INTEGRATION WITH ZCLI SUBSYSTEMS

**zConfig (config_session.py):**
    Provides all session/auth constants:
        SESSION_KEY_ZAUTH, ZAUTH_KEY_ZSESSION, ZAUTH_KEY_APPLICATIONS,
        ZAUTH_KEY_ACTIVE_CONTEXT, ZAUTH_KEY_DUAL_MODE, CONTEXT_*
    
    Maintains consistent session structure across subsystems.

**zDisplay:**
    All authentication feedback uses generic zDisplay events:
        - success(), error(), warning(), text(), header()
        - zAuth composes these to create auth-specific UI
    
    Dual-mode compatible (Terminal + Bifrost).

**zData (data_operations.py):**
    Session persistence and permission storage use declarative zData operations.
    No raw SQL - all database operations go through zData subsystem.

═══════════════════════════════════════════════════════════════════════════════
USAGE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Basic zSession Authentication (Tier 1):
    from zOS import zOS
    
    zcli = zCLI()
    
    # Login (zSession)
    result = zcli.auth.login("user@zolo.com", "password", persist=True)
    if result["status"] == "success":
        print("Logged in as:", result["user"]["username"])
    
    # Check authentication
    if zcli.auth.is_authenticated():
        print("User is authenticated")
    
    # RBAC
    if zcli.auth.has_role("admin"):
        print("User is admin")
    
    # Logout
    zcli.auth.logout()

Multi-App Authentication (Tier 2):
    # Authenticate app user (e.g., store customer)
    result = zcli.auth.authenticate_app_user(
        app_name="my_store",
        token="app_user_token_123",
        config={"auth_endpoint": "https://store.com/api/auth"}
    )
    
    # Get specific app user
    store_user = zcli.auth.get_app_user("my_store")
    print("Store user:", store_user["user_id"])
    
    # Switch between apps
    zcli.auth.switch_app("admin_panel")
    
    # Logout from specific app
    zcli.auth.logout(context="application", app_name="my_store")

Dual-Mode Authentication (Tier 3):
    # Login as Zolo user (zSession)
    zcli.auth.login("admin@zolo.com", "password")
    
    # Authenticate as app user (Application)
    zcli.auth.authenticate_app_user("my_store", "token", config)
    
    # Set dual-mode context
    zcli.auth.set_active_context("dual")
    
    # Get current user (based on active_context)
    current_user = zcli.auth.get_active_user()
    
    # RBAC in dual mode uses OR logic
    # Returns True if EITHER zSession OR app user has the role
    if zcli.auth.has_role("admin"):
        print("User has admin access")
    
    # Logout from all contexts
    zcli.auth.logout(context="all")

THREAD SAFETY

All methods operate on the zCLI session object, which is NOT thread-safe by design.
Each zCLI instance maintains a single session dictionary.

For multi-threaded applications:
- Each thread should use its own zCLI instance
- Multi-app authentication within a SINGLE session is fully supported and isolated
"""

from zOS import Any, Optional, Dict, Union, List
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZAUTH

from .zAuth_modules import PasswordSecurity, SessionPersistence, Authentication, RBAC

# Module Constants

# Logging
LOG_PREFIX: str = "[zAuth]"

# Status values
STATUS_SUCCESS: str = "success"
STATUS_FAIL: str = "fail"
STATUS_ERROR: str = "error"
STATUS_PENDING: str = "pending"

# Dictionary keys
KEY_STATUS: str = "status"
KEY_USERNAME: str = "username"
KEY_USER_ID: str = "user_id"
KEY_ROLE: str = "role"
KEY_CREDENTIALS: str = "credentials"
KEY_PASSWORD: str = "password"
KEY_PERSIST: str = "persist"
KEY_DELETE_PERSISTENT: str = "delete_persistent"
KEY_USER: str = "user"

# Database/Data keys
TABLE_SESSIONS: str = "sessions"
DATA_LABEL_AUTH: str = "auth"
META_KEY: str = "zMeta"
DATA_LABEL_KEY: str = "Data_Label"

# Configuration
COLOR_ZAUTH: str = "ZAUTH"
MSG_READY: str = "zAuth Ready"
SESSION_DURATION_DAYS: int = 7

# Context values (for logout and context management)
CONTEXT_ZSESSION: str = "zSession"
CONTEXT_APPLICATION: str = "application"
CONTEXT_ALL_APPS: str = "all_apps"
CONTEXT_ALL: str = "all"
CONTEXT_DUAL: str = "dual"

# Default role
DEFAULT_ROLE: str = "user"


class zAuth:
    """
    Authentication Subsystem Facade - Orchestrates Three-Tier Authentication
    
    This class implements the Facade Pattern, providing a unified API for:
    1. Password Security (bcrypt hashing/verification)
    2. Session Persistence (SQLite-based, 7-day expiry)
    3. Three-Tier Authentication (zSession, Application, Dual)
    4. Context-Aware RBAC (Role-Based Access Control)
    
    v1.5.4+: Modularized architecture with:
    - bcrypt password hashing (12 rounds, random salting)
    - Persistent sessions with automatic cleanup
    - Multi-app simultaneous authentication
    - Context-aware RBAC with OR logic in dual mode
    
    BREAKING CHANGE (v1.5.4): Plaintext passwords no longer supported.
    All passwords are now hashed using bcrypt before storage.
    
    Module Composition:
        - self.password_security: PasswordSecurity instance
        - self.session_persistence: SessionPersistence instance
        - self.authentication: Authentication instance (CORE three-tier logic)
        - self.rbac: RBAC instance (context-aware role/permission checks)
    
    Method Categories:
        Password Security: hash_password, verify_password
        Layer 1 (zSession): login, logout, is_authenticated, get_credentials, status
        Layer 2 (Application): authenticate_app_user, switch_app, get_app_user
        Context Management: set_active_context, get_active_user
        RBAC: has_role, has_permission, grant_permission, revoke_permission
        Deprecated: _ensure_sessions_db, _load_session, _save_session, etc.
    
    Integration:
        - zConfig: SESSION_KEY_ZAUTH and all ZAUTH_KEY_* constants
        - zDisplay: All UI feedback via generic display events
        - zComm: Remote authentication via comm_http.py
        - zData: Persistent storage via declarative operations
        - zWizard: RBAC integration for zVaF menu access control
    
    Thread Safety:
        NOT thread-safe. Each thread should use its own zCLI instance.
        Multi-app authentication within a SINGLE session is fully supported.
    
    Examples:
        # Basic zSession login
        result = zcli.auth.login("user@zolo.com", "password")
        
        # Multi-app authentication
        zcli.auth.authenticate_app_user("store", "token", config)
        
        # Dual-mode context
        zcli.auth.set_active_context("dual")
        
        # RBAC checks
        if zcli.auth.has_role("admin"):
            # Admin-only operations
    """
    
    # Class-level type declarations
    zcli: Any
    session: Dict[str, Any]
    logger: Any
    mycolor: str
    password_security: PasswordSecurity
    session_persistence: SessionPersistence
    authentication: Authentication
    rbac: RBAC
    
    def __init__(self, zcli: Any) -> None:
        """
        Initialize authentication subsystem with modular architecture.
        
        Creates instances of all four authentication modules and displays
        a ready message via zDisplay.
        
        Args:
            zcli: The main zCLI instance (provides session, logger, display, data)
        
        Returns:
            None
        
        Integration:
            - Initializes all 4 modules with zcli instance
            - Uses zDisplay.zDeclare() for ready message
            - Database initialization deferred until after zParser/zLoader ready
              (lazy initialization on first use)
        
        Example:
            # Automatically called during zCLI initialization
            auth = zAuth(zcli)
        """
        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
        self.mycolor = COLOR_ZAUTH  # Orange-brown bg (Authentication)
        
        # Initialize modular components (all require zcli instance)
        self.password_security = PasswordSecurity(logger=self.logger)
        self.session_persistence = SessionPersistence(zcli, session_duration_days=SESSION_DURATION_DAYS)
        self.authentication = Authentication(zcli)
        self.rbac = RBAC(zcli)
        
        # Display ready message via zDisplay facade
        self.zcli.display.zDeclare(MSG_READY, color=self.mycolor, indent=0, style="full")
        
        # Note: Database initialization is deferred until after zParser/zLoader are ready
        # Will be called automatically on first use (lazy initialization)
    
    # ════════════════════════════════════════════════════════════════════════════
    # PASSWORD SECURITY (Facade → password_security module)
    # ════════════════════════════════════════════════════════════════════════════
    
    def hash_password(self, plain_password: str) -> str:
        """
        Hash a plaintext password using bcrypt.
        
        Delegates to: password_security.hash_password()
        
        Uses bcrypt with 12 rounds (2^12 = 4096 iterations) and random salting.
        Passwords longer than 72 bytes are truncated with a warning logged.
        
        Args:
            plain_password: Plaintext password string
        
        Returns:
            str: bcrypt hashed password (UTF-8 decoded), e.g., "$2b$12$..."
        
        Raises:
            ValueError: If password is empty or None
        
        Integration:
            - Used by login() to hash passwords before save_session()
            - Used by session_persistence.save_session() for storage
        
        Example:
            hashed = zcli.auth.hash_password("my_secure_password")
            # Returns: "$2b$12$abc123..."
        """
        return self.password_security.hash_password(plain_password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a bcrypt hash.
        
        Delegates to: password_security.verify_password()
        
        Uses timing-safe comparison to prevent timing attacks.
        
        Args:
            plain_password: Plaintext password to verify
            hashed_password: bcrypt hashed password (from database/storage)
        
        Returns:
            bool: True if password matches, False otherwise
        
        Integration:
            - Used by authentication.login() for password verification
            - Used by session_persistence.load_session() for persistent sessions
        
        Example:
            is_valid = zcli.auth.verify_password("password123", "$2b$12$...")
            if is_valid:
                print("Password correct!")
        """
        return self.password_security.verify_password(plain_password, hashed_password)
    
    # ════════════════════════════════════════════════════════════════════════════
    # LAYER 1: ZSESSION AUTHENTICATION (Facade → authentication module)
    # ════════════════════════════════════════════════════════════════════════════
    
    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        server_url: Optional[str] = None,
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        Authenticate user (zSession) and optionally persist session.
        
        Delegates to: authentication.login() + session_persistence.save_session()
        
        This method handles Layer 1 (zSession) authentication for internal zCLI/Zolo
        users. Supports both local (prompt) and remote (server_url) authentication.
        
        Args:
            username: Username for authentication (prompts if None)
            password: Password for authentication (prompts if None)
            server_url: Optional remote Zolo server URL for authentication
            persist: If True, save session to sessions.db (default: True)
        
        Returns:
            Dict: {"status": "success"|"fail"|"pending", "user": {...}}
                - status="success": Authentication successful
                - status="fail": Invalid credentials
                - status="pending": Remote auth initiated (async)
        
        Integration:
            - Uses zDisplay generic events for prompts and feedback
            - Uses zComm for remote authentication (comm_http.py)
            - Uses session_persistence.save_session() if persist=True
            - Updates session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
        
        Context Awareness:
            After successful login, active_context is set to:
            - "zSession" if no app authenticated
            - "dual" if app already authenticated
        
        Example:
            # Basic login (prompts for credentials)
            result = zcli.auth.login()
            
            # Login with credentials
            result = zcli.auth.login("user@zolo.com", "password", persist=True)
            
            # Remote authentication
            result = zcli.auth.login("user", "pass", server_url="https://zolo.com")
        """
        result = self.authentication.login(username, password, server_url, persist)
        
        # Handle session persistence if login was successful
        if result.get(KEY_STATUS) == STATUS_SUCCESS and result.get(KEY_PERSIST):
            credentials = result.get(KEY_CREDENTIALS)
            password_for_hash = result.get(KEY_PASSWORD)
            
            if credentials and password_for_hash:
                # Hash password and save session to SQLite
                password_hash = self.hash_password(password_for_hash)
                self.session_persistence.save_session(
                    username=credentials.get(KEY_USERNAME),
                    password_hash=password_hash,
                    user_id=credentials.get(KEY_USER_ID),
                    role=credentials.get(KEY_ROLE, DEFAULT_ROLE)
                )
        
        # Clean up sensitive data before returning (security best practice)
        if KEY_PASSWORD in result:
            del result[KEY_PASSWORD]
        if KEY_PERSIST in result:
            del result[KEY_PERSIST]
        
        return result
    
    def logout(
        self,
        context: str = CONTEXT_ZSESSION,
        app_name: Optional[str] = None,
        delete_persistent: bool = True
    ) -> Dict[str, str]:
        """
        Clear session authentication and optionally delete persistent session.
        
        Delegates to: authentication.logout() + session_persistence cleanup
        
        Supports context-aware logout for all three authentication tiers:
        - "zSession": Logout from zSession only
        - "application": Logout from specific app (requires app_name)
        - "all_apps": Logout from all authenticated apps
        - "all": Logout from everything (zSession + all apps)
        
        Args:
            context: Authentication context to logout from (default: "zSession")
                    - "zSession": Logout zCLI/Zolo user
                    - "application": Logout specific app user (requires app_name)
                    - "all_apps": Logout from all apps
                    - "all": Logout from zSession and all apps
            app_name: App name for "application" context logout (optional)
            delete_persistent: If True, delete SQLite session entry (default: True)
        
        Returns:
            Dict: {"status": "success", "cleared": ["zSession", "app1", ...]}
        
        Integration:
            - Uses zDisplay generic events for logout feedback
            - Uses zData to delete persistent session (if delete_persistent=True)
            - Clears session[SESSION_KEY_ZAUTH] based on context
        
        Context Behavior:
            After logout, active_context is updated:
            - "zSession" logout: context → "application" (if app exists) or None
            - "application" logout: context → "zSession" (if exists) or None
            - "all" logout: context → None
        
        Examples:
            # Logout from zSession only
            zcli.auth.logout()
            
            # Logout from specific app
            zcli.auth.logout(context="application", app_name="my_store")
            
            # Logout from all apps but keep zSession
            zcli.auth.logout(context="all_apps")
            
            # Logout from everything
            zcli.auth.logout(context="all", delete_persistent=True)
        """
        result = self.authentication.logout(
            context=context,
            app_name=app_name,
            delete_persistent=delete_persistent
        )
        
        # Delete persistent session from SQLite if requested
        if result.get(KEY_DELETE_PERSISTENT) and result.get(KEY_USERNAME):
            try:
                # Check if zData handler is ready and schema is loaded
                if (self.zcli.data.handler and 
                    self.zcli.data.schema.get(META_KEY, {}).get(DATA_LABEL_KEY) == DATA_LABEL_AUTH):
                    # Use declarative zData delete operation
                    self.zcli.data.delete(
                        table=TABLE_SESSIONS,
                        where=f"{KEY_USERNAME} = '{result.get(KEY_USERNAME)}'"
                    )
                    self.logger.info(f"{LOG_PREFIX} Persistent session deleted for user: {result.get(KEY_USERNAME)}")
            except Exception as e:
                self.logger.error(f"{LOG_PREFIX} Error deleting persistent session: {e}")
        
        return {KEY_STATUS: STATUS_SUCCESS}
    
    def status(self) -> Dict[str, Any]:
        """
        Show current authentication status for all tiers.
        
        Delegates to: authentication.status()
        
        Returns comprehensive authentication status including:
        - zSession authentication (username, role)
        - Application authentications (all apps)
        - Active context (zSession, application, dual)
        - Dual mode status
        
        Returns:
            Dict: {
                "status": "authenticated"|"not_authenticated",
                "user": {...},  # Current user based on active_context
                "zsession": {...},  # zSession auth data
                "applications": {...},  # All app auth data
                "active_context": "zSession"|"application"|"dual",
                "dual_mode": bool
            }
        
        Integration:
            - Uses zDisplay generic events for status display
            - Reads from session[SESSION_KEY_ZAUTH]
        
        Example:
            status = zcli.auth.status()
            print(f"Authenticated: {status['status']}")
            print(f"Current user: {status['user']}")
            print(f"Active context: {status['active_context']}")
        """
        return self.authentication.status()
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated in ANY context.
        
        Delegates to: authentication.is_authenticated()
        
        Returns True if:
        - zSession is authenticated, OR
        - At least one application is authenticated
        
        Returns:
            bool: True if authenticated in any context, False otherwise
        
        Context Awareness:
            This checks for ANY authentication. For context-specific checks,
            use get_credentials() or get_app_user(app_name).
        
        Example:
            if zcli.auth.is_authenticated():
                print("User is authenticated")
            else:
                print("Please login")
        """
        return self.authentication.is_authenticated()
    
    def get_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Get current zSession authentication data.
        
        Delegates to: authentication.get_credentials()
        
        Returns zSession (Layer 1) authentication data only.
        For application user data, use get_app_user(app_name).
        
        Returns:
            Optional[Dict]: {
                "username": str,
                "user_id": str,
                "role": str,
                "server_url": str (optional)
            }
            Returns None if not authenticated.
        
        Integration:
            - Reads from session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
        
        Example:
            creds = zcli.auth.get_credentials()
            if creds:
                print(f"Logged in as: {creds['username']}")
                print(f"Role: {creds['role']}")
        """
        return self.authentication.get_credentials()
    
    # ════════════════════════════════════════════════════════════════════════════
    # LAYER 2: APPLICATION AUTHENTICATION (Facade → authentication module)
    # ════════════════════════════════════════════════════════════════════════════
    
    def authenticate_app_user(
        self,
        app_name: str,
        token: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Authenticate an application user (Layer 2 - Multi-App).
        
        Delegates to: authentication.authenticate_app_user()
        
        This method handles application-specific user authentication for apps
        BUILT with zCLI. Each app maintains independent user identities and
        credentials. Multiple apps can be authenticated simultaneously.
        
        Args:
            app_name: Application identifier (e.g., "my_store", "admin_panel")
            token: Application-specific authentication token
            config: Optional authentication configuration
                   {"auth_endpoint": str, "verify_ssl": bool, ...}
        
        Returns:
            Dict: {
                "status": "success"|"fail",
                "user": {
                    "user_id": str,
                    "role": str,
                    "username": str (optional),
                    ...app-specific fields...
                },
                "app_name": str
            }
        
        Integration:
            - Uses zComm for remote app authentication (comm_http.py)
            - Updates session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]
            - If zSession also authenticated, sets dual_mode = True
        
        Context Behavior:
            After successful app authentication:
            - If zSession also authenticated: active_context → "dual"
            - If zSession not authenticated: active_context → "application"
        
        Example:
            # Authenticate store customer
            result = zcli.auth.authenticate_app_user(
                app_name="my_store",
                token="customer_token_123",
                config={"auth_endpoint": "https://store.com/api/auth"}
            )
            
            if result["status"] == "success":
                print(f"App user: {result['user']['user_id']}")
        """
        return self.authentication.authenticate_app_user(app_name, token, config)
    
    def switch_app(self, app_name: str) -> bool:
        """
        Switch active application context.
        
        Delegates to: authentication.switch_app()
        
        Changes the active_context to focus on a specific authenticated app.
        The app must already be authenticated via authenticate_app_user().
        
        Args:
            app_name: Application name to switch to
        
        Returns:
            bool: True if switch successful, False if app not authenticated
        
        Integration:
            - Updates session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT]
            - RBAC checks will now use this app's user for role/permission checks
        
        Example:
            # Authenticate multiple apps
            zcli.auth.authenticate_app_user("store", token1, config1)
            zcli.auth.authenticate_app_user("admin", token2, config2)
            
            # Switch between apps
            zcli.auth.switch_app("store")
            # RBAC now checks store user's roles
            
            zcli.auth.switch_app("admin")
            # RBAC now checks admin user's roles
        """
        return self.authentication.switch_app(app_name)
    
    def get_app_user(self, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Get authentication data for a specific application.
        
        Delegates to: authentication.get_app_user()
        
        Returns the authenticated user data for the specified app.
        Returns None if the app is not currently authenticated.
        
        Args:
            app_name: Application name to get user data for
        
        Returns:
            Optional[Dict]: {
                "user_id": str,
                "role": str,
                "username": str (optional),
                ...app-specific fields...
            }
            Returns None if app not authenticated.
        
        Integration:
            - Reads from session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]
        
        Example:
            store_user = zcli.auth.get_app_user("my_store")
            if store_user:
                print(f"Store user: {store_user['user_id']}")
                print(f"Store role: {store_user['role']}")
            else:
                print("Not authenticated with store")
        """
        return self.authentication.get_app_user(app_name)
    
    # ════════════════════════════════════════════════════════════════════════════
    # CONTEXT MANAGEMENT (Facade → authentication module)
    # ════════════════════════════════════════════════════════════════════════════
    
    def set_active_context(self, context: str) -> bool:
        """
        Set the active authentication context (zSession, application, or dual).
        
        Delegates to: authentication.set_active_context()
        
        Controls which authentication tier is considered "active" for RBAC checks
        and get_active_user() calls. In dual mode, RBAC uses OR logic (either
        context can grant access).
        
        Args:
            context: Context to activate
                    - "zSession": Use zSession auth for RBAC
                    - "application": Use app auth for RBAC (requires authenticated app)
                    - "dual": Use both (OR logic - either can grant access)
        
        Returns:
            bool: True if context set successfully, False if requested context unavailable
                 (e.g., trying to set "application" when no apps authenticated)
        
        Integration:
            - Updates session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT]
            - Updates session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] for "dual"
            - Affects RBAC checks (rbac.has_role, rbac.has_permission)
        
        RBAC Behavior:
            - "zSession": Only zSession user's roles/permissions checked
            - "application": Only active app user's roles/permissions checked
            - "dual": BOTH checked with OR logic (either grants access)
        
        Example:
            # Login as Zolo user
            zcli.auth.login("admin@zolo.com", "password")
            
            # Authenticate as store owner
            zcli.auth.authenticate_app_user("store", "owner_token", config)
            
            # Set dual mode (both contexts active)
            zcli.auth.set_active_context("dual")
            
            # RBAC now checks both contexts with OR logic
            if zcli.auth.has_role("admin"):  # True if admin in EITHER context
                print("Admin access granted")
        """
        return self.authentication.set_active_context(context)
    
    def get_active_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active user based on active_context.
        
        Delegates to: authentication.get_active_user()
        
        Returns the user data for the currently active authentication context:
        - "zSession": Returns zSession user
        - "application": Returns active app user
        - "dual": Returns zSession user (by convention)
        
        Returns:
            Optional[Dict]: Current active user data, or None if not authenticated
                          Structure depends on active_context:
                          - zSession: {"username", "user_id", "role", ...}
                          - application: {"user_id", "role", ...app-specific...}
        
        Integration:
            - Reads from session[SESSION_KEY_ZAUTH] based on active_context
        
        Example:
            zcli.auth.set_active_context("application")
            user = zcli.auth.get_active_user()
            print(f"Active user: {user['user_id']}")
            
            zcli.auth.set_active_context("zSession")
            user = zcli.auth.get_active_user()
            print(f"Active user: {user['username']}")
        """
        return self.authentication.get_active_user()
    
    # ════════════════════════════════════════════════════════════════════════════
    # RBAC - CONTEXT-AWARE (Facade → rbac module)
    # ════════════════════════════════════════════════════════════════════════════
    
    def has_role(self, required_role: Union[str, List[str], None]) -> bool:
        """
        Check if the current user has the required role (context-aware).
        
        Delegates to: rbac.has_role()
        
        Checks roles based on active_context:
        - "zSession": Checks zSession user's role
        - "application": Checks active app user's role
        - "dual": Checks BOTH with OR logic (either context can grant)
        
        Args:
            required_role: Role name (str), list of roles (list), or None
                         - str: User must have this exact role
                         - list: User must have ANY of these roles (OR logic)
                         - None: Public access (always returns True)
        
        Returns:
            bool: True if user has the required role(s), False otherwise
        
        Integration:
            - Used by zWizard for zVaF menu access control
            - Reads role from session[SESSION_KEY_ZAUTH] based on active_context
        
        Dual-Mode Behavior:
            In dual mode, returns True if user has role in EITHER context:
            - zSession user has "admin" OR
            - Active app user has "admin"
        
        Examples:
            # Single role check
            if zcli.auth.has_role("admin"):
                print("User is admin")
            
            # Multiple roles (OR logic)
            if zcli.auth.has_role(["admin", "moderator"]):
                print("User is admin OR moderator")
            
            # Public access
            if zcli.auth.has_role(None):
                print("Always True - public access")
        """
        return self.rbac.has_role(required_role)
    
    def has_permission(self, required_permission: Union[str, List[str]]) -> bool:
        """
        Check if the current user has the required permission (context-aware).
        
        Delegates to: rbac.has_permission()
        
        Checks permissions based on active_context:
        - "zSession": Checks zSession user's permissions
        - "application": Checks active app user's permissions
        - "dual": Checks BOTH with OR logic (either context can grant)
        
        Permissions are stored in SQLite (permissions table) and checked via
        declarative zData operations.
        
        Args:
            required_permission: Permission name (str) or list of permissions (list)
                               - str: User must have this exact permission
                               - list: User must have ANY of these permissions (OR logic)
        
        Returns:
            bool: True if user has the required permission(s), False otherwise
        
        Integration:
            - Permissions stored in SQLite via zData
            - Used by zWizard for granular access control
        
        Dual-Mode Behavior:
            In dual mode, returns True if user has permission in EITHER context:
            - zSession user has "data.delete" OR
            - Active app user has "data.delete"
        
        Examples:
            # Single permission
            if zcli.auth.has_permission("users.delete"):
                # Delete user operation
            
            # Multiple permissions (OR logic)
            if zcli.auth.has_permission(["data.read", "data.write"]):
                # User can read OR write
        """
        return self.rbac.has_permission(required_permission)
    
    def grant_permission(
        self,
        user_id: str,
        permission: str,
        granted_by: Optional[str] = None
    ) -> bool:
        """
        Grant a permission to a user (admin-only operation).
        
        Delegates to: rbac.grant_permission()
        
        Stores permission in SQLite (permissions table) via declarative zData
        operations. Permissions are persistent across sessions.
        
        Args:
            user_id: User ID to grant permission to
            permission: Permission name (e.g., "users.delete", "system.shutdown")
            granted_by: Optional admin username who granted this permission
        
        Returns:
            bool: True if permission was granted successfully, False otherwise
        
        Integration:
            - Uses zData.insert() for persistence
            - Requires auth.db SQLite database (permissions table)
        
        Example:
            # Grant permission
            success = zcli.auth.grant_permission(
                user_id="user123",
                permission="users.delete",
                granted_by="admin@zolo.com"
            )
            
            if success:
                print("Permission granted")
        """
        return self.rbac.grant_permission(user_id, permission, granted_by)
    
    def revoke_permission(self, user_id: str, permission: str) -> bool:
        """
        Revoke a permission from a user (admin-only operation).
        
        Delegates to: rbac.revoke_permission()
        
        Removes permission from SQLite (permissions table) via declarative zData
        operations.
        
        Args:
            user_id: User ID to revoke permission from
            permission: Permission name to revoke
        
        Returns:
            bool: True if permission was revoked successfully, False otherwise
        
        Integration:
            - Uses zData.delete() for persistence
            - Requires auth.db SQLite database (permissions table)
        
        Example:
            # Revoke permission
            success = zcli.auth.revoke_permission(
                user_id="user123",
                permission="users.delete"
            )
            
            if success:
                print("Permission revoked")
        """
        return self.rbac.revoke_permission(user_id, permission)
    
    # ════════════════════════════════════════════════════════════════════════════
    # DEPRECATED METHODS (Backwards Compatibility)
    # ════════════════════════════════════════════════════════════════════════════
    
    def _ensure_sessions_db(self) -> bool:
        """
        DEPRECATED since v1.5.4: Use session_persistence.ensure_sessions_db() directly.
        
        Alternative:
            zcli.auth.session_persistence.ensure_sessions_db()
        
        Migration:
            # Old (deprecated)
            zcli.auth._ensure_sessions_db()
            
            # New (direct module access)
            zcli.auth.session_persistence.ensure_sessions_db()
        
        Removal planned: v1.6.0
        
        Kept for backwards compatibility with existing tests.
        """
        return self.session_persistence.ensure_sessions_db()
    
    def _load_session(self) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED since v1.5.4: Use session_persistence.load_session() directly.
        
        Alternative:
            zcli.auth.session_persistence.load_session(identifier, identifier_type)
        
        Migration:
            # Old (deprecated - no parameters)
            session_data = zcli.auth._load_session()
            
            # New (explicit parameters)
            session_data = zcli.auth.session_persistence.load_session(
                identifier="user@example.com",
                identifier_type="username"
            )
        
        Removal planned: v1.6.0
        
        Kept for backwards compatibility with existing tests.
        """
        return self.session_persistence.load_session()
    
    def _save_session(
        self,
        username: str,
        password_hash: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        DEPRECATED since v1.5.4: Use session_persistence.save_session() directly.
        
        Alternative:
            zcli.auth.session_persistence.save_session(username, password_hash, user_id, role)
        
        Migration:
            # Old (deprecated - role from session)
            zcli.auth._save_session("user@example.com", hashed_pwd, "123")
            
            # New (explicit role parameter)
            zcli.auth.session_persistence.save_session(
                username="user@example.com",
                password_hash=hashed_pwd,
                user_id="123",
                role="admin"
            )
        
        Removal planned: v1.6.0
        
        Kept for backwards compatibility with existing tests.
        """
        # Get role from session (fallback to session_persistence behavior)
        role = self.session.get(SESSION_KEY_ZAUTH, {}).get(KEY_ROLE, DEFAULT_ROLE)
        return self.session_persistence.save_session(username, password_hash, user_id, role)
    
    def _cleanup_expired(self) -> int:
        """
        DEPRECATED since v1.5.4: Use session_persistence.cleanup_expired() directly.
        
        Alternative:
            zcli.auth.session_persistence.cleanup_expired()
        
        Migration:
            # Old (deprecated)
            count = zcli.auth._cleanup_expired()
            
            # New (direct module access)
            count = zcli.auth.session_persistence.cleanup_expired()
        
        Removal planned: v1.6.0
        
        Kept for backwards compatibility with existing tests.
        """
        return self.session_persistence.cleanup_expired()
    
    def _authenticate_remote(
        self,
        username: str,
        password: str,
        server_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        DEPRECATED since v1.5.4: Use authentication.authenticate_remote() directly.
        
        Alternative:
            zcli.auth.authentication.authenticate_remote(username, password, server_url)
        
        Migration:
            # Old (deprecated)
            result = zcli.auth._authenticate_remote("user", "pass", "https://zolo.com")
            
            # New (direct module access)
            result = zcli.auth.authentication.authenticate_remote(
                username="user",
                password="pass",
                server_url="https://zolo.com"
            )
        
        Removal planned: v1.6.0
        
        Kept for backwards compatibility.
        """
        return self.authentication.authenticate_remote(username, password, server_url)
    
    def _ensure_permissions_db(self) -> bool:
        """
        DEPRECATED since v1.5.4: Use rbac.ensure_permissions_db() directly.
        
        Alternative:
            zcli.auth.rbac.ensure_permissions_db()
        
        Migration:
            # Old (deprecated)
            zcli.auth._ensure_permissions_db()
            
            # New (direct module access)
            zcli.auth.rbac.ensure_permissions_db()
        
        Removal planned: v1.6.0
        
        Kept for backwards compatibility with existing tests.
        """
        return self.rbac.ensure_permissions_db()
