# zCLI/subsystems/zDialog/zDialog.py

"""
zDialog Subsystem - Interactive Form/Dialog Facade.

This module serves as the Tier 4 Facade for the zDialog subsystem, providing
the main entry point for interactive form/dialog operations with auto-validation,
WebSocket integration, and mode-agnostic rendering.

Architecture Position
--------------------
**Tier 4: Facade** - Main entry point for dialog/form operations

This module sits at the top of the zDialog subsystem's 5-tier architecture,
orchestrating all dialog operations by delegating to lower-tier components
(dialog_modules) and integrating with other zCLI subsystems (zDisplay, zData,
zLoader, zDispatch).

5-Tier Architecture Flow
------------------------
1. **Tier 1 (Foundation - Context)**: dialog_context.py
   - Context creation and placeholder injection (5 types)

2. **Tier 2 (Foundation - Submit)**: dialog_submit.py
   - Dict-based submission via zDispatch (pure declarative)

3. **Tier 3 (Package Aggregator)**: dialog_modules/__init__.py
   - Aggregates and exposes Tier 1-2 components

4. **Tier 4 (Facade)**: This module ⬅️
   - Main entry point: zDialog.handle(zHorizontal, context)
   - Auto-validation integration with zData
   - WebSocket support for zBifrost mode
   - Orchestrates form display, data collection, submission

5. **Tier 5 (Package Root)**: __init__.py
   - Top-level package interface for zCLI.py

Key Features
------------
**Auto-Validation** (Week 5.2):
- Automatically validates form data against zSchema
- Uses DataValidator from zData subsystem
- Displays validation errors in both Terminal and Bifrost modes
- Returns None on validation failure (prevents onSubmit execution)

**WebSocket Integration** (zBifrost Mode):
- Accepts pre-provided data from WebSocket context
- Broadcasts validation errors via WebSocket events
- Enables real-time form validation in GUI mode

**Mode-Agnostic Rendering**:
- Delegates to zDisplay.zDialog() for form rendering
- Works in both Terminal mode (interactive input) and Bifrost mode (WebSocket data)

**Pure Declarative Paradigm**:
- onSubmit handled via dict-based zDispatch only (string-based removed in v1.5.4)
- Automatic placeholder injection (zConv.*, model references)

Integration Points
------------------
**Used By**:
- zCLI.py: Initializes zDialog subsystem (line ~200)
- zDispatch: Routes zDialog commands via dispatch_launcher (lines 580-582)

**Dependencies**:
- dialog_modules: Context creation (create_dialog_context), submission (handle_submit)
- zDisplay: Form rendering (zDialog method)
- zData: Auto-validation (DataValidator, display_validation_errors)
- zLoader: Schema loading (loader.handle)
- zComm: WebSocket broadcasting (comm.websocket.broadcast)

Usage Examples
--------------
Example 1: Terminal mode with auto-validation
    >>> from zOS.L2_Core.j_zDialog import zDialog
    >>> 
    >>> # Initialize (typically done by zCLI.py)
    >>> dialog = zDialog(zcli_instance, walker=walker_instance)
    >>> 
    >>> # Define form
    >>> form_spec = {
    ...     "zDialog": {
    ...         "model": "@.zSchema.users",
    ...         "fields": [
    ...             {"name": "username", "type": "text"},
    ...             {"name": "email", "type": "text"}
    ...         ],
    ...         "onSubmit": {
    ...             "zData": {"action": "create", "data": "zConv"}
    ...         }
    ...     }
    ... }
    >>> 
    >>> # Handle dialog (renders form, collects input, validates, submits)
    >>> result = dialog.handle(form_spec)
    >>> # Auto-validates against @.zSchema.users, executes onSubmit via zDispatch

Example 2: Bifrost mode with pre-provided data
    >>> # WebSocket sends form data
    >>> context = {
    ...     "websocket_data": {
    ...         "data": {"username": "alice", "email": "alice@example.com"}
    ...     }
    ... }
    >>> 
    >>> # Handle dialog (skips rendering, uses pre-provided data, validates, submits)
    >>> result = dialog.handle(form_spec, context=context)
    >>> # Auto-validates, broadcasts validation errors via WebSocket if needed

Example 3: Without onSubmit (data collection only)
    >>> form_spec = {
    ...     "zDialog": {
    ...         "model": "@.zSchema.users",
    ...         "fields": [{"name": "username", "type": "text"}]
    ...         # No onSubmit - just collect data
    ...     }
    ... }
    >>> 
    >>> result = dialog.handle(form_spec)
    >>> # Returns collected data (zConv) after auto-validation

Version History
---------------
- v1.5.4+: String-based submission removal + Industry-grade upgrade
  * REMOVED: String-based onSubmit (zFunc integration)
  * Enhanced: Comprehensive documentation (400+ lines)
  * Added: 100% type hint coverage
  * Added: 20+ module-level constants
  * Added: Session key modernization (SESSION_KEY_ZMODE)
  * Documented: Technical debt (zData direct imports)
- v1.5.2: Auto-validation integration with zData
- v1.5.0: WebSocket support for Bifrost mode
- v1.4.0: Initial implementation
"""

