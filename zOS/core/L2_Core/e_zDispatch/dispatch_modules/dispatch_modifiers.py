# zCLI/subsystems/zDispatch/dispatch_modules/dispatch_modifiers.py

"""
Modifier Processor for zDispatch Subsystem.

This module provides the ModifierProcessor class, which handles prefix and suffix
modifiers that alter command behavior within the zCLI framework. Modifiers enable
powerful command routing patterns like bounce-back navigation, menu creation, 
required actions, and anchor points.

Architecture:
    The ModifierProcessor follows a detection-and-processing pattern:
    
    1. Detection Phase:
       - check_prefix(): Detects prefix modifiers (^ ~)
       - check_suffix(): Detects suffix modifiers (* !)
    
    2. Processing Phase:
       - process(): Executes modifier-specific behavior
       - Delegates to CommandLauncher for action execution
       - Handles mode-specific return values (Terminal vs. Bifrost)

Modifier Semantics:
    PREFIX MODIFIERS:
    - ^ (caret): "Bounce Back" - Execute action, then return to previous menu
      * Terminal/Walker mode: Returns "zBack" for navigation
      * Bifrost mode: Returns actual result for API consumption
      * Supports ^key resolution from zUI files
    
    - ~ (tilde): "Anchor" - Disable back navigation (used with *)
      * Modifies menu behavior: allow_back=False
      * Creates "anchored" menus with no escape option
      * Often used for required workflows
    
    SUFFIX MODIFIERS:
    - * (asterisk): "Menu" - Create menu from horizontal data
      * Routes to zNavigation.create()
      * Respects ~ anchor modifier
      * Works for both walker and non-walker contexts
    
    - ! (exclamation): "Required" - Retry until success
      * Enters retry loop until action returns truthy result
      * User can abort with "stop" input
      * Useful for validation and mandatory steps

Mode-Specific Behavior:
    Terminal/Walker Mode:
        - ^ modifier: Returns "zBack" for menu navigation
        - All modifiers: Standard navigation flow
        - User interaction: Synchronous input for ! modifier
    
    Bifrost Mode:
        - ^ modifier: Returns actual result (no navigation)
        - All modifiers: API-oriented returns
        - User interaction: Asynchronous input patterns

Forward Dependencies:
    This module integrates with 3 subsystems that will be refactored in future weeks:
    
    - zNavigation (Week 6.7): create() method for menu display
    - zLoader (Week 6.9): handle() method for zUI file loading (^key resolution)
    - CommandLauncher (Week 6.6.2): launch() method for action execution ✅ (COMPLETE)

Usage Examples:
    # Bounce back modifier (^): Execute and return
    modifiers = ["^"]
    result = processor.process(modifiers, "^save", {"zFunc": "save_data"}, context, walker)
    # Terminal: Returns "zBack"
    # Bifrost: Returns save_data result
    
    # Menu modifier (*): Create menu
    modifiers = ["*"]
    result = processor.process(modifiers, "menu*", menu_dict, context, walker)
    # Creates menu via zNavigation.create()
    
    # Anchor modifier (~): Disable back in menu
    modifiers = ["~", "*"]
    result = processor.process(modifiers, "~menu*", menu_dict, context, walker)
    # Creates anchored menu (no back button)
    
    # Required modifier (!): Retry until success
    modifiers = ["!"]
    result = processor.process(modifiers, "validate!", {"zFunc": "validate"}, context, walker)
    # Retries until validate() returns True
    
    # Detection methods
    prefix_mods = processor.check_prefix("^action")  # Returns ["^"]
    suffix_mods = processor.check_suffix("menu*")    # Returns ["*"]
    combo_mods = processor.check_prefix("~menu*") + processor.check_suffix("~menu*")
    # Returns ["~", "*"]

Thread Safety:
    - Relies on thread-safe logger and display instances from zCLI
    - Mode detection reads from session (zcli.session[SESSION_KEY_ZMODE])
    - No internal state mutation during processing

Integration with zSession:
    - Mode detection: Uses SESSION_KEY_ZMODE from session (canonical source)
    - Context passing: All handlers accept optional context parameter for request data
    - Session access: Via self.zcli.session (centralized session management)

zAuth Integration:
    - Implicit via context: Authentication state passed through context dict
    - No direct zAuth calls: Action handlers are responsible for auth checks
    - Mode-specific returns: Bifrost mode may return different data structures

Constants:
    All magic strings are replaced with module constants to improve maintainability
    and reduce the risk of typos. See module-level constants below for complete list.
"""

