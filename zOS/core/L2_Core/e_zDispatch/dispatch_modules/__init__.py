# zCLI/subsystems/zDispatch/dispatch_modules/__init__.py

"""
zDispatch Modules Package - Command Dispatch Components.

This package provides the core components for command dispatch and routing in zCLI,
enabling flexible command execution with modifier support (^ ~ * !).

Package Architecture:
    The dispatch_modules package follows a two-component design:
    
    1. CommandLauncher (dispatch_launcher.py):
       - Foundation Tier (Tier 1)
       - Handles actual command execution
       - Supports multiple command formats (string, dict)
       - Routes to appropriate subsystems (zFunc, zWizard, zDialog, zData, etc.)
    
    2. ModifierProcessor (dispatch_modifiers.py):
       - Foundation Tier (Tier 1)
       - Handles prefix and suffix modifiers
       - Alters command behavior (bounce-back, menu creation, required, anchor)
       - Provides mode-specific returns (Terminal vs. Bifrost)

Component Dependencies:
    Tier 1 (Foundation - No dependencies):
    - CommandLauncher: Foundation for all command execution
    - ModifierProcessor: Foundation for all modifier processing

Exported Components:
    - CommandLauncher: Core command execution and routing
    - ModifierProcessor: Modifier detection and processing

Usage:
    # Import entire package
    from zOS.L2_Core.e_zDispatch import dispatch_modules
    launcher = dispatch_modules.CommandLauncher(dispatch)
    modifiers = dispatch_modules.ModifierProcessor(dispatch)
    
    # Import specific components
    from zOS.L2_Core.e_zDispatch.dispatch_modules import CommandLauncher, ModifierProcessor
    launcher = CommandLauncher(dispatch)
    modifiers = ModifierProcessor(dispatch)

Integration:
    - zConfig: Session and mode constants
    - zDisplay: UI output and user interaction
    - Forward Dependencies: 7 subsystems (zNavigation, zParser, zLoader, zFunc, zDialog, zWizard, zData)

Thread Safety:
    Both components rely on thread-safe instances from zCLI (logger, display, session).
    No internal state mutation during processing.

Version History:
    - v1.5.4: Initial bottom-up refactoring
      * Renamed from zDispatch_modules to dispatch_modules
      * All files renamed to dispatch_* prefix
      * Industry-grade upgrade (D → A+ for both components)
      * Added 40+ constants per file
      * 100% type hint coverage
      * Comprehensive documentation
"""

# ============================================================================
# PACKAGE METADATA
# ============================================================================

__version__ = "1.5.4"
__author__ = "Zolo"
__description__ = "Command dispatch and routing components for zCLI subsystem"

# ============================================================================
# COMPONENT IMPORTS (Tier 1 - Foundation)
# ============================================================================

# Layer 0: Constants (Foundation)
from .dispatch_constants import *  # Centralized constants for all dispatch modules

# Tier 1: Foundation Components (no internal dependencies)
from .dispatch_launcher import CommandLauncher      # Command execution & routing
from .dispatch_modifiers import ModifierProcessor  # Modifier detection & processing

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    'CommandLauncher',     # Command execution and routing
    'ModifierProcessor',   # Modifier detection and processing
]
