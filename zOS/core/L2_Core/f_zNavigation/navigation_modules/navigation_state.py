# zCLI/subsystems/zNavigation/navigation_modules/navigation_state.py

"""
Navigation State Management for zNavigation - Session State Component.

This module provides the Navigation class, which manages navigation state and
history within the zSession. It tracks the current location and maintains a
history of previous locations for backward navigation support.

Architecture
------------
The Navigation class is a Tier 1 (Foundation) component that manages two
primary session keys for navigation state:

1. **Current Location** (session[SESSION_KEY_CURRENT_LOCATION])
   - Stores the current navigation target, context, and timestamp
   - Updated on each navigate_to() call
   - Used to track "where we are now"

2. **Navigation History** (session[SESSION_KEY_NAVIGATION_HISTORY])
   - Stores a list of previous locations (up to _HISTORY_MAX_SIZE items)
   - FIFO (First In, First Out) overflow strategy
   - Used for backward navigation via go_back()

State Model
-----------
Current Location Structure::

    session[SESSION_KEY_CURRENT_LOCATION] = {
        "target": "some_target",
        "context": {"key": "value"},
        "timestamp": "2025-10-31 12:34:56"
    }

Navigation History Structure::

    session[SESSION_KEY_NAVIGATION_HISTORY] = [
        {"target": "prev_1", "context": {...}, "timestamp": "..."},
        {"target": "prev_2", "context": {...}, "timestamp": "..."},
        ...  # Up to 50 items (FIFO overflow)
    ]

History Management
------------------
The navigation history automatically manages its size to prevent unbounded growth:

- **Size Limit**: _HISTORY_MAX_SIZE (50 items by default)
- **Overflow Strategy**: FIFO - when limit is reached, oldest item (index 0) is removed
- **Storage**: List of location dicts in session
- **Separate from Current**: Current location is stored separately, not in history

When navigating:
1. Current location is added to history
2. New target becomes current location
3. If history exceeds limit, oldest item is removed

Core Methods
------------
Public Methods:
- navigate_to(target, context=None) -> Dict[str, str]
  Navigate to a new target, storing current location in history
  
- go_back() -> Dict[str, Any]
  Navigate back to previous location from history
  
- get_current_location() -> Dict[str, Any]
  Get the current navigation location from session
  
- get_navigation_history() -> List[Dict[str, Any]]
  Get the full navigation history list from session
  
- clear_history() -> None
  Clear all navigation history (current location preserved)

Private Methods:
- _add_to_history(location) -> None
  Add a location to history with FIFO overflow management
  
- _set_current_location(target, context) -> None
  Set current location in session with timestamp
  
- _get_timestamp() -> str
  Get current timestamp for location metadata
  
- _get_history() -> List[Dict[str, Any]]
  Get history list from session (DRY helper)

Session Integration
-------------------
This module manages navigation-specific session keys:

**Session Keys (Module-level Constants):**
- SESSION_KEY_CURRENT_LOCATION: Current navigation location
- SESSION_KEY_NAVIGATION_HISTORY: Navigation history list

**Note on Session Keys**: These are module-specific constants defined in this file,
not in zConfig's centralized session constants. This is appropriate because these
keys are only used within the navigation_state module and are not accessed by other
subsystems.

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Tier 1 (Foundation)

Integration
-----------
- Called by: zNavigation facade, MenuSystem
- Uses: zSession (state management)
- Logging: Debug logging for navigation actions, info for history clearing

Usage Examples
--------------
Navigate to a target::

    nav = Navigation(navigation_system)
    result = nav.navigate_to("settings_menu", context={"user": "admin"})
    # result = {"status": "navigated", "target": "settings_menu"}

Navigate backward::

    result = nav.go_back()
    if result.get("status") == "error":
        print(result["message"])
    else:
        print(f"Navigated to: {result['target']}")

Get current location::

    current = nav.get_current_location()
    print(f"Current target: {current.get('target')}")

Clear history::

    nav.clear_history()
    # History cleared, current location preserved

Module Constants
----------------
SESSION_KEY_* : str
    Session key names for navigation state
DICT_KEY_* : str
    Dictionary key names for location/result objects
STATUS_* : str
    Status values for navigation results
MSG_* : str
    Message strings for results and logging
HISTORY_* : int
    History management constants (size limits)
_TIMESTAMP_FORMAT : str
    Timestamp format string
"""

from zOS import time, Any, Dict, List, Optional

