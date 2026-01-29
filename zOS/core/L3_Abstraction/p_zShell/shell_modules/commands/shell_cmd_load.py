# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_load.py
"""
Load command execution for zCLI shell.

This module provides the `load` shell command for managing zLoader cache operations.
It enables loading, displaying, and clearing cached resources in the zCLI framework.

═══════════════════════════════════════════════════════════════════════════════
THREE-TIER CACHE SYSTEM
═══════════════════════════════════════════════════════════════════════════════

zLoader implements a three-tier caching architecture for optimal performance:

**Tier 1: Pinned Cache (User-Loaded Resources)**
  - Resources explicitly loaded via `load <zPath>` command
  - Persistent for the session lifetime
  - Not subject to eviction
  - Accessible by name for quick reference
  - Stored in: zcli.loader.cache.pinned_cache

**Tier 2: System Cache (Auto-Cached Files)**
  - Automatically caches frequently accessed files
  - LRU eviction policy (Least Recently Used)
  - mtime invalidation (detects file changes)
  - Limited size (configurable max entries)
  - Stored in: zcli.loader.cache.system_cache

**Tier 3: Disk I/O (Fallback)**
  - Direct filesystem reads when not cached
  - No eviction - always available
  - Slowest but most reliable
  - Used when cache misses occur

═══════════════════════════════════════════════════════════════════════════════
COMMAND SYNTAX
═══════════════════════════════════════════════════════════════════════════════

**Load Resource:**
    load <zPath>                    # Load and pin resource to Tier 1 cache

**Show Cache:**
    load show                       # Show all three cache tiers
    load show pinned                # Show Tier 1 only (user-loaded)
    load show cached                # Show Tier 2 stats (system cache)
    load show schemas               # Filter by schema resources
    load show ui                    # Filter by UI resources
    load show config                # Filter by config resources

**Clear Cache:**
    load clear                      # Clear all pinned resources (Tier 1)
    load clear [pattern]            # Clear resources matching pattern

═══════════════════════════════════════════════════════════════════════════════
RESOURCE TYPES
═══════════════════════════════════════════════════════════════════════════════

Resources are auto-detected based on zPath notation:

  - **schema**: Contains "zSchema." in path
  - **ui**: Contains "zUI." in path
  - **config**: Contains "zConfig." in path
  - **other**: All other resources

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION POINTS
═══════════════════════════════════════════════════════════════════════════════

**zLoader Subsystem:**
  - zcli.loader.handle(zPath) - Load resources into cache
  - zcli.loader.cache.pinned_cache - Tier 1 cache access
  - zcli.loader.cache.system_cache - Tier 2 cache stats

**zParser Subsystem:**
  - zcli.zparser.zPath_decoder() - Decode zPath to filesystem path
  - zcli.zparser.identify_zFile() - Identify resource file type

**zDisplay Subsystem:**
  - zcli.display.header() - Section headers
  - zcli.display.zDeclare() - Tier section titles
  - zcli.display.text() - Plain text output
  - zcli.display.info() - Informational messages
  - zcli.display.success() - Success confirmations
  - zcli.display.error() - Error messages
  - zcli.display.warning() - Warning messages

**zLogger:**
  - zcli.logger.info() - Success operations
  - zcli.logger.error() - Error conditions
  - zcli.logger.debug() - Debug information

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

    # Load a schema to cache
    load @.zCLI.Schemas.zSchema.sqlite_demo
    # Output: [OK] Loaded schema: @.zCLI.Schemas.zSchema.sqlite_demo (3 tables)

    # Show all cache tiers
    load show
    # Output: Tier 1, Tier 2, and Tier 3 statistics

    # Show only pinned resources
    load show pinned
    # Output: User-loaded resources with age and metadata

    # Filter by resource type
    load show schemas
    # Output: Only schema resources

    # Clear all pinned resources
    load clear
    # Output: [OK] Cleared 3 loaded resources

    # Clear resources matching pattern
    load clear sqlite
    # Output: [OK] Cleared 1 loaded resources matching 'sqlite'

═══════════════════════════════════════════════════════════════════════════════
NOTES
═══════════════════════════════════════════════════════════════════════════════

- Pinned resources persist for the session lifetime
- System cache uses LRU eviction when full
- File changes invalidate system cache entries (mtime check)
- Resource type detection is case-sensitive
- Clear operations only affect Tier 1 (pinned cache)
- Show operations are read-only and do not modify cache state

═══════════════════════════════════════════════════════════════════════════════
AUTHOR & VERSION
═══════════════════════════════════════════════════════════════════════════════

Author: zCLI Development Team
Version: 1.5.4
Last Updated: 2025-11-06
"""

