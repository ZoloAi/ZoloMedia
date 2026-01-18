"""
Session Persistence Module - SQLite-based session management (v1.5.4+)

This module provides persistent session storage using SQLite, enabling
"Remember me" functionality across application restarts. It integrates
deeply with zCLI's declarative zData subsystem and three-tier authentication
architecture.

ARCHITECTURE - Session Persistence Layer

Design Pattern:
    - SQLite-backed persistent storage (unified auth database)
    - Declarative zData operations (no raw SQL)
    - Lazy initialization (database loaded on demand)
    - Automatic expiration and cleanup
    - Integration with three-tier authentication

Session Lifecycle:
    1. LOAD:    Restore valid session from database on startup
    2. SAVE:    Persist authenticated session to database
    3. EXPIRE:  Sessions expire after 7 days (configurable)
    4. CLEANUP: Automatic removal of expired sessions

Storage Location:
    - Platform-specific data directory (via platformdirs)
    - Unified auth database: sessions + permissions tables
    - Schema: zSchema.auth.yaml (declarative YAML)

DATABASE STRUCTURE - Unified Auth Database

Database Label: "auth"
    - Shared between SessionPersistence and RBAC modules
    - Defined in zSchema.auth.yaml (zAuth subsystem)

Table: sessions
    Fields:
        - session_id:    Unique session identifier (32-byte URL-safe token)
        - user_id:       User identifier (from authentication)
        - username:      Username for the session
        - role:          User role (user, admin, etc.)
        - password_hash: bcrypt password hash (for verification)
        - token:         API token (32-byte URL-safe token)
        - created_at:    Timestamp when session was created
        - expires_at:    Timestamp when session expires (7 days)
        - last_accessed: Timestamp of last access (updated on restore)

Table: user_permissions
    - Managed by RBAC module (authzRBAC.py)
    - Shared database for unified auth operations

SECURITY MODEL

Token Generation:
    - Uses secrets.token_urlsafe(32) for cryptographically secure tokens
    - Session ID: 32-byte URL-safe token (unique identifier)
    - API Token: 32-byte URL-safe token (authentication credential)

Session Expiration:
    - Default: 7 days from creation (configurable)
    - Automatic cleanup on startup
    - Manual cleanup available via cleanup_expired()

Password Storage:
    - Stores bcrypt password hash (from auth_password_security.py)
    - Never stores plaintext passwords
    - Hash used for session verification if needed

Single Session Per User:
    - Deletes existing sessions for user before creating new one
    - Prevents session accumulation
    - Last login wins (invalidates previous sessions)

THREE-TIER AUTHENTICATION INTEGRATION

Session Persistence Scope:
    - PERSISTS:     zSession context only (Layer 1)
    - NOT PERSISTED: Application contexts (Layer 2)
    - NOT PERSISTED: Dual-auth state (Layer 3)

Rationale:
    - zSession represents the zCLI/Zolo user (persistent identity)
    - Application contexts are transient (per-application session)
    - Dual-auth is a runtime state (not persisted across restarts)

Session Restoration:
    - Loads zSession credentials from database
    - Sets active_context to "zSession"
    - Applications must re-authenticate on startup
    - Dual-auth must be re-established if needed

Integration with zAuth:
    - Used by auth_authentication.py for login/logout
    - Integrates with session["zAuth"] structure (via SESSION_KEY_ZAUTH)
    - Respects three-tier authentication model
    - Coordinates with RBAC via shared database

ZCLI INTEGRATION - Declarative zData Operations

zData Integration:
    - NO raw SQL queries (fully declarative)
    - Uses zData.select(), zData.insert(), zData.update(), zData.delete()
    - Schema loaded from zSchema.auth.yaml via zParser
    - Database handler managed by zData subsystem

zParser Integration:
    - Loads YAML schema from package directory
    - Parses schema into zData-compatible format
    - Handles package-internal file paths

zConfig Integration:
    - Imports ZAUTH_KEY_* constants (field names)
    - Imports SESSION_KEY_ZAUTH (session structure key)
    - Imports CONTEXT_ZSESSION (authentication context)
    - Ensures consistency with zConfig session structure

Lazy Initialization:
    - Database not loaded until first use
    - ensure_sessions_db() loads schema on demand
    - Graceful degradation if database unavailable

═══════════════════════════════════════════════════════════════════════════════
SESSION LIFECYCLE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Initialization:
    >>> from zOS.L2_Core.d_zAuth.zAuth_modules import SessionPersistence
    >>> session_mgr = SessionPersistence(zcli, session_duration_days=7)
    >>> session_mgr.ensure_sessions_db()

Load Session on Startup:
    >>> # Called automatically by zAuth on initialization
    >>> session_mgr.load_session()
    # If valid session exists:
    # - Restores username, role, API key to session["zAuth"]["zSession"]
    # - Sets active_context to "zSession"
    # - Updates last_accessed timestamp

Save Session After Login:
    >>> # Called by auth_authentication.py after successful login
    >>> session_id = session_mgr.save_session(
    ...     username="john_doe",
    ...     password_hash="$2b$12$...",
    ...     user_id="zU_12345",
    ...     role="admin"
    ... )
    # Creates new session with 7-day expiration

Cleanup Expired Sessions:
    >>> # Called automatically on startup
    >>> deleted = session_mgr.cleanup_expired()
    >>> print(f"Cleaned up {deleted} expired sessions")

ERROR HANDLING & LOGGING

Graceful Degradation:
    - Database unavailable: Continue without persistence
    - Schema load failure: Log warning, continue
    - Session restore failure: Start with clean session

Logging Levels:
    - INFO:  Successful operations (DB init, session saved/restored, cleanup)
    - DEBUG: Operational details (no session found, DB checks)
    - WARN:  Non-fatal issues (schema not found, DB not loaded)
    - ERROR: Operation failures (save failed, restore failed)

Error Recovery:
    - All methods return gracefully on error
    - Try/except blocks with comprehensive logging
    - Never exposes sensitive data in logs (passwords, tokens)
    - Provides context for debugging (operation, reason)
"""

