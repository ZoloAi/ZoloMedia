# zCLI/subsystems/zParser/parser_modules/vafile/__init__.py

"""
zVaFile parsing package - Foundation of the declarative paradigm.

This package provides comprehensive parsing, validation, and metadata extraction
for zVaFiles (zVacum Files - from quantum Fields theory).

Public API (for external usage):
    - parse_zva_file: Main entry point
    - parse_ui_file: UI file parser (CRITICAL - used by parser_file.py)
    - parse_schema_file: Schema file parser
    - parse_config_file: Config file parser
    - parse_generic_file: Generic fallback parser
    - extractzRBAC_directives: RBAC extraction (v1.5.4 Week 3.3)
    - validate_zva_structure: Structure validation

Package Structure:
    - vafile_ui.py: UI file parsing (~500 lines)
    - vafile_schema.py: Schema file parsing (~400 lines)
    - vafile_config.py: Config file parsing (~200 lines)
    - vafile_generic.py: Generic fallback parsing (~100 lines)

See module docstring in original parser_vafile.py for complete documentation.
"""

from zOS import Any, Dict, List, Optional, Tuple

# ============================================================================
# MODULE CONSTANTS (Shared across all vafile modules)
# ============================================================================
# NOTE: Constants must be defined BEFORE importing submodules to avoid circular imports

# File Types
FILE_TYPE_ZUI: str = "zUI"
FILE_TYPE_ZSCHEMA: str = "zSchema"
FILE_TYPE_ZCONFIG: str = "zConfig"
FILE_TYPE_UI: str = "ui"
FILE_TYPE_SCHEMA: str = "schema"
FILE_TYPE_CONFIG: str = "config"
FILE_TYPE_GENERIC: str = "generic"
FILE_TYPE_TABLE: str = "table"
FILE_TYPE_ZBLOCK: str = "zblock"
FILE_TYPE_UNKNOWN: str = "unknown"

# Log Prefixes
LOG_PREFIX_INFO: str = "[INFO]"
LOG_PREFIX_ERROR: str = "[ERROR]"
LOG_PREFIX_WARN: str = "[WARN]"
LOG_PREFIX_DEBUG: str = "[DEBUG]"
LOG_PREFIX_OK: str = "[OK]"
LOG_PREFIX_CHECK: str = "[CHECK]"
LOG_PREFIX_RBAC: str = "[RBAC]"
LOG_PREFIX_UI: str = "[UI]"
LOG_PREFIX_SCHEMA: str = "[SCHEMA]"
LOG_PREFIX_CONFIG: str = "[CONFIG]"

# Log Messages (Shared)
LOG_MSG_PARSING_ZVAFILE: str = "Parsing zVaFile (type: %s, path: %s)"
LOG_MSG_INVALID_DATA_TYPE: str = "Invalid zVaFile data: expected dict, got %s"
LOG_MSG_VALIDATION_FAILED: str = "zVaFile structure validation failed: %s"
LOG_MSG_PARSING_COMPLETE: str = "zVaFile parsing completed successfully"
LOG_MSG_VALIDATING_STRUCTURE: str = "Validating zVaFile structure (type: %s)"
LOG_MSG_EXTRACTING_METADATA: str = "Extracting metadata for file type: %s"
LOG_MSG_DIRECTIVE_EXTRACTED: str = "%s-level directive extracted: %s = %s"

