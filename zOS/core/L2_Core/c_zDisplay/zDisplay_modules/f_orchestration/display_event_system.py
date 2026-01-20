# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_system.py
"""
zSystem - zCLI System Introspection & Navigation UI Events (v1.5.4+)
=====================================================================

This module provides system-level user interface events for the zDisplay subsystem,
enabling comprehensive introspection and display of zCLI's internal state across both
Terminal and Bifrost (GUI) modes.

REFACTORING v2.0 (Phase 3 Complete):
    - Decomposed monolith (2,363 lines) into 5 specialized modules
    - Tiered architecture (Tier 0 Infrastructure → Tier 2 Events)
    - DRY refactoring with shared infrastructure helpers
    - Composition pattern: zSystemEvents orchestrates specialized modules

ARCHITECTURE: System-Level UI Integration

zSystem is unique among zDisplay event packages as it operates at the **system level**,
directly interacting with zCLI's core state management structures.

Integration Flow:
    zCLI core → zSystem (coordinator) → Specialized Modules → zDisplay → zPrimitives

Module Decomposition:
    1. system_event_declare.py      - zDeclare (system messages)
    2. system_event_navigation.py   - zCrumbs, zMenu (navigation UI)
    3. system_event_session.py      - zSession, zConfig (state display)
    4. system_event_dialog.py       - zDialog (form collection)
    5. system_event_dashboard.py    - zDash (interactive dashboards)

PUBLIC METHODS (Delegated to Specialized Modules):

    zDeclare(label, color, indent, style)
        Display system message (e.g., "Session Initialized")
        → Delegates to: DeclareEvents

    zCrumbs(session_data)
        Display breadcrumb navigation trail
        → Delegates to: NavigationEvents

    zMenu(menu_items, prompt, return_selection)
        Display menu options and optionally collect selection
        → Delegates to: NavigationEvents

    zSession(session_data, break_after, break_message)
        Display complete zCLI session state
        → Delegates to: SessionEvents

    zConfig(config_data, break_after, break_message)
        Display zConfig machine/environment configuration
        → Delegates to: SessionEvents

    zDialog(context, _zcli, _walker)
        Display form dialog and collect validated input
        → Delegates to: DialogEvents

    zDash(folder, sidebar, default, _zcli)
        Display dashboard with interactive panel navigation
        → Delegates to: DashboardEvents

ZSESSION INTEGRATION (19 Core Session Keys):

Core Session Fields (Imported from zConfig):
    SESSION_KEY_ZS_ID, SESSION_KEY_ZMODE, SESSION_KEY_ZMACHINE, SESSION_KEY_ZAUTH,
    SESSION_KEY_ZSPACE, SESSION_KEY_ZVAFOLDER, SESSION_KEY_ZVAFILE, SESSION_KEY_ZBLOCK,
    SESSION_KEY_ZCRUMBS, SESSION_KEY_ZCACHE, SESSION_KEY_WIZARD_MODE, SESSION_KEY_ZSPARK,
    SESSION_KEY_VIRTUAL_ENV, SESSION_KEY_SYSTEM_ENV, SESSION_KEY_ZLOGGER,
    SESSION_KEY_ZTRACEBACK, SESSION_KEY_LOGGER_INSTANCE, SESSION_KEY_ZVARS, SESSION_KEY_ZSHORTCUTS

ZAUTH INTEGRATION (Three-Tier Authentication Model):

Layer 1 - zSession Auth (Internal zCLI/Zolo Users)
Layer 2 - Application Auth (External App Users, Multi-App Support)
Layer 3 - Dual-Auth (Simultaneous zSession + Application)

ZCACHE INTEGRATION (4-Tier Caching System):

Tier 1 - System Cache (SESSION_KEY_ZCACHE + ZCACHE_KEY_SYSTEM)
Tier 2 - Pinned Cache (ZCACHE_KEY_PINNED)
Tier 3 - Schema Cache (ZCACHE_KEY_SCHEMA)
Tier 4 - Plugin Cache (ZCACHE_KEY_PLUGIN)
"""

from typing import Any, Optional, Dict, List, Tuple, Union

# Import specialized event modules (Phase 3 Decomposition)
from .system_event_declare import DeclareEvents
from .system_event_navigation import NavigationEvents
from .system_event_session import SessionEvents
from .system_event_dialog import DialogEvents
from .system_event_dashboard import DashboardEvents

# Import constants
from ..display_constants import (
    DEFAULT_INDENT,
    DEFAULT_STYLE,
    DEFAULT_MENU_PROMPT
)


