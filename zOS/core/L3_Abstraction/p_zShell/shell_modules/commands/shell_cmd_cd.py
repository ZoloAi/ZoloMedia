# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_cd.py

"""
Change Directory (cd) and Current Working Directory (cwd/pwd) Command Executors.

This module provides shell commands for directory navigation and inspection
using zCLI's declarative zPath syntax alongside traditional filesystem paths.

OVERVIEW:
    The 'cd' command changes the current OS working directory (via os.chdir()),
    while 'cwd' (alias: 'pwd') displays the current location in both absolute
    and zPath formats. SESSION_KEY_ZSPACE remains constant as the "home base"
    workspace directory (set at shell startup), allowing 'cd @.' to always return
    to the original workspace root.

COMMAND NAMING:
    • cwd: Primary command (Current Working Directory) - modern, semantically accurate
    • pwd: Alias command (Print Working Directory) - Unix compatibility for veteran users
    Both execute the same function but 'cwd' is the preferred modern terminology.

ZPATH SYNTAX:
    zCLI uses a dot-notation path syntax (zPath) that parallels filesystem paths:
    
    • @.path.to.dir       → Workspace-relative (e.g., @.src.components)
    • ~.path.to.dir       → Home-relative (e.g., ~.Projects.zolo-zcli)
    • ~                   → Home directory
    • ..                  → Parent directory
    • .                   → Current directory
    • /absolute/path      → Standard absolute path
    • relative/path       → Standard relative path

COMMAND EXAMPLES:
    cd ~.Projects.zolo-zcli   # Navigate to ~/Projects/zolo-zcli
    cd @.src                  # Navigate to workspace/src
    cd ..                     # Go to parent directory
    cd                        # Go to home directory
    cwd                       # Show current directory in both formats (primary)
    pwd                       # Same as 'cwd' (Unix compatibility alias)

ARCHITECTURE:
    Both commands are UI adapters - they display friendly messages directly
    to the user via zDisplay and return None on success. For programmatic
    directory manipulation, use os.chdir() and os.getcwd() directly.

SESSION INTEGRATION:
    • Reads: SESSION_KEY_ZSPACE for workspace root (constant "home base")
    • Writes: NONE - SESSION_KEY_ZSPACE is immutable during shell session
    • cd command: Uses os.chdir() to change OS working directory
    • pwd/cwd command: Uses os.getcwd() to read current OS directory
    • cd @. behavior: Navigates to SESSION_KEY_ZSPACE (workspace root)
    • Pattern: Uses centralized constants from zConfig.config_session

CROSS-SUBSYSTEM DEPENDENCIES:
    • zConfig: SESSION_KEY_ZSPACE constant, session management
    • zDisplay: User feedback (success, error, info messages)
    • zParser: Future integration for standardized zPath resolution

DISPLAY MODES:
    • Terminal: Shows formatted messages with zDisplay (no JSON output)
    • Bifrost: Same display pattern (WebSocket mode-agnostic)

TYPE SAFETY:
    All functions include comprehensive type hints using types imported from
    the zCLI namespace for consistency across the framework.

ERROR HANDLING:
    Gracefully handles invalid paths, permission errors, non-existent directories,
    and attempts to cd into files. All errors display user-friendly messages.

FUTURE ENHANCEMENTS:
    • cd -: Return to previous directory (history stack)
    • cd bookmarks: Save/restore favorite locations
    • pwd -P: Show physical path (resolve symlinks)
    • Integration with zParser for standardized zPath resolution

RELATED COMMANDS:
    • shell_cmd_ls: List directory contents (uses similar zPath resolution)
    • shell_cmd_where: Toggle prompt display of current location
    • navigation_state: Manages navigation history in UI mode

Author: zOS Framework
Version: 1.5.4
Module: zShell (Command Executors - Group A: Basic Terminal Commands)
"""

import os
from pathlib import Path

from zOS import Any, Dict, Optional
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZSPACE

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# zPath Prefixes
ZPATH_WORKSPACE_PREFIX: str = "@."
ZPATH_HOME_PREFIX: str = "~."
ZPATH_HOME: str = "~"
ZPATH_PARENT: str = ".."
ZPATH_CURRENT: str = "."
ZPATH_SEPARATOR: str = "."
ZMACHINE_PREFIX_SHORT: str = "zMachine"
ZMACHINE_PREFIX_LONG: str = "~zMachine"

