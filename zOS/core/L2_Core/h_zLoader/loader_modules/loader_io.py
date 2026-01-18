# zCLI/subsystems/zLoader/loader_modules/loader_io.py

"""
Raw file I/O operations for zLoader subsystem.

This module provides the foundational file reading layer for the zLoader subsystem,
handling raw disk I/O operations with comprehensive error handling and optional
visual feedback integration.

Purpose
-------
The loader_io module serves as Tier 1 (Foundation) in the zLoader architecture,
providing a single, focused function for loading raw file content from the
filesystem. It abstracts away the complexities of file handling, encoding, and
error management, exposing a simple interface to higher-level loader components.

Architecture
------------
**Tier 1 - Foundation (File I/O)**
    - Position: Bottom-most layer of zLoader subsystem
    - Dependencies: None (pure file I/O using Python stdlib)
    - Used By: zLoader.py facade (line 59)
    - Purpose: Raw file content loading from disk

Key Design Decisions
--------------------
1. **UTF-8 Encoding**: All files are read with UTF-8 encoding, which is the
   standard for zCLI configuration files, UI definitions, and schema files.

2. **Comprehensive Error Handling**: Three specific exception types are caught
   and re-raised as RuntimeError with descriptive messages:
   - FileNotFoundError: File doesn't exist at specified path
   - PermissionError: Insufficient permissions to read file
   - Generic Exception: Any other I/O error

3. **Error Chaining**: Original exceptions are preserved using `raise ... from e`
   to maintain full traceback for debugging.

4. **Optional Display Integration**: The display parameter allows visual feedback
   in both Terminal and Bifrost modes, showing a "Reading" message during I/O.

5. **Logging Strategy**: Debug-level logging for normal operations (file open,
   bytes read), error-level logging for failures.

External Usage
--------------
**Used By**:
    - zCLI/subsystems/zLoader/zLoader.py (Line 59)
      Usage: zFile_raw = load_file_raw(zFilePath_identified, self.logger, self.display)
      Purpose: Load raw file content after cache miss (Priority 3 - Disk I/O)

Usage Examples
--------------
**Basic Usage** (without display feedback):
    >>> from zOS.L2_Core.h_zLoader.loader_modules import load_file_raw
    >>> logger = get_logger()
    >>> content = load_file_raw("/path/to/file.yaml", logger)
    >>> print(len(content))
    1234

**With Display Feedback** (Terminal/Bifrost modes):
    >>> from zOS.L2_Core.h_zLoader.loader_modules import load_file_raw
    >>> logger = get_logger()
    >>> display = zcli.display
    >>> content = load_file_raw("/path/to/file.yaml", logger, display)
    # Displays: "Reading" with SUBLOADER color in Terminal/Bifrost

**Error Handling**:
    >>> try:
    ...     content = load_file_raw("/nonexistent.yaml", logger)
    ... except RuntimeError as e:
    ...     print(f"Error: {e}")
    Error: Unable to load zFile (not found): /nonexistent.yaml

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 1 Foundation)
    - Tier 1: Foundation (File I/O) ← THIS MODULE
    - Tier 2: Cache Implementations (SystemCache, PinnedCache, SchemaCache, PluginCache)
    - Tier 3: Cache Orchestrator (Routes cache requests)
    - Tier 4: Package Aggregator (loader_modules/__init__.py)
    - Tier 5: Facade (zLoader.py)
    - Tier 6: Package Root (__init__.py)

Dependencies
------------
Internal:
    - None (Tier 1 - Foundation, no internal dependencies)

External:
    - Python stdlib: open() for file I/O
    - zCLI typing imports: Any, Optional (for type hints)

Performance Considerations
--------------------------
- **File Size**: This function loads the entire file into memory. Suitable for
  zCLI configuration files (typically < 100KB). Not suitable for large data files.
- **Encoding**: UTF-8 decoding is fast for ASCII-compatible content.
- **Error Handling**: Exception handling has minimal overhead for success path.

Thread Safety
-------------
This function is thread-safe as it uses the standard library's file I/O
operations, which are thread-safe in CPython. Each call operates independently
with its own file handle via the `with` statement.

See Also
--------
- zLoader.py: Main facade that calls this function
- CacheOrchestrator: Manages multi-tier caching before falling back to disk I/O
- loader_cache_system.py: System cache with mtime checking

Version History
---------------
- v1.5.4: Industry-grade upgrade (type hints, constants, comprehensive docs)
- v1.5.3: Original implementation (27 lines, basic error handling)
"""

