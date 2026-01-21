# zCLI/subsystems/zComm/zComm_modules/bifrost/bridge_modules/bridge_messages.py

"""
Message Handler Module - WebSocket Message Routing and Dispatch.

This module provides comprehensive message routing for the Bifrost WebSocket bridge,
handling incoming client messages and dispatching them to appropriate handlers based
on event types, actions, and command patterns.

Architecture:
    - Route incoming WebSocket messages to specialized handlers
    - Support special actions (cache control, schema requests, discovery)
    - Cache-aware zDispatch command execution with user context isolation
    - Async/await patterns for non-blocking I/O
    - Integration with zDisplay input routing

Key Responsibilities:
    - Parse and validate incoming JSON messages
    - Route to special action handlers (schema, cache, discovery)
    - Execute zDispatch commands with cache support
    - Broadcast results to connected clients
    - Handle input responses from UI

Cache-Aware Dispatch:
    - Read operations are cached with user context isolation
    - Cache keys include: user_id, app_name, role, auth_context
    - Prevents cross-user and cross-application data leaks
    - TTL-based expiration with configurable timeouts

Supported Actions:
    - get_schema: Load model schema via zLoader
    - clear_cache: Clear all cached data
    - cache_stats: Get cache performance statistics
    - set_query_cache_ttl: Configure cache TTL
    - discover: Auto-discover available models
    - introspect: Introspect model structure
    - zDispatch commands: Execute via zKey/zHorizontal routing

Example:
    # Initialize with required dependencies
    handler = MessageHandler(
        logger, cache_manager, zcli, walker,
        connection_info_manager=conn_info,
        auth_manager=auth
    )
    
    # Handle incoming WebSocket message
    await handler.handle_message(ws, json_message, broadcast_func)
"""

from zOS import asyncio, json, Dict, Any, Optional, Callable, Awaitable, safe_json_dumps
from .bridge_auth import _CONTEXT_ZSESSION, _CONTEXT_APPLICATION, _CONTEXT_DUAL

# ═══════════════════════════════════════════════════════════
# Module Constants
# ═══════════════════════════════════════════════════════════

# Event Names
EVENT_INPUT_RESPONSE: str = "input_response"

# Action Names
ACTION_GET_SCHEMA: str = "get_schema"
ACTION_CLEAR_CACHE: str = "clear_cache"
ACTION_CACHE_STATS: str = "cache_stats"
ACTION_SET_TTL: str = "set_query_cache_ttl"
ACTION_DISCOVER: str = "discover"
ACTION_INTROSPECT: str = "introspect"
ACTION_READ: str = "read"

# Message Keys
MSG_KEY_EVENT: str = "event"
MSG_KEY_ACTION: str = "action"
MSG_KEY_MODEL: str = "model"
MSG_KEY_REQUEST_ID: str = "requestId"
MSG_KEY_VALUE: str = "value"
MSG_KEY_ZKEY: str = "zKey"
MSG_KEY_CMD: str = "cmd"
MSG_KEY_ZHORIZONTAL: str = "zHorizontal"
MSG_KEY_CACHE_TTL: str = "cache_ttl"
MSG_KEY_NO_CACHE: str = "no_cache"
MSG_KEY_TTL: str = "ttl"
MSG_KEY_RESULT: str = "result"
MSG_KEY_ERROR: str = "error"
MSG_KEY_CACHED: str = "_cached"
MSG_KEY_STATS: str = "stats"
MSG_KEY_MODELS: str = "models"

# Command Prefixes (for cacheable operation detection)
CMD_PREFIX_LIST: str = "^List"
CMD_PREFIX_GET: str = "^Get"
CMD_PREFIX_SEARCH: str = "^Search"

# Log Prefixes
LOG_PREFIX: str = "[MessageHandler]"
LOG_OK: str = "[OK]"
LOG_DISPATCH: str = "[DISPATCH]"
LOG_ERROR: str = "[ERROR]"

# Default Values
DEFAULT_CACHE_TTL: int = 60

# Loader Error Values
LOADER_ERROR_VALUE: str = "error"

# Response Messages
RESPONSE_CACHE_CLEARED: str = "Cache cleared"
RESPONSE_TTL_SET: str = "Query cache TTL set to {ttl}s"
RESPONSE_DISCOVERY_NOT_AVAILABLE: str = "Discovery not available"
RESPONSE_INTROSPECTION_NOT_AVAILABLE: str = "Introspection not available"
RESPONSE_MODEL_REQUIRED: str = "Model name required"
RESPONSE_SCHEMA_NOT_FOUND: str = "Schema not found: {model}"
RESPONSE_MODEL_NOT_FOUND: str = "Model '{model}' not found"


