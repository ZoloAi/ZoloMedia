# zCLI/subsystems/zParser/parser_modules/vafile/vafile_schema.py

"""
Schema file parsing for zVaFile package.

Handles parsing, validation, and metadata extraction for zSchema.* files.
"""

from zOS import Any, Dict, Optional

# Import constants from parent package
from . import (
    FILE_TYPE_SCHEMA, FILE_TYPE_TABLE, FILE_TYPE_UNKNOWN,
    DICT_KEY_TYPE, DICT_KEY_FILE_PATH, DICT_KEY_TABLES, DICT_KEY_METADATA_KEY,
    DICT_KEY_NAME, DICT_KEY_FIELDS, DICT_KEY_VALIDATED, DICT_KEY_ERRORS,
    DICT_KEY_WARNINGS, DICT_KEY_VALID, DICT_KEY_DATA,
    SCHEMA_KEY_DB_PATH, SCHEMA_KEY_META, SCHEMA_KEY_REQUIRED, SCHEMA_KEY_DEFAULT,
    SCHEMA_KEY_FK, SCHEMA_KEY_VALIDATION,
    LOG_MSG_VALIDATING_SCHEMA, LOG_MSG_PARSING_SCHEMA, LOG_MSG_PROCESSING_TABLE,
    LOG_MSG_SKIPPING_INVALID_TABLE, LOG_MSG_PARSING_SCHEMA_COMPLETED,
    LOG_MSG_PARSING_TABLE, LOG_MSG_PROCESSING_FIELD, LOG_MSG_PARSING_FIELD,
    LOG_MSG_INVALID_FIELD_DEF, LOG_MSG_PARSING_SHORTHAND, LOG_MSG_PARSING_DETAILED,
    CHAR_EXCLAMATION, CHAR_EQUALS, CHAR_QUESTION,
    METADATA_KEY_TYPE, METADATA_KEY_TABLE_COUNT, METADATA_KEY_TOTAL_FIELDS,
    METADATA_KEY_FIELD_TYPES, METADATA_KEY_HAS_DB_PATH, METADATA_KEY_HAS_META,
    extract_schema_metadata
)

# Import schema-specific constants from centralized module
from ..parser_constants import (
    _ERROR_MSG_SCHEMA_EMPTY as ERROR_MSG_SCHEMA_EMPTY,
    _ERROR_MSG_NO_TABLES as ERROR_MSG_NO_TABLES,
    _ERROR_MSG_NO_FIELD_DEFS as ERROR_MSG_NO_FIELD_DEFS,
    _ERROR_MSG_NO_FIELD_TYPE as ERROR_MSG_NO_FIELD_TYPE,
    _ERROR_MSG_INVALID_FIELD_TYPE as ERROR_MSG_INVALID_FIELD_TYPE,
    _ERROR_MSG_UI_KEYS_IN_SCHEMA as ERROR_MSG_UI_KEYS_IN_SCHEMA,
    _ERROR_MSG_INVALID_FIELD_FORMAT as ERROR_MSG_INVALID_FIELD_FORMAT,
    RESERVED_SCHEMA_KEYS,  # PUBLIC constant - no privatization needed
)


# SCHEMA FILE PROCESSING
# ============================================================================

