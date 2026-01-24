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

# Phase 5: Import extracted modules for incremental integration
from .data_resolver import DataResolver
from .auth_handler import AuthHandler
from .crud_handler import CRUDHandler
from .navigation_handler import NavigationHandler
from .subsystem_router import SubsystemRouter
from .shorthand_expander import ShorthandExpander
from .wizard_detector import WizardDetector
from .organizational_handler import OrganizationalHandler
from .list_commands import ListCommandHandler
from .string_commands import StringCommandHandler


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
        # Phase 5 Micro-Step 5.1: Initialize Extracted Modules
        # ========================================================================
        # These modules are initialized but not yet used. They will be integrated
        # incrementally in subsequent micro-steps.
        
        # Phase 1 modules (Leaf)
        self.data_resolver = DataResolver(self.zcli)
        self.auth_handler = AuthHandler(self.zcli, self.display, self.logger)
        self.crud_handler = CRUDHandler(self.zcli, self.display, self.logger)
        
        # Phase 2 modules (Core Logic)
        self.navigation_handler = NavigationHandler(self.zcli, self.display, self.logger)
        self.subsystem_router = SubsystemRouter(
            self.zcli,
            self.display,
            self.logger,
            self.auth_handler,
            self.navigation_handler
        )
        
        # Phase 3 modules (Shorthand & Detection)
        self.shorthand_expander = ShorthandExpander(self.logger)
        self.wizard_detector = WizardDetector()
        self.organizational_handler = OrganizationalHandler(
            self.shorthand_expander,  # Needs expander, not zcli
            self.logger
        )
        
        # Phase 4 modules (Command Handlers)
        self.list_handler = ListCommandHandler(self.zcli, self.logger)
        self.string_handler = StringCommandHandler(
            self.zcli,
            self.logger,
            self.subsystem_router,
            self.launch  # Pass launch function for recursion
        )
        # Note: dict_handler will be added in later micro-step (has circular deps)

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
        # Phase 5 Micro-Step 5.7: Delegate to ListCommandHandler (Phase 4)
        return self.list_handler.handle(zHorizontal, context, walker, self.launch)

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
            - Phase 5 Micro-Step 5.8: Delegated to StringCommandHandler (Phase 4)
        """
        # Phase 5 Micro-Step 5.8: Delegate to StringCommandHandler (Phase 4)
        return self.string_handler.handle(zHorizontal, context, walker)

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
        # Get ALL content keys, excluding only metadata (_zClass, _zStyle, etc.)
        # This matches the organizational_handler logic to include organizational containers like _Visual_Progression
        metadata_keys = {'_zClass', '_zStyle', '_zId', '_zScripts', 'zId'}
        content_keys = [k for k in zHorizontal.keys() if k not in metadata_keys]
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
        # SHORTHAND SYNTAX EXPANSION (zH1-zH6, zText, zUL, zOL, zDL, zTable, zBtn, zMD, zImage, zURL)
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
        
        # Phase 5 Micro-Step 5.3: MODE-AGNOSTIC Shorthand Expansion (FIXES zCrumbs BUG!)
        # OLD: Only expanded in Terminal mode → zCrumbs never rendered in Bifrost
        # NEW: Expands for BOTH modes → zCrumbs work everywhere!
        zHorizontal, is_subsystem_call = self.shorthand_expander.expand(
            zHorizontal,
            self.zcli.session,  # Pass session dict (not .data)
            is_subsystem_call
        )
        
        # Recalculate content_keys and subsystem check after shorthand expansion
        # Use same metadata filtering as initial check to include organizational containers
        content_keys = [k for k in zHorizontal.keys() if k not in metadata_keys]
        
        # Check for explicit subsystem keys at top level (zDisplay, zFunc, etc.)
        has_explicit_subsystem_keys = any(k in zHorizontal for k in subsystem_keys)
        if has_explicit_subsystem_keys:
            is_subsystem_call = True
        
        # ========================================================================
        # ORGANIZATIONAL STRUCTURE DETECTION (mutually exclusive with wizard)
        # ========================================================================
        # After shorthand expansion, we may have: {'zH1': {'zDisplay': {...}}, 'zText': {'zDisplay': {...}}}
        # These are organizational structures that need recursive launching, even if is_subsystem_call=True
        if not is_crud_call and len(content_keys) > 0 and not has_explicit_subsystem_keys:
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
        # Phase 5 Micro-Step 5.4: Delegate Auth routing to AuthHandler (Phase 1)
        if KEY_ZLOGIN in zHorizontal:
            return self.auth_handler.handle_zlogin(zHorizontal, context)
        if KEY_ZLOGOUT in zHorizontal:
            return self.auth_handler.handle_zlogout()
        # Phase 5 Micro-Step 5.5: Delegate Navigation routing to NavigationHandler (Phase 2)
        if KEY_ZLINK in zHorizontal:
            return self.navigation_handler.handle_zlink(zHorizontal, walker)
        if KEY_ZDELTA in zHorizontal:
            return self.navigation_handler.handle_zdelta(zHorizontal, walker)
        if KEY_ZWIZARD in zHorizontal:
            return self._handle_wizard_dict(zHorizontal, walker, context)
        if KEY_ZREAD in zHorizontal:
            return self._handle_read_dict(zHorizontal, context)
        if KEY_ZDATA in zHorizontal:
            return self._handle_data_dict(zHorizontal, context)
        
        # ========================================================================
        # CRUD FALLBACK
        # ========================================================================
        # Phase 5 Micro-Step 5.6: Delegate CRUD detection to CRUDHandler (Phase 1)
        if self.crud_handler.is_crud_pattern(zHorizontal):
            return self.crud_handler.handle(zHorizontal, context)
        
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
        # Phase 5 Micro-Step 5.2: Delegate to DataResolver (Phase 1 module)
        if "_data" in zHorizontal and not is_subsystem_call:
            self.logger.framework.info("[zCLI Data] Detected _data block, resolving queries...")
            resolved_data = self.data_resolver.resolve_block_data(zHorizontal["_data"], context)
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
        
        REFACTORED: Phase 3 - Delegates to OrganizationalHandler (extracted module).
        All shorthand expansion now handled by ShorthandExpander (Phase 3).
        
        Args:
            zHorizontal: Dict command
            content_keys: List of non-metadata keys
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Recursion result, or None if not organizational structure
        """
        # Phase 5 Integration: Delegate to OrganizationalHandler (Phase 3 extraction)
        return self.organizational_handler.handle(zHorizontal, context, walker, self)
    
    def _handle_implicit_wizard(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Handle implicit wizard (dict with multiple content keys, not purely organizational).
        
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
        # DEBUG: Log display_data to diagnose parameter issues
        self.logger.framework.debug(f"[_route_zdisplay] display_data keys: {list(display_data.keys()) if isinstance(display_data, dict) else 'not a dict'}")
        self.logger.framework.debug(f"[_route_zdisplay] display_data: {display_data}")
        
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
    
    # ========================================================================
    # DATA RESOLUTION HELPERS - Decomposed from _resolve_block_data()
    # ========================================================================

