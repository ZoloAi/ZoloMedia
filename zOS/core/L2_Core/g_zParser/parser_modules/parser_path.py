# zCLI/subsystems/zParser/parser_modules/parser_path.py

"""
zPath resolution and file discovery functionality within zParser subsystem.

This module provides comprehensive path resolution utilities for the zCLI system:

1. **zPath_decoder**: Main path decoder that resolves dotted paths to file paths
   with support for workspace-relative (@), absolute (~), and relative paths.
   CRITICAL function used externally by zLoader and zShell.

2. **identify_zFile**: File type identifier and extension resolver for zVaFiles
   (zUI, zSchema, zConfig) and regular files. CRITICAL function used externally
   by zLoader and zShell.

3. **resolve_zmachine_path**: Resolves zMachine.* path references to OS-specific
   paths in the user data directory.

4. **resolve_symbol_path**: Path resolution helper that handles symbol prefixes
   (@, ~, or no symbol).

5. **is_zvafile_type**: Detection utility for zVaFile prefixes (zUI., zSchema., zConfig.).

6. **Private helpers**: _handle_ui_mode_path, _extract_filename_from_parts,
   _extract_non_zvafile_filename, _find_filename_start.

Architecture
------------
This module is part of Tier 0 (Foundation) - it has no internal dependencies
and provides core path resolution utilities used by other zParser modules and
external subsystems.

Key Design Decisions:
    - **Signature Stability**: zPath_decoder and identify_zFile signatures are
      used externally and must remain stable. Any changes require verification
      with zLoader.py and zShell/load_executor.py.
    - **Path Symbols**: Three resolution modes supported:
        * @ (at): Workspace-relative path
        * ~ (tilde): Absolute path from root
        * (none): Relative path from workspace
    - **zVaFile Detection**: Auto-detects file extensions (.zolo, .json, .yaml, .yml)
      for zUI, zSchema, and zConfig files.
    - **zMachine Paths**: Special syntax for referencing user data directory:
        * zMachine.* → Direct reference
        * ~.zMachine.* → Alternative reference

External Usage (CRITICAL)
--------------------------
**zPath_decoder** is used by:
    - zCLI/subsystems/zLoader/zLoader.py (Week 6.9 - CRITICAL)
      Purpose: Resolve file paths before loading UI/Schema/Config files
    - zCLI/subsystems/zShell/zShell_modules/executor_commands/load_executor.py
      Purpose: Shell command path resolution

**identify_zFile** is used by:
    - zCLI/subsystems/zLoader/zLoader.py (Week 6.9 - CRITICAL)
      Purpose: Identify file type and find actual file with extension
    - zCLI/subsystems/zShell/zShell_modules/executor_commands/load_executor.py
      Purpose: Shell command file identification

Signatures must remain stable:
    - zPath_decoder(zSession, logger, zPath=None, zType=None, display=None)
    - identify_zFile(filename, full_zFilePath, logger, display=None)

Usage Examples
--------------
**zPath_decoder** - Resolve dotted paths:
    >>> zSession = {'zSpace': '/app'}
    >>> logger = get_logger()
    >>> zPath_decoder(zSession, logger, zPath='@.config.zUI.users.main')
    ('/app/config/zUI.users', 'zUI.users')

    >>> zPath_decoder(zSession, logger, zPath='~.etc.config.zSchema.db.users')
    ('/etc/config/zSchema.db', 'zSchema.db')

**identify_zFile** - Identify and find files:
    >>> identify_zFile('zUI.users', '/app/config/zUI.users', logger)
    ('/app/config/zUI.users.yaml', '.yaml')

    >>> identify_zFile('script.py', '/app/scripts/script.py', logger)
    ('/app/scripts/script.py', '.py')

**resolve_zmachine_path** - Resolve zMachine paths:
    >>> resolve_zmachine_path('zMachine.Data.cache', logger)
    '/Users/user/Library/Application Support/zolo-zcli/Data/cache'

    >>> resolve_zmachine_path('~.zMachine.zSchema.auth', logger)
    '/Users/user/Library/Application Support/zolo-zcli/zSchema.auth'

**is_zvafile_type** - Check zVaFile status:
    >>> is_zvafile_type('zUI.users')
    True
    >>> is_zvafile_type(['config', 'zSchema.db', 'users'])
    True
    >>> is_zvafile_type('script.py')
    False

Path Symbol Conventions
-----------------------
@ (At Symbol) - Workspace-Relative:
    Format: @.path.to.file
    Resolves: Relative to zSession['zSpace'] or os.getcwd()
    Example: @.config.zUI.users → {workspace}/config/zUI.users

~ (Tilde Symbol) - Absolute Path:
    Format: ~.path.to.file
    Resolves: Absolute path from root
    Example: ~.etc.config.zUI.users → /etc/config/zUI.users

(No Symbol) - Relative to Workspace:
    Format: path.to.file
    Resolves: Relative to zSession['zSpace'] or os.getcwd()
    Example: config.zUI.users → {workspace}/config/zUI.users

zMachine Path Resolution
-------------------------
zMachine.* paths resolve to the user data directory (typically
~/Library/Application Support/zolo-zcli on macOS).

Format Options:
    - zMachine.{subpath}
    - ~.zMachine.{subpath}

Dot notation is converted to path separators:
    zMachine.Data.cache → {user_data_dir}/Data/cache
    ~.zMachine.zSchema.auth → {user_data_dir}/zSchema/auth

zVaFile Detection Logic
-----------------------
zVaFiles are identified by their prefix:
    - zUI.* → UI definition files
    - zSchema.* → Schema definition files
    - zConfig.* → Configuration files

Extension auto-detection tries in order:
    1. .json
    2. .yaml
    3. .yml

If no file found, raises FileNotFoundError.

Layer Position
--------------
Layer 1, Position 5 (zParser - Tier 0 Foundation)
    - No internal dependencies
    - Used by: zParser facade, zLoader (external), zShell (external)
    - Provides: Core path resolution and file identification

Dependencies
------------
Internal:
    - None (Tier 0 - Foundation)

External:
    - zCLI core imports (os)
    - zCLI typing imports (Any, Dict, List, Optional, Tuple, Union)
    - pathlib.Path (for zMachine path validation)
    - zConfig.zConfigPaths (for user data directory resolution)
    - zExceptions.zMachinePathError (for zMachine path errors)

See Also
--------
- zLoader.py: External usage of zPath_decoder and identify_zFile
- zShell/load_executor.py: External usage of zPath_decoder and identify_zFile
- parser_utils.py: Related parsing utilities
- parser_file.py: File parsing utilities
"""

