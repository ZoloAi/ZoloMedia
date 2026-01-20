# zOS/core/L2_Core/e_zDispatch/dispatch_modules/subsystem_router.py

"""
Subsystem Router Module for zDispatch Subsystem.

This module provides the SubsystemRouter class, which routes commands to
all subsystems (zFunc, zDialog, zDisplay, zRead, zData, etc.). It acts as
a central dispatcher with focused routing logic.

Extracted from dispatch_launcher.py as part of Phase 2 refactoring.
This module depends on all subsystems but has no internal dispatch dependencies.

Supported Subsystems:
    - zDisplay: UI rendering and display events
    - zFunc: Function execution and plugin invocation
    - zDialog: Interactive forms and user input
    - zRead/zData: Data operations (CRUD)
    - zNavigation: zLink (via NavigationHandler)
    - zAuth: zLogin/zLogout (via AuthHandler)

Features:
    - Focused routing per subsystem (one method per command type)
    - Context passing for %data.* variable resolution
    - Plugin invocation detection (& prefix)
    - Default action setting for data operations
    - Integration with Phase 1 handlers (Auth, Navigation)

Usage Example:
    router = SubsystemRouter(zcli, display, logger, auth_handler, nav_handler)
    
    # Route zDisplay command
    result = router.route_zdisplay({"zDisplay": {"event": "text", "content": "..."}}, context)
    
    # Route zFunc command
    result = router.route_zfunc({"zFunc": "calculate"}, context)
    
    # Route zLogin command (delegates to AuthHandler)
    result = router.route_zlogin({"zLogin": "zCloud"}, context)

Integration:
    - zDisplay: Display events via zcli.display.handle()
    - zFunc: Function execution via zcli.zfunc.handle()
    - zDialog: Interactive dialogs via handle_zDialog()
    - zData: Data operations via zcli.data.handle_request()
    - zNavigation: Navigation via zcli.navigation.handle_zLink()
    - zAuth: Authentication via auth_handler
    - NavigationHandler: zLink/zDelta routing
    - AuthHandler: zLogin/zLogout routing

Thread Safety:
    - Stateless routing (no instance state mutation)
    - Safe for concurrent execution
"""

from zOS import Any, Dict, Optional, ast

# Import dispatch constants
from .dispatch_constants import (
    KEY_ZDISPLAY,
    KEY_ZFUNC,
    KEY_ZDIALOG,
    KEY_ZLINK,
    KEY_ZDELTA,
    KEY_ZREAD,
    KEY_ZDATA,
    KEY_ZLOGIN,
    KEY_ZLOGOUT,
    KEY_ACTION,
    KEY_MODEL,
    CMD_PREFIX_ZREAD,
    CMD_PREFIX_ZWIZARD,
    PLUGIN_PREFIX,
    NAV_ZBACK,
    _LABEL_HANDLE_ZFUNC_DICT,
    _LABEL_HANDLE_ZREAD_STRING,
    _LABEL_HANDLE_ZREAD_DICT,
    _LABEL_HANDLE_ZDATA_DICT,
    _DEFAULT_ACTION_READ,
    _DEFAULT_INDENT_HANDLER,
    _DEFAULT_INDENT_LAUNCHER,
    _DEFAULT_STYLE_SINGLE,
)

# Import dispatch helpers
from .dispatch_helpers import is_bifrost_mode