# Additional log messages (UI/Schema/Config/Generic specific)
LOG_MSG_VALIDATING_UI: str = "[UI] Validating UI file structure"
LOG_MSG_PARSING_UI: str = "[UI] Parsing UI file"
LOG_MSG_PROCESSING_ZBLOCK: str = "Processing zBlock: %s"
LOG_MSG_SKIPPING_INVALID_ZBLOCK: str = "Skipping invalid zBlock '%s': expected dict, got %s"
LOG_MSG_PARSING_UI_COMPLETED: str = "[OK] UI file parsing completed: %d zBlocks processed"
LOG_MSG_PARSING_ZBLOCK: str = "[INFO] Parsing zBlock: %s"
LOG_MSG_PROCESSING_ZBLOCK_ITEMS: str = "[RBAC] Processing zBlock '%s' with %d items"
LOG_MSG_PROCESSING_ITEM: str = "[RBAC] Processing item: '%s'"
LOG_MSG_FOUND_CONSTRUCT: str = "[DEBUG] Found %s construct: %s"
LOG_MSG_PUBLIC_ACCESS: str = "[RBAC] Public access for '%s' (no zRBAC specified)"
LOG_MSG_PARSING_UI_ITEM: str = "[DEBUG] Parsing UI item: %s (type: %s)"
LOG_MSG_FILE_RBAC_FOUND: str = "[RBAC] File-level directives found: %s"
LOG_MSG_INLINE_RBAC_FOUND: str = "Found inline zRBAC for '%s': %s"
LOG_MSG_INLINE_RBAC_APPLIED: str = "[RBAC] Applied inline RBAC to '%s': %s"
LOG_MSG_VALIDATING_SCHEMA: str = "🔍 Validating schema file structure"
LOG_MSG_PARSING_SCHEMA: str = "[SCHEMA] Parsing schema file"
LOG_MSG_PROCESSING_TABLE: str = "Processing table: %s"
LOG_MSG_SKIPPING_INVALID_TABLE: str = "Skipping invalid table '%s': expected dict, got %s"
LOG_MSG_PARSING_SCHEMA_COMPLETED: str = "[OK] Schema file parsing completed: %d tables processed"
LOG_MSG_PARSING_TABLE: str = "[INFO] Parsing schema table: %s"
LOG_MSG_PROCESSING_FIELD: str = "Processing field: %s"
LOG_MSG_PARSING_FIELD: str = "[DEBUG] Parsing schema field: %s"
LOG_MSG_INVALID_FIELD_DEF: str = "Invalid field definition for '%s': expected string or dict"
LOG_MSG_PARSING_SHORTHAND: str = "[DEBUG] Parsing shorthand field: %s"
LOG_MSG_PARSING_DETAILED: str = "[DEBUG] Parsing detailed field: %s"
LOG_MSG_PARSING_GENERIC: str = "[INFO] Parsing generic zVaFile"


# Dict Keys
DICT_KEY_METADATA: str = "_metadata"
DICT_KEY_RBAC: str = "zRBAC"
DICT_KEY_FILE_RBAC: str = "_filezRBAC"
DICT_KEY_ERROR: str = "error"
DICT_KEY_ERRORS: str = "errors"
DICT_KEY_WARNINGS: str = "warnings"
DICT_KEY_VALID: str = "valid"
DICT_KEY_TYPE: str = "type"
DICT_KEY_FILE_TYPE: str = "file_type"
DICT_KEY_FILE_PATH: str = "file_path"
DICT_KEY_ZBLOCKS: str = "zblocks"
DICT_KEY_ITEMS: str = "items"
DICT_KEY_CONSTRUCTS: str = "constructs"
DICT_KEY_METADATA_KEY: str = "metadata"
DICT_KEY_TABLES: str = "tables"
DICT_KEY_FIELDS: str = "fields"
DICT_KEY_NAME: str = "name"
DICT_KEY_DATA: str = "data"
DICT_KEY_VALIDATED: str = "validated"
DICT_KEY_DETAILS: str = "details"

# UI Constructs (6 Declarative Primitives)
UI_CONSTRUCT_ZFUNC: str = "zFunc"
UI_CONSTRUCT_ZLINK: str = "zLink"
UI_CONSTRUCT_ZDIALOG: str = "zDialog"
UI_CONSTRUCT_ZMENU: str = "zMenu"
UI_CONSTRUCT_ZWIZARD: str = "zWizard"
UI_CONSTRUCT_ZDISPLAY: str = "zDisplay"

# Schema Keys
SCHEMA_KEY_DB_PATH: str = "db_path"
SCHEMA_KEY_META: str = "meta"
SCHEMA_KEY_SCHEMA: str = "schema"
SCHEMA_KEY_TABLE: str = "table"
SCHEMA_KEY_FK: str = "fk"
SCHEMA_KEY_VALIDATION: str = "validation"
SCHEMA_KEY_REQUIRED: str = "required"
SCHEMA_KEY_DEFAULT: str = "default"
SCHEMA_KEY_UNIQUE: str = "unique"
SCHEMA_KEY_AUTO_INCREMENT: str = "auto_increment"
SCHEMA_KEY_PK: str = "pk"

# RBAC Keys and Prefixes
RBAC_PREFIX_REQUIRE: str = "!require_"
RBAC_KEY_REQUIRE_ROLE: str = "!require_role"
RBAC_KEY_REQUIRE_PERMISSION: str = "!require_permission"
RBAC_KEY_ROLE: str = "require_role"
RBAC_KEY_PERMISSION: str = "require_permission"

# Error Messages
ERROR_MSG_INVALID_STRUCTURE: str = "Invalid data structure"
ERROR_MSG_VALIDATION_FAILED: str = "Structure validation failed"
ERROR_MSG_ROOT_NOT_DICT: str = "Root structure must be a dictionary"

# Special Characters
CHAR_EXCLAMATION: str = "!"
CHAR_EQUALS: str = "="
CHAR_QUESTION: str = "?"

