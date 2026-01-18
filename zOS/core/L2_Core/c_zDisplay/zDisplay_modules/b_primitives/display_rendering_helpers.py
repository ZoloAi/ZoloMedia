# zCLI/L2_Core/c_zDisplay/zDisplay_modules/b_primitives/display_rendering_helpers.py

"""
Display Rendering Helpers - Tier 1 Primitives
==============================================

This module provides DRY (Don't Repeat Yourself) utility functions extracted
from decomposed display event methods. These helpers eliminate code duplication
and establish reusable rendering patterns.

Tier Architecture:
    Tier 0: Infrastructure (display_event_helpers.py)
    Tier 1: Primitives (THIS MODULE, display_utilities.py, display_primitives.py)
    Tier 2: Basic Events (outputs, signals)
    Tier 3: Data/Input/Media/Links
    Tier 4: Advanced (advanced, timebased)
    Tier 5: Orchestration (system)

Functions:
    get_config_value(display, config_type, key, default)
        Safely access zConfig values with fallback
        Extracted from: 4+ locations (display_event_timebased, display_event_system)
    
    wrap_with_color(content, color_name, zColors)
        Wrap content with semantic color codes
        Extracted from: 3+ locations (display_event_outputs, display_event_links)
    
    apply_indent_to_lines(content, indent, indent_unit)
        Apply indentation to multi-line content
        Extracted from: 2+ locations (display_event_data)
    
    check_prefix_match(value, valid_prefixes)
        Check if value starts with any prefix from set
        Extracted from: 2+ locations (display_event_timebased)

Purpose:
    - Eliminate code duplication (DRY principle)
    - Centralize common rendering patterns
    - Improve testability and maintainability
    - Establish clear primitive layer (Linux from Scratch)

Dependencies:
    - typing: Type hints only
    - No zCLI subsystem dependencies (pure utilities)

Usage:
    from ..b_primitives.display_rendering_helpers import (
        get_config_value,
        wrap_with_color,
        apply_indent_to_lines,
        check_prefix_match
    )
"""

from typing import Any, Optional, Set


def get_config_value(display: Any, config_type: str, key: str, default: Any = None) -> Any:
    """
    Safely access zConfig values with fallback.
    
    Provides a unified way to access zConfig machine/environment settings
    with proper error handling and default fallback. Eliminates repeated
    hasattr chains and None checks across display event methods.
    
    Args:
        display: Display instance (must have .zcli.config attribute)
        config_type: Type of config to access ("machine" or "environment")
        key: Configuration key to retrieve
        default: Default value if key not found or config unavailable (default: None)
    
    Returns:
        Any: Configuration value if found, otherwise default
    
    Examples:
        >>> term = get_config_value(self.display, "machine", "terminal", "unknown")
        >>> # Returns: "xterm-256color" or "unknown" if not found
        
        >>> ide = get_config_value(self.display, "machine", "ide", None)
        >>> # Returns: "cursor" or None if not found
        
        >>> env = get_config_value(self.display, "environment", "name", "development")
        >>> # Returns: "production" or "development" if not found
    
    Replaces Pattern:
        # OLD (4+ occurrences):
        if hasattr(self.display, 'zcli') and hasattr(self.display.zcli, 'config'):
            value = self.display.zcli.config.get_machine("terminal")
            return value if value else "unknown"
        return "unknown"
        
        # NEW (1 line):
        return get_config_value(self.display, "machine", "terminal", "unknown")
    
    Used In:
        - display_event_timebased.py: _get_term_from_config()
        - display_event_timebased.py: _check_ide_capability()
        - display_event_system.py: Config access in various methods
    
    Notes:
        - Thread-safe (no state mutation)
        - Returns default if display instance lacks zcli/config
        - Returns default if config value is None or empty string
        - Supports both machine and environment config types
    """
    # Check if display instance has required attributes
    if not hasattr(display, 'zcli') or not hasattr(display.zcli, 'config'):
        return default
    
    # Access appropriate config type
    try:
        if config_type == 'machine':
            value = display.zcli.config.get_machine(key)
        elif config_type == 'environment':
            value = display.zcli.config.get_environment(key)
        else:
            return default
        
        # Return value if truthy, otherwise default
        return value if value else default
    except Exception:
        return default


