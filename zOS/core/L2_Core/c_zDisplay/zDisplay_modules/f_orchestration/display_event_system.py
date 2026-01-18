# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_system.py
"""
zSystem - zCLI System Introspection & Navigation UI Events (v1.5.4+)

This module provides system-level user interface events for the zDisplay subsystem,
enabling comprehensive introspection and display of zCLI's internal state across both
Terminal and Bifrost (GUI) modes. It serves as the UI presentation layer for core
zCLI concepts: zSession, zMachine, zAuth, zCrumbs, zMenu, and zDialog.

ARCHITECTURE: System-Level UI Integration

zSystem is unique among zDisplay event packages as it operates at the **system level**,
directly interacting with zCLI's core state management structures. Unlike other event
packages that handle user data, zSystem displays zCLI's own internal state.

Integration Flow:
    zCLI core → zSystem → zDisplay → zPrimitives → Terminal/Bifrost

Example:
    # Display complete session state
    zcli.display.zEvents.zSystem.zSession(zcli.session)
    
    # Display navigation breadcrumbs
    zcli.display.zEvents.zSystem.zCrumbs(zcli.session)
    
    # Show interactive menu
    choice = zcli.display.zEvents.zSystem.zMenu(
        menu_items=[(1, "Create"), (2, "Read"), (3, "Update")],
        return_selection=True
    )


ZSESSION INTEGRATION (19 Core Session Keys)

zSession is the central state dictionary that persists throughout a zCLI session.
zSystem uses **standardized SESSION_KEY_* constants** from zConfig to ensure safe,
refactor-proof access to session data.

Core Session Fields (Imported from zConfig):
    SESSION_KEY_ZS_ID           - "zS_id" - Unique session identifier
    SESSION_KEY_ZMODE           - "zMode" - UI mode (Terminal, Walker, Bifrost)
    SESSION_KEY_ZMACHINE        - "zMachine" - Machine configuration dict
    SESSION_KEY_ZAUTH           - "zAuth" - Authentication state dict
    SESSION_KEY_ZSPACE      - "zSpace" - Current workspace path
    SESSION_KEY_ZVAFOLDER       - "zVaFolder" - Folder containing zVaFile
    SESSION_KEY_ZVAFILE     - "zVaFile" - zVaFile filename
    SESSION_KEY_ZBLOCK          - "zBlock" - Current block/scope
    SESSION_KEY_ZCRUMBS         - "zCrumbs" - Breadcrumb navigation dict
    SESSION_KEY_ZCACHE          - "zCache" - Session-level cache
    SESSION_KEY_WIZARD_MODE     - "wizard_mode" - Wizard mode flag
    SESSION_KEY_ZSPARK          - "zSpark" - Spark integration
    SESSION_KEY_VIRTUAL_ENV     - "virtual_env" - Virtual environment path
    SESSION_KEY_SYSTEM_ENV      - "system_env" - System environment
    SESSION_KEY_ZLOGGER         - "zLogger" - Logger configuration
    SESSION_KEY_ZTRACEBACK      - "zTraceback" - Traceback configuration
    SESSION_KEY_LOGGER_INSTANCE - "logger_instance" - Logger instance
    SESSION_KEY_ZVARS           - "zVars" - User-defined variables
    SESSION_KEY_ZSHORTCUTS      - "zShortcuts" - File shortcuts

Usage Example:
    # ❌ OLD (Legacy, error-prone):
    session_id = session.get("zS_id")
    mode = session.get("zMode")
    
    # ✅ NEW (Modern, refactor-safe):
    session_id = session.get(SESSION_KEY_ZS_ID)
    mode = session.get(SESSION_KEY_ZMODE)


ZAUTH INTEGRATION (Three-Tier Authentication Model)

zAuth v1.5.4+ supports a **three-tier authentication architecture** that zSystem must
correctly display. zSystem uses **standardized ZAUTH_KEY_* constants** from zConfig.

Layer 1 - zSession Auth (Internal zCLI/Zolo Users):
    Purpose:     Premium zCLI features, plugins, Zolo cloud services
    Triggered:   zcli.auth.login()
    Session Key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ZSESSION]
    Contains:    authenticated, id, username, role, api_key
    Example:     Developer authenticating to access premium features

Layer 2 - Application Auth (External App Users, Multi-App Support):
    Purpose:     Users of applications BUILT on zCLI
    Triggered:   zcli.auth.authenticate_app_user(app_name, token, config)
    Session Key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_APPLICATIONS][app_name]
    Contains:    authenticated, id, username, role, api_key (per app)
    Example:     Store customer authenticating to eCommerce app
    Note:        Multiple apps can be authenticated simultaneously

Layer 3 - Dual-Auth (Simultaneous zSession + Application):
    Purpose:     Developer working on their own application
    Session Key: session[SESSION_KEY_ZAUTH][ZAUTH_KEY_DUAL_MODE] = True
    Example:     Store owner (zSession) logged into their store (app user)

Context Management:
    session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_CONTEXT]:  "zSession", "application", or "dual"
    session[SESSION_KEY_ZAUTH][ZAUTH_KEY_ACTIVE_APP]:      Current focused app name

zAuth Constants (Imported from zConfig):
    ZAUTH_KEY_ZSESSION          - "zSession" - zSession auth dict key
    ZAUTH_KEY_APPLICATIONS      - "applications" - App auth dict key
    ZAUTH_KEY_ACTIVE_APP        - "active_app" - Focused app name
    ZAUTH_KEY_AUTHENTICATED     - "authenticated" - Auth status flag
    ZAUTH_KEY_ID                - "id" - User ID (NOT "zAuth_id"!)
    ZAUTH_KEY_USERNAME          - "username" - Username
    ZAUTH_KEY_ROLE              - "role" - User role
    ZAUTH_KEY_API_KEY           - "api_key" - API key
    ZAUTH_KEY_ACTIVE_CONTEXT    - "active_context" - Current context
    ZAUTH_KEY_DUAL_MODE         - "dual_mode" - Dual auth flag
    CONTEXT_ZSESSION            - "zSession" - zSession context value
    CONTEXT_APPLICATION         - "application" - App context value
    CONTEXT_DUAL                - "dual" - Dual context value

Display Integration:
    _display_zauth() method now shows:
    - Current authentication context (zSession/application/dual)
    - Active app name (if in application/dual context)
    - All authenticated apps (if multiple)
    - Dual-mode indicator (if both contexts active)


ZMACHINE INTEGRATION (Machine Configuration)

zMachine contains the machine and environment configuration where zCLI is running.
zSystem displays this structured information in organized sections.

zMachine Fields (10+ keys):
    Identity & Deployment:
        _ZMACHINE_KEY_OS               - "os" - Operating system
        _ZMACHINE_KEY_HOSTNAME         - "hostname" - Machine hostname
        _ZMACHINE_KEY_ARCHITECTURE     - "architecture" - CPU architecture
        _ZMACHINE_KEY_PYTHON_VERSION   - "python_version" - Python version
        _ZMACHINE_KEY_DEPLOYMENT       - "deployment" - Deployment mode (dev/prod)
        _ZMACHINE_KEY_ROLE             - "role" - Machine role
    
    Tool Preferences:
        _ZMACHINE_KEY_BROWSER          - "browser" - Preferred browser
        _ZMACHINE_KEY_IDE              - "ide" - Preferred IDE
        _ZMACHINE_KEY_SHELL            - "shell" - Preferred shell
    
    System Capabilities:
        _ZMACHINE_KEY_CPU_CORES        - "cpu_cores" - Number of CPU cores
        _ZMACHINE_KEY_MEMORY_GB        - "memory_gb" - RAM in GB
    
    zCLI Version:
        _ZMACHINE_KEY_ZCLI_VERSION     - "zcli_version" - zCLI version number


SYSTEM METHODS PROVIDED

Core System Displays:
    zSession():     Display complete session state (zS_id, zMode, zMachine, zAuth, etc.)
    zCrumbs():      Display navigation breadcrumb trails (scope paths)
    zMenu():        Display interactive menu with selection support
    zDialog():      Display form dialog and collect validated input
    zDeclare():     Display system declaration/message with log-level conditioning

Helper Methods (Private):
    _try_gui_event():       DRY helper for GUI event dispatch
    _output_text():         DRY helper for BasicOutputs text
    _get_color():           DRY helper for color code lookup
    _display_field():       Display labeled field with color
    _display_section():     Display section title with color
    _display_zmachine():    Display complete zMachine structure
    _display_zauth():       Display complete zAuth state (three-tier aware)
    _should_show_sysmsg():  Check logging level for system message display


DUAL-MODE I/O PATTERN

All public methods follow the GUI-first, Terminal-fallback pattern established by
zDisplay's dual-mode architecture:

1. Try Bifrost (GUI) mode first via send_gui_event()
2. If GUI mode succeeds (returns True), return immediately
3. If GUI mode unavailable (returns False), fall back to Terminal mode
4. Terminal mode uses composition: BasicOutputs, Signals, BasicInputs

Example Flow:
    zSession(session_data)
    ├─ GUI Mode:      Send _EVENT_ZSESSION to Bifrost
    │                 → Frontend shows interactive session viewer
    │                 → Return immediately
    └─ Terminal Mode: Use zDeclare() + _display_field() + _display_zmachine() + _display_zauth()
                      → Display formatted session in terminal


COMPOSITION PATTERN

zSystem depends on three sibling event packages via composition (most dependencies
of any event package):

Dependencies:
    BasicOutputs (display_event_outputs.py):
        - header():  Display section headers
        - text():    Display formatted text
        - Used for: All session/machine/auth field display
    
    Signals (display_event_signals.py):
        - success(), error(), warning(), info():  Colored status messages
        - Used for: System message feedback (future integration)
    
    BasicInputs (display_event_inputs.py):
        - selection():  Interactive numbered selection
        - Used for: zMenu() interactive mode

Cross-Reference:
    zSystem depends on: BasicOutputs, Signals, BasicInputs
    No other packages depend on zSystem (leaf node in dependency graph)


LOGGING INTEGRATION (_should_show_sysmsg)

System messages (zDeclare) are conditionally displayed based on logging level and
deployment mode. This prevents verbose system messages in production environments.

Check Priority:
    1. Logger method:      zcli.logger.should_show_sysmsg() (if available)
    2. Debug flag:         session.get("debug") (legacy fallback)
    3. Deployment mode:    session[SESSION_KEY_ZMACHINE][_ZMACHINE_KEY_DEPLOYMENT]
                          - "dev" → show messages (default)
                          - "prod" → hide messages

Usage:
    def zDeclare(self, label, ...):
        if not self._should_show_sysmsg():
            return  # Don't display in prod or when logging level is too high
        # Display system message


ZDIALOG INTEGRATION (Week 6.5 Preparation)

Current Implementation (Simple):
    - Basic field collection (text input only)
    - No schema validation
    - No field type support (checkbox, select, etc.)
    - No validation feedback

Note: For advanced form features (schema validation, field types, validation feedback),
      use zcli.dialog.handle() from the zDialog subsystem (L2_Core.j_zDialog).


USAGE EXAMPLES

1. Display Complete Session State:
    ```python
    # Show all session information
    zcli.display.zEvents.zSystem.zSession(zcli.session)
    
    # Output (Terminal):
    # ══════════════════════════ View zSession ═══════════════════════════
    # zSession_ID: abc123-def456
    # zMode: Terminal
    # 
    # zMachine:
    #   os: macOS
    #   hostname: dev-machine
    #   deployment: dev
    #   ...
    # 
    # zAuth:
    #   Active Context: zSession
    #   ID: 12345
    #   Username: admin
    #   Role: admin
    # 
    # zSpace: /Users/dev/project
    # zVaFolder: /Users/dev/project/app.yaml
    # Press Enter to continue...
    ```

2. Display Navigation Breadcrumbs:
    ```python
    # Show navigation trail
    zcli.display.zEvents.zSystem.zCrumbs(zcli.session)
    
    # Output (Terminal):
    # zCrumbs:
    #   file[Main > Setup > Config]
    #   vafile[App > Database > Users]
    #   block[^Root* > User Management]
    ```

3. Interactive Menu Selection:
    ```python
    # Display menu with user selection
    menu_items = [
        (1, "Create New User"),
        (2, "List Users"),
        (3, "Delete User"),
        (4, "Exit")
    ]
    choice = zcli.display.zEvents.zSystem.zMenu(
        menu_items=menu_items,
        prompt="Select an action:",
        return_selection=True
    )
    # Returns: "Create New User" (user selected 1)
    ```


THREAD SAFETY

Instance is thread-safe (read-only access to parent display and session).
All state is stored in zCLI session dict, not in zSystem.


MODULE CONSTANTS

See below for 60+ module-level constants defining event names, dict keys,
messages, colors, styles, zMachine keys, and default values.
"""

