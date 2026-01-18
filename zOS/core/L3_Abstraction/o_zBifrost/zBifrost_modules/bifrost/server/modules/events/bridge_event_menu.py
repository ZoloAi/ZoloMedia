# zCLI/subsystems/zBifrost/zBifrost_modules/bifrost/server/modules/events/bridge_event_menu.py
"""
Menu Event Handlers for zBifrost WebSocket Bridge.

This module provides event handlers for menu navigation in Bifrost mode,
enabling the backend to emit menu events and resume walker execution when
the user makes a selection.

Features:
    - Menu Selection Routing: Routes menu selections from web clients to zWalker
    - Walker State Management: Stores and resumes paused walker states
    - Breadcrumb Integration: Updates breadcrumbs on menu selection
    - Error Handling: Comprehensive exception handling for invalid selections

Architecture:
    MenuEvents acts as a bridge between WebSocket menu_selection events and
    the zWalker/zNavigation subsystems, ensuring proper flow control for
    menu-based navigation in Bifrost mode.

Integration:
    - zWalker: For resuming execution at selected block
    - zNavigation: For breadcrumb updates
    - zDisplay: For rendering selected block content

Example:
    ```python
    # Initialize menu events handler
    menu_events = MenuEvents(bifrost)
    
    # Handle menu selection from web client
    await menu_events.handle_menu_selection(ws, {
        "menu_key": "Settings_Menu*",
        "selected": "Change_Password"
    })
    ```

Module Structure:
    - Constants: Event keys, message keys, log prefixes, error messages
    - MenuEvents class: Main event handler for menu navigation
"""

from zOS import json, Dict, Any, Optional

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Data Keys (incoming event data)
_KEY_MENU_KEY = "menu_key"
_KEY_SELECTED = "selected"

# Event Names
_EVENT_MENU_SELECTION = "menu_selection"

# Message Keys (outgoing messages)
_MSG_KEY_EVENT = "event"
_MSG_KEY_DATA = "data"
_MSG_KEY_ERROR = "error"

# Log Prefixes
_LOG_PREFIX = "[MenuEvents]"
_LOG_PREFIX_SELECTION = "[MenuEvents:Selection]"

# Error Messages
_ERR_NO_MENU_KEY = "Missing menu_key in selection"
_ERR_NO_SELECTED = "Missing selected option in selection"
_ERR_NO_WALKER_STATE = "No paused walker state found for session"
_ERR_INVALID_SELECTION = "Invalid menu selection"
_ERR_RESUME_FAILED = "Failed to resume walker execution"


# ═══════════════════════════════════════════════════════════
# MenuEvents Class
# ═══════════════════════════════════════════════════════════

