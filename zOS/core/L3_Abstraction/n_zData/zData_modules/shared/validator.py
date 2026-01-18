# zCLI/subsystems/zData/zData_modules/shared/validator.py
"""
Schema-based data validation engine for zData CRUD operations.

This module implements a 5-layer validation architecture that enforces schema rules
before data operations (INSERT/UPDATE). Validation is fail-fast and extensible via
plugin validators.

Architecture Position
--------------------
- **Layer**: Tier 0 - Foundation
- **Dependencies**: Parsers (indirect), plugin system (optional)
- **Used By**: CRUD operations (insert, update), data_operations
- **Purpose**: Enforce data integrity before backend operations

5-Layer Validation Architecture
-------------------------------
The validator uses a layered approach where each layer validates specific aspects
of the data. Validation stops at the first failure (fail-fast):

**Layer 1: String Rules**
- min_length: Minimum string length
- max_length: Maximum string length

**Layer 2: Numeric Rules**
- min: Minimum numeric value
- max: Maximum numeric value

**Layer 3: Pattern Rules**
- pattern: Regex pattern matching

**Layer 4: Format Rules**
- email: RFC-compliant email validation
- url: HTTP/HTTPS URL validation
- phone: International phone number validation
- date: Date format validation (uses zConfig date_format)
- time: Time format validation (uses zConfig time_format)
- datetime: Datetime format validation (uses zConfig datetime_format)

**Layer 5: Plugin Validators**
- Custom business logic via zCLI plugin system
- Cross-field validation support
- Reusable validation functions

Supported Schema Rules
---------------------
**Field-Level Rules:**
- required: Field must be present (INSERT only)
- min_length: Minimum string length
- max_length: Maximum string length
- min: Minimum numeric value
- max: Maximum numeric value
- pattern: Regex pattern (with optional pattern_message)
- format: Built-in format validator (email, url, phone, date, time, datetime)
- validator: Plugin validator (&plugin.function syntax)
- error_message: Custom error message (overrides default)

**Field Attributes:**
- pk: Primary key (auto-skips required check)
- default: Has default value (auto-skips required check)

INSERT vs UPDATE Validation
---------------------------
**INSERT (Full Validation):**
- All layers (1-5) executed
- Required field checking enforced
- All fields in data validated

**UPDATE (Partial Validation):**
- All layers (1-5) executed
- Required field checking SKIPPED
- Only provided fields validated

This allows partial updates without requiring all fields.

Plugin Validator Integration
----------------------------
Layer 5 validators use the zCLI plugin system (&plugin.function syntax):

Schema example:
    email:
      type: str
      rules:
        format: email              # Layer 4: Built-in email format
        validator: "&validators.check_company_domain(['acme.com'])"  # Layer 5: Plugin

Plugin function signature:
    def check_company_domain(allowed_domains, value, field_name, table=None, full_data=None):
        # allowed_domains: User-provided args from schema
        # value: Field value being validated
        # field_name: Name of field
        # table: Table name (context)
        # full_data: All field data (for cross-field validation)
        
        if value.split('@')[1] not in allowed_domains:
            return (False, f"{field_name} must use company email domain")
        return (True, None)

Plugin validators must return: (is_valid: bool, error_message: str or None)

Usage Examples
-------------
INSERT validation (full):
    >>> validator = DataValidator(schema, logger=logger, zcli=zcli)
    >>> data = {"username": "john", "email": "john@acme.com", "age": 25}
    >>> is_valid, errors = validator.validate_insert("users", data)
    >>> if not is_valid:
    ...     print(f"Validation failed: {errors}")

UPDATE validation (partial):
    >>> data = {"email": "newemail@acme.com"}  # Only updating email
    >>> is_valid, errors = validator.validate_update("users", data)
    >>> # No required field errors, only validates provided fields

Format validator:
    >>> # Schema: email: { rules: { format: email } }
    >>> data = {"email": "invalid-email"}
    >>> is_valid, errors = validator.validate_insert("users", data)
    >>> # Returns: (False, {"email": "Invalid email address format"})

Plugin validator:
    >>> # Schema: email: { rules: { validator: "&validators.check_domain(['acme.com'])" } }
    >>> data = {"email": "user@badsite.com"}
    >>> is_valid, errors = validator.validate_insert("users", data)
    >>> # Returns: (False, {"email": "email must use company email domain"})

Integration
----------
This validator is used by:
- crud_insert.py: Pre-insert validation
- crud_update.py: Pre-update validation
- crud_upsert.py: Pre-upsert validation
- data_operations.py: Validation orchestration

See Also
--------
- crud_insert.py: Uses validate_insert() before INSERT
- crud_update.py: Uses validate_update() before UPDATE
- zParser plugin system: Plugin resolution mechanism
"""

from zOS import Dict, Tuple, Optional, Any, re

