# zCLI/subsystems/zParser/parser_modules/parser_file.py

"""
Centralized file parsing module for YAML, JSON, and expression parsing.

This module provides comprehensive file content parsing with automatic format detection,
UI file RBAC transformation, and expression evaluation. It serves as the primary
interface for loading and parsing declarative zVaFiles (zUI, zSchema, zConfig) and
other configuration files throughout the zCLI system.

Key Features:
    - **Format Auto-Detection**: Automatically detects JSON vs YAML from content
    - **RBAC Transformation**: Applies RBAC directive extraction for UI files
    - **zWalker Compatibility**: Transforms parsed UI structure for zWalker consumption
    - **Multi-Format Support**: Handles .json, .yaml, .yml, .zolo, and expression strings
    - **Robust Error Handling**: Comprehensive exception handling with logging

Architecture:
    1. **parse_file_content()**: Main entry point (6 external usages)
       - Detects format, routes to parser, applies UI transformations
    2. **parse_yaml() / parse_json()**: Format-specific parsers
       - Safe parsing with error handling
    3. **detect_format()**: Content-based format detection
       - Fallback when file extension unavailable
    4. **parse_file_by_path()**: Convenience method
       - Loads + parses in one call
    5. **parse_json_expr()**: Expression parsing
       - For zExpr_eval compatibility

RBAC Transformation (zUI Files):
    When a UI file is detected (via "zUI" in path or "/UI/" in path), the module:
    1. Delegates to vafile.parse_ui_file() for RBAC extraction
    2. Transforms the structured format to zWalker-compatible format
    3. Merges zRBAC metadata into items for dispatch consumption
    
    Transformation Flow:
        Input (from vafile):  {zblocks: {block: {items: {item: {data, zRBAC}}}}}
        Output (for zWalker): {block: {item: {data + zRBAC merged}}}
    
    This transformation is CRITICAL for zLoader (line 63) which loads UI files
    for the zWalker navigation system. The zRBAC metadata must be properly merged
    so that authzRBAC.py can check permissions during command dispatch.

UI File Detection:
    A file is considered a UI file if:
    1. "zUI" appears in the file path (e.g., "zUI.users.yaml")
    2. "/UI/" appears in the directory path (e.g., "/path/to/UI/users.yaml")
    3. "zUI" appears in the file extension (e.g., ".zUI.yaml")
    
    Detection uses multiple fallbacks to ensure UI files are always identified,
    even when path information is incomplete.

External Usage (6 Files - CRITICAL):
    1. **zParser.py** (line 150):
       - Facade delegates all file parsing
       - parse_file_content(raw_content, logger, file_extension, session, file_path)
    
    2. **zLoader.py** (line 63): ⚠️ CRITICAL
       - Loads UI files for zWalker
       - Relies on RBAC transformation for navigation
    
    3. **authzRBAC.py**:
       - Loads RBAC policy files
       - parse_file_content(raw_content, logger, ".yaml")
    
    4. **auth_session_persistence.py**:
       - Loads session data
       - parse_file_content(raw_content, logger)
    
    5. **func_args.py**:
       - Loads function argument definitions
       - parse_file_content(raw_content, logger, ".yaml")
    
    6. **load_executor.py**:
       - Loads executable files
       - parse_file_content(raw_content, logger, ext)

Signature Stability:
    All function signatures are STABLE and must maintain backward compatibility.
    Any changes to parse_file_content() parameters or return format will break
    6 external usages. Type hints and internal refactoring are safe.

Format Auto-Detection:
    When file_extension is None, detect_format() analyzes content:
    - JSON: Starts with { or [
    - YAML: Contains : or starts with -
    - Default: YAML (most common in zCLI)
    
    Detection is heuristic-based and handles common formats reliably.

Dependencies:
    - **vafile package**: For UI file RBAC extraction (Week 6.8.6)
    - **yaml, json**: Python standard libraries for parsing
    - **os**: For file operations

Performance:
    - Parsing is I/O bound (file reading)
    - RBAC transformation is O(n) where n = number of UI items
    - Format detection is O(1) (first char inspection)

Thread Safety:
    All functions are thread-safe (no shared state).
    Logger is passed as parameter (no global state).

Examples:
    >>> # Parse YAML file
    >>> with open("config.yaml", "r") as f:
    ...     data = parse_file_content(f.read(), logger, ".yaml")
    
    >>> # Parse UI file (with RBAC)
    >>> with open("zUI.users.yaml", "r") as f:
    ...     ui_data = parse_file_content(f.read(), logger, ".yaml", 
    ...                                   file_path="zUI.users.yaml")
    
    >>> # Parse with auto-detection
    >>> data = parse_file_content('{"key": "value"}', logger)  # Detects JSON
    
    >>> # Parse file by path (convenience)
    >>> data = parse_file_by_path("/path/to/file.yaml", logger)

Notes:
    - Empty content returns None (not an error)
    - Unsupported extensions return None with error log
    - YAML is preferred default (zCLI convention)
    - RBAC transformation only applies to UI files
    - Expression parsing uses single-quote normalization

Version History:
    - v1.5.4 Week 6.8.6: Added vafile package integration
    - v1.5.4 Week 6.8.7: Industry-grade upgrade (D+ → A+)
                         - Added 100% type hints
                         - Added 35+ module constants
                         - Extracted RBAC transformation helper
                         - Comprehensive documentation
                         - Eliminated all magic strings

See Also:
    - vafile package: UI/Schema/Config parsing (Week 6.8.6)
    - zLoader: UI file loading for zWalker
    - authzRBAC: RBAC permission checking
    - zParser: Main parsing facade
"""

