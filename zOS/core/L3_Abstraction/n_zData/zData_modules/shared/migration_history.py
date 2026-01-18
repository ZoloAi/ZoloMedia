# zCLI/subsystems/zData/zData_modules/shared/migration_history.py
"""
Migration history tracking for declarative migrations in zData.

This module provides functionality to track applied migrations in a special
`_zdata_migrations` table stored in the same database as application data.
It enables idempotent migrations (avoid re-applying the same schema) and
provides an audit trail of when and how the schema evolved.

Core Principle
--------------
The `_zdata_migrations` table stores metadata about each migration execution:
- Schema hash (SHA256 of YAML content) - prevents duplicate migrations
- Schema version (e.g., "v1.2.3" or git commit hash) - human-readable identifier
- Applied timestamp - when migration ran
- Duration - how long it took
- Metrics - tables/columns added/dropped
- Status - success or failed
- Error message - if failed, why

This provides:
- **Idempotency**: Check hash before migrating to avoid duplicates
- **Audit Trail**: Track what was applied and when
- **Rollback Info**: See what changed in case rollback needed
- **Performance Metrics**: Track migration duration over time

Table Schema
-----------
The _zdata_migrations table is auto-created on first use:

_zdata_migrations:
  Columns:
    id: {type: integer, primary_key: true, auto_increment: true}
    schema_version: {type: string}      # e.g., "v1.2.3" or git commit
    schema_hash: {type: string}         # SHA256 of YAML content
    applied_at: {type: timestamp}       # When migration ran
    duration_ms: {type: integer}        # Migration execution time
    tables_added: {type: integer}       # Count of tables created
    tables_dropped: {type: integer}     # Count of tables dropped
    columns_added: {type: integer}      # Count of columns added
    columns_dropped: {type: integer}    # Count of columns dropped
    status: {type: string}              # "success" or "failed"
    error_message: {type: string}       # If failed, error details

Usage Examples
-------------
Ensure migrations table exists:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import ensure_migrations_table
    >>> ensure_migrations_table(adapter)

Record successful migration:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import record_migration
    >>> metrics = {
    ...     'schema_version': 'v1.2.3',
    ...     'schema_hash': 'abc123...',
    ...     'tables_added': 2,
    ...     'tables_dropped': 0,
    ...     'columns_added': 5,
    ...     'columns_dropped': 1,
    ...     'duration_ms': 234,
    ...     'status': 'success'
    ... }
    >>> record_migration(adapter, metrics)

Check if migration already applied:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import is_migration_applied
    >>> schema_hash = get_current_schema_hash(schema_dict)
    >>> if is_migration_applied(adapter, schema_hash):
    ...     print("Migration already applied - skipping")

Get migration history:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.migration_history import get_migration_history
    >>> history = get_migration_history(adapter)
    >>> for record in history:
    ...     print(f"{record['applied_at']}: {record['schema_version']} - {record['status']}")

Integration
----------
- **Used By**: ddl_migrate.py (after successful migration)
- **Depends On**: None (uses adapter directly)
- **Storage**: Same database as application data

See Also
--------
- ddl_migrate.py: Migration executor that records history
- schema_diff.py: Computes diffs for migrations
- zData.py: Main facade with get_migration_history() method
"""

import hashlib
import time
from datetime import datetime
from zOS import Dict, List, Any

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Table Name
TABLE_MIGRATIONS = "_zdata_migrations"

# Column Names
COL_ID = "id"
COL_SCHEMA_VERSION = "schema_version"
COL_SCHEMA_HASH = "schema_hash"
COL_APPLIED_AT = "applied_at"
COL_DURATION_MS = "duration_ms"
COL_TABLES_ADDED = "tables_added"
COL_TABLES_DROPPED = "tables_dropped"
COL_COLUMNS_ADDED = "columns_added"
COL_COLUMNS_DROPPED = "columns_dropped"
COL_STATUS = "status"
COL_ERROR_MESSAGE = "error_message"

# Status Values
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"

# Default Values
DEFAULT_VERSION = "unknown"
DEFAULT_DURATION = 0

