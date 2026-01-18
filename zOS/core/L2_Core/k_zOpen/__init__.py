# zCLI/subsystems/zOpen/__init__.py

"""
zOpen Subsystem - Package Root

This module serves as the package root for the zOpen subsystem, providing file and URL
opening functionality for the zCLI framework.

Architecture Position:
    - Tier 3 (Package Root) of zOpen's 3-tier architecture
    - Exposes zOpen class from Tier 2 (facade) to zCLI
    - Top-level entry point for the subsystem

3-Tier Architecture Summary:
    Tier 1: Foundation Modules (open_modules/)
        - open_paths.py: zPath resolution (@ and ~ symbols)
        - open_urls.py: URL opening in browsers
        - open_files.py: File opening by extension (HTML, text)
        - __init__.py: Package aggregator

    Tier 2: Facade (zOpen.py)
        - zOpen class: Main interface
        - handle() method: Request parsing, routing, hook execution
        - Delegates to Tier 1 modules

    Tier 3: Package Root (THIS FILE)
        - Exports zOpen class to zCLI
        - Package-level documentation
        - Integration guidance

Key Features:
    - Mode-Agnostic: Works in both Terminal and Bifrost modes
    - Type Detection: Automatically identifies URLs, zPaths, and local files
    - Extension Routing: Opens files based on extension (.html → browser, .txt → IDE)
    - Hook Support: Executes onSuccess/onFail callbacks via zFunc
    - Session Integration: Uses workspace and machine preferences from zConfig
    - Interactive Prompts: File creation and IDE selection via zDialog

Supported Operations:
    URL Opening:
        - http:// and https:// URLs
        - www. prefix auto-detection
        - User's preferred browser (from session)
        - System default browser fallback
        - Display URL info if browser fails

    zPath Resolution:
        - @ Symbol: Workspace-relative paths (@.folder.file.ext)
        - ~ Symbol: Absolute paths (~.Users.username.file.txt)
        - Automatic translation to filesystem paths
        - Opens resolved file based on extension

    File Opening:
        - HTML/HTM: Opens in browser (file:// URL)
        - Text formats: Opens in IDE (.txt, .md, .py, .js, .json, .yaml, .yml)
        - IDE preference from session (zMachine.ide)
        - Interactive IDE selection if not configured (via zDialog)
        - File creation prompt for missing files (via zDialog)
        - Content display fallback if IDE fails

Integration with zCLI:
    Initialized in zCLI.__init__() (line ~210):
        from zOS.L2_Core.k_zOpen import zOpen
        self.open = zOpen(self)

    Called from zDispatch (dispatch_launcher.py):
        # Line 424-428: zOpen() command detection and routing
        if zHorizontal.startswith("zOpen("):
            return self.zcli.open.handle(zHorizontal)

    Dependencies:
        - zConfig: Session access (workspace, IDE, browser preferences)
        - zDisplay: Mode-agnostic output and status messages
        - zFunc: Hook callback execution (onSuccess/onFail)
        - zDialog: Interactive prompts (file creation, IDE selection)

Usage Example:
    # From zDispatch (typical usage)
    result = zcli.open.handle("zOpen(/path/to/file.txt)")

    # From custom code (direct usage)
    from zOS.subsystems.zOpen import zOpen
    
    zopen = zOpen(zcli)
    
    # Open local file
    result = zopen.handle("zOpen(/path/to/script.py)")
    # Opens in IDE (e.g., Cursor, VS Code, nano)
    
    # Open URL
    result = zopen.handle("zOpen(https://github.com)")
    # Opens in browser
    
    # Open with hooks
    result = zopen.handle({
        "zOpen": {
            "path": "/path/to/file.txt",
            "onSuccess": "log_success()",
            "onFail": "log_error()"
        }
    })

Return Values:
    - "zBack": Opening successful, return to previous screen
    - "stop": Opening failed or user cancelled
    - Hook result: If onSuccess/onFail hook executes

Future Extensions:
    The modular architecture supports easy addition of new file types:
    - Documents: PDF, Word, Excel, PowerPoint
    - Images: PNG, JPG, GIF, SVG (with Bifrost integration)
    - Archives: ZIP, TAR, GZ (with extraction options)
    - Media: Audio and video files (with player integration)

    To add support:
    1. Update open_files.py with new extension constants
    2. Add handler function (e.g., _open_document(), _open_image())
    3. Update routing logic in open_file()
    4. Document in module and package docstrings

Version History:
    - v1.5.4: Refactored from 2-tier to 3-tier modular architecture
    - v1.5.4: Enhanced documentation to industry-grade standards
    - v1.5.4: Added type hints and constants throughout

Author: zCLI Development Team
"""

from .zOpen import zOpen  # Main facade class (Tier 2) # noqa: F401

# ═══════════════════════════════════════════════════════════════
# Public API Exports
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'zOpen',  # Main facade class for file/URL opening operations
]