from pathlib import Path
from zOS import os, Any, Dict, List, Optional, Tuple, Union
from zSys.errors import zMachinePathError

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Display Configuration
COLOR_SUBLOADER: str = "SUBLOADER"
INDENT_PATH: int = 2
STYLE_SINGLE: str = "single"

# Display Messages
DISPLAY_MSG_PATH_DECODER: str = "zPath decoder"
DISPLAY_MSG_FILE_TYPE_TEMPLATE: str = "Type: {}|{}"

# Session Keys (should use zConfig constants in future)
SESSION_KEY_ZSPACE: str = "zSpace"
SESSION_KEY_ZVAFOLDER: str = "zVaFolder"
SESSION_KEY_ZVAFILE: str = "zVaFile"

# Path Symbols
SYMBOL_AT: str = "@"
SYMBOL_TILDE: str = "~"

# Path Separators
PATH_SEP_DOT: str = "."
PATH_SEP_SLASH: str = "/"

# zMachine Prefixes
ZMACHINE_PREFIX_SHORT: str = "zMachine."
ZMACHINE_PREFIX_LONG: str = "~.zMachine."

# zVaFile Prefixes
ZVAFILE_PREFIX_UI: str = "zUI."
ZVAFILE_PREFIX_SCHEMA: str = "zSchema."
ZVAFILE_PREFIX_CONFIG: str = "zConfig."
ZVAFILE_PREFIXES: Tuple[str, str, str] = (
    ZVAFILE_PREFIX_UI,
    ZVAFILE_PREFIX_SCHEMA,
    ZVAFILE_PREFIX_CONFIG
)

# File Type Names
FILE_TYPE_ZUI: str = "zUI"
FILE_TYPE_ZSCHEMA: str = "zSchema"
FILE_TYPE_ZCONFIG: str = "zConfig"
FILE_TYPE_ZVAFILE: str = "zVaFile"
FILE_TYPE_ZOTHER: str = "zOther"

# zVaFile Extensions (priority order for auto-detection)
ZVAFILE_EXT_JSON: str = ".json"
ZVAFILE_EXT_YAML: str = ".yaml"
ZVAFILE_EXT_YML: str = ".yml"
ZVAFILE_EXT_ZOLO: str = ".zolo"
ZVAFILE_EXTENSIONS: List[str] = [
    ZVAFILE_EXT_ZOLO,    # Try .zolo first (new DRY format)
    ZVAFILE_EXT_JSON,
    ZVAFILE_EXT_YAML,
    ZVAFILE_EXT_YML
]

# Common File Extensions (for non-zVaFile detection)
FILE_EXT_PY: str = ".py"
FILE_EXT_JS: str = ".js"
FILE_EXT_SH: str = ".sh"
FILE_EXT_MD: str = ".md"
FILE_EXT_TXT: str = ".txt"
FILE_EXT_JSON: str = ".json"
FILE_EXT_YAML: str = ".yaml"
FILE_EXT_YML: str = ".yml"
FILE_EXT_XML: str = ".xml"
FILE_EXT_HTML: str = ".html"
FILE_EXT_CSS: str = ".css"
FILE_EXTENSIONS: List[str] = [
    FILE_EXT_PY,
    FILE_EXT_JS,
    FILE_EXT_SH,
    FILE_EXT_MD,
    FILE_EXT_TXT,
    FILE_EXT_JSON,
    FILE_EXT_YAML,
    FILE_EXT_YML,
    FILE_EXT_XML,
    FILE_EXT_HTML,
    FILE_EXT_CSS
]

