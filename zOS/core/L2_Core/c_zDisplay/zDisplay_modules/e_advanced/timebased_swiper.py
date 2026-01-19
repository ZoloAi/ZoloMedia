# zCLI/L2_Core/c_zDisplay/zDisplay_modules/e_advanced/timebased_swiper.py
"""
TimeBased Swiper Events - Interactive Content Carousel
=======================================================

This module provides interactive content carousels (swipers) with keyboard
navigation, auto-advance, and touch gesture support. Swipers display multiple
slides with smooth transitions and user controls.

Purpose:
    - Display multi-slide content carousels
    - Support keyboard navigation (arrow keys, numbers)
    - Auto-advance with configurable delay
    - Box-drawing UI for Terminal, WebSocket events for Bifrost

Public Methods:
    swiper(slides, label, auto_advance, delay, loop)
        Display interactive content carousel with navigation

Dependencies:
    - display_event_helpers: is_bifrost_mode, emit_websocket_event, generate_event_id
    - display_primitives: zPrimitives for terminal I/O
    - display_constants: Event names, keys, defaults, box-drawing characters

Extracted From:
    display_event_timebased.py (lines 959-1219)
"""

import sys
import os
import time
import threading
from typing import Any, Optional, List, Dict

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
    _EVENT_SWIPER_INIT,
    _EVENT_SWIPER_UPDATE,
    _EVENT_SWIPER_COMPLETE,
    _KEY_EVENT,
    _KEY_SWIPER_ID,
    _KEY_LABEL,
    _KEY_SLIDES,
    _KEY_CURRENT_SLIDE,
    _KEY_TOTAL_SLIDES,
    _KEY_AUTO_ADVANCE,
    _KEY_DELAY,
    _KEY_LOOP,
    _KEY_CONTAINER,
    _DEFAULT_LABEL_SLIDES,
    _DEFAULT_CONTAINER,
    DEFAULT_SWIPER_DELAY,
    DEFAULT_AUTO_ADVANCE,
    DEFAULT_LOOP,
    DEFAULT_SWIPER_WIDTH,
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
    _MSG_SWIPER_COMPLETED
)


