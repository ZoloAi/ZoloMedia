# zCLI/subsystems/zOpen/open_modules/open_paths.py

"""
zPath Resolution Module

This module provides zPath resolution functionality for the zOpen subsystem, translating
symbolic path notation (@, ~) into absolute filesystem paths.

Architecture Position:
    - Tier 1a (Foundation Module) of zOpen's 3-tier architecture
    - Provides path translation services for the facade layer

Key Features:
    - @ Symbol: Workspace-relative paths (requires active zSpace in session)
    - ~ Symbol: Absolute paths from root
    - Dot Notation: Converts dot-separated paths to filesystem paths
    - Validation: Ensures zPaths are well-formed before resolution
    - Error Handling: Defensive checks for missing workspace context

zPath Syntax:
    @.folder.subfolder.filename.ext  → {zSpace}/folder/subfolder/filename.ext
    ~.Users.username.file.txt        → /Users/username/file.txt
    @.README.md                       → {zSpace}/README.md

Integration Points:
    - zConfig: Session access for zSpace resolution
    - open_files: Resolved paths are passed to file opening handlers
    - zOpen facade: Primary entry point via handle()

Dependencies:
    - os: Path manipulation and filesystem operations
    - zConfig constants: SESSION_KEY_ZSPACE for session dict keys

Usage Example:
    from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZSPACE
    from zOS.L2_Core.k_zOpen.open_modules.open_paths import resolve_zpath, validate_zpath

    session = {SESSION_KEY_ZSPACE: "/home/user/project"}
    
    # Validate before resolving
    if validate_zpath("@.src.main.py"):
        path = resolve_zpath("@.src.main.py", session, logger)
        # Returns: "/home/user/project/src/main.py"

Version History:
    - v1.5.4: Extracted from monolithic zOpen.py, added industry-grade documentation
    - v1.5.4: Added type hints, constants, and validation helper
    - v1.5.4: Modernized session key access (SESSION_KEY_ZSPACE)

Author: zCLI Development Team
"""

from zOS import os, Optional, Any

# Import centralized session constants
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZSPACE
from .open_constants import (
    ZPATH_SEPARATOR,
    ZPATH_SYMBOL_ABSOLUTE,
    ZPATH_SYMBOL_WORKSPACE,
    _ERR_INVALID_ZPATH,
    _ERR_NO_WORKSPACE,
    _ERR_RESOLUTION_FAILED,
    _LOG_INVALID_FORMAT,
    _LOG_RESOLVED_SUCCESS,
    _LOG_RESOLVING_ZPATH,
    _LOG_WORKSPACE_MISSING,
    _ZPATH_MIN_PARTS,
)

# ═══════════════════════════════════════════════════════════════
# Module-Level Constants
# ═══════════════════════════════════════════════════════════════

# zPath Symbols

# Minimum zPath Components (symbol + name + extension)

# Error Messages

# Log Messages


# ═══════════════════════════════════════════════════════════════
# Public API Functions
# ═══════════════════════════════════════════════════════════════

