# zCLI/L2_Core/c_zDisplay/zDisplay_modules/f_orchestration/system_event_dialog.py

"""
System Dialog Events - zDialog
================================

This module provides form dialog display and input collection with field-by-field
validation support. zDialog orchestrates the complete form workflow from display
to validation to data collection.

Purpose:
    - Display form dialogs with field prompts
    - Collect user input for each field
    - Validate fields against schema (if provided)
    - Retry on validation errors
    - Support both Terminal and Bifrost modes

Public Methods:
    zDialog(context, _zcli, _walker)
        Display form dialog and collect validated input

Private Helpers:
    _log_zdialog_start(context, _zcli)
        Log zDialog start (debug mode only)
        
    _try_zdialog_gui_mode(context, _zcli)
        Try to send zDialog event to Bifrost
        
    _setup_zdialog_validator(context, _zcli)
        Setup schema validator for field-by-field validation
        
    _collect_zdialog_fields(fields, validator, table_name, logger)
        Collect all form fields with validation
        
    (+ 6 more helpers for validation, error display, field parsing)

Dependencies:
    - display_constants: _EVENT_*, _KEY_*, _MSG_*, _FORMAT_*
    - display_event_helpers: try_gui_event
    - display_logging_helpers: get_display_logger
    - display_rendering_utilities: output_text_via_basics
    - zData.DataValidator: Schema validation

Extracted From:
    display_event_system.py (lines 1612-1953)
"""

from typing import Any, Optional, Dict

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import try_gui_event
from ..a_infrastructure.display_logging_helpers import get_display_logger
from ..a_infrastructure.display_rendering_utilities import output_text_via_basics

# Import constants
from ..display_constants import (
    _EVENT_ZDIALOG,
    _KEY_FIELDS,
    _KEY_MODEL,
    _MSG_FORM_INPUT,
    _MSG_FORM_COMPLETE,
    _FORMAT_FIELD_PROMPT
)


