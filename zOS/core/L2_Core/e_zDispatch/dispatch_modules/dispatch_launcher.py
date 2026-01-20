# zCLI/subsystems/zDispatch/dispatch_modules/dispatch_launcher.py

"""
Command Launcher for zDispatch Subsystem.

This module provides the CommandLauncher class, which handles routing and execution
of commands within the zCLI framework. It acts as a central dispatcher for various
command types (string-based and dict-based), routing them to appropriate subsystem
handlers.

Architecture:
    The CommandLauncher follows a command routing pattern with two main pathways:
    
    1. String Commands:
       - Format: "zFunc(...)", "zLink(...)", "zOpen(...)", "zWizard(...)", "zRead(...)"
       - Parsed and routed to appropriate subsystem handlers
       - Special handling for plain strings in Bifrost mode (zUI resolution)
    
    2. Dict Commands:
       - Format: {"zFunc": ...}, {"zLink": ...}, {"zDelta": ...}, {"zDialog": ...}, etc.
       - Direct key-based routing to subsystem handlers
       - Support for CRUD operations and legacy zDisplay format
    
    Command Routing Flow:
        launch() -> Type Detection (str vs dict)
                |
        _launch_string() or _launch_dict()
                |
        Specific handler (_handle_wizard_string, _handle_read_dict, etc.)
                |
        Subsystem execution (zFunc, zNavigation, zOpen, zWizard, zData, etc.)

Mode-Specific Behavior:
    Terminal Mode:
        - Plain strings: Return None (no navigation)
        - zWizard: Returns "zBack" for navigation
        - zFunc/zOpen/zLink/zDelta: Returns subsystem result
    
    Bifrost Mode:
        - Plain strings: Resolve from zUI or return {"message": str}
        - zWizard: Returns zHat (actual result) for API consumption
        - zFunc/zOpen/zLink/zDelta: Returns subsystem result
        - Supports recursive resolution (zUI key -> dict with zFunc)

Forward Dependencies:
    This module integrates with 8 subsystems that will be refactored in future weeks:
    
    - zFunc (Week 6.10): Function execution and plugin invocation
    - zNavigation (Week 6.7): zLink handling (inter-file) and menu creation
    - zWalker: zDelta handling (intra-file block navigation)
    - zOpen (Week 6.12): File/URL opening
    - zWizard (Week 6.14): Multi-step workflow execution
    - zLoader (Week 6.9): zUI file loading and parsing
    - zParser (Week 6.8): Plugin invocation resolution
    - zData (Week 6.16): CRUD operations and data management
    - zDialog (Week 6.11): Interactive forms and user input

Plugin Support:
    Supports plugin invocations via "&" prefix in zFunc commands:
    - String: "zFunc(&my_plugin)"
    - Dict: {"zFunc": "&my_plugin"}
    - Resolved via zParser.resolve_plugin_invocation()

CRUD Detection:
    Smart fallback for generic CRUD operations that don't use zRead/zData wrappers:
    - Detects presence of CRUD keys: action, model, table, fields, values, etc.
    - Automatically routes to zData.handle_request()
    - Sets default action to "read" if not specified

Usage Examples:
    # String commands
    launcher.launch("zFunc(my_function)")
    launcher.launch("zLink(menu:users)")
    launcher.launch("zOpen(https://example.com)")
    launcher.launch("zWizard({'steps': [...]})")
    launcher.launch("zRead(users)")
    
    # Dict commands
    launcher.launch({"zFunc": "my_function"})
    launcher.launch({"zLink": "menu:users"})
    launcher.launch({"zDelta": "%Demo_Block"})
    launcher.launch({"zDialog": {"fields": [...]}})
    launcher.launch({"zRead": {"model": "users", "where": {"id": 1}}})
    launcher.launch({"zData": {"action": "create", "model": "users", "values": {...}}})
    
    # Generic CRUD (auto-detected)
    launcher.launch({"action": "read", "model": "users"})
    
    # Legacy zDisplay format (backward compatibility)
    launcher.launch({"zDisplay": {"event": "text", "content": "Hello"}})
    
    # Plain string in Bifrost mode (zUI resolution)
    launcher.launch("my_button_key", context={"mode": "zBifrost"})

Thread Safety:
    - Relies on thread-safe logger and display instances from zCLI
    - Mode detection reads from session context (context dict)
    - No internal state mutation during command execution

Integration with zSession:
    - Mode detection: Uses SESSION_KEY_ZMODE from context
    - Context passing: All handlers accept optional context parameter
    - Session access: Via self.zcli.session (centralized session management)

zAuth Integration:
    - Implicit via context: Authentication state passed through context dict
    - No direct zAuth calls: Command handlers are responsible for auth checks
    - Mode-specific returns: Bifrost mode may return different data structures

Constants:
    All magic strings are replaced with module constants to improve maintainability
    and reduce the risk of typos. See module-level constants below for complete list.
"""

from zOS import ast, Any, Optional, Dict, Union, List

# Import ACTION_PLACEHOLDER and SESSION_KEY_ZMODE from zConfig
from zOS.L1_Foundation.a_zConfig.zConfig_modules import ACTION_PLACEHOLDER, SESSION_KEY_ZMODE

# Import all dispatch constants from centralized location
from .dispatch_constants import (
    # Command Prefixes
    CMD_PREFIX_ZFUNC,
    CMD_PREFIX_ZLINK,
    CMD_PREFIX_ZOPEN,
    CMD_PREFIX_ZWIZARD,
    CMD_PREFIX_ZREAD,
    # Dict Keys - Subsystem Commands
    KEY_ZFUNC,
    KEY_ZLINK,
    KEY_ZDELTA,
    KEY_ZOPEN,
    KEY_ZWIZARD,
    KEY_ZREAD,
    KEY_ZDATA,
    KEY_ZDIALOG,
    KEY_ZDISPLAY,
    KEY_ZLOGIN,
    KEY_ZLOGOUT,
    # Dict Keys - Context & Session (KEY_MODE removed - using SESSION_KEY_ZMODE)
    KEY_ZVAFILE,
    KEY_ZBLOCK,
    # Mode Values
    MODE_BIFROST,
    MODE_TERMINAL,
    MODE_WALKER,
    # Display Labels (INTERNAL)
    _LABEL_LAUNCHER,
    _LABEL_HANDLE_ZFUNC,
    _LABEL_HANDLE_ZFUNC_DICT,
    _LABEL_HANDLE_ZLINK,
    _LABEL_HANDLE_ZDELTA,
    _LABEL_HANDLE_ZOPEN,
    _LABEL_HANDLE_ZWIZARD,
    _LABEL_HANDLE_ZREAD_STRING,
    _LABEL_HANDLE_ZREAD_DICT,
    _LABEL_HANDLE_ZDATA_DICT,
    _LABEL_HANDLE_CRUD_DICT,
    _LABEL_HANDLE_ZLOGIN,
    _LABEL_HANDLE_ZLOGOUT,
    # Display Event Keys (INTERNAL)
    _EVENT_TEXT,
    _EVENT_SYSMSG,
    _EVENT_HEADER,
    _EVENT_SUCCESS,
    _EVENT_ERROR,
    _EVENT_WARNING,
    _EVENT_INFO,
    _EVENT_LINE,
    _EVENT_LIST,
    # Data Keys
    KEY_ACTION,
    KEY_MODEL,
    KEY_TABLE,
    KEY_TABLES,
    KEY_FIELDS,
    KEY_VALUES,
    KEY_FILTERS,
    KEY_WHERE,
    KEY_ORDER_BY,
    KEY_LIMIT,
    KEY_OFFSET,
    KEY_CONTENT,
    KEY_INDENT,
    KEY_EVENT,
    KEY_LABEL,
    KEY_COLOR,
    KEY_STYLE,
    KEY_MESSAGE,
    # Default Values (INTERNAL)
    _DEFAULT_ACTION_READ,
    _DEFAULT_ZBLOCK,
    _DEFAULT_CONTENT,
    _DEFAULT_INDENT,
    _DEFAULT_INDENT_LAUNCHER,
    _DEFAULT_INDENT_HANDLER,
    _DEFAULT_STYLE_SINGLE,
    _DEFAULT_LABEL,
    # Navigation
    NAV_ZBACK,
    # Plugins
    PLUGIN_PREFIX,
)

# Import shared dispatch helpers
from .dispatch_helpers import is_bifrost_mode


