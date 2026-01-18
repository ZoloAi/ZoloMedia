# zCLI/subsystems/zDisplay/zDisplay_modules/display_primitives.py

"""
Primitive I/O Operations for zDisplay - Foundation Layer.

This module provides the foundational I/O primitives for the entire zDisplay subsystem.
It is THE place where Terminal/Bifrost mode switching happens for all display operations.
All 8 event files (62 references) depend on this module.

Architecture:
    zPrimitives is the foundation layer (Layer 1) that provides dual-mode I/O:
    
    - Terminal Mode: Direct console I/O via print/input (synchronous)
    - Bifrost Mode: WebSocket events via zComm (asynchronous)
    
    The dual-mode strategy ensures terminal users always get output while GUI
    users receive both terminal output and WebSocket events.

Terminal/Bifrost Mode Switching:
    This is THE ONLY place where mode switching happens for I/O operations.
    
    Mode Detection:
        - Reads self.display.mode (set from session[SESSION_KEY_ZMODE])
        - Terminal modes: "Terminal", "Walker", "" (empty string)
        - Bifrost modes: Everything else (e.g., "zBifrost", "WebSocket")
    
    Switching Logic (_is_gui_mode):
        - Returns False for Terminal/Walker modes → Use print/input
        - Returns True for all other modes → Use WebSocket + print/input
    
    Why Dual Output:
        - Terminal output: ALWAYS happens (immediate feedback)
        - WebSocket output: CONDITIONAL (when in Bifrost mode)
        - This ensures terminal users see output, GUI clients get both
        - GUI failures don't break terminal UX

Layer 1 Position:
    As a Layer 1 (Foundation) module, zPrimitives:
    
    Dependencies (Layer 0):
        - zConfig: Provides session[SESSION_KEY_ZMODE] for mode detection
        - zComm: Provides WebSocket broadcast for Bifrost output
    
    Used By (Layer 2):
        - events/display_event_outputs.py (output formatting)
        - events/display_event_signals.py (error/warning/success)
        - events/display_event_data.py (list/json display)
        - events/display_event_inputs.py (user input collection)
        - events/display_event_widgets.py (progress bars, spinners)
        - events/display_event_advanced.py (tables, complex data)
        - events/display_event_system.py (menus, dialogs)
    
    Total: 56 references from all event files (post-zAuthEvents removal)

Dual-Mode I/O Methods:
    Output Methods (synchronous):
        - raw(content, flush): Raw output, no formatting (preferred API)
        - line(content): Single line with newline (preferred API)
        - block(content): Multi-line block with final newline (preferred API)
        
        Legacy aliases (backward compatibility):
        - write_raw → raw
        - write_line → line
        - write_block → block
        
        Behavior:
            1. ALWAYS output to terminal (print)
            2. IF in Bifrost mode, ALSO send via WebSocket
    
    Input Methods (synchronous OR asynchronous):
        - read_string(prompt): Read text input
        - read_password(prompt): Read masked password input
        
        Return Types:
            - Terminal mode: Returns str (synchronous)
            - Bifrost mode: Returns asyncio.Future (asynchronous)
            - Type hint: Union[str, asyncio.Future]

zBifrost Integration:
    WebSocket Output:
        - Uses zcli.bifrost.orchestrator.broadcast() for all GUI output
        - Sends JSON events with structure:
            {
                "event": "output",
                "type": "raw" | "line" | "block",
                "content": "...",
                "timestamp": <unix_time>
            }
    
    WebSocket Input:
        - Sends input request via broadcast_websocket()
        - Returns asyncio.Future that will be resolved by GUI client
        - GUI client responds via handle_input_response()
        - Request structure:
            {
                "event": "input_request",
                "requestId": "<uuid>",
                "type": "string" | "password",
                "prompt": "...",
                "timestamp": <unix_time>
            }

Thread Safety & Async:
    - Async future management for GUI input requests
    - pending_input_requests: Dict[str, Any] (unused, kept for compatibility)
    - response_futures: Dict[str, asyncio.Future] (active futures)
    - Handles RuntimeError when no event loop is running (tests)
    - Graceful fallback to terminal input if GUI request fails

Error Handling:
    - Silent failures for GUI operations (terminal fallback)
    - Comprehensive hasattr() checks prevent crashes
    - Try/except blocks around all WebSocket operations
    - GUI failures never break terminal output

zSession Integration:
    Mode Detection Chain:
        1. zConfig sets session[SESSION_KEY_ZMODE] during Layer 0 init
        2. zDisplay.__init__() reads: self.mode = session.get(SESSION_KEY_ZMODE, "Terminal")
        3. zPrimitives._is_gui_mode() checks: self.display.mode not in (MODE_TERMINAL, MODE_WALKER, MODE_EMPTY)
    
    Session Keys Used:
        - SESSION_KEY_ZMODE: Read via self.display.mode (not directly accessed)

Usage Pattern:
    From event files (Layer 2):
        ```python
        # Output (always synchronous) - Preferred API
        self.zPrimitives.line("Hello World")
        self.zPrimitives.raw("Loading...")
        
        # Input (synchronous OR asynchronous)
        result = self.zPrimitives.read_string("Enter name: ")
        if isinstance(result, asyncio.Future):
            # Bifrost mode - await the future
            name = await result
        else:
            # Terminal mode - use directly
            name = result
        ```

Backward-Compatible Aliases:
    Legacy methods maintained for backward compatibility:
        - .write_raw → .raw (preferred)
        - .write_line → .line (preferred)
        - .write_block → .block (preferred)
    
    Other aliases:
        - .read → .read_string
"""