# ============================================================
# Module Constants - Schema Keys
# ============================================================

# Schema structure keys
SCHEMA_KEY_RULES = "rules"
SCHEMA_KEY_REQUIRED = "required"
SCHEMA_KEY_PK = "pk"
SCHEMA_KEY_DEFAULT = "default"

# ============================================================
# Module Constants - Rule Keys
# ============================================================

# String validation rules
RULE_KEY_MIN_LENGTH = "min_length"
RULE_KEY_MAX_LENGTH = "max_length"

# Numeric validation rules
RULE_KEY_MIN = "min"
RULE_KEY_MAX = "max"

# Pattern validation rules
RULE_KEY_PATTERN = "pattern"
RULE_KEY_PATTERN_MESSAGE = "pattern_message"

# Format validation rules
RULE_KEY_FORMAT = "format"

# Plugin validator rules
RULE_KEY_VALIDATOR = "validator"

# Error message override
RULE_KEY_ERROR_MESSAGE = "error_message"

# ============================================================
# Module Constants - Format Types
# ============================================================

FORMAT_EMAIL = "email"
FORMAT_URL = "url"
FORMAT_PHONE = "phone"
FORMAT_DATE = "date"
FORMAT_TIME = "time"
FORMAT_DATETIME = "datetime"

# ============================================================
# Module Constants - Regex Patterns
# ============================================================

# Email validation pattern (RFC-compliant)
PATTERN_EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# URL validation pattern (HTTP/HTTPS)
PATTERN_URL = r'^https?://[^\s/$.?#].[^\s]*$'

# Phone validation pattern (10-15 digits, optional +)
PATTERN_PHONE = r'^\+?[0-9]{10,15}$'

# Phone cleaning pattern (remove formatting characters)
PATTERN_PHONE_CLEAN = r'[\s\-\(\)\.]'

# ============================================================
# Module Constants - Plugin System
# ============================================================

# Plugin invocation symbol
PLUGIN_SYMBOL = "&"

# Cache type for plugin resolution
CACHE_TYPE_PLUGIN = "plugin"

# ============================================================
# Module Constants - Error Messages
# ============================================================

# Required field errors
ERR_FIELD_REQUIRED = "{field_name} is required"

# String validation errors
ERR_MIN_LENGTH = "{field_name} must be at least {min_length} characters"
ERR_MAX_LENGTH = "{field_name} cannot exceed {max_length} characters"

# Numeric validation errors
ERR_MIN_VALUE = "{field_name} must be at least {min_val}"
ERR_MAX_VALUE = "{field_name} cannot exceed {max_val}"

# Pattern validation errors
ERR_INVALID_FORMAT = "Invalid format for {field_name}"

# Format validation errors
ERR_EMAIL_FORMAT = "Invalid email address format"
ERR_URL_FORMAT = "Invalid URL format"
ERR_PHONE_FORMAT = "Invalid phone number format"
ERR_DATE_FORMAT = "Invalid date format"
ERR_TIME_FORMAT = "Invalid time format"
ERR_DATETIME_FORMAT = "Invalid datetime format"

# Plugin validator errors
ERR_PLUGIN_INVALID_RETURN = "Plugin validator error: invalid return format"
ERR_PLUGIN_EXECUTION = "Plugin validator error: {error}"

# ============================================================
# Module Constants - Log Messages
# ============================================================

LOG_NO_SCHEMA = "No schema found for table: %s"
LOG_VALIDATION_FAILED = "Validation failed with %d error(s)"
LOG_VALIDATION_PASSED = "[OK] Validation passed for table: %s"
LOG_UNKNOWN_FORMAT = "Unknown format type: %s"
LOG_PLUGIN_NO_ZCLI = "Plugin validator specified but zcli not provided to DataValidator: %s"
LOG_PLUGIN_INVALID_SYNTAX = "Invalid validator syntax (must start with &): %s"
LOG_PLUGIN_NOT_FOUND = "Plugin validator not found (skipping validation): %s"
LOG_PLUGIN_FUNCTION_MISSING = "Function '%s' not found in plugin '%s'"
LOG_PLUGIN_INVALID_RETURN_FORMAT = "Plugin validator must return (is_valid, error_msg) tuple: %s.%s"
LOG_PLUGIN_EXECUTION_ERROR = "Plugin validator execution error (%s): %s"

# ============================================================
# Module Constants - Plugin Context Keys
# ============================================================

CONTEXT_KEY_TABLE = "table"
CONTEXT_KEY_FULL_DATA = "full_data"

# ============================================================
# Public API
# ============================================================

__all__ = ["DataValidator"]

