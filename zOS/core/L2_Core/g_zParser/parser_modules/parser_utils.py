# zCLI/subsystems/zParser/parser_modules/parser_utils.py

"""
Utility functions for parsing operations within zParser subsystem.

This module provides essential parsing utilities used throughout the zCLI system:

1. **zExpr_eval**: JSON expression evaluator for converting string expressions
   to Python objects (dicts, lists, strings). Critical function used externally
   by navigation_linking.py for permission dictionary parsing.

2. **parse_dotted_path**: Dotted path parser for extracting table names and
   path components from reference expressions.

3. **handle_zRef**: YAML reference resolver for loading data from external
   YAML files using dot-notation paths.

4. **handle_zParser**: Placeholder function for future parser initialization
   (currently always returns True).

Architecture
------------
This module is part of Tier 0 (Foundation) - it has no internal dependencies
and provides core parsing utilities used by other zParser modules and external
subsystems.

Key Design Decisions:
    - **Signature Stability**: zExpr_eval signature is used externally and must
      remain stable. Any changes require verification with navigation_linking.py.
    - **Error Handling**: Functions return None on error for graceful degradation.
      Logging provides detailed error context.
    - **Display Integration**: Optional display parameter allows visual feedback
      in both Terminal and Bifrost modes.

External Usage (CRITICAL)
--------------------------
**zExpr_eval** is used by:
    - zCLI/subsystems/zNavigation/navigation_modules/navigation_linking.py (Line 545)
      Usage: required = zExpr_eval(perms_str, self.logger)
      Purpose: Parse permission dictionaries from zLink expressions
      
Signature must remain stable: zExpr_eval(expr, logger, display=None)

Usage Examples
--------------
**zExpr_eval** - Evaluate JSON expressions:
    >>> logger = get_logger()
    >>> zExpr_eval('{"role": "admin"}', logger)
    {'role': 'admin'}
    >>> zExpr_eval('["item1", "item2"]', logger)
    ['item1', 'item2']
    >>> zExpr_eval('"quoted string"', logger)
    'quoted string'

**parse_dotted_path** - Parse dotted paths:
    >>> parse_dotted_path("users.table.name")
    {'is_valid': True, 'table': 'name', 'parts': ['users', 'table', 'name']}
    >>> parse_dotted_path("invalid")
    {'is_valid': False, 'error': 'not enough path parts'}

**handle_zRef** - Load YAML data:
    >>> logger = get_logger()
    >>> handle_zRef('zRef("config.users.admin")', logger, base_path="/app")
    # Loads /app/config/users.yaml and returns data['admin']

**handle_zParser** - Placeholder:
    >>> handle_zParser("zUI.example.yaml")
    True

Layer Position
--------------
Layer 1, Position 5 (zParser - Tier 0 Foundation)
    - No internal dependencies
    - Used by: zParser facade, navigation_linking.py (external)
    - Provides: Core parsing utilities

Dependencies
------------
Internal:
    - None (Tier 0 - Foundation)

External:
    - zCLI core imports (os, json, yaml)
    - zCLI typing imports (Any, Dict, List, Optional, Union)

See Also
--------
- navigation_linking.py: External usage of zExpr_eval
- parser_path.py: Path resolution utilities
- parser_file.py: File parsing utilities
"""

from zOS import os, json, yaml, Any, Dict, List, Optional, Union

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Display Configuration
COLOR_PARSER: str = "PARSER"
INDENT_EXPR: int = 1
INDENT_REF: int = 6
INDENT_PARSER: int = 0
STYLE_SINGLE: str = "single"
STYLE_FULL: str = "full"

# Display Messages
DISPLAY_MSG_EXPR: str = "zExpr Evaluation"
DISPLAY_MSG_REF: str = "handle_zRef"
DISPLAY_MSG_PARSER: str = "zParser"

# Log Prefixes
LOG_PREFIX_RECEIVED: str = "[>>]"
LOG_PREFIX_DATA: str = "[Data]"
LOG_PREFIX_OK: str = "[OK]"
LOG_PREFIX_STR: str = "[Str]"
LOG_PREFIX_FAIL: str = "[FAIL]"
LOG_PREFIX_WARN: str = "[WARN]"
LOG_PREFIX_LOAD: str = "[Load]"

# Log Messages
LOG_MSG_RECEIVED_EXPR: str = "Received expr: %s"
LOG_MSG_DICT_LIST_FORMAT: str = "Detected dict/list format — using json.loads()"
LOG_MSG_PARSED_VALUE: str = "Parsed value: %s"
LOG_MSG_QUOTED_STRING: str = "Detected quoted string — stripping quotes"
LOG_MSG_UNSUPPORTED_FORMAT: str = "Unsupported format in zExpr_eval."
LOG_MSG_EVAL_FAILED: str = "zExpr_eval failed: %s"
LOG_MSG_INVALID_ZREF: str = "Invalid zRef format: %s"
LOG_MSG_ZREF_FILE_NOT_FOUND: str = "zRef file not found: %s"
LOG_MSG_ZREF_LOADED: str = "zRef: %s → %s"
LOG_MSG_ZREF_ERROR: str = "zRef error in %s: %s"