from zOS import json, time, getpass, asyncio, uuid, os, shutil, subprocess, Any, Dict, Union, Optional
from .display_constants import (
    # Modes (PUBLIC API)
    MODE_TERMINAL,
    MODE_WALKER,
    MODE_EMPTY,
    # Event Types (Internal)
    _EVENT_TYPE_OUTPUT,
    _EVENT_TYPE_INPUT_REQUEST,
    _EVENT_TYPE_ZDISPLAY,
    # Write Types (Internal)
    _WRITE_TYPE_RAW,
    _WRITE_TYPE_LINE,
    _WRITE_TYPE_BLOCK,
    # Input Types (Internal)
    _INPUT_TYPE_STRING,
    _INPUT_TYPE_PASSWORD,
    # JSON Keys (Internal - already private)
    _KEY_EVENT,
    _KEY_TYPE,
    _KEY_CONTENT,
    _KEY_TIMESTAMP,
    _KEY_REQUEST_ID,
    _KEY_PROMPT,
    _KEY_DISPLAY_EVENT,
    _KEY_DATA,
    _KEY_MASKED,
    _DEFAULT_PROMPT,
    _DEFAULT_FLUSH,
    _TERMINAL_COLS_DEFAULT,
    _TERMINAL_COLS_MIN,
    _TERMINAL_COLS_MAX,
)


