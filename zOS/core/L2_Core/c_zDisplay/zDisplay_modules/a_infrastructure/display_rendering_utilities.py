# zCLI/L2_Core/c_zDisplay/zDisplay_modules/a_infrastructure/display_rendering_utilities.py

"""
Display Rendering Utilities - Tier 0 Infrastructure
====================================================

This module provides reusable rendering helpers for all display events.
It centralizes common patterns for field rendering, section display, and
text output to enforce DRY principles across the zDisplay system.

Tier Architecture:
    Tier 0: Infrastructure (THIS MODULE) - Shared rendering utilities
    Tier 1: Primitives - Raw I/O foundation
    Tier 2+: Event packages - Use these utilities for consistent rendering

Purpose:
    - DRY: Single implementation for field/section rendering
    - Consistency: Same formatting across all events
    - Testability: Unit tests for rendering logic
    - Maintainability: One place to update rendering behavior

Functions:
    render_field(label, value, indent, color, display)
        Render a labeled field with color formatting
        
    render_section_title(title, indent, color, display)
        Render a section title with color formatting
        
    get_color_code(color_name, zColors)
        Get ANSI color code with fallback to RESET
        
    output_text_via_basics(content, indent, break_after, display)
        Output text via BasicOutputs if available
        
    format_value_for_display(value, max_length)
        Format value for display (handle bool, None, dict, list, long strings)

Dependencies:
    - typing: Type hints
    - zOS.core.zSys.formatting.colors: Colors class for ANSI codes

Extracted From:
    - display_event_system._display_field() (1 occurrence)
    - display_event_system._display_section() (1 occurrence)
    - display_event_system._get_color() (1 occurrence)
    - display_event_system._output_text() (1 occurrence)
    - Similar patterns in display_event_advanced, display_event_data
"""

from typing import Any, Optional


def render_field(
    label: str,
    value: Any,
    indent: int,
    color: str,
    display: Any
) -> None:
    """
    Render a labeled field with color formatting (Terminal).
    
    This is the standard way to display key-value pairs across all
    zDisplay events. It provides consistent formatting with colored
    labels and proper indentation.
    
    Args:
        label: Field label text (e.g., "Username", "zSession_ID")
        value: Field value to display (any type, converted to string)
        indent: Indentation level (0 = no indent)
        color: Color name for label (e.g., "GREEN", "YELLOW", "CYAN")
        display: zDisplay instance (for accessing BasicOutputs and zColors)
    
    Returns:
        None
    
    Format:
        <color>label:<reset> value
    
    Example Output:
        Username: admin          (with colored "Username:")
        zSession_ID: abc123     (with colored "zSession_ID:")
    
    Usage:
        render_field("Username", "admin", indent=0, color="GREEN", display=self.display)
        render_field("  Role", "developer", indent=1, color="YELLOW", display=self.display)
    
    Notes:
        - Gracefully handles missing BasicOutputs (no-op if unavailable)
        - Converts value to string automatically
        - Color name resolved via get_color_code()
    
    Extracted From:
        display_event_system._display_field() (line 1957-1988)
    """
    if not display or not hasattr(display, 'zEvents') or not display.zEvents.BasicOutputs:
        return
    
    color_code = get_color_code(color, display.zColors)
    content = f"{color_code}{label}:{display.zColors.RESET} {value}"
    output_text_via_basics(content, indent, break_after=False, display=display)


def render_section_title(
    title: str,
    indent: int,
    color: str,
    display: Any
) -> None:
    """
    Render a section title with color formatting (Terminal).
    
    This is the standard way to display section headers across all
    zDisplay events. It provides consistent formatting with colored
    titles and proper indentation.
    
    Args:
        title: Section title text (e.g., "zMachine", "Tool Preferences")
        indent: Indentation level (0 = no indent)
        color: Color name for title (e.g., "GREEN", "CYAN")
        display: zDisplay instance (for accessing BasicOutputs and zColors)
    
    Returns:
        None
    
    Format:
        <color>title:<reset>
    
    Example Output:
        zMachine:                (with colored "zMachine:")
        Tool Preferences:        (with colored "Tool Preferences:")
    
    Usage:
        render_section_title("zMachine", indent=0, color="GREEN", display=self.display)
        render_section_title("  Tool Preferences", indent=1, color="CYAN", display=self.display)
    
    Notes:
        - Gracefully handles missing BasicOutputs (no-op if unavailable)
        - Color name resolved via get_color_code()
        - Similar to render_field but without value (title-only)
    
    Extracted From:
        display_event_system._display_section() (line 1990-2019)
    """
    if not display or not hasattr(display, 'zEvents') or not display.zEvents.BasicOutputs:
        return
    
    color_code = get_color_code(color, display.zColors)
    content = f"{color_code}{title}:{display.zColors.RESET}"
    output_text_via_basics(content, indent, break_after=False, display=display)


