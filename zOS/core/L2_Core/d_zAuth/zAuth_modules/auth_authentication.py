"""
Authentication Module - CORE three-tier authentication and session management (v1.5.4+)

ARCHITECTURE OVERVIEW

This is the CORE authentication module for the zCLI framework, implementing a
sophisticated three-tier authentication model that supports:

1. **zSession Authentication** (Internal zCLI/Zolo users)
2. **Application Authentication** (External users of zCLI-built applications)
3. **Dual-Mode Authentication** (Both contexts active simultaneously)

The module provides a unified API for authentication operations across all three
tiers while maintaining complete isolation between authentication contexts.

THREE-TIER AUTHENTICATION MODEL

**Layer 1 - zSession Authentication (Internal Users):**
    Purpose:
        - Authenticate zCLI/Zolo platform users
        - Grant access to premium zCLI features, plugins, and Zolo cloud services
        - Manage developer accounts and zCLI premium subscriptions
    
    Authentication Flow:
        1. User calls: zcli.auth.login(username, password)
        2. Credentials validated against Zolo authentication server
        3. Session structure populated: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
        4. Active context set to: CONTEXT_ZSESSION
    
    Session Structure:
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION] = {
            ZAUTH_KEY_AUTHENTICATED: True,
            ZAUTH_KEY_ID: "user_id",
            ZAUTH_KEY_USERNAME: "username",
            ZAUTH_KEY_ROLE: "admin|user|developer",
            ZAUTH_KEY_API_KEY: "api_key_token"
        }
    
    Use Cases:
        - zCLI developer authenticating to access premium plugins
        - Store owner authenticating to Zolo cloud for zCLI features
        - Admin managing zCLI system settings

**Layer 2 - Application Authentication (External Users):**
    Purpose:
        - Authenticate end-users of applications BUILT with zCLI
        - Enable multi-app simultaneous authentication
        - Isolate application user data from zCLI system users
    
    Authentication Flow:
        1. App calls: zcli.auth.authenticate_app_user(app_name, token, config)
        2. Token validated against application's user database (via zData)
        3. Session structure populated: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]
        4. Active context set to: CONTEXT_APPLICATION
        5. Active app set to: app_name
    
    Session Structure (Multi-App):
        session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS] = {
            "ecommerce_store": {
                ZAUTH_KEY_AUTHENTICATED: True,
                ZAUTH_KEY_ID: "store_user_123",
                ZAUTH_KEY_USERNAME: "customer@email.com",
                ZAUTH_KEY_ROLE: "customer",
                ZAUTH_KEY_API_KEY: "store_token_xyz"
            },
            "analytics_dashboard": {
                ZAUTH_KEY_AUTHENTICATED: True,
                ZAUTH_KEY_ID: "analytics_user_456",
                ZAUTH_KEY_USERNAME: "analyst@company.com",
                ZAUTH_KEY_ROLE: "analyst",
                ZAUTH_KEY_API_KEY: "analytics_token_abc"
            }
        }
    
    Use Cases:
        - Customer shopping on an eCommerce store built with zCLI
        - Employee accessing company analytics dashboard
        - Student logging into educational platform
        - Each app has independent user database and credentials

**Layer 3 - Dual-Mode Authentication (Both Contexts):**
    Purpose:
        - Enable simultaneous zSession AND application authentication
        - Allow zCLI developers to work on their own applications
        - Support admin/owner scenarios with dual identity
    
    Authentication Flow:
        1. User authenticates to zSession: zcli.auth.login()
        2. Same user authenticates to their app: zcli.auth.authenticate_app_user()
        3. System automatically detects both contexts are active
        4. Active context set to: CONTEXT_DUAL
        5. Dual mode flag set to: True
    
    Session Structure:
        session[SESSION_KEY_ZAUTH] = {
            ZAUTH_KEY_ACTIVE_CONTEXT: CONTEXT_DUAL,
            ZAUTH_KEY_DUAL_MODE: True,
            ZAUTH_KEY_ZSESSION: {...},  # zCLI developer credentials
            ZAUTH_KEY_APPLICATIONS: {
                "my_store": {...}  # Store owner credentials
            }
        }
    
    Use Cases:
        - Store owner analyzing their store data (zCLI analytics + store user)
        - Developer debugging their application (zCLI dev + app user)
        - Admin managing application settings (zCLI admin + app admin)

CONTEXT MANAGEMENT

The module maintains the following session keys for context management:

    session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT]: str
        - Indicates which authentication tier is currently active
        - Values: CONTEXT_ZSESSION, CONTEXT_APPLICATION, CONTEXT_DUAL
        - Determines which credentials are used by RBAC and permissions
    
    session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP]: str
        - Tracks which application is currently focused (multi-app support)
        - Only relevant when CONTEXT_APPLICATION or CONTEXT_DUAL
        - Used to retrieve correct app credentials from applications dict
    
    session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE]: bool
        - True when both zSession AND application are authenticated
        - False in single-context scenarios
        - Used by RBAC for OR logic (either context can grant access)

Context Switching:
    - Users can switch between contexts: zcli.auth.set_active_context("zSession")
    - Switching apps: zcli.auth.switch_app("analytics_dashboard")
    - Context automatically updates on login/logout operations

METHOD CATEGORIZATION

**Layer 1 Methods (zSession Authentication):**
    - login(username, password, server_url, persist) → Dict
    - is_authenticated() → bool
    - get_credentials() → Optional[Dict]
    - status() → Dict

**Layer 2 Methods (Application Authentication):**
    - authenticate_app_user(app_name, token, config) → Dict
    - switch_app(app_name) → bool
    - get_app_user(app_name) → Optional[Dict]

**Context Management Methods:**
    - set_active_context(context) → bool
    - get_active_user() → Optional[Dict]

**Logout Methods (Context-Aware):**
    - logout(context, app_name, delete_persistent) → Dict

**Remote Authentication Methods:**
    - authenticate_remote(username, password, server_url) → Dict

**Internal Helper Methods:**
    - _log(level, message) → None
    - _get_auth_data(context) → Optional[Dict]
    - _set_auth_data(context, data) → None
    - _create_status_response(status, **kwargs) → Dict
    - _check_session() → bool
    - _update_active_context() → None

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION WITH OTHER MODULES
═══════════════════════════════════════════════════════════════════════════════

**auth_password_security.py:**
    - login() uses PasswordSecurity.hash_password() for secure password storage
    - Bcrypt hashing with 12 rounds, random salting

**auth_session_persistence.py:**
    - login() returns persist flag for SessionPersistence to handle
    - logout() can delete persistent sessions from SQLite database

**authzRBAC.py:**
    - RBAC module queries active_context to determine authorization
    - Context-aware role/permission checks across all three tiers
    - Dual-mode uses OR logic (either context can grant access)

**zConfig (config_session.py):**
    - Imports all session constants (SESSION_KEY_ZAUTH, ZAUTH_KEY_*)
    - Maintains consistent session structure across subsystems

**zDisplay:**
    - All authentication feedback uses generic zDisplay events
    - Methods: success(), error(), warning(), text(), header()
    - Dual-mode compatible (Terminal + Bifrost)

**zComm (comm_http.py):**
    - authenticate_remote() uses zComm.http_post() for API communication
    - Secure HTTPS communication with Zolo authentication server

USAGE EXAMPLES

**Example 1: zSession Authentication (Internal User)**
    # Developer authenticates to zCLI
    result = zcli.auth.login("developer@zolo.com", "password123")
    # Session now contains zSession credentials
    # active_context = "zSession"
    
    # Check authentication status
    if zcli.auth.is_authenticated():
        creds = zcli.auth.get_credentials()
        print(f"Logged in as: {creds['username']} (role: {creds['role']})")

**Example 2: Application Authentication (External User)**
    # Customer authenticates to eCommerce store
    result = zcli.auth.authenticate_app_user(
        app_name="ecommerce_store",
        token="customer_token_xyz",
        config={"user_model": "@.store.users"}
    )
    # Session now contains application credentials
    # active_context = "application"
    # active_app = "ecommerce_store"

**Example 3: Dual-Mode Authentication (Both Contexts)**
    # Step 1: Developer authenticates to zCLI
    zcli.auth.login("developer@zolo.com", "password")
    
    # Step 2: Same developer authenticates to their store
    zcli.auth.authenticate_app_user("my_store", "store_token", {...})
    
    # System automatically detects dual-mode
    # active_context = "dual"
    # dual_mode = True
    
    # Get both credentials
    user = zcli.auth.get_active_user()
    # Returns: {"zSession": {...}, "application": {...}}

**Example 4: Context Switching**
    # Switch to zSession context
    zcli.auth.set_active_context("zSession")
    
    # Switch to application context
    zcli.auth.set_active_context("application")
    
    # Switch to dual mode
    zcli.auth.set_active_context("dual")

**Example 5: Multi-App Management**
    # Authenticate to multiple apps
    zcli.auth.authenticate_app_user("store", "token1", {...})
    zcli.auth.authenticate_app_user("analytics", "token2", {...})
    
    # Switch between apps
    zcli.auth.switch_app("store")
    zcli.auth.switch_app("analytics")
    
    # Get specific app credentials
    store_user = zcli.auth.get_app_user("store")
    analytics_user = zcli.auth.get_app_user("analytics")

**Example 6: Context-Aware Logout**
    # Logout from zCLI only
    zcli.auth.logout("zSession")
    
    # Logout from specific app
    zcli.auth.logout("application", app_name="store")
    
    # Logout from all apps (keep zSession)
    zcli.auth.logout("all_apps")
    
    # Logout from everything
    zcli.auth.logout("all")

THREAD SAFETY & CONCURRENT AUTHENTICATION

This module operates on the zCLI session object, which is NOT thread-safe by design.
Each zCLI instance maintains a single session dictionary. For multi-threaded
applications, each thread should use its own zCLI instance.

Multi-app authentication within a SINGLE session is fully supported and isolated
by app_name keys in the applications dictionary.
"""

