# zOS/core/L2_Core/e_zDispatch/dispatch_modules/auth_handler.py

"""
Authentication Handler Module for zDispatch Subsystem.

This module provides the AuthHandler class, which routes zLogin and zLogout
commands to the zAuth subsystem. It handles context building and parameter
extraction for authentication operations.

Extracted from dispatch_launcher.py as part of Phase 1 refactoring (Leaf Module).
This module has no internal dispatch dependencies - only depends on zAuth subsystem.

Supported Commands:
    - zLogin: Authenticate user with app/platform credentials
    - zLogout: Terminate user session for specific app

Features:
    - Context building from zDialog responses
    - Model and field extraction
    - zConv (conversation/form data) passing
    - Debug logging for auth operations

Usage Example:
    handler = AuthHandler(zcli, display, logger)
    
    # zLogin command
    result = handler.handle_zlogin(
        {"zLogin": "zCloud"},
        context={"zConv": {"username": "...", "password": "..."}, "model": "users"}
    )
    
    # zLogout command
    result = handler.handle_zlogout({"zLogout": "zCloud"})

Integration:
    - zAuth: Authentication operations via handle_zLogin/handle_zLogout
    - zDialog: Receives form data (zConv) from dialog responses
    - zDisplay: Handler label display (optional)

Thread Safety:
    - Stateless operations (no instance state mutation)
    - Safe for concurrent execution
"""

from zOS import Any, Dict, Optional

# Import zAuth subsystem handlers
from zOS.L2_Core.d_zAuth.zAuth_modules import handle_zLogin, handle_zLogout

# Import dispatch constants
from .dispatch_constants import (
    KEY_ZLOGIN,
    KEY_ZLOGOUT,
    _LABEL_HANDLE_ZLOGIN,
    _LABEL_HANDLE_ZLOGOUT,
    _DEFAULT_INDENT_HANDLER,
    _DEFAULT_STYLE_SINGLE,
)

class AuthHandler:
    """
    Routes authentication commands (zLogin, zLogout) to zAuth subsystem.
    
    This class provides focused routing for authentication operations,
    extracting context and parameters from command dicts and dispatching
    to the appropriate zAuth handlers.
    
    Attributes:
        zcli: Root zCLI instance (provides session, auth, logger)
        display: zDisplay instance for UI output (optional)
        logger: Logger instance for debug output
    
    Methods:
        handle_zlogin(): Route zLogin command to zAuth
        handle_zlogout(): Route zLogout command to zAuth
        
        Private:
        _build_auth_context(): Build zContext dict for zAuth operations
        _display_handler(): Display handler label (optional styling)
    
    Example:
        handler = AuthHandler(zcli, display, logger)
        
        # Login with dialog data
        login_result = handler.handle_zlogin(
            {"zLogin": "zCloud"},
            context={"zConv": {"username": "john", "password": "***"}, "model": "users"}
        )
        
        # Logout
        logout_result = handler.handle_zlogout({"zLogout": "zCloud"})
    """
    
    def __init__(self, zcli: Any, display: Any, logger: Any) -> None:
        """
        Initialize authentication handler.
        
        Args:
            zcli: Root zCLI instance (provides session, auth)
            display: zDisplay instance for UI output
            logger: Logger instance for debug output
        
        Example:
            handler = AuthHandler(zcli, display, logger)
        """
        self.zcli = zcli
        self.display = display
        self.logger = logger
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def handle_zlogin(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Route zLogin command to zAuth subsystem.
        
        Extracts authentication parameters from command dict and context,
        builds zContext, and dispatches to zAuth.handle_zLogin().
        
        Args:
            zHorizontal: Dict containing KEY_ZLOGIN (app name or auth type)
            context: Optional context dict (contains zConv, model from zDialog)
        
        Returns:
            Login result from zAuth (typically user session dict or error)
        
        Example:
            # After zDialog collected credentials
            result = handler.handle_zlogin(
                {"zLogin": "zCloud"},
                context={
                    "zConv": {"username": "john", "password": "***"},
                    "model": "users",
                    "fields": ["username", "password"]
                }
            )
        
        Notes:
            - zConv contains form data from zDialog
            - model specifies which data model to authenticate against
            - fields list is passed for validation
            - Logs authentication attempt and result
        """
        self._display_handler(_LABEL_HANDLE_ZLOGIN)
        
        # Get app name from zLogin value (string)
        app_or_type = zHorizontal[KEY_ZLOGIN]
        
        self.logger.debug(f"[AuthHandler] zLogin: {app_or_type}")
        
        # Build zContext from command and context
        zContext = self._build_auth_context(zHorizontal, context)
        
        # Extract zConv (conversation/form data)
        zConv = context.get("zConv", {}) if context else {}
        
        self.logger.debug(
            f"[AuthHandler] Calling zLogin with zConv keys: {list(zConv.keys())}, "
            f"model: {zContext.get('model')}"
        )
        
        # Call zAuth subsystem
        result = handle_zLogin(
            app_or_type=app_or_type,
            zConv=zConv,
            zContext=zContext,
            zcli=self.zcli
        )
        
        self.logger.debug(f"[AuthHandler] zLogin result: {result}")
        return result
    
    def handle_zlogout(
        self,
        zHorizontal: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Route zLogout command to zAuth subsystem.
        
        Extracts app name and dispatches to zAuth.handle_zLogout().
        No context or form data needed for logout.
        
        Args:
            zHorizontal: Dict containing KEY_ZLOGOUT (app name)
        
        Returns:
            Logout result from zAuth (typically success confirmation)
        
        Example:
            result = handler.handle_zlogout({"zLogout": "zCloud"})
        
        Notes:
            - No zConv or model needed (just app name)
            - Terminates session for specified app
            - Logs logout attempt and result
        """
        self._display_handler(_LABEL_HANDLE_ZLOGOUT)
        
        # Get app name from zLogout value (string)
        app_name = zHorizontal[KEY_ZLOGOUT]
        
        self.logger.debug(f"[AuthHandler] zLogout: {app_name}")
        
        # zLogout doesn't need zConv/model, pass empty dicts for consistency
        zConv = {}
        zContext = {}
        
        # Call zAuth subsystem
        result = handle_zLogout(
            app_name=app_name,
            zConv=zConv,
            zContext=zContext,
            zcli=self.zcli
        )
        
        self.logger.debug(f"[AuthHandler] zLogout result: {result}")
        return result
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _build_auth_context(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build zContext dict for zAuth operations.
        
        Extracts model, fields, and zConv from context (set by zDialog)
        and builds the context dict expected by zAuth subsystem.
        
        Args:
            zHorizontal: Command dict (may contain 'model' key)
            context: Optional context dict (from zDialog)
        
        Returns:
            zContext dict with model, fields, zConv
        
        Example:
            context = {"zConv": {...}, "model": "users", "fields": ["username", "password"]}
            zContext = _build_auth_context(cmd, context)
            # Returns: {"model": "users", "fields": [...], "zConv": {...}}
        
        Notes:
            - Model can come from context or zHorizontal (fallback)
            - zConv is always from context (dialog form data)
            - fields list passed for validation
        """
        # Get zConv and model from context (set by zDialog)
        zConv = context.get("zConv", {}) if context else {}
        model = context.get("model") if context else None
        
        # If model wasn't in context, check if it was injected into zHorizontal
        if not model and "model" in zHorizontal:
            model = zHorizontal["model"]
        
        # Build zContext for zAuth
        return {
            "model": model,
            "fields": context.get("fields", []) if context else [],
            "zConv": zConv
        }
    
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
