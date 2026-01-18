# zCLI/subsystems/zParser/parser_modules/vafile/vafile_ui.py

"""
UI file parsing for zVaFile package.

Handles parsing, validation, and metadata extraction for zUI.* files.
"""

from zOS import Any, Dict, List, Optional

# Import constants from parent package
from . import (
    FILE_TYPE_UI, FILE_TYPE_ZBLOCK, FILE_TYPE_UNKNOWN,
    DICT_KEY_TYPE, DICT_KEY_FILE_PATH, DICT_KEY_ZBLOCKS, DICT_KEY_METADATA_KEY,
    DICT_KEY_RBAC, DICT_KEY_FILE_RBAC, DICT_KEY_NAME, DICT_KEY_ITEMS,
    DICT_KEY_CONSTRUCTS, DICT_KEY_DATA, DICT_KEY_VALIDATED, DICT_KEY_ERRORS,
    DICT_KEY_WARNINGS, DICT_KEY_VALID,
    UI_CONSTRUCT_ZFUNC, UI_CONSTRUCT_ZLINK, UI_CONSTRUCT_ZDIALOG,
    UI_CONSTRUCT_ZMENU, UI_CONSTRUCT_ZWIZARD, UI_CONSTRUCT_ZDISPLAY,
    UI_CONSTRUCTS_LIST,
    LOG_MSG_VALIDATING_UI, LOG_MSG_PARSING_UI, LOG_MSG_PROCESSING_ZBLOCK,
    LOG_MSG_SKIPPING_INVALID_ZBLOCK, LOG_MSG_PARSING_UI_COMPLETED,
    LOG_MSG_PARSING_ZBLOCK, LOG_MSG_PROCESSING_ZBLOCK_ITEMS, LOG_MSG_PROCESSING_ITEM,
    LOG_MSG_FOUND_CONSTRUCT, LOG_MSG_PUBLIC_ACCESS, LOG_MSG_PARSING_UI_ITEM,
    LOG_MSG_FILE_RBAC_FOUND, LOG_MSG_INLINE_RBAC_FOUND, LOG_MSG_INLINE_RBAC_APPLIED,
    SCOPE_FILE,
    METADATA_KEY_TYPE, METADATA_KEY_ZBLOCK_COUNT, METADATA_KEY_CONSTRUCT_COUNTS,
    METADATA_KEY_TOTAL_ITEMS,
    extractzRBAC_directives,
    extract_ui_metadata
)

# UI-specific constants
ERROR_MSG_UI_EMPTY: str = "UI file cannot be empty"
ERROR_MSG_NO_ZBLOCKS: str = "UI file must contain at least one zBlock (menu section)"
ERROR_MSG_NO_RECOGNIZED_CONSTRUCTS: str = "zBlock '%s' contains no recognized UI constructs (zFunc, zLink, zDialog, zMenu, zWizard)"
ERROR_MSG_RESERVED_KEYS_UI: str = "UI file contains reserved keys that may conflict with schema files: %s"
ERROR_MSG_MISSING_CONSTRUCT_KEY: str = "%s item missing '%s' key"
ERROR_MSG_INVALID_CONSTRUCT_TYPE: str = "%s value must be a %s"
ERROR_MSG_MISSING_EVENT_FIELD: str = "zDisplay item missing required 'event' field"

RESERVED_UI_KEYS: List[str] = ["db_path", "meta", "schema", "table"]


# UI FILE PROCESSING
# ============================================================================

