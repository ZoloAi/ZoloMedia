# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_plugin_mgmt.py

"""
Plugin cache management for zCLI shell.

This module provides plugin cache management operations for the zCLI shell, including
loading plugins from zPath, showing loaded plugins and cache statistics, clearing the
plugin cache, and reloading plugins. It handles the "plugin load", "plugin show",
"plugin clear", and "plugin reload" subcommands.

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

Manage the plugin cache (zLoader.cache.plugin_cache) via shell commands. This module
provides a user-friendly interface for runtime plugin management, complementing the
boot-time plugin loading handled by zUtils.

**Key Responsibilities**:
    1. Load plugins from zPath (via zLoader.load_plugin_from_zpath facade)
    2. Display loaded plugins with metadata (name, path, cache hits)
    3. Display cache statistics (size, hits, misses, evictions, etc.)
    4. Clear plugin cache (all or by pattern)
    5. Reload plugins (clear + load)

═══════════════════════════════════════════════════════════════════════════════
COMMAND SYNTAX
═══════════════════════════════════════════════════════════════════════════════

**Load Plugin**:
    plugin load <zPath>                 # Load plugin from zPath

**Show Plugins**:
    plugin show                         # Show all loaded plugins
    plugin show cache                   # Show cache statistics

**Clear Cache**:
    plugin clear                        # Clear all cached plugins
    plugin clear [pattern]              # Clear plugins matching pattern

**Reload Plugin**:
    plugin reload <zPath>               # Reload plugin (clear + load)

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

**Backend Facade Integration**:
    - Uses zcli.loader.load_plugin_from_zpath() (NEW facade method)
    - Eliminates manual zPath resolution and file validation
    - Backend handles all complex logic, shell handles display

**Before (Lines 56-75 of old plugin.py)**:
    ```python
    # WRONG: Parser logic in shell command
    if zpath.startswith("zMachine."):
        file_path = zcli.zparser.resolve_zmachine_path(zpath)
    else:
        symbol = '@' if zpath.startswith('@') else ...
        # ... manual path parsing ...
    if not os.path.isfile(file_path):  # Filesystem check in UI
        return {"error": ...}
    ```

**After (Current Implementation)**:
    ```python
    # CORRECT: Backend facade delegation
    module = zcli.loader.load_plugin_from_zpath(zpath)
    # Backend handles: zPath resolution + file validation + loading
    ```

**Benefits of Facade**:
    - Shell stays thin and testable
    - Backend logic centralized in one place
    - Proper exception handling (FileNotFoundError, ValueError)
    - Easy to unit test and maintain

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION POINTS
═══════════════════════════════════════════════════════════════════════════════

**Dependencies**:
    - zLoader (Week 6.9): load_plugin_from_zpath() facade (NEW), cache.plugin_cache
    - zDisplay: All output display methods
    - zLogger: Debug/info logging

**Used By**:
    - shell_cmd_plugin.py: Main router (routes load/show/clear/reload here)

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

    # Load plugin from workspace
    plugin load @.plugins.auth
    # Output: [OK] Loaded plugin: auth
    #         Path: /workspace/plugins/auth.py
    #         Functions: hash_password, verify_password

    # Show loaded plugins
    plugin show
    # Output: Loaded Plugins
    #         • auth
    #           Path: /workspace/plugins/auth.py
    #           Cache hits: 5

    # Show cache statistics
    plugin show cache
    # Output: Plugin Cache Statistics
    #         Size: 3/50
    #         Hits: 15
    #         Misses: 3
    #         Hit Rate: 83.3%

    # Clear specific plugin
    plugin clear auth
    # Output: [OK] Cleared plugins matching: auth

    # Reload plugin
    plugin reload @.plugins.auth
    # Output: [OK] Reloaded plugin: auth

═══════════════════════════════════════════════════════════════════════════════
AUTHOR & VERSION
═══════════════════════════════════════════════════════════════════════════════

Author: zCLI Development Team
Version: 1.5.4
Last Updated: 2025-11-07
"""

