# zCLI/subsystems/zNavigation/navigation_modules/navigation_menu_system.py

"""
Unified Menu System for zNavigation - Composition Orchestrator.

This module provides the MenuSystem class, which orchestrates menu creation,
rendering, and interaction through composition of specialized components. It acts
as the primary interface for menu operations in the zNavigation subsystem.

Architecture
------------
The MenuSystem class follows the Composition Pattern, delegating to three
specialized components:

1. **MenuBuilder** (navigation_menu_builder.py)
   - Constructs menu objects from various input formats
   - Handles static options, dynamic data, and function-based menus
   - Manages "Back" option injection

2. **MenuRenderer** (navigation_menu_renderer.py)
   - Renders menu objects in various display formats
   - Supports mode-agnostic output (Terminal/Bifrost)
   - Handles full, simple, and compact rendering strategies

3. **MenuInteraction** (navigation_menu_interaction.py)
   - Handles user input and menu selection
   - Supports single choice, multiple choices, and search
   - Validates user input with error handling

Composition Flow
----------------
Each public method follows a consistent delegation pattern::

    1. Retrieve display adapter (walker or zcli)
    2. Display declaration banner
    3. Delegate to builder → construct menu object
    4. Delegate to renderer → display menu
    5. Delegate to interaction → get user choice
    6. Return selected choice

This pattern ensures clean separation of concerns and maintainability.

Public Methods
--------------
create(options, title=None, allow_back=True, walker=None)
    Full-featured menu creation with navigation support
    - Used for primary navigation menus
    - Supports "Back" option for navigation
    - Integrates with breadcrumb system

select(options, prompt="Select option", walker=None)
    Simple selection menu without navigation features
    - Used for quick selections
    - No "Back" option
    - Simplified display

handle(zMenu_obj, walker=None)
    Legacy menu handler for backward compatibility
    - Supports old zMenu object format
    - Maintains anchor mode logic
    - Graceful migration path

zDispatch Integration
---------------------
The create() method is called from dispatch_modifiers.py for the * (menu) modifier.

**Call site (dispatch_modifiers.py, line 413):**
    self.zcli.navigation.create(
        zHorizontal,                   # Menu options
        allow_back=not is_anchor,      # Anchor mode control
        walker=walker                  # Walker instance
    )

**Signature alignment:**
    def create(self, options, title=None, allow_back=True, walker=None)

**Parameter mapping:**
- zHorizontal → options (first positional)
- title → None (default, not passed from dispatch)
- allow_back=not is_anchor → allow_back (named arg)
- walker=walker → walker (named arg)

**Verification:** ✅ Perfect alignment confirmed during Week 6.7.8 refactor

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Tier 2 (Composition)

Integration
-----------
- Called by: zNavigation facade (public API)
- Uses: MenuBuilder, MenuRenderer, MenuInteraction
- Display: Via walker.display or zcli.display
- Logging: Debug for legacy operations

Usage Examples
--------------
Create a navigation menu::

    menu_system = MenuSystem(navigation)
    choice = menu_system.create(
        options=["Settings", "Profile", "Logout"],
        title="Main Menu",
        allow_back=True,
        walker=walker
    )

Simple selection menu::

    choice = menu_system.select(
        options=["Option A", "Option B", "Option C"],
        prompt="Choose an option",
        walker=walker
    )

Legacy menu handling::

    zMenu_obj = {
        "zBlock": "MainMenu",
        "zKey": "menu_key",
        "zHorizontal": ["Item 1", "Item 2"],
        "is_anchor": False
    }
    choice = menu_system.handle(zMenu_obj, walker)

Module Constants
----------------
DISPLAY_* : str
    Display messages and styles
NAV_* : str
    Navigation values (e.g., NAV_ZBACK)
LOG_* : str
    Log message templates
"""

from zOS import Any, Dict, List, Optional, Union