from zOS import Any, Optional, Dict, List, Union

# Import SESSION_KEY_ZMODE from zConfig for mode detection
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZMODE

# Import all dispatch constants from centralized location
from .dispatch_constants import (
    # Modifiers
    MOD_CARET,
    MOD_TILDE,
    MOD_ASTERISK,
    MOD_EXCLAMATION,
    PREFIX_MODIFIERS,
    SUFFIX_MODIFIERS,
    ALL_MODIFIERS,
    # Dict Keys - Context & Session (KEY_MODE removed - using SESSION_KEY_ZMODE)
    KEY_ZVAFILE,
    KEY_ZBLOCK,
    # Modes & Navigation
    MODE_BIFROST,
    NAV_ZBACK,
    # Display Labels (INTERNAL)
    _LABEL_PROCESS_MODIFIERS,
    _LABEL_ZBOUNCE,
    _LABEL_ZREQUIRED,
    _LABEL_ZREQUIRED_RETURN,
    # Log Messages (INTERNAL)
    _LOG_PREFIX_MODIFIERS,
    _LOG_MSG_PARSING_PREFIX,
    _LOG_MSG_PARSING_SUFFIX,
    _LOG_MSG_PRE_MODIFIERS,
    _LOG_MSG_SUF_MODIFIERS,
    _LOG_MSG_RESOLVED,
    _LOG_MSG_MENU_DETECTED,
    _LOG_MSG_ZBOUNCE_RESULT,
    _LOG_MSG_ZBOUNCE_CONTEXT,
    _LOG_MSG_ZBOUNCE_MODE_CHECK,
    _LOG_MSG_BIFROST_DETECTED,
    _LOG_MSG_REQUIRED_STEP,
    _LOG_MSG_REQUIRED_RESULTS,
    _LOG_MSG_REQUIREMENT_NOT_SATISFIED,
    _LOG_MSG_REQUIREMENT_SATISFIED,
    _LOG_MSG_LOOKING_UP_KEY,
    _LOG_MSG_RESOLVED_KEY,
    _LOG_MSG_COULD_NOT_LOAD,
    _LOG_MSG_NO_ZVAFILE,
    _LOG_MSG_CANNOT_RESOLVE,
    # Prompts & Input (INTERNAL)
    _PROMPT_REQUIRED_CONTINUE,
    _INPUT_STOP,
    # Defaults (INTERNAL)
    _DEFAULT_ZBLOCK,
    _DEFAULT_INDENT_PROCESS,
    _DEFAULT_INDENT_MODIFIER,
    # Styles (INTERNAL)
    _STYLE_SINGLE,
    _STYLE_WAVY,
)

# Import shared dispatch helpers
from .dispatch_helpers import is_bifrost_mode


