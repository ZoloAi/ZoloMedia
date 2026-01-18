# zCLI/subsystems/zDisplay/zDisplay_modules/delegates/delegate_primitives.py

"""
Primitive I/O Delegate Methods for zDisplay.

This module provides low-level input/output convenience methods that wrap
basic read and write operations. These are the most fundamental display
operations, used by higher-level events.

Methods:
    Output Primitives (3 + 3 legacy):
    - raw: Write raw content without processing (preferred)
    - line: Write content with automatic newline (preferred)
    - block: Write content as formatted block (preferred)
    - write_raw: Legacy alias for raw()
    - write_line: Legacy alias for line()
    - write_block: Legacy alias for block()
    
    Input Primitives (4):
    - read_string: Read string input from user
    - read_password: Read password input (masked)
    - read_primitive: Read string with obj parameter
    - read_password_primitive: Read password with obj parameter

Pattern:
    All methods delegate to handle() with primitive event dictionaries.
    These operations bypass formatting and go directly to Terminal or GUI I/O.

Grade: A+ (Type hints, constants, comprehensive docs)
"""

from zOS import Any, Dict
from ..display_constants import (
    _KEY_EVENT,
    _EVENT_WRITE_RAW,
    _EVENT_WRITE_LINE,
    _EVENT_WRITE_BLOCK,
    _EVENT_READ_STRING,
    _EVENT_READ_PASSWORD,
)


class DelegatePrimitives:
    """Mixin providing primitive I/O delegate methods.
    
    These are low-level read/write operations that bypass formatting
    and event processing, going directly to Terminal or GUI I/O.
    """

    # Primitive Output Delegates (Preferred API)

    def raw(self, content: str) -> Any:
        """Write raw content without processing.
        
        Args:
            content: Text to write without formatting or newline
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.raw("Loading")
            display.raw("... ")
            display.raw("Done\\n")
        """
        return self.handle({_KEY_EVENT: _EVENT_WRITE_RAW, "content": content})

    def line(self, content: str) -> Any:
        """Write content with automatic newline.
        
        Args:
            content: Text to write with automatic newline
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.line("Processing complete")
        """
        return self.handle({_KEY_EVENT: _EVENT_WRITE_LINE, "content": content})

    def block(self, content: str) -> Any:
        """Write content as a formatted block.
        
        Args:
            content: Text to write as formatted block
            
        Returns:
            Any: Result from handle() method
        """
        return self.handle({_KEY_EVENT: _EVENT_WRITE_BLOCK, "content": content})

    # Backward-Compatible Aliases (Legacy Support)

    def write_raw(self, content: str) -> Any:
        """Backward-compatible alias for raw().
        
        Note: Prefer using .raw() for cleaner API calls.
        
        Args:
            content: Text to write without formatting or newline
            
        Returns:
            Any: Result from handle() method
        """
        return self.raw(content)

    def write_line(self, content: str) -> Any:
        """Backward-compatible alias for line().
        
        Note: Prefer using .line() for cleaner API calls.
        
        Args:
            content: Text to write with automatic newline
            
        Returns:
            Any: Result from handle() method
        """
        return self.line(content)

    def write_block(self, content: str) -> Any:
        """Backward-compatible alias for block().
        
        Note: Prefer using .block() for cleaner API calls.
        
        Args:
            content: Text to write as formatted block
            
        Returns:
            Any: Result from handle() method
        """
        return self.block(content)

    # Primitive Input Delegates

    def read_string(self, prompt: str = "") -> Any:
        """Read string input from user.
        
        Args:
            prompt: Input prompt text (default: empty)
            
        Returns:
            Any: User input string from handle() method
            
        Example:
            name = display.read_string("Enter your name: ")
        """
        return self.handle({_KEY_EVENT: _EVENT_READ_STRING, "prompt": prompt})

    def read_password(self, prompt: str = "") -> Any:
        """Read password input (masked during entry).
        
        Args:
            prompt: Input prompt text (default: empty)
            
        Returns:
            Any: User input string (masked during entry)
            
        Example:
            password = display.read_password("Enter password: ")
        """
        return self.handle({_KEY_EVENT: _EVENT_READ_PASSWORD, "prompt": prompt})

    def read_primitive(self, obj: Dict[str, Any]) -> Any:
        """Read string primitive with obj parameter.
        
        Args:
            obj: Dictionary with 'prompt' key
            
        Returns:
            Any: User input string from handle() method
        """
        prompt = obj.get("prompt", "")
        return self.handle({_KEY_EVENT: _EVENT_READ_STRING, "prompt": prompt})

    def read_password_primitive(self, obj: Dict[str, Any]) -> Any:
        """Read password primitive with obj parameter.
        
        Args:
            obj: Dictionary with 'prompt' key
            
        Returns:
            Any: User input string (masked during entry)
        """
        prompt = obj.get("prompt", "")
        return self.handle({_KEY_EVENT: _EVENT_READ_PASSWORD, "prompt": prompt})

