# zCLI/L2_Core/d_zAuth/zAuth_modules/auth_constants.py
"""
Centralized constants for zAuth subsystem.

This module provides a single source of truth for all zAuth constants, including:
- Status and response keys (PUBLIC)
- Database configuration (PUBLIC)
- Field names (PUBLIC)
- Log messages (INTERNAL - prefixed with _)
- Error messages (INTERNAL - prefixed with _)
- Default values (PUBLIC)
- Schema configuration (PUBLIC)

Constants Naming Convention:
- PUBLIC constants: No prefix (e.g., STATUS_SUCCESS, DB_LABEL_AUTH)
- INTERNAL constants: _ prefix (e.g., _LOG_PREFIX_AUTH, _ERR_NO_SESSION)

Internal constants are implementation details not intended for external use.
"""

# Status Response Constants
STATUS_SUCCESS = "success"
STATUS_FAIL = "fail"
STATUS_ERROR = "error"
STATUS_PENDING = "pending"

# Response Dictionary Keys
KEY_STATUS = "status"
KEY_REASON = "reason"
KEY_CREDENTIALS = "credentials"
KEY_USER = "user"
KEY_CONTEXT = "context"
KEY_CLEARED = "cleared"
KEY_PERSIST = "persist"
KEY_DELETE_PERSISTENT = "delete_persistent"
KEY_PASSWORD = "password"
KEY_APP_NAME = "app_name"
KEY_USERNAME = "username"
KEY_SERVER_URL = "server_url"

# Database Configuration
DB_LABEL_AUTH = "auth"
TABLE_SESSIONS = "sessions"
TABLE_PERMISSIONS = "user_permissions"

# Field Names (sessions and user_permissions tables)
FIELD_SESSION_ID = "session_id"
FIELD_USER_ID = "user_id"
FIELD_USERNAME = "username"
FIELD_PASSWORD = "password"
FIELD_ROLE = "role"
FIELD_API_KEY = "api_key"
FIELD_PASSWORD_HASH = "password_hash"
FIELD_TOKEN = "token"
FIELD_CREATED_AT = "created_at"
FIELD_EXPIRES_AT = "expires_at"
FIELD_LAST_ACCESSED = "last_accessed"
FIELD_PERMISSION = "permission"
FIELD_GRANTED_BY = "granted_by"
FIELD_GRANTED_AT = "granted_at"

# Schema Configuration
SCHEMAS_DIR = "Schemas"
SCHEMA_FILE_NAME = "zSchema.auth.yaml"
SCHEMA_META_KEY = "zMeta"
SCHEMA_LABEL_KEY = "Data_Label"

# Query Configuration
QUERY_LIMIT_ONE = 1
_QUERY_LEN_ZERO = 0  # Internal: Query length check
ORDER_BY_LAST_ACCESSED = "last_accessed DESC"

# Session Configuration
DEFAULT_SESSION_DURATION_DAYS = 7
_TOKEN_LENGTH = 32  # Internal: Token byte length
_SESSION_KEY_SESSION_ID = "session_id"  # Internal: Session storage key

# Default Values (Authentication)
DEFAULT_SERVER_URL = "http://localhost:5000"
DEFAULT_USER_MODEL = "@.zCloud.schemas.schema.zIndex.zUsers"
DEFAULT_ID_FIELD = "id"
DEFAULT_USERNAME_FIELD = "username"
DEFAULT_ROLE_FIELD = "role"
DEFAULT_API_KEY_FIELD = "api_key"
DEFAULT_PERSIST = True
DEFAULT_DELETE_PERSISTENT = True

# Default Values (RBAC)
DEFAULT_GRANTED_BY = "system"

# Default Values (Login)
DEFAULT_IDENTITY_FIELDS = ["email", "username"]
DEFAULT_PASSWORD_FIELD = "password"
DEFAULT_ROLE = "zUser"

# Reserved Keywords
RESERVED_ZOLO_KEYWORD = "zolo"

# Environment Variable Keys
ENV_USE_REMOTE_API = "ZOLO_USE_REMOTE_API"
ENV_API_URL = "ZOLO_API_URL"
ENV_TRUE = "true"

# HTTP/API Constants
HTTP_MODE_KEY = "mode"
HTTP_MODE_TERMINAL = "Terminal"
HTTP_DATA_KEY = "data"

# Placeholder Values (for TODO: zData integration)
PLACEHOLDER_USER_ID = 12345
PLACEHOLDER_ROLE = "user"

# bcrypt Configuration
BCRYPT_ROUNDS = 12
BCRYPT_MAX_PASSWORD_BYTES = 72
BCRYPT_PREFIX = "$2b$"
_SALT_LENGTH = 22  # Internal: bcrypt salt length
_HASH_TIME_SECONDS = 0.3  # Internal: Estimated hash time
_ENCODING_UTF8 = "utf-8"  # Internal: Password encoding

# Log Level Constants (Internal)
_LOG_LEVEL_INFO = "info"
_LOG_LEVEL_WARNING = "warning"
_LOG_LEVEL_ERROR = "error"
_LOG_LEVEL_DEBUG = "debug"