from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Action Constants (for internal use)
ACTION_LOAD: str = "load"
ACTION_SHOW: str = "show"
ACTION_CLEAR: str = "clear"
ACTION_RELOAD: str = "reload"

# Show Mode Constants
SHOW_MODE_PLUGINS: str = "plugins"  # Show loaded plugins (default)
SHOW_MODE_CACHE: str = "cache"      # Show cache statistics

# Error Messages
ERROR_NO_ZPATH: str = "Usage: plugin load <zPath>\nExample: plugin load @.plugins.auth"
ERROR_LOAD_FAILED: str = "Failed to load plugin: {error}"
ERROR_NOT_FOUND: str = "Plugin file not found: {zpath}"
ERROR_NO_ZPATH_RELOAD: str = "Usage: plugin reload <zPath>\nExample: plugin reload @.plugins.auth"
ERROR_RELOAD_FAILED: str = "Failed to reload plugin: {error}"

# Success Messages
MSG_LOADED: str = "[OK] Loaded plugin: {name}"
MSG_CLEARED: str = "[OK] Cleared all cached plugins"
MSG_CLEARED_PATTERN: str = "[OK] Cleared plugins matching: {pattern}"
MSG_RELOADED: str = "[OK] Reloaded plugin: {name}"

# Display Headers
HEADER_PLUGINS: str = "Loaded Plugins"
HEADER_CACHE: str = "Plugin Cache Statistics"

# Display Labels
LABEL_PATH: str = "Path:"
LABEL_FUNCTIONS: str = "Functions:"
LABEL_CACHE_HITS: str = "Cache hits:"
LABEL_SIZE: str = "Size:"
LABEL_HITS: str = "Hits:"
LABEL_MISSES: str = "Misses:"
LABEL_HIT_RATE: str = "Hit Rate:"
LABEL_LOADS: str = "Loads:"
LABEL_EVICTIONS: str = "Evictions:"
LABEL_INVALIDATIONS: str = "Invalidations:"
LABEL_COLLISIONS: str = "Collisions:"
LABEL_TOTAL: str = "Total:"

# Info Messages
MSG_NO_PLUGINS: str = "No plugins loaded"
MSG_USE_LOAD: str = "Use 'plugin load <zPath>' to load a plugin"
MSG_USE_AUTO: str = "Or use '&PluginName.function()' - auto-loads from standard paths"

# Dict Keys
KEY_NAME: str = "name"
KEY_FILEPATH: str = "filepath"
KEY_HITS: str = "hits"
KEY_SIZE: str = "size"
KEY_MAX_SIZE: str = "max_size"
KEY_HIT_RATE: str = "hit_rate"
KEY_MISSES: str = "misses"
KEY_LOADS: str = "loads"
KEY_EVICTIONS: str = "evictions"
KEY_INVALIDATIONS: str = "invalidations"
KEY_COLLISIONS: str = "collisions"
KEY_PLUGIN_CACHE: str = "plugin_cache"

# Log Messages
LOG_LOAD_SUCCESS: str = "Loaded plugin %s from %s"
LOG_LOAD_FAILED: str = "Failed to load plugin from %s: %s"
LOG_CLEARED: str = "Cleared %s plugins"
LOG_CLEARED_PATTERN: str = "Cleared plugins matching '%s'"
LOG_RELOAD_SUCCESS: str = "Reloaded plugin %s"

