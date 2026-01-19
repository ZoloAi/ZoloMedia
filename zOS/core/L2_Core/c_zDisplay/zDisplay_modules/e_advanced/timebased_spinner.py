# zCLI/L2_Core/c_zDisplay/zDisplay_modules/e_advanced/timebased_spinner.py
"""
TimeBased Spinner Events - Animated Loading Indicators
=======================================================

This module provides animated spinner context managers for indefinite operations.
Spinners give visual feedback when the duration of an operation is unknown.

Purpose:
    - Display animated loading spinners (dots, lines, arcs, etc.)
    - Support both Terminal (threaded animation) and Bifrost (WebSocket) modes
    - Context manager pattern for automatic cleanup
    - Multiple spinner styles (dots, line, arc, arrow, bouncingBall, simple)

Public Methods:
    spinner(label, style)
        Context manager for animated loading spinner

Dependencies:
    - display_event_helpers: is_bifrost_mode, emit_websocket_event, generate_event_id
    - display_primitives: zPrimitives for terminal I/O
    - display_constants: Event names, keys, defaults, ANSI codes

Extracted From:
    display_event_timebased.py (lines 730-852, spinner styles from __init__)
"""

import time
import threading
from typing import Any, Iterator
from contextlib import contextmanager

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import (
    is_bifrost_mode,
    emit_websocket_event,
    generate_event_id
)

# Import Tier 1 primitives
from ..b_primitives.display_utilities import ActiveStateManager

# Import constants
from ..display_constants import (
    _EVENT_SPINNER_START,
    _EVENT_SPINNER_STOP,
    _KEY_EVENT,
    _KEY_SPINNER_ID,
    _KEY_LABEL,
    _KEY_STYLE,
    _KEY_CONTAINER,
    _DEFAULT_LABEL_LOADING,
    _DEFAULT_CONTAINER,
    _DEFAULT_ANIMATION_DELAY,
    _DEFAULT_THREAD_JOIN_TIMEOUT,
    _DEFAULT_SPINNER_STYLE,
    _CHAR_CHECKMARK,
    _ANSI_CARRIAGE_RETURN,
    _ANSI_CLEAR_LINE,
    _ANSI_CURSOR_UP,
    STYLE_DOTS,
    STYLE_LINE,
    STYLE_ARC,
    STYLE_ARROW,
    STYLE_BOUNCING_BALL,
    STYLE_SIMPLE
)


