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
import signal
from ..display_constants import (
    MODE_TERMINAL,
    MODE_WALKER,
    MODE_EMPTY,
    _EVENT_TYPE_OUTPUT,
    _EVENT_TYPE_INPUT_REQUEST,
    _EVENT_TYPE_ZDISPLAY,
    _EVENT_READ_STRING,
    _EVENT_READ_PASSWORD,
    _EVENT_READ_BOOL,
    _EVENT_READ_RANGE,
    _WRITE_TYPE_RAW,
    _WRITE_TYPE_LINE,
    _WRITE_TYPE_BLOCK,
    _INPUT_TYPE_STRING,
    _INPUT_TYPE_PASSWORD,
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
    _ANSI_CARRIAGE_RETURN,
    _ANSI_CLEAR_LINE,
    _ANSI_CURSOR_UP,
    _TERMINAL_COLS_MIN,
    _TERMINAL_COLS_MAX,
)

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import is_bifrost_mode


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
        
        DEPRECATED: This method now delegates to Tier 0 infrastructure helper.
        Use is_bifrost_mode(display) directly for new code.
        
        This is THE mode detection method used throughout zDisplay. It determines
        whether output should be sent via WebSocket in addition to terminal.
        
        Returns:
            bool: True if in Bifrost mode (needs WebSocket output),
                  False if in Terminal mode (print/input only)
        
        Notes:
            - Terminal modes: MODE_TERMINAL, MODE_WALKER, MODE_EMPTY
            - Bifrost modes: Everything else (e.g., "zBifrost", "WebSocket")
            - Mode comes from session[SESSION_KEY_ZMODE] set by zConfig
            - Delegates to: events.display_event_helpers.is_bifrost_mode()
        """
        # Delegate to Tier 0 infrastructure helper
        return is_bifrost_mode(self.display)

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
                    asyncio.run_coroutine_threadsafe(
                        zcli.bifrost.orchestrator.broadcast(json.dumps(request_event)),
                        loop
                    )
                except RuntimeError:
                    # No running event loop - likely in worker thread, send via broadcast
                    # This happens during Walker execution from Bifrost
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

    def read_string(self, prompt: str = _DEFAULT_PROMPT, **kwargs) -> Union[str, 'asyncio.Future']:
        """Read string input - terminal (synchronous) or GUI (buffered event).
        
        Critical dual-mode method with different return types based on mode:
            - Terminal mode: Returns str directly (synchronous)
            - Bifrost mode: Buffers input_request event, returns empty string (non-blocking)
        
        Args:
            prompt: Prompt text to display (default: empty string)
            **kwargs: Additional parameters:
                - type: Input type (text, email, number, tel, url, textarea, file)
                - placeholder: Placeholder text
                - required: Whether input is required
                - default: Default value
                - prefix: Text prefix (e.g., '$', 'https://')
                - suffix: Text suffix (e.g., '@company.com', '.com')
                - disabled: Display only (no interaction)
                - readonly: Display value, no editing
                - datalist: List of suggestions
                - multiple: Multiple file selection (for type='file')
        
        Returns:
            Union[str, asyncio.Future]: 
                - str if in Terminal mode (actual user input with prefix/suffix concatenated)
                - str if in Bifrost mode (empty string, actual input handled by frontend)
        
        Notes:
            - Bifrost: Buffers input_request event for frontend rendering
            - Terminal: Synchronous input() with prefix/suffix shown in prompt
            - Prefix/suffix are concatenated with user input: prefix + input + suffix
            - Always has terminal fallback if GUI request fails
            - Strips whitespace from Terminal input
        
        Example:
            # Basic input
            result = primitives.read_string("Enter name:", type="text")
            # Terminal: "Enter name: " → Returns "John"
            # Bifrost: Returns "" (input rendered on frontend)
            
            # Input with prefix/suffix (input groups)
            result = primitives.read_string("Email:", suffix="@company.com")
            # Terminal: "Email [...@company.com]: " → User types "sarah" → Returns "sarah@company.com"
            # Bifrost: Returns "" (rendered as <span>@company.com</span><input>)
        """
        # Terminal input (always available as fallback)
        # Handle multi-line textarea with Ctrl+D (EOF)
        if not self._is_gui_mode():
            input_type = kwargs.get('type', 'text')
            disabled = kwargs.get('disabled', False)
            readonly = kwargs.get('readonly', False)
            placeholder = kwargs.get('placeholder', '')
            default_value = kwargs.get('default', '')
            
            # Handle disabled inputs (display only, no interaction)
            if disabled:
                display_value = default_value or placeholder
                if prompt:
                    print(f"{prompt} [disabled]: {display_value}")
                else:
                    print(f"[disabled] {display_value}")
                return display_value  # Return placeholder/default, not empty string
            
            # Handle readonly inputs (display value, no editing)
            if readonly:
                if prompt:
                    print(f"{prompt} [readonly]: {default_value}")
                else:
                    print(f"[readonly] {default_value}")
                return default_value
            
            # Multi-line textarea input (Ctrl+D to finish)
            if input_type == 'textarea':
                if prompt:
                    print(prompt)
                    print("  (Press Ctrl+D on empty line to finish)")
                lines = []
                try:
                    while True:
                        line = input()
                        lines.append(line)
                except EOFError:
                    # Ctrl+D pressed - user is done
                    pass
                return '\n'.join(lines)
            
            # File input (Terminal mode: enter file path with validation)
            if input_type == 'file':
                import os
                multiple = kwargs.get('multiple', False)
                
                # Helper function to resolve and validate path using zParser
                def resolve_and_validate_path(path_str: str) -> tuple:
                    """
                    Resolve and validate a file path using zParser.
                    Returns (resolved_path, is_valid, error_message)
                    """
                    try:
                        # Handle zPath formats: @.path.to.file or ~.path.to.file
                        if path_str.startswith(('@.', '~.')):
                            symbol = path_str[0]
                            path_parts = path_str[1:].split('.')
                            # Prepend symbol for resolve_symbol_path
                            zRelPath_parts = [symbol] + path_parts
                            
                            # Use zParser to resolve path
                            if hasattr(self.display, 'zcli') and hasattr(self.display.zcli, 'zparser'):
                                resolved_path = self.display.zcli.zparser.resolve_symbol_path(symbol, zRelPath_parts)
                            else:
                                return None, False, "zParser not available"
                        # Handle Unix path formats: ~/path/to/file or /absolute/path or relative/path
                        else:
                            resolved_path = os.path.expanduser(path_str)
                        
                        # Validate file exists
                        if os.path.exists(resolved_path):
                            return resolved_path, True, None
                        else:
                            return resolved_path, False, f"File does not exist: {path_str}"
                    except Exception as e:
                        return None, False, f"Path resolution error: {str(e)}"
                
                while True:
                    if prompt:
                        file_prompt = prompt if prompt.endswith(' ') else prompt + ' '
                        print(file_prompt.strip())
                        if multiple:
                            print("  (Enter file paths, comma-separated for multiple files)")
                            print("  (Formats: ~/path/file.txt, @.folder.file.txt, ~.home.folder.file.txt)")
                        else:
                            print("  (Formats: ~/path/file.txt, @.folder.file.txt, ~.home.folder.file.txt)")
                    
                    user_input = input("  Path: " if prompt else "").strip()
                    
                    if not user_input:
                        print("  ❌ Error: File path cannot be empty. Please try again.")
                        continue
                    
                    # Handle multiple files (comma-separated)
                    if multiple:
                        paths = [p.strip() for p in user_input.split(',')]
                        invalid_paths = []
                        valid_paths = []
                        
                        for path in paths:
                            resolved, is_valid, error_msg = resolve_and_validate_path(path)
                            
                            if is_valid:
                                valid_paths.append(resolved)
                            else:
                                invalid_paths.append((path, error_msg))
                        
                        if invalid_paths:
                            print(f"  ❌ Error: The following paths are invalid:")
                            for path, error_msg in invalid_paths:
                                print(f"     - {path}: {error_msg}")
                            print("  Please try again.")
                            continue
                        else:
                            print(f"  ✓ Valid: {len(valid_paths)} file(s) selected")
                            return ', '.join(valid_paths)
                    else:
                        # Single file
                        resolved, is_valid, error_msg = resolve_and_validate_path(user_input)
                        
                        if is_valid:
                            print(f"  ✓ Valid: {resolved}")
                            return resolved
                        else:
                            print(f"  ❌ Error: {error_msg}")
                            print("  Please try again.")
                            continue
            
            # Datalist input (Terminal mode: show numbered options, allow free text)
            datalist_options = kwargs.get('datalist', None)
            if datalist_options and isinstance(datalist_options, list):
                if prompt:
                    print(prompt)
                print("  (Type to search or select number. Free text allowed.)")
                for idx, option in enumerate(datalist_options, 1):
                    print(f"  {idx}. {option}")
                
                user_input = input("  " if prompt else "").strip()
                
                # Check if user entered a number (selecting from list)
                if user_input.isdigit():
                    option_num = int(user_input)
                    if 1 <= option_num <= len(datalist_options):
                        return datalist_options[option_num - 1]
                
                # Otherwise return what they typed (free text)
                return user_input
            
            # Single-line input (all other types without datalist)
            # Extract prefix/suffix for input groups (Terminal-first pattern)
            # Helper to convert prefix/suffix values to strings intelligently
            def _format_affix(value):
                """Format prefix/suffix values, handling numbers intelligently."""
                if not value and value != 0:  # Allow 0/0.0 to pass through
                    return ''
                if isinstance(value, str):
                    return value
                if isinstance(value, bool):
                    return str(value)
                if isinstance(value, (int, float)):
                    # For decimals like 0.0, format with 2 decimal places
                    if isinstance(value, float) and 0 <= abs(value) < 1:
                        return f"{value:.2f}".lstrip('0') or '0'  # .00 or .50
                    return str(value)
                return str(value)
            
            prefix = _format_affix(kwargs.get('prefix'))
            suffix = _format_affix(kwargs.get('suffix'))
            
            # Terminal-First: Generate prompt from placeholder if no prompt provided
            # This ensures users know what they're entering (e.g., in grouped inputs)
            if not prompt and kwargs.get('placeholder'):
                prompt = str(kwargs.get('placeholder'))
            
            # Build enhanced prompt showing prefix/suffix context
            if prompt:
                terminal_prompt = prompt
                # Show prefix/suffix as visual context in prompt
                if prefix and suffix:
                    terminal_prompt = f"{prompt} [{prefix}...{suffix}]: "
                elif prefix:
                    terminal_prompt = f"{prompt} [{prefix}...]: "
                elif suffix:
                    terminal_prompt = f"{prompt} [...{suffix}]: "
                else:
                    # Ensure space after prompt for better UX in Terminal
                    terminal_prompt = prompt if prompt.endswith(' ') else prompt + ' '
                
                user_input = input(terminal_prompt).strip()
            else:
                user_input = input().strip()
            
            # Concatenate prefix + user_input + suffix for final result
            result = f"{prefix}{user_input}{suffix}"
            return result

        # Bifrost mode - buffer read_string event and return empty string
        # The frontend will render the input and handle user interaction
        request_id = self._generate_request_id()
        request_event = {
            _KEY_EVENT: _EVENT_READ_STRING,  # Use read_string, not input_request
            _KEY_REQUEST_ID: request_id,
            _KEY_PROMPT: prompt,
            _KEY_TIMESTAMP: time.time(),
            **kwargs  # type, placeholder, required, default
        }
        
        # Buffer the input request (like zDialog does)
        if self.display and hasattr(self.display, 'buffer_event'):
            self.display.buffer_event(request_event)
        
        # Return empty string (wizard continues, frontend handles input)
        return ""

    def read_password(self, prompt: str = _DEFAULT_PROMPT) -> str:
        """Read password input - terminal (synchronous) or GUI (buffered event).
        
        Critical dual-mode method with different return types based on mode:
            - Terminal mode: Returns str directly (synchronous, masked with getpass)
            - Bifrost mode: Buffers input_request event, returns empty string (non-blocking)
        
        Args:
            prompt: Prompt text to display (default: empty string)
        
        Returns:
            str: 
                - Terminal mode: Actual masked password input
                - Bifrost mode: Empty string (input handled by frontend)
        
        Notes:
            - Terminal: Uses getpass.getpass() for masked input
            - Bifrost: Buffers input_request with masked=True flag
            - Always has terminal fallback if GUI request fails
            - Strips whitespace from Terminal input
        
        Example:
            result = primitives.read_password("Password:")
            # Terminal: Returns actual password string
            # Bifrost: Returns "" (input rendered on frontend)
        """
        # Terminal input (always available as fallback)
        if not self._is_gui_mode():
            if prompt:
                return getpass.getpass(prompt).strip()
            return getpass.getpass().strip()

        # Bifrost mode - buffer read_password event and return empty string
        request_id = self._generate_request_id()
        request_event = {
            _KEY_EVENT: _EVENT_READ_PASSWORD,  # Use read_password, not input_request
            _KEY_REQUEST_ID: request_id,
            _KEY_PROMPT: prompt,
            _KEY_TIMESTAMP: time.time(),
            'masked': True
        }
        
        # Buffer the input request (like zDialog does)
        if self.display and hasattr(self.display, 'buffer_event'):
            self.display.buffer_event(request_event)
        
        # Return empty string (wizard continues, frontend handles input)
        return ""

    def read_bool(self, prompt: str = _DEFAULT_PROMPT, **kwargs) -> Union[bool, str]:
        """Read boolean checkbox - terminal (synchronous) or GUI (buffered event).
        
        Critical dual-mode method for checkbox/toggle inputs:
            - Terminal mode: Returns bool directly (synchronous y/n prompt)
            - Bifrost mode: Buffers read_bool event, returns empty string (non-blocking)
        
        Args:
            prompt: Prompt text to display (default: empty string)
            **kwargs: Additional parameters for Bifrost mode (ignored in Terminal):
                - checked: Default checked state (True/False, default: False)
                - required: Whether checkbox is required (default: False)
                - label: Alternative to prompt for consistency
        
        Returns:
            Union[bool, str]: 
                - bool if in Terminal mode (actual user choice)
                - str if in Bifrost mode (empty string, checkbox rendered on frontend)
        
        Notes:
            - Terminal: Displays checkbox icon (☐/☑) + y/n prompt
            - Bifrost: Buffers read_bool event for frontend checkbox rendering
            - Terminal mode ignores 'checked' default (always starts unchecked in prompt)
            - Strips whitespace and accepts y/yes for True, everything else False
        
        Example:
            result = primitives.read_bool("Subscribe to newsletter?", checked=False)
            # Terminal: ☐ Subscribe to newsletter? (y/n): y → Returns True
            # Bifrost: Returns "" (checkbox rendered on frontend)
        """
        # Terminal input (always available as fallback)
        if not self._is_gui_mode():
            # Get checkbox state from kwargs (default False)
            checked = kwargs.get('checked', False)
            disabled = kwargs.get('disabled', False)
            checkbox_icon = "☑" if checked else "☐"
            
            # Handle disabled state - display only, no input
            if disabled:
                display_text = f"{checkbox_icon} {prompt} [DISABLED]" if prompt else f"{checkbox_icon} [DISABLED]"
                print(display_text)
                return checked
            
            # Build terminal prompt with default hint
            default_hint = " [Y]" if checked else " [N]"
            if prompt:
                terminal_prompt = f"{checkbox_icon} {prompt} (y/n){default_hint}: "
            else:
                terminal_prompt = f"{checkbox_icon} (y/n){default_hint}: "
            
            # Read input and convert to boolean
            response = input(terminal_prompt).strip().lower()
            
            # Empty input uses default (checked value)
            if not response:
                return checked
            
            return response in ['y', 'yes']

        # Bifrost mode - buffer read_bool event and return empty string
        # The frontend will render the checkbox and handle user interaction
        request_id = self._generate_request_id()
        
        # Support both 'prompt' and 'label' (label takes precedence for consistency)
        display_label = kwargs.get('label', prompt)
        
        request_event = {
            _KEY_EVENT: _EVENT_READ_BOOL,
            _KEY_REQUEST_ID: request_id,
            _KEY_PROMPT: display_label,
            _KEY_TIMESTAMP: time.time(),
            'checked': kwargs.get('checked', False),
            'required': kwargs.get('required', False)
        }
        
        # Buffer the checkbox request
        if self.display and hasattr(self.display, 'buffer_event'):
            self.display.buffer_event(request_event)
        
        # Return empty string (wizard continues, frontend handles checkbox)
        return ""

    def read_range(self, prompt: str = _DEFAULT_PROMPT, **kwargs) -> Union[int, float, str]:
        """Read numeric range slider - terminal (interactive) or GUI (buffered event).
        
        Interactive range slider with real-time visual feedback:
            - Terminal mode: Renders visual slider with keyboard controls
            - Bifrost mode: Buffers read_range event, returns empty string (non-blocking)
        
        Args:
            prompt: Label text to display (default: empty string)
            **kwargs: Range configuration:
                - min: Minimum value (default: 0)
                - max: Maximum value (default: 100)
                - step: Increment step (default: 1)
                - value: Initial/default value (default: midpoint)
                - disabled: Whether slider is disabled (default: False)
        
        Returns:
            Union[int, float, str]: 
                - int/float if in Terminal mode (actual user selection)
                - str if in Bifrost mode (empty string, slider rendered on frontend)
        
        Terminal Controls:
            - Arrow keys (←/→): Decrease/increase value by step
            - +/- keys: Alternative increment/decrement
            - Enter: Confirm selection
            - ESC: Cancel (returns default value)
        
        Visual Example:
            Volume: [====●-----]  50/100
            (Use ← → or +/- to adjust, Enter to confirm)
        
        Notes:
            - Uses carriage return for in-place updates (modern terminals)
            - Fallback to newlines for Terminal.app
            - Validates min/max boundaries
            - Handles step increments properly
            - Returns int if step is whole number, float otherwise
        
        Example:
            volume = primitives.read_range("Volume", min=0, max=100, step=5, value=50)
            # Terminal: Interactive slider → Returns 75 (int)
            # Bifrost: Returns "" (slider rendered on frontend)
        """
        # Extract parameters with defaults
        min_val = kwargs.get('min', 0)
        max_val = kwargs.get('max', 100)
        step = kwargs.get('step', 1)
        value = kwargs.get('value', (min_val + max_val) / 2)
        disabled = kwargs.get('disabled', False)
        
        # Validate and normalize value
        value = max(min_val, min(max_val, value))
        
        # Determine return type (int if step is whole number, else float)
        is_integer = step == int(step)
        
        # Terminal input (interactive slider)
        if not self._is_gui_mode():
            import sys
            import tty
            import termios
            
            # Handle disabled state - display only, no interaction
            if disabled:
                display_text = f"{prompt}: {value} [DISABLED]" if prompt else f"{value} [DISABLED]"
                print(display_text)
                return int(value) if is_integer else value
            
            # Helper function to render slider visual
            def render_slider(current_val):
                # Calculate percentage for visual bar
                percentage = (current_val - min_val) / (max_val - min_val) if max_val > min_val else 0
                bar_width = 20
                filled = int(percentage * bar_width)
                bar = "=" * filled + "●" + "-" * (bar_width - filled - 1)
                
                # Format value display
                val_display = int(current_val) if is_integer else f"{current_val:.2f}"
                max_display = int(max_val) if is_integer else f"{max_val:.2f}"
                
                # Build display line
                label = f"{prompt}: " if prompt else ""
                return f"{label}[{bar}]  {val_display}/{max_display}"
            
            # Save terminal settings for restoration
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Set raw mode for immediate key capture
                tty.setraw(fd)
                
                current_value = value
                
                # Print instructions using zOS primitives
                self.line("(Use ← → or +/- to adjust, Enter to confirm)")
                
                # Initial render of slider using zOS primitives
                self.raw(f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{render_slider(current_value)}", flush=True)
                
                # Keyboard input loop
                while True:
                    # Read single character
                    char = sys.stdin.read(1)
                    
                    # Handle Ctrl+C (trigger graceful shutdown)
                    if char == '\x03':  # Ctrl+C
                        # Clean up display
                        self.raw(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}{_ANSI_CLEAR_LINE}\n", flush=True)
                        # Restore terminal first
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        # Send SIGINT to ourselves to trigger zOS graceful shutdown handler
                        os.kill(os.getpid(), signal.SIGINT)
                        # Should not reach here, but return default as fallback
                        return int(value) if is_integer else value
                    
                    # Handle Enter key (confirm)
                    if char == '\r' or char == '\n':
                        break
                    
                    # Handle ESC key (cancel - return default)
                    if char == '\x1b':
                        # Check if it's an arrow key sequence
                        next_chars = sys.stdin.read(2)
                        if next_chars == '[C':  # Right arrow
                            current_value = min(max_val, current_value + step)
                        elif next_chars == '[D':  # Left arrow
                            current_value = max(min_val, current_value - step)
                        else:
                            # ESC without arrow - cancel
                            current_value = value
                            break
                    
                    # Handle +/- keys
                    elif char == '+' or char == '=':
                        current_value = min(max_val, current_value + step)
                    elif char == '-' or char == '_':
                        current_value = max(min_val, current_value - step)
                    else:
                        # Ignore other keys
                        continue
                    
                    # Re-render slider using zOS primitives (in-place update)
                    self.raw(f"{_ANSI_CARRIAGE_RETURN}{_ANSI_CLEAR_LINE}{render_slider(current_value)}", flush=True)
                
                # Move to new line after slider - carriage return first, then newline
                self.raw("\r\n")  # Return to column 0, then newline
                
                # Return value (let zDispatch continue)
                return int(current_value) if is_integer else current_value
            
            finally:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        # Bifrost mode - buffer read_range event and return empty string
        request_id = self._generate_request_id()
        
        # Support both 'prompt' and 'label' (label takes precedence)
        display_label = kwargs.get('label', prompt)
        
        request_event = {
            _KEY_EVENT: _EVENT_READ_RANGE,
            _KEY_REQUEST_ID: request_id,
            _KEY_PROMPT: display_label,
            _KEY_TIMESTAMP: time.time(),
            'min': min_val,
            'max': max_val,
            'step': step,
            'value': value,
            'disabled': disabled
        }
        
        # Buffer the range request
        if self.display and hasattr(self.display, 'buffer_event'):
            self.display.buffer_event(request_event)
        
        # Return empty string (wizard continues, frontend handles slider)
        return ""

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