# Hash Algorithm
HASH_ALGORITHM = "sha256"

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_migrations_table(adapter: Any) -> None:
    """
    Create _zdata_migrations table if it doesn't exist.
    
    This function should be called before any migration operations to ensure
    the history table exists. It's idempotent - safe to call multiple times.
    
    Args:
        adapter: Database adapter (SQLite, PostgreSQL, or CSV)
    
    Examples:
        >>> ensure_migrations_table(adapter)
        # Table created if not exists, otherwise no-op
    
    Notes:
        - Uses IF NOT EXISTS for idempotency
        - Table schema matches documentation above
        - Timestamps stored as ISO 8601 strings for portability
    """
    # Check if table already exists
    if adapter.table_exists(TABLE_MIGRATIONS):
        return
    
    # Define table schema
    schema = {
        COL_ID: {
            "type": "integer",
            "primary_key": True,
            "auto_increment": True
        },
        COL_SCHEMA_VERSION: {
            "type": "string"
        },
        COL_SCHEMA_HASH: {
            "type": "string"
        },
        COL_APPLIED_AT: {
            "type": "string"  # ISO 8601 timestamp
        },
        COL_DURATION_MS: {
            "type": "integer"
        },
        COL_TABLES_ADDED: {
            "type": "integer"
        },
        COL_TABLES_DROPPED: {
            "type": "integer"
        },
        COL_COLUMNS_ADDED: {
            "type": "integer"
        },
        COL_COLUMNS_DROPPED: {
            "type": "integer"
        },
        COL_STATUS: {
            "type": "string"
        },
        COL_ERROR_MESSAGE: {
            "type": "string"
        }
    }
    
    # Create table
    adapter.create_table(TABLE_MIGRATIONS, schema)

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION RECORDING
# ═══════════════════════════════════════════════════════════════════════════════

def record_migration(adapter: Any, metrics: Dict[str, Any]) -> None:
    """
    Record a migration execution in the history table.
    
    Inserts a new row into _zdata_migrations with all migration metadata.
    This should be called after a successful (or failed) migration to maintain
    the audit trail.
    
    Args:
        adapter: Database adapter
        metrics: Dict with migration metadata:
            - schema_version: Version string (required)
            - schema_hash: SHA256 hash of schema (required)
            - tables_added: Count of tables created (default 0)
            - tables_dropped: Count of tables dropped (default 0)
            - columns_added: Count of columns added (default 0)
            - columns_dropped: Count of columns dropped (default 0)
            - duration_ms: Migration duration in milliseconds (default 0)
            - status: "success" or "failed" (required)
            - error_message: Error details if failed (optional)
    
    Examples:
        >>> metrics = {
        ...     'schema_version': 'v1.2.3',
        ...     'schema_hash': 'abc123...',
        ...     'tables_added': 2,
        ...     'status': 'success'
        ... }
        >>> record_migration(adapter, metrics)
    
    Notes:
        - Ensure migrations table exists before calling
        - Timestamps are auto-generated (current time)
        - All metrics have sensible defaults if not provided
    """
    # Ensure table exists
    ensure_migrations_table(adapter)
    
    # Build record
    record = {
        COL_SCHEMA_VERSION: metrics.get(COL_SCHEMA_VERSION, DEFAULT_VERSION),
        COL_SCHEMA_HASH: metrics.get(COL_SCHEMA_HASH, ""),
        COL_APPLIED_AT: datetime.now().isoformat(),
        COL_DURATION_MS: metrics.get(COL_DURATION_MS, DEFAULT_DURATION),
        COL_TABLES_ADDED: metrics.get(COL_TABLES_ADDED, 0),
        COL_TABLES_DROPPED: metrics.get(COL_TABLES_DROPPED, 0),
        COL_COLUMNS_ADDED: metrics.get(COL_COLUMNS_ADDED, 0),
        COL_COLUMNS_DROPPED: metrics.get(COL_COLUMNS_DROPPED, 0),
        COL_STATUS: metrics.get(COL_STATUS, STATUS_SUCCESS),
        COL_ERROR_MESSAGE: metrics.get(COL_ERROR_MESSAGE, "")
    }
    
    # Insert record (adapter expects fields and values as separate lists)
    fields = list(record.keys())
    values = list(record.values())
    adapter.insert(TABLE_MIGRATIONS, fields, values)

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