def validate_ui_structure(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Validate UI file structure.
    
    Validates that a UI file has the correct structure:
    - At least one zBlock (menu section)
    - Each zBlock contains recognized UI constructs
    - No reserved schema keys that might cause conflicts
    
    Args:
        data: Parsed UI file data
        logger: Logger instance for diagnostic output
        file_path: Optional file path for error messages
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List, "warnings": List}
    
    Examples:
        >>> data = {"Menu": {"Item": {"zFunc": "func"}}}
        >>> logger = get_logger()
        >>> result = validate_ui_structure(data, logger)
        >>> result["valid"]
        True
        
        >>> data = {}  # Empty
        >>> result = validate_ui_structure(data, logger)
        >>> result["valid"]
        False
    
    Notes:
        - Checks for at least one zBlock
        - Warns if zBlocks contain no recognized UI constructs
        - Warns if reserved schema keys are found
    
    See Also:
        - validate_zva_structure: Calls this for UI files
        - parse_ui_file: Uses validation results
    """
    logger.debug(LOG_MSG_VALIDATING_UI)

    validation_result: Dict[str, Any] = {
        DICT_KEY_VALID: True,
        DICT_KEY_ERRORS: [],
        DICT_KEY_WARNINGS: []
    }

    # Check for required UI structure elements
    if not data:
        validation_result[DICT_KEY_ERRORS].append(ERROR_MSG_UI_EMPTY)
        return validation_result

    # Validate zBlock structure (UI files should have menu blocks)
    zblock_count = 0
    for key, value in data.items():
        if isinstance(value, dict):
            zblock_count += 1

            # Check for common UI constructs
            has_ui_construct = any(construct in value for construct in UI_CONSTRUCTS_LIST)

            if not has_ui_construct:
                validation_result[DICT_KEY_WARNINGS].append(
                    ERROR_MSG_NO_RECOGNIZED_CONSTRUCTS % key
                )

    if zblock_count == 0:
        validation_result[DICT_KEY_ERRORS].append(ERROR_MSG_NO_ZBLOCKS)

    # Check for reserved keys
    found_reserved = [key for key in data.keys() if key in RESERVED_UI_KEYS]
    if found_reserved:
        validation_result[DICT_KEY_WARNINGS].append(
            ERROR_MSG_RESERVED_KEYS_UI % found_reserved
        )

    validation_result[DICT_KEY_VALID] = len(validation_result[DICT_KEY_ERRORS]) == 0
    return validation_result


def validate_schema_structure(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Validate schema file structure.
    
    Validates that a schema file has the correct structure:
    - At least one table definition
    - Each table has field definitions
    - Fields have required attributes
    - No UI-specific keys that might cause conflicts
    
    Args:
        data: Parsed schema file data
        logger: Logger instance for diagnostic output
        file_path: Optional file path for error messages
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List, "warnings": List}
    
    Examples:
        >>> data = {"users": {"id": "int!", "name": "str"}}
        >>> logger = get_logger()
        >>> result = validate_schema_structure(data, logger)
        >>> result["valid"]
        True
        
        >>> data = {}  # Empty
        >>> result = validate_schema_structure(data, logger)
        >>> result["valid"]
        False
    
    Notes:
        - Checks for at least one table definition
        - Validates field definitions (dict or string)
        - Warns if fields are missing type attribute
        - Warns if UI-specific keys are found
    
    See Also:
        - validate_zva_structure: Calls this for schema files
        - parse_schema_file: Uses validation results
    """
    logger.debug(LOG_MSG_VALIDATING_SCHEMA)

    validation_result: Dict[str, Any] = {
        DICT_KEY_VALID: True,
        DICT_KEY_ERRORS: [],
        DICT_KEY_WARNINGS: []
    }

    # Check for required schema structure elements
    if not data:
        validation_result[DICT_KEY_ERRORS].append(ERROR_MSG_SCHEMA_EMPTY)
        return validation_result

    # Validate table definitions
    table_count = 0
    for key, value in data.items():
        if key in [SCHEMA_KEY_DB_PATH, SCHEMA_KEY_META]:
            # Skip metadata keys
            continue

        if isinstance(value, dict):
            table_count += 1

            # Check for field definitions
            if not value:
                validation_result[DICT_KEY_WARNINGS].append(ERROR_MSG_NO_FIELD_DEFS % key)
                continue

            # Validate field structure
            for field_name, field_def in value.items():
                if isinstance(field_def, dict):
                    # Check for required field attributes
                    if DICT_KEY_TYPE not in field_def:
                        validation_result[DICT_KEY_WARNINGS].append(
                            ERROR_MSG_NO_FIELD_TYPE % (field_name, key)
                        )
                elif isinstance(field_def, str):
                    # String field definition (shorthand)
                    pass
                else:
                    validation_result[DICT_KEY_ERRORS].append(
                        ERROR_MSG_INVALID_FIELD_TYPE % (field_name, key)
                    )

    if table_count == 0:
        validation_result[DICT_KEY_ERRORS].append(ERROR_MSG_NO_TABLES)

    # Check for UI-specific keys that shouldn't be in schema files
    found_ui_keys = [key for key in data.keys() if key in RESERVED_SCHEMA_KEYS]
    if found_ui_keys:
        validation_result[DICT_KEY_WARNINGS].append(
            ERROR_MSG_UI_KEYS_IN_SCHEMA % found_ui_keys
        )

    validation_result[DICT_KEY_VALID] = len(validation_result[DICT_KEY_ERRORS]) == 0
    return validation_result