def parse_schema_file(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None,
    session: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse schema file with schema-specific logic and validation.
    
    Parses a schema file (zSchema.*) with table and field definitions. Schema
    files declare database structures using either shorthand (str!, int=5) or
    detailed (full dictionary) syntax.
    
    Args:
        data: Parsed YAML/JSON data from schema file
        logger: Logger instance for diagnostic output
        file_path: Optional file path for error messages and logging
        session: Optional session dict (reserved for future session-aware parsing)
    
    Returns:
        Dict[str, Any]: Parsed schema structure with format:
            {
                "type": "schema",
                "file_path": str or None,
                "tables": {
                    "table_name": {
                        "name": str,
                        "type": "table",
                        "fields": {...},
                        "metadata": {}
                    }
                },
                "metadata": {...}
            }
    
    Examples:
        >>> data = {
        ...     "users": {
        ...         "id": "int!",
        ...         "name": "str!",
        ...         "email": {"type": "str", "unique": True}
        ...     }
        ... }
        >>> logger = get_logger()
        >>> result = parse_schema_file(data, logger, file_path="zSchema.users.yaml")
        >>> result["type"]
        "schema"
        >>> "users" in result["tables"]
        True
    
    Notes:
        - Skips metadata keys (db_path, meta)
        - Tables must be dictionaries
        - Fields can be shorthand strings or detailed dicts
        - Metadata includes table count, field counts, field types
    
    See Also:
        - parse_schema_table: Parses individual tables
        - parse_schema_field: Parses individual fields
        - validate_schema_structure: Validates schema structure
    """
    logger.info(LOG_MSG_PARSING_SCHEMA)

    parsed_schema: Dict[str, Any] = {
        DICT_KEY_TYPE: FILE_TYPE_SCHEMA,
        DICT_KEY_FILE_PATH: file_path,
        DICT_KEY_TABLES: {},
        DICT_KEY_METADATA_KEY: {}
    }

    # Process each table definition
    for table_name, table_data in data.items():
        if table_name in [SCHEMA_KEY_DB_PATH, SCHEMA_KEY_META]:
            # Handle metadata separately
            continue

        if not isinstance(table_data, dict):
            logger.warning(LOG_MSG_SKIPPING_INVALID_TABLE, 
                         table_name, type(table_data).__name__)
            continue

        logger.debug(LOG_MSG_PROCESSING_TABLE, table_name)

        # Parse table structure
        parsed_table = parse_schema_table(table_name, table_data, logger, session)
        parsed_schema[DICT_KEY_TABLES][table_name] = parsed_table

    # Extract schema metadata
    parsed_schema[DICT_KEY_METADATA_KEY] = extract_schema_metadata(data)

    logger.info(LOG_MSG_PARSING_SCHEMA_COMPLETED, len(parsed_schema[DICT_KEY_TABLES]))
    return parsed_schema


def parse_schema_table(
    table_name: str,
    table_data: Dict[str, Any],
    logger: Any,
    session: Optional[Dict[str, Any]] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Parse individual schema table with field validation.
    
    Parses a single table definition from a schema file, processing each field
    definition (shorthand or detailed).
    
    Args:
        table_name: Name of the table
        table_data: Dictionary of field definitions
        logger: Logger instance for diagnostic output
        session: Optional session dict (reserved for future use)
    
    Returns:
        Dict[str, Any]: Parsed table structure with format:
            {
                "name": str,
                "type": "table",
                "fields": {
                    "field_name": {...}
                },
                "metadata": {}
            }
    
    Examples:
        >>> table_data = {"id": "int!", "name": "str"}
        >>> logger = get_logger()
        >>> result = parse_schema_table("users", table_data, logger)
        >>> result["name"]
        "users"
        >>> "id" in result["fields"]
        True
    
    See Also:
        - parse_schema_file: Calls this for each table
        - parse_schema_field: Parses individual fields
    """
    logger.debug(LOG_MSG_PARSING_TABLE, table_name)

    parsed_table: Dict[str, Any] = {
        DICT_KEY_NAME: table_name,
        DICT_KEY_TYPE: FILE_TYPE_TABLE,
        DICT_KEY_FIELDS: {},
        DICT_KEY_METADATA_KEY: {}
    }

    # Process each field definition
    for field_name, field_data in table_data.items():
        logger.debug(LOG_MSG_PROCESSING_FIELD, field_name)

        # Parse field definition
        parsed_field = parse_schema_field(field_name, field_data, logger, session)
        parsed_table[DICT_KEY_FIELDS][field_name] = parsed_field

    return parsed_table


def parse_schema_field(
    field_name: str,
    field_data: Any,
    logger: Any,
    session: Optional[Dict[str, Any]] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Parse individual schema field with type validation.
    
    Parses a single field definition, supporting both shorthand (str!, int=5)
    and detailed (full dictionary) syntax.
    
    Args:
        field_name: Name of the field
        field_data: Field definition (string or dict)
        logger: Logger instance for diagnostic output
        session: Optional session dict (reserved for future use)
    
    Returns:
        Dict[str, Any]: Parsed field structure with format:
            {
                "name": str,
                "type": str,
                "required": bool,
                "default": Any or None,
                "validated": bool,
                "errors": List[str]
            }
    
    Examples:
        >>> parse_schema_field("id", "int!", logger)
        {"name": "id", "type": "int", "required": True, ...}
        
        >>> parse_schema_field("name", {"type": "str", "unique": True}, logger)
        {"name": "name", "type": "str", "unique": True, ...}
    
    See Also:
        - parse_schema_table: Calls this for each field
        - parse_shorthand_field: Handles shorthand syntax
        - parse_detailed_field: Handles detailed syntax
    """
    logger.debug(LOG_MSG_PARSING_FIELD, field_name)

    if isinstance(field_data, str):
        # Shorthand field definition (e.g., "str", "int=5")
        parsed_field = parse_shorthand_field(field_data, logger)
    elif isinstance(field_data, dict):
        # Detailed field definition
        parsed_field = parse_detailed_field(field_data, logger)
    else:
        logger.warning(LOG_MSG_INVALID_FIELD_DEF, field_name)
        parsed_field = {
            DICT_KEY_NAME: field_name,
            DICT_KEY_TYPE: FILE_TYPE_UNKNOWN,
            DICT_KEY_VALIDATED: False,
            DICT_KEY_ERRORS: [ERROR_MSG_INVALID_FIELD_FORMAT]
        }

    parsed_field[DICT_KEY_NAME] = field_name
    return parsed_field


def parse_shorthand_field(field_str: str, logger: Any) -> Dict[str, Any]:
    """
    Parse shorthand field definition (e.g., "str", "int=5", "str!").
    
    Shorthand Syntax:
        - type: Field type (str, int, float, datetime, bool)
        - type!: Required field (ends with !)
        - type=value: Default value (contains =)
        - type!=value: Required field with default (combines ! and =)
    
    Args:
        field_str: Shorthand field definition string
        logger: Logger instance for diagnostic output
    
    Returns:
        Dict[str, Any]: Parsed field with format:
            {
                "type": str,
                "required": bool,
                "default": Any or None,
                "validated": bool,
                "errors": []
            }
    
    Examples:
        >>> parse_shorthand_field("str!", logger)
        {"type": "str", "required": True, "default": None, "validated": True, "errors": []}
        
        >>> parse_shorthand_field("int=5", logger)
        {"type": "int", "required": False, "default": "5", "validated": True, "errors": []}
    
    See Also:
        - parse_schema_field: Calls this for string field definitions
    """
    logger.debug(LOG_MSG_PARSING_SHORTHAND, field_str)

    # Basic shorthand parsing (type, required, default)
    field_type = field_str.rstrip(CHAR_EXCLAMATION + CHAR_QUESTION)
    required = field_str.endswith(CHAR_EXCLAMATION)
    default = None

    if CHAR_EQUALS in field_type:
        field_type, default = field_type.split(CHAR_EQUALS, 1)

    return {
        DICT_KEY_TYPE: field_type.strip(),
        SCHEMA_KEY_REQUIRED: required,
        SCHEMA_KEY_DEFAULT: default,
        DICT_KEY_VALIDATED: True,
        DICT_KEY_ERRORS: []
    }


def parse_detailed_field(field_dict: Dict[str, Any], logger: Any) -> Dict[str, Any]:
    """
    Parse detailed field definition dictionary.
    
    Detailed fields provide full attribute specification including type,
    required, unique, default, foreign keys, and validation rules.
    
    Args:
        field_dict: Dictionary with field attributes
        logger: Logger instance for diagnostic output
    
    Returns:
        Dict[str, Any]: Parsed field with all attributes
    
    Examples:
        >>> field_dict = {
        ...     "type": "str",
        ...     "required": True,
        ...     "unique": True,
        ...     "default": "N/A"
        ... }
        >>> parse_detailed_field(field_dict, logger)
        {"type": "str", "required": True, "unique": True, "default": "N/A", ...}
    
    See Also:
        - parse_schema_field: Calls this for dict field definitions
    """
    logger.debug(LOG_MSG_PARSING_DETAILED, field_dict)

    # Extract standard field attributes
    return {
        DICT_KEY_TYPE: field_dict.get(DICT_KEY_TYPE, FILE_TYPE_UNKNOWN),
        SCHEMA_KEY_REQUIRED: field_dict.get(SCHEMA_KEY_REQUIRED, False),
        SCHEMA_KEY_DEFAULT: field_dict.get(SCHEMA_KEY_DEFAULT),
        SCHEMA_KEY_FK: field_dict.get(SCHEMA_KEY_FK),
        SCHEMA_KEY_VALIDATION: field_dict.get(SCHEMA_KEY_VALIDATION, {}),
        DICT_KEY_VALIDATED: True,
        DICT_KEY_ERRORS: []
    }


# ============================================================================