class DialogEvents:
    """
    Form dialog with field-by-field validation.
    
    Provides zDialog event for displaying forms and collecting validated
    user input in both Terminal and Bifrost modes.
    
    Composition:
        - DeclareEvents: For form header/footer (set after zSystem init)
        - Signals: For error messages (set after zSystem init)
        - zPrimitives: For input collection (from display)
    
    Usage:
        # Via zSystem coordinator
        context = {"fields": ["username", "email", "role"], "model": "@.zSchema.users"}
        data = zcli.display.zEvents.zSystem.zDialog(context, _zcli=zcli)
    """
    
    # Class-level type declarations
    display: Any                     # Parent zDisplay instance
    zPrimitives: Any                 # Primitives for input collection
    DeclareEvents: Optional[Any]     # DeclareEvents (for form headers)
    Signals: Optional[Any]           # Signals (for error messages)
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize DialogEvents with reference to parent zDisplay instance.
        
        Args:
            display_instance: Parent zDisplay instance
        
        Returns:
            None
        
        Notes:
            - DeclareEvents and Signals are set to None initially
            - Will be populated by zSystem after all event packages instantiated
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.DeclareEvents = None  # Will be set after zSystem initialization
        self.Signals = None        # Will be set after zSystem initialization
    
    def zDialog(
        self, 
        context: Dict[str, Any], 
        _zcli: Optional[Any] = None, 
        _walker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Display form dialog and collect validated input (Terminal or Bifrost mode).
        
        ORCHESTRATOR METHOD - Coordinates form display and collection workflow.
        
        Args:
            context: Form context dict containing:
                    - _KEY_FIELDS: List of field names to collect
                    - _KEY_MODEL: Optional schema path for validation
            _zcli: zCLI instance for logging integration
            _walker: zWalker instance for navigation (reserved for future use)
        
        Returns:
            Dict[str, Any]: Collected form data {field_name: value, ...}
                           Empty dict {} if GUI mode (async collection)
        
        Bifrost Mode:
            - Sends _EVENT_ZDIALOG event with form context
            - Frontend displays interactive form UI
            - Returns empty dict (data sent back via WebSocket)
        
        Terminal Mode:
            - Displays form header
            - Collects text input for each field
            - Validates against schema (if provided)
            - Displays form complete footer
            - Returns collected data dict
        
        Usage:
            context = {_KEY_FIELDS: ["username", "email", "role"]}
            data = display.zEvents.zSystem.zDialog(context)
        """
        # 1. Debug logging
        self._log_zdialog_start(context, _zcli)
        
        # 2. Try Bifrost (GUI) mode first
        if self._try_zdialog_gui_mode(context, _zcli):
            return {}  # GUI event sent successfully
        
        # 3. Terminal mode - display header
        fields = context.get(_KEY_FIELDS, [])
        if self.DeclareEvents:
            self.DeclareEvents.zDeclare(_MSG_FORM_INPUT, indent=0)
        
        # 4. Setup schema validation (if available)
        validator, table_name, logger = self._setup_zdialog_validator(context, _zcli)
        
        # 5. Collect form fields with validation
        zConv = self._collect_zdialog_fields(fields, validator, table_name, logger)
        
        # 6. Display footer
        if self.DeclareEvents:
            self.DeclareEvents.zDeclare(_MSG_FORM_COMPLETE, indent=0)
        
        return zConv
    
    # ZDIALOG HELPER METHODS (Private)
    
    def _log_zdialog_start(self, context: Dict[str, Any], _zcli: Optional[Any]) -> None:
        """Log zDialog start (debug mode only)."""
        logger = get_display_logger(self.display) if self.display else None
        if not logger:
            return
        
        logger.debug(f"\n{'='*80}")
        logger.debug(f"[zDialog] 📋 ZDIALOG CALLED - Context: {list(context.keys())}")
        logger.debug(f"[zDialog] Fields: {context.get('fields', [])}")
        logger.debug(f"[zDialog] Model: {context.get('model', 'N/A')}")
        logger.debug(f"[zDialog] Has onSubmit: {bool(context.get('onSubmit'))}")
        logger.debug(f"{'='*80}\n")
    
    def _try_zdialog_gui_mode(self, context: Dict[str, Any], _zcli: Optional[Any]) -> bool:
        """Try to send zDialog event to Bifrost (GUI) mode. Returns True if GUI mode active."""
        gui_sent = try_gui_event(self.display, _EVENT_ZDIALOG, context)
        
        logger = get_display_logger(self.display) if self.display else None
        if logger:
            logger.debug(f"[zDialog] GUI event sent: {gui_sent}")
        
        return gui_sent
    
    def _setup_zdialog_validator(
        self,
        context: Dict[str, Any],
        _zcli: Optional[Any]
    ) -> tuple:
        """
        Setup schema validator for field-by-field validation.
        
        Returns:
            tuple: (validator, table_name, logger) or (None, None, logger) if validation disabled
        """
        model = context.get(_KEY_MODEL)
        logger = get_display_logger(self.display)
        
        if logger:
            logger.debug(f"[zDialog] Field-by-field validation setup - model: {model}")
        
        # Check if validation is possible
        if not (model and isinstance(model, str) and model.startswith('@') and _zcli):
            self._log_validation_disabled_reason(model, _zcli, logger)
            return None, None, logger
        
        # Try to load schema and create validator
        try:
            validator, table_name = self._load_zdialog_schema_validator(model, _zcli, logger)
            if validator and table_name:
                return validator, table_name, logger
            else:
                self._display_schema_error(f"Schema not found: {model}", logger)
                return None, None, logger
        except Exception as e:
            self._display_schema_error(f"Failed to load schema: {e}", logger)
            return None, None, logger
    
    def _log_validation_disabled_reason(
        self,
        model: Optional[str],
        _zcli: Optional[Any],
        logger: Optional[Any]
    ) -> None:
        """Log why validation is disabled."""
        if not logger:
            return
        
        if not model:
            logger.debug(f"[zDialog] No model specified - validation disabled")
        elif not model.startswith('@'):
            logger.debug(f"[zDialog] Model doesn't start with '@' - validation disabled: {model}")
        elif not _zcli:
            logger.debug(f"[zDialog] No zcli instance - validation disabled")
    
    def _load_zdialog_schema_validator(
        self,
        model: str,
        _zcli: Any,
        logger: Optional[Any]
    ) -> tuple:
        """
        Load schema and create validator.
        
        Returns:
            tuple: (validator, table_name) or (None, None) if schema not found
        """
        if logger:
            logger.debug(f"[zDialog] Loading schema from: {model}")
        
        # Load schema for validation
        from zOS.L3_Abstraction.n_zData.zData_modules.shared.validator import DataValidator
        schema_dict = _zcli.loader.handle(model) if hasattr(_zcli, 'loader') else None
        
        if logger:
            logger.debug(f"[zDialog] Schema loaded: {bool(schema_dict)}")
        
        if not schema_dict:
            return None, None
        
        # Extract table name and create validator
        table_name = model.split('.')[-1]
        if logger:
            logger.debug(f"[zDialog] Table name extracted: {table_name}")
            logger.debug(f"[zDialog] Schema fields: {list(schema_dict.get(table_name, {}).keys())}")
        
        # Create validator
        validator_logger = logger or (_zcli.logger if hasattr(_zcli, 'logger') else None)
        if validator_logger:
            validator = DataValidator(schema_dict, validator_logger)
            if logger:
                logger.info(f"[zDialog] ✅ Field-by-field validation ENABLED for table: {table_name}")
            return validator, table_name
        
        return None, None
    
    def _display_schema_error(self, error_msg: str, logger: Optional[Any]) -> None:
        """Display schema loading error to user."""
        if logger:
            logger.error(f"[zDialog] {error_msg}")
        if self.Signals:
            self.Signals.error(f"[ERROR] {error_msg}", indent=0)
            output_text_via_basics("", 0, False, self.display)
            self.Signals.error("Form cannot proceed without schema validation.", indent=1)
    
    def _collect_zdialog_fields(
        self,
        fields: list,
        validator: Optional[Any],
        table_name: Optional[str],
        logger: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Collect all form fields with validation.
        
        Returns:
            Dict[str, Any]: Collected field data {field_name: value, ...}
        """
        zConv = {}
        
        for field in fields:
            # Add newline before each field (except first)
            if zConv:
                output_text_via_basics("", 0, False, self.display)
            
            # Parse field metadata
            field_name, field_type, field_label = self._parse_zdialog_field(field)
            
            # Collect field value with validation loop
            value = self._collect_single_field_with_validation(
                field_name, field_type, field_label, validator, table_name, logger
            )
            
            # Save collected value
            zConv[field_name] = value
        
        return zConv
    
    def _parse_zdialog_field(self, field: Any) -> tuple:
        """
        Parse field specification into (name, type, label).
        
        Returns:
            tuple: (field_name, field_type, field_label)
        """
        if isinstance(field, dict):
            field_name = field.get('name', field.get('field', 'unknown'))
            field_type = field.get('type', None)
            field_label = field.get('label', field_name)
        else:
            field_name = str(field)
            field_type = None
            field_label = field_name
        
        # Auto-detect password fields
        if field_type is None:
            if 'password' in field_name.lower():
                field_type = 'password'
            else:
                field_type = 'text'
        
        return field_name, field_type, field_label
    
    def _collect_single_field_with_validation(
        self,
        field_name: str,
        field_type: str,
        field_label: str,
        validator: Optional[Any],
        table_name: Optional[str],
        logger: Optional[Any]
    ) -> Any:
        """
        Collect a single field value with validation retry loop.
        
        Returns:
            Any: The validated field value
        """
        while True:
            # Collect input
            value = self._read_field_input(field_type, field_label, logger, field_name)
            
            # Validate if validator available
            if validator and table_name:
                is_valid, error_msg = self._validate_field_value(
                    field_name, value, validator, table_name, logger
                )
                
                if is_valid:
                    if logger:
                        logger.info(f"[zDialog] ✅ Field '{field_name}' validation passed")
                    return value
                else:
                    # Display error and retry
                    self._display_field_error(error_msg, logger, field_name)
            else:
                # No validation - accept value
                if logger:
                    logger.debug(f"[zDialog] No validation for field '{field_name}' - accepting value")
                return value
    
    def _read_field_input(
        self,
        field_type: str,
        field_label: str,
        logger: Optional[Any],
        field_name: str
    ) -> Any:
        """Read input for a single field based on type."""
        prompt = _FORMAT_FIELD_PROMPT.format(label=field_label)
        
        if field_type == 'password':
            value = self.zPrimitives.read_password(prompt)
        else:
            value = self.zPrimitives.read_string(prompt)
        
        if logger:
            log_value = '********' if field_type == 'password' else value
            logger.debug(f"[zDialog] Field '{field_name}' input received: '{log_value}' (type: {field_type})")
        
        return value
    
    def _validate_field_value(
        self,
        field_name: str,
        value: Any,
        validator: Any,
        table_name: str,
        logger: Optional[Any]
    ) -> tuple:
        """
        Validate a field value against schema.
        
        Returns:
            tuple: (is_valid: bool, error_msg: Optional[str])
        """
        if logger:
            logger.debug(f"[zDialog] Validating field '{field_name}' against table '{table_name}'")
        
        is_valid, errors = validator.validate_field(table_name, field_name, value)
        
        if logger:
            logger.debug(f"[zDialog] Validation result for '{field_name}': valid={is_valid}, errors={errors}")
        
        if not is_valid and field_name in errors:
            error_msg = errors[field_name]
            if logger:
                logger.info(f"[zDialog] Field '{field_name}' validation failed: {error_msg}")
            return False, error_msg
        
        return True, None
    
    def _display_field_error(
        self,
        error_msg: str,
        logger: Optional[Any],
        field_name: str
    ) -> None:
        """Display field validation error to user."""
        if self.Signals:
            self.Signals.error(f"[ERROR] {error_msg}", indent=1)
            output_text_via_basics("", 0, False, self.display)
