# zCLI/L2_Core/c_zDisplay/zDisplay_modules/b_primitives/display_utilities.py

"""
Display Utilities - Tier 1 Primitives
======================================

This module provides reusable utility primitives for zDisplay events.
It serves as Tier 1 in the zDisplay event architecture, offering foundational
components that higher-tier events can compose.

Tier Architecture:
    Tier 0: Infrastructure (display_event_helpers.py) - ID generation, mode detection
    Tier 1: Primitives (THIS MODULE, display_primitives.py) - Utilities, raw I/O
    Tier 2: Basic Events (outputs, signals)
    Tier 3: Data/Input/Media/Links
    Tier 4: Advanced (advanced, timebased)
    Tier 5: Orchestration (system)

Classes:
    ActiveStateManager: Manages the state of active display events (progress bars, spinners, swipers)

Functions:
    format_time_duration(seconds) -> str: Formats duration in seconds to human-readable string

Purpose:
    - Centralize common utility logic
    - Promote DRY principle (no duplication)
    - Improve testability and maintainability
    - Establish clear primitive layer (Linux from Scratch)

Dependencies:
    - typing: Type hints only

Usage:
    from ..b_primitives.display_utilities import ActiveStateManager, format_time_duration
    
    # State tracking
    state = ActiveStateManager()
    state.register("progress_Loading_1a2b", {"current": 50, "total": 100})
    
    # Time formatting
    eta_str = format_time_duration(125)  # "2m 5s"
"""

# Centralized imports from zCLI
from zOS import Any, Dict, Optional


class ActiveStateManager:
    """
    Manages the state of active display events for Bifrost mode.
    
    This class provides a centralized way to track active events (progress bars,
    spinners, swipers) by their unique IDs, enabling updates and cleanup.
    
    Attributes:
        _states: Internal dictionary mapping event IDs to their data
    
    Methods:
        register(event_id, event_data): Register a new active event
        unregister(event_id): Remove an active event
        get(event_id): Retrieve event data by ID
        find_by_label(prefix, label): Find existing event by prefix+label
        has(event_id): Check if event ID exists
        count(): Get number of active events
        clear_all(): Remove all active events
    
    Usage:
        # In TimeBased.__init__:
        self._active_state = ActiveStateManager()
        
        # Register event:
        event_id = generate_event_id("progress", label)
        self._active_state.register(event_id, event_data)
        
        # Find existing:
        existing_id = self._active_state.find_by_label("progress", label)
        if existing_id:
            # Update existing event
        
        # Cleanup:
        self._active_state.unregister(event_id)
    
    Replaces:
        - TimeBased._active_progress dict (10+ usages)
        - TimeBased._active_spinners dict (4+ usages)
        - TimeBased._active_swipers dict (4+ usages)
    
    Benefits:
        - Single unified API for all event types
        - find_by_label() enables smart event reuse
        - count() for debugging/monitoring
        - clear_all() for cleanup/testing
    """
    
    def __init__(self):
        """Initialize empty state manager."""
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def register(self, event_id: str, event_data: Dict[str, Any]) -> None:
        """
        Register an active event with its data.
        
        Args:
            event_id: Unique event identifier (from generate_event_id)
            event_data: Event data dictionary to store
        
        Returns:
            None
        
        Example:
            self._active_state.register("progress_Loading_1a2b", {
                "current": 50,
                "total": 100,
                "label": "Loading"
            })
        """
        self._states[event_id] = event_data
    
    def unregister(self, event_id: str) -> None:
        """
        Unregister an active event (cleanup).
        
        Args:
            event_id: Event ID to remove
        
        Returns:
            None
        
        Notes:
            - Safe to call with non-existent ID (no-op)
            - Used when event completes or is cancelled
        """
        self._states.pop(event_id, None)
    
    def get(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve event data by ID.
        
        Args:
            event_id: Event ID to look up
        
        Returns:
            Optional[Dict[str, Any]]: Event data dict if found, None otherwise
        
        Example:
            event_data = self._active_state.get("progress_Loading_1a2b")
            if event_data:
                current = event_data["current"]
        """
        return self._states.get(event_id)
    
    def find_by_label(self, prefix: str, label: str) -> Optional[str]:
        """
        Find an existing event ID by its prefix and label.
        
        Useful for updating existing events rather than creating duplicates.
        Matches events that start with "{prefix}_{sanitized_label}" and have
        the same label in their data.
        
        Args:
            prefix: Event type prefix (e.g., "progress", "spinner")
            label: Human-readable label to match
        
        Returns:
            Optional[str]: Event ID if found, None otherwise
        
        Example:
            # Check if progress bar with this label already exists
            existing_id = self._active_state.find_by_label("progress", "Loading")
            if existing_id:
                # Update existing progress bar
                progress_id = existing_id
            else:
                # Create new progress bar
                progress_id = generate_event_id("progress", "Loading")
        
        Notes:
            - Enables smart event reuse (avoid duplicate progress bars)
            - Matches on both ID prefix and label data
        """
        sanitized_label = label.replace(' ', '_')
        prefix_pattern = f"{prefix}_{sanitized_label}"
        
        for event_id, event_data in self._states.items():
            if event_id.startswith(prefix_pattern) and event_data.get('label') == label:
                return event_id
        
        return None
    
    def has(self, event_id: str) -> bool:
        """
        Check if an event with the given ID is currently active.
        
        Args:
            event_id: Event ID to check
        
        Returns:
            bool: True if event exists, False otherwise
        
        Example:
            if self._active_state.has("progress_Loading_1a2b"):
                print("Progress bar is still active")
        """
        return event_id in self._states
    
    def count(self) -> int:
        """
        Get the number of currently active events.
        
        Returns:
            int: Count of active events
        
        Example:
            print(f"Active events: {self._active_state.count()}")
        """
        return len(self._states)
    
    def clear_all(self) -> None:
        """
        Clear all active event states (for cleanup/testing).
        
        Returns:
            None
        
        Notes:
            - Use sparingly (mainly for testing or emergency cleanup)
            - Events should normally be unregistered individually
        """
        self._states.clear()


def format_time_duration(seconds: float) -> str:
    """
    Format seconds into human-readable time string.
    
    Converts a duration in seconds to a compact, human-friendly string format
    appropriate for progress bars, ETAs, and elapsed time displays.
    
    Args:
        seconds: Duration in seconds (float)
    
    Returns:
        str: Formatted time string
    
    Format Rules:
        - < 60s: "45s"
        - < 1h: "2m 30s"
        - >= 1h: "1h 15m"
    
    Examples:
        >>> format_time_duration(45.2)
        "45s"
        
        >>> format_time_duration(150)
        "2m 30s"
        
        >>> format_time_duration(3720)
        "1h 2m"
        
        >>> format_time_duration(7380)
        "2h 3m"
    
    Usage:
        # In progress bar
        eta_str = format_time_duration(eta_seconds)
        print(f"ETA: {eta_str}")
        
        # In spinner (elapsed time)
        elapsed_str = format_time_duration(time.time() - start_time)
    
    Replaces:
        - TimeBased._format_time() method (3+ usages)
        - Manual formatting in progress_bar() (2 usages)
    
    Benefits:
        - Consistent time formatting across all events
        - Testable in isolation
        - Reusable by other subsystems
        - Clear Tier 1 primitive (no dependencies)
    
    Notes:
        - Rounds down to nearest second/minute/hour
        - Always shows two units for clarity (except seconds-only)
        - Optimized for terminal width (compact format)
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"

