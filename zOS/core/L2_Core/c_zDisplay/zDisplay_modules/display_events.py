# zCLI/subsystems/zDisplay/zDisplay_modules/display_events.py

"""
zEvents - Event Orchestrator for zDisplay Subsystem
===================================================

This module implements the composition pattern to orchestrate 8 event packages,
providing a unified interface for complex display operations and managing
inter-package dependencies through cross-reference wiring.

Architecture - Composition Pattern
----------------------------------
zEvents acts as an **orchestrator** that composes 8 specialized event packages
into a cohesive display system. Each package handles a specific category of
UI operations (outputs, signals, data, etc.).

**Key Responsibilities:**
1. **Package Initialization**: Instantiate all 8 event packages
2. **Cross-Reference Wiring**: Set up dependencies between packages
3. **Convenience Delegation**: Provide 21 backward-compatible delegate methods

Layer Design
------------
This module occupies **Layer 2** in the zDisplay architecture:

```
Layer 3: display_delegates.py (PRIMARY API)
    ↓ calls methods on
Layer 2: display_events.py (ORCHESTRATOR) ← THIS MODULE
    ↓ composes 8 packages from
Layer 2: events/*.py (EVENT IMPLEMENTATIONS)
    ↓ all use
Layer 1: display_primitives.py (FOUNDATION - Terminal/Bifrost switching)
    ↓ uses
Layer 0: zConfig (session) + zComm (WebSocket)
```

Event Package Composition
--------------------------
The 8 event packages are:

1. **BasicOutputs** - Formatted output (header, text)
2. **BasicInputs** - User input collection (selection)
3. **Signals** - Status messages (error, warning, success, info, zMarker)
4. **BasicData** - Data display (list, json)
5. **AdvancedData** - Complex data (zTable with pagination)
6. **zSystem** - System UI (zDeclare, zSession, zCrumbs, zMenu, zDialog)
7. **TimeBased** - Time-based events (progress_bar, spinner)

Cross-Reference Architecture
-----------------------------
After initializing packages, __init__ wires them together so packages can
call each other's methods. This enables composition patterns like:

```python
# In Signals.error():
self.BasicOutputs.header("ERROR")  # Works via cross-reference
```

**Dependency Graph:**
- BasicOutputs → Used by ALL 6 other packages (foundation)
- Signals → Used by AdvancedData, zSystem
- BasicInputs → Used by zSystem

Convenience Delegates
---------------------
Provides 21 backward-compatible delegate methods that forward calls to the
appropriate package. This allows both access patterns:

```python
# Direct package access:
display.zEvents.BasicOutputs.header("Title")

# Via convenience delegate:
display.zEvents.header("Title")  # Same result
```

Usage Example
-------------
```python
# Initialized by zDisplay:
events = zEvents(display_instance)

# Direct package access:
events.BasicOutputs.header("Application Started", color="GREEN")
events.Signals.success("Operation completed")

# Via convenience delegates:
events.header("Application Started", color="GREEN")
events.success("Operation completed")
```

zCLI Integration
----------------
- **Initialized by:** zDisplay.__init__() (line ~35)
- **Used by:** display_delegates.py (PRIMARY API) and event packages
- **Dependencies:** All 7 event packages (events/*.py)
- **No direct session access** - delegates to event packages

Thread Safety
-------------
Not thread-safe. Should only be accessed from the main thread or with
appropriate synchronization.

Module Constants
----------------
Defines default values for styles, labels, colors, and prompts used across
convenience delegate methods.
"""

from zOS import Any, Optional, List, Dict

from .c_basic.display_event_outputs import BasicOutputs
from .c_basic.display_event_signals import Signals
from .d_interaction.display_event_inputs import BasicInputs
from .d_interaction.display_event_data import BasicData
from .d_interaction.display_event_media import MediaEvents
from .d_interaction.display_event_links import LinkEvents
from .e_advanced.display_event_advanced import AdvancedData
from .e_advanced.display_event_timebased import TimeBased
from .f_orchestration.display_event_system import zSystem

# Module Constants

