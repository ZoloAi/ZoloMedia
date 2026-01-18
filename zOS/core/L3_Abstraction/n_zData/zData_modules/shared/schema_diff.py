# zCLI/subsystems/zData/zData_modules/shared/schema_diff.py
"""
Schema diff engine for declarative migrations in zData.

This module provides the core diff algorithm that compares two zData schema
definitions (old vs new) and returns a structured diff describing all changes.
The diff is used by the migration executor to generate and apply DDL operations.

Core Principle
--------------
In zCLI's declarative migration system, the YAML schema is the source of truth.
Instead of writing imperative migration scripts, we compute the diff between:
- **Old Schema**: Current database state (or previous YAML)
- **New Schema**: Target YAML schema

The diff engine detects:
- Tables added, dropped, or modified
- Columns added, dropped, or modified (type changes, constraints)
- Constraints added or dropped (PRIMARY KEY, UNIQUE, FOREIGN KEY)
- Hooks added or dropped (onBeforeInsert, onAfterInsert, etc.)

Architecture
-----------
The diff engine is a pure Python algorithm with no database dependencies.
It performs deep comparison of nested dictionaries to detect all changes.

**Key Functions:**
- diff_schemas(): Main entry point - returns complete diff
- detect_table_changes(): Detect table additions/drops
- detect_column_changes(): Detect column modifications within tables
- detect_constraint_changes(): Detect constraint modifications
- detect_hook_changes(): Detect hook modifications
- format_diff_report(): Generate human-readable summary for display

Diff Structure
-------------
The diff is returned as a structured dictionary:

{
    'tables_added': ['posts', 'comments'],
    'tables_dropped': ['temp_table'],
    'tables_modified': {
        'users': {
            'columns_added': {
                'age': {'type': 'integer', 'min': 0, 'max': 150},
                'email': {'type': 'string', 'format': 'email'}
            },
            'columns_dropped': ['old_field'],
            'columns_modified': {
                'status': {
                    'old': {'type': 'string'},
                    'new': {'type': 'string', 'required': True}
                }
            },
            'constraints_added': ['UNIQUE(email)'],
            'constraints_dropped': [],
            'hooks_added': {'onBeforeInsert': '&MyPlugin.validate'},
            'hooks_dropped': []
        }
    },
    'has_destructive_changes': True,  # True if any drops or type changes
    'change_count': {
        'tables_added': 2,
        'tables_dropped': 1,
        'columns_added': 2,
        'columns_dropped': 1,
        'columns_modified': 1
    }
}

Usage Examples
-------------
Basic schema diff:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.schema_diff import diff_schemas
    >>> old_schema = {'Tables': {'users': {'Columns': {'id': {'type': 'integer'}}}}}
    >>> new_schema = {'Tables': {'users': {'Columns': {'id': {'type': 'integer'}, 'name': {'type': 'string'}}}}}
    >>> diff = diff_schemas(old_schema, new_schema)
    >>> print(diff['tables_modified']['users']['columns_added'])
    {'name': {'type': 'string'}}

Detect destructive changes:
    >>> diff = diff_schemas(old_schema, new_schema)
    >>> if diff['has_destructive_changes']:
    ...     print("⚠️ This migration will drop data!")

Generate human-readable report:
    >>> report = format_diff_report(diff)
    >>> print(report)
    Migration Summary:
      + 2 tables added (posts, comments)
      - 1 table dropped (temp_table)
      ~ 1 table modified (users)
        + 2 columns added to users
        - 1 column dropped from users

Integration
----------
- **Used By**: ddl_migrate.py (migration executor)
- **Depends On**: None (pure Python, no zCLI dependencies)
- **Output To**: zDisplay (formatted reports)

See Also
--------
- ddl_migrate.py: Migration executor that applies diffs
- migration_history.py: Tracks applied migrations
- validator.py: Schema validation before diffing
"""

from zOS import Dict, List, Any

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Schema Keys
KEY_TABLES = "Tables"
KEY_COLUMNS = "Columns"
KEY_CONSTRAINTS = "Constraints"
KEY_HOOKS = "Hooks"
KEY_META = "Meta"

