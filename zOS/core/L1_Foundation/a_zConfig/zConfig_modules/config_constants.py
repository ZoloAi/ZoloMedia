# zCLI/L1_Foundation/a_zConfig/zConfig_modules/constants.py
"""
Centralized constants for zConfig subsystem.

This module contains all public constants used throughout the zCLI framework
for session management, authentication, caching, and configuration.
"""

# ============================================================
# zMode Values
# ============================================================

ZMODE_TERMINAL = "Terminal"
ZMODE_ZBIFROST = "zBifrost"

# ============================================================
# Action Routing
# ============================================================

ACTION_PLACEHOLDER = "#"  # No-op action for development/testing

# ============================================================
# Session Dictionary Keys
# ============================================================
# Keys for accessing session state throughout the framework

SESSION_KEY_ZS_ID = "zS_id"
SESSION_KEY_TITLE = "title"
SESSION_KEY_ZSPACE = "zSpace"
SESSION_KEY_ZVAFOLDER = "zVaFolder"
SESSION_KEY_ZVAFILE = "zVaFile"
SESSION_KEY_ZBLOCK = "zBlock"
SESSION_KEY_ZMODE = "zMode"
SESSION_KEY_ZLOGGER = "zLogger"
SESSION_KEY_LOGGER_PATH = "logger_path"
SESSION_KEY_ZTRACEBACK = "zTraceback"
SESSION_KEY_ZMACHINE = "zMachine"
SESSION_KEY_ZAUTH = "zAuth"
SESSION_KEY_ZCRUMBS = "zCrumbs"
SESSION_KEY_ZCACHE = "zCache"
SESSION_KEY_WIZARD_MODE = "wizard_mode"
SESSION_KEY_ZSPARK = "zSpark"
SESSION_KEY_VIRTUAL_ENV = "virtual_env"
SESSION_KEY_SYSTEM_ENV = "system_env"
SESSION_KEY_LOGGER_INSTANCE = "logger_instance"
SESSION_KEY_ZVARS = "zVars"
SESSION_KEY_ZSHORTCUTS = "zShortcuts"
SESSION_KEY_BROWSER = "browser"
SESSION_KEY_IDE = "ide"
SESSION_KEY_SESSION_HASH = "session_hash"  # v1.6.0: For frontend cache invalidation

# ============================================================
# zSpark Configuration Keys
# ============================================================
# Keys for zSpark boot configuration

ZSPARK_KEY_TITLE = "title"
ZSPARK_KEY_ZSPACE = "zSpace"
ZSPARK_KEY_ZVAFOLDER = "zVaFolder"
ZSPARK_KEY_ZVAFILE = "zVaFile"
ZSPARK_KEY_ZBLOCK = "zBlock"
ZSPARK_KEY_ZTRACEBACK = "zTraceback"
ZSPARK_KEY_ZMODE = "zMode"
ZSPARK_KEY_LOGGER = "logger"
ZSPARK_KEY_LOGGER_PATH = "logger_path"

# ============================================================
# zAuth Keys (Three-Tier Architecture)
# ============================================================

# Top-level structure keys
ZAUTH_KEY_ZSESSION = "zSession"
ZAUTH_KEY_APPLICATIONS = "applications"  # Multi-app support
ZAUTH_KEY_ACTIVE_APP = "active_app"
ZAUTH_KEY_ACTIVE_CONTEXT = "active_context"
ZAUTH_KEY_DUAL_MODE = "dual_mode"

# User info keys (used in both zSession and application contexts)
ZAUTH_KEY_AUTHENTICATED = "authenticated"
ZAUTH_KEY_ID = "id"
ZAUTH_KEY_USERNAME = "username"
ZAUTH_KEY_ROLE = "role"
ZAUTH_KEY_API_KEY = "api_key"

# Context values
CONTEXT_ZSESSION = "zSession"
CONTEXT_APPLICATION = "application"
CONTEXT_DUAL = "dual"

# ============================================================
# zCache Keys
# ============================================================

ZCACHE_KEY_SYSTEM = "system_cache"
ZCACHE_KEY_PINNED = "pinned_cache"
ZCACHE_KEY_SCHEMA = "schema_cache"
ZCACHE_KEY_PLUGIN = "plugin_cache"

# ============================================================
# Wizard Mode Keys
# ============================================================

WIZARD_KEY_ACTIVE = "active"
WIZARD_KEY_LINES = "lines"
WIZARD_KEY_FORMAT = "format"
WIZARD_KEY_TRANSACTION = "transaction"