from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Command Actions
ACTION_LOAD: str = "load"
ACTION_SHOW: str = "show"
ACTION_CLEAR: str = "clear"

# Show Subcommands
SHOW_ALL: Optional[str] = None  # Default: show all tiers
SHOW_PINNED: str = "pinned"
SHOW_CACHED: str = "cached"
SHOW_SCHEMAS: str = "schemas"
SHOW_UI: str = "ui"
SHOW_CONFIG: str = "config"

# Resource Types
RESOURCE_TYPE_SCHEMA: str = "schema"
RESOURCE_TYPE_UI: str = "ui"
RESOURCE_TYPE_CONFIG: str = "config"
RESOURCE_TYPE_OTHER: str = "other"
RESOURCE_TYPE_UNKNOWN: str = "unknown"

# Resource Type Detection Patterns
PATTERN_SCHEMA: str = "zSchema."
PATTERN_UI: str = "zUI."
PATTERN_CONFIG: str = "zConfig."

# Item Type Names
ITEM_TYPE_TABLES: str = "tables"
ITEM_TYPE_BLOCKS: str = "blocks"

# Cache Meta Keys
META_KEY: str = "zMeta"

# Error Messages
ERROR_NO_ARGS: str = "Usage: load <zPath> | load show | load clear [pattern]"
ERROR_LOAD_FAILED: str = "Failed to load: {zpath}"
ERROR_UNKNOWN_SHOW_OPTION: str = "Unknown show option: {option}"
ERROR_NO_LOADER: str = "zLoader subsystem not available"
ERROR_NO_PARSER: str = "zParser subsystem not available"
ERROR_INVALID_RESULT: str = "Load operation returned invalid result"

# Success Messages
MSG_LOADED: str = "[OK] Loaded {type}: {path} ({count} {item_type})"
MSG_CLEARED: str = "[OK] Cleared all {count} loaded resources"
MSG_CLEARED_PATTERN: str = "[OK] Cleared {count} loaded resources matching '{pattern}'"

# Info Messages
MSG_EMPTY_CACHE: str = "No pinned resources."
MSG_EMPTY_CACHE_HELP: str = "Use 'load <zPath>' to pin resources to cache."
MSG_EMPTY_FILTERED: str = "No {type} resources loaded."
MSG_EMPTY_FILTERED_HELP: str = "Use 'load @.{type}s.{type}' to load {type} resources."

# Display Headers
HEADER_CACHE_SYSTEM: str = "Cache System - Three Tiers"
HEADER_TIER1: str = "Tier 1: Pinned Cache (User-Loaded)"
HEADER_TIER2: str = "Tier 2: System Cache (Auto-Cached Files)"
HEADER_TIER3: str = "Tier 3: Disk I/O (Fallback)"
HEADER_RESOURCES: str = "Resources: {type}"
HEADER_PINNED: str = "Tier 1: Pinned Cache (User-Loaded)"
HEADER_CACHED: str = "Tier 2: System Cache (Auto-Cached Files)"

# Display Formatting
DISPLAY_SEPARATOR: str = "=" * 70
DISPLAY_INDENT: str = "  "
DISPLAY_BULLET: str = "•"
DISPLAY_ARROW: str = "=>"

# Display Colors
COLOR_HEADER: str = "CYAN"
COLOR_SECTION: str = "BLUE"
COLOR_SUCCESS: str = "GREEN"
COLOR_WARNING: str = "YELLOW"
COLOR_INFO: str = "BLUE"
COLOR_ERROR: str = "RED"

# Display Styles
STYLE_FULL: str = "full"

# Display Indentation Levels
INDENT_ZERO: int = 0
INDENT_ONE: int = 1
INDENT_TWO: int = 2