class SpinnerEvents:
    """
    Animated loading spinner events with context manager pattern.
    
    Provides spinner() context manager for displaying animated loading
    indicators during indefinite operations in both Terminal and Bifrost modes.
    
    Composition:
        - zPrimitives: For terminal I/O (raw, line)
        - ActiveStateManager: For tracking active spinners (Bifrost)
    
    Usage:
        # Via TimeBased coordinator
        with display.spinner("Loading data", style="dots"):
            data = fetch_large_dataset()
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    _active_state: ActiveStateManager
    _spinner_styles: dict
    _supports_carriage_return: bool
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize SpinnerEvents with reference to parent display instance.
        
        Args:
            display_instance: Parent display instance (TimeBased or zDisplay)
        
        Returns:
            None
        
        Notes:
            - zPrimitives accessed via display_instance
            - Spinner styles initialized here
            - Terminal capabilities inherited from parent
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives if hasattr(display_instance, 'zPrimitives') else None
        self._active_state = display_instance._active_state if hasattr(display_instance, '_active_state') else ActiveStateManager()
        self._supports_carriage_return = getattr(display_instance, '_supports_carriage_return', True)
        
        # Spinner styles - animation frames for each style
        self._spinner_styles = {
            STYLE_DOTS: ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            STYLE_LINE: ["-", "\\", "|", "/"],
            STYLE_ARC: ["◜", "◠", "◝", "◞", "◡", "◟"],
            STYLE_ARROW: ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            STYLE_BOUNCING_BALL: ["⠁", "⠂", "⠄", "⠂"],
            STYLE_SIMPLE: [".", "..", "...", ""]
        }
    
    @contextmanager
    def spinner(
        self,
        label: str = _DEFAULT_LABEL_LOADING,
        style: str = _DEFAULT_SPINNER_STYLE
    ) -> Iterator[None]:
        """
        Context manager for animated loading spinner (Terminal + zBifrost mode).
        
        Args:
            label: Text to show (str, default "Loading")
            style: Spinner style (str, default "dots")
                   Options: 'dots', 'line', 'arc', 'arrow', 'bouncingBall', 'simple'
        
        Returns:
            Iterator[None]: Context manager (use with 'with' statement)
        
        Terminal Example:
            Loading data ⠋  (animates through 10 frames)
            Loading data ⠙
            Loading data ⠹
            Loading data ✓  (on completion)
        
        Bifrost Example:
            Emits 'spinner_start' → React shows spinner component
            Emits 'spinner_stop' → React removes spinner
        
        Usage:
            with display.spinner("Loading data", style="dots"):
                data = fetch_large_dataset()
                process_data(data)
            # Automatically prints "Loading data ✓" on exit
        
        Notes:
            - Terminal: Background thread animates frames at 10 FPS
            - Bifrost: WebSocket events, no animation thread needed
            - Context manager ensures cleanup (stop thread + show checkmark)
            - Thread-safe: threading.Event() for coordination
        """
        # Generate unique ID for this spinner
        spinner_id = generate_event_id("spinner", label)
        
        # zBifrost mode - emit WebSocket events
        if is_bifrost_mode(self.display):
            # Start spinner
            start_event = {
                _KEY_EVENT: _EVENT_SPINNER_START,
                _KEY_SPINNER_ID: spinner_id,
                _KEY_LABEL: label,
                _KEY_STYLE: style,
                _KEY_CONTAINER: _DEFAULT_CONTAINER
            }
            emit_websocket_event(self.display, start_event)
            self._active_state.register(spinner_id, start_event)
            
            try:
                yield  # Execute the context block
            finally:
                # Stop spinner
                stop_event = {
                    _KEY_EVENT: _EVENT_SPINNER_STOP,
                    _KEY_SPINNER_ID: spinner_id
                }
                emit_websocket_event(self.display, stop_event)
                self._active_state.unregister(spinner_id)
            return
        
        # Terminal mode - animated spinner
        # Get spinner frames
        frames = self._spinner_styles.get(style, self._spinner_styles[STYLE_DOTS])
        
        # Spinner state
        stop_event_flag = threading.Event()
        frame_idx = [0]  # Use list for mutable reference in nested function
        
        def animate():
            """Animation loop running in separate thread."""
            is_first_frame = True
            while not stop_event_flag.is_set():
                frame = frames[frame_idx[0] % len(frames)]
                
                # Use capability-aware rendering
                if self._supports_carriage_return:
                    # Modern terminals: Use carriage return for in-place update
                    if self.zPrimitives:
                        self.zPrimitives.raw(
                            f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{label} {frame}",
                            flush=True
                        )
                else:
                    # Terminal.app: Use cursor-up + clear line for animation
                    if not is_first_frame:
                        # Move up and clear previous frame
                        if self.zPrimitives:
                            self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                    # Print new frame
                    if self.zPrimitives:
                        self.zPrimitives.line(f"{label} {frame}")
                    is_first_frame = False
                
                frame_idx[0] += 1
                time.sleep(_DEFAULT_ANIMATION_DELAY)
        
        # Start animation thread for all terminals
        animation_thread = threading.Thread(target=animate, daemon=True)
        animation_thread.start()
        
        try:
            yield  # Execute the context block
        finally:
            # Stop animation if running
            if animation_thread:
                stop_event_flag.set()
                animation_thread.join(timeout=_DEFAULT_THREAD_JOIN_TIMEOUT)
            
            # Show completion
            if self._supports_carriage_return:
                # Modern terminals: Clear and show checkmark in-place
                if self.zPrimitives:
                    self.zPrimitives.raw(
                        f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{label} {_CHAR_CHECKMARK}\n",
                        flush=True
                    )
            else:
                # Terminal.app: Clear the spinner line and show checkmark
                if self.zPrimitives:
                    self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                    self.zPrimitives.line(f"{label} {_CHAR_CHECKMARK}")