from zOS import secrets, datetime, timedelta, Path, Optional, Any, Dict
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_AUTHENTICATED,
    ZAUTH_KEY_ID,
    ZAUTH_KEY_USERNAME,
    ZAUTH_KEY_ROLE,
    ZAUTH_KEY_API_KEY,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    SESSION_KEY_ZAUTH,  # CRITICAL: Modernization from Week 6.2
    CONTEXT_ZSESSION
)

# ═══════════════════════════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Import centralized constants
from .auth_constants import (
    # Public constants
    DEFAULT_SESSION_DURATION_DAYS,
    DB_LABEL_AUTH,
    TABLE_SESSIONS,
    TABLE_PERMISSIONS,
    FIELD_SESSION_ID,
    FIELD_USER_ID,
    FIELD_USERNAME,
    FIELD_ROLE,
    FIELD_PASSWORD_HASH,
    FIELD_TOKEN,
    FIELD_CREATED_AT,
    FIELD_EXPIRES_AT,
    FIELD_LAST_ACCESSED,
    QUERY_LIMIT_ONE,
    ORDER_BY_LAST_ACCESSED,
    SCHEMAS_DIR,
    SCHEMA_FILE_NAME,
    SCHEMA_META_KEY,
    SCHEMA_LABEL_KEY,
    # Internal constants (private)
    _TOKEN_LENGTH,
    _SESSION_KEY_SESSION_ID,
    _LOG_PREFIX_PERSISTENCE,
    _LOG_DB_INIT,
    _LOG_TABLE_CREATED_SESSIONS,
    _LOG_TABLE_CREATED_PERMISSIONS,
    _LOG_SCHEMA_NOT_FOUND,
    _LOG_SCHEMA_PARSE_FAILED,
    _LOG_HANDLER_FAILED,
    _LOG_WRONG_SCHEMA,
    _LOG_SESSION_RESTORED,
    _LOG_SESSION_SAVED,
    _LOG_SESSIONS_CLEANED,
    _LOG_NO_SESSION,
    _LOG_NO_EXPIRED_SESSIONS,
    _LOG_DB_NOT_LOADED_SKIP,
    _LOG_DB_NOT_LOADED_ATTEMPT,
    _LOG_DB_NOT_LOADED_WARNING,
    _LOG_NO_EXISTING_SESSIONS,
    _LOG_ERROR_INIT_DB,
    _LOG_ERROR_LOAD_SESSION,
    _LOG_ERROR_SAVE_SESSION,
    _LOG_ERROR_CLEANUP,
)

