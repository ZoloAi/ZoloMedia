# zCLI/L2_Core/c_zDisplay/zDisplay_modules/events/display_event_helpers.py

"""
Display Event Helpers - Tier 0 Infrastructure
==============================================

This module provides foundational infrastructure helpers for all display events.
It serves as Tier 0 in the zDisplay event architecture, providing shared utilities
that all higher-tier events depend on.

Tier Architecture:
    Tier 0: Infrastructure (THIS MODULE) - Shared mode detection, GUI/WebSocket helpers
    Tier 1: Primitives (display_primitives.py) - Raw I/O foundation
    Tier 2: Basic Events (outputs, signals) - Foundation events
    Tier 3: Data/Input/Media/Links - User interaction events
    Tier 4: Advanced (advanced, timebased) - Complex visualizations
    Tier 5: Orchestration (system) - Workflow coordination

Functions:
    generate_event_id(prefix, label) -> str
        Generate unique event IDs for tracking (e.g., "spinner_Loading_1a2b3c4d")
        Replaces manual ID generation in progress_bar, spinner, swiper
    
    is_bifrost_mode(display) -> bool
        Unified mode detection for Terminal vs Bifrost/GUI mode
        Replaces: _is_gui_mode (primitives) + _is_bifrost_mode (timebased)
    
    try_gui_event(display, event_name, data) -> bool
        Attempt to send GUI event via WebSocket
        Extracted from: display_event_system.py
    
    emit_websocket_event(display, event_data) -> None
        Emit WebSocket event for Bifrost mode
        Extracted from: display_event_timebased.py

Purpose:
    - Single source of truth for mode detection
    - DRY principle (no duplicate implementations)
    - Easier testing and maintenance
    - Clear infrastructure layer (Linux from Scratch)

Dependencies:
    - typing: Type hints
    - asyncio, json: WebSocket emission
    - zCLI constants: MODE_TERMINAL, MODE_WALKER, MODE_EMPTY
"""

# Centralized imports from zCLI
from zOS import asyncio, json, uuid, Any, Dict, Optional

# Import mode constants from display_constants
from ..display_constants import MODE_TERMINAL, MODE_WALKER, MODE_EMPTY


def generate_event_id(prefix: str, label: str) -> str:
    """
    Generate a unique event ID using a prefix, sanitized label, and short UUID.
    
    Creates human-readable but globally unique IDs for tracking active display
    events (progress bars, spinners, swipers) in Bifrost mode.
    
    Args:
        prefix: Short string indicating event type (e.g., "progress", "spinner", "swiper")
        label: Human-readable label for the event
    
    Returns:
        str: Unique event ID (e.g., "spinner_Loading_Data_1a2b3c4d")
    
    Format:
        {prefix}_{sanitized_label}_{uuid8}
        - prefix: Event type identifier
        - sanitized_label: Label with spaces replaced by underscores
        - uuid8: First 8 chars of UUID4 (collision-resistant)
    
    Examples:
        >>> generate_event_id("progress", "Processing Files")
        "progress_Processing_Files_7f3a2b1c"
        
        >>> generate_event_id("spinner", "Loading Data")
        "spinner_Loading_Data_9d4e5f6a"
    
    Usage:
        progress_id = generate_event_id("progress", label)
        self._active_state.register(progress_id, event_data)
    
    Benefits:
        - Human-readable for debugging (includes label)
        - Globally unique (UUID prevents collisions)
        - Consistent format across all event types
        - Can find by prefix+label for updates
    
    Notes:
        - Replaces manual ID generation in 3 locations:
          * TimeBased.progress_bar() - "progress_{base_id}_{timestamp}"
          * TimeBased.spinner() - "spinner_{label}_{uuid8}"
          * TimeBased.swiper() - "swiper_{label}_{uuid8}"
    """
    sanitized_label = label.replace(' ', '_')
    return f"{prefix}_{sanitized_label}_{str(uuid.uuid4())[:8]}"


def is_bifrost_mode(display: Any) -> bool:
    """
    Check if running in Bifrost/GUI mode (vs Terminal mode).
    
    This is THE unified mode detection method for all zDisplay events.
    It determines whether output should be sent via WebSocket in addition
    to (or instead of) terminal I/O.
    
    Args:
        display: zDisplay instance (or any object with 'mode' attribute)
    
    Returns:
        bool: True if in Bifrost/GUI mode (needs WebSocket output),
              False if in Terminal mode (print/input only)
    
    Mode Classification:
        Terminal modes (False): MODE_TERMINAL, MODE_WALKER, MODE_EMPTY
        Bifrost modes (True): "zBifrost", "WebSocket", or any other non-terminal mode
    
    Notes:
        - Gracefully handles missing display or mode attribute (returns False)
        - Mode comes from session[SESSION_KEY_ZMODE] set by zConfig
        - Unifies _is_gui_mode() (primitives) + _is_bifrost_mode() (timebased)
    
    Usage:
        if is_bifrost_mode(self.display):
            # Send WebSocket event
        else:
            # Use terminal I/O
    
    Replaces:
        - display_primitives._is_gui_mode() (9 occurrences)
        - display_event_timebased._is_bifrost_mode() (6 occurrences)
    """
    if not display or not hasattr(display, 'mode'):
        import logging
        logger = logging.getLogger('Framework')
        logger.info(f"[is_bifrost_mode] 🚨 NO DISPLAY OR NO MODE ATTRIBUTE! display={display}, hasattr={hasattr(display, 'mode') if display else 'N/A'}")
        return False
    
    # Non-interactive modes: anything that's not Terminal, Walker, or Empty
    result = display.mode not in (MODE_TERMINAL, MODE_WALKER, MODE_EMPTY)
    import logging
    logger = logging.getLogger('Framework')
    logger.info(f"[is_bifrost_mode] 🔍 display.mode={display.mode}, result={result}")
    return result


