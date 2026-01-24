# zCLI/subsystems/zDisplay/zDisplay.py
"""
Display & Rendering Subsystem for zCLI.

This module provides the primary facade for all display capabilities in zCLI,
including event-driven rendering, input collection, and multi-mode output.
zDisplay is a Layer 1 subsystem that provides the UI backbone for the entire framework.

Architecture:
    zDisplay follows the Facade pattern, providing a unified interface to display
    capabilities while delegating implementation to specialized modules:
    
    - display_primitives: Low-level I/O (write_raw, read_string, read_password)
    - display_events: High-level event packages (outputs, inputs, signals, data, widgets)
    - display_delegates: Backward-compatible convenience methods
    
    The unified handle() method routes all display operations through a single
    entry point, enabling consistent validation, logging, and error handling.

Layer 1 Design:
    As a Layer 1 subsystem, zDisplay:
    - Depends on Layer 0 (zConfig, zComm) for configuration and communication
    - Provides UI infrastructure for higher layers (zParser, zWalker, zWizard)
    - Supports multiple modes (Terminal, zBifrost/WebSocket) transparently
    - No display logic runs before Layer 0 is initialized

zSession Integration:
    zDisplay reads session state but does not modify it directly. It reads:
    - session[SESSION_KEY_ZMODE]: Determines Terminal vs zBifrost mode
    - session (passed to events): For configuration and state access
    
    Mode selection affects rendering behavior:
    - Terminal: Direct console I/O via print/input
    - zBifrost: WebSocket messages to connected GUI client

zAuth Integration:
    zAuth composes generic zDisplay events for authentication UI:
    - success(), error(), warning() for feedback
    - text(), header() for status display
    - Primitives for credential collection
    
    zDisplay provides generic presentation layer; zAuth handles auth-specific composition.
    This maintains proper separation of concerns.

Event Routing System:
    All display operations route through handle() with event dictionaries:
    
    ```python
    display.handle({
        "event": "text",       # Event name (required)
        "content": "Hello",    # Event-specific parameters
        "color": "INFO"
    })
    ```
    
    The event map routes to appropriate handlers:
    - Output events: text, header, line
    - Signal events: error, warning, success, info, zMarker
    - Data events: list, json, json_data, zTable
    - System events: zDeclare, zSession, zCrumbs, zMenu, zDialog
    - Widget events: progress_bar, spinner, progress_iterator, indeterminate_progress
    - Input events: selection, read_string, read_password
    - Primitive events: write_raw, write_line, write_block

Multi-Mode Support:
    zDisplay automatically adapts to mode from session:
    
    Terminal Mode:
        - Direct console I/O (print, input, getpass)
        - ANSI color codes for styling
        - Blocking input methods
    
    zBifrost Mode:
        - WebSocket messages to GUI client
        - JSON-serialized event data
        - Non-blocking (async) operations
        
    Mode detection happens once at initialization and is cached.

Delegation Pattern:
    Convenience methods delegate to handle() for backward compatibility:
    
    ```python
    # Old style (still supported)
    display.progress_bar(50, 100, "Processing")
    
    # New style (preferred)
    display.handle({
        "event": "progress_bar",
        "current": 50,
        "total": 100,
        "label": "Processing"
    })
    ```
    
    These exist for convenience and backward compatibility only.
    New code should use handle() directly with event dictionaries.

Error Handling:
    The handle() method provides comprehensive error handling:
    - Validates display_obj is a dict
    - Ensures 'event' key is present
    - Verifies event is registered
    - Catches TypeError for invalid parameters
    - Logs all errors with appropriate severity
    - Returns None on error (never raises)

Auto-Initialization:
    zDisplay automatically:
    1. Validates zCLI instance (session, logger required)
    2. Extracts session and logger references
    3. Detects mode from session
    4. Initializes primitives and events modules
    5. Builds event routing map
    6. Emits ready message via zDeclare event
"""