# Misc Constants
SCOPE_FILE: str = "file"
SCOPE_BLOCK: str = "block"
RBAC_PREFIX_LENGTH: int = 1  # Length of "!" to strip

# UI Construct Lists (for validation)
UI_CONSTRUCTS_LIST: List[str] = [
    UI_CONSTRUCT_ZFUNC,
    UI_CONSTRUCT_ZLINK,
    UI_CONSTRUCT_ZDIALOG,
    UI_CONSTRUCT_ZMENU,
    UI_CONSTRUCT_ZWIZARD,
    UI_CONSTRUCT_ZDISPLAY
]

# Metadata Keys
METADATA_KEY_TYPE: str = "type"
METADATA_KEY_ZBLOCK_COUNT: str = "zblock_count"
METADATA_KEY_CONSTRUCT_COUNTS: str = "construct_counts"
METADATA_KEY_TOTAL_ITEMS: str = "total_items"
METADATA_KEY_TABLE_COUNT: str = "table_count"
METADATA_KEY_TOTAL_FIELDS: str = "total_fields"
METADATA_KEY_FIELD_TYPES: str = "field_types"
METADATA_KEY_HAS_DB_PATH: str = "has_db_path"
METADATA_KEY_HAS_META: str = "has_meta"
METADATA_KEY_KEY_COUNT: str = "key_count"
METADATA_KEY_DATA_TYPE: str = "data_type"


# ============================================================================
# RBAC DIRECTIVE EXTRACTION (v1.5.4 Week 3.3)
# ============================================================================