def parse_ui_file(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None,
    session: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse UI file with UI-specific logic and validation.
    
    ⚠️ CRITICAL: This function is used externally by parser_file.py.
    Signature must remain stable.
    
    Parses a UI file (zUI.*) with comprehensive RBAC directive extraction and
    zBlock processing. This is the main entry point for UI file parsing and is
    called by parser_file.py when a UI file is detected.
    
    Process Flow:
        1. **File-Level RBAC Extraction**: Extract !require_* directives from root
        2. **zBlock Processing**: Parse each menu section (zBlock)
        3. **Metadata Extraction**: Count zBlocks, UI constructs, and items
        4. **Return**: Structured UI data with RBAC and metadata
    
    Args:
        data: Parsed YAML/JSON data from UI file
        logger: Logger instance for diagnostic output
        file_path: Optional file path for error messages and logging
        session: Optional session dict (reserved for future session-aware parsing)
    
    Returns:
        Dict[str, Any]: Parsed UI structure with format:
            {
                "type": "ui",
                "file_path": str or None,
                "zblocks": {
                    "zblock_name": {
                        "name": str,
                        "type": "zblock",
                        "items": {...},
                        "constructs": {...},
                        "_filezRBAC": {...} or None
                    }
                },
                "metadata": {...},
                "zRBAC": {...} or None  # File-level RBAC (if exists)
            }
    
    Examples:
        >>> data = {
        ...     "!require_role": "user",
        ...     "Main Menu": {
        ...         "Add User": {"zFunc": "add_user"},
        ...         "Delete User": {
        ...             "zRBAC": {"require_role": "admin"},
        ...             "zFunc": "delete_user"
        ...         }
        ...     }
        ... }
        >>> logger = get_logger()
        >>> result = parse_ui_file(data, logger, file_path="zUI.users.yaml")
        >>> result["zRBAC"]
        {"require_role": "user"}
        >>> result["zblocks"]["Main Menu"]["items"]["Add User"]["zRBAC"]
        None  # Inherits from file-level
        >>> result["zblocks"]["Main Menu"]["items"]["Delete User"]["zRBAC"]
        {"require_role": "admin"}  # Inline RBAC overrides
    
    External Usage:
        parser_file.py (line 43):
            from .parser_vafile import parse_ui_file
            parsed_ui = parse_ui_file(data, logger, file_path=file_path, session=session)
        Purpose: Parse UI files with RBAC extraction
    
    Notes:
        - Signature stability is CRITICAL for external usage
        - File-level RBAC applies to all items (unless overridden)
        - Inline zRBAC in items overrides file-level RBAC
        - Default behavior: PUBLIC ACCESS (no RBAC = accessible to all)
        - zBlocks must be dictionaries (validated)
        - Metadata includes zBlock count, construct counts, total items
    
    See Also:
        - extractzRBAC_directives: Extracts file-level RBAC
        - parse_ui_zblock: Parses individual zBlocks
        - parser_file.py: External usage
        - authzRBAC.py: Verifies RBAC during execution
    """
    logger.framework.debug(LOG_MSG_PARSING_UI)

    parsed_ui: Dict[str, Any] = {
        DICT_KEY_TYPE: FILE_TYPE_UI,
        DICT_KEY_FILE_PATH: file_path,
        DICT_KEY_ZBLOCKS: {},
        DICT_KEY_METADATA_KEY: {}
    }

    # Extract file-level RBAC directives (v1.5.4 Week 3.3)
    filezRBAC, data_withoutzRBAC = extractzRBAC_directives(data, logger, scope=SCOPE_FILE)
    if filezRBAC:
        parsed_ui[DICT_KEY_RBAC] = filezRBAC
        logger.framework.debug(LOG_MSG_FILE_RBAC_FOUND, filezRBAC)

    # Process each zBlock (menu section) using cleaned data
    for zblock_name, zblock_data in data_withoutzRBAC.items():
        if not isinstance(zblock_data, dict):
            # Enhanced error message with clear fix suggestion
            logger.error(
                f"\n{'='*60}\n"
                f"ERROR: Empty or invalid zBlock detected\n"
                f"{'='*60}\n"
                f"  File: {file_path}\n"
                f"  Block: '{zblock_name}'\n"
                f"  Problem: zBlock is empty (got {type(zblock_data).__name__})\n"
                f"\n"
                f"  Current YAML:\n"
                f"    {zblock_name}:\n"
                f"\n"
                f"  Expected YAML:\n"
                f"    {zblock_name}:\n"
                f"      Block_Name:\n"
                f"        - zDisplay:\n"
                f"            event: text\n"
                f"            content: 'Your content here'\n"
                f"\n"
                f"  Fix: Add at least one sub-block with content under '{zblock_name}'\n"
                f"{'='*60}"
            )
            # Return None to immediately stop processing - this is a fatal error
            return None

        logger.debug(LOG_MSG_PROCESSING_ZBLOCK, zblock_name)

        # Parse zBlock content (with file-level RBAC passed down)
        parsed_zblock = parse_ui_zblock(zblock_name, zblock_data, logger, session, filezRBAC=filezRBAC)
        parsed_ui[DICT_KEY_ZBLOCKS][zblock_name] = parsed_zblock

    # Extract UI metadata
    parsed_ui[DICT_KEY_METADATA_KEY] = extract_ui_metadata(data)

    logger.framework.debug(LOG_MSG_PARSING_UI_COMPLETED, len(parsed_ui[DICT_KEY_ZBLOCKS]))
    return parsed_ui


def parse_ui_zblock(
    zblock_name: str,
    zblock_data: Dict[str, Any],
    logger: Any,
    session: Optional[Dict[str, Any]] = None,
    filezRBAC: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse individual UI zBlock with validation and RBAC directives (v1.5.4 Week 3.3).
    
    Parses a single zBlock (menu section) from a UI file, processing each item
    and applying RBAC directives (file-level or inline).
    
    RBAC Processing:
        - File-level RBAC is inherited by all items (unless overridden)
        - Inline zRBAC in an item overrides file-level RBAC
        - If no RBAC is specified, the item is PUBLIC (default behavior)
    
    Args:
        zblock_name: Name of the zBlock (menu section)
        zblock_data: Dictionary of items in the zBlock
        logger: Logger instance for diagnostic output
        session: Optional session dict (reserved for future use)
        filezRBAC: Optional file-level RBAC directives (inherited from parent)
    
    Returns:
        Dict[str, Any]: Parsed zBlock structure with format:
            {
                "name": str,
                "type": "zblock",
                "items": {
                    "item_name": {...}
                },
                "constructs": {
                    "zFunc": [list of item names],
                    "zLink": [list of item names],
                    ...
                },
                "_filezRBAC": {...} or None
            }
    
    Examples:
        >>> zblock_data = {
        ...     "Add User": {"zFunc": "add_user"},
        ...     "Delete User": {
        ...         "zRBAC": {"require_role": "admin"},
        ...         "zFunc": "delete_user"
        ...     }
        ... }
        >>> filezRBAC = {"require_role": "user"}
        >>> logger = get_logger()
        >>> result = parse_ui_zblock("Admin", zblock_data, logger, filezRBAC=filezRBAC)
        >>> result["_filezRBAC"]
        {"require_role": "user"}
        >>> "Add User" in result["items"]
        True
    
    Notes:
        - All items in zBlock are processed
        - Inline zRBAC is extracted and stored separately
        - UI construct type is identified for each dict item
        - Construct lists track which items use which constructs
    
    See Also:
        - parse_ui_file: Calls this for each zBlock
        - parse_ui_item: Parses individual items
        - identify_ui_construct: Identifies construct type
    """
    logger.debug(LOG_MSG_PARSING_ZBLOCK, zblock_name)

    parsed_zblock: Dict[str, Any] = {
        DICT_KEY_NAME: zblock_name,
        DICT_KEY_TYPE: FILE_TYPE_ZBLOCK,
        DICT_KEY_ITEMS: {},
        DICT_KEY_CONSTRUCTS: {
            UI_CONSTRUCT_ZFUNC: [],
            UI_CONSTRUCT_ZLINK: [],
            UI_CONSTRUCT_ZDIALOG: [],
            UI_CONSTRUCT_ZMENU: [],
            UI_CONSTRUCT_ZWIZARD: [],
            UI_CONSTRUCT_ZDISPLAY: []
        }
    }

    # Store file-level RBAC (inherited from parent)
    if filezRBAC:
        parsed_zblock[DICT_KEY_FILE_RBAC] = filezRBAC

    # Process each item in the zBlock
    # RBAC is now INLINE in the item data (v1.5.4 Week 3.3)
    logger.debug(LOG_MSG_PROCESSING_ZBLOCK_ITEMS, zblock_name, len(zblock_data))
    
    for item_name, item_data in zblock_data.items():
        logger.debug(LOG_MSG_PROCESSING_ITEM, item_name)
        
        # zKeys can be strings (zFunc, zLink), lists (menus), or dicts (zWizard, zDialog)
        # Accept all types - validation happens in dispatch

        # Check if item already has inline zRBAC
        inlinezRBAC = None
        if isinstance(item_data, dict) and DICT_KEY_RBAC in item_data:
            inlinezRBAC = item_data.pop(DICT_KEY_RBAC)  # Extract and remove from data
            logger.framework.debug(LOG_MSG_INLINE_RBAC_FOUND, item_name, inlinezRBAC)

        # Identify UI construct type (only for dict items)
        construct_type = None
        if isinstance(item_data, dict):
            construct_type = identify_ui_construct(item_data)
            if construct_type:
                parsed_zblock[DICT_KEY_CONSTRUCTS][construct_type].append(item_name)
                logger.debug(LOG_MSG_FOUND_CONSTRUCT, construct_type, item_name)

        # Parse and validate the item
        parsed_item = parse_ui_item(item_name, item_data, construct_type, logger, session)
        
        # Apply RBAC: Default is PUBLIC ACCESS (no restrictions)
        # Only apply RBAC if explicitly specified
        if inlinezRBAC is not None:
            # Item has explicit inline RBAC - use it
            parsed_item[DICT_KEY_RBAC] = inlinezRBAC
            logger.framework.debug(LOG_MSG_INLINE_RBAC_APPLIED, item_name, inlinezRBAC)
        else:
            # No inline RBAC = public access (default behavior)
            logger.debug(LOG_MSG_PUBLIC_ACCESS, item_name)
        
        parsed_zblock[DICT_KEY_ITEMS][item_name] = parsed_item

    return parsed_zblock


def identify_ui_construct(item_data: Dict[str, Any]) -> Optional[str]:
    """
    Identify the type of UI construct based on item data.
    
    Scans item data dictionary for known UI construct keys and returns the
    first match found.
    
    UI Constructs:
        - zFunc: Function invocation
        - zLink: Inter-file linking
        - zDialog: Interactive forms
        - zMenu: Menu definitions
        - zWizard: Multi-step workflows
        - zDisplay: Display events
    
    Args:
        item_data: Dictionary containing UI item data
    
    Returns:
        Optional[str]: UI construct type (e.g., "zFunc", "zLink") or None if not found
    
    Examples:
        >>> identify_ui_construct({"zFunc": "my_function"})
        "zFunc"
        
        >>> identify_ui_construct({"zLink": "@.path.to.file"})
        "zLink"
        
        >>> identify_ui_construct({"data": "value"})  # No construct
        None
    
    Notes:
        - Returns first construct found (if multiple, precedence by list order)
        - Returns None if no recognized constructs found
        - Used for categorization and validation
    
    See Also:
        - parse_ui_zblock: Uses this to categorize items
        - UI_CONSTRUCTS_LIST: List of recognized constructs
    """
    for construct in UI_CONSTRUCTS_LIST:
        if construct in item_data:
            return construct
    
    return None


def parse_ui_item(
    item_name: str,
    item_data: Any,
    construct_type: Optional[str],
    logger: Any,
    session: Optional[Dict[str, Any]] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Parse individual UI item with type-specific validation.
    
    Parses a single UI item (menu entry) and performs construct-specific
    validation based on the identified type.
    
    Args:
        item_name: Name of the UI item
        item_data: Data for the item (can be str, list, or dict)
        construct_type: Type of UI construct (zFunc, zLink, etc.) or None
        logger: Logger instance for diagnostic output
        session: Optional session dict (reserved for future use)
    
    Returns:
        Dict[str, Any]: Parsed item structure with format:
            {
                "name": str,
                "type": str,  # Construct type or "unknown"
                "data": Any,  # Original item data
                "validated": bool,
                "errors": List[str],
                "warnings": List[str] or None
            }
    
    Examples:
        >>> parse_ui_item("Add", {"zFunc": "add_user"}, "zFunc", logger)
        {"name": "Add", "type": "zFunc", "data": {...}, "validated": True, "errors": []}
        
        >>> parse_ui_item("Bad", {"zFunc": 123}, "zFunc", logger)  # Invalid type
        {"name": "Bad", "type": "zFunc", "data": {...}, "validated": False, "errors": [...]}
    
    Notes:
        - Type-specific validation only for dict items with constructs
        - Non-dict items (strings, lists) are accepted without validation
        - Validation errors are collected but don't prevent parsing
    
    See Also:
        - parse_ui_zblock: Calls this for each item
        - validate_*_item: Type-specific validators
    """
    logger.debug(LOG_MSG_PARSING_UI_ITEM, item_name, construct_type or FILE_TYPE_UNKNOWN)

    parsed_item: Dict[str, Any] = {
        DICT_KEY_NAME: item_name,
        DICT_KEY_TYPE: construct_type or FILE_TYPE_UNKNOWN,
        DICT_KEY_DATA: item_data,
        DICT_KEY_VALIDATED: True,
        DICT_KEY_ERRORS: []
    }

    # Type-specific validation (only for dict items with constructs)
    if isinstance(item_data, dict) and construct_type:
        if construct_type == UI_CONSTRUCT_ZFUNC:
            validation_result = validate_zfunc_item(item_data)
        elif construct_type == UI_CONSTRUCT_ZLINK:
            validation_result = validate_zlink_item(item_data)
        elif construct_type == UI_CONSTRUCT_ZDIALOG:
            validation_result = validate_zdialog_item(item_data)
        elif construct_type == UI_CONSTRUCT_ZMENU:
            validation_result = validate_zmenu_item(item_data)
        elif construct_type == UI_CONSTRUCT_ZWIZARD:
            validation_result = validate_zwizard_item(item_data)
        elif construct_type == UI_CONSTRUCT_ZDISPLAY:
            validation_result = validate_zdisplay_item(item_data)
        else:
            validation_result = {DICT_KEY_VALID: True, DICT_KEY_ERRORS: [], DICT_KEY_WARNINGS: []}

        parsed_item[DICT_KEY_VALIDATED] = validation_result[DICT_KEY_VALID]
        parsed_item[DICT_KEY_ERRORS] = validation_result[DICT_KEY_ERRORS]
        parsed_item[DICT_KEY_WARNINGS] = validation_result.get(DICT_KEY_WARNINGS, [])

    return parsed_item


# ============================================================================
# UI CONSTRUCT VALIDATORS (6 Declarative Primitives)
# ============================================================================

def validate_zfunc_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate zFunc item structure.
    
    zFunc items must have:
    - A "zFunc" key
    - The value must be a string (function name)
    
    Args:
        item_data: Dictionary containing zFunc item data
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List[str]}
    
    Examples:
        >>> validate_zfunc_item({"zFunc": "my_function"})
        {"valid": True, "errors": []}
        
        >>> validate_zfunc_item({"zFunc": 123})  # Invalid type
        {"valid": False, "errors": ["zFunc value must be a string"]}
    
    See Also:
        - parse_ui_item: Calls this for zFunc items
    """
    errors: List[str] = []

    if UI_CONSTRUCT_ZFUNC not in item_data:
        errors.append(ERROR_MSG_MISSING_CONSTRUCT_KEY % (UI_CONSTRUCT_ZFUNC, UI_CONSTRUCT_ZFUNC))
    elif not isinstance(item_data[UI_CONSTRUCT_ZFUNC], str):
        errors.append(ERROR_MSG_INVALID_CONSTRUCT_TYPE % (UI_CONSTRUCT_ZFUNC, "string"))

    return {DICT_KEY_VALID: len(errors) == 0, DICT_KEY_ERRORS: errors}


def validate_zlink_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate zLink item structure.
    
    zLink items must have:
    - A "zLink" key
    - The value must be a string (link path)
    
    Args:
        item_data: Dictionary containing zLink item data
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List[str]}
    
    Examples:
        >>> validate_zlink_item({"zLink": "@.path.to.file"})
        {"valid": True, "errors": []}
        
        >>> validate_zlink_item({"zLink": 123})  # Invalid type
        {"valid": False, "errors": ["zLink value must be a string"]}
    
    See Also:
        - parse_ui_item: Calls this for zLink items
    """
    errors: List[str] = []

    if UI_CONSTRUCT_ZLINK not in item_data:
        errors.append(ERROR_MSG_MISSING_CONSTRUCT_KEY % (UI_CONSTRUCT_ZLINK, UI_CONSTRUCT_ZLINK))
    elif not isinstance(item_data[UI_CONSTRUCT_ZLINK], str):
        errors.append(ERROR_MSG_INVALID_CONSTRUCT_TYPE % (UI_CONSTRUCT_ZLINK, "string"))

    return {DICT_KEY_VALID: len(errors) == 0, DICT_KEY_ERRORS: errors}


def validate_zdialog_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate zDialog item structure.
    
    zDialog items must have:
    - A "zDialog" key
    - The value must be a string or dictionary
    
    Args:
        item_data: Dictionary containing zDialog item data
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List[str]}
    
    Examples:
        >>> validate_zdialog_item({"zDialog": {"fields": [...]}})
        {"valid": True, "errors": []}
        
        >>> validate_zdialog_item({"zDialog": 123})  # Invalid type
        {"valid": False, "errors": ["zDialog value must be a string or dictionary"]}
    
    See Also:
        - parse_ui_item: Calls this for zDialog items
    """
    errors: List[str] = []

    if UI_CONSTRUCT_ZDIALOG not in item_data:
        errors.append(ERROR_MSG_MISSING_CONSTRUCT_KEY % (UI_CONSTRUCT_ZDIALOG, UI_CONSTRUCT_ZDIALOG))
    elif not isinstance(item_data[UI_CONSTRUCT_ZDIALOG], (str, dict)):
        errors.append(ERROR_MSG_INVALID_CONSTRUCT_TYPE % (UI_CONSTRUCT_ZDIALOG, "string or dictionary"))

    return {DICT_KEY_VALID: len(errors) == 0, DICT_KEY_ERRORS: errors}


def validate_zmenu_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate zMenu item structure.
    
    zMenu items must have:
    - A "zMenu" key
    - The value must be a string, dictionary, or list
    
    Args:
        item_data: Dictionary containing zMenu item data
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List[str]}
    
    Examples:
        >>> validate_zmenu_item({"zMenu": [item1, item2]})
        {"valid": True, "errors": []}
        
        >>> validate_zmenu_item({"zMenu": 123})  # Invalid type
        {"valid": False, "errors": ["zMenu value must be a string, dictionary, or list"]}
    
    See Also:
        - parse_ui_item: Calls this for zMenu items
    """
    errors: List[str] = []

    if UI_CONSTRUCT_ZMENU not in item_data:
        errors.append(ERROR_MSG_MISSING_CONSTRUCT_KEY % (UI_CONSTRUCT_ZMENU, UI_CONSTRUCT_ZMENU))
    elif not isinstance(item_data[UI_CONSTRUCT_ZMENU], (str, dict, list)):
        errors.append(ERROR_MSG_INVALID_CONSTRUCT_TYPE % (UI_CONSTRUCT_ZMENU, "string, dictionary, or list"))

    return {DICT_KEY_VALID: len(errors) == 0, DICT_KEY_ERRORS: errors}


def validate_zwizard_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate zWizard item structure.
    
    zWizard items must have:
    - A "zWizard" key
    - The value must be a dictionary
    
    Args:
        item_data: Dictionary containing zWizard item data
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List[str]}
    
    Examples:
        >>> validate_zwizard_item({"zWizard": {"steps": [...]}})
        {"valid": True, "errors": []}
        
        >>> validate_zwizard_item({"zWizard": "string"})  # Invalid type
        {"valid": False, "errors": ["zWizard value must be a dictionary"]}
    
    See Also:
        - parse_ui_item: Calls this for zWizard items
    """
    errors: List[str] = []

    if UI_CONSTRUCT_ZWIZARD not in item_data:
        errors.append(ERROR_MSG_MISSING_CONSTRUCT_KEY % (UI_CONSTRUCT_ZWIZARD, UI_CONSTRUCT_ZWIZARD))
    elif not isinstance(item_data[UI_CONSTRUCT_ZWIZARD], dict):
        errors.append(ERROR_MSG_INVALID_CONSTRUCT_TYPE % (UI_CONSTRUCT_ZWIZARD, "dictionary"))

    return {DICT_KEY_VALID: len(errors) == 0, DICT_KEY_ERRORS: errors}


