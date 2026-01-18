# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_ls.py

"""
Directory Listing Command Executor for zShell.

This module provides directory listing commands for the zCLI shell environment.
Supports multiple command aliases for different user preferences:
- `list` - Modern, beginner-friendly (zCLI style)
- `ls` - Industry standard (Unix style)
- `dir` - Windows compatibility

All commands support zPath syntax, multiple display formats, recursive listing,
and filtering options.

Core Features:
--------------
1. **Directory Listing:**
   - List files and directories in current or specified location
   - Group by type (directories first, then files)
   - Display file sizes in human-readable format
   
2. **zPath Support:**
   - Workspace-relative: `@.src.components` → workspace/src/components
   - Absolute zPath: `~.Projects.myapp` → /Users/name/Projects/myapp
   - Regular paths: `./src` or `/absolute/path`
   
3. **Display Options (Dual Support):**
   
   **Modern zCLI Terminology (Beginner-Friendly):**
   - `-size`: Show file sizes
   - `-hidden`: Include hidden files (starting with .)
   - `-deep`: List subdirectories recursively
   - `-file`: Show only files (exclude directories)
   - `-dir` or `-folder`: Show only directories (exclude files)
   
   **Industry Standard Unix (Experienced Users):**
   - `-l` or `-long`: Show file sizes (alias for -size)
   - `-a` or `-all`: Include hidden files (alias for -hidden)
   - `-r` or `-recursive`: Recursive listing (alias for -deep)
   
4. **Bulk Display Architecture:**
   - Uses single `display.list()` call for all entries
   - Efficient for large directories
   - Mode-agnostic (Terminal + Bifrost)

Commands:
---------
- `list [path] [options]` - List directory contents (zCLI style, beginner-friendly)
- `ls [path] [options]` - List directory contents (Unix-style, industry standard)
- `dir [path] [options]` - List directory contents (Windows-style compatibility)

Examples:
---------
**Modern zCLI Style (Beginner-Friendly):**
```
list                      # List current workspace
list @.src                # List workspace/src
list @.src -size          # List with file sizes
list @.src -hidden        # Include hidden files
list @.src -deep          # Recursive listing
list @.src -file          # Show only files
list @.src -dir           # Show only directories
list -size -hidden        # Combine options
```

**Industry Standard Unix Style:**
```
ls -l                   # List with file sizes
ls -a                   # Include hidden files
ls -r                   # Recursive listing
ls -alr                 # Combined flags (Unix-style)
ls @.src -l             # zPath with Unix flags
dir                     # Windows alias for ls
```

**Mixed Style (Best of Both):**
```
list -file -l             # Modern filtering + Unix display flag
list @.src -deep -a       # Modern + Unix options mixed
ls -file -size            # Unix command + modern options
```

Output Format:
--------------
Directory: /path/to/directory

  [DIR] subdirectory1/
  [DIR] subdirectory2/

  [FILE] file1.py          2.5KB
  [FILE] file2.txt         1.2KB
  
Total: 2 dirs, 2 files

Architecture:
-------------
1. **zPath Resolution:** Delegates to shared helper or zParser
2. **Entry Collection:** Gathers files/dirs with metadata
3. **Bulk Display:** Single display.list() call
4. **UI Adapter Pattern:** Returns None (display-only)

Session Integration:
-------------------
- Reads SESSION_KEY_ZSPACE for default directory
- No session modifications (read-only command)

Cross-Subsystem Dependencies:
-----------------------------
- zConfig: SESSION_KEY_ZSPACE for workspace path
- zDisplay: display.list() for bulk output, display.error() for errors
- zParser: (optional) parse_path() for advanced zPath resolution

Type Safety:
-----------
- 100% type hint coverage on all functions
- Imported from zCLI: Any, Dict, List, Optional, Union
- Path types from pathlib for filesystem operations

Error Handling:
--------------
- FileNotFoundError: Path doesn't exist
- PermissionError: No read access
- OSError: Filesystem errors
- ValueError: Invalid path format
All errors display via display.error() and return None

Author: zCLI Development Team
Version: 1.5.4
Last Updated: 2025-11-02
"""

# Standard library imports
import os
from pathlib import Path

# zCLI type imports
from zOS import Any, Dict, List, Optional

# zConfig imports
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZSPACE,
)


# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# --- Option Flags (Modern zCLI Terminology - Single Dash) ---
OPTION_SIZE: str = "size"            # Show file sizes (modern: -size)
OPTION_HIDDEN: str = "hidden"        # Show hidden files (modern: -hidden)
OPTION_DEEP: str = "deep"            # Recursive listing (modern: -deep)
OPTION_FILE: str = "file"            # Show only files (modern: -file)
OPTION_DIR: str = "dir"              # Show only directories (modern: -dir)
OPTION_FOLDER: str = "folder"        # Alias for -dir

# --- Option Flags (Industry Standard Unix) ---
OPTION_LONG: str = "long"            # Show file sizes (Unix)
OPTION_L: str = "l"                  # Show file sizes (Unix short)
OPTION_ALL: str = "all"              # Show hidden files (Unix)
OPTION_A: str = "a"                  # Show hidden files (Unix short)
OPTION_RECURSIVE: str = "recursive"  # Recursive listing (Unix)
OPTION_R: str = "r"                  # Recursive listing (Unix short)
OPTION_HUMAN: str = "human"          # Human-readable (compatibility)
OPTION_H: str = "h"                  # Human-readable (compatibility)

# --- Entry Types ---
ENTRY_TYPE_DIR: str = "dir"
ENTRY_TYPE_FILE: str = "file"

# --- Display Icons ---
ICON_DIRECTORY: str = "[DIR]"
ICON_FILE: str = "[FILE]"
ICON_HEADER: str = "Directory:"

# --- zPath Prefixes ---
ZPATH_WORKSPACE_PREFIX: str = "@."
ZPATH_ABSOLUTE_PREFIX: str = "~."
ZPATH_SEPARATOR: str = "."

# --- Error Codes ---
ERROR_PATH_NOT_FOUND: str = "path_not_found"
ERROR_NOT_A_DIRECTORY: str = "not_a_directory"
ERROR_PERMISSION_DENIED: str = "permission_denied"
ERROR_FILESYSTEM_ERROR: str = "filesystem_error"
ERROR_INVALID_PATH: str = "invalid_path"

# --- User Messages ---
MSG_PATH_NOT_FOUND: str = "Path not found: {path}"
MSG_NOT_A_DIRECTORY: str = "Not a directory: {path}"
MSG_PERMISSION_DENIED: str = "Permission denied: {path}"
MSG_FILESYSTEM_ERROR: str = "Failed to list directory: {error}"
MSG_EMPTY_DIRECTORY: str = "(empty directory)"
MSG_DIRECTORY_HEADER: str = "{icon} {path}"
MSG_DIRECTORIES_LABEL: str = "Directories:"
MSG_FILES_LABEL: str = "Files:"
MSG_TOTAL_SUMMARY: str = "Total: {dirs} dirs, {files} files"

# --- Dictionary Keys ---
DICT_KEY_ARGS: str = "args"
DICT_KEY_OPTIONS: str = "options"
DICT_KEY_NAME: str = "name"
DICT_KEY_TYPE: str = "type"
DICT_KEY_PATH: str = "path"
DICT_KEY_SIZE: str = "size"

# --- Defaults ---
DEFAULT_TARGET_DIR: str = "."
DEFAULT_LIST_STYLE: str = "none"
DEFAULT_NAME_WIDTH: int = 50
DEFAULT_SIZE_WIDTH: int = 10

# --- File Size Constants ---
SIZE_UNIT_BYTE: int = 1
SIZE_UNIT_KB: int = 1024
SIZE_UNIT_MB: int = 1024 * 1024
SIZE_UNIT_GB: int = 1024 * 1024 * 1024
SIZE_LABEL_BYTE: str = "B"
SIZE_LABEL_KB: str = "KB"
SIZE_LABEL_MB: str = "MB"
SIZE_LABEL_GB: str = "GB"
SIZE_FORMAT_PRECISION: int = 1

# --- Display Constants ---
DISPLAY_BLANK_LINE: str = ""
DISPLAY_DIR_SUFFIX: str = "/"
DISPLAY_INDENT_BASE: int = 2


# ============================================================================
# PUBLIC API
# ============================================================================