class ModifierProcessor:
    """
    Modifier processor for zDispatch subsystem.
    
    Handles prefix and suffix modifiers that alter command behavior, including
    bounce-back navigation (^), menu creation (*), required actions (!), and
    anchor points (~).
    
    Attributes:
        dispatch: Parent zDispatch instance
        zcli: Root zCLI instance
        logger: Logger instance from zCLI
    
    Methods:
        check_prefix(): Detect prefix modifiers (^ ~)
        check_suffix(): Detect suffix modifiers (* !)
        process(): Execute modifier-specific behavior
        
        Helper methods (DRY):
        _display_modifier(): Display modifier label with consistent styling
        _resolve_ui_key(): Resolve ^key from zUI file
        
        Shared utilities (from dispatch_helpers):
        is_bifrost_mode(): Check if session is in Bifrost mode (no self, uses session dict)
    
    Integration:
        - zConfig: Uses SESSION_KEY_ZMODE from session for mode detection
        - zDisplay: UI output via zDeclare() and read_string()
        - zSession: Mode detection via session[SESSION_KEY_ZMODE]
        - Forward dependencies: 3 subsystems (see module docstring)
    """
    
    # Class-level type declarations
    dispatch: Any  # zDispatch instance
    zcli: Any  # zCLI instance
    logger: Any  # Logger instance

    def __init__(self, dispatch: Any) -> None:
        """
        Initialize modifier processor with parent dispatch instance.
        
        Args:
            dispatch: Parent zDispatch instance providing access to zCLI and logger
        
        Example:
            processor = ModifierProcessor(dispatch)
        """
        self.dispatch = dispatch
        self.zcli = dispatch.zcli
        self.logger = dispatch.logger

    # ========================================================================
    # PUBLIC METHODS - Modifier Detection
    # ========================================================================

    def check_prefix(self, zKey: str) -> List[str]:
        """
        Check for prefix modifiers at the start of a key.
        
        Detects the following prefix modifiers:
        - ^ (caret): Bounce back modifier
        - ~ (tilde): Anchor modifier
        
        Args:
            zKey: Key string to check for prefix modifiers
        
        Returns:
            List of detected prefix modifier symbols (may be empty)
        
        Examples:
            # Single prefix
            check_prefix("^action")  # Returns ["^"]
            check_prefix("~menu*")   # Returns ["~"]
            
            # No prefix
            check_prefix("action")   # Returns []
            check_prefix("menu*")    # Returns []
        
        Notes:
            - Multiple prefixes can be detected (though rare in practice)
            - Detection is order-independent
            - Uses module-level PREFIX_MODIFIERS constant
        """
        self.logger.framework.debug(_LOG_MSG_PARSING_PREFIX, zKey)
        pre_modifiers = [sym for sym in PREFIX_MODIFIERS if zKey.startswith(sym)]
        self.logger.framework.debug(_LOG_MSG_PRE_MODIFIERS, pre_modifiers)
        return pre_modifiers

    def check_suffix(self, zKey: str) -> List[str]:
        """
        Check for suffix modifiers at the end of a key.
        
        Detects the following suffix modifiers:
        - ! (exclamation): Required modifier
        - * (asterisk): Menu modifier
        
        Args:
            zKey: Key string to check for suffix modifiers
        
        Returns:
            List of detected suffix modifier symbols (may be empty)
        
        Examples:
            # Single suffix
            check_suffix("validate!")  # Returns ["!"]
            check_suffix("menu*")      # Returns ["*"]
            
            # No suffix
            check_suffix("action")     # Returns []
            check_suffix("^action")    # Returns []
        
        Notes:
            - Multiple suffixes can be detected (though rare in practice)
            - Detection is order-independent
            - Uses module-level SUFFIX_MODIFIERS constant
        """
        self.logger.framework.debug(_LOG_MSG_PARSING_SUFFIX, zKey)
        suf_modifiers = [sym for sym in SUFFIX_MODIFIERS if zKey.endswith(sym)]
        self.logger.framework.debug(_LOG_MSG_SUF_MODIFIERS, suf_modifiers)
        return suf_modifiers

    # ========================================================================
    # PUBLIC METHODS - Modifier Processing
    # ========================================================================

    def process(
        self,
        modifiers: List[str],
        zKey: str,
        zHorizontal: Any,
        context: Optional[Dict[str, Any]] = None,
        walker: Optional[Any] = None
    ) -> Optional[Union[str, Any]]:
        """
        Process modifiers and execute appropriate behavior (ORCHESTRATOR).
        
        Routes modifier processing to focused handlers. This method has been
        decomposed from 211 lines into a clean orchestrator + 4 helpers.
        
        Modifier priority:
        1. * (menu): Create menu via zNavigation
        2. ^ (bounce): Execute action → return based on mode
        3. ! (required): Retry loop until success
        4. No modifiers: Pass through to launcher
        
        Args:
            modifiers: List of detected modifier symbols
            zKey: Original key with modifiers
            zHorizontal: Command/data to execute
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Modifier-specific result (varies by modifier type)
        
        Examples:
            result = process(["*"], "menu*", menu_dict, context, walker)
            result = process(["^"], "^save", {"zFunc": "save"}, context, walker)
            result = process(["!"], "validate!", {"zFunc": "validate"}, context, walker)
        
        Notes:
            - Decomposed from 211 lines → 45 lines (79% reduction)
            - 4 processing helpers extracted for focused logic
            - Mode-specific behavior handled in helpers
            - Maintains backward compatibility with all modifier types
        """
        # Use walker's display if available, otherwise use zCLI's display
        display = walker.display if walker else self.zcli.display

        self._display_modifier(display, _LABEL_PROCESS_MODIFIERS, _DEFAULT_INDENT_PROCESS)
        self.logger.framework.debug(_LOG_MSG_RESOLVED, modifiers, zKey)

        # Priority 1: Menu modifier (*)
        if MOD_ASTERISK in modifiers:
            return self._process_menu_modifier(modifiers, zKey, zHorizontal, walker)

        # Priority 2: Bounce modifier (^)
        if MOD_CARET in modifiers:
            return self._process_bounce_modifier(zKey, zHorizontal, context, walker, display)

        # Priority 3: Required modifier (!)
        if MOD_EXCLAMATION in modifiers:
            return self._process_required_modifier(zKey, zHorizontal, context, walker, display)

        # No modifiers: Pass through to launcher
        return self.dispatch.launcher.launch(zHorizontal, context=context, walker=walker)

    # ========================================================================
    # MODIFIER PROCESSING HELPERS - Decomposed from process()
    # ========================================================================

    def _process_menu_modifier(
        self,
        modifiers: List[str],
        zKey: str,
        zHorizontal: Any,
        walker: Optional[Any]
    ) -> Optional[Union[str, Any]]:
        """
        Process menu modifier (*) - creates menu via zNavigation.
        
        Args:
            modifiers: List of detected modifier symbols
            zKey: Original key with modifiers
            zHorizontal: Menu items (list or dict)
            walker: Optional walker instance
        
        Returns:
            Menu navigation result
        
        Notes:
            - Checks for anchor (~) modifier to disable back button
            - Tracks menu appearance in breadcrumbs (POP semantics)
            - Applies RBAC filtering for navbar menus
            - Re-dispatches dict results (e.g., zLink navigation)
        """
        is_anchor = MOD_TILDE in modifiers
        self.logger.debug(_LOG_MSG_MENU_DETECTED, zKey, is_anchor)

        # Track menu appearance in breadcrumbs
        if self.zcli and hasattr(self.zcli, 'navigation') and not zKey.startswith("~zNavBar"):
            self.zcli.navigation.handle_zCrumbs(
                zKey,
                walker=None,
                operation='APPEND'
            )
            self.logger.debug(f"[Menu] Tracked menu appearance: {zKey}")

        # Apply RBAC filtering for navbar menus
        if zKey.startswith("~zNavBar"):
            zHorizontal = self._apply_navbarzRBAC_filtering(zKey, zHorizontal)

        # Create menu via zNavigation
        result = self.zcli.navigation.create(
            zHorizontal, 
            allow_back=not is_anchor, 
            walker=walker
        )

        # Re-dispatch dict results (e.g., zLink navigation)
        if isinstance(result, dict):
            self.logger.framework.debug(f"[Menu] Returned dict, re-dispatching: {result}")
            return self.dispatch.launcher.launch(result, None, walker)
        
        return result

    def _apply_navbarzRBAC_filtering(
        self,
        zKey: str,
        zHorizontal: List[Any]
    ) -> List[str]:
        """
        Apply RBAC filtering to navbar menu items.
        
        Filters navbar items based on current authentication state,
        re-evaluated dynamically on every render.
        
        Args:
            zKey: Navbar key (starts with ~zNavBar)
            zHorizontal: Raw navbar items (may have $ prefixes)
        
        Returns:
            Filtered navbar items with $ prefixes restored
        
        Notes:
            - Strips $ prefixes before RBAC filtering
            - Re-adds $ prefixes after filtering (for delta navigation)
            - Sets navbar navigation flag in session for OP_RESET
        """
        self.logger.framework.debug(
            f"[Dispatch] Applying dynamic RBAC filtering for navbar: {zKey}"
        )
        
        # Strip existing $ prefixes from zHorizontal before filtering
        clean_items = []
        for item in zHorizontal:
            if isinstance(item, str):
                clean_items.append(item.lstrip('$'))
            else:
                clean_items.append(item)
        
        # Filter the navbar items based on current authentication state
        filtered_items = self.zcli.navigation._filter_navbar_byzRBAC(clean_items)
        self.logger.framework.info(
            f"[Dispatch] Navbar filtered: {len(zHorizontal)} → {len(filtered_items)} items"
        )
        
        # Add delta prefix ($) to filtered items for intra-file navigation
        # Keep dict items (with zSub metadata) as dicts, but prefix the key
        filtered_with_prefix = []
        for item in filtered_items:
            if isinstance(item, str):
                # Simple string item - add $ prefix
                filtered_with_prefix.append(f"${item}")
            elif isinstance(item, dict):
                # Dict item with metadata (zSub, zRBAC) - prefix the key but keep as dict
                item_name = list(item.keys())[0]
                item_data = item[item_name]
                filtered_with_prefix.append({f"${item_name}": item_data})
            else:
                # Unknown type - keep as-is
                filtered_with_prefix.append(item)
        
        # SET NAVBAR FLAG: Mark that next navigation is from navbar
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZCRUMBS
        if SESSION_KEY_ZCRUMBS not in self.zcli.session:
            self.zcli.session[SESSION_KEY_ZCRUMBS] = {}
        self.zcli.session[SESSION_KEY_ZCRUMBS]["_navbar_navigation"] = True
        self.logger.framework.debug(
            "[Dispatch] Navbar flag set: next navigation will trigger OP_RESET"
        )
        
        return filtered_with_prefix

    def _process_bounce_modifier(
        self,
        zKey: str,
        zHorizontal: Any,
        context: Optional[Dict[str, Any]],
        walker: Optional[Any],
        display: Any
    ) -> Union[str, Any]:
        """
        Process bounce modifier (^) - executes action then returns.
        
        Args:
            zKey: Original key with modifiers
            zHorizontal: Command to execute
            context: Optional context dict
            walker: Optional walker instance
            display: Display instance for output
        
        Returns:
            - Terminal mode: "zBack" (for navigation)
            - Bifrost mode: Action result (for API consumption)
        
        Notes:
            - Resolves ^key from UI file if needed
            - Mode-specific return behavior
            - Logs mode detection for debugging
        """
        self._display_modifier(display, _LABEL_ZBOUNCE, _DEFAULT_INDENT_MODIFIER)
        
        # Resolve ^key from UI file if needed
        if isinstance(zHorizontal, str) and zHorizontal.startswith(MOD_CARET):
            zHorizontal = self._resolve_ui_key(zHorizontal, walker)
        
        # Execute the action
        result = self.dispatch.launcher.launch(zHorizontal, context=context, walker=walker)
        self.logger.framework.debug(_LOG_MSG_ZBOUNCE_RESULT, result)
        
        # Debug logging for mode detection
        self.logger.framework.debug(_LOG_MSG_ZBOUNCE_CONTEXT, context)
        self.logger.framework.debug(
            _LOG_MSG_ZBOUNCE_MODE_CHECK, 
            True,
            self.zcli.session.get(SESSION_KEY_ZMODE)
        )
        
        # Mode-specific return behavior
        if is_bifrost_mode(self.zcli.session):
            self.logger.framework.debug(_LOG_MSG_BIFROST_DETECTED)
            return result
        
        # Terminal/Walker: Return zBack for navigation
        return NAV_ZBACK

    def _process_required_modifier(
        self,
        zKey: str,
        zHorizontal: Any,
        context: Optional[Dict[str, Any]],
        walker: Optional[Any],
        display: Any
    ) -> Optional[Any]:
        """
        Process required modifier (!) - retry loop until success.
        
        Args:
            zKey: Original key with modifiers
            zHorizontal: Command to execute
            context: Optional context dict
            walker: Optional walker instance
            display: Display instance for prompts
        
        Returns:
            Action result after successful execution, or None if aborted
        
        Notes:
            - Bifrost mode: Frontend handles retry UI
            - Terminal mode: Backend retry loop with prompts
            - User can abort with "stop", "n", or "no"
            - Handles Ctrl+C and shutdown signals gracefully
        """
        self._display_modifier(display, _LABEL_ZREQUIRED, _DEFAULT_INDENT_MODIFIER)
        self.logger.framework.debug(_LOG_MSG_REQUIRED_STEP, zKey)
        
        # Execute action
        result = self.dispatch.launcher.launch(zHorizontal, context=context, walker=walker)
        self.logger.framework.debug(_LOG_MSG_REQUIRED_RESULTS, result)
        
        # Mode-aware retry handling
        is_bifrost = is_bifrost_mode(self.zcli.session)
        
        if is_bifrost:
            # Bifrost mode: Frontend handles retry UI
            if not result:
                self.logger.info(
                    f"[{MOD_EXCLAMATION}] Bifrost mode - gate failed, frontend will handle retry"
                )
            else:
                self.logger.info(f"[{MOD_EXCLAMATION}] Bifrost mode - gate passed")
            return result
        
        # Terminal mode: Backend retry loop
        while not result:
            # Check for shutdown signal
            if hasattr(self.zcli, '_shutdown_requested') and self.zcli._shutdown_requested:
                self.logger.info(
                    f"[{MOD_EXCLAMATION}] Shutdown requested, aborting retry loop for: {zKey}"
                )
                return None
            
            self.logger.warning(_LOG_MSG_REQUIREMENT_NOT_SATISFIED, zKey)
            if walker:
                try:
                    choice = display.read_string(_PROMPT_REQUIRED_CONTINUE).strip().lower()
                except (KeyboardInterrupt, EOFError):
                    self.logger.info(
                        f"[{MOD_EXCLAMATION}] Interrupted during retry prompt for: {zKey}"
                    )
                    return None
                
                if choice in [_INPUT_STOP, 'n', 'no']:
                    self.logger.framework.debug(
                        f"[{MOD_EXCLAMATION}] User declined retry for: {zKey}"
                    )
                    return None
            result = self.dispatch.launcher.launch(zHorizontal, context=context, walker=walker)
        
        self.logger.framework.debug(_LOG_MSG_REQUIREMENT_SATISFIED, zKey)
        self._display_modifier(
            display, 
            _LABEL_ZREQUIRED_RETURN, 
            _DEFAULT_INDENT_MODIFIER, 
            style=_STYLE_WAVY
        )
        return result

    # ========================================================================
    # HELPER METHODS - DRY Refactoring
    # ========================================================================

    def _display_modifier(
        self,
        display: Any,
        label: str,
        indent: int,
        style: str = _STYLE_SINGLE
    ) -> None:
        """
        Display modifier label with consistent styling.
        
        Args:
            display: Display instance (walker.display or zcli.display)
            label: Modifier label to display
            indent: Indentation level (spaces)
            style: Display style (default: "single")
        
        Example:
            self._display_modifier(display, _LABEL_ZBOUNCE, 3)
        
        Notes:
            - Uses parent dispatch color for consistency
            - Avoids repeated zDeclare calls with identical styling
            - Default style is _STYLE_SINGLE ("single")
        """
        display.zDeclare(
            label,
            color=self.dispatch.mycolor,
            indent=indent,
            style=style
        )

    def _resolve_ui_key(self, zHorizontal: str, walker: Optional[Any]) -> Any:
        """
        Resolve ^key from zUI file (for bounce modifier).
        
        When a ^key is encountered, this method attempts to look up the actual
        command from the walker's zUI file. This enables cleaner YAML declarations
        where menu items can reference actions with ^ prefix.
        
        Args:
            zHorizontal: Key string starting with ^ (e.g., "^save")
            walker: Optional walker instance with zUI context
        
        Returns:
            Resolved horizontal value from zUI, or original zHorizontal if resolution fails
        
        Example:
            # In zUI file (root block):
            # save: {zFunc: save_data}
            
            zHorizontal = self._resolve_ui_key("^save", walker)
            # Returns: {zFunc: save_data}
        
        Notes:
            - Requires walker context (returns original if walker is None)
            - Loads zUI file via zLoader (Week 6.9)
            - Strips ^ prefix before lookup
            - Gracefully handles missing files/blocks/keys
        """
        if walker:
            # Load the UI file to get the block dictionary
            zVaFile = self.zcli.zspark_obj.get(KEY_ZVAFILE)
            zBlock = self.zcli.zspark_obj.get(KEY_ZBLOCK, _DEFAULT_ZBLOCK)
            
            if zVaFile:
                raw_zFile = self.zcli.loader.handle(zVaFile)
                if raw_zFile and zBlock in raw_zFile:
                    block_dict = raw_zFile[zBlock]
                    
                    # Strip the ^ prefix to look up the actual key in the UI dict
                    lookup_key = zHorizontal[1:] if zHorizontal.startswith(MOD_CARET) else zHorizontal
                    self.logger.warning(_LOG_MSG_LOOKING_UP_KEY, lookup_key, list(block_dict.keys()))
                    
                    # Resolve key or return original if not found
                    resolved = block_dict.get(lookup_key, zHorizontal)
                    self.logger.warning(_LOG_MSG_RESOLVED_KEY, lookup_key, resolved)
                    return resolved
                else:
                    self.logger.warning(_LOG_MSG_COULD_NOT_LOAD, zBlock, zVaFile)
            else:
                self.logger.warning(_LOG_MSG_NO_ZVAFILE)
        else:
            self.logger.warning(_LOG_MSG_CANNOT_RESOLVE)
        
        # Return original if resolution fails
        return zHorizontal