from typing import Any, Optional, Dict, Union, List, Tuple
from pathlib import Path

# Import SESSION_KEY_* constants from zConfig (17 constants)
# Note: Some constants imported for documentation (module docstring) but not yet used in code
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZS_ID,              # "zS_id"
    SESSION_KEY_ZMODE,              # "zMode"
    SESSION_KEY_ZMACHINE,           # "zMachine"
    SESSION_KEY_ZAUTH,              # "zAuth"
    SESSION_KEY_ZSPACE,         # "zSpace"
    SESSION_KEY_ZVAFOLDER,          # "zVaFolder"
    SESSION_KEY_ZVAFILE,        # "zVaFile"
    SESSION_KEY_ZBLOCK,             # "zBlock"
    SESSION_KEY_ZCRUMBS,            # "zCrumbs"
    SESSION_KEY_ZCACHE,             # "zCache" - NOW USED for cache display
    ZCACHE_KEY_SYSTEM,              # "system_cache" - System-level cache
    ZCACHE_KEY_PINNED,              # "pinned_cache" - Pinned items
    ZCACHE_KEY_SCHEMA,              # "schema_cache" - Database schemas
    ZCACHE_KEY_PLUGIN,              # "plugin_cache" - Loaded plugins
    SESSION_KEY_WIZARD_MODE,        # "wizard_mode" - documented for future use  # noqa: F401
    SESSION_KEY_ZSPARK,             # "zSpark" - documented for future use  # noqa: F401
    SESSION_KEY_VIRTUAL_ENV,        # "virtual_env" - documented for future use  # noqa: F401
    SESSION_KEY_SYSTEM_ENV,         # "system_env" - documented for future use  # noqa: F401
    SESSION_KEY_ZLOGGER,            # "zLogger" - documented for future use  # noqa: F401
    SESSION_KEY_ZTRACEBACK,         # "zTraceback" - documented for future use  # noqa: F401
    SESSION_KEY_LOGGER_INSTANCE,    # "logger_instance" - documented for future use  # noqa: F401
    SESSION_KEY_ZVARS,              # "zVars" - User-defined variables
    SESSION_KEY_ZSHORTCUTS          # "zShortcuts" - File shortcuts
)

# Import ZAUTH_KEY_* constants from zConfig (13 constants)
# Note: Some constants imported for documentation (module docstring) but not yet used in code
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    ZAUTH_KEY_ZSESSION,             # "zSession"
    ZAUTH_KEY_APPLICATIONS,         # "applications"
    ZAUTH_KEY_ACTIVE_APP,           # "active_app"
    ZAUTH_KEY_AUTHENTICATED,        # "authenticated" - documented for future use  # noqa: F401
    ZAUTH_KEY_ID,                   # "id"
    ZAUTH_KEY_USERNAME,             # "username"
    ZAUTH_KEY_ROLE,                 # "role"
    ZAUTH_KEY_API_KEY,              # "api_key" - documented for future use  # noqa: F401
    ZAUTH_KEY_ACTIVE_CONTEXT,       # "active_context"
    ZAUTH_KEY_DUAL_MODE,            # "dual_mode"
    CONTEXT_ZSESSION,               # "zSession"
    CONTEXT_APPLICATION,            # "application"
    CONTEXT_DUAL                    # "dual"
)

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import try_gui_event

# Import constants from centralized module
from ..display_constants import (
    # Event Names (Internal)
    _EVENT_ZSESSION,
    _EVENT_ZCONFIG,
    _EVENT_ZCRUMBS,
    _EVENT_ZMENU,
    _EVENT_ZDASH,
    _EVENT_ZDIALOG,
    # JSON Keys (Internal)
    _KEY_SESSION,
    _KEY_BREAK,
    _KEY_BREAK_MESSAGE,
    _KEY_CRUMBS,
    _KEY_MENU,
    _KEY_PROMPT,
    _KEY_RETURN_SELECTION,
    _KEY_CONTEXT,
    _KEY_MODEL,
    _KEY_FIELDS,
    # Messages (Internal)
    _MSG_NO_SESSION,
    _MSG_VIEW_ZSESSION,
    _MSG_ZCRUMBS_HEADER,
    _MSG_DEFAULT_MENU_PROMPT,
    _MSG_FORM_INPUT,
    _MSG_FORM_COMPLETE,
    _MSG_PRESS_ENTER,
    _MSG_TOOL_PREFERENCES,
    _MSG_SYSTEM,
    _MSG_ZMACHINE_SECTION,
    _MSG_ZAUTH_SECTION,
    _MSG_ACTIVE_CONTEXT,
    _MSG_DUAL_MODE_INDICATOR,
    _MSG_AUTHENTICATED_APPS,
    # Colors (PUBLIC API)
    COLOR_MAIN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_CYAN,
    COLOR_RESET,
    # Styles (PUBLIC API)
    STYLE_FULL,
    STYLE_SINGLE,
    STYLE_WAVE,
    STYLE_NUMBERED,
    # Public Defaults
    DEFAULT_INDENT,
    DEFAULT_STYLE,
    # Internal Constants
    _DEFAULT_DEPLOYMENT,
    _ZMACHINE_KEY_OS,
    _ZMACHINE_KEY_HOSTNAME,
    _ZMACHINE_KEY_ARCHITECTURE,
    _ZMACHINE_KEY_PYTHON_VERSION,
    _ZMACHINE_KEY_DEPLOYMENT,
    _ZMACHINE_KEY_ROLE,
    _ZMACHINE_KEY_BROWSER,
    _ZMACHINE_KEY_IDE,
    _ZMACHINE_KEY_SHELL,
    _ZMACHINE_KEY_CPU_CORES,
    _ZMACHINE_KEY_MEMORY_GB,
    _ZMACHINE_KEY_ZCLI_VERSION,
    _ZMACHINE_IDENTITY_FIELDS,
    _ZMACHINE_TOOL_FIELDS,
    _ZMACHINE_SYSTEM_FIELDS,
    _FORMAT_BREADCRUMB_SEPARATOR,
    _FORMAT_CRUMB_SCOPE,
    _FORMAT_MENU_ITEM,
    _FORMAT_FIELD_PROMPT,
    _FORMAT_FIELD_NEWLINE,
    _FORMAT_FIELD_LABEL_INDENT,
    _FORMAT_TOOL_FIELD_INDENT,
    _LABEL_ZSESSION_ID,
    _LABEL_ZMODE,
    _LABEL_ZCLI_VERSION,
    _DEPLOYMENT_MODE_DEV,
    _DEPLOYMENT_MODE_PROD,
)

# Local constants (aliasing for backward compat within this module)
_EVENT_ZSESSION = _EVENT_ZSESSION
_EVENT_ZCONFIG = _EVENT_ZCONFIG
_EVENT_ZCRUMBS = _EVENT_ZCRUMBS
_EVENT_ZMENU = _EVENT_ZMENU
_EVENT_ZDASH = _EVENT_ZDASH
_EVENT_ZDIALOG = _EVENT_ZDIALOG
_KEY_SESSION = _KEY_SESSION
_KEY_BREAK = _KEY_BREAK
_KEY_BREAK_MESSAGE = _KEY_BREAK_MESSAGE
_KEY_CRUMBS = _KEY_CRUMBS
_KEY_MENU = _KEY_MENU
_KEY_PROMPT = _KEY_PROMPT
_KEY_RETURN_SELECTION = _KEY_RETURN_SELECTION
_KEY_CONTEXT = _KEY_CONTEXT
_KEY_MODEL = _KEY_MODEL
_KEY_FIELDS = _KEY_FIELDS
_MSG_NO_SESSION = _MSG_NO_SESSION
_MSG_VIEW_ZSESSION = _MSG_VIEW_ZSESSION
_MSG_ZCRUMBS_HEADER = _MSG_ZCRUMBS_HEADER
DEFAULT_MENU_PROMPT = _MSG_DEFAULT_MENU_PROMPT
_MSG_FORM_INPUT = _MSG_FORM_INPUT
_MSG_FORM_COMPLETE = _MSG_FORM_COMPLETE
_MSG_PRESS_ENTER = _MSG_PRESS_ENTER
_MSG_TOOL_PREFERENCES = _MSG_TOOL_PREFERENCES
_MSG_SYSTEM = _MSG_SYSTEM
_MSG_ZMACHINE_SECTION = _MSG_ZMACHINE_SECTION
_MSG_ZAUTH_SECTION = _MSG_ZAUTH_SECTION
_MSG_ACTIVE_CONTEXT = _MSG_ACTIVE_CONTEXT
_MSG_DUAL_MODE_INDICATOR = _MSG_DUAL_MODE_INDICATOR
_MSG_AUTHENTICATED_APPS = _MSG_AUTHENTICATED_APPS
_DEFAULT_DEPLOYMENT = _DEFAULT_DEPLOYMENT
_ZMACHINE_KEY_OS = _ZMACHINE_KEY_OS
_ZMACHINE_KEY_HOSTNAME = _ZMACHINE_KEY_HOSTNAME
_ZMACHINE_KEY_ARCHITECTURE = _ZMACHINE_KEY_ARCHITECTURE
_ZMACHINE_KEY_PYTHON_VERSION = _ZMACHINE_KEY_PYTHON_VERSION
_ZMACHINE_KEY_DEPLOYMENT = _ZMACHINE_KEY_DEPLOYMENT
_ZMACHINE_KEY_ROLE = _ZMACHINE_KEY_ROLE
_ZMACHINE_KEY_BROWSER = _ZMACHINE_KEY_BROWSER
_ZMACHINE_KEY_IDE = _ZMACHINE_KEY_IDE
_ZMACHINE_KEY_SHELL = _ZMACHINE_KEY_SHELL
_ZMACHINE_KEY_CPU_CORES = _ZMACHINE_KEY_CPU_CORES
_ZMACHINE_KEY_MEMORY_GB = _ZMACHINE_KEY_MEMORY_GB
_ZMACHINE_KEY_ZCLI_VERSION = _ZMACHINE_KEY_ZCLI_VERSION
_ZMACHINE_IDENTITY_FIELDS = _ZMACHINE_IDENTITY_FIELDS
_ZMACHINE_TOOL_FIELDS = _ZMACHINE_TOOL_FIELDS
_ZMACHINE_SYSTEM_FIELDS = _ZMACHINE_SYSTEM_FIELDS
_FORMAT_BREADCRUMB_SEPARATOR = _FORMAT_BREADCRUMB_SEPARATOR
_FORMAT_CRUMB_SCOPE = _FORMAT_CRUMB_SCOPE
_FORMAT_MENU_ITEM = _FORMAT_MENU_ITEM
_FORMAT_FIELD_PROMPT = _FORMAT_FIELD_PROMPT
_FORMAT_FIELD_NEWLINE = _FORMAT_FIELD_NEWLINE
_FORMAT_FIELD_LABEL_INDENT = _FORMAT_FIELD_LABEL_INDENT
_FORMAT_TOOL_FIELD_INDENT = _FORMAT_TOOL_FIELD_INDENT
_LABEL_ZSESSION_ID = _LABEL_ZSESSION_ID
_LABEL_ZMODE = _LABEL_ZMODE
_LABEL_ZCLI_VERSION = _LABEL_ZCLI_VERSION
_DEPLOYMENT_MODE_DEV = _DEPLOYMENT_MODE_DEV
_DEPLOYMENT_MODE_PROD = _DEPLOYMENT_MODE_PROD
DEFAULT_BREAK_MESSAGE = _MSG_PRESS_ENTER