from zOS import Any, Optional

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Display Configuration
COLOR_SUBLOADER: str = "SUBLOADER"
INDENT_IO: int = 2
STYLE_SINGLE: str = "single"
DISPLAY_MSG_READING: str = "Reading"

# File I/O Configuration
FILE_MODE_READ: str = "r"
FILE_ENCODING_UTF8: str = "utf-8"

# Error Messages (f-string templates)
ERROR_FILE_NOT_FOUND: str = "Unable to load zFile (not found): {path}"
ERROR_PERMISSION_DENIED: str = "Unable to load zFile (permission denied): {path}"
ERROR_GENERIC: str = "Unable to load zFile: {path}"

# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================

def load_file_raw(full_path: str, logger: Any, display: Optional[Any] = None) -> str:
    """
    Load raw file content from filesystem with comprehensive error handling.

    This function reads the entire contents of a file from disk, using UTF-8
    encoding, and returns it as a string. It provides detailed error handling
    for common file I/O issues and optional visual feedback via the display
    parameter.

    Args:
        full_path (str): Absolute path to the file to load. Must be a valid
            OS path to an existing, readable file.
        logger (Any): Logger instance for debug/error messages. Typically
            from zConfig.logger.
        display (Optional[Any], optional): Display instance for visual feedback
            in Terminal/Bifrost modes. If provided, shows "Reading" message
            during I/O operation. Defaults to None.

    Returns:
        str: Raw file content as a UTF-8 decoded string. Preserves all
            whitespace, newlines, and formatting from the original file.

    Raises:
        RuntimeError: Raised for any file I/O error, with specific messages:
            - "Unable to load zFile (not found): {path}" - File doesn't exist
            - "Unable to load zFile (permission denied): {path}" - No read access
            - "Unable to load zFile: {path}" - Any other I/O error
            
            Original exception is chained via `from e` for full traceback.

    Examples:
        Load a YAML file without display feedback:
            >>> logger = get_logger()
            >>> content = load_file_raw("/app/config.yaml", logger)
            >>> print(content[:50])
            'zType: zConfig\nversion: 1.0\nsettings:\n  debug: ...'

        Load a file with display feedback (Terminal/Bifrost modes):
            >>> logger = get_logger()
            >>> display = zcli.display
            >>> content = load_file_raw("/app/ui.yaml", logger, display)
            # Displays: "Reading" with SUBLOADER color, indent=2

        Handle file not found error:
            >>> try:
            ...     content = load_file_raw("/missing.yaml", logger)
            ... except RuntimeError as e:
            ...     print(e)
            Unable to load zFile (not found): /missing.yaml

    Notes:
        - Files are read with UTF-8 encoding (standard for zCLI files)
        - Entire file is loaded into memory (suitable for config/UI files)
        - File handle is automatically closed via context manager
        - Debug logging shows file path and bytes read on success
        - Error logging shows file path and error details on failure
    """
    logger.debug("Opening file: %s", full_path)

    if display:
        display.zDeclare(DISPLAY_MSG_READING, color=COLOR_SUBLOADER, indent=INDENT_IO, style=STYLE_SINGLE)

    try:
        with open(full_path, FILE_MODE_READ, encoding=FILE_ENCODING_UTF8) as f:
            zFile_raw = f.read()
        logger.debug("File read successfully (%d bytes)", len(zFile_raw))
    except FileNotFoundError as e:
        logger.error("File not found: %s", full_path)
        raise RuntimeError(ERROR_FILE_NOT_FOUND.format(path=full_path)) from e
    except PermissionError as e:
        logger.error("Permission denied: %s", full_path)
        raise RuntimeError(ERROR_PERMISSION_DENIED.format(path=full_path)) from e
    except Exception as e:
        logger.error("Failed to read file at %s: %s", full_path, e)
        raise RuntimeError(ERROR_GENERIC.format(path=full_path)) from e

    return zFile_raw


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = ["load_file_raw"]
