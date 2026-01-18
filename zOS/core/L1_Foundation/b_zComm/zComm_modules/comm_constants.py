# zCLI/L1_Foundation/b_zComm/zComm_modules/constants.py
"""
Shared constants for zComm subsystem.

Public constants that may be referenced by other subsystems or configuration.
Module-specific constants (LOG_*, ERROR_*) remain in their respective modules.
"""

# Service Identifiers (Public API)
SERVICE_POSTGRESQL = "postgresql"
# Future: SERVICE_REDIS = "redis"
# Future: SERVICE_MONGODB = "mongodb"

# Network Configuration (Shared)
PORT_MIN = 1
PORT_MAX = 65535
DEFAULT_HOST = "localhost"
DEFAULT_TIMEOUT_SECONDS = 1

# HTTP Configuration
HTTP_DEFAULT_TIMEOUT = 10  # seconds

# WebSocket Close Codes (Public API)
WS_CLOSE_CODE_POLICY_VIOLATION = 1008
WS_CLOSE_CODE_INTERNAL_ERROR = 1011

# WebSocket Close Reasons (Public API)
WS_REASON_INVALID_ORIGIN = "Invalid origin"
WS_REASON_AUTH_REQUIRED = "Authentication required"
WS_REASON_INVALID_TOKEN = "Invalid token"
WS_REASON_MAX_CONNECTIONS = "Maximum connections reached"

# Storage Configuration
STORAGE_DEFAULT_BACKEND = "local"
STORAGE_SUPPORTED_BACKENDS = ["local", "s3", "azure", "gcs"]

# Storage Config Keys (Public API - used in .zEnv files)
STORAGE_CONFIG_KEY_BACKEND = "storage_backend"
STORAGE_CONFIG_KEY_LOCAL_ROOT = "storage_local_root"
STORAGE_CONFIG_KEY_S3_BUCKET = "storage_s3_bucket"
STORAGE_CONFIG_KEY_S3_REGION = "storage_s3_region"

# PostgreSQL Defaults (Shared)
POSTGRESQL_DEFAULT_PORT = 5432
POSTGRESQL_DEFAULT_USER = "postgres"
POSTGRESQL_DEFAULT_DATABASE = "postgres"
POSTGRESQL_DEFAULT_HOST = "localhost"

# Status Dict Keys (Public API)
STATUS_KEY_ERROR = "error"
STATUS_KEY_SERVICE = "service"
STATUS_KEY_RUNNING = "running"
STATUS_KEY_PORT = "port"
STATUS_KEY_OS = "os"
STATUS_KEY_CONNECTION_INFO = "connection_info"
STATUS_KEY_MESSAGE = "message"

# Connection Info Keys (Public API)
CONN_KEY_HOST = "host"
CONN_KEY_PORT = "port"
CONN_KEY_USER = "user"
CONN_KEY_DATABASE = "database"
CONN_KEY_CONNECTION_STRING = "connection_string"