class CommandLauncher:
    """
    Central command launcher for zDispatch subsystem.
    
    Routes string and dict commands to appropriate subsystem handlers, with mode-aware
    behavior for Terminal vs. Bifrost execution environments.
    
    Attributes:
        dispatch: Parent zDispatch instance
        zcli: Root zCLI instance
        logger: Logger instance from zCLI
        display: zDisplay instance for UI output
    
    Methods:
        launch(): Main entry point for command routing (type detection)
        _launch_string(): Route string-based commands (zFunc(), zLink(), etc.)
        _launch_dict(): Route dict-based commands ({zFunc:, zLink:, etc.})
        _handle_wizard_string(): Parse and execute wizard from string
        _handle_wizard_dict(): Execute wizard from dict
        _handle_read_string(): Handle zRead string -> zData
        _handle_read_dict(): Handle zRead dict -> zData
        _handle_data_dict(): Handle zData dict -> zData
        _handle_crud_dict(): Handle generic CRUD dict -> zData
        
        Helper methods (DRY):
        _display_handler(): Display handler label with consistent styling
        _log_detected(): Log detected command with consistent format
        _check_walker(): Validate walker instance for zLink commands
        _set_default_action(): Set default action for data requests
        
        Shared utilities (from dispatch_helpers):
        is_bifrost_mode(): Check if session is in Bifrost mode (no self, uses session dict)
    
    Integration:
        - zConfig: Uses session constants (TODO: SESSION_KEY_ZMODE)
        - zDisplay: UI output via zDeclare() and text()
        - zSession: Mode detection via context dict
        - Forward dependencies: 8 subsystems (see module docstring)
    """
    
    # Class-level type declarations
    dispatch: Any  # zDispatch instance
    zcli: Any  # zCLI instance
    logger: Any  # Logger instance
    display: Any  # zDisplay instance

    def __init__(self, dispatch: Any) -> None:
        """
        Initialize command launcher with parent dispatch instance.
        
        Args:
            dispatch: Parent zDispatch instance providing access to zCLI, logger, and display
        
        Raises:
            AttributeError: If dispatch is missing required attributes (zcli, logger)
        
        Example:
            launcher = CommandLauncher(dispatch)
        """
        self.dispatch = dispatch
        self.zcli = dispatch.zcli
        self.logger = dispatch.logger
        self.display = dispatch.zcli.display

    # ========================================================================
    # PUBLIC METHODS - Main Entry Points
    # ========================================================================

    def launch(
        self,
        zHorizontal: Union[str, Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        walker: Optional[Any] = None
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Launch appropriate handler for zHorizontal command with optional context and walker.
        
        This is the main entry point for command routing. It detects the type of command
        (string vs. dict) and delegates to the appropriate handler.
        
        Args:
            zHorizontal: Command to execute (string format like "zFunc(...)" or dict format)
            context: Optional context dict with mode, session, and other metadata
            walker: Optional walker instance for navigation commands (zLink, zWizard)
        
        Returns:
            Command execution result, or None if command type is unknown or execution fails.
            Return type varies by command:
            - zFunc: Function result (any type)
            - zLink: Navigation result (str or dict)
            - zWizard: "zBack" (Terminal) or zHat result (Bifrost)
            - zRead/zData: Data result (dict or list)
            - Plain string (Bifrost): {"message": str} or resolved zUI value
            - Unknown: None
        
        Examples:
            # String commands
            result = launcher.launch("zFunc(my_function)")
            result = launcher.launch("zLink(menu:users)", walker=walker_instance)
            result = launcher.launch("zRead(users)", context={"mode": "Terminal"})
            
            # Dict commands
            result = launcher.launch({"zFunc": "my_function"})
            result = launcher.launch({"zDialog": {"fields": [...]}})
            
            # Plain string in Bifrost mode
            result = launcher.launch("my_button_key", context={"mode": "zBifrost"})
        
        Notes:
            - Displays "zLauncher" label via zDeclare for visual feedback
            - Unknown command types (not str or dict) return None
            - Mode-specific behavior handled by individual command handlers
        """
        self._display_handler(_LABEL_LAUNCHER, _DEFAULT_INDENT_LAUNCHER)

        # Early return for placeholder actions (development/testing)
        if zHorizontal == ACTION_PLACEHOLDER:
            self.logger.debug(f"[CommandLauncher] Placeholder action detected: '{ACTION_PLACEHOLDER}' - no-op")
            return None

        if isinstance(zHorizontal, str):
            return self._launch_string(zHorizontal, context, walker)
        elif isinstance(zHorizontal, dict):
            return self._launch_dict(zHorizontal, context, walker)
        elif isinstance(zHorizontal, list):
            return self._launch_list(zHorizontal, context, walker)
        
        # Unknown type - return None
        return None

    # ========================================================================
    # PRIVATE METHODS - List Command Routing (Sequential Execution)
    # ========================================================================

    def _launch_list(
        self,
        zHorizontal: list,
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Execute a list of commands sequentially.
        
        This enables streamlined YAML where multiple zDisplay events (or other commands)
        can be listed directly under a key without requiring intermediate named sub-keys.
        
        Examples:
            # YAML Pattern - List of zDisplay events
            Hero_Section:
              - zDisplay:
                  event: header
                  content: "Zolo"
              - zDisplay:
                  event: header
                  content: "A digital solution"
              - zDisplay:
                  event: text
                  content: "Build intelligent CLI..."
        
        Args:
            zHorizontal: List of commands (dicts, strings, or nested lists)
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Result from the last item in the list, or None
        """
        if not zHorizontal:
            return None
        
        result = None
        for i, item in enumerate(zHorizontal):
            self.logger.framework.debug(f"[zCLI _launch_list] Processing item {i+1}/{len(zHorizontal)}: {type(item)}")
            # Recursively launch each item (supports dict, str, or nested list)
            if isinstance(item, dict):
                result = self._launch_dict(item, context, walker)
            elif isinstance(item, str):
                result = self._launch_string(item, context, walker)
            elif isinstance(item, list):
                result = self._launch_list(item, context, walker)
            
            # Check for navigation signals (stop processing if user wants to go back/exit)
            if result in ('zBack', 'exit', 'stop', 'error'):
                self.logger.framework.warning(f"[zCLI _launch_list] Stopping at item {i+1} due to signal: {result}")
                return result
            
            # Check for zLink navigation (stop processing and return to trigger navigation)
            if isinstance(result, dict) and 'zLink' in result:
                return result
        
        return result

    # ========================================================================
    # PRIVATE METHODS - String Command Routing
    # ========================================================================

    def _launch_string(
        self,
        zHorizontal: str,
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Handle string-based launch commands (ORCHESTRATOR).
        
        Routes string commands based on prefix or mode-specific handling.
        This method has been streamlined for better maintainability.
        
        Command prefixes:
        - zFunc(...): Function execution
        - zLink(...): Navigation link
        - zOpen(...): File/URL opening
        - zWizard(...): Multi-step workflow
        - zRead(...): Data read operation
        
        Plain strings (no prefix):
        - Terminal: Return None (display-only)
        - Bifrost: Resolve from zUI or return {"message": str}
        
        Args:
            zHorizontal: String command to execute
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Command execution result or None
        
        Examples:
            result = _launch_string("zFunc(calculate)", context, walker)
            result = _launch_string("zLink(menu:users)", context, walker)
            result = _launch_string("submit_button", bifrost_context, walker)
        
        Notes:
            - Refactored from 106 lines → 40 lines (62% reduction)
            - Bifrost plain string resolution extracted to helper
            - Walker validation for navigation commands
            - Mode-specific plain string handling
        """
        # Prefix-based routing (5 command types)
        if zHorizontal.startswith(CMD_PREFIX_ZFUNC):
            self._log_detected("zFunc request")
            self._display_handler(_LABEL_HANDLE_ZFUNC, _DEFAULT_INDENT_HANDLER)
            return self.zcli.zfunc.handle(zHorizontal)

        if zHorizontal.startswith(CMD_PREFIX_ZLINK):
            if not self._check_walker(walker, "zLink"):
                return None
            self._log_detected("zLink request")
            self._display_handler(_LABEL_HANDLE_ZLINK, _DEFAULT_INDENT_LAUNCHER)
            return self.zcli.navigation.handle_zLink(zHorizontal, walker=walker)

        if zHorizontal.startswith(CMD_PREFIX_ZOPEN):
            self._log_detected("zOpen request")
            self._display_handler(_LABEL_HANDLE_ZOPEN, _DEFAULT_INDENT_LAUNCHER)
            return self.zcli.open.handle(zHorizontal)

        if zHorizontal.startswith(CMD_PREFIX_ZWIZARD):
            return self._handle_wizard_string(zHorizontal, walker, context)

        if zHorizontal.startswith(CMD_PREFIX_ZREAD):
            return self._handle_read_string(zHorizontal, context)

        # Plain string - mode-specific handling
        if is_bifrost_mode(self.zcli.session):
            return self._resolve_plain_string_in_bifrost(zHorizontal, context, walker)
        
        # Terminal mode: Plain strings are displayed but return None
        return None

    # ========================================================================
    # STRING ROUTING HELPERS - Decomposed from _launch_string()
    # ========================================================================

    def _resolve_plain_string_in_bifrost(
        self,
        zHorizontal: str,
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Union[Dict[str, Any], Any]:
        """
        Resolve plain string in Bifrost mode (attempts zUI resolution).
        
        Args:
            zHorizontal: Plain string key
            context: Context dict
            walker: Optional walker instance
        
        Returns:
            Resolved value (recursively launched) or {"message": str}
        
        Notes:
            - Attempts to resolve key from current zUI block
            - Recursively launches resolved value (could be dict with zFunc)
            - Falls back to {"message": str} if resolution fails
            - Error handling for missing zUI context
        """
        zVaFile = self.zcli.zspark_obj.get(KEY_ZVAFILE)
        zBlock = self.zcli.zspark_obj.get(KEY_ZBLOCK, _DEFAULT_ZBLOCK)
        
        if zVaFile and zBlock:
            try:
                raw_zFile = self.zcli.loader.handle(zVaFile)
                if raw_zFile and zBlock in raw_zFile:
                    block_dict = raw_zFile[zBlock]
                    
                    # Look up the key in the block
                    if zHorizontal in block_dict:
                        resolved_value = block_dict[zHorizontal]
                        self.logger.framework.debug(
                            f"[{MODE_BIFROST}] Resolved key '{zHorizontal}' from zUI to: {resolved_value}"
                        )
                        # Recursively launch with the resolved value
                        return self.launch(resolved_value, context=context, walker=walker)
                    else:
                        self.logger.framework.debug(
                            f"[{MODE_BIFROST}] Key '{zHorizontal}' not found in zUI block '{zBlock}'"
                        )
            except Exception as e:
                self.logger.warning(f"[{MODE_BIFROST}] Error resolving key from zUI: {e}")
        
        # If we couldn't resolve it, return as display message
        self.logger.framework.debug(f"Plain string in {MODE_BIFROST} mode - returning as message")
        return {KEY_MESSAGE: zHorizontal}

    # ========================================================================
    # PRIVATE METHODS - Dict Command Routing
    # ========================================================================

    def _launch_dict(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Handle dict-based launch commands (ORCHESTRATOR).
        
        Routes dict commands to appropriate subsystem handlers. This method
        has been decomposed into focused helpers for maintainability.
        
        Routing priority:
        1. Content wrapper unwrapping (single "Content" key)
        2. Block-level data resolution (_data block)
        3. Organizational structure detection (nested dicts/lists)
        4. Implicit wizard detection (multiple content keys)
        5. Explicit subsystem routing (zFunc, zDialog, zLink, etc.)
        6. CRUD fallback (action/model/table keys)
        
        Args:
            zHorizontal: Dict command to execute
            context: Optional context dict with mode and session metadata
            walker: Optional walker instance for navigation commands
        
        Returns:
            Command execution result, or None if command is unhandled.
            Return type varies by command (see launch() docstring).
        
        Examples:
            result = _launch_dict({"zFunc": "calculate"}, context, walker)
            result = _launch_dict({"zDialog": {"fields": [...]}}, context, walker)
            result = _launch_dict({"action": "read", "model": "users"}, context, walker)
        
        Notes:
            - Decomposed from 423 lines → 60 lines (86% reduction)
            - 14 routing helpers extracted for focused logic
            - Maintains backward compatibility with all command formats
        """
        # ========================================================================
        # PRELIMINARY CHECKS
        # ========================================================================
        subsystem_keys = {KEY_ZDISPLAY, KEY_ZFUNC, KEY_ZDIALOG, KEY_ZLINK, KEY_ZWIZARD, KEY_ZREAD, KEY_ZDATA}
        content_keys = [k for k in zHorizontal.keys() if not k.startswith('_')]
        is_subsystem_call = any(k in zHorizontal for k in subsystem_keys)
        crud_keys = {'action', 'model', 'table', 'collection'}
        is_crud_call = any(k in zHorizontal for k in crud_keys)
        
        # ========================================================================
        # CONTENT WRAPPER UNWRAPPING
        # ========================================================================
        result = self._unwrap_content_wrapper(zHorizontal, content_keys, context, walker)
        if result is not None or (len(content_keys) == 1 and content_keys[0] == 'Content'):
            return result
        
        # ========================================================================
        # BLOCK-LEVEL DATA RESOLUTION
        # ========================================================================
        if context is not None:  # Only resolve if context exists
            self._resolve_data_block_if_present(zHorizontal, is_subsystem_call, context)
        
        # ========================================================================
        # SHORTHAND SYNTAX EXPANSION (zH1-zH6, zText, zUL, zOL, zTable, zMD, zImage, zURL)
        # ========================================================================
        # Check if this is a shorthand display event BEFORE wizard/organizational detection
        # This ensures zImage/zText/zUL/etc don't get misinterpreted as wizards or organizational structures
        
        # FIRST: Check for PLURAL shorthands at top level (zURLs, zTexts, etc.)
        # This handles the case where dispatch is called directly: dispatch.handle('zUL', {'zURLs': {...}})
        plural_shorthands = ['zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs']
        found_plural_at_top = None
        for plural_key in plural_shorthands:
            if plural_key in zHorizontal and isinstance(zHorizontal[plural_key], dict):
                found_plural_at_top = plural_key
                break
        
        if found_plural_at_top:
            # Plural shorthand detected at top level: expand to implicit wizard with semantic keys
            self.logger.debug(f"[Shorthand] Found plural at top level: {found_plural_at_top}")
            plural_items = zHorizontal[found_plural_at_top]
            expanded_wizard = {}
            singular_event = None
            
            # Determine event type from plural key
            if found_plural_at_top == 'zURLs':
                singular_event = 'zURL'
            elif found_plural_at_top == 'zTexts':
                singular_event = 'text'
            elif found_plural_at_top == 'zImages':
                singular_event = 'image'
            elif found_plural_at_top == 'zMDs':
                singular_event = 'rich_text'
            elif found_plural_at_top.startswith('zH') and found_plural_at_top.endswith('s'):
                # zH1s, zH2s, etc.
                indent_level = int(found_plural_at_top[2])
                if 1 <= indent_level <= 6:
                    singular_event = ('header', indent_level)
            
            if singular_event:
                for item_key, item_params in plural_items.items():
                    if isinstance(item_params, dict):
                        if isinstance(singular_event, tuple):
                            # Header event with indent level
                            event_type, indent = singular_event
                            expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': event_type, 'indent': indent, **item_params}}
                        else:
                            expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': singular_event, **item_params}}
                
                if expanded_wizard:
                    # Apply _zClass to each item if present
                    if '_zClass' in zHorizontal:
                        for item_key in expanded_wizard:
                            if KEY_ZDISPLAY in expanded_wizard[item_key]:
                                expanded_wizard[item_key][KEY_ZDISPLAY]['_zClass'] = zHorizontal['_zClass']
                    
                    self.logger.debug(f"[Shorthand] Expanded {found_plural_at_top} to {len(expanded_wizard)} wizard steps")
                    zHorizontal = expanded_wizard
                    is_subsystem_call = False
        
        # SECOND & THIRD: Shorthand expansion (Terminal mode only)
        # In Bifrost mode, skip shorthand expansion - let raw structure pass through to client
        if not is_bifrost_mode(self.zcli.session):
            # DEBUG: Log start of shorthand expansion
            self.logger.debug(f"[Shorthand] Starting expansion for zHorizontal keys: {list(zHorizontal.keys())}")
            
            # SECOND: Pre-check - Skip shorthand loop if multiple UI event keys (implicit sequence)
            # Note: zCrumbs is NOT counted as a UI event for implicit sequences - it's a standalone directive
            non_meta_keys = [k for k in zHorizontal.keys() if not k.startswith('_')]
            ui_event_count = 0
            for key in non_meta_keys:
                if key.startswith('zH') and len(key) == 3 and key[2].isdigit():
                    ui_event_count += 1
                elif key in ['zText', 'zMD', 'zImage', 'zURL']:
                    ui_event_count += 1
        
            # Skip shorthand loop if ALL keys are UI events (let organizational handler process as sequence)
            skip_shorthand_loop = (ui_event_count >= 2 and ui_event_count == len(non_meta_keys))
        
            # THIRD: Check for regular shorthand keys (zUL, zOL, zImage, zText, etc.)
            for key in list(zHorizontal.keys()):
                # DEBUG: Log which key we're checking
                self.logger.debug(f"[Shorthand] Checking key: {key}, skip_shorthand_loop={skip_shorthand_loop}")
                
                # Skip UI event keys if implicit sequence detected (let it fall through to organizational handler)
                # EXCEPT for zCrumbs, which is always processed (standalone directive)
                if skip_shorthand_loop:
                    # Strip __dup{N} suffix when checking (LSP duplicate key handling)
                    clean_key_check = key.split('__dup')[0] if '__dup' in key else key
                    is_ui_event = (
                        (clean_key_check.startswith('zH') and len(clean_key_check) == 3 and clean_key_check[2].isdigit()) or
                        clean_key_check in ['zText', 'zMD', 'zImage', 'zURL']
                    )
                    if is_ui_event:
                        continue
            
                # Check if there are non-UI-event siblings (organizational containers)
                # If yes, expand in-place to preserve them
                # ALSO check if ALL keys are UI events (pure implicit sequence)
                # Note: zCrumbs is NOT counted as a UI event - it's a standalone directive
                has_organizational_siblings = False
                all_siblings_are_ui_events = True
                for sibling_key in non_meta_keys:
                    # Strip __dup{N} suffix when checking (LSP duplicate key handling)
                    clean_sibling_key = sibling_key.split('__dup')[0] if '__dup' in sibling_key else sibling_key
                    is_sibling_ui_event = (
                        (clean_sibling_key.startswith('zH') and len(clean_sibling_key) == 3 and clean_sibling_key[2].isdigit()) or
                        clean_sibling_key in ['zText', 'zMD', 'zImage', 'zURL', 'zUL', 'zOL', 'zTable']
                    )
                    if not is_sibling_ui_event:
                        has_organizational_siblings = True
                        all_siblings_are_ui_events = False
                        break
                
                # If ALL siblings are UI events (pure implicit sequence), SKIP early expansion
                # Let _handle_organizational_structure handle the full sequence
                if all_siblings_are_ui_events and len(non_meta_keys) >= 2:
                    continue  # Skip this key, don't expand it here
            
                # Strip __dup{N} suffix when checking (LSP duplicate key handling)
                clean_key = key.split('__dup')[0] if '__dup' in key else key
                
                if clean_key.startswith('zH') and len(clean_key) == 3 and clean_key[2].isdigit():
                    indent_level = int(clean_key[2])
                    if 1 <= indent_level <= 6:
                        # Extract the header parameters
                        header_params = zHorizontal[key]
                        if isinstance(header_params, dict):
                            if has_organizational_siblings:
                                # Expand in-place to preserve organizational siblings
                                zHorizontal[key] = {
                                    KEY_ZDISPLAY: {
                                        'event': 'header',
                                        'indent': indent_level,
                                        **header_params
                                    }
                                }
                                # Continue to next key (don't break)
                            else:
                                # Replace entire dict (single UI event, no siblings)
                                zHorizontal = {
                                    KEY_ZDISPLAY: {
                                        'event': 'header',
                                        'indent': indent_level,
                                        **header_params
                                    }
                                }
                                # Mark as subsystem call to skip other detection
                                is_subsystem_call = True
                                break
                elif clean_key == 'zText':
                    # Extract the text parameters
                    # Handle both regular and suffixed keys (LSP duplicate strategy)
                    text_params = zHorizontal[key]
                    if isinstance(text_params, dict):
                        if has_organizational_siblings:
                            # Expand in-place to preserve organizational siblings
                            zHorizontal[key] = {
                                KEY_ZDISPLAY: {
                                    'event': 'text',
                                    **text_params
                                }
                            }
                            # Continue to next key
                        else:
                            # Replace entire dict (single UI event, no siblings)
                            zHorizontal = {
                                KEY_ZDISPLAY: {
                                    'event': 'text',
                                    **text_params
                                }
                            }
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                elif clean_key == 'zUL':
                    # Unordered list (bullet style)
                    list_params = zHorizontal[key]
                    if isinstance(list_params, dict):
                        # NEW: Check for plural shorthand (zURLs, zTexts, zH1s-zH6s, zImages, zMDs)
                        # This is more DRY than items list for homogeneous lists
                        plural_shorthands = ['zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs']
                        found_plural = None
                        for plural_key in plural_shorthands:
                            if plural_key in list_params:
                                found_plural = plural_key
                                break
                    
                        if found_plural:
                            # Plural shorthand detected: expand to implicit wizard with semantic keys
                            plural_items = list_params[found_plural]
                            if isinstance(plural_items, dict):
                                expanded_wizard = {}
                                singular_event = None
                            
                                # Determine event type from plural key
                                if found_plural == 'zURLs':
                                    singular_event = 'zURL'
                                elif found_plural == 'zTexts':
                                    singular_event = 'text'
                                elif found_plural == 'zImages':
                                    singular_event = 'image'
                                elif found_plural == 'zMDs':
                                    singular_event = 'rich_text'
                                elif found_plural.startswith('zH') and found_plural.endswith('s'):
                                    # zH1s, zH2s, etc.
                                    indent_level = int(found_plural[2])
                                    if 1 <= indent_level <= 6:
                                        singular_event = ('header', indent_level)
                            
                                if singular_event:
                                    for item_key, item_params in plural_items.items():
                                        if isinstance(item_params, dict):
                                            if isinstance(singular_event, tuple):
                                                # Header event with indent level
                                                event_type, indent = singular_event
                                                expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': event_type, 'indent': indent, **item_params}}
                                            else:
                                                expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': singular_event, **item_params}}
                                
                                    if expanded_wizard:
                                        # Apply _zClass to each item if present
                                        if '_zClass' in list_params:
                                            for item_key in expanded_wizard:
                                                if KEY_ZDISPLAY in expanded_wizard[item_key]:
                                                    expanded_wizard[item_key][KEY_ZDISPLAY]['_zClass'] = list_params['_zClass']
                                    
                                        zHorizontal = expanded_wizard
                                        # Will be treated as implicit wizard (multiple keys)
                                        is_subsystem_call = False
                                        break
                    
                        # Check if items contain shorthands (zURL, zImage, etc.)
                        items = list_params.get('items', [])
                        has_shorthands = any(
                            isinstance(item, dict) and len(item) == 1 and 
                            list(item.keys())[0] in ['zURL', 'zImage', 'zText', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6']
                            for item in items if isinstance(item, dict)
                        )
                    
                        if has_shorthands:
                            # Items contain shorthands: expand to implicit wizard
                            expanded_wizard = {}
                            for idx, item in enumerate(items):
                                if isinstance(item, dict) and len(item) == 1:
                                    shorthand_key = list(item.keys())[0]
                                    shorthand_value = item[shorthand_key]
                                    if shorthand_key == 'zURL':
                                        expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'zURL', **shorthand_value}}
                                    elif shorthand_key == 'zImage':
                                        expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'image', **shorthand_value}}
                                    elif shorthand_key == 'zText':
                                        expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'text', **shorthand_value}}
                                    elif shorthand_key.startswith('zH') and len(shorthand_key) == 3 and shorthand_key[2].isdigit():
                                        indent_level = int(shorthand_key[2])
                                        if 1 <= indent_level <= 6:
                                            expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **shorthand_value}}
                        
                            if expanded_wizard:
                                # Store _zClass in wizard context for styling (if needed)
                                if '_zClass' in list_params:
                                    for item_key in expanded_wizard:
                                        # Apply _zClass to each item's zDisplay
                                        if KEY_ZDISPLAY in expanded_wizard[item_key]:
                                            expanded_wizard[item_key][KEY_ZDISPLAY]['_zClass'] = list_params['_zClass']
                            
                                zHorizontal = expanded_wizard
                                # Will be treated as implicit wizard (multiple keys)
                                is_subsystem_call = False
                                break
                        else:
                            # Items are simple text: use normal list display
                            zHorizontal = {
                                KEY_ZDISPLAY: {
                                    'event': 'list',
                                    'style': 'bullet',
                                    **list_params
                                }
                            }
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                elif clean_key == 'zOL':
                    # Ordered list (numbered style)
                    list_params = zHorizontal[key]
                    if isinstance(list_params, dict):
                        # NEW: Check for plural shorthand (zURLs, zTexts, zH1s-zH6s, zImages, zMDs)
                        # This is more DRY than items list for homogeneous lists
                        plural_shorthands = ['zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs']
                        found_plural = None
                        for plural_key in plural_shorthands:
                            if plural_key in list_params:
                                found_plural = plural_key
                                break
                    
                        if found_plural:
                            # Plural shorthand detected: expand to implicit wizard with semantic keys
                            plural_items = list_params[found_plural]
                            if isinstance(plural_items, dict):
                                expanded_wizard = {}
                                singular_event = None
                            
                                # Determine event type from plural key
                                if found_plural == 'zURLs':
                                    singular_event = 'zURL'
                                elif found_plural == 'zTexts':
                                    singular_event = 'text'
                                elif found_plural == 'zImages':
                                    singular_event = 'image'
                                elif found_plural == 'zMDs':
                                    singular_event = 'rich_text'
                                elif found_plural.startswith('zH') and found_plural.endswith('s'):
                                    # zH1s, zH2s, etc.
                                    indent_level = int(found_plural[2])
                                    if 1 <= indent_level <= 6:
                                        singular_event = ('header', indent_level)
                            
                                if singular_event:
                                    for item_key, item_params in plural_items.items():
                                        if isinstance(item_params, dict):
                                            if isinstance(singular_event, tuple):
                                                # Header event with indent level
                                                event_type, indent = singular_event
                                                expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': event_type, 'indent': indent, **item_params}}
                                            else:
                                                expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': singular_event, **item_params}}
                                
                                    if expanded_wizard:
                                        # Apply _zClass to each item if present
                                        if '_zClass' in list_params:
                                            for item_key in expanded_wizard:
                                                if KEY_ZDISPLAY in expanded_wizard[item_key]:
                                                    expanded_wizard[item_key][KEY_ZDISPLAY]['_zClass'] = list_params['_zClass']
                                    
                                        zHorizontal = expanded_wizard
                                        # Will be treated as implicit wizard (multiple keys)
                                        is_subsystem_call = False
                                        break
                    
                        # Check if items contain shorthands (zURL, zImage, etc.)
                        items = list_params.get('items', [])
                        has_shorthands = any(
                            isinstance(item, dict) and len(item) == 1 and 
                            list(item.keys())[0] in ['zURL', 'zImage', 'zText', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6']
                            for item in items if isinstance(item, dict)
                        )
                    
                        if has_shorthands:
                            # Items contain shorthands: expand to implicit wizard
                            expanded_wizard = {}
                            for idx, item in enumerate(items):
                                if isinstance(item, dict) and len(item) == 1:
                                    shorthand_key = list(item.keys())[0]
                                    shorthand_value = item[shorthand_key]
                                    if shorthand_key == 'zURL':
                                        expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'zURL', **shorthand_value}}
                                    elif shorthand_key == 'zImage':
                                        expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'image', **shorthand_value}}
                                    elif shorthand_key == 'zText':
                                        expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'text', **shorthand_value}}
                                    elif shorthand_key.startswith('zH') and len(shorthand_key) == 3 and shorthand_key[2].isdigit():
                                        indent_level = int(shorthand_key[2])
                                        if 1 <= indent_level <= 6:
                                            expanded_wizard[f"item_{idx}"] = {KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **shorthand_value}}
                        
                            if expanded_wizard:
                                # Store _zClass in wizard context for styling (if needed)
                                if '_zClass' in list_params:
                                    for item_key in expanded_wizard:
                                        # Apply _zClass to each item's zDisplay
                                        if KEY_ZDISPLAY in expanded_wizard[item_key]:
                                            expanded_wizard[item_key][KEY_ZDISPLAY]['_zClass'] = list_params['_zClass']
                            
                                zHorizontal = expanded_wizard
                                # Will be treated as implicit wizard (multiple keys)
                                is_subsystem_call = False
                                break
                        else:
                            # Items are simple text: use normal list display
                            zHorizontal = {
                                KEY_ZDISPLAY: {
                                    'event': 'list',
                                    'style': 'number',
                                    **list_params
                                }
                            }
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                elif clean_key == 'zTable':
                    # Table display
                    table_params = zHorizontal[key]
                    if isinstance(table_params, dict):
                        # Transform to full zDisplay format
                        zHorizontal = {
                            KEY_ZDISPLAY: {
                                'event': 'zTable',
                                **table_params
                            }
                        }
                        # Mark as subsystem call to skip other detection
                        is_subsystem_call = True
                        break
                elif clean_key == 'zMD':
                    # Rich text / Markdown
                    md_params = zHorizontal[key]
                    if isinstance(md_params, dict):
                        if has_organizational_siblings:
                            # Expand in-place to preserve organizational siblings
                            zHorizontal[key] = {
                                KEY_ZDISPLAY: {
                                    'event': 'rich_text',
                                    **md_params
                                }
                            }
                            # Continue to next key
                        else:
                            # Replace entire dict (single UI event, no siblings)
                            zHorizontal = {
                                KEY_ZDISPLAY: {
                                    'event': 'rich_text',
                                    **md_params
                                }
                            }
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                elif clean_key == 'zCrumbs':
                    # Breadcrumb navigation shorthand
                    crumbs_params = zHorizontal[key]
                    self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Detected zCrumbs key with value: {crumbs_params}")
                    if isinstance(crumbs_params, dict):
                        # Check for 'show' parameter
                        if 'show' in crumbs_params:
                            show_value = crumbs_params.get('show', False)
                            if show_value is True or (isinstance(show_value, str) and show_value.lower() == 'true'):
                                # Pass through all params except 'show'
                                params_without_show = {k: v for k, v in crumbs_params.items() if k != 'show'}
                                if has_organizational_siblings:
                                    # Expand in-place to preserve organizational siblings
                                    zHorizontal[key] = {
                                        KEY_ZDISPLAY: {
                                            'event': 'zCrumbs',
                                            **params_without_show
                                        }
                                    }
                                    self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Expanded (in-place) to: {zHorizontal[key]}")
                                    # Continue to next key
                                else:
                                    # Replace entire dict (single directive, no siblings)
                                    zHorizontal = {
                                        KEY_ZDISPLAY: {
                                            'event': 'zCrumbs',
                                            **params_without_show
                                        }
                                    }
                                    self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Expanded (replace) to: {zHorizontal}")
                                    # Mark as subsystem call to skip other detection
                                    is_subsystem_call = True
                                    break
                            else:
                                # show: false - skip this key
                                self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] show=false, skipping")
                                continue
                        else:
                            # Missing 'show' parameter - skip this key
                            self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Missing 'show' parameter, skipping")
                            continue
                elif clean_key == 'zImage':
                    # Image display
                    image_params = zHorizontal[key]
                    if isinstance(image_params, dict):
                        if has_organizational_siblings:
                            # Expand in-place to preserve organizational siblings
                            zHorizontal[key] = {
                                KEY_ZDISPLAY: {
                                    'event': 'image',
                                    **image_params
                                }
                            }
                            # Continue to next key
                        else:
                            # Replace entire dict (single UI event, no siblings)
                            zHorizontal = {
                                KEY_ZDISPLAY: {
                                    'event': 'image',
                                    **image_params
                                }
                            }
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                elif clean_key == 'zURL':
                    # URL/Link display
                    url_params = zHorizontal[key]
                    if isinstance(url_params, dict):
                        # Single link: {zURL: {label: ..., href: ...}}
                        if has_organizational_siblings:
                            # Expand in-place to preserve organizational siblings
                            zHorizontal[key] = {
                                KEY_ZDISPLAY: {
                                    'event': 'zURL',
                                    **url_params
                                }
                            }
                            # Continue to next key
                        else:
                            # Replace entire dict (single UI event, no siblings)
                            zHorizontal = {
                                KEY_ZDISPLAY: {
                                    'event': 'zURL',
                                    **url_params
                                }
                            }
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                    elif isinstance(url_params, list):
                        # Multiple links: {zURL: [{label: ..., href: ...}, {...}]}
                        # This becomes an implicit wizard with multiple steps
                        expanded_links = {}
                        for idx, link_params in enumerate(url_params):
                            if isinstance(link_params, dict):
                                expanded_links[f"zURL_{idx}"] = [{KEY_ZDISPLAY: {'event': 'zURL', **link_params}}]
                        if expanded_links:
                            if has_organizational_siblings:
                                # Expand in-place
                                zHorizontal[key] = expanded_links
                                # Continue to next key
                            else:
                                # Replace entire dict
                                zHorizontal = expanded_links
                                # Will be treated as implicit wizard (multiple keys)
                                is_subsystem_call = False
                                break
                elif clean_key == 'zCrumbs':
                    # Breadcrumb display shorthand with explicit show property
                    # Supports:
                    #   zCrumbs: {show: true}                             → Session-based breadcrumbs
                    #   zCrumbs: {show: true, parent: "zProducts.zTheme"} → Declarative breadcrumbs (Phase 1)
                    #   zCrumbs: {show: false}                            → Suppressed (no display)
                    crumbs_value = zHorizontal[key]
                    
                    # Only expand if show is explicitly true
                    should_expand = False
                    zdisplay_params = {'event': 'zCrumbs'}
                    
                    if isinstance(crumbs_value, dict):
                        show_value = crumbs_value.get('show', False)
                        if show_value is True or (isinstance(show_value, str) and show_value.lower() == 'true'):
                            should_expand = True
                            # Pass through all params except 'show' (e.g., parent, session_data)
                            # This enables: zCrumbs: {show: true, parent: "zProducts.zTheme"}
                            params_without_show = {k: v for k, v in crumbs_value.items() if k != 'show'}
                            zdisplay_params.update(params_without_show)
                    
                    # NOTE: We don't explicitly pass session_data
                    # The zCrumbs display event auto-injects session if None (Phase 1 enhancement)
                    
                    if should_expand:
                        # Expand to zDisplay event
                        if has_organizational_siblings:
                            # Expand in-place to preserve organizational siblings
                            zHorizontal[key] = {KEY_ZDISPLAY: zdisplay_params}
                            # Continue to next key
                        else:
                            # Replace entire dict (single UI event, no siblings)
                            zHorizontal = {KEY_ZDISPLAY: zdisplay_params}
                            # Mark as subsystem call to skip other detection
                            is_subsystem_call = True
                            break
                    else:
                        # show: false or missing show property → skip this key (don't display)
                        continue
        
            # Recalculate content_keys and subsystem check after shorthand expansion (Terminal mode)
            content_keys = [k for k in zHorizontal.keys() if not k.startswith('_')]
            is_subsystem_call = any(k in zHorizontal for k in subsystem_keys) or is_subsystem_call
        # End of Terminal mode shorthand expansion
        
        # Ensure content_keys is always up-to-date (for both Terminal and Bifrost modes)
        content_keys = [k for k in zHorizontal.keys() if not k.startswith('_')]
        
        # ========================================================================
        # ORGANIZATIONAL STRUCTURE DETECTION (mutually exclusive with wizard)
        # ========================================================================
        if not is_subsystem_call and not is_crud_call and len(content_keys) > 0:
            result = self._handle_organizational_structure(zHorizontal, content_keys, context, walker)
            # If organizational structure was detected and processed, return immediately
            # (even if result is None) to prevent fallthrough to implicit wizard
            if result is not None:
                return result
            
            # Check if organizational structure was detected (all keys are nested)
            all_nested = all(
                isinstance(zHorizontal[k], (dict, list))
                for k in content_keys
            )
            if all_nested:
                # Organizational structure was processed, don't fall through to wizard
                return result
        
        # ========================================================================
        # IMPLICIT WIZARD DETECTION
        # ========================================================================
        # Run after shorthand expansion so zImage/zText/etc are already converted
        if not is_subsystem_call and not is_crud_call and len(content_keys) > 1:
            return self._handle_implicit_wizard(zHorizontal, walker)
        
        # ========================================================================
        # EXPLICIT SUBSYSTEM ROUTING
        # ========================================================================
        if KEY_ZDISPLAY in zHorizontal:
            return self._route_zdisplay(zHorizontal, context)
        if KEY_ZFUNC in zHorizontal:
            return self._route_zfunc(zHorizontal, context)
        if KEY_ZDIALOG in zHorizontal:
            return self._route_zdialog(zHorizontal, context, walker)
        if KEY_ZLOGIN in zHorizontal:
            return self._route_zlogin(zHorizontal, context)
        if KEY_ZLOGOUT in zHorizontal:
            return self._route_zlogout(zHorizontal)
        if KEY_ZLINK in zHorizontal:
            return self._route_zlink(zHorizontal, walker)
        if KEY_ZDELTA in zHorizontal:
            return self._route_zdelta(zHorizontal, walker)
        if KEY_ZWIZARD in zHorizontal:
            return self._handle_wizard_dict(zHorizontal, walker, context)
        if KEY_ZREAD in zHorizontal:
            return self._handle_read_dict(zHorizontal, context)
        if KEY_ZDATA in zHorizontal:
            return self._handle_data_dict(zHorizontal, context)
        
        # ========================================================================
        # CRUD FALLBACK
        # ========================================================================
        crud_detection_keys = {
            KEY_ACTION, KEY_TABLE, KEY_MODEL, KEY_FIELDS, KEY_VALUES, KEY_WHERE
        }
        if any(key in zHorizontal for key in crud_detection_keys):
            return self._handle_crud_dict(zHorizontal, context)
        
        # No recognized keys found
        self.logger.framework.debug("[zCLI Launcher] No recognized keys found, returning None")
        return None

    # ========================================================================
    # PRIVATE METHODS - Specialized Command Handlers
    # ========================================================================

    def _handle_wizard_string(
        self,
        zHorizontal: str,
        walker: Optional[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Union[str, Any]]:
        """
        Handle zWizard string command.
        
        Parses the wizard payload from string format and executes it via walker or
        wizard subsystem. Returns mode-specific results (zBack for Terminal, zHat for Bifrost).
        
        Args:
            zHorizontal: String command in format "zWizard(...)"
            walker: Optional walker instance (preferred for navigation context)
            context: Optional context dict with mode metadata
        
        Returns:
            - Bifrost mode: zHat (actual wizard result)
            - Terminal/Walker mode: "zBack" (for navigation) or zHat (no walker)
            - Parse error: None
        
        Example:
            result = _handle_wizard_string("zWizard({'steps': [...])})", walker, context)
        
        Notes:
            - Uses ast.literal_eval() for safe payload parsing
            - Walker extends wizard, so walker.handle() is preferred over wizard.handle()
            - Mode-specific returns enable proper Terminal vs. API behavior
        """
        self._log_detected("zWizard request")
        self._display_handler(_LABEL_HANDLE_ZWIZARD, _DEFAULT_INDENT_LAUNCHER)
        
        # Extract and parse payload
        inner = zHorizontal[len(CMD_PREFIX_ZWIZARD):-1].strip()
        try:
            wizard_obj = ast.literal_eval(inner)
            
            # Use modern OOP API - walker extends wizard, so it has handle()
            if walker:
                zHat = walker.handle(wizard_obj)
            else:
                zHat = self.zcli.wizard.handle(wizard_obj)
            
            # Mode-specific return behavior
            if is_bifrost_mode(self.zcli.session):
                # Bifrost: Return zHat for API consumption
                return zHat
            
            # Terminal/Walker: Return zBack for navigation (or zHat if no walker)
            return NAV_ZBACK if walker else zHat
        except Exception as e:
            self.logger.error(f"Failed to parse zWizard payload: {e}")
            return None

    def _handle_wizard_dict(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Union[str, Any]]:
        """
        Handle zWizard dict command.
        
        Executes wizard payload from dict format via walker or wizard subsystem.
        Returns mode-specific results (zBack for Terminal, zHat for Bifrost).
        
        Args:
            zHorizontal: Dict command with "zWizard" key
            walker: Optional walker instance (preferred for navigation context)
            context: Optional context dict with mode metadata
        
        Returns:
            - Bifrost mode: zHat (actual wizard result)
            - Terminal/Walker mode: "zBack" (for navigation) or zHat (no walker)
        
        Example:
            result = _handle_wizard_dict({"zWizard": {"steps": [...]}}, walker, context)
        
        Notes:
            - No parsing needed (already dict format)
            - Walker extends wizard, so walker.handle() is preferred
            - Mode-specific returns enable proper Terminal vs. API behavior
        """
        self._log_detected("zWizard (dict)")
        
        # DEBUG: Log wizard handling
        self.logger.debug("=" * 80)
        self.logger.debug("[_handle_wizard_dict] ENTRY POINT")
        self.logger.debug(f"  Walker: {walker is not None}")
        self.logger.debug(f"  zWizard keys: {list(zHorizontal[KEY_ZWIZARD].keys())}")
        self.logger.debug("=" * 80)
        
        # Use modern OOP API - walker extends wizard, so it has handle()
        if walker:
            self.logger.debug("[_handle_wizard_dict] Calling walker.handle()")
            zHat = walker.handle(zHorizontal[KEY_ZWIZARD])
            self.logger.debug(f"[_handle_wizard_dict] walker.handle() returned: {type(zHat)}")
        else:
            self.logger.debug("[_handle_wizard_dict] Calling zcli.wizard.handle()")
            zHat = self.zcli.wizard.handle(zHorizontal[KEY_ZWIZARD])
            self.logger.debug(f"[_handle_wizard_dict] zcli.wizard.handle() returned: {type(zHat)}")
        
        # Mode-specific return behavior
        if is_bifrost_mode(self.zcli.session):
            # Bifrost: Return zHat for API consumption
            return zHat
        
        # Terminal/Walker: Return zBack for navigation (or zHat if no walker)
        return NAV_ZBACK if walker else zHat

    def _handle_read_string(
        self,
        zHorizontal: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """
        Handle zRead string command.
        
        Parses the model name from string format and dispatches to zData subsystem
        with default action "read".
        
        Args:
            zHorizontal: String command in format "zRead(...)"
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request() (typically dict or list)
        
        Example:
            result = _handle_read_string("zRead(users)", context)
            # Equivalent to: {"action": "read", "model": "users"}
        
        Notes:
            - Empty payload: {"action": "read"} (no model specified)
            - Non-empty payload: {"action": "read", "model": "..."}
            - Dispatched to zData.handle_request()
        """
        self._log_detected("zRead request (string)")
        self._display_handler(_LABEL_HANDLE_ZREAD_STRING, _DEFAULT_INDENT_LAUNCHER)
        
        # Extract and build request
        inner = zHorizontal[len(CMD_PREFIX_ZREAD):-1].strip()
        req = {KEY_ACTION: _DEFAULT_ACTION_READ}
        if inner:
            req[KEY_MODEL] = inner
        
        self.logger.framework.debug(f"Dispatching zRead (string) with request: {req}")
        return self.zcli.data.handle_request(req, context=context)

    def _handle_read_dict(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """
        Handle zRead dict command.
        
        Extracts the read request from dict format and dispatches to zData subsystem
        with default action "read".
        
        Args:
            zHorizontal: Dict command with "zRead" key
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request() (typically dict or list)
        
        Example:
            result = _handle_read_dict({"zRead": {"model": "users", "where": {"id": 1}}}, context)
            # Dispatched as: {"action": "read", "model": "users", "where": {"id": 1}}
        
        Notes:
            - String payload: {"zRead": "users"} -> {"action": "read", "model": "users"}
            - Dict payload: {"zRead": {...}} -> {action: "read", ...}
            - Sets default action if not specified
        """
        self._log_detected("zRead (dict)")
        self._display_handler(_LABEL_HANDLE_ZREAD_DICT, _DEFAULT_INDENT_LAUNCHER)
        
        # Extract and normalize request
        req = zHorizontal.get(KEY_ZREAD) or {}
        if isinstance(req, str):
            req = {KEY_MODEL: req}
        
        self._set_default_action(req, _DEFAULT_ACTION_READ)
        
        self.logger.framework.debug(f"Dispatching zRead (dict) with request: {req}")
        return self.zcli.data.handle_request(req, context=context)

    def _handle_data_dict(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """
        Handle zData dict command.
        
        Extracts the data request from dict format and dispatches to zData subsystem
        with default action "read".
        
        Args:
            zHorizontal: Dict command with "zData" key
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request() (typically dict or list)
        
        Example:
            result = _handle_data_dict({"zData": {"action": "create", "model": "users", ...}}, context)
        
        Notes:
            - String payload: {"zData": "users"} -> {"action": "read", "model": "users"}
            - Dict payload: {"zData": {...}} -> {action: "read" (default), ...}
            - Sets default action if not specified
        """
        self._log_detected("zData (dict)")
        self._display_handler(_LABEL_HANDLE_ZDATA_DICT, _DEFAULT_INDENT_LAUNCHER)
        
        # Extract and normalize request
        req = zHorizontal.get(KEY_ZDATA) or {}
        if isinstance(req, str):
            req = {KEY_MODEL: req}
        
        self._set_default_action(req, _DEFAULT_ACTION_READ)
        
        self.logger.framework.debug(f"Dispatching zData (dict) with request: {req}")
        return self.zcli.data.handle_request(req, context=context)

    def _handle_crud_dict(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """
        Handle generic CRUD dict command.
        
        Smart fallback for dicts that look like CRUD operations but don't use
        zRead/zData wrappers. Detects CRUD keys and dispatches to zData subsystem.
        
        Args:
            zHorizontal: Dict with CRUD keys (action, model, table, fields, values, etc.)
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request(), or None if not a valid CRUD dict
        
        Example:
            result = _handle_crud_dict({"action": "read", "model": "users"}, context)
            result = _handle_crud_dict({"model": "users", "where": {"id": 1}}, context)
            # Second example: action defaults to "read"
        
        Notes:
            - Requires "model" key to be present (validation)
            - Detects CRUD keys: action, model, tables, fields, values, filters, where, order_by, limit, offset
            - Sets default action to "read" if not specified
            - Creates a copy to avoid mutating original dict
        """
        # CRUD key detection
        maybe_crud = {
            KEY_ACTION, KEY_MODEL, KEY_TABLES, KEY_FIELDS, KEY_VALUES,
            KEY_FILTERS, KEY_WHERE, KEY_ORDER_BY, KEY_LIMIT, KEY_OFFSET
        }
        
        # Validate: Must have at least one CRUD key AND "model" key
        if any(k in zHorizontal for k in maybe_crud) and KEY_MODEL in zHorizontal:
            req = dict(zHorizontal)  # Create copy to avoid mutation
            self._set_default_action(req, _DEFAULT_ACTION_READ)
            
            self._log_detected(f"generic CRUD dict => {req}")
            self._display_handler(_LABEL_HANDLE_CRUD_DICT, _DEFAULT_INDENT_LAUNCHER)
            
            return self.zcli.data.handle_request(req, context=context)
        
        return None

    # ========================================================================
    # DICT ROUTING HELPERS - Decomposed from _launch_dict()
    # ========================================================================

    def _unwrap_content_wrapper(
        self,
        zHorizontal: Dict[str, Any],
        content_keys: List[str],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Unwrap single "Content" key pattern.
        
        Common UI pattern: {_zClass: "...", Content: [events]}
        Unwraps and dispatches the Content directly.
        
        Args:
            zHorizontal: Dict command
            content_keys: List of non-metadata keys
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Recursively dispatched result, or None if not a Content wrapper
        """
        if len(content_keys) == 1 and content_keys[0] == 'Content':
            self._log_detected("Content wrapper (unwrapping)")
            content_value = zHorizontal['Content']
            return self.launch(content_value, context=context, walker=walker)
        return None

    def _resolve_data_block_if_present(
        self,
        zHorizontal: Dict[str, Any],
        is_subsystem_call: bool,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """
        Resolve block-level _data queries if present (Flask/Jinja pattern).
        
        If dict has _data block, resolves queries BEFORE processing children.
        Stores results in context["_resolved_data"] for child blocks to access.
        
        Args:
            zHorizontal: Dict command
            is_subsystem_call: Whether this is a direct subsystem call
            context: Context dict to store resolved data
        
        Notes:
            - Modifies context in-place (adds/updates "_resolved_data")
            - Only resolves if NOT a subsystem call
            - Logs resolution results
        """
        if "_data" in zHorizontal and not is_subsystem_call:
            self.logger.framework.info("[zCLI Data] Detected _data block, resolving queries...")
            resolved_data = self._resolve_block_data(zHorizontal["_data"], context)
            if resolved_data:
                if "_resolved_data" not in context:
                    context["_resolved_data"] = {}
                context["_resolved_data"].update(resolved_data)
                self.logger.framework.info(f"[zCLI Data] Resolved {len(resolved_data)} data queries for block")
            else:
                self.logger.framework.warning("[zCLI Data] _data block present but no data resolved")

    def _expand_nested_shorthands(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand nested shorthand keys within 'items' list (e.g., zURL, zImage).
        Used when zUL/zOL contain items with nested shorthands.
        NOTE: This method is now deprecated as shorthand expansion for lists
        is handled directly in the shorthand expansion block.
        """
        if 'items' not in params or not isinstance(params['items'], list):
            return params
        
        expanded_items = []
        for item in params['items']:
            if isinstance(item, dict) and len(item) == 1:
                # Check if item is a shorthand (e.g., {zURL: {...}})
                shorthand_key = list(item.keys())[0]
                shorthand_value = item[shorthand_key]
                
                if shorthand_key == 'zURL' and isinstance(shorthand_value, dict):
                    # Expand zURL to full zDisplay format
                    expanded_items.append({KEY_ZDISPLAY: {'event': 'zURL', **shorthand_value}})
                elif shorthand_key == 'zImage' and isinstance(shorthand_value, dict):
                    expanded_items.append({KEY_ZDISPLAY: {'event': 'image', **shorthand_value}})
                elif shorthand_key == 'zText' and isinstance(shorthand_value, dict):
                    expanded_items.append({KEY_ZDISPLAY: {'event': 'text', **shorthand_value}})
                elif shorthand_key.startswith('zH') and len(shorthand_key) == 3 and shorthand_key[2].isdigit():
                    indent_level = int(shorthand_key[2])
                    if 1 <= indent_level <= 6:
                        expanded_items.append({KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **shorthand_value}})
                else:
                    # Not a recognized shorthand, keep as-is
                    expanded_items.append(item)
            else:
                # Not a single-key dict, keep as-is
                expanded_items.append(item)
        
        # Return params with expanded items
        return {**params, 'items': expanded_items}

    def _handle_organizational_structure(
        self,
        zHorizontal: Dict[str, Any],
        content_keys: List[str],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Handle organizational structure (nested dicts/lists with no direct actions).
        
        If dict has only nested dicts/lists, it's organizational - recurse into it
        rather than treating as implicit wizard. Enables flexible YAML organization.
        
        Args:
            zHorizontal: Dict command
            content_keys: List of non-metadata keys
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Recursion result, or None if not organizational structure
        
        Notes:
            - In Bifrost mode: Skip expansion/execution, pass through raw structure
            - In Terminal mode: Expand shorthands and recurse into nested structures
        """
        # Bifrost mode: Don't expand or execute - just pass through raw structure
        # The Bifrost client will handle rendering based on shorthand key names
        if is_bifrost_mode(self.zcli.session):
            # In Bifrost mode, organizational structures are passed through unchanged
            # The wizard will collect them for chunked delivery to the client
            return None
        
        # Terminal mode: Continue with shorthand expansion and execution
        # First, check for shorthand syntax in content_keys BEFORE other processing
        # This handles cases like {_zClass: "...", zImage: {...}} where mixed types exist
        # NOTE: This is a fallback for edge cases - primary expansion happens in zWizard
        for key in content_keys:
            value = zHorizontal[key]
            if isinstance(value, list):
                # Case 1a: KEY itself is a shorthand with list value (e.g., zURL: [{...}, {...}])
                expanded_items = []
                for item in value:
                    if isinstance(item, dict):
                        # Skip if already expanded (has zDisplay wrapper)
                        if KEY_ZDISPLAY in item:
                            expanded_items.append(item)
                        elif key == 'zImage':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'image', **item}})
                        elif key == 'zURL':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'zURL', **item}})
                        elif key.startswith('zH') and len(key) == 3 and key[2].isdigit():
                            indent_level = int(key[2])
                            if 1 <= indent_level <= 6:
                                expanded_items.append({KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **item}})
                        elif key == 'zText':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'text', **item}})
                        elif key == 'zUL':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **item}})
                        elif key == 'zOL':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **item}})
                        elif key == 'zTable':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'zTable', **item}})
                        elif key == 'zMD':
                            expanded_items.append({KEY_ZDISPLAY: {'event': 'rich_text', **item}})
                if expanded_items:
                    zHorizontal[key] = expanded_items
            elif isinstance(value, dict):
                # Case 1b: KEY itself is a shorthand with dict value (e.g., zImage: {src: ...})
                if key == 'zImage':
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'image', **value}}
                elif key == 'zURL':
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'zURL', **value}}
                elif key.startswith('zH') and len(key) == 3 and key[2].isdigit():
                    indent_level = int(key[2])
                    if 1 <= indent_level <= 6 and KEY_ZDISPLAY not in value:
                        zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **value}}
                elif key == 'zText' and KEY_ZDISPLAY not in value:
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'text', **value}}
                elif key == 'zUL' and KEY_ZDISPLAY not in value:
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **value}}
                elif key == 'zOL' and KEY_ZDISPLAY not in value:
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **value}}
                elif key == 'zTable' and KEY_ZDISPLAY not in value:
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'zTable', **value}}
                elif key == 'zMD' and KEY_ZDISPLAY not in value:
                    zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'rich_text', **value}}
                elif key == 'zCrumbs' and KEY_ZDISPLAY not in value:
                    # zCrumbs shorthand - handle 'show' parameter
                    self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Detected zCrumbs key with value: {value}")
                    if 'show' in value:
                        show_value = value.get('show', False)
                        if show_value is True or (isinstance(show_value, str) and show_value.lower() == 'true'):
                            # Pass through all params except 'show'
                            params_without_show = {k: v for k, v in value.items() if k != 'show'}
                            zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'zCrumbs', **params_without_show}}
                            self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Expanded to: {zHorizontal[key]}")
                        else:
                            # show: false - remove key from processing
                            self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] show=false, skipping")
                            continue
                    else:
                        # Missing 'show' parameter - skip
                        self.logger.framework.debug(f"[zCrumbs Shorthand MAIN] Missing 'show' parameter, skipping")
                        continue
                # Case 2: VALUE contains a single shorthand key (e.g., Link_zCLI: {zURL: {label: ...}} or zURL: [{...}, {...}])
                elif len(value) == 1:
                    inner_key = list(value.keys())[0]
                    inner_value = value[inner_key]
                    if isinstance(inner_value, dict):
                        # Single item: {zURL: {label: ...}}
                        if inner_key == 'zImage':
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'image', **inner_value}}]
                        elif inner_key == 'zURL':
                            # Wrap in list to create separate wizard step with prompt
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'zURL', **inner_value}}]
                        elif inner_key.startswith('zH') and len(inner_key) == 3 and inner_key[2].isdigit():
                            indent_level = int(inner_key[2])
                            if 1 <= indent_level <= 6:
                                zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **inner_value}}]
                        elif inner_key == 'zText':
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'text', **inner_value}}]
                        elif inner_key == 'zUL':
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **inner_value}}]
                        elif inner_key == 'zOL':
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **inner_value}}]
                        elif inner_key == 'zTable':
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'zTable', **inner_value}}]
                        elif inner_key == 'zMD':
                            zHorizontal[key] = [{KEY_ZDISPLAY: {'event': 'rich_text', **inner_value}}]
                    elif isinstance(inner_value, list):
                        # Multiple items: {zURL: [{...}, {...}, {...}]}
                        expanded_items = []
                        for item in inner_value:
                            if isinstance(item, dict):
                                if inner_key == 'zImage':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'image', **item}})
                                elif inner_key == 'zURL':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'zURL', **item}})
                                elif inner_key.startswith('zH') and len(inner_key) == 3 and inner_key[2].isdigit():
                                    indent_level = int(inner_key[2])
                                    if 1 <= indent_level <= 6:
                                        expanded_items.append({KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **item}})
                                elif inner_key == 'zText':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'text', **item}})
                                elif inner_key == 'zUL':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **item}})
                                elif inner_key == 'zOL':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **item}})
                                elif inner_key == 'zTable':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'zTable', **item}})
                                elif inner_key == 'zMD':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'rich_text', **item}})
                        if expanded_items:
                            zHorizontal[key] = expanded_items
        
        # SURGICAL FIX: Check if ALL keys are UI event shorthands (implicit sequence)
        # If yes, process sequentially instead of recursively
        # FIRST: Expand any list values for UI event keys (from LSP duplicate handling)
        # ALSO: Strip __dup{N} suffix from duplicate keys (LSP suffix strategy)
        ui_event_keys = []
        for key in content_keys:
            # Strip __dup{N} suffix if present (from LSP duplicate key handling)
            clean_key = key.split('__dup')[0] if '__dup' in key else key
            
            if clean_key.startswith('zH') and len(clean_key) == 3 and clean_key[2].isdigit():
                ui_event_keys.append(key)
                # Expand using clean_key logic
                val = zHorizontal[key]
                if isinstance(val, dict) and KEY_ZDISPLAY not in val:
                    indent_level = int(clean_key[2])
                    if 1 <= indent_level <= 6:
                        zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **val}}
            elif clean_key in ['zText', 'zMD', 'zImage', 'zURL']:
                ui_event_keys.append(key)
                # Expand using clean_key logic
                val = zHorizontal[key]
                if isinstance(val, dict) and KEY_ZDISPLAY not in val:
                    if clean_key == 'zText':
                        zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'text', **val}}
                    elif clean_key == 'zMD':
                        zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'rich_text', **val}}
                    elif clean_key == 'zImage':
                        zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'image', **val}}
                    elif clean_key == 'zURL':
                        zHorizontal[key] = {KEY_ZDISPLAY: {'event': 'zURL', **val}}
        
        # If ALL content keys are UI events, treat as implicit sequence
        if len(ui_event_keys) == len(content_keys) and len(ui_event_keys) >= 2:
            # Collect expanded shorthands into sequential list
            implicit_sequence = []
            for key in content_keys:
                val = zHorizontal[key]
                if isinstance(val, dict) and KEY_ZDISPLAY in val:
                    # Single UI event - already expanded by above logic
                    implicit_sequence.append(val)
            
            if implicit_sequence:
                self.logger.framework.debug(
                    f"[zCLI Implicit Sequence] Detected {len(implicit_sequence)} UI events, processing sequentially"
                )
                return self._launch_list(implicit_sequence, context, walker)
        
        # Check if ALL content values are dicts or lists
        all_nested = all(
            isinstance(zHorizontal[k], (dict, list))
            for k in content_keys
        )
        
        if all_nested:
            self.logger.framework.debug(
                f"[zCLI Recursion] Organizational structure detected "
                f"({len(content_keys)} keys), recursing..."
            )
            
            result = None
            for key in content_keys:
                value = zHorizontal[key]
                self.logger.framework.debug(
                    f"[zCLI Recursion] Processing nested key: {key} "
                    f"(type: {type(value).__name__})"
                )
                
                # Check for shorthand syntax BEFORE recursing
                # NOTE: This is a fallback - primary expansion happens in zWizard
                # Case 1: KEY itself is a shorthand
                if key == 'zImage' and isinstance(value, dict):
                    value = {KEY_ZDISPLAY: {'event': 'image', **value}}
                elif key == 'zURL' and isinstance(value, dict):
                    value = {KEY_ZDISPLAY: {'event': 'zURL', **value}}
                elif key.startswith('zH') and len(key) == 3 and key[2].isdigit() and isinstance(value, dict):
                    indent_level = int(key[2])
                    if 1 <= indent_level <= 6 and KEY_ZDISPLAY not in value:
                        value = {KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **value}}
                elif key == 'zText' and isinstance(value, dict) and KEY_ZDISPLAY not in value:
                    value = {KEY_ZDISPLAY: {'event': 'text', **value}}
                elif key == 'zUL' and isinstance(value, dict) and KEY_ZDISPLAY not in value:
                    value = {KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **value}}
                elif key == 'zOL' and isinstance(value, dict) and KEY_ZDISPLAY not in value:
                    value = {KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **value}}
                elif key == 'zTable' and isinstance(value, dict) and KEY_ZDISPLAY not in value:
                    value = {KEY_ZDISPLAY: {'event': 'zTable', **value}}
                elif key == 'zMD' and isinstance(value, dict) and KEY_ZDISPLAY not in value:
                    value = {KEY_ZDISPLAY: {'event': 'rich_text', **value}}
                elif key == 'zCrumbs' and isinstance(value, dict) and KEY_ZDISPLAY not in value:
                    # zCrumbs shorthand - handle 'show' parameter
                    self.logger.framework.debug(f"[zCrumbs Shorthand] Detected zCrumbs key with value: {value}")
                    if 'show' in value:
                        show_value = value.get('show', False)
                        self.logger.framework.debug(f"[zCrumbs Shorthand] show value: {show_value}")
                        if show_value is True or (isinstance(show_value, str) and show_value.lower() == 'true'):
                            # Pass through all params except 'show'
                            params_without_show = {k: v for k, v in value.items() if k != 'show'}
                            value = {KEY_ZDISPLAY: {'event': 'zCrumbs', **params_without_show}}
                            self.logger.framework.debug(f"[zCrumbs Shorthand] Expanded to: {value}")
                        else:
                            # show: false - skip to next key
                            self.logger.framework.debug(f"[zCrumbs Shorthand] show=false, skipping")
                            continue
                    else:
                        # Missing 'show' parameter - skip to next key  
                        self.logger.framework.debug(f"[zCrumbs Shorthand] Missing 'show' parameter, skipping")
                        continue
                # Case 2: VALUE contains a single shorthand key (e.g., Link_zCLI: {zURL: {label: ...}} or zURL: [{...}, {...}])
                elif isinstance(value, dict) and len(value) == 1:
                    inner_key = list(value.keys())[0]
                    inner_value = value[inner_key]
                    if isinstance(inner_value, dict):
                        # Single item
                        if inner_key == 'zImage':
                            value = [{KEY_ZDISPLAY: {'event': 'image', **inner_value}}]
                        elif inner_key == 'zURL':
                            # Wrap in list to create separate wizard step with prompt
                            value = [{KEY_ZDISPLAY: {'event': 'zURL', **inner_value}}]
                        elif inner_key.startswith('zH') and len(inner_key) == 3 and inner_key[2].isdigit():
                            indent_level = int(inner_key[2])
                            if 1 <= indent_level <= 6:
                                value = [{KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **inner_value}}]
                        elif inner_key == 'zText':
                            value = [{KEY_ZDISPLAY: {'event': 'text', **inner_value}}]
                        elif inner_key == 'zUL':
                            value = [{KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **inner_value}}]
                        elif inner_key == 'zOL':
                            value = [{KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **inner_value}}]
                        elif inner_key == 'zTable':
                            value = [{KEY_ZDISPLAY: {'event': 'zTable', **inner_value}}]
                        elif inner_key == 'zMD':
                            value = [{KEY_ZDISPLAY: {'event': 'rich_text', **inner_value}}]
                    elif isinstance(inner_value, list):
                        # Multiple items: {zURL: [{...}, {...}, {...}]}
                        expanded_items = []
                        for item in inner_value:
                            if isinstance(item, dict):
                                if inner_key == 'zImage':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'image', **item}})
                                elif inner_key == 'zURL':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'zURL', **item}})
                                elif inner_key.startswith('zH') and len(inner_key) == 3 and inner_key[2].isdigit():
                                    indent_level = int(inner_key[2])
                                    if 1 <= indent_level <= 6:
                                        expanded_items.append({KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **item}})
                                elif inner_key == 'zText':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'text', **item}})
                                elif inner_key == 'zUL':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **item}})
                                elif inner_key == 'zOL':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **item}})
                                elif inner_key == 'zTable':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'zTable', **item}})
                                elif inner_key == 'zMD':
                                    expanded_items.append({KEY_ZDISPLAY: {'event': 'rich_text', **item}})
                        if expanded_items:
                            value = expanded_items
                
                # Recursively process nested content
                if isinstance(value, dict):
                    result = self._launch_dict(value, context, walker)
                elif isinstance(value, list):
                    result = self._launch_list(value, context, walker)
                
                # Check for navigation signals (string signals AND zLink dicts)
                if result in ('zBack', 'exit', 'stop', 'error'):
                    return result
                
                # Check for zLink navigation (stop processing and return to trigger navigation)
                if isinstance(result, dict) and 'zLink' in result:
                    return result
            
            self.logger.framework.debug(
                f"[zCLI Recursion] Completed organizational recursion, returning: {result}"
            )
            return result
        
        return None

    def _handle_implicit_wizard(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any]
    ) -> Optional[Union[str, Any]]:
        """
        Handle implicit wizard (multiple non-metadata, non-subsystem keys).
        
        If dict has multiple content keys and NOT purely organizational,
        treats as wizard steps.
        
        Args:
            zHorizontal: Dict command
            walker: Optional walker instance
        
        Returns:
            Wizard execution result (zHat)
        """
        self._log_detected("Implicit zWizard (multi-step)")
        
        # Call wizard with proper context - use walker if available
        if walker:
            zHat = walker.handle(zHorizontal)
        else:
            zHat = self.zcli.wizard.handle(zHorizontal)
        
        # For implicit wizards (nested sections), return zHat to continue execution
        # Don't return 'zBack' as that would trigger navigation and create loops
        return zHat

    def _route_zdisplay(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """
        Route zDisplay command (legacy format).
        
        Args:
            zHorizontal: Dict containing KEY_ZDISPLAY
            context: Optional context dict
        
        Returns:
            Result from display event (e.g. user input for read_string/selection, None for display-only events)
        """
        self._log_detected("zDisplay (wrapped)")
        display_data = zHorizontal[KEY_ZDISPLAY]
        
        if isinstance(display_data, dict):
            # Pass context for %data.* variable resolution
            if context and "_resolved_data" in context:
                display_data["_context"] = context
            
            # Use display.handle() to pass through ALL parameters automatically and return result
            result = self.display.handle(display_data)
            return result
        else:
            self.logger.framework.warning(f"[_route_zdisplay] display_data is not a dict! Type: {type(display_data)}")
        
        return None

    def _route_zfunc(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """
        Route zFunc command (function execution or plugin invocation).
        
        Args:
            zHorizontal: Dict containing KEY_ZFUNC
            context: Optional context dict
        
        Returns:
            Function/plugin execution result
        """
        self._log_detected("zFunc (dict)")
        self._display_handler(_LABEL_HANDLE_ZFUNC_DICT, _DEFAULT_INDENT_HANDLER)
        func_spec = zHorizontal[KEY_ZFUNC]
        
        # DEBUG: Log context to diagnose zHat passing
        self.logger.debug(f"[_route_zfunc] context type: {type(context)}, keys: {context.keys() if context else 'None'}")
        if context and "zHat" in context:
            self.logger.debug(f"[_route_zfunc] zHat found in context: {context['zHat']}")
        
        # Check if it's a plugin invocation (starts with &)
        if isinstance(func_spec, str) and func_spec.startswith(PLUGIN_PREFIX):
            self._log_detected(f"plugin invocation in zFunc: {func_spec}")
            return self.zcli.zparser.resolve_plugin_invocation(func_spec, context=context)
        
        # Non-plugin zFunc calls
        return self.zcli.zfunc.handle(func_spec, zContext=context)

    def _route_zdialog(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any]
    ) -> Optional[Any]:
        """
        Route zDialog command (interactive form/dialog).
        
        Args:
            zHorizontal: Dict containing KEY_ZDIALOG
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Dialog execution result
        """
        from ...j_zDialog import handle_zDialog
        self._log_detected("zDialog")
        return handle_zDialog(zHorizontal, zcli=self.zcli, walker=walker, context=context)

    def _route_zlogin(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """
        Route zLogin command (built-in authentication action).
        
        Args:
            zHorizontal: Dict containing KEY_ZLOGIN
            context: Optional context dict (contains zConv, model from zDialog)
        
        Returns:
            Login result
        """
        self._display_handler(_LABEL_HANDLE_ZLOGIN, _DEFAULT_INDENT_HANDLER)
        self._log_detected(f"zLogin: {zHorizontal[KEY_ZLOGIN]}")
        
        # Get app name from zLogin value (string)
        app_or_type = zHorizontal[KEY_ZLOGIN]
        
        # Get zConv and model from context (set by zDialog)
        zConv = context.get("zConv", {}) if context else {}
        model = context.get("model") if context else None
        
        # If model wasn't in context, check if it was injected into zHorizontal
        if not model and "model" in zHorizontal:
            model = zHorizontal["model"]
        
        # Build zContext for zLogin
        zContext = {
            "model": model,
            "fields": context.get("fields", []) if context else [],
            "zConv": zConv
        }
        
        # Import and call handle_zLogin
        from zOS.L2_Core.d_zAuth.zAuth_modules import handle_zLogin
        
        self.logger.debug(
            f"[zLauncher] Calling zLogin with zConv keys: {list(zConv.keys())}, "
            f"model: {model}"
        )
        
        result = handle_zLogin(
            app_or_type=app_or_type,
            zConv=zConv,
            zContext=zContext,
            zcli=self.zcli
        )
        
        self.logger.debug(f"[zLauncher] zLogin result: {result}")
        return result

    def _route_zlogout(
        self,
        zHorizontal: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Route zLogout command (built-in logout action).
        
        Args:
            zHorizontal: Dict containing KEY_ZLOGOUT
        
        Returns:
            Logout result
        """
        self._display_handler(_LABEL_HANDLE_ZLOGOUT, _DEFAULT_INDENT_HANDLER)
        self._log_detected(f"zLogout: {zHorizontal[KEY_ZLOGOUT]}")
        
        # Get app name from zLogout value (string)
        app_name = zHorizontal[KEY_ZLOGOUT]
        
        # zLogout doesn't need zConv/model, pass empty dicts for consistency
        zConv = {}
        zContext = {}
        
        # Import and call handle_zLogout
        from zOS.L2_Core.d_zAuth.zAuth_modules import handle_zLogout
        
        self.logger.debug(f"[zLauncher] Calling zLogout for app: {app_name}")
        
        result = handle_zLogout(
            app_name=app_name,
            zConv=zConv,
            zContext=zContext,
            zcli=self.zcli
        )
        
        self.logger.debug(f"[zLauncher] zLogout result: {result}")
        return result

    def _route_zlink(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any]
    ) -> Optional[Any]:
        """
        Route zLink command (navigation link).
        
        Args:
            zHorizontal: Dict containing KEY_ZLINK
            walker: Walker instance (required for navigation)
        
        Returns:
            Navigation result, or None if walker not available
        """
        if not self._check_walker(walker, "zLink"):
            return None
        self._log_detected("zLink")
        return self.zcli.navigation.handle_zLink(zHorizontal, walker=walker)

    def _route_zdelta(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any]
    ) -> Optional[Any]:
        """
        Route zDelta command (intra-file block navigation).
        
        Handles navigation to a different block within the same UI file or
        auto-discovers blocks from separate files (fallback pattern).
        
        Args:
            zHorizontal: Dict containing KEY_ZDELTA
            walker: Walker instance (required for navigation)
        
        Returns:
            Navigation result, or None if walker not available or block not found
        
        Notes:
            - Strips $ or % prefix from target block name
            - Fallback: If block not in current file, tries loading zUI.{blockName}.yaml
            - Creates new breadcrumb scope for target block
            - Updates session zBlock to reflect navigation
        """
        if not self._check_walker(walker, "zDelta"):
            return None
        
        self._log_detected("zDelta")
        self._display_handler(_LABEL_HANDLE_ZDELTA, _DEFAULT_INDENT_HANDLER)
        
        # Extract target block name
        target_block_name = zHorizontal[KEY_ZDELTA]
        
        # Strip $ or % prefix if present (delta navigation markers)
        if isinstance(target_block_name, str):
            if target_block_name.startswith(("$", "%")):
                target_block_name = target_block_name[1:]
        
        self.logger.framework.debug(f"zDelta navigation to block: {target_block_name}")
        
        # Get current zVaFile from session
        current_zVaFile = walker.session.get("zVaFile") or walker.zSpark_obj.get("zVaFile")
        if not current_zVaFile:
            self.logger.error("No zVaFile in session or zspark_obj")
            return None
        
        # Reload the UI file
        raw_zFile = walker.loader.handle(current_zVaFile)
        if not raw_zFile:
            self.logger.error(f"Failed to load UI file: {current_zVaFile}")
            return None
        
        # Extract the target block dict - with fallback chain
        target_block_dict = self._resolve_delta_target_block(
            target_block_name,
            raw_zFile,
            current_zVaFile,
            walker
        )
        
        if not target_block_dict:
            self.logger.error(f"Failed to resolve block '{target_block_name}'")
            return None
        
        # Update session and create breadcrumb scope
        walker.session["zBlock"] = target_block_name
        self._initialize_delta_breadcrumb_scope(target_block_name, current_zVaFile, walker)
        
        # Navigate to the target block
        result = walker.execute_loop(items_dict=target_block_dict)
        return result

    def _resolve_delta_target_block(
        self,
        target_block_name: str,
        raw_zFile: Dict[str, Any],
        current_zVaFile: str,
        walker: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve target block for zDelta navigation with fallback.
        
        FALLBACK CHAIN:
        1. Try finding block in current file
        2. If not found, try loading {blockName}.yaml from same directory
        
        Args:
            target_block_name: Name of target block
            raw_zFile: Current UI file content
            current_zVaFile: Current zVaFile path
            walker: Walker instance
        
        Returns:
            Target block dict, or None if not found
        """
        # Try current file first
        if target_block_name in raw_zFile:
            self.logger.framework.debug(
                f"zDelta: Block '{target_block_name}' found in current file"
            )
            return raw_zFile[target_block_name]
        
        # FALLBACK: Try loading zUI.{blockName}.yaml from same directory
        fallback_zPath = self._construct_fallback_zpath(target_block_name, current_zVaFile)
        
        self.logger.framework.debug(
            f"zDelta: Block '{target_block_name}' not in current file, "
            f"trying fallback zPath: {fallback_zPath}"
        )
        
        # Try loading the fallback file
        try:
            fallback_zFile = walker.loader.handle(fallback_zPath)
        except Exception as e:
            self.logger.debug(f"zDelta: Fallback failed: {e}")
            fallback_zFile = None
        
        if fallback_zFile and isinstance(fallback_zFile, dict):
            # SUCCESS: Fallback file loaded
            self.logger.info(
                f"✓ zDelta: Auto-discovered block '{target_block_name}' "
                f"from separate file: {fallback_zPath}"
            )
            return fallback_zFile
        else:
            # FAILED: Neither current file nor fallback file has the block
            self.logger.error(
                f"Block '{target_block_name}' not found:\n"
                f"  - Not in current file: {current_zVaFile}\n"
                f"  - Fallback zPath not found: {fallback_zPath}"
            )
            return None

    def _construct_fallback_zpath(
        self,
        target_block_name: str,
        current_zVaFile: str
    ) -> str:
        """
        Construct fallback zPath for zDelta auto-discovery.
        
        File naming: zUI.{blockName}.yaml -> zPath = "@.UI.zUI.{blockName}"
        
        Args:
            target_block_name: Name of target block
            current_zVaFile: Current zVaFile path
        
        Returns:
            Fallback zPath string
        
        Example:
            current = "@.UI.zUI.index" -> fallback = "@.UI.zUI.zAbout"
        """
        if current_zVaFile.startswith("@"):
            # Parse current zPath to get folder
            path_parts = current_zVaFile.split(".")
            # Replace the last part with target block name
            fallback_path_parts = path_parts[:-1] + [target_block_name]
            return ".".join(fallback_path_parts)
        else:
            # Absolute path - construct relative to current file
            return f"@.UI.zUI.{target_block_name}"

    def _initialize_delta_breadcrumb_scope(
        self,
        target_block_name: str,
        current_zVaFile: str,
        walker: Any
    ) -> None:
        """
        Initialize new breadcrumb scope for zDelta target block.
        
        Creates new node in zCrumbs with full breadcrumb path: zVaFile.zBlock
        
        Args:
            target_block_name: Name of target block
            current_zVaFile: Current zVaFile path
            walker: Walker instance (modifies walker.session in-place)
        
        Notes:
            - Modifies walker.session["zCrumbs"] in-place
            - Creates empty breadcrumb trail for new scope
        """
        # Construct full breadcrumb path
        zVaFile = walker.session.get("zVaFile") or current_zVaFile
        full_crumb_path = f"{zVaFile}.{target_block_name}" if zVaFile else target_block_name
        
        # Initialize empty breadcrumb trail for the new scope
        if "zCrumbs" not in walker.session:
            walker.session["zCrumbs"] = {}
        walker.session["zCrumbs"][full_crumb_path] = []
        
        self.logger.framework.debug(f"zDelta: Created new breadcrumb scope: {full_crumb_path}")

    # ========================================================================
    # HELPER METHODS - DRY Refactoring
    # ========================================================================

    def _display_handler(self, label: str, indent: int) -> None:
        """
        Display handler label with consistent styling.
        
        Args:
            label: Handler label to display
            indent: Indentation level (spaces)
        
        Example:
            self._display_handler("[HANDLE] zFunc", 5)
        
        Notes:
            - Uses parent dispatch color for consistency
            - Style is always "single" for handler labels
            - Avoids repeated zDeclare calls with identical styling
        """
        self.display.zDeclare(
            label,
            color=self.dispatch.mycolor,
            indent=indent,
            style=_DEFAULT_STYLE_SINGLE
        )

    def _log_detected(self, message: str) -> None:
        """
        Log detected command with consistent format.
        
        Args:
            message: Detection message (e.g., "zFunc request", "plugin invocation")
        
        Example:
            self._log_detected("zFunc request")
            self._log_detected("plugin invocation in zFunc: &my_plugin")
        
        Notes:
            - Prefixes all messages with "Detected " for consistency
            - Uses INFO level for all command detection logs
            - Avoids repeated "Detected" string in calling code
        """
        self.logger.framework.debug(f"Detected {message}")

    def _check_walker(self, walker: Optional[Any], command_name: str) -> bool:
        """
        Validate walker instance for commands that require it.
        
        Args:
            walker: Walker instance to validate (can be None)
            command_name: Name of command requiring walker (for error message)
        
        Returns:
            True if walker is valid (not None), False otherwise
        
        Example:
            if not self._check_walker(walker, "zLink"):
                return None
        
        Notes:
            - Logs warning if walker is None
            - Calling code should return None if validation fails
            - Used by zLink and zWizard commands
        """
        if not walker:
            self.logger.warning(f"{command_name} requires walker instance")
            return False
        return True

    def _set_default_action(self, req: Dict[str, Any], default_action: str) -> None:
        """
        Set default action for data request if not specified.
        
        Args:
            req: Request dict to modify (mutated in place)
            default_action: Default action value (typically "read")
        
        Example:
            req = {"model": "users"}
            self._set_default_action(req, "read")
            # req is now: {"model": "users", "action": "read"}
        
        Notes:
            - Mutates req dict in place
            - Uses dict.setdefault() to avoid overwriting existing action
            - Eliminates repeated setdefault calls in handler methods
        """
        req.setdefault(KEY_ACTION, default_action)
    
    def _resolve_block_data(
        self,
        data_block: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute data queries defined in block-level _data (ORCHESTRATOR).
        
        This method has been decomposed from 129 lines into a clean orchestrator
        + 4 focused helpers for query processing.
        
        Supports 3 query formats:
        1. Declarative dict: {model: "...", where: {...}, limit: 1}
        2. Shorthand string: "@.models.zSchema.contacts"
        3. Explicit zData: {zData: {action: "read", model: "..."}}
        
        Args:
            data_block: _data section from zUI block
            context: Current execution context
        
        Returns:
            Dictionary of query results: {"user": {...}, "stats": [...]}
        
        Examples:
            # Declarative format (recommended)
            _data:
              user:
                model: "@.models.zSchema.users"
                where: {id: "%session.zAuth.applications.zCloud.id"}
                limit: 1
            
            # Shorthand format (backward compatibility)
            _data:
              user: "@.models.zSchema.contacts"
            
            # Explicit zData format
            _data:
              stats:
                zData:
                  action: read
                  model: "@.models.zSchema.user_stats"
        
        Notes:
            - Decomposed from 129 lines → 45 lines (65% reduction)
            - 4 data resolution helpers extracted
            - Session-based auto-filtering for security
            - Supports %session.* interpolation in WHERE clauses
        """
        results = {}
        
        for key, query_def in data_block.items():
            try:
                # Format 1: Declarative dict
                if isinstance(query_def, dict) and "model" in query_def:
                    query_def = self._build_declarative_query(query_def)
                
                # Format 2: Shorthand string
                elif isinstance(query_def, str) and query_def.startswith('@.models.'):
                    query_def = self._build_shorthand_query(key, query_def)
                
                # Format 3: Explicit zData block
                if isinstance(query_def, dict) and "zData" in query_def:
                    results[key] = self._execute_data_query(key, query_def, context)
                else:
                    self.logger.framework.warning(f"[zCLI Data] Invalid _data entry: {key}")
                    results[key] = None
                    
            except Exception as e:
                self.logger.framework.error(f"[zCLI Data] Query '{key}' failed: {e}")
                results[key] = None
        
        return results

    # ========================================================================
    # DATA RESOLUTION HELPERS - Decomposed from _resolve_block_data()
    # ========================================================================

    def _interpolate_session_values(
        self,
        where_clause: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Interpolate %session.* values in WHERE clause.
        
        Args:
            where_clause: WHERE clause dict (may contain %session.* values)
        
        Returns:
            WHERE clause with interpolated session values
        
        Example:
            where = {"id": "%session.zAuth.applications.zCloud.id"}
            result = _interpolate_session_values(where)
            # Returns: {"id": 123}  (actual user ID from session)
        
        Notes:
            - Navigates session dict using dot notation
            - Returns None if path doesn't exist
            - Logs interpolation for debugging
        """
        interpolated = {}
        for field, value in where_clause.items():
            if isinstance(value, str) and value.startswith("%session."):
                # Extract session path: %session.zAuth.applications.zCloud.id
                session_path = value[9:]  # Remove "%session." prefix
                path_parts = session_path.split('.')
                
                # Navigate session dict
                session_value = self.zcli.session
                for part in path_parts:
                    if isinstance(session_value, dict):
                        session_value = session_value.get(part)
                    else:
                        session_value = None
                        break
                
                interpolated[field] = session_value
                self.logger.framework.debug(
                    f"[_data] Interpolated {value} → {session_value}"
                )
            else:
                interpolated[field] = value
        
        return interpolated

    def _build_declarative_query(
        self,
        query_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build zData query from declarative dict format.
        
        Args:
            query_def: Declarative query (model + where + limit)
        
        Returns:
            zData query dict
        
        Example:
            query = {"model": "@.models.zSchema.users", "where": {"id": 123}, "limit": 1}
            result = _build_declarative_query(query)
            # Returns: {"zData": {"action": "read", "model": "...", "options": {...}}}
        
        Notes:
            - Interpolates %session.* values in WHERE clause
            - Defaults to limit=1 for single record queries
            - WHERE clause is optional
        """
        model = query_def.get("model")
        where_clause = query_def.get("where", {})
        
        # Interpolate %session.* values in WHERE clause
        interpolated_where = self._interpolate_session_values(where_clause)
        
        return {
            "zData": {
                "action": "read",
                "model": model,
                "options": {
                    "where": interpolated_where if interpolated_where else {},
                    "limit": query_def.get("limit", 1)
                }
            }
        }

    def _build_shorthand_query(
        self,
        key: str,
        model_path: str
    ) -> Dict[str, Any]:
        """
        Build zData query from shorthand string format.
        
        Shorthand: user: "@.models.zSchema.contacts"
        Auto-filters by authenticated user ID for security.
        
        Args:
            key: Query key (for logging)
            model_path: Model path string (@.models.*)
        
        Returns:
            zData query dict with auth filtering
        
        Notes:
            - Backward compatibility (hardcodes 'id' field)
            - Warns about hardcoded field
            - Auto-filters by authenticated user ID
            - Supports 3-layer auth architecture
        """
        self.logger.framework.warning(
            f"[_data] Shorthand syntax '{key}: \"{model_path}\"' uses hardcoded 'id' field. "
            f"Consider using declarative syntax with explicit WHERE clause."
        )
        
        # Get authenticated user ID from zAuth
        zauth = self.zcli.session.get('zAuth', {})
        active_app = zauth.get('active_app')
        
        # Try app-specific auth first
        if active_app:
            app_auth = zauth.get('applications', {}).get(active_app, {})
            user_id = app_auth.get('id')
        else:
            # Fallback to Zolo platform auth
            user_id = zauth.get('zSession', {}).get('id')
        
        return {
            "zData": {
                "action": "read",
                "model": model_path,
                "options": {
                    "where": {"id": user_id} if user_id else {"id": 0},
                    "limit": 1
                }
            }
        }

    def _execute_data_query(
        self,
        key: str,
        query_def: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute zData query and extract result.
        
        Args:
            key: Query key (for logging)
            query_def: zData query dict
            context: Execution context
        
        Returns:
            Query result (dict for single record, list for multiple)
        
        Notes:
            - Sets silent=True to suppress display output
            - Works in any zMode (Terminal, Bifrost)
            - Extracts first record for limit=1 queries
            - Logs result type and count
        """
        # Execute zData query in SILENT mode
        query_def["zData"]["silent"] = True
        result = self.zcli.data.handle_request(query_def["zData"], context)
        
        # Extract first record if limit=1
        limit = query_def["zData"].get("options", {}).get("limit")
        if isinstance(result, list) and limit == 1 and len(result) > 0:
            final_result = result[0]  # Return dict instead of list
        else:
            final_result = result
        
        # Log result
        result_type = type(final_result).__name__
        result_count = len(result) if isinstance(result, list) else 1
        self.logger.framework.debug(
            f"[zCLI Data] Query '{key}' returned {result_type} ({result_count} records)"
        )
        
        return final_result