# Dict Keys (for parse_dotted_path return structure)
DICT_KEY_IS_VALID: str = "is_valid"
DICT_KEY_ERROR: str = "error"
DICT_KEY_TABLE: str = "table"
DICT_KEY_PARTS: str = "parts"

# Error Messages
ERROR_MSG_NOT_STRING: str = "not a string"
ERROR_MSG_NOT_ENOUGH_PARTS: str = "not enough path parts"
ERROR_MSG_UNSUPPORTED_FORMAT: str = "Unsupported format for zExpr_eval."
ERROR_MSG_ZREF_MIN_PARTS: str = "zRef requires at least one file and one key"

# File Operations
FILE_EXT_YAML: str = ".yaml"
FILE_MODE_READ: str = "r"
FILE_ENCODING_UTF8: str = "utf-8"

# String Literals
ZREF_PREFIX: str = "zRef("
ZREF_SUFFIX: str = ")"
CHAR_DOT: str = "."
QUOTE_SINGLE: str = "'"
QUOTE_DOUBLE: str = '"'
CHAR_OPEN_BRACE: str = "{"
CHAR_OPEN_BRACKET: str = "["

# Thresholds
MIN_PATH_PARTS: int = 2


# ============================================================================
# FUNCTIONS
# ============================================================================

def zExpr_eval(
    expr: str,
    logger: Any,
    display: Optional[Any] = None
) -> Union[Dict, List, str, None]:
    """
    Evaluate JSON expressions and convert to Python objects.
    
    ⚠️ CRITICAL: This function is used externally by navigation_linking.py
    for permission dictionary parsing. Signature must remain stable.
    
    Converts string representations of JSON objects to their Python equivalents:
    - Dict/List: Uses json.loads() with quote normalization
    - Quoted strings: Strips surrounding double quotes
    - Other formats: Returns None (unsupported)
    
    Quote Replacement Behavior:
        Single quotes are automatically replaced with double quotes before
        JSON parsing, allowing Python-style dict syntax: {'key': 'value'}
    
    Supported Formats:
        - Dictionaries: '{"key": "value"}' or "{'key': 'value'}"
        - Lists: '["item1", "item2"]' or "['item1', 'item2']"
        - Quoted strings: '"some string"'
    
    Unsupported Formats:
        - Bare strings (without quotes)
        - Numbers, booleans, null (not standalone)
        - Complex nested structures with mixed quotes
    
    Args:
        expr: String expression to evaluate (JSON format expected)
        logger: Logger instance for diagnostic output
        display: Optional display adapter for visual feedback
                 (Terminal/Bifrost mode-agnostic)
    
    Returns:
        Union[Dict, List, str, None]:
            - Dict: If expr is a valid dict string
            - List: If expr is a valid list string
            - str: If expr is a quoted string
            - None: If parsing fails or format is unsupported
    
    Raises:
        None: All exceptions are caught and logged. Returns None on error.
    
    Examples:
        >>> logger = get_logger()
        
        # Dict evaluation
        >>> zExpr_eval('{"role": "admin"}', logger)
        {'role': 'admin'}
        
        # Dict with single quotes (Python style)
        >>> zExpr_eval("{'role': 'admin'}", logger)
        {'role': 'admin'}
        
        # List evaluation
        >>> zExpr_eval('["item1", "item2"]', logger)
        ['item1', 'item2']
        
        # Quoted string
        >>> zExpr_eval('"Hello World"', logger)
        'Hello World'
        
        # Unsupported format
        >>> zExpr_eval('bare_string', logger)
        None
    
    External Usage:
        navigation_linking.py (Line 545):
            required = zExpr_eval(perms_str, self.logger)
        Purpose: Parse permission dicts from zLink expressions
    
    Notes:
        - Returns None on error for graceful degradation
        - Logging provides detailed diagnostic context
        - Display integration allows visual feedback
        - Quote replacement enables Python-style dict syntax
        - Signature stability is CRITICAL for external usage
    
    See Also:
        - navigation_linking.py: External usage for permission parsing
        - parse_dotted_path: Related path parsing utility
    """
    if display:
        display.zDeclare(DISPLAY_MSG_EXPR, color=COLOR_PARSER, indent=INDENT_EXPR, style=STYLE_SINGLE)

    logger.info(f"{LOG_PREFIX_RECEIVED} {LOG_MSG_RECEIVED_EXPR}", expr)
    expr = expr.strip()

    try:
        # Check for dict/list format (starts with { or [)
        if expr.startswith(CHAR_OPEN_BRACE) or expr.startswith(CHAR_OPEN_BRACKET):
            logger.info(f"{LOG_PREFIX_DATA} {LOG_MSG_DICT_LIST_FORMAT}")
            # Normalize quotes: replace single quotes with double quotes for JSON compatibility
            converted = json.loads(expr.replace(QUOTE_SINGLE, QUOTE_DOUBLE))
            logger.info(f"{LOG_PREFIX_OK} {LOG_MSG_PARSED_VALUE}", converted)
            return converted

        # Check for quoted string format
        if expr.startswith(QUOTE_DOUBLE) and expr.endswith(QUOTE_DOUBLE):
            logger.info(f"{LOG_PREFIX_STR} {LOG_MSG_QUOTED_STRING}")
            # Strip surrounding quotes
            return expr[1:-1]

        # Unsupported format
        logger.error(f"{LOG_PREFIX_FAIL} {LOG_MSG_UNSUPPORTED_FORMAT}")
        raise ValueError(ERROR_MSG_UNSUPPORTED_FORMAT)

    except (json.JSONDecodeError, ValueError) as e:
        # Specific exceptions for known error cases
        logger.error(f"{LOG_PREFIX_FAIL} {LOG_MSG_EVAL_FAILED}", e)
        return None
    except Exception as e:  # pylint: disable=broad-except
        # Catch-all for unexpected errors (should be rare)
        logger.error(f"{LOG_PREFIX_FAIL} {LOG_MSG_EVAL_FAILED}", e)
        return None