def execute_ls(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute list/ls/dir command to list directory contents.
    
    This is the main entry point for the directory listing command. It resolves
    the target path (using zPath syntax if provided), collects directory entries,
    and displays them using a single bulk display.list() call for efficiency.
    
    The function follows the UI adapter pattern, displaying output directly via
    zDisplay and returning None on both success and failure (errors are displayed
    but don't propagate exceptions).
    
    Args:
        zcli: The zCLI instance providing access to session, display, and parser
        parsed: Dictionary containing parsed command data with keys:
            - "args" (List[str]): Optional target directory path
            - "options" (Dict[str, bool]): Command options (-l, -a, -r, etc.)
    
    Returns:
        None: Always returns None (UI adapter pattern)
    
    Display Options (Dual Support):
        Modern zCLI (Semantic, Beginner-Friendly):
            -size: Show file sizes
            -hidden: Include hidden files (starting with .)
            -deep: List subdirectories recursively
            -file: Show only files (exclude directories)
            -dir, -folder: Show only directories (exclude files)
        
        Industry Standard Unix (Aliases):
            -l, -long: Alias for -size
            -a, -all: Alias for -hidden
            -r, -recursive: Alias for -deep
            -h, -human: Human-readable sizes (always on, kept for compatibility)
    
    Examples:
        >>> execute_ls(zcli, {"args": [], "options": {}})
        # Lists current working directory (works for list/ls/dir)
        
        >>> execute_ls(zcli, {"args": ["@.src"], "options": {"size": True}})
        # Lists workspace/src with file sizes (modern: -size)
        
        >>> execute_ls(zcli, {"args": ["@.src"], "options": {"long": True}})
        # Lists workspace/src with file sizes (Unix: -l)
        
        >>> execute_ls(zcli, {"args": ["~.Projects"], "options": {"hidden": True}})
        # Lists ~/Projects including hidden files (modern: -hidden)
        
        >>> execute_ls(zcli, {"args": ["@.src"], "options": {"file": True}})
        # Lists only files in workspace/src (modern: -file)
    
    Session Access:
        - Reads current working directory via os.getcwd() for default
        - No session modifications (read-only)
    
    Error Handling:
        All errors are caught, displayed via display.error(), and return None.
        No exceptions propagate to caller.
    """
    args: List[str] = parsed.get(DICT_KEY_ARGS, [])
    options: Dict[str, bool] = parsed.get(DICT_KEY_OPTIONS, {})
    
    # Determine target directory
    target: str
    if args:
        target = args[0]
    else:
        # Use current working directory (not workspace)
        target = os.getcwd()
    
    # Resolve zPath to filesystem path
    resolved: Optional[Path] = _resolve_zpath(zcli, target)
    if resolved is None:
        return None  # Error already displayed
    
    # Validate path exists and is a directory
    if not resolved.exists():
        zcli.display.error(MSG_PATH_NOT_FOUND.format(path=resolved))
        return None
    
    if not resolved.is_dir():
        zcli.display.error(MSG_NOT_A_DIRECTORY.format(path=resolved))
        return None
    
    # Collect directory entries
    try:
        entries: List[Dict[str, Any]] = _collect_entries(resolved, options)
        
        # Display entries using bulk display
        _display_entries_bulk(zcli, resolved, entries, options)
        
        return None  # Success - output already displayed
        
    except PermissionError:
        zcli.display.error(MSG_PERMISSION_DENIED.format(path=resolved))
        return None
    except (OSError, IOError) as e:
        zcli.display.error(MSG_FILESYSTEM_ERROR.format(error=str(e)))
        return None
    except ValueError as e:
        zcli.display.error(MSG_FILESYSTEM_ERROR.format(error=str(e)))
        return None


# ============================================================================
# PRIVATE HELPERS
# ============================================================================

def _resolve_zpath(zcli: Any, target: str) -> Optional[Path]:
    """
    Resolve zPath syntax to filesystem Path object.
    
    Handles three path formats:
    1. Workspace-relative: @.src.components → workspace/src/components
    2. Absolute zPath: ~.Projects.myapp → /Users/name/Projects/myapp
    3. Regular path: ./src or /absolute/path
    
    Args:
        zcli: The zCLI instance for session access
        target: Target path string (may use zPath syntax)
    
    Returns:
        Path object if resolution successful, None if error (error displayed)
    
    Examples:
        >>> _resolve_zpath(zcli, "@.src")
        Path('/workspace/src')
        
        >>> _resolve_zpath(zcli, "~.Projects")
        Path('/Users/name/Projects')
        
        >>> _resolve_zpath(zcli, "./src")
        Path('./src')
    """
    try:
        if target.startswith(ZPATH_WORKSPACE_PREFIX):
            # Workspace-relative path: @.src.components
            workspace_str: str = zcli.session.get(SESSION_KEY_ZSPACE, DEFAULT_TARGET_DIR)
            workspace: Path = Path(workspace_str)
            
            # Remove @. prefix and split by .
            path_suffix: str = target[len(ZPATH_WORKSPACE_PREFIX):]
            if path_suffix:
                path_parts: List[str] = path_suffix.split(ZPATH_SEPARATOR)
                resolved: Path = workspace / "/".join(path_parts)
            else:
                resolved = workspace
            
            return resolved
            
        elif target.startswith(ZPATH_ABSOLUTE_PREFIX):
            # Absolute zPath: ~.Projects.myapp
            path_suffix = target[len(ZPATH_ABSOLUTE_PREFIX):]
            if path_suffix:
                path_parts = path_suffix.split(ZPATH_SEPARATOR)
                resolved = Path.home() / "/".join(path_parts)
            else:
                resolved = Path.home()
            
            return resolved
            
        else:
            # Regular filesystem path
            return Path(target)
            
    except (ValueError, OSError) as e:
        zcli.display.error(MSG_FILESYSTEM_ERROR.format(error=str(e)))
        return None


def _collect_entries(resolved: Path, options: Dict[str, bool]) -> List[Dict[str, Any]]:
    """
    Collect directory entries with metadata.
    
    Gathers all files and directories in the target path, optionally including
    subdirectories (recursive) and hidden files (all). Supports filtering by type.
    
    Args:
        resolved: Path object pointing to directory
        options: Command options dictionary (supports both modern and Unix flags)
    
    Returns:
        List of entry dictionaries with keys: name, type, path, size (for files)
    
    Raises:
        PermissionError: If directory cannot be read
        OSError: For other filesystem errors
    """
    entries: List[Dict[str, Any]] = []
    
    # Check for recursive option (modern: -deep, Unix: -r/-recursive)
    is_recursive: bool = (options.get(OPTION_DEEP, False) or 
                          options.get(OPTION_RECURSIVE, False) or 
                          options.get(OPTION_R, False))
    
    # Check for hidden files option (modern: -hidden, Unix: -a/-all)
    show_all: bool = (options.get(OPTION_HIDDEN, False) or 
                      options.get(OPTION_ALL, False) or 
                      options.get(OPTION_A, False))
    
    # Check for type filtering (modern only: -file, -dir/-folder)
    files_only: bool = options.get(OPTION_FILE, False)
    dirs_only: bool = (options.get(OPTION_DIR, False) or 
                       options.get(OPTION_FOLDER, False))
    
    if is_recursive:
        # Recursive listing
        for item in resolved.rglob("*"):
            rel_path: Path = item.relative_to(resolved)
            entry: Dict[str, Any] = _format_entry(item, str(rel_path))
            entries.append(entry)
    else:
        # Single level listing
        for item in sorted(resolved.iterdir()):
            entry = _format_entry(item, item.name)
            entries.append(entry)
    
    # Filter hidden files unless --hidden/-a flag
    if not show_all:
        entries = [e for e in entries if not e[DICT_KEY_NAME].startswith(".")]
    
    # Filter by type if requested
    if files_only:
        entries = [e for e in entries if e[DICT_KEY_TYPE] == ENTRY_TYPE_FILE]
    elif dirs_only:
        entries = [e for e in entries if e[DICT_KEY_TYPE] == ENTRY_TYPE_DIR]
    
    return entries


def _format_entry(path: Path, name: str) -> Dict[str, Any]:
    """
    Format a single directory entry with metadata.
    
    Creates a dictionary with entry information including name, type (dir/file),
    full path, and size (for files only).
    
    Args:
        path: Path object for the entry
        name: Display name (may be relative path for recursive listings)
    
    Returns:
        Dictionary with keys: name, type, path, size (optional)
    
    Examples:
        >>> _format_entry(Path("/workspace/src"), "src")
        {"name": "src", "type": "dir", "path": "/workspace/src"}
        
        >>> _format_entry(Path("/workspace/main.py"), "main.py")
        {"name": "main.py", "type": "file", "path": "/workspace/main.py", "size": 1234}
    """
    entry: Dict[str, Any] = {
        DICT_KEY_NAME: name,
        DICT_KEY_TYPE: ENTRY_TYPE_DIR if path.is_dir() else ENTRY_TYPE_FILE,
        DICT_KEY_PATH: str(path)
    }
    
    # Add file size for files
    if path.is_file():
        try:
            entry[DICT_KEY_SIZE] = path.stat().st_size
        except OSError:
            # If we can't get size, default to 0
            entry[DICT_KEY_SIZE] = 0
    
    return entry


def _display_entries_bulk(
    zcli: Any,
    path: Path,
    entries: List[Dict[str, Any]],
    options: Dict[str, bool]
) -> None:
    """
    Display directory entries using single bulk display.list() call.
    
    This function builds a formatted list of strings and displays them all at
    once using display.list() for efficiency. This is the critical architectural
    improvement over the old per-file display.text() approach.
    
    Args:
        zcli: The zCLI instance for display access
        path: Path object of the directory being listed
        entries: List of entry dictionaries from _collect_entries()
        options: Command options for formatting (long, etc.)
    
    Returns:
        None: Output displayed via display.list()
    
    Display Format:
        Directory: /path
        
          [DIR] dir1/
          [DIR] dir2/
          
          [FILE] file1.py    2.5KB
          [FILE] file2.txt   1.2KB
        
        Total: 2 dirs, 2 files
    """
    # Build formatted items list
    items: List[str] = []
    
    # Add header
    items.append(MSG_DIRECTORY_HEADER.format(icon=ICON_HEADER, path=path))
    items.append(DISPLAY_BLANK_LINE)
    
    # Handle empty directory
    if not entries:
        items.append(f"  {MSG_EMPTY_DIRECTORY}")
        zcli.display.list(items, style=DEFAULT_LIST_STYLE)
        return
    
    # Group by type
    dirs: List[Dict[str, Any]] = [e for e in entries if e[DICT_KEY_TYPE] == ENTRY_TYPE_DIR]
    files: List[Dict[str, Any]] = [e for e in entries if e[DICT_KEY_TYPE] == ENTRY_TYPE_FILE]
    
    # Check for long format (modern: -size, Unix: -l/-long)
    is_long_format: bool = (options.get(OPTION_SIZE, False) or 
                            options.get(OPTION_LONG, False) or 
                            options.get(OPTION_L, False))
    
    # Display directories first
    if dirs:
        for entry in dirs:
            dir_name: str = entry[DICT_KEY_NAME]
            items.append(f"  {ICON_DIRECTORY} {dir_name}{DISPLAY_DIR_SUFFIX}")
    
    # Add blank line between dirs and files if both exist
    if dirs and files:
        items.append(DISPLAY_BLANK_LINE)
    
    # Display files
    if files:
        for entry in files:
            file_name: str = entry[DICT_KEY_NAME]
            
            if is_long_format:
                # Long format with sizes
                size: int = entry.get(DICT_KEY_SIZE, 0)
                size_str: str = _format_size(size)
                items.append(f"  {ICON_FILE} {file_name:<{DEFAULT_NAME_WIDTH}} {size_str:>{DEFAULT_SIZE_WIDTH}}")
            else:
                # Simple format
                items.append(f"  {ICON_FILE} {file_name}")
    
    # Add summary
    items.append(DISPLAY_BLANK_LINE)
    items.append(MSG_TOTAL_SUMMARY.format(dirs=len(dirs), files=len(files)))
    
    # Single bulk display call ✅
    zcli.display.list(items, style=DEFAULT_LIST_STYLE)


def _format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Converts byte count to appropriate unit (B, KB, MB, GB) with precision.
    
    Args:
        size_bytes: File size in bytes
    
    Returns:
        Formatted size string (e.g., "2.5KB", "1.2MB")
    
    Examples:
        >>> _format_size(512)
        "512B"
        
        >>> _format_size(2048)
        "2.0KB"
        
        >>> _format_size(1536000)
        "1.5MB"
        
        >>> _format_size(2147483648)
        "2.0GB"
    """
    if size_bytes < SIZE_UNIT_KB:
        return f"{size_bytes}{SIZE_LABEL_BYTE}"
    elif size_bytes < SIZE_UNIT_MB:
        return f"{size_bytes / SIZE_UNIT_KB:.{SIZE_FORMAT_PRECISION}f}{SIZE_LABEL_KB}"
    elif size_bytes < SIZE_UNIT_GB:
        return f"{size_bytes / SIZE_UNIT_MB:.{SIZE_FORMAT_PRECISION}f}{SIZE_LABEL_MB}"
    else:
        return f"{size_bytes / SIZE_UNIT_GB:.{SIZE_FORMAT_PRECISION}f}{SIZE_LABEL_GB}"