def get_color_code(color_name: str, zColors: Any) -> str:
    """
    Get ANSI color code from zColors with fallback to RESET.
    
    This is a safe wrapper for accessing color codes that ensures
    invalid color names don't crash the application.
    
    Args:
        color_name: Color attribute name (e.g., "GREEN", "YELLOW", "CYAN")
        zColors: Colors instance from display.zColors
    
    Returns:
        str: ANSI color code from zColors, or RESET if not found
    
    Example:
        >>> get_color_code("GREEN", display.zColors)
        "\\033[92m"  # ANSI green
        
        >>> get_color_code("INVALID_COLOR", display.zColors)
        "\\033[0m"   # RESET (fallback)
    
    Usage:
        color_code = get_color_code("GREEN", self.zColors)
        print(f"{color_code}Success!{self.zColors.RESET}")
    
    Notes:
        - Always returns a valid string (never None)
        - Fallback to RESET ensures safe concatenation
        - Uses getattr for safe attribute access
    
    Extracted From:
        display_event_system._get_color() (line 667-680)
    """
    if not zColors:
        return ""
    return getattr(zColors, color_name, getattr(zColors, 'RESET', ''))


def output_text_via_basics(
    content: str,
    indent: int,
    break_after: bool,
    display: Any
) -> None:
    """
    Output text via BasicOutputs if available (DRY helper).
    
    This is a convenience wrapper for BasicOutputs.text() that handles
    the case where BasicOutputs might not be available yet.
    
    Args:
        content: Text content to display
        indent: Indentation level (0 = no indent)
        break_after: Add line break after text (default: False)
        display: zDisplay instance (for accessing BasicOutputs)
    
    Returns:
        None
    
    Example:
        output_text_via_basics("Hello, world!", indent=0, break_after=False, display=self.display)
        output_text_via_basics("  Indented text", indent=1, break_after=True, display=self.display)
    
    Usage:
        output_text_via_basics("Status: OK", 0, False, self.display)
    
    Notes:
        - Gracefully handles missing BasicOutputs (no-op if unavailable)
        - Delegates to BasicOutputs.text() for actual rendering
        - Used by render_field() and render_section_title()
    
    Extracted From:
        display_event_system._output_text() (line 644-665)
    """
    if not display or not hasattr(display, 'zEvents') or not display.zEvents.BasicOutputs:
        return
    display.zEvents.BasicOutputs.text(content, indent=indent, break_after=break_after)


def format_value_for_display(value: Any, max_length: int = 60) -> str:
    """
    Format value for display (handle bool, None, dict, list, long strings).
    
    This provides consistent formatting for different value types,
    ensuring terminal output is readable and doesn't overflow.
    
    Args:
        value: Value to format (any type)
        max_length: Maximum string length before truncation (default: 60)
    
    Returns:
        str: Formatted value string
    
    Formatting Rules:
        - bool: "True" or "False" (capitalized)
        - None: "None"
        - dict/list: str(value), truncated with "..." if > max_length
        - str: Truncated with "..." if > max_length
        - other: str(value)
    
    Example:
        >>> format_value_for_display(True)
        "True"
        
        >>> format_value_for_display(None)
        "None"
        
        >>> format_value_for_display({"key": "value", "another": "long value here"})
        "{'key': 'value', 'another': 'long value here'}"  # or truncated
        
        >>> format_value_for_display("A" * 100, max_length=60)
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA..."
    
    Usage:
        # In zSession display
        for key, val in config.items():
            formatted = format_value_for_display(val)
            render_field(key, formatted, 0, "GREEN", self.display)
    
    Notes:
        - Prevents terminal overflow with long values
        - Consistent formatting across all events
        - Used by zSession, zConfig, and other system events
    
    Similar To:
        display_event_system.zConfig() (line 1022-1033, 1044-1055)
    """
    # Format booleans
    if isinstance(value, bool):
        return "True" if value else "False"
    
    # Format None
    if value is None:
        return "None"
    
    # Format dict/list
    if isinstance(value, (dict, list)):
        value_str = str(value)
        if len(value_str) > max_length:
            return value_str[:max_length - 3] + "..."
        return value_str
    
    # Format string
    value_str = str(value)
    if len(value_str) > max_length:
        return value_str[:max_length - 3] + "..."
    
    return value_str
