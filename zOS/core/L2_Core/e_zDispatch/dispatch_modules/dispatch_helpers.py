# zCLI/L2_Core/e_zDispatch/dispatch_modules/dispatch_helpers.py

"""
Shared Helper Utilities for zDispatch Subsystem.

This module provides reusable utility functions shared across dispatch components
(launcher, modifiers, facade). These helpers eliminate code duplication and ensure
consistent behavior across the dispatch subsystem.

Architecture:
    Tier: Foundation (Tier 0) - Pure utilities with no internal dependencies
    
    Components that use these helpers:
    - CommandLauncher (dispatch_launcher.py)
    - ModifierProcessor (dispatch_modifiers.py)
    - zDispatch facade (zDispatch.py)

Helper Functions:
    - is_bifrost_mode(): Check if session indicates Bifrost mode execution

Usage Examples:
    # From CommandLauncher
    from .dispatch_helpers import is_bifrost_mode
    
    if is_bifrost_mode(self.zcli.session):
        # Handle Bifrost-specific behavior
    
    # From ModifierProcessor
    from .dispatch_helpers import is_bifrost_mode
    
    if is_bifrost_mode(self.zcli.session):
        # Apply Bifrost-specific modifier logic

Integration:
    - zConfig: Uses SESSION_KEY_ZMODE constant for mode key
    - Session: Reads from zcli.session dict (canonical source of truth)
    - Mode Values: Uses MODE_BIFROST constant for comparison

Thread Safety:
    - All helpers are stateless functions (thread-safe)
    - No shared mutable state
    - Safe to call from any thread/context

Version History:
    - v1.5.6: Created during Phase 3.3.8 (zDispatch DRY extraction)
      * Extracted is_bifrost_mode() from 2 duplicate implementations
      * Fixed constant inconsistency (SESSION_KEY_ZMODE)
      * Established pattern for shared dispatch utilities
"""

from zOS import Any, Dict, Optional

# Import canonical constants from zConfig
from zOS.L1_Foundation.a_zConfig.zConfig_modules import SESSION_KEY_ZMODE

# Import mode constants from dispatch_constants
from .dispatch_constants import MODE_BIFROST


# ============================================================================
# Mode Detection Helpers
# ============================================================================

def is_bifrost_mode(session: Dict[str, Any]) -> bool:
    """
    Check if session indicates Bifrost mode execution.
    
    This helper provides a single, canonical way to check if the current
    execution context is in Bifrost mode (WebSocket/API mode) vs Terminal mode.
    
    Args:
        session: Session dictionary from zcli.session
    
    Returns:
        True if session mode is "zBifrost", False otherwise (defaults to Terminal)
    
    Examples:
        >>> # From any dispatch component
        >>> from .dispatch_helpers import is_bifrost_mode
        >>> 
        >>> if is_bifrost_mode(self.zcli.session):
        ...     # Bifrost mode: Return JSON data structures
        ...     return {"result": data, "status": "success"}
        >>> else:
        ...     # Terminal mode: Display to console
        ...     self.display.text("Success!")
        ...     return None
    
    Implementation Notes:
        - Mode is sourced from session[SESSION_KEY_ZMODE] (canonical source)
        - Uses constant SESSION_KEY_ZMODE from zConfig ("zMode")
        - Uses constant MODE_BIFROST from dispatch_constants ("zBifrost")
        - Gracefully handles missing zMode key (defaults to False/Terminal)
        - Case-sensitive mode comparison (exact match required)
        - No side effects (pure function)
    
    Design Rationale:
        - Single source of truth: session["zMode"] is the canonical mode location
        - Consistent API: All dispatch components use same mode check
        - Type safety: Uses constants instead of raw strings
        - Defensive: Handles missing keys gracefully
        - DRY compliance: Eliminates 2 duplicate implementations
    
    Related:
        - SESSION_KEY_ZMODE: Defined in zConfig (config_constants.py)
        - MODE_BIFROST: Defined in dispatch_constants.py
        - Mode set by: zBifrost (bridge_walker.py), config_session.py
    
    Thread Safety:
        - Read-only operation (no mutations)
        - No shared state
        - Safe to call from any thread
    """
    return session.get(SESSION_KEY_ZMODE) == MODE_BIFROST


# ============================================================================
# Future Helper Functions
# ============================================================================

# This module can be extended with additional shared helpers as needed:
#
# def is_terminal_mode(session: Dict[str, Any]) -> bool:
#     """Check if session is in Terminal mode."""
#     return session.get(SESSION_KEY_ZMODE) != MODE_BIFROST
#
# def get_current_mode(session: Dict[str, Any]) -> str:
#     """Get current session mode with default."""
#     return session.get(SESSION_KEY_ZMODE, MODE_TERMINAL)
#
# def validate_session(session: Dict[str, Any]) -> bool:
#     """Validate session has required keys."""
#     ...