# Default Values
DEFAULT_UNKNOWN: str = "unknown"
DEFAULT_NONE: str = "none"
DEFAULT_ZERO: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_plugin_functions(module: Any) -> List[str]:
    """
    Extract callable function names from a plugin module.

    Parameters
    ----------
    module : Any
        Loaded plugin module object

    Returns
    -------
    List[str]
        List of public function names (excludes private methods starting with '_')

    Notes
    -----
    **Filtering Rules**:
        - Excludes names starting with '_' (private)
        - Only includes callables (functions, methods)
        - Respects __all__ if defined in module

    **Examples**:
        >>> module.func1 = lambda: None
        >>> module._private = lambda: None
        >>> module.data = "not callable"
        >>> _get_plugin_functions(module)
        ['func1']
    """
    return [
        name for name in dir(module)
        if not name.startswith("_") and callable(getattr(module, name))
    ]


def _extract_module_name(zpath: str) -> str:
    """
    Extract module name from zPath string.

    Parameters
    ----------
    zpath : str
        zPath string (e.g., "@.plugins.auth", "zMachine.plugins.helper")

    Returns
    -------
    str
        Module name (last component of path)

    Examples
    --------
    >>> _extract_module_name("@.plugins.auth")
    'auth'
    >>> _extract_module_name("zMachine.plugins.helper")
    'helper'
    >>> _extract_module_name("~.custom.generator")
    'generator'

    Notes
    -----
    Removes zPath prefixes (@., ~., zMachine.) and extracts last component.
    """
    # Remove zPath prefixes
    clean_path = zpath.replace("@.", "").replace("~.", "").replace("zMachine.", "")
    # Split by dots and take last component
    parts = clean_path.split(".")
    return parts[-1] if parts else zpath