# zMachine Keywords (for file validation)
ZMACHINE_KEYWORD_ZSCHEMA: str = "zSchema"
ZMACHINE_KEYWORD_ZUI: str = "zUI"
ZMACHINE_KEYWORD_ZCONFIG: str = "zConfig"
ZMACHINE_KEYWORDS: List[str] = [
    ZMACHINE_KEYWORD_ZSCHEMA,
    ZMACHINE_KEYWORD_ZUI,
    ZMACHINE_KEYWORD_ZCONFIG
]

# Log Messages
LOG_MSG_ZMACHINE_PATH: str = "[zMachine Path] %s => %s"
LOG_MSG_ZSPACE: str = "\nzSpace: %s"
LOG_MSG_ZRELPATH: str = "\nzRelPath: %s"
LOG_MSG_ZFILENAME: str = "\nzFileName: %s"
LOG_MSG_OS_RELPATH: str = "\nos_RelPath: %s"
LOG_MSG_ZVAFOLDER_PATH: str = "\nzVaFolder path: %s"
LOG_MSG_ZBLOCK: str = "\nzBlock: %s"
LOG_MSG_ZPATH_2_ZFILE: str = "\nzPath_2_zFile: %s"
LOG_MSG_ZFILENAME_SHORT: str = "zFileName: %s"
LOG_MSG_ZRELPATH_PARTS: str = "zRelPath_parts: %s"
LOG_MSG_NO_ZBLOCK: str = "\nNo zBlock (not a zVaFile)"
LOG_MSG_PARTS: str = "\nparts: %s"
LOG_MSG_IS_ZVAFILE: str = "is_zvafile: %s"
LOG_MSG_SYMBOL: str = "symbol: %s"
LOG_MSG_ZVAFILE_FULLPATH: str = "zVaFile path + zVaFile:\n%s"
LOG_MSG_SYMBOL_AT: str = "↪ '@' → workspace-relative path"
LOG_MSG_SYMBOL_TILDE: str = "↪ '~' → absolute path"
LOG_MSG_SYMBOL_NONE: str = "↪ no symbol → treat whole as relative"
LOG_MSG_NO_WORKSPACE: str = "⚠️ '@' path requested but no workspace configured in zSession"
LOG_MSG_NO_WORKSPACE_HELP: str = "   Use 'session set zSpace <path>' to configure workspace"
LOG_MSG_NO_WORKSPACE_FALLBACK: str = "   Falling back to current working directory: %s"
LOG_MSG_FILE_TYPE: str = "File Type: %s"
LOG_MSG_FILE_TYPE_UNKNOWN: str = "File Type: zVaFile (unknown subtype)"
LOG_MSG_FILE_TYPE_OTHER: str = "File Type: zOther (extension provided)"
LOG_MSG_ZFILE_EXTENSION: str = "zFile extension: %s"

# Error Messages
ERROR_MSG_NO_ZVAFILE_FOUND: str = "No zVaFile found for base path: {} (tried .zolo/.json/.yaml/.yml)"
ERROR_MSG_FILE_NOT_FOUND: str = "File not found: {}"

# Thresholds and Limits
MIN_PARTS_FOR_ZVAFILE: int = 2
FILENAME_PARTS_FOR_SHORT: int = 2
FALLBACK_FILENAME_START: int = 2


# ============================================================================
# FUNCTIONS
# ============================================================================