class zPrimitives:
    """Primitive I/O operations container for streamlined display operations."""

    # Type hints for instance attributes
    display: Any  # Parent zDisplay instance
    pending_input_requests: Dict[str, Any]  # Unused, kept for compatibility
    response_futures: Dict[str, 'asyncio.Future']  # Active GUI input futures

    def __init__(self, display_instance: Any) -> None:
        """Initialize zPrimitives with reference to parent display instance.
        
        Args:
            display_instance: Parent zDisplay instance (provides mode, zcli access)
        """
        self.display = display_instance
        # Track pending input requests for GUI mode
        self.pending_input_requests = {}
        self.response_futures = {}

    def _is_gui_mode(self) -> bool:
        """Check if running in zBifrost (non-interactive WebSocket) mode.
        
        This is THE mode detection method used throughout zDisplay. It determines
        whether output should be sent via WebSocket in addition to terminal.
        
        Returns:
            bool: True if in Bifrost mode (needs WebSocket output),
                  False if in Terminal mode (print/input only)
        
        Notes:
            - Terminal modes: MODE_TERMINAL, MODE_WALKER, MODE_EMPTY
            - Bifrost modes: Everything else (e.g., "zBifrost", "WebSocket")
            - Mode comes from session[SESSION_KEY_ZMODE] set by zConfig
        """
        if not self.display or not hasattr(self.display, 'mode'):
            return False
        # Non-interactive modes: anything that's not Terminal or Walker
        return self.display.mode not in (MODE_TERMINAL, MODE_WALKER, MODE_EMPTY)

    def get_terminal_columns(self) -> int:
        """Detect terminal width (columns) at print time and clamp it.
        
        Rules:
            - Detect dynamically (env COLUMNS, shutil.get_terminal_size, tput cols)
            - Clamp to [60–120]
            - Fallback to 80 when detection is unavailable
        """
        cols: Optional[int] = None

        # 1) $COLUMNS (fast path)
        try:
            env_cols = os.environ.get("COLUMNS", "").strip()
            if env_cols.isdigit():
                cols = int(env_cols)
        except Exception:
            cols = None

        # 2) Equivalent: shutil.get_terminal_size
        if not cols:
            try:
                cols = int(shutil.get_terminal_size(fallback=(_TERMINAL_COLS_DEFAULT, 24)).columns)
            except Exception:
                cols = None

        # 3) tput cols (best-effort)
        if not cols:
            try:
                result = subprocess.run(
                    ["tput", "cols"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                out = (result.stdout or "").strip()
                if out.isdigit():
                    cols = int(out)
            except Exception:
                cols = None

        if not cols or cols <= 0:
            cols = _TERMINAL_COLS_DEFAULT

        # Clamp
        if cols < _TERMINAL_COLS_MIN:
            cols = _TERMINAL_COLS_MIN
        elif cols > _TERMINAL_COLS_MAX:
            cols = _TERMINAL_COLS_MAX

        return cols

    # Output Primitives - Terminal + Optional GUI

    def raw(self, content: str, flush: bool = _DEFAULT_FLUSH) -> None:
        """Write raw content with no formatting or newline.
        
        Dual-mode behavior:
            - ALWAYS outputs to terminal (print)
            - IF in Bifrost mode, ALSO sends via WebSocket
        
        Args:
            content: Text to write (no newline added)
            flush: Whether to flush terminal output immediately
            
        Example:
            z.display.raw("Loading")
            z.display.raw("...")
            z.display.raw(" Done!\n")
        """
        # Terminal output (always)
        print(content, end='', flush=flush)

        # GUI output (if in GUI mode)
        if self._is_gui_mode():
            self._write_gui(content, _WRITE_TYPE_RAW)

    def line(self, content: str) -> None:
        """Write single line, ensuring newline.
        
        Dual-mode behavior:
            - ALWAYS outputs to terminal with newline
            - IF in Bifrost mode, ALSO sends via WebSocket (without newline)
        
        Args:
            content: Text to write (newline added for terminal)
            
        Example:
            z.display.line("Processing complete")
        """
        # Ensure content has newline for terminal
        terminal_content = content
        if not terminal_content.endswith('\n'):
            terminal_content = terminal_content + '\n'

        # Terminal output (always)
        print(terminal_content, end='', flush=True)

        # GUI output (if in GUI mode) - send without newline
        if self._is_gui_mode():
            self._write_gui(content.rstrip('\n'), _WRITE_TYPE_LINE)

    def block(self, content: str) -> None:
        """Write multi-line block, ensuring final newline.
        
        Dual-mode behavior:
            - ALWAYS outputs to terminal with final newline
            - IF in Bifrost mode, ALSO sends via WebSocket (without trailing newlines)
        
        Args:
            content: Multi-line text to write (final newline added for terminal)
        """
        # Ensure content has newline for terminal
        terminal_content = content
        if terminal_content and not terminal_content.endswith('\n'):
            terminal_content = terminal_content + '\n'

        # Terminal output (always)
        print(terminal_content, end='', flush=True)

        # GUI output (if in GUI mode) - send without trailing newlines
        if self._is_gui_mode():
            self._write_gui(content.rstrip('\n') if content else "", _WRITE_TYPE_BLOCK)

    # GUI Communication Primitives

    def _write_gui(self, content: str, write_type: str) -> None:
        """Common GUI primitive - sends JSON event via bifrost/WebSocket for all write types.
        
        This is the core WebSocket integration method. It broadcasts output events
        to all connected Bifrost (GUI) clients via zComm's WebSocket infrastructure.
        
        Args:
            content: Text content to send (newlines already stripped)
            write_type: Type of write operation (_WRITE_TYPE_RAW, _WRITE_TYPE_LINE, _WRITE_TYPE_BLOCK)
        
        Notes:
            - Accesses zcli.bifrost.orchestrator.broadcast() from zBifrost subsystem
            - Sends JSON event with structure: {event, type, content, timestamp}
            - Silent failure: GUI errors don't affect terminal output
            - Handles RuntimeError when no asyncio event loop (tests/initialization)
        """
        # Access zcli through display instance to send via comm subsystem
        if not self.display or not hasattr(self.display, 'zcli'):
            return

        zcli = self.display.zcli
        if not zcli or not hasattr(zcli, 'comm'):
            return

        try:
            # Remove trailing newlines for JSON (consistent with WebSocket output)
            content = content.rstrip('\n') if content else ""

            # Create JSON event (same structure as WebSocket output adapter)
            event_data = {
                _KEY_EVENT: _EVENT_TYPE_OUTPUT,
                _KEY_TYPE: write_type,
                _KEY_CONTENT: content,
                _KEY_TIMESTAMP: time.time()
            }

            # Broadcast to all connected WebSocket clients
            if hasattr(zcli.comm, 'broadcast_websocket'):
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.run_coroutine_threadsafe(
                        zcli.bifrost.orchestrator.broadcast(json.dumps(event_data)),
                        loop
                    )
                except RuntimeError:
                    # No running event loop - skip broadcast (tests/initialization)
                    pass

        except Exception:
            # Silently ignore GUI send failures - terminal fallback handles the output
            pass

    def _generate_request_id(self) -> str:
        """Generate unique request ID for GUI input requests.
        
        Returns:
            str: UUID string for tracking input request/response pairs
        """
        return str(uuid.uuid4())

    def _send_input_request(self, request_type: str, prompt: str = _DEFAULT_PROMPT, **kwargs) -> Optional['asyncio.Future']:
        """Common GUI input primitive - sends input request via bifrost/WebSocket.
        
        Creates an asyncio.Future that will be resolved when the GUI client responds.
        The future is stored in response_futures dict keyed by request_id.
        
        Args:
            request_type: Type of input (_INPUT_TYPE_STRING or _INPUT_TYPE_PASSWORD)
            prompt: Prompt text to display to user
            **kwargs: Additional request parameters (e.g., masked=True for passwords)
        
        Returns:
            Optional[asyncio.Future]: Future that will resolve to user input,
                                      or None if GUI request fails (use terminal fallback)
        
        Notes:
            - Sends JSON event: {event, requestId, type, prompt, timestamp, ...kwargs}
            - GUI client must call handle_input_response() to resolve future
            - Handles RuntimeError when no event loop (tests)
        """
        # Access zcli through display instance to send via comm subsystem
        if not self.display or not hasattr(self.display, 'zcli'):
            return None

        zcli = self.display.zcli
        if not zcli or not hasattr(zcli, 'comm'):
            return None

        request_id = self._generate_request_id()

        try:
            # Create input request event (same structure as WebSocketInput)
            request_event = {
                _KEY_EVENT: _EVENT_TYPE_INPUT_REQUEST,
                _KEY_REQUEST_ID: request_id,
                _KEY_TYPE: request_type,
                _KEY_PROMPT: prompt,
                _KEY_TIMESTAMP: time.time(),
                **kwargs
            }

            # Create future for response
            try:
                loop = asyncio.get_running_loop()
                future = loop.create_future()
            except RuntimeError:
                # No running event loop - use asyncio.Future()
                future = asyncio.Future()

            self.response_futures[request_id] = future

            # Send request via zComm's WebSocket broadcast
            if hasattr(zcli.comm, 'broadcast_websocket'):
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(
                        zcli.bifrost.orchestrator.broadcast(json.dumps(request_event))
                    )
                except RuntimeError:
                    # No running event loop - for tests, just log the request
                    pass

            return future

        except Exception:
            # Return None if GUI request fails - terminal fallback will handle input
            return None

    def handle_input_response(self, request_id: str, value: Any) -> None:
        """Handle input response from GUI client.
        
        Resolves the asyncio.Future associated with the given request_id.
        Called by zComm when GUI client sends input response.
        
        Args:
            request_id: UUID of the original input request
            value: User's input value from GUI client
        """
        # Get logger from parent display instance
        logger = self.display.zcli.logger if self.display and hasattr(self.display, 'zcli') else None
        
        if logger:
            logger.info(f"🟢 handle_input_response called! RequestID: {request_id}, Value: {value}")
            logger.info(f"🔍 Available futures: {list(self.response_futures.keys())}")
        
        if request_id in self.response_futures:
            future = self.response_futures.pop(request_id)
            if logger:
                logger.info(f"✅ Found matching future! Done: {future.done()}")
            if not future.done():
                future.set_result(value)
                if logger:
                    logger.info(f"✅ Future resolved with value: {value}")
        else:
            if logger:
                logger.warning(f"⚠️ No matching future found for requestId: {request_id}")

    def send_gui_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """GUI primitive - buffer clean event object for zBifrost capture pattern.
        
        Used by event handlers to send structured events directly to GUI clients.
        Events are buffered and returned as part of command result (capture pattern).
        
        Args:
            event_name: Name of the display event (e.g., "header", "error")
            data: Event data dictionary to send to GUI
        
        Returns:
            bool: True if event was buffered successfully, False otherwise
        
        Notes:
            - Only works in Bifrost mode (returns False in Terminal mode)
            - Used by events/*.py for rich GUI rendering
            - Events are captured in buffer, not broadcasted directly
            - Example: send_gui_event("header", {"label": "Test", "color": "BLUE"})
        """
        # Only works in GUI mode
        if not self._is_gui_mode():
            return False

        if not self.display or not hasattr(self.display, 'buffer_event'):
            return False

        try:
            # Special system events (zDash, etc.) need top-level event key for frontend routing
            SPECIAL_EVENTS = ['zDash', 'zMenu', 'zDialog']
            
            if event_name in SPECIAL_EVENTS:
                # Create special event structure with top-level 'event' key
                event_data = {
                    _KEY_EVENT: event_name,  # "event": "zDash" (frontend expects this)
                    **data  # Spread data into top level
                }
            else:
                # Regular display events use nested structure
                event_data = {
                    _KEY_DISPLAY_EVENT: event_name,
                    _KEY_DATA: data,
                    _KEY_TIMESTAMP: time.time()
                }

            # Buffer event for collection (backward compatibility with zWalker)
            self.display.buffer_event(event_data)
            
            # ALSO broadcast immediately for custom handlers (new capability)
            if self.display and hasattr(self.display, 'zcli'):
                zcli = self.display.zcli
                if zcli and hasattr(zcli, 'comm') and hasattr(zcli.comm, 'broadcast_websocket'):
                    try:
                        loop = asyncio.get_running_loop()
                        asyncio.run_coroutine_threadsafe(
                            zcli.bifrost.orchestrator.broadcast(json.dumps(event_data)),
                            loop
                        )
                    except RuntimeError:
                        # No running event loop - buffering still works
                        pass
            
            return True
            
        except Exception:
            pass

        return False

    # Input Primitives - Terminal OR GUI (Dual Return Types)

    def read_string(self, prompt: str = _DEFAULT_PROMPT) -> Union[str, 'asyncio.Future']:
        """Read string input - terminal (synchronous) or GUI (async future).
        
        Critical dual-mode method with different return types based on mode:
            - Terminal mode: Returns str directly (synchronous)
            - Bifrost mode: Returns asyncio.Future (asynchronous)
        
        Args:
            prompt: Prompt text to display (default: empty string)
        
        Returns:
            Union[str, asyncio.Future]: 
                - str if in Terminal mode
                - asyncio.Future if in Bifrost mode (await to get str)
        
        Notes:
            - Always has terminal fallback if GUI request fails
            - Strips whitespace from input
            - Use isinstance(result, asyncio.Future) to detect async return
        
        Example:
            result = primitives.read_string("Enter name: ")
            if isinstance(result, asyncio.Future):
                name = await result  # Bifrost mode
            else:
                name = result  # Terminal mode
        """
        # Terminal input (always available as fallback)
        if not self._is_gui_mode():
            if prompt:
                return input(prompt).strip()
            return input().strip()

        # GUI input - return future that will be resolved by GUI response
        gui_future = self._send_input_request(_INPUT_TYPE_STRING, prompt)

        # Fallback to terminal if GUI request fails
        if gui_future is None:
            if prompt:
                return input(prompt).strip()
            return input().strip()

        return gui_future

    def read_password(self, prompt: str = _DEFAULT_PROMPT) -> Union[str, 'asyncio.Future']:
        """Read password input - terminal (synchronous) or GUI (async future).
        
        Critical dual-mode method with different return types based on mode:
            - Terminal mode: Returns str directly (synchronous, masked with getpass)
            - Bifrost mode: Returns asyncio.Future (asynchronous, GUI handles masking)
        
        Args:
            prompt: Prompt text to display (default: empty string)
        
        Returns:
            Union[str, asyncio.Future]: 
                - str if in Terminal mode (via getpass.getpass)
                - asyncio.Future if in Bifrost mode (await to get str)
        
        Notes:
            - Terminal: Uses getpass.getpass() for masked input
            - GUI: Sends masked=True flag, GUI client handles masking
            - Always has terminal fallback if GUI request fails
            - Strips whitespace from input
        
        Example:
            result = primitives.read_password("Password: ")
            if isinstance(result, asyncio.Future):
                password = await result  # Bifrost mode
            else:
                password = result  # Terminal mode (getpass)
        """
        # Terminal input (always available as fallback)
        if not self._is_gui_mode():
            if prompt:
                return getpass.getpass(prompt).strip()
            return getpass.getpass().strip()

        # GUI input - return future that will be resolved by GUI response
        gui_future = self._send_input_request(_INPUT_TYPE_PASSWORD, prompt, masked=True)

        # Fallback to terminal if GUI request fails
        if gui_future is None:
            if prompt:
                return getpass.getpass(prompt).strip()
            return getpass.getpass().strip()

        return gui_future

    # Backward-Compatible Aliases (Legacy Support)

    @property
    def write_raw(self):
        """Backward-compatible alias for raw().
        
        Note: Prefer using .raw() for cleaner API calls.
        
        Returns:
            Callable: The raw method
        """
        return self.raw

    @property
    def write_line(self):
        """Backward-compatible alias for line().
        
        Note: Prefer using .line() for cleaner API calls.
        
        Returns:
            Callable: The line method
        """
        return self.line

    @property
    def write_block(self):
        """Backward-compatible alias for block().
        
        Note: Prefer using .block() for cleaner API calls.
        
        Returns:
            Callable: The block method
        """
        return self.block

    @property
    def read(self):
        """Alias for read_string.
        
        Returns:
            Callable: The read_string method
        """
        return self.read_string