from .navigation_menu_builder import MenuBuilder
from .navigation_menu_renderer import MenuRenderer
from .navigation_menu_interaction import MenuInteraction
from .navigation_constants import (
    _DISPLAY_MSG_CREATE,
    _DISPLAY_MSG_SELECT,
    _DISPLAY_MSG_HANDLE,
    _DISPLAY_MSG_RETURN,
    _DISPLAY_STYLE_FULL,
    _DISPLAY_STYLE_SINGLE,
    _DISPLAY_STYLE_TILDE,
    _DISPLAY_INDENT_MENU,
    NAV_ZBACK,
    _LOG_ZMENU_OBJECT,
    _LOG_ANCHOR_ACTIVE,
    _LOG_MENU_OPTIONS,
    _LOG_MENU_SELECTED,
)

# Dict Keys (for legacy handle method - not in constants as they're legacy-specific)
DICT_KEY_ZBLOCK: str = "zBlock"
DICT_KEY_ZKEY: str = "zKey"
DICT_KEY_ZHORIZONTAL: str = "zHorizontal"
DICT_KEY_IS_ANCHOR: str = "is_anchor"

# Dict Keys (for menu object from builder.build())
DICT_KEY_OPTIONS: str = "options"
DICT_KEY_ALLOW_BACK: str = "allow_back"
DICT_KEY_METADATA: str = "metadata"
DICT_KEY_TITLE: str = "title"


# ============================================================================
# MenuSystem Class
# ============================================================================