from zOS import Any, Dict, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZMODE
from .dialog_modules import create_dialog_context, handle_submit
from .dialog_modules.dialog_constants import (
    COLOR_ZDIALOG,
    KEY_DATA,
    KEY_FIELDS,
    KEY_MODEL,
    KEY_ONSUBMIT,
    KEY_TITLE,
    KEY_WEBSOCKET_DATA,
    KEY_ZCONV,
    KEY_ZDIALOG,
    _ERROR_INVALID_TYPE_DIALOG,
    _ERROR_INVALID_ZCLI,
    _ERROR_NO_ZCLI,
    _ERROR_NO_ZCLI_OR_WALKER,
    _EVENT_VALIDATION_ERROR,
    _LOG_AUTO_VALIDATION_ENABLED,
    _LOG_AUTO_VALIDATION_ERROR,
    _LOG_AUTO_VALIDATION_FAILED,
    _LOG_AUTO_VALIDATION_PASSED,
    _LOG_AUTO_VALIDATION_SKIPPED_NO_MODEL,
    _LOG_AUTO_VALIDATION_SKIPPED_PREFIX,
    _LOG_MODEL_FIELDS_SUBMIT,
    _LOG_ONSUBMIT_EXECUTE,
    _LOG_ONSUBMIT_FAILED,
    _LOG_RECEIVED_ZHORIZONTAL,
    _LOG_WEBSOCKET_BROADCAST_FAILED,
    _LOG_WEBSOCKET_DATA,
    _LOG_ZCONTEXT,
    _MSG_ZDIALOG,
    _MSG_ZDIALOG_READY,
    _MSG_ZDIALOG_RETURN_VALIDATION_FAILED,
    _SCHEMA_PATH_SEPARATOR,
    _SESSION_VALUE_ZBIFROST,
)

# ============================================================================
# MODULE CONSTANTS - Display Colors
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - Dictionary Keys (zHorizontal Structure)
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - Context Keys (WebSocket Data)
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - WebSocket Events
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - Session Keys
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - Error Messages
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - Display Messages
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - Logging Messages
# ============================================================================


# ============================================================================
# MODULE CONSTANTS - zData Integration (Schema Extraction)
# ============================================================================