from zOS import os, json, yaml, Any, Dict, List, Optional, Union

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# File Extensions
FILE_EXT_JSON: str = ".json"
FILE_EXT_YAML: str = ".yaml"
FILE_EXT_YML: str = ".yml"
FILE_EXT_ZOLO: str = ".zolo"

# Log Prefixes
LOG_PREFIX_PARSE: str = "[parse_file_content]"
LOG_PREFIX_RBAC: str = "[RBAC]"

# File Type Markers (for UI file detection)
FILE_MARKER_ZUI: str = "zUI"
FILE_MARKER_UI_PATH: str = "/UI/"

# Dict Keys (from vafile package - for RBAC transformation)
DICT_KEY_ZBLOCKS: str = "zblocks"
DICT_KEY_ITEMS: str = "items"
DICT_KEY_DATA: str = "data"
DICT_KEY_RBAC: str = "zRBAC"
DICT_KEY_VALUE: str = "_value"

# Content Detection Markers
CONTENT_MARKER_JSON_START_BRACE: str = "{"
CONTENT_MARKER_JSON_START_BRACKET: str = "["
CONTENT_MARKER_YAML_COLON: str = ":"
CONTENT_MARKER_YAML_DASH: str = "-"

# Log Messages
LOG_MSG_PARSE_CALLED: str = "Called with file_extension=%s"
LOG_MSG_EMPTY_CONTENT: str = "Empty content provided for parsing"
LOG_MSG_AUTO_DETECTED: str = "Auto-detected format: %s"
LOG_MSG_IS_UI_FILE: str = "is_ui_file=%s (file_extension=%s, file_path=%s)"
LOG_MSG_DETECTED_UI: str = "Detected UI file, applying RBAC parsing"
LOG_MSG_RAW_DATA_KEYS: str = "Raw data keys: %s"
LOG_MSG_PARSED_UI_TYPE: str = "Parsed UI structure: %s"
LOG_MSG_PARSED_UI_KEYS: str = "Parsed UI keys: %s"
LOG_MSG_TRANSFORMING_ZBLOCKS: str = "Transforming zblocks: %s"
LOG_MSG_PROCESSING_ZBLOCK: str = "Processing zblock: %s"
LOG_MSG_FOUND_ITEMS: str = "Found %d items in %s"
LOG_MSG_ATTACHED_RBAC: str = "Attached zRBAC to %s"
LOG_MSG_WRAPPED_RBAC: str = "Wrapped %s with zRBAC"
LOG_MSG_TRANSFORM_COMPLETE: str = "Transformation complete, returning %d zblocks"
LOG_MSG_FINAL_RESULT_KEYS: str = "Final result keys: %s"
LOG_MSG_NO_ZBLOCKS_STRUCTURE: str = "Parsed UI doesn't have expected 'zblocks' structure!"
LOG_MSG_UNSUPPORTED_EXT: str = "Unsupported file extension: %s"
LOG_MSG_YAML_PARSED: str = "YAML parsed successfully! Type: %s, Keys: %s"
LOG_MSG_YAML_PARSE_ERROR: str = "Failed to parse YAML: %s"
LOG_MSG_YAML_UNEXPECTED_ERROR: str = "Unexpected error parsing YAML: %s"
LOG_MSG_JSON_PARSED: str = "JSON parsed successfully! Type: %s, Keys: %s"
LOG_MSG_JSON_PARSE_ERROR: str = "Failed to parse JSON: %s"
LOG_MSG_JSON_UNEXPECTED_ERROR: str = "Unexpected error parsing JSON: %s"
LOG_MSG_DETECTED_JSON: str = "Detected JSON format (starts with { or [)"
LOG_MSG_DETECTED_YAML: str = "Detected YAML format (contains : or starts with -)"
LOG_MSG_DEFAULT_YAML: str = "Could not detect format, defaulting to YAML"
LOG_MSG_FILE_NOT_FOUND: str = "File not found: %s"
LOG_MSG_FILE_READ_ERROR: str = "Failed to read file %s: %s"
LOG_MSG_JSON_EXPR_ERROR: str = "Failed to parse JSON expression: %s"

