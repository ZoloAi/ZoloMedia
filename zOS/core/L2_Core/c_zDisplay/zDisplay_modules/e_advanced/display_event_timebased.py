# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_timebased.py
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    zDisplay TimeBased Events Package                      ║
║                 Progress, Spinners, and Temporal Feedback                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

REFACTORING v2.0 (Phase 4 Complete):
    - Decomposed monolith (1,219 lines) into 3 specialized modules
    - Tiered architecture (Tier 0 Infrastructure → Tier 2 Events)
    - Composition pattern: TimeBased orchestrates specialized modules

ARCHITECTURE OVERVIEW

What Makes This "TimeBased"?
    These UI elements provide temporal, non-blocking feedback for operations
    that take TIME to complete. Unlike BasicOutputs (instant display) or
    BasicInputs (wait for user), TimeBased events are ANIMATED and update
    over time while work happens in the background.

Temporal UI Elements Provided:
    1. progress_bar()         - Visual progress indicator with percentage/ETA
    2. spinner()              - Animated loading spinner (context manager)
    3. progress_iterator()    - Wrap iterable with auto-updating progress bar
    4. indeterminate_progress() - Spinner for unknown-duration operations
    5. swiper()               - Interactive content carousel with auto-advance

MODULE DECOMPOSITION (Phase 4):

    timebased_progress.py   - Progress bars, iterators, indeterminate progress
    timebased_spinner.py    - Animated loading spinners
    timebased_swiper.py     - Interactive content carousels
    display_event_timebased.py (Coordinator) - Composes all 3 modules

DUAL-MODE PATTERN (Terminal + Bifrost)

Terminal Mode (Synchronous):
    - ANSI escape sequences, box-drawing characters
    - Animation via threading
    - Non-blocking input: termios + select for keyboard navigation
    - Live updates: Overwrite same line with \r for progress bars

Bifrost Mode (Asynchronous WebSocket):
    - WebSocket events: progress_bar, spinner_start, swiper_init
    - Frontend handles rendering
    - Async-safe: asyncio.run_coroutine_threadsafe
    - State tracking: _active_progress, _active_spinners, _active_swipers

PUBLIC METHODS (Delegated to Specialized Modules):

    progress_bar(current, total, label, ...) → ProgressEvents
    progress_iterator(iterable, label, ...) → ProgressEvents
    indeterminate_progress(label) → ProgressEvents
    spinner(label, style) → SpinnerEvents
    swiper(slides, label, ...) → SwiperEvents

