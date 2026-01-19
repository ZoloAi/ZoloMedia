# zCLI/L2_Core/c_zDisplay/zDisplay_modules/f_orchestration/system_event_session.py

"""
System Session Events - zSession, zConfig
==========================================

This module provides display events for zCLI session state and configuration.
These events show comprehensive system information including machine config,
authentication state, caching, and workspace paths.

Purpose:
    - Display complete session state (zSession)
    - Display machine and environment configuration (zConfig)
    - Format session data for user-friendly terminal output
    - Support both Terminal and Bifrost modes

Public Methods:
    zSession(session_data, break_after, break_message)
        Display complete zCLI session state
        
    zConfig(config_data, break_after, break_message)
        Display zConfig machine and environment configuration

Private Helpers:
    _format_path_as_zpath(path_value, session_data)
        Convert absolute paths to zPath notation
        
    _display_zmachine(zMachine)
        Display complete zMachine section
        
    _display_zauth(zAuth)
        Display complete zAuth section (three-tier aware)
        
    _display_zcache(zCache)
        Display complete zCache section (4-tier caching)
        
    _display_zshortcuts(zvars, zshortcuts)
        Display zVars and file shortcuts section

Dependencies:
    - display_constants: SESSION_KEY_*, ZAUTH_KEY_*, ZCACHE_KEY_*, _EVENT_*, _KEY_*, _MSG_*, COLOR_*, _FORMAT_*
    - display_event_helpers: try_gui_event
    - display_rendering_utilities: render_field, render_section_title, output_text_via_basics, format_value_for_display
    - pathlib: Path operations for zPath formatting

Extracted From:
    display_event_system.py (lines 758-1083, 2021-2319)
"""

from typing import Any, Optional, Dict
from pathlib import Path

# Import SESSION_KEY_* constants
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZS_ID,
    SESSION_KEY_ZMODE,
    SESSION_KEY_ZMACHINE,
    SESSION_KEY_ZAUTH,
    SESSION_KEY_ZSPACE,
    SESSION_KEY_ZVAFOLDER,
    SESSION_KEY_ZVAFILE,
    SESSION_KEY_ZBLOCK,
    SESSION_KEY_ZCACHE,
    ZCACHE_KEY_SYSTEM,
    ZCACHE_KEY_PINNED,
    ZCACHE_KEY_SCHEMA,
    ZCACHE_KEY_PLUGIN,
    SESSION_KEY_ZVARS,
    SESSION_KEY_ZSHORTCUTS
)

# Import ZAUTH_KEY_* constants
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    ZAUTH_KEY_ZSESSION,
    ZAUTH_KEY_APPLICATIONS,
    ZAUTH_KEY_ACTIVE_APP,
    ZAUTH_KEY_ID,
    ZAUTH_KEY_USERNAME,
    ZAUTH_KEY_ROLE,
    ZAUTH_KEY_ACTIVE_CONTEXT,
    ZAUTH_KEY_DUAL_MODE,
    ZAUTH_KEY_AUTHENTICATED,
    CONTEXT_ZSESSION,
    CONTEXT_APPLICATION,
    CONTEXT_DUAL
)

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import try_gui_event
from ..a_infrastructure.display_rendering_utilities import (
    render_field,
    render_section_title,
    output_text_via_basics,
    format_value_for_display
)

# Import constants
from ..display_constants import (
    # Event Names
    _EVENT_ZSESSION,
    _EVENT_ZCONFIG,
    # JSON Keys
    _KEY_SESSION,
    _KEY_BREAK,
    _KEY_BREAK_MESSAGE,
    # Messages
    _MSG_NO_SESSION,
    _MSG_VIEW_ZSESSION,
    _MSG_ZMACHINE_SECTION,
    _MSG_ZAUTH_SECTION,
    _MSG_ACTIVE_CONTEXT,
    _MSG_DUAL_MODE_INDICATOR,
    _MSG_AUTHENTICATED_APPS,
    _MSG_TOOL_PREFERENCES,
    _MSG_SYSTEM,
    # Colors
    COLOR_MAIN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_CYAN,
    COLOR_RESET,
    # Format strings
    _FORMAT_FIELD_LABEL_INDENT,
    _FORMAT_TOOL_FIELD_INDENT,
    # zMachine field lists
    _ZMACHINE_KEY_ZCLI_VERSION,
    _ZMACHINE_IDENTITY_FIELDS,
    _ZMACHINE_TOOL_FIELDS,
    _ZMACHINE_SYSTEM_FIELDS,
    # Labels
    _LABEL_ZSESSION_ID,
    _LABEL_ZMODE,
    _LABEL_ZCLI_VERSION
)