# Error Messages
ERROR_MSG_UNSUPPORTED_EXTENSION: str = "Unsupported file extension"
ERROR_MSG_FILE_NOT_FOUND: str = "File not found"
ERROR_MSG_FILE_READ_FAILED: str = "Failed to read file"

# Default Values
DEFAULT_ENCODING: str = "utf-8"
DEFAULT_FORMAT: str = FILE_EXT_YAML

# Special Values
STR_N_A: str = "N/A"
CHAR_SINGLE_QUOTE: str = "'"
CHAR_DOUBLE_QUOTE: str = '"'


# ============================================================================
# STANDALONE ZOLO LIBRARY INTEGRATION
# ============================================================================
# 
# The .zolo format is now handled by a standalone library (just like YAML).
# zCLI is file-format agnostic and simply imports external parsers.
# 
# For .zolo files: import zolo (standalone library)
# For .yaml files: import yaml (PyYAML library)
# For .json files: import json (Python stdlib)
# 
# No parsing logic lives in zCLI - it's delegated to the libraries.
# ============================================================================

try:
    from zlsp.core import parser as zolo
    ZOLO_AVAILABLE = True
except ImportError:
    ZOLO_AVAILABLE = False
    # Fallback: zolo library not installed, .zolo files will be treated as YAML
except Exception:
    ZOLO_AVAILABLE = False


# ============================================================================
# RBAC TRANSFORMATION HELPER
# ============================================================================

def _transform_parsed_ui_for_walker(
    parsed_ui: Dict[str, Any],
    logger: Any
) -> Optional[Dict[str, Any]]:
    """
    Transform parsed UI structure to zWalker-compatible format.
    
    This is a CRITICAL helper function that transforms the structured UI format
    returned by vafile.parse_ui_file() into the flat format expected by zWalker.
    
    Transformation:
        Input:  {zblocks: {block: {items: {item: {data: {...}, zRBAC: {...}}}}}}
        Output: {block: {item: {... data merged with zRBAC ...}}}
    
    The transformation ensures that:
    1. zRBAC metadata is properly merged into item data
    2. Non-dict values are wrapped with {_value: value, zRBAC: {...}}
    3. zWalker receives a flat structure it can navigate
    4. authzRBAC.py can access zRBAC during dispatch
    
    Args:
        parsed_ui: Structured UI data from vafile.parse_ui_file()
        logger: Logger instance for diagnostic output
    
    Returns:
        Optional[Dict[str, Any]]: Transformed structure for zWalker, or None if invalid
    
    Process:
        1. Extract zblocks from parsed_ui
        2. For each zblock, extract items
        3. For each item, merge zRBAC into data
        4. Handle both dict and non-dict values
        5. Return flat {block: {item: data}} structure
    
    Examples:
        >>> parsed_ui = {
        ...     "zblocks": {
        ...         "Menu": {
        ...             "items": {
        ...                 "Add": {"data": {"zFunc": "add"}, "zRBAC": {"require_role": "user"}},
        ...                 "Delete": {"data": {"zFunc": "delete"}, "zRBAC": {"require_role": "admin"}}
        ...             }
        ...         }
        ...     }
        ... }
        >>> result = _transform_parsed_ui_for_walker(parsed_ui, logger)
        >>> result
        {"Menu": {"Add": {"zFunc": "add", "zRBAC": {...}}, "Delete": {"zFunc": "delete", "zRBAC": {...}}}}
    
    Notes:
        - This function is performance-critical (called for every UI file load)
        - Complexity is O(n) where n = total UI items across all zblocks
        - Handles edge cases: missing data key, non-dict values, missing zRBAC
        - Logs transformation steps for debugging
    
    External Dependencies:
        - Used exclusively by parse_file_content() (line ~75)
        - Result consumed by zLoader.py (line 63) for zWalker
        - zRBAC metadata used by authzRBAC.py during dispatch
    
    See Also:
        - parse_file_content: Calls this helper for UI files
        - vafile.parse_ui_file: Produces the input structure
        - zLoader: Consumes the output structure
        - authzRBAC: Uses zRBAC metadata for permission checks
    """
    if not isinstance(parsed_ui, dict) or DICT_KEY_ZBLOCKS not in parsed_ui:
        logger.warning(LOG_MSG_NO_ZBLOCKS_STRUCTURE)
        return None
    
    result: Dict[str, Any] = {}
    logger.debug(LOG_MSG_TRANSFORMING_ZBLOCKS, list(parsed_ui[DICT_KEY_ZBLOCKS].keys()))
    
    for zblock_name, zblock_data in parsed_ui[DICT_KEY_ZBLOCKS].items():
        logger.debug(LOG_MSG_PROCESSING_ZBLOCK, zblock_name)
        
        if not isinstance(zblock_data, dict) or DICT_KEY_ITEMS not in zblock_data:
            continue
        
        result[zblock_name] = {}
        logger.debug(LOG_MSG_FOUND_ITEMS, len(zblock_data[DICT_KEY_ITEMS]), zblock_name)
        
        for item_name, item_data in zblock_data[DICT_KEY_ITEMS].items():
            # Merge zRBAC into the data for dispatch
            if isinstance(item_data, dict):
                value = item_data.get(DICT_KEY_DATA, item_data)
                
                # If value is dict, add zRBAC to it; otherwise wrap it
                if isinstance(value, dict) and DICT_KEY_RBAC in item_data:
                    value[DICT_KEY_RBAC] = item_data[DICT_KEY_RBAC]
                    logger.debug(LOG_MSG_ATTACHED_RBAC, item_name)
                elif DICT_KEY_RBAC in item_data:
                    # Wrap non-dict values with zRBAC metadata
                    value = {DICT_KEY_VALUE: value, DICT_KEY_RBAC: item_data[DICT_KEY_RBAC]}
                    logger.debug(LOG_MSG_WRAPPED_RBAC, item_name)
                
                result[zblock_name][item_name] = value
            else:
                result[zblock_name][item_name] = item_data
    
    logger.framework.debug(LOG_MSG_TRANSFORM_COMPLETE, len(result))
    logger.debug(LOG_MSG_FINAL_RESULT_KEYS, list(result.keys()))
    return result