def resolve_zmachine_path(
    data_path: Any,
    logger: Any,
    config_paths: Optional[Any] = None
) -> Union[str, Any]:
    """
    Resolve zMachine.* or ~.zMachine.* path references to OS-specific paths.
    
    Converts zMachine path syntax to actual file system paths in the user data
    directory (typically ~/Library/Application Support/zolo-zcli on macOS).
    
    Supported formats:
        - zMachine.{subpath}
        - ~.zMachine.{subpath}
    
    Dot notation is converted to path separators:
        zMachine.Data.cache → {user_data_dir}/Data/cache
        ~.zMachine.zSchema.auth → {user_data_dir}/zSchema/auth
    
    For paths containing zVaFile keywords (zSchema, zUI, zConfig), validates
    that the file exists (adding .yaml extension).
    
    Args:
        data_path: Path string to resolve, or non-string to return as-is
        logger: Logger instance for diagnostic output
        config_paths: Optional zConfigPaths instance (created if not provided)
    
    Returns:
        Union[str, Any]:
            - str: Resolved OS-specific path if zMachine path
            - Any: Original data_path if not a zMachine path or not a string
    
    Raises:
        zMachinePathError: If file path cannot be resolved or file not found
                           (only for paths containing zVaFile keywords)
    
    Examples:
        >>> logger = get_logger()
        
        # Simple zMachine path
        >>> resolve_zmachine_path('zMachine.Data.cache', logger)
        '/Users/user/Library/Application Support/zolo-zcli/Data/cache'
        
        # Alternative format
        >>> resolve_zmachine_path('~.zMachine.zSchema.auth', logger)
        '/Users/user/Library/Application Support/zolo-zcli/zSchema/auth'
        
        # Non-zMachine path (returned as-is)
        >>> resolve_zmachine_path('regular/path', logger)
        'regular/path'
        
        # Non-string (returned as-is)
        >>> resolve_zmachine_path(123, logger)
        123
    
    Notes:
        - Non-string inputs are returned without modification
        - Non-zMachine paths are returned without modification
        - File existence is only validated for zVaFile paths
        - Uses zConfigPaths to get user data directory
        - Raises zMachinePathError for missing zVaFiles
    
    See Also:
        - zPath_decoder: Related path resolution utility
        - is_zvafile_type: zVaFile detection
    """
    # Return non-string inputs as-is
    if not isinstance(data_path, str):
        return data_path
    
    # Check for both zMachine formats
    if data_path.startswith(ZMACHINE_PREFIX_SHORT):
        prefix = ZMACHINE_PREFIX_SHORT
    elif data_path.startswith(ZMACHINE_PREFIX_LONG):
        prefix = ZMACHINE_PREFIX_LONG
    else:
        # Not a zMachine path, return as-is
        return data_path

    # Get config paths (import inline to avoid circular dependency)
    if not config_paths:
        from zOS.L1_Foundation.a_zConfig.zConfig_modules import zConfigPaths
        config_paths = zConfigPaths()

    # Extract the subpath after zMachine prefix
    # Example: "zMachine.zDataTests" => "zDataTests"
    # Example: "~.zMachine.Data/cache.csv" => "Data/cache.csv"
    subpath = data_path[len(prefix):]
    
    # Convert dot notation to path separators
    # Example: "zDataTests" stays as is, "tests.zData_tests" => "tests/zData_tests"
    subpath = subpath.replace(PATH_SEP_DOT, PATH_SEP_SLASH)

    # Build full path using user_data_dir as base
    base_dir = config_paths.user_data_dir
    full_path = base_dir / subpath

    logger.debug(LOG_MSG_ZMACHINE_PATH, data_path, full_path)
    
    # Validate if this looks like a file reference (contains zVaFile keywords)
    if any(keyword in data_path for keyword in ZMACHINE_KEYWORDS):
        # Check if file exists (add .yaml extension for zVaFiles)
        test_path = Path(str(full_path) + ZVAFILE_EXT_YAML)
        if not test_path.exists():
            raise zMachinePathError(
                zpath=data_path,
                resolved_path=str(test_path),
                context_type="file"
            )

    return str(full_path)


def is_zvafile_type(filename_or_parts: Union[str, List[str]]) -> bool:
    """
    Check if a filename indicates a zVaFile (zUI., zSchema., zConfig.).
    
    Detects zVaFile prefixes in either a filename string or a list of path parts.
    zVaFiles are special declarative files in zCLI with auto-detected extensions.
    
    Args:
        filename_or_parts: Filename string or list of path parts to check
    
    Returns:
        bool: True if filename/parts indicate a zVaFile, False otherwise
    
    Examples:
        >>> is_zvafile_type('zUI.users')
        True
        
        >>> is_zvafile_type('zSchema.database')
        True
        
        >>> is_zvafile_type('zConfig.settings')
        True
        
        >>> is_zvafile_type('script.py')
        False
        
        >>> is_zvafile_type(['config', 'zUI.users', 'main'])
        True
        
        >>> is_zvafile_type(['scripts', 'utils.py'])
        False
    
    Notes:
        - Checks for prefixes: zUI., zSchema., zConfig.
        - For lists, returns True if ANY part has a zVaFile prefix
        - Case-sensitive matching
        - Period (.) after prefix is required
    
    See Also:
        - identify_zFile: File type identification using this function
        - zPath_decoder: Path resolution using this function
    """
    if isinstance(filename_or_parts, list):
        # Check if any part starts with zVaFile prefixes
        for part in filename_or_parts:
            if part.startswith(ZVAFILE_PREFIXES):
                return True
        return False

    # Check filename string
    return filename_or_parts.startswith(ZVAFILE_PREFIXES)


def _handle_ui_mode_path(
    zSession: Dict[str, Any],
    zSpace: str,
    logger: Any
) -> Tuple[str, str]:
    """
    Handle UI mode path resolution from session state.
    
    Internal helper for zPath_decoder when no zPath is provided but zType is "zUI".
    Extracts path information from zSession and constructs base path and filename.
    
    Args:
        zSession: Session dictionary containing path information
        zSpace: Workspace directory path
        logger: Logger instance for diagnostic output
    
    Returns:
        Tuple[str, str]: (base_path, filename)
            - base_path: Directory path for the zVaFile
            - filename: Filename of the zVaFile
    
    Notes:
        - Private helper function (not for external use)
        - Extracts zVaFolder and zVaFile from zSession
        - Converts dot notation to OS path separators
        - Logs all intermediate steps for debugging
    
    See Also:
        - zPath_decoder: Main function using this helper
    """
    zVaFolder = zSession.get(SESSION_KEY_ZVAFOLDER) or ""
    zRelPath = (
        zVaFolder.lstrip(PATH_SEP_DOT).split(PATH_SEP_DOT)
        if PATH_SEP_DOT in zVaFolder
        else [zVaFolder]
    )
    zFileName = zSession[SESSION_KEY_ZVAFILE]
    logger.framework.debug(LOG_MSG_ZSPACE, zSpace)
    logger.framework.debug(LOG_MSG_ZRELPATH, zRelPath)
    logger.framework.debug(LOG_MSG_ZFILENAME, zFileName)

    os_RelPath = os.path.join(*zRelPath[1:]) if len(zRelPath) > 1 else ""
    logger.framework.debug(LOG_MSG_OS_RELPATH, os_RelPath)

    zVaFolder_basepath = os.path.join(zSpace, os_RelPath)
    logger.framework.debug(LOG_MSG_ZVAFOLDER_PATH, zVaFolder_basepath)
    return zVaFolder_basepath, zFileName