from zOS import Colors, Any, Dict, Optional, Callable
from zOS.utils import validate_zcli_instance
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZMODE
from .zDisplay_modules.b_primitives.display_primitives import zPrimitives
from .zDisplay_modules.display_events import zEvents
from .zDisplay_modules.display_delegates import zDisplayDelegates
from .zDisplay_modules.display_constants import (
    SUBSYSTEM_NAME,
    READY_MESSAGE,
    DEFAULT_COLOR,
    DEFAULT_MODE,
    _EVENT_TEXT,
    _EVENT_RICH_TEXT,
    _EVENT_HEADER,
    _EVENT_LINE,
    _EVENT_ERROR,
    _EVENT_WARNING,
    _EVENT_SUCCESS,
    _EVENT_INFO,
    _EVENT_ZMARKER,
    _EVENT_LIST,
    _EVENT_DL,
    _EVENT_JSON,
    _EVENT_JSON_DATA,
    _EVENT_ZTABLE,
    _EVENT_IMAGE,
    _EVENT_VIDEO,
    _EVENT_AUDIO,
    _EVENT_PICTURE,
    _EVENT_ZDECLARE,
    _EVENT_ZSESSION,
    _EVENT_ZCONFIG,
    _EVENT_ZCRUMBS,
    _EVENT_ZMENU,
    _EVENT_ZDASH,
    _EVENT_ZDIALOG,
    _EVENT_PROGRESS_BAR,
    _EVENT_SPINNER,
    _EVENT_PROGRESS_ITERATOR,
    _EVENT_INDETERMINATE_PROGRESS,
    _EVENT_SELECTION,
    _EVENT_READ_STRING,
    _EVENT_READ_PASSWORD,
    _EVENT_BUTTON,
    _EVENT_LINK,
    _EVENT_WRITE_RAW,
    _EVENT_WRITE_LINE,
    _EVENT_WRITE_BLOCK,
    _ERR_INVALID_OBJ,
    _ERR_MISSING_EVENT,
    _ERR_UNKNOWN_EVENT,
    _ERR_INVALID_PARAMS,
    _KEY_EVENT,
)


