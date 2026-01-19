# zCLI/L2_Core/c_zDisplay/zDisplay_modules/f_orchestration/system_event_dashboard.py

"""
System Dashboard Events - zDash
================================

This module provides interactive dashboard display with sidebar navigation,
panel rendering, and RBAC-filtered content. zDash orchestrates the complete
dashboard workflow including panel discovery, metadata loading, and navigation.

Purpose:
    - Display dashboards with sidebar navigation
    - Load and render dashboard panels dynamically
    - Filter panels based on RBAC permissions
    - Handle interactive panel switching (Terminal)
    - Support both Terminal (interactive loop) and Bifrost (WebSocket) modes

Public Methods:
    zDash(folder, sidebar, default, _zcli, **kwargs)
        Display dashboard with interactive panel navigation

Private Helpers:
    _filter_accessible_panels(sidebar, folder, _zcli, logger)
        Filter sidebar panels based on RBAC access
        
    _build_panel_metadata(panel_name, panel_file, folder, logger)
        Extract metadata from panel file
        
    _send_zdash_bifrost_event(folder, accessible_panels, panel_metadata, default)
        Send zDash event to Bifrost frontend
        
    _run_zdash_terminal_loop(folder, accessible_panels, panel_metadata, default, _zcli, logger)
        Run interactive dashboard loop in Terminal mode
        
    _render_zdash_panel(panel_name, folder, _zcli, logger)
        Render a single dashboard panel
        
    _show_zdash_menu(accessible_panels, panel_metadata, current_panel)
        Display dashboard menu with panel options

Dependencies:
    - display_constants: _EVENT_*, _KEY_*, _MSG_*
    - display_event_helpers: try_gui_event
    - display_logging_helpers: get_display_logger
    - display_rendering_utilities: output_text_via_basics
    - zWizard.wizardzRBAC: checkzRBAC_access (for panel filtering)

Extracted From:
    display_event_system.py (lines 1243-1611)
"""

from typing import Any, Optional, Dict, List

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import try_gui_event
from ..a_infrastructure.display_logging_helpers import get_display_logger
from ..a_infrastructure.display_rendering_utilities import output_text_via_basics

# Import constants
from ..display_constants import (
    _EVENT_ZDASH,
    _KEY_FOLDER,
    _KEY_SIDEBAR,
    _KEY_DEFAULT,
    _KEY_PANELS,
    _MSG_DASHBOARD_MENU_PROMPT,
    _MSG_INVALID_PANEL_CHOICE,
    _MSG_INVALID_INPUT_FORMAT,
    _FORMAT_MENU_ITEM
)