def _extract_filename_from_parts(
    zPath_parts: List[str],
    is_zvafile: bool,
    logger: Any
) -> Tuple[str, List[str]]:
    """
    Extract filename and path parts from zPath components.
    
    Internal helper that handles both zVaFile and non-zVaFile extraction logic.
    For zVaFiles, extracts block (last part) and filename (last 2 parts before block).
    For non-zVaFiles, delegates to _extract_non_zvafile_filename.
    
    Args:
        zPath_parts: List of dot-separated path components
        is_zvafile: Whether this is a zVaFile path
        logger: Logger instance for diagnostic output
    
    Returns:
        Tuple[str, List[str]]: (filename, relative_path_parts)
            - filename: Extracted filename (may include dots)
            - relative_path_parts: Remaining path components
    
    Notes:
        - Private helper function (not for external use)
        - zVaFile paths have format: path.parts.zUI.filename.block
        - Non-zVaFile paths include extension in filename
        - Logs extraction steps for debugging
    
    See Also:
        - zPath_decoder: Main function using this helper
        - _extract_non_zvafile_filename: Non-zVaFile extraction
    """
    if is_zvafile:
        # zVaFile: Extract block (last part) and filename (last 2 parts before block)
        zBlock = zPath_parts[-1]
        logger.framework.debug(LOG_MSG_ZBLOCK, zBlock)

        zPath_2_zFile = zPath_parts[:-1]
        logger.framework.debug(LOG_MSG_ZPATH_2_ZFILE, zPath_2_zFile)

        # Extract file name (last 2 parts, or just last part if only 2 total)
        if len(zPath_2_zFile) == FILENAME_PARTS_FOR_SHORT:
            zFileName = zPath_2_zFile[-1]
        else:
            zFileName = PATH_SEP_DOT.join(zPath_2_zFile[-2:])
        logger.framework.debug(LOG_MSG_ZFILENAME_SHORT, zFileName)

        zRelPath_parts = zPath_parts[:-2]
        logger.framework.debug(LOG_MSG_ZRELPATH_PARTS, zRelPath_parts)
        return zFileName, zRelPath_parts

    # Non-zVaFile: No block extraction, filename includes extension
    logger.framework.debug(LOG_MSG_NO_ZBLOCK)
    return _extract_non_zvafile_filename(zPath_parts, logger)


def _extract_non_zvafile_filename(
    zPath_parts: List[str],
    logger: Any
) -> Tuple[str, List[str]]:
    """
    Extract filename from non-zVaFile path parts.
    
    Internal helper for extracting regular file names (with extensions) from
    path components. Handles symbol prefixes (@, ~) and finds filename start
    by detecting file extensions.
    
    Args:
        zPath_parts: List of dot-separated path components
        logger: Logger instance for diagnostic output
    
    Returns:
        Tuple[str, List[str]]: (filename, relative_path_parts)
            - filename: Extracted filename with extension
            - relative_path_parts: Remaining path components (including symbols)
    
    Notes:
        - Private helper function (not for external use)
        - Handles @ and ~ symbol prefixes
        - Uses _find_filename_start to detect filename boundary
        - Joins parts with dots to form filename
        - Logs extraction results for debugging
    
    See Also:
        - _extract_filename_from_parts: Caller function
        - _find_filename_start: Helper for finding filename start
    """
    symbol_idx = -1
    if zPath_parts and zPath_parts[0] in [SYMBOL_AT, SYMBOL_TILDE]:
        symbol_idx = 0

    if len(zPath_parts) >= MIN_PARTS_FOR_ZVAFILE:
        filename_start_idx = _find_filename_start(zPath_parts, symbol_idx)
        zFileName = PATH_SEP_DOT.join(zPath_parts[filename_start_idx:])
        zRelPath_parts = zPath_parts[:filename_start_idx]
    else:
        zFileName = PATH_SEP_DOT.join(zPath_parts[symbol_idx + 1:] if symbol_idx >= 0 else zPath_parts)
        zRelPath_parts = zPath_parts[:symbol_idx + 1] if symbol_idx >= 0 else []

    logger.framework.debug(LOG_MSG_ZFILENAME_SHORT, zFileName)
    logger.framework.debug(LOG_MSG_ZRELPATH_PARTS, zRelPath_parts)
    return zFileName, zRelPath_parts


