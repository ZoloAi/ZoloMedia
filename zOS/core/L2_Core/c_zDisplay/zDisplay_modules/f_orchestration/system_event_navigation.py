# zCLI/L2_Core/c_zDisplay/zDisplay_modules/f_orchestration/system_event_navigation.py

"""
System Navigation Events - zCrumbs, zMenu
==========================================

This module provides navigation UI events for breadcrumb trails and menu display.
These events help users understand their current location in the system and
navigate between options.

Purpose:
    - Display breadcrumb navigation trails (zCrumbs)
    - Display interactive or display-only menus (zMenu)
    - Support both Terminal and Bifrost modes

Public Methods:
    zCrumbs(session_data)
        Display breadcrumb navigation trail showing scope paths
        
    zMenu(menu_items, prompt, return_selection)
        Display menu options and optionally collect user selection

Dependencies:
    - display_constants: SESSION_KEY_*, _EVENT_*, _KEY_*, _FORMAT_*, _MSG_*
    - display_event_helpers: try_gui_event
    - display_rendering_utilities: output_text_via_basics
    - BasicOutputs (via cross-reference): text() for rendering
    - BasicInputs (via cross-reference): selection() for interactive menus

Extracted From:
    display_event_system.py (lines 1084-1241)
"""

from typing import Any, Optional, Dict, List, Tuple, Union

# Import SESSION_KEY_* constants
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZCRUMBS

# Import colors
from zOS.zSys.formatting.colors import Colors

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import try_gui_event
from ..a_infrastructure.display_rendering_utilities import output_text_via_basics

# Import constants
from ..display_constants import (
    # Event Names
    _EVENT_ZCRUMBS,
    _EVENT_ZMENU,
    # JSON Keys
    _KEY_CRUMBS,
    _KEY_MENU,
    _KEY_PROMPT,
    _KEY_RETURN_SELECTION,
    # Messages
    _MSG_ZCRUMBS_HEADER,
    _MSG_DEFAULT_MENU_PROMPT,
    # Format strings
    _FORMAT_BREADCRUMB_SEPARATOR,
    _FORMAT_CRUMB_SCOPE,
    _FORMAT_MENU_ITEM,
    # Styles
    STYLE_NUMBERED
)


