# zOS/core/L2_Core/e_zDispatch/dispatch_modules/crud_handler.py

"""
CRUD Handler Module for zDispatch Subsystem.

This module provides the CRUDHandler class, which detects and routes generic
CRUD operations that don't use explicit zRead/zData wrappers. It serves as a
smart fallback for direct data operations.

Extracted from dispatch_launcher.py as part of Phase 1 refactoring (Leaf Module).
This module has no internal dispatch dependencies - only depends on zData subsystem.

Supported Pattern:
    Direct CRUD dicts with action/model/where/fields/values keys:
    
    {"action": "read", "model": "users", "where": {"id": 1}}
    {"model": "users", "fields": ["name", "email"]}  # action defaults to "read"

Features:
    - Auto-detection of CRUD patterns (action, model, where, fields, etc.)
    - Default action to "read" if not specified
    - Validation (requires "model" key)
    - Safe mutation (creates copy before modification)

Usage Example:
    handler = CRUDHandler(zcli, display, logger)
    
    # Detect and handle CRUD dict
    cmd = {"model": "users", "where": {"id": 1}}
    result = handler.handle(cmd, context)
    # Returns: User record or None if not a CRUD pattern

Integration:
    - zData: Query execution via zcli.data.handle_request()
    - Fallback: Returns None if not a valid CRUD pattern

Thread Safety:
    - Stateless operations (no instance state mutation)
    - Creates copy of input dict (no mutation)
    - Safe for concurrent execution
"""

from zOS import Any, Dict, Optional

# Import dispatch constants
from .dispatch_constants import (
    KEY_ACTION,
    KEY_MODEL,
    KEY_TABLES,
    KEY_FIELDS,
    KEY_VALUES,
    KEY_FILTERS,
    KEY_WHERE,
    KEY_ORDER_BY,
    KEY_LIMIT,
    KEY_OFFSET,
    _DEFAULT_ACTION_READ,
    _LABEL_HANDLE_CRUD_DICT,
    _DEFAULT_INDENT_LAUNCHER,
    _DEFAULT_STYLE_SINGLE,
)

class CRUDHandler:
    """
    Detects and routes generic CRUD operations to zData subsystem.
    
    This class provides smart fallback handling for dicts that look like
    CRUD operations but don't use explicit zRead/zData wrappers. It detects
    CRUD keys and dispatches to the appropriate zData handler.
    
    Attributes:
        zcli: Root zCLI instance (provides data subsystem, logger)
        display: zDisplay instance for UI output (optional)
        logger: Logger instance for debug output
    
    Methods:
        handle(): Main entry point - detect and route CRUD operations
        is_crud_pattern(): Check if dict matches CRUD pattern
        
        Private:
        _extract_crud_request(): Build request dict for zData
        _display_handler(): Display handler label (optional styling)
    
    Example:
        handler = CRUDHandler(zcli, display, logger)
        
        # Direct CRUD dict (no zRead/zData wrapper)
        cmd = {"action": "read", "model": "users", "where": {"id": 1}}
        result = handler.handle(cmd, context)
        
        # Auto-default action
        cmd = {"model": "users"}  # action defaults to "read"
        result = handler.handle(cmd, context)
        
        # Not a CRUD pattern
        cmd = {"zFunc": "calculate"}
        result = handler.handle(cmd, context)  # Returns None
    """
    
    # CRUD detection keys
    CRUD_KEYS = {
        KEY_ACTION, KEY_MODEL, KEY_TABLES, KEY_FIELDS, KEY_VALUES,
        KEY_FILTERS, KEY_WHERE, KEY_ORDER_BY, KEY_LIMIT, KEY_OFFSET
    }
    
    def __init__(self, zcli: Any, display: Any, logger: Any) -> None:
        """
        Initialize CRUD handler.
        
        Args:
            zcli: Root zCLI instance (provides data subsystem)
            display: zDisplay instance for UI output
            logger: Logger instance for debug output
        
        Example:
            handler = CRUDHandler(zcli, display, logger)
        """
        self.zcli = zcli
        self.display = display
        self.logger = logger
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def handle(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
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
            result = handler.handle({"action": "read", "model": "users"}, context)
            result = handler.handle({"model": "users", "where": {"id": 1}}, context)
            # Second example: action defaults to "read"
        
        Notes:
            - Requires "model" key to be present (validation)
            - Detects CRUD keys: action, model, tables, fields, values, filters, where, order_by, limit, offset
            - Sets default action to "read" if not specified
            - Creates a copy to avoid mutating original dict
        """
        # Check if this is a CRUD pattern
        if not self.is_crud_pattern(zHorizontal):
            return None
        
        # Extract and build CRUD request
        req = self._extract_crud_request(zHorizontal)
        
        self.logger.framework.debug(f"[CRUDHandler] Detected generic CRUD dict => {req}")
        self._display_handler(_LABEL_HANDLE_CRUD_DICT)
        
        # Dispatch to zData subsystem
        return self.zcli.data.handle_request(req, context=context)
    
    def is_crud_pattern(self, zHorizontal: Dict[str, Any]) -> bool:
        """
        Check if dict matches CRUD pattern.
        
        A dict is considered a CRUD pattern if:
        1. It contains at least one CRUD key (action, model, where, etc.)
        2. It contains the "model" key (required for data operations)
        
        Args:
            zHorizontal: Dict to check
        
        Returns:
            True if dict matches CRUD pattern, False otherwise
        
        Example:
            handler.is_crud_pattern({"action": "read", "model": "users"})  # True
            handler.is_crud_pattern({"model": "users"})                     # True
            handler.is_crud_pattern({"where": {"id": 1}})                   # False (no model)
            handler.is_crud_pattern({"zFunc": "calculate"})                 # False (no CRUD keys)
        """
        # Validate: Must have at least one CRUD key AND "model" key
        return (
            any(k in zHorizontal for k in self.CRUD_KEYS) and 
            KEY_MODEL in zHorizontal
        )
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _extract_crud_request(self, zHorizontal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build request dict for zData subsystem.
        
        Creates a copy of the input dict and sets default action to "read"
        if not specified.
        
        Args:
            zHorizontal: CRUD dict (validated)
        
        Returns:
            Request dict ready for zData.handle_request()
        
        Example:
            cmd = {"model": "users", "where": {"id": 1}}
            req = _extract_crud_request(cmd)
            # Returns: {"action": "read", "model": "users", "where": {"id": 1}}
        
        Notes:
            - Creates copy to avoid mutating original dict
            - Sets default action to "read" if not present
        """
        # Create copy to avoid mutation
        req = dict(zHorizontal)
        
        # Set default action to "read" if not specified
        req.setdefault(KEY_ACTION, _DEFAULT_ACTION_READ)
        
        return req
    
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
                    indent=_DEFAULT_INDENT_LAUNCHER,
                    style=_DEFAULT_STYLE_SINGLE
                )
