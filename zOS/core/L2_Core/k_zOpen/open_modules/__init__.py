# zCLI/subsystems/zOpen/open_modules/__init__.py

"""
zOpen Foundation Modules - Package Aggregator

This package aggregates the three foundation modules of the zOpen subsystem, providing
a centralized import point for path resolution, URL opening, and file opening functionality.

Architecture Position:
    - Tier 1d (Package Aggregator) of zOpen's 3-tier architecture
    - Consolidates Tier 1a-1c foundation modules
    - Provides clean public API to Tier 2 (facade)

Package Structure:
    open_modules/
    ├── __init__.py           # This file - Package aggregator
    ├── open_paths.py         # Tier 1a: zPath resolution
    ├── open_urls.py          # Tier 1b: URL opening handlers
    └── open_files.py         # Tier 1c: File opening handlers

Foundation Modules:
    Tier 1a - open_paths:
        - resolve_zpath(): Translate zPath notation to filesystem paths
        - validate_zpath(): Validate zPath format before resolution
        - Handles @ (workspace-relative) and ~ (absolute) symbols

    Tier 1b - open_urls:
        - open_url(): Open URLs in user's preferred or system default browser
        - Handles http/https URLs with browser preference
        - Fallback display for failed browser launches

    Tier 1c - open_files:
        - open_file(): Open local files based on extension
        - Routes to HTML (browser) or text (IDE) handlers
        - zDialog integration for file creation and IDE selection
        - Fallback content display for IDE failures

Public API Exports:
    From open_paths:
        - resolve_zpath: Main zPath resolution function
        - validate_zpath: zPath format validation

    From open_urls:
        - open_url: Main URL opening function

    From open_files:
        - open_file: Main file opening function

Integration Points:
    - Used by zOpen.py facade (Tier 2)
    - Each module is independently testable
    - Clear separation of concerns (paths, URLs, files)

Usage Example:
    # Import from aggregator (recommended)
    from zOS.L2_Core.k_zOpen.open_modules import resolve_zpath, open_url, open_file

    # Or import from specific modules (also valid)
    from zOS.L2_Core.k_zOpen.open_modules.open_paths import resolve_zpath
    from zOS.L2_Core.k_zOpen.open_modules.open_urls import open_url
    from zOS.L2_Core.k_zOpen.open_modules.open_files import open_file

    # Usage (typically called from zOpen facade)
    path = resolve_zpath("@.README.md", session, logger)
    result = open_file(path, session, display, dialog, logger)

Design Pattern:
    This aggregator follows the same pattern as:
    - zCLI.subsystems.zLoader.loader_modules
    - zCLI.subsystems.zFunc.zFunc_modules
    - zCLI.subsystems.zDialog.dialog_modules

    The pattern provides:
    - Centralized import point
    - Clean public API boundary
    - Flexibility for internal reorganization
    - Improved maintainability

Version History:
    - v1.5.4: Created as part of zOpen modular refactoring
    - v1.5.4: Industry-grade documentation and public API definition

Author: zCLI Development Team
"""

# Import from foundation modules
from .open_paths import resolve_zpath, validate_zpath  # noqa: F401
from .open_urls import open_url  # noqa: F401
from .open_files import open_file  # noqa: F401

# ═══════════════════════════════════════════════════════════════
# Public API Exports
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # zPath Resolution (Tier 1a)
    "resolve_zpath",   # Translate zPath to filesystem path
    "validate_zpath",  # Validate zPath format

    # URL Opening (Tier 1b)
    "open_url",        # Open URL in browser

    # File Opening (Tier 1c)
    "open_file",       # Open local file by extension
]