class MenuSystem:
    """
    Unified menu system orchestrator for zNavigation.
    
    Orchestrates menu operations through composition of specialized components:
    MenuBuilder (construction), MenuRenderer (display), and MenuInteraction (input).
    Provides a clean, consistent interface for menu creation and selection.
    
    Attributes
    ----------
    navigation : Any
        Reference to parent navigation system
    zcli : Any
        Reference to zCLI core instance
    logger : Any
        Logger instance for menu operations
    builder : MenuBuilder
        Menu construction component
    renderer : MenuRenderer
        Menu rendering component
    interaction : MenuInteraction
        Menu interaction component
    
    Methods
    -------
    create(options, title=None, allow_back=True, walker=None)
        Create full-featured navigation menu
    select(options, prompt="Select option", walker=None)
        Create simple selection menu
    handle(zMenu_obj, walker=None)
        Handle legacy zMenu object format
    
    Private Methods
    ---------------
    _get_display(walker)
        Get display adapter from walker or zcli (DRY helper)
    
    Examples
    --------
    Create navigation menu::
    
        menu_system = MenuSystem(navigation)
        choice = menu_system.create(
            ["Settings", "Profile", "Logout"],
            title="Main Menu",
            walker=walker
        )
    
    Simple selection::
    
        choice = menu_system.select(
            ["Red", "Green", "Blue"],
            prompt="Choose color",
            walker=walker
        )
    
    Legacy support::
    
        zMenu_obj = {
            "zBlock": "Menu",
            "zKey": "key",
            "zHorizontal": ["A", "B"],
            "is_anchor": False
        }
        choice = menu_system.handle(zMenu_obj, walker)
    
    Integration
    -----------
    - Parent: zNavigation facade
    - Components: MenuBuilder, MenuRenderer, MenuInteraction
    - Display: Via walker or zcli
    - zDispatch: create() called from dispatch_modifiers.py (* modifier)
    """

    # Class-level type declarations
    navigation: Any  # Navigation system reference
    zcli: Any  # zCLI core instance
    logger: Any  # Logger instance
    builder: MenuBuilder  # Menu builder component
    renderer: MenuRenderer  # Menu renderer component
    interaction: MenuInteraction  # Menu interaction component

    def __init__(self, navigation: Any) -> None:
        """
        Initialize menu system with composition components.
        
        Args
        ----
        navigation : Any
            Parent navigation system instance
        
        Notes
        -----
        Initializes the three composition components (builder, renderer, interaction)
        which handle menu construction, display, and user input respectively. This
        composition pattern ensures clean separation of concerns.
        """
        self.navigation = navigation
        self.zcli = navigation.zcli
        self.logger = navigation.logger

        # Initialize menu components via composition
        self.builder = MenuBuilder(self)
        self.renderer = MenuRenderer(self)
        self.interaction = MenuInteraction(self)

    def create(
        self,
        options: Any,
        title: Optional[str] = None,
        allow_back: bool = True,
        walker: Optional[Any] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Create and display a menu, return user choice.
        
        Full-featured menu creation with navigation support. Builds menu object,
        renders it via display adapter, and captures user selection. Supports
        "Back" option for navigation and integrates with breadcrumb system.
        
        **Delta Link Support (v1.5.9):**
        If user selects an option with $ prefix (e.g., "$zAbout"), returns a
        zLink dict for same-file navigation instead of a raw string.
        
        Args
        ----
        options : Any
            List of menu options or dict with options
        title : Optional[str], default=None
            Optional menu title
        allow_back : bool, default=True
            Whether to add "Back" option to menu
        walker : Optional[Any], default=None
            Optional walker instance for display context
        
        Returns
        -------
        Union[str, Dict[str, Any]]
            - str: Selected option string (or NAV_ZBACK if back chosen)
            - Dict: zLink dict for same-file navigation ($ prefix)
        
        Examples
        --------
        Basic navigation menu::
        
            choice = menu_system.create(
                ["Settings", "Profile", "Logout"],
                title="Main Menu",
                walker=walker
            )
            # User sees: Main Menu with Back option
        
        Menu without Back option (anchor mode)::
        
            choice = menu_system.create(
                ["Yes", "No"],
                title="Confirm Action",
                allow_back=False,
                walker=walker
            )
            # User sees: No Back option (forced choice)
        
        Called from zDispatch (dispatch_modifiers.py)::
        
            # * modifier triggers menu creation
            # ~* modifier creates anchor menu (no back)
            result = self.zcli.navigation.create(
                zHorizontal,                   # Options
                allow_back=not is_anchor,      # Anchor control
                walker=walker
            )
        
        Notes
        -----
        - **Display Declaration**: Shows "zNavigation Menu Create" banner
        - **Composition Flow**: builder → renderer → interaction
        - **Mode-Agnostic**: Works in Terminal and Bifrost modes
        - **zDispatch Integration**: Called for * modifier (verified Week 6.7.8)
        
        Delegation Chain
        ----------------
        1. Get display adapter (_get_display)
        2. Display declaration banner
        3. Builder: Construct menu object
        4. Renderer: Display menu to user
        5. Interaction: Capture user choice
        6. Return selected option
        """
        # Get display adapter
        display = self._get_display(walker)
        
        # Display declaration
        display.zDeclare(
            _DISPLAY_MSG_CREATE,
            color=self.navigation.mycolor,
            indent=_DISPLAY_INDENT_MENU,
            style=_DISPLAY_STYLE_FULL
        )

        # Build menu object
        menu_obj = self.builder.build(options, title, allow_back)
        
        # ════════════════════════════════════════════════════════════
        # BIFROST MODE: Emit zMenu event via zDisplay
        # ════════════════════════════════════════════════════════════
        # In Bifrost mode, we emit a zMenu display event that the
        # frontend will handle. The frontend renders an interactive
        # menu and sends back the user's selection.
        from zOS.L1_Foundation.a_zConfig.zConfig_modules import ZMODE_ZBIFROST
        mode = self.zcli.session.get("zMode", "Terminal")
        
        if mode == ZMODE_ZBIFROST:
            self.logger.debug("[MenuSystem] Bifrost mode detected - emitting zMenu event")
            
            # Prepare menu data for frontend
            # Note: menu_obj from builder.build() uses "options" key, not "zHorizontal"
            menu_data = {
                "options": menu_obj[DICT_KEY_OPTIONS],
                "title": title,
                "allow_back": menu_obj[DICT_KEY_ALLOW_BACK],
                "metadata": menu_obj.get(DICT_KEY_METADATA, {})
            }
            
            # Emit via zDisplay (uses send_gui_event which handles buffering + broadcast)
            if hasattr(self.zcli, 'display') and hasattr(self.zcli.display, 'primitives'):
                self.zcli.display.primitives.send_gui_event('zMenu', menu_data)
                self.logger.info("[MenuSystem] ✅ zMenu event emitted to Bifrost frontend")
            
            # Return None - Bifrost will handle rendering and user interaction
            # The walker will receive the selection via a separate WebSocket event
            return None
        
        # ════════════════════════════════════════════════════════════
        # TERMINAL MODE: Render and block for user input
        # ════════════════════════════════════════════════════════════
        # Render menu (breadcrumbs displayed internally by renderer)
        self.renderer.render(menu_obj, display)
        
        # Get user interaction
        choice = self.interaction.get_choice(menu_obj, display)
        
        return choice

    def select(
        self,
        options: List[str],
        prompt: str = "Select option",
        walker: Optional[Any] = None
    ) -> str:
        """
        Simple selection menu without complex navigation.
        
        Simplified menu for quick selections. No "Back" option, no navigation
        features. Used for straightforward choices where navigation is not needed.
        
        Args
        ----
        options : List[str]
            List of options to select from
        prompt : str, default="Select option"
            Prompt text to display
        walker : Optional[Any], default=None
            Optional walker instance for display context
        
        Returns
        -------
        str
            Selected option string
        
        Examples
        --------
        Color selection::
        
            color = menu_system.select(
                ["Red", "Green", "Blue"],
                prompt="Choose a color",
                walker=walker
            )
            # User sees: Simple list, no Back option
        
        Quick yes/no::
        
            answer = menu_system.select(
                ["Yes", "No"],
                prompt="Continue?",
                walker=walker
            )
        
        Data source selection::
        
            source = menu_system.select(
                ["Database", "CSV", "API"],
                prompt="Select data source",
                walker=walker
            )
        
        Notes
        -----
        - **No Back Option**: allow_back hardcoded to False
        - **Simpler Display**: Uses single-line style
        - **Use Case**: Quick selections without navigation
        
        Delegation Chain
        ----------------
        1. Get display adapter (_get_display)
        2. Display declaration banner (single style)
        3. Builder: Construct simple menu (allow_back=False)
        4. Renderer: Display menu to user
        5. Interaction: Capture user choice
        6. Return selected option
        """
        # Get display adapter
        display = self._get_display(walker)
        
        # Display declaration
        display.zDeclare(
            _DISPLAY_MSG_SELECT,
            color=self.navigation.mycolor,
            indent=_DISPLAY_INDENT_MENU,
            style=_DISPLAY_STYLE_SINGLE
        )

        # Build simple menu (no back option)
        menu_obj = self.builder.build(options, prompt, allow_back=False)
        
        # Render menu
        self.renderer.render(menu_obj, display)
        
        # Get user choice
        choice = self.interaction.get_choice(menu_obj, display)
        
        return choice

    def handle(
        self,
        zMenu_obj: Dict[str, Any],
        walker: Optional[Any] = None
    ) -> str:
        """
        Handle legacy zMenu object format (for backward compatibility).
        
        Maintains support for legacy zMenu object format used in older code.
        Handles anchor mode logic (automatic "Back" injection) and logs detailed
        menu object information for debugging. Provides graceful migration path.
        
        Args
        ----
        zMenu_obj : Dict[str, Any]
            Legacy menu object with keys:
            - "zBlock": Block name
            - "zKey": Key identifier
            - "zHorizontal": List of menu options
            - "is_anchor": Whether anchor mode is active
        walker : Optional[Any], default=None
            Walker instance (required for legacy format)
        
        Returns
        -------
        str
            Selected menu option string
        
        Raises
        ------
        ValueError
            If walker is not provided (required for legacy format)
        
        Examples
        --------
        Handle legacy menu object::
        
            zMenu_obj = {
                "zBlock": "MainMenu",
                "zKey": "menu_key",
                "zHorizontal": ["Settings", "Profile"],
                "is_anchor": False
            }
            choice = menu_system.handle(zMenu_obj, walker)
            # Automatically adds "zBack" option
        
        Anchor mode (no back)::
        
            zMenu_obj = {
                "zBlock": "ConfirmMenu",
                "zKey": "confirm_key",
                "zHorizontal": ["Yes", "No"],
                "is_anchor": True
            }
            choice = menu_system.handle(zMenu_obj, walker)
            # No "zBack" option added
        
        Notes
        -----
        - **Legacy Support**: Maintains old zMenu object format compatibility
        - **Anchor Mode**: is_anchor=False → adds "zBack" option automatically
        - **Detailed Logging**: Logs all zMenu object fields for debugging
        - **Migration Path**: Allows gradual transition to new create() method
        
        Algorithm
        ---------
        1. Validate walker exists (raise ValueError if not)
        2. Get display from walker
        3. Display declaration banner
        4. Log detailed zMenu object information
        5. Extract options from zHorizontal
        6. If not anchor mode, inject NAV_ZBACK into options
        7. Log final menu options
        8. Create menu pairs for display
        9. Display breadcrumbs and menu
        10. Get user choice via interaction component
        11. Display return banner
        12. Log and return selected choice
        """
        # Validate walker
        if not walker:
            raise ValueError("Legacy zNavigation.handle requires walker instance")
        
        # Get display adapter
        display = self._get_display(walker)
        
        # Display declaration
        display.zDeclare(
            _DISPLAY_MSG_HANDLE,
            color=self.navigation.mycolor,
            indent=_DISPLAY_INDENT_MENU,
            style=_DISPLAY_STYLE_FULL
        )

        # Log zMenu object details
        self.logger.debug(
            _LOG_ZMENU_OBJECT,
            zMenu_obj.get(DICT_KEY_ZBLOCK),
            zMenu_obj.get(DICT_KEY_ZKEY),
            zMenu_obj.get(DICT_KEY_ZHORIZONTAL),
            zMenu_obj.get(DICT_KEY_IS_ANCHOR)
        )

        # Handle anchor mode logic
        options = zMenu_obj[DICT_KEY_ZHORIZONTAL]
        if not zMenu_obj[DICT_KEY_IS_ANCHOR]:
            self.logger.debug(_LOG_ANCHOR_ACTIVE)
            options = options + [NAV_ZBACK]

        self.logger.debug(_LOG_MENU_OPTIONS, options)

        # Create menu pairs for display
        menu_pairs = list(enumerate(options))
        display.zCrumbs(self.zcli.session)
        display.zMenu(menu_pairs)

        # Get user choice
        choice = self.interaction.get_choice_from_list(options, display)
        
        # Display return banner
        display.zDeclare(
            _DISPLAY_MSG_RETURN,
            color=self.navigation.mycolor,
            indent=_DISPLAY_INDENT_MENU,
            style=_DISPLAY_STYLE_TILDE
        )
        
        self.logger.debug(_LOG_MENU_SELECTED, choice)
        return choice

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _get_display(self, walker: Optional[Any]) -> Any:
        """
        Get display adapter from walker or zcli.
        
        Args
        ----
        walker : Optional[Any]
            Walker instance (may be None)
        
        Returns
        -------
        Any
            Display adapter instance (walker.display or self.zcli.display)
        
        Notes
        -----
        DRY Helper: Eliminates 3 duplications of display adapter retrieval logic.
        If walker is provided, uses walker.display; otherwise falls back to
        self.zcli.display. This ensures consistent display access across all methods.
        """
        return walker.display if walker else self.zcli.display
