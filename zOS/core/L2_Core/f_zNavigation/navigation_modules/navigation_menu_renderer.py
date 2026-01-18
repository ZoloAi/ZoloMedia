# zCLI/subsystems/zNavigation/navigation_modules/navigation_menu_renderer.py

"""
Menu Renderer for zNavigation - Foundation Module.

This module provides the MenuRenderer class, which implements rendering strategies
for displaying menus in different formats and contexts. It integrates with zDisplay
to provide mode-agnostic rendering (Terminal and Bifrost).

Architecture
------------
The MenuRenderer is a Tier 1 (Foundation) component with no internal dependencies.
It provides three distinct rendering strategies optimized for different use cases:

1. Full Rendering (render):
   - Displays title with colored headers
   - Shows breadcrumb navigation
   - Uses zDisplay.zMenu() for formatted output
   - Best for primary navigation menus
   
2. Simple Rendering (render_simple):
   - Displays prompt with single-line header
   - Shows numbered list of options
   - Uses basic text output
   - Best for quick selections and dialogs
   
3. Compact Rendering (render_compact):
   - Single-line space-efficient format
   - Format: "0:option1 | 1:option2 | 2:option3"
   - Uses minimal display space
   - Best for space-constrained displays

Mode-Agnostic Rendering
------------------------
All rendering methods delegate to zDisplay, which handles Terminal vs. Bifrost
mode switching automatically:

- Terminal Mode: Direct console output with ANSI colors
- Bifrost Mode: WebSocket events sent to frontend

The renderer doesn't need to know which mode is active; zDisplay handles the
abstraction transparently.

Display Integration
-------------------
MenuRenderer uses the following zDisplay methods:

- zDeclare(text, color, indent, style):
  Used for titles and prompts with colored formatting
  
- zCrumbs(session):
  Displays breadcrumb navigation trail
  
- zMenu(menu_pairs):
  Renders formatted menu with numbered options
  
- text(content):
  Simple text output without special formatting

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Tier 1 (Foundation)

Integration
-----------
- Called by: MenuSystem (navigation_menu_system.py)
- Uses: zDisplay for all output operations
- Session: Accesses session for breadcrumb display
- Logging: Logs all rendering operations at debug level

Thread Safety
-------------
MenuRenderer is thread-safe as it does not maintain state between render calls.
Each render operation is independent.

Usage Examples
--------------
Full menu rendering::

    renderer = MenuRenderer(menu_system)
    menu_obj = {
        "options": ["Edit", "Delete", "View", "zBack"],
        "title": "Actions Menu",
        "allow_back": True
    }
    renderer.render(menu_obj, display)

Simple menu rendering::

    options = ["Option 1", "Option 2", "Option 3"]
    renderer.render_simple(options, display, prompt="Choose action")

Compact menu rendering::

    options = ["Yes", "No", "Cancel"]
    renderer.render_compact(options, display)

Module Constants
----------------
KEY_* : str
    Menu object dictionary keys
DEFAULT_* : str/int/bool
    Default values for rendering parameters
TEMPLATE_* : str
    String templates for formatting
SEPARATOR_* : str
    Separators for compact rendering
LOG_* : str
    Logging message templates
"""

from zOS import Any, Optional, Dict, List

from .navigation_constants import (
    KEY_OPTIONS,
    KEY_TITLE,
    KEY_ALLOW_BACK,
    _DEFAULT_ALLOW_BACK,
    _DEFAULT_INDENT,
    _DEFAULT_STYLE_FULL,
    _DEFAULT_STYLE_SINGLE,
    _DEFAULT_PROMPT,
    _TEMPLATE_SIMPLE_ITEM,
    _TEMPLATE_COMPACT_ITEM,
    _SEPARATOR_COMPACT,
    _LOG_RENDERED_MENU,
    _LOG_RENDERED_SIMPLE,
    _LOG_RENDERED_COMPACT,
    _LOG_BREADCRUMB_FAILED,
)


# ============================================================================
# MenuRenderer Class
# ============================================================================