# ============================================================================
# MAIN FILE PARSING
# ============================================================================

def parse_file_content(
    raw_content: Union[str, bytes],
    logger: Any,
    file_extension: Optional[str] = None,
    session: Optional[Dict[str, Any]] = None,
    file_path: Optional[str] = None
) -> Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]:
    """
    Parse raw file content into Python objects with format detection and RBAC transformation.
    
    ⚠️ CRITICAL: This function has 6 external usages. Signature must remain stable.
    
    Main entry point for file parsing throughout zCLI. Handles:
    - Automatic format detection (JSON vs YAML)
    - UI file detection and RBAC transformation
    - Format-specific parsing with error handling
    - zWalker-compatible output transformation
    
    Args:
        raw_content: Raw file content (string or bytes)
        logger: Logger instance for diagnostic output
        file_extension: Optional file extension hint (".json", ".yaml", ".yml")
                       If None, format is auto-detected from content
        session: Optional session dict (passed to parse_ui_file for RBAC context)
        file_path: Optional file path for UI file detection and logging
    
    Returns:
        Optional[Union[Dict, List, str, int, float, bool]]: Parsed data structure, or None on error
        - Dict/List: YAML/JSON objects
        - None: Empty content, parse error, or unsupported format
    
    Raises:
        No exceptions raised - all errors logged and return None
    
    Process Flow:
        1. Check for empty content → return None
        2. Auto-detect format if extension not provided
        3. Check if UI file (via path markers: "zUI", "/UI/")
        4. Route to format-specific parser (JSON or YAML)
        5. If UI file: Apply RBAC transformation via _transform_parsed_ui_for_walker()
        6. Return parsed data (transformed if UI, raw otherwise)
    
    UI File Detection:
        A file is considered a UI file if any of:
        - file_path contains "zUI" (e.g., "zUI.users.yaml")
        - file_path contains "/UI/" (e.g., "/path/to/UI/file.yaml")
        - file_extension contains "zUI" (e.g., ".zUI.yaml")
    
    RBAC Transformation (UI Files Only):
        For UI files, the function:
        1. Delegates to vafile.parse_ui_file() for RBAC extraction
        2. Calls _transform_parsed_ui_for_walker() to flatten structure
        3. Returns zWalker-compatible format with zRBAC merged
    
    Examples:
        >>> # Parse YAML file
        >>> data = parse_file_content("key: value", logger, ".yaml")
        >>> data
        {"key": "value"}
        
        >>> # Parse JSON file
        >>> data = parse_file_content('{"key": "value"}', logger, ".json")
        >>> data
        {"key": "value"}
        
        >>> # Auto-detect format (JSON)
        >>> data = parse_file_content('{"key": "value"}', logger)
        >>> data
        {"key": "value"}
        
        >>> # Parse UI file (with RBAC transformation)
        >>> raw = "Menu:\\n  Add: {zFunc: add}"
        >>> data = parse_file_content(raw, logger, ".yaml", file_path="zUI.users.yaml")
        >>> data  # Transformed for zWalker
        {"Menu": {"Add": {"zFunc": "add"}}}
        
        >>> # Empty content
        >>> data = parse_file_content("", logger)
        >>> data
        None
    
    External Usage (6 Files):
        1. zParser.py (line 150): parse_file_content(raw_content, self.logger, file_extension, session, file_path)
        2. zLoader.py (line 63): self.parse_file_content(zFile_raw, zFile_extension, session, file_path)
        3. authzRBAC.py: parse_file_content(raw_content, logger, ".yaml")
        4. auth_session_persistence.py: parse_file_content(raw_content, logger)
        5. func_args.py: parse_file_content(raw_content, logger, ".yaml")
        6. load_executor.py: parse_file_content(raw_content, logger, ext)
    
    Notes:
        - Empty content returns None (not an error - valid use case)
        - Unsupported extensions log error and return None
        - YAML is default format (zCLI convention)
        - Format detection is heuristic (first char inspection)
        - RBAC transformation only for UI files (not schema/config)
        - Session parameter reserved for future session-aware parsing
    
    Performance:
        - O(1) for format detection
        - O(n) for YAML/JSON parsing (n = content size)
        - O(m) for RBAC transformation (m = number of UI items)
    
    Thread Safety:
        Thread-safe (no shared state, logger passed as parameter)
    
    See Also:
        - parse_yaml: YAML-specific parsing
        - parse_json: JSON-specific parsing
        - detect_format: Auto-detection logic
        - _transform_parsed_ui_for_walker: RBAC transformation
        - vafile.parse_ui_file: UI file RBAC extraction
    """
    logger.framework.debug(f"{LOG_PREFIX_PARSE} {LOG_MSG_PARSE_CALLED}", file_extension)
    
    if not raw_content:
        logger.warning(LOG_MSG_EMPTY_CONTENT)
        return None

    # Auto-detect format if no extension provided
    if not file_extension:
        file_extension = detect_format(raw_content, logger)
        logger.debug(LOG_MSG_AUTO_DETECTED, file_extension)

    # Check if this is a UI file - check both extension and file_path
    is_ui_file: bool = False
    if file_path and (FILE_MARKER_ZUI in str(file_path) or FILE_MARKER_UI_PATH in str(file_path)):
        is_ui_file = True
    elif file_extension and (FILE_MARKER_ZUI in file_extension):
        is_ui_file = True
    
    # Check if this is a Server routing file (v1.5.4 Phase 2)
    is_server_file: bool = False
    if file_path and "zServer" in str(file_path):
        is_server_file = True
    elif file_extension and "zServer" in file_extension:
        is_server_file = True
    
    logger.framework.debug(f"{LOG_PREFIX_PARSE} {LOG_MSG_IS_UI_FILE}", is_ui_file, file_extension, file_path)
    
    # Route to appropriate parser
    if file_extension == FILE_EXT_JSON:
        return parse_json(raw_content, logger, file_extension)
    elif file_extension in [FILE_EXT_YAML, FILE_EXT_YML, FILE_EXT_ZOLO] or "yaml" in file_extension.lower():
        data = parse_yaml(raw_content, logger, file_extension)
        
        # Apply UI-specific parsing (RBAC extraction) if this is a UI file
        if is_ui_file and data:
            from .vafile import parse_ui_file
            logger.framework.debug(f"{LOG_PREFIX_RBAC} {LOG_MSG_DETECTED_UI}")
            logger.debug(f"{LOG_PREFIX_RBAC} {LOG_MSG_RAW_DATA_KEYS}", 
                        list(data.keys()) if isinstance(data, dict) else STR_N_A)
            
            parsed_ui = parse_ui_file(data, logger, file_path=file_path, session=session)
            
            # If UI parsing failed (returned None), stop immediately - this is a fatal error
            if parsed_ui is None:
                return None
            
            # Only log structure details if parsing succeeded
            logger.debug(f"{LOG_PREFIX_RBAC} {LOG_MSG_PARSED_UI_TYPE}", type(parsed_ui))
            logger.debug(f"{LOG_PREFIX_RBAC} {LOG_MSG_PARSED_UI_KEYS}", 
                        list(parsed_ui.keys()) if isinstance(parsed_ui, dict) else STR_N_A)
            
            # Transform parsed structure back to zWalker-compatible format
            transformed = _transform_parsed_ui_for_walker(parsed_ui, logger)
            if transformed is not None:
                return transformed
            
            # Fallback if transformation failed
            return parsed_ui.get(DICT_KEY_ZBLOCKS, data) if isinstance(parsed_ui, dict) else data
        
        # Apply Server-specific parsing (routing) if this is a Server file (v1.5.4 Phase 2)
        if is_server_file and data:
            from .vafile import parse_server_file
            logger.framework.debug("[zServer] Detected server routing file")
            parsed_server = parse_server_file(data, logger, file_path=file_path, session=session)
            return parsed_server
        
        return data
    else:
        logger.error(LOG_MSG_UNSUPPORTED_EXT, file_extension)
        return None