# Diff Result Keys
KEY_TABLES_ADDED = "tables_added"
KEY_TABLES_DROPPED = "tables_dropped"
KEY_TABLES_MODIFIED = "tables_modified"
KEY_COLUMNS_ADDED = "columns_added"
KEY_COLUMNS_DROPPED = "columns_dropped"
KEY_COLUMNS_MODIFIED = "columns_modified"
KEY_CONSTRAINTS_ADDED = "constraints_added"
KEY_CONSTRAINTS_DROPPED = "constraints_dropped"
KEY_HOOKS_ADDED = "hooks_added"
KEY_HOOKS_DROPPED = "hooks_dropped"
KEY_HAS_DESTRUCTIVE = "has_destructive_changes"
KEY_CHANGE_COUNT = "change_count"

# Column Properties
PROP_TYPE = "type"
PROP_REQUIRED = "required"
PROP_DEFAULT = "default"
PROP_PRIMARY_KEY = "primary_key"
PROP_AUTO_INCREMENT = "auto_increment"
PROP_UNIQUE = "unique"
PROP_FOREIGN_KEY = "foreign_key"

# Change Categories
CATEGORY_SAFE = "safe"
CATEGORY_DESTRUCTIVE = "destructive"
CATEGORY_TYPE_CHANGE = "type_change"