# Dict Keys
KEY_STATUS: str = "status"
KEY_ERROR: str = "error"
KEY_TYPE: str = "type"
KEY_PATH: str = "path"
KEY_COUNT: str = "count"
KEY_ITEMS: str = "items"
KEY_ARGS: str = "args"
KEY_OPTIONS: str = "options"
KEY_NAME: str = "name"
KEY_ZPATH: str = "zpath"
KEY_AGE: str = "age"
KEY_SIZE: str = "size"
KEY_MAX_SIZE: str = "max_size"
KEY_HIT_RATE: str = "hit_rate"
KEY_HITS: str = "hits"
KEY_MISSES: str = "misses"
KEY_EVICTIONS: str = "evictions"
KEY_INVALIDATIONS: str = "invalidations"
KEY_NAMESPACE: str = "namespace"

# Status Values
STATUS_SUCCESS: str = "success"
STATUS_EMPTY: str = "empty"
STATUS_ERROR: str = "error"

# Time Conversion
SECONDS_PER_MINUTE: int = 60
SECONDS_PER_HOUR: int = 3600
SECONDS_PER_DAY: int = 86400

# Time Unit Names
UNIT_SECOND: str = "second"
UNIT_MINUTE: str = "minute"
UNIT_HOUR: str = "hour"
UNIT_DAY: str = "day"
UNIT_SECONDS: str = "seconds"
UNIT_MINUTES: str = "minutes"
UNIT_HOURS: str = "hours"
UNIT_DAYS: str = "days"

# Logging Messages
LOG_LOAD_SUCCESS: str = "[OK] Loaded %s: %s (%d %s)"
LOG_LOAD_FAILED: str = "Failed to load %s: %s"
LOG_SHOW_CACHE: str = "Displaying cache system (all tiers)"
LOG_SHOW_PINNED: str = "Displaying pinned cache (Tier 1)"
LOG_SHOW_CACHED: str = "Displaying system cache stats (Tier 2)"
LOG_SHOW_FILTERED: str = "Displaying %s resources"
LOG_CLEAR_ALL: str = "Cleared %d pinned resources"
LOG_CLEAR_PATTERN: str = "Cleared %d resources matching '%s'"

# Default Values
DEFAULT_AGE: int = 0
DEFAULT_COUNT: int = 0
DEFAULT_PATTERN: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_loader_subsystem(zcli: Any) -> Optional[Dict[str, str]]:
    """
    Validate that the zLoader subsystem is available.
    
    Args:
        zcli: The zCLI application instance
        
    Returns:
        Error dict if loader is unavailable, None if valid
        
    Example:
        >>> error = _validate_loader_subsystem(zcli)
        >>> if error:
        >>>     return error
    """
    if not hasattr(zcli, "loader") or zcli.loader is None:
        zcli.display.error(ERROR_NO_LOADER)
        zcli.logger.error(ERROR_NO_LOADER)
        return {KEY_ERROR: ERROR_NO_LOADER}
    return None


def _validate_parser_subsystem(zcli: Any) -> Optional[Dict[str, str]]:
    """
    Validate that the zParser subsystem is available.
    
    Args:
        zcli: The zCLI application instance
        
    Returns:
        Error dict if parser is unavailable, None if valid
        
    Example:
        >>> error = _validate_parser_subsystem(zcli)
        >>> if error:
        >>>     return error
    """
    if not hasattr(zcli, "zparser") or zcli.zparser is None:
        zcli.display.error(ERROR_NO_PARSER)
        zcli.logger.error(ERROR_NO_PARSER)
        return {KEY_ERROR: ERROR_NO_PARSER}
    return None


def _detect_resource_type(zpath: str) -> str:
    """
    Detect resource type based on zPath pattern.
    
    Args:
        zpath: The zPath string to analyze
        
    Returns:
        Resource type string (schema, ui, config, other)
        
    Example:
        >>> _detect_resource_type("@.zCLI.Schemas.zSchema.sqlite_demo")
        'schema'
        >>> _detect_resource_type("@.zCLI.UI.zUI.zcli_sys")
        'ui'
    """
    if PATTERN_SCHEMA in zpath:
        return RESOURCE_TYPE_SCHEMA
    elif PATTERN_UI in zpath:
        return RESOURCE_TYPE_UI
    elif PATTERN_CONFIG in zpath:
        return RESOURCE_TYPE_CONFIG
    else:
        return RESOURCE_TYPE_OTHER