# Error Codes
ERROR_INVALID_PATH: str = "invalid_path"
ERROR_DIR_NOT_FOUND: str = "directory_not_found"
ERROR_NOT_A_DIRECTORY: str = "not_a_directory"
ERROR_PERMISSION_DENIED: str = "permission_denied"

# Dictionary Keys
DICT_KEY_ERROR: str = "error"
DICT_KEY_PATH: str = "path"
DICT_KEY_ARGS: str = "args"

# User Messages - cd
MSG_CD_SUCCESS: str = "Changed directory to: {path}"
MSG_CD_ERROR_INVALID: str = "Invalid path: {error}"
MSG_CD_ERROR_NOT_FOUND: str = "Directory not found: {path}"
MSG_CD_ERROR_NOT_DIR: str = "Not a directory: {path}"
MSG_CD_ERROR_PERMISSION: str = "Permission denied: {path}"

# User Messages - pwd
MSG_PWD_HEADER: str = "Current Working Directory"
MSG_PWD_ZPATH_PREFIX: str = "(as zPath: {zpath})"

# Display Constants
DISPLAY_COLOR_INFO: str = "INFO"
DISPLAY_COLOR_ERROR: str = "ERROR"
DISPLAY_COLOR_SUCCESS: str = "SUCCESS"
DISPLAY_STYLE_FULL: str = "full"
DISPLAY_INDENT_HEADER: int = 0
DISPLAY_INDENT_PATH: int = 1


# ============================================================================
# PUBLIC API
# ============================================================================

