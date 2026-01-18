"""
navigation_helpers.py

Shared helper functions for the zNavigation subsystem.

This module provides common utility functions used across multiple navigation
modules to eliminate code duplication and centralize navigation logic.

Architecture:
- DRY helpers extracted during Phase 3.4.8 cleanup
- Shared across navigation_linking, navigation_breadcrumbs, etc.
- Single source of truth for common patterns

Dependencies:
- typing (Python standard library)
- zCLI.L1_Foundation.a_zConfig (session keys)

Created: Phase 3.4.8 - Extract DRY Helpers
"""

from zOS import Any, Dict


def reload_current_file(walker: Any) -> Dict[str, Any]:
    """
    Reload the current file from session using zLoader.
    
    This helper encapsulates the common pattern of reloading a file based
    on the current session state (zFolder, zFile, zBlock). It handles both
    walker.loader and walker.zcli.loader access patterns.
    
    The loader.handle(None) call triggers session-based file resolution,
    which loads the file currently referenced in the session variables
    (SESSION_KEY_ZVAFOLDER, SESSION_KEY_ZVAFILE).
    
    Args:
        walker: The zWalker instance with loader and session access
    
    Returns:
        Parsed file dictionary with zBlocks as keys
    
    Example:
        ```python
        # After updating session to point to a new file
        walker.session[SESSION_KEY_ZVAFILE] = 'zUI.zVaF'
        
        # Reload the file to get its parsed content
        zFile_parsed = reload_current_file(walker)
        block_dict = zFile_parsed.get('Hero_Section', {})
        ```
    
    Usage Locations:
    - navigation_linking.py: _restore_bounce_back() - reload source after bounce-back
    - navigation_breadcrumbs.py: _reload_file_after_back() - reload after zBack navigation
    
    Pattern Replaced:
        ```python
        if hasattr(walker, "loader"):
            zFile_parsed = walker.loader.handle(None)
        else:
            zFile_parsed = walker.zcli.loader.handle(None)
        ```
    """
    # Handle both walker.loader and walker.zcli.loader access patterns
    if hasattr(walker, "loader"):
        return walker.loader.handle(None)
    else:
        return walker.zcli.loader.handle(None)


# Export public API
__all__ = [
    'reload_current_file',
]