def _find_filename_start(zPath_parts: List[str], symbol_idx: int) -> int:
    """
    Find where filename starts in path parts by detecting file extensions.
    
    Internal helper that scans path parts backwards to find the start of a
    filename by checking for common file extensions (.py, .js, .yaml, etc.).
    
    Args:
        zPath_parts: List of dot-separated path components
        symbol_idx: Index of symbol prefix (@ or ~), or -1 if none
    
    Returns:
        int: Index where filename starts in zPath_parts
    
    Notes:
        - Private helper function (not for external use)
        - Scans backwards from last part
        - Checks against FILE_EXTENSIONS list (11 common types)
        - Falls back to second-to-last part if no extension detected
        - Respects symbol_idx boundary (doesn't scan before symbol)
    
    See Also:
        - _extract_non_zvafile_filename: Caller function
        - FILE_EXTENSIONS: List of supported extensions
    """
    filename_start_idx = -1
    
    # Scan backwards from the end to find extension boundary
    for i in range(len(zPath_parts) - 1, symbol_idx, -1):
        if i == len(zPath_parts) - 1:
            if i > 0:
                # Check if last 2 parts form a valid filename.extension
                potential_filename = PATH_SEP_DOT.join(zPath_parts[i-1:])
                if any(potential_filename.endswith(ext) for ext in FILE_EXTENSIONS):
                    filename_start_idx = i - 1
                    break

    # Fallback: assume filename starts 2 parts from end (or after symbol)
    if filename_start_idx == -1:
        filename_start_idx = max(symbol_idx + 1, len(zPath_parts) - FALLBACK_FILENAME_START)

    return filename_start_idx


def zPath_decoder(
    zSession: Dict[str, Any],
    logger: Any,
    zPath: Optional[str] = None,
    zType: Optional[str] = None,
    display: Optional[Any] = None
) -> Tuple[str, str]:
    """
    Resolve dotted paths to file paths with workspace support.
    
    ⚠️ CRITICAL: This function is used externally by zLoader.py and zShell/load_executor.py.
    Signature must remain stable.
    
    Main path decoder that converts dot-notation paths to OS-specific file paths.
    Supports three resolution modes via symbol prefixes:
        - @ (at): Workspace-relative path
        - ~ (tilde): Absolute path from root
        - (none): Relative path from workspace
    
    Handles both zVaFiles (zUI, zSchema, zConfig) and regular files, with
    automatic filename extraction and path component resolution.
    
    Path Format Examples:
        @.config.zUI.users.main → {workspace}/config/zUI.users
        ~.etc.config.zSchema.db.users → /etc/config/zSchema.db
        config.scripts.utils.py → {workspace}/config/scripts/utils.py
    
    Args:
        zSession: Session dictionary containing workspace and file information
                  Expected keys: 'zSpace', 'zVaFolder', 'zVaFile'
        logger: Logger instance for diagnostic output
        zPath: Optional dotted path string to resolve
               If None and zType='zUI', uses session state
        zType: Optional file type hint (e.g., "zUI")
               Triggers UI mode path resolution if zPath is None
        display: Optional display adapter for visual feedback
                 (Terminal/Bifrost mode-agnostic)
    
    Returns:
        Tuple[str, str]: (full_path, filename)
            - full_path: Complete OS-specific file path (without extension for zVaFiles)
            - filename: Extracted filename
    
    Examples:
        >>> zSession = {'zSpace': '/app'}
        >>> logger = get_logger()
        
        # Workspace-relative zVaFile
        >>> zPath_decoder(zSession, logger, zPath='@.config.zUI.users.main')
        ('/app/config/zUI.users', 'zUI.users')
        
        # Absolute zVaFile
        >>> zPath_decoder(zSession, logger, zPath='~.etc.config.zSchema.db.users')
        ('/etc/config/zSchema.db', 'zSchema.db')
        
        # Relative regular file
        >>> zPath_decoder(zSession, logger, zPath='config.scripts.utils.py')
        ('/app/config/scripts/utils.py', 'utils.py')
        
        # UI mode (from session)
        >>> zSession['zVaFolder'] = 'config.ui'
        >>> zSession['zVaFile'] = 'zUI.users'
        >>> zPath_decoder(zSession, logger, zType='zUI')
        ('/app/config/ui/zUI.users', 'zUI.users')
    
    External Usage:
        zLoader.py (Week 6.9 - CRITICAL):
            full_path, filename = zPath_decoder(zSession, logger, zPath=path)
        Purpose: Resolve file paths before loading UI/Schema/Config files
        
        zShell/load_executor.py:
            full_path, filename = zPath_decoder(zSession, logger, zPath=path)
        Purpose: Shell command path resolution
    
    Notes:
        - Returns tuple of (full_path, filename)
        - full_path does NOT include extension for zVaFiles
        - Workspace defaults to os.getcwd() if not in zSession
        - Logs detailed resolution steps for debugging
        - Display integration allows visual feedback
        - Signature stability is CRITICAL for external usage
    
    See Also:
        - identify_zFile: File identification after path resolution
        - resolve_symbol_path: Symbol-based path resolution helper
        - is_zvafile_type: zVaFile detection
    """
    if display:
        display.zDeclare(DISPLAY_MSG_PATH_DECODER, color=COLOR_SUBLOADER, indent=INDENT_PATH, style=STYLE_SINGLE)

    # Get workspace from session or fall back to current directory
    zSpace = zSession.get(SESSION_KEY_ZSPACE) or os.getcwd()

    # UI mode: resolve from session state
    if not zPath and zType == FILE_TYPE_ZUI:
        zVaFolder_basepath, zFileName = _handle_ui_mode_path(zSession, zSpace, logger)
    else:
        # Standard mode: parse dotted path
        zPath_parts = zPath.lstrip(PATH_SEP_DOT).split(PATH_SEP_DOT)
        logger.framework.debug(LOG_MSG_PARTS, zPath_parts)

        # Detect if this is a zVaFile path
        is_zvafile = is_zvafile_type(zPath_parts)
        logger.framework.debug(LOG_MSG_IS_ZVAFILE, is_zvafile)

        # Extract filename and relative path components
        zFileName, zRelPath_parts = _extract_filename_from_parts(zPath_parts, is_zvafile, logger)

        # Resolve path based on symbol prefix (@, ~, or none)
        symbol = zRelPath_parts[0] if zRelPath_parts else None
        logger.framework.debug(LOG_MSG_SYMBOL, symbol)

        zVaFolder_basepath = resolve_symbol_path(symbol, zRelPath_parts, zSpace, zSession, logger)

    # Combine base path and filename
    zVaFile_fullpath = os.path.join(zVaFolder_basepath, zFileName)
    logger.framework.debug(LOG_MSG_ZVAFILE_FULLPATH, zVaFile_fullpath)

    return zVaFile_fullpath, zFileName