class zDisplay(zDisplayDelegates):
    """Display and rendering subsystem with unified event routing.
    
    Provides a clean facade for all display operations, supporting both Terminal
    and zBifrost (WebSocket/GUI) modes. All operations route through a unified
    handle() method with event dictionaries.
    
    Architecture:
        - Facade pattern with delegation to specialized modules
        - Unified event routing through handle() method
        - Multi-mode support (Terminal, zBifrost) via session
        - Backward-compatible convenience methods
    
    Usage:
        ```python
        # Via handle() (preferred)
        display.handle({
            "event": "text",
            "content": "Hello World",
            "color": "INFO"
        })
        
        # Via convenience methods (backward compatible)
        display.progress_bar(50, 100, "Processing")
        ```
    """

    # Type hints for instance attributes
    zcli: Any  # zCLI instance
    session: Dict[str, Any]  # Session dictionary
    logger: Any  # Logger instance
    mode: str  # Display mode (Terminal or zBifrost)
    zColors: Any  # Colors utility
    mycolor: str  # Default color for subsystem
    zPrimitives: zPrimitives  # Primitives module
    zEvents: zEvents  # Events module
    _event_map: Dict[str, Callable]  # Event routing map
    _event_buffer: list  # Buffer for capturing events in zBifrost mode

    def __init__(self, zcli: Any) -> None:
        """Initialize zDisplay subsystem.
        
        Initialization Order:
            1. Validate zCLI instance (fail fast)
            2. Extract session and logger references
            3. Detect mode from session
            4. Initialize primitives and events modules
            5. Build event routing map
            6. Emit ready message
        
        Args:
            zcli: zCLI instance (required, must have session and logger)
            
        Raises:
            ValueError: If zcli is invalid or missing required attributes
        """
        # Validate zCLI instance FIRST
        validate_zcli_instance(zcli, SUBSYSTEM_NAME)

        # Core dependencies from zCLI
        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
        self.mode = self.session.get(SESSION_KEY_ZMODE, DEFAULT_MODE)

        # Colors utility
        self.zColors = Colors
        self.mycolor = DEFAULT_COLOR

        # Initialize module containers
        self.zPrimitives = zPrimitives(self)
        self.zEvents = zEvents(self)

        # Event buffer for zBifrost mode (capture events instead of broadcasting)
        self._event_buffer = []

        # Unified event routing map
        self._event_map = {
            # Output events
            _EVENT_TEXT: self.zEvents.text,
            _EVENT_RICH_TEXT: self.zEvents.rich_text,
            _EVENT_HEADER: self.zEvents.header,
            _EVENT_LINE: self.zEvents.text,

            # Signal events
            _EVENT_ERROR: self.zEvents.error,
            _EVENT_WARNING: self.zEvents.warning,
            _EVENT_SUCCESS: self.zEvents.success,
            _EVENT_INFO: self.zEvents.info,
            _EVENT_ZMARKER: self.zEvents.zMarker,

            # Data events
            _EVENT_LIST: self.zEvents.list,
            _EVENT_DL: lambda **kwargs: self.zEvents.list(style='details', **kwargs),
            _EVENT_JSON: self.zEvents.json_data,
            _EVENT_JSON_DATA: self.zEvents.json_data,
            _EVENT_ZTABLE: self.zEvents.zTable,

            # Media events
            _EVENT_IMAGE: self.zEvents.image,
            _EVENT_VIDEO: self.zEvents.video,
            _EVENT_AUDIO: self.zEvents.audio,
            _EVENT_PICTURE: self.zEvents.picture,

            # System events
            _EVENT_ZDECLARE: self.zEvents.zDeclare,
            _EVENT_ZSESSION: self.zEvents.zSession,
            _EVENT_ZCONFIG: self.zEvents.zConfig,
            _EVENT_ZCRUMBS: self.zEvents.zCrumbs,
            _EVENT_ZMENU: self.zEvents.zMenu,
            _EVENT_ZDASH: self.zEvents.zDash,
            _EVENT_ZDIALOG: self.zEvents.zDialog,

            # Widget events (progress, spinners)
            _EVENT_PROGRESS_BAR: self.zEvents.progress_bar,
            _EVENT_SPINNER: self.zEvents.spinner,
            _EVENT_PROGRESS_ITERATOR: self.zEvents.progress_iterator,
            _EVENT_INDETERMINATE_PROGRESS: self.zEvents.indeterminate_progress,

            # Input events
            _EVENT_SELECTION: self.zEvents.selection,
            _EVENT_READ_STRING: self.zPrimitives.read_string,
            _EVENT_READ_PASSWORD: self.zPrimitives.read_password,
            _EVENT_BUTTON: self.zEvents.button,
            _EVENT_LINK: self.zEvents.link,

            # Primitive events
            _EVENT_WRITE_RAW: self.zPrimitives.raw,
            _EVENT_WRITE_LINE: self.zPrimitives.line,
            _EVENT_WRITE_BLOCK: self.zPrimitives.block,
        }

        # Initialize ready message using modern handler
        self.handle({
            _KEY_EVENT: _EVENT_ZDECLARE,
            "label": READY_MESSAGE,
            "color": self.mycolor,
            "indent": 0,
            "style": "full",
        })

    @property
    def handler(self) -> Callable:
        """Return handler function for external routing (alias for handle).
        
        Returns:
            Callable: The handle method for event routing
        """
        return self.handle

    def handle(self, display_obj: Dict[str, Any]) -> Any:
        """Single event handler for all zDisplay operations.
        
        Validates the display object, routes to the appropriate handler,
        and executes with comprehensive error handling.
        
        Args:
            display_obj: Event dictionary with 'event' key and event-specific parameters
                Example: {"event": "text", "content": "Hello", "color": "INFO"}
        
        Returns:
            Any: Result from event handler, or None if error occurred
            
        Error Handling:
            - Logs warning if display_obj is not a dict
            - Logs warning if 'event' key is missing
            - Logs warning if event is not registered
            - Logs error if parameters are invalid for event
            - Never raises exceptions (returns None on error)
        """
        if not isinstance(display_obj, dict):
            self.logger.warning(_ERR_INVALID_OBJ, type(display_obj))
            return None

        event = display_obj.get(_KEY_EVENT)
        if not event:
            self.logger.warning(_ERR_MISSING_EVENT)
            return None

        handler = self._event_map.get(event)
        if not handler:
            self.logger.warning(_ERR_UNKNOWN_EVENT, event)
            return None

        # Filter out 'event' key AND metadata keys (starting with _)
        # Metadata keys like _zClass, _zStyle, _id, zRBAC are Bifrost-only and should not be passed to Terminal event methods
        # EXCEPTIONS:
        #   - _context is needed for %data.* variable resolution (v1.5.12)
        #   - parent is needed for declarative breadcrumbs (Phase 1)
        params = {k: v for k, v in display_obj.items() if k != _KEY_EVENT and (not k.startswith('_') or k == '_context')}

        try:
            return handler(**params)
        except TypeError as error:
            self.logger.error(_ERR_INVALID_PARAMS, event, error)
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # Event Buffer Management (zBifrost Mode)
    # ═══════════════════════════════════════════════════════════════════════════

    def buffer_event(self, event_data: Dict[str, Any]) -> None:
        """
        Buffer a display event for zBifrost mode.
        
        Instead of broadcasting immediately, events are captured in a buffer
        and returned as part of the command result. This solves the async
        event loop issue when zDispatch runs in a worker thread.
        
        Args:
            event_data: Event dictionary to buffer
        """
        self._event_buffer.append(event_data)

    def collect_buffered_events(self) -> list:
        """
        Collect all buffered events and clear the buffer.
        
        Returns:
            list: All buffered events since last collection
        """
        events = self._event_buffer.copy()
        self._event_buffer.clear()
        return events

    def clear_event_buffer(self) -> None:
        """Clear the event buffer without returning events."""
        self._event_buffer.clear()

    # ═══════════════════════════════════════════════════════════════════════════
    # Convenience Method Delegates (Backward Compatibility)
    # ═══════════════════════════════════════════════════════════════════════════

    def progress_bar(
        self,
        current: int,
        total: Optional[int] = None,
        label: str = "Processing",
        **kwargs: Any
    ) -> Any:
        """Convenience method: Display a progress bar.
        
        Args:
            current: Current progress value
            total: Total value (None for indeterminate)
            label: Progress bar label
            **kwargs: Additional parameters (color, width, etc.)
            
        Returns:
            Any: Result from progress_bar handler
        """
        return self.zEvents.progress_bar(current, total, label, **kwargs)

    def spinner(self, label: str = "Loading", style: str = "dots") -> Any:
        """Convenience method: Loading spinner context manager.
        
        Args:
            label: Spinner label
            style: Spinner style (dots, arc, line)
            
        Returns:
            Any: Context manager for spinner
        """
        return self.zEvents.spinner(label, style)

    def progress_iterator(
        self,
        iterable: Any,
        label: str = "Processing",
        **kwargs: Any
    ) -> Any:
        """Convenience method: Wrap iterable with progress bar.
        
        Args:
            iterable: Iterable to wrap
            label: Progress bar label
            **kwargs: Additional parameters
            
        Returns:
            Any: Iterator with progress bar
        """
        return self.zEvents.progress_iterator(iterable, label, **kwargs)

    def indeterminate_progress(self, label: str = "Processing") -> Any:
        """Convenience method: Indeterminate progress indicator.
        
        Args:
            label: Progress indicator label
            
        Returns:
            Any: Context manager for indeterminate progress
        """
        return self.zEvents.indeterminate_progress(label)

    def button(
        self,
        label: str,
        action: Optional[str] = None,
        color: str = "primary"
    ) -> bool:
        """Convenience method: Display a button that requires confirmation.
        
        Terminal-First Design:
        - Terminal: Colored prompt based on semantic button color
        - Bifrost: Styled button with same semantic color
        
        Args:
            label: Button label text (e.g., "Submit", "Delete", "Save")
            action: Optional action identifier or zVar name
            color: Button semantic color (primary, success, danger, warning, info, secondary)
            
        Returns:
            bool: True if clicked (y), False if cancelled (n)
        """
        return self.zEvents.button(label, action, color)

    def link(
        self,
        label: str,
        href: str,
        target: str = "_self",
        **kwargs
    ) -> Optional[Any]:
        """Convenience method: Display a semantic link with mode-aware rendering.
        
        Terminal-First Design:
        - Terminal: Auto-navigate for internal links, prompt for external links
        - Bifrost: Semantic <a> tag with proper target and security attributes
        
        Supports:
        - Internal navigation (delta $, zPath @)
        - External URLs (http/https) with target control
        - Anchor links (#section) with smooth scroll
        - Placeholder links (#) for styled text
        - Window features for custom popup windows
        
        Args:
            label: Link text to display
            href: Link destination (internal $/@, external http/https, anchor #, placeholder #)
            target: Target behavior (_self, _blank, _parent, _top)
            **kwargs: Additional parameters:
                - color: Link color theme
                - rel: Link relationship (auto-added for _blank external)
                - window: Dict with width, height, features for window.open()
                - _zClass: CSS classes for styling (e.g., "zBtn zBtn-primary")
            
        Returns:
            Navigation result (for internal links) or None
            
        Examples:
            # Internal navigation
            zcli.display.link("About", "$zAbout")
            
            # External link (new tab)
            zcli.display.link("GitHub", "https://github.com", target="_blank")
            
            # Styled as button
            zcli.display.link("Docs", "https://docs.site.com", 
                             _zClass="zBtn zBtn-primary")
            
            # Placeholder for mock/design
            zcli.display.link("Coming Soon", "#", _zClass="zBtn zBtn-secondary")
        """
        return self.zEvents.link(label, href, target, **kwargs)
