# zCLI/subsystems/zDisplay/zDisplay_modules/delegates/delegate_signals.py

"""
Signal Event Delegate Methods for zDisplay.

This module provides status signal convenience methods for common user feedback
patterns like errors, warnings, success messages, and info notices. These are
high-level semantic methods that convey meaning through both content and styling.

Methods:
    - error: Display error messages
    - warning: Display warning messages
    - success: Display success messages
    - info: Display informational messages
    - zMarker: Display zCLI markers (breadcrumbs, indicators)

Pattern:
    All methods delegate to handle() with signal event dictionaries.
    Color and styling are typically handled by the event processor.

Grade: A+ (Type hints, constants, comprehensive docs)
"""

from zOS import Any
from ..display_constants import (
    _KEY_EVENT,
    _EVENT_ERROR,
    _EVENT_WARNING,
    _EVENT_SUCCESS,
    _EVENT_INFO,
    _EVENT_ZMARKER,
)

# Module-specific constants
DEFAULT_INDENT = 0
_DEFAULT_MARKER_LABEL = "Marker"
DEFAULT_COLOR_MAGENTA = "MAGENTA"


class DelegateSignals:
    """Mixin providing signal event delegate methods.
    
    These methods provide consistent semantic signaling for user feedback,
    typically with automatic color coding based on signal type.
    """

    # Signal Event Delegates

    def error(self, content: str, indent: int = DEFAULT_INDENT) -> Any:
        """Display error message with ERROR styling.
        
        Args:
            content: Error message text to display
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.error("File not found: config.yaml")
            display.error("Connection failed", indent=2)
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ERROR,
            "content": content,
            "indent": indent,
        })

    def warning(self, content: str, indent: int = DEFAULT_INDENT) -> Any:
        """Display warning message with WARNING styling.
        
        Args:
            content: Warning message text to display
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.warning("Cache is full, consider clearing")
        """
        return self.handle({
            _KEY_EVENT: _EVENT_WARNING,
            "content": content,
            "indent": indent,
        })

    def success(self, content: str, indent: int = DEFAULT_INDENT) -> Any:
        """Display success message with SUCCESS styling.
        
        Args:
            content: Success message text to display
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.success("User created successfully")
            display.success("Operation completed", indent=1)
        """
        return self.handle({
            _KEY_EVENT: _EVENT_SUCCESS,
            "content": content,
            "indent": indent,
        })

    def info(self, content: str, indent: int = DEFAULT_INDENT) -> Any:
        """Display informational message with INFO styling.
        
        Args:
            content: Info message text to display
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.info("Processing 10 records...")
        """
        return self.handle({
            _KEY_EVENT: _EVENT_INFO,
            "content": content,
            "indent": indent,
        })

    def zMarker(
        self, 
        label: str = _DEFAULT_MARKER_LABEL, 
        color: str = DEFAULT_COLOR_MAGENTA, 
        indent: int = DEFAULT_INDENT
    ) -> Any:
        """Display zCLI marker for visual separation.
        
        Args:
            label: Marker label text (default: "Marker")
            color: Color code (default: MAGENTA)
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.zMarker("Checkpoint 1", color="CYAN")
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZMARKER,
            "label": label,
            "color": color,
            "indent": indent,
        })