class MenuRenderer:
    """
    Menu rendering engine for zNavigation.
    
    Provides three rendering strategies (full, simple, compact) for displaying
    menus in different contexts. Integrates with zDisplay for mode-agnostic
    rendering across Terminal and Bifrost modes.
    
    Attributes
    ----------
    menu : MenuSystem
        Reference to parent menu system
    zcli : zCLI
        Reference to zCLI core instance
    logger : logging.Logger
        Logger instance for rendering operations
    
    Methods
    -------
    render(menu_obj, display)
        Full menu rendering with title, breadcrumbs, and formatted display
    render_simple(options, display, prompt)
        Simple numbered list rendering with prompt
    render_compact(options, display)
        Compact single-line rendering for space efficiency
    
    Private Methods
    ---------------
    _log_render(strategy, option_count)
        Log rendering operation (DRY helper)
    
    Examples
    --------
    Full rendering with title and breadcrumbs::
    
        menu_obj = builder.build(["Edit", "Delete"], "Actions")
        renderer.render(menu_obj, display)
    
    Simple rendering for quick selection::
    
        renderer.render_simple(["Yes", "No"], display, "Confirm?")
    
    Compact rendering for space-constrained UI::
    
        renderer.render_compact(["A", "B", "C"], display)
    
    Integration
    -----------
    - Called by: MenuSystem for all menu display operations
    - Uses: zDisplay for all output (mode-agnostic)
    - Logging: All rendering operations logged at debug level
    - Session: Accessed for breadcrumb navigation display
    """

    # Class-level type declarations
    menu: Any  # MenuSystem reference
    zcli: Any  # zCLI core instance
    logger: Any  # Logger instance

    def __init__(self, menu: Any) -> None:
        """
        Initialize menu renderer.
        
        Args
        ----
        menu : MenuSystem
            Parent menu system instance that provides access to zcli and logger
        
        Notes
        -----
        The MenuRenderer stores references to the parent menu system, zcli core,
        and logger for use during rendering operations. No rendering state is
        maintained between calls.
        """
        self.menu = menu
        self.zcli = menu.zcli
        self.logger = menu.logger

    def render(
        self,
        menu_obj: Dict[str, Any],
        display: Any
    ) -> None:
        """
        Render full menu with title, breadcrumbs, and formatted display.
        
        This is the primary rendering method, providing a complete menu experience
        with optional title, breadcrumb navigation, and formatted menu display
        through zDisplay.zMenu().
        
        Args
        ----
        menu_obj : Dict[str, Any]
            Menu object containing:
            - "options": List of menu option strings
            - "title": Optional menu title (or None)
            - "allow_back": Boolean flag (default: True)
        display : Any
            Display adapter (zDisplay instance) for output operations
        
        Returns
        -------
        None
            Output is sent directly to display adapter
        
        Examples
        --------
        Render menu with title::
        
            menu_obj = {
                "options": ["Edit", "Delete", "View", "zBack"],
                "title": "Actions Menu",
                "allow_back": True
            }
            renderer.render(menu_obj, display)
        
        Render menu without title::
        
            menu_obj = {
                "options": ["Option 1", "Option 2"],
                "title": None,
                "allow_back": True
            }
            renderer.render(menu_obj, display)
        
        Notes
        -----
        - Title is displayed using zDisplay.zDeclare() with full style
        - Breadcrumbs are displayed if available (Walker context)
        - Menu options are rendered using zDisplay.zMenu()
        - All output is mode-agnostic (Terminal/Bifrost handled by zDisplay)
        - If breadcrumb display fails, error is logged but rendering continues
        
        Mode Behavior
        -------------
        - Terminal: ANSI-colored output with interactive selection
        - Bifrost: WebSocket events sent to frontend for rendering
        """
        # Extract menu object properties
        options = menu_obj[KEY_OPTIONS]
        title = menu_obj.get(KEY_TITLE)
        allow_back = menu_obj.get(KEY_ALLOW_BACK, _DEFAULT_ALLOW_BACK)

        # Show title if provided
        if title:
            display.zDeclare(
                title,
                color=self.menu.navigation.mycolor,
                indent=_DEFAULT_INDENT,
                style=_DEFAULT_STYLE_FULL
            )

        # Create menu pairs for display (enumerate with indices)
        # Strip $ prefix from display labels (delta links) for cleaner UX
        # The underlying option value keeps $ for navigation logic
        # Format sub-items: "zProducts (zCLI, zBifrost, zTheme, zTrivia)"
        menu_pairs = []
        for i, opt in enumerate(options):
            if isinstance(opt, dict) and len(opt) == 1:
                # Dict with metadata: {"$zProducts": {"zSub": ["zCLI", "zBifrost", ...]}}
                item_name = list(opt.keys())[0]
                item_data = opt[item_name]
                
                # Extract display name (strip $ prefix)
                display_name = item_name.lstrip('$')
                
                # Check for sub-items in metadata
                if isinstance(item_data, dict) and "zSub" in item_data:
                    sub_items = item_data["zSub"]
                    display_text = f"{display_name} ({', '.join(sub_items)})"
                else:
                    display_text = display_name
                
                menu_pairs.append((i, display_text))
            elif isinstance(opt, str):
                menu_pairs.append((i, opt.lstrip('$')))
            else:
                menu_pairs.append((i, str(opt)))
        
        # Show breadcrumbs if available (for Walker context)
        try:
            display.zCrumbs(self.zcli.session)
        except AttributeError as e:
            # Log if zCrumbs method not available
            self.logger.debug(_LOG_BREADCRUMB_FAILED, e)

        # Render menu using modern zDisplay method
        display.zMenu(menu_pairs)

        # Log rendering operation
        self._log_render("full", len(options))

    def render_simple(
        self,
        options: List[str],
        display: Any,
        prompt: str = _DEFAULT_PROMPT
    ) -> None:
        """
        Render simple menu without complex formatting.
        
        Provides a lightweight menu rendering with a prompt and numbered list.
        Best for quick selections, dialogs, and scenarios where full menu
        formatting is not needed.
        
        Args
        ----
        options : List[str]
            List of option strings to display
        display : Any
            Display adapter (zDisplay instance) for output
        prompt : str, default="Select option"
            Prompt text displayed above options
        
        Returns
        -------
        None
            Output is sent directly to display adapter
        
        Examples
        --------
        Simple yes/no prompt::
        
            renderer.render_simple(["Yes", "No"], display, "Continue?")
        
        Quick action selection::
        
            actions = ["Edit", "Delete", "Cancel"]
            renderer.render_simple(actions, display, "Choose action")
        
        Default prompt::
        
            renderer.render_simple(["A", "B", "C"], display)
            # Uses default prompt: "Select option"
        
        Notes
        -----
        - Prompt is displayed using zDisplay.zDeclare() with single style
        - Each option is numbered starting from 0
        - Format: "  [0] option1"
        - Uses display.text() for simple output
        - No breadcrumbs or complex formatting
        
        Use Cases
        ---------
        - Dialog confirmations (Yes/No/Cancel)
        - Quick action selections
        - Nested menu selections
        - Space-efficient alternatives to full menus
        """
        # Display prompt with single-line style
        display.zDeclare(
            prompt,
            color=self.menu.navigation.mycolor,
            indent=_DEFAULT_INDENT,
            style=_DEFAULT_STYLE_SINGLE
        )

        # Simple numbered list
        for i, option in enumerate(options):
            formatted_item = _TEMPLATE_SIMPLE_ITEM.format(index=i, option=option)
            display.text(formatted_item)

        # Log rendering operation
        self._log_render("simple", len(options))

    def render_compact(
        self,
        options: List[str],
        display: Any
    ) -> None:
        """
        Render compact menu for space-constrained displays.
        
        Provides the most space-efficient menu rendering with all options on
        a single line, separated by pipes. Best for mobile displays, small
        terminals, or when screen real estate is limited.
        
        Args
        ----
        options : List[str]
            List of option strings to display
        display : Any
            Display adapter (zDisplay instance) for output
        
        Returns
        -------
        None
            Output is sent directly to display adapter
        
        Examples
        --------
        Compact yes/no menu::
        
            renderer.render_compact(["Yes", "No"], display)
            # Output: "0:Yes | 1:No"
        
        Compact action menu::
        
            actions = ["Edit", "Delete", "View", "Cancel"]
            renderer.render_compact(actions, display)
            # Output: "0:Edit | 1:Delete | 2:View | 3:Cancel"
        
        Notes
        -----
        - Format: "index:option | index:option | index:option"
        - No prompt or title displayed
        - Single line of output
        - Uses display.text() for output
        - Each option is numbered starting from 0
        
        Format Details
        --------------
        - Separator: " | " (space-pipe-space)
        - Item format: "index:option" (no spaces)
        - Example: "0:option1 | 1:option2 | 2:option3"
        
        Use Cases
        ---------
        - Mobile-optimized displays
        - Small terminal windows
        - Status bar menus
        - Quick inline selections
        - Dashboard controls
        """
        # Show options in compact format
        formatted_items = [
            _TEMPLATE_COMPACT_ITEM.format(index=i, option=opt)
            for i, opt in enumerate(options)
        ]
        option_text = _SEPARATOR_COMPACT.join(formatted_items)
        display.text(option_text)

        # Log rendering operation
        self._log_render("compact", len(options))

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _log_render(
        self,
        strategy: str,
        option_count: int
    ) -> None:
        """
        Log menu rendering operation.
        
        Args
        ----
        strategy : str
            Rendering strategy used ("full", "simple", or "compact")
        option_count : int
            Number of options rendered
        
        Notes
        -----
        DRY Helper: Eliminates 3 duplications of logging pattern
        (lines 43, 60, 74 in original)
        
        Logs at debug level with format: "Rendered {strategy} menu with N options"
        """
        if strategy == "full":
            self.logger.debug(_LOG_RENDERED_MENU, option_count)
        elif strategy == "simple":
            self.logger.debug(_LOG_RENDERED_SIMPLE, option_count)
        elif strategy == "compact":
            self.logger.debug(_LOG_RENDERED_COMPACT, option_count)