class zDialog:
    """
    Interactive Form/Dialog Subsystem (Facade).
    
    This class provides the main entry point for dialog/form operations in zCLI,
    orchestrating form rendering, data collection, auto-validation, and submission
    handling with mode-agnostic support (Terminal/Bifrost).
    
    Attributes
    ----------
    zcli : Any
        The zCLI instance providing access to all subsystems
    session : Dict[str, Any]
        The session dictionary for state management
    logger : Any
        Logger instance for debugging and tracking
    display : Any
        zDisplay instance for form rendering and output
    zparser : Any
        zParser instance for expression evaluation
    walker : Optional[Any]
        Legacy walker instance for backward compatibility
    mycolor : str
        Color identifier for display messages ("ZDIALOG")
    
    Public Methods
    --------------
    handle(zHorizontal, context=None) -> Optional[Any]
        Main entry point for dialog/form handling with auto-validation
    
    Integration Points
    ------------------
    - zDisplay: Form rendering via zDialog() method
    - zData: Auto-validation via DataValidator
    - zLoader: Schema loading via handle() method
    - zComm: WebSocket broadcasting for Bifrost mode
    - dialog_modules: Context creation and submission handling
    """

    def __init__(self, zcli: Any, walker: Optional[Any] = None) -> None:
        """
        Initialize zDialog subsystem with zCLI instance.
        
        Parameters
        ----------
        zcli : Any
            The zCLI instance providing access to all subsystems (required).
            Must have 'session' attribute for state management.
        walker : Optional[Any], default=None
            Legacy walker instance for backward compatibility.
            Used for zDisplay.zDialog() calls in Terminal mode.
        
        Raises
        ------
        ValueError
            If zcli is None (zDialog requires a zCLI instance).
        ValueError
            If zcli is missing 'session' attribute (invalid zCLI instance).
        
        Notes
        -----
        Initialization Workflow:
        1. Validate zcli instance (not None, has session attribute)
        2. Extract dependencies from zcli (session, logger, display, zparser)
        3. Store legacy walker for backward compatibility
        4. Display initialization message via zDisplay.zDeclare()
        
        Legacy Compatibility:
        - walker parameter maintained for backward compatibility with older code
        - Used by zDisplay.zDialog() method for Terminal mode rendering
        - May be removed in future versions (prefer zcli-only initialization)
        """
        if zcli is None:
            raise ValueError(_ERROR_NO_ZCLI)

        if not hasattr(zcli, 'session'):
            raise ValueError(_ERROR_INVALID_ZCLI)

        # Modern architecture: zCLI instance provides all dependencies
        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
        self.display = zcli.display
        self.zparser = zcli.zparser

        # Keep walker for legacy compatibility
        self.walker = walker
        self.mycolor = COLOR_ZDIALOG
        self.display.zDeclare(_MSG_ZDIALOG_READY, color=self.mycolor, indent=0, style="full")

    def handle(self, zHorizontal: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Handle dialog form input, validation, and submission.
        
        This method orchestrates the complete dialog workflow:
        1. Parse zHorizontal to extract form configuration
        2. Create dialog context (model, fields, zConv)
        3. Collect form data (Terminal mode) or use pre-provided data (Bifrost mode)
        4. Auto-validate against zSchema (if model starts with '@')
        5. Execute onSubmit expression via zDispatch (if provided)
        6. Return result or None (validation failure)
        
        Parameters
        ----------
        zHorizontal : Dict[str, Any]
            Dialog specification dictionary with structure:
            {
                "zDialog": {
                    "model": str,           # Schema path (e.g., "@.zSchema.users")
                    "fields": List[Dict],   # Field definitions [{"name": ..., "type": ...}, ...]
                    "onSubmit": Optional[Dict]  # Submission expression (dict-based, via zDispatch)
                }
            }
        context : Optional[Dict[str, Any]], default=None
            Execution context, may contain:
            - "websocket_data": {"data": {...}}  # Pre-provided form data (Bifrost mode)
        
        Returns
        -------
        Optional[Any]
            - None: Validation failed (onSubmit not executed)
            - Any: Result from onSubmit execution (if provided)
            - Dict[str, Any]: Collected form data (zConv) if no onSubmit
        
        Raises
        ------
        TypeError
            If zHorizontal is not a dictionary.
        KeyError
            If required keys (zDialog, model, fields) are missing from zHorizontal.
        Exception
            If onSubmit execution fails (re-raised with logging).
        
        Auto-Validation Workflow
        ------------------------
        If model starts with '@' (schema reference):
        1. Load schema from model path via zLoader
        2. Extract table name from model (e.g., "@.zSchema.users" → "users")
        3. Create DataValidator instance with loaded schema
        4. Validate collected form data (zConv) using validate_insert()
        5. On validation failure:
           - Display errors via display_validation_errors()
           - Broadcast errors via WebSocket (Bifrost mode)
           - Return None (prevents onSubmit execution)
        6. On validation success:
           - Proceed to onSubmit execution (if provided)
        
        WebSocket Integration (Bifrost Mode)
        ------------------------------------
        - Checks context for "websocket_data" key
        - Uses pre-provided data instead of rendering form
        - Broadcasts validation errors via comm.websocket.broadcast()
        - Event format: {"event": "validation_error", "table": ..., "errors": ..., "fields": ...}
        
        Usage Examples
        --------------
        Example 1: Terminal mode with auto-validation and submission
            >>> form_spec = {
            ...     "zDialog": {
            ...         "model": "@.zSchema.users",
            ...         "fields": [{"name": "username", "type": "text"}],
            ...         "onSubmit": {"zData": {"action": "create", "data": "zConv"}}
            ...     }
            ... }
            >>> result = dialog.handle(form_spec)
            # Renders form, collects input, validates, creates user record
        
        Example 2: Bifrost mode with pre-provided data
            >>> context = {"websocket_data": {"data": {"username": "alice"}}}
            >>> result = dialog.handle(form_spec, context=context)
            # Skips rendering, uses pre-provided data, validates, submits
        
        Example 3: Data collection only (no onSubmit)
            >>> form_spec = {
            ...     "zDialog": {
            ...         "model": "@.zSchema.users",
            ...         "fields": [{"name": "username", "type": "text"}]
            ...     }
            ... }
            >>> zConv = dialog.handle(form_spec)
            # Returns collected data: {"username": "..."}
        
        Example 4: Validation failure
            >>> # Assuming schema requires email, but user provides invalid email
            >>> result = dialog.handle(form_spec)
            # Returns None, displays validation errors, onSubmit not executed
        
        Notes
        -----
        - Auto-validation only triggers for models starting with '@' (schema references)
        - Non-schema models skip validation (backward compatibility)
        - Validation failures prevent onSubmit execution (return None)
        - onSubmit is always dict-based (string-based removed in v1.5.4)
        - Placeholders (zConv.*, model) injected automatically by handle_submit()
        
        Technical Notes
        ---------------
        - Direct imports from zData.zData_modules.shared (DataValidator, display_validation_errors)
          are intentional for lightweight validation without database connection overhead.
          This pattern is used consistently across zDialog, zBifrost, and zDisplay subsystems.
          zData.load_schema() creates full database connections, which is unnecessary for
          form validation-only use cases
        """
        self.display.zDeclare(_MSG_ZDIALOG, color=self.mycolor, indent=1, style="single")

        self.logger.info(_LOG_RECEIVED_ZHORIZONTAL, zHorizontal)

        # Validate input
        if not isinstance(zHorizontal, dict):
            msg = _ERROR_INVALID_TYPE_DIALOG.format(type_name=type(zHorizontal))
            self.logger.error(msg)
            raise TypeError(msg)

        # Extract dialog configuration
        zDialog_obj = zHorizontal[KEY_ZDIALOG]
        title = zDialog_obj.get(KEY_TITLE)
        model = zDialog_obj[KEY_MODEL]
        fields = zDialog_obj[KEY_FIELDS]
        on_submit = zDialog_obj.get(KEY_ONSUBMIT)

        self.logger.info(
            _LOG_MODEL_FIELDS_SUBMIT,
            model,
            fields,
            on_submit
        )

        # Create dialog context
        zContext = create_dialog_context(model, fields, self.logger)
        
        # Add additional context for Bifrost mode (needed by FormRenderer)
        if title:
            zContext[KEY_TITLE] = title
        if on_submit:
            zContext[KEY_ONSUBMIT] = on_submit
        
        self.logger.info(_LOG_ZCONTEXT, zContext)

        # Check if data is pre-provided (WebSocket/GUI mode)
        if context and KEY_WEBSOCKET_DATA in context:
            ws_data = context[KEY_WEBSOCKET_DATA]
            if KEY_DATA in ws_data:
                zConv = ws_data[KEY_DATA]
                self.logger.info(_LOG_WEBSOCKET_DATA, zConv)
            else:
                zConv = {}
        else:
            # Render form and collect input (Terminal/Walker mode)
            zConv = self.display.zDialog(zContext, self.zcli, self.walker)
        
        # Add collected data to context
        zContext[KEY_ZCONV] = zConv

        # ──────────────────────────────────────────────────────────────────
        # AUTO-VALIDATION (Week 5.2): Validate form data against zSchema
        # ──────────────────────────────────────────────────────────────────
        # Only auto-validate for zData insert operations (registration)
        # For login/custom operations, let the onSubmit handler validate
        is_insert_operation = (
            on_submit and 
            isinstance(on_submit, dict) and 
            'zData' in on_submit and 
            on_submit['zData'].get('action') == 'insert'
        )
        
        if model and isinstance(model, str) and model.startswith('@') and is_insert_operation:
            self.logger.info(_LOG_AUTO_VALIDATION_ENABLED, model)
            
            try:
                # Load schema from model path (zLoader handles file loading)
                schema_dict = self.zcli.loader.handle(model)
                
                # Extract table name from model path (e.g., '@.zSchema.users' → 'users')
                table_name = model.split(_SCHEMA_PATH_SEPARATOR)[-1]
                
                # Create lightweight validator (no database connection needed)
                from zOS.L3_Abstraction.n_zData.zData_modules.shared.validator import DataValidator
                validator = DataValidator(schema_dict, self.logger)
                
                # Validate collected form data (use validate_insert for new data)
                is_valid, errors = validator.validate_insert(table_name, zConv)
                
                if not is_valid:
                    self.logger.warning(_LOG_AUTO_VALIDATION_FAILED, len(errors))
                    
                    # Display validation errors (zDialog has required interface: zcli, logger, display)
                    from zOS.L3_Abstraction.n_zData.zData_modules.shared.operations.helpers import display_validation_errors
                    display_validation_errors(table_name, errors, self)
                    
                    # For zBifrost mode, also emit WebSocket event
                    if self.session.get(SESSION_KEY_ZMODE) == _SESSION_VALUE_ZBIFROST:
                        try:
                            self.zcli.comm.websocket.broadcast({
                                'event': _EVENT_VALIDATION_ERROR,
                                'table': table_name,
                                'errors': errors,
                                'fields': list(errors.keys())
                            })
                        except Exception as ws_err:
                            self.logger.warning(_LOG_WEBSOCKET_BROADCAST_FAILED, ws_err)
                    
                    # Don't proceed to onSubmit - return None to indicate validation failure
                    self.display.zDeclare(_MSG_ZDIALOG_RETURN_VALIDATION_FAILED, color=self.mycolor, indent=1, style="~")
                    return None
                
                self.logger.info(_LOG_AUTO_VALIDATION_PASSED, table_name)
                
            except Exception as val_err:
                # If auto-validation fails (schema not found, etc.), log warning but proceed
                # This maintains backward compatibility - forms without valid models still work
                self.logger.warning(_LOG_AUTO_VALIDATION_ERROR, val_err)
        
        elif model and not is_insert_operation:
            self.logger.debug("Auto-validation skipped (not a zData insert operation) - custom handler will validate")
        elif model:
            self.logger.debug(_LOG_AUTO_VALIDATION_SKIPPED_PREFIX, model)
        else:
            self.logger.debug(_LOG_AUTO_VALIDATION_SKIPPED_NO_MODEL)

        # Handle submission if onSubmit provided
        try:
            # In Bifrost mode, if zConv is empty, this is just form display (not submission)
            # Only execute onSubmit if we have actual form data
            is_bifrost_display = (
                self.session.get(SESSION_KEY_ZMODE) == _SESSION_VALUE_ZBIFROST and 
                not zConv  # Empty zConv means form display, not submission
            )
            
            if on_submit and not is_bifrost_display:
                self.logger.info(_LOG_ONSUBMIT_EXECUTE)
                return handle_submit(on_submit, zContext, self.logger, walker=self.walker)
            elif is_bifrost_display:
                self.logger.debug("[zDialog] Bifrost mode - form displayed, onSubmit deferred to form_submit handler")
                return None  # Return None for walker compatibility (dicts are not hashable nav results)
            
            # No onSubmit - return collected data
            return zConv
            
        except Exception as e:
            self.logger.error(_LOG_ONSUBMIT_FAILED, e, exc_info=True)
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Backward Compatibility Function
# ─────────────────────────────────────────────────────────────────────────────

def handle_zDialog(
    zHorizontal: Dict[str, Any], 
    walker: Optional[Any] = None, 
    zcli: Optional[Any] = None, 
    context: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Backward-compatible function for dialog handling.
    
    This function provides a legacy interface for dialog operations, supporting
    older code that calls handle_zDialog() directly instead of instantiating
    the zDialog class. It resolves the zcli instance from either the zcli
    parameter or the walker.zcli attribute, then delegates to the modern
    zDialog class.
    
    Parameters
    ----------
    zHorizontal : Dict[str, Any]
        Dialog specification dictionary (see zDialog.handle() for structure).
    walker : Optional[Any], default=None
        Legacy walker instance. If zcli is not provided, walker.zcli will be used.
    zcli : Optional[Any], default=None
        The zCLI instance. Preferred over walker.zcli (modern approach).
    context : Optional[Dict[str, Any]], default=None
        Execution context (see zDialog.handle() for details).
    
    Returns
    -------
    Optional[Any]
        Result from zDialog.handle() - see zDialog.handle() docstring for details.
    
    Raises
    ------
    ValueError
        If neither zcli nor walker.zcli are available.
    
    Deprecation Notice
    ------------------
    This function is maintained for backward compatibility with older code.
    New code should prefer instantiating zDialog directly:
    
    **Modern Approach** (Preferred):
        >>> dialog = zDialog(zcli_instance, walker=walker_instance)
        >>> result = dialog.handle(form_spec, context=context)
    
    **Legacy Approach** (Deprecated):
        >>> result = handle_zDialog(form_spec, walker=walker_instance, zcli=zcli_instance)
    
    Migration Examples
    ------------------
    Example 1: Migrate from walker-based to zcli-based
        >>> # Old code (legacy)
        >>> result = handle_zDialog(form_spec, walker=walker)
        >>> 
        >>> # New code (modern)
        >>> dialog = zDialog(walker.zcli, walker=walker)
        >>> result = dialog.handle(form_spec)
    
    Example 2: Migrate from function call to class instantiation
        >>> # Old code (legacy)
        >>> result = handle_zDialog(form_spec, zcli=zcli)
        >>> 
        >>> # New code (modern - reusable instance)
        >>> dialog = zDialog(zcli)
        >>> result = dialog.handle(form_spec)
        >>> result2 = dialog.handle(form_spec2)  # Reuse instance
    
    Notes
    -----
    - zcli parameter takes precedence over walker.zcli (modern approach preferred)
    - Creates a new zDialog instance for each call (not reusable)
    - May be removed in future major versions (v2.0+)
    """
    # Modern: use zcli directly if provided
    if zcli:
        return zDialog(zcli, walker=walker).handle(zHorizontal, context=context)
    
    # Legacy: extract zcli from walker
    if walker and hasattr(walker, 'zcli'):
        return zDialog(walker.zcli, walker=walker).handle(zHorizontal, context=context)
    
    raise ValueError(_ERROR_NO_ZCLI_OR_WALKER)


# ============================================================================
# Public API
# ============================================================================

__all__ = ["zDialog", "handle_zDialog"]