class zSystem:
    """
    zCLI System Introspection & Navigation UI Events (v2.0 - Refactored).
    
    COORDINATOR CLASS - Orchestrates specialized event modules via composition.
    
    This class no longer contains implementation logic. Instead, it instantiates
    and coordinates 5 specialized event modules, delegating all public methods
    to the appropriate module.
    
    Composition:
        - DeclareEvents: System messages (zDeclare)
        - NavigationEvents: Navigation UI (zCrumbs, zMenu)
        - SessionEvents: State display (zSession, zConfig)
        - DialogEvents: Form collection (zDialog)
        - DashboardEvents: Interactive dashboards (zDash)
    
    Usage:
        # Via zDisplay
        zcli.display.zEvents.zSystem.zSession(zcli.session)
        zcli.display.zEvents.zSystem.zMenu(menu_items, return_selection=True)
        zcli.display.zEvents.zSystem.zDash("@.UI.zAccount", sidebar=["Overview", "Apps"])
    
    Architecture:
        Before (v1.x):  2,363 lines, monolithic
        After (v2.0):   ~200 lines, coordinator + 5 specialized modules (~2,050 lines total)
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    BasicOutputs: Optional[Any]
    BasicInputs: Optional[Any]
    Signals: Optional[Any]
    
    # Specialized event modules (Phase 3 Decomposition)
    DeclareEvents: DeclareEvents
    NavigationEvents: NavigationEvents
    SessionEvents: SessionEvents
    DialogEvents: DialogEvents
    DashboardEvents: DashboardEvents
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize zSystem coordinator with specialized modules.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Phase 3 Refactoring:
            - Instantiate 5 specialized event modules
            - Cross-wire dependencies (BasicOutputs, BasicInputs, Signals)
            - Maintain backward compatibility (same public API)
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        
        # Will be set after zEvents initialization
        self.BasicOutputs = None
        self.BasicInputs = None
        self.Signals = None
        
        # Instantiate specialized event modules (Phase 3)
        self.DeclareEvents = DeclareEvents(display_instance)
        self.NavigationEvents = NavigationEvents(display_instance)
        self.SessionEvents = SessionEvents(display_instance)
        self.DialogEvents = DialogEvents(display_instance)
        self.DashboardEvents = DashboardEvents(display_instance)
        
        # Cross-wire dependencies (will be updated after zEvents init)
        self._update_cross_references()
    
    def _update_cross_references(self) -> None:
        """
        Update cross-references between specialized modules.
        
        Called after zEvents initialization to wire up dependencies:
        - BasicOutputs, BasicInputs, Signals
        - Inter-module references (e.g., DialogEvents needs DeclareEvents)
        """
        # Wire BasicOutputs to all modules
        self.DeclareEvents.BasicOutputs = self.BasicOutputs
        self.NavigationEvents.BasicOutputs = self.BasicOutputs
        self.SessionEvents.BasicOutputs = self.BasicOutputs
        
        # Wire BasicInputs to modules that need it
        self.NavigationEvents.BasicInputs = self.BasicInputs
        
        # Wire inter-module dependencies
        self.SessionEvents.DeclareEvents = self.DeclareEvents
        self.DialogEvents.DeclareEvents = self.DeclareEvents
        self.DialogEvents.Signals = self.Signals
        self.DashboardEvents.NavigationEvents = self.NavigationEvents
    
    # PUBLIC METHODS (Delegation to Specialized Modules)
    
    def zDeclare(
        self,
        label: str,
        color: Optional[str] = None,
        indent: int = DEFAULT_INDENT,
        style: Optional[str] = DEFAULT_STYLE
    ) -> None:
        """
        Display system declaration/message with log-level conditioning.
        
        Delegates to: DeclareEvents.zDeclare()
        """
        return self.DeclareEvents.zDeclare(label, color, indent, style)
    
    def zCrumbs(self, session_data: Optional[Dict[str, Any]] = None, parent: Optional[str] = None, show: str = 'session') -> None:
        """
        Display breadcrumb navigation trail.
        
        Delegates to: NavigationEvents.zCrumbs()
        
        Args:
            session_data: Session dict (defaults to self.display.zcli.session if None)
            parent: Declarative parent path (works in both Terminal and Bifrost, e.g., "zProducts.zTheme")
            show: Display mode - 'session' (default, session-based) or 'static' (declarative from parent)
        
        Note: session_data defaults to self.display.zcli.session if None
        """
        if session_data is None and hasattr(self.display, 'zcli'):
            session_data = self.display.zcli.session
        
        return self.NavigationEvents.zCrumbs(session_data, parent=parent, show=show)
    
    def zMenu(
        self,
        menu_items: Optional[List[Tuple[Any, str]]],
        prompt: str = DEFAULT_MENU_PROMPT,
        return_selection: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """
        Display menu options and optionally collect user selection.
        
        Delegates to: NavigationEvents.zMenu()
        """
        return self.NavigationEvents.zMenu(menu_items, prompt, return_selection)
    
    def zSession(
        self,
        session_data: Optional[Dict[str, Any]],
        break_after: bool = True,
        break_message: Optional[str] = None
    ) -> None:
        """
        Display complete zCLI session state.
        
        Delegates to: SessionEvents.zSession()
        """
        return self.SessionEvents.zSession(session_data, break_after, break_message)
    
    def zConfig(
        self,
        config_data: Optional[Dict[str, Any]] = None,
        break_after: bool = True,
        break_message: Optional[str] = None
    ) -> None:
        """
        Display zConfig machine and environment configuration.
        
        Delegates to: SessionEvents.zConfig()
        """
        return self.SessionEvents.zConfig(config_data, break_after, break_message)
    
    def zDialog(
        self,
        context: Dict[str, Any],
        _zcli: Optional[Any] = None,
        _walker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Display form dialog and collect validated input.
        
        Delegates to: DialogEvents.zDialog()
        """
        return self.DialogEvents.zDialog(context, _zcli, _walker)
    
    def zDash(
        self,
        folder: str,
        sidebar: List[str],
        default: Optional[str] = None,
        _zcli: Optional[Any] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Display dashboard with interactive panel navigation.
        
        Delegates to: DashboardEvents.zDash()
        """
        return self.DashboardEvents.zDash(folder, sidebar, default, _zcli, **kwargs)
