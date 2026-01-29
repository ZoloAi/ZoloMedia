# zCLI/subsystems/zData/zData_modules/shared/migration_detection.py
"""
Migration detection and schema comparison utilities.

Provides functions for:
- Computing schema hashes (SHA256)
- Detecting schema changes (added/dropped/modified columns)
- Suggesting version bumps (semantic versioning)
- Loading migration history
"""

import hashlib
import yaml
from zOS import Dict, List, Any, Optional, Tuple
from pathlib import Path


def compute_schema_hash(schema: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of a schema dictionary.
    
    Used for change detection - if hash changes, schema has been modified.
    
    Args:
        schema: Schema dictionary (from YAML)
    
    Returns:
        str: 64-character SHA256 hex digest
    
    Example:
        >>> schema = {'zMeta': {...}, 'users': {...}}
        >>> compute_schema_hash(schema)
        'abc123def456...'
    """
    # Convert schema to canonical YAML string (sorted keys)
    schema_yaml = yaml.dump(schema, sort_keys=True, default_flow_style=False)
    
    # Compute SHA256 hash
    hash_obj = hashlib.sha256(schema_yaml.encode('utf-8'))
    return hash_obj.hexdigest()


def get_last_migration(z: Any, table_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the last applied migration for a table.
    
    Queries __zmigration_{table_name} for the most recent migration record.
    
    Args:
        z: zCLI instance
        table_name: Table name (e.g., 'users')
    
    Returns:
        Dict with keys: to_version, schema_hash, applied_at, etc.
        None if no migrations found or table doesn't exist
    
    Example:
        >>> last = get_last_migration(z, 'users')
        >>> last['to_version']
        'v1.3.0'
    """
    migration_table = f"__zmigration_{table_name}"
    
    try:
        # Try to query the migration table
        result = z.data.select(
            table=migration_table,
            order_by="applied_at DESC",
            limit=1
        )
        
        if result and len(result) > 0:
            return result[0]
        
        return None
        
    except Exception as e:
        # Table doesn't exist yet (first migration) or other error
        return None


def detect_schema_changes(old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect changes between two schema versions.
    
    Compares column definitions to find added, dropped, and modified fields.
    
    Args:
        old_schema: Previous schema dict
        new_schema: Current schema dict
    
    Returns:
        Dict with keys:
        - added: List of new columns [{name, type, nullable, default}, ...]
        - dropped: List of removed columns [{name, type}, ...]
        - modified: List of changed columns [{name, old_type, new_type, changes}, ...]
    
    Example:
        >>> changes = detect_schema_changes(old, new)
        >>> changes['added']
        [{'name': 'cover_url', 'type': 'str', 'nullable': True}]
    """
    changes = {
        'added': [],
        'dropped': [],
        'modified': []
    }
    
    # Get table definitions (skip Meta)
    old_tables = {k: v for k, v in old_schema.items() if k != 'zMeta'}
    new_tables = {k: v for k, v in new_schema.items() if k != 'zMeta'}
    
    # For each table, compare columns
    for table_name in new_tables.keys():
        old_columns = old_tables.get(table_name, {})
        new_columns = new_tables[table_name]
        
        old_column_names = set(old_columns.keys())
        new_column_names = set(new_columns.keys())
        
        # Detect added columns
        for col_name in (new_column_names - old_column_names):
            col_def = new_columns[col_name]
            changes['added'].append({
                'name': col_name,
                'type': col_def.get('type', 'unknown'),
                'nullable': not col_def.get('required', False),
                'default': col_def.get('default'),
                'comment': col_def.get('comment')
            })
        
        # Detect dropped columns
        for col_name in (old_column_names - new_column_names):
            col_def = old_columns[col_name]
            changes['dropped'].append({
                'name': col_name,
                'type': col_def.get('type', 'unknown')
            })
        
        # Detect modified columns
        for col_name in (old_column_names & new_column_names):
            old_col = old_columns[col_name]
            new_col = new_columns[col_name]
            
            # Check for type changes
            old_type = old_col.get('type')
            new_type = new_col.get('type')
            
            if old_type != new_type:
                changes['modified'].append({
                    'name': col_name,
                    'old_type': old_type,
                    'new_type': new_type,
                    'change': 'type'
                })
            
            # Check for required changes
            old_required = old_col.get('required', False)
            new_required = new_col.get('required', False)
            
            if old_required != new_required:
                changes['modified'].append({
                    'name': col_name,
                    'old_required': old_required,
                    'new_required': new_required,
                    'change': 'required'
                })
    
    return changes


def is_breaking_change(changes: Dict[str, List[Dict[str, Any]]]) -> bool:
    """
    Determine if schema changes are breaking.
    
    Breaking changes:
    - Dropped columns
    - Modified column types
    - Adding required (non-nullable) columns without defaults
    - Changing nullable to required
    
    Non-breaking changes:
    - Adding nullable columns
    - Adding columns with defaults
    - Changing required to nullable
    - Adding indexes/constraints (not yet detected)
    
    Args:
        changes: Output from detect_schema_changes()
    
    Returns:
        bool: True if changes are breaking
    """
    # Dropped columns are always breaking
    if changes['dropped']:
        return True
    
    # Modified columns are usually breaking
    if changes['modified']:
        for mod in changes['modified']:
            # Type changes are breaking
            if mod.get('change') == 'type':
                return True
            # Making column required is breaking
            if mod.get('change') == 'required' and mod.get('new_required'):
                return True
    
    # Adding required columns without defaults is breaking
    for added in changes['added']:
        if not added['nullable'] and added['default'] is None:
            return True
    
    return False


def suggest_version_bump(current_version: str, is_breaking: bool) -> str:
    """
    Suggest next version based on semantic versioning.
    
    Rules:
    - Breaking changes: Bump minor (x.Y.z)
    - Non-breaking changes: Bump patch (x.y.Z)
    - User can override with --version flag
    
    Args:
        current_version: Current version (e.g., 'v1.3.0')
        is_breaking: Whether changes are breaking
    
    Returns:
        str: Suggested version (e.g., 'v1.4.0' or 'v1.3.1')
    
    Example:
        >>> suggest_version_bump('v1.3.0', is_breaking=False)
        'v1.3.1'
        >>> suggest_version_bump('v1.3.0', is_breaking=True)
        'v1.4.0'
    """
    # Handle 'none' or missing version
    if not current_version or current_version == 'none':
        return 'v1.0.0'
    
    # Parse version (handle 'v1.2.3' format)
    version_str = current_version.lstrip('v')
    try:
        parts = version_str.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        # Malformed version, default to v1.0.0
        return 'v1.0.0'
    
    # Bump version
    if is_breaking:
        # Bump minor, reset patch
        minor += 1
        patch = 0
    else:
        # Bump patch
        patch += 1
    
    return f"v{major}.{minor}.{patch}"


def format_changes_summary(changes: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Format changes into human-readable summary.
    
    Args:
        changes: Output from detect_schema_changes()
    
    Returns:
        str: Formatted summary (e.g., "added:cover_url,avatar_updated_at | dropped:old_field")
    """
    summary_parts = []
    
    if changes['added']:
        added_names = [c['name'] for c in changes['added']]
        summary_parts.append(f"added:{','.join(added_names)}")
    
    if changes['dropped']:
        dropped_names = [c['name'] for c in changes['dropped']]
        summary_parts.append(f"dropped:{','.join(dropped_names)}")
    
    if changes['modified']:
        modified_names = [c['name'] for c in changes['modified']]
        summary_parts.append(f"modified:{','.join(modified_names)}")
    
    return " | ".join(summary_parts) if summary_parts else "no changes"


def load_schema_from_file(schema_path: Path) -> Dict[str, Any]:
    """
    Load schema from YAML file.
    
    Args:
        schema_path: Path to schema YAML file
    
    Returns:
        Dict: Parsed schema
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

