# zCLI/subsystems/zDispatch/__init__.py

"""
zDispatch Package - Core Command Dispatch Subsystem.

This package provides the zDispatch subsystem for command dispatch and routing
in zCLI, implementing a Facade pattern to orchestrate command execution with
flexible modifier support (^ ~ * !).

Package Architecture:
    The zDispatch package follows a hierarchical facade design:
    
    Top Level (Facade):
    - zDispatch: Main facade class orchestrating ModifierProcessor and CommandLauncher
    - handle_zDispatch: Standalone convenience function for external callers
    
    Component Level (dispatch_modules/):
    - CommandLauncher: Executes commands in various formats (zFunc, zWizard, etc.)
    - ModifierProcessor: Handles prefix (^~) and suffix (*!) modifiers

Facade Pattern:
    zDispatch acts as a simplified interface to the complex command dispatch subsystem:
    
    1. Component Creation:
       - Initialize ModifierProcessor and CommandLauncher
       - Store references to zCLI, session, and logger
    
    2. Orchestration:
       - Check for modifiers (prefix + suffix detection)
       - Route to ModifierProcessor if modifiers detected
       - Route to CommandLauncher if no modifiers
    
    3. Result Handling:
       - Return processed result to caller
       - Handle mode-specific returns (Terminal vs. Bifrost)

Exported Components:
    - zDispatch: Main facade class for command dispatch
    - handle_zDispatch: Standalone function for convenience API

Forward Dependencies:
    The dispatch subsystem integrates with 7 future subsystems:
    - zNavigation (Week 6.7): Menu creation and navigation
    - zParser (Week 6.8): Plugin invocation resolution
    - zLoader (Week 6.9): zUI file loading
    - zFunc (Week 6.10): Function execution
    - zDialog (Week 6.11): Interactive forms
    - zWizard (Week 6.14): Multi-step workflows
    - zData (Week 6.16): Data management and CRUD operations

Usage:
    # Import entire package
    from zOS.L2_Core import e_zDispatch as dispatch_module
    dispatch = dispatch_module.zDispatch(zcli)
    
    # Import specific components
    from zOS.L2_Core.e_zDispatch import zDispatch, handle_zDispatch
    dispatch = zDispatch(zcli)
    result = handle_zDispatch("action", cmd, zcli=zcli)
    
    # Typical usage in zCLI
    result = zcli.dispatch.handle("action", {"zFunc": "my_function"})
    
    # With modifiers
    result = zcli.dispatch.handle("^save", {"zFunc": "save"})  # Bounce back
    result = zcli.dispatch.handle("menu*", menu_dict)          # Create menu

Integration:
    - zConfig: Session constants (future: SESSION_KEY_ZMODE)
    - zDisplay: UI output (zDeclare) and user interaction
    - zSession: Context passing for mode detection
    - zAuth: Authentication state passed through context

Thread Safety:
    - All components rely on thread-safe instances from zCLI
    - No internal state mutation during dispatch
    - Stateless command execution

Version History:
    - v1.5.4: Initial bottom-up refactoring
      * Renamed from zDispatch/ to zDispatch/ (already correct)
      * Renamed zDispatch_modules/ to dispatch_modules/
      * All internal files renamed to dispatch_* prefix
      * Industry-grade upgrade (D/D+ → A+ for all components)
      * Added 20-40+ constants per file
      * 100% type hint coverage across all files
      * Comprehensive documentation
      * DRY refactoring with helper methods
      * Forward dependency documentation (17 TODOs for 7 subsystems)
"""

# ============================================================================
# PACKAGE METADATA
# ============================================================================

__version__ = "1.5.4"
__author__ = "Zolo"
__description__ = "Core command dispatch and routing subsystem for zCLI"

# ============================================================================
# FACADE IMPORTS
# ============================================================================

# Facade components (main entry points)
from .zDispatch import zDispatch            # Main facade class
from .zDispatch import handle_zDispatch    # Standalone convenience function

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    'zDispatch',           # Main facade class for command dispatch
    'handle_zDispatch',    # Standalone function for convenience API
]