# Logging Prefixes (Internal)
_LOG_PREFIX_AUTH = "[Authentication]"
_LOG_PREFIX_RBAC = "[RBAC]"
_LOG_PREFIX_PERSISTENCE = "[SessionPersistence]"
_LOG_PREFIX_PASSWORD = "[PasswordSecurity]"
_LOG_PREFIX_LOGIN = "[zLogin]"

# Log Messages - Authentication (Internal)
_LOG_REMOTE_AUTH = f"{_LOG_PREFIX_AUTH} Authenticating with remote server"
_LOG_REMOTE_SUCCESS = f"{_LOG_PREFIX_AUTH} Remote authentication successful"
_LOG_REMOTE_FAIL = f"{_LOG_PREFIX_AUTH} Remote authentication failed"
_LOG_AUTH_FAILED = f"{_LOG_PREFIX_AUTH} Authentication failed: Invalid credentials"
_LOG_LOGOUT_ZSESSION = f"{_LOG_PREFIX_AUTH} Logged out from zSession"
_LOG_LOGOUT_APP = f"{_LOG_PREFIX_AUTH} Logged out from application"
_LOG_LOGOUT_ALL_APPS = f"{_LOG_PREFIX_AUTH} Logged out from all applications"
_LOG_APP_AUTH_SUCCESS = f"{_LOG_PREFIX_AUTH} Application user authenticated"
_LOG_APP_SWITCH = f"{_LOG_PREFIX_AUTH} Switched to application"
_LOG_APP_SWITCH_FAIL = f"{_LOG_PREFIX_AUTH} Cannot switch to application: Not authenticated"
_LOG_CONTEXT_SET = f"{_LOG_PREFIX_AUTH} Active context set to"
_LOG_CONTEXT_INVALID = f"{_LOG_PREFIX_AUTH} Invalid context"
_LOG_CONTEXT_NO_ZSESSION = f"{_LOG_PREFIX_AUTH} Cannot set zSession context: Not authenticated"
_LOG_CONTEXT_NO_APP = f"{_LOG_PREFIX_AUTH} Cannot set application context: No active app"
_LOG_CONTEXT_NO_DUAL = f"{_LOG_PREFIX_AUTH} Cannot set dual context: Requires both zSession and application auth"
_LOG_SESSION_DELETE = f"{_LOG_PREFIX_AUTH} Deleted persistent session for"
_LOG_SESSION_DELETE_FAIL = f"{_LOG_PREFIX_AUTH} Could not delete session"
_LOG_APP_AUTH_ERROR = f"{_LOG_PREFIX_AUTH} Application authentication failed"
_LOG_CONTEXT_UPDATED = f"{_LOG_PREFIX_AUTH} Active context updated"
_LOG_DUAL_MODE_ACTIVATED = f"{_LOG_PREFIX_AUTH} Dual mode activated"

# Log Messages - RBAC (Internal)
_LOG_NOT_AUTHENTICATED = "User not authenticated, role check failed"
_LOG_NO_ROLE = "User has no role assigned"
_LOG_INVALID_ROLE_TYPE = "Invalid role type"
_LOG_NO_USER_ID = "No user_id in session"
_LOG_PERMISSION_CHECK_FAILED = "User not authenticated, permission check failed"
_LOG_PERMISSION_GRANTED = "Granted permission"
_LOG_PERMISSION_ALREADY_GRANTED = "Permission already granted to user"
_LOG_PERMISSION_REVOKED = "Revoked permission"
_LOG_INVALID_PERMISSION_TYPE = "Invalid permission type"
_LOG_PERMISSION_ERROR = "Error checking permission"
_LOG_GRANT_ERROR = "Error granting permission"
_LOG_REVOKE_ERROR = "Error revoking permission"
_LOG_DB_INIT = "Auth database initialized (sessions + permissions)"
_LOG_TABLE_CREATED = "User permissions table created"
_LOG_SESSIONS_TABLE_CREATED = "Sessions table created"
_LOG_SCHEMA_LOADED = "Auth schema loaded"
_LOG_SCHEMA_NOT_FOUND = "Auth schema not found"
_LOG_SCHEMA_PARSE_FAILED = "Failed to parse auth schema"
_LOG_HANDLER_FAILED = "Failed to create data handler after loading schema"
_LOG_WRONG_SCHEMA = "Wrong schema loaded"
_LOG_DB_ERROR = "Error initializing permissions database"
_LOG_CONTEXT_ZSESSION = "Checking role in zSession context"
_LOG_CONTEXT_APPLICATION = "Checking role in application context"
_LOG_CONTEXT_DUAL = "Checking role in dual context (OR logic)"
_LOG_DUAL_ROLE_MATCH = "Role matched in dual context"
_LOG_NO_ACTIVE_APP = "No active application in session"
_LOG_UNKNOWN_CONTEXT = "Unknown active context"