from zOS import os, Dict, Optional, Any, Tuple
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    SESSION_KEY_ZAUTH,         # CRITICAL: Session key for all auth data
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_APPLICATIONS,    # Multi-app support
    ZAUTH_KEY_ACTIVE_APP,      # Tracks focused app
    ZAUTH_KEY_AUTHENTICATED,
    ZAUTH_KEY_ID,
    ZAUTH_KEY_USERNAME,
    ZAUTH_KEY_ROLE,
    ZAUTH_KEY_API_KEY,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_DUAL_MODE,
    CONTEXT_ZSESSION,
    CONTEXT_APPLICATION,
    CONTEXT_DUAL
)
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SessionConfig


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Import centralized constants
from .auth_constants import (
    # Public constants
    STATUS_SUCCESS,
    STATUS_FAIL,
    STATUS_ERROR,
    STATUS_PENDING,
    KEY_STATUS,
    KEY_REASON,
    KEY_CREDENTIALS,
    KEY_USER,
    KEY_CONTEXT,
    KEY_CLEARED,
    KEY_PERSIST,
    KEY_DELETE_PERSISTENT,
    KEY_PASSWORD,
    KEY_APP_NAME,
    KEY_USERNAME,
    KEY_SERVER_URL,
    TABLE_SESSIONS,
    FIELD_USERNAME,
    FIELD_PASSWORD,
    FIELD_ROLE,
    FIELD_API_KEY,
    DEFAULT_SERVER_URL,
    DEFAULT_USER_MODEL,
    DEFAULT_ID_FIELD,
    DEFAULT_USERNAME_FIELD,
    DEFAULT_ROLE_FIELD,
    DEFAULT_API_KEY_FIELD,
    DEFAULT_PERSIST,
    DEFAULT_DELETE_PERSISTENT,
    ENV_USE_REMOTE_API,
    ENV_API_URL,
    ENV_TRUE,
    HTTP_MODE_KEY,
    HTTP_MODE_TERMINAL,
    HTTP_DATA_KEY,
    PLACEHOLDER_USER_ID,
    PLACEHOLDER_ROLE,
    # Internal constants (private)
    _LOG_PREFIX_AUTH,
    _LOG_LEVEL_INFO,
    _LOG_LEVEL_WARNING,
    _LOG_LEVEL_ERROR,
    _LOG_LEVEL_DEBUG,
    _LOG_REMOTE_AUTH,
    _LOG_REMOTE_SUCCESS,
    _LOG_REMOTE_FAIL,
    _LOG_AUTH_FAILED,
    _LOG_LOGOUT_ZSESSION,
    _LOG_LOGOUT_APP,
    _LOG_LOGOUT_ALL_APPS,
    _LOG_APP_AUTH_SUCCESS,
    _LOG_APP_SWITCH,
    _LOG_APP_SWITCH_FAIL,
    _LOG_CONTEXT_SET,
    _LOG_CONTEXT_INVALID,
    _LOG_CONTEXT_NO_ZSESSION,
    _LOG_CONTEXT_NO_APP,
    _LOG_CONTEXT_NO_DUAL,
    _LOG_SESSION_DELETE,
    _LOG_SESSION_DELETE_FAIL,
    _LOG_APP_AUTH_ERROR,
    _LOG_CONTEXT_UPDATED,
    _LOG_DUAL_MODE_ACTIVATED,
    _ERR_NO_SESSION,
    _ERR_INVALID_CREDS,
    _ERR_CONNECTION_FAILED,
    _ERR_APP_NAME_REQUIRED,
    _ERR_APP_NOT_AUTH,
    _ERR_INVALID_CONTEXT,
    _ERR_NO_ACTIVE_APP,
    _MSG_AWAITING_GUI,
    _MSG_NOT_AUTHENTICATED,
)

# Session Access Helpers (DRY utilities)
from .auth_helpers import (
    get_auth_data,
    get_zsession_data,
    get_applications_data,
    get_active_context,
)

# Module uses _LOG_PREFIX_AUTH as LOG_PREFIX for compatibility
LOG_PREFIX = _LOG_PREFIX_AUTH


# Authentication Class - Core Three-Tier Model