def validate_zdisplay_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate zDisplay item structure.
    
    zDisplay items must have:
    - A "zDisplay" key
    - The value must be a dictionary
    - The dictionary must have an "event" field
    
    Args:
        item_data: Dictionary containing zDisplay item data
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List[str]}
    
    Examples:
        >>> validate_zdisplay_item({"zDisplay": {"event": "output", "data": {...}}})
        {"valid": True, "errors": []}
        
        >>> validate_zdisplay_item({"zDisplay": {"data": {...}}})  # Missing event
        {"valid": False, "errors": ["zDisplay item missing required 'event' field"]}
    
    See Also:
        - parse_ui_item: Calls this for zDisplay items
    """
    errors: List[str] = []

    if UI_CONSTRUCT_ZDISPLAY not in item_data:
        errors.append(ERROR_MSG_MISSING_CONSTRUCT_KEY % (UI_CONSTRUCT_ZDISPLAY, UI_CONSTRUCT_ZDISPLAY))
    elif not isinstance(item_data[UI_CONSTRUCT_ZDISPLAY], dict):
        errors.append(ERROR_MSG_INVALID_CONSTRUCT_TYPE % (UI_CONSTRUCT_ZDISPLAY, "dictionary"))
    else:
        # Check for required event field
        display_obj = item_data[UI_CONSTRUCT_ZDISPLAY]
        if "event" not in display_obj:
            errors.append(ERROR_MSG_MISSING_EVENT_FIELD)

    return {DICT_KEY_VALID: len(errors) == 0, DICT_KEY_ERRORS: errors}


# ============================================================================