class MenuEvents:
    """
    Menu event handlers for Bifrost WebSocket bridge.
    
    Handles menu selection events from web clients and resumes walker
    execution at the selected block.
    
    Attributes:
        bifrost: zBifrost instance (provides logger, zcli, walker)
        logger: Logger instance from bifrost
        zcli: zCLI instance for navigation and walker access
    """
    
    def __init__(self, bifrost: Any) -> None:
        """
        Initialize MenuEvents handler.
        
        Args:
            bifrost: zBifrost instance with logger and zcli
        """
        self.bifrost = bifrost
        self.logger = bifrost.logger
        self.zcli = bifrost.zcli if hasattr(bifrost, 'zcli') else None
        
        # Storage for paused walker states (session_id -> walker_state)
        self.paused_walkers: Dict[str, Dict[str, Any]] = {}
    
    async def handle_menu_selection(self, ws: Any, data: Dict[str, Any]) -> None:
        """
        Handle menu selection event from web client.
        
        When a user selects a menu option in the Bifrost frontend, this
        handler:
        1. Validates the selection
        2. Updates breadcrumbs
        3. Retrieves the paused walker state
        4. Resumes walker execution at the selected block
        
        Args:
            ws: WebSocket connection object
            data: Event data with menu_key and selected option
            
        Expected data format:
            {
                "event": "menu_selection",
                "menu_key": "Settings_Menu*",
                "selected": "Change_Password"
            }
        """
        self.logger.info(f"{_LOG_PREFIX_SELECTION} Received menu selection")
        
        # Validate required fields
        menu_key = data.get(_KEY_MENU_KEY)
        selected = data.get(_KEY_SELECTED)
        
        if not menu_key:
            self.logger.error(f"{_LOG_PREFIX_SELECTION} {_ERR_NO_MENU_KEY}")
            await self._send_error(ws, _ERR_NO_MENU_KEY)
            return
        
        if not selected:
            self.logger.error(f"{_LOG_PREFIX_SELECTION} {_ERR_NO_SELECTED}")
            await self._send_error(ws, _ERR_NO_SELECTED)
            return
        
        # Get Bifrost session ID from WebSocket connection
        session_id = ws.session_id  # Format: zB_xxxxxxxx
        full_session_id = ws.full_session_id  # Format: zS_xxxxxxxx:zB_xxxxxxxx
        
        self.logger.debug(
            f"{_LOG_PREFIX_SELECTION} Session: {full_session_id}, "
            f"Menu: {menu_key}, Selected: {selected}"
        )
        
        # Retrieve paused walker state
        if session_id not in self.paused_walkers:
            self.logger.error(
                f"{_LOG_PREFIX_SELECTION} {_ERR_NO_WALKER_STATE} "
                f"(session: {full_session_id})"
            )
            await self._send_error(ws, _ERR_NO_WALKER_STATE)
            return
        
        walker_state = self.paused_walkers.pop(session_id)
        self.logger.debug(
            f"{_LOG_PREFIX_SELECTION} Retrieved walker state for session: {full_session_id}"
        )
        
        # Update breadcrumbs
        if self.zcli and hasattr(self.zcli, 'navigation'):
            try:
                # APPEND menu key (if not already tracked)
                self.zcli.navigation.handle_zCrumbs(
                    menu_key,
                    walker=None,  # Breadcrumbs is self-aware
                    operation='APPEND'
                )
                
                # APPEND selected option
                self.zcli.navigation.handle_zCrumbs(
                    selected,
                    walker=None,
                    operation='APPEND'
                )
                
                self.logger.debug(f"{_LOG_PREFIX_SELECTION} Breadcrumbs updated: {menu_key} > {selected}")
            except Exception as e:
                self.logger.warning(f"{_LOG_PREFIX_SELECTION} Failed to update breadcrumbs: {e}")
        
        # Resume walker execution at selected block
        try:
            # The selected option is the key to execute next
            # In zWizard, this would be handled by returning the selected key
            # which causes a "key jump" to that block
            
            # For now, we'll send a success response back to the client
            # The actual walker resumption logic will be handled by the bridge orchestrator
            # when it processes the menu_selection event
            
            response = {
                _MSG_KEY_EVENT: "menu_selected",
                _MSG_KEY_DATA: {
                    "menu_key": menu_key,
                    "selected": selected,
                    "success": True
                }
            }
            
            await ws.send(json.dumps(response))
            self.logger.info(f"{_LOG_PREFIX_SELECTION} Menu selection processed successfully")
            
            # Broadcast the selection to all clients (for multi-client sync)
            await self.bifrost.broadcast(json.dumps(response), sender=ws)
            
        except Exception as e:
            self.logger.error(f"{_LOG_PREFIX_SELECTION} {_ERR_RESUME_FAILED}: {e}")
            await self._send_error(ws, f"{_ERR_RESUME_FAILED}: {str(e)}")
    
    def store_walker_state(self, session_id: str, walker_state: Dict[str, Any]) -> None:
        """
        Store walker state for later resumption.
        
        Args:
            session_id: Session identifier
            walker_state: Walker state dict with menu context
        """
        self.paused_walkers[session_id] = walker_state
        self.logger.debug(f"{_LOG_PREFIX} Stored walker state for session: {session_id}")
    
    async def _send_error(self, ws: Any, error_message: str) -> None:
        """
        Send error response to client.
        
        Args:
            ws: WebSocket connection
            error_message: Error message to send
        """
        try:
            error_response = {
                _MSG_KEY_EVENT: "error",
                _MSG_KEY_ERROR: error_message
            }
            await ws.send(json.dumps(error_response))
        except Exception as e:
            self.logger.error(f"{_LOG_PREFIX} Failed to send error: {e}")

