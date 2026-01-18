# zCLI/L3_Abstraction/l_zUtils/utils_modules/utils_constants.py

"""
Centralized constants for the zUtils subsystem.

This module contains all constants used by the zUtils plugin management system.
Constants are organized into PUBLIC (exported API) and INTERNAL (implementation
details) sections.

PUBLIC Constants:
    - Subsystem metadata (SUBSYSTEM_NAME, SUBSYSTEM_COLOR)
    - Default values (DEFAULT_PLUGINS_DICT)

INTERNAL Constants:
    - Display messages (prefixed with _MSG_)
    - Log messages (prefixed with _LOG_MSG_)
    - Warning messages (prefixed with _WARN_MSG_)
    - Error messages (prefixed with _ERROR_MSG_)
    - Plugin loading configuration (prefixed with _ATTR_)
    - Cache configuration (prefixed with _CACHE_)
    - Stats configuration (prefixed with _STATS_)
    - Mtime configuration (prefixed with _MTIME_)

Usage:
    >>> from zOS.L3_Abstraction.l_zUtils.utils_modules import SUBSYSTEM_NAME
    >>> from zOS.L3_Abstraction.l_zUtils.utils_modules.utils_constants import _LOG_MSG_LOADING
"""

from zOS import Any, Dict

# ============================================================================
# PUBLIC CONSTANTS (API)
# ============================================================================

# Subsystem Metadata
SUBSYSTEM_NAME: str = "zUtils"
SUBSYSTEM_COLOR: str = "ZUTILS"

# Default Values
DEFAULT_PLUGINS_DICT: Dict[str, Any] = {}


# ============================================================================
# INTERNAL CONSTANTS (Implementation Details)
# ============================================================================

# Display Messages
_MSG_READY: str = "zUtils Ready"

# Log Messages
_LOG_MSG_LOADING: str = "Loading plugins"
_LOG_MSG_LOADED_FILE: str = "Loaded plugin from file: %s (session injected)"
_LOG_MSG_LOADED_MODULE: str = "Loaded plugin from module: %s (session injected)"
_LOG_MSG_EXPOSED_COUNT: str = "Exposed %d callables from plugin: %s"
_LOG_MSG_LOAD_START: str = "Loading plugin: %s"
_LOG_MSG_LOAD_SUCCESS: str = "Successfully loaded plugin: %s"
_LOG_MSG_CACHED_TO_LOADER: str = "Plugin cached in zLoader.plugin_cache: %s"
_LOG_MSG_USING_ALL: str = "Plugin %s uses __all__, exposing %d functions"

# Warning Messages
_WARN_MSG_LOAD_FAILED: str = "Failed to load plugin '%s': %s"
_WARN_MSG_NO_MODULE: str = "Plugin module could not be loaded: %s"
_WARN_MSG_COLLISION: str = "Method collision skipped for plugin '%s': %s already exists"
_WARN_MSG_NO_ALL: str = "Plugin %s has no __all__, exposing all public callables (security risk)"
_WARN_MSG_NOT_IN_ALL: str = "Function '%s' in plugin %s not in __all__, skipping exposure"

# Error Messages
_ERROR_MSG_IMPORT_FAILED: str = "Import failed for plugin: {path}"
_ERROR_MSG_SPEC_FAILED: str = "Failed to create module spec for: {path}"
_ERROR_MSG_EXEC_FAILED: str = "Failed to execute plugin module: {path}"
_ERROR_MSG_INVALID_PATH: str = "Invalid plugin path: {path}"
_ERROR_MSG_LOADER_UNAVAILABLE: str = "zLoader unavailable, cannot cache plugin: {path}"
_ERROR_MSG_COLLISION: str = "Plugin collision: '{name}' already loaded from {existing_path}"

# Plugin Loading Constants
_ATTR_PREFIX_PRIVATE: str = "_"
_ATTR_NAME_ZCLI: str = "zcli"
_ATTR_NAME_ALL: str = "__all__"

# Cache Constants
_CACHE_TYPE_PLUGIN: str = "plugin"

# Stats Constants (Phase 3)
_STATS_KEY_TOTAL_LOADS: str = "total_loads"
_STATS_KEY_COLLISIONS: str = "collisions"
_STATS_KEY_RELOADS: str = "reloads"
_STATS_KEY_PLUGINS_LOADED: str = "plugins_loaded"

# Mtime Constants (Phase 3)
_MTIME_CHECK_INTERVAL: float = 1.0  # seconds between mtime checks
_MTIME_CACHE_KEY: str = "mtime"
_PATH_CACHE_KEY: str = "path"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Public API Constants
    'SUBSYSTEM_NAME',
    'SUBSYSTEM_COLOR',
    'DEFAULT_PLUGINS_DICT',
]