VERSION INFO
Created:  Week 6.4 (zDisplay subsystem refactoring)
Upgraded: Week 6.4.11c (Industry-grade: type hints, constants, docstrings)
Refactored: Phase 4 (Decomposed into 3 specialized modules)
Line Count: 1,219 → ~200 lines (coordinator) + 3 modules (~1,040 lines total)
"""

from typing import Any, Optional, List, Callable, Iterator

# Import specialized event modules (Phase 4 Decomposition)
from .timebased_progress import ProgressEvents
from .timebased_spinner import SpinnerEvents
from .timebased_swiper import SwiperEvents

# Import Tier 1 primitives
from ..b_primitives.display_utilities import ActiveStateManager
from ..b_primitives.display_rendering_helpers import get_config_value, check_prefix_match

# Import constants
from ..display_constants import (
    _DEFAULT_LABEL_PROCESSING,
    _DEFAULT_LABEL_LOADING,
    _DEFAULT_LABEL_SLIDES,
    _DEFAULT_SPINNER_STYLE,
    DEFAULT_WIDTH,
    DEFAULT_SHOW_PERCENTAGE,
    DEFAULT_SHOW_ETA,
    DEFAULT_SWIPER_DELAY,
    DEFAULT_AUTO_ADVANCE,
    DEFAULT_LOOP
)


class TimeBased:
    """
    TimeBased Events Coordinator (v2.0 - Refactored).
    
    COORDINATOR CLASS - Orchestrates specialized event modules via composition.
    
    This class no longer contains implementation logic. Instead, it instantiates
    and coordinates 3 specialized event modules, delegating all public methods
    to the appropriate module.
    
    Composition:
        - ProgressEvents: Progress bars, iterators, indeterminate progress
        - SpinnerEvents: Animated loading spinners
        - SwiperEvents: Interactive content carousels
    
    Usage:
        # Via zDisplay
        display.progress_bar(60, 100, "Processing files")
        
        with display.spinner("Loading data", style="dots"):
            data = fetch_large_dataset()
        
        for item in display.progress_iterator(items, "Processing"):
            process(item)
        
        display.swiper(slides, label="Tutorial", auto_advance=True)
    
    Architecture:
        Before (v1.x):  1,219 lines, monolithic
        After (v2.0):   ~200 lines, coordinator + 3 specialized modules (~1,040 lines total)
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    zColors: Any
    BasicOutputs: Optional[Any]
    _active_state: ActiveStateManager
    _supports_carriage_return: bool
    
    # Specialized event modules (Phase 4 Decomposition)
    ProgressEvents: ProgressEvents
    SpinnerEvents: SpinnerEvents
    SwiperEvents: SwiperEvents
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize TimeBased coordinator with specialized modules.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Phase 4 Refactoring:
            - Instantiate 3 specialized event modules
            - Detect terminal capabilities for rendering
            - Setup active state manager for Bifrost tracking
            - Maintain backward compatibility (same public API)
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        self.BasicOutputs = None  # Will be set after zEvents initialization
        
        # Active state tracking for Bifrost mode
        self._active_state = ActiveStateManager()
        
        # Detect terminal capabilities for progress rendering
        self._detect_terminal_capabilities()
        
        # Instantiate specialized event modules (Phase 4)
        self.ProgressEvents = ProgressEvents(self)
        self.SpinnerEvents = SpinnerEvents(self)
        self.SwiperEvents = SwiperEvents(self)
    
    #                        TERMINAL CAPABILITY DETECTION
    
    def _detect_terminal_capabilities(self) -> None:
        """
        Detect terminal capabilities for progress rendering.
        
        Determines if the current terminal supports ANSI escape sequences like
        carriage return (\r) for in-place progress bar updates.
        
        Sets:
            self._supports_carriage_return: bool - True if terminal supports \r
        """
        self._supports_carriage_return = True  # Default optimistic
        
        try:
            # Check for blocked terminals
            if self._is_blocked_terminal():
                self._supports_carriage_return = False
                return
            
            # Check TERM type and IDE capabilities
            term = get_config_value(self.display, "machine", "terminal", "unknown")
            supports = self._check_term_capability(term)
            
            # Apply force_ansi override if set
            self._supports_carriage_return = self._apply_ansi_override(supports)
        
        except Exception:
            self._supports_carriage_return = True  # Fail-safe default
    
    def _is_blocked_terminal(self) -> bool:
        """Check if current terminal is known to block carriage return."""
        import os
        term_program = os.getenv("TERM_PROGRAM", "").lower()
        BLOCKED_TERMINALS = {"apple_terminal", "cmd", "powershell"}
        return term_program in BLOCKED_TERMINALS
    
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
    
    # PUBLIC METHODS (Delegation to Specialized Modules)
    
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
        
        Delegates to: ProgressEvents.progress_bar()
        """
        return self.ProgressEvents.progress_bar(
            current, total, label, width, show_percentage, show_eta, start_time, color
        )
    
    def spinner(
        self,
        label: str = _DEFAULT_LABEL_LOADING,
        style: str = _DEFAULT_SPINNER_STYLE
    ) -> Iterator[None]:
        """
        Context manager for animated loading spinner.
        
        Delegates to: SpinnerEvents.spinner()
        """
        return self.SpinnerEvents.spinner(label, style)
    
    def progress_iterator(
        self,
        iterable: Any,
        label: str = _DEFAULT_LABEL_PROCESSING,
        show_percentage: bool = DEFAULT_SHOW_PERCENTAGE,
        show_eta: bool = True
    ) -> Iterator[Any]:
        """
        Wrap iterable with auto-updating progress bar.
        
        Delegates to: ProgressEvents.progress_iterator()
        """
        return self.ProgressEvents.progress_iterator(
            iterable, label, show_percentage, show_eta
        )
    
    def indeterminate_progress(
        self,
        label: str = _DEFAULT_LABEL_PROCESSING
    ) -> Callable[[], None]:
        """
        Show indeterminate progress indicator.
        
        Delegates to: ProgressEvents.indeterminate_progress()
        """
        return self.ProgressEvents.indeterminate_progress(label)
    
    def swiper(
        self,
        slides: List[str],
        label: str = _DEFAULT_LABEL_SLIDES,
        auto_advance: bool = DEFAULT_AUTO_ADVANCE,
        delay: int = DEFAULT_SWIPER_DELAY,
        loop: bool = DEFAULT_LOOP
    ) -> None:
        """
        Display interactive content carousel.
        
        Delegates to: SwiperEvents.swiper()
        """
        return self.SwiperEvents.swiper(slides, label, auto_advance, delay, loop)