def extractzRBAC_directives(
    data: Dict[str, Any],
    logger: Any,
    scope: str = SCOPE_FILE
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract RBAC directives from YAML data (v1.5.4 Week 3.3).
    
    See original parser_vafile.py for complete documentation.
    """
    rbac_directives: Dict[str, Any] = {}
    data_withoutzRBAC: Dict[str, Any] = {}
    
    for key, value in data.items():
        if key.startswith(RBAC_PREFIX_REQUIRE):
            directive_name = key[RBAC_PREFIX_LENGTH:]
            rbac_directives[directive_name] = value
            logger.debug(LOG_MSG_DIRECTIVE_EXTRACTED, scope, directive_name, value)
        else:
            data_withoutzRBAC[key] = value
    
    return rbac_directives if rbac_directives else None, data_withoutzRBAC


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def parse_zva_file(
    data: Dict[str, Any],
    file_type: str,
    logger: Any,
    file_path: Optional[str] = None,
    session: Optional[Dict[str, Any]] = None,
    display: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Main entry point for zVaFile parsing and validation.
    
    See original parser_vafile.py for complete documentation.
    """
    if display:
        display.zDeclare("parse_zva_file", color="SCHEMA", indent=6, style="single")

    logger.info(LOG_MSG_PARSING_ZVAFILE, file_type, file_path or FILE_TYPE_UNKNOWN)

    if not isinstance(data, dict):
        logger.error(LOG_MSG_INVALID_DATA_TYPE, type(data).__name__)
        return {DICT_KEY_ERROR: ERROR_MSG_INVALID_STRUCTURE, DICT_KEY_TYPE: file_type}

    # Validate basic structure
    validation_result = validate_zva_structure(data, file_type, logger, file_path)
    if validation_result.get(DICT_KEY_ERRORS):
        logger.error(LOG_MSG_VALIDATION_FAILED, validation_result[DICT_KEY_ERRORS])
        return {DICT_KEY_ERROR: ERROR_MSG_VALIDATION_FAILED, DICT_KEY_DETAILS: validation_result}

    # Parse based on file type
    if file_type == FILE_TYPE_ZUI:
        result = parse_ui_file(data, logger, file_path, session)
    elif file_type == FILE_TYPE_ZSCHEMA:
        result = parse_schema_file(data, logger, file_path, session)
    elif file_type == FILE_TYPE_ZCONFIG:
        result = parse_config_file(data, logger, file_path, session)
    else:
        # Generic parsing for other file types
        result = parse_generic_file(data, logger, file_path)

    # Extract metadata
    metadata = extract_zva_metadata(data, file_type, logger)
    result[DICT_KEY_METADATA] = metadata

    logger.info(LOG_MSG_PARSING_COMPLETE)
    return result


def validate_zva_structure(
    data: Dict[str, Any],
    file_type: str,
    logger: Any,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate zVaFile structure based on type.
    
    See original parser_vafile.py for complete documentation.
    """
    logger.debug(LOG_MSG_VALIDATING_STRUCTURE, file_type)

    validation_result: Dict[str, Any] = {
        DICT_KEY_VALID: True,
        DICT_KEY_ERRORS: [],
        DICT_KEY_WARNINGS: [],
        DICT_KEY_FILE_TYPE: file_type,
        DICT_KEY_FILE_PATH: file_path
    }

    if not isinstance(data, dict):
        validation_result[DICT_KEY_VALID] = False
        validation_result[DICT_KEY_ERRORS].append(ERROR_MSG_ROOT_NOT_DICT)
        return validation_result

    # Type-specific validation
    if file_type == FILE_TYPE_ZUI:
        ui_validation = validate_ui_structure(data, logger, file_path)
        validation_result[DICT_KEY_ERRORS].extend(ui_validation.get(DICT_KEY_ERRORS, []))
        validation_result[DICT_KEY_WARNINGS].extend(ui_validation.get(DICT_KEY_WARNINGS, []))

    elif file_type == FILE_TYPE_ZSCHEMA:
        schema_validation = validate_schema_structure(data, logger, file_path)
        validation_result[DICT_KEY_ERRORS].extend(schema_validation.get(DICT_KEY_ERRORS, []))
        validation_result[DICT_KEY_WARNINGS].extend(schema_validation.get(DICT_KEY_WARNINGS, []))

    elif file_type == FILE_TYPE_ZCONFIG:
        config_validation = validate_config_structure(data, logger, file_path)
        validation_result[DICT_KEY_ERRORS].extend(config_validation.get(DICT_KEY_ERRORS, []))
        validation_result[DICT_KEY_WARNINGS].extend(config_validation.get(DICT_KEY_WARNINGS, []))

    validation_result[DICT_KEY_VALID] = len(validation_result[DICT_KEY_ERRORS]) == 0
    return validation_result


def extract_zva_metadata(
    data: Dict[str, Any],
    file_type: str,
    logger: Any
) -> Dict[str, Any]:
    """
    Extract metadata from zVaFiles.
    
    See original parser_vafile.py for complete documentation.
    """
    logger.debug(LOG_MSG_EXTRACTING_METADATA, file_type)

    if file_type == FILE_TYPE_ZUI:
        return extract_ui_metadata(data)
    elif file_type == FILE_TYPE_ZSCHEMA:
        return extract_schema_metadata(data)
    elif file_type == FILE_TYPE_ZCONFIG:
        return extract_config_metadata(data)
    else:
        return extract_generic_metadata(data)


# ============================================================================
# IMPORT TYPE-SPECIFIC PARSERS (After constants are defined)
# ============================================================================
# NOTE: These imports must come AFTER all constants to avoid circular imports
# CRITICAL: vafile_generic MUST be imported FIRST because it contains metadata
# extraction functions that other modules depend on

# Import metadata functions FIRST (from generic)
from .vafile_generic import (
    extract_ui_metadata,
    extract_schema_metadata,
    extract_generic_metadata,
    parse_generic_file
)

# Now import UI and Schema (they depend on metadata functions)
from .vafile_ui import (
    parse_ui_file,
    validate_ui_structure,
    validate_schema_structure
)
from .vafile_schema import (
    parse_schema_file
)

# Config has its own metadata extraction
from .vafile_config import (
    parse_config_file,
    validate_config_structure,
    extract_config_metadata
)

# Server routing (v1.5.4 Phase 2)
from .vafile_server import (
    parse_server_file
)


# Export all public API
__all__ = [
    # Main entry points
    'parse_zva_file',
    'validate_zva_structure',
    'extract_zva_metadata',
    'extractzRBAC_directives',
    
    # Type-specific parsers
    'parse_ui_file',
    'parse_schema_file',
    'parse_config_file',
    'parse_server_file',
    'parse_generic_file',
    
    # Type-specific validators
    'validate_ui_structure',
    'validate_schema_structure',
    'validate_config_structure',
    
    # Type-specific metadata extractors
    'extract_ui_metadata',
    'extract_schema_metadata',
    'extract_config_metadata',
    'extract_generic_metadata',
    
    # Constants (selected - most commonly used externally)
    'FILE_TYPE_ZUI',
    'FILE_TYPE_ZSCHEMA',
    'FILE_TYPE_ZCONFIG',
    'FILE_TYPE_UI',
    'FILE_TYPE_SCHEMA',
    'FILE_TYPE_CONFIG',
    'FILE_TYPE_GENERIC',
    'UI_CONSTRUCT_ZFUNC',
    'UI_CONSTRUCT_ZLINK',
    'UI_CONSTRUCT_ZDIALOG',
    'UI_CONSTRUCT_ZMENU',
    'UI_CONSTRUCT_ZWIZARD',
    'UI_CONSTRUCT_ZDISPLAY',
]


