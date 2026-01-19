# zCLI/L2_Core/c_zDisplay/zDisplay_modules/e_advanced/timebased_progress.py
"""
TimeBased Progress Events - Progress Bars & ETA Tracking
=========================================================

This module provides progress tracking and visualization for operations with
known or unknown durations. Progress bars show visual feedback with percentages,
ETA calculations, and automatic updates.

Purpose:
    - Display progress bars with percentage and ETA
    - Wrap iterables with auto-updating progress tracking
    - Show indeterminate progress for unknown durations
    - Support both Terminal (ANSI) and Bifrost (WebSocket) modes

Public Methods:
    progress_bar(current, total, label, ...)
        Display a progress bar with percentage and ETA
        
    progress_iterator(iterable, label, ...)
        Wrap iterable with auto-updating progress bar
        
    indeterminate_progress(label)
        Show spinner for operations with unknown duration

Dependencies:
    - display_event_helpers: is_bifrost_mode, emit_websocket_event, generate_event_id
    - display_primitives: zPrimitives for terminal I/O, format_time_duration
    - display_constants: Event names, keys, defaults, ANSI codes, characters

Extracted From:
    display_event_timebased.py (lines 565-728, 853-957)
"""

import time
from typing import Any, Optional, Iterator, Callable

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import (
    is_bifrost_mode,
    emit_websocket_event,
    generate_event_id
)

# Import Tier 1 primitives
from ..b_primitives.display_utilities import ActiveStateManager, format_time_duration

# Import constants
from ..display_constants import (
    _EVENT_PROGRESS_BAR,
    _EVENT_PROGRESS_COMPLETE,
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
    _DEFAULT_LABEL_PROCESSING,
    _DEFAULT_CONTAINER,
    DEFAULT_WIDTH,
    DEFAULT_SHOW_PERCENTAGE,
    DEFAULT_SHOW_ETA,
    _CHAR_FILLED,
    _CHAR_EMPTY,
    _CHAR_SPACE,
    _ANSI_CARRIAGE_RETURN,
    _ANSI_CLEAR_LINE,
    _ANSI_CURSOR_UP,
    STYLE_DOTS
)


class ProgressEvents:
    """
    Progress tracking and visualization events.
    
    Provides progress_bar(), progress_iterator(), and indeterminate_progress()
    for displaying progress feedback in both Terminal and Bifrost modes.
    
    Composition:
        - zPrimitives: For terminal I/O (raw, line)
        - zColors: For colored progress bars
        - ActiveStateManager: For tracking active progress (Bifrost)
    
    Usage:
        # Via TimeBased coordinator
        display.progress_bar(60, 100, "Processing files")
        
        for item in display.progress_iterator(items, "Processing"):
            process(item)
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    zColors: Any
    _active_state: ActiveStateManager
    _spinner_styles: dict
    _supports_carriage_return: bool
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize ProgressEvents with reference to parent display instance.
        
        Args:
            display_instance: Parent display instance (TimeBased or zDisplay)
        
        Returns:
            None
        
        Notes:
            - zPrimitives and zColors accessed via display_instance
            - Terminal capabilities inherited from parent
            - Active state manager for Bifrost tracking
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives if hasattr(display_instance, 'zPrimitives') else None
        self.zColors = display_instance.zColors if hasattr(display_instance, 'zColors') else None
        self._active_state = display_instance._active_state if hasattr(display_instance, '_active_state') else ActiveStateManager()
        self._supports_carriage_return = getattr(display_instance, '_supports_carriage_return', True)
        
        # Spinner styles for indeterminate progress
        self._spinner_styles = {
            STYLE_DOTS: ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        }
    
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
            # New progress bar - generate unique ID
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
                self._active_state.unregister(progress_id)
            else:
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
                if self.zPrimitives:
                    self.zPrimitives.raw(f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{output}", flush=True)
            else:
                # Fallback: only show every 5th frame to reduce clutter
                if int(time.time() * 10) % 5 == 0 and self.zPrimitives:
                    self.zPrimitives.line(output)
            
            return output
        
        # Calculate percentage
        percentage = min(100, max(0, int((current / total) * 100)))
        
        # Adjust width for Terminal.app to prevent line wrapping
        adjusted_width = width
        if not self._supports_carriage_return:
            # Reduce width to fit 80-column terminal
            adjusted_width = min(width, 40)
        
        filled = int((current / total) * adjusted_width)
        bar = _CHAR_FILLED * filled + _CHAR_EMPTY * (adjusted_width - filled)
        
        # Build output components
        output_parts = [label]
        
        # Add the bar
        if color and self.zColors:
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
            if self.zPrimitives:
                self.zPrimitives.raw(f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{output}", flush=True)
                
                # Add newline if complete
                if current >= total:
                    self.zPrimitives.raw("\n")
        else:
            # Limited terminal: Use newline with cursor-up trick
            interval = max(1, total // 10)  # ~10% intervals
            should_print = (current == 0 or 
                           current >= total or 
                           current % interval == 0)
            
            if should_print and self.zPrimitives:
                # Clear previous line for updates after first one
                if current > 0:
                    self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                # Print new progress bar with newline
                self.zPrimitives.line(output)
        
        return output
    
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
        is_first_update = [True]
        frames = self._spinner_styles[STYLE_DOTS]
        
        def update() -> None:
            """Update the spinner frame (caller controls frequency)."""
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
                # Terminal.app: Use cursor-up + clear line
                if not is_first_update[0] and self.zPrimitives:
                    self.zPrimitives.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")
                # Print new frame
                if self.zPrimitives:
                    self.zPrimitives.line(f"{label} {frame}")
                is_first_update[0] = False
            
            frame_idx[0] += 1
        
        return update
