# zCLI/subsystems/zComm/zComm_modules/bifrost/bridge_modules/events/bridge_event_client.py
"""
Client Event Handlers for zBifrost WebSocket Bridge.

This module provides event handlers for client-side interactions with the
zBifrost WebSocket bridge, enabling real-time bidirectional communication
between web frontends and the zCLI backend.

Features:
    - Input Response Routing: Routes user input from web clients to zDisplay.zPrimitives
    - Connection Info Delivery: Sends server metadata and authentication context to clients
    - User Context Awareness: Validates and logs authentication context for all events
    - Error Handling: Comprehensive exception handling for WebSocket and zCLI operations
    - Security: Integrates with three-tier authentication (zSession, application, dual)

Architecture:
    ClientEvents acts as a bridge between WebSocket events and zCLI subsystems,
    particularly zDisplay. It ensures that client-side events (input responses,
    info requests) are properly validated, authenticated, and routed to the
    appropriate zCLI handlers.

Security Model:
    All events extract and log user context (user_id, app_name, role, auth_context)
    to ensure proper audit trails and context-aware routing. While currently
    non-blocking (events are logged but not rejected), this provides the foundation
    for future authorization rules.

Integration:
    - zDisplay.zPrimitives: For input response routing
    - bridge_connection.py: For connection metadata
    - bridge_auth.py: For user context extraction
    - zSession/zAuth: For three-tier authentication context

Example:
    ```python
    # Initialize with auth_manager for user context
    client_events = ClientEvents(bifrost, auth_manager=auth_manager)
    
    # Handle input response from web client
    await client_events.handle_input_response(ws, {
        "requestId": "req-123",
        "value": "user input"
    })
    
    # Send connection info to client
    await client_events.handle_connection_info(ws, {})
    ```

Module Structure:
    - Constants: Event keys, message keys, log prefixes, error messages
    - ClientEvents class: Main event handler with security awareness
    - _extract_user_context: Extracts authentication context from WebSocket
"""

from zOS import json, Dict, Any, Optional
from .base_event_handler import BaseEventHandler

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Data Keys (incoming event data)
_KEY_REQUEST_ID = "requestId"
_KEY_VALUE = "value"

# Event Names
_EVENT_CONNECTION_INFO = "connection_info"

# Message Keys (outgoing messages)
_MSG_KEY_EVENT = "event"
_MSG_KEY_DATA = "data"

# Log Prefixes
_LOG_PREFIX = "[ClientEvents]"
_LOG_PREFIX_INPUT = "[ClientEvents:Input]"
_LOG_PREFIX_CONNECTION = "[ClientEvents:Connection]"

# Error Messages
_ERR_NO_REQUEST_ID = "Missing requestId in input response"
_ERR_NO_ZCLI = "zCLI instance not available"
_ERR_NO_DISPLAY = "zDisplay subsystem not available"
_ERR_NO_PRIMITIVES = "zDisplay.zPrimitives not available"
_ERR_SEND_FAILED = "Failed to send connection info"
_ERR_ROUTE_FAILED = "Failed to route input response"

# Note: User Context Keys and Default Values now inherited from BaseEventHandler.
# Module-level constants kept for convenience (match base class values exactly).
from .base_event_handler import (
    _CONTEXT_KEY_USER_ID, _CONTEXT_KEY_APP_NAME, _CONTEXT_KEY_ROLE, _CONTEXT_KEY_AUTH_CONTEXT,
    _DEFAULT_USER_ID, _DEFAULT_APP_NAME, _DEFAULT_ROLE, _DEFAULT_AUTH_CONTEXT
)


# ═══════════════════════════════════════════════════════════
# ClientEvents Class
# ═══════════════════════════════════════════════════════════