class SwiperEvents:
    """
    Interactive content carousel events with keyboard navigation.
    
    Provides swiper() for displaying multi-slide content with auto-advance,
    keyboard navigation, and box-drawing UI in Terminal or WebSocket events
    in Bifrost mode.
    
    Composition:
        - zPrimitives: For terminal I/O (raw, line)
        - BasicOutputs: For fallback rendering
        - ActiveStateManager: For tracking active swipers (Bifrost)
    
    Usage:
        # Via TimeBased coordinator
        slides = ["Slide 1 content", "Slide 2 content", "Slide 3 content"]
        display.swiper(slides, label="Tutorial", auto_advance=True, delay=3)
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    BasicOutputs: Optional[Any]
    _active_state: ActiveStateManager
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize SwiperEvents with reference to parent display instance.
        
        Args:
            display_instance: Parent display instance (TimeBased or zDisplay)
        
        Returns:
            None
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives if hasattr(display_instance, 'zPrimitives') else None
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self._active_state = display_instance._active_state if hasattr(display_instance, '_active_state') else ActiveStateManager()
    
    def swiper(
        self,
        slides: List[str],
        label: str = _DEFAULT_LABEL_SLIDES,
        auto_advance: bool = DEFAULT_AUTO_ADVANCE,
        delay: int = DEFAULT_SWIPER_DELAY,
        loop: bool = DEFAULT_LOOP
    ) -> None:
        """
        Display interactive content carousel with keyboard navigation.
        
        Args:
            slides: List of content strings to display (one per slide)
            label: Title for the swiper (str, default "Slides")
            auto_advance: Auto-advance slides (bool, default True)
            delay: Seconds between auto-advances (int, default 3)
            loop: Loop back to start (bool, default True)
        
        Returns:
            None
        
        Terminal Navigation:
            - Arrow keys (◀▶): Navigate prev/next
            - Number keys (1-9): Jump to specific slide
            - 'p': Pause/resume auto-advance
            - 'q': Quit swiper
        
        Bifrost Navigation:
            - Touch gestures: Swipe left/right
            - WebSocket events for slide changes
        
        Usage:
            slides = [
                "Welcome to the tutorial",
                "Step 1: Configuration",
                "Step 2: Implementation"
            ]
            display.swiper(slides, label="Getting Started", auto_advance=True)
        
        Notes:
            - Terminal: Box-drawing UI with keyboard input
            - Bifrost: WebSocket events for React carousel component
            - Windows fallback: Simple Enter/q navigation (no termios)
        """
        if not slides:
            return
        
        # Generate unique ID
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
                _KEY_CONTAINER: _DEFAULT_CONTAINER
            }
            emit_websocket_event(self.display, init_event)
            self._active_state.register(swiper_id, init_event)
            
            # Bifrost handles navigation via WebSocket, so we just return
            # Frontend will emit swiper_update and swiper_complete events
            return
        
        # Terminal mode - interactive carousel
        # Check if termios is available (Unix-like systems)
        try:
            import termios
            import tty
            import select
            has_termios = True
        except ImportError:
            has_termios = False
        
        # Fallback for Windows or systems without termios
        if not has_termios:
            self._swiper_fallback(slides, label)
            return
        
        # Full terminal swiper with keyboard navigation
        self._swiper_terminal(slides, label, auto_advance, delay, loop, termios, tty, select)
    
    def _swiper_fallback(self, slides: List[str], label: str) -> None:
        """
        Fallback swiper for Windows/systems without termios.
        
        Simple navigation: Press Enter for next slide, 'q' to quit.
        """
        if self.BasicOutputs:
            self.BasicOutputs.header(label, color="INFO", style="full")
        
        for idx, slide in enumerate(slides, 1):
            if self.zPrimitives:
                self.zPrimitives.line(f"\n[Slide {idx}/{len(slides)}]")
                self.zPrimitives.line(slide)
                
                if idx < len(slides):
                    user_input = input("\nPress Enter for next slide (or 'q' to quit): ").strip().lower()
                    if user_input == 'q':
                        break
        
        if self.zPrimitives:
            self.zPrimitives.line(_MSG_SWIPER_COMPLETED)
    
    def _swiper_terminal(
        self,
        slides: List[str],
        label: str,
        auto_advance: bool,
        delay: int,
        loop: bool,
        termios: Any,
        tty: Any,
        select: Any
    ) -> None:
        """
        Full-featured terminal swiper with keyboard navigation.
        
        Uses termios for non-blocking keyboard input and box-drawing characters
        for beautiful UI.
        """
        current_slide = 0
        is_paused = False
        running = True
        last_advance = time.time()
        
        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Set terminal to raw mode for non-blocking input
            tty.setraw(fd)
            
            # Main swiper loop
            while running:
                # Render current slide
                self._render_slide_box(slides[current_slide], label, current_slide + 1, len(slides), is_paused)
                
                # Check for keyboard input (non-blocking)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    
                    # Handle escape sequences (arrow keys)
                    if key == _ESC_KEY:
                        key += sys.stdin.read(2)  # Read [A or [B or [C or [D
                    
                    # Process key commands
                    if key == _SWIPER_CMD_QUIT or key == 'q':
                        running = False
                    elif key == _SWIPER_CMD_PAUSE or key == 'p':
                        is_paused = not is_paused
                        last_advance = time.time()  # Reset timer on pause toggle
                    elif key == _ARROW_RIGHT or key == _SWIPER_CMD_NEXT:
                        current_slide = self._next_slide(current_slide, len(slides), loop)
                        last_advance = time.time()
                    elif key == _ARROW_LEFT or key == _SWIPER_CMD_PREV:
                        current_slide = self._prev_slide(current_slide, len(slides), loop)
                        last_advance = time.time()
                    elif key.isdigit() and 1 <= int(key) <= len(slides):
                        current_slide = int(key) - 1
                        last_advance = time.time()
                
                # Auto-advance logic
                if auto_advance and not is_paused:
                    if time.time() - last_advance >= delay:
                        next_idx = self._next_slide(current_slide, len(slides), loop)
                        if next_idx == 0 and not loop:
                            # Reached end without loop
                            running = False
                        else:
                            current_slide = next_idx
                            last_advance = time.time()
        
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            # Clear screen and show completion message
            if self.zPrimitives:
                self.zPrimitives.raw(_ANSI_CLEAR_SCREEN + _ANSI_HOME)
                self.zPrimitives.line(_MSG_SWIPER_COMPLETED)
    
    def _render_slide_box(
        self,
        content: str,
        title: str,
        current: int,
        total: int,
        is_paused: bool
    ) -> None:
        """Render slide with box-drawing UI."""
        if not self.zPrimitives:
            return
        
        # Clear screen and move to home
        self.zPrimitives.raw(_ANSI_CLEAR_SCREEN + _ANSI_HOME)
        
        width = DEFAULT_SWIPER_WIDTH
        
        # Top border
        top_line = _BOX_TOP_LEFT + _BOX_HORIZONTAL * (width - 2) + _BOX_TOP_RIGHT
        self.zPrimitives.line(top_line)
        
        # Title line
        status = _SWIPER_STATUS_PAUSED if is_paused else (_SWIPER_STATUS_AUTO if current else _SWIPER_STATUS_MANUAL)
        title_text = f"{title} - Slide {current}/{total} {status}"
        title_line = _BOX_VERTICAL + _CHAR_SPACE + title_text.ljust(width - 4) + _CHAR_SPACE + _BOX_VERTICAL
        self.zPrimitives.line(title_line)
        
        # Separator
        sep_line = _BOX_LEFT_T + _BOX_HORIZONTAL * (width - 2) + _BOX_RIGHT_T
        self.zPrimitives.line(sep_line)
        
        # Content lines (word-wrapped)
        content_lines = self._wrap_text(content, width - 4)
        for line in content_lines:
            content_line = _BOX_VERTICAL + _CHAR_SPACE + line.ljust(width - 4) + _CHAR_SPACE + _BOX_VERTICAL
            self.zPrimitives.line(content_line)
        
        # Bottom border
        bottom_line = _BOX_BOTTOM_LEFT + _BOX_HORIZONTAL * (width - 2) + _BOX_BOTTOM_RIGHT
        self.zPrimitives.line(bottom_line)
        
        # Navigation hint
        hint = "◀▶:Navigate | p:Pause | q:Quit"
        self.zPrimitives.line(f"\n{hint}")
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to fit within specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_len = len(word)
            if current_length + word_len + len(current_line) <= width:
                current_line.append(word)
                current_length += word_len
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_len
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [""]
    
    def _next_slide(self, current: int, total: int, loop: bool) -> int:
        """Calculate next slide index."""
        next_idx = current + 1
        if next_idx >= total:
            return 0 if loop else current
        return next_idx
    
    def _prev_slide(self, current: int, total: int, loop: bool) -> int:
        """Calculate previous slide index."""
        prev_idx = current - 1
        if prev_idx < 0:
            return total - 1 if loop else 0
        return prev_idx
