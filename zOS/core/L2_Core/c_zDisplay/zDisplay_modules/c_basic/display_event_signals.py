# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_signals.py

"""
Signals - Colored Feedback Messages for User Notifications
===========================================================

This event package provides colored feedback signals for user notifications,
building on the BasicOutputs A+ foundation (Week 6.4.7 complete).

Composition Architecture
------------------------
Signals builds on BasicOutputs (the A+ grade foundation):

Layer 3: display_delegates.py (PRIMARY API)
    ↓
Layer 2: display_events.py (ORCHESTRATOR)
    ↓
Layer 2: events/display_event_signals.py (Signals) ← THIS MODULE
    ↓
Layer 2: events/display_event_outputs.py (BasicOutputs) ← A+ FOUNDATION
    ↓
Layer 1: display_primitives.py (FOUNDATION I/O)

Composition Flow:
1. Signals method called (e.g., error())
2. Try GUI mode via primitives.send_gui_event()
3. If terminal mode:
   a. Apply semantic color to content
   b. Call BasicOutputs.text() for output
   c. BasicOutputs handles indentation + I/O via primitives

Signal Types & Color Semantics
-------------------------------
Signals provides 5 feedback methods with industry-standard semantic colors:

**Feedback Signals (4):**
1. **error(content, indent)** - RED
   - Critical errors, validation failures
   - Used by: AdvancedData (data validation), zAuth (auth failures)

2. **warning(content, indent)** - YELLOW
   - Warnings, deprecations, cautions
   - Used by: zSystem (system operations)

3. **success(content, indent)** - GREEN
   - Success confirmations, completions
   - Used by: zSystem (operation success)

4. **info(content, indent)** - CYAN
   - Informational messages, hints
   - Used by: zSystem (info messages)

**Flow Control (1):**
5. **zMarker(label, color, indent)** - MAGENTA (default)
   - Visual workflow separators
   - Creates marker lines with centered label
   - Used by: zSystem (workflow stages)

Dual-Mode I/O Pattern
----------------------
All signal methods implement the same dual-mode pattern:

1. **GUI Mode (Bifrost):** Try send_gui_event() first
   - Send clean JSON event with signal type + data
   - Returns True if successful
   - GUI frontend applies semantic colors

2. **Terminal Mode (Fallback):** Apply color + compose
   - Apply semantic color using zColors
   - Call BasicOutputs.text() for output
   - BasicOutputs handles dual-mode I/O + indentation

Benefits of Composition
-----------------------
- **Reuses BasicOutputs logic:** Indentation, I/O, dual-mode handling
- **Consistent behavior:** All events use same I/O primitives
- **Fallback safety:** Handles BasicOutputs initialization race conditions
- **Single responsibility:** Signals only handles colors + semantics

Layer Position
--------------
Signals occupies the Event Layer in the zDisplay architecture:
- **Depends on:** BasicOutputs (A+ foundation)
- **Used by:** AdvancedData (error messages), zSystem (warnings), zAuth (error feedback)
- **Dependency:** BasicOutputs must be wired after initialization (done by display_events.py)

Usage Statistics
----------------
- **17 total references** across 4 files
- **Used by 3 packages:** AdvancedData, zSystem, zAuth
- **5 signal methods** (error, warning, success, info, zMarker)

zCLI Integration
----------------
- **Initialized by:** display_events.py (zEvents.__init__)
- **Cross-referenced:** BasicOutputs wired after init (lines 225-228 in display_events.py)
- **Accessed via:** zcli.display.zEvents.Signals
- **No session access** - delegates to primitives + BasicOutputs

Thread Safety
-------------
Not thread-safe. All display operations should occur on the main thread or
with appropriate synchronization.

Example
-------
```python
# Via display_events orchestrator:
events = zEvents(display_instance)
events.Signals.error("Operation failed")
events.Signals.warning("Deprecated feature", indent=1)
events.Signals.success("Task complete!")
events.Signals.info("Hint: Use --verbose for details")
events.Signals.zMarker("Processing Stage 2")

# Direct usage (rare):
signals = Signals(display_instance)
signals.BasicOutputs = basic_outputs  # Must wire dependency
signals.error("Critical error")
```
"""