class DataValidator:
    """
    Schema-based data validation engine with 5-layer architecture.
    
    This class implements a layered validation system that enforces schema rules
    before CRUD operations. It supports built-in validators (string, numeric,
    pattern, format) and extensible plugin validators for custom business logic.
    
    Validation Architecture
    ----------------------
    The validator uses a fail-fast approach with 5 layers:
    
    1. **String Rules**: min_length, max_length
    2. **Numeric Rules**: min, max
    3. **Pattern Rules**: regex matching
    4. **Format Rules**: email, url, phone (extensible registry)
    5. **Plugin Validators**: Custom business logic via &plugin.function syntax
    
    Public API
    ---------
    - **validate_insert(table, data)**: Full validation (INSERT operations)
      - Validates all fields in data
      - Enforces required field checks
      - Returns: (is_valid: bool, errors: Dict or None)
    
    - **validate_update(table, data)**: Partial validation (UPDATE operations)
      - Validates only provided fields
      - Skips required field checks
      - Returns: (is_valid: bool, errors: Dict or None)
    
    Format Validator Registry
    ------------------------
    The format_validators dict maps format types to validation functions:
    - 'email' → _validate_email()
    - 'url' → _validate_url()
    - 'phone' → _validate_phone()
    
    New format validators can be added by extending this registry.
    
    Plugin Validator Integration
    ---------------------------
    Plugin validators (Layer 5) are resolved via the zCLI plugin system.
    Requires zcli instance to be provided during initialization.
    
    Example:
        >>> validator = DataValidator(schema, logger=logger, zcli=zcli)
        >>> is_valid, errors = validator.validate_insert("users", data)
        >>> if not is_valid:
        ...     print(f"Errors: {errors}")
    
    Attributes:
        schema (Dict): Schema definition with table/field structure
        logger: Logger instance for validation messages
        zcli: zCLI instance (required for plugin validator resolution)
        format_validators (Dict): Registry of format validator functions
    """

    def __init__(
        self,
        schema: Dict[str, Any],
        logger: Optional[Any] = None,
        zcli: Optional[Any] = None
    ) -> None:
        """
        Initialize DataValidator with schema and optional dependencies.
        
        Args:
            schema: Schema definition with table/field structure. Format:
                {
                    "table_name": {
                        "field_name": {
                            "type": "str",
                            "required": True,
                            "rules": {
                                "min_length": 3,
                                "max_length": 50,
                                "pattern": "^[a-zA-Z]+$",
                                "format": "email",
                                "validator": "&validators.custom_check(args)"
                            }
                        }
                    }
                }
            
            logger: Optional logger instance for validation messages.
                   If provided, logs warnings for validation failures
                   and debug messages for successful validations.
            
            zcli: Optional zCLI instance. Required if using plugin validators
                  (Layer 5). Provides access to plugin cache and resolution.
        
        Example:
            Basic initialization:
                >>> validator = DataValidator(schema)
            
            With logger:
                >>> validator = DataValidator(schema, logger=my_logger)
            
            With plugin support:
                >>> validator = DataValidator(schema, logger=my_logger, zcli=z)
        
        Notes:
            - schema must contain table-level definitions
            - Plugin validators gracefully degrade if zcli not provided
            - Format validators are always available (no dependencies)
        """
        self.schema = schema
        self.logger = logger
        self.zcli = zcli  # For plugin validator resolution
        
        # Format validator registry (Layer 4)
        self.format_validators = {
            FORMAT_EMAIL: self._validate_email,
            FORMAT_URL: self._validate_url,
            FORMAT_PHONE: self._validate_phone,
            FORMAT_DATE: self._validate_date,
            FORMAT_TIME: self._validate_time,
            FORMAT_DATETIME: self._validate_datetime,
        }
        
        # TODO: Architecture Review - Consider centralizing ALL zData parsing logic to zParser
        #       Current state: zData has its own parsers/ directory (value_parser, where_parser)
        #       Proposal: Evaluate moving format validators and value parsing to zParser subsystem
        #       Rationale: Parsing is semantically zParser territory, but zData needs domain-specific validation
        #       Decision: Keep in zData for v1.5.14 (consistent with email/url/phone), revisit in v1.6.0
        #       Reference: This architectural question raised during Step 4.3.2d cleanup (2026-01-01)

    def validate_field(
        self,
        table: str,
        field_name: str,
        value: Any
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Validate a single field value against schema rules.
        
        This method allows field-by-field validation for progressive form input.
        It validates the field using all 5 validation layers.
        
        Args:
            table: Table name to validate against
            field_name: Name of the field to validate
            value: Value to validate
        
        Returns:
            Tuple of (is_valid, errors):
            - is_valid: True if validation passes, False otherwise
            - errors: None if valid, Dict with {field_name: error_message} if invalid
        
        Examples:
            Valid field:
                >>> is_valid, errors = validator.validate_field("users", "email", "john@acme.com")
                >>> # Returns: (True, None)
            
            Invalid field:
                >>> is_valid, errors = validator.validate_field("users", "email", "invalid")
                >>> # Returns: (False, {"email": "Invalid email address format"})
        """
        # Get table schema
        table_schema = self.schema.get(table)
        if not table_schema or not isinstance(table_schema, dict):
            return True, None  # No schema = no validation (graceful)
        
        # Get field definition
        field_def = table_schema.get(field_name)
        if not field_def or not isinstance(field_def, dict):
            return True, None  # No field def = no validation
        
        # Get rules
        rules = field_def.get(SCHEMA_KEY_RULES, {})
        if not rules and not field_def.get(SCHEMA_KEY_REQUIRED, False):
            return True, None  # No rules and not required = valid
        
        # Validate using internal method
        is_valid, error_msg = self._validate_field(
            field_name=field_name,
            value=value,
            rules=rules,
            field_def=field_def,
            table_name=table,
            full_data={field_name: value}
        )
        
        # Return in same format as validate_insert
        if is_valid:
            return True, None
        else:
            return False, {field_name: error_msg}

    def validate_insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Validate data for INSERT operation (full validation).
        
        INSERT validation performs full checks including:
        - All 5 validation layers for provided fields
        - Required field enforcement (with pk/default exceptions)
        - Returns detailed error messages per field
        
        Args:
            table: Table name to validate against
            data: Dictionary of field_name → value to validate
        
        Returns:
            Tuple of (is_valid, errors):
            - is_valid: True if all validations pass, False otherwise
            - errors: None if valid, Dict of {field_name: error_message} if invalid
        
        Validation Process:
            1. Check schema exists for table
            2. Run 5-layer validation on each provided field
            3. Check required fields are present (skip pk/default)
            4. Return combined error dict or success
        
        Examples:
            Valid data:
                >>> data = {"username": "john", "email": "john@acme.com", "age": 25}
                >>> is_valid, errors = validator.validate_insert("users", data)
                >>> # Returns: (True, None)
            
            Invalid data (min_length):
                >>> data = {"username": "ab"}  # min_length: 3
                >>> is_valid, errors = validator.validate_insert("users", data)
                >>> # Returns: (False, {"username": "username must be at least 3 characters"})
            
            Missing required field:
                >>> data = {"username": "john"}  # email is required
                >>> is_valid, errors = validator.validate_insert("users", data)
                >>> # Returns: (False, {"email": "email is required"})
        
        Notes:
            - Returns (True, None) if table schema not found (graceful)
            - Skips fields without schema definition
            - Primary keys and fields with defaults skip required check
            - Plugin validators (Layer 5) executed if zcli provided
        
        See Also:
            - validate_update(): Partial validation for UPDATE operations
            - _validate_field(): 5-layer validation implementation
        """
        table_schema = self.schema.get(table, {})
        if not table_schema:
            if self.logger:
                self.logger.warning(LOG_NO_SCHEMA, table)
            return True, None

        errors = {}

        # Validate provided fields (all 5 layers)
        for field_name, value in data.items():
            field_def = table_schema.get(field_name)
            if not field_def or not isinstance(field_def, dict):
                continue

            rules = field_def.get(SCHEMA_KEY_RULES, {})
            if not rules:
                continue

            # Pass table_name and full_data for plugin validator context
            is_valid, error_msg = self._validate_field(
                field_name, value, rules, field_def,
                table_name=table, full_data=data
            )
            if not is_valid:
                errors[field_name] = error_msg

        # Check required fields (INSERT only)
        for field_name, field_def in table_schema.items():
            if not isinstance(field_def, dict):
                continue

            is_required = field_def.get(SCHEMA_KEY_REQUIRED, False)
            if is_required and field_name not in data:
                # Skip required check for pk and default fields
                if field_def.get(SCHEMA_KEY_PK, False) or SCHEMA_KEY_DEFAULT in field_def:
                    continue
                errors[field_name] = ERR_FIELD_REQUIRED.format(field_name=field_name)

        # Return results
        if errors:
            if self.logger:
                self.logger.warning(LOG_VALIDATION_FAILED, len(errors))
            return False, errors

        if self.logger:
            self.logger.debug(LOG_VALIDATION_PASSED, table)
        return True, None

    def validate_update(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Validate data for UPDATE operation (partial validation).
        
        UPDATE validation performs partial checks:
        - All 5 validation layers for provided fields
        - NO required field enforcement (allows partial updates)
        - Returns detailed error messages per field
        
        Args:
            table: Table name to validate against
            data: Dictionary of field_name → value to validate (partial data)
        
        Returns:
            Tuple of (is_valid, errors):
            - is_valid: True if all validations pass, False otherwise
            - errors: None if valid, Dict of {field_name: error_message} if invalid
        
        Validation Process:
            1. Check schema exists for table
            2. Run 5-layer validation on each provided field
            3. Skip required field checks (partial update)
            4. Return combined error dict or success
        
        Examples:
            Valid partial update:
                >>> data = {"email": "newemail@acme.com"}  # Only updating email
                >>> is_valid, errors = validator.validate_update("users", data)
                >>> # Returns: (True, None)
            
            Invalid partial update:
                >>> data = {"email": "invalid-email"}  # format check fails
                >>> is_valid, errors = validator.validate_update("users", data)
                >>> # Returns: (False, {"email": "Invalid email address format"})
            
            Multiple field update:
                >>> data = {"username": "newname", "age": 30}
                >>> is_valid, errors = validator.validate_update("users", data)
                >>> # Returns: (True, None) - validates both fields
        
        Differences from validate_insert:
            - No required field enforcement
            - Only validates provided fields
            - Allows empty data dict (returns success)
        
        Notes:
            - Returns (True, None) if table schema not found (graceful)
            - Skips fields without schema definition
            - Plugin validators (Layer 5) executed if zcli provided
            - Same 5-layer validation as INSERT for provided fields
        
        See Also:
            - validate_insert(): Full validation for INSERT operations
            - _validate_field(): 5-layer validation implementation
        """
        table_schema = self.schema.get(table, {})
        if not table_schema:
            if self.logger:
                self.logger.warning(LOG_NO_SCHEMA, table)
            return True, None

        errors = {}

        # Validate provided fields only (all 5 layers)
        for field_name, value in data.items():
            field_def = table_schema.get(field_name)
            if not field_def or not isinstance(field_def, dict):
                continue

            rules = field_def.get(SCHEMA_KEY_RULES, {})
            if not rules:
                continue

            # Pass table_name and full_data for plugin validator context
            is_valid, error_msg = self._validate_field(
                field_name, value, rules, field_def,
                table_name=table, full_data=data
            )
            if not is_valid:
                errors[field_name] = error_msg

        # Return results (no required field check)
        if errors:
            if self.logger:
                self.logger.warning(LOG_VALIDATION_FAILED, len(errors))
            return False, errors

        if self.logger:
            self.logger.debug(LOG_VALIDATION_PASSED, table)
        return True, None

    def _validate_field(
        self,
        field_name: str,
        value: Any,
        rules: Dict[str, Any],
        field_def: Dict[str, Any],
        table_name: Optional[str] = None,
        full_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate single field against schema rules (5-layer validation).
        
        This method implements the core validation logic using a fail-fast approach.
        Each layer validates a specific aspect, stopping at the first error.
        
        Validation Order (fail-fast):
            Layer 1: String rules (min_length, max_length)
            Layer 2: Numeric rules (min, max)
            Layer 3: Pattern rules (regex)
            Layer 4: Format rules (email, url, phone)
            Layer 5: Plugin validator (custom business logic)
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate (any type)
            rules: Validation rules from schema (dict of rule_key: rule_value)
            field_def: Full field definition from schema
            table_name: Table name for plugin context (optional)
            full_data: All field data for cross-field validation (optional)
        
        Returns:
            Tuple of (is_valid, error_msg):
            - is_valid: True if validation passes, False otherwise
            - error_msg: None if valid, error message string if invalid
        
        Notes:
            - None or empty string values skip validation if not required
            - Each layer only validates if relevant (e.g., string layer skips non-strings)
            - Plugin validators run last (after all built-in validators)
            - Returns at first error (fail-fast)
        """
        # Handle None/empty values
        if value is None or value == "":
            if field_def.get(SCHEMA_KEY_REQUIRED, False):
                return False, ERR_FIELD_REQUIRED.format(field_name=field_name)
            return True, None

        # Layer 1: String rules
        error = self._check_string_rules(field_name, value, rules)
        if error:
            return False, error

        # Layer 2: Numeric rules
        error = self._check_numeric_rules(field_name, value, rules)
        if error:
            return False, error

        # Layer 3: Pattern rules
        error = self._check_pattern_rules(field_name, value, rules)
        if error:
            return False, error

        # Layer 4: Format rules
        error = self._check_format_rules(field_name, value, rules)
        if error:
            return False, error

        # Layer 5: Plugin validator (runs AFTER all built-in validators pass)
        error = self._check_plugin_validator(field_name, value, rules, table_name, full_data)
        if error:
            return False, error

        return True, None

    def _check_string_rules(
        self,
        field_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check string length validation rules (Layer 1).
        
        Validates:
        - min_length: Minimum character count
        - max_length: Maximum character count
        
        Args:
            field_name: Name of field (for error messages)
            value: Value to validate (only checks if string)
            rules: Validation rules dict
        
        Returns:
            None if valid or not a string, error message string if invalid
        
        Examples:
            >>> rules = {"min_length": 3, "max_length": 50}
            >>> _check_string_rules("username", "ab", rules)
            "username must be at least 3 characters"
            
            >>> _check_string_rules("username", "valid_name", rules)
            None
        """
        if not isinstance(value, str):
            return None

        min_length = rules.get(RULE_KEY_MIN_LENGTH)
        if min_length and len(value) < min_length:
            custom_error = rules.get(RULE_KEY_ERROR_MESSAGE)
            return custom_error or ERR_MIN_LENGTH.format(
                field_name=field_name,
                min_length=min_length
            )

        max_length = rules.get(RULE_KEY_MAX_LENGTH)
        if max_length and len(value) > max_length:
            custom_error = rules.get(RULE_KEY_ERROR_MESSAGE)
            return custom_error or ERR_MAX_LENGTH.format(
                field_name=field_name,
                max_length=max_length
            )

        return None

    def _check_numeric_rules(
        self,
        field_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check numeric range validation rules (Layer 2).
        
        Validates:
        - min: Minimum numeric value
        - max: Maximum numeric value
        
        Args:
            field_name: Name of field (for error messages)
            value: Value to validate (only checks if int/float)
            rules: Validation rules dict
        
        Returns:
            None if valid or not numeric, error message string if invalid
        
        Examples:
            >>> rules = {"min": 0, "max": 100}
            >>> _check_numeric_rules("age", -5, rules)
            "age must be at least 0"
            
            >>> _check_numeric_rules("age", 25, rules)
            None
        """
        if not isinstance(value, (int, float)):
            return None

        min_val = rules.get(RULE_KEY_MIN)
        if min_val is not None and value < min_val:
            custom_error = rules.get(RULE_KEY_ERROR_MESSAGE)
            return custom_error or ERR_MIN_VALUE.format(
                field_name=field_name,
                min_val=min_val
            )

        max_val = rules.get(RULE_KEY_MAX)
        if max_val is not None and value > max_val:
            custom_error = rules.get(RULE_KEY_ERROR_MESSAGE)
            return custom_error or ERR_MAX_VALUE.format(
                field_name=field_name,
                max_val=max_val
            )

        return None

    def _check_pattern_rules(
        self,
        field_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check regex pattern validation rules (Layer 3).
        
        Validates:
        - pattern: Regex pattern matching
        
        Args:
            field_name: Name of field (for error messages)
            value: Value to validate (only checks if string)
            rules: Validation rules dict
        
        Returns:
            None if valid or not a string, error message string if invalid
        
        Examples:
            >>> rules = {"pattern": "^[A-Z][a-z]+$", "pattern_message": "Must start with capital"}
            >>> _check_pattern_rules("name", "john", rules)
            "Must start with capital"
            
            >>> _check_pattern_rules("name", "John", rules)
            None
        
        Notes:
            - Uses pattern_message if provided, otherwise error_message, otherwise default
        """
        pattern = rules.get(RULE_KEY_PATTERN)
        if pattern and isinstance(value, str) and not re.match(pattern, value):
            # Priority: pattern_message > error_message > default
            return (
                rules.get(RULE_KEY_PATTERN_MESSAGE) or
                rules.get(RULE_KEY_ERROR_MESSAGE) or
                ERR_INVALID_FORMAT.format(field_name=field_name)
            )
        return None

    def _check_format_rules(
        self,
        field_name: str,  # pylint: disable=unused-argument
        value: Any,
        rules: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check built-in format validation rules (Layer 4).
        
        Validates:
        - format: Built-in format validators (email, url, phone)
        
        Supported formats:
        - email: RFC-compliant email validation
        - url: HTTP/HTTPS URL validation
        - phone: International phone number validation
        
        Args:
            field_name: Name of field (unused, kept for signature consistency)
            value: Value to validate (only checks if string)
            rules: Validation rules dict
        
        Returns:
            None if valid or no format rule, error message string if invalid
        
        Examples:
            >>> rules = {"format": "email"}
            >>> _check_format_rules("contact", "invalid-email", rules)
            "Invalid email address format"
            
            >>> _check_format_rules("contact", "valid@example.com", rules)
            None
        
        Notes:
            - Format type is case-insensitive
            - Custom error_message overrides default format error
            - Unknown format types log warning but don't fail
        """
        format_type = rules.get(RULE_KEY_FORMAT)
        if not format_type or not isinstance(value, str):
            return None

        # Look up format validator (case-insensitive)
        validator = self.format_validators.get(format_type.lower())
        if validator:
            is_valid, error = validator(value)
            if not is_valid:
                # Use custom error_message if provided, otherwise use validator's error
                return rules.get(RULE_KEY_ERROR_MESSAGE) or error
        else:
            # Unknown format type - log but don't fail
            if self.logger:
                self.logger.warning(LOG_UNKNOWN_FORMAT, format_type)

        return None

    def _validate_email(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address format (RFC-compliant).
        
        Format rules:
        - Username: alphanumeric, dots, underscores, hyphens, plus signs
        - @ symbol required
        - Domain: alphanumeric, dots, hyphens
        - TLD: 2+ letters
        
        Args:
            value: Email address string to validate
        
        Returns:
            Tuple of (is_valid, error_msg):
            - (True, None) if valid email
            - (False, error_message) if invalid
        
        Examples:
            >>> _validate_email("user@example.com")
            (True, None)
            
            >>> _validate_email("invalid-email")
            (False, "Invalid email address format")
        """
        if re.match(PATTERN_EMAIL, value):
            return True, None
        return False, ERR_EMAIL_FORMAT

    def _validate_url(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format (HTTP/HTTPS only).
        
        Format rules:
        - Protocol: http:// or https:// (case-insensitive)
        - Domain: valid characters (no whitespace)
        - Path/query: any non-whitespace
        
        Args:
            value: URL string to validate
        
        Returns:
            Tuple of (is_valid, error_msg):
            - (True, None) if valid URL
            - (False, error_message) if invalid
        
        Examples:
            >>> _validate_url("https://example.com")
            (True, None)
            
            >>> _validate_url("ftp://example.com")
            (False, "Invalid URL format")
        """
        if re.match(PATTERN_URL, value, re.IGNORECASE):
            return True, None
        return False, ERR_URL_FORMAT

    def _validate_phone(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate phone number format (international).
        
        Format rules:
        - Optional + prefix
        - 10-15 digits
        - Formatting characters removed (spaces, dashes, parentheses, dots)
        
        Args:
            value: Phone number string to validate
        
        Returns:
            Tuple of (is_valid, error_msg):
            - (True, None) if valid phone
            - (False, error_message) if invalid
        
        Examples:
            >>> _validate_phone("+1 (555) 123-4567")
            (True, None)
            
            >>> _validate_phone("123")
            (False, "Invalid phone number format")
        
        Notes:
            - Accepts various formatting styles
            - Strips formatting before validation
            - Requires 10-15 digits after cleaning
        """
        # Remove formatting characters
        cleaned = re.sub(PATTERN_PHONE_CLEAN, '', value)
        
        # Validate cleaned number
        if re.match(PATTERN_PHONE, cleaned):
            return True, None
        return False, ERR_PHONE_FORMAT

    def _validate_date(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate date format against zConfig settings."""
        from datetime import datetime
        
        date_format = "yyyy-mm-dd"  # Default
        if self.zcli:
            date_format = self.zcli.config.get('date_format', date_format)
        
        format_map = {
            "ddmmyyyy": "%d%m%Y", "mmddyyyy": "%m%d%Y", "yyyy-mm-dd": "%Y-%m-%d",
            "dd/mm/yyyy": "%d/%m/%Y", "mm/dd/yyyy": "%m/%d/%Y",
            "dd-mm-yyyy": "%d-%m-%Y", "mm-dd-yyyy": "%m-%d-%Y",
        }
        strptime_format = format_map.get(date_format, "%Y-%m-%d")
        
        try:
            datetime.strptime(value, strptime_format)
            return True, None
        except ValueError:
            return False, f"{ERR_DATE_FORMAT} (expected: {date_format})"

    def _validate_time(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate time format against zConfig settings."""
        from datetime import datetime
        
        time_format = "HH:MM:SS"  # Default
        if self.zcli:
            time_format = self.zcli.config.get('time_format', time_format)
        
        format_map = {
            "HH:MM:SS": "%H:%M:%S", "HH:MM": "%H:%M",
            "hh:mm:ss": "%I:%M:%S", "hh:mm": "%I:%M",
        }
        strptime_format = format_map.get(time_format, "%H:%M:%S")
        
        try:
            datetime.strptime(value, strptime_format)
            return True, None
        except ValueError:
            return False, f"{ERR_TIME_FORMAT} (expected: {time_format})"

    def _validate_datetime(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate datetime format against zConfig settings."""
        from datetime import datetime
        
        datetime_format = "yyyy-mm-dd HH:MM:SS"  # Default
        if self.zcli:
            datetime_format = self.zcli.config.get('datetime_format', datetime_format)
        
        format_map = {
            "ddmmyyyy HH:MM:SS": "%d%m%Y %H:%M:%S", "mmddyyyy HH:MM:SS": "%m%d%Y %H:%M:%S",
            "yyyy-mm-dd HH:MM:SS": "%Y-%m-%d %H:%M:%S",
            "dd/mm/yyyy HH:MM:SS": "%d/%m/%Y %H:%M:%S", "mm/dd/yyyy HH:MM:SS": "%m/%d/%Y %H:%M:%S",
            "dd-mm-yyyy HH:MM:SS": "%d-%m-%Y %H:%M:%S", "mm-dd-yyyy HH:MM:SS": "%m-%d-%Y %H:%M:%S",
        }
        strptime_format = format_map.get(datetime_format, "%Y-%m-%d %H:%M:%S")
        
        try:
            datetime.strptime(value, strptime_format)
            return True, None
        except ValueError:
            return False, f"{ERR_DATETIME_FORMAT} (expected: {datetime_format})"

    def _check_plugin_validator(
        self,
        field_name: str,
        value: Any,
        rules: Dict[str, Any],
        table_name: Optional[str] = None,
        full_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Check custom plugin validator (Layer 5 - business logic).
        
        Plugin validators run AFTER all built-in validators pass (layered validation).
        Uses existing zCLI plugin infrastructure (&PluginName.function(args) pattern).
        
        Args:
            field_name: Name of the field being validated
            value: Field value to validate
            rules: Validation rules from schema
            table_name: Table name for context (optional)
            full_data: All field data for cross-field validation (optional)
        
        Returns:
            None if valid or no validator, error message string if invalid
        
        Plugin Function Signature:
            def custom_validator(user_arg1, user_arg2, ..., value, field_name, table=None, full_data=None):
                # User-provided args come first
                # value and field_name injected automatically
                # table and full_data provided as kwargs for context
                return (is_valid: bool, error_message: str or None)
        
        Example schema usage:
            email:
              type: str
              rules:
                format: email  # Built-in (Layer 4)
                validator: "&validators.check_email_domain(['company.com'])"  # Plugin (Layer 5)
        
        Notes:
            - Requires zcli instance (graceful degradation if missing)
            - Invalid syntax logs warning but doesn't fail
            - Missing plugins log warning but don't fail
            - Plugin execution errors return error message
        """
        validator_spec = rules.get(RULE_KEY_VALIDATOR)
        if not validator_spec:
            return None  # No plugin validator specified
        
        # Check if zcli instance is available (required for plugin resolution)
        if not self.zcli:
            if self.logger:
                self.logger.warning(LOG_PLUGIN_NO_ZCLI, validator_spec)
            return None  # Graceful degradation
        
        # Validate plugin invocation syntax (must start with &)
        if not isinstance(validator_spec, str) or not validator_spec.startswith(PLUGIN_SYMBOL):
            if self.logger:
                self.logger.warning(LOG_PLUGIN_INVALID_SYNTAX, validator_spec)
            return None  # Skip invalid syntax
        
        try:
            # Use existing zCLI plugin infrastructure to resolve and execute
            # Parse the plugin invocation (e.g., "&validators.check_email_domain(['company.com'])")
            # pylint: disable=import-outside-toplevel
            from zOS.L2_Core.g_zParser.parser_modules.parser_plugin import (
                _parse_invocation, _parse_arguments
            )
            
            plugin_name, function_name, args_str = _parse_invocation(validator_spec)
            
            # Check plugin cache first (reuse existing infrastructure)
            cached_module = self.zcli.loader.cache.get(plugin_name, cache_type=CACHE_TYPE_PLUGIN)
            
            if not cached_module:
                # Plugin not found - graceful degradation
                if self.logger:
                    self.logger.warning(LOG_PLUGIN_NOT_FOUND, plugin_name)
                return None  # Skip validation if plugin missing
            
            # Get function from cached module
            if not hasattr(cached_module, function_name):
                if self.logger:
                    self.logger.warning(LOG_PLUGIN_FUNCTION_MISSING, function_name, plugin_name)
                return None  # Skip if function missing
            
            func = getattr(cached_module, function_name)
            
            # Parse user-provided arguments from schema
            user_args, user_kwargs = _parse_arguments(args_str)
            
            # Inject validator-specific arguments:
            # User args come first, then value, field_name, then kwargs context
            final_args = list(user_args) + [value, field_name]
            final_kwargs = {
                **user_kwargs,
                CONTEXT_KEY_TABLE: table_name,
                CONTEXT_KEY_FULL_DATA: full_data or {}
            }
            
            # Execute validator plugin
            result = func(*final_args, **final_kwargs)
            
            # Validate return format (must be tuple: (is_valid, error_msg))
            if not isinstance(result, tuple) or len(result) != 2:
                if self.logger:
                    self.logger.error(
                        LOG_PLUGIN_INVALID_RETURN_FORMAT,
                        plugin_name, function_name
                    )
                return ERR_PLUGIN_INVALID_RETURN
            
            is_valid, error_msg = result
            
            # Return custom error_message if specified in rules, otherwise use plugin's error
            if not is_valid:
                return rules.get(RULE_KEY_ERROR_MESSAGE) or error_msg
            
            return None  # Validation passed
            
        except Exception as e:  # pylint: disable=broad-except
            # Log plugin execution errors but don't crash validation
            if self.logger:
                self.logger.error(
                    LOG_PLUGIN_EXECUTION_ERROR,
                    validator_spec, e, exc_info=True
                )
            return ERR_PLUGIN_EXECUTION.format(error=str(e))