# Report Formatting
SYMBOL_ADDED = "+"
SYMBOL_DROPPED = "-"
SYMBOL_MODIFIED = "~"
INDENT_LEVEL_1 = "  "
INDENT_LEVEL_2 = "    "

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DIFF FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def diff_schemas(old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two schema dictionaries and return a structured diff.
    
    This is the main entry point for schema diffing. It performs a deep comparison
    of two schema dictionaries (old vs new) and returns all detected changes in a
    structured format suitable for migration execution.
    
    Args:
        old_schema: Current/old schema dict (from database or previous YAML)
        new_schema: Target/new schema dict (from YAML file)
    
    Returns:
        Structured diff dictionary with keys:
        - tables_added: List of new table names
        - tables_dropped: List of removed table names
        - tables_modified: Dict of {table_name: table_changes}
        - has_destructive_changes: True if any drops or type changes
        - change_count: Summary counts of all changes
    
    Examples:
        >>> old = {'Tables': {'users': {'Columns': {'id': {'type': 'integer'}}}}}
        >>> new = {'Tables': {'users': {'Columns': {'id': {'type': 'integer'}, 'name': {'type': 'string'}}}}}
        >>> diff = diff_schemas(old, new)
        >>> diff['tables_modified']['users']['columns_added']
        {'name': {'type': 'string'}}
    
    Notes:
        - Empty schemas are treated as having no tables
        - Tables section is optional (defaults to empty dict)
        - Deep comparison handles nested dicts (Columns, Constraints, Hooks)
        - Destructive flag set if any tables/columns dropped or types changed
    """
    # Extract Tables section (default to empty if missing)
    old_tables = old_schema.get(KEY_TABLES, {})
    new_tables = new_schema.get(KEY_TABLES, {})
    
    # Detect table-level changes
    tables_added, tables_dropped = detect_table_changes(old_tables, new_tables)
    
    # Detect modifications within existing tables
    tables_modified = {}
    common_tables = set(old_tables.keys()) & set(new_tables.keys())
    
    for table_name in common_tables:
        old_table = old_tables[table_name]
        new_table = new_tables[table_name]
        
        table_changes = detect_table_modifications(old_table, new_table)
        
        # Only include if there are actual changes
        if any(table_changes.values()):
            tables_modified[table_name] = table_changes
    
    # Determine if there are destructive changes
    has_destructive = _has_destructive_changes(tables_dropped, tables_modified)
    
    # Count all changes
    change_count = _count_changes(tables_added, tables_dropped, tables_modified)
    
    return {
        KEY_TABLES_ADDED: tables_added,
        KEY_TABLES_DROPPED: tables_dropped,
        KEY_TABLES_MODIFIED: tables_modified,
        KEY_HAS_DESTRUCTIVE: has_destructive,
        KEY_CHANGE_COUNT: change_count
    }

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE-LEVEL DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_table_changes(old_tables: Dict[str, Any], new_tables: Dict[str, Any]) -> tuple:
    """
    Detect tables that were added or dropped.
    
    Compares the set of table names in old vs new schemas to determine which
    tables were added (exist in new but not old) or dropped (exist in old but not new).
    
    Args:
        old_tables: Dict of tables from old schema {table_name: table_def}
        new_tables: Dict of tables from new schema {table_name: table_def}
    
    Returns:
        Tuple of (tables_added, tables_dropped)
        - tables_added: List of table names that exist in new but not old
        - tables_dropped: List of table names that exist in old but not new
    
    Examples:
        >>> old = {'users': {}, 'temp': {}}
        >>> new = {'users': {}, 'posts': {}}
        >>> added, dropped = detect_table_changes(old, new)
        >>> added
        ['posts']
        >>> dropped
        ['temp']
    
    Notes:
        - Returns empty lists if no changes
        - Table names are case-sensitive
        - Order of tables in lists is alphabetical for consistency
    """
    old_set = set(old_tables.keys())
    new_set = set(new_tables.keys())
    
    tables_added = sorted(list(new_set - old_set))
    tables_dropped = sorted(list(old_set - new_set))
    
    return tables_added, tables_dropped

def detect_table_modifications(old_table: Dict[str, Any], 
                               new_table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect all modifications within a single table.
    
    Compares old and new definitions of the same table to detect changes in:
    - Columns (added, dropped, modified)
    - Constraints (added, dropped)
    - Hooks (added, dropped)
    
    Args:
        old_table: Old table definition dict
        new_table: New table definition dict
    
    Returns:
        Dict with keys:
        - columns_added: Dict of {column_name: column_def}
        - columns_dropped: List of column names
        - columns_modified: Dict of {column_name: {'old': old_def, 'new': new_def}}
        - constraints_added: List of constraint definitions
        - constraints_dropped: List of constraint definitions
        - hooks_added: Dict of {hook_name: hook_value}
        - hooks_dropped: List of hook names
    
    Examples:
        >>> old = {'Columns': {'id': {'type': 'integer'}}}
        >>> new = {'Columns': {'id': {'type': 'integer'}, 'name': {'type': 'string'}}}
        >>> changes = detect_table_modifications(old, new)
        >>> changes['columns_added']
        {'name': {'type': 'string'}}
    
    Notes:
        - Empty sections (Columns, Constraints, Hooks) default to empty dicts
        - All change categories returned even if empty (for consistency)
    """
    # Extract sections (default to empty if missing)
    old_columns = old_table.get(KEY_COLUMNS, {})
    new_columns = new_table.get(KEY_COLUMNS, {})
    old_constraints = old_table.get(KEY_CONSTRAINTS, {})
    new_constraints = new_table.get(KEY_CONSTRAINTS, {})
    old_hooks = old_table.get(KEY_HOOKS, {})
    new_hooks = new_table.get(KEY_HOOKS, {})
    
    # Detect column changes
    columns_added, columns_dropped, columns_modified = detect_column_changes(
        old_columns, new_columns
    )
    
    # Detect constraint changes
    constraints_added, constraints_dropped = detect_constraint_changes(
        old_constraints, new_constraints
    )
    
    # Detect hook changes
    hooks_added, hooks_dropped = detect_hook_changes(old_hooks, new_hooks)
    
    return {
        KEY_COLUMNS_ADDED: columns_added,
        KEY_COLUMNS_DROPPED: columns_dropped,
        KEY_COLUMNS_MODIFIED: columns_modified,
        KEY_CONSTRAINTS_ADDED: constraints_added,
        KEY_CONSTRAINTS_DROPPED: constraints_dropped,
        KEY_HOOKS_ADDED: hooks_added,
        KEY_HOOKS_DROPPED: hooks_dropped
    }

# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN-LEVEL DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_column_changes(old_columns: Dict[str, Any], 
                         new_columns: Dict[str, Any]) -> tuple:
    """
    Detect columns that were added, dropped, or modified.
    
    Compares column definitions to find:
    - Columns added (exist in new but not old)
    - Columns dropped (exist in old but not new)
    - Columns modified (exist in both but have different definitions)
    
    Modification detection includes:
    - Type changes (e.g., string → integer)
    - Constraint changes (required, unique, primary_key)
    - Default value changes
    - Validation rule changes (min, max, pattern, format)
    
    Args:
        old_columns: Dict of columns from old table {column_name: column_def}
        new_columns: Dict of columns from new table {column_name: column_def}
    
    Returns:
        Tuple of (columns_added, columns_dropped, columns_modified)
        - columns_added: Dict of {column_name: column_def} for new columns
        - columns_dropped: List of column names that were removed
        - columns_modified: Dict of {column_name: {'old': old_def, 'new': new_def}}
    
    Examples:
        >>> old = {'id': {'type': 'integer'}, 'status': {'type': 'string'}}
        >>> new = {'id': {'type': 'integer'}, 'status': {'type': 'string', 'required': True}, 'email': {'type': 'string'}}
        >>> added, dropped, modified = detect_column_changes(old, new)
        >>> added
        {'email': {'type': 'string'}}
        >>> modified
        {'status': {'old': {'type': 'string'}, 'new': {'type': 'string', 'required': True}}}
    
    Notes:
        - Deep comparison of column definitions (not just shallow)
        - Type changes are always considered modifications
        - Adding/removing constraints is a modification, not a drop
    """
    old_set = set(old_columns.keys())
    new_set = set(new_columns.keys())
    
    # Detect additions and drops
    columns_added = {col: new_columns[col] for col in sorted(new_set - old_set)}
    columns_dropped = sorted(list(old_set - new_set))
    
    # Detect modifications in common columns
    columns_modified = {}
    common_columns = old_set & new_set
    
    for col_name in sorted(common_columns):
        old_def = old_columns[col_name]
        new_def = new_columns[col_name]
        
        # Deep comparison of column definitions
        if old_def != new_def:
            columns_modified[col_name] = {
                "old": old_def,
                "new": new_def
            }
    
    return columns_added, columns_dropped, columns_modified

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRAINT & HOOK DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_constraint_changes(old_constraints: Dict[str, Any], 
                              new_constraints: Dict[str, Any]) -> tuple:
    """
    Detect constraints that were added or dropped.
    
    Compares constraint definitions between old and new tables. Constraints include:
    - PRIMARY KEY
    - UNIQUE
    - FOREIGN KEY
    - CHECK constraints
    
    Args:
        old_constraints: Dict of constraints from old table
        new_constraints: Dict of constraints from new table
    
    Returns:
        Tuple of (constraints_added, constraints_dropped)
        - constraints_added: List of constraint definitions that were added
        - constraints_dropped: List of constraint definitions that were removed
    
    Examples:
        >>> old = {}
        >>> new = {'unique_email': {'type': 'UNIQUE', 'columns': ['email']}}
        >>> added, dropped = detect_constraint_changes(old, new)
        >>> added
        [{'type': 'UNIQUE', 'columns': ['email']}]
    
    Notes:
        - Constraints are compared by name (key in dict)
        - Constraint modifications not currently supported (drop + add instead)
        - Returns list of constraint defs, not just names
    """
    old_set = set(old_constraints.keys())
    new_set = set(new_constraints.keys())
    
    constraints_added = [new_constraints[c] for c in sorted(new_set - old_set)]
    constraints_dropped = [old_constraints[c] for c in sorted(old_set - new_set)]
    
    return constraints_added, constraints_dropped