# Style constants
DEFAULT_COLOR = "RESET"
DEFAULT_STYLE_FULL = "full"
DEFAULT_STYLE_NUMBERED = "numbered"
DEFAULT_STYLE_BULLET = "bullet"
DEFAULT_STYLE_DOTS = "dots"

# Label constants
_DEFAULT_MARKER_LABEL = "Marker"
_DEFAULT_MARKER_COLOR = "MAGENTA"
_DEFAULT_LABEL_PROCESSING = "Processing"
_DEFAULT_LABEL_LOADING = "Loading"

# Prompt constants
DEFAULT_MENU_PROMPT = "Select an option:"

# Event Orchestrator Class

class zEvents:
    """Event orchestrator - composes 9 event packages with cross-references.
    
    This class implements the composition pattern to orchestrate specialized
    event packages, wiring them together so they can call each other's methods.
    It also provides convenience delegate methods for backward compatibility.
    
    **Architecture Pattern:**
    - **Composition**: Composes 9 specialized event packages
    - **Cross-Reference**: Wires packages together for inter-dependencies
    - **Delegation**: Provides backward-compatible convenience methods
    
    **Event Packages:**
    - BasicOutputs: header, text (foundation for all other packages)
    - BasicInputs: selection, button (unified single/multi-select)
    - Signals: error, warning, success, info, zMarker
    - BasicData: list, json_data
    - AdvancedData: zTable (with pagination)
    - zSystem: zDeclare, zSession, zCrumbs, zMenu, zDialog
    - TimeBased: progress_bar, spinner, progress_iterator, indeterminate_progress
    - MediaEvents: image, video, audio (media rendering)
    - LinkEvents: link (semantic link rendering with target support)
    
    **Cross-Reference Dependencies:**
    - BasicOutputs → Used by ALL other packages
    - Signals → Used by AdvancedData, zSystem
    - BasicInputs → Used by zSystem, MediaEvents
    
    **Layer Position:** Layer 2 (Orchestrator)
    - Built on: primitives (Layer 1)
    - Used by: display_delegates (Layer 3/PRIMARY API)
    """

    # Type hints for instance attributes
    display: Any  # zDisplay instance
    BasicOutputs: Any  # BasicOutputs package instance
    BasicInputs: Any  # BasicInputs package instance
    Signals: Any  # Signals package instance
    BasicData: Any  # BasicData package instance
    AdvancedData: Any  # AdvancedData package instance
    zSystem: Any  # zSystem package instance
    TimeBased: Any  # TimeBased package instance

    def __init__(self, display_instance: Any) -> None:
        """Initialize zEvents orchestrator with all 8 event packages.
        
        This method performs three critical steps:
        1. Store reference to parent display instance
        2. Initialize all 8 event packages
        3. Wire cross-references so packages can call each other
        
        Args:
            display_instance: Parent zDisplay instance
        
        Note:
            Cross-references (lines below) are critical for package composition.
            Without them, packages cannot call each other's methods.
        """
        self.display = display_instance

        # Step 1: Initialize all 9 event packages
        self.BasicOutputs = BasicOutputs(display_instance)
        self.BasicInputs = BasicInputs(display_instance)
        self.Signals = Signals(display_instance)
        self.BasicData = BasicData(display_instance)
        self.AdvancedData = AdvancedData(display_instance)
        self.zSystem = zSystem(display_instance)
        self.TimeBased = TimeBased(display_instance)
        self.MediaEvents = MediaEvents(display_instance)
        self.LinkEvents = LinkEvents(display_instance)

        # Step 2: Set up cross-references (packages can call each other)
        # 
        # This wiring enables composition patterns like:
        #   In Signals.error():
        #       self.BasicOutputs.header("ERROR")  # Works via cross-reference
        #
        # Dependency Graph:
        #   BasicOutputs ← BasicInputs, Signals, BasicData, AdvancedData, zSystem, TimeBased
        #   Signals ← AdvancedData, zSystem
        #   BasicInputs ← zSystem
        
        self.BasicInputs.BasicOutputs = self.BasicOutputs
        self.Signals.BasicOutputs = self.BasicOutputs
        self.BasicData.BasicOutputs = self.BasicOutputs
        self.AdvancedData.BasicOutputs = self.BasicOutputs
        self.AdvancedData.Signals = self.Signals
        self.zSystem.BasicOutputs = self.BasicOutputs
        self.zSystem.Signals = self.Signals
        self.zSystem.BasicInputs = self.BasicInputs
        self.TimeBased.BasicOutputs = self.BasicOutputs
        self.MediaEvents.BasicOutputs = self.BasicOutputs
        self.MediaEvents.BasicInputs = self.BasicInputs
        self.LinkEvents.BasicOutputs = self.BasicOutputs
        self.LinkEvents.BasicInputs = self.BasicInputs

    # Convenience Delegates - BasicOutputs

    def header(self, label: str, color: str = DEFAULT_COLOR, indent: int = 0, style: str = DEFAULT_STYLE_FULL, semantic: Optional[str] = None, **kwargs) -> Any:
        """Display formatted header with styling.
        
        Convenience delegate to BasicOutputs.header for backward compatibility.
        
        Args:
            label: Header text to display
            color: Color name for styling (default: RESET)
            indent: Indentation level (default: 0)
            style: Header style (default: full)
            semantic: Optional semantic HTML element type (e.g., "strong", "em")
            **kwargs: Additional parameters (e.g., 'class' for custom CSS classes)
            
        Returns:
            Any: Result from BasicOutputs.header method
        """
        return self.BasicOutputs.header(label, color, indent, style, semantic=semantic, **kwargs)

    def text(
        self, 
        content: str, 
        indent: int = 0, 
        pause: bool = False, 
        break_message: Optional[str] = None,
        break_after: Optional[bool] = None,
        semantic: Optional[str] = None,
        **kwargs  # NEW v1.5.12: Pass through _context and other params
    ) -> Any:
        """Display plain text content.
        
        Convenience delegate to BasicOutputs.text for backward compatibility.
        
        Args:
            content: Text content to display
            indent: Indentation level (default: 0)
            pause: Pause for user acknowledgment (default: False)
            break_message: Optional break message
            break_after: Legacy parameter - use 'pause' instead
            semantic: Optional semantic HTML element type (e.g., "code", "strong", "kbd")
            
        Returns:
            Any: Result from BasicOutputs.text method
        """
        # Pass to BasicOutputs with new signature
        return self.BasicOutputs.text(
            content, 
            indent=indent, 
            pause=pause,
            break_message=break_message,
            break_after=break_after,
            semantic=semantic,
            **kwargs  # NEW v1.5.12: Pass through _context
        )
    
    def rich_text(
        self,
        content: str,
        indent: int = 0,
        pause: bool = False,
        break_message: Optional[str] = None,
        format: str = "markdown",
        **kwargs
    ) -> Any:
        """Display rich text with inline formatting.
        
        Convenience delegate to BasicOutputs.rich_text for inline semantic markup.
        
        Args:
            content: Text with markdown inline formatting
            indent: Indentation level (default: 0)
            pause: Pause for user acknowledgment (default: False)
            break_message: Optional break message
            format: Format type (default: "markdown")
            **kwargs: Additional parameters passed through
            
        Returns:
            Any: Result from BasicOutputs.rich_text method
        """
        return self.BasicOutputs.rich_text(
            content,
            indent=indent,
            pause=pause,
            break_message=break_message,
            format=format,
            **kwargs
        )

    # Convenience Delegates - BasicInputs

    def selection(self, prompt: str, options: List[Any], multi: bool = False, default: Optional[Any] = None, style: str = DEFAULT_STYLE_NUMBERED, action_type: Optional[str] = None, type: Optional[str] = None) -> Any:
        """Prompt user for selection from options.
        
        Convenience delegate to BasicInputs.selection for backward compatibility.
        
        NEW v1.6.1: Added action_type parameter for link actions.
        
        Args:
            prompt: Selection prompt text
            options: List of options to choose from (strings or link dicts)
            multi: Allow multiple selections (default: False)
            default: Default selection value
            style: Display style (default: numbered)
            action_type: Action to perform after selection (default: None)
                         - "link": Execute link action (open URL, navigate)
                         - None: Return selected value(s) only
            type: Rendering hint for Bifrost (radio/checkbox/dropdown). Ignored in Terminal mode.
            
        Returns:
            Any: Selected option(s) from BasicInputs.selection method
        """
        return self.BasicInputs.selection(prompt, options, multi, default, style, action_type, type)

    def button(self, label: str, action: Optional[str] = None, color: str = "primary", **kwargs) -> bool:
        """Display a button that requires confirmation to execute.
        
        Convenience delegate to BasicInputs.button for cross-mode button rendering.
        
        Args:
            label: Button label text (e.g., "Submit", "Delete", "Save")
            action: Optional action identifier or zVar name
            color: Button semantic color (primary, success, danger, warning, info, secondary)
            **kwargs: Additional parameters (e.g., _context)
            
        Returns:
            bool: True if clicked (y), False if cancelled (n)
        """
        return self.BasicInputs.button(label, action, color, **kwargs)

    def link(self, label: str, href: str, target: str = "_self", **kwargs) -> Optional[Any]:
        """Display a semantic link with mode-aware rendering.
        
        Convenience delegate to LinkEvents.handle_link for cross-mode link rendering.
        
        Terminal Mode:
        - Internal links: Auto-navigate via zLink
        - External links: Prompt user, open in browser
        - Anchor links: Display with icon (no scroll)
        - Placeholder (#): Display as styled text
        
        Bifrost Mode:
        - Renders as semantic <a> tag with proper target and security attributes
        - Internal links: Client-side routing
        - External links: Native browser behavior
        - Anchor links: Smooth scroll
        
        Args:
            label: Link text to display
            href: Link destination (internal $/@, external http/https, anchor #)
            target: Target behavior (_self, _blank, _parent, _top)
            **kwargs: Additional parameters:
                - color: Link color theme
                - rel: Link relationship (auto-added for _blank external)
                - window: Dict with width, height, features for window.open()
                - _zClass: CSS classes for styling
            
        Returns:
            Navigation result (for internal links) or None
            
        Examples:
            # Internal navigation
            display.zEvents.link("About", "$zAbout")
            
            # External link (new tab)
            display.zEvents.link("GitHub", "https://github.com", target="_blank")
            
            # Styled as button
            display.zEvents.link("Docs", "https://docs.site.com", 
                                _zClass="zBtn zBtn-primary")
        """
        link_data = {
            'label': label,
            'href': href,
            'target': target,
            **kwargs
        }
        return self.LinkEvents.handle_link(link_data)

    # Convenience Delegates - Signals

    def error(self, content: str, indent: int = 0) -> Any:
        """Display error message with ERROR styling.
        
        Convenience delegate to Signals.error for backward compatibility.
        
        Args:
            content: Error message text
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from Signals.error method
        """
        return self.Signals.error(content, indent)

    def warning(self, content: str, indent: int = 0) -> Any:
        """Display warning message with WARNING styling.
        
        Convenience delegate to Signals.warning for backward compatibility.
        
        Args:
            content: Warning message text
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from Signals.warning method
        """
        return self.Signals.warning(content, indent)

    def success(self, content: str, indent: int = 0) -> Any:
        """Display success message with SUCCESS styling.
        
        Convenience delegate to Signals.success for backward compatibility.
        
        Args:
            content: Success message text
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from Signals.success method
        """
        return self.Signals.success(content, indent)

    def info(self, content: str, indent: int = 0) -> Any:
        """Display info message with INFO styling.
        
        Convenience delegate to Signals.info for backward compatibility.
        
        Args:
            content: Info message text
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from Signals.info method
        """
        return self.Signals.info(content, indent)

    def zMarker(self, label: str = _DEFAULT_MARKER_LABEL, color: str = _DEFAULT_MARKER_COLOR, indent: int = 0) -> Any:
        """Display visual marker for debugging/tracking.
        
        Convenience delegate to Signals.zMarker for backward compatibility.
        
        Args:
            label: Marker label text (default: Marker)
            color: Marker color (default: MAGENTA)
            indent: Indentation level (default: 0)
            
        Returns:
            Any: Result from Signals.zMarker method
        """
        return self.Signals.zMarker(label, color, indent)

    # Convenience Delegates - BasicData

    def list(self, items: List[Any], style: str = DEFAULT_STYLE_BULLET, indent: int = 0, **kwargs) -> Optional[Any]:
        """Display list of items with formatting.
        
        Convenience delegate to BasicData.list for backward compatibility.
        
        Args:
            items: List of items to display
            style: List style (default: bullet)
            indent: int = 0 (default: 0)
            **kwargs: Additional parameters (e.g., _context)
            
        Returns:
            Optional[Any]: Navigation signal (zLink dict) if user clicked a link, None otherwise
        """
        return self.BasicData.list(items, style, indent, **kwargs)

    def outline(self, items: List[Any], styles: Optional[List[str]] = None, indent: int = 0) -> Any:
        """Display hierarchical outline with multi-level numbering.
        
        Convenience delegate to BasicData.outline for backward compatibility.
        
        Args:
            items: List of items (strings or dicts with 'content' and 'children')
            styles: List of styles per indentation level (default: number→letter→roman→bullet)
            indent: Base indentation level (default: 0)
            
        Returns:
            Any: Result from BasicData.outline method
        """
        return self.BasicData.outline(items, styles, indent)

    def json_data(self, data: Dict[str, Any], indent_size: int = 2, indent: int = 0, color: bool = False) -> Any:
        """Display JSON data with formatting.
        
        Convenience delegate to BasicData.json_data for backward compatibility.
        
        Args:
            data: Dictionary data to display as JSON
            indent_size: JSON indentation size (default: 2)
            indent: Overall indentation level (default: 0)
            color: Enable color syntax highlighting (default: False)
            
        Returns:
            Any: Result from BasicData.json_data method
        """
        return self.BasicData.json_data(data, indent_size, indent, color)

    # Convenience Delegates - AdvancedData

    def zTable(self, title: str, columns: List[str], rows: List[List[Any]], limit: Optional[int] = None, offset: int = 0, show_header: bool = True, interactive: bool = False, caption: Optional[str] = None) -> Any:
        """Display data in table format with pagination support.
        
        Convenience delegate to AdvancedData.zTable for backward compatibility.
        
        Args:
            title: Table title
            columns: Column header names
            rows: Table row data
            limit: Maximum rows to display (pagination)
            offset: Row offset for pagination (default: 0)
            show_header: Show column headers (default: True)
            interactive: Enable keyboard navigation in Terminal mode (default: False)
            caption: Optional table caption describing the table contents
            
        Returns:
            Any: Result from AdvancedData.zTable method
        """
        return self.AdvancedData.zTable(title, columns, rows, limit, offset, show_header, interactive, caption)

    # Convenience Delegates - zSystem

    def zDeclare(self, label: str, color: Optional[str] = None, indent: int = 0, style: Optional[str] = None) -> Any:
        """Display system declaration message.
        
        Convenience delegate to zSystem.zDeclare for backward compatibility.
        
        Args:
            label: Declaration text
            color: Optional color override
            indent: Indentation level (default: 0)
            style: Optional style override
            
        Returns:
            Any: Result from zSystem.zDeclare method
        """
        return self.zSystem.zDeclare(label, color, indent, style)

    def zSession(self, session_data: Dict[str, Any], break_after: bool = True, break_message: Optional[str] = None) -> Any:
        """Display session information.
        
        Convenience delegate to zSystem.zSession for backward compatibility.
        
        Args:
            session_data: Session dictionary to display
            break_after: Add line break after (default: True)
            break_message: Optional break message
            
        Returns:
            Any: Result from zSystem.zSession method
        """
        return self.zSystem.zSession(session_data, break_after, break_message)

    def zConfig(self, config_data: Optional[Dict[str, Any]] = None, break_after: bool = True, break_message: Optional[str] = None) -> Any:
        """Display configuration information.
        
        Convenience delegate to zSystem.zConfig for backward compatibility.
        
        Args:
            config_data: Config dictionary with 'machine' and 'environment' keys
            break_after: Add line break after (default: True)
            break_message: Optional break message
            
        Returns:
            Any: Result from zSystem.zConfig method
        """
        return self.zSystem.zConfig(config_data, break_after, break_message)

    def zCrumbs(self, session_data: Optional[Dict[str, Any]] = None, parent: Optional[str] = None, show: str = 'session') -> Any:
        """Display breadcrumb navigation from session.
        
        Convenience delegate to zSystem.zCrumbs for backward compatibility.
        
        Args:
            session_data: Session dictionary containing navigation
            parent: Declarative parent path (works in both Terminal and Bifrost, e.g., "zProducts.zTheme")
            show: Display mode - 'session' (default) or 'static'
            
        Returns:
            Any: Result from zSystem.zCrumbs method
        """
        return self.zSystem.zCrumbs(session_data, parent=parent, show=show)

    def zMenu(self, menu_items: List[Any], prompt: str = DEFAULT_MENU_PROMPT, return_selection: bool = False) -> Any:
        """Display interactive menu for user selection.
        
        Convenience delegate to zSystem.zMenu for backward compatibility.
        
        Args:
            menu_items: List of menu items
            prompt: Menu prompt text (default: "Select an option:")
            return_selection: Return selection instead of executing (default: False)
            
        Returns:
            Any: Result from zSystem.zMenu method
        """
        return self.zSystem.zMenu(menu_items, prompt, return_selection)

    def zDash(self, folder: str, sidebar: List[str], default: Optional[str] = None, _zcli: Optional[Any] = None, **kwargs) -> Any:
        """Display dashboard with panel navigation.
        
        Convenience delegate to zSystem.zDash for backward compatibility.
        
        Args:
            folder: Base folder for panel discovery
            sidebar: List of panel names
            default: Default panel to navigate to (optional)
            _zcli: zCLI instance for context (optional)
            **kwargs: Additional parameters (e.g., _context)
            
        Returns:
            Any: Result from zSystem.zDash method
        """
        return self.zSystem.zDash(folder, sidebar, default, _zcli, **kwargs)

    def zDialog(self, context: str, zcli: Optional[Any] = None, walker: Optional[Any] = None) -> Any:
        """Display interactive dialog system.
        
        Convenience delegate to zSystem.zDialog for backward compatibility.
        
        Args:
            context: Dialog context/configuration
            zcli: Optional zCLI instance
            walker: Optional walker instance
            
        Returns:
            Any: Result from zSystem.zDialog method
        """
        return self.zSystem.zDialog(context, zcli, walker)

    # Convenience Delegates - TimeBased

    def progress_bar(self, current: int, total: Optional[int] = None, label: str = _DEFAULT_LABEL_PROCESSING, **kwargs: Any) -> Any:
        """Display progress bar with current/total status.
        
        Convenience delegate to TimeBased.progress_bar for backward compatibility.
        
        Args:
            current: Current progress value
            total: Total progress value (optional)
            label: Progress label text (default: "Processing")
            **kwargs: Additional time-based event options
            
        Returns:
            Any: Result from TimeBased.progress_bar method
        """
        return self.TimeBased.progress_bar(current, total, label, **kwargs)

    def spinner(self, label: str = _DEFAULT_LABEL_LOADING, style: str = DEFAULT_STYLE_DOTS) -> Any:
        """Display animated spinner for loading indication.
        
        Convenience delegate to TimeBased.spinner for backward compatibility.
        
        Args:
            label: Spinner label text (default: "Loading")
            style: Spinner animation style (default: "dots")
            
        Returns:
            Any: Result from TimeBased.spinner method
        """
        return self.TimeBased.spinner(label, style)

    def progress_iterator(self, iterable: Any, label: str = _DEFAULT_LABEL_PROCESSING, **kwargs: Any) -> Any:
        """Iterate with progress indication.
        
        Convenience delegate to TimeBased.progress_iterator for backward compatibility.
        
        Args:
            iterable: Iterable to process
            label: Progress label text (default: "Processing")
            **kwargs: Additional time-based event options
            
        Returns:
            Any: Result from TimeBased.progress_iterator method
        """
        return self.TimeBased.progress_iterator(iterable, label, **kwargs)

    def indeterminate_progress(self, label: str = _DEFAULT_LABEL_PROCESSING) -> Any:
        """Display indeterminate progress indicator.
        
        Convenience delegate to TimeBased.indeterminate_progress for backward compatibility.
        
        Args:
            label: Progress label text (default: "Processing")
            
        Returns:
            Any: Result from TimeBased.indeterminate_progress method
        """
        return self.TimeBased.indeterminate_progress(label)
    
    def swiper(self, slides: list, label: str = "Slides", auto_advance: bool = True, delay: int = 3, loop: bool = False, container: str = "#app") -> Any:
        """Display interactive content carousel/swiper.
        
        Convenience delegate to TimeBased.swiper for backward compatibility.
        
        Args:
            slides: List of slide content strings
            label: Title for the swiper (default: "Slides")
            auto_advance: Auto-cycle through slides (default: True)
            delay: Seconds between auto-advance (default: 3)
            loop: Wrap around to start after last slide (default: False)
            container: Bifrost DOM container (default: "#app")
            
        Returns:
            Any: Result from TimeBased.swiper method
        """
        return self.TimeBased.swiper(slides, label, auto_advance, delay, loop, container)

    # Convenience Delegates - MediaEvents

    def image(
        self,
        src: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Display an image event.
        
        Convenience delegate to MediaEvents.image for backward compatibility.
        
        Args:
            src: The source URL or path of the image
            alt_text: Alternative text for the image (accessibility)
            caption: An optional caption for the image
            open_prompt: If True (default), displays a button in terminal mode (with action="#").
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output
            color: Color for terminal output text
            **kwargs: Additional parameters to pass through to the event
            
        Returns:
            Any: Result from MediaEvents.image method
        """
        return self.MediaEvents.image(src, alt_text, caption, open_prompt, indent, color, **kwargs)

    def video(
        self,
        src: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Display a video event.
        
        Convenience delegate to MediaEvents.video for backward compatibility.
        
        Args:
            src: The source URL or path of the video
            alt_text: Alternative text for the video (accessibility)
            caption: An optional caption for the video
            open_prompt: If True (default), displays a button in terminal mode.
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output
            color: Color for terminal output text
            **kwargs: Additional parameters to pass through to the event
            
        Returns:
            Any: Result from MediaEvents.video method
        """
        return self.MediaEvents.video(src, alt_text, caption, open_prompt, indent, color, **kwargs)

    def audio(
        self,
        src: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Display an audio event.
        
        Convenience delegate to MediaEvents.audio for backward compatibility.
        
        Args:
            src: The source URL or path of the audio file
            alt_text: Alternative text for the audio (accessibility)
            caption: An optional caption for the audio
            open_prompt: If True (default), displays a button in terminal mode.
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output
            color: Color for terminal output text
            **kwargs: Additional parameters to pass through to the event
            
        Returns:
            Any: Result from MediaEvents.audio method
        """
        return self.MediaEvents.audio(src, alt_text, caption, open_prompt, indent, color, **kwargs)

    def picture(
        self,
        sources: list,
        fallback: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Display a picture element (responsive image with source selection).
        
        Convenience delegate to MediaEvents.picture for backward compatibility.
        
        Args:
            sources: List of source dicts with 'srcset' and 'media' keys
                    e.g., [{"srcset": "large.jpg", "media": "(min-width: 1024px)"}]
            fallback: Fallback image path (required, used as default)
            alt_text: Alternative text for the picture (accessibility)
            caption: An optional caption for the picture
            open_prompt: If True (default), displays interactive selection in terminal mode.
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output
            color: Color for terminal output text
            **kwargs: Additional parameters to pass through to the event
            
        Returns:
            Any: Result from MediaEvents.picture method
        """
        return self.MediaEvents.picture(sources, fallback, alt_text, caption, open_prompt, indent, color, **kwargs)