# Session Access Helpers (DRY utilities)
from .auth_helpers import (
    get_auth_data,
    get_zsession_data,
    get_applications_data,
    get_active_context,
)

# Module uses _LOG_PREFIX_PERSISTENCE as LOG_PREFIX for compatibility
LOG_PREFIX = _LOG_PREFIX_PERSISTENCE


# Session Persistence Class

class SessionPersistence:
    """
    SQLite-based persistent session management with declarative zData integration.
    
    This class provides session persistence across application restarts using
    SQLite storage. It integrates with zCLI's declarative zData subsystem and
    supports the three-tier authentication architecture.
    
    Architecture:
        - SQLite backend (unified auth database)
        - Declarative operations (no raw SQL)
        - Lazy initialization (load on demand)
        - Automatic expiration (7-day default)
        - Three-tier awareness (persists zSession only)
    
    Session Lifecycle:
        1. LOAD:    Restore valid session from database on startup
        2. SAVE:    Persist authenticated session to database
        3. EXPIRE:  Sessions expire after DEFAULT_SESSION_DURATION_DAYS
        4. CLEANUP: Automatic removal of expired sessions
    
    Security Features:
        - Cryptographically secure tokens (secrets.token_urlsafe)
        - bcrypt password hashes (never plaintext)
        - Automatic expiration and cleanup
        - Single session per user (last login wins)
    
    zData Integration:
        - No raw SQL queries (fully declarative)
        - Uses zData.select(), insert(), update(), delete()
        - Schema loaded from zSchema.auth.yaml via zParser
        - Graceful degradation if database unavailable
    
    Three-Tier Authentication:
        - PERSISTS:     zSession context (Layer 1)
        - NOT PERSISTED: Application contexts (Layer 2)
        - NOT PERSISTED: Dual-auth state (Layer 3)
        - Rationale: zSession is persistent identity, apps are transient
    
    Methods:
        ensure_sessions_db():     Initialize database and tables
        load_session():           Restore session from database on startup
        save_session(user, ...):  Persist authenticated session
        cleanup_expired():        Remove expired sessions (housekeeping)
        _is_db_ready():          Check if database is loaded (helper)
        _get_current_timestamp(): Get ISO timestamp (helper)
        _log(level, message):    Centralized logging (helper)
        _ensure_db_loaded():     Try to load database (helper)
    
    Usage:
        >>> session_mgr = SessionPersistence(zcli, session_duration_days=7)
        >>> session_mgr.ensure_sessions_db()
        >>> session_mgr.load_session()  # On startup
        >>> session_id = session_mgr.save_session("john", hash, role="admin")
        >>> deleted = session_mgr.cleanup_expired()  # Housekeeping
    
    Integration:
        - Used by auth_authentication.py for login/logout
        - Shares database with authzRBAC.py (permissions)
        - Respects SESSION_KEY_ZAUTH from zConfig
        - Coordinates with three-tier authentication model
    
    Attributes:
        zcli: Any                      - zCLI instance
        logger: Any                    - Logger instance
        session: Dict[str, Any]        - In-memory session dictionary
        session_duration_days: int     - Session expiration period
        auth_db_label: str             - Database label ("auth")
    """
    
    # Class-level type declarations
    zcli: Any
    logger: Any
    session: Dict[str, Any]
    session_duration_days: int
    auth_db_label: str
    
    def __init__(self, zcli: Any, session_duration_days: int = DEFAULT_SESSION_DURATION_DAYS):
        """Initialize session persistence module with configurable expiration.
        
        Args:
            zcli: zCLI instance providing access to:
                - data: zData subsystem for database operations
                - loader: zLoader for schema loading
                - logger: Logging instance
                - session: In-memory session dictionary
                - zparser: YAML parser for schema files
            session_duration_days: Session expiration period in days.
                Default is DEFAULT_SESSION_DURATION_DAYS (7 days).
                After this period, sessions expire and are removed.
        
        Notes:
            - Database is NOT initialized here (lazy initialization)
            - Call ensure_sessions_db() to initialize database
            - Gracefully handles missing zCLI subsystems
        
        Example:
            >>> # Default 7-day expiration
            >>> session_mgr = SessionPersistence(zcli)
            >>> 
            >>> # Custom 30-day expiration (long-lived sessions)
            >>> session_mgr = SessionPersistence(zcli, session_duration_days=30)
            >>> 
            >>> # Initialize database
            >>> session_mgr.ensure_sessions_db()
        """
        self.zcli = zcli
        self.logger = zcli.logger
        self.session = zcli.session
        self.session_duration_days = session_duration_days
        self.auth_db_label = DB_LABEL_AUTH
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Private Helper Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _is_db_ready(self) -> bool:
        """Check if zData handler is ready with auth schema loaded.
        
        This helper consolidates the database readiness check that was
        duplicated 3 times across the module.
        
        Returns:
            bool: True if database handler exists and auth schema is loaded,
                  False otherwise.
        
        Checks:
            1. zData handler exists (self.zcli.data.handler)
            2. Schema is loaded (self.zcli.data.schema)
            3. Schema label matches DB_LABEL_AUTH
        
        Example:
            >>> if self._is_db_ready():
            >>>     # Perform database operation
            >>>     results = self.zcli.data.select(...)
            >>> else:
            >>>     # Graceful degradation
            >>>     self._log("debug", LOG_DB_NOT_LOADED_SKIP)
        """
        return (
            self.zcli.data.handler is not None and
            self.zcli.data.schema.get(SCHEMA_META_KEY, {}).get(SCHEMA_LABEL_KEY) == self.auth_db_label
        )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        This helper consolidates timestamp generation that was duplicated
        7 times across the module.
        
        Returns:
            str: Current datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.mmmmmm)
        
        Example:
            >>> timestamp = self._get_current_timestamp()
            >>> print(timestamp)
            '2025-10-30T15:30:45.123456'
        
        Notes:
            - Uses datetime.now().isoformat()
            - Compatible with SQLite datetime storage
            - Includes microsecond precision
        """
        return datetime.now().isoformat()
    
    def _log(self, level: str, message: str):
        """Centralized logging with LOG_PREFIX.
        
        This helper consolidates logging that was duplicated 15 times
        across the module, ensuring consistent prefix usage.
        
        Args:
            level: Log level (info, debug, warning, error)
            message: Log message (without prefix)
        
        Example:
            >>> self._log("info", LOG_SESSION_SAVED)
            >>> self._log("error", f"{LOG_ERROR_SAVE_SESSION}: {e}")
            >>> self._log("debug", LOG_NO_SESSION)
        
        Notes:
            - Automatically prepends LOG_PREFIX to all messages
            - Supports all standard logging levels
            - Gracefully handles missing logger (no-op)
        """
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(f"{LOG_PREFIX} {message}")
    
    def _ensure_db_loaded(self) -> bool:
        """Attempt to load database if not ready.
        
        This helper consolidates the database loading attempt that was
        duplicated 2 times in save_session() logic.
        
        Returns:
            bool: True if database is ready (was ready or successfully loaded),
                  False if database could not be loaded.
        
        Flow:
            1. Check if database is already ready
            2. If not ready, log attempt and call ensure_sessions_db()
            3. Check again after attempt
            4. Return final readiness status
        
        Example:
            >>> if not self._ensure_db_loaded():
            >>>     self._log("warning", LOG_DB_NOT_LOADED_WARNING)
            >>>     return None
            >>> 
            >>> # Database is ready, proceed with operation
            >>> self.zcli.data.insert(...)
        """
        if self._is_db_ready():
            return True
        
        self._log("debug", LOG_DB_NOT_LOADED_ATTEMPT)
        self.ensure_sessions_db()
        
        return self._is_db_ready()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Database Initialization
    # ═══════════════════════════════════════════════════════════════════════════
    
    def ensure_sessions_db(self):
        """Ensure the sessions database is initialized (declarative zCLI way).
        
        This method performs lazy initialization of the SQLite database using
        zCLI's declarative zData subsystem. It loads the schema from
        zSchema.auth.yaml, creates tables if needed, and performs initial cleanup.
        
        Process:
            1. Locate zSchema.auth.yaml in zAuth subsystem directory
            2. Load and parse schema using zParser
            3. Initialize zData handler with schema
            4. Create sessions table if it doesn't exist
            5. Create user_permissions table if it doesn't exist (for RBAC)
            6. Clean up any expired sessions
        
        Schema Location:
            - Located in zAuth subsystem directory
            - Path: zCLI/subsystems/zAuth/zSchema.auth.yaml
            - Unified schema for sessions + permissions
        
        Error Handling:
            - Schema not found: Log warning, return gracefully
            - Parse failure: Log warning, return gracefully
            - Handler creation failure: Log error, return gracefully
            - Wrong schema loaded: Log error, return gracefully
        
        Example:
            >>> # Explicit initialization (recommended)
            >>> session_mgr = SessionPersistence(zcli)
            >>> session_mgr.ensure_sessions_db()
            >>> 
            >>> # Lazy initialization (automatic on first use)
            >>> session_id = session_mgr.save_session(...)  # Calls ensure_sessions_db()
        
        Notes:
            - Safe to call multiple times (idempotent)
            - Automatic cleanup on initialization
            - Shares database with RBAC module
        """
        try:
            # Get absolute path to zSchema.auth.yaml (centralized location)
            # Schema Location (v1.5.4+): Centralized in zCLI/Schemas/
            zcli_root = Path(__file__).parent.parent.parent.parent  # Navigate to zCLI root
            schema_path = zcli_root / SCHEMAS_DIR / SCHEMA_FILE_NAME
            
            if not schema_path.exists():
                self._log("warning", f"{LOG_SCHEMA_NOT_FOUND}: {schema_path}")
                return
            
            # Load schema using zParser (bypass zLoader for package files)
            schema_content = Path(schema_path).read_text()
            parsed_schema = self.zcli.zparser.parse_file_content(schema_content, ".yaml")
            
            if not parsed_schema:
                self._log("warning", LOG_SCHEMA_PARSE_FAILED)
                return
            
            # Load schema into zData
            self.zcli.data.load_schema(parsed_schema)
            
            # Verify handler was created
            if not self.zcli.data.handler:
                self._log("error", LOG_HANDLER_FAILED)
                return
            
            # Verify correct schema is loaded
            loaded_label = self.zcli.data.schema.get(SCHEMA_META_KEY, {}).get(SCHEMA_LABEL_KEY)
            if loaded_label != self.auth_db_label:
                self._log("error", f"{LOG_WRONG_SCHEMA}: {loaded_label} (expected: {self.auth_db_label})")
                return
            
            # Create sessions table if it doesn't exist
            if not self.zcli.data.table_exists(TABLE_SESSIONS):
                self.zcli.data.create_table(TABLE_SESSIONS)
                self._log("info", LOG_TABLE_CREATED_SESSIONS)
            
            # Create permissions table if it doesn't exist (shared with RBAC)
            if not self.zcli.data.table_exists(TABLE_PERMISSIONS):
                self.zcli.data.create_table(TABLE_PERMISSIONS)
                self._log("info", LOG_TABLE_CREATED_PERMISSIONS)
            
            self._log("info", LOG_DB_INIT)
            
            # Clean up expired sessions on startup
            self.cleanup_expired()
            
        except Exception as e:
            self._log("error", f"{LOG_ERROR_INIT_DB}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Session Lifecycle Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def load_session(self):
        """Load and restore persistent session on startup (if exists and valid).
        
        This method checks the sessions database for a valid (non-expired)
        session and restores it to the in-memory session state, enabling
        "Remember me" functionality across application restarts.
        
        Session Restoration:
            1. Check if database is ready
            2. Query for most recent valid session (not expired)
            3. Restore session data to session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
            4. Set active_context to CONTEXT_ZSESSION
            5. Update last_accessed timestamp in database
        
        Query Logic:
            - WHERE: expires_at > current_time (not expired)
            - ORDER BY: last_accessed DESC (most recent first)
            - LIMIT: 1 (single most recent session)
        
        Restored Fields:
            - authenticated: Set to True
            - id: User ID from session
            - username: Username from session
            - role: User role from session
            - api_key: API token from session
            - session_id: Session identifier
        
        Returns:
            None: Updates session dictionary in-place
        
        Example:
            >>> # Called automatically by zAuth on initialization
            >>> session_mgr = SessionPersistence(zcli)
            >>> session_mgr.ensure_sessions_db()
            >>> session_mgr.load_session()
            >>> 
            >>> # Check if session was restored
            >>> is_authenticated = session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_AUTHENTICATED]
            >>> if is_authenticated:
            >>>     print(f"Restored session for: {session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION][ZAUTH_KEY_USERNAME]}")
        
        Security:
            - Only restores non-expired sessions
            - Verifies expires_at > current_time
            - Updates last_accessed to prevent premature expiration
        
        Error Handling:
            - Database not ready: Log debug message, return gracefully
            - No valid session: Log debug message, start clean
            - Query failure: Log error, return gracefully
        """
        try:
            # Check if zData is initialized with auth schema
            if not self._is_db_ready():
                self._log("debug", f"{LOG_DB_NOT_LOADED_SKIP} restore")
                return
            
            # Query for most recent valid session (not expired)
            now = self._get_current_timestamp()
            
            results = self.zcli.data.select(
                table=TABLE_SESSIONS,
                where=f"{FIELD_EXPIRES_AT} > '{now}'",
                order=ORDER_BY_LAST_ACCESSED,
                limit=QUERY_LIMIT_ONE
            )
            
            if not results or len(results) == 0:
                self._log("debug", LOG_NO_SESSION)
                return
            
            # Restore session to in-memory state (zSession context)
            session_data = results[0]
            
            get_zsession_data(self.session).update({
                ZAUTH_KEY_AUTHENTICATED: True,
                ZAUTH_KEY_ID: session_data.get(FIELD_USER_ID),
                ZAUTH_KEY_USERNAME: session_data.get(FIELD_USERNAME),
                ZAUTH_KEY_ROLE: session_data.get(FIELD_ROLE, "user"),
                ZAUTH_KEY_API_KEY: session_data.get(FIELD_TOKEN),
                SESSION_KEY_SESSION_ID: session_data.get(FIELD_SESSION_ID)
            })
            
            # Set active context to zSession
            self.session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT] = CONTEXT_ZSESSION
            
            # Update last_accessed timestamp
            self.zcli.data.update(
                table=TABLE_SESSIONS,
                fields=[FIELD_LAST_ACCESSED],
                values=[self._get_current_timestamp()],
                where=f"{FIELD_SESSION_ID} = '{session_data.get(FIELD_SESSION_ID)}'"
            )
            
            self._log("info", f"{LOG_SESSION_RESTORED}: {session_data.get(FIELD_USERNAME)}")
            
        except Exception as e:
            self._log("error", f"{LOG_ERROR_LOAD_SESSION}: {e}")
    
    def save_session(self, username: str, password_hash: str, user_id: Optional[str] = None, role: str = "user") -> Optional[str]:
        """Save current session to persistent storage (sessions database).
        
        Creates a new session record with DEFAULT_SESSION_DURATION_DAYS expiry,
        enabling "Remember me" functionality across app restarts. Deletes any
        existing sessions for the user (single session per user policy).
        
        Args:
            username: Username for the session (required)
            password_hash: bcrypt password hash for verification (from auth_password_security.py)
            user_id: Optional user ID (defaults to username if not provided)
            role: User role for the session (default: "user")
        
        Returns:
            str: Generated session_id if successful, None if failed
        
        Session Fields Generated:
            - session_id: TOKEN_LENGTH-byte cryptographically secure token
            - token: TOKEN_LENGTH-byte API token
            - created_at: Current timestamp
            - expires_at: Current timestamp + session_duration_days
            - last_accessed: Current timestamp
        
        Security:
            - Uses secrets.token_urlsafe(TOKEN_LENGTH) for secure tokens
            - Stores bcrypt hash (never plaintext password)
            - Single session per user (deletes existing sessions)
            - Automatic expiration after configured duration
        
        Example:
            >>> # After successful login
            >>> password_hash = pwd_security.hash_password("user_password")
            >>> session_id = session_mgr.save_session(
            ...     username="john_doe",
            ...     password_hash=password_hash,
            ...     user_id="zU_12345",
            ...     role="admin"
            ... )
            >>> if session_id:
            >>>     print(f"Session saved: {session_id}")
        
        Database Operations:
            1. Ensure database is loaded (lazy initialization)
            2. Generate session_id and token (cryptographically secure)
            3. Calculate expiration timestamp
            4. Delete existing sessions for user (single session policy)
            5. Insert new session record
            6. Update in-memory session with session_id
        
        Error Handling:
            - Database not ready: Attempt to load, warn if still unavailable
            - Existing session deletion: Log debug if no sessions found
            - Insert failure: Log error, return None
        """
        try:
            # Validate database is ready
            if not self._ensure_db_loaded():
                self._log("warning", LOG_DB_NOT_LOADED_WARNING)
                return None
            
            # Generate session data
            session_data = self._generate_session_data(username, user_id)
            
            # Delete existing sessions for user
            self._delete_existing_sessions(username)
            
            # Insert new session record
            self._insert_session_record(
                session_data['session_id'],
                session_data['user_id'],
                username,
                role,
                password_hash,
                session_data['token'],
                session_data['created_at'],
                session_data['expires_at'],
                session_data['last_accessed']
            )
            
            # Update in-memory session
            self._update_session_id(session_data['session_id'])
            
            # Log success
            self._log("info", f"{LOG_SESSION_SAVED}: {username} (expires: {session_data['expires_at']})")
            
            return session_data['session_id']
            
        except Exception as e:
            self._log("error", f"{LOG_ERROR_SAVE_SESSION}: {e}")
            return None
    
    def _generate_session_data(self, username: str, user_id: Optional[str]) -> Dict[str, str]:
        """Generate session data with secure tokens and timestamps."""
        # Generate unique session ID and API token (cryptographically secure)
        session_id = secrets.token_urlsafe(TOKEN_LENGTH)
        token = secrets.token_urlsafe(TOKEN_LENGTH)
        
        # Calculate expiration and timestamps
        expires_at = (datetime.now() + timedelta(days=self.session_duration_days)).isoformat()
        created_at = self._get_current_timestamp()
        last_accessed = created_at
        
        # Use user_id or fall back to username
        effective_user_id = user_id if user_id else username
        
        return {
            'session_id': session_id,
            'token': token,
            'user_id': effective_user_id,
            'created_at': created_at,
            'expires_at': expires_at,
            'last_accessed': last_accessed
        }
    
    def _delete_existing_sessions(self, username: str) -> None:
        """Delete any existing sessions for user (single session policy)."""
        try:
            self.zcli.data.delete(
                table=TABLE_SESSIONS,
                where=f"{FIELD_USERNAME} = '{username}'"
            )
        except Exception as e:
            self._log("debug", f"{LOG_NO_EXISTING_SESSIONS}: {e}")
    
    def _insert_session_record(
        self,
        session_id: str,
        user_id: str,
        username: str,
        role: str,
        password_hash: str,
        token: str,
        created_at: str,
        expires_at: str,
        last_accessed: str
    ) -> None:
        """Insert new session record into database."""
        self.zcli.data.insert(
            table=TABLE_SESSIONS,
            fields=[
                FIELD_SESSION_ID,
                FIELD_USER_ID,
                FIELD_USERNAME,
                FIELD_ROLE,
                FIELD_PASSWORD_HASH,
                FIELD_TOKEN,
                FIELD_CREATED_AT,
                FIELD_EXPIRES_AT,
                FIELD_LAST_ACCESSED
            ],
            values=[
                session_id,
                user_id,
                username,
                role,
                password_hash,
                token,
                created_at,
                expires_at,
                last_accessed
            ]
        )
    
    def _update_session_id(self, session_id: str) -> None:
        """Update in-memory session with session_id."""
        self.session[SESSION_KEY_ZAUTH][SESSION_KEY_SESSION_ID] = session_id
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions from database (housekeeping).
        
        This method removes all sessions where expires_at <= current time.
        Called automatically on startup (ensure_sessions_db) and can be
        called manually for periodic cleanup.
        
        Housekeeping Strategy:
            - Automatic: Called on database initialization
            - Manual: Can be scheduled (cron, periodic task)
            - Criteria: expires_at <= current timestamp
            - Effect: Frees database space, maintains data hygiene
        
        Returns:
            int: Number of sessions deleted (0 if none expired)
        
        Query Logic:
            - WHERE: expires_at <= current_time
            - DELETE: All matching records
            - RESULT: Count of deleted records
        
        Example:
            >>> # Automatic cleanup on startup
            >>> session_mgr.ensure_sessions_db()  # Calls cleanup_expired()
            >>> 
            >>> # Manual cleanup (scheduled task)
            >>> deleted = session_mgr.cleanup_expired()
            >>> if deleted > 0:
            >>>     print(f"Cleaned up {deleted} expired sessions")
            >>> 
            >>> # Periodic cleanup (cron-like)
            >>> import schedule
            >>> schedule.every().day.at("03:00").do(session_mgr.cleanup_expired)
        
        Security:
            - Removes only expired sessions (safe operation)
            - Prevents accumulation of old sessions
            - Frees storage space over time
        
        Error Handling:
            - Database not ready: Log debug, return 0
            - No expired sessions: Log debug, return 0
            - Delete failure: Log error, return 0
        """
        try:
            # Check if zData is initialized with auth schema
            if not self._is_db_ready():
                self._log("debug", f"{LOG_DB_NOT_LOADED_SKIP} cleanup")
                return 0
            
            # Delete expired sessions (declarative zData operation)
            now = self._get_current_timestamp()
            
            deleted = self.zcli.data.delete(
                table=TABLE_SESSIONS,
                where=f"{FIELD_EXPIRES_AT} <= '{now}'"
            )
            
            if deleted and deleted > 0:
                self._log("info", f"{LOG_SESSIONS_CLEANED}: {deleted}")
                return deleted
            else:
                self._log("debug", LOG_NO_EXPIRED_SESSIONS)
                return 0
                
        except Exception as e:
            self._log("error", f"{LOG_ERROR_CLEANUP}: {e}")
            return 0