class MessageHandler:
    """
    Handles incoming WebSocket messages and routes them to appropriate handlers.
    
    This class serves as the central message dispatcher for the Bifrost bridge,
    routing messages based on event types and action names. It integrates with
    the cache manager for performance optimization and the authentication manager
    for secure user context isolation.
    
    Features:
        - Automatic JSON parsing with fallback to broadcast
        - Special action routing (cache, schema, discovery)
        - Cache-aware zDispatch command execution
        - User context extraction for multi-tenant isolation
        - Async/await patterns for non-blocking I/O
    
    Attributes:
        logger: Logger instance for diagnostics
        cache: CacheManager instance for query result caching
        zcli: zCLI instance for access to subsystems
        walker: Walker instance for data operations
        connection_info: ConnectionInfoManager for API discovery
        auth: AuthenticationManager for user context extraction
    """
    
    def __init__(
        self,
        logger: Any,
        cache_manager: Any,
        zcli: Any,
        walker: Any,
        connection_info_manager: Optional[Any] = None,
        auth_manager: Optional[Any] = None
    ) -> None:
        """
        Initialize message handler with required dependencies.
        
        Args:
            logger: Logger instance for diagnostics and error reporting
            cache_manager: CacheManager instance for query result caching
            zcli: zCLI instance for access to zDisplay, zDispatch, etc.
            walker: Walker instance for data operations and schema loading
            connection_info_manager: Optional ConnectionInfoManager for introspection
            auth_manager: Optional AuthenticationManager for user context extraction
        """
        self.logger = logger
        self.cache = cache_manager
        self.zcli = zcli
        self.walker = walker
        self.connection_info = connection_info_manager
        self.auth = auth_manager
        
        # Generator resumption: Store paused generators by WebSocket connection
        # Key: ws id, Value: {generator, block_dict, zBlock, breadcrumb_path, request_id, chunk_num}
        self._paused_generators = {}
    
    async def handle_message(
        self,
        ws: Any,
        message: str,
        broadcast_func: Callable[[str, Any], Awaitable[None]]
    ) -> bool:
        """
        Handle incoming WebSocket message and route to appropriate handler.
        
        This is the main entry point for all incoming messages. It attempts to
        parse the message as JSON, then routes it to special action handlers or
        the zDispatch command handler.
        
        Args:
            ws: WebSocket connection object
            message: Raw message string from client
            broadcast_func: Async function to broadcast messages to other clients
            
        Returns:
            bool: True if message was successfully handled, False otherwise
            
        Flow:
            1. Parse JSON (or fallback to broadcast)
            2. Check for special actions (cache, schema, discovery)
            3. Execute zDispatch commands (with cache support)
            4. Broadcast results to connected clients
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            # Fallback to simple broadcast if not JSON
            await broadcast_func(message, sender=ws)
            return True
        
        # Route to appropriate handler
        if await self._handle_special_actions(ws, data):
            return True
        
        # Handle zDispatch commands
        return await self._handle_dispatch(ws, data, broadcast_func)
    
    async def _handle_special_actions(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle special action messages (cache control, schema requests, etc.).
        
        Special actions are non-zDispatch messages that control the bridge itself,
        such as cache management, schema loading, and API discovery.
        
        Args:
            ws: WebSocket connection object
            data: Parsed message data dictionary
            
        Returns:
            bool: True if handled as special action, False to continue routing
        """
        # Get event field (supports both 'event' and 'action' for backward compatibility)
        event = self._get_event(data)
        
        # Input response routing
        if event == EVENT_INPUT_RESPONSE:
            return await self._handle_input_response(data)
        
        # Schema requests
        if event == ACTION_GET_SCHEMA:
            return await self._handle_schema_request(ws, data)
        
        # Cache control
        if event == ACTION_CLEAR_CACHE:
            return await self._handle_clear_cache(ws, data)
        
        if event == ACTION_CACHE_STATS:
            return await self._handle_cache_stats(ws, data)
        
        if event == ACTION_SET_TTL:
            return await self._handle_set_ttl(ws, data)
        
        # Auto-discovery API (v1.5.4+)
        if event == ACTION_DISCOVER:
            return await self._handle_discover(ws, data)
        
        if event == ACTION_INTROSPECT:
            return await self._handle_introspect(ws, data)
        
        # Walker execution (v1.5.8+)
        if event == "execute_walker" or event == "load_page":
            return await self._handle_walker_execution(ws, data)
        
        # Form submission (async form handling)
        if event == "form_submit":
            return await self._handle_form_submit(ws, data)
        
        # Page unload notification (lifecycle cleanup)
        if event == "page_unload":
            return await self._handle_page_unload(ws, data)
        
        return False
    
    async def _handle_input_response(self, data: Dict[str, Any]) -> bool:
        """
        Route input response to zDisplay for UI input handling.
        
        Args:
            data: Message data containing requestId and value
            
        Returns:
            bool: Always True (message handled)
        """
        request_id = data.get(MSG_KEY_REQUEST_ID)
        value = data.get(MSG_KEY_VALUE)
        
        if request_id and self.zcli and hasattr(self.zcli, 'display'):
            if hasattr(self.zcli.display.input, 'handle_input_response'):
                self.zcli.display.input.handle_input_response(request_id, value)
                self.logger.debug(
                    f"{LOG_PREFIX} {LOG_OK} Routed input response: {request_id}"
                )
        
        return True
    
    async def _handle_schema_request(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle schema request by loading via zLoader.
        
        Args:
            ws: WebSocket connection object
            data: Message data containing model name
            
        Returns:
            bool: True if request was processed (even if schema not found)
        """
        model = data.get(MSG_KEY_MODEL)
        if not model:
            return False
        
        # Load schema via zLoader (no redundant backend cache)
        def schema_loader(m: str) -> Optional[Dict[str, Any]]:
            if self.walker and hasattr(self.walker, 'loader'):
                schema = self.walker.loader.handle(m)
                return schema if schema != LOADER_ERROR_VALUE else None
            return None
        
        schema = self.cache.get_schema(model, loader_func=schema_loader)
        
        if schema:
            await ws.send(self._build_response(data, result=schema))
        else:
            await ws.send(self._build_response(data, error=RESPONSE_SCHEMA_NOT_FOUND.format(model=model)))
        
        return True
    
    async def _handle_clear_cache(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle cache clear request and return statistics.
        
        Args:
            ws: WebSocket connection object
            
        Returns:
            bool: Always True (request handled)
        """
        self.cache.clear_all()
        stats = self.cache.get_all_stats()
        await ws.send(self._build_response(data, result=RESPONSE_CACHE_CLEARED, stats=stats))
        return True
    
    async def _handle_cache_stats(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle cache statistics request.
        
        Args:
            ws: WebSocket connection object
            
        Returns:
            bool: Always True (request handled)
        """
        stats = self.cache.get_all_stats()
        await ws.send(self._build_response(data, result=stats))
        return True
    
    async def _handle_set_ttl(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle set TTL request to configure cache expiration.
        
        Args:
            ws: WebSocket connection object
            data: Message data containing ttl value
            
        Returns:
            bool: Always True (request handled)
        """
        ttl = data.get(MSG_KEY_TTL, DEFAULT_CACHE_TTL)
        self.cache.set_query_ttl(ttl)
        await ws.send(self._build_response(data, result=RESPONSE_TTL_SET.format(ttl=ttl)))
        return True
    
    async def _handle_discover(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle discover models request for API auto-discovery.
        
        Args:
            ws: WebSocket connection object
            
        Returns:
            bool: Always True (request handled)
        """
        if not self.connection_info:
            await ws.send(self._build_response(data, error=RESPONSE_DISCOVERY_NOT_AVAILABLE))
            return True
        
        # pylint: disable=protected-access
        # Reason: _discover_models is an internal API method intended for bridge use
        models = self.connection_info._discover_models()
        await ws.send(self._build_response(data, result={MSG_KEY_MODELS: models}))
        return True
    
    async def _handle_introspect(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle introspect model request for detailed model information.
        
        Args:
            ws: WebSocket connection object
            data: Message data containing model name
            
        Returns:
            bool: Always True (request handled)
        """
        model = data.get(MSG_KEY_MODEL)
        if not model:
            await ws.send(self._build_response(data, error=RESPONSE_MODEL_REQUIRED))
            return True
        
        if not self.connection_info:
            await ws.send(self._build_response(data, error=RESPONSE_INTROSPECTION_NOT_AVAILABLE))
            return True
        
        model_info = self.connection_info.introspect_model(model)
        if model_info:
            await ws.send(self._build_response(data, result=model_info))
        else:
            await ws.send(self._build_response(data, error=RESPONSE_MODEL_NOT_FOUND.format(model=model)))
        
        return True
    
    async def _handle_walker_execution(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Execute walker with specified zVaFile/zBlock and stream display events.
        
        This handler enables declarative UI rendering from YAML files. When a client
        requests walker execution, the server loads the YAML file, executes the block
        via walker, and all display events are automatically streamed to the client.
        
        Args:
            ws: WebSocket connection
            data: Request data with:
                - zVaFile (str): YAML file name (e.g., "zUI.index")
                - zVaFolder (str, optional): YAML folder path (e.g., "@.UI")
                - zBlock (str, optional): Block name (default: "zVaF")
                - _requestId (int, optional): Request ID for response correlation
        
        Returns:
            bool: True (always handled)
        
        Process:
            1. Extract zVaFile/zVaFolder/zBlock from request
            2. Update zCLI session with these values
            3. Load YAML file via zLoader
            4. Execute block via walker.zBlock_loop()
            5. All display events automatically buffered and sent
            6. Send completion response
        
        Example Request:
            {
                "event": "execute_walker",
                "zVaFile": "zUI.index",
                "zVaFolder": "@.UI",
                "zBlock": "zVaF",
                "_requestId": 0
            }
        
        Example Response (success):
            {
                "_requestId": 0,
                "result": "completed"
            }
        
        Example Response (error):
            {
                "_requestId": 0,
                "error": "No zVaFile found for base path: ..."
            }
        """
        print(f"\n{'='*80}")
        print(f"[MessageHandler] 🚀 WALKER EXECUTION REQUESTED")
        print(f"{'='*80}")
        self.logger.info("[MessageHandler] Walker execution requested")
        
        # Check for shutdown signal (Ctrl+C/SIGTERM)
        if hasattr(self.zcli, '_shutdown_requested') and self.zcli._shutdown_requested:
            self.logger.info("[MessageHandler] Shutdown requested, aborting walker execution")
            await ws.send(self._build_response(data, result="aborted", reason="shutdown"))
            return True
        
        try:
            # Extract parameters
            zVaFile = data.get("zVaFile")
            zVaFolder = data.get("zVaFolder", "@.UI")  # Default folder
            zBlock = data.get("zBlock", "zVaF")  # Default block
            
            if not zVaFile:
                await ws.send(self._build_response(data, error="Missing zVaFile parameter"))
                return True
            
            # ═══════════════════════════════════════════════════════════════
            # HTTP/WebSocket Session Sync (CRITICAL for RBAC)
            # ═══════════════════════════════════════════════════════════════
            # WebSockets don't automatically send HTTP cookies. To support RBAC,
            # we extract the HTTP session ID from the WebSocket message and load
            # the authenticated session into zcli.session.
            session_id = data.get("_sessionId")
            if session_id:
                try:
                    # Load HTTP session from session backend
                    http_session = await self._load_http_session(session_id)
                    if http_session:
                        # Inject authenticated session into zcli.session
                        self.zcli.session.update(http_session)
                        self.logger.info(f"[MessageHandler] 🔐 Loaded HTTP session (user authenticated)")
                        self.logger.debug(f"[MessageHandler] Session keys: {list(http_session.keys())}")
                    else:
                        self.logger.warning(f"[MessageHandler] ⚠️  Session ID provided but session not found (expired?)")
                except Exception as e:
                    self.logger.error(f"[MessageHandler] Error loading HTTP session: {e}")
                    # Continue anyway - session sync is best-effort
            else:
                self.logger.debug(f"[MessageHandler] No session ID provided (user not logged in)")
            
            self.logger.info(f"[MessageHandler] Executing walker: {zVaFolder}/{zVaFile}.{zBlock}")
            
            # Check if this is a dashboard panel load (has _renderTarget)
            # Dashboard panel loads should NOT update session to prevent persistence bugs
            is_dashboard_panel = "_renderTarget" in data
            
            if is_dashboard_panel:
                self.logger.debug(f"[MessageHandler] Dashboard panel load detected - not updating session")
            else:
                # Update session with walker parameters (only for top-level navigation)
                self.zcli.session["zVaFile"] = zVaFile
                self.zcli.session["zVaFolder"] = zVaFolder
                self.zcli.session["zBlock"] = zBlock
                self.logger.debug(f"[MessageHandler] Updated session: zVaFolder={zVaFolder}")
            
            # Always update zSpark_obj (walker uses this for YAML resolution)
            self.zcli.zspark_obj["zVaFile"] = zVaFile
            self.zcli.zspark_obj["zVaFolder"] = zVaFolder
            self.zcli.zspark_obj["zBlock"] = zBlock
            
            # Construct explicit zPath for loader (don't rely on session for dashboard panels)
            # Format: @.{folder}.{file} (e.g., @.UI.zAccount.zUI.Overview)
            folder_part = zVaFolder.lstrip('@.')  # Remove leading @.
            zPath = f"@.{folder_part}.{zVaFile}"
            
            self.logger.debug(f"[MessageHandler] Loading YAML from zPath: {zPath}")
            
            # Load YAML file via loader with explicit path
            raw_zFile = await asyncio.to_thread(self.zcli.loader.handle, zPath)
            
            if not raw_zFile:
                error_msg = f"Failed to load zVaFile: {zVaFolder}/{zVaFile}"
                self.logger.error(f"[MessageHandler] {error_msg}")
                await ws.send(self._build_response(data, error=error_msg))
                return True
            
            if zBlock not in raw_zFile:
                error_msg = f"Block '{zBlock}' not found in {zVaFile}"
                self.logger.error(f"[MessageHandler] {error_msg}")
                await ws.send(self._build_response(data, error=error_msg))
                return True
            
            # Extract zMeta section from YAML for client-side features (v1.5.13: _zScripts support)
            meta_section = raw_zFile.get("zMeta", {})
            if isinstance(meta_section, dict):
                self.zcli.session["zVaFile_meta"] = meta_section
                self.logger.debug(f"[MessageHandler] Stored zVaFile zMeta in session: {list(meta_section.keys())}")
            else:
                self.zcli.session["zVaFile_meta"] = {}
                self.logger.debug(f"[MessageHandler] No zMeta section found in zVaFile")
            
            # Phase 1: Setup per-WebSocket schema cache for DB connection reuse
            # This allows multiple zData operations across walker executions
            # to reuse the same database connection (5-10x performance gain)
            # The cache is stored per ws_id to isolate users (security + correctness)
            ws_id = id(ws)
            if not hasattr(self, '_ws_schema_caches'):
                self._ws_schema_caches = {}
            
            if ws_id not in self._ws_schema_caches:
                from zOS.L2_Core.h_zLoader.loader_modules.loader_cache_schema import SchemaCache
                self._ws_schema_caches[ws_id] = SchemaCache(self.zcli.session, self.logger)
                self.logger.debug(f"[Phase1] Created schema cache for ws_id={ws_id} (DB connection reuse)")
            
            # Store schema cache in zcli.wizard for zData to discover
            # This follows the existing wizard mode pattern (see zData._init_wizard_handler)
            if hasattr(self.zcli, 'wizard') and self.zcli.wizard:
                self.zcli.wizard.schema_cache = self._ws_schema_caches[ws_id]
            
            # Execute the block via walker
            # Note: walker.zBlock_loop() generates display events which are auto-buffered in zBifrost mode
            # Use zcli.walker (always available) instead of self.walker (may be None in web server mode)
            walker = self.walker or self.zcli.walker  # Fallback to zcli.walker if self.walker is None
            
            # Initialize breadcrumbs before executing (required for walker_dispatch)
            # Construct full breadcrumb path: @.{zVaFolder}.{zVaFile}.{zBlock}
            folder_part = zVaFolder.lstrip('@.')
            full_crumb_path = f"@.{folder_part}.{zVaFile}.{zBlock}"
            
            # Initialize zCrumbs with enhanced format v2.0 (trails + metadata)
            # This matches the format from zNavigation subsystem (commit d455efd)
            if "zCrumbs" not in self.zcli.session:
                self.zcli.session["zCrumbs"] = {
                    'trails': {},
                    '_context': {},
                    '_depth_map': {}
                }
                self.logger.debug(f"[MessageHandler] Initialized zCrumbs with enhanced v2.0 format")
            
            # Ensure enhanced format structure exists (auto-migrate from flat format if needed)
            if 'trails' not in self.zcli.session["zCrumbs"]:
                self.logger.info(f"[MessageHandler] Migrating zCrumbs from flat to enhanced v2.0 format")
                # Preserve existing trails (filter out metadata keys starting with _)
                old_trails = {k: v for k, v in self.zcli.session["zCrumbs"].items() if not k.startswith('_')}
                self.zcli.session["zCrumbs"] = {
                    'trails': old_trails,
                    '_context': {},
                    '_depth_map': {}
                }
            
            # Set breadcrumb for this block (in trails sub-dict for enhanced format)
            self.zcli.session["zCrumbs"]['trails'][full_crumb_path] = []
            self.zcli.session["zBlock"] = zBlock
            
            self.logger.debug(f"[MessageHandler] Initialized breadcrumb: {full_crumb_path}")
            
            # Check for shutdown before executing block
            if hasattr(self.zcli, '_shutdown_requested') and self.zcli._shutdown_requested:
                self.logger.info("[MessageHandler] Shutdown requested before block execution, aborting")
                await ws.send(self._build_response(data, result="aborted", reason="shutdown"))
                return True
            
            # Execute the block
            block_dict = raw_zFile[zBlock]
            
            # Check if walker execution returns a generator (chunked mode)
            result = await asyncio.to_thread(walker.execute_loop, block_dict)
            
            # Check if result is a generator (chunked execution mode)
            import types
            if isinstance(result, types.GeneratorType):
                self.logger.info("[MessageHandler] 🎬 Chunked execution mode - consuming generator")
                
                # Consume generator and send chunks progressively
                try:
                    chunk_num = 0
                    paused_at_gate = False  # Track if we paused at a gate
                    for chunk_keys, is_gate, gate_value in result:
                        # Check for shutdown during chunk processing
                        if hasattr(self.zcli, '_shutdown_requested') and self.zcli._shutdown_requested:
                            self.logger.info("[MessageHandler] Shutdown requested during chunk processing, aborting")
                            await ws.send(self._build_response(data, result="aborted", reason="shutdown"))
                            return True
                        
                        chunk_num += 1
                        self.logger.info(f"[MessageHandler] 📦 Chunk {chunk_num}: {chunk_keys} (gate={is_gate})")
                        
                        # Check for special RBAC denial chunk
                        if gate_value and isinstance(gate_value, dict) and gate_value.get("zRBAC_denied"):
                            # RBAC was denied - collect and send buffered display events
                            buffered_events = self.zcli.display.collect_buffered_events()
                            self.logger.info(f"[MessageHandler] 📛 RBAC denied - sending {len(buffered_events)} buffered events")
                            
                            # Extract the denial message from buffered events
                            denial_messages = []
                            for event in buffered_events:
                                if isinstance(event, dict):
                                    # Extract content from display events
                                    content = event.get("content") or event.get("label") or str(event)
                                    denial_messages.append(content)
                                else:
                                    denial_messages.append(str(event))
                            
                            # Send RBAC denial event to frontend
                            if denial_messages:
                                error_msg = {
                                    "event": "rbac_denied",
                                    "message": "\n".join(denial_messages),
                                    "_requestId": data.get("_requestId")
                                }
                                await ws.send(safe_json_dumps(error_msg))
                                self.logger.info("[MessageHandler] ✅ Sent RBAC denial message to frontend")
                            
                            # Send navigate_back event
                            if gate_value.get("_signal") == "navigate_back":
                                navigate_back_msg = {
                                    "event": "navigate_back",
                                    "reason": "rbac_denied",
                                    "_requestId": data.get("_requestId")
                                }
                                await ws.send(safe_json_dumps(navigate_back_msg))
                                self.logger.info("[MessageHandler] ✅ Sent navigate_back event")
                            
                            # Skip normal chunk processing
                            continue
                        
                        # Extract YAML data for chunk keys (frontend will render properly)
                        # Filter out internal keys like ~zNavBar* (already rendered separately)
                        chunk_data = {}
                        
                        # FIRST: Always include block-level metadata (_zClass, _zStyle, _zId)
                        # These are attributes that apply to the parent container (not content blocks)
                        METADATA_KEYS = ['_zClass', '_zStyle', '_zId']
                        for key in METADATA_KEYS:
                            if key in block_dict:
                                chunk_data[key] = block_dict[key]
                        
                        # THEN: Add the specific content keys for this chunk (maintains document order)
                        # NOTE: Terminal-suppressed content (_Live_Demo_Section) is already filtered by wizard
                        for key in chunk_keys:
                            # Skip internal/meta keys (start with ~)
                            if key.startswith('~'):
                                continue
                            if key in block_dict:
                                # v1.5.17: Send raw structure - dispatcher is mode-aware
                                # Terminal mode: Dispatcher expands shorthands during execution
                                # Bifrost mode: Dispatcher skips expansion, sends raw to client
                                chunk_data[key] = block_dict[key]
                        
                        # NOTE: We send suffixed keys as-is to Bifrost (e.g., zText__dup2)
                        # The Bifrost client will strip the __dup{N} suffix when determining 
                        # which renderer to use, allowing duplicate UI events to render correctly
                        self.logger.info(f"[MessageHandler] ✅ Sending chunk data with suffixed keys to Bifrost")
                        
                        # Extract and send special zDisplay events (zDash, etc.) as standalone messages
                        # before sending the chunk. These events need special frontend handling.
                        special_events_sent = await self._extract_and_send_special_events(ws, chunk_data, data)
                        if special_events_sent:
                            self.logger.info(f"[MessageHandler] ✅ Sent {special_events_sent} special event(s) from chunk")
                        
                        # NEW v1.5.12: Resolve %data.* variables in chunk_data FIRST (before injection)
                        # This enables Flask/Jinja-style data interpolation while keeping DB credentials in .zEnv
                        # Access context from walker if available (created in zBlock_loop with _resolved_data)
                        walker_context = getattr(walker, 'block_context', None)
                        if walker_context and "_resolved_data" in walker_context:
                            chunk_data = self._resolve_data_variables_recursive(chunk_data, walker_context)
                            self.logger.info(f"[MessageHandler] ✅ Resolved %data.* variables in chunk data")
                        
                        # NEW v1.5.15: Resolve zPath references in chunk_data FIRST (before expansion)
                        # This enables declarative path resolution for Bifrost mode (@ and ~ paths → web URLs)
                        chunk_data = self._resolve_zpath_references(chunk_data, self.zcli)
                        
                        # NEW v1.5.18: Expand shorthands in chunk_data SECOND (before injection)
                        # This creates zDisplay directives from raw YAML (zImage → {zDisplay: {event: 'image', ...}})
                        # so that buffered event injection can find matching directives!
                        # This is critical for deeply nested organizational structures (like zTheme).
                        chunk_data = self._expand_chunk_shorthands(chunk_data, walker)
                        
                        # NEW Phase 1: Inject buffered event data back into zDisplay directives AFTER expansion
                        # This allows declarative zDisplay events (like zCrumbs with _parent) to include
                        # the data that was generated by the backend (without double-rendering)
                        # CRITICAL: Must happen AFTER expansion so zDisplay directives exist for injection!
                        buffered_events = self.zcli.display.collect_buffered_events()
                        if buffered_events:
                            self.logger.info(f"[MessageHandler] 🔄 Injecting {len(buffered_events)} buffered events back into chunk data")
                            
                            # Group buffered events by type into queues (preserves processing order)
                            from collections import defaultdict, deque
                            event_queues = defaultdict(deque)
                            for event in buffered_events:
                                if isinstance(event, dict) and 'display_event' in event:
                                    event_name = event['display_event']
                                    event_data = event.get('data', {})
                                    
                                    # NEW v1.5.20: Resolve zPath references in buffered event data
                                    # This ensures @ paths in href/src become web URLs before injection
                                    original_href = event_data.get('href', None) if event_name == 'link' else None
                                    event_data = self._resolve_zpath_references(event_data, self.zcli)
                                    if original_href and original_href.startswith('@'):
                                        resolved_href = event_data.get('href', original_href)
                                        self.logger.info(f"[MessageHandler] 🔗 Resolved link: {original_href} → {resolved_href}")
                                    
                                    event_queues[event_name].append(event_data)
                            
                            # Inject buffered events into matching zDisplay directives in traversal order
                            injected = self._inject_buffered_events_in_order(chunk_data, event_queues)
                            self.logger.info(f"[MessageHandler] ✅ Injected {injected} buffered events into chunk data")
                            # DEBUG: Log a sample of the chunk_data to verify structure
                            import json
                            sample = str(chunk_data)[:500] if chunk_data else "None"
                            self.logger.debug(f"[MessageHandler] chunk_data sample after injection: {sample}...")
                            
                            # NEW v1.5.19: Unwrap zDisplay directives AFTER injection
                            # Frontend expects {event: '...', params} not {zDisplay: {event: '...', params}}
                        chunk_data = self._unwrap_zdisplay_directives(chunk_data)
                        self.logger.info(f"[MessageHandler] ✅ Unwrapped zDisplay directives for frontend")
                        
                        # DEBUG: Check if zCrumbs was unwrapped correctly
                        if 'Page_Header' in chunk_data and 'zCrumbs' in chunk_data['Page_Header']:
                            zcrumbs_data = chunk_data['Page_Header']['zCrumbs']
                            self.logger.debug(f"[MessageHandler] 🔍 zCrumbs after unwrap: {zcrumbs_data}")
                            if isinstance(zcrumbs_data, dict):
                                self.logger.debug(f"[MessageHandler] 🔍 zCrumbs keys: {list(zcrumbs_data.keys())}")
                                if 'event' in zcrumbs_data:
                                    self.logger.debug(f"[MessageHandler] ✅ zCrumbs has 'event' key: {zcrumbs_data['event']}")
                                else:
                                    self.logger.error(f"[MessageHandler] ❌ zCrumbs missing 'event' key! Has zDisplay wrapper: {'zDisplay' in zcrumbs_data}")
                        
                        # Send chunk to frontend with YAML data (not HTML)
                        # Frontend will render using its existing _renderItems() pipeline
                        chunk_msg = {
                            "event": "render_chunk",
                            "chunk_num": chunk_num,
                            "keys": chunk_keys,
                            "data": chunk_data,  # Send YAML data with resolved variables
                            "is_gate": is_gate,
                            "zBlock": zBlock,  # Include block name for id attribute
                            "_requestId": data.get("_requestId")
                        }
                        
                        # DEBUG: Log a sample zDisplay event from the data being sent
                        if chunk_data and isinstance(chunk_data, dict):
                            for key, value in list(chunk_data.items())[:3]:  # First 3 keys
                                if isinstance(value, dict):
                                    for subkey, subvalue in list(value.items())[:2]:  # First 2 subkeys
                                        if isinstance(subvalue, dict) and 'zDisplay' in subvalue:
                                            self.logger.debug(f"[MessageHandler] Sending {key}.{subkey}: {subvalue}")
                                            break
                        
                        await ws.send(safe_json_dumps(chunk_msg))
                        self.logger.info(f"[MessageHandler] ✅ Sent chunk {chunk_num}")
                        
                        if is_gate:
                            # Check if this gate contains auto-executable actions (zLogout, zLogin, zFunc, etc.)
                            # These should execute automatically, not wait for user interaction
                            auto_executable = await self._auto_execute_gate_actions(ws, data, chunk_data, chunk_keys, block_dict)
                            
                            if auto_executable:
                                # Action was executed and generator was resumed - continue to next chunk
                                self.logger.info(f"[MessageHandler] ✅ Gate action auto-executed, generator resumed")
                                paused_at_gate = False  # Don't mark as paused since we resumed
                                continue
                            
                            # Pause here - stop sending chunks until gate completes (for forms/dialogs)
                            self.logger.info(f"[MessageHandler] ⏸️  Paused at gate - storing generator state")
                            
                            # Store generator state for resumption after form submission
                            ws_id = id(ws)  # Use WebSocket connection ID as key
                            self._paused_generators[ws_id] = {
                                'generator': result,  # The generator object itself
                                'block_dict': block_dict,  # Full block YAML (for rendering remaining chunks)
                                'zBlock': zBlock,  # Block name (for ^ navigation check)
                                'breadcrumb_path': full_crumb_path,  # For logging
                                'request_id': data.get("_requestId"),  # Original walker request ID
                                'chunk_num': chunk_num  # Current chunk number
                            }
                            
                            self.logger.info(f"[MessageHandler] Stored generator state for ws={ws_id}")
                            self.logger.info(f"[MessageHandler] Post-gate content will be sent after successful form submission")
                            paused_at_gate = True  # Mark that we paused
                            break  # Exit loop - don't send post-gate chunks yet
                    
                    # Generator completed
                    self.logger.info("[MessageHandler] Generator exhausted - all chunks sent")
                    
                except StopIteration as e:
                    # Generator finished, get return value
                    final_result = e.value if hasattr(e, 'value') else None
                    self.logger.info(f"[MessageHandler] Generator completed with: {final_result}")
                
                # NOTE: Buffered display events are now injected back into chunk data (Phase 1)
                # No need to clear them here - already consumed during chunk assembly
                
                # Only handle bounce-back if we didn't pause at a gate
                # (gate-based bounce-back is handled in _resume_generator_after_gate)
                if not paused_at_gate:
                    # Check if block has bounce-back modifier (^)
                    if zBlock.startswith('^'):
                        self.logger.info(f"[MessageHandler] Block {zBlock} has ^ modifier - triggering bounce-back")
                        navigate_back_msg = {
                            "event": "navigate_back",
                            "reason": "bounce_back_block_completed",
                            "_requestId": data.get("_requestId")
                        }
                        await ws.send(safe_json_dumps(navigate_back_msg))
                        self.logger.info("[MessageHandler] ✅ Sent navigate_back event for bounce-back block")
                        return True  # Don't send completion, just return (matching gate-based pattern)
                    
                    # Send completion (only for non-bounce-back blocks)
                    await ws.send(self._build_response(data, result="completed"))
                
                return True
            
            else:
                # Regular non-chunked execution
                self.logger.info("[MessageHandler] Standard execution mode (no chunking)")
                
                # Collect buffered display events and broadcast them
                # Clear buffered events without broadcasting them
                # In Bifrost mode, the frontend renders directly from YAML (preserving _zClass styling)
                # Broadcasting buffered events would cause double-rendering
                buffered_events = self.zcli.display.collect_buffered_events()
                self.logger.info(f"[MessageHandler] Cleared {len(buffered_events)} buffered display events (not broadcasting - frontend renders from YAML)")
                
                # Send completion response
                await ws.send(self._build_response(data, result="completed"))
                self.logger.info("[MessageHandler] Walker execution completed successfully")
                return True
            
        except Exception as e:
            error_msg = f"Walker execution failed: {str(e)}"
            self.logger.error(f"[MessageHandler] {error_msg}", exc_info=True)
            await ws.send(self._build_response(data, error=error_msg))
            return True
    
    async def _handle_form_submit(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle form submission from Bifrost frontend (async form handling).
        
        This handler enables async form submission in Bifrost mode. When a user
        fills out a zDialog form in the browser and clicks Submit, the frontend
        sends the form data along with the onSubmit action. This handler validates
        the data and executes the onSubmit action via zDispatch.
        
        Args:
            ws: WebSocket connection
            data: Request data with:
                - data (dict): Form field values {field_name: value, ...}
                - onSubmit (dict): Submit action to execute (e.g., zData insert)
                - model (str, optional): Schema model path for validation
                - dialogId (str, optional): Dialog identifier
                - _requestId (int, optional): Request ID for response correlation
        
        Returns:
            bool: True (always handled)
        
        Process:
            1. Extract form data and onSubmit action from request
            2. Validate data against schema (if model specified)
            3. Execute onSubmit action via zDispatch
            4. Send success/error response back to frontend
        
        Example Request:
            {
                "event": "form_submit",
                "dialogId": "dialog-123",
                "data": {"name": "Gal", "email": "gal@zolo.media", "password": "secret123"},
                "onSubmit": {"zData": {"action": "insert", "table": "users", ...}},
                "model": "@.models.zSchema.contacts",
                "_requestId": 5
            }
        
        Example Response (success):
            {
                "_requestId": 5,
                "success": true,
                "message": "✓ Registration successful! Welcome to zCLI."
            }
        
        Example Response (validation error):
            {
                "_requestId": 5,
                "success": false,
                "message": "Validation failed",
                "errors": ["Email is required", "Password must be at least 8 characters"]
            }
        """
        self.logger.info("[MessageHandler] Form submission received")
        
        try:
            # Extract form data and onSubmit action
            form_data = data.get('data', {})
            on_submit = data.get('onSubmit')
            model = data.get('model')
            dialog_id = data.get('dialogId', 'unknown')
            
            # Mask passwords in form_data for logging
            from zOS.L2_Core.j_zDialog.dialog_modules.dialog_submit import _mask_passwords_in_dict
            masked_form_data = _mask_passwords_in_dict(form_data)
            
            self.logger.debug(f"[FormSubmit] Dialog ID: {dialog_id}")
            self.logger.debug(f"[FormSubmit] Fields: {list(form_data.keys())}")
            self.logger.debug(f"[FormSubmit] Data: {masked_form_data}")
            self.logger.debug(f"[FormSubmit] Model: {model}")
            
            # Validate if model is specified AND it's an insert operation
            # Only auto-validate for zData insert operations (registration)
            # For login/custom operations, let the onSubmit handler validate
            is_insert_operation = (
                on_submit and 
                isinstance(on_submit, dict) and 
                'zData' in on_submit and 
                on_submit.get('zData', {}).get('action') == 'insert'
            )
            
            if model and isinstance(model, str) and model.startswith('@') and is_insert_operation:
                self.logger.info(f"[FormSubmit] Validating against schema: {model}")
                
                try:
                    # Load schema
                    schema_dict = self.zcli.loader.handle(model) if hasattr(self.zcli, 'loader') else None
                    
                    if schema_dict:
                        # Extract table name from model path
                        table_name = model.split('.')[-1]
                        
                        # Create validator
                        from zOS.L3_Abstraction.n_zData.zData_modules.shared.validator import DataValidator
                        validator = DataValidator(schema_dict, self.logger)
                        
                        # Validate insert data
                        is_valid, errors = validator.validate_insert(table_name, form_data)
                        
                        if not is_valid:
                            self.logger.warning(f"[FormSubmit] Validation failed: {errors}")
                            
                            # Format error messages for frontend
                            error_messages = [f"{field}: {msg}" for field, msg in errors.items()]
                            
                            await ws.send(self._build_response(data,
                                success=False,
                                message="Validation failed. Please correct the errors and try again.",
                                errors=error_messages
                            ))
                            return True
                        
                        self.logger.info("[FormSubmit] Validation passed")
                    else:
                        self.logger.warning(f"[FormSubmit] Schema not found: {model}")
                
                except Exception as e:
                    self.logger.error(f"[FormSubmit] Validation error: {e}", exc_info=True)
                    # Continue without validation (non-blocking)
            elif model and not is_insert_operation:
                self.logger.info("[FormSubmit] Auto-validation skipped (not a zData insert operation) - custom handler will validate")
            else:
                self.logger.debug("[FormSubmit] No validation - no model specified")
            
            # Check if onSubmit action exists
            if not on_submit:
                self.logger.warning("[FormSubmit] No onSubmit action provided")
                await ws.send(self._build_response(data,
                    success=False,
                    message="Form configuration error: No onSubmit action specified."
                ))
                return True
            
            # Inject form data into onSubmit action (placeholder replacement)
            from zOS.L2_Core.j_zDialog.dialog_modules.dialog_context import inject_placeholders
            
            # Create dialog context for placeholder injection
            dialog_context = {
                'model': model,
                'fields': list(form_data.keys()),
                'zConv': form_data
            }
            
            # Inject zConv placeholders into onSubmit
            injected_action = inject_placeholders(on_submit, dialog_context, self.logger)
            
            # Mask passwords in injected action for logging
            masked_action = _mask_passwords_in_dict(injected_action)
            self.logger.debug(f"[FormSubmit] Injected action: {masked_action}")
            
            self.logger.info(f"[FormSubmit] Executing onSubmit action via zDispatch")
            
            # Detect action type and execute appropriately
            if 'zFunc' in injected_action:
                # Plugin function call
                self.logger.debug(f"[FormSubmit] Executing zFunc: {injected_action['zFunc']}")
                
                # Execute via plugin resolver
                # Note: zcli is already bound to zparser, only pass the function string and context
                result = await asyncio.to_thread(
                    self.zcli.zparser.resolve_plugin_invocation,
                    injected_action['zFunc'],
                    context=dialog_context
                )
                
                # Check if result is a dict with success/message (from plugin)
                if isinstance(result, dict) and 'success' in result:
                    # Plugin returned structured response for Bifrost
                    await ws.send(self._build_response(data, **result))
                    
                    # Resume generator if action was successful
                    if result.get('success'):
                        await self._resume_generator_after_gate(ws, data)
                    
                    return True
                else:
                    # Plugin returned None or simple value (Terminal-style)
                    await ws.send(self._build_response(data,
                        success=True,
                        message="✓ Action completed successfully!"
                    ))
                    
                    # Resume generator after successful form submission
                    await self._resume_generator_after_gate(ws, data)
                    
                    return True
            
            elif 'zLogin' in injected_action:
                # Built-in authentication action
                self.logger.debug(f"[FormSubmit] Executing zLogin: {injected_action['zLogin']}")
                
                # Import and execute handle_zLogin
                from zOS.L2_Core.d_zAuth.zAuth_modules import handle_zLogin
                
                result = await asyncio.to_thread(
                    handle_zLogin,
                    app_or_type=injected_action['zLogin'],
                    zConv=dialog_context.get('zConv', {}),
                    zContext=dialog_context,
                    zcli=self.zcli
                )
                
                # handle_zLogin always returns a dict with success/message
                await ws.send(self._build_response(data, **result))
                
                # Resume generator if form submission was successful
                if result.get('success'):
                    await self._resume_generator_after_gate(ws, data)
                
                return True
                    
            elif 'zData' in injected_action:
                # Data operation (insert, update, etc.)
                result = await asyncio.to_thread(
                    self.zcli.dispatch.handle,
                    'zData',
                    injected_action.get('zData', injected_action)
                )
                
                self.logger.info(f"[FormSubmit] Action executed successfully")
                
                # Send success response
                await ws.send(self._build_response(data,
                    success=True,
                    message="✓ Form submitted successfully!"
                ))
                
                # Resume generator after successful form submission
                await self._resume_generator_after_gate(ws, data)
                
                return True
            else:
                # Unknown action type
                self.logger.warning(f"[FormSubmit] Unknown action type: {list(injected_action.keys())}")
                await ws.send(self._build_response(data,
                    success=False,
                    message="Form configuration error: Unknown action type."
                ))
                return True
            
        except Exception as e:
            error_msg = f"Form submission failed: {str(e)}"
            self.logger.error(f"[MessageHandler] {error_msg}", exc_info=True)
            await ws.send(self._build_response(data,
                success=False,
                message="An error occurred while submitting the form. Please try again.",
                errors=[str(e)]
            ))
            return True
    
    async def _handle_page_unload(self, ws: Any, data: Dict[str, Any]) -> bool:
        """
        Handle page unload notification from frontend (lifecycle cleanup).
        
        This handler is called when the frontend detects page navigation (e.g., browser
        back/forward button, or user clicking a different nav item). It cleans up any
        state associated with the WebSocket connection, such as paused generators.
        
        Args:
            ws: WebSocket connection
            data: Request data with:
                - reason (str): Reason for unload (e.g., "navigation")
                - timestamp (int): Client timestamp
        
        Returns:
            bool: True (always handled)
        
        Process:
            1. Log the page unload event
            2. Clean up any paused generators for this connection
            3. Acknowledge the unload
        """
        reason = data.get('reason', 'unknown')
        ws_id = id(ws)
        
        self.logger.info(f"[PageUnload] Client page unloading (reason: {reason}, ws={ws_id})")
        
        # Clean up any paused generators for this connection
        if ws_id in self._paused_generators:
            gen_state = self._paused_generators[ws_id]
            zBlock = gen_state.get('zBlock', 'unknown')
            self.logger.info(f"[PageUnload] Cleaning up paused generator for block: {zBlock}")
            del self._paused_generators[ws_id]
        
        # No need to send a response - page is already navigating away
        return True
    
    async def _resume_generator_after_gate(self, ws: Any, form_data: Dict[str, Any]) -> None:
        """
        Resume a paused generator after successful gate completion (form submission).
        
        This method is called after a form submission succeeds (e.g., successful login).
        It retrieves the stored generator state, resumes iteration, and sends the
        remaining chunks to the frontend. This bridges Terminal's synchronous execution
        with Bifrost's asynchronous nature while maintaining proper execution semantics.
        
        Architecture:
            - Terminal: Synchronous gate execution (pause for user input in loop)
            - Bifrost: Async gate execution (pause generator, resume after WS message)
            - Both modes: Same execution order and post-gate content rendering
        
        Args:
            ws: WebSocket connection
            form_data: Original form submission data (for request ID and logging)
        
        Process:
            1. Retrieve stored generator state by WebSocket ID
            2. Resume generator iteration from paused state
            3. Send remaining chunks progressively to frontend
            4. Handle nested gates (pause again if encountered)
            5. Check for ^ bounce-back modifier and trigger navigation
            6. Cleanup generator state after completion
        """
        ws_id = id(ws)
        
        # Check if there's a paused generator for this connection
        if ws_id not in self._paused_generators:
            self.logger.debug(f"[GeneratorResume] No paused generator for ws={ws_id}")
            return
        
        # Retrieve stored generator state
        gen_state = self._paused_generators[ws_id]
        generator = gen_state['generator']
        block_dict = gen_state['block_dict']
        zBlock = gen_state['zBlock']
        chunk_num = gen_state['chunk_num']
        
        self.logger.info(f"[GeneratorResume] 🎬 Resuming generator for block: {zBlock}")
        
        try:
            # Continue consuming generator from where we left off
            for chunk_keys, is_gate, gate_value in generator:
                # Check for shutdown during chunk processing
                if hasattr(self.zcli, '_shutdown_requested') and self.zcli._shutdown_requested:
                    self.logger.info("[GeneratorResume] Shutdown requested, aborting")
                    break
                
                chunk_num += 1
                self.logger.info(f"[GeneratorResume] 📦 Chunk {chunk_num}: {chunk_keys} (gate={is_gate})")
                
                # Extract YAML data for chunk keys
                # Filter out internal keys like ~zNavBar* (already rendered separately)
                chunk_data = {}
                
                # FIRST: Always include block-level metadata (_zClass, _zStyle, _zId)
                # These are attributes that apply to the parent container (not content blocks)
                METADATA_KEYS = ['_zClass', '_zStyle', '_zId']
                for key in METADATA_KEYS:
                    if key in block_dict:
                        chunk_data[key] = block_dict[key]
                
                # THEN: Add the specific content keys for this chunk (maintains document order)
                # NOTE: Terminal-suppressed content (_Live_Demo_Section) is already filtered by wizard
                for key in chunk_keys:
                    if key.startswith('~'):  # Skip internal/meta keys
                        continue
                    if key in block_dict:
                        chunk_data[key] = block_dict[key]
                
                # Send chunk to frontend with YAML data (not HTML)
                chunk_msg = {
                    "event": "render_chunk",
                    "chunk_num": chunk_num,
                    "keys": chunk_keys,
                    "data": chunk_data,
                    "is_gate": is_gate,
                    "zBlock": zBlock,  # Include block name for id attribute
                    "_requestId": gen_state['request_id']  # Use original walker request ID
                }
                await ws.send(safe_json_dumps(chunk_msg))
                self.logger.info(f"[GeneratorResume] ✅ Sent post-gate chunk {chunk_num}")
                
                # If another gate is encountered, pause again (nested gates)
                if is_gate:
                    self.logger.info(f"[GeneratorResume] Another gate encountered, pausing again")
                    gen_state['chunk_num'] = chunk_num
                    return  # Keep generator stored, don't cleanup
            
            # Generator completed - all chunks sent
            self.logger.info(f"[GeneratorResume] ✅ All post-gate chunks sent")
            
            # Check for ^ bounce-back modifier in block name
            if zBlock.startswith('^'):
                self.logger.info(f"[GeneratorResume] Block has ^ modifier - triggering bounce-back")
                # Send bounce-back navigation signal to frontend
                bounce_msg = {
                    "event": "navigate_back",
                    "reason": "bounce_back_block_completed",
                    "_requestId": form_data.get("_requestId")
                }
                await ws.send(safe_json_dumps(bounce_msg))
            
        except StopIteration as e:
            # Generator finished naturally
            final_result = e.value if hasattr(e, 'value') else None
            self.logger.info(f"[GeneratorResume] Generator completed with: {final_result}")
        
        except Exception as e:
            self.logger.error(f"[GeneratorResume] Error resuming generator: {e}", exc_info=True)
        
        finally:
            # Clean up stored generator
            if ws_id in self._paused_generators:
                del self._paused_generators[ws_id]
                self.logger.debug(f"[GeneratorResume] Cleaned up generator state for ws={ws_id}")
    
    def _unwrap_zdisplay_directives(self, data: Any) -> Any:
        """
        Recursively unwraps zDisplay directives in chunk_data for frontend consumption.
        
        Converts {'zImage': {'zDisplay': {event: 'image', ...}}} 
        to      {'zImage': {event: 'image', ...}}
        
        This method is called AFTER buffered event injection.
        """
        if isinstance(data, dict):
            unwrapped = {}
            for key, value in data.items():
                if key.startswith('_'):  # Preserve metadata keys
                    unwrapped[key] = value
                    continue
                
                # If value is a dict with a single 'zDisplay' key, unwrap it
                if isinstance(value, dict) and 'zDisplay' in value and len(value) == 1:
                    unwrapped[key] = self._unwrap_zdisplay_directives(value['zDisplay'])
                else:
                    unwrapped[key] = self._unwrap_zdisplay_directives(value)
            return unwrapped
        elif isinstance(data, list):
            return [self._unwrap_zdisplay_directives(item) for item in data]
        else:
            return data
    
    def _expand_chunk_shorthands(self, data: Any, walker: Any) -> Any:
        """
        Expand UI shorthand elements in chunk_data to create zDisplay directives.
        
        This is critical for buffered event injection to work! The injection logic
        searches for zDisplay directives in chunk_data, but the raw YAML only contains
        shorthands like {zImage: {src: '...', alt_text: '...'}}.
        
        This method recursively expands shorthands to create the zDisplay structure:
            {zImage: {src: '...', alt_text: '...'}}
            → {zDisplay: {event: 'image', src: '...', alt_text: '...'}}
        
        Args:
            data: The data structure to expand (dict, list, or other)
            walker: Walker instance (provides access to session and expander)
            
        Returns:
            Expanded data structure with zDisplay directives
        """
        from zOS.L2_Core.e_zDispatch.dispatch_modules.shorthand_expander import ShorthandExpander
        
        # Get the shorthand expander from walker's dispatcher
        expander = None
        if hasattr(walker, 'dispatcher') and hasattr(walker.dispatcher, 'shorthand_expander'):
            expander = walker.dispatcher.shorthand_expander
        
        if not expander:
            # Fallback: create new expander instance
            logger = getattr(walker, 'logger', self.logger)
            expander = ShorthandExpander(logger)
            # Set the session attribute (expander stores session as instance variable)
            expander.session = getattr(walker, 'session', self.zcli.session)
        
        # Recursively expand shorthands in the data structure
        if isinstance(data, dict):
            expanded = {}
            for key, value in data.items():
                # Skip metadata keys (start with _)
                if key.startswith('_'):
                    expanded[key] = value
                    continue
                
                # Check if this key is a UI shorthand (zImage, zText, zH1, zUL, etc.)
                # Organizational keys like "Features_Section" don't start with lowercase 'z'
                if key.startswith('z') and len(key) > 1 and key[1].isupper() and isinstance(value, dict):
                    # This looks like a UI shorthand (zImage, zText, etc.)
                    # Expand it using the shorthand expander
                    ui_dict = {key: value}  # Wrap in dict for expander
                    expanded_dict, _ = expander.expand(ui_dict, expander.session, is_subsystem_call=False)
                    
                    # The expander returns the expanded structure - use it
                    expanded_value = expanded_dict.get(key, value)  # Get the expanded value for this key
                    # DEBUG: Log the expanded structure
                    self.logger.debug(f"[_expand_chunk_shorthands] Expanded {key}: {expanded_value}")
                    expanded[key] = expanded_value
                else:
                    # Organizational structure or other key - recursively process
                    expanded[key] = self._expand_chunk_shorthands(value, walker)
            return expanded
        elif isinstance(data, list):
            return [self._expand_chunk_shorthands(item, walker) for item in data]
        else:
            return data
    
    def _inject_buffered_events_in_order(self, data: Any, event_queues: Dict[str, Any], path: str = "root") -> int:
        """
        Recursively process zDisplay events and inject buffered data in traversal order.
        
        This fixes the bug where multiple events of the same type (e.g., 6 images) were
        all getting the same buffered data injected. Now each event pops the next buffered
        event from its type-specific queue, preserving processing order.
        
        Args:
            data: The data structure to process (dict, list, or other)
            event_queues: Dict mapping event types to deques of buffered event data
            path: Current path for logging (e.g., "Features_Section.Feature_Grid.UtilityFirst_Card")
            
        Returns:
            Number of zDisplay events that were injected
        """
        injected_count = 0
        
        if isinstance(data, dict):
            # Check if this dict contains a zDisplay event
            if 'zDisplay' in data:
                zdisplay = data['zDisplay']
                if isinstance(zdisplay, dict):
                    event_name = zdisplay.get('event')
                    # Map zURL to link (backend buffers zURL events as 'link' type)
                    buffer_event_name = 'link' if event_name == 'zURL' else event_name
                    # DEBUG: Log what we're trying to inject
                    self.logger.debug(f"[_inject] Found zDisplay at {path}, event={event_name}, buffer_event={buffer_event_name}, queue_has_data={buffer_event_name in event_queues and bool(event_queues.get(buffer_event_name))}")
                    # If there's a buffered event for this type, pop and inject it
                    if buffer_event_name and buffer_event_name in event_queues and event_queues[buffer_event_name]:
                        event_data = event_queues[buffer_event_name].popleft()
                        # Exclude 'event' key to avoid overwriting the original event type
                        filtered_data = {k: v for k, v in event_data.items() if k != 'event'}
                        self.logger.debug(f"[_inject] Injecting data at {path}: {filtered_data}")
                        data['zDisplay'].update(filtered_data)
                        injected_count += 1
            
            # Recursively process all dict values (depth-first to match processing order)
            for key, value in data.items():
                injected_count += self._inject_buffered_events_in_order(value, event_queues, f"{path}.{key}")
        
        elif isinstance(data, list):
            # Recursively process all list items in order
            for i, item in enumerate(data):
                injected_count += self._inject_buffered_events_in_order(item, event_queues, f"{path}[{i}]")
        
        return injected_count
    
    def _resolve_data_variables_recursive(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        Recursively resolve %data.* variables in chunk data before sending to frontend.
        
        This enables Flask/Jinja-style data interpolation while keeping DB credentials
        secure in .zEnv. Variables like %data.user.name are resolved from
        context["_resolved_data"] which was populated by _data block queries.
        
        Args:
            data: The data structure to process (dict, list, or string)
            context: Execution context containing _resolved_data from queries
            
        Returns:
            The data structure with all %data.* variables resolved
            
        Example:
            data = {"label": "%data.user.name", "items": ["%data.user.email"]}
            context = {"_resolved_data": {"user": {"name": "Gal", "email": "gal@..."}}}
            result = {"label": "Gal", "items": ["gal@..."]}
        """
        from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
        
        if isinstance(data, dict):
            # Recursively process dictionary values
            return {key: self._resolve_data_variables_recursive(value, context) for key, value in data.items()}
        elif isinstance(data, list):
            # Recursively process list items
            return [self._resolve_data_variables_recursive(item, context) for item in data]
        elif isinstance(data, str) and "%" in data:
            # Resolve variables in strings
            return resolve_variables(data, self.zcli, context)
        else:
            # Return primitives as-is (int, bool, None, etc.)
            return data
    
    def _resolve_zpath_references(self, data: Any, zcli: Any) -> Any:
        """
        Recursively resolve zPath references (@, ~) in chunk data before sending to Bifrost.
        
        Converts workspace-relative (@) and home-relative (~) paths to web-relative URLs
        for serving via zServer. This enables the declarative zPath approach where the
        same path definition works in both Terminal (absolute filesystem) and Bifrost (web URL) modes.
        
        Args:
            data: The data structure to process (dict, list, or string)
            zcli: zCLI instance for accessing zparser and zserver
            
        Returns:
            The data structure with all zPath references resolved to web URLs
            
        Example:
            data = {"src": "@.static.brand.logo.png"}
            result = {"src": "/static/brand/logo.png"}  # Ready for zServer
            
            data = {"zLink": "@.UI.zProducts.zUI.zTheme.zTheme_Details"}
            result = {"zLink": "/zProducts/zTheme"}  # Navigation route
        """
        from pathlib import Path
        
        if isinstance(data, dict):
            # Recursively process dictionary values
            return {key: self._resolve_zpath_references(value, zcli) for key, value in data.items()}
        elif isinstance(data, list):
            # Recursively process list items
            return [self._resolve_zpath_references(item, zcli) for item in data]
        elif isinstance(data, str) and data.startswith(("@", "~")):
            # Resolve zPath to web-relative URL
            try:
                # Check if this is a navigation zPath (@.UI.*)
                if data.startswith("@.UI."):
                    # Navigation path: convert to HTTP route
                    web_path = self._convert_ui_zpath_to_http_route(data, zcli)
                    self.logger.debug(f"[zPath] Navigation: {data} → {web_path}")
                    return web_path
                
                # Resource path logic (static, templates, etc.)
                # Step 1: Resolve zPath to absolute filesystem path
                resolved_path = zcli.zparser.resolve_data_path(data)
                self.logger.debug(f"[zPath] Resolved: {data} → {resolved_path}")
                
                # Step 2: Convert to web-relative URL for zServer
                zserver = getattr(zcli, 'server', None)
                if zserver:
                    serve_path = Path(zserver.serve_path).resolve()
                    resolved_path_obj = Path(resolved_path)
                    
                    if resolved_path_obj.is_relative_to(serve_path):
                        # Convert to URL path relative to serve_path
                        rel_path = resolved_path_obj.relative_to(serve_path)
                        web_path = "/" + str(rel_path).replace("\\", "/")
                        self.logger.debug(f"[zPath] Converted to web path: {web_path}")
                        return web_path
                    else:
                        # Path outside serve_path - keep absolute (fallback)
                        self.logger.warning(f"[zPath] Path outside serve_path: {resolved_path}")
                        return resolved_path
                else:
                    # No zServer - keep absolute path (shouldn't happen in Bifrost)
                    self.logger.warning(f"[zPath] No zServer found: {data}")
                    return resolved_path
            except Exception as e:
                # Error resolving - return original
                self.logger.error(f"[zPath] Error resolving {data}: {e}")
                return data
        else:
            # Return primitives and non-zPath strings as-is
            return data
    
    def _convert_ui_zpath_to_http_route(self, ui_zpath: str, zcli: Any) -> str:
        """
        Convert UI zPath to HTTP route format for navigation.
        
        Navigation zPaths follow the pattern: @.UI.<folders>.zUI.<file>.<block>
        HTTP routes strip the zUI. prefix and block name to create clean URLs.
        
        Args:
            ui_zpath: UI zPath string (e.g., @.UI.zProducts.zUI.zTheme.zTheme_Details)
            zcli: zCLI instance (currently unused but available for future enhancements)
        
        Returns:
            str: HTTP route (e.g., /zProducts/zTheme)
        
        Examples:
            @.UI.zProducts.zUI.zTheme.zTheme_Details → /zProducts/zTheme
            @.UI.zUI.zVaF.zVaF → /
            @.UI.zUI.zAbout.meta → /zAbout
            @.UI.zProducts.zTheme.zUI.zBreakpoints.zBreakpoints_Details → /zProducts/zTheme/zBreakpoints
        
        Notes:
            - Strips @.UI. prefix
            - Removes zUI. prefixes from parts
            - Removes block name (last part)
            - Returns "/" for root routes
        """
        # Strip @.UI. prefix (5 characters)
        path_after_ui = ui_zpath[5:]
        
        # Split into parts
        parts = path_after_ui.split('.')
        
        # Remove zUI. prefixes and block names (last part)
        route_parts = []
        for part in parts[:-1]:  # Skip last part (block name)
            if not part.startswith('zUI'):
                route_parts.append(part)
        
        # Build HTTP route
        if not route_parts:
            return "/"  # Root route
        else:
            return "/" + "/".join(route_parts)
    
    async def _extract_and_send_special_events(
        self,
        ws: Any,
        chunk_data: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> int:
        """
        Extract and send special zDisplay events (zDash, etc.) as standalone messages.
        
        Scans chunk_data for zDisplay events that require special frontend handling
        (like zDash for dashboard rendering). These events are sent as standalone
        WebSocket messages and removed from the chunk data.
        
        Args:
            ws: WebSocket connection
            chunk_data: Dictionary of block items to scan
            request_data: Original request data (for _requestId)
        
        Returns:
            int: Number of special events sent
        """
        events_sent = 0
        keys_to_remove = []
        
        # Scan chunk data for zDisplay events
        for key, value in chunk_data.items():
            if not isinstance(value, list):
                continue
            
            # Check each item in the list
            for item in value:
                if not isinstance(item, dict):
                    continue
                
                # Check for zDisplay events
                if 'zDisplay' in item:
                    display_event = item['zDisplay']
                    if isinstance(display_event, dict):
                        event_type = display_event.get('event')
                        
                        # Special events that need standalone handling
                        _SPECIAL_EVENTS = ['zDash']
                        
                        if event_type in _SPECIAL_EVENTS:
                            self.logger.info(f"[MessageHandler] 🎯 Found special event: {event_type} in key '{key}'")
                            
                            # Create standalone event message
                            event_msg = {
                                "event": event_type,
                                **{k: v for k, v in display_event.items() if k != 'event'}
                            }
                            
                            if "_requestId" in request_data:
                                event_msg["_requestId"] = request_data["_requestId"]
                            
                            # Send the special event
                            await ws.send(safe_json_dumps(event_msg))
                            self.logger.info(f"[MessageHandler] ✅ Sent special {event_type} event")
                            events_sent += 1
                            
                            # Mark this key for removal from chunk
                            if key not in keys_to_remove:
                                keys_to_remove.append(key)
        
        # Remove keys that contained only special events from chunk_data
        # This prevents double-rendering (once as special event, once in chunk)
        for key in keys_to_remove:
            if key in chunk_data:
                del chunk_data[key]
                self.logger.info(f"[MessageHandler] 🗑️  Removed '{key}' from chunk (sent as special event)")
        
        return events_sent
    
    async def _auto_execute_gate_actions(
        self,
        ws: Any,
        data: Dict[str, Any],
        chunk_data: Dict[str, Any],
        chunk_keys: list,
        block_dict: Dict[str, Any]
    ) -> bool:
        """
        Auto-execute actions in gate blocks (zLogout, zLogin, zFunc, etc.).
        
        This method checks if a gate chunk contains auto-executable actions
        (zLogout, zLogin, zFunc, zLink, etc.) and executes them automatically.
        This is the "system gate" pattern where actions execute without user
        interaction, unlike form gates which wait for submission.
        
        Args:
            ws: WebSocket connection
            data: Original walker execution request
            chunk_data: Data sent in the chunk (may contain actions)
            chunk_keys: Keys in this chunk
            block_dict: Full block YAML dictionary
            
        Returns:
            bool: True if action was auto-executed (generator resumed),
                  False if this is a form gate (needs user interaction)
        
        Auto-Executable Actions:
            - zLogout: "app_name"
            - zLogin: "app_name" (though typically in onSubmit)
            - zFunc: "function_name"
            - zLink: "link_target"
            - Any other standalone action
            
        Not Auto-Executable:
            - zDialog: {...} - Needs user form submission
        """
        # Check each key in the chunk for executable actions
        for key in chunk_keys:
            if key not in block_dict:
                continue
            
            key_value = block_dict[key]
            
            # key_value is typically a list of dicts
            if not isinstance(key_value, list):
                continue
            
            for item in key_value:
                if not isinstance(item, dict):
                    continue
                
                # Check for auto-executable actions
                # zDialog is NOT auto-executable (needs form submission)
                if 'zDialog' in item:
                    self.logger.debug(f"[GateAction] Found zDialog - needs user interaction, not auto-executing")
                    return False  # This is a form gate, not auto-executable
                
                # Check for zLogout
                if 'zLogout' in item:
                    app_name = item['zLogout']
                    self.logger.info(f"[GateAction] Auto-executing zLogout: {app_name}")
                    
                    try:
                        # Import and execute zLogout via zDispatch
                        from zOS.L2_Core.e_zDispatch import handle_zDispatch
                        
                        # Build context for zLogout (empty zConv, no model needed)
                        context = {
                            "zConv": {},
                            "model": None,
                            "mode": "zBifrost"
                        }
                        
                        # Execute zLogout
                        result = await asyncio.to_thread(
                            handle_zDispatch,
                            "zLogout",
                            item,  # {"zLogout": "zCloud"}
                            zcli=self.zcli,
                            walker=self.walker,
                            context=context
                        )
                        
                        self.logger.info(f"[GateAction] zLogout executed: {result}")
                        
                        # Send success message to frontend (if result is dict with success/message)
                        if isinstance(result, dict) and 'success' in result:
                            await ws.send(safe_json_dumps({
                                "success": result.get("success"),
                                "message": result.get("message", "Logout completed"),
                                "_requestId": data.get("_requestId")
                            }))
                        
                        # Resume generator to send remaining chunks (post-gate content)
                        await self._resume_generator_after_gate(ws, data)
                        
                        return True  # Action was auto-executed
                    
                    except Exception as e:
                        self.logger.error(f"[GateAction] Failed to auto-execute zLogout: {e}", exc_info=True)
                        await ws.send(safe_json_dumps({
                            "success": False,
                            "message": f"Logout failed: {str(e)}",
                            "_requestId": data.get("_requestId")
                        }))
                        return False
                
                # Check for zLogin (typically in onSubmit, but could be standalone)
                if 'zLogin' in item:
                    # zLogin typically needs form data, so it's not auto-executable
                    # unless it's being used in a special way
                    self.logger.debug(f"[GateAction] Found zLogin - typically needs form data, not auto-executing")
                    return False
                
                # Check for zFunc
                if 'zFunc' in item:
                    func_name = item['zFunc']
                    self.logger.info(f"[GateAction] Auto-executing zFunc: {func_name}")
                    
                    try:
                        # Execute via zParser
                        # Note: Mode is in session, context for request-scoped data only
                        context = {}
                        result = await asyncio.to_thread(
                            self.zcli.zparser.resolve_plugin_invocation,
                            func_name,
                            context=context
                        )
                        
                        self.logger.info(f"[GateAction] zFunc executed: {result}")
                        
                        # Resume generator
                        await self._resume_generator_after_gate(ws, data)
                        
                        return True
                    
                    except Exception as e:
                        self.logger.error(f"[GateAction] Failed to auto-execute zFunc: {e}", exc_info=True)
                        return False
                
                # Check for zLink (auto-executable for navigation)
                if 'zLink' in item:
                    link_target = item['zLink']
                    self.logger.info(f"[GateAction] Auto-executing zLink: {link_target}")
                    
                    try:
                        # Execute via zDispatch
                        from zOS.L2_Core.e_zDispatch import handle_zDispatch
                        
                        # Note: Mode is in session, context for request-scoped data only
                        context = {}
                        result = await asyncio.to_thread(
                            handle_zDispatch,
                            "zLink",
                            item,
                            zcli=self.zcli,
                            walker=self.walker,
                            context=context
                        )
                        
                        self.logger.info(f"[GateAction] zLink executed: {result}")
                        
                        # Resume generator
                        await self._resume_generator_after_gate(ws, data)
                        
                        return True
                    
                    except Exception as e:
                        self.logger.error(f"[GateAction] Failed to auto-execute zLink: {e}", exc_info=True)
                        return False
        
        # No auto-executable actions found
        return False
    
    def _get_event(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Get event field from message, supporting both 'event' and 'action' (deprecated).
        
        Args:
            data: Message data dictionary
            
        Returns:
            str: Event name, or None if not present
            
        Note:
            Prefers 'event' field over 'action' for forward compatibility.
            The 'action' field is deprecated as of v1.5.5.
        """
        return data.get(MSG_KEY_EVENT) or data.get(MSG_KEY_ACTION)
    
    async def _load_http_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load HTTP session data from session backend for WebSocket/HTTP session sync.
        
        This method bridges HTTP sessions (cookies) with WebSocket connections,
        enabling RBAC to work correctly across both protocols. It loads the
        authenticated session from Flask's session backend and returns the
        session data as a dictionary.
        
        Args:
            session_id: HTTP session ID from cookie
            
        Returns:
            Dict with session data (including zAuth context) or None if not found
            
        Raises:
            No exceptions - returns None on any error (fail-safe)
        """
        try:
            # Check if we have a Flask session interface
            if not hasattr(self.zcli, 'server') or not hasattr(self.zcli.server, 'app'):
                self.logger.debug("[MessageHandler] No Flask app found, cannot load HTTP session")
                return None
            
            flask_app = self.zcli.server.app
            
            # Import Flask session utilities
            from itsdangerous import URLSafeTimedSerializer, BadSignature
            from flask.sessions import SecureCookieSessionInterface
            
            # Create session interface
            session_interface = SecureCookieSessionInterface()
            
            # Deserialize the session cookie (Flask uses signed cookies)
            serializer = URLSafeTimedSerializer(
                flask_app.secret_key,
                salt='cookie-session',
                serializer=session_interface.serializer
            )
            
            try:
                # Decode the session cookie
                session_data = serializer.loads(session_id)
                self.logger.info(f"[MessageHandler] ✅ Successfully loaded HTTP session")
                return dict(session_data)
            except BadSignature:
                self.logger.warning(f"[MessageHandler] Invalid or expired session signature")
                return None
            except Exception as e:
                self.logger.error(f"[MessageHandler] Error deserializing session: {e}")
                return None
                
        except ImportError as e:
            self.logger.warning(f"[MessageHandler] Flask not available for session loading: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[MessageHandler] Unexpected error loading HTTP session: {e}")
            return None
    
    def _build_response(self, data: Dict[str, Any], **response_fields) -> str:
        """
        Build JSON response with _requestId echoed from request.
        
        Args:
            data: Original request data (may contain _requestId)
            **response_fields: Response fields (result, error, etc.)
            
        Returns:
            str: JSON-encoded response with _requestId if present in request
        """
        response = dict(response_fields)
        
        # Echo _requestId if present in request
        if "_requestId" in data:
            response["_requestId"] = data["_requestId"]
        
        return safe_json_dumps(response)
    
    async def _handle_dispatch(
        self,
        ws: Any,
        data: Dict[str, Any],
        broadcast_func: Callable[[str, Any], Awaitable[None]]
    ) -> bool:
        """
        Handle zDispatch command with cache support and user context isolation.
        
        This method executes zCLI commands via the zDispatch subsystem, with
        intelligent caching for read operations. Cache keys include user context
        (user_id, app_name, role, auth_context) to prevent data leaks.
        
        Args:
            ws: WebSocket connection object
            data: Message data containing zKey, zHorizontal, and parameters
            broadcast_func: Async function to broadcast results to other clients
            
        Returns:
            bool: Always True (command handled, even if it fails)
            
        Cache Behavior:
            - Read operations are cached with user context isolation
            - Cache can be disabled per-request with no_cache=true
            - TTL can be customized per-request with cache_ttl parameter
            - Cache hits are marked with _cached: true in response
        """
        zKey = data.get(MSG_KEY_ZKEY) or data.get(MSG_KEY_CMD)
        zHorizontal = data.get(MSG_KEY_ZHORIZONTAL) or zKey
        
        if not zKey:
            # No command, just broadcast
            await broadcast_func(safe_json_dumps(data), sender=ws)
            return True
        
        from zOS.L2_Core.e_zDispatch import handle_zDispatch
        
        # Check if cacheable
        is_cacheable = self._is_cacheable_operation(data, zKey)
        cache_ttl = data.get(MSG_KEY_CACHE_TTL, None)
        disable_cache = data.get(MSG_KEY_NO_CACHE, False)
        
        # Extract user context for caching (needed for both cache lookup and storage)
        user_context = None
        cache_key = None
        if is_cacheable and not disable_cache:
            user_context = self._extract_user_context(ws)
            cache_key = self.cache.generate_cache_key(data, user_context)
            cached_result = self.cache.get_query(cache_key)
            
            if cached_result is not None:
                # Cache hit!
                payload = self._build_response(data, result=cached_result, _cached=True)
                await ws.send(payload)
                await broadcast_func(payload, sender=ws)
                return True
        
        # Cache miss or not cacheable - execute query
        self.logger.debug(f"{LOG_PREFIX} {LOG_DISPATCH} {zKey}")
        
        try:
            # Note: Mode is in session, context for request-scoped data only
            context = {"websocket_data": data}
            
            result = await asyncio.to_thread(
                handle_zDispatch, zKey, zHorizontal,
                zcli=self.zcli, walker=self.walker, context=context
            )
            
            # Cache result if cacheable
            if is_cacheable and not disable_cache and cache_key:
                self.cache.cache_query(cache_key, result, ttl=cache_ttl, user_context=user_context)
            
            payload = self._build_response(data, result=result)
        
        # pylint: disable=broad-except
        # Reason: zDispatch can raise many exception types - need broad catch
        except Exception as exc:
            self.logger.error(f"{LOG_PREFIX} {LOG_ERROR} CLI execution error: {exc}")
            payload = self._build_response(data, error=str(exc))
        
        # Send result back
        await ws.send(payload)
        await broadcast_func(payload, sender=ws)
        
        return True
    
    def _is_cacheable_operation(self, data: Dict[str, Any], zKey: str) -> bool:
        """
        Check if operation is cacheable (read-only).
        
        Cacheable operations are read-only queries that can be safely cached
        without risking stale data in write scenarios.
        
        Args:
            data: Message data dictionary
            zKey: Command key string
            
        Returns:
            bool: True if operation is cacheable, False otherwise
            
        Cacheable Patterns:
            - event == "read"
            - zKey starts with "^List"
            - zKey starts with "^Get"
            - zKey starts with "^Search"
        """
        event = self._get_event(data)
        return (
            event == ACTION_READ or
            zKey.startswith(CMD_PREFIX_LIST) or
            zKey.startswith(CMD_PREFIX_GET) or
            zKey.startswith(CMD_PREFIX_SEARCH)
        )
    
    def _extract_user_context(self, ws: Any) -> Optional[Dict[str, Any]]:
        """
        Extract user context for secure cache isolation.
        
        This method retrieves authentication information from the WebSocket
        connection and formats it for cache key generation. The context includes
        user_id, app_name, role, and auth_context to ensure cache isolation
        between different users and applications.
        
        Args:
            ws: WebSocket connection object
            
        Returns:
            User context dictionary with keys:
                - user_id: Unique user identifier
                - app_name: Application name (for Layer 2/3 auth)
                - role: User role (e.g., "admin", "user", "guest")
                - auth_context: Authentication context ("zSession", "application", "dual")
            Returns None if no authentication info available (falls back to anonymous)
            
        Three-Tier Authentication Support:
            - zSession (Layer 1): Internal zCLI connections
            - Application (Layer 2): External application users
            - Dual (Layer 3): Both zSession and application authenticated
        """
        if not self.auth:
            return None
        
        auth_info = self.auth.get_client_info(ws)
        if not auth_info:
            return None
        
        # Extract auth context
        auth_context = auth_info.get("context", "none")
        app_name = auth_info.get("app_name", "default")
        
        # Determine which user data to use based on context
        if auth_context == _CONTEXT_DUAL:
            # Dual mode: Prefer application context for cache key
            user_data = auth_info.get("application") or auth_info.get("zSession")
        elif auth_context == _CONTEXT_APPLICATION:
            user_data = auth_info.get("application")
        elif auth_context == _CONTEXT_ZSESSION:
            user_data = auth_info.get("zSession")
        else:
            user_data = None
        
        if not user_data:
            return None
        
        return {
            "user_id": user_data.get("id", "unknown"),
            "app_name": app_name,
            "role": user_data.get("role", "guest"),
            "auth_context": auth_context
        }