def execute_cd(zcli: Any, parsed: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Execute cd (change directory) command with zPath support.
    
    Changes the current working directory (session zSpace) to the specified
    target. Supports zPath syntax (@., ~.), traditional paths, and shortcuts
    (., .., ~). Validates the target exists and is a directory before changing.
    
    Args:
        zcli: zCLI instance with session, config, and display access
        parsed: Parsed command dictionary with 'args' and 'options'
    
    Returns:
        Optional[Dict[str, str]]: Error dict if operation fails, None on success.
        Success messages are displayed directly to the user.
    
    Command Syntax:
        cd                        # Go to home directory
        cd ~                      # Go to home directory (explicit)
        cd ~.Projects.zolo-zcli   # Go to ~/Projects/zolo-zcli
        cd @.src.components       # Go to workspace/src/components
        cd ..                     # Go to parent directory
        cd .                      # Stay in current directory
        cd /absolute/path         # Go to absolute path
        cd relative/path          # Go to relative path
    
    zPath Resolution:
        @.path.to.dir → workspace/path/to/dir
        ~.path.to.dir → ~/path/to/dir
        ~             → Home directory
        ..            → Parent of current directory
        .             → Current directory (no change)
    
    Validation:
        • Target path must exist
        • Target must be a directory (not a file)
        • Must have permission to access target
    
    Side Effects:
        Changes OS working directory via os.chdir(). Does NOT modify
        SESSION_KEY_ZSPACE (which remains constant as workspace root).
    
    Examples:
        >>> execute_cd(zcli, {"args": ["~.Projects"], "options": {}})
        # Displays: "Changed directory to: /Users/name/Projects"
        # os.getcwd() now returns: /Users/name/Projects
        # Returns: None
        
        >>> execute_cd(zcli, {"args": ["nonexistent"], "options": {}})
        # Displays: "Directory not found: /current/path/nonexistent"
        # Returns: {"error": "directory_not_found", "path": "..."}
    
    Note:
        Shell commands are UI adapters - they display messages directly.
        For programmatic directory changes, use os.chdir() directly.
    
    Related:
        execute_pwd(), _resolve_zpath(), shell_interactive._get_prompt()
    """
    args: list = parsed.get(DICT_KEY_ARGS, [])
    
    # Determine target (default to home if no args)
    if not args:
        target = ZPATH_HOME
    else:
        target = args[0]
    
    # Resolve zPath or standard path to absolute Path object
    try:
        resolved: Path = _resolve_zpath(zcli, target)
    except (OSError, ValueError, PermissionError) as e:
        zcli.display.error(MSG_CD_ERROR_INVALID.format(error=str(e)))
        return {DICT_KEY_ERROR: ERROR_INVALID_PATH}
    
    # Validate target exists
    if not resolved.exists():
        zcli.display.error(MSG_CD_ERROR_NOT_FOUND.format(path=resolved))
        return {DICT_KEY_ERROR: ERROR_DIR_NOT_FOUND, DICT_KEY_PATH: str(resolved)}
    
    # Validate target is a directory
    if not resolved.is_dir():
        zcli.display.error(MSG_CD_ERROR_NOT_DIR.format(path=resolved))
        return {DICT_KEY_ERROR: ERROR_NOT_A_DIRECTORY, DICT_KEY_PATH: str(resolved)}
    
    # Change OS working directory (does NOT update SESSION_KEY_ZSPACE)
    os.chdir(resolved)
    
    # Display success message
    zcli.display.success(MSG_CD_SUCCESS.format(path=resolved))
    
    return None


def execute_pwd(zcli: Any, parsed: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
    """
    Execute cwd/pwd (current/print working directory) command with dual format display.
    
    Displays the current OS working directory (from os.getcwd()) in both absolute
    filesystem format and zPath format (if under home directory). Provides users
    with clear context about their current location.
    
    Command Naming:
        This function handles both 'cwd' (primary) and 'pwd' (alias) commands.
        They execute identically - 'cwd' is preferred for modern clarity,
        'pwd' is provided for Unix compatibility.
    
    Args:
        zcli: zCLI instance with session and display access
        parsed: Parsed command dictionary (not used, but required for interface)
    
    Returns:
        None: All output is displayed directly to user
    
    Display Format:
        Current Working Directory
          /Users/name/Projects/zolo-zcli
          (as zPath: ~.Projects.zolo-zcli)
        
        OR (if outside home directory):
        Current Working Directory
          /usr/local/bin
    
    zPath Conversion:
        If current directory is under home, shows zPath format:
        • /Users/name/Projects/zolo-zcli → ~.Projects.zolo-zcli
        • /Users/name → ~ (just home)
        
        If outside home, only shows absolute path.
    
    Session Integration:
        Reads from os.getcwd() for current OS working directory.
        Does NOT read SESSION_KEY_ZSPACE (which is workspace root).
    
    Examples:
        >>> execute_pwd(zcli, {"args": [], "options": {}})
        # Works for both 'cwd' and 'pwd' commands
        # Displays formatted output with both path formats
        # Returns: None
    
    Note:
        Shell commands are UI adapters - they display messages directly.
        For programmatic access to current directory, use os.getcwd().
    
    Related:
        execute_cd(), _format_zpath_display(), shell_cmd_where.py
    """
    # Get current OS working directory
    current_dir: str = os.getcwd()
    resolved: Path = Path(current_dir).resolve()
    
    # Display header
    zcli.display.zDeclare(
        MSG_PWD_HEADER,
        color=DISPLAY_COLOR_INFO,
        indent=DISPLAY_INDENT_HEADER,
        style=DISPLAY_STYLE_FULL
    )
    
    # Display absolute path
    zcli.display.text(f"  {resolved}", indent=DISPLAY_INDENT_PATH)
    
    # Also show as zPath if under home directory
    zpath: Optional[str] = _format_zpath_display(resolved)
    if zpath:
        zcli.display.text(
            f"  {MSG_PWD_ZPATH_PREFIX.format(zpath=zpath)}",
            indent=DISPLAY_INDENT_PATH
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _resolve_zpath(zcli: Any, target: str) -> Path:
    """
    Resolve a zPath or standard path to an absolute Path object.
    
    Handles multiple path formats:
    • @.path.to.dir → workspace-relative (from session zSpace)
    • ~zMachine.path → zMachine user data directory paths
    • zMachine.path  → zMachine user data directory paths
    • ~.path.to.dir → home-relative
    • ~             → home directory
    • ..            → parent of current directory
    • .             → current directory
    • /abs/path     → absolute path (unchanged)
    • rel/path      → relative to current directory
    
    Args:
        zcli: zCLI instance for session access (to get current workspace)
        target: Path string in any supported format
    
    Returns:
        Path: Resolved absolute path object (not yet validated to exist)
    
    Raises:
        OSError: If path resolution fails
        ValueError: If path format is invalid
        PermissionError: If path is inaccessible
    
    Examples:
        >>> _resolve_zpath(zcli, "@.src.components")
        Path("/workspace/path/src/components")
        
        >>> _resolve_zpath(zcli, "~.Projects.zolo-zcli")
        Path("/Users/name/Projects/zolo-zcli")
        
        >>> _resolve_zpath(zcli, "..")
        Path("/current/parent")
    
    Note:
        This is a DRY helper used by execute_cd(). Similar logic exists in
        shell_cmd_ls.py and should eventually be unified or delegated to zParser.
    
    TODO:
        Consider extracting to shared utility module or delegating to
        zParser.parse_zpath() for standardized resolution across zShell commands.
    """
    # Get workspace root (constant) for @. prefix
    workspace_root: Path = Path(zcli.session.get(SESSION_KEY_ZSPACE, ZPATH_CURRENT))
    
    # Get current working directory for relative paths (., .., relative)
    current_dir: Path = Path(os.getcwd())
    
    # Workspace-relative zPath (@.path.to.dir)
    if target.startswith(ZPATH_WORKSPACE_PREFIX):
        path_parts = target[len(ZPATH_WORKSPACE_PREFIX):].split(ZPATH_SEPARATOR)
        resolved = workspace_root / "/".join(path_parts)
    
    # zMachine paths (~zMachine.* or zMachine.*)
    elif target.startswith(ZMACHINE_PREFIX_LONG) or target.startswith(ZMACHINE_PREFIX_SHORT):
        # Get user data directory from zConfig
        user_data_dir = zcli.config.sys_paths.user_data_dir
        
        # Remove prefix and get subpath
        if target.startswith(ZMACHINE_PREFIX_LONG):
            # ~zMachine or ~zMachine.subpath
            remainder = target[len(ZMACHINE_PREFIX_LONG):]
        else:
            # zMachine or zMachine.subpath
            remainder = target[len(ZMACHINE_PREFIX_SHORT):]
        
        # Handle just ~zMachine or zMachine (no subpath)
        if not remainder or remainder == ".":
            resolved = Path(user_data_dir)
        # Handle ~zMachine.subpath or zMachine.subpath
        elif remainder.startswith("."):
            # Remove leading dot and convert dot notation to path
            subpath = remainder[1:]  # Remove leading "."
            path_parts = subpath.split(ZPATH_SEPARATOR)
            resolved = Path(user_data_dir) / "/".join(path_parts)
        else:
            # Invalid format (no dot after zMachine)
            resolved = current_dir / target
    
    # Home-relative zPath (~.path.to.dir)
    elif target.startswith(ZPATH_HOME_PREFIX):
        path_parts = target[len(ZPATH_HOME_PREFIX):].split(ZPATH_SEPARATOR)
        resolved = Path.home() / "/".join(path_parts)
    
    # Home directory shortcut (~)
    elif target == ZPATH_HOME:
        resolved = Path.home()
    
    # Parent directory shortcut (..)
    elif target == ZPATH_PARENT:
        resolved = current_dir.parent
    
    # Current directory shortcut (.)
    elif target == ZPATH_CURRENT:
        resolved = current_dir
    
    # Absolute or relative standard path
    else:
        if Path(target).is_absolute():
            resolved = Path(target)
        else:
            resolved = current_dir / target
    
    # Resolve to absolute path (resolves symlinks, normalizes)
    return resolved.resolve()


def _format_zpath_display(path: Path) -> Optional[str]:
    """
    Format an absolute path as zPath notation for display.
    
    Converts filesystem paths to zCLI's dot-notation format, but only if the
    path is under the user's home directory. Paths outside home are not
    converted to zPath format.
    
    Args:
        path: Absolute Path object to format
    
    Returns:
        Optional[str]: zPath string if under home, None otherwise
    
    zPath Format:
        /Users/name                    → ~ (just home)
        /Users/name/Projects/zolo-zcli → ~.Projects.zolo-zcli
        /usr/local/bin                 → None (outside home)
    
    Examples:
        >>> _format_zpath_display(Path("/Users/name/Projects/zolo-zcli"))
        "~.Projects.zolo-zcli"
        
        >>> _format_zpath_display(Path("/Users/name"))
        "~"
        
        >>> _format_zpath_display(Path("/usr/local/bin"))
        None
    
    Note:
        Similar logic exists in shell_cmd_where._format_zpath_display().
        Consider unifying if zPath formatting becomes more widespread.
    
    Related:
        execute_pwd() uses this for dual-format display
    """
    try:
        home: Path = Path.home()
        
        # Check if path is under home directory
        if path.is_relative_to(home):
            relative_path: Path = path.relative_to(home)
            
            # Special case: exactly at home directory
            if relative_path == Path(ZPATH_CURRENT):
                return ZPATH_HOME
            
            # Build zPath with dots
            zpath_parts: tuple = relative_path.parts
            return ZPATH_HOME_PREFIX + ZPATH_SEPARATOR.join(zpath_parts)
        
        # Path is outside home, no zPath representation
        return None
    
    except (ValueError, AttributeError):
        # Error in path comparison, return None
        return None
