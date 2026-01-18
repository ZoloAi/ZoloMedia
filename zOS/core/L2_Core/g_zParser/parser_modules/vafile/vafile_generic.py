# zCLI/subsystems/zParser/parser_modules/vafile/vafile_generic.py

"""
Generic file parsing for zVaFile package.

Handles parsing and metadata extraction for unrecognized file types (fallback).
"""

from zOS import Any, Dict, Optional

# Import constants from parent package
from . import (
    FILE_TYPE_GENERIC, FILE_TYPE_UI, FILE_TYPE_SCHEMA,
    DICT_KEY_TYPE, DICT_KEY_FILE_PATH, DICT_KEY_DATA, DICT_KEY_METADATA_KEY,
    LOG_MSG_PARSING_GENERIC,
    METADATA_KEY_TYPE, METADATA_KEY_KEY_COUNT, METADATA_KEY_DATA_TYPE,
    METADATA_KEY_ZBLOCK_COUNT, METADATA_KEY_CONSTRUCT_COUNTS, METADATA_KEY_TOTAL_ITEMS,
    METADATA_KEY_TABLE_COUNT, METADATA_KEY_TOTAL_FIELDS, METADATA_KEY_FIELD_TYPES,
    METADATA_KEY_HAS_DB_PATH, METADATA_KEY_HAS_META,
    SCHEMA_KEY_DB_PATH, SCHEMA_KEY_META,
    UI_CONSTRUCT_ZFUNC, UI_CONSTRUCT_ZLINK, UI_CONSTRUCT_ZDIALOG,
    UI_CONSTRUCT_ZMENU, UI_CONSTRUCT_ZWIZARD, UI_CONSTRUCT_ZDISPLAY
)


# GENERIC FILE PROCESSING
# ============================================================================

