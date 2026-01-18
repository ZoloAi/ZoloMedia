# zCLI/subsystems/zNavigation/__init__.py

"""
zNavigation - Unified Navigation System Subsystem.

This package provides comprehensive navigation functionality for zCLI,
including menu creation, breadcrumb management, navigation state tracking,
and inter-file linking. The subsystem follows a facade pattern with the
zNavigation class serving as the primary interface.

Subsystem Overview
------------------
The zNavigation subsystem enables:

- **Menu Creation**: Interactive menus with Terminal/Bifrost support
- **Breadcrumb Trails**: Navigation history with "Back" functionality
- **Navigation State**: Location tracking and history management
- **Inter-file Linking**: zLink expressions with RBAC permissions

Architecture
------------
The subsystem implements a facade pattern with component delegation:

**zNavigation Facade:**
  - Primary interface for external clients
  - Delegates to 4 specialized components
  - Provides clean, consistent public API
  - Maintains backward compatibility (standalone functions)

**Specialized Components:**
  1. MenuSystem - Menu creation and interaction
  2. Breadcrumbs - Navigation trail management
  3. Navigation - State and history tracking
  4. Linking - Inter-file navigation (zLink)

Package Exports
---------------
This package exports three items for external use:

**Primary Export (Facade):**

zNavigation : class
    Main facade class providing navigation operations
    
    Public methods:
    - create(options, title, allow_back, walker) → str
    - select(options, prompt, walker) → str
    - handle_zCrumbs(zBlock, zKey, walker) → Any
    - handle_zBack(show_banner, walker) → str
    - navigate_to(target, context) → Dict
    - get_current_location() → Dict
    - get_navigation_history() → List
    - handle_zLink(zHorizontal, walker) → str

**Backward Compatibility Exports (Standalone Functions):**

handle_zLink(zHorizontal, walker) : function
    Standalone function for Walker integration
    Delegates to zNavigation facade internally

handle_zCrumbs(zBlock, zKey, walker) : function
    Standalone function for Walker integration
    Delegates to zNavigation facade internally

Usage
-----
The recommended usage is via the zCLI core facade::

    # Initialize zCLI (automatic in production)
    zcli = zCLI()
    
    # Use navigation via facade (recommended)
    choice = zcli.navigation.create(
        ["Settings", "Profile", "Logout"],
        title="Main Menu",
        walker=walker
    )
    
    # Handle breadcrumbs
    zcli.navigation.handle_zCrumbs("menu_block", "option_key", walker)
    
    # Navigate to location
    zcli.navigation.navigate_to("users.menu.list_users")

For legacy Walker integration (backward compatibility)::

    # Import standalone functions
    from zOS.L2_Core.f_zNavigation import handle_zLink, handle_zCrumbs
    
    # Use standalone functions (legacy)
    result = handle_zLink("zLink(path.to.file)", walker)
    handle_zCrumbs("block", "key", walker)

Integration
-----------
- **Parent**: zCLI core (zCLI.py)
- **Used By**: zDispatch (menu system), zWalker (navigation), external clients
- **Dependencies**: zDisplay, zSession, zParser, zLoader, zFunc

Layer Position
--------------
Layer 1, Position 4 (zNavigation)

See Also
--------
- zNavigation.py : Facade implementation
- navigation_modules/ : Component implementations
- zDispatch : Menu system integration (* modifier)
- zWalker : Navigation orchestration
"""

from zOS import List

from .zNavigation import zNavigation, handle_zLink, handle_zCrumbs

__all__: List[str] = [
    'zNavigation',
    'handle_zLink',
    'handle_zCrumbs',
]