class NavigationEvents:
    """
    Navigation UI events (breadcrumbs, menus).
    
    Provides zCrumbs and zMenu events for displaying navigation information
    and collecting user choices in both Terminal and Bifrost modes.
    
    Composition:
        - BasicOutputs: For text() rendering (set after zEvents init)
        - BasicInputs: For selection() in interactive menus (set after zEvents init)
    
    Usage:
        # Via zSystem coordinator
        zcli.display.zEvents.zSystem.zCrumbs(zcli.session)
        zcli.display.zEvents.zSystem.zMenu(menu_items, return_selection=True)
    """
    
    # Class-level type declarations
    display: Any          # Parent zDisplay instance
    BasicOutputs: Optional[Any]  # BasicOutputs event package (set after init)
    BasicInputs: Optional[Any]   # BasicInputs event package (set after init)
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize NavigationEvents with reference to parent zDisplay instance.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Notes:
            - BasicOutputs and BasicInputs are set to None initially
            - Will be populated by zSystem after all event packages instantiated
        """
        self.display = display_instance
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self.BasicInputs = None   # Will be set after zEvents initialization
    
    def zCrumbs(self, session_data: Optional[Dict[str, Any]] = None, parent: Optional[str] = None, show: str = 'session') -> None:
        """
        Display breadcrumb navigation trail showing scope paths (Terminal or Bifrost mode).
        
        Breadcrumbs show the navigation trail through different scopes (file, vafile, block).
        Uses SESSION_KEY_ZCRUMBS for safe session access.
        
        Args:
            session_data: zCLI session dictionary containing zCrumbs
            parent: Declarative parent path for stateless breadcrumbs (works in both Terminal and Bifrost)
                    Format: "zProducts.zTheme" or "zProducts.zTheme.Containers"
            show: Display mode - 'session' (default, session-based) or 'static' (declarative from parent)
        
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
        
        Structure (Session-based):
            session[SESSION_KEY_ZCRUMBS] = {
                "trails": {
                    "file": ["Main", "Setup", "Config"],
                    "vafile": ["App", "Database", "Users"],
                    "block": ["^Root*", "User Management"]
                },
                "_context": {...},  # Internal metadata (filtered out)
                "_depth_map": {...}  # Internal metadata (filtered out)
            }
        
        Structure (Declarative with parent):
            {
                "trails": {
                    "declarative": ["zProducts", "zTheme", "Containers"]
                },
                "_source": "declarative"
            }
        
        Usage:
            # Session-based (Terminal or warm GUI)
            zcli.display.zEvents.zSystem.zCrumbs(zcli.session)
            
            # Declarative (works in both Terminal and Bifrost)
            zcli.display.zEvents.zSystem.zCrumbs(parent="zProducts.zTheme", show='static')
        
        Notes:
            - Uses SESSION_KEY_ZCRUMBS constant for session access
            - Joins trail items with " > " separator
            - Displays in "scope[path]" format
            - Filters out internal metadata keys (_context, _depth_map)
            - parent parameter enables stateless breadcrumbs for both Terminal and Bifrost
        """
        # Auto-inject session if not provided (declarative .zolo support)
        if session_data is None and hasattr(self.display, 'zcli'):
            session_data = self.display.zcli.session
        
        # Phase 1: Build declarative trail from parent if show='static' and parent is provided
        if show == 'static' and parent:
            # Split parent path (e.g., "zProducts.zTheme" → ["zProducts", "zTheme"])
            parent_parts = parent.split('.')
            
            # Get current page name from session if available
            current_page = None
            if session_data and hasattr(self.display, 'zcli'):
                # Try to extract current page from zVaFile
                zvafile = session_data.get('zVaFile', '')
                if zvafile:
                    # Extract display name (e.g., "zUI.zContainers" → "Containers")
                    current_page = zvafile.split('.')[-1].replace('z', '')
            
            # Build declarative trail: parent parts + current page
            trail = parent_parts.copy()
            if current_page:
                trail.append(current_page)
            
            # Create declarative crumbs structure
            z_crumbs = {
                'trails': {
                    'declarative': trail
                },
                '_source': 'declarative'
            }
        else:
            # Use session-based breadcrumbs (default behavior for show='session' or missing parent)
            z_crumbs = session_data.get(SESSION_KEY_ZCRUMBS, {}) if session_data else {}
        
        if try_gui_event(self.display, _EVENT_ZCRUMBS, {_KEY_CRUMBS: z_crumbs}):
            return  # GUI event sent successfully
        
        # Terminal mode - display breadcrumbs using composed events
        # Phase 1: For show='session', if breadcrumbs are empty, initialize with current file path
        if show == 'session' and not z_crumbs and session_data:
            # Construct full file path from session (same format as navigation system)
            # Format: @.UI.zProducts.zTheme.zUI.zContainers.zContainers_Details
            zfolder = session_data.get('zVaFolder', '')  # e.g., "@.UI.zProducts.zTheme"
            zfile = session_data.get('zVaFile', '')      # e.g., "zUI.zContainers"
            zblock = session_data.get('zBlock', '')      # e.g., "zContainers_Details"
            
            # Construct full path
            full_path_parts = []
            if zfolder:
                full_path_parts.append(zfolder)
            if zfile:
                full_path_parts.append(zfile)
            if zblock:
                full_path_parts.append(zblock)
            
            if full_path_parts:
                full_path = '.'.join(full_path_parts)
                # Initialize breadcrumbs with file path and empty trail
                z_crumbs = {
                    'trails': {
                        full_path: []  # Empty trail, but full file path is shown
                    }
                }
        
        if not z_crumbs:
            return
        
        # Phase 0.5: Use centralized banner method to filter out metadata (_context, _depth_map)
        # This ensures only user-facing trails are displayed, not internal architecture
        # NOTE: If show='static' OR if we manually initialized z_crumbs, use z_crumbs directly
        manually_initialized = ('trails' in z_crumbs and len(z_crumbs.get('trails', {})) == 1 and 
                                list(z_crumbs.get('trails', {}).values())[0] == [])
        
        if show == 'static' or manually_initialized or not (hasattr(self.display, 'zcli') and hasattr(self.display.zcli, 'navigation') and hasattr(self.display.zcli.navigation, 'breadcrumbs')):
            # Declarative mode (show='static'), manually initialized, or fallback for systems without navigation subsystem
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
        else:
            # Session-based mode (show='session'): DRY reuse breadcrumbs.zCrumbs_banner() which handles enhanced format correctly
            crumbs_display = self.display.zcli.navigation.breadcrumbs.zCrumbs_banner()
        
        # Display breadcrumbs using BasicOutputs.text()
        output_text_via_basics("", 0, False, self.display)
        # Header with PRIMARY color
        header_colored = f"{Colors.PRIMARY}{_MSG_ZCRUMBS_HEADER}{Colors.RESET}"
        output_text_via_basics(header_colored, 0, False, self.display)
        for scope, path in crumbs_display.items():
            # For declarative breadcrumbs, skip the scope prefix and just show [path]
            if scope == 'declarative':
                content = f"[{path}]"
            else:
                content = _FORMAT_CRUMB_SCOPE.format(scope=scope, path=path)
            output_text_via_basics(content, 0, False, self.display)
        # Add blank line after breadcrumbs
        output_text_via_basics("", 0, False, self.display)
    
    def zMenu(
        self, 
        menu_items: Optional[List[Tuple[Any, str]]], 
        prompt: str = _MSG_DEFAULT_MENU_PROMPT, 
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
        if try_gui_event(self.display, _EVENT_ZMENU, {
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
            output_text_via_basics("", 0, False, self.display)  # Blank line
            for number, label in menu_items:
                content = _FORMAT_MENU_ITEM.format(index=number, label=label)
                output_text_via_basics(content, 0, False, self.display)
            return None