def parse_generic_file(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse generic zVaFile (non-UI, non-Schema).
    
    Fallback parser for files that don't match UI or Schema types.
    
    Args:
        data: Parsed YAML/JSON data
        logger: Logger instance for diagnostic output
        file_path: Optional file path for logging
    
    Returns:
        Dict[str, Any]: Parsed generic structure with format:
            {
                "type": "generic",
                "file_path": str or None,
                "data": Any,
                "metadata": {...}
            }
    
    See Also:
        - parse_zva_file: Calls this for non-UI, non-Schema files
    """
    logger.info(LOG_MSG_PARSING_GENERIC)

    return {
        DICT_KEY_TYPE: FILE_TYPE_GENERIC,
        DICT_KEY_FILE_PATH: file_path,
        DICT_KEY_DATA: data,
        DICT_KEY_METADATA_KEY: extract_generic_metadata(data)
    }


# ============================================================================
# METADATA EXTRACTION
# ============================================================================

def extract_zva_metadata(
    data: Dict[str, Any],
    file_type: str,
    logger: Any
) -> Dict[str, Any]:
    """
    Extract metadata from zVaFiles.
    
    Routes to type-specific metadata extractors based on file type.
    
    Args:
        data: Parsed zVaFile data
        file_type: Type of zVaFile ("zUI", "zSchema", "zConfig")
        logger: Logger instance for diagnostic output
    
    Returns:
        Dict[str, Any]: File-specific metadata
    
    See Also:
        - extract_ui_metadata: Extracts UI metadata
        - extract_schema_metadata: Extracts schema metadata
        - extract_generic_metadata: Extracts generic metadata
    """
    logger.debug(LOG_MSG_EXTRACTING_METADATA, file_type)

    if file_type == FILE_TYPE_ZUI:
        return extract_ui_metadata(data)
    elif file_type == FILE_TYPE_ZSCHEMA:
        return extract_schema_metadata(data)
    else:
        return extract_generic_metadata(data)


def extract_ui_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from UI files.
    
    Counts zBlocks, UI constructs, and total items for debugging and analytics.
    
    Args:
        data: Parsed UI file data
    
    Returns:
        Dict[str, Any]: UI metadata with format:
            {
                "type": "ui",
                "zblock_count": int,
                "construct_counts": {
                    "zFunc": int,
                    "zLink": int,
                    ...
                },
                "total_items": int
            }
    
    See Also:
        - extract_zva_metadata: Routes to this for UI files
    """
    metadata: Dict[str, Any] = {
        METADATA_KEY_TYPE: FILE_TYPE_UI,
        METADATA_KEY_ZBLOCK_COUNT: 0,
        METADATA_KEY_CONSTRUCT_COUNTS: {
            UI_CONSTRUCT_ZFUNC: 0,
            UI_CONSTRUCT_ZLINK: 0,
            UI_CONSTRUCT_ZDIALOG: 0,
            UI_CONSTRUCT_ZMENU: 0,
            UI_CONSTRUCT_ZWIZARD: 0,
            UI_CONSTRUCT_ZDISPLAY: 0
        },
        METADATA_KEY_TOTAL_ITEMS: 0
    }

    for _key, value in data.items():
        if isinstance(value, dict):
            metadata[METADATA_KEY_ZBLOCK_COUNT] += 1
            metadata[METADATA_KEY_TOTAL_ITEMS] += len(value)

            # Count UI constructs
            for construct in metadata[METADATA_KEY_CONSTRUCT_COUNTS]:
                metadata[METADATA_KEY_CONSTRUCT_COUNTS][construct] += sum(
                    1 for item in value.values() 
                    if isinstance(item, dict) and construct in item
                )

    return metadata


def extract_schema_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from schema files.
    
    Counts tables, fields, and field types for debugging and analytics.
    
    Args:
        data: Parsed schema file data
    
    Returns:
        Dict[str, Any]: Schema metadata with format:
            {
                "type": "schema",
                "table_count": int,
                "total_fields": int,
                "field_types": {
                    "str": int,
                    "int": int,
                    ...
                },
                "has_db_path": bool,
                "has_meta": bool
            }
    
    See Also:
        - extract_zva_metadata: Routes to this for schema files
    """
    metadata: Dict[str, Any] = {
        METADATA_KEY_TYPE: FILE_TYPE_SCHEMA,
        METADATA_KEY_TABLE_COUNT: 0,
        METADATA_KEY_TOTAL_FIELDS: 0,
        METADATA_KEY_FIELD_TYPES: {},
        METADATA_KEY_HAS_DB_PATH: SCHEMA_KEY_DB_PATH in data,
        METADATA_KEY_HAS_META: SCHEMA_KEY_META in data
    }

    for key, value in data.items():
        if key in [SCHEMA_KEY_DB_PATH, SCHEMA_KEY_META]:
            continue

        if isinstance(value, dict):
            metadata[METADATA_KEY_TABLE_COUNT] += 1
            metadata[METADATA_KEY_TOTAL_FIELDS] += len(value)

            # Count field types
            for _field_name, field_data in value.items():
                if isinstance(field_data, dict) and DICT_KEY_TYPE in field_data:
                    field_type = field_data[DICT_KEY_TYPE]
                elif isinstance(field_data, str):
                    # Parse shorthand type
                    field_type = field_data.split(CHAR_EQUALS)[0].rstrip(CHAR_EXCLAMATION + CHAR_QUESTION).strip()
                else:
                    field_type = FILE_TYPE_UNKNOWN

                metadata[METADATA_KEY_FIELD_TYPES][field_type] = metadata[METADATA_KEY_FIELD_TYPES].get(field_type, 0) + 1

    return metadata


def extract_generic_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from generic files.
    
    Basic metadata for non-UI, non-Schema files.
    
    Args:
        data: Parsed file data
    
    Returns:
        Dict[str, Any]: Generic metadata with format:
            {
                "type": "generic",
                "key_count": int,
                "data_type": str
            }
    
    See Also:
        - extract_zva_metadata: Routes to this for generic files
    """
    return {
        METADATA_KEY_TYPE: FILE_TYPE_GENERIC,
        METADATA_KEY_KEY_COUNT: len(data) if isinstance(data, dict) else 0,
        METADATA_KEY_DATA_TYPE: type(data).__name__
    }