class Authentication:
    """
    CORE authentication module implementing three-tier authentication model.
    
    This class is the primary authentication interface for the zCLI framework,
    providing unified API for:
    
    **Three-Tier Authentication:**
        1. zSession Auth (Internal zCLI/Zolo users)
        2. Application Auth (External users of zCLI-built apps)
        3. Dual-Mode Auth (Both contexts active simultaneously)
    
    **Architecture:**
        - Facade pattern: Delegates to PasswordSecurity, SessionPersistence, RBAC
        - Context-aware: All operations respect active_context
        - Multi-app capable: Simultaneous authentication to multiple applications
        - Session-based: All auth state stored in session[SESSION_KEY_ZAUTH]
    
    **Session Structure:**
        session[SESSION_KEY_ZAUTH] = {
            ZAUTH_KEY_ACTIVE_CONTEXT: "zSession"|"application"|"dual",
            ZAUTH_KEY_ACTIVE_APP: "app_name",
            ZAUTH_KEY_DUAL_MODE: True|False,
            ZAUTH_KEY_ZSESSION: {
                ZAUTH_KEY_AUTHENTICATED: bool,
                ZAUTH_KEY_ID: str,
                ZAUTH_KEY_USERNAME: str,
                ZAUTH_KEY_ROLE: str,
                ZAUTH_KEY_API_KEY: str
            },
            ZAUTH_KEY_APPLICATIONS: {
                "app1": {...},  # Same structure as zSession
                "app2": {...},
                ...
            }
        }
    
    **Method Categories:**
        Layer 1 (zSession): login, is_authenticated, get_credentials, status
        Layer 2 (Application): authenticate_app_user, switch_app, get_app_user
        Context Management: set_active_context, get_active_user
        Logout: logout (context-aware)
        Remote: authenticate_remote
        Internal: _log, _get_auth_data, _set_auth_data, etc.
    
    **Integration:**
        - auth_password_security: Password hashing (bcrypt)
        - auth_session_persistence: SQLite persistent sessions
        - authzRBAC: Context-aware role/permission checks
        - zConfig: Session structure constants
        - zDisplay: Authentication UI events
        - zComm: Remote API authentication
    
    **Context Management:**
        - Active context determines which credentials are used
        - RBAC checks active_context for authorization
        - Dual-mode uses OR logic (either context can grant access)
        - Context automatically updates on login/logout
    
    **Thread Safety:**
        NOT thread-safe by design. Each thread should use its own zCLI instance.
        Multi-app authentication within a single session is fully supported.
    
    **Usage:**
        # zSession authentication
        zcli.auth.login("user@zolo.com", "password")
        
        # Application authentication
        zcli.auth.authenticate_app_user("store", "token", config)
        
        # Context switching
        zcli.auth.set_active_context("dual")
        
        # Logout
        zcli.auth.logout("all")
    
    Attributes:
        zcli: zCLI instance (provides session, display, comm, logger)
        session: Session dictionary (zCLI.session)
        logger: Logger instance (zCLI.logger)
    """
    
    # Class-level type declarations
    zcli: Any
    session: Dict[str, Any]
    logger: Any
    
    def __init__(self, zcli: Any) -> None:
        """Initialize authentication module.
        
        Args:
            zcli: zCLI instance (provides access to session, display, comm, logger)
        
        Returns:
            None
        """
        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTERNAL HELPER METHODS (Private)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _log(self, level: str, message: str) -> None:
        """Centralized logging with LOG_PREFIX.
        
        Args:
            level: Log level (info, warning, error, debug)
            message: Log message (prefix already included in constants)
        
        Returns:
            None
        
        Example:
            self._log(LOG_LEVEL_INFO, LOG_REMOTE_SUCCESS)
            self._log(LOG_LEVEL_ERROR, f"{LOG_APP_AUTH_ERROR}: {error}")
        """
        if level == LOG_LEVEL_INFO:
            self.logger.info(message)
        elif level == LOG_LEVEL_WARNING:
            self.logger.warning(message)
        elif level == LOG_LEVEL_ERROR:
            self.logger.error(message)
        elif level == LOG_LEVEL_DEBUG:
            self.logger.debug(message)
    
    def _check_session(self) -> bool:
        """Validate that session exists.
        
        Returns:
            bool: True if session exists, False otherwise
        
        Example:
            if not self._check_session():
                return self._create_status_response(STATUS_ERROR, reason=ERR_NO_SESSION)
        """
        return self.session is not None
    
    def _create_status_response(self, status: str, **kwargs: Any) -> Dict[str, Any]:
        """Create standardized status response dictionary.
        
        Args:
            status: Status value (STATUS_SUCCESS, STATUS_FAIL, STATUS_ERROR, STATUS_PENDING)
            **kwargs: Additional key-value pairs to include in response
        
        Returns:
            dict: Standardized status response with KEY_STATUS and additional keys
        
        Example:
            return self._create_status_response(STATUS_SUCCESS, user=user_data, context="zSession")
            return self._create_status_response(STATUS_ERROR, reason=ERR_NO_SESSION)
        """
        response = {KEY_STATUS: status}
        response.update(kwargs)
        return response
    
    def _update_active_context(self) -> None:
        """Update active_context based on current authentication state.
        
        Automatically determines the correct active_context by checking:
        1. zSession authentication status
        2. Application authentication status (active_app)
        3. Sets context to: zSession, application, dual, or None
        
        Returns:
            None
        
        Context Logic:
            - Both authenticated → CONTEXT_DUAL (dual_mode = True)
            - Only zSession authenticated → CONTEXT_ZSESSION
            - Only application authenticated → CONTEXT_APPLICATION
            - Neither authenticated → None
        
        Example:
            # After login, update context automatically
            self._update_active_context()
        """
        if not self._check_session():
            return
        
        zsession_auth = get_zsession_data(self.session).get(ZAUTH_KEY_AUTHENTICATED, False)
        active_app = self.session.get(SESSION_KEY_ZAUTH, {}).get(ZAUTH_KEY_ACTIVE_APP)
        apps = get_applications_data(self.session)
        app_auth = active_app and active_app in apps
        
        if zsession_auth and app_auth:
            # Both authenticated → dual mode
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_DUAL
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = True
            self._log(LOG_LEVEL_INFO, LOG_DUAL_MODE_ACTIVATED)
        elif zsession_auth:
            # Only zSession authenticated
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_ZSESSION
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
        elif app_auth:
            # Only application authenticated
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_APPLICATION
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
        else:
            # Neither authenticated
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = None
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 1: ZSESSION AUTHENTICATION (Internal zCLI/Zolo Users)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        server_url: Optional[str] = None,
        persist: bool = DEFAULT_PERSIST
    ) -> Dict[str, Any]:
        """Authenticate zCLI/Zolo user to zSession context (Layer 1).
        
        Authenticates internal zCLI/Zolo users against the Zolo authentication server.
        On success, populates session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION] with
        user credentials and sets active_context to CONTEXT_ZSESSION.
        
        Args:
            username: Username for authentication (optional, will prompt if None)
            password: Password for authentication (optional, will prompt if None)
            server_url: Optional remote server URL (defaults to ZOLO_API_URL env var)
            persist: If True, save session to SQLite database (default: True)
        
        Returns:
            dict: Status response with one of:
                - {KEY_STATUS: STATUS_SUCCESS, KEY_CREDENTIALS: {...}, KEY_PERSIST: bool, KEY_PASSWORD: str}
                - {KEY_STATUS: STATUS_FAIL, KEY_REASON: str}
                - {KEY_STATUS: STATUS_PENDING, KEY_REASON: MSG_AWAITING_GUI} (GUI mode)
        
        Context Behavior:
            - Sets active_context to CONTEXT_ZSESSION
            - If application already authenticated → automatically switches to CONTEXT_DUAL
            - Updates dual_mode flag accordingly
        
        Integration:
            - zDisplay: Uses zEvents.zAuth.login_prompt() for credential collection
            - zDisplay: Uses zEvents.zAuth.login_success() for success feedback
            - zDisplay: Uses zEvents.zAuth.login_failure() for failure feedback
            - zComm: Uses comm.http_post() for remote authentication
            - SessionPersistence: Caller should persist session if persist=True
        
        Example:
            # Interactive login (prompts for credentials)
            result = zcli.auth.login()
            
            # Programmatic login
            result = zcli.auth.login("user@zolo.com", "password123")
            
            # With custom server
            result = zcli.auth.login("user", "pass", server_url="https://api.zolo.com")
            
            # Check result
            if result[KEY_STATUS] == STATUS_SUCCESS:
                print(f"Logged in as: {result[KEY_CREDENTIALS][KEY_USERNAME]}")
        
        Security:
            - Passwords are hashed with bcrypt before persistence (by SessionPersistence)
            - API keys are generated by authentication server
            - HTTPS communication with remote server
        """
        # Get credentials (prompt if not provided)
        username, password, pending_response = self._get_login_credentials(username, password)
        if pending_response:
            return pending_response
        
        # Try remote authentication
        if os.getenv(ENV_USE_REMOTE_API, "false").lower() == ENV_TRUE:
            result = self.authenticate_remote(username, password, server_url)
            if result.get(KEY_STATUS) == STATUS_SUCCESS:
                return self._handle_successful_login(result, persist, password)
        
        # Authentication failed
        return self._handle_failed_login()
    
    def _get_login_credentials(
        self,
        username: Optional[str],
        password: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Get login credentials, prompting if not provided. Returns (username, password, pending_response)."""
        if username and password:
            return username, password, None
        
        # Try GUI mode first
        pending_response = self._try_gui_login_prompt(username, password)
        if pending_response:
            return None, None, pending_response
        
        # Terminal mode - interactive prompts
        if not username:
            username = self.zcli.display.zPrimitives.read_string("Username: ")
        if not password:
            password = self.zcli.display.zPrimitives.read_password("Password: ")
        
        return username, password, None
    
    def _try_gui_login_prompt(
        self,
        username: Optional[str],
        password: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Try to send GUI login prompt. Returns pending response if GUI mode, None otherwise."""
        if self.zcli.display.zPrimitives.send_gui_event("auth_login_prompt", {
            "username": username,
            "password": password,
            "fields": ["username", "password"]
        }):
            return self._create_status_response(STATUS_PENDING, reason=MSG_AWAITING_GUI)
        return None
    
    def _handle_successful_login(
        self,
        result: Dict[str, Any],
        persist: bool,
        password: str
    ) -> Dict[str, Any]:
        """Handle successful remote authentication."""
        credentials = result.get(KEY_CREDENTIALS)
        if not credentials or not self.session:
            return result
        
        # Update session with auth result
        self._update_zsession_with_credentials(credentials)
        
        # Update active context
        self._update_active_context()
        
        # Display success
        self._display_login_success(credentials)
        
        # Add persist info for caller
        result[KEY_PERSIST] = persist
        result[KEY_PASSWORD] = password
        
        return result
    
    def _update_zsession_with_credentials(self, credentials: Dict[str, Any]) -> None:
        """Update zSession in session dict with credentials."""
        get_zsession_data(self.session).update({
            ZAUTH_KEY_AUTHENTICATED: True,
            ZAUTH_KEY_ID: credentials.get("user_id"),
            ZAUTH_KEY_USERNAME: credentials.get(KEY_USERNAME),
            ZAUTH_KEY_ROLE: credentials.get(FIELD_ROLE),
            ZAUTH_KEY_API_KEY: credentials.get(FIELD_API_KEY)
        })
    
    def _display_login_success(self, credentials: Dict[str, Any]) -> None:
        """Display successful login message."""
        username = credentials.get(KEY_USERNAME)
        role = credentials.get(FIELD_ROLE)
        user_id = credentials.get("user_id")
        api_key = credentials.get(FIELD_API_KEY)
        
        self.zcli.display.success(f"[OK] Logged in as: {username} ({role})")
        self.zcli.display.text(f"     User ID: {user_id}", indent=0, pause=False)
        
        if api_key:
            truncated_key = api_key[:20] + "..." if len(api_key) > 20 else api_key
            self.zcli.display.text(f"     API Key: {truncated_key}", indent=0, pause=False)
    
    def _handle_failed_login(self) -> Dict[str, Any]:
        """Handle failed authentication."""
        self._log(LOG_LEVEL_WARNING, LOG_AUTH_FAILED)
        self.zcli.display.error(f"[FAIL] Authentication failed: {ERR_INVALID_CREDS}")
        return self._create_status_response(STATUS_FAIL, reason=ERR_INVALID_CREDS)
    
    def logout(
        self,
        context: str = CONTEXT_ZSESSION,
        app_name: Optional[str] = None,
        delete_persistent: bool = DEFAULT_DELETE_PERSISTENT
    ) -> Dict[str, Any]:
        """Clear session authentication (context-aware, multi-app support).
        
        Performs context-aware logout operations:
        - "zSession": Logout from zCLI/Zolo (Layer 1)
        - "application": Logout from specific app (Layer 2, requires app_name)
        - "all_apps": Logout from all applications (keep zSession)
        - "all": Logout from everything (zSession + all apps)
        
        Args:
            context: What to logout from (default: CONTEXT_ZSESSION)
                - CONTEXT_ZSESSION: Logout from zCLI/Zolo
                - CONTEXT_APPLICATION: Logout from specific app (requires app_name)
                - "all_apps": Logout from all applications
                - "all": Logout from everything
            app_name: Required if context=CONTEXT_APPLICATION - which app to logout from
            delete_persistent: If True, also delete persistent session from DB (zSession only)
        
        Returns:
            dict: Status response with:
                - {KEY_STATUS: STATUS_SUCCESS, KEY_CONTEXT: str, KEY_CLEARED: list, KEY_DELETE_PERSISTENT: bool}
                - {KEY_STATUS: STATUS_ERROR, KEY_REASON: str}
        
        Context Behavior:
            - Automatically updates active_context after logout
            - zSession logout: If apps still authenticated → switch to CONTEXT_APPLICATION
            - App logout: If no more apps → clear CONTEXT_APPLICATION
            - All logout: Clears all contexts
            - Dual-mode: Intelligently switches context based on remaining auth
        
        Integration:
            - zDisplay: Uses zEvents.zAuth.logout_success() for success feedback
            - zDisplay: Uses zEvents.zAuth.logout_warning() for already-logged-out
            - zData: Uses data.delete() to remove persistent session from SQLite
            - SessionPersistence: Delete from sessions table if delete_persistent=True
        
        Example:
            # Logout from zCLI
            result = zcli.auth.logout(CONTEXT_ZSESSION)
            
            # Logout from specific app
            result = zcli.auth.logout(CONTEXT_APPLICATION, app_name="ecommerce_store")
            
            # Logout from all apps (keep zSession)
            result = zcli.auth.logout("all_apps")
            
            # Logout from everything
            result = zcli.auth.logout("all")
            
            # Check what was cleared
            print(f"Cleared: {result[KEY_CLEARED]}")
        
        Session Persistence:
            - If delete_persistent=True and context includes zSession:
              → Deletes session record from SQLite database
            - If delete_persistent=False:
              → Session remains in DB for future automatic login
        """
        # Validate session
        if not self._check_session():
            return self._create_status_response(STATUS_ERROR, reason=ERR_NO_SESSION)
        
        # Initialize tracking
        cleared = []
        is_logged_in = self.is_authenticated()
        
        # Handle zSession logout
        if context in [CONTEXT_ZSESSION, "all"]:
            username = self._logout_zsession(cleared, delete_persistent)
        else:
            username = None
        
        # Display feedback
        self._display_logout_feedback(is_logged_in)
        
        # Handle application logout
        if context == CONTEXT_APPLICATION:
            error_response = self._logout_application(app_name, cleared)
            if error_response:
                return error_response
        
        # Handle all apps logout
        if context in ["all_apps", "all"]:
            self._logout_all_applications(cleared)
        
        # Regenerate session hash
        new_hash = SessionConfig.regenerate_session_hash(self.session)
        self._log(LOG_LEVEL_DEBUG, f"Session hash regenerated on logout: {new_hash}")
        
        return self._create_status_response(
            STATUS_SUCCESS,
            context=context,
            cleared=cleared,
            delete_persistent=delete_persistent if context in [CONTEXT_ZSESSION, "all"] else False
        )
    
    def _logout_zsession(self, cleared: list, delete_persistent: bool) -> Optional[str]:
        """Logout from zSession and update context."""
        username = get_zsession_data(self.session).get(ZAUTH_KEY_USERNAME)
        
        # Clear zSession data
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION] = {
            ZAUTH_KEY_AUTHENTICATED: False,
            ZAUTH_KEY_ID: None,
            ZAUTH_KEY_USERNAME: None,
            ZAUTH_KEY_ROLE: None,
            ZAUTH_KEY_API_KEY: None
        }
        
        # Update context
        self._update_context_after_zsession_logout()
        
        # Track cleared
        cleared.append(f"{CONTEXT_ZSESSION} ({username})")
        
        # Delete persistent session if requested
        if delete_persistent and username:
            self._delete_persistent_session(username)
        
        return username
    
    def _update_context_after_zsession_logout(self) -> None:
        """Update active context after zSession logout."""
        # Clear active context if it was zSession
        if self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_CONTEXT) == CONTEXT_ZSESSION:
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = None
        
        # If dual mode, switch to application context if apps exist
        if self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_DUAL_MODE):
            apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
            if apps:
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_APPLICATION
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
            else:
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = None
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
    
    def _delete_persistent_session(self, username: str) -> None:
        """Delete persistent session from SQLite database."""
        try:
            if hasattr(self.zcli, HTTP_DATA_KEY) and self.zcli.data.handler:
                self.zcli.data.delete(
                    table=TABLE_SESSIONS,
                    where=f"{FIELD_USERNAME} = '{username}'"
                )
                self._log(LOG_LEVEL_DEBUG, f"{LOG_SESSION_DELETE}: {username}")
        except Exception as e:
            self._log(LOG_LEVEL_DEBUG, f"{LOG_SESSION_DELETE_FAIL}: {e}")
    
    def _display_logout_feedback(self, is_logged_in: bool) -> None:
        """Display logout feedback to user."""
        if is_logged_in:
            self.zcli.display.success("[OK] Logged out successfully")
        else:
            self.zcli.display.warning("[WARN] Not currently logged in")
    
    def _logout_application(self, app_name: Optional[str], cleared: list) -> Optional[Dict[str, Any]]:
        """Logout from specific application. Returns error response if fails, None if success."""
        if not app_name:
            return self._create_status_response(STATUS_ERROR, reason=ERR_APP_NAME_REQUIRED)
        
        apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
        if app_name not in apps:
            return self._create_status_response(STATUS_ERROR, reason=f"{ERR_APP_NOT_AUTH} {app_name}")
        
        # Remove app from session
        app_username = apps[app_name].get(ZAUTH_KEY_USERNAME)
        del get_applications_data(self.session)[app_name]
        cleared.append(f"{CONTEXT_APPLICATION}/{app_name} ({app_username})")
        
        # Update active app and context
        self._update_context_after_app_logout(app_name)
        
        self._log(LOG_LEVEL_INFO, f"{LOG_LOGOUT_APP}: {app_name}")
        return None
    
    def _update_context_after_app_logout(self, app_name: str) -> None:
        """Update active app and context after logging out of an application."""
        # If this was the active app, clear it
        if self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_APP) == app_name:
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = None
            
            # If no more apps, clear application context
            if not get_applications_data(self.session):
                if self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_CONTEXT) == CONTEXT_APPLICATION:
                    self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = None
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
    
    def _logout_all_applications(self, cleared: list) -> None:
        """Logout from all applications."""
        apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
        
        # Track all cleared apps
        for app_name_iter, app_data in apps.items():
            app_username = app_data.get(ZAUTH_KEY_USERNAME)
            cleared.append(f"{CONTEXT_APPLICATION}/{app_name_iter} ({app_username})")
        
        # Clear all apps
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS] = {}
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = None
        
        # Update context
        self._update_context_after_all_apps_logout()
        
        self._log(LOG_LEVEL_INFO, f"{LOG_LOGOUT_ALL_APPS} ({len(apps)} apps)")
    
    def _update_context_after_all_apps_logout(self) -> None:
        """Update context after logging out of all applications."""
        if self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_CONTEXT) in [CONTEXT_APPLICATION, CONTEXT_DUAL]:
            # If zSession still authenticated, switch to it
            if get_zsession_data(self.session).get(ZAUTH_KEY_AUTHENTICATED):
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_ZSESSION
            else:
                self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = None
        
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = False
    
    def status(self) -> Dict[str, Any]:
        """Show current zSession authentication status.
        
        Returns:
            dict: Status response with:
                - {KEY_STATUS: "authenticated", KEY_USER: dict} if zSession authenticated
                - {KEY_STATUS: MSG_NOT_AUTHENTICATED} if not authenticated
        
        Context Awareness:
            - Only checks zSession authentication (Layer 1)
            - For application status, use get_app_user(app_name)
            - For all contexts, use get_active_user()
        
        Integration:
            - zDisplay: Uses zEvents.zAuth.status_display() to show user info
            - zDisplay: Uses zEvents.zAuth.status_not_authenticated() for not logged in
        
        Example:
            # Check status
            status = zcli.auth.status()
            if status[KEY_STATUS] == "authenticated":
                print(f"User: {status[KEY_USER][ZAUTH_KEY_USERNAME]}")
                print(f"Role: {status[KEY_USER][ZAUTH_KEY_ROLE]}")
        """
        if self.is_authenticated():
            # Get zSession auth data (primary authentication context)
            auth_data = get_zsession_data(self.session)
            # Display using generic zDisplay events
            self.zcli.display.header("[*] Authentication Status")
            self.zcli.display.text(f"Username:   {auth_data.get(ZAUTH_KEY_USERNAME)}", indent=1, pause=False)
            self.zcli.display.text(f"Role:       {auth_data.get(ZAUTH_KEY_ROLE)}", indent=1, pause=False)
            self.zcli.display.text(f"User ID:    {auth_data.get(ZAUTH_KEY_ID)}", indent=1, pause=False)
            if api_key := auth_data.get(ZAUTH_KEY_API_KEY):
                truncated_key = api_key[:20] + "..." if len(api_key) > 20 else api_key
                self.zcli.display.text(f"API Key:    {truncated_key}", indent=1, pause=False)
            return self._create_status_response("authenticated", user=auth_data)
        else:
            # Display using generic zDisplay events
            self.zcli.display.warning("[WARN] Not authenticated. Run 'auth login' to authenticate.")
            return self._create_status_response(MSG_NOT_AUTHENTICATED)
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated in ANY context.
        
        Returns:
            bool: True if authenticated in zSession OR any application, False otherwise
        
        Context Awareness:
            - Checks BOTH zSession authentication (Layer 1) AND application authentication (Layer 2)
            - Returns True if authenticated in ANY context
            - For specific context checks, use: get_app_user(app_name) or get_credentials()
        
        Example:
            # Check any authentication
            if zcli.auth.is_authenticated():
                print("User is logged in (zSession or application)")
            
            # Check specific application authentication
            if zcli.auth.get_app_user("store"):
                print("Logged into store app")
        """
        if not self._check_session():
            return False
        
        # Check zSession authentication (Layer 1)
        zsession = get_zsession_data(self.session)
        if zsession.get(ZAUTH_KEY_AUTHENTICATED, False) and zsession.get(ZAUTH_KEY_USERNAME) is not None:
            return True
        
        # Check application authentication (Layer 2)
        applications = get_applications_data(self.session)
        for app_name, app_session in applications.items():
            if app_session.get(ZAUTH_KEY_AUTHENTICATED, False) and app_session.get(ZAUTH_KEY_ID) is not None:
                return True
        
        return False
    
    def get_credentials(self) -> Optional[Dict[str, Any]]:
        """Get current zSession authentication data.
        
        Returns:
            dict: zSession auth data if authenticated, None otherwise
                {
                    ZAUTH_KEY_AUTHENTICATED: bool,
                    ZAUTH_KEY_ID: str,
                    ZAUTH_KEY_USERNAME: str,
                    ZAUTH_KEY_ROLE: str,
                    ZAUTH_KEY_API_KEY: str
                }
        
        Context Awareness:
            - Only returns zSession credentials (Layer 1)
            - For app credentials, use get_app_user(app_name)
            - For context-aware credentials, use get_active_user()
        
        Example:
            # Get zSession credentials
            creds = zcli.auth.get_credentials()
            if creds:
                print(f"Username: {creds[ZAUTH_KEY_USERNAME]}")
                print(f"API Key: {creds[ZAUTH_KEY_API_KEY]}")
        """
        if self.is_authenticated():
            return get_zsession_data(self.session)
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 2: APPLICATION AUTHENTICATION (External Users of zCLI-Built Apps)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def authenticate_app_user(
        self,
        app_name: str,
        token: str,
        config: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Authenticate user to a specific application (Layer 2 auth).
        
        Supports multiple simultaneous application authentications in one session.
        Each app can have its own user identity, credentials, and permissions.
        
        Args:
            app_name: Application identifier (e.g., "ecommerce_store", "analytics_dashboard")
            token: API key/token to validate against app's user database
            config: Optional auth configuration dict:
                {
                    "user_model": "@.store_users.users",  # zData model path
                    "id_field": "id",                      # Field name for user ID
                    "username_field": "email",             # Field name for username
                    "role_field": "role",                  # Field name for role
                    "api_key_field": "api_key"             # Field name for API key
                }
        
        Returns:
            dict: Status response with:
                - {KEY_STATUS: STATUS_SUCCESS, KEY_APP_NAME: str, KEY_USER: dict, KEY_CONTEXT: str}
                - {KEY_STATUS: STATUS_ERROR, KEY_APP_NAME: str, KEY_REASON: str}
        
        Context Behavior:
            - If zSession already authenticated → sets CONTEXT_DUAL (dual_mode = True)
            - If only app authenticated → sets CONTEXT_APPLICATION
            - Sets active_app to app_name
            - Multiple apps can be authenticated simultaneously
        
        Integration:
            - zData: TODO - Query application user database (not yet implemented)
              NOTE: Consider migrating to zCloud plugin for Zolo security (app-layer logic)
            - Currently uses placeholder data for development
        
        Example:
            # Store owner authenticates to their eCommerce store
            result = zcli.auth.authenticate_app_user(
                "ecommerce_store",
                "store_token_xyz",
                {"user_model": "@.store_users.users"}
            )
            
            # Later, same owner authenticates to analytics dashboard
            result = zcli.auth.authenticate_app_user(
                "analytics_dashboard",
                "analytics_token_abc",
                {"user_model": "@.analytics_users.users"}
            )
            
            # Both authentications persist simultaneously!
            print(f"Authenticated to: {result[KEY_APP_NAME]}")
            print(f"Context: {result[KEY_CONTEXT]}")
        
        Multi-App Support:
            - Applications are isolated by app_name keys
            - Each app maintains separate credentials
            - User can be "admin" in one app and "user" in another
            - RBAC checks respect active_app when in CONTEXT_APPLICATION
        
        TODO:
            - Integrate with zData to query application user database
            - Validate token against user_model
            - NOTE: Consider migrating to zCloud plugin (app-layer logic vs. core framework)
            - Currently uses placeholder data
        """
        if not self._check_session():
            return self._create_status_response(STATUS_ERROR, reason=ERR_NO_SESSION)
        
        # Configure authentication settings
        auth_config = self._configure_app_auth(config)
        
        try:
            # Authenticate user (currently placeholder, TODO: integrate zData)
            user_data = self._authenticate_app_user_data(app_name, token, auth_config)
            
            # Store authentication and update context
            self._store_app_authentication(app_name, user_data)
            
            # Log success
            self._log_app_auth_success(app_name, user_data)
            
            return self._create_status_response(
                STATUS_SUCCESS,
                app_name=app_name,
                user=user_data,
                context=get_active_context(self.session)
            )
            
        except Exception as e:
            self._log(LOG_LEVEL_ERROR, f"{LOG_APP_AUTH_ERROR} for {app_name}: {e}")
            return self._create_status_response(
                STATUS_ERROR,
                app_name=app_name,
                reason=str(e)
            )
    
    def _configure_app_auth(self, config: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Configure authentication settings with defaults."""
        default_config = {
            "user_model": DEFAULT_USER_MODEL,
            DEFAULT_ID_FIELD: DEFAULT_ID_FIELD,
            DEFAULT_USERNAME_FIELD: DEFAULT_USERNAME_FIELD,
            DEFAULT_ROLE_FIELD: DEFAULT_ROLE_FIELD,
            DEFAULT_API_KEY_FIELD: DEFAULT_API_KEY_FIELD
        }
        return {**default_config, **(config or {})}
    
    def _authenticate_app_user_data(
        self,
        app_name: str,
        token: str,
        auth_config: Dict[str, str]  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """Authenticate app user and return user data (currently placeholder).
        
        TODO: Query application user database using zData
        NOTE: Consider migrating to zCloud plugin (app-layer logic vs. core framework)
        """
        # Placeholder: Simulate successful authentication
        # In production, this would validate token against the user model
        return {
            ZAUTH_KEY_AUTHENTICATED: True,
            ZAUTH_KEY_ID: PLACEHOLDER_USER_ID,  # Would come from database
            ZAUTH_KEY_USERNAME: f"user_from_{app_name}",  # Would come from database
            ZAUTH_KEY_ROLE: PLACEHOLDER_ROLE,  # Would come from database
            ZAUTH_KEY_API_KEY: token
        }
    
    def _store_app_authentication(self, app_name: str, user_data: Dict[str, Any]) -> None:
        """Store app authentication in session and update context."""
        # Store authentication in applications dict
        get_applications_data(self.session)[app_name] = user_data
        
        # Set active app
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = app_name
        
        # Update active context
        self._update_active_context()
    
    def _log_app_auth_success(self, app_name: str, user_data: Dict[str, Any]) -> None:
        """Log successful application authentication."""
        self._log(
            LOG_LEVEL_INFO,
            f"{LOG_APP_AUTH_SUCCESS}: {app_name} "
            f"(username={user_data[ZAUTH_KEY_USERNAME]}, "
            f"context={get_active_context(self.session)})"
        )
    
    def switch_app(self, app_name: str) -> bool:
        """Switch focus to a different authenticated application.
        
        Args:
            app_name: Name of the application to switch to
        
        Returns:
            bool: True if successful, False if app not authenticated
        
        Context Behavior:
            - Does NOT change active_context (remains in CONTEXT_APPLICATION or CONTEXT_DUAL)
            - Only changes ZAUTH_KEY_ACTIVE_APP
            - Used when multiple apps are authenticated simultaneously
        
        Example:
            # User has multiple apps authenticated
            zcli.auth.authenticate_app_user("ecommerce_store", "token1", {...})
            zcli.auth.authenticate_app_user("analytics_dashboard", "token2", {...})
            
            # Switch focus between them
            zcli.auth.switch_app("ecommerce_store")  # Now: active_app = "ecommerce_store"
            zcli.auth.switch_app("analytics_dashboard")  # Now: active_app = "analytics_dashboard"
            
            # RBAC checks will use the active_app's credentials
        """
        if not self._check_session():
            return False
        
        # Check if app is authenticated
        apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
        if app_name not in apps:
            self._log(LOG_LEVEL_WARNING, f"{LOG_APP_SWITCH_FAIL}: {app_name}")
            return False
        
        # Switch active app
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP] = app_name
        
        self._log(LOG_LEVEL_INFO, f"{LOG_APP_SWITCH}: {app_name}")
        return True
    
    def get_app_user(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get authentication info for a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            dict: App user data if authenticated, None otherwise
                {
                    ZAUTH_KEY_AUTHENTICATED: bool,
                    ZAUTH_KEY_ID: str,
                    ZAUTH_KEY_USERNAME: str,
                    ZAUTH_KEY_ROLE: str,
                    ZAUTH_KEY_API_KEY: str
                }
        
        Example:
            # Get credentials for specific apps
            store_user = zcli.auth.get_app_user("ecommerce_store")
            if store_user:
                print(f"Store user: {store_user[ZAUTH_KEY_USERNAME]}")
                print(f"Store role: {store_user[ZAUTH_KEY_ROLE]}")
            
            analytics_user = zcli.auth.get_app_user("analytics_dashboard")
            if analytics_user:
                print(f"Analytics user: {analytics_user[ZAUTH_KEY_USERNAME]}")
        
        Multi-App Support:
            - Returns credentials for any authenticated app
            - Does NOT require app to be the active_app
            - Useful for checking if user is authenticated to specific app
        """
        if not self._check_session():
            return None
        
        apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
        return apps.get(app_name)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONTEXT MANAGEMENT (Switch Between Authentication Contexts)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_active_context(self, context: str) -> bool:
        """Set the active authentication context.
        
        Args:
            context: One of CONTEXT_ZSESSION, CONTEXT_APPLICATION, or CONTEXT_DUAL
        
        Returns:
            bool: True if successful, False if invalid or no auth for that context
        
        Validation:
            - CONTEXT_ZSESSION: Requires zSession authenticated
            - CONTEXT_APPLICATION: Requires active_app authenticated
            - CONTEXT_DUAL: Requires BOTH zSession AND active_app authenticated
        
        Context Behavior:
            - Sets ZAUTH_KEY_ACTIVE_CONTEXT to requested context
            - Updates ZAUTH_KEY_DUAL_MODE flag (True if CONTEXT_DUAL, False otherwise)
            - RBAC module reads active_context for authorization decisions
        
        Example:
            # Switch to zSession context (zCLI user)
            success = zcli.auth.set_active_context(CONTEXT_ZSESSION)
            # Now: RBAC uses zSession role/permissions
            
            # Switch to application context (app user)
            success = zcli.auth.set_active_context(CONTEXT_APPLICATION)
            # Now: RBAC uses active_app role/permissions
            
            # Switch to dual mode (both)
            success = zcli.auth.set_active_context(CONTEXT_DUAL)
            # Now: RBAC uses OR logic (either context can grant access)
        
        Integration:
            - authzRBAC: RBAC module queries active_context for role/permission checks
            - Dual-mode: RBAC uses OR logic (either zSession OR app can grant access)
        """
        if not self._check_session():
            return False
        
        # Validate context value
        valid_contexts = [CONTEXT_ZSESSION, CONTEXT_APPLICATION, CONTEXT_DUAL]
        if context not in valid_contexts:
            self._log(LOG_LEVEL_WARNING, f"{LOG_CONTEXT_INVALID}: {context}")
            return False
        
        # Validate that requested context has authenticated user
        if context == CONTEXT_ZSESSION:
            if not get_zsession_data(self.session).get(ZAUTH_KEY_AUTHENTICATED):
                self._log(LOG_LEVEL_WARNING, LOG_CONTEXT_NO_ZSESSION)
                return False
        
        elif context == CONTEXT_APPLICATION:
            active_app = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_APP)
            if not active_app:
                self._log(LOG_LEVEL_WARNING, LOG_CONTEXT_NO_APP)
                return False
            apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
            if active_app not in apps:
                self._log(LOG_LEVEL_WARNING, f"{LOG_CONTEXT_NO_APP}: {active_app} not authenticated")
                return False
        
        elif context == CONTEXT_DUAL:
            # Dual mode requires both zSession and application authenticated
            zsession_auth = get_zsession_data(self.session).get(ZAUTH_KEY_AUTHENTICATED)
            active_app = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_APP)
            apps = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_APPLICATIONS, {})
            
            if not zsession_auth or not active_app or active_app not in apps:
                self._log(LOG_LEVEL_WARNING, LOG_CONTEXT_NO_DUAL)
                return False
        
        # Set context
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = context
        self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = (context == CONTEXT_DUAL)
        
        self._log(LOG_LEVEL_INFO, f"{LOG_CONTEXT_SET}: {context}")
        return True
    
    def get_active_user(self) -> Optional[Dict[str, Any]]:
        """Get user data for the current active authentication context.
        
        Returns:
            dict: User data based on active context:
                - If CONTEXT_ZSESSION: Returns zSession user data
                - If CONTEXT_APPLICATION: Returns active app user data
                - If CONTEXT_DUAL: Returns {"zSession": {...}, "application": {...}}
                - If no authentication: Returns None
        
        Context-Aware Return Values:
            - zSession context:
                {
                    ZAUTH_KEY_AUTHENTICATED: bool,
                    ZAUTH_KEY_ID: str,
                    ZAUTH_KEY_USERNAME: str,
                    ZAUTH_KEY_ROLE: str,
                    ZAUTH_KEY_API_KEY: str
                }
            
            - Application context:
                Same structure as zSession, but from active_app
            
            - Dual context:
                {
                    "zSession": {...},      # zSession credentials
                    "application": {...}    # Active app credentials
                }
        
        Example:
            # Get current active user (whatever context is active)
            user = zcli.auth.get_active_user()
            
            # zSession context
            if isinstance(user, dict) and "zSession" not in user:
                print(f"zSession user: {user[ZAUTH_KEY_USERNAME]}")
            
            # Dual context
            elif isinstance(user, dict) and "zSession" in user:
                print(f"zSession: {user['zSession'][ZAUTH_KEY_USERNAME]}")
                print(f"App: {user['application'][ZAUTH_KEY_USERNAME]}")
        
        Use Cases:
            - Generic code that works across all contexts
            - UI components that display current user info
            - Logging/auditing that needs to know who is acting
        """
        if not self._check_session():
            return None
        
        active_context = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_CONTEXT)
        
        if not active_context:
            return None
        
        if active_context == CONTEXT_ZSESSION:
            return get_zsession_data(self.session)
        
        elif active_context == CONTEXT_APPLICATION:
            active_app = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_APP)
            if active_app:
                return get_applications_data(self.session).get(active_app)
            return None
        
        elif active_context == CONTEXT_DUAL:
            active_app = self.session[SESSION_KEY_ZAUTH].get(ZAUTH_KEY_ACTIVE_APP)
            return {
                "zSession": get_zsession_data(self.session),
                "application": get_applications_data(self.session).get(active_app) if active_app else None
            }
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # REMOTE AUTHENTICATION (Original Methods)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def authenticate_remote(
        self,
        username: str,
        password: str,
        server_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate via Flask API (remote server).
        
        Args:
            username: Username for authentication
            password: Password for authentication
            server_url: Optional server URL (defaults to ZOLO_API_URL env var or localhost:5000)
        
        Returns:
            dict: Status response with:
                - {KEY_STATUS: STATUS_SUCCESS, KEY_CREDENTIALS: {...}}
                - {KEY_STATUS: STATUS_FAIL, KEY_REASON: str}
                - {KEY_STATUS: STATUS_ERROR, KEY_REASON: str}
        
        Integration:
            - zComm: Uses comm.http_post() for secure API communication
            - zDisplay: Uses modern zEvents for feedback (BasicOutputs, Signals)
        
        Security:
            - HTTPS communication with authentication server
            - Credentials validated against Zolo user database
            - API keys generated by server, not client
        
        Example:
            # Authenticate against remote server
            result = zcli.auth.authenticate_remote("user@zolo.com", "password123")
            
            # With custom server
            result = zcli.auth.authenticate_remote(
                "user",
                "pass",
                server_url="https://api.zolo.com"
            )
            
            # Check result
            if result[KEY_STATUS] == STATUS_SUCCESS:
                creds = result[KEY_CREDENTIALS]
                print(f"API Key: {creds[FIELD_API_KEY]}")
        
        Environment Variables:
            - ZOLO_API_URL: Default server URL if not provided
            - Defaults to http://localhost:5000 if not set
        """
        # Get server URL
        server_url = self._get_server_url(server_url)
        
        # Log authentication attempt
        self._log(LOG_LEVEL_INFO, f"{LOG_REMOTE_AUTH}: {server_url}")
        
        try:
            # Send authentication request
            response = self._send_auth_request(username, password, server_url)
            if not response:
                return self._create_status_response(STATUS_FAIL, reason=ERR_CONNECTION_FAILED)
            
            # Parse response
            result = response.json()
            
            # Handle success
            if result and result.get(KEY_STATUS) == STATUS_SUCCESS:
                return self._handle_remote_auth_success(result, server_url)
            
            # Handle failure
            return self._handle_remote_auth_failure()
        
        except Exception as e:
            return self._handle_remote_auth_error(e)
    
    def _get_server_url(self, server_url: Optional[str]) -> str:
        """Get server URL from parameter, environment, or default."""
        if server_url:
            return server_url
        return os.getenv(ENV_API_URL, DEFAULT_SERVER_URL)
    
    def _send_auth_request(self, username: str, password: str, server_url: str):
        """Send HTTP POST request to authentication server."""
        return self.zcli.comm.http_post(
            f"{server_url}/zAuth",
            data={KEY_USERNAME: username, KEY_PASSWORD: password, HTTP_MODE_KEY: HTTP_MODE_TERMINAL}
        )
    
    def _handle_remote_auth_success(self, result: Dict[str, Any], server_url: str) -> Dict[str, Any]:
        """Handle successful remote authentication."""
        user = result.get(KEY_USER, {})
        
        # Prepare credentials
        credentials = self._prepare_credentials(user, server_url)
        
        # Log success
        self._log(
            LOG_LEVEL_INFO,
            f"{LOG_REMOTE_SUCCESS}: {credentials[KEY_USERNAME]} (role={credentials[FIELD_ROLE]})"
        )
        
        # Display success
        self._display_remote_auth_success(credentials, server_url)
        
        return self._create_status_response(STATUS_SUCCESS, credentials=credentials)
    
    def _prepare_credentials(self, user: Dict[str, Any], server_url: str) -> Dict[str, Any]:
        """Prepare credentials dict from user data."""
        return {
            KEY_USERNAME: user.get(KEY_USERNAME),
            FIELD_API_KEY: user.get(FIELD_API_KEY),
            FIELD_ROLE: user.get(FIELD_ROLE),
            "user_id": user.get("id"),
            KEY_SERVER_URL: server_url
        }
    
    def _display_remote_auth_success(self, credentials: Dict[str, Any], server_url: str) -> None:
        """Display remote authentication success message."""
        self.zcli.display.zEvents.BasicOutputs.text("")
        self.zcli.display.zEvents.Signals.success(
            f"Logged in as: {credentials[KEY_USERNAME]} ({credentials[FIELD_ROLE]})"
        )
        self.zcli.display.zEvents.BasicOutputs.text(
            f"API Key: {credentials[FIELD_API_KEY][:20]}...",
            indent=1
        )
        self.zcli.display.zEvents.BasicOutputs.text(
            f"Server: {server_url}",
            indent=1
        )
    
    def _handle_remote_auth_failure(self) -> Dict[str, Any]:
        """Handle remote authentication failure."""
        self._log(LOG_LEVEL_WARNING, LOG_REMOTE_FAIL)
        self.zcli.display.zEvents.BasicOutputs.text("")
        self.zcli.display.zEvents.Signals.error(f"Authentication failed: {ERR_INVALID_CREDS}")
        self.zcli.display.zEvents.BasicOutputs.text("")
        return self._create_status_response(STATUS_FAIL, reason=ERR_INVALID_CREDS)
    
    def _handle_remote_auth_error(self, error: Exception) -> Dict[str, Any]:
        """Handle remote authentication error."""
        self._log(LOG_LEVEL_ERROR, f"{LOG_APP_AUTH_ERROR}: {error}")
        self.zcli.display.zEvents.BasicOutputs.text("")
        self.zcli.display.zEvents.Signals.error(f"Error connecting to remote server: {error}")
        self.zcli.display.zEvents.BasicOutputs.text("")
        return self._create_status_response(STATUS_ERROR, reason=str(error))
