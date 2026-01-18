# zCLI/subsystems/zParser/parser_modules/vafile/vafile_config.py

"""
Config file parsing for zVaFile package.

Handles parsing, validation, and metadata extraction for zConfig.* files.
This is a NEW module to properly handle zConfig files (previously falling through
to generic parsing).
"""

from zOS import Any, Dict, List, Optional

# Import constants from parent package
from . import (
    FILE_TYPE_CONFIG,
    DICT_KEY_TYPE, DICT_KEY_FILE_PATH, DICT_KEY_DATA, DICT_KEY_METADATA_KEY,
    DICT_KEY_VALID, DICT_KEY_ERRORS, DICT_KEY_WARNINGS,
    LOG_PREFIX_CONFIG,
    METADATA_KEY_TYPE
)

# Config-specific constants
LOG_MSG_VALIDATING_CONFIG: str = f"{LOG_PREFIX_CONFIG} Validating config file structure"
LOG_MSG_PARSING_CONFIG: str = f"{LOG_PREFIX_CONFIG} Parsing config file"
LOG_MSG_PARSING_CONFIG_COMPLETED: str = f"{LOG_PREFIX_CONFIG} Config file parsing completed: %d settings processed"
ERROR_MSG_CONFIG_EMPTY: str = "Config file cannot be empty"
ERROR_MSG_RESERVED_KEYS_CONFIG: str = "Config file contains reserved keys that may conflict with other file types: %s"

# Reserved keys that shouldn't be in config files
RESERVED_CONFIG_KEYS: List[str] = ["zFunc", "zLink", "zDialog", "zMenu", "zWizard", "zDisplay"]

# Common config top-level keys (informational)
COMMON_CONFIG_KEYS: List[str] = [
    "environment", "paths", "database", "server", "logging",
    "features", "plugins", "api", "security", "cache"
]


def validate_config_structure(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Validate config file structure.
    
    Validates that a config file has the correct structure:
    - Not empty
    - No UI-specific keys that might cause conflicts
    
    Args:
        data: Parsed config file data
        logger: Logger instance for diagnostic output
        file_path: Optional file path for error messages
    
    Returns:
        Dict[str, Any]: Validation result {"valid": bool, "errors": List, "warnings": List}
    
    Examples:
        >>> data = {"environment": "production", "database": {"host": "localhost"}}
        >>> logger = get_logger()
        >>> result = validate_config_structure(data, logger)
        >>> result["valid"]
        True
        
        >>> data = {}  # Empty
        >>> result = validate_config_structure(data, logger)
        >>> result["valid"]
        False
    
    Notes:
        - Checks for at least one setting
        - Warns if UI-specific keys are found
        - Config files are flexible (allow any structure)
    
    See Also:
        - validate_zva_structure: Calls this for config files
        - parse_config_file: Uses validation results
    """
    logger.debug(LOG_MSG_VALIDATING_CONFIG)

    validation_result: Dict[str, Any] = {
        DICT_KEY_VALID: True,
        DICT_KEY_ERRORS: [],
        DICT_KEY_WARNINGS: []
    }

    # Check for required config structure elements
    if not data:
        validation_result[DICT_KEY_ERRORS].append(ERROR_MSG_CONFIG_EMPTY)
        return validation_result

    # Check for UI-specific keys that shouldn't be in config files
    found_ui_keys = [key for key in data.keys() if key in RESERVED_CONFIG_KEYS]
    if found_ui_keys:
        validation_result[DICT_KEY_WARNINGS].append(
            ERROR_MSG_RESERVED_KEYS_CONFIG % found_ui_keys
        )

    validation_result[DICT_KEY_VALID] = len(validation_result[DICT_KEY_ERRORS]) == 0
    return validation_result


def parse_config_file(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None,
    session: Optional[Dict[str, Any]] = None  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Parse config file with config-specific logic and validation.
    
    Parses a config file (zConfig.*) with flexible structure support. Config files
    can contain environment settings, paths, database configurations, feature flags,
    and any other application-specific settings.
    
    Args:
        data: Parsed YAML/JSON data from config file
        logger: Logger instance for diagnostic output
        file_path: Optional file path for error messages and logging
        session: Optional session dict (reserved for future session-aware parsing)
    
    Returns:
        Dict[str, Any]: Parsed config structure with format:
            {
                "type": "config",
                "file_path": str or None,
                "data": {...},  # Raw config data
                "metadata": {...}
            }
    
    Examples:
        >>> data = {
        ...     "environment": "production",
        ...     "database": {
        ...         "host": "localhost",
        ...         "port": 5432
        ...     },
        ...     "features": {
        ...         "enable_auth": True,
        ...         "enable_cache": False
        ...     }
        ... }
        >>> logger = get_logger()
        >>> result = parse_config_file(data, logger, file_path="zConfig.app.yaml")
        >>> result["type"]
        "config"
        >>> "database" in result["data"]
        True
    
    Notes:
        - Config files have flexible structure (no strict schema)
        - All data is preserved in the "data" key
        - Metadata includes setting count and common keys found
        - Future: May add environment-specific parsing, validation rules
    
    See Also:
        - validate_config_structure: Validates config structure
        - extract_config_metadata: Extracts config-specific metadata
    """
    logger.info(LOG_MSG_PARSING_CONFIG)

    parsed_config: Dict[str, Any] = {
        DICT_KEY_TYPE: FILE_TYPE_CONFIG,
        DICT_KEY_FILE_PATH: file_path,
        DICT_KEY_DATA: data,
        DICT_KEY_METADATA_KEY: {}
    }

    # Extract config metadata
    parsed_config[DICT_KEY_METADATA_KEY] = extract_config_metadata(data)

    logger.info(LOG_MSG_PARSING_CONFIG_COMPLETED, len(data))
    return parsed_config


def extract_config_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from config files.
    
    Extracts basic metadata for config files, including setting count and
    identification of common config keys.
    
    Args:
        data: Parsed config file data
    
    Returns:
        Dict[str, Any]: Config metadata with format:
            {
                "type": "config",
                "setting_count": int,
                "top_level_keys": List[str],
                "common_keys_found": List[str]
            }
    
    Examples:
        >>> data = {"environment": "prod", "database": {...}, "logging": {...}}
        >>> metadata = extract_config_metadata(data)
        >>> metadata["setting_count"]
        3
        >>> "database" in metadata["common_keys_found"]
        True
    
    Notes:
        - Identifies common config keys (environment, paths, database, etc.)
        - Counts top-level settings
        - Future: May add nested structure analysis, type detection
    
    See Also:
        - parse_config_file: Uses this to extract metadata
    """
    metadata: Dict[str, Any] = {
        METADATA_KEY_TYPE: FILE_TYPE_CONFIG,
        "setting_count": len(data),
        "top_level_keys": list(data.keys()),
        "common_keys_found": []
    }

    # Identify common config keys
    for key in data.keys():
        if key in COMMON_CONFIG_KEYS:
            metadata["common_keys_found"].append(key)

    return metadata