from .navigation_constants import (
    SESSION_KEY_CURRENT_LOCATION,
    SESSION_KEY_NAVIGATION_HISTORY,
    _DICT_KEY_TARGET,
    _DICT_KEY_CONTEXT,
    _DICT_KEY_TIMESTAMP,
    _DICT_KEY_STATUS,
    _DICT_KEY_MESSAGE,
    STATUS_NAVIGATED,
    STATUS_ERROR,
    _MSG_NO_HISTORY,
    _MSG_HISTORY_CLEARED,
    _LOG_NAVIGATING_TO,
    _HISTORY_MAX_SIZE,
    _HISTORY_FIRST_INDEX,
    _TIMESTAMP_FORMAT,
)


# ============================================================================
# Navigation Class
# ============================================================================

class Navigation:
    """
    Navigation state and history manager for zNavigation.
    
    Manages current navigation location and history of previous locations within
    zSession. Provides methods for navigating to targets, going back through history,
    and querying navigation state.
    
    Attributes
    ----------
    navigation : Any
        Reference to parent navigation system
    zcli : Any
        Reference to zCLI core instance
    logger : Any
        Logger instance for navigation operations
    
    Methods
    -------
    navigate_to(target, context=None)
        Navigate to target, storing current location in history
    go_back()
        Navigate back to previous location from history
    get_current_location()
        Get current navigation location from session
    get_navigation_history()
        Get full navigation history list from session
    clear_history()
        Clear all navigation history
    
    Private Methods
    ---------------
    _add_to_history(location)
        Add location to history with FIFO overflow
    _set_current_location(target, context)
        Set current location in session
    _get_timestamp()
        Get current timestamp for metadata
    _get_history()
        Get history list from session (DRY helper)
    
    Examples
    --------
    Navigate to a target::
    
        nav = Navigation(navigation_system)
        result = nav.navigate_to("settings", {"user": "admin"})
    
    Navigate backward::
    
        result = nav.go_back()
        if result["status"] == "error":
            print("No history available")
    
    Query current location::
    
        current = nav.get_current_location()
        target = current.get("target", "unknown")
    
    Integration
    -----------
    - Parent: zNavigation system
    - Session: Manages SESSION_KEY_CURRENT_LOCATION and SESSION_KEY_NAVIGATION_HISTORY
    - Logging: Debug for navigation actions, info for history clearing
    """

    # Class-level type declarations
    navigation: Any  # Navigation system reference
    zcli: Any  # zCLI core instance
    logger: Any  # Logger instance

    def __init__(self, navigation: Any) -> None:
        """
        Initialize navigation manager.
        
        Args
        ----
        navigation : Any
            Parent navigation system instance that provides access to zcli and logger
        
        Notes
        -----
        Stores references to the parent navigation system, zcli core, and logger
        for use during navigation operations. No state is maintained beyond these
        references - all navigation state is stored in zSession.
        
        Session Dependencies
        --------------------
        This module manages the following session keys:
        - SESSION_KEY_CURRENT_LOCATION: Dict with target, context, timestamp
        - SESSION_KEY_NAVIGATION_HISTORY: List of location dicts (up to _HISTORY_MAX_SIZE)
        """
        self.navigation = navigation
        self.zcli = navigation.zcli
        self.logger = navigation.logger

    def navigate_to(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Navigate to a specific target.
        
        Stores the current location in history before navigating to the new target.
        Updates the current location in session with the new target, context, and
        timestamp.
        
        Args
        ----
        target : str
            Navigation target (file, block, key, etc.)
        context : Optional[Dict[str, Any]], default=None
            Optional navigation context (e.g., user info, parameters)
        
        Returns
        -------
        Dict[str, str]
            Navigation result with keys:
            - "status": STATUS_NAVIGATED
            - "target": The target that was navigated to
        
        Examples
        --------
        Navigate to settings menu::
        
            result = nav.navigate_to("settings_menu")
            # result = {"status": "navigated", "target": "settings_menu"}
        
        Navigate with context::
        
            result = nav.navigate_to(
                "user_profile",
                context={"user_id": 123, "edit_mode": True}
            )
        
        Navigate multiple times (history builds up)::
        
            nav.navigate_to("page1")
            nav.navigate_to("page2")
            nav.navigate_to("page3")
            # History now has: [page1, page2]
            # Current: page3
        
        Notes
        -----
        - **History Update**: Current location (if exists) is added to history before navigation
        - **Session Mutation**: Updates session[SESSION_KEY_CURRENT_LOCATION]
        - **Automatic Overflow**: History is automatically limited to _HISTORY_MAX_SIZE items
        - **Timestamp**: New location is timestamped automatically
        
        Navigation Flow
        ---------------
        1. Log navigation action
        2. Get current location from session
        3. If current location exists, add to history (with FIFO overflow)
        4. Set new location as current (with timestamp and context)
        5. Return success result
        """
        self.logger.debug(_LOG_NAVIGATING_TO, target)
        
        # Store current location in history before navigating
        current = self.get_current_location()
        if current:
            self._add_to_history(current)
        
        # Update current location to new target
        self._set_current_location(target, context)
        
        return {
            _DICT_KEY_STATUS: STATUS_NAVIGATED,
            _DICT_KEY_TARGET: target
        }

    def go_back(self) -> Dict[str, Any]:
        """
        Navigate back to previous location.
        
        Pops the last location from history and navigates to it. If history is empty,
        returns an error result.
        
        Returns
        -------
        Dict[str, Any]
            Navigation result:
            - On success: Same format as navigate_to() result
            - On error: {"status": "error", "message": "No navigation history"}
        
        Examples
        --------
        Navigate back successfully::
        
            nav.navigate_to("page1")
            nav.navigate_to("page2")
            result = nav.go_back()
            # result = {"status": "navigated", "target": "page1"}
        
        Navigate back with no history::
        
            nav = Navigation(navigation_system)
            result = nav.go_back()
            # result = {"status": "error", "message": "No navigation history"}
        
        Handle error::
        
            result = nav.go_back()
            if result[_DICT_KEY_STATUS] == STATUS_ERROR:
                print(f"Cannot go back: {result[_DICT_KEY_MESSAGE]}")
        
        Notes
        -----
        - **History Mutation**: Pops last item from session[SESSION_KEY_NAVIGATION_HISTORY]
        - **Error Handling**: Returns error dict if history is empty (does not raise exception)
        - **Re-navigation**: Calls navigate_to() with previous target and context
        - **No History Loss**: Previous location is re-added to history by navigate_to()
        
        Algorithm
        ---------
        1. Get navigation history from session
        2. If history is empty, return error result
        3. Pop last location from history
        4. Update session with modified history
        5. Navigate to previous location (target and context)
        6. Return navigation result
        """
        # Get history from session
        history = self.get_navigation_history()
        
        # Check if history is empty
        if not history:
            return {
                _DICT_KEY_STATUS: STATUS_ERROR,
                _DICT_KEY_MESSAGE: _MSG_NO_HISTORY
            }
        
        # Pop last location from history
        previous = history.pop()
        self.zcli.session[SESSION_KEY_NAVIGATION_HISTORY] = history
        
        # Navigate to previous location
        return self.navigate_to(
            previous[_DICT_KEY_TARGET],
            previous.get(_DICT_KEY_CONTEXT)
        )

    def get_current_location(self) -> Dict[str, Any]:
        """
        Get current navigation location.
        
        Retrieves the current location from session. Returns empty dict if no
        current location is set.
        
        Returns
        -------
        Dict[str, Any]
            Current location dict with keys:
            - "target": Navigation target (str)
            - "context": Navigation context (Dict, optional)
            - "timestamp": ISO timestamp (str)
            Returns empty dict {} if no current location exists.
        
        Examples
        --------
        Get current location::
        
            current = nav.get_current_location()
            if current:
                print(f"Current target: {current['target']}")
                print(f"Timestamp: {current['timestamp']}")
        
        Handle empty location::
        
            current = nav.get_current_location()
            target = current.get("target", "unknown")
        
        Notes
        -----
        - **Read-Only**: Does not modify session state
        - **Default Value**: Returns empty dict {} if key doesn't exist in session
        - **No Validation**: Does not validate structure of returned dict
        """
        return self.zcli.session.get(SESSION_KEY_CURRENT_LOCATION, {})

    def get_navigation_history(self) -> List[Dict[str, Any]]:
        """
        Get navigation history.
        
        Retrieves the full navigation history list from session. Returns empty list
        if no history exists.
        
        Returns
        -------
        List[Dict[str, Any]]
            List of location dicts, each with keys:
            - "target": Navigation target (str)
            - "context": Navigation context (Dict, optional)
            - "timestamp": ISO timestamp (str)
            Returns empty list [] if no history exists.
        
        Examples
        --------
        Get full history::
        
            history = nav.get_navigation_history()
            print(f"History size: {len(history)}")
            for loc in history:
                print(f"- {loc['target']} at {loc['timestamp']}")
        
        Check history size::
        
            history = nav.get_navigation_history()
            if len(history) >= _HISTORY_MAX_SIZE:
                print("History is at maximum size")
        
        Notes
        -----
        - **Read-Only**: Does not modify session state
        - **Default Value**: Returns empty list [] if key doesn't exist in session
        - **Order**: Items are in chronological order (oldest first, newest last)
        - **Size Limit**: Maximum _HISTORY_MAX_SIZE items (managed by _add_to_history)
        """
        return self.zcli.session.get(SESSION_KEY_NAVIGATION_HISTORY, [])

    def clear_history(self) -> None:
        """
        Clear navigation history.
        
        Removes all items from navigation history. Current location is preserved.
        Logs an info message when history is cleared.
        
        Returns
        -------
        None
        
        Examples
        --------
        Clear history::
        
            nav.clear_history()
            # History is now empty, current location preserved
        
        Verify cleared::
        
            nav.clear_history()
            history = nav.get_navigation_history()
            assert history == []
        
        Notes
        -----
        - **Session Mutation**: Sets session[SESSION_KEY_NAVIGATION_HISTORY] to empty list
        - **Current Preserved**: Does NOT clear session[SESSION_KEY_CURRENT_LOCATION]
        - **Logging**: Logs info message when history is cleared
        - **Use Case**: Useful for starting fresh navigation or managing memory
        """
        self.zcli.session[SESSION_KEY_NAVIGATION_HISTORY] = []
        self.logger.info(_MSG_HISTORY_CLEARED)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _add_to_history(self, location: Dict[str, Any]) -> None:
        """
        Add location to navigation history.
        
        Appends location to history and enforces FIFO overflow when limit is reached.
        
        Args
        ----
        location : Dict[str, Any]
            Location dict to add to history
        
        Notes
        -----
        DRY Helper: Centralizes history access and overflow management.
        
        Algorithm
        ---------
        1. Get current history from session
        2. Append new location
        3. If history exceeds _HISTORY_MAX_SIZE, remove oldest (index 0)
        4. Update session with modified history
        
        Overflow Strategy
        -----------------
        FIFO (First In, First Out): When history reaches _HISTORY_MAX_SIZE items,
        the oldest item (at index 0) is removed before adding the new item.
        """
        # Get history using helper
        history = self._get_history()
        
        # Add location to history
        history.append(location)
        
        # Enforce size limit with FIFO overflow
        if len(history) > _HISTORY_MAX_SIZE:
            history.pop(_HISTORY_FIRST_INDEX)
        
        # Update session with modified history
        self.zcli.session[SESSION_KEY_NAVIGATION_HISTORY] = history

    def _set_current_location(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Set current navigation location.
        
        Creates a location dict with target, context, and timestamp, then stores
        it in session as the current location.
        
        Args
        ----
        target : str
            Navigation target
        context : Optional[Dict[str, Any]], default=None
            Optional navigation context
        
        Notes
        -----
        - Automatically adds timestamp using _get_timestamp()
        - Overwrites any existing current location
        - Updates session[SESSION_KEY_CURRENT_LOCATION]
        """
        location = {
            _DICT_KEY_TARGET: target,
            _DICT_KEY_CONTEXT: context,
            _DICT_KEY_TIMESTAMP: self._get_timestamp()
        }
        self.zcli.session[SESSION_KEY_CURRENT_LOCATION] = location

    def _get_timestamp(self) -> str:
        """
        Get current timestamp for navigation metadata.
        
        Returns
        -------
        str
            Current timestamp in _TIMESTAMP_FORMAT (YYYY-MM-DD HH:MM:SS)
        
        Examples
        --------
        Get timestamp::
        
            timestamp = self._get_timestamp()
            # "2025-10-31 12:34:56"
        
        Notes
        -----
        Uses time.strftime() with _TIMESTAMP_FORMAT constant.
        """
        return time.strftime(_TIMESTAMP_FORMAT)

    def _get_history(self) -> List[Dict[str, Any]]:
        """
        Get history list from session.
        
        Returns
        -------
        List[Dict[str, Any]]
            Navigation history list from session
        
        Notes
        -----
        DRY Helper: Eliminates 2-4 duplications of session history access.
        Centralizes default value handling (returns [] if key doesn't exist).
        """
        return self.zcli.session.get(SESSION_KEY_NAVIGATION_HISTORY, [])