def resolve_zpath(
    zpath: str,
    session: dict[str, Any],
    logger: Any
) -> Optional[str]:
    """
    Translate a zPath to an absolute filesystem path.

    This function parses a zPath (dot-separated symbolic path notation) and converts
    it to an absolute filesystem path. It handles both workspace-relative (@) and
    absolute (~) path symbols.

    Args:
        zpath: zPath string in dot notation (e.g., "@.folder.file.ext" or "~.Users.file.txt")
        session: zCLI session dictionary containing workspace and machine context
        logger: Logger instance for debug/error output

    Returns:
        Absolute filesystem path as string, or None if resolution fails

    Resolution Logic:
        1. Clean leading dots from zPath
        2. Split by dot separator
        3. Identify symbol (@ or ~) and determine base path
        4. Validate minimum component count
        5. Reconstruct filesystem path from components
        6. Return absolute path

    Symbol Handling:
        @ (Workspace-relative):
            - Requires active zSpace in session
            - Base path: session[SESSION_KEY_ZSPACE]
            - Example: "@.src.main.py" → "{workspace}/src/main.py"
            - Returns None if workspace not set

        ~ (Absolute):
            - Base path: os.path.sep (root directory)
            - Example: "~.Users.me.file.txt" → "/Users/me/file.txt"
            - Platform-independent (uses os.path.sep)

    Error Conditions:
        - Returns None if:
            - zPath has < 2 components (invalid format)
            - @ symbol used but no workspace set in session
            - Path reconstruction fails (exception during os.path.join)

    Integration Notes:
        - Called by zOpen facade's handle() method
        - Resolved paths are passed to open_files.open_file()
        - Uses centralized SESSION_KEY_ZSPACE constant
        - Defensive error handling with logger output

    Example Usage:
        >>> session = {SESSION_KEY_ZSPACE: "/home/user/project"}
        >>> resolve_zpath("@.README.md", session, logger)
        "/home/user/project/README.md"

        >>> resolve_zpath("~.etc.hosts", session, logger)
        "/etc/hosts"

        >>> resolve_zpath("@.src.utils.helper.py", session, logger)
        "/home/user/project/src/utils/helper.py"

    See Also:
        - validate_zpath(): Pre-validation helper for zPath format
        - open_files.open_file(): Consumer of resolved paths
        - SESSION_KEY_ZSPACE: Centralized session key constant

    Version: v1.5.4
    """
    logger.debug(_LOG_RESOLVING_ZPATH, zpath)

    # Clean the zPath (remove leading dots)
    zpath_cleaned = zpath.lstrip(ZPATH_SEPARATOR)
    parts = zpath_cleaned.split(ZPATH_SEPARATOR)

    # Determine base path from symbol
    if parts[0] == ZPATH_SYMBOL_WORKSPACE:
        # Workspace-relative path
        base = session.get(SESSION_KEY_ZSPACE) or ""
        if not base:
            logger.error(_ERR_NO_WORKSPACE + ": %s", zpath)
            return None
        parts = parts[1:]  # Remove symbol from parts

    elif parts[0] == ZPATH_SYMBOL_ABSOLUTE:
        # Absolute path from root
        base = os.path.sep
        parts = parts[1:]  # Remove symbol from parts

    else:
        # No recognized symbol, treat as normal filesystem path
        base = ""

    # Validate minimum parts count (name + extension)
    if len(parts) < _ZPATH_MIN_PARTS:
        logger.error(_ERR_INVALID_ZPATH + ": %s", zpath)
        return None

    # Reconstruct filesystem path from components
    try:
        # Last two parts are filename and extension
        *dirs, filename, ext = parts
        file_name = f"{filename}{ZPATH_SEPARATOR}{ext}"

        # Build absolute path
        resolved_path = os.path.abspath(os.path.join(base, *dirs, file_name))
        logger.debug(_LOG_RESOLVED_SUCCESS, zpath, resolved_path)
        return resolved_path

    except Exception as e:
        logger.error(_ERR_RESOLUTION_FAILED + " '%s': %s", zpath, e)
        return None


def validate_zpath(zpath: str) -> bool:
    """
    Validate zPath format before attempting resolution.

    This helper function performs basic format validation on a zPath string,
    checking for the presence of required components without accessing the
    session or performing full resolution.

    Args:
        zpath: zPath string to validate

    Returns:
        True if zPath format is valid, False otherwise

    Validation Rules:
        - Must contain at least 2 parts after symbol (name + extension)
        - Must start with recognized symbol (@ or ~) after cleaning dots
        - Must use dot separator notation

    Example Usage:
        >>> validate_zpath("@.README.md")
        True

        >>> validate_zpath("@.file")  # Missing extension
        False

        >>> validate_zpath("invalid")  # No symbol
        False

    Note:
        This function only validates format, not context (e.g., workspace availability).
        Use resolve_zpath() for full resolution with context validation.

    Version: v1.5.4
    """
    # Clean and split zPath
    zpath_cleaned = zpath.lstrip(ZPATH_SEPARATOR)
    parts = zpath_cleaned.split(ZPATH_SEPARATOR)

    # Check for valid symbol
    if not parts or parts[0] not in (ZPATH_SYMBOL_WORKSPACE, ZPATH_SYMBOL_ABSOLUTE):
        return False

    # Check minimum parts count (symbol + name + extension)
    # After removing symbol, should have at least 2 parts remaining
    return len(parts) >= (_ZPATH_MIN_PARTS + 1)


# ═══════════════════════════════════════════════════════════════
# Module Exports
# ═══════════════════════════════════════════════════════════════

__all__ = [
    "resolve_zpath",    # Main zPath resolution function
    "validate_zpath",   # Format validation helper
]