def parse_dotted_path(ref_expr: Any) -> Dict[str, Any]:
    """
    Parse a dotted path string into table name, parts list, and validity.
    
    Extracts components from dot-separated path expressions, commonly used
    for referencing database tables or nested data structures.
    
    Return Structure:
        Success: {
            'is_valid': True,
            'table': <last part>,
            'parts': [<all parts>]
        }
        
        Failure: {
            'is_valid': False,
            'error': <error description>
        }
    
    Args:
        ref_expr: Path expression to parse (expected to be string, but accepts Any
                  for graceful error handling)
    
    Returns:
        Dict[str, Any]: Parsed path dictionary with structure documented above
    
    Examples:
        >>> parse_dotted_path("users.table.name")
        {'is_valid': True, 'table': 'name', 'parts': ['users', 'table', 'name']}
        
        >>> parse_dotted_path("database.users")
        {'is_valid': True, 'table': 'users', 'parts': ['database', 'users']}
        
        >>> parse_dotted_path("invalid")
        {'is_valid': False, 'error': 'not enough path parts'}
        
        >>> parse_dotted_path(123)  # Non-string input
        {'is_valid': False, 'error': 'not a string'}
    
    Notes:
        - Requires at least 2 parts (MIN_PATH_PARTS)
        - Last part is designated as 'table'
        - Whitespace is automatically trimmed
        - Returns error dict for invalid inputs
    
    See Also:
        - handle_zRef: Uses similar path parsing logic
    """
    # Validate input type
    if not isinstance(ref_expr, str):
        return {DICT_KEY_IS_VALID: False, DICT_KEY_ERROR: ERROR_MSG_NOT_STRING}

    # Normalize and split path
    ref_expr = ref_expr.strip()
    parts = ref_expr.split(CHAR_DOT)

    # Validate minimum parts requirement
    if len(parts) < MIN_PATH_PARTS:
        return {DICT_KEY_IS_VALID: False, DICT_KEY_ERROR: ERROR_MSG_NOT_ENOUGH_PARTS}

    # Return success structure
    return {
        DICT_KEY_IS_VALID: True,
        DICT_KEY_TABLE: parts[-1],  # Last part is table name
        DICT_KEY_PARTS: parts,
    }