def detect_hook_changes(old_hooks: Dict[str, Any], new_hooks: Dict[str, Any]) -> tuple:
    """
    Detect hooks that were added or dropped.
    
    Compares hook definitions between old and new tables. Hooks include:
    - onBeforeInsert
    - onAfterInsert
    - onBeforeUpdate
    - onAfterUpdate
    
    Args:
        old_hooks: Dict of hooks from old table {hook_name: hook_value}
        new_hooks: Dict of hooks from new table {hook_name: hook_value}
    
    Returns:
        Tuple of (hooks_added, hooks_dropped)
        - hooks_added: Dict of {hook_name: hook_value} for new hooks
        - hooks_dropped: List of hook names that were removed
    
    Examples:
        >>> old = {}
        >>> new = {'onBeforeInsert': '&MyPlugin.validate_user'}
        >>> added, dropped = detect_hook_changes(old, new)
        >>> added
        {'onBeforeInsert': '&MyPlugin.validate_user'}
    
    Notes:
        - Hook value changes are treated as drop + add
        - Hook values are typically zFunc references (&PluginName.function)
    """
    old_set = set(old_hooks.keys())
    new_set = set(new_hooks.keys())
    
    hooks_added = {hook: new_hooks[hook] for hook in sorted(new_set - old_set)}
    hooks_dropped = sorted(list(old_set - new_set))
    
    # Also detect modified hooks (value changed)
    common_hooks = old_set & new_set
    for hook in common_hooks:
        if old_hooks[hook] != new_hooks[hook]:
            # Treat as drop + add
            hooks_dropped.append(hook)
            hooks_added[hook] = new_hooks[hook]
    
    return hooks_added, hooks_dropped