def _display_plugin_info(zcli: Any, plugin_info: Dict[str, Any]) -> None:
    """
    Display formatted information for a single plugin.

    Parameters
    ----------
    zcli : Any
        zCLI instance for display access
    plugin_info : Dict[str, Any]
        Plugin information dictionary with keys:
            - "name": Plugin name
            - "filepath": Full file path
            - "hits": Cache hit count

    Notes
    -----
    **Display Format**:
        • plugin_name
          Path: /full/path/to/plugin.py
          Cache hits: 5

    **Used By**:
        - show_plugins() for each plugin in list
    """
    name = plugin_info.get(KEY_NAME, DEFAULT_UNKNOWN)
    filepath = plugin_info.get(KEY_FILEPATH, DEFAULT_UNKNOWN)
    hits = plugin_info.get(KEY_HITS, DEFAULT_ZERO)

    zcli.display.text(f"\n[BULLET] {name}")
    zcli.display.text(f"  {LABEL_PATH} {filepath}")
    zcli.display.text(f"  {LABEL_CACHE_HITS} {hits}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MANAGEMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def load_plugin(zcli: Any, args: List[str]) -> None:
    """
    Load a plugin from zPath and display information.

    Uses the zLoader.load_plugin_from_zpath() backend facade to handle all
    complex logic (path resolution, file validation, loading). Shell command
    only handles argument validation and display formatting.

    Parameters
    ----------
    zcli : Any
        zCLI instance providing access to loader, display, logger
    args : List[str]
        Command arguments where args[0] is the zPath

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Examples
    --------
    >>> load_plugin(zcli, ["@.plugins.auth"])
    # Displays: [OK] Loaded plugin: auth
    #           Path: /workspace/plugins/auth.py
    #           Functions: hash_password, verify_password

    Notes
    -----
    **Backend Facade**:
        All heavy lifting done by zcli.loader.load_plugin_from_zpath():
        - zPath resolution (delegates to zParser)
        - File existence validation
        - Plugin loading (delegates to plugin_cache)
        - Session injection (automatic)

    **Error Handling**:
        - FileNotFoundError: Plugin file not found
        - ValueError: Plugin load error (syntax, collision, etc.)
        - Display user-friendly error messages
    """
    # Validate args
    if not args:
        zcli.display.error(ERROR_NO_ZPATH)
        return

    zpath: str = args[0]

    try:
        # Use backend facade (handles zPath resolution + file validation + loading)
        module = zcli.loader.load_plugin_from_zpath(zpath)

        # Extract module name and file path from zpath
        module_name: str = _extract_module_name(zpath)

        # Get available functions
        functions: List[str] = _get_plugin_functions(module)

        # Log success
        zcli.logger.info(LOG_LOAD_SUCCESS, module_name, zpath)

        # Display success
        success_msg: str = MSG_LOADED.format(name=module_name)
        zcli.display.success(success_msg)

        # Display path (get from module if available)
        if hasattr(module, "__file__") and module.__file__:
            zcli.display.info(f"  {LABEL_PATH} {module.__file__}")

        # Display functions
        functions_str: str = ", ".join(functions) if functions else DEFAULT_NONE
        zcli.display.info(f"  {LABEL_FUNCTIONS} {functions_str}")

    except FileNotFoundError as e:
        zcli.logger.error(LOG_LOAD_FAILED, zpath, str(e))
        error_msg: str = ERROR_NOT_FOUND.format(zpath=zpath)
        zcli.display.error(error_msg)

    except (ValueError, Exception) as e:
        zcli.logger.error(LOG_LOAD_FAILED, zpath, str(e))
        error_msg = ERROR_LOAD_FAILED.format(error=str(e))
        zcli.display.error(error_msg)


def show_plugins(zcli: Any, args: List[str]) -> None:
    """
    Show loaded plugins or cache statistics.

    Displays either loaded plugins (default) or cache statistics based on args.

    Parameters
    ----------
    zcli : Any
        zCLI instance providing access to loader, display, logger
    args : List[str]
        Command arguments where args[0] may be "cache" for stats mode

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Examples
    --------
    **Show Loaded Plugins**:
        >>> show_plugins(zcli, [])
        # Displays: Loaded Plugins
        #           • auth
        #             Path: /workspace/plugins/auth.py
        #             Cache hits: 5
        #           Total: 1 plugins

    **Show Cache Statistics**:
        >>> show_plugins(zcli, ["cache"])
        # Displays: Plugin Cache Statistics
        #           Size: 3/50
        #           Hits: 15
        #           Misses: 3
        #           Hit Rate: 83.3%

    Notes
    -----
    **Two Display Modes**:
        - No args or args[0] != "cache": Show loaded plugins
        - args[0] == "cache": Show cache statistics

    **Cache Statistics**:
        Retrieved via zcli.loader.cache.get_stats(cache_type="plugin")
    """
    # Check if showing cache stats
    if args and args[0] == SHOW_MODE_CACHE:
        # Show cache statistics
        stats: Dict[str, Any] = zcli.loader.cache.get_stats(cache_type="plugin")
        plugin_cache_stats: Dict[str, Any] = stats.get(KEY_PLUGIN_CACHE, {})

        zcli.display.header(HEADER_CACHE)
        zcli.display.text(
            f"{LABEL_SIZE} {plugin_cache_stats.get(KEY_SIZE, DEFAULT_ZERO)}/"
            f"{plugin_cache_stats.get(KEY_MAX_SIZE, DEFAULT_ZERO)}"
        )
        zcli.display.text(f"{LABEL_HITS} {plugin_cache_stats.get(KEY_HITS, DEFAULT_ZERO)}")
        zcli.display.text(f"{LABEL_MISSES} {plugin_cache_stats.get(KEY_MISSES, DEFAULT_ZERO)}")
        zcli.display.text(f"{LABEL_HIT_RATE} {plugin_cache_stats.get(KEY_HIT_RATE, '0%')}")
        zcli.display.text(f"{LABEL_LOADS} {plugin_cache_stats.get(KEY_LOADS, DEFAULT_ZERO)}")
        zcli.display.text(f"{LABEL_EVICTIONS} {plugin_cache_stats.get(KEY_EVICTIONS, DEFAULT_ZERO)}")
        zcli.display.text(f"{LABEL_INVALIDATIONS} {plugin_cache_stats.get(KEY_INVALIDATIONS, DEFAULT_ZERO)}")
        zcli.display.text(f"{LABEL_COLLISIONS} {plugin_cache_stats.get(KEY_COLLISIONS, DEFAULT_ZERO)}")
        return

    # Show loaded plugins
    cached_plugins: List[Dict[str, Any]] = zcli.loader.cache.plugin_cache.list_plugins()

    zcli.display.header(HEADER_PLUGINS)

    if cached_plugins:
        # Display each plugin
        for plugin_info in cached_plugins:
            _display_plugin_info(zcli, plugin_info)

        # Display total
        total: int = len(cached_plugins)
        zcli.display.text(f"\n{LABEL_TOTAL} {total} plugins")
    else:
        # No plugins loaded
        zcli.display.warning(MSG_NO_PLUGINS)
        zcli.display.info(MSG_USE_LOAD)
        zcli.display.info(MSG_USE_AUTO)


def clear_plugins(zcli: Any, args: List[str]) -> None:
    """
    Clear plugin cache (all or by pattern).

    Parameters
    ----------
    zcli : Any
        zCLI instance providing access to loader, display, logger
    args : List[str]
        Command arguments where args[0] (optional) is the pattern to match

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Examples
    --------
    **Clear All Plugins**:
        >>> clear_plugins(zcli, [])
        # Displays: [OK] Cleared all cached plugins

    **Clear by Pattern**:
        >>> clear_plugins(zcli, ["auth"])
        # Displays: [OK] Cleared plugins matching: auth

    Notes
    -----
    **Pattern Matching**:
        If pattern provided, only clears plugins whose names match the pattern.
        Uses plugin_cache.clear(pattern) for pattern-based clearing.
    """
    pattern: Optional[str] = args[0] if args else None

    if pattern:
        zcli.loader.cache.clear(cache_type="plugin", pattern=pattern)
        success_msg: str = MSG_CLEARED_PATTERN.format(pattern=pattern)
        zcli.display.success(success_msg)
        zcli.logger.info(LOG_CLEARED_PATTERN, pattern)
    else:
        zcli.loader.cache.clear(cache_type="plugin")
        zcli.display.success(MSG_CLEARED)
        zcli.logger.info(LOG_CLEARED, "all")


def reload_plugin(zcli: Any, args: List[str]) -> None:
    """
    Reload a plugin (clear + load).

    Clears the plugin from cache and then loads it fresh. Useful during development
    when plugin code has been modified.

    Parameters
    ----------
    zcli : Any
        zCLI instance providing access to loader, display, logger
    args : List[str]
        Command arguments where args[0] is the zPath

    Returns
    -------
    None
        All output is displayed via zDisplay (UI adapter pattern)

    Examples
    --------
    >>> reload_plugin(zcli, ["@.plugins.auth"])
    # Displays: [OK] Cleared plugins matching: auth
    #           [OK] Loaded plugin: auth
    #           Path: /workspace/plugins/auth.py
    #           Functions: hash_password, verify_password
    #           [OK] Reloaded plugin: auth

    Notes
    -----
    **Two-Step Process**:
        1. Clear plugin from cache by name
        2. Load plugin fresh from zPath

    **Error Handling**:
        If clear or load fails, displays error and stops.
    """
    # Validate args
    if not args:
        zcli.display.error(ERROR_NO_ZPATH_RELOAD)
        return

    zpath: str = args[0]

    try:
        # Extract module name for clearing
        module_name: str = _extract_module_name(zpath)

        # Step 1: Clear from cache
        clear_plugins(zcli, [module_name])

        # Step 2: Load fresh
        load_plugin(zcli, [zpath])

        # Display reload success
        success_msg: str = MSG_RELOADED.format(name=module_name)
        zcli.display.success(success_msg)
        zcli.logger.info(LOG_RELOAD_SUCCESS, module_name)

    except Exception as e:  # pylint: disable=broad-except
        error_msg: str = ERROR_RELOAD_FAILED.format(error=str(e))
        zcli.display.error(error_msg)

