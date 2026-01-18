# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_timebased.py
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    zDisplay TimeBased Events Package                      ║
║                 Progress, Spinners, and Temporal Feedback                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

ARCHITECTURE OVERVIEW

What Makes This "TimeBased"?
    The "TimeBased" naming was chosen over "Widgets" to reflect the
    distinguishing characteristic of these UI elements: they provide temporal,
    non-blocking feedback for operations that take TIME to complete.
    
    Unlike BasicOutputs (instant display) or BasicInputs (wait for user),
    TimeBased events are ANIMATED and update over time while work happens in
    the background.

Temporal UI Elements Provided:
    1. progress_bar()         - Visual progress indicator with percentage/ETA
    2. spinner()              - Animated loading spinner (context manager)
    3. progress_iterator()    - Wrap iterable with auto-updating progress bar
    4. indeterminate_progress() - Spinner for unknown-duration operations
    5. swiper()               - Interactive content carousel with auto-advance

DUAL-MODE PATTERN (Terminal + Bifrost)

Terminal Mode (Synchronous):
    - ANSI escape sequences: Carriage returns (\r), clear screen (\033[2J)
    - Box-drawing characters: ╔═╗║╠╣╚═╝ (Unicode)
    - Animation via threading: Background threads update display
    - Non-blocking input: termios + select for keyboard navigation
    - Live updates: Overwrite same line with \r for progress bars
    - Context managers: Automatic cleanup with try/finally

Bifrost Mode (Asynchronous WebSocket):
    - WebSocket events: progress_bar, spinner_start, swiper_init, etc.
    - Frontend handles rendering: React components receive events
    - Async-safe: asyncio.run_coroutine_threadsafe for event loop
    - Touch gestures: Swipe left/right for swiper navigation
    - Auto-advance: Configurable delays for automatic progression
    - State tracking: _active_progress, _active_spinners, _active_swipers

LAYER POSITION (Event Package Layer - Depends on BasicOutputs)

    Layer 1: zDisplay.py (Facade)
            ↓
    Layer 2: display_events.py (Composition)
            ↓
    Layer 3: display_event_timebased.py ← YOU ARE HERE
            ↓
    Layer 4: display_event_outputs.py (BasicOutputs fallback)
            ↓
    Foundation: display_primitives.py (Dual-mode I/O)

    Dependencies:
        - display_primitives.py (zPrimitives): Terminal I/O (write_raw, write_line)
        - zColors: ANSI color codes
        - BasicOutputs: Fallback for non-critical output (header, text)
        - zComm: WebSocket broadcast for Bifrost mode

    Used by:
        - display_events.py (delegates to all 5 methods)
        - End-user code (via display.progress_bar, etc.)

TERMINAL PARADIGM (How Time-Based Events Work in Console)

Challenge: Terminals are line-based and synchronous by default
Solution:  Multi-threading + ANSI escape codes for animation

Progress Bars:
    1. Use \r (carriage return) to overwrite same line
    2. Caller updates in loop: for i in range(100): progress_bar(i, 100)
    3. No thread needed - caller controls update frequency

Spinners:
    1. Context manager: with spinner("Loading"): do_work()
    2. Background thread animates frames while do_work() runs
    3. Automatic cleanup: stop thread + print checkmark

Swiper (Interactive Carousel):
    1. Background thread: auto-advances slides every N seconds
    2. Foreground thread: non-blocking keyboard input (termios + select)
    3. Navigation: Arrow keys (◀▶), Number keys (1-9), Pause (p), Quit (q)
    4. Box-drawing UI: Beautiful bordered display with live status
    5. Windows fallback: Basic Enter/q navigation (no termios)

BIFROST PROTOCOL (WebSocket Event Structure)

Progress Bar Events:
    {
        "event": "progress_bar" | "progress_complete",
        "progressId": "progress_Processing_Files",
        "current": 60,
        "total": 100,
        "label": "Processing Files",
        "showPercentage": true,
        "showETA": true,
        "eta": "2m 30s",
        "color": "GREEN",
        "container": "#app"
    }

Spinner Events:
    {
        "event": "spinner_start" | "spinner_stop",
        "spinnerId": "spinner_Loading_abc123",
        "label": "Loading data",
        "style": "dots",
        "container": "#app"
    }

Swiper Events:
    {
        "event": "swiper_init" | "swiper_update" | "swiper_complete",
        "swiperId": "swiper_Tutorial_xyz789",
        "label": "Tutorial",
        "slides": ["Slide 1", "Slide 2", "Slide 3"],
        "currentSlide": 0,
        "totalSlides": 3,
        "autoAdvance": true,
        "delay": 3,
        "loop": false,
        "container": "#app"
    }

THREAD SAFETY

    Threading Usage:
        - spinner(): Background thread animates frames
        - swiper(): Background thread for auto-advance
        - threading.Event(): Clean shutdown coordination
        - daemon=True: Threads exit when main thread exits
        - join(timeout=0.5): Max 500ms wait on cleanup

    Asyncio Integration (Bifrost):
        - asyncio.get_running_loop(): Check for active event loop
        - asyncio.run_coroutine_threadsafe(): Thread-safe event loop access
        - Graceful fallback: Silent failure if no event loop

    State Tracking:
        - _active_progress: Dict[str, Dict] (progress bars by ID)
        - _active_spinners: Dict[str, Dict] (spinners by ID)
        - _active_swipers: Dict[str, Dict] (swipers by ID)
        - Cleanup: Delete from dict when complete

FUTURE EXTENSIONS (Time-Based Event Ideas)

    1. typing_indicator(): "User is typing..." with animated dots
    2. countdown_timer(): Countdown from N seconds to 0
    3. marquee(): Scrolling text banner (left-to-right)
    4. toast(): Auto-dismissing notification (5-second display)
    5. pulse_indicator(): Breathing/pulsing dot for "waiting"
    6. slide_transition(): Animated slide-in/slide-out for content

USAGE EXAMPLES

Progress Bar (Manual Updates):
    ```python
    import time
    total = 100
    start = time.time()
    for i in range(total + 1):
        display.progress_bar(
            current=i,
            total=total,
            label="Processing files",
            show_percentage=True,
            show_eta=True,
            start_time=start,
            color="GREEN"
        )
        time.sleep(0.05)
    ```

Spinner (Context Manager):
    ```python
    with display.spinner("Loading data", style="dots"):
        data = fetch_large_dataset()
        process_data(data)
    # Automatically prints "Loading data ✓" on exit
    ```

Progress Iterator (Automatic):
    ```python
    items = ["file1.txt", "file2.txt", "file3.txt"]
    for item in display.progress_iterator(items, "Processing files"):
        process_file(item)
    # Progress updates automatically for each iteration
    ```

Swiper (Interactive Carousel):
    ```python
    slides = [
        "Welcome to zCLI!",
        "Feature 1: Progress Bars",
        "Feature 2: Spinners",
        "Thank you!"
    ]
    display.swiper(
        slides,
        label="Getting Started",
        auto_advance=True,
        delay=3,
        loop=True
    )
    # Auto-advances every 3s, user can navigate with arrow keys
    ```

MODULE CONSTANTS
See constants section below for all 45+ defined constants used throughout.

VERSION INFO
Created:  Week 6.4 (zDisplay subsystem refactoring)
Upgraded: Week 6.4.11c (Industry-grade: type hints, constants, docstrings)
Line Count: 554 → ~700 lines (documentation & constants)
"""

import os
import sys
import time
import threading
import asyncio
import json
import uuid
from contextlib import contextmanager
from typing import Any, Optional, List, Dict, Callable, Iterator

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import is_bifrost_mode, emit_websocket_event, generate_event_id

# Import Tier 1 primitives
from ..b_primitives.display_utilities import ActiveStateManager, format_time_duration
from ..b_primitives.display_rendering_helpers import get_config_value, check_prefix_match

# Import constants from centralized module
from ..display_constants import (
    MODE_BIFROST,
    _EVENT_PROGRESS_BAR,
    _EVENT_PROGRESS_COMPLETE,
    _EVENT_SPINNER_START,
    _EVENT_SPINNER_STOP,
    _EVENT_SWIPER_INIT,
    _EVENT_SWIPER_UPDATE,
    _EVENT_SWIPER_COMPLETE,
    _KEY_EVENT,
    _KEY_PROGRESS_ID,
    _KEY_CURRENT,
    _KEY_TOTAL,
    _KEY_LABEL,
    _KEY_SHOW_PERCENTAGE,
    _KEY_SHOW_ETA,
    _KEY_ETA,
    _KEY_COLOR,
    _KEY_CONTAINER,
    _KEY_SPINNER_ID,
    _KEY_STYLE,
    _KEY_SWIPER_ID,
    _KEY_SLIDES,
    _KEY_CURRENT_SLIDE,
    _KEY_TOTAL_SLIDES,
    _KEY_AUTO_ADVANCE,
    _KEY_DELAY,
    _KEY_LOOP,
    _DEFAULT_LABEL_PROCESSING,
    _DEFAULT_LABEL_LOADING,
    _DEFAULT_LABEL_SLIDES,
    _DEFAULT_CONTAINER,
    DEFAULT_WIDTH,
    DEFAULT_SWIPER_DELAY,
    DEFAULT_SHOW_PERCENTAGE,
    DEFAULT_SHOW_ETA,
    DEFAULT_AUTO_ADVANCE,
    DEFAULT_LOOP,
    DEFAULT_SWIPER_WIDTH,
    _DEFAULT_THREAD_JOIN_TIMEOUT,
    _DEFAULT_ANIMATION_DELAY,
    _DEFAULT_SPINNER_STYLE,
    _CHAR_FILLED,
    _CHAR_EMPTY,
    _CHAR_CHECKMARK,
    _CHAR_SPACE,
    _BOX_TOP_LEFT,
    _BOX_TOP_RIGHT,
    _BOX_BOTTOM_LEFT,
    _BOX_BOTTOM_RIGHT,
    _BOX_HORIZONTAL,
    _BOX_VERTICAL,
    _BOX_LEFT_T,
    _BOX_RIGHT_T,
    _ANSI_CLEAR_SCREEN,
    _ANSI_HOME,
    _ANSI_CLEAR_LINE,
    _ANSI_CURSOR_UP,
    _ANSI_CARRIAGE_RETURN,
    _SWIPER_CMD_PREV,
    _SWIPER_CMD_NEXT,
    _SWIPER_CMD_PAUSE,
    _SWIPER_CMD_QUIT,
    _ESC_KEY,
    _ARROW_RIGHT,
    _ARROW_LEFT,
    _SWIPER_STATUS_PAUSED,
    _SWIPER_STATUS_AUTO,
    _SWIPER_STATUS_MANUAL,
    _MSG_SWIPER_FALLBACK,
    _MSG_BIFROST_INITIALIZED,
    _MSG_SWIPER_COMPLETED,
    STYLE_DOTS,
    STYLE_LINE,
    STYLE_ARC,
    STYLE_ARROW,
    STYLE_BOUNCING_BALL,
    STYLE_SIMPLE,
)


class TimeBased:
    """
    Time-based events for long-running operations with dual-mode support.
    
    COMPOSITION PATTERN
    This class composes BasicOutputs (for fallback text display) and depends
    on zPrimitives (for low-level Terminal/Bifrost I/O). It provides temporal,
    animated UI feedback that updates over time while work happens in background.
    
    METHODS PROVIDED
    1. progress_bar()          - Visual progress indicator with % and ETA
    2. spinner()               - Animated loading spinner (context manager)
    3. progress_iterator()     - Wrap iterable with auto-updating progress bar
    4. indeterminate_progress()- Spinner for unknown-duration operations
    5. swiper()                - Interactive content carousel with navigation
    
    DUAL-MODE SUPPORT
    - Terminal: ANSI escape sequences, threading, non-blocking keyboard input
    - Bifrost: WebSocket events for React frontend, asyncio-safe broadcasts
    
    THREAD SAFETY
    - Background threads for animation (spinner, swiper auto-advance)
    - threading.Event() for clean shutdown coordination
    - asyncio.run_coroutine_threadsafe() for event loop integration
    
    STATE TRACKING
    - _active_progress: Dict[str, Dict] (progress bars by ID)
    - _active_spinners: Dict[str, Dict] (spinners by ID)
    - _active_swipers: Dict[str, Dict] (swipers by ID)
    
    Dependencies: zPrimitives, zColors, BasicOutputs (optional), zComm (Bifrost)
    """
    
    # Type declarations for class-level attributes
    display: Any  # Parent zDisplay instance
    zPrimitives: Any  # display_primitives.zPrimitives instance
    zColors: Any  # zColors module reference
    BasicOutputs: Optional[Any]  # display_event_outputs.BasicOutputs (set after init)
    _spinner_styles: Dict[str, List[str]]  # Spinner animation frames by style name
    _active_progress: Dict[str, Dict[str, Any]]  # Active progress bars (Bifrost)
    _active_spinners: Dict[str, Dict[str, Any]]  # Active spinners (Bifrost)
    _active_swipers: Dict[str, Dict[str, Any]]  # Active swipers (Bifrost)

    def __init__(self, display_instance: Any) -> None:
        """
        Initialize TimeBased with reference to parent display instance.
        
        Args:
            display_instance: Parent zDisplay instance (provides mode, zcli, etc.)
        
        Returns:
            None
        
        Sets up:
            - display: Parent reference
            - zPrimitives: Low-level I/O (write_raw, write_line)
            - zColors: ANSI color codes
            - BasicOutputs: None initially (set by display_events.py after init)
            - _spinner_styles: Dict of animation frames for 6 spinner styles
            - _active_*: Empty dicts for tracking Bifrost state
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        # Get references to other packages for composition
        self.BasicOutputs = None  # Will be set after zEvents initialization
        
        # Spinner styles - animation frames for each style
        self._spinner_styles = {
            STYLE_DOTS: ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            STYLE_LINE: ["-", "\\", "|", "/"],
            STYLE_ARC: ["◜", "◠", "◝", "◞", "◡", "◟"],
            STYLE_ARROW: ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            STYLE_BOUNCING_BALL: ["⠁", "⠂", "⠄", "⠂"],
            STYLE_SIMPLE: [".", "..", "...", ""],
        }
        
        # Track active progress bars/spinners/swipers by ID using Tier 1 primitive
        self._active_state = ActiveStateManager()
        
        # Detect terminal capabilities for progress rendering
        self._detect_terminal_capabilities()

    #                        TERMINAL CAPABILITY DETECTION
    
    def _detect_terminal_capabilities(self) -> None:
        """Detect terminal capabilities for progress rendering.
        
        Determines if the current terminal supports ANSI escape sequences like
        carriage return (\r) for in-place progress bar updates.
        
        Sets:
            self._supports_carriage_return: bool - True if terminal supports \r
        """
        self._supports_carriage_return = True  # Default optimistic
        
        try:
            # Check for blocked terminals (Terminal.app, cmd.exe)
            if self._is_blocked_terminal():
                self._supports_carriage_return = False
                return
            
            # Check TERM type and IDE capabilities
            term = self._get_term_from_config()
            supports = self._check_term_capability(term)
            
            # Apply force_ansi override if set
            self._supports_carriage_return = self._apply_ansi_override(supports)
                    
        except Exception:
            self._supports_carriage_return = True  # Fail-safe default

    def _is_blocked_terminal(self) -> bool:
        """Check if current terminal is known to block carriage return."""
        term_program = os.getenv("TERM_PROGRAM", "").lower()
        BLOCKED_TERMINALS = {"apple_terminal", "cmd", "powershell"}
        return term_program in BLOCKED_TERMINALS

    def _get_term_from_config(self) -> str:
        """Get TERM value from zConfig machine detection."""
        return get_config_value(self.display, "machine", "terminal", "unknown")

    def _check_term_capability(self, term: str) -> bool:
        """Check if TERM type supports carriage return."""
        CAPABLE_TERMS = {
            "screen", "screen-256color", "screen-16color",
            "tmux", "tmux-256color", "tmux-16color",
            "alacritty", "kitty", "wezterm",
            "iterm", "iterm2",
            "linux", "cygwin", "rxvt", "konsole", "gnome", "xfce"
        }
        
        # Check if term matches any capable terminal
        supports = check_prefix_match(term, CAPABLE_TERMS)
        
        # xterm variants are capable
        if not supports and term.lower().startswith("xterm"):
            supports = True
        
        # Fallback: Check IDE for unknown terminals
        if not supports and term.lower() in ["unknown", "dumb"]:
            supports = self._check_ide_capability()
        
        return supports

    def _check_ide_capability(self) -> bool:
        """Check if running in a modern IDE that supports ANSI."""
        ide = get_config_value(self.display, "machine", "ide", None)
        if not ide:
            return False
        
        CAPABLE_IDES = {"cursor", "code", "fleet", "zed", "pycharm", "webstorm"}
        return ide.lower() in CAPABLE_IDES

    def _apply_ansi_override(self, supports: bool) -> bool:
        """Apply force_ansi override from zSpark if present."""
        if not hasattr(self.display, 'zcli') or not hasattr(self.display.zcli, 'session'):
            return supports
        
        zspark = self.display.zcli.session.get("zSpark", {})
        force_ansi = zspark.get("force_ansi")
        
        if force_ansi is True:
            return True
        elif force_ansi is False:
            return False
        
        return supports

    #                              HELPER METHODS
    
    def _is_bifrost_mode(self) -> bool:
        """
        Check if running in zBifrost (WebSocket) mode.
        
        DEPRECATED: This method now delegates to Tier 0 infrastructure helper.
        Use is_bifrost_mode(display) directly for new code.
        
        Returns:
            bool: True if in Bifrost/GUI mode, False if in Terminal mode
        
        Notes:
            - Gracefully handles missing display or mode attribute
            - Used to determine Terminal vs. Bifrost rendering path
            - Delegates to: display_event_helpers.is_bifrost_mode()
        """
        # Delegate to Tier 0 infrastructure helper
        return is_bifrost_mode(self.display)
    
    def _emit_websocket_event(self, event_data: Dict[str, Any]) -> None:
        """
        Emit a WebSocket event for zBifrost mode.
        
        DEPRECATED: This method now delegates to Tier 0 infrastructure helper.
        Use emit_websocket_event(display, event_data) directly for new code.
        
        Args:
            event_data: Event dictionary with 'event' key and payload
        
        Returns:
            None
        
        Notes:
            - Only sends if in Bifrost mode
            - Uses zComm.broadcast_websocket() for async event loop
            - Thread-safe: asyncio.run_coroutine_threadsafe()
            - Graceful failure: Silent return if no event loop or zComm missing
            - Delegates to: display_event_helpers.emit_websocket_event()
        
        Example event_data:
            {
                "event": "progress_bar",
                "progressId": "progress_Processing_Files",
                "current": 60,
                "total": 100,
                "label": "Processing Files"
            }
        """
        # Delegate to Tier 0 infrastructure helper
        emit_websocket_event(self.display, event_data)
    
    def _format_time(self, seconds: float) -> str:
        """
        Format seconds into human-readable time string.
        
        Delegates to Tier 1 primitive for formatting (backward compatibility wrapper).
        
        Args:
            seconds: Duration in seconds (float)
        
        Returns:
            str: Formatted time string (e.g., "5s", "2m 30s", "1h 15m")
        
        Examples:
            - _format_time(45.2) → "45s"
            - _format_time(150) → "2m 30s"
            - _format_time(3720) → "1h 2m"
        
        Notes:
            - Delegates to format_time_duration() (Tier 1 primitive)
            - Used for ETA display in progress_bar()
            - Automatically chooses appropriate unit (s/m/h)
        """
        return format_time_duration(seconds)
    
    #                           PUBLIC METHODS

    def progress_bar(
        self,
        current: int,
        total: Optional[int] = None,
        label: str = _DEFAULT_LABEL_PROCESSING,
        width: int = DEFAULT_WIDTH,
        show_percentage: bool = DEFAULT_SHOW_PERCENTAGE,
        show_eta: bool = DEFAULT_SHOW_ETA,
        start_time: Optional[float] = None,
        color: Optional[str] = None
    ) -> str:
        """
        Display a progress bar (Terminal + zBifrost mode).
        
        Args:
            current: Current progress value (int)
            total: Total value (int) or None for indeterminate spinner
            label: Description text (str, default "Processing")
            width: Bar width in characters (int, default 50)
            show_percentage: Show percentage complete (bool, default True)
            show_eta: Show estimated time to completion (bool, default False)
            start_time: Start timestamp for ETA calculation (float, optional)
            color: Color name for the bar (str, optional)
        
        Returns:
            str: The rendered progress bar string
        
        Terminal Example:
            Processing files [████████████░░░░░░░] 60% (ETA: 2m 30s)
        
        Bifrost Example:
            Emits WebSocket event → React renders progress component
        
        Notes:
            - Terminal: Uses \r (carriage return) to overwrite same line
            - Bifrost: Emits 'progress_bar' or 'progress_complete' event
            - Indeterminate mode: If total=None, shows spinner instead of bar
            - ETA calculation: Requires start_time parameter
        """
        # Generate unique ID - check if we're updating an existing progress bar
        existing_id = self._active_state.find_by_label("progress", label)
        if existing_id:
            # Reuse existing ID for updates
            progress_id = existing_id
        else:
            # New progress bar - generate unique ID using Tier 0 primitive
            progress_id = generate_event_id("progress", label)
        
        # Calculate ETA string if requested
        eta_str = None
        if show_eta and start_time and current > 0 and total and total > 0:
            elapsed = time.time() - start_time
            rate = current / elapsed
            remaining = (total - current) / rate if rate > 0 else 0
            eta_str = format_time_duration(remaining)
        
        # zBifrost mode - emit WebSocket event
        if is_bifrost_mode(self.display):
            event_data = {
                _KEY_EVENT: _EVENT_PROGRESS_BAR if current < total else _EVENT_PROGRESS_COMPLETE,
                _KEY_PROGRESS_ID: progress_id,
                _KEY_CURRENT: current,
                _KEY_TOTAL: total,
                _KEY_LABEL: label,
                _KEY_SHOW_PERCENTAGE: show_percentage,
                _KEY_SHOW_ETA: show_eta,
                _KEY_ETA: eta_str,
                _KEY_COLOR: color,
                _KEY_CONTAINER: _DEFAULT_CONTAINER
            }
            emit_websocket_event(self.display, event_data)
            
            # Clean up completed progress bars
            if current >= total:
                # Remove from active tracking so next progress bar with same label gets new ID
                self._active_state.unregister(progress_id)
            else:
                # Store active progress bar using Tier 1 primitive
                self._active_state.register(progress_id, event_data)
            
            return f"{label}: {current}/{total}" if total else label
        
        # Terminal mode - render to console
        # Indeterminate mode (spinner)
        if total is None or total == 0:
            spinner_frame = self._spinner_styles[STYLE_DOTS][int(time.time() * 10) % 10]
            output = f"{label} {spinner_frame}"
            
            # Use capability-aware rendering
            if self._supports_carriage_return:
                # Clear line before writing to prevent artifacts
                self.zPrimitives.raw(f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{output}", flush=True)
            else:
                # Fallback: only show every 5th frame to reduce clutter
                if int(time.time() * 10) % 5 == 0:
                    self.zPrimitives.line(output)
            
            return output
        
        # Calculate percentage
        percentage = min(100, max(0, int((current / total) * 100)))
        
        # Adjust width for Terminal.app to prevent line wrapping (80-column limit)
        # Reduce width if not using carriage return (Terminal.app)
        adjusted_width = width
        if not self._supports_carriage_return:
            # Terminal.app: Reduce width to fit 80-column terminal
            # Label(~15) + brackets(2) + percentage(5) + ETA(12) + bar = ~80
            adjusted_width = min(width, 40)  # Max 40-char bar for Terminal.app
        
        filled = int((current / total) * adjusted_width)
        bar = _CHAR_FILLED * filled + _CHAR_EMPTY * (adjusted_width - filled)
        
        # Build output components
        output_parts = [label]
        
        # Add the bar
        if color:
            color_code = getattr(self.zColors, color, self.zColors.RESET)
            colored_bar = f"{color_code}{bar}{self.zColors.RESET}"
            output_parts.append(f"[{colored_bar}]")
        else:
            output_parts.append(f"[{bar}]")
        
        # Add percentage
        if show_percentage:
            output_parts.append(f"{percentage}%")
        
        # Add ETA
        if eta_str:
            output_parts.append(f"(ETA: {eta_str})")
        
        # Join and render
        output = _CHAR_SPACE.join(output_parts)
        
        # Choose rendering mode based on terminal capabilities
        if self._supports_carriage_return:
            # Modern terminal: Clear line + carriage return for in-place update
            # Using \r\033[2K ensures the line is fully cleared before writing new content
            self.zPrimitives.raw(f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{output}", flush=True)
            
            # Add newline if complete
            if current >= total:
                self.zPrimitives.raw("\n")
        else:
            # Limited terminal (e.g. Terminal.app): Use newline with cursor-up trick
            # Terminal.app doesn't support \r, but DOES support cursor movement
            # Strategy: Print line with \n, then move cursor up and clear for next update
            # Calculate interval to ensure ~10 updates total (0%, 10%, 20%, ..., 100%)
            interval = max(1, total // 10)  # ~10% intervals
            should_print = (current == 0 or 
                           current >= total or 
                           current % interval == 0)
            
            if should_print:
                # For all updates after the first one, clear the previous line
                if current > 0:
                    # Move cursor up one line and clear it (removes previous progress bar)
                    self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                # Print new progress bar with newline
                self.zPrimitives.line(output)
        
        return output

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
        # Generate unique ID for this spinner using Tier 0 primitive
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
            self._emit_websocket_event(start_event)
            self._active_state.register(spinner_id, start_event)
            
            try:
                yield  # Execute the context block
            finally:
                # Stop spinner
                stop_event = {
                    _KEY_EVENT: _EVENT_SPINNER_STOP,
                    _KEY_SPINNER_ID: spinner_id
                }
                self._emit_websocket_event(stop_event)
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
                    self.zPrimitives.raw(
                        f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{label} {frame}",
                        flush=True
                    )
                else:
                    # Terminal.app: Use cursor-up + clear line for animation
                    if not is_first_frame:
                        # Move up and clear previous frame
                        self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                    # Print new frame
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
                self.zPrimitives.raw(
                    f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{label} {_CHAR_CHECKMARK}\n",
                    flush=True
                )
            else:
                # Terminal.app: Clear the spinner line and show checkmark
                self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                self.zPrimitives.line(f"{label} {_CHAR_CHECKMARK}")

    def progress_iterator(
        self,
        iterable: Any,
        label: str = _DEFAULT_LABEL_PROCESSING,
        show_percentage: bool = DEFAULT_SHOW_PERCENTAGE,
        show_eta: bool = True
    ) -> Iterator[Any]:
        """
        Wrap an iterable with a progress bar that auto-updates on each iteration.
        
        Args:
            iterable: Any iterable (list, range, generator, etc.)
            label: Description text (str, default "Processing")
            show_percentage: Show percentage complete (bool, default True)
            show_eta: Show estimated time to completion (bool, default True)
        
        Yields:
            Any: Items from the iterable, one at a time
        
        Terminal Example:
            Processing items [████████░░] 80% (ETA: 30s)
        
        Usage:
            items = ["file1.txt", "file2.txt", "file3.txt"]
            for item in display.progress_iterator(items, "Processing files"):
                process_file(item)
                # Progress bar updates automatically after each iteration
        
        Notes:
            - Converts iterable to list to get total count
            - Automatically tracks start_time for ETA calculation
            - Updates progress bar after yielding each item
        """
        items = list(iterable)
        total = len(items)
        start_time = time.time()
        
        for idx, item in enumerate(items, 1):
            self.progress_bar(
                current=idx,
                total=total,
                label=label,
                show_percentage=show_percentage,
                show_eta=show_eta,
                start_time=start_time
            )
            yield item

    def indeterminate_progress(
        self,
        label: str = _DEFAULT_LABEL_PROCESSING
    ) -> Callable[[], None]:
        """
        Show an indeterminate progress indicator (when total count is unknown).
        
        Args:
            label: Description text (str, default "Processing")
        
        Returns:
            Callable[[], None]: update() function to call for each frame update
        
        Terminal Example:
            Processing ⠋  (call update() to advance frame)
            Processing ⠙
            Processing ⠹
        
        Usage:
            update = display.indeterminate_progress("Loading data")
            while processing:
                update()  # Call to update spinner frame
                do_some_work()
                time.sleep(0.1)
        
        Notes:
            - Returns a closure that maintains frame state
            - Caller controls update frequency (call update() in loop)
            - Use spinner() context manager for automatic animation
        """
        frame_idx = [0]
        is_first_update = [True]  # Track if this is the first update
        frames = self._spinner_styles[STYLE_DOTS]
        
        def update() -> None:
            """Update the spinner frame (caller controls frequency)."""
            frame = frames[frame_idx[0] % len(frames)]
            
            # Use capability-aware rendering
            if self._supports_carriage_return:
                # Modern terminals: Use carriage return for in-place update
                self.zPrimitives.raw(
                    f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{label} {frame}",
                    flush=True
                )
            else:
                # Terminal.app: Use cursor-up + clear line
                if not is_first_update[0]:
                    # Move up and clear previous frame
                    self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                # Print new frame
                self.zPrimitives.line(f"{label} {frame}")
                is_first_update[0] = False
            
            frame_idx[0] += 1
        
        return update

    def swiper(
        self,
        slides: List[str],
        label: str = _DEFAULT_LABEL_SLIDES,
        auto_advance: bool = DEFAULT_AUTO_ADVANCE,
        delay: int = DEFAULT_SWIPER_DELAY,
        loop: bool = DEFAULT_LOOP,
        container: str = _DEFAULT_CONTAINER
    ) -> None:
        """
        Display a content carousel/swiper with navigation (Terminal + zBifrost mode).
        
        Args:
            slides: List of slide content strings (list of str)
            label: Title for the swiper (str, default "Slides")
            auto_advance: Auto-cycle through slides (bool, default True)
            delay: Seconds between auto-advance (int, default 3)
            loop: Wrap around to start after last slide (bool, default False)
            container: Bifrost DOM container (str, default "#app")
        
        Returns:
            None
        
        Terminal Mode (Hybrid B+C):
            - Auto-cycle: Slides advance every N seconds (if auto_advance=True)
            - Manual control: Arrow keys (◀ prev, ▶ next), Number keys (1-N jump)
            - Pause/Resume: 'p' key toggles auto-advance
            - Quit: 'q' key exits swiper
            
        Bifrost Mode:
            - Touch gestures: Swipe left/right for navigation
            - Auto-advance: Same as Terminal (configurable)
            - Slide indicators: Dots showing position (1/N, 2/N, etc.)
            - Loop mode: Optional wrap around to start
        
        Usage:
            slides = [
                "Welcome to zCLI!",
                "Feature 1: Progress Bars",
                "Feature 2: Spinners",
                "Feature 3: Swipers",
                "Thank you!"
            ]
            display.swiper(slides, "Getting Started", auto_advance=True, delay=3)
        
        Example output (Terminal):
            ╔═══════════════════════════════════════════════╗
            ║  Getting Started (Slide 2/5)                 ║
            ╠═══════════════════════════════════════════════╣
            ║                                               ║
            ║  Feature 1: Progress Bars                    ║
            ║                                               ║
            ╠═══════════════════════════════════════════════╣
            ║  ◀ Prev  ▶ Next  1-5 Jump  P Pause  Q Quit   ║
            ╚═══════════════════════════════════════════════╝
        """
        if not slides:
            return
        
        # Generate unique ID for this swiper using Tier 0 primitive
        swiper_id = generate_event_id("swiper", label)
        
        # zBifrost mode - emit WebSocket events
        if is_bifrost_mode(self.display):
            # Initialize swiper
            init_event = {
                _KEY_EVENT: _EVENT_SWIPER_INIT,
                _KEY_SWIPER_ID: swiper_id,
                _KEY_LABEL: label,
                _KEY_SLIDES: slides,
                _KEY_CURRENT_SLIDE: 0,
                _KEY_TOTAL_SLIDES: len(slides),
                _KEY_AUTO_ADVANCE: auto_advance,
                _KEY_DELAY: delay,
                _KEY_LOOP: loop,
                _KEY_CONTAINER: container
            }
            self._emit_websocket_event(init_event)
            self._active_state.register(swiper_id, init_event)
            
            # Bifrost mode is async - frontend handles navigation
            # For now, just display a simple confirmation in terminal fallback
            self.zPrimitives.line(f"\n{label}: Swiper initialized with {len(slides)} slides (Bifrost mode)")
            self.zPrimitives.line(_MSG_BIFROST_INITIALIZED)
            return
        
        # Terminal mode - interactive swiper with auto-cycle + manual control
        current_slide = [0]  # Mutable reference for nested function
        is_paused = [False]  # Pause state
        stop_event = threading.Event()
        
        def display_slide(idx: int) -> None:
            """Render a single slide in terminal with box-drawing UI."""
            # Clear screen (ANSI escape codes)
            self.zPrimitives.raw(f"{_ANSI_CLEAR_SCREEN}{_ANSI_HOME}", flush=True)
            
            # Calculate box width
            width = DEFAULT_SWIPER_WIDTH
            inner_width = width - 4
            
            # Build slide display
            slide_content = slides[idx]
            slide_num = f"Slide {idx + 1}/{len(slides)}"
            
            # Header
            header_text = f"  {label} ({slide_num})"
            header_padding = _CHAR_SPACE * (width - len(header_text) - 2)
            self.zPrimitives.line(
                f"{_BOX_TOP_LEFT}{_BOX_HORIZONTAL * (width - 2)}{_BOX_TOP_RIGHT}"
            )
            self.zPrimitives.line(
                f"{_BOX_VERTICAL}{header_text}{header_padding}{_BOX_VERTICAL}"
            )
            self.zPrimitives.line(
                f"{_BOX_LEFT_T}{_BOX_HORIZONTAL * (width - 2)}{_BOX_RIGHT_T}"
            )
            
            # Content (multi-line support)
            self.zPrimitives.line(
                f"{_BOX_VERTICAL}{_CHAR_SPACE * (width - 2)}{_BOX_VERTICAL}"
            )
            
            # Split content into lines and render each within the box
            content_lines = slide_content.strip().split('\n')
            for line in content_lines:
                # Truncate if line is too long
                line_trimmed = line[:inner_width - 4] if len(line) > inner_width - 4 else line
                # Left-align content with proper padding
                padding_right = _CHAR_SPACE * (inner_width - len(line_trimmed) - 4)
                content_line = f"{_BOX_VERTICAL}  {line_trimmed}{padding_right}  {_BOX_VERTICAL}"
                self.zPrimitives.line(content_line)
            
            self.zPrimitives.line(
                f"{_BOX_VERTICAL}{_CHAR_SPACE * (width - 2)}{_BOX_VERTICAL}"
            )
            
            # Controls
            if is_paused[0]:
                status = _SWIPER_STATUS_PAUSED
                pause_label = "P Resume"  # Show "Resume" when paused
            elif auto_advance:
                status = _SWIPER_STATUS_AUTO.format(delay)
                pause_label = "P Pause"   # Show "Pause" when running
            else:
                status = _SWIPER_STATUS_MANUAL
                pause_label = "P Pause"   # Manual mode can still pause
            
            self.zPrimitives.line(
                f"{_BOX_LEFT_T}{_BOX_HORIZONTAL * (width - 2)}{_BOX_RIGHT_T}"
            )
            controls = f"  ◀ Prev  ▶ Next  1-{len(slides)} Jump  {pause_label}  Q Quit  {status}"
            controls_padding = _CHAR_SPACE * max(0, width - len(controls) - 2)
            self.zPrimitives.line(
                f"{_BOX_VERTICAL}{controls}{controls_padding}{_BOX_VERTICAL}"
            )
            self.zPrimitives.line(
                f"{_BOX_BOTTOM_LEFT}{_BOX_HORIZONTAL * (width - 2)}{_BOX_BOTTOM_RIGHT}"
            )
        
        def auto_advance_loop():
            """Auto-advance slides in background thread."""
            while not stop_event.is_set():
                if auto_advance and not is_paused[0]:
                    time.sleep(delay)
                    if not stop_event.is_set():
                        # Move to next slide
                        if loop or current_slide[0] < len(slides) - 1:
                            current_slide[0] = (current_slide[0] + 1) % len(slides)
                            display_slide(current_slide[0])
                        else:
                            # Reached end without loop - stop
                            stop_event.set()
                else:
                    time.sleep(0.1)
        
        # Start auto-advance thread if enabled
        if auto_advance:
            advance_thread = threading.Thread(target=auto_advance_loop, daemon=True)
            advance_thread.start()
        
        # Display first slide
        display_slide(current_slide[0])
        
        # Handle keyboard input (non-blocking)
        try:
            import termios
            import tty
            import select
            
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            
            while not stop_event.is_set():
                # Check for keyboard input (non-blocking)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    
                    # Handle arrow keys (escape sequences)
                    if key == _ESC_KEY:  # ESC
                        next_keys = sys.stdin.read(2)
                        if next_keys == _ARROW_RIGHT:  # Right arrow
                            if loop or current_slide[0] < len(slides) - 1:
                                current_slide[0] = (current_slide[0] + 1) % len(slides)
                                display_slide(current_slide[0])
                        elif next_keys == _ARROW_LEFT:  # Left arrow
                            if loop or current_slide[0] > 0:
                                current_slide[0] = (current_slide[0] - 1) % len(slides)
                                display_slide(current_slide[0])
                    # Handle number keys (1-9)
                    elif key.isdigit():
                        target_idx = int(key) - 1
                        if 0 <= target_idx < len(slides):
                            current_slide[0] = target_idx
                            display_slide(current_slide[0])
                    # Handle pause toggle
                    elif key.lower() == _SWIPER_CMD_PAUSE:
                        is_paused[0] = not is_paused[0]
                        display_slide(current_slide[0])
                    # Handle quit
                    elif key.lower() == _SWIPER_CMD_QUIT:
                        stop_event.set()
                        break
        
        except (ImportError, AttributeError, termios.error):
            # Fallback for systems without termios (Windows)
            # Just display slides sequentially with basic input
            self.zPrimitives.line(_MSG_SWIPER_FALLBACK)
            for idx in range(len(slides)):
                if stop_event.is_set():
                    break
                display_slide(idx)
                user_input = input()
                if user_input.lower() == _SWIPER_CMD_QUIT:
                    break
        
        finally:
            # Restore terminal settings
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except (OSError, AttributeError):
                pass
            
            # Stop auto-advance thread
            stop_event.set()
            if auto_advance:
                advance_thread.join(timeout=_DEFAULT_THREAD_JOIN_TIMEOUT)
            
            # Clear screen and show completion
            self.zPrimitives.raw(f"{_ANSI_CLEAR_SCREEN}{_ANSI_HOME}", flush=True)
            self.zPrimitives.line(_MSG_SWIPER_COMPLETED.format(label))
            
            # Emit completion event for Bifrost
            if self._active_state.has(swiper_id):
                complete_event = {
                    _KEY_EVENT: _EVENT_SWIPER_COMPLETE,
                    _KEY_SWIPER_ID: swiper_id
                }
                self._emit_websocket_event(complete_event)
                self._active_state.unregister(swiper_id)