def _count_resource_items(
    result: Dict[str, Any],
    resource_type: str
) -> Tuple[List[str], str]:
    """
    Count items in loaded resource and determine item type.
    
    Args:
        result: The loaded resource dictionary
        resource_type: The detected resource type
        
    Returns:
        Tuple of (items_list, item_type_name)
        
    Example:
        >>> result = {"users": {...}, "posts": {...}, "zMeta": {...}}
        >>> items, item_type = _count_resource_items(result, "schema")
        >>> # items = ["users", "posts"], item_type = "tables"
    """
    if resource_type == RESOURCE_TYPE_SCHEMA:
        # Exclude Meta key for schemas
        items = [k for k in result.keys() if k != META_KEY]
        item_type = ITEM_TYPE_TABLES
    else:
        # Include all keys for other resource types
        items = list(result.keys())
        item_type = ITEM_TYPE_BLOCKS
    
    return items, item_type


def _format_cache_age(age_seconds: int) -> str:
    """
    Convert age in seconds to human-readable format.
    
    Args:
        age_seconds: Age in seconds
        
    Returns:
        Formatted age string (e.g., "5 minutes", "2 hours", "3 days")
        
    Example:
        >>> _format_cache_age(300)
        '5 minutes'
        >>> _format_cache_age(7200)
        '2 hours'
        >>> _format_cache_age(86400)
        '1 day'
    """
    if age_seconds < SECONDS_PER_MINUTE:
        value = age_seconds
        unit = UNIT_SECOND if value == 1 else UNIT_SECONDS
    elif age_seconds < SECONDS_PER_HOUR:
        value = age_seconds // SECONDS_PER_MINUTE
        unit = UNIT_MINUTE if value == 1 else UNIT_MINUTES
    elif age_seconds < SECONDS_PER_DAY:
        value = age_seconds // SECONDS_PER_HOUR
        unit = UNIT_HOUR if value == 1 else UNIT_HOURS
    else:
        value = age_seconds // SECONDS_PER_DAY
        unit = UNIT_DAY if value == 1 else UNIT_DAYS
    
    return f"{value} {unit}"


def _display_cache_header(
    zcli: Any,
    title: str,
    tier_name: Optional[str] = None
) -> None:
    """
    Display a cache section header.
    
    Args:
        zcli: The zCLI application instance
        title: Header title text
        tier_name: Optional tier name for context
        
    Example:
        >>> _display_cache_header(zcli, "Cache System - Three Tiers")
        >>> _display_cache_header(zcli, "Tier 1", "Pinned Cache")
    """
    zcli.display.text("")  # Blank line before header
    full_title = f"{title}: {tier_name}" if tier_name else title
    zcli.display.header(full_title, color=COLOR_HEADER)


def _display_resource_item(
    zcli: Any,
    item: Dict[str, Any],
    resource_type: str
) -> None:
    """
    Display a single cached resource item.
    
    Args:
        zcli: The zCLI application instance
        item: Resource item dictionary with name, zpath, age
        resource_type: Resource type for formatting context
        
    Example:
        >>> item = {"name": "myschema", "zpath": "@.Schemas.myschema", "age": 300}
        >>> _display_resource_item(zcli, item, "schema")
    """
    _ = resource_type  # Reserved for future type-specific formatting
    age_formatted = _format_cache_age(item.get(KEY_AGE, DEFAULT_AGE))
    name = item.get(KEY_NAME, "unknown")
    zpath = item.get(KEY_ZPATH, "N/A")
    
    zcli.display.text(f"{DISPLAY_INDENT}{DISPLAY_BULLET} {name}", indent=INDENT_ONE)
    zcli.display.text(f"Path: {zpath}", indent=INDENT_TWO)
    zcli.display.text(f"Age: {age_formatted}", indent=INDENT_TWO)


def _display_section_summary(
    zcli: Any,
    count: int,
    resource_type: Optional[str] = None
) -> None:
    """
    Display summary line for a cache section.
    
    Args:
        zcli: The zCLI application instance
        count: Number of items in section
        resource_type: Optional resource type for filtering context
        
    Example:
        >>> _display_section_summary(zcli, 5)
        >>> _display_section_summary(zcli, 3, "schema")
    """
    zcli.display.text("")  # Blank line before summary
    
    if resource_type:
        summary = f"Total: {count} {resource_type} resource(s)"
    else:
        summary = f"Total: {count} pinned resources"
    
    zcli.display.info(summary)