# ============================================================================
# FORMAT-SPECIFIC PARSERS
# ============================================================================

def parse_yaml(
    raw_content: Union[str, bytes],
    logger: Any,
    file_extension: Optional[str] = None
) -> Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]:
    """
    Parse YAML content into Python objects with robust error handling.
    
    Uses yaml.safe_load() for secure parsing (prevents code execution).
    Handles all YAML data types: scalars, sequences, mappings.
    
    File-Format Agnostic Processing:
        - .zolo files: Delegated to standalone zolo library (string-first + type hints)
        - .yaml files: Standard YAML parsing via PyYAML (native types)
    
    Args:
        raw_content: Raw YAML content (string or bytes)
        logger: Logger instance for diagnostic output
        file_extension: File extension (.zolo, .yaml) to determine which library to use
    
    Returns:
        Optional[Union[Dict, List, str, int, float, bool]]: Parsed YAML object, or None on error
        - Dict: YAML mapping (most common)
        - List: YAML sequence
        - Scalar: str, int, float, bool
        - None: Parse error
    
    Raises:
        No exceptions raised - all errors logged and return None
    
    Examples:
        >>> # .yaml file (standard YAML parsing)
        >>> parse_yaml("port: 8080", logger, ".yaml")
        {"port": 8080}  # int (YAML native)
        
        >>> # .zolo file (delegated to zolo library)
        >>> parse_yaml("port: 8080", logger, ".zolo")
        {"port": "8080"}  # str (zolo string-first)
        
        >>> # .zolo file with type hint (delegated to zolo library)
        >>> parse_yaml("port(int): 8080", logger, ".zolo")
        {"port": 8080}  # int (zolo type hint)
    
    Error Handling:
        - yaml.YAMLError: Malformed YAML syntax
        - Exception: Unexpected errors (broad catch for safety)
    
    Notes:
        - File-format agnostic: Uses appropriate library based on extension
        - .zolo files: Uses standalone zolo library (if available)
        - .yaml files: Uses PyYAML (yaml.safe_load)
        - Logs success with type/keys info
        - Returns None on any parse error
    
    Performance:
        O(n) where n = content size
    
    Thread Safety:
        Thread-safe (no shared state)
    
    See Also:
        - parse_file_content: Calls this for YAML/Zolo files
        - parse_json: JSON equivalent
        - zolo library: Standalone .zolo parser (external)
    """
    try:
        # File-format agnostic: Use appropriate library
        if file_extension == '.zolo' and ZOLO_AVAILABLE:
            # Use standalone zolo library for .zolo files
            parsed = zolo.loads(raw_content, file_extension=file_extension)
            logger.debug(LOG_MSG_YAML_PARSED,
                        type(parsed).__name__,
                        list(parsed.keys()) if isinstance(parsed, dict) else STR_N_A)
        else:
            # Use PyYAML for .yaml files (or .zolo if zolo not installed)
            parsed = yaml.safe_load(raw_content)
            logger.debug(LOG_MSG_YAML_PARSED,
                        type(parsed).__name__,
                        list(parsed.keys()) if isinstance(parsed, dict) else STR_N_A)
        
        return parsed
    except yaml.YAMLError as e:
        logger.error(LOG_MSG_YAML_PARSE_ERROR, e)
        return None
    except Exception as e:  # pylint: disable=broad-except
        logger.error(LOG_MSG_YAML_UNEXPECTED_ERROR, e)
        return None