# ═══════════════════════════════════════════════════════════════════════════════
# DIFF ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _has_destructive_changes(tables_dropped: List[str], 
                            tables_modified: Dict[str, Any]) -> bool:
    """
    Determine if diff contains destructive changes.
    
    Destructive changes include:
    - Dropping tables (data loss)
    - Dropping columns (data loss)
    - Type changes that may lose data (e.g., integer → string is safe, string → integer is not)
    
    Args:
        tables_dropped: List of dropped table names
        tables_modified: Dict of table modifications
    
    Returns:
        True if any destructive changes detected, False otherwise
    
    Notes:
        - Used to trigger safety warnings and confirmation prompts
        - Type changes are always considered potentially destructive
    """
    # Any dropped tables = destructive
    if tables_dropped:
        return True
    
    # Check for dropped columns in modified tables
    for table_changes in tables_modified.values():
        if table_changes.get(KEY_COLUMNS_DROPPED):
            return True
        
        # Check for type changes (potentially destructive)
        columns_modified = table_changes.get(KEY_COLUMNS_MODIFIED, {})
        for col_changes in columns_modified.values():
            old_type = col_changes.get("old", {}).get(PROP_TYPE)
            new_type = col_changes.get("new", {}).get(PROP_TYPE)
            if old_type != new_type:
                return True
    
    return False

def _count_changes(tables_added: List[str], tables_dropped: List[str], 
                  tables_modified: Dict[str, Any]) -> Dict[str, int]:
    """
    Count all changes for summary statistics.
    
    Args:
        tables_added: List of added table names
        tables_dropped: List of dropped table names
        tables_modified: Dict of table modifications
    
    Returns:
        Dict with counts: {
            'tables_added': int,
            'tables_dropped': int,
            'tables_modified': int,
            'columns_added': int,
            'columns_dropped': int,
            'columns_modified': int
        }
    
    Notes:
        - Used for migration summary display
        - Aggregates counts across all modified tables
    """
    counts = {
        KEY_TABLES_ADDED: len(tables_added),
        KEY_TABLES_DROPPED: len(tables_dropped),
        KEY_TABLES_MODIFIED: len(tables_modified),
        KEY_COLUMNS_ADDED: 0,
        KEY_COLUMNS_DROPPED: 0,
        KEY_COLUMNS_MODIFIED: 0
    }
    
    for table_changes in tables_modified.values():
        counts[KEY_COLUMNS_ADDED] += len(table_changes.get(KEY_COLUMNS_ADDED, {}))
        counts[KEY_COLUMNS_DROPPED] += len(table_changes.get(KEY_COLUMNS_DROPPED, []))
        counts[KEY_COLUMNS_MODIFIED] += len(table_changes.get(KEY_COLUMNS_MODIFIED, {}))
    
    return counts

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════