def _display_empty_cache_message(
    zcli: Any,
    cache_type: str,
    resource_filter: Optional[str] = None
) -> None:
    """
    Display message for empty cache.
    
    Args:
        zcli: The zCLI application instance
        cache_type: Type of cache (pinned, system, etc.)
        resource_filter: Optional resource type filter
        
    Example:
        >>> _display_empty_cache_message(zcli, "pinned")
        >>> _display_empty_cache_message(zcli, "pinned", "schema")
    """
    _ = cache_type  # Reserved for future cache-specific messaging
    zcli.display.text("")  # Blank line
    
    if resource_filter:
        message = MSG_EMPTY_FILTERED.format(type=resource_filter)
        help_text = MSG_EMPTY_FILTERED_HELP.format(type=resource_filter)
    else:
        message = MSG_EMPTY_CACHE
        help_text = MSG_EMPTY_CACHE_HELP
    
    zcli.display.info(message)
    zcli.display.text(help_text, indent=INDENT_ONE)


def _get_cache_resources_by_type(
    zcli: Any,
    filter_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve cached resources, optionally filtered by type.
    
    Args:
        zcli: The zCLI application instance
        filter_type: Optional resource type to filter (schema, ui, config)
        
    Returns:
        List of resource dictionaries
        
    Example:
        >>> resources = _get_cache_resources_by_type(zcli)
        >>> schema_resources = _get_cache_resources_by_type(zcli, "schema")
    """
    all_resources = zcli.loader.cache.pinned_cache.list_aliases()
    
    if filter_type:
        return [r for r in all_resources if r.get(KEY_TYPE) == filter_type]
    
    return all_resources


def _group_resources_by_type(
    resources: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group resources by their type.
    
    Args:
        resources: List of resource dictionaries
        
    Returns:
        Dictionary mapping type -> list of resources
        
    Example:
        >>> resources = [{"type": "schema", ...}, {"type": "ui", ...}]
        >>> grouped = _group_resources_by_type(resources)
        >>> # {"schema": [...], "ui": [...]}
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    
    for resource in resources:
        res_type = resource.get(KEY_TYPE, RESOURCE_TYPE_UNKNOWN)
        if res_type not in grouped:
            grouped[res_type] = []
        grouped[res_type].append(resource)
    
    return grouped


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN COMMAND FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def execute_load(zcli: Any, parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute load command to manage zLoader cache operations.
    
    This function handles three main actions:
    1. Load resources into cache (default)
    2. Show cache contents and statistics
    3. Clear cached resources
    
    Args:
        zcli: The zCLI application instance
        parsed: Parsed command dictionary with keys:
            - "args": List of command arguments
            - "options": Dict of command options (reserved)
            
    Returns:
        Result dictionary with keys:
            - "status": Operation status (success, empty, error)
            - "error": Error message (if status is error)
            - Additional keys based on operation
            
    Examples:
        >>> # Load a schema
        >>> parsed = {"args": ["@.Schemas.myschema"], "options": {}}
        >>> result = execute_load(zcli, parsed)
        >>> # {"status": "success", "type": "schema", "count": 3, ...}
        
        >>> # Show all cache tiers
        >>> parsed = {"args": ["show"], "options": {}}
        >>> result = execute_load(zcli, parsed)
        
        >>> # Clear cache
        >>> parsed = {"args": ["clear"], "options": {}}
        >>> result = execute_load(zcli, parsed)
    """
    # Validate subsystems
    loader_error = _validate_loader_subsystem(zcli)
    if loader_error:
        return loader_error
    
    # Extract arguments
    args = parsed.get(KEY_ARGS, [])
    _ = parsed.get(KEY_OPTIONS, {})  # Reserved for future use
    
    # Check if first arg is a subcommand (show/clear)
    if args and args[0] in [ACTION_SHOW, ACTION_CLEAR]:
        subcommand = args[0]
        remaining_args = args[1:]
        
        if subcommand == ACTION_SHOW:
            # Handle show variants
            if not remaining_args:
                # load show - show all tiers
                return show_all_cache_tiers(zcli)
            elif remaining_args[0] == SHOW_PINNED:
                # load show pinned - show Tier 1 only
                return show_pinned_resources(zcli)
            elif remaining_args[0] == SHOW_CACHED:
                # load show cached - show Tier 2 only
                return show_cached_stats(zcli)
            elif remaining_args[0] in [SHOW_SCHEMAS, SHOW_UI, SHOW_CONFIG]:
                # load show schemas/ui/config - filter by type
                return show_resources_by_type(zcli, remaining_args[0])
            else:
                error_msg = ERROR_UNKNOWN_SHOW_OPTION.format(option=remaining_args[0])
                zcli.display.error(error_msg)
                zcli.logger.error(error_msg)
                return {KEY_ERROR: error_msg}
                
        elif subcommand == ACTION_CLEAR:
            pattern = remaining_args[0] if remaining_args else DEFAULT_PATTERN
            return clear_loaded_resources(zcli, pattern)
    
    # Load resource (default action)
    if not args:
        zcli.display.error(ERROR_NO_ARGS)
        return {KEY_ERROR: ERROR_NO_ARGS}
    
    zPath = args[0]
    
    try:
        # Validate parser subsystem
        parser_error = _validate_parser_subsystem(zcli)
        if parser_error:
            return parser_error
        
        # Load via zLoader (uses SmartCache)
        result = zcli.loader.handle(zPath)
        
        if result == STATUS_ERROR or result is None:
            error_msg = ERROR_LOAD_FAILED.format(zpath=zPath)
            zcli.display.error(error_msg)
            zcli.logger.error(LOG_LOAD_FAILED, zPath, "Invalid result")
            return {KEY_ERROR: error_msg}
        
        # Get resolved filepath from zParser (for validation)
        zVaFile_fullpath, zVaFile = zcli.zparser.zPath_decoder(zPath, None)
        _, _ = zcli.zparser.identify_zFile(zVaFile, zVaFile_fullpath)
        
        # Detect resource type
        resource_type = _detect_resource_type(zPath)
        
        # Count items
        items, item_type = _count_resource_items(result, resource_type)
        
        # Log success
        zcli.logger.info(LOG_LOAD_SUCCESS, resource_type, zPath, len(items), item_type)
        
        # Display success message
        success_msg = MSG_LOADED.format(
            type=resource_type,
            path=zPath,
            count=len(items),
            item_type=item_type
        )
        zcli.display.success(success_msg)
        
        return {
            KEY_STATUS: STATUS_SUCCESS,
            KEY_TYPE: resource_type,
            KEY_PATH: zPath,
            KEY_ITEMS: items,
            KEY_COUNT: len(items)
        }
        
    except Exception as e:  # pylint: disable=broad-except
        error_msg = ERROR_LOAD_FAILED.format(zpath=zPath)
        zcli.logger.error(LOG_LOAD_FAILED, zPath, str(e))
        zcli.display.error(f"{error_msg}: {str(e)}")
        return {KEY_ERROR: str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# SHOW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def show_all_cache_tiers(zcli: Any) -> Dict[str, Any]:
    """
    Show all three cache tiers with statistics.
    
    Displays:
    - Tier 1: Pinned Cache (user-loaded resources)
    - Tier 2: System Cache (auto-cached files with stats)
    - Tier 3: Disk I/O (fallback description)
    
    Args:
        zcli: The zCLI application instance
        
    Returns:
        Result dictionary with tier counts
        
    Example:
        >>> result = show_all_cache_tiers(zcli)
        >>> # {"status": "success", "tier1_count": 3, "tier2_count": 12, ...}
    """
    zcli.logger.debug(LOG_SHOW_CACHE)
    
    # Main header
    _display_cache_header(zcli, HEADER_CACHE_SYSTEM)
    
    total_items = DEFAULT_COUNT
    
    # ============================================================
    # TIER 1: Pinned Cache (User-Loaded)
    # ============================================================
    zcli.display.text("")
    zcli.display.zDeclare(
        HEADER_TIER1,
        color=COLOR_SECTION,
        indent=INDENT_ZERO,
        style=STYLE_FULL
    )
    
    loaded_resources = _get_cache_resources_by_type(zcli)
    
    if loaded_resources:
        # Group by type
        by_type = _group_resources_by_type(loaded_resources)
        
        for res_type, items in by_type.items():
            zcli.display.text("")
            zcli.display.text(f"{res_type.upper()}:", indent=INDENT_ONE)
            
            for item in items:
                _display_resource_item(zcli, item, res_type)
        
        total_items += len(loaded_resources)
        _display_section_summary(zcli, len(loaded_resources))
    else:
        _display_empty_cache_message(zcli, "pinned")
    
    # ============================================================
    # TIER 2: System Cache (Auto-Cached Files)
    # ============================================================
    zcli.display.text("")
    zcli.display.zDeclare(
        HEADER_TIER2,
        color=COLOR_SECTION,
        indent=INDENT_ZERO,
        style=STYLE_FULL
    )
    
    # Get system cache statistics
    system_stats = zcli.loader.cache.system_cache.get_stats()
    
    zcli.display.text(
        f"Size: {system_stats.get(KEY_SIZE, 0)}/{system_stats.get(KEY_MAX_SIZE, 0)}",
        indent=INDENT_ONE
    )
    zcli.display.text(
        f"Hit Rate: {system_stats.get(KEY_HIT_RATE, '0%')}",
        indent=INDENT_ONE
    )
    zcli.display.text(
        f"Hits: {system_stats.get(KEY_HITS, 0)} | "
        f"Misses: {system_stats.get(KEY_MISSES, 0)}",
        indent=INDENT_ONE
    )
    zcli.display.text(
        f"Evictions: {system_stats.get(KEY_EVICTIONS, 0)} | "
        f"Invalidations: {system_stats.get(KEY_INVALIDATIONS, 0)}",
        indent=INDENT_ONE
    )
    
    total_items += system_stats.get(KEY_SIZE, DEFAULT_COUNT)
    
    # ============================================================
    # TIER 3: Disk I/O
    # ============================================================
    zcli.display.text("")
    zcli.display.zDeclare(
        HEADER_TIER3,
        color=COLOR_SECTION,
        indent=INDENT_ZERO,
        style=STYLE_FULL
    )
    zcli.display.text("Loads directly from filesystem when not cached", indent=INDENT_ONE)
    zcli.display.text("No eviction - always available", indent=INDENT_ONE)
    
    # Summary
    zcli.display.text("")
    zcli.display.header(f"Total Cached Items: {total_items}", color=COLOR_INFO)
    zcli.display.text("")
    
    return {
        KEY_STATUS: STATUS_SUCCESS,
        "tier1_count": len(loaded_resources),
        "tier2_count": system_stats.get(KEY_SIZE, DEFAULT_COUNT),
        "total": total_items
    }


def show_pinned_resources(zcli: Any) -> Dict[str, Any]:
    """
    Show only Tier 1 (pinned/loaded) resources.
    
    Args:
        zcli: The zCLI application instance
        
    Returns:
        Result dictionary with resource count
        
    Example:
        >>> result = show_pinned_resources(zcli)
        >>> # {"status": "success", "count": 3}
    """
    zcli.logger.debug(LOG_SHOW_PINNED)
    
    _display_cache_header(zcli, HEADER_PINNED)
    
    loaded_resources = _get_cache_resources_by_type(zcli)
    
    if not loaded_resources:
        _display_empty_cache_message(zcli, "pinned")
        return {KEY_STATUS: STATUS_EMPTY}
    
    # Group by type
    by_type = _group_resources_by_type(loaded_resources)
    
    for res_type, items in by_type.items():
        zcli.display.text("")
        zcli.display.text(f"{res_type.upper()}:", indent=INDENT_ONE)
        
        for item in items:
            _display_resource_item(zcli, item, res_type)
    
    _display_section_summary(zcli, len(loaded_resources))
    zcli.display.text("")
    
    return {KEY_STATUS: STATUS_SUCCESS, KEY_COUNT: len(loaded_resources)}


def show_cached_stats(zcli: Any) -> Dict[str, Any]:
    """
    Show only Tier 2 (system cache) statistics.
    
    Args:
        zcli: The zCLI application instance
        
    Returns:
        Result dictionary with cache stats
        
    Example:
        >>> result = show_cached_stats(zcli)
        >>> # {"status": "success", "stats": {...}}
    """
    zcli.logger.debug(LOG_SHOW_CACHED)
    
    _display_cache_header(zcli, HEADER_CACHED)
    
    system_stats = zcli.loader.cache.system_cache.get_stats()
    
    zcli.display.text("")
    zcli.display.text(
        f"Namespace: {system_stats.get(KEY_NAMESPACE, 'N/A')}",
        indent=INDENT_ONE
    )
    zcli.display.text(
        f"Size: {system_stats.get(KEY_SIZE, 0)}/"
        f"{system_stats.get(KEY_MAX_SIZE, 0)} entries",
        indent=INDENT_ONE
    )
    
    zcli.display.text("")
    zcli.display.text("Performance:", indent=INDENT_ONE)
    zcli.display.text(
        f"Hit Rate: {system_stats.get(KEY_HIT_RATE, '0%')}",
        indent=INDENT_TWO
    )
    zcli.display.text(
        f"Hits: {system_stats.get(KEY_HITS, 0)}",
        indent=INDENT_TWO
    )
    zcli.display.text(
        f"Misses: {system_stats.get(KEY_MISSES, 0)}",
        indent=INDENT_TWO
    )
    
    zcli.display.text("")
    zcli.display.text("Maintenance:", indent=INDENT_ONE)
    zcli.display.text(
        f"Evictions: {system_stats.get(KEY_EVICTIONS, 0)} (LRU)",
        indent=INDENT_TWO
    )
    zcli.display.text(
        f"Invalidations: {system_stats.get(KEY_INVALIDATIONS, 0)} (mtime)",
        indent=INDENT_TWO
    )
    
    zcli.display.text("")
    
    return {KEY_STATUS: STATUS_SUCCESS, "stats": system_stats}


def show_resources_by_type(zcli: Any, resource_type: str) -> Dict[str, Any]:
    """
    Show resources filtered by type (schemas, ui, config).
    
    Args:
        zcli: The zCLI application instance
        resource_type: Resource type to filter (schemas, ui, config)
        
    Returns:
        Result dictionary with filtered resources
        
    Example:
        >>> result = show_resources_by_type(zcli, "schemas")
        >>> # {"status": "success", "type": "schema", "count": 2}
    """
    # Normalize type name
    type_map = {
        SHOW_SCHEMAS: RESOURCE_TYPE_SCHEMA,
        SHOW_UI: RESOURCE_TYPE_UI,
        SHOW_CONFIG: RESOURCE_TYPE_CONFIG
    }
    filter_type = type_map.get(resource_type, resource_type)
    
    zcli.logger.debug(LOG_SHOW_FILTERED, filter_type)
    
    header_title = HEADER_RESOURCES.format(type=filter_type.upper())
    _display_cache_header(zcli, header_title)
    
    loaded_resources = _get_cache_resources_by_type(zcli, filter_type)
    
    if not loaded_resources:
        _display_empty_cache_message(zcli, "pinned", filter_type)
        return {KEY_STATUS: STATUS_EMPTY}
    
    zcli.display.text("")
    zcli.display.text(
        f"Found {len(loaded_resources)} {filter_type} resource(s):",
        indent=INDENT_ONE
    )
    zcli.display.text("")
    
    for item in loaded_resources:
        _display_resource_item(zcli, item, filter_type)
    
    _display_section_summary(zcli, len(loaded_resources), filter_type)
    zcli.display.text("")
    
    return {KEY_STATUS: STATUS_SUCCESS, KEY_TYPE: filter_type, KEY_COUNT: len(loaded_resources)}


# ═══════════════════════════════════════════════════════════════════════════════
# CLEAR FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def clear_loaded_resources(zcli: Any, pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear loaded resources from Tier 1 cache.
    
    Args:
        zcli: The zCLI application instance
        pattern: Optional pattern to match resource names
        
    Returns:
        Result dictionary with cleared count
        
    Example:
        >>> result = clear_loaded_resources(zcli)
        >>> # {"status": "success", "cleared": 3}
        
        >>> result = clear_loaded_resources(zcli, "sqlite")
        >>> # {"status": "success", "cleared": 1}
    """
    count = zcli.loader.cache.pinned_cache.clear(pattern)
    
    if pattern:
        message = MSG_CLEARED_PATTERN.format(count=count, pattern=pattern)
        zcli.logger.info(LOG_CLEAR_PATTERN, count, pattern)
    else:
        message = MSG_CLEARED.format(count=count)
        zcli.logger.info(LOG_CLEAR_ALL, count)
    
    zcli.display.text("")
    zcli.display.success(message)
    zcli.display.text("")
    
    return {KEY_STATUS: STATUS_SUCCESS, "cleared": count}