# Session Field Lists (defined here as it references SESSION_KEY_* from zConfig)
SESSION_WORKSPACE_FIELDS = [
    SESSION_KEY_ZSPACE,
    SESSION_KEY_ZVAFOLDER,
    SESSION_KEY_ZVAFILE,
    SESSION_KEY_ZBLOCK
]

# zSystem Class

class zSystem:
    """
    zCLI System Introspection & Navigation UI Events (Dual-Mode Terminal + Bifrost).
    
    Provides user interface presentation for zCLI's core system structures across
    both Terminal and Bifrost (GUI) modes. This is the ONLY event package that
    operates at the system level, directly displaying zCLI's internal state.
    
    System Integration:
        zCLI core → zSystem → zDisplay → Terminal/Bifrost
    
    Session Integration (17 SESSION_KEY_* constants):
        Uses standardized constants from zConfig for safe, refactor-proof access
        to zSession dict (zS_id, zMode, zMachine, zAuth, zSpace, etc.)
    
    zAuth Integration (13 ZAUTH_KEY_* constants + three-tier model):
        Displays authentication state with full awareness of:
        - Layer 1: zSession auth (internal zCLI users)
        - Layer 2: Application auth (external app users, multi-app)
        - Layer 3: Dual-auth (simultaneous contexts)
    
    zMachine Integration (12 ZMACHINE_KEY_* constants):
        Displays machine configuration in organized sections:
        - Identity & Deployment (os, hostname, deployment, role)
        - Tool Preferences (browser, ide, shell)
        - System Capabilities (cpu_cores, memory_gb)
        - zCLI Version
    
    Composition:
        Depends on: BasicOutputs (text/header), Signals (status messages), BasicInputs (selection)
        Most dependencies of any event package (3 packages)
    
    Methods:
        Core System Displays:
            - zSession():   Display complete session state
            - zCrumbs():    Display navigation breadcrumb trails
            - zMenu():      Display interactive menu (with optional selection)
            - zDialog():    Display form dialog and collect input
            - zDeclare():   Display system declaration (log-level aware)
        
        Helper Methods (Private):
            - _try_gui_event():     DRY helper for GUI dispatch
            - _output_text():       DRY helper for text output
            - _get_color():         DRY helper for color lookup
            - _display_field():     Display labeled field
            - _display_section():   Display section title
            - _display_zmachine():  Display zMachine structure
            - _display_zauth():     Display zAuth state (three-tier aware)
            - _should_show_sysmsg(): Check logging level for message display
    
    Dual-Mode Pattern:
        All methods follow GUI-first, Terminal-fallback:
        1. Try Bifrost (GUI) via send_gui_event()
        2. If GUI succeeds, return immediately
        3. If GUI unavailable, fall back to Terminal output
    
    Usage:
        # Display session
        zcli.display.zEvents.zSystem.zSession(zcli.session)
        
        # Interactive menu
        choice = zcli.display.zEvents.zSystem.zMenu(
            menu_items=[(1, "Create"), (2, "Read")],
            return_selection=True
        )
    """
    
    # Class-level type declarations
    display: Any                           # Parent zDisplay instance
    zPrimitives: Any                       # Primitives for I/O operations
    zColors: Any                           # Colors for Terminal output
    BasicOutputs: Optional[Any]            # BasicOutputs event package (set after init)
    Signals: Optional[Any]                 # Signals event package (set after init)
    BasicInputs: Optional[Any]             # BasicInputs event package (set after init)

    def __init__(self, display_instance: Any) -> None:
        """
        Initialize zSystem with reference to parent zDisplay instance.
        
        Args:
            display_instance: Parent zDisplay instance (provides access to
                            zPrimitives, zColors, session, and will provide
                            BasicOutputs, Signals, BasicInputs after zEvents
                            initialization completes)
        
        Returns:
            None
        
        Notes:
            - BasicOutputs, Signals, BasicInputs are set to None initially
            - They will be populated by zEvents.__init__ after all event
              packages are instantiated (to avoid circular dependencies)
            - This is part of zDisplay's cross-reference architecture
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        # Get references to other packages for composition
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self.Signals = None  # Will be set after zEvents initialization
        self.BasicInputs = None  # Will be set after zEvents initialization


    # HELPER METHODS (Private - DRY Refactoring)

    def _try_gui_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """
        Try to send GUI event to Bifrost mode (DRY helper).
        
        DEPRECATED: This method now delegates to Tier 0 infrastructure helper.
        Use try_gui_event(display, event_name, data) directly for new code.
        
        Args:
            event_name: WebSocket event name (e.g., _EVENT_ZSESSION)
            data: Event data dictionary to send to frontend
        
        Returns:
            bool: True if GUI mode succeeded (message sent), False if Terminal mode
        
        Usage:
            if self._try_gui_event(_EVENT_ZSESSION, {_KEY_SESSION: session_data}):
                return  # GUI handled it
            # Fall back to Terminal mode
        """
        # Delegate to Tier 0 infrastructure helper
        return try_gui_event(self.display, event_name, data)

    def _output_text(
        self, 
        content: str, 
        indent: int = 0, 
        break_after: bool = False
    ) -> None:
        """
        Output text if BasicOutputs package available (DRY helper).
        
        Args:
            content: Text content to display
            indent: Indentation level (default: 0)
            break_after: Add line break after text (default: False)
        
        Returns:
            None
        
        Usage:
            self._output_text(_MSG_NO_SESSION, break_after=False)
        """
        if self.BasicOutputs:
            self.BasicOutputs.text(content, indent=indent, break_after=break_after)

    def _get_color(self, color_name: str) -> str:
        """
        Get color code from zColors with fallback to RESET (DRY helper).
        
        Args:
            color_name: Color attribute name (e.g., "GREEN", "YELLOW")
        
        Returns:
            str: ANSI color code from zColors, or RESET if not found
        
        Usage:
            color_code = self._get_color(COLOR_GREEN)
        """
        return getattr(self.zColors, color_name, self.zColors.RESET)


    # PUBLIC METHODS (System Display Events)

    def zDeclare(
        self, 
        label: str, 
        color: Optional[str] = None, 
        indent: int = DEFAULT_INDENT, 
        style: Optional[str] = DEFAULT_STYLE
    ) -> None:
        """
        Display system declaration/message with log-level conditioning and auto-style.
        
        System messages (zDeclare) are displayed only when appropriate based on:
        - Logging level (via zcli.logger.should_show_sysmsg())
        - Debug flag (legacy: session["debug"])
        - Deployment mode (dev → show, prod → hide)
        
        Args:
            label: Declaration text to display
            color: Color name (default: display.mycolor or "RESET")
            indent: Indentation level (default: 0)
            style: Header style ("full", "single", "wave", or None for auto-select)
        
        Returns:
            None
        
        Style Auto-Selection:
            indent 0 → "full" (full-width header)
            indent 1 → "single" (single-line header)
            indent 2+ → "wave" (wave-style header)
        
        Terminal Mode:
            Renders colored header via BasicOutputs.header()
        
        Bifrost Mode:
            N/A (zDeclare is Terminal-only, system messages shown in console)
        
        Usage:
            # Display main system message
            display.zEvents.zSystem.zDeclare("Session Initialized", color="MAIN")
            
            # Display indented sub-message
            display.zEvents.zSystem.zDeclare("Loading config...", indent=1)
        
        Notes:
            - Respects logging level (won't display in prod or high log levels)
            - Uses display.mycolor if no color specified (preserves user preference)
            - Composes BasicOutputs.header() for actual rendering
        """
        # Check if system messages should be displayed based on logging level
        if not self._should_show_sysmsg():
            return

        # zDeclare is Terminal-only: skip in zBifrost/GUI mode
        # System messages are for debug flow visualization in terminal, not user-facing UI
        if self.zPrimitives and self.zPrimitives._is_gui_mode():
            return

        # Use display's mycolor if no color specified
        if color is None:
            color = getattr(self.display, 'mycolor', COLOR_RESET)

        # Auto-select style based on indent if not specified
        if style is None:
            if indent == 0:
                style = STYLE_FULL
            elif indent == 1:
                style = STYLE_SINGLE
            else:  # indent >= 2
                style = STYLE_WAVE

        # Compose: use header event to do the actual rendering
        if self.BasicOutputs:
            self.BasicOutputs.header(label, color, indent, style)

    def _format_path_as_zpath(self, path_value: str, session_data: Dict[str, Any]) -> str:
        """
        Convert absolute path to zPath notation for user-friendly display.
        
        IMPORTANT: Preserves existing zPath notation (@., ~., ~zMachine) as-is.
        Only converts absolute filesystem paths to zPath equivalents.
        
        Args:
            path_value: Path (may be zPath notation or absolute path)
            session_data: Session dict (for getting user data dir from zMachine)
        
        Returns:
            str: zPath notation if applicable, otherwise absolute path
        
        Conversion Rules (ONLY for absolute paths):
            /Users/user/Library/Application Support/zolo-zcli → ~zMachine
            /Users/user/Library/Application Support/zolo-zcli/zConfigs → ~zMachine.zConfigs
            /Users/user/Projects → ~.Projects
            /Users/user → ~
        
        Preservation Rules:
            @.zUIs → @.zUIs (PRESERVED - workspace-relative)
            ~zMachine → ~zMachine (PRESERVED - already zPath)
            ~.Projects → ~.Projects (PRESERVED - already zPath)
        """
        if not path_value or path_value == "None":
            return path_value
        
        # PRESERVE existing zPath notation (don't convert it)
        if any(path_value.startswith(prefix) for prefix in ["@.", "~.", "~zMachine", "zMachine."]):
            return path_value
        
        # Only convert absolute paths to zPath notation
        try:
            abs_path_obj = Path(path_value).resolve()
            home = Path.home()
            
            # Try zMachine path first (user data directory)
            try:
                zmachine = session_data.get(SESSION_KEY_ZMACHINE, {})
                user_data_dir_str = zmachine.get("user_data_dir", "")
                
                # Only process if user_data_dir is actually set (avoid Path("").resolve() bug!)
                if user_data_dir_str:
                    user_data_dir = Path(user_data_dir_str).resolve()
                    
                    if abs_path_obj == user_data_dir:
                        return "~zMachine"
                    elif abs_path_obj.is_relative_to(user_data_dir):
                        rel_path = abs_path_obj.relative_to(user_data_dir)
                        return f"~zMachine.{str(rel_path).replace('/', '.')}"
            except (ValueError, AttributeError):
                pass
            
            # Try home-relative path (~.)
            if abs_path_obj == home:
                return "~"
            elif abs_path_obj.is_relative_to(home):
                rel_path = abs_path_obj.relative_to(home)
                return f"~.{str(rel_path).replace('/', '.')}"
            
            # Return absolute path if no zPath match
            return path_value
        except Exception:
            # If any error, return original
            return path_value

    def zSession(
        self, 
        session_data: Optional[Dict[str, Any]], 
        break_after: bool = True, 
        break_message: Optional[str] = None
    ) -> None:
        """
        Display complete zCLI session state (Terminal or Bifrost mode).
        
        Displays all core session fields using SESSION_KEY_* constants for
        safe, refactor-proof access:
        - zSession ID, zMode
        - zMachine (machine configuration)
        - zAuth (authentication state - three-tier aware)
        - zSpace, zVaFolder, zVaFile, zBlock
        - zCache (4-tier caching system with item counts)
        - zVars & zShortcuts (unified aliasing system)
        
        Args:
            session_data: zCLI session dictionary (zcli.session)
            break_after: Add "Press Enter" prompt at end (default: True)
            break_message: Custom break message (default: "Press Enter to continue...")
        
        Returns:
            None
        
        Bifrost Mode:
            - Sends _EVENT_ZSESSION event with full session data
            - Frontend displays interactive session viewer
            - Returns immediately
        
        Terminal Mode:
            - Displays formatted session structure:
              1. Header: "View zSession"
              2. Core fields: zSession_ID, zMode
              3. zMachine section (if present)
              4. Workspace fields (zSpace, zVaFolder, zVaFile, zBlock)
              5. zAuth section (if present) - three-tier aware
              6. zCache section (4-tier caching with item counts)
              7. zVars & Shortcuts section (if present)
              8. Optional break prompt
        
        Usage:
            # Display full session
            zcli.display.zEvents.zSystem.zSession(zcli.session)
            
            # Display without break prompt
            zcli.display.zEvents.zSystem.zSession(zcli.session, break_after=False)
            
            # Custom break message
            zcli.display.zEvents.zSystem.zSession(
                zcli.session,
                break_message="Review complete. Press Enter..."
            )
        
        Notes:
            - Uses SESSION_KEY_* and ZCACHE_KEY_* constants for all session access
            - Composes _display_zmachine(), _display_zauth(), _display_zcache() for subsections
            - Shows None for unset workspace fields (user visibility)
            - Handles missing session data gracefully
        """
        # Try Bifrost (GUI) mode first - send clean event
        if self._try_gui_event(_EVENT_ZSESSION, {
            _KEY_SESSION: session_data,
            _KEY_BREAK: break_after,
            _KEY_BREAK_MESSAGE: break_message
        }):
            return  # GUI event sent successfully

        # Terminal mode - display session using composed events
        if not session_data:
            self._output_text(_MSG_NO_SESSION, break_after=False)
            return

        # Header
        self.zDeclare(_MSG_VIEW_ZSESSION, color=COLOR_MAIN, indent=0)

        # Core session fields
        self._display_field(_LABEL_ZSESSION_ID, session_data.get(SESSION_KEY_ZS_ID))
        self._display_field(_LABEL_ZMODE, session_data.get(SESSION_KEY_ZMODE))

        # zMachine section
        zMachine = session_data.get(SESSION_KEY_ZMACHINE, {})
        if zMachine:
            self._display_zmachine(zMachine)

        # Session fields (show all, including None values)
        self._output_text("", break_after=False)
        for field_key in SESSION_WORKSPACE_FIELDS:
            value = session_data.get(field_key)
            # Extract field name from constant (e.g., SESSION_KEY_ZSPACE → "zSpace")
            field_name = field_key  # Constants match the actual field names
            
            # Convert path fields to zPath notation for user-friendly display
            if field_key in (SESSION_KEY_ZSPACE, SESSION_KEY_ZVAFOLDER) and value:
                value = self._format_path_as_zpath(value, session_data)
            
            # Display all fields, including None (user wants to see what's not set)
            self._display_field(field_name, value if value is not None else "None")

        # zAuth section
        zAuth = session_data.get(SESSION_KEY_ZAUTH, {})
        if zAuth:
            self._display_zauth(zAuth)

        # zCache section (4-tier caching system)
        zCache = session_data.get(SESSION_KEY_ZCACHE, {})
        if zCache:
            self._display_zcache(zCache)

        # zVars and zShortcuts section (unified aliasing system)
        zvars = session_data.get(SESSION_KEY_ZVARS, {})
        zshortcuts = session_data.get(SESSION_KEY_ZSHORTCUTS, {})
        if zvars or zshortcuts:
            self._display_zshortcuts(zvars, zshortcuts)

        # Optional break at the end
        if break_after:
            self._output_text("", break_after=False)
            # Display break message and pause (break_after adds the actual pause)
            if break_message:
                self._output_text(break_message, break_after=True)
            else:
                # Use BasicOutputs text() with break_after for standard prompt
                self._output_text("", break_after=True)

    def zConfig(
        self,
        config_data: Optional[Dict[str, Any]] = None,
        break_after: bool = True,
        break_message: Optional[str] = None
    ) -> None:
        """
        Display zConfig machine and environment configuration (Terminal or Bifrost mode).
        
        Displays complete zConfig state including machine configuration (OS, hardware,
        capabilities) and environment configuration (deployment, role, venv status).
        
        Args:
            config_data: Dict with 'machine' and 'environment' keys, or None to use zcli.config
            break_after: Add "Press Enter" prompt at end (default: True)
            break_message: Custom break message (default: "Press Enter to continue...")
        
        Returns:
            None
        
        Bifrost Mode:
            - Sends _EVENT_ZCONFIG event with config data
            - Frontend displays interactive config viewer
            - Returns immediately
        
        Terminal Mode:
            - Displays formatted config structure:
              1. Machine Configuration header
              2. Machine fields (os, hostname, architecture, etc.)
              3. Environment Configuration header
              4. Environment fields (deployment, role, venv, etc.)
              5. Optional break prompt
        
        Usage:
            # Display full config (auto-fetches from zcli.config)
            zcli.display.zConfig()
            
            # Display with custom config data
            zcli.display.zConfig({
                'machine': {...},
                'environment': {...}
            })
            
            # Display without break prompt
            zcli.display.zConfig(break_after=False)
        
        Notes:
            - If config_data is None, assumes display is bound to zcli and uses zcli.config
            - Shows all configuration keys in sorted order
            - Handles missing values gracefully
        """
        # Try Bifrost (GUI) mode first - send clean event
        if self._try_gui_event(_EVENT_ZCONFIG, {
            "config": config_data,
            _KEY_BREAK: break_after,
            _KEY_BREAK_MESSAGE: break_message
        }):
            return  # GUI event sent successfully

        # Terminal mode - display config using composed events
        if not config_data:
            self._output_text("No configuration data available", break_after=False)
            return

        # Machine Configuration section
        machine = config_data.get('machine', {})
        if machine:
            self._output_text("", break_after=False)
            self.BasicOutputs.header(" zConfig: Machine Configuration", color="CONFIG", style="full")
            self._output_text("", break_after=False)
            
            for key, value in sorted(machine.items()):
                # Format value for display
                if isinstance(value, bool):
                    value_str = "True" if value else "False"
                elif isinstance(value, (dict, list)):
                    value_str = str(value)
                    if len(value_str) > 60:
                        value_str = value_str[:57] + "..."
                elif value is None:
                    value_str = "None"
                else:
                    value_str = str(value)
                
                self._display_field(key, value_str)

        # Environment Configuration section
        environment = config_data.get('environment', {})
        if environment:
            self._output_text("", break_after=False)
            self.BasicOutputs.header(" zConfig: Environment Configuration", color="CONFIG", style="full")
            self._output_text("", break_after=False)
            
            for key, value in sorted(environment.items()):
                # Format value for display
                if isinstance(value, bool):
                    value_str = "True" if value else "False"
                elif isinstance(value, (dict, list)):
                    value_str = str(value)
                    if len(value_str) > 60:
                        value_str = value_str[:57] + "..."
                elif value is None:
                    value_str = "None"
                else:
                    value_str = str(value)
                
                self._display_field(key, value_str)

        # Break prompt (if requested)
        if break_after:
            self._output_text("", break_after=False)
            if break_message:
                self._output_text(break_message, break_after=True)
            else:
                # Use BasicOutputs text() with break_after for standard prompt
                self._output_text("", break_after=True)

    def zCrumbs(self, session_data: Optional[Dict[str, Any]]) -> None:
        """
        Display breadcrumb navigation trail showing scope paths (Terminal or Bifrost mode).
        
        Breadcrumbs show the navigation trail through different scopes (file, vafile, block).
        Uses SESSION_KEY_ZCRUMBS for safe session access.
        
        Args:
            session_data: zCLI session dictionary containing zCrumbs
        
        Returns:
            None
        
        Bifrost Mode:
            - Sends _EVENT_ZCRUMBS event with crumbs data
            - Frontend displays interactive breadcrumb UI
            - Returns immediately
        
        Terminal Mode:
            - Displays formatted breadcrumb trails:
              zCrumbs:
                file[Main > Setup > Config]
                vafile[App > Database > Users]
                block[^Root* > User Management]
        
        Structure:
            session[SESSION_KEY_ZCRUMBS] = {
                "file": ["Main", "Setup", "Config"],
                "vafile": ["App", "Database", "Users"],
                "block": ["^Root*", "User Management"]
            }
        
        Usage:
            # Display navigation breadcrumbs
            zcli.display.zEvents.zSystem.zCrumbs(zcli.session)
        
        Notes:
            - Uses SESSION_KEY_ZCRUMBS constant for session access
            - Joins trail items with " > " separator
            - Displays in "scope[path]" format
        """
        # Try Bifrost (GUI) mode first - send clean event
        z_crumbs = session_data.get(SESSION_KEY_ZCRUMBS, {}) if session_data else {}

        if self._try_gui_event(_EVENT_ZCRUMBS, {_KEY_CRUMBS: z_crumbs}):
            return  # GUI event sent successfully

        # Terminal mode - display breadcrumbs using composed events
        if not z_crumbs:
            return

        # Phase 0.5: Use centralized banner method to filter out metadata (_context, _depth_map)
        # This ensures only user-facing trails are displayed, not internal architecture
        if hasattr(self.display, 'zcli') and hasattr(self.display.zcli, 'navigation') and hasattr(self.display.zcli.navigation, 'breadcrumbs'):
            # DRY: Reuse breadcrumbs.zCrumbs_banner() which handles enhanced format correctly
            crumbs_display = self.display.zcli.navigation.breadcrumbs.zCrumbs_banner()
        else:
            # Fallback for systems without navigation subsystem (backward compatible)
            crumbs_display = {}
            # Handle enhanced format: check if 'trails' key exists (Phase 0.5+)
            trails_dict = z_crumbs.get('trails', z_crumbs)
            for scope, trail in trails_dict.items():
                # Skip internal metadata keys (_context, _depth_map)
                if scope.startswith('_'):
                    continue
                # Only process actual trail lists
                if isinstance(trail, list):
                    path = _FORMAT_BREADCRUMB_SEPARATOR.join(trail) if trail else ""
                    crumbs_display[scope] = path

        # Display breadcrumbs using BasicOutputs.text()
        self._output_text("", break_after=False)
        self._output_text(_MSG_ZCRUMBS_HEADER, break_after=False)
        for scope, path in crumbs_display.items():
            content = _FORMAT_CRUMB_SCOPE.format(scope=scope, path=path)
            self._output_text(content, break_after=False)

    def zMenu(
        self, 
        menu_items: Optional[List[Tuple[Any, str]]], 
        prompt: str = DEFAULT_MENU_PROMPT, 
        return_selection: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """
        Display menu options and optionally collect user selection (Terminal or Bifrost mode).
        
        Supports two modes:
        - Display-only: Show menu items without interaction
        - Interactive: Show menu and return user's selection
        
        Args:
            menu_items: List of (number, label) tuples, e.g., [(1, "Create"), (2, "Read")]
            prompt: Menu prompt text (default: "Select an option:")
            return_selection: Enable interactive selection (default: False)
        
        Returns:
            Optional[Union[str, List[str]]]: 
                - None if display-only mode or GUI mode
                - Selected label(s) if interactive Terminal mode
        
        Bifrost Mode:
            - Sends _EVENT_ZMENU event with menu data
            - Frontend displays interactive menu UI
            - Returns None (selection handled via WebSocket callback)
        
        Terminal Mode:
            - Display-only: Shows numbered menu items
            - Interactive: Composes BasicInputs.selection() for user input
        
        Usage:
            # Display-only menu
            menu = [(1, "Create"), (2, "Read"), (3, "Update"), (4, "Delete")]
            display.zEvents.zSystem.zMenu(menu)
            
            # Interactive menu
            menu = [(1, "Create"), (2, "Read"), (3, "Update")]
            choice = display.zEvents.zSystem.zMenu(
                menu_items=menu,
                prompt="Select an action:",
                return_selection=True
            )
            # Returns: "Create" (if user selected 1)
        
        Notes:
            - Menu items are (number, label) tuples
            - Interactive mode uses STYLE_NUMBERED for consistency
            - Composes BasicInputs.selection() for actual selection logic
        """
        # Try Bifrost (GUI) mode first - send clean event
        if self._try_gui_event(_EVENT_ZMENU, {
            _KEY_MENU: menu_items,
            _KEY_PROMPT: prompt,
            _KEY_RETURN_SELECTION: return_selection
        }):
            return None  # GUI event sent successfully

        # Terminal mode - compose BasicInputs.selection()
        if not menu_items:
            return None

        # Extract just the labels for selection
        options = [label for _, label in menu_items]

        # If interactive, use selection event
        if return_selection and self.BasicInputs:
            return self.BasicInputs.selection(
                prompt=prompt,
                options=options,
                multi=False,
                style=STYLE_NUMBERED
            )
        else:
            # Display-only mode: just show the menu
            self._output_text("", break_after=False)  # Blank line
            for number, label in menu_items:
                content = _FORMAT_MENU_ITEM.format(index=number, label=label)
                self._output_text(content, break_after=False)
            return None

    def zDash(
        self,
        folder: str,
        sidebar: List[str],
        default: Optional[str] = None,
        _zcli: Optional[Any] = None,
        **kwargs  # NEW v1.5.12: Accept _context and other params
    ) -> Optional[str]:
        """
        Display dashboard with interactive panel navigation (Terminal or Bifrost mode).
        
        Built-in Gate Behavior (Terminal):
        - Runs in interactive loop until user enters "done"
        - Allows panel switching between sidebar items
        - Acts as built-in gate (no need for ! modifier)
        
        Terminal-First Approach:
        - Auto-navigates to default panel on first load
        - Shows interactive menu after each panel render
        - "done" command exits dashboard and continues execution
        
        Args:
            folder: Base folder for panel discovery (e.g., "@.UI.zAccount")
            sidebar: List of panel names (e.g., ["Overview", "Apps", "Billing"])
            default: Default panel to navigate to (defaults to first in sidebar)
            _zcli: zCLI instance for zLoader access
        
        Returns:
            Optional[str]: Last panel viewed (Terminal), None (Bifrost)
        
        Bifrost Mode:
            - Sends _EVENT_ZDASH event with dashboard structure
            - Frontend renders sidebar and content panels
            - Returns None (navigation handled via WebSocket)
        
        Terminal Mode:
            - Discovers panel metadata from folder
            - Auto-navigates to default panel immediately
            - Shows menu after panel content
            - Loops until "done" entered
            - Panel content rendered by zDispatch
        
        Usage:
            display.handle({
                "event": "zDash",
                "folder": "@.UI.zAccount",
                "sidebar": ["Overview", "Apps", "Billing", "Settings"],
                "default": "Overview"
            })
        
        Menu Commands:
            - [1-N]: Switch to panel by number
            - done: Exit dashboard (satisfies built-in gate)
        """
        # Validate sidebar
        if not sidebar:
            if hasattr(self.display, 'logger'):
                self.display.logger.warning("[zDash] No sidebar items provided")
            return None
        
        # Get zCLI instance (from display parent)
        if not _zcli:
            _zcli = getattr(self.display, 'zcli', None)
        
        if not _zcli:
            if hasattr(self.display, 'logger'):
                self.display.logger.error("[zDash] Cannot navigate without zCLI instance")
            return None
        
        logger = self.display.logger if hasattr(self.display, 'logger') else None
        
        # RBAC-FILTERED SIDEBAR: Filter panels based on user's role
        # Load each panel and check RBAC access before including in sidebar
        from zOS.L3_Abstraction.m_zWizard.zWizard_modules.wizardzRBAC import checkzRBAC_access, RBAC_ACCESS_GRANTED
        
        accessible_panels = []
        panel_metadata = {}
        
        for panel_name in sidebar:
            try:
                zLink_path = f"{folder}.zUI.{panel_name}"
                panel_file = _zcli.loader.handle(zPath=zLink_path) if hasattr(_zcli, 'loader') else {}
                
                # Get the panel's main block (should match panel_name)
                panel_block = panel_file.get(panel_name, {})
                
                # Check RBAC access for this panel
                rbac_result = checkzRBAC_access(
                    key=panel_name,
                    value=panel_block,
                    zcli=_zcli,
                    walker=None,
                    logger=logger if logger else _zcli.logger,
                    display=None  # Don't show access denied here (silent filter)
                )
                
                # Only include panel if user has access
                if rbac_result == RBAC_ACCESS_GRANTED:
                    accessible_panels.append(panel_name)
                    
                    # Cache panel metadata for menu display
                    panel_meta = panel_file.get('meta', {})
                    panel_metadata[panel_name] = {
                        'label': panel_meta.get('panel_label', panel_name),
                        'icon': panel_meta.get('panel_icon', ''),
                        'order': panel_meta.get('panel_order', 999)
                    }
                elif logger:
                    logger.debug(f"[zDash RBAC] Panel '{panel_name}' filtered out (access denied)")
                    
            except Exception as e:
                # If panel load fails, include it with default metadata (fail-open for robustness)
                if logger:
                    logger.warning(f"[zDash] Failed to load panel '{panel_name}': {e}")
                accessible_panels.append(panel_name)
                panel_metadata[panel_name] = {
                    'label': panel_name,
                    'icon': '',
                    'order': 999
                }
        
        # Update sidebar to only accessible panels
        sidebar = accessible_panels
        
        if not sidebar:
            if logger:
                logger.warning("[zDash] No accessible panels after RBAC filtering")
            return None
        
        # Determine starting panel (must be in filtered sidebar)
        current_panel = default if default in sidebar else sidebar[0]
        
        # Try Bifrost (GUI) mode - send FILTERED sidebar
        if self._try_gui_event(_EVENT_ZDASH, {
            "folder": folder,
            "sidebar": sidebar,  # RBAC-filtered sidebar
            "default": current_panel
        }):
            return None  # GUI event sent successfully
        
        # Terminal mode - interactive dashboard loop (built-in gate)
        while True:
            # 1. Load and render current panel
            zLink_path = f"{folder}.zUI.{current_panel}"
            
            if logger:
                logger.info(f"[zDash] Navigating to: {current_panel}")
            
            try:
                # Load panel file
                if not hasattr(_zcli, 'loader'):
                    if logger:
                        logger.error("[zDash] zLoader not available")
                    break
                
                panel_file = _zcli.loader.handle(zPath=zLink_path)
                panel_meta = panel_file.get('meta', {})
                
                # BUG FIX: Update session context for delta links to work correctly
                # When inside a panel file, delta links ($zBlock_2) should resolve relative to the panel file
                # Save old context to restore later
                from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZVAFILE, SESSION_KEY_ZVAFOLDER
                old_vafile = _zcli.session.get(SESSION_KEY_ZVAFILE, "")
                old_vafolder = _zcli.session.get(SESSION_KEY_ZVAFOLDER, "")
                
                # Update session to panel's file context
                _zcli.session[SESSION_KEY_ZVAFILE] = f"zUI.{current_panel}"
                _zcli.session[SESSION_KEY_ZVAFOLDER] = folder if folder and folder != "@" else "@"
                
                if logger:
                    logger.debug(f"[zDash] Session context updated for delta links:")
                    logger.debug(f"[zDash]   VaFolder: {old_vafolder} → {_zcli.session[SESSION_KEY_ZVAFOLDER]}")
                    logger.debug(f"[zDash]   VaFile: {old_vafile} → {_zcli.session[SESSION_KEY_ZVAFILE]}")
                
                # Extract panel metadata for logging
                panel_label = panel_meta.get('panel_label', current_panel)
                panel_icon = panel_meta.get('panel_icon', '')
                
                if logger:
                    logger.debug(f"[zDash] Loaded panel: {panel_icon} {panel_label}")
                
                # Get the first executable block
                panel_blocks = [k for k in panel_file.keys() if k != 'meta' and not k.startswith('_')]
                
                if not panel_blocks:
                    if logger:
                        logger.warning(f"[zDash] No executable blocks in panel: {zLink_path}")
                    break
                
                first_block = panel_blocks[0]
                if logger:
                    logger.info(f"[zDash] Executing panel block: {first_block}")
                
                # PATH 4 BREADCRUMB TRACKING: Panels get separate trail keys
                # Clear old panel keys and create new panel key
                if hasattr(_zcli, 'navigation') and hasattr(_zcli.navigation, 'breadcrumbs'):
                    breadcrumbs = _zcli.navigation.breadcrumbs
                    
                    # Clear all other panel keys (panel switching)
                    breadcrumbs._clear_other_panel_keys(current_panel, _zcli.session)
                    
                    # Create new panel key (or reuse if exists)
                    panel_key = breadcrumbs._create_panel_key(current_panel, _zcli.session)
                    
                    # Update session to point to panel context (for panel content tracking)
                    from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZBLOCK
                    old_block = _zcli.session.get(SESSION_KEY_ZBLOCK, "")
                    _zcli.session[SESSION_KEY_ZBLOCK] = f"{old_block}.{current_panel}"
                    
                    if logger:
                        logger.debug(f"[zDash] Panel context: {panel_key}")
                        logger.debug(f"[zDash] Session zBlock updated: {old_block} → {_zcli.session[SESSION_KEY_ZBLOCK]}")
                
                # Execute the block via zDispatch
                if not (hasattr(_zcli, 'dispatch') and hasattr(_zcli.dispatch, 'launcher')):
                    if logger:
                        logger.error("[zDash] zDispatch not available")
                    break
                
                # Get the block content (dict with Panel_Header, Panel_Content, etc.)
                panel_block_content = panel_file[first_block]
                
                # NEW v1.5.12: Resolve _data block BEFORE rendering panel items
                # This enables %data.* variable resolution in panel content
                panel_context = {}
                if "_data" in panel_block_content:
                    if logger:
                        logger.debug(f"[zDash] Resolving _data block for panel: {first_block}")
                    resolved_data = _zcli.dispatch.launcher._resolve_block_data(
                        panel_block_content["_data"], panel_context
                    )
                    if resolved_data:
                        panel_context["_resolved_data"] = resolved_data
                        if logger:
                            logger.debug(f"[zDash] Context enriched with {len(resolved_data)} data queries: {list(resolved_data.keys())}")
                
                # Iterate through the block's items and execute each one
                # This ensures Panel_Header, Panel_Content, etc. are all rendered
                for key, value in panel_block_content.items():
                    # Skip metadata keys like zRBAC, _data, _zClass, etc.
                    if key.startswith('_'):
                        continue
                    
                    # Check if key has modifiers (* for menu, ~ for anchor)
                    # If so, use dispatch.handle() so modifiers are detected and processed
                    if '*' in key or '~' in key:
                        # Key has modifier - use dispatch.handle() to detect and process it
                        # Menu modifiers need zWizard to handle navigation loop
                        # Pass entire panel_block_content so wizard can navigate between keys
                        if logger:
                            logger.debug(f"[zDash] Menu modifier detected: {key}, delegating to zWizard")
                        _zcli.wizard.execute_loop(
                            items_dict=panel_block_content,
                            context=panel_context,
                            start_key=key
                        )
                        # Menu/wizard handles all navigation - break out of zDash loop
                        break
                    
                    # Track internal panel keys in breadcrumbs (e.g., Panel_Header, Panel_Content)
                    # This creates the panel's internal trail: ['Panel_Header', 'Panel_Content']
                    if hasattr(_zcli, 'navigation') and hasattr(_zcli.navigation, 'breadcrumbs'):
                        _zcli.navigation.breadcrumbs.handle_zCrumbs(key, walker=None)
                    
                    # BUG FIX #4: Use dispatch.handle() for all panel content to support zLinks and navigation
                    # dispatch.handle() properly detects zLinks and passes walker context
                    # This enables dashboard-in-dashboard and other nested navigation patterns
                    if isinstance(value, list):
                        for item in value:
                            # Check if item is a dict that might contain navigation (zLink, etc.)
                            if isinstance(item, dict):
                                # Use dispatch.handle() to support navigation events
                                _zcli.dispatch.handle(key, item, context=panel_context, walker=self.display.zcli.walker)
                            else:
                                # Simple display event, use launcher
                                _zcli.dispatch.launcher.launch(zHorizontal=item, context=panel_context)
                    else:
                        # For non-list values, always use dispatch.handle() to support navigation
                        _zcli.dispatch.handle(key, value, context=panel_context, walker=self.display.zcli.walker)
                
            except Exception as e:
                if logger:
                    logger.error(f"[zDash] Error loading panel {zLink_path}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                break
            finally:
                # Restore session context to dashboard level after panel execution
                # This ensures next panel gets correct context
                from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZBLOCK, SESSION_KEY_ZVAFILE, SESSION_KEY_ZVAFOLDER
                
                # Restore zBlock
                if hasattr(_zcli, 'navigation') and hasattr(_zcli.navigation, 'breadcrumbs'):
                    if old_block:  # Restore to dashboard block
                        _zcli.session[SESSION_KEY_ZBLOCK] = old_block
                        if logger:
                            logger.debug(f"[zDash] Restored session zBlock: {_zcli.session[SESSION_KEY_ZBLOCK]}")
                
                # Restore file context (for delta links)
                _zcli.session[SESSION_KEY_ZVAFILE] = old_vafile
                _zcli.session[SESSION_KEY_ZVAFOLDER] = old_vafolder
                if logger:
                    logger.debug(f"[zDash] Restored session VaFile: {old_vafile}, VaFolder: {old_vafolder}")
            
            # 2. Build and show dashboard navigation menu
            self._output_text("", break_after=False)  # Blank line
            
            menu_items = []
            for i, panel_name in enumerate(sidebar, 1):
                meta = panel_metadata.get(panel_name, {})
                label = meta.get('label', panel_name)
                
                # Mark current panel
                current_marker = " [current]" if panel_name == current_panel else ""
                
                # Format: [1] Overview [current]
                # Icons are visual only (terminal doesn't support them)
                display_text = f"{label}{current_marker}"
                menu_items.append((i, display_text))
            
            # Add "done" option
            self._output_text("", break_after=False)
            self._output_text("Dashboard Menu:", break_after=False)
            
            # Display menu items
            for number, label in menu_items:
                content = f"  [{number}] {label}"
                self._output_text(content, break_after=False)
            
            # Display "done" option
            self._output_text("", break_after=False)
            self._output_text("  [done] Exit Dashboard", break_after=False)
            self._output_text("", break_after=False)
            
            # 3. Get user selection
            user_input = self.zPrimitives.read_string("> ").strip().lower()
            
            if logger:
                logger.debug(f"[zDash] User input: '{user_input}'")
            
            # 4. Handle user choice
            if user_input == "done":
                if logger:
                    logger.info("[zDash] User exited dashboard via 'done' command")
                break  # Exit loop, gate satisfied
            
            # Try to parse as number
            try:
                choice_num = int(user_input)
                if 1 <= choice_num <= len(sidebar):
                    current_panel = sidebar[choice_num - 1]
                    if logger:
                        logger.info(f"[zDash] User selected panel: {current_panel}")
                    # Loop continues to render new panel
                else:
                    if logger:
                        logger.warning(f"[zDash] Invalid menu choice: {choice_num}")
                    self._output_text(f"Invalid choice. Please enter 1-{len(sidebar)} or 'done'", break_after=False)
            except ValueError:
                if logger:
                    logger.warning(f"[zDash] Invalid input (not a number or 'done'): {user_input}")
                self._output_text(f"Invalid input. Please enter 1-{len(sidebar)} or 'done'", break_after=False)
        
        # Gate satisfied - execution continues
        if logger:
            logger.info("[zDash] Dashboard gate satisfied, continuing execution")
        
        return current_panel

    def zDialog(
        self, 
        context: Dict[str, Any], 
        _zcli: Optional[Any] = None, 
        _walker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Display form dialog and collect validated input (Terminal or Bifrost mode).
        
        ORCHESTRATOR METHOD - Coordinates form display and collection workflow.
        
        ⚠️  CURRENT IMPLEMENTATION: Simple field collection only.
        📋 FUTURE (Week 6.5): Full schema validation, field types, validation feedback.
        
        Args:
            context: Form context dict containing:
                    - _KEY_FIELDS: List of field names to collect
                    - Additional schema/validation data (future)
            _zcli: zCLI instance for logging integration
            _walker: zWalker instance for navigation (reserved for future use)
        
        Returns:
            Dict[str, Any]: Collected form data {field_name: value, ...}
                           Empty dict {} if GUI mode (async collection)
        
        Bifrost Mode:
            - Sends _EVENT_ZDIALOG event with form context
            - Frontend displays interactive form UI
            - Returns empty dict (data sent back via WebSocket)
        
        Terminal Mode:
            - Displays form header
            - Collects text input for each field
            - Displays form complete footer
            - Returns collected data dict
        
        Usage:
            # Simple field collection (current)
            context = {_KEY_FIELDS: ["username", "email", "role"]}
            data = display.zEvents.zSystem.zDialog(context)
            # Returns: {"username": "admin", "email": "a@b.com", "role": "admin"}
            
            # For advanced form features, use zcli.dialog.handle() instead:
            # result = zcli.dialog.handle({"zDialog": {"model": "@.zSchema.users", "fields": [...]}})
        
        Notes:
            - Simple text input only (by design)
            - For schema validation and advanced features, use zcli.dialog.handle()
            - Uses zDeclare() for form header/footer
            - Composes zPrimitives.read_string() for input collection
        """
        # 1. Debug logging
        self._log_zdialog_start(context, _zcli)
        
        # 2. Try Bifrost (GUI) mode first
        if self._try_zdialog_gui_mode(context, _zcli):
            return {}  # GUI event sent successfully
        
        # 3. Terminal mode - display header
        fields = context.get(_KEY_FIELDS, [])
        self.zDeclare(_MSG_FORM_INPUT, indent=0)
        
        # 4. Setup schema validation (if available)
        validator, table_name, logger = self._setup_zdialog_validator(context, _zcli)
        
        # 5. Collect form fields with validation
        zConv = self._collect_zdialog_fields(fields, validator, table_name, logger)
        
        # 6. Display footer
        self.zDeclare(_MSG_FORM_COMPLETE, indent=0)
        
        return zConv
    
    # ZDIALOG HELPER METHODS (Private)
    
    def _log_zdialog_start(self, context: Dict[str, Any], _zcli: Optional[Any]) -> None:
        """Log zDialog start (debug mode only)."""
        if _zcli and hasattr(_zcli, 'logger'):
            _zcli.logger.debug(f"\n{'='*80}")
            _zcli.logger.debug(f"[zDialog] 📋 ZDIALOG CALLED - Context: {list(context.keys())}")
            _zcli.logger.debug(f"[zDialog] Fields: {context.get('fields', [])}")
            _zcli.logger.debug(f"[zDialog] Model: {context.get('model', 'N/A')}")
            _zcli.logger.debug(f"[zDialog] Has onSubmit: {bool(context.get('onSubmit'))}")
            _zcli.logger.debug(f"{'='*80}\n")
    
    def _try_zdialog_gui_mode(self, context: Dict[str, Any], _zcli: Optional[Any]) -> bool:
        """Try to send zDialog event to Bifrost (GUI) mode. Returns True if GUI mode active."""
        gui_sent = self._try_gui_event(_EVENT_ZDIALOG, context)
        if _zcli and hasattr(_zcli, 'logger'):
            _zcli.logger.debug(f"[zDialog] GUI event sent: {gui_sent}")
        return gui_sent
    
    def _setup_zdialog_validator(
        self,
        context: Dict[str, Any],
        _zcli: Optional[Any]
    ) -> tuple:
        """
        Setup schema validator for field-by-field validation.
        
        Returns:
            tuple: (validator, table_name, logger) or (None, None, logger) if validation disabled
        """
        model = context.get(_KEY_MODEL)
        logger = self.display.logger if hasattr(self.display, 'logger') else None
        
        if logger:
            logger.debug(f"[zDialog] Field-by-field validation setup - model: {model}")
        
        # Check if validation is possible
        if not (model and isinstance(model, str) and model.startswith('@') and _zcli):
            self._log_validation_disabled_reason(model, _zcli, logger)
            return None, None, logger
        
        # Try to load schema and create validator
        try:
            validator, table_name = self._load_zdialog_schema_validator(model, _zcli, logger)
            if validator and table_name:
                return validator, table_name, logger
            else:
                # Schema not found - critical error
                self._display_schema_error(f"Schema not found: {model}", logger)
                return None, None, logger
        except Exception as e:
            # Schema loading failed - critical error
            self._display_schema_error(f"Failed to load schema: {e}", logger)
            return None, None, logger
    
    def _log_validation_disabled_reason(
        self,
        model: Optional[str],
        _zcli: Optional[Any],
        logger: Optional[Any]
    ) -> None:
        """Log why validation is disabled."""
        if not logger:
            return
        
        if not model:
            logger.debug(f"[zDialog] No model specified - validation disabled")
        elif not model.startswith('@'):
            logger.debug(f"[zDialog] Model doesn't start with '@' - validation disabled: {model}")
        elif not _zcli:
            logger.debug(f"[zDialog] No zcli instance - validation disabled")
    
    def _load_zdialog_schema_validator(
        self,
        model: str,
        _zcli: Any,
        logger: Optional[Any]
    ) -> tuple:
        """
        Load schema and create validator.
        
        Returns:
            tuple: (validator, table_name) or (None, None) if schema not found
        """
        if logger:
            logger.debug(f"[zDialog] Loading schema from: {model}")
        
        # Load schema for validation
        from zOS.L3_Abstraction.n_zData.zData_modules.shared.validator import DataValidator
        schema_dict = _zcli.loader.handle(model) if hasattr(_zcli, 'loader') else None
        
        if logger:
            logger.debug(f"[zDialog] Schema loaded: {bool(schema_dict)}")
        
        if not schema_dict:
            return None, None
        
        # Extract table name and create validator
        table_name = model.split('.')[-1]
        if logger:
            logger.debug(f"[zDialog] Table name extracted: {table_name}")
            logger.debug(f"[zDialog] Schema fields: {list(schema_dict.get(table_name, {}).keys())}")
        
        # Use display's logger if available, otherwise try zcli's
        validator_logger = logger or (_zcli.logger if hasattr(_zcli, 'logger') else None)
        if validator_logger:
            validator = DataValidator(schema_dict, validator_logger)
            if logger:
                logger.info(f"[zDialog] ✅ Field-by-field validation ENABLED for table: {table_name}")
            return validator, table_name
        
        return None, None
    
    def _display_schema_error(self, error_msg: str, logger: Optional[Any]) -> None:
        """Display schema loading error to user."""
        if logger:
            logger.error(f"[zDialog] {error_msg}")
        if self.Signals:
            self.Signals.error(f"[ERROR] {error_msg}", indent=0)
            self._output_text("", break_after=False)
            self.Signals.error("Form cannot proceed without schema validation.", indent=1)
    
    def _collect_zdialog_fields(
        self,
        fields: list,
        validator: Optional[Any],
        table_name: Optional[str],
        logger: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Collect all form fields with validation.
        
        Returns:
            Dict[str, Any]: Collected field data {field_name: value, ...}
        """
        zConv = {}
        
        for field in fields:
            # Add newline before each field (except first)
            if zConv:
                self._output_text("", break_after=False)
            
            # Parse field metadata
            field_name, field_type, field_label = self._parse_zdialog_field(field)
            
            # Collect field value with validation loop
            value = self._collect_single_field_with_validation(
                field_name, field_type, field_label, validator, table_name, logger
            )
            
            # Save collected value
            zConv[field_name] = value
        
        return zConv
    
    def _parse_zdialog_field(self, field: Any) -> tuple:
        """
        Parse field specification into (name, type, label).
        
        Args:
            field: Either a string field name or a dict with 'name', 'type', 'label'
        
        Returns:
            tuple: (field_name, field_type, field_label)
        """
        if isinstance(field, dict):
            field_name = field.get('name', field.get('field', 'unknown'))
            field_type = field.get('type', None)  # None = auto-detect
            field_label = field.get('label', field_name)  # Use label if provided
        else:
            field_name = str(field)
            field_type = None  # Auto-detect
            field_label = field_name
        
        # Auto-detect password fields if type not specified
        if field_type is None:
            if 'password' in field_name.lower():
                field_type = 'password'
            else:
                field_type = 'text'
        
        return field_name, field_type, field_label
    
    def _collect_single_field_with_validation(
        self,
        field_name: str,
        field_type: str,
        field_label: str,
        validator: Optional[Any],
        table_name: Optional[str],
        logger: Optional[Any]
    ) -> Any:
        """
        Collect a single field value with validation retry loop.
        
        Returns:
            Any: The validated field value
        """
        while True:
            # Collect input based on field type
            value = self._read_field_input(field_type, field_label, logger, field_name)
            
            # Validate if validator available
            if validator and table_name:
                is_valid, error_msg = self._validate_field_value(
                    field_name, value, validator, table_name, logger
                )
                
                if is_valid:
                    if logger:
                        logger.info(f"[zDialog] ✅ Field '{field_name}' validation passed")
                    return value
                else:
                    # Display error and retry
                    self._display_field_error(error_msg, logger, field_name)
                    # Loop continues - retry this field
            else:
                # No validation - accept value
                if logger:
                    logger.debug(f"[zDialog] No validation for field '{field_name}' - accepting value")
                return value
    
    def _read_field_input(
        self,
        field_type: str,
        field_label: str,
        logger: Optional[Any],
        field_name: str
    ) -> Any:
        """Read input for a single field based on type."""
        prompt = _FORMAT_FIELD_PROMPT.format(label=field_label)
        
        if field_type == 'password':
            value = self.zPrimitives.read_password(prompt)
        else:
            value = self.zPrimitives.read_string(prompt)
        
        if logger:
            # Mask password fields in logs for security
            log_value = '********' if field_type == 'password' else value
            logger.debug(f"[zDialog] Field '{field_name}' input received: '{log_value}' (type: {field_type})")
        
        return value
    
    def _validate_field_value(
        self,
        field_name: str,
        value: Any,
        validator: Any,
        table_name: str,
        logger: Optional[Any]
    ) -> tuple:
        """
        Validate a field value against schema.
        
        Returns:
            tuple: (is_valid: bool, error_msg: Optional[str])
        """
        if logger:
            logger.debug(f"[zDialog] Validating field '{field_name}' against table '{table_name}'")
        
        is_valid, errors = validator.validate_field(table_name, field_name, value)
        
        if logger:
            logger.debug(f"[zDialog] Validation result for '{field_name}': valid={is_valid}, errors={errors}")
        
        if not is_valid and field_name in errors:
            error_msg = errors[field_name]
            if logger:
                logger.info(f"[zDialog] Field '{field_name}' validation failed: {error_msg}")
            return False, error_msg
        
        return True, None
    
    def _display_field_error(
        self,
        error_msg: str,
        logger: Optional[Any],
        field_name: str
    ) -> None:
        """Display field validation error to user."""
        if self.Signals:
            self.Signals.error(f"[ERROR] {error_msg}", indent=1)
            self._output_text("", break_after=False)


    # ZSESSION DISPLAY HELPERS (Private)

    def _display_field(
        self, 
        label: str, 
        value: Any, 
        indent: int = 0, 
        color: str = COLOR_GREEN
    ) -> None:
        """
        Display a labeled field with color formatting (Terminal).
        
        Args:
            label: Field label text
            value: Field value to display
            indent: Indentation level (default: 0)
            color: Color name for label (default: COLOR_GREEN)
        
        Returns:
            None
        
        Format:
            <color>label:<reset> value
        
        Usage:
            self._display_field("Username", "admin", color=COLOR_YELLOW)
            # Output: Username: admin (with colored label)
        """
        if not self.BasicOutputs:
            return

        color_code = self._get_color(color)
        content = f"{color_code}{label}:{self.zColors.RESET} {value}"
        self._output_text(content, indent=indent, break_after=False)

    def _display_section(
        self, 
        title: str, 
        indent: int = 0, 
        color: str = COLOR_GREEN
    ) -> None:
        """
        Display a section title with color formatting (Terminal).
        
        Args:
            title: Section title text
            indent: Indentation level (default: 0)
            color: Color name for title (default: COLOR_GREEN)
        
        Returns:
            None
        
        Format:
            <color>title:<reset>
        
        Usage:
            self._display_section("zMachine", color=COLOR_GREEN)
            # Output: zMachine: (with colored title)
        """
        if not self.BasicOutputs:
            return

        color_code = self._get_color(color)
        content = f"{color_code}{title}:{self.zColors.RESET}"
        self._output_text(content, indent=indent, break_after=False)

    def _display_zmachine(self, zMachine: Dict[str, Any]) -> None:
        """
        Display complete zMachine section with organized subsections (Terminal).
        
        Displays machine configuration in three organized sections:
        1. Identity & Deployment (os, hostname, architecture, python_version, deployment, role)
        2. Tool Preferences (browser, ide, shell)
        3. System Capabilities (cpu_cores, memory_gb)
        4. zCLI Version
        
        Args:
            zMachine: zMachine dictionary from session[SESSION_KEY_ZMACHINE]
        
        Returns:
            None
        
        Structure:
            zMachine:
              os: macOS
              hostname: dev-machine
              architecture: arm64
              python_version: 3.11.5
              deployment: dev
              role: developer
              
              Tool Preferences:
                browser: Chrome
                ide: VSCode
                shell: zsh
              
              System:
                cpu_cores: 8
                memory_gb: 16
              
              zcli_version: 1.5.4
        
        Notes:
            - Uses ZMACHINE_KEY_* constants for all field access
            - Color-coded sections (GREEN for main, CYAN for subsections, YELLOW for fields)
            - Only displays sections if fields present
        """
        if not self.BasicOutputs:
            return

        self._output_text("", break_after=False)
        self._display_section(_MSG_ZMACHINE_SECTION, color=COLOR_GREEN)

        # Identity & Deployment
        for field_key in _ZMACHINE_IDENTITY_FIELDS:
            if zMachine.get(field_key):
                label = _FORMAT_FIELD_LABEL_INDENT.format(field=field_key)
                self._display_field(label, zMachine.get(field_key), color=COLOR_YELLOW)

        # Tool Preferences
        has_tools = any(zMachine.get(tool) for tool in _ZMACHINE_TOOL_FIELDS)
        if has_tools:
            self._output_text("", break_after=False)
            self._display_section(_FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_TOOL_PREFERENCES), color=COLOR_CYAN)
            for tool_key in _ZMACHINE_TOOL_FIELDS:
                if zMachine.get(tool_key):
                    label = _FORMAT_TOOL_FIELD_INDENT.format(field=tool_key)
                    self._display_field(label, zMachine.get(tool_key), color=COLOR_RESET)

        # System Capabilities
        has_system = any(zMachine.get(field) for field in _ZMACHINE_SYSTEM_FIELDS)
        if has_system:
            self._output_text("", break_after=False)
            self._display_section(_FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_SYSTEM), color=COLOR_CYAN)
            for field_key in _ZMACHINE_SYSTEM_FIELDS:
                if zMachine.get(field_key):
                    label = _FORMAT_TOOL_FIELD_INDENT.format(field=field_key)
                    self._display_field(label, zMachine.get(field_key), color=COLOR_RESET)

        # zcli version
        if zMachine.get(_ZMACHINE_KEY_ZCLI_VERSION):
            self._output_text("", break_after=False)
            self._display_field(
                _LABEL_ZCLI_VERSION, 
                zMachine.get(_ZMACHINE_KEY_ZCLI_VERSION), 
                color=COLOR_YELLOW
            )


    # ZAUTH DISPLAY HELPERS (Private - Three-Tier Model Aware)

    def _display_zauth(self, zAuth: Dict[str, Any]) -> None:
        """
        Display complete zAuth section with three-tier model awareness (Terminal).
        
        Displays authentication state with full awareness of zAuth's three-tier model:
        - Layer 1: zSession auth (internal zCLI users)
        - Layer 2: Application auth (external app users, multi-app)
        - Layer 3: Dual-auth (simultaneous contexts)
        
        Displays:
        1. Active Context (zSession/application/dual)
        2. Dual-mode indicator (if dual_mode = True)
        3. Current authentication (from active context)
        4. All authenticated apps (if multiple apps, Layer 2)
        5. Active app indicator (if in application/dual context)
        
        Args:
            zAuth: zAuth dictionary from session[SESSION_KEY_ZAUTH]
        """
        if not self.BasicOutputs or not zAuth:
            return

        self._output_text("", break_after=False)
        self._display_section(_MSG_ZAUTH_SECTION, color=COLOR_GREEN)

        # Orchestrate display in logical order
        active_context = self._render_zauth_active_context(zAuth)
        if not active_context:
            return  # Not authenticated
        
        active_app = self._render_zauth_active_app(zAuth)
        self._render_zauth_authenticated_apps(zAuth, active_app)
        self._render_zauth_current_user(zAuth, active_context, active_app)

    def _render_zauth_active_context(self, zAuth: Dict[str, Any]) -> Optional[str]:
        """Render active context with dual-mode indicator, return context or None if not authenticated."""
        active_context = zAuth.get(ZAUTH_KEY_ACTIVE_CONTEXT)
        
        if not active_context:
            if not self._check_zauth_authentication(zAuth):
                return None
            active_context = CONTEXT_ZSESSION
        
        # Display context with dual-mode indicator
        context_label = _FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_ACTIVE_CONTEXT)
        dual_mode = zAuth.get(ZAUTH_KEY_DUAL_MODE, False)
        context_display = f"{active_context} {_MSG_DUAL_MODE_INDICATOR}" if dual_mode else active_context
        self._display_field(context_label, context_display, color=COLOR_YELLOW)
        
        return active_context

    def _check_zauth_authentication(self, zAuth: Dict[str, Any]) -> bool:
        """Check if user is authenticated, display status if not."""
        zsession_auth = zAuth.get(ZAUTH_KEY_ZSESSION, {})
        is_authenticated = zsession_auth.get(ZAUTH_KEY_AUTHENTICATED, False)
        
        if not is_authenticated:
            label = _FORMAT_FIELD_LABEL_INDENT.format(field="Status")
            self._display_field(label, "Not authenticated", color=COLOR_YELLOW)
            return False
        return True

    def _render_zauth_active_app(self, zAuth: Dict[str, Any]) -> Optional[str]:
        """Render active app if in application or dual context, return app name."""
        active_app = zAuth.get(ZAUTH_KEY_ACTIVE_APP)
        if active_app:
            label = _FORMAT_FIELD_LABEL_INDENT.format(field="Active App")
            self._display_field(label, active_app, color=COLOR_YELLOW)
        return active_app

    def _render_zauth_authenticated_apps(self, zAuth: Dict[str, Any], active_app: Optional[str]) -> None:
        """Render list of authenticated apps if multiple (Layer 2 multi-app support)."""
        applications = zAuth.get(ZAUTH_KEY_APPLICATIONS, {})
        if not isinstance(applications, dict) or len(applications) <= 1:
            return
        
        self._output_text("", break_after=False)
        label = _FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_AUTHENTICATED_APPS)
        self._display_section(label, color=COLOR_CYAN)
        
        for app_name in applications.keys():
            app_display = f"{app_name} (ACTIVE)" if app_name == active_app else app_name
            app_label = _FORMAT_TOOL_FIELD_INDENT.format(field="-")
            self._display_field(app_label, app_display, color=COLOR_RESET)

    def _render_zauth_current_user(self, zAuth: Dict[str, Any], active_context: str, active_app: Optional[str]) -> None:
        """Render current authentication data (ID, Username, Role) from active context."""
        auth_data = self._get_zauth_active_data(zAuth, active_context, active_app)
        
        for field_key, field_label in [
            (ZAUTH_KEY_ID, "ID"),
            (ZAUTH_KEY_USERNAME, "Username"),
            (ZAUTH_KEY_ROLE, "Role")
        ]:
            if auth_data.get(field_key):
                label = _FORMAT_FIELD_LABEL_INDENT.format(field=field_label)
                self._display_field(label, auth_data.get(field_key), color=COLOR_YELLOW)

    def _get_zauth_active_data(self, zAuth: Dict[str, Any], active_context: str, active_app: Optional[str]) -> Dict[str, Any]:
        """Get authentication data from active context."""
        applications = zAuth.get(ZAUTH_KEY_APPLICATIONS, {})
        
        if active_context == CONTEXT_ZSESSION:
            return zAuth.get(ZAUTH_KEY_ZSESSION, {})
        elif active_context == CONTEXT_APPLICATION and active_app:
            return applications.get(active_app, {})
        elif active_context == CONTEXT_DUAL and active_app:
            # For dual context, show from active app (future: show both)
            return applications.get(active_app, {})
        
        return {}

    def _display_zcache(self, zCache: Dict[str, Any]) -> None:
        """
        Display complete zCache section with 4-tier caching system (Terminal).
        
        Displays cache state for all 4 cache types:
        - system_cache: System-level cache (UI files, configs)
        - pinned_cache: Pinned items that persist across sessions
        - schema_cache: Database schema definitions
        - plugin_cache: Loaded plugin modules
        
        Args:
            zCache: zCache dictionary from session[SESSION_KEY_ZCACHE]
        
        Returns:
            None
        
        Display Format:
            zCache:
              system_cache: 12 items
              pinned_cache: 3 items
              schema_cache: 5 items
              plugin_cache: 8 items
        
        Notes:
            - Uses ZCACHE_KEY_* constants for all field access
            - Shows item count for each cache type
            - Empty caches show "0 items"
        """
        if not self.BasicOutputs or not zCache:
            return

        self._output_text("", break_after=False)
        self._display_section("zCache", color=COLOR_CYAN)

        # Display each cache tier with item count
        for cache_key, cache_label in [
            (ZCACHE_KEY_SYSTEM, "system_cache"),
            (ZCACHE_KEY_PINNED, "pinned_cache"),
            (ZCACHE_KEY_SCHEMA, "schema_cache"),
            (ZCACHE_KEY_PLUGIN, "plugin_cache")
        ]:
            cache_data = zCache.get(cache_key, {})
            item_count = len(cache_data) if isinstance(cache_data, dict) else 0
            label = _FORMAT_FIELD_LABEL_INDENT.format(field=cache_label)
            value = f"{item_count} items" if item_count != 1 else "1 item"
            self._display_field(label, value, color=COLOR_RESET)

    def _display_zshortcuts(
        self,
        zvars: Dict[str, Any],
        zshortcuts: Dict[str, Any]
    ) -> None:
        """
        Display zVars and file shortcuts section (Terminal).
        
        Displays user-defined variables (zVars) and file shortcuts from the unified
        aliasing system. Shows empty state if no variables or shortcuts are defined.
        
        Args:
            zvars: zVars dictionary from session[SESSION_KEY_ZVARS]
            zshortcuts: zShortcuts dictionary from session[SESSION_KEY_ZSHORTCUTS]
        
        Returns:
            None
        
        Display Format:
            zVars & Shortcuts:
              zVars: 3 defined
              zShortcuts: 2 defined
        
        Or if empty:
            zVars & Shortcuts:
              zVars: none
              zShortcuts: none
        
        Notes:
            - Uses SESSION_KEY_ZVARS and SESSION_KEY_ZSHORTCUTS constants
            - Shows count for each type
            - Empty dicts show "none"
        """
        if not self.BasicOutputs:
            return

        # Skip section entirely if both are empty
        if not zvars and not zshortcuts:
            return

        self._output_text("", break_after=False)
        self._display_section("zVars & Shortcuts", color=COLOR_CYAN)

        # Display zVars count
        zvars_count = len(zvars) if isinstance(zvars, dict) else 0
        zvars_label = _FORMAT_FIELD_LABEL_INDENT.format(field="zVars")
        zvars_value = f"{zvars_count} defined" if zvars_count > 0 else "none"
        self._display_field(zvars_label, zvars_value, color=COLOR_RESET)

        # Display zShortcuts count
        shortcuts_count = len(zshortcuts) if isinstance(zshortcuts, dict) else 0
        shortcuts_label = _FORMAT_FIELD_LABEL_INDENT.format(field="zShortcuts")
        shortcuts_value = f"{shortcuts_count} defined" if shortcuts_count > 0 else "none"
        self._display_field(shortcuts_label, shortcuts_value, color=COLOR_RESET)


    # SYSTEM INTEGRATION HELPERS (Private - Logging)

    def _should_show_sysmsg(self) -> bool:
        """
        Check if system messages should be displayed based on deployment mode.
        
        System messages (zDeclare) are conditionally displayed to prevent verbose output
        in production environments.
        
        Check Priority:
            1. Logger method:      zcli.logger.should_show_sysmsg() (if available)
            2. Config method:      zcli.config.is_production() (if available)
            3. Legacy debug flag:  session.get("debug") (backward compatibility)
        
        Returns:
            bool: True if system messages should be displayed, False otherwise
        
        Usage:
            if not self._should_show_sysmsg():
                return  # Don't display system message
        
        Notes:
            - Respects zCLI's logging framework
            - Falls back gracefully if logger/config not available
            - Production deployment hides system messages
            - Development deployments show system messages
        """
        if not self.display or not hasattr(self.display, 'session'):
            return True

        session = self.display.session

        # Priority 1: Check logger's should_show_sysmsg (uses deployment internally)
        if hasattr(self.display, 'zcli'):
            zcli = self.display.zcli
            
            # Check via logger (preferred method)
            if zcli and hasattr(zcli, 'logger') and hasattr(zcli.logger, 'should_show_sysmsg'):
                return zcli.logger.should_show_sysmsg()
            
            # Priority 2: Check via config deployment mode
            if zcli and hasattr(zcli, 'config'):
                # Suppress in both Production AND Testing modes (only show in Development)
                if hasattr(zcli.config, 'is_production') and zcli.config.is_production():
                    return False
                
                # Check for Testing mode
                if hasattr(zcli.config, 'environment') and hasattr(zcli.config.environment, 'is_testing'):
                    if zcli.config.environment.is_testing():
                        return False
                
                # Also check deployment string directly as fallback
                if hasattr(zcli.config, 'get_environment'):
                    deployment = str(zcli.config.get_environment('deployment', '')).lower()
                    if deployment in ['testing', 'info', 'production']:
                        return False
                
                return True

        # Priority 3: Fallback to legacy session debug flag
        debug = session.get("debug")
        if debug is not None:
            return debug

        # Default: show messages (development mode)
        return True