class SubsystemRouter:
    """
    Routes commands to all subsystems (zFunc, zDialog, zDisplay, etc.).
    
    This class provides centralized routing logic for all subsystem commands,
    with integration to Phase 1 handlers (AuthHandler, NavigationHandler) for
    focused delegation.
    
    Attributes:
        zcli: Root zCLI instance (provides subsystem access)
        display: zDisplay instance for UI output
        logger: Logger instance for debug output
        auth_handler: AuthHandler instance (for zLogin/zLogout)
        nav_handler: NavigationHandler instance (for zLink/zDelta)
    
    Methods:
        route_zdisplay(): Route zDisplay command
        route_zfunc(): Route zFunc command (function/plugin)
        route_zdialog(): Route zDialog command
        route_zlink(): Route zLink command (delegates to NavigationHandler)
        route_zdelta(): Route zDelta command (delegates to NavigationHandler)
        route_zlogin(): Route zLogin command (delegates to AuthHandler)
        route_zlogout(): Route zLogout command (delegates to AuthHandler)
        route_zwizard(): Route zWizard command
        route_zread_string(): Route zRead string command
        route_zread_dict(): Route zRead dict command
        route_zdata(): Route zData dict command
        
        Private:
        _display_handler(): Display handler label
        _log_detected(): Log command detection
        _set_default_action(): Set default action for data operations
    
    Example:
        router = SubsystemRouter(zcli, display, logger, auth_handler, nav_handler)
        
        # Display command
        result = router.route_zdisplay({"zDisplay": {"event": "text", ...}}, context)
        
        # Function command
        result = router.route_zfunc({"zFunc": "calculate"}, context)
        
        # Auth command (delegates to AuthHandler)
        result = router.route_zlogin({"zLogin": "zCloud"}, context)
        
        # Navigation command (delegates to NavigationHandler)
        result = router.route_zlink({"zLink": "menu:users"}, walker)
    """
    
    def __init__(
        self,
        zcli: Any,
        display: Any,
        logger: Any,
        auth_handler: Optional[Any] = None,
        nav_handler: Optional[Any] = None
    ) -> None:
        """
        Initialize subsystem router.
        
        Args:
            zcli: Root zCLI instance (provides subsystem access)
            display: zDisplay instance for UI output
            logger: Logger instance for debug output
            auth_handler: AuthHandler instance (optional, for zLogin/zLogout)
            nav_handler: NavigationHandler instance (optional, for zLink/zDelta)
        
        Example:
            router = SubsystemRouter(zcli, display, logger, auth_handler, nav_handler)
        """
        self.zcli = zcli
        self.display = display
        self.logger = logger
        self.auth_handler = auth_handler
        self.nav_handler = nav_handler
    
    # ========================================================================
    # PUBLIC API - Subsystem Routing
    # ========================================================================
    
    def route_zdisplay(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Route zDisplay command (legacy format).
        
        Args:
            zHorizontal: Dict containing KEY_ZDISPLAY
            context: Optional context dict (for %data.* variable resolution)
        
        Returns:
            Result from display event (e.g. user input for read_string/selection,
            None for display-only events)
        
        Example:
            result = router.route_zdisplay(
                {"zDisplay": {"event": "text", "content": "Hello"}},
                context
            )
        
        Notes:
            - Passes context for %data.* variable resolution
            - Uses display.handle() to dispatch to event handlers
        """
        self._log_detected("zDisplay (wrapped)")
        display_data = zHorizontal[KEY_ZDISPLAY]
        
        if isinstance(display_data, dict):
            # Pass context for %data.* variable resolution
            if context and "_resolved_data" in context:
                display_data["_context"] = context
            
            # Use display.handle() to pass through ALL parameters automatically
            result = self.display.handle(display_data)
            return result
        else:
            self.logger.framework.warning(
                f"[SubsystemRouter] display_data is not a dict! Type: {type(display_data)}"
            )
        
        return None
    
    def route_zfunc(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zFunc command (function execution or plugin invocation).
        
        Args:
            zHorizontal: Dict containing KEY_ZFUNC
            context: Optional context dict (passed to function/plugin)
        
        Returns:
            Function/plugin execution result
        
        Example:
            result = router.route_zfunc({"zFunc": "calculate"}, context)
            result = router.route_zfunc({"zFunc": "&my_plugin"}, context)
        
        Notes:
            - Detects plugin invocations (& prefix)
            - Passes context to function/plugin
            - Logs context keys for debugging
        """
        self._log_detected("zFunc (dict)")
        self._display_handler(_LABEL_HANDLE_ZFUNC_DICT)
        func_spec = zHorizontal[KEY_ZFUNC]
        
        # DEBUG: Log context to diagnose zHat passing
        self.logger.debug(
            f"[SubsystemRouter] zFunc context type: {type(context)}, "
            f"keys: {context.keys() if context else 'None'}"
        )
        if context and "zHat" in context:
            self.logger.debug(f"[SubsystemRouter] zHat found in context: {context['zHat']}")
        
        # Check if it's a plugin invocation (starts with &)
        if isinstance(func_spec, str) and func_spec.startswith(PLUGIN_PREFIX):
            self._log_detected(f"plugin invocation in zFunc: {func_spec}")
            return self.zcli.zparser.resolve_plugin_invocation(func_spec, context=context)
        
        # Non-plugin zFunc calls
        return self.zcli.zfunc.handle(func_spec, zContext=context)
    
    def route_zdialog(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        walker: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Route zDialog command (interactive form/dialog).
        
        Args:
            zHorizontal: Dict containing KEY_ZDIALOG
            context: Optional context dict
            walker: Optional walker instance
        
        Returns:
            Dialog execution result
        
        Example:
            result = router.route_zdialog(
                {"zDialog": {"fields": ["username", "password"]}},
                context,
                walker
            )
        """
        from ...j_zDialog import handle_zDialog
        self._log_detected("zDialog")
        return handle_zDialog(zHorizontal, zcli=self.zcli, walker=walker, context=context)
    
    def route_zlink(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Route zLink command (delegates to NavigationHandler).
        
        Args:
            zHorizontal: Dict containing KEY_ZLINK
            walker: Walker instance (required for navigation)
        
        Returns:
            Navigation result, or None if nav_handler not available
        
        Example:
            result = router.route_zlink({"zLink": "menu:users"}, walker)
        """
        if self.nav_handler:
            return self.nav_handler.handle_zlink(zHorizontal, walker)
        else:
            self.logger.warning("[SubsystemRouter] NavigationHandler not available for zLink")
            return None
    
    def route_zdelta(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Route zDelta command (delegates to NavigationHandler).
        
        Args:
            zHorizontal: Dict containing KEY_ZDELTA
            walker: Walker instance (required for navigation)
        
        Returns:
            Navigation result, or None if nav_handler not available
        
        Example:
            result = router.route_zdelta({"zDelta": "$Settings"}, walker)
        """
        if self.nav_handler:
            return self.nav_handler.handle_zdelta(zHorizontal, walker)
        else:
            self.logger.warning("[SubsystemRouter] NavigationHandler not available for zDelta")
            return None
    
    def route_zlogin(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zLogin command (delegates to AuthHandler).
        
        Args:
            zHorizontal: Dict containing KEY_ZLOGIN
            context: Optional context dict (contains zConv, model from zDialog)
        
        Returns:
            Login result, or None if auth_handler not available
        
        Example:
            result = router.route_zlogin({"zLogin": "zCloud"}, context)
        """
        if self.auth_handler:
            return self.auth_handler.handle_zlogin(zHorizontal, context)
        else:
            self.logger.warning("[SubsystemRouter] AuthHandler not available for zLogin")
            return None
    
    def route_zlogout(
        self,
        zHorizontal: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Route zLogout command (delegates to AuthHandler).
        
        Args:
            zHorizontal: Dict containing KEY_ZLOGOUT
        
        Returns:
            Logout result, or None if auth_handler not available
        
        Example:
            result = router.route_zlogout({"zLogout": "zCloud"})
        """
        if self.auth_handler:
            return self.auth_handler.handle_zlogout(zHorizontal)
        else:
            self.logger.warning("[SubsystemRouter] AuthHandler not available for zLogout")
            return None
    
    def route_zwizard(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zWizard command.
        
        Args:
            zHorizontal: Dict command with "zWizard" key
            walker: Optional walker instance (preferred for navigation context)
            context: Optional context dict with mode metadata
        
        Returns:
            - Bifrost mode: zHat (actual wizard result)
            - Terminal/Walker mode: "zBack" (for navigation) or zHat (no walker)
        
        Example:
            result = router.route_zwizard({"zWizard": {"steps": [...]}}, walker, context)
        """
        self._log_detected("zWizard (dict)")
        
        # Use modern OOP API - walker extends wizard, so it has handle()
        if walker:
            zHat = walker.handle(zHorizontal["zWizard"])
        else:
            zHat = self.zcli.wizard.handle(zHorizontal["zWizard"])
        
        # Mode-specific return behavior
        if is_bifrost_mode(self.zcli.session):
            # Bifrost: Return zHat for API consumption
            return zHat
        
        # Terminal/Walker: Return zBack for navigation (or zHat if no walker)
        return NAV_ZBACK if walker else zHat
    
    def route_zread_string(
        self,
        zHorizontal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zRead string command.
        
        Parses the model name from string format and dispatches to zData subsystem
        with default action "read".
        
        Args:
            zHorizontal: String command in format "zRead(...)"
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request() (typically dict or list)
        
        Example:
            result = router.route_zread_string("zRead(users)", context)
            # Equivalent to: {"action": "read", "model": "users"}
        """
        self._log_detected("zRead request (string)")
        self._display_handler(_LABEL_HANDLE_ZREAD_STRING)
        
        # Extract and build request
        inner = zHorizontal[len(CMD_PREFIX_ZREAD):-1].strip()
        req = {KEY_ACTION: _DEFAULT_ACTION_READ}
        if inner:
            req[KEY_MODEL] = inner
        
        self.logger.framework.debug(f"[SubsystemRouter] Dispatching zRead (string): {req}")
        return self.zcli.data.handle_request(req, context=context)
    
    def route_zread_dict(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zRead dict command.
        
        Extracts the read request from dict format and dispatches to zData subsystem
        with default action "read".
        
        Args:
            zHorizontal: Dict command with "zRead" key
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request() (typically dict or list)
        
        Example:
            result = router.route_zread_dict(
                {"zRead": {"model": "users", "where": {"id": 1}}},
                context
            )
        """
        self._log_detected("zRead (dict)")
        self._display_handler(_LABEL_HANDLE_ZREAD_DICT)
        
        # Extract and normalize request
        req = zHorizontal.get(KEY_ZREAD) or {}
        if isinstance(req, str):
            req = {KEY_MODEL: req}
        
        self._set_default_action(req)
        
        self.logger.framework.debug(f"[SubsystemRouter] Dispatching zRead (dict): {req}")
        return self.zcli.data.handle_request(req, context=context)
    
    def route_zdata(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zData dict command.
        
        Extracts the data request from dict format and dispatches to zData subsystem
        with default action "read".
        
        Args:
            zHorizontal: Dict command with "zData" key
            context: Optional context dict for data operation
        
        Returns:
            Data result from zData.handle_request() (typically dict or list)
        
        Example:
            result = router.route_zdata(
                {"zData": {"action": "create", "model": "users", ...}},
                context
            )
        """
        self._log_detected("zData (dict)")
        self._display_handler(_LABEL_HANDLE_ZDATA_DICT)
        
        # Extract and normalize request
        req = zHorizontal.get(KEY_ZDATA) or {}
        if isinstance(req, str):
            req = {KEY_MODEL: req}
        
        self._set_default_action(req)
        
        self.logger.framework.debug(f"[SubsystemRouter] Dispatching zData (dict): {req}")
        return self.zcli.data.handle_request(req, context=context)
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _set_default_action(self, req: Dict[str, Any]) -> None:
        """
        Set default action for data request if not specified.
        
        Args:
            req: Request dict to modify (mutated in place)
        
        Notes:
            - Mutates req dict in place
            - Uses dict.setdefault() to avoid overwriting existing action
        """
        req.setdefault(KEY_ACTION, _DEFAULT_ACTION_READ)
    
    def _display_handler(self, label: str) -> None:
        """
        Display handler label with consistent styling.
        
        Args:
            label: Handler label to display (from dispatch_constants)
        
        Notes:
            - Uses zDisplay.zDeclare for consistent styling
            - Style is always "single" for handler labels
            - Color comes from parent dispatch instance (via self.display)
        """
        if self.display:
            # Get color from display instance (set by parent dispatcher)
            color = getattr(self.display, 'mycolor', None)
            if color:
                self.display.zDeclare(
                    label,
                    color=color,
                    indent=_DEFAULT_INDENT_HANDLER,
                    style=_DEFAULT_STYLE_SINGLE
                )
    
    def _log_detected(self, message: str) -> None:
        """
        Log detected command with consistent format.
        
        Args:
            message: Detection message (e.g., "zFunc request", "plugin invocation")
        
        Notes:
            - Prefixes all messages with "SubsystemRouter: " for clarity
            - Uses framework.debug level for all command detection logs
        """
        self.logger.framework.debug(f"[SubsystemRouter] Detected {message}")