from zOS import Any, Optional

# Import constants from centralized module
from ..display_constants import (
    _EVENT_NAME_ERROR,
    _EVENT_NAME_WARNING,
    _EVENT_NAME_SUCCESS,
    _EVENT_NAME_INFO,
    _EVENT_NAME_ZMARKER,
    COLOR_RED,
    COLOR_YELLOW,
    COLOR_GREEN,
    COLOR_CYAN,
    COLOR_ERROR,
    COLOR_WARNING,
    COLOR_SUCCESS,
    COLOR_INFO,
    COLOR_MAGENTA,
    COLOR_RESET,
    _KEY_CONTENT,
    _KEY_INDENT,
    _KEY_LABEL,
    _KEY_COLOR,
    DEFAULT_INDENT,
    _DEFAULT_MARKER_LABEL,
    _DEFAULT_MARKER_COLOR,
    _MARKER_LINE_CHAR,
    _MARKER_LINE_WIDTH,
    _EMPTY_LINE,
    _INDENT_STR,
)

# Signals Class

class Signals:
    """Colored feedback signals for user notifications.
    
    Builds on BasicOutputs (A+ foundation) to provide semantic colored
    feedback messages. Implements composition pattern where Signals applies
    colors and BasicOutputs handles I/O.
    
    **Composition:**
    - Depends on BasicOutputs (A+ grade, Week 6.4.7)
    - Pattern: Apply color → Call BasicOutputs.text()
    - Benefits: Reuses BasicOutputs logic (indent, I/O, dual-mode)
    
    **Signal Types:**
    - error() - RED - Critical errors, validation failures
    - warning() - YELLOW - Warnings, deprecations, cautions
    - success() - GREEN - Success confirmations, completions
    - info() - CYAN - Informational messages, hints
    - zMarker() - MAGENTA (default) - Visual workflow separators
    
    **Usage:**
    - 17 references across 4 files
    - Used by: AdvancedData, zSystem, zAuth
    
    **Pattern:**
    All methods implement dual-mode I/O (GUI-first, terminal fallback).
    """

    # Type hints for instance attributes
    display: Any  # Parent zDisplay instance
    zPrimitives: Any  # Primitives instance for I/O operations
    zColors: Any  # Colors instance for terminal styling
    BasicOutputs: Optional[Any]  # BasicOutputs instance for composition (wired after init)

    def __init__(self, display_instance: Any) -> None:
        """Initialize Signals with parent display reference.
        
        Args:
            display_instance: Parent zDisplay instance providing primitives and colors
            
        Note:
            BasicOutputs is set to None initially and wired after initialization
            by display_events.py to avoid circular dependencies. The fallback
            logic handles the rare edge case where BasicOutputs is not yet set.
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        # Get reference to BasicOutputs for composition
        self.BasicOutputs = None  # Will be set after zEvents initialization

    # Helper Methods

    def _colorize(self, content: str, color_attr: str) -> str:
        """Apply semantic color to content (DRY helper).
        
        Args:
            content: Text content to colorize
            color_attr: Color attribute name (e.g., "RED", "GREEN")
            
        Returns:
            str: Colorized content with RESET suffix
            
        Note:
            This helper eliminates 4 duplicate color application patterns.
        """
        color_code = getattr(self.zColors, color_attr, self.zColors.RESET)
        return f"{color_code}{content}{self.zColors.RESET}"

    def _output_text(self, content: str, indent: int, break_after: bool = False) -> None:
        """Output text via BasicOutputs with fallback (DRY helper).
        
        Args:
            content: Text content to output
            indent: Indentation level
            break_after: Whether to pause after output (default: False)
            
        Note:
            This helper eliminates 5 duplicate BasicOutputs check + fallback patterns.
            The fallback handles the rare edge case where BasicOutputs is not yet
            wired (initialization race condition).
        """
        if self.BasicOutputs:
            self.BasicOutputs.text(content, indent=indent, break_after=break_after)
        else:
            # Fallback if BasicOutputs not set (initialization race condition)
            indent_str = self._build_indent(indent)
            self.zPrimitives.line(f"{indent_str}{content}")

    def _build_indent(self, indent: int) -> str:
        """Build indentation string (DRY helper).
        
        Args:
            indent: Indentation level (0 = no indent)
            
        Returns:
            str: Indentation string (2 spaces per level)
            
        Note:
            This helper eliminates duplicate indent calculations in fallback logic.
        """
        return _INDENT_STR * indent

    # Feedback Signal Methods

    def error(self, content: str, indent: int = DEFAULT_INDENT) -> None:
        """Display error message with red color (semantic feedback).
        
        Signal method for critical errors and validation failures. Implements
        dual-mode I/O pattern and composes with BasicOutputs for terminal output.
        
        Semantic Color: RED (industry standard for errors)
        
        Args:
            content: Error message text
            indent: Indentation level (default: 0)
                    Each level = 2 spaces
                    
        Returns:
            None
            
        Example:
            self.Signals.error("Operation failed")
            self.Signals.error("Invalid input detected", indent=1)
            
        Note:
            Used by: AdvancedData (data validation errors), zAuth (auth failures)
            Composes with: BasicOutputs.text() for terminal output
        """
        # Try GUI mode first - send clean event
        if self.zPrimitives.send_gui_event(_EVENT_NAME_ERROR, {
            _KEY_CONTENT: content,
            _KEY_INDENT: indent
        }):
            return  # GUI event sent successfully

        # Terminal mode - apply semantic error color (CSS-aligned) and compose with BasicOutputs
        colored = self._colorize(content, COLOR_ERROR)
        self._output_text(colored, indent, break_after=False)

    def warning(self, content: str, indent: int = DEFAULT_INDENT) -> None:
        """Display warning message with yellow color (semantic feedback).
        
        Signal method for warnings, deprecations, and cautions. Implements
        dual-mode I/O pattern and composes with BasicOutputs for terminal output.
        
        Semantic Color: YELLOW (industry standard for warnings)
        
        Args:
            content: Warning message text
            indent: Indentation level (default: 0)
                    Each level = 2 spaces
                    
        Returns:
            None
            
        Example:
            self.Signals.warning("Deprecated feature in use")
            self.Signals.warning("Configuration may be invalid", indent=1)
            
        Note:
            Used by: zSystem (system operation warnings)
            Composes with: BasicOutputs.text() for terminal output
        """
        # Try GUI mode first - send clean event
        if self.zPrimitives.send_gui_event(_EVENT_NAME_WARNING, {
            _KEY_CONTENT: content,
            _KEY_INDENT: indent
        }):
            return  # GUI event sent successfully

        # Terminal mode - apply semantic warning color (CSS-aligned) and compose with BasicOutputs
        colored = self._colorize(content, COLOR_WARNING)
        self._output_text(colored, indent, break_after=False)

    def success(self, content: str, indent: int = DEFAULT_INDENT) -> None:
        """Display success message with green color (semantic feedback).
        
        Signal method for success confirmations and completions. Implements
        dual-mode I/O pattern and composes with BasicOutputs for terminal output.
        
        Semantic Color: GREEN (industry standard for success)
        
        Args:
            content: Success message text
            indent: Indentation level (default: 0)
                    Each level = 2 spaces
                    
        Returns:
            None
            
        Example:
            self.Signals.success("Operation completed successfully")
            self.Signals.success("All tests passed", indent=1)
            
        Note:
            Used by: zSystem (operation success confirmations)
            Composes with: BasicOutputs.text() for terminal output
        """
        # Try GUI mode first - send clean event
        if self.zPrimitives.send_gui_event(_EVENT_NAME_SUCCESS, {
            _KEY_CONTENT: content,
            _KEY_INDENT: indent
        }):
            return  # GUI event sent successfully

        # Terminal mode - apply semantic success color (CSS-aligned) and compose with BasicOutputs
        colored = self._colorize(content, COLOR_SUCCESS)
        self._output_text(colored, indent, break_after=False)

    def info(self, content: str, indent: int = DEFAULT_INDENT) -> None:
        """Display info message with cyan color (semantic feedback).
        
        Signal method for informational messages and hints. Implements
        dual-mode I/O pattern and composes with BasicOutputs for terminal output.
        
        Semantic Color: CYAN (industry standard for info)
        
        Args:
            content: Info message text
            indent: Indentation level (default: 0)
                    Each level = 2 spaces
                    
        Returns:
            None
            
        Example:
            self.Signals.info("Hint: Use --verbose for more details")
            self.Signals.info("Configuration loaded from file", indent=1)
            
        Note:
            Used by: zSystem (informational messages)
            Composes with: BasicOutputs.text() for terminal output
        """
        # Try GUI mode first - send clean event
        if self.zPrimitives.send_gui_event(_EVENT_NAME_INFO, {
            _KEY_CONTENT: content,
            _KEY_INDENT: indent
        }):
            return  # GUI event sent successfully

        # Terminal mode - apply semantic info color (CSS-aligned) and compose with BasicOutputs
        colored = self._colorize(content, COLOR_INFO)
        self._output_text(colored, indent, break_after=False)

    # Flow Control Methods

    def zMarker(self, label: str = _DEFAULT_MARKER_LABEL, color: str = _DEFAULT_MARKER_COLOR, indent: int = DEFAULT_INDENT) -> None:
        """Display visual workflow marker (flow control signal).
        
        Flow control method for visual workflow stage separators. Creates
        marker lines with centered colored label. Implements dual-mode I/O
        pattern and composes with BasicOutputs for terminal output.
        
        Semantic Color: MAGENTA (default) - Visual separator
        
        Args:
            label: Marker label text (default: "Marker")
            color: Color name for label (default: "MAGENTA")
                   Examples: "RED", "GREEN", "CYAN", "MAGENTA"
            indent: Indentation level (default: 0)
                    Each level = 2 spaces
                    
        Returns:
            None
            
        Example:
            self.Signals.zMarker("Processing Stage 1")
            self.Signals.zMarker("Validation Phase", color="CYAN")
            self.Signals.zMarker("Final Stage", color="GREEN", indent=1)
            
        Note:
            Used by: zSystem (workflow stage separators)
            Composes with: BasicOutputs.text() for terminal output
            Terminal Output: Blank line, marker line, colored label, marker line, blank line
        """
        # Try GUI mode first - send clean event
        if self.zPrimitives.send_gui_event(_EVENT_NAME_ZMARKER, {
            _KEY_LABEL: label,
            _KEY_COLOR: color,
            _KEY_INDENT: indent
        }):
            return  # GUI event sent successfully

        # Terminal mode - create visual marker with separator lines
        # Get color from Colors class (with fallback to MAGENTA)
        color_code = getattr(self.zColors, color.upper(), self.zColors.MAGENTA)

        # Create marker line and colored label
        marker_line = _MARKER_LINE_CHAR * _MARKER_LINE_WIDTH
        colored_label = f"{color_code}{label}{self.zColors.RESET}"

        # Compose: use BasicOutputs.text() for all lines
        if self.BasicOutputs:
            self.BasicOutputs.text(_EMPTY_LINE, indent=indent, break_after=False)  # Blank line before
            self.BasicOutputs.text(marker_line, indent=indent, break_after=False)
            self.BasicOutputs.text(colored_label, indent=indent, break_after=False)
            self.BasicOutputs.text(marker_line, indent=indent, break_after=False)
            self.BasicOutputs.text(_EMPTY_LINE, indent=indent, break_after=False)  # Blank line after
        else:
            # Fallback if BasicOutputs not set (initialization race condition)
            indent_str = self._build_indent(indent)
            self.zPrimitives.line(_EMPTY_LINE)
            self.zPrimitives.line(f"{indent_str}{marker_line}")
            self.zPrimitives.line(f"{indent_str}{colored_label}")
            self.zPrimitives.line(f"{indent_str}{marker_line}")
            self.zPrimitives.line(_EMPTY_LINE)