def resolve_symbol_path(
    symbol: Optional[str],
    zRelPath_parts: List[str],
    zSpace: str,
    zSession: Dict[str, Any],
    logger: Any
) -> str:
    """
    Resolve path based on symbol (@, ~, or no symbol).
    
    Internal helper that handles the three path resolution modes:
        - @ (at): Workspace-relative path
        - ~ (tilde): Absolute path from root
        - (none): Relative path from workspace
    
    Args:
        symbol: Path symbol prefix (SYMBOL_AT, SYMBOL_TILDE, or None)
        zRelPath_parts: List of path components (including symbol if present)
        zSpace: Workspace directory path
        zSession: Session dictionary (for workspace validation)
        logger: Logger instance for diagnostic output
    
    Returns:
        str: Resolved base path
    
    Examples:
        >>> resolve_symbol_path('@', ['@', 'config', 'data'], '/app', {}, logger)
        '/app/config/data'
        
        >>> resolve_symbol_path('~', ['~', 'etc', 'config'], '/app', {}, logger)
        '/etc/config'
        
        >>> resolve_symbol_path(None, ['config', 'data'], '/app', {}, logger)
        '/app/config/data'
    
    Notes:
        - @ symbol: Relative to zSpace in zSession (or cwd)
        - ~ symbol: Absolute path from root
        - No symbol: Relative to zSpace (same as @)
        - Logs warnings if @ used without configured workspace
        - Skips first part (symbol) when building path
    
    See Also:
        - zPath_decoder: Main function using this helper
    """
    if symbol == SYMBOL_AT:
        logger.framework.debug(LOG_MSG_SYMBOL_AT)

        # Warn if workspace not configured
        if not zSession.get(SESSION_KEY_ZSPACE):
            logger.warning(LOG_MSG_NO_WORKSPACE)
            logger.warning(LOG_MSG_NO_WORKSPACE_HELP)
            logger.warning(LOG_MSG_NO_WORKSPACE_FALLBACK, zSpace)

        # Build path: skip first part (symbol), join rest
        rel_base_parts = zRelPath_parts[1:]
        zVaFolder_basepath = os.path.join(zSpace, *rel_base_parts)
        logger.framework.debug(LOG_MSG_ZVAFOLDER_PATH, zVaFolder_basepath)
        
    elif symbol == SYMBOL_TILDE:
        logger.framework.debug(LOG_MSG_SYMBOL_TILDE)
        # Build path: skip first part (symbol), join rest from root
        rel_base_parts = zRelPath_parts[1:]
        zVaFolder_basepath = os.path.join(*rel_base_parts)
        
    else:
        logger.framework.debug(LOG_MSG_SYMBOL_NONE)
        # Build path: join all parts relative to workspace
        zVaFolder_basepath = os.path.join(zSpace, *(zRelPath_parts or []))

    return zVaFolder_basepath