def handle_zRef(
    ref_expr: str,
    logger: Any,
    base_path: Optional[str] = None,
    display: Optional[Any] = None
) -> Any:
    """
    Handle zRef expressions to load YAML data from external files.
    
    Resolves zRef() expressions by:
    1. Parsing the dotted path inside zRef()
    2. Resolving file path (all parts except last → file.yaml)
    3. Loading YAML file using safe_load
    4. Extracting value using final key
    
    Path Resolution Logic:
        zRef("config.users.admin") with base_path="/app"
        → Loads: /app/config/users.yaml
        → Returns: data['admin']
    
    Args:
        ref_expr: zRef expression string (format: 'zRef("path.to.key")')
        logger: Logger instance for diagnostic output
        base_path: Optional base directory for resolving relative paths
                   (defaults to current working directory)
        display: Optional display adapter for visual feedback
                 (Terminal/Bifrost mode-agnostic)
    
    Returns:
        Any: Value extracted from YAML file at specified key
             Returns None if file not found, invalid format, or parsing error
    
    Raises:
        None: All exceptions are caught and logged. Returns None on error.
    
    Examples:
        >>> logger = get_logger()
        
        # Load admin config
        >>> handle_zRef('zRef("config.users.admin")', logger, base_path="/app")
        # Loads /app/config/users.yaml → returns data['admin']
        
        # Load with single quotes
        >>> handle_zRef("zRef('settings.database.host')", logger)
        # Loads {cwd}/settings/database.yaml → returns data['host']
        
        # Invalid format
        >>> handle_zRef("invalid_format", logger)
        None
    
    Error Conditions:
        - Invalid zRef format (missing prefix/suffix)
        - Path with less than 2 parts
        - YAML file not found
        - YAML parsing error
        - Key not found in loaded data
    
    Notes:
        - Uses yaml.safe_load for security (no code execution)
        - Automatically handles single and double quotes
        - Returns None on any error for graceful degradation
        - Logging provides detailed error context
        - Display integration allows visual feedback
    
    See Also:
        - parse_dotted_path: Related path parsing utility
    """
    if display:
        display.zDeclare(DISPLAY_MSG_REF, color=COLOR_PARSER, indent=INDENT_REF, style=STYLE_SINGLE)

    # Validate zRef format
    if not (isinstance(ref_expr, str) and ref_expr.startswith(ZREF_PREFIX) and ref_expr.endswith(ZREF_SUFFIX)):
        logger.warning(f"{LOG_PREFIX_WARN} {LOG_MSG_INVALID_ZREF}", ref_expr)
        return None

    try:
        # Extract path from zRef("path") or zRef('path')
        raw_path = ref_expr[len(ZREF_PREFIX):-1].strip().strip(QUOTE_SINGLE + QUOTE_DOUBLE)
        parts = raw_path.split(CHAR_DOT)
        
        # Validate minimum parts requirement
        if len(parts) < MIN_PATH_PARTS:
            raise ValueError(ERROR_MSG_ZREF_MIN_PARTS)

        # Split into file path components and final key
        # Example: "config.users.admin" → file_parts=['config', 'users'], final_key='admin'
        *file_parts, final_key = parts
        yaml_path = os.path.join(base_path or os.getcwd(), *file_parts) + FILE_EXT_YAML

        # Verify file exists
        if not os.path.exists(yaml_path):
            logger.error(f"{LOG_PREFIX_FAIL} {LOG_MSG_ZREF_FILE_NOT_FOUND}", yaml_path)
            return None

        # Load and parse YAML file
        with open(yaml_path, FILE_MODE_READ, encoding=FILE_ENCODING_UTF8) as f:
            data = yaml.safe_load(f)

        logger.info(f"{LOG_PREFIX_LOAD} {LOG_MSG_ZREF_LOADED}", yaml_path, final_key)
        return data.get(final_key)

    except (ValueError, FileNotFoundError, yaml.YAMLError, OSError) as e:
        # Handle specific expected exceptions
        logger.error(f"{LOG_PREFIX_FAIL} {LOG_MSG_ZREF_ERROR}", ref_expr, e)
        return None


def handle_zParser(zFile_raw: str, display: Optional[Any] = None) -> bool:  # pylint: disable=unused-argument
    """
    Placeholder function for future parser initialization.
    
    Currently always returns True to maintain compatibility with existing code
    that checks this function's return value. Will be expanded in future versions
    to handle actual parser initialization logic.
    
    Purpose:
        - Reserved for future parser setup/initialization
        - Maintains API compatibility
        - Provides extension point for parser configuration
    
    Args:
        zFile_raw: Raw file path or identifier (currently unused)
        display: Optional display adapter for visual feedback
                 (Terminal/Bifrost mode-agnostic)
    
    Returns:
        bool: Always True (placeholder behavior)
    
    Examples:
        >>> handle_zParser("zUI.example.yaml")
        True
        
        >>> from zOS import get_display
        >>> display = get_display()
        >>> handle_zParser("config.yaml", display=display)
        True
    
    Notes:
        - Currently a no-op (always returns True)
        - Reserved for future parser initialization logic
        - Display integration allows visual feedback
        - Parameter marked with pylint disable (intentional)
    
    Future Enhancements:
        - Parser configuration validation
        - File format detection
        - Parser state initialization
        - Error condition detection
    """
    if display:
        display.zDeclare(DISPLAY_MSG_PARSER, color=COLOR_PARSER, indent=INDENT_PARSER, style=STYLE_FULL)
    return True