def format_diff_report(diff: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of schema diff.
    
    Converts the structured diff into a formatted text report suitable for
    displaying to users via zDisplay. The report uses symbols to indicate
    additions (+), drops (-), and modifications (~).
    
    Args:
        diff: Structured diff from diff_schemas()
    
    Returns:
        Multi-line string report with formatted summary
    
    Examples:
        >>> diff = diff_schemas(old_schema, new_schema)
        >>> report = format_diff_report(diff)
        >>> print(report)
        Migration Summary:
          + 2 tables added (posts, comments)
          - 1 table dropped (temp_table)
          ~ 1 table modified (users)
            + 2 columns added to users
            - 1 column dropped from users
    
    Notes:
        - Empty sections are omitted from report
        - Destructive changes are highlighted with ⚠️ symbol
        - Used by ddl_migrate.py for preview display
    """
    lines = ["Migration Summary:"]
    
    # Table-level changes
    if diff[KEY_TABLES_ADDED]:
        tables = ", ".join(diff[KEY_TABLES_ADDED])
        lines.append(f"{INDENT_LEVEL_1}{SYMBOL_ADDED} {len(diff[KEY_TABLES_ADDED])} table(s) added ({tables})")
    
    if diff[KEY_TABLES_DROPPED]:
        tables = ", ".join(diff[KEY_TABLES_DROPPED])
        lines.append(f"{INDENT_LEVEL_1}{SYMBOL_DROPPED} {len(diff[KEY_TABLES_DROPPED])} table(s) dropped ({tables})")
    
    # Modified tables
    if diff[KEY_TABLES_MODIFIED]:
        lines.append(f"{INDENT_LEVEL_1}{SYMBOL_MODIFIED} {len(diff[KEY_TABLES_MODIFIED])} table(s) modified")
        
        for table_name, changes in diff[KEY_TABLES_MODIFIED].items():
            lines.append(f"{INDENT_LEVEL_2}Table: {table_name}")
            
            if changes[KEY_COLUMNS_ADDED]:
                lines.append(f"{INDENT_LEVEL_2}{INDENT_LEVEL_1}{SYMBOL_ADDED} {len(changes[KEY_COLUMNS_ADDED])} column(s) added")
            
            if changes[KEY_COLUMNS_DROPPED]:
                cols = ", ".join(changes[KEY_COLUMNS_DROPPED])
                lines.append(f"{INDENT_LEVEL_2}{INDENT_LEVEL_1}{SYMBOL_DROPPED} {len(changes[KEY_COLUMNS_DROPPED])} column(s) dropped ({cols})")
            
            if changes[KEY_COLUMNS_MODIFIED]:
                lines.append(f"{INDENT_LEVEL_2}{INDENT_LEVEL_1}{SYMBOL_MODIFIED} {len(changes[KEY_COLUMNS_MODIFIED])} column(s) modified")
    
    # Destructive warning
    if diff[KEY_HAS_DESTRUCTIVE]:
        lines.append("")
        lines.append(f"{INDENT_LEVEL_1}⚠️  WARNING: This migration contains DESTRUCTIVE changes!")
        lines.append(f"{INDENT_LEVEL_1}   Data may be lost. Review carefully before applying.")
    
    # Change summary
    counts = diff[KEY_CHANGE_COUNT]
    total_changes = sum(counts.values())
    lines.append("")
    lines.append(f"{INDENT_LEVEL_1}Total changes: {total_changes}")
    
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "diff_schemas",
    "detect_table_changes",
    "detect_column_changes",
    "detect_constraint_changes",
    "detect_hook_changes",
    "format_diff_report"
]