def parse_json(
    raw_content: Union[str, bytes],
    logger: Any,
    file_extension: Optional[str] = None  # pylint: disable=unused-argument
) -> Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]:
    """
    Parse JSON content into Python objects with robust error handling.
    
    Uses json.loads() for standard JSON parsing.
    Handles all JSON data types: objects, arrays, strings, numbers, booleans, null.
    
    Args:
        raw_content: Raw JSON content (string or bytes)
        logger: Logger instance for diagnostic output
        file_extension: File extension (.json) - currently unused, for API consistency
    
    Returns:
        Optional[Union[Dict, List, str, int, float, bool]]: Parsed JSON object, or None on error
        - Dict: JSON object (most common)
        - List: JSON array
        - Scalar: str, int, float, bool, None
        - None: Parse error
    
    Raises:
        No exceptions raised - all errors logged and return None
    
    Examples:
        >>> parse_json('{"key": "value"}', logger)
        {"key": "value"}
        
        >>> parse_json('[1, 2, 3]', logger)
        [1, 2, 3]
        
        >>> parse_json('{"invalid": }', logger)  # Parse error
        None
    
    Error Handling:
        - json.JSONDecodeError: Malformed JSON syntax
        - Exception: Unexpected errors (broad catch for safety)
    
    Notes:
        - Standard JSON parsing (no format-specific processing)
        - Logs success with type/keys info
        - Returns None on any parse error
    
    Performance:
        O(n) where n = content size
    
    Thread Safety:
        Thread-safe (no shared state)
    
    See Also:
        - parse_file_content: Calls this for JSON files
        - parse_yaml: YAML/Zolo equivalent
    """
    try:
        # Use standard JSON parsing (no format-specific processing)
        parsed = json.loads(raw_content)
        logger.debug(LOG_MSG_JSON_PARSED,
                    type(parsed).__name__,
                    list(parsed.keys()) if isinstance(parsed, dict) else STR_N_A)
        
        return parsed
    except json.JSONDecodeError as e:
        logger.error(LOG_MSG_JSON_PARSE_ERROR, e)
        return None
    except Exception as e:  # pylint: disable=broad-except
        logger.error(LOG_MSG_JSON_UNEXPECTED_ERROR, e)
        return None


