# zCLI/L2_Core/c_zDisplay/zDisplay_modules/f_orchestration/system_event_declare.py

"""
System Declaration Events - zDeclare
=====================================

This module provides system message display with log-level conditioning and
deployment-aware visibility. zDeclare is used for debug flow visualization in
terminal mode, showing system initialization and state changes.

Purpose:
    - Display system messages (e.g., "Session Initialized", "Loading Config...")
    - Respect deployment mode (dev: show, prod/test: hide)
    - Auto-select header style based on indentation level
    - Log-level aware (only show if appropriate)

Public Methods:
    zDeclare(label, color, indent, style)
        Display system declaration/message with log-level conditioning

Dependencies:
    - display_constants: COLOR_*, STYLE_*, DEFAULT_*
    - display_logging_helpers: should_show_system_message
    - BasicOutputs (via cross-reference): header() for rendering

Extracted From:
    display_event_system.py (lines 685-757)
"""

from typing import Any, Optional

# Import constants
from ..display_constants import (
    COLOR_RESET,
    STYLE_FULL,
    STYLE_SINGLE,
    STYLE_WAVE,
    DEFAULT_INDENT,
    DEFAULT_STYLE
)

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_logging_helpers import should_show_system_message


class DeclareEvents:
    """
    System declaration/message display with log-level conditioning.
    
    Provides the zDeclare event for displaying system messages in Terminal mode.
    Messages are conditionally displayed based on deployment mode and logging level.
    
    Composition:
        - BasicOutputs: For header() rendering (set after zEvents init)
    
    Usage:
        # Via zSystem coordinator
        zcli.display.zEvents.zSystem.zDeclare("Session Initialized", color="MAIN")
        
        # With auto-style selection
        zcli.display.zEvents.zSystem.zDeclare("Loading...", indent=1)  # Uses "single" style
    """
    
    # Class-level type declarations
    display: Any          # Parent zDisplay instance
    BasicOutputs: Optional[Any]  # BasicOutputs event package (set after init)
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize DeclareEvents with reference to parent zDisplay instance.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Notes:
            - BasicOutputs is set to None initially
            - Will be populated by zSystem after all event packages instantiated
        """
        self.display = display_instance
        self.BasicOutputs = None  # Will be set after zEvents initialization
    
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
        if not should_show_system_message(self.display):
            return
        
        # zDeclare is Terminal-only: skip in zBifrost/GUI mode
        # System messages are for debug flow visualization in terminal, not user-facing UI
        if self.display.zPrimitives and self.display.zPrimitives._is_gui_mode():
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
