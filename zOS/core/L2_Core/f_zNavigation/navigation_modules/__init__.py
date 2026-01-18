# zCLI/subsystems/zNavigation/navigation_modules/__init__.py

"""
zNavigation Modules Package - Unified Navigation System Components.

This package provides specialized components for the zNavigation subsystem,
organized into a three-tier architecture supporting menu creation, navigation
state management, breadcrumb trails, and inter-file linking.

Package Architecture
--------------------
The navigation_modules package is organized into three tiers:

**Tier 1 - Foundation Components (4 components)**

These components provide core navigation functionality:

1. **Breadcrumbs** (navigation_breadcrumbs.py)
   - Navigation trail management (zCrumbs)
   - "Back" functionality (zBack)
   - Session breadcrumb storage
   - UI file reloading based on breadcrumb state

2. **Navigation** (navigation_state.py)
   - Current navigation location tracking
   - Navigation history management (FIFO overflow)
   - Session state storage
   - Timestamp metadata for navigation events

3. **Linking** (navigation_linking.py)
   - Inter-file linking (zLink expressions)
   - RBAC permission checking for links
   - Session context updates (zVaFolder, zVaFile, zBlock)
   - zParser integration for expression evaluation

4. **MenuBuilder** (navigation_menu_builder.py)
   - Menu object construction from various sources
   - Static options, dynamic data, function-based menus
   - "Back" option injection management
   - zFunc integration for dynamic menu generation

**Tier 1 - Display Components (2 components)**

These components handle menu presentation and interaction:

5. **MenuRenderer** (navigation_menu_renderer.py)
   - Mode-agnostic menu rendering (Terminal/Bifrost)
   - Multiple display formats (full, simple, compact)
   - Breadcrumb integration
   - zDisplay delegation for output

6. **MenuInteraction** (navigation_menu_interaction.py)
   - User input handling for menu selections
   - Single choice, multiple choices, search functionality
   - Input validation and error handling
   - zDisplay delegation for input

**Tier 2 - Composition Component (1 component)**

This component orchestrates the display components:

7. **MenuSystem** (navigation_menu_system.py)
   - Orchestrates builder, renderer, and interaction components
   - Provides unified menu creation interface
   - Supports both navigation menus and simple selections
   - Maintains backward compatibility with legacy zMenu objects
   - Integrates with zDispatch (* modifier)

Component Dependencies
----------------------
MenuSystem (Tier 2)
  ├─→ MenuBuilder (Tier 1 - Foundation)
  ├─→ MenuRenderer (Tier 1 - Display)
  └─→ MenuInteraction (Tier 1 - Display)

External Dependencies:
  • Breadcrumbs → zSession (breadcrumb storage)
  • Navigation → zSession (navigation state)
  • Linking → zParser (zExpr_eval), zLoader (file loading), zWalker (orchestration)
  • MenuBuilder → zFunc (function-based menus)
  • MenuRenderer → zDisplay (mode-agnostic output)
  • MenuInteraction → zDisplay (user input)

Facade Integration
------------------
All components are designed to be accessed via the zNavigation facade, which
provides a clean, consistent public API:

    # Recommended: Use facade (from zOS.py)
    zcli.navigation.create(["Option A", "Option B"], title="Menu")
    zcli.navigation.navigate_to("path.to.file.block")
    zcli.navigation.add_crumb("Menu", "option_key")

Direct component usage is supported but not recommended for most use cases:

    # Advanced: Direct component usage (from navigation_modules)
    from zOS.L2_Core.f_zNavigation.navigation_modules import MenuSystem
    menu_system = MenuSystem(navigation)
    choice = menu_system.create(["A", "B"], walker=walker)

Usage Examples
--------------
Via Facade (Recommended)::

    # Create navigation menu with breadcrumb integration
    choice = zcli.navigation.create(
        ["Settings", "Profile", "Logout"],
        title="Main Menu",
        allow_back=True,
        walker=walker
    )

    # Navigate to a specific file/block
    zcli.navigation.navigate_to("users.menu.list_users")

    # Add breadcrumb for navigation trail
    zcli.navigation.add_crumb("Users Menu", "list_users_key")

Direct Component Usage (Advanced)::

    from zOS.L2_Core.f_zNavigation.navigation_modules import (
        MenuSystem, Breadcrumbs, Navigation, Linking
    )

    # Create menu system
    menu_system = MenuSystem(navigation)
    choice = menu_system.create(["A", "B"], walker=walker)

    # Manage breadcrumbs
    breadcrumbs = Breadcrumbs(navigation)
    breadcrumbs.handle_zCrumbs("users.menu", "option_key")

    # Handle inter-file linking
    linking = Linking(navigation)
    result = linking.handle("zLink(path.to.file.block)", walker=walker)

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Specialized Modules

Integration
-----------
- Parent: zNavigation facade (zNavigation.py)
- Used By: zCLI core, zDispatch (menu system)
- Uses: zSession, zDisplay, zParser, zLoader, zFunc, zWalker

See Also
--------
- zNavigation.py : Facade providing public API
- zDispatch : Integrates with menu system (* modifier)
- zSession : Stores breadcrumbs, navigation state
"""

from zOS import List

from .navigation_constants import *  # noqa: F403, F401
from .navigation_menu_system import MenuSystem
from .navigation_breadcrumbs import Breadcrumbs
from .navigation_state import Navigation
from .navigation_linking import Linking
from .navigation_menu_builder import MenuBuilder
from .navigation_menu_renderer import MenuRenderer
from .navigation_menu_interaction import MenuInteraction

__all__: List[str] = [
    'MenuSystem',
    'Breadcrumbs',
    'Navigation',
    'Linking',
    'MenuBuilder',
    'MenuRenderer',
    'MenuInteraction',
]