def wrap_with_color(content: str, color_name: str, zColors: Any) -> str:
    """
    Wrap content with semantic color codes.
    
    Applies ANSI color codes to content using semantic color names,
    automatically adding reset codes. Provides consistent color wrapping
    across all display events.
    
    Args:
        content: Text content to colorize
        color_name: Semantic color name (e.g., "PRIMARY", "SUCCESS", "ERROR")
        zColors: Colors instance (must have get_semantic_color() and RESET)
    
    Returns:
        str: Colorized content with reset code, or original content if color not found
    
    Examples:
        >>> colored = wrap_with_color("Success!", "SUCCESS", self.zColors)
        >>> # Returns: "\033[92mSuccess!\033[0m" (green text)
        
        >>> colored = wrap_with_color("Error!", "ERROR", self.zColors)
        >>> # Returns: "\033[91mError!\033[0m" (red text)
        
        >>> colored = wrap_with_color("Info", "UNKNOWN_COLOR", self.zColors)
        >>> # Returns: "Info" (no color applied)
    
    Replaces Pattern:
        # OLD (3+ occurrences):
        color_code = self.zColors.get_semantic_color(color_name)
        if color_code:
            return f"{color_code}{content}{self.zColors.RESET}"
        return content
        
        # NEW (1 line):
        return wrap_with_color(content, color_name, self.zColors)
    
    Used In:
        - display_event_outputs.py: _apply_header_color()
        - display_event_links.py: _prompt_link_confirmation()
        - display_event_outputs.py: Various text coloring
    
    Notes:
        - Always adds RESET code when color is applied
        - Returns original content if color_name not found
        - Safe to use with empty/None content (returns as-is)
        - Thread-safe (no state mutation)
    """
    if not content:
        return content
    
    try:
        color_code = zColors.get_semantic_color(color_name)
        if color_code:
            reset_code = getattr(zColors, 'RESET', '')
            return f"{color_code}{content}{reset_code}"
    except Exception:
        pass
    
    return content


def apply_indent_to_lines(content: str, indent: int, indent_unit: str = "  ") -> str:
    """
    Apply indentation to each line of multi-line content.
    
    Splits content by newlines and prepends indentation to each line,
    maintaining original line structure. Useful for nested display
    (JSON, code blocks, nested lists).
    
    Args:
        content: Multi-line string to indent
        indent: Number of indentation units to apply
        indent_unit: String to use per indent level (default: "  " - 2 spaces)
    
    Returns:
        str: Indented content with each line prefixed
    
    Examples:
        >>> json_str = '{\n  "key": "value"\n}'
        >>> indented = apply_indent_to_lines(json_str, 2)
        >>> print(indented)
        # Output:
        #     {
        #       "key": "value"
        #     }
        
        >>> code = 'def func():\n    return True'
        >>> indented = apply_indent_to_lines(code, 1, "    ")
        >>> # Each line prefixed with 4 spaces
    
    Replaces Pattern:
        # OLD (2+ occurrences):
        indent_str = self._build_indent(indent)
        lines = content.split('\n')
        return '\n'.join(f"{indent_str}{line}" for line in lines)
        
        # NEW (1 line):
        return apply_indent_to_lines(content, indent)
    
    Used In:
        - display_event_data.py: _apply_json_indentation()
        - display_event_outputs.py: Nested text display
    
    Notes:
        - Returns original content if indent <= 0
        - Preserves empty lines (they get indented too)
        - Works with any line ending style (\n, \r\n)
        - Thread-safe (no state mutation)
    """
    if indent <= 0:
        return content
    
    indent_str = indent_unit * indent
    lines = content.split('\n')
    return '\n'.join(f"{indent_str}{line}" for line in lines)


def check_prefix_match(value: str, valid_prefixes: Set[str]) -> bool:
    """
    Check if value starts with any prefix from set (case-insensitive).
    
    Performs case-insensitive prefix matching against a set of valid
    prefixes. Useful for terminal type detection, capability checking,
    and similar pattern matching scenarios.
    
    Args:
        value: String to check for prefix match
        valid_prefixes: Set of valid prefix strings
    
    Returns:
        bool: True if value starts with any prefix, False otherwise
    
    Examples:
        >>> terms = {"xterm", "screen", "tmux", "iterm"}
        >>> check_prefix_match("xterm-256color", terms)
        True
        
        >>> check_prefix_match("screen-16color", terms)
        True
        
        >>> check_prefix_match("unknown-terminal", terms)
        False
        
        >>> check_prefix_match("XTERM-COLOR", terms)
        True  # Case-insensitive
    
    Replaces Pattern:
        # OLD (2+ occurrences):
        CAPABLE_TERMS = {"screen", "tmux", "xterm", ...}
        supports = any(
            term.lower().startswith(capable.lower()) 
            for capable in CAPABLE_TERMS
        )
        
        # NEW (1 line):
        supports = check_prefix_match(term, CAPABLE_TERMS)
    
    Used In:
        - display_event_timebased.py: _check_term_capability()
        - display_event_timebased.py: Terminal detection logic
    
    Notes:
        - Case-insensitive comparison
        - Returns False if value is empty/None
        - Returns False if valid_prefixes is empty
        - Thread-safe (no state mutation)
        - Optimized with any() for early exit
    """
    if not value or not valid_prefixes:
        return False
    
    value_lower = value.lower()
    return any(value_lower.startswith(prefix.lower()) for prefix in valid_prefixes)