# Session field list
SESSION_WORKSPACE_FIELDS = [
    SESSION_KEY_ZSPACE,
    SESSION_KEY_ZVAFOLDER,
    SESSION_KEY_ZVAFILE,
    SESSION_KEY_ZBLOCK
]


class SessionEvents:
    """
    Session and configuration display events.
    
    Provides zSession and zConfig events for displaying comprehensive
    system state information in both Terminal and Bifrost modes.
    
    Composition:
        - BasicOutputs: For text() rendering (set after zEvents init)
        - DeclareEvents: For header rendering (set after zSystem init)
    
    Usage:
        # Via zSystem coordinator
        zcli.display.zEvents.zSystem.zSession(zcli.session)
        zcli.display.zEvents.zSystem.zConfig(config_data)
    """
    
    # Class-level type declarations
    display: Any          # Parent zDisplay instance
    BasicOutputs: Optional[Any]  # BasicOutputs event package (set after init)
    DeclareEvents: Optional[Any]  # DeclareEvents (for zDeclare) (set after init)
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize SessionEvents with reference to parent zDisplay instance.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Notes:
            - BasicOutputs and DeclareEvents are set to None initially
            - Will be populated by zSystem after all event packages instantiated
        """
        self.display = display_instance
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self.DeclareEvents = None  # Will be set after zSystem initialization
    
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
                
                # Only process if user_data_dir is actually set
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
            - Displays formatted session structure with all sections
        
        Usage:
            zcli.display.zEvents.zSystem.zSession(zcli.session)
        """
        # Try Bifrost (GUI) mode first
        if try_gui_event(self.display, _EVENT_ZSESSION, {
            _KEY_SESSION: session_data,
            _KEY_BREAK: break_after,
            _KEY_BREAK_MESSAGE: break_message
        }):
            return
        
        # Terminal mode
        if not session_data:
            output_text_via_basics(_MSG_NO_SESSION, 0, False, self.display)
            return
        
        # Header
        if self.DeclareEvents:
            self.DeclareEvents.zDeclare(_MSG_VIEW_ZSESSION, color=COLOR_MAIN, indent=0)
        
        # Core session fields
        render_field(_LABEL_ZSESSION_ID, session_data.get(SESSION_KEY_ZS_ID), 0, COLOR_GREEN, self.display)
        render_field(_LABEL_ZMODE, session_data.get(SESSION_KEY_ZMODE), 0, COLOR_GREEN, self.display)
        
        # zMachine section
        zMachine = session_data.get(SESSION_KEY_ZMACHINE, {})
        if zMachine:
            self._display_zmachine(zMachine)
        
        # Workspace fields
        output_text_via_basics("", 0, False, self.display)
        for field_key in SESSION_WORKSPACE_FIELDS:
            value = session_data.get(field_key)
            field_name = field_key
            
            # Convert path fields to zPath notation
            if field_key in (SESSION_KEY_ZSPACE, SESSION_KEY_ZVAFOLDER) and value:
                value = self._format_path_as_zpath(value, session_data)
            
            render_field(field_name, value if value is not None else "None", 0, COLOR_GREEN, self.display)
        
        # zAuth section
        zAuth = session_data.get(SESSION_KEY_ZAUTH, {})
        if zAuth:
            self._display_zauth(zAuth)
        
        # zCache section
        zCache = session_data.get(SESSION_KEY_ZCACHE, {})
        if zCache:
            self._display_zcache(zCache)
        
        # zVars and zShortcuts section
        zvars = session_data.get(SESSION_KEY_ZVARS, {})
        zshortcuts = session_data.get(SESSION_KEY_ZSHORTCUTS, {})
        if zvars or zshortcuts:
            self._display_zshortcuts(zvars, zshortcuts)
        
        # Optional break
        if break_after:
            output_text_via_basics("", 0, False, self.display)
            if break_message:
                output_text_via_basics(break_message, 0, True, self.display)
            else:
                output_text_via_basics("", 0, True, self.display)
    
    def zConfig(
        self,
        config_data: Optional[Dict[str, Any]] = None,
        break_after: bool = True,
        break_message: Optional[str] = None
    ) -> None:
        """
        Display zConfig machine and environment configuration (Terminal or Bifrost mode).
        
        Args:
            config_data: Dict with 'machine' and 'environment' keys
            break_after: Add "Press Enter" prompt at end (default: True)
            break_message: Custom break message
        
        Returns:
            None
        """
        # Try Bifrost mode first
        if try_gui_event(self.display, _EVENT_ZCONFIG, {
            "config": config_data,
            _KEY_BREAK: break_after,
            _KEY_BREAK_MESSAGE: break_message
        }):
            return
        
        # Terminal mode
        if not config_data:
            output_text_via_basics("No configuration data available", 0, False, self.display)
            return
        
        # Machine Configuration
        machine = config_data.get('machine', {})
        if machine and self.BasicOutputs:
            output_text_via_basics("", 0, False, self.display)
            self.BasicOutputs.header(" zConfig: Machine Configuration", color="CONFIG", style="full")
            output_text_via_basics("", 0, False, self.display)
            
            for key, value in sorted(machine.items()):
                value_str = format_value_for_display(value)
                render_field(key, value_str, 0, COLOR_GREEN, self.display)
        
        # Environment Configuration
        environment = config_data.get('environment', {})
        if environment and self.BasicOutputs:
            output_text_via_basics("", 0, False, self.display)
            self.BasicOutputs.header(" zConfig: Environment Configuration", color="CONFIG", style="full")
            output_text_via_basics("", 0, False, self.display)
            
            for key, value in sorted(environment.items()):
                value_str = format_value_for_display(value)
                render_field(key, value_str, 0, COLOR_GREEN, self.display)
        
        # Break prompt
        if break_after:
            output_text_via_basics("", 0, False, self.display)
            if break_message:
                output_text_via_basics(break_message, 0, True, self.display)
            else:
                output_text_via_basics("", 0, True, self.display)
    
    # HELPER METHODS (Private)
    
    def _display_zmachine(self, zMachine: Dict[str, Any]) -> None:
        """Display complete zMachine section with organized subsections."""
        output_text_via_basics("", 0, False, self.display)
        render_section_title(_MSG_ZMACHINE_SECTION, 0, COLOR_GREEN, self.display)
        
        # Identity & Deployment
        for field_key in _ZMACHINE_IDENTITY_FIELDS:
            if zMachine.get(field_key):
                label = _FORMAT_FIELD_LABEL_INDENT.format(field=field_key)
                render_field(label, zMachine.get(field_key), 0, COLOR_YELLOW, self.display)
        
        # Tool Preferences
        has_tools = any(zMachine.get(tool) for tool in _ZMACHINE_TOOL_FIELDS)
        if has_tools:
            output_text_via_basics("", 0, False, self.display)
            render_section_title(_FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_TOOL_PREFERENCES), 0, COLOR_CYAN, self.display)
            for tool_key in _ZMACHINE_TOOL_FIELDS:
                if zMachine.get(tool_key):
                    label = _FORMAT_TOOL_FIELD_INDENT.format(field=tool_key)
                    render_field(label, zMachine.get(tool_key), 0, COLOR_RESET, self.display)
        
        # System Capabilities
        has_system = any(zMachine.get(field) for field in _ZMACHINE_SYSTEM_FIELDS)
        if has_system:
            output_text_via_basics("", 0, False, self.display)
            render_section_title(_FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_SYSTEM), 0, COLOR_CYAN, self.display)
            for field_key in _ZMACHINE_SYSTEM_FIELDS:
                if zMachine.get(field_key):
                    label = _FORMAT_TOOL_FIELD_INDENT.format(field=field_key)
                    render_field(label, zMachine.get(field_key), 0, COLOR_RESET, self.display)
        
        # zcli version
        if zMachine.get(_ZMACHINE_KEY_ZCLI_VERSION):
            output_text_via_basics("", 0, False, self.display)
            render_field(_LABEL_ZCLI_VERSION, zMachine.get(_ZMACHINE_KEY_ZCLI_VERSION), 0, COLOR_YELLOW, self.display)
    
    def _display_zauth(self, zAuth: Dict[str, Any]) -> None:
        """Display complete zAuth section with three-tier model awareness."""
        if not zAuth:
            return
        
        output_text_via_basics("", 0, False, self.display)
        render_section_title(_MSG_ZAUTH_SECTION, 0, COLOR_GREEN, self.display)
        
        # Active context
        active_context = zAuth.get(ZAUTH_KEY_ACTIVE_CONTEXT)
        if not active_context:
            zsession_auth = zAuth.get(ZAUTH_KEY_ZSESSION, {})
            if not zsession_auth.get(ZAUTH_KEY_AUTHENTICATED, False):
                label = _FORMAT_FIELD_LABEL_INDENT.format(field="Status")
                render_field(label, "Not authenticated", 0, COLOR_YELLOW, self.display)
                return
            active_context = CONTEXT_ZSESSION
        
        # Display context with dual-mode indicator
        context_label = _FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_ACTIVE_CONTEXT)
        dual_mode = zAuth.get(ZAUTH_KEY_DUAL_MODE, False)
        context_display = f"{active_context} {_MSG_DUAL_MODE_INDICATOR}" if dual_mode else active_context
        render_field(context_label, context_display, 0, COLOR_YELLOW, self.display)
        
        # Active app
        active_app = zAuth.get(ZAUTH_KEY_ACTIVE_APP)
        if active_app:
            label = _FORMAT_FIELD_LABEL_INDENT.format(field="Active App")
            render_field(label, active_app, 0, COLOR_YELLOW, self.display)
        
        # Authenticated apps (if multiple)
        applications = zAuth.get(ZAUTH_KEY_APPLICATIONS, {})
        if isinstance(applications, dict) and len(applications) > 1:
            output_text_via_basics("", 0, False, self.display)
            label = _FORMAT_FIELD_LABEL_INDENT.format(field=_MSG_AUTHENTICATED_APPS)
            render_section_title(label, 0, COLOR_CYAN, self.display)
            
            for app_name in applications.keys():
                app_display = f"{app_name} (ACTIVE)" if app_name == active_app else app_name
                app_label = _FORMAT_TOOL_FIELD_INDENT.format(field="-")
                render_field(app_label, app_display, 0, COLOR_RESET, self.display)
        
        # Current user
        auth_data = self._get_zauth_active_data(zAuth, active_context, active_app)
        for field_key, field_label in [
            (ZAUTH_KEY_ID, "ID"),
            (ZAUTH_KEY_USERNAME, "Username"),
            (ZAUTH_KEY_ROLE, "Role")
        ]:
            if auth_data.get(field_key):
                label = _FORMAT_FIELD_LABEL_INDENT.format(field=field_label)
                render_field(label, auth_data.get(field_key), 0, COLOR_YELLOW, self.display)
    
    def _get_zauth_active_data(self, zAuth: Dict[str, Any], active_context: str, active_app: Optional[str]) -> Dict[str, Any]:
        """Get authentication data from active context."""
        applications = zAuth.get(ZAUTH_KEY_APPLICATIONS, {})
        
        if active_context == CONTEXT_ZSESSION:
            return zAuth.get(ZAUTH_KEY_ZSESSION, {})
        elif active_context == CONTEXT_APPLICATION and active_app:
            return applications.get(active_app, {})
        elif active_context == CONTEXT_DUAL and active_app:
            return applications.get(active_app, {})
        
        return {}
    
    def _display_zcache(self, zCache: Dict[str, Any]) -> None:
        """Display complete zCache section with 4-tier caching system."""
        if not zCache:
            return
        
        output_text_via_basics("", 0, False, self.display)
        render_section_title("zCache", 0, COLOR_CYAN, self.display)
        
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
            render_field(label, value, 0, COLOR_RESET, self.display)
    
    def _display_zshortcuts(self, zvars: Dict[str, Any], zshortcuts: Dict[str, Any]) -> None:
        """Display zVars and file shortcuts section."""
        if not zvars and not zshortcuts:
            return
        
        output_text_via_basics("", 0, False, self.display)
        render_section_title("zVars & Shortcuts", 0, COLOR_CYAN, self.display)
        
        # Display zVars count
        zvars_count = len(zvars) if isinstance(zvars, dict) else 0
        zvars_label = _FORMAT_FIELD_LABEL_INDENT.format(field="zVars")
        zvars_value = f"{zvars_count} defined" if zvars_count > 0 else "none"
        render_field(zvars_label, zvars_value, 0, COLOR_RESET, self.display)
        
        # Display zShortcuts count
        shortcuts_count = len(zshortcuts) if isinstance(zshortcuts, dict) else 0
        shortcuts_label = _FORMAT_FIELD_LABEL_INDENT.format(field="zShortcuts")
        shortcuts_value = f"{shortcuts_count} defined" if shortcuts_count > 0 else "none"
        render_field(shortcuts_label, shortcuts_value, 0, COLOR_RESET, self.display)
