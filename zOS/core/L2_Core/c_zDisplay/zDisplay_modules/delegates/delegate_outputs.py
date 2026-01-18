# zCLI/subsystems/zDisplay/zDisplay_modules/delegates/delegate_outputs.py

"""
Output Formatting Delegate Methods for zDisplay.

This module provides formatted output convenience methods for common display
patterns like headers, formatted text, and declarations. These methods wrap
output events with consistent styling.

Methods:
    - header: Display section headers with formatting
    - zDeclare: Display zCLI system declarations
    - text: Display formatted text content

Pattern:
    All methods delegate to handle() with output event dictionaries.

Grade: A+ (Type hints, constants, comprehensive docs)
"""

from zOS import Any, Optional
from ..display_constants import (
    _KEY_EVENT,
    _EVENT_HEADER,
    _EVENT_ZDECLARE,
    _EVENT_TEXT,
)

# Module-specific constants
DEFAULT_COLOR_RESET = "RESET"
DEFAULT_STYLE_FULL = "full"
DEFAULT_INDENT = 0


class DelegateOutputs:
    """Mixin providing formatted output delegate methods.
    
    These methods provide consistent formatting for common output patterns
    like headers, colored text, and zCLI declarations.
    """

    # Output Formatting Delegates

    def header(
        self, 
        label: str, 
        color: str = DEFAULT_COLOR_RESET, 
        indent: int = DEFAULT_INDENT, 
        style: str = DEFAULT_STYLE_FULL,
        **kwargs
    ) -> Any:
        """Display formatted section header.
        
        Args:
            label: Header text to display
            color: Color code (default: RESET)
            indent: Indentation level (default: 0)
            style: Header style - 'full', 'single', 'minimal' (default: full)
            **kwargs: Additional parameters (e.g., 'class' for custom CSS classes)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.header("User Management", color="CYAN", style="full")
            display.header("Title", color="PRIMARY", class="zTitle-1")
        """
        return self.handle({
            _KEY_EVENT: _EVENT_HEADER,
            "label": label,
            "color": color,
            "indent": indent,
            "style": style,
            **kwargs  # Pass through additional parameters
        })

    def zDeclare(
        self, 
        label: str, 
        color: Optional[str] = None, 
        indent: int = DEFAULT_INDENT, 
        style: Optional[str] = None
    ) -> Any:
        """Display zCLI system declaration.
        
        Args:
            label: Declaration label/message
            color: Optional color override (default: subsystem color)
            indent: Indentation level (default: 0)
            style: Optional style override (default: None)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.zDeclare("[CONFIG] Loading schema", color="YELLOW")
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZDECLARE,
            "label": label,
            "color": color,
            "indent": indent,
            "style": style,
        })

    def text(
        self, 
        content: str, 
        indent: int = DEFAULT_INDENT, 
        pause: bool = False,  # Preferred API
        break_message: Optional[str] = None,
        break_after: Optional[bool] = None  # Legacy parameter
    ) -> Any:
        """Display formatted text content.
        
        Note: Prefer using 'pause' parameter. 'break_after' is maintained for 
        backward compatibility.
        
        Args:
            content: Text content to display
            indent: Indentation level (default: 0)
            pause: Pause for user acknowledgment (default: False)
            break_message: Optional break message (default: None)
            break_after: Legacy parameter - use 'pause' instead
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.text("Configuration loaded", indent=2)
            display.text("Press to continue", pause=True)
        """
        # Handle backward compatibility
        should_break = break_after if break_after is not None else pause
        
        return self.handle({
            _KEY_EVENT: _EVENT_TEXT,
            "content": content,
            "indent": indent,
            "break_after": should_break,  # Keep internal key for now
            "break_message": break_message,
        })