class ClientEvents(BaseEventHandler):
    """
    Handles client-side events for the zBifrost WebSocket bridge.
    
    This class manages input responses and connection information delivery,
    with full integration into the three-tier authentication system and
    comprehensive error handling for production-grade reliability.
    
    Features:
        - Input response routing to zDisplay.zPrimitives
        - Connection info delivery with server metadata
        - User context extraction and logging
        - Comprehensive error handling
        - Security-aware event processing
    
    Attributes:
        bifrost: zBifrost instance (provides logger, zcli, connection_info)
        logger: Logger instance from bifrost
        zcli: zCLI instance from bifrost (for zDisplay access)
        auth: AuthenticationManager instance for user context extraction
    
    Security:
        All events extract and log user context (user_id, app_name, role,
        auth_context) to provide audit trails and enable future authorization.
        Currently non-blocking, but foundation for access control.
    """
    
    def __init__(self, bifrost, auth_manager: Optional[Any] = None) -> None:
        """
        Initialize client events handler with authentication awareness.
        
        Args:
            bifrost: zBifrost instance providing logger, zcli, connection_info
            auth_manager: Optional AuthenticationManager for user context extraction
        
        Example:
            ```python
            client_events = ClientEvents(bifrost, auth_manager=auth_manager)
            ```
        """
        super().__init__(bifrost, auth_manager)
        self.zcli = bifrost.zcli
    
    async def handle_input_response(self, ws, data: Dict[str, Any]) -> None:
        """
        Route input response from web client to zDisplay.zPrimitives.
        
        Extracts user context, validates input data, and routes the response
        to the appropriate zCLI display handler. Includes comprehensive error
        handling and logging for debugging and security auditing.
        
        Args:
            ws: WebSocket connection (used for user context extraction)
            data: Event data containing:
                - requestId (str): Unique identifier for the input request
                - value (Any): User's input value
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Validate requestId is present
            3. Check zCLI and zDisplay availability
            4. Route to zPrimitives.handle_input_response()
            5. Log success or errors
        
        Security:
            Logs user context (user_id, app_name, role, auth_context) for
            audit trails. Future enhancement: Add authorization checks.
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await client_events.handle_input_response(ws, {
                "requestId": "req-123",
                "value": "John Doe"
            })
            ```
        """
        self.logger.info(f"{_LOG_PREFIX_INPUT} 🔵 handle_input_response CALLED! Data: {data}")
        
        # Extract user context for logging and future authorization
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        self.logger.debug(
            f"{_LOG_PREFIX_INPUT} User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context}"
        )
        
        # Validate input data
        request_id = data.get(_KEY_REQUEST_ID)
        if not request_id:
            self.logger.warning(f"{_LOG_PREFIX_INPUT} {_ERR_NO_REQUEST_ID}")
            return
        
        value = data.get(_KEY_VALUE)
        
        # Validate zCLI availability
        if not self.zcli:
            self.logger.warning(f"{_LOG_PREFIX_INPUT} {_ERR_NO_ZCLI}")
            return
        
        if not hasattr(self.zcli, 'display'):
            self.logger.warning(f"{_LOG_PREFIX_INPUT} {_ERR_NO_DISPLAY}")
            return
        
        if not hasattr(self.zcli.display, 'zPrimitives'):
            self.logger.warning(f"{_LOG_PREFIX_INPUT} {_ERR_NO_PRIMITIVES}")
            return
        
        # Check if this is a sandbox input (from zTerminal execute_code)
        if hasattr(self, '_pending_inputs') and request_id in self._pending_inputs:
            input_event, input_value = self._pending_inputs[request_id]
            input_value[0] = value
            input_event.set()  # Signal the waiting thread
            self.logger.debug(f"{_LOG_PREFIX_INPUT} Sandbox input received: {request_id} | Value: {value}")
            return
        
        # Route input response to zDisplay
        try:
            self.zcli.display.zPrimitives.handle_input_response(request_id, value)
            self.logger.debug(
                f"{_LOG_PREFIX_INPUT} Routed: {request_id} | "
                f"User: {user_id} | Value: {value}"
            )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_INPUT} {_ERR_ROUTE_FAILED}: {request_id} | "
                f"Error: {str(e)}"
            )
    
    async def handle_execute_code(self, ws, data: Dict[str, Any]) -> None:
        """
        Execute code in sandboxed environment and return result.
        
        Handles zTerminal code execution requests from Bifrost frontend.
        Executes Python code in a restricted sandbox environment and returns
        the captured output or error message.
        
        Args:
            ws: WebSocket connection (used for sending response)
            data: Event data containing:
                - requestId (str): Unique identifier for correlation
                - language (str): Code language (python, zolo, bash)
                - content (str): Code to execute
        
        Security:
            - Python: Sandboxed with restricted builtins (no file/network/system access)
            - Bash: Completely blocked (returns error)
            - Zolo: Safe (declarative UI only)
        
        Response Format:
            {
                "event": "execute_code_response",
                "requestId": "...",
                "success": true/false,
                "output": "..." or "error": "..."
            }
        """
        import io
        import contextlib
        
        request_id = data.get(_KEY_REQUEST_ID)
        content = data.get('content', '')
        
        # Extract language from code fence syntax (```language ... ```)
        # Handles nested code fences: if content has nested ```, closing will have 6+ backticks
        # Example: ```zolo\n  content: ```python\n    print("hi")``````
        import re
        
        # Match opening fence and handle nested closings (3, 6, 9+ backticks)
        fence_match = re.match(r'^```(\w+)?\s*\n?(.*?)(`{3,})\s*$', content, re.DOTALL)
        if fence_match:
            language = (fence_match.group(1) or 'text').lower()
            inner_content = fence_match.group(2)
            closing_backticks = fence_match.group(3)
            
            # If closing has more than 3 backticks, there's nested content
            # Strip one level of fence (3 backticks) from the inner content's end
            if len(closing_backticks) > 3:
                # Nested fences - the inner content ends with the remaining backticks
                remaining_backticks = '`' * (len(closing_backticks) - 3)
                inner_content = inner_content.rstrip() + remaining_backticks
            
            content = inner_content.strip()
        else:
            # No code fence - default to text (no execution)
            language = 'text'
        
        self.logger.info(f"[ClientEvents] 🖥️ execute_code: lang={language}, requestId={request_id}")
        
        # SANDBOX MODE - Restricted execution with zOS access
        # Whitelist of allowed imports for zTerminal
        ALLOWED_IMPORTS = {'zOS', 'math', 'random', 'datetime', 'json', 're', 'collections', 'itertools', 'functools'}
        
        def safe_import(name, globs=None, locs=None, fromlist=(), level=0):
            """Controlled import that only allows whitelisted modules"""
            if name not in ALLOWED_IMPORTS:
                raise ImportError(f"Import of '{name}' is not allowed in sandbox. Allowed: {', '.join(sorted(ALLOWED_IMPORTS))}")
            return __builtins__['__import__'](name, globs, locs, fromlist, level)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Interactive Input Support
        # ═══════════════════════════════════════════════════════════════════════════
        # Custom input() that sends WebSocket request and waits for response
        import threading
        import asyncio
        
        input_event = threading.Event()
        input_value = [None]  # Use list to allow mutation in nested function
        input_prompt = [None]
        event_loop = asyncio.get_running_loop()  # Capture current loop for thread safety
        
        # Password-like prompt patterns for auto-detection
        PASSWORD_PATTERNS = ['password', 'passwd', 'secret', 'token', 'api_key', 'apikey', 'api key', 'credential', 'pin']
        
        def sandbox_input(prompt="", is_password=None):
            """Interactive input that requests from Bifrost frontend"""
            self.logger.info(f"[ClientEvents] 🔵 sandbox_input() called with prompt: {prompt}")
            input_prompt[0] = prompt
            input_event.clear()
            
            # Auto-detect password prompts if not explicitly set
            if is_password is None:
                prompt_lower = prompt.lower()
                is_password = any(pattern in prompt_lower for pattern in PASSWORD_PATTERNS)
            
            # Send request_input event to frontend (from background thread)
            self.logger.info(f"[ClientEvents] 🔵 Sending request_input event to frontend... (isPassword={is_password})")
            try:
                future = asyncio.run_coroutine_threadsafe(
                    ws.send(json.dumps({
                        'event': 'request_input',
                        'requestId': request_id,
                        'prompt': prompt,
                        'isPassword': is_password
                    })),
                    event_loop
                )
                # Wait for send to complete (with timeout)
                future.result(timeout=5)
                self.logger.info(f"[ClientEvents] ✅ request_input event sent successfully")
            except Exception as e:
                self.logger.error(f"[ClientEvents] ❌ Failed to send request_input: {e}")
                raise RuntimeError(f"Failed to send input request: {e}")
            
            # Wait for input response (with timeout)
            self.logger.info(f"[ClientEvents] 🔵 Waiting for input_response from frontend...")
            if input_event.wait(timeout=60):  # 60 second timeout for user input
                self.logger.info(f"[ClientEvents] ✅ Input received: {input_value[0]}")
                return input_value[0]
            else:
                self.logger.error(f"[ClientEvents] ❌ Input timeout - no response received")
                raise TimeoutError("Input timeout - no response received")
        
        # Store input handler for this request
        if not hasattr(self, '_pending_inputs'):
            self._pending_inputs = {}
        self._pending_inputs[request_id] = (input_event, input_value)
        
        SAFE_BUILTINS = {
            # Import (controlled whitelist)
            '__import__': safe_import,
            # Output
            'print': print,
            # Input (interactive via WebSocket)
            'input': sandbox_input,
            # Types & conversions
            'int': int, 'float': float, 'str': str, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'bytes': bytes, 'bytearray': bytearray,
            # Iteration & sequences
            'range': range, 'enumerate': enumerate, 'zip': zip,
            'map': map, 'filter': filter, 'reversed': reversed, 'sorted': sorted,
            'len': len, 'min': min, 'max': max, 'sum': sum,
            'all': all, 'any': any,
            # Math
            'abs': abs, 'round': round, 'pow': pow, 'divmod': divmod,
            # String
            'chr': chr, 'ord': ord, 'repr': repr, 'format': format,
            # Object inspection (safe subset)
            'type': type, 'isinstance': isinstance, 'issubclass': issubclass,
            'hasattr': hasattr, 'getattr': getattr,
            'callable': callable, 'id': id, 'hash': hash,
            # Exceptions (for try/except)
            'Exception': Exception, 'TypeError': TypeError, 'ValueError': ValueError,
            'KeyError': KeyError, 'IndexError': IndexError, 'AttributeError': AttributeError,
            'RuntimeError': RuntimeError, 'StopIteration': StopIteration,
            'ZeroDivisionError': ZeroDivisionError, 'ImportError': ImportError,
            'TimeoutError': TimeoutError,
            # Constants
            'True': True, 'False': False, 'None': None,
        }
        
        # Use the existing running zOS instance (self.zcli)
        # This avoids signal handler issues since we're not creating a new instance
        z_instance = self.zcli  # The running zOS instance
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Sandbox Display Wrapper
        # ═══════════════════════════════════════════════════════════════════════════
        # The sandbox always runs in Terminal mode (set in run_code() below).
        # This wrapper only overrides input methods to use WebSocket for interactivity.
        class SandboxDisplayWrapper:
            """Display wrapper for sandbox execution.
            
            - Terminal mode is set by run_code() for proper output capture
            - Input methods redirect to WebSocket for interactive prompts
            """
            def __init__(self, original_display, blocking_input_fn):
                self._original = original_display
                self._blocking_input = blocking_input_fn
            
            def read_string(self, prompt="", **kwargs):
                """Interactive string input via WebSocket"""
                return self._blocking_input(prompt, is_password=False)
            
            def read_password(self, prompt="", **kwargs):
                """Interactive password input via WebSocket (masked)"""
                return self._blocking_input(prompt, is_password=True)
            
            def __getattr__(self, name):
                """Delegate all other methods to original display"""
                return getattr(self._original, name)
        
        class SandboxZWrapper:
            """Wrapper for z instance with overridden display.read_string"""
            def __init__(self, original_z, blocking_input_fn):
                self._original = original_z
                self._display_wrapper = SandboxDisplayWrapper(original_z.display, blocking_input_fn)
            
            @property
            def display(self):
                return self._display_wrapper
            
            def __getattr__(self, name):
                """Delegate all other attributes to original z"""
                return getattr(self._original, name)
        
        # Create wrapped z instance with blocking input
        z_wrapped = SandboxZWrapper(z_instance, sandbox_input)
        
        response = {
            'event': 'execute_code_response',
            'requestId': request_id
        }
        
        try:
            if language == 'python':
                # Capture stdout - SANDBOXED execution with zOS access
                output_buffer = io.StringIO()
                
                # Build execution globals with wrapped zOS instance (blocking input)
                exec_globals = {"__builtins__": SAFE_BUILTINS}
                exec_globals['z'] = z_wrapped   # Wrapped instance with blocking read_string
                
                # Run in thread to allow blocking input() calls
                exec_exception = [None]
                
                def run_code():
                    # ═══════════════════════════════════════════════════════════════
                    # Virtual zTerminal Environment
                    # ═══════════════════════════════════════════════════════════════
                    # The sandbox always runs in Terminal mode, like a built-in zSpark:
                    #   zMode: Terminal
                    #   logger: PROD
                    # This ensures display output goes to stdout for capture.
                    original_mode = z_instance.display.mode
                    z_instance.display.mode = "Terminal"
                    try:
                        with contextlib.redirect_stdout(output_buffer):
                            exec(content, exec_globals, {})
                    except Exception as e:
                        exec_exception[0] = e
                    finally:
                        # Restore original mode after execution
                        z_instance.display.mode = original_mode
                
                exec_thread = threading.Thread(target=run_code)
                exec_thread.start()
                
                # Use async-friendly polling instead of blocking join()
                # This allows the event loop to process incoming messages (input_response)
                start_time = asyncio.get_event_loop().time()
                timeout_seconds = 60
                while exec_thread.is_alive():
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= timeout_seconds:
                        break
                    # Yield to event loop to process incoming messages
                    await asyncio.sleep(0.1)
                
                # Clean up pending input handler
                if request_id in self._pending_inputs:
                    del self._pending_inputs[request_id]
                
                if exec_thread.is_alive():
                    response['success'] = False
                    response['error'] = "Execution timeout"
                elif exec_exception[0]:
                    e = exec_exception[0]
                    if isinstance(e, NameError):
                        response['success'] = False
                        response['error'] = f"Sandbox Error: {e} (blocked for security)"
                    elif isinstance(e, SyntaxError):
                        response['success'] = False
                        response['error'] = f"Syntax Error: {e}"
                    else:
                        response['success'] = False
                        response['error'] = f"Execution Error: {e}"
                else:
                    output = output_buffer.getvalue()
                    response['success'] = True
                    response['output'] = output if output else ''
                    
            elif language == 'bash':
                # Bash is BLOCKED in sandbox mode
                response['success'] = False
                response['error'] = "Bash execution is blocked in sandbox mode for security"
                
            elif language == 'zolo':
                # ═══════════════════════════════════════════════════════════════
                # ZOLO EXECUTION: Spawn new zOS instance like zTest.py
                # ═══════════════════════════════════════════════════════════════
                # Simple: write swap file to zSpace, run with zVaFolder: "@", zBlock: "zVaF"
                import os
                import re as re_module
                
                try:
                    # Get title and sanitize for filename
                    terminal_title = data.get('title', 'zTerminal_Swap')
                    sanitized_title = re_module.sub(r'[^a-zA-Z0-9]', '_', terminal_title)
                    sanitized_title = re_module.sub(r'_+', '_', sanitized_title).strip('_') or 'zTerminal_Swap'
                    
                    # Swap file goes directly in zSpace (same as zTest.py location)
                    zspace = z_instance.session.get('zSpace', os.getcwd())
                    swap_filename = f"zUI.{sanitized_title}.zolo"
                    swap_path = os.path.join(zspace, swap_filename)
                    
                    # Write content to swap file
                    with open(swap_path, 'w') as swap_file:
                        swap_file.write(content)
                    
                    try:
                        from zOS import zOS as zOS_Class
                        
                        zSpark = {
                            "deployment": "Production",
                            "title": f"zTerminal: {terminal_title}",
                            "logger": "PROD",
                            "zMode": "Terminal",
                            "zSpace": zspace,
                            "zVaFolder": "@",
                            "zVaFile": f"zUI.{sanitized_title}",
                            "zBlock": "zVaF",
                        }
                        
                        # Capture stdout from new zOS instance
                        output_buffer = io.StringIO()
                        
                        with contextlib.redirect_stdout(output_buffer):
                            z_temp = zOS_Class(zSpark)
                            z_temp.run()
                        
                        response['output'] = output_buffer.getvalue()
                        response['success'] = True
                        
                    finally:
                        # Clean up swap file
                        if os.path.exists(swap_path):
                            os.unlink(swap_path)
                            
                except Exception as e:
                    import traceback
                    self.logger.error(f"[ClientEvents] Zolo execution error: {traceback.format_exc()}")
                    response['success'] = False
                    response['error'] = f"Zolo error: {e}"
                
            else:
                response['success'] = False
                response['error'] = f"Unsupported language: {language}"
                
        except Exception as e:
            self.logger.error(f"[ClientEvents] execute_code error: {e}")
            response['success'] = False
            response['error'] = str(e)
        
        # Send response back to frontend
        await ws.send(json.dumps(response))
        self.logger.info(f"[ClientEvents] ✅ execute_code response sent: success={response.get('success')}")
    
    async def handle_connection_info(self, ws, data: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
        """
        Send connection info to client with server metadata and context.
        
        Retrieves server connection information (models, endpoints, server status)
        and sends it to the requesting client. Usually triggered automatically
        on connection, but can be requested manually by clients.
        
        Args:
            ws: WebSocket connection (used for sending and user context)
            data: Event data (currently unused, reserved for future filtering)
        
        Process:
            1. Extract and log user context (auth-aware)
            2. Retrieve connection info from bridge_connection
            3. Send JSON message with event and data
            4. Log success or errors
        
        Security:
            Logs user context for audit trails. Future enhancement: Filter
            connection info based on user role/permissions.
        
        Message Format:
            ```json
            {
                "event": "connection_info",
                "data": {
                    "server": "zBifrost",
                    "version": "1.5.4",
                    "models": [...],
                    "endpoints": [...]
                }
            }
            ```
        
        Raises:
            Does not raise - logs errors instead for resilience
        
        Example:
            ```python
            await client_events.handle_connection_info(ws, {})
            ```
        """
        # Extract user context for logging and future authorization
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        auth_context = user_context.get(_CONTEXT_KEY_AUTH_CONTEXT, _DEFAULT_AUTH_CONTEXT)
        
        self.logger.debug(
            f"{_LOG_PREFIX_CONNECTION} Request | User: {user_id} | App: {app_name} | "
            f"Role: {role} | Context: {auth_context}"
        )
        
        try:
            # Retrieve connection info from bridge_connection
            connection_info = self.bifrost.connection_info.get_info()
            
            # Send to client
            await ws.send(json.dumps({
                _MSG_KEY_EVENT: _EVENT_CONNECTION_INFO,
                _MSG_KEY_DATA: connection_info
            }))
            
            self.logger.debug(
                f"{_LOG_PREFIX_CONNECTION} Sent to {user_id} | "
                f"App: {app_name} | Models: {len(connection_info.get('models', []))}"
            )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_CONNECTION} {_ERR_SEND_FAILED} | "
                f"User: {user_id} | Error: {str(e)}"
            )
    
    # Note: _extract_user_context() method removed - now inherited from BaseEventHandler
    
    async def handle_button_action(self, ws, data: Dict[str, Any]) -> None:
        """
        Handle button action execution from Bifrost (for buttons with plugin actions).
        
        When a button in a zWizard has an action parameter (e.g., "&plugin.func(zHat[0])"),
        the frontend collects wizard input values and sends them here for execution.
        
        Args:
            ws: WebSocket connection (used for user context extraction)
            data: Event data containing:
                - requestId (str): Unique identifier for the button
                - action (str): Plugin action string (e.g., "&plugin.func(zHat[0])")
                - collected_values (list): Collected wizard input values
        
        Process:
            1. Extract user context and validate data
            2. Substitute zHat[N] placeholders with collected values
            3. Execute plugin action via zParser
            4. Log result
        
        Example:
            ```python
            await client_events.handle_button_action(ws, {
                "requestId": "req-button-123",
                "action": "&input_group_demo.show_search_result(zHat[0])",
                "collected_values": ["laptop"]
            })
            ```
        """
        self.logger.info(f"{_LOG_PREFIX_INPUT} 🎯 handle_button_action CALLED! Data: {data}")
        
        # Extract user context
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        role = user_context.get(_CONTEXT_KEY_ROLE, _DEFAULT_ROLE)
        
        self.logger.debug(
            f"{_LOG_PREFIX_INPUT} User: {user_id} | App: {app_name} | Role: {role}"
        )
        
        # Validate data
        request_id = data.get('requestId')
        action = data.get('action')
        collected_values = data.get('collected_values', [])
        
        if not action or not action.startswith('&'):
            self.logger.warning(f"{_LOG_PREFIX_INPUT} Invalid or missing action: {action}")
            return
        
        # Validate zCLI availability
        if not self.zcli:
            self.logger.warning(f"{_LOG_PREFIX_INPUT} {_ERR_NO_ZCLI}")
            return
        
        # Substitute zHat[N] placeholders with collected values
        import re
        substituted_action = action
        
        # Find all zHat[N] references and replace with collected values
        def replace_zhat(match):
            index = int(match.group(1))
            if 0 <= index < len(collected_values):
                # Quote the value for safe execution
                return f"'{collected_values[index]}'"
            return match.group(0)  # Keep original if index out of range
        
        substituted_action = re.sub(r'zHat\[(\d+)\]', replace_zhat, substituted_action)
        
        self.logger.info(
            f"{_LOG_PREFIX_INPUT} Substituted action: {action} → {substituted_action}"
        )
        
        # Execute plugin action
        try:
            if hasattr(self.zcli, 'zparser') and hasattr(self.zcli.zparser, 'resolve_plugin_invocation'):
                self.logger.info(f"{_LOG_PREFIX_INPUT} Executing plugin: {substituted_action}")
                result = self.zcli.zparser.resolve_plugin_invocation(substituted_action, self.zcli)
                self.logger.info(
                    f"{_LOG_PREFIX_INPUT} ✅ Plugin executed successfully | "
                    f"User: {user_id} | Result: {result}"
                )
            else:
                self.logger.warning(
                    f"{_LOG_PREFIX_INPUT} zParser not available - cannot execute action"
                )
        except Exception as e:
            self.logger.error(
                f"{_LOG_PREFIX_INPUT} ❌ Plugin execution failed: {e} | "
                f"User: {user_id} | Action: {substituted_action}",
                exc_info=True
            )
    
    async def handle_page_unload(self, ws, data: Dict[str, Any]) -> None:
        """
        Handle page unload notification from frontend (lifecycle cleanup).
        
        This handler is called when the frontend detects page navigation (e.g., browser
        back/forward button, or user clicking a different nav item). It cleans up any
        state associated with the WebSocket connection, such as paused generators.
        
        Args:
            ws: WebSocket connection
            data: Event data with:
                - reason (str): Reason for unload (e.g., "navigation")
                - timestamp (int): Client timestamp
        
        Process:
            1. Log the page unload event with user context
            2. Clean up any paused generators (via bridge's message_handler)
            3. No response needed (page is already navigating away)
        
        Security:
            Logs user context for audit trails. Non-critical operation, failures are logged
            but don't block cleanup.
        
        Example:
            ```python
            await client_events.handle_page_unload(ws, {
                "reason": "navigation",
                "timestamp": 1765985548958
            })
            ```
        """
        # Extract user context for logging
        user_context = self._extract_user_context(ws)
        user_id = user_context.get(_CONTEXT_KEY_USER_ID, _DEFAULT_USER_ID)
        app_name = user_context.get(_CONTEXT_KEY_APP_NAME, _DEFAULT_APP_NAME)
        
        reason = data.get('reason', 'unknown')
        ws_id = id(ws)
        
        self.logger.info(
            f"{_LOG_PREFIX} Page unload | User: {user_id} | App: {app_name} | "
            f"Reason: {reason} | ws={ws_id}"
        )
        
        # Clean up any paused generators for this connection
        if hasattr(self.bifrost, 'message_handler') and hasattr(self.bifrost.message_handler, '_paused_generators'):
            if ws_id in self.bifrost.message_handler._paused_generators:
                gen_state = self.bifrost.message_handler._paused_generators[ws_id]
                zBlock = gen_state.get('zBlock', 'unknown')
                self.logger.info(
                    f"{_LOG_PREFIX} Cleaned up paused generator for block: {zBlock} | "
                    f"User: {user_id} | ws={ws_id}"
                )
                del self.bifrost.message_handler._paused_generators[ws_id]
        
        # No response needed - page is already navigating away