def try_gui_event(display: Any, event_name: str, data: Dict[str, Any]) -> bool:
    """
    Try to send GUI event to Bifrost mode (DRY helper).
    
    Attempts to send a GUI event via WebSocket to the frontend. Returns True
    if the event was sent (Bifrost mode), False if in Terminal mode.
    
    Args:
        display: zDisplay instance with zPrimitives
        event_name: WebSocket event name (e.g., "zSession", "zDash")
        data: Event data dictionary to send to frontend
    
    Returns:
        bool: True if GUI mode succeeded (message sent), False if Terminal mode
    
    Usage:
        if try_gui_event(self.display, "zSession", {"session": session_data}):
            return  # GUI handled it
        # Fall back to Terminal mode rendering
    
    Notes:
        - Delegates to display.zPrimitives.send_gui_event()
        - Used by orchestration events (zSystem) for dual-mode rendering
        - Safe to call in any mode (returns False if not Bifrost)
    
    Extracted from:
        display_event_system._try_gui_event() (1 occurrence)
    """
    if not display or not hasattr(display, 'zPrimitives'):
        return False
    
    return display.zPrimitives.send_gui_event(event_name, data)


def emit_websocket_event(display: Any, event_data: Dict[str, Any]) -> None:
    """
    Emit a WebSocket event for zBifrost mode.
    
    Sends an event to the frontend via WebSocket using zComm's broadcast
    mechanism. Only sends if in Bifrost mode, otherwise silently returns.
    
    Args:
        display: zDisplay instance with access to zcli.comm and zcli.bifrost
        event_data: Event dictionary with 'event' key and payload
    
    Returns:
        None
    
    Example event_data:
        {
            "event": "progress_bar",
            "progressId": "progress_Processing_Files",
            "current": 60,
            "total": 100,
            "label": "Processing Files"
        }
    
    Notes:
        - Only sends if is_bifrost_mode() returns True
        - Uses zComm.broadcast_websocket() for async event loop
        - Thread-safe: asyncio.run_coroutine_threadsafe()
        - Graceful failure: Silent return if no event loop or zComm missing
        - Does NOT raise exceptions (fails silently for robustness)
    
    Usage:
        emit_websocket_event(self.display, {
            "event": "spinner",
            "spinnerId": "spinner_loading",
            "active": True
        })
    
    Extracted from:
        display_event_timebased._emit_websocket_event() (6 occurrences)
        display_event_system._emit_websocket_event() (1 occurrence)
    """
    # Only send if in Bifrost mode
    if not is_bifrost_mode(display):
        return
    
    try:
        zcli = display.zcli if hasattr(display, 'zcli') else None
        if not zcli or not hasattr(zcli, 'comm'):
            return
        
        # Send via zComm's WebSocket broadcast
        if hasattr(zcli.comm, 'broadcast_websocket'):
            try:
                loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(
                    zcli.bifrost.orchestrator.broadcast(json.dumps(event_data)),
                    loop
                )
            except RuntimeError:
                # No running event loop - skip broadcast
                pass
    except Exception:
        # Silently fail in case of WebSocket issues
        # (display events should never crash the app)
        pass


def safe_get_nested(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested attribute/dict value with fallback.
    
    This provides safe navigation of nested structures (objects with attributes,
    dicts with keys, or mixed). Returns default if any level is missing.
    
    Args:
        obj: Root object to navigate (dict, object, or any)
        *keys: Sequence of keys/attributes to traverse
        default: Default value if any key/attribute missing (default: None)
    
    Returns:
        Any: Value at nested path, or default if not found
    
    Example:
        >>> data = {"user": {"profile": {"name": "Alice"}}}
        >>> safe_get_nested(data, "user", "profile", "name")
        "Alice"
        
        >>> safe_get_nested(data, "user", "missing", "key", default="Unknown")
        "Unknown"
        
        >>> session = session_object
        >>> safe_get_nested(session, "zAuth", "zSession", "username", default="guest")
        "guest"  # if path doesn't exist
    
    Usage:
        # Safe nested dict access
        username = safe_get_nested(
            session,
            SESSION_KEY_ZAUTH,
            ZAUTH_KEY_ZSESSION,
            ZAUTH_KEY_USERNAME,
            default="Unknown"
        )
        
        # Safe nested object access
        deployment = safe_get_nested(
            zcli,
            "config",
            "environment",
            "deployment",
            default="development"
        )
    
    Notes:
        - Works with both dict keys and object attributes
        - Returns default at first missing key/attribute
        - Never raises KeyError or AttributeError
        - Useful for optional configuration access
    """
    current = obj
    for key in keys:
        if current is None:
            return default
        
        # Try dict access first
        if isinstance(current, dict):
            current = current.get(key, default)
            if current == default:
                return default
        # Try attribute access
        elif hasattr(current, key):
            current = getattr(current, key, default)
        else:
            return default
    
    return current