def get_migration_history(adapter: Any, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve migration history records.
    
    Returns list of migration records ordered by applied_at (most recent first).
    Useful for displaying migration audit trail to users.
    
    Args:
        adapter: Database adapter
        limit: Maximum number of records to return (default 100)
    
    Returns:
        List of migration record dicts, each with keys:
        - id, schema_version, schema_hash, applied_at, duration_ms,
          tables_added, tables_dropped, columns_added, columns_dropped,
          status, error_message
    
    Examples:
        >>> history = get_migration_history(adapter, limit=10)
        >>> for record in history:
        ...     print(f"{record['applied_at']}: {record['status']}")
    
    Notes:
        - Returns empty list if table doesn't exist
        - Results ordered by applied_at DESC (newest first)
        - Limit prevents loading huge history (default 100)
    """
    # Check if table exists
    if not adapter.table_exists(TABLE_MIGRATIONS):
        return []
    
    # Query history with limit and order
    results = adapter.select(
        TABLE_MIGRATIONS,
        order_by=f"{COL_APPLIED_AT} DESC",
        limit=limit
    )
    
    return results if results else []

def is_migration_applied(adapter: Any, schema_hash: str) -> bool:
    """
    Check if a migration with the given schema hash has been applied.
    
    Queries _zdata_migrations to see if a successful migration with this
    schema hash exists. Used to prevent duplicate migrations.
    
    Args:
        adapter: Database adapter
        schema_hash: SHA256 hash of schema YAML content
    
    Returns:
        True if migration already applied successfully, False otherwise
    
    Examples:
        >>> schema_hash = get_current_schema_hash(schema_dict)
        >>> if is_migration_applied(adapter, schema_hash):
        ...     print("Migration already applied")
    
    Notes:
        - Only considers successful migrations (status="success")
        - Returns False if table doesn't exist
        - Schema hash provides idempotency guarantee
    """
    # Check if table exists
    if not adapter.table_exists(TABLE_MIGRATIONS):
        return False
    
    # Query for matching hash with success status
    where = {
        COL_SCHEMA_HASH: schema_hash,
        COL_STATUS: STATUS_SUCCESS
    }
    
    results = adapter.select(TABLE_MIGRATIONS, where=where, limit=1)
    
    return len(results) > 0 if results else False

# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA HASHING
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_schema_hash(schema: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of schema dictionary.
    
    Converts schema dict to stable string representation and computes hash.
    The hash serves as a unique identifier for the schema state, enabling
    idempotent migrations.
    
    Args:
        schema: Schema dictionary (from YAML)
    
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
    
    Examples:
        >>> schema = {'Tables': {'users': {'Columns': {...}}}}
        >>> hash_value = get_current_schema_hash(schema)
        >>> len(hash_value)
        64
    
    Notes:
        - Uses str() for stable serialization
        - Hash is deterministic (same schema → same hash)
        - Hash changes if any part of schema changes
    """
    # Convert schema to stable string representation
    schema_str = str(schema)
    
    # Compute SHA256 hash
    hash_obj = hashlib.sha256(schema_str.encode('utf-8'))
    
    return hash_obj.hexdigest()

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION TIMING
# ═══════════════════════════════════════════════════════════════════════════════

class MigrationTimer:
    """
    Context manager for timing migration execution.
    
    Simplifies tracking migration duration with automatic start/stop timing.
    
    Usage:
        >>> with MigrationTimer() as timer:
        ...     # Execute migration operations
        ...     pass
        >>> duration_ms = timer.duration_ms()
    """
    
    def __init__(self):
        """Initialize timer (not started yet)."""
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timing when entering context."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing when exiting context."""
        self.end_time = time.time()
        return False  # Don't suppress exceptions
    
    def duration_ms(self) -> int:
        """
        Get migration duration in milliseconds.
        
        Returns:
            Duration in milliseconds (rounded to nearest integer)
        
        Notes:
            - Returns 0 if timer hasn't been stopped yet
        """
        if self.start_time is None or self.end_time is None:
            return 0
        
        duration_seconds = self.end_time - self.start_time
        return int(duration_seconds * 1000)

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "ensure_migrations_table",
    "record_migration",
    "get_migration_history",
    "is_migration_applied",
    "get_current_schema_hash",
    "MigrationTimer",
    "TABLE_MIGRATIONS",
    "STATUS_SUCCESS",
    "STATUS_FAILED"
]