# ============================================================================
# FORMAT DETECTION
# ============================================================================

def detect_format(
    raw_content: Union[str, bytes],
    logger: Any
) -> str:
    """
    Auto-detect file format (JSON vs YAML) from content inspection.
    
    Heuristic-based detection using first character analysis.
    Falls back to YAML (zCLI default) if detection inconclusive.
    
    Detection Logic:
        1. JSON: Starts with { or [ (object/array)
        2. YAML: Contains : (mapping) or starts with - (sequence)
        3. Default: YAML (most common in zCLI)
    
    Args:
        raw_content: Raw file content (string or bytes)
        logger: Logger instance for diagnostic output
    
    Returns:
        str: Detected format (".json" or ".yaml")
        - ".json": JSON detected
        - ".yaml": YAML detected or default
    
    Examples:
        >>> detect_format('{"key": "value"}', logger)
        ".json"
        
        >>> detect_format('key: value', logger)
        ".yaml"
        
        >>> detect_format('- item1', logger)
        ".yaml"
        
        >>> detect_format('ambiguous content', logger)  # Default
        ".yaml"
    
    Notes:
        - Heuristic (not parsing - fast)
        - Trims whitespace before detection
        - YAML is preferred default (zCLI convention)
        - Detection is O(1) (first char inspection)
        - Returns extension format (not actual extension)
    
    Limitations:
        - Won't detect YAML scalars (no : or -)
        - Won't detect JSON primitives ("string", 123, true)
        - These cases default to YAML
    
    Performance:
        O(1) - constant time (first char inspection + one linear scan for :)
    
    Thread Safety:
        Thread-safe (no shared state)
    
    See Also:
        - parse_file_content: Calls this when extension not provided
    """
    if not raw_content:
        return DEFAULT_FORMAT

    # Trim whitespace for detection
    content = raw_content.strip()

    # JSON detection - starts with { or [
    if content.startswith(CONTENT_MARKER_JSON_START_BRACE) or \
       content.startswith(CONTENT_MARKER_JSON_START_BRACKET):
        logger.debug(LOG_MSG_DETECTED_JSON)
        return FILE_EXT_JSON

    # YAML detection - contains : or - patterns
    if CONTENT_MARKER_YAML_COLON in content or \
       content.startswith(CONTENT_MARKER_YAML_DASH):
        logger.debug(LOG_MSG_DETECTED_YAML)
        return FILE_EXT_YAML

    # Default to YAML (most common in zolo-zcli)
    logger.debug(LOG_MSG_DEFAULT_YAML)
    return DEFAULT_FORMAT