def identify_zFile(
    filename: str,
    full_zFilePath: str,
    logger: Any,
    display: Optional[Any] = None
) -> Tuple[str, str]:
    """
    Identify file type and find actual file path with extension.
    
    ⚠️ CRITICAL: This function is used externally by zLoader.py and zShell/load_executor.py.
    Signature must remain stable.
    
    Determines file type (zUI, zSchema, zConfig, zVaFile, zOther) and resolves
    the actual file path with extension. For zVaFiles, auto-detects extension
    by trying .json, .yaml, .yml in order. For regular files, uses provided
    extension and validates file existence.
    
    Args:
        filename: Filename to identify (may be zVaFile or regular file)
        full_zFilePath: Full path without extension (for zVaFiles) or
                       with extension (for regular files)
        logger: Logger instance for diagnostic output
        display: Optional display adapter for visual feedback
                 (Terminal/Bifrost mode-agnostic)
    
    Returns:
        Tuple[str, str]: (found_path, extension)
            - found_path: Actual file path with extension
            - extension: File extension (e.g., '.yaml', '.py')
    
    Raises:
        FileNotFoundError: If file cannot be found (zVaFile with no extension
                          match, or regular file does not exist)
    
    Examples:
        >>> logger = get_logger()
        
        # zUI file (extension auto-detected)
        >>> identify_zFile('zUI.users', '/app/config/zUI.users', logger)
        ('/app/config/zUI.users.yaml', '.yaml')
        
        # zSchema file (tries .json, .yaml, .yml)
        >>> identify_zFile('zSchema.db', '/etc/zSchema.db', logger)
        ('/etc/zSchema.db.json', '.json')
        
        # Regular file (extension provided)
        >>> identify_zFile('script.py', '/app/scripts/script.py', logger)
        ('/app/scripts/script.py', '.py')
        
        # File not found
        >>> identify_zFile('missing.yaml', '/app/missing.yaml', logger)
        FileNotFoundError: File not found: /app/missing.yaml
    
    External Usage:
        zLoader.py (Week 6.9 - CRITICAL):
            file_path, ext = identify_zFile(filename, full_path, logger)
        Purpose: Identify file type and find actual file with extension
        
        zShell/load_executor.py:
            file_path, ext = identify_zFile(filename, full_path, logger)
        Purpose: Shell command file identification
    
    Notes:
        - zVaFiles: Tries extensions in order (.zolo, .json, .yaml, .yml)
        - Regular files: Extension already in filename
        - Validates file existence for all types
        - Logs file type and extension for debugging
        - Display integration allows visual feedback
        - Signature stability is CRITICAL for external usage
    
    See Also:
        - zPath_decoder: Path resolution before file identification
        - is_zvafile_type: zVaFile detection
    """
    # Detect if this is a zVaFile
    is_zvafile = is_zvafile_type(filename)

    if is_zvafile:
        # zVaFiles: Auto-detect extension
        # Determine specific type
        if filename.startswith(ZVAFILE_PREFIX_UI):
            logger.debug(LOG_MSG_FILE_TYPE, FILE_TYPE_ZUI)
            zFile_type = FILE_TYPE_ZUI
        elif filename.startswith(ZVAFILE_PREFIX_SCHEMA):
            logger.debug(LOG_MSG_FILE_TYPE, FILE_TYPE_ZSCHEMA)
            zFile_type = FILE_TYPE_ZSCHEMA
        elif filename.startswith(ZVAFILE_PREFIX_CONFIG):
            logger.debug(LOG_MSG_FILE_TYPE, FILE_TYPE_ZCONFIG)
            zFile_type = FILE_TYPE_ZCONFIG
        else:
            logger.debug(LOG_MSG_FILE_TYPE_UNKNOWN)
            zFile_type = FILE_TYPE_ZVAFILE

        # Try to find file with supported extensions
        found_path = None
        zFile_extension = None

        for ext in ZVAFILE_EXTENSIONS:
            candidate = full_zFilePath + ext
            if os.path.exists(candidate):
                found_path = candidate
                zFile_extension = ext
                logger.debug(LOG_MSG_ZFILE_EXTENSION, ext)
                break

        # If no match found, raise error
        if not found_path:
            msg = ERROR_MSG_NO_ZVAFILE_FOUND.format(full_zFilePath)
            logger.error(msg)
            raise FileNotFoundError(msg)
            
    else:
        # Other files: Extension already provided in filename
        logger.debug(LOG_MSG_FILE_TYPE_OTHER)
        zFile_type = FILE_TYPE_ZOTHER

        # Extract extension from filename for display
        _, zFile_extension = os.path.splitext(filename)

        # File path already includes extension
        found_path = full_zFilePath

        # Verify file exists
        if not os.path.exists(found_path):
            msg = ERROR_MSG_FILE_NOT_FOUND.format(found_path)
            logger.error(msg)
            raise FileNotFoundError(msg)

    # Display file type and extension if display available
    if display:
        display.zDeclare(
            DISPLAY_MSG_FILE_TYPE_TEMPLATE.format(zFile_type, zFile_extension),
            color=COLOR_SUBLOADER,
            indent=INDENT_PATH,
            style=STYLE_SINGLE
        )

    return found_path, zFile_extension