# Log Messages - Session Persistence (Internal)
_LOG_TABLE_CREATED_SESSIONS = "Sessions table created"
_LOG_TABLE_CREATED_PERMISSIONS = "User permissions table created"
_LOG_SESSION_RESTORED = "Restored persistent session for user"
_LOG_SESSION_SAVED = "Persistent session saved for user"
_LOG_SESSIONS_CLEANED = "Cleaned up expired session(s)"
_LOG_NO_SESSION = "No valid persistent session found"
_LOG_NO_EXPIRED_SESSIONS = "No expired sessions to clean up"
_LOG_DB_NOT_LOADED_SKIP = "Sessions database not loaded, skipping"
_LOG_DB_NOT_LOADED_ATTEMPT = "Auth DB not loaded, attempting to initialize..."
_LOG_DB_NOT_LOADED_WARNING = "Auth database not loaded, cannot persist session"
_LOG_NO_EXISTING_SESSIONS = "No existing sessions to delete"
_LOG_ERROR_INIT_DB = "Error initializing sessions database"
_LOG_ERROR_LOAD_SESSION = "Error loading persistent session"
_LOG_ERROR_SAVE_SESSION = "Error saving persistent session"
_LOG_ERROR_CLEANUP = "Error cleaning up expired sessions"

# Log Messages - Password Security (Internal)
_LOG_TRUNCATION_WARNING = "Password > 72 bytes, truncating (bcrypt limit)"
_LOG_VERIFICATION_ERROR = "Password verification error"

# Error Messages (Internal)
_ERR_NO_SESSION = "No session available"
_ERR_INVALID_CREDS = "Invalid credentials"
_ERR_CONNECTION_FAILED = "Connection failed"
_ERR_APP_NAME_REQUIRED = "app_name required for application logout"
_ERR_APP_NOT_AUTH = "Not authenticated to"
_ERR_INVALID_CONTEXT = "Invalid context"
_ERR_NO_ACTIVE_APP = "No active app"
_ERR_EMPTY_PASSWORD = "Password cannot be empty"

# User Messages (Internal)
_MSG_AWAITING_GUI = "Awaiting GUI response"
_MSG_NOT_AUTHENTICATED = "not_authenticated"

# Export PUBLIC constants only (internal constants with _ prefix are not exported)
__all__ = [
    # Status & Keys (PUBLIC API)
    'STATUS_SUCCESS', 'STATUS_FAIL', 'STATUS_ERROR', 'STATUS_PENDING',
    'KEY_STATUS', 'KEY_REASON', 'KEY_CREDENTIALS', 'KEY_USER', 'KEY_CONTEXT',
    'KEY_CLEARED', 'KEY_PERSIST', 'KEY_DELETE_PERSISTENT', 'KEY_PASSWORD',
    'KEY_APP_NAME', 'KEY_USERNAME', 'KEY_SERVER_URL',
    
    # Database (PUBLIC API)
    'DB_LABEL_AUTH', 'TABLE_SESSIONS', 'TABLE_PERMISSIONS',
    
    # Fields (PUBLIC API)
    'FIELD_SESSION_ID', 'FIELD_USER_ID', 'FIELD_USERNAME', 'FIELD_PASSWORD',
    'FIELD_ROLE', 'FIELD_API_KEY', 'FIELD_PASSWORD_HASH', 'FIELD_TOKEN',
    'FIELD_CREATED_AT', 'FIELD_EXPIRES_AT', 'FIELD_LAST_ACCESSED',
    'FIELD_PERMISSION', 'FIELD_GRANTED_BY', 'FIELD_GRANTED_AT',
    
    # Schema (PUBLIC API)
    'SCHEMAS_DIR', 'SCHEMA_FILE_NAME', 'SCHEMA_META_KEY', 'SCHEMA_LABEL_KEY',
    
    # Query (PUBLIC API)
    'QUERY_LIMIT_ONE', 'ORDER_BY_LAST_ACCESSED',
    
    # Session (PUBLIC API)
    'DEFAULT_SESSION_DURATION_DAYS',
    
    # Defaults (PUBLIC API)
    'DEFAULT_SERVER_URL', 'DEFAULT_USER_MODEL', 'DEFAULT_ID_FIELD',
    'DEFAULT_USERNAME_FIELD', 'DEFAULT_ROLE_FIELD', 'DEFAULT_API_KEY_FIELD',
    'DEFAULT_PERSIST', 'DEFAULT_DELETE_PERSISTENT', 'DEFAULT_GRANTED_BY',
    'DEFAULT_IDENTITY_FIELDS', 'DEFAULT_PASSWORD_FIELD', 'DEFAULT_ROLE',
    
    # Reserved (PUBLIC API)
    'RESERVED_ZOLO_KEYWORD',
    
    # Environment (PUBLIC API)
    'ENV_USE_REMOTE_API', 'ENV_API_URL', 'ENV_TRUE',
    
    # HTTP/API (PUBLIC API)
    'HTTP_MODE_KEY', 'HTTP_MODE_TERMINAL', 'HTTP_DATA_KEY',
    
    # Placeholders (PUBLIC API - temporary)
    'PLACEHOLDER_USER_ID', 'PLACEHOLDER_ROLE',
    
    # bcrypt (PUBLIC API)
    'BCRYPT_ROUNDS', 'BCRYPT_MAX_PASSWORD_BYTES', 'BCRYPT_PREFIX',
]