class DashboardEvents:
    """
    Interactive dashboard with sidebar navigation and RBAC filtering.
    
    Provides zDash event for displaying multi-panel dashboards with
    built-in navigation in Terminal mode and WebSocket-based navigation
    in Bifrost mode.
    
    Composition:
        - NavigationEvents: For menu display (set after zSystem init)
        - zNav: For panel navigation (from zcli)
        - zLoader: For panel file loading (from zcli)
    
    Usage:
        # Via zSystem coordinator
        display.zEvents.zSystem.zDash(
            folder="@.UI.zAccount",
            sidebar=["Overview", "Apps", "Settings"],
            default="Overview",
            _zcli=zcli
        )
    """
    
    # Class-level type declarations
    display: Any                     # Parent zDisplay instance
    NavigationEvents: Optional[Any]  # NavigationEvents (for menu display)
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize DashboardEvents with reference to parent zDisplay instance.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Notes:
            - NavigationEvents is set to None initially
            - Will be populated by zSystem after all event packages instantiated
        """
        self.display = display_instance
        self.NavigationEvents = None  # Will be set after zSystem initialization
    
    def zDash(
        self,
        folder: str,
        sidebar: List[str],
        default: Optional[str] = None,
        _zcli: Optional[Any] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Display dashboard with interactive panel navigation (Terminal or Bifrost mode).
        
        Built-in Gate Behavior (Terminal):
        - Runs in interactive loop until user enters "done"
        - Allows panel switching between sidebar items
        - Acts as built-in gate (no need for ! modifier)
        
        Args:
            folder: Base folder for panel discovery (e.g., "@.UI.zAccount")
            sidebar: List of panel names (e.g., ["Overview", "Apps", "Settings"])
            default: Default panel to navigate to (defaults to first in sidebar)
            _zcli: zCLI instance for zLoader access
            **kwargs: Additional parameters (e.g., _context for extended metadata)
        
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
            display.zEvents.zSystem.zDash(
                folder="@.UI.zAccount",
                sidebar=["Overview", "Apps", "Settings"]
            )
        """
        # Validate sidebar
        if not sidebar:
            logger = get_display_logger(self.display)
            if logger:
                logger.warning("[zDash] No sidebar items provided")
            return None
        
        # Get zCLI instance
        if not _zcli:
            _zcli = getattr(self.display, 'zcli', None)
        
        if not _zcli:
            logger = get_display_logger(self.display)
            if logger:
                logger.error("[zDash] Cannot navigate without zCLI instance")
            return None
        
        logger = get_display_logger(self.display)
        
        # Filter panels based on RBAC access and collect metadata
        accessible_panels, panel_metadata = self._filter_accessible_panels(
            sidebar, folder, _zcli, logger
        )
        
        if not accessible_panels:
            if logger:
                logger.warning("[zDash] No accessible panels after RBAC filtering")
            if self.display.Signals:
                self.display.Signals.warning("No dashboard panels available", indent=0)
            return None
        
        # Set default panel (first accessible if not specified)
        if not default or default not in accessible_panels:
            default = accessible_panels[0]
        
        # Try Bifrost (GUI) mode first
        if self._send_zdash_bifrost_event(folder, accessible_panels, panel_metadata, default):
            return None
        
        # Terminal mode - run interactive dashboard loop
        return self._run_zdash_terminal_loop(
            folder, accessible_panels, panel_metadata, default, _zcli, logger
        )
    
    # ZDASH HELPER METHODS (Private)
    
    def _filter_accessible_panels(
        self,
        sidebar: List[str],
        folder: str,
        _zcli: Any,
        logger: Optional[Any]
    ) -> tuple:
        """
        Filter sidebar panels based on RBAC access and collect metadata.
        
        Returns:
            tuple: (accessible_panels: List[str], panel_metadata: Dict[str, Dict])
        """
        from zOS.L3_Abstraction.m_zWizard.zWizard_modules.wizardzRBAC import (
            checkzRBAC_access,
            RBAC_ACCESS_GRANTED
        )
        
        accessible_panels = []
        panel_metadata = {}
        
        for panel_name in sidebar:
            try:
                zLink_path = f"{folder}.zUI.{panel_name}"
                panel_file = _zcli.loader.handle(zPath=zLink_path) if hasattr(_zcli, 'loader') else {}
                
                # Get the panel's main block
                panel_block = panel_file.get(panel_name, {})
                
                # Check RBAC access
                rbac_result = checkzRBAC_access(
                    key=panel_name,
                    value=panel_block,
                    zcli=_zcli,
                    walker=None,
                    logger=logger if logger else _zcli.logger,
                    display=None  # Silent filter (no access denied message)
                )
                
                # Only include panel if user has access
                if rbac_result == RBAC_ACCESS_GRANTED:
                    accessible_panels.append(panel_name)
                    panel_metadata[panel_name] = self._build_panel_metadata(
                        panel_name, panel_file, folder, logger
                    )
                elif logger:
                    logger.debug(f"[zDash] Panel '{panel_name}' filtered out by RBAC")
            
            except Exception as e:
                if logger:
                    logger.error(f"[zDash] Error loading panel '{panel_name}': {e}")
        
        return accessible_panels, panel_metadata
    
    def _build_panel_metadata(
        self,
        panel_name: str,
        panel_file: Dict[str, Any],
        folder: str,
        logger: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Extract metadata from panel file for dashboard display.
        
        Returns:
            Dict[str, Any]: Panel metadata {title, icon, description, ...}
        """
        panel_block = panel_file.get(panel_name, {})
        
        # Extract zMeta if present
        zmeta = panel_block.get('zMeta', {})
        
        metadata = {
            'title': zmeta.get('title', panel_name),
            'icon': zmeta.get('icon', '📄'),
            'description': zmeta.get('description', ''),
            'zLink': f"{folder}.zUI.{panel_name}"
        }
        
        if logger:
            logger.debug(f"[zDash] Panel metadata for '{panel_name}': {metadata}")
        
        return metadata
    
    def _send_zdash_bifrost_event(
        self,
        folder: str,
        accessible_panels: List[str],
        panel_metadata: Dict[str, Dict],
        default: str
    ) -> bool:
        """
        Send zDash event to Bifrost frontend.
        
        Returns:
            bool: True if GUI event sent successfully
        """
        return try_gui_event(self.display, _EVENT_ZDASH, {
            _KEY_FOLDER: folder,
            _KEY_SIDEBAR: accessible_panels,
            _KEY_PANELS: panel_metadata,
            _KEY_DEFAULT: default
        })
    
    def _run_zdash_terminal_loop(
        self,
        folder: str,
        accessible_panels: List[str],
        panel_metadata: Dict[str, Dict],
        default: str,
        _zcli: Any,
        logger: Optional[Any]
    ) -> str:
        """
        Run interactive dashboard loop in Terminal mode.
        
        Returns:
            str: Last panel viewed
        """
        current_panel = default
        
        # Log dashboard start
        if logger:
            logger.info(f"[zDash] Starting Terminal dashboard - folder: {folder}")
            logger.info(f"[zDash] Accessible panels: {accessible_panels}")
            logger.info(f"[zDash] Default panel: {default}")
        
        # Auto-navigate to default panel on first load
        self._render_zdash_panel(current_panel, folder, _zcli, logger)
        
        # Interactive loop: show menu and navigate until "done"
        while True:
            # Show menu
            self._show_zdash_menu(accessible_panels, panel_metadata, current_panel)
            
            # Get user choice
            user_input = self.display.zPrimitives.read_string("\n> ").strip().lower()
            
            # Handle "done" command
            if user_input == "done":
                if logger:
                    logger.info("[zDash] User entered 'done' - exiting dashboard")
                break
            
            # Handle numeric choice
            try:
                choice_num = int(user_input)
                
                # Validate choice
                if 1 <= choice_num <= len(accessible_panels):
                    new_panel = accessible_panels[choice_num - 1]
                    
                    if logger:
                        logger.info(f"[zDash] User selected panel {choice_num}: {new_panel}")
                    
                    # Navigate to new panel
                    current_panel = new_panel
                    self._render_zdash_panel(current_panel, folder, _zcli, logger)
                else:
                    if logger:
                        logger.warning(f"[zDash] Invalid menu choice: {choice_num}")
                    output_text_via_basics(
                        _MSG_INVALID_PANEL_CHOICE.format(max=len(accessible_panels)),
                        0, False, self.display
                    )
            
            except ValueError:
                if logger:
                    logger.warning(f"[zDash] Invalid input (not a number or 'done'): {user_input}")
                output_text_via_basics(
                    _MSG_INVALID_INPUT_FORMAT.format(max=len(accessible_panels)),
                    0, False, self.display
                )
        
        # Dashboard loop complete
        if logger:
            logger.info("[zDash] Dashboard gate satisfied, continuing execution")
        
        return current_panel
    
    def _render_zdash_panel(
        self,
        panel_name: str,
        folder: str,
        _zcli: Any,
        logger: Optional[Any]
    ) -> None:
        """Render a single dashboard panel by navigating to it."""
        zLink_path = f"{folder}.zUI.{panel_name}"
        
        if logger:
            logger.info(f"[zDash] Rendering panel: {panel_name} (path: {zLink_path})")
        
        try:
            # Navigate to panel (triggers zDispatch for rendering)
            if hasattr(_zcli, 'navigation') and hasattr(_zcli.navigation, 'navigate'):
                _zcli.navigation.navigate(zLink_path)
            else:
                if logger:
                    logger.error(f"[zDash] Cannot navigate - zNav not available")
                if self.display.Signals:
                    self.display.Signals.error(f"Panel navigation failed: {panel_name}", indent=0)
        
        except Exception as e:
            if logger:
                logger.error(f"[zDash] Error rendering panel '{panel_name}': {e}")
            if self.display.Signals:
                self.display.Signals.error(f"Error loading panel: {panel_name}", indent=0)
    
    def _show_zdash_menu(
        self,
        accessible_panels: List[str],
        panel_metadata: Dict[str, Dict],
        current_panel: str
    ) -> None:
        """Display dashboard menu with panel options."""
        output_text_via_basics("", 0, False, self.display)
        output_text_via_basics(_MSG_DASHBOARD_MENU_PROMPT, 0, False, self.display)
        
        for idx, panel_name in enumerate(accessible_panels, 1):
            # Get panel title from metadata
            metadata = panel_metadata.get(panel_name, {})
            title = metadata.get('title', panel_name)
            icon = metadata.get('icon', '📄')
            
            # Mark current panel
            indicator = " (current)" if panel_name == current_panel else ""
            
            # Format menu item
            menu_text = _FORMAT_MENU_ITEM.format(
                index=idx,
                label=f"{icon} {title}{indicator}"
            )
            output_text_via_basics(menu_text, 0, False, self.display)
        
        # Add "done" option
        output_text_via_basics("", 0, False, self.display)
        output_text_via_basics("Enter 'done' to exit dashboard", 0, False, self.display)