# ============================================================================
# CONVENIENCE METHODS
# ============================================================================

def parse_file_by_path(
    file_path: str,
    logger: Any
) -> Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]:
    """
    Load and parse file in one convenient call.
    
    Combines file reading + parsing into a single operation.
    Automatically extracts extension and passes to parse_file_content().
    
    Args:
        file_path: Path to file to load and parse
        logger: Logger instance for diagnostic output
    
    Returns:
        Optional[Union[Dict, List, str, int, float, bool]]: Parsed file content, or None on error
        - Same return type as parse_file_content()
        - None: File not found, read error, or parse error
    
    Raises:
        No exceptions raised - all errors logged and return None
    
    Process:
        1. Check file existence
        2. Extract extension from path
        3. Read file content (UTF-8 encoding)
        4. Delegate to parse_file_content()
    
    Examples:
        >>> parse_file_by_path("/path/to/config.yaml", logger)
        {"key": "value"}
        
        >>> parse_file_by_path("/path/to/data.json", logger)
        {"key": "value"}
        
        >>> parse_file_by_path("/nonexistent.yaml", logger)
        None
    
    Error Handling:
        - File not found: Logs error, returns None
        - Read error: Logs error, returns None
        - Parse error: Delegated to parse_file_content()
    
    Notes:
        - Uses UTF-8 encoding (zCLI standard)
        - Extension extracted via os.path.splitext()
        - All errors logged before returning None
    
    Performance:
        O(n) where n = file size (I/O bound)
    
    Thread Safety:
        Thread-safe (file I/O is atomic)
    
    See Also:
        - parse_file_content: Handles actual parsing
    """
    if not os.path.exists(file_path):
        logger.error(LOG_MSG_FILE_NOT_FOUND, file_path)
        return None

    # Determine extension
    _, ext = os.path.splitext(file_path)

    # Read file
    try:
        with open(file_path, 'r', encoding=DEFAULT_ENCODING) as f:
            raw_content = f.read()
    except Exception as e:  # pylint: disable=broad-except
        logger.error(LOG_MSG_FILE_READ_ERROR, file_path, e)
        return None

    # Parse content
    return parse_file_content(raw_content, logger, ext)


# ============================================================================
# EXPRESSION PARSING (for zExpr_eval compatibility)
# ============================================================================

def parse_json_expr(
    expr: str,
    logger: Any
) -> Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]]:
    """
    Parse JSON-like expression strings into Python objects.
    
    Specialized parser for expression evaluation (zExpr_eval compatibility).
    Handles single-quote to double-quote normalization for Python expressions.
    
    Args:
        expr: JSON-like expression string (may use single quotes)
        logger: Logger instance for diagnostic output
    
    Returns:
        Optional[Union[Dict, List, str, int, float, bool]]: Parsed expression, or None on error
        - Same types as JSON parsing
        - None: Parse error
    
    Raises:
        No exceptions raised - all errors logged and return None
    
    Examples:
        >>> parse_json_expr('{"key": "value"}', logger)
        {"key": "value"}
        
        >>> parse_json_expr("{'key': 'value'}", logger)  # Single quotes
        {"key": "value"}
        
        >>> parse_json_expr("[1, 2, 3]", logger)
        [1, 2, 3]
        
        >>> parse_json_expr("invalid", logger)
        None
    
    Normalization:
        - Replaces ' with " (Python → JSON format)
        - Allows Python-style expressions in zCLI
    
    Notes:
        - Used by zExpr_eval for expression evaluation
        - Logs debug message on parse error (not error level)
        - Returns None on any parse error (expected for non-JSON strings)
    
    Limitations:
        - Simple quote replacement (doesn't handle escaped quotes)
        - Not suitable for complex Python expressions
        - Best for simple JSON-like structures
    
    Performance:
        O(n) where n = expression length
    
    Thread Safety:
        Thread-safe (no shared state)
    
    See Also:
        - zExpr_eval: Main consumer of this function
    """
    try:
        # Handle single quotes (common in Python expressions)
        normalized = expr.replace(CHAR_SINGLE_QUOTE, CHAR_DOUBLE_QUOTE)
        return json.loads(normalized)
    except Exception as e:  # pylint: disable=broad-except
        logger.debug(LOG_MSG_JSON_EXPR_ERROR, e)
        return None
