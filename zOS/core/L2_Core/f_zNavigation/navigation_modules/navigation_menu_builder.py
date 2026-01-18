# zCLI/subsystems/zNavigation/navigation_modules/navigation_menu_builder.py

"""
Menu Builder for zNavigation - Foundation Module.

This module provides the MenuBuilder class, which implements the Builder pattern
for constructing menu objects in zNavigation. It supports three distinct build
strategies for creating menus from different data sources.

Architecture
------------
The MenuBuilder is a Tier 1 (Foundation) component with no internal dependencies.
It provides a flexible API for creating menu objects that are then passed to
MenuRenderer for display and MenuInteraction for user input handling.

Build Strategies:
    1. Static Build (build):
       - Creates menus from known, predefined options
       - Accepts List, Dict, or String inputs
       - Automatically normalizes to standard menu object format
    
    2. Dynamic Build (build_dynamic):
       - Creates menus from dynamic data sources
       - Supports callable data sources (functions, lambdas)
       - Extracts display fields from data objects
    
    3. Function-based Build (build_from_function):
       - Creates menus from zFunc execution results
       - Calls Python functions and converts output to menu options
       - Forward dependency: zFunc (Week 6.10)

Menu Object Structure
---------------------
All build methods produce a standardized menu object::

    {
        "options": ["item1", "item2", "zBack"],
        "title": "Menu Title",
        "allow_back": True,
        "metadata": {
            "created_by": "zMenu",
            "timestamp": "2025-10-31 12:00:00"
        }
    }

The menu object structure is consistent across all build strategies, enabling
MenuRenderer and MenuInteraction to process menus uniformly.

Forward Dependencies
--------------------
- zFunc: build_from_function() uses zcli.zfunc.handle()

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Tier 1 (Foundation)

Integration
-----------
- Called by: MenuSystem (navigation_menu_system.py)
- Used by: Navigation menu creation throughout zCLI
- Session: No direct session integration (menu history could be added)
- Logging: Logs all menu creation and errors

Thread Safety
-------------
MenuBuilder is thread-safe as it does not maintain shared state between menu
builds. Each build operation is independent.

Usage Examples
--------------
Static menu from list::

    builder = MenuBuilder(menu_system)
    menu_obj = builder.build(["Option 1", "Option 2"], "Main Menu")

Dynamic menu from data source::

    def get_users():
        return [{"name": "Alice", "id": 1}, {"name": "Bob", "id": 2}]
    
    menu_obj = builder.build_dynamic(get_users, display_field="name", title="Users")

Function-based menu::

    menu_obj = builder.build_from_function("get_available_actions")

Module Constants
----------------
NAV_ZBACK : str
    Navigation constant for back option
CREATOR_ZMENU : str
    Menu creator identifier for metadata
KEY_* : str
    Menu object dictionary keys
ERR_* : str
    Error messages for fallback menus
LOG_* : str
    Logging message templates
TEMPLATE_* : str
    String templates for dynamic content
_TIMESTAMP_FORMAT : str
    ISO-style timestamp format for metadata
"""

from zOS import time, Any, Optional, Dict, List, Union, Callable

from .navigation_constants import (
    NAV_ZBACK,
    CREATOR_ZMENU,
    KEY_OPTIONS,
    KEY_TITLE,
    KEY_ALLOW_BACK,
    KEY_METADATA,
    KEY_CREATED_BY,
    KEY_TIMESTAMP,
    _ERR_DYNAMIC_MENU,
    _ERR_FUNCTION_MENU,
    _TITLE_ERROR,
    _TITLE_FUNC_ERROR_TEMPLATE,
    _TEMPLATE_RESULTS_FROM,
    _TEMPLATE_ERROR_CALLING,
    _LOG_BUILT_MENU,
    _LOG_FAILED_DYNAMIC,
    _LOG_FAILED_FUNCTION,
    _TIMESTAMP_FORMAT,
)


# ============================================================================
# MenuBuilder Class
# ============================================================================

class MenuBuilder:
    """
    Menu object constructor for zNavigation.
    
    Implements the Builder pattern for creating menu objects from various data
    sources. Supports static options, dynamic data sources, and function-based
    menu generation.
    
    Attributes
    ----------
    menu : MenuSystem
        Reference to parent menu system
    zcli : zCLI
        Reference to zCLI core instance
    logger : logging.Logger
        Logger instance for menu creation
    
    Methods
    -------
    build(options, title, allow_back)
        Build menu from static options (list, dict, or string)
    build_dynamic(data_source, display_field, title, allow_back)
        Build menu from dynamic data source or callable
    build_from_function(func_name, *args, **kwargs)
        Build menu from zFunc execution result
    
    Private Methods
    ---------------
    _normalize_to_string_list(data, display_field)
        Normalize various data types to list of strings
    _build_error_menu(error_message, title)
        Build fallback error menu
    _get_timestamp()
        Get current timestamp for menu metadata
    
    Examples
    --------
    Static menu::
    
        menu_obj = builder.build(["Edit", "Delete", "View"], "Actions")
    
    Dynamic menu with dict extraction::
    
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        menu_obj = builder.build_dynamic(data, display_field="name", title="Users")
    
    Function-based menu::
    
        menu_obj = builder.build_from_function("list_available_modules")
    
    Integration
    -----------
    - Called by: MenuSystem.create(), MenuSystem.select()
    - Logging: All menu creation and errors logged
    - Forward Dependency: zFunc (Week 6.10)
    """

    # Class-level type declarations
    menu: Any  # MenuSystem reference
    zcli: Any  # zCLI core instance
    logger: Any  # Logger instance

    def __init__(self, menu: Any) -> None:
        """
        Initialize menu builder.
        
        Args
        ----
        menu : MenuSystem
            Parent menu system instance that provides access to zcli and logger
        
        Notes
        -----
        The MenuBuilder stores references to the parent menu system, zcli core,
        and logger for use during menu creation.
        """
        self.menu = menu
        self.zcli = menu.zcli
        self.logger = menu.logger

    def build(
        self,
        options: Union[List, Dict, str],
        title: Optional[str] = None,
        allow_back: bool = True
    ) -> Dict[str, Any]:
        """
        Build menu object from static options.
        
        This is the primary build method for creating menus from known, predefined
        options. It normalizes various input formats (list, dict, string) into a
        standardized menu object structure.
        
        Args
        ----
        options : Union[List, Dict, str]
            Menu options in any of the following formats:
            - List of strings: ["Option 1", "Option 2"]
            - Dict with options as keys: {"Option 1": data, "Option 2": data}
            - Single string: "Single Option"
        title : Optional[str], default=None
            Optional menu title displayed above options
        allow_back : bool, default=True
            Whether to automatically add "zBack" option to menu
        
        Returns
        -------
        Dict[str, Any]
            Standardized menu object with keys:
            - "options": List of option strings
            - "title": Menu title or None
            - "allow_back": Boolean flag
            - "metadata": Dict with "created_by" and "timestamp"
        
        Examples
        --------
        Build from list::
        
            menu_obj = builder.build(["Edit", "Delete", "View"], "Actions Menu")
        
        Build from dict::
        
            options_dict = {"Edit": edit_func, "Delete": delete_func}
            menu_obj = builder.build(options_dict, "Available Actions")
        
        Build from string::
        
            menu_obj = builder.build("Single Action", allow_back=False)
        
        Notes
        -----
        - The "zBack" option is automatically added unless:
          1. allow_back=False, or
          2. "zBack" already exists in options
        - All options are converted to strings for consistent rendering
        - Menu metadata includes creator and timestamp for tracking
        """
        # Normalize options to list
        if isinstance(options, dict):
            option_list = list(options.keys())
        elif isinstance(options, list):
            option_list = options
        else:
            option_list = [str(options)]

        # Add back option if requested and not present
        if allow_back and NAV_ZBACK not in option_list:
            option_list.append(NAV_ZBACK)

        # Create menu object with standardized structure
        menu_obj = {
            KEY_OPTIONS: option_list,
            KEY_TITLE: title,
            KEY_ALLOW_BACK: allow_back,
            KEY_METADATA: {
                KEY_CREATED_BY: CREATOR_ZMENU,
                KEY_TIMESTAMP: self._get_timestamp()
            }
        }

        self.logger.debug(_LOG_BUILT_MENU, menu_obj)
        return menu_obj

    def build_dynamic(
        self,
        data_source: Union[Callable, List, Any],
        display_field: Optional[str] = None,
        title: Optional[str] = None,
        allow_back: bool = True
    ) -> Dict[str, Any]:
        """
        Build menu from dynamic data source.
        
        Creates a menu from data that may change between calls. Supports callable
        data sources (functions, lambdas) and direct data. Extracts display values
        from complex objects using the display_field parameter.
        
        Args
        ----
        data_source : Union[Callable, List, Any]
            Data source for menu options:
            - Callable: Function that returns data when called
            - List: Direct list of data items
            - Any: Single data item converted to list
        display_field : Optional[str], default=None
            Field name to extract from dict objects for display.
            If None, entire object is converted to string.
        title : Optional[str], default=None
            Optional menu title
        allow_back : bool, default=True
            Whether to add "zBack" option
        
        Returns
        -------
        Dict[str, Any]
            Standardized menu object (see build() for structure)
        
        Examples
        --------
        Menu from callable data source::
        
            def get_users():
                return [{"name": "Alice", "id": 1}, {"name": "Bob", "id": 2}]
            
            menu_obj = builder.build_dynamic(
                get_users,
                display_field="name",
                title="Select User"
            )
        
        Menu from direct data::
        
            users = [{"name": "Alice"}, {"name": "Bob"}]
            menu_obj = builder.build_dynamic(users, display_field="name")
        
        Menu with lambda::
        
            menu_obj = builder.build_dynamic(
                lambda: database.get_active_sessions(),
                display_field="session_id"
            )
        
        Notes
        -----
        - If data_source is callable, it is invoked at menu creation time
        - If data extraction fails, falls back to error menu
        - All items are converted to strings for rendering
        - Empty data sources create empty option lists
        
        Error Handling
        --------------
        On any exception, returns a fallback error menu with single error message
        option, preventing menu system from crashing.
        """
        try:
            # Get data from source (invoke if callable)
            if callable(data_source):
                data = data_source()
            else:
                data = data_source

            # Extract display values using helper
            options = self._normalize_to_string_list(data, display_field)

            # Build using standard build method
            return self.build(options, title, allow_back)

        except Exception as e:
            self.logger.error(_LOG_FAILED_DYNAMIC, e)
            return self._build_error_menu(_ERR_DYNAMIC_MENU, _TITLE_ERROR)

    def build_from_function(
        self,
        func_name: str,
        *args: Any,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Build menu from zFunc execution result.
        
        Executes a Python function through zFunc and converts the result into a
        menu. Useful for dynamically generating menu options based on runtime state
        or external data.
        
        Args
        ----
        func_name : str
            Name of function to call through zFunc
        *args : Any
            Positional arguments to pass to function
        **kwargs : Any
            Keyword arguments to pass to function
        
        Returns
        -------
        Dict[str, Any]
            Standardized menu object (see build() for structure)
        
        Examples
        --------
        Simple function call::
        
            menu_obj = builder.build_from_function("get_available_modules")
        
        Function with arguments::
        
            menu_obj = builder.build_from_function(
                "filter_items",
                "active",
                limit=10
            )
        
        Notes
        -----
        - Function result is converted to list of strings
        - If result is already a list, each item becomes an option
        - If result is not a list, it becomes a single option
        - Menu title is "Results from {func_name}"
        
        Forward Dependency
        ------------------
        Uses zcli.zfunc.handle() with standard zFunc string format.
        Format: f"zFunc({func_name}, {args}, {kwargs})"
        
        Error Handling
        --------------
        On execution failure, returns error menu with function name in title.
        """
        try:
            # Call function through zFunc (standard string format)
            result = self.zcli.zfunc.handle(f"zFunc({func_name}, {args}, {kwargs})")
            
            # Convert result to menu options
            if isinstance(result, list):
                options = self._normalize_to_string_list(result, display_field=None)
            else:
                options = [str(result)]

            # Build menu with function name in title
            title = _TEMPLATE_RESULTS_FROM.format(func_name=func_name)
            return self.build(options, title, allow_back=True)

        except Exception as e:
            self.logger.error(_LOG_FAILED_FUNCTION, func_name, e)
            title = _TEMPLATE_ERROR_CALLING.format(func_name=func_name)
            return self._build_error_menu(_ERR_FUNCTION_MENU, title)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _normalize_to_string_list(
        self,
        data: Any,
        display_field: Optional[str] = None
    ) -> List[str]:
        """
        Normalize various data types to list of strings.
        
        Handles extraction of display values from complex data structures,
        converting everything to a list of strings suitable for menu rendering.
        
        Args
        ----
        data : Any
            Data to normalize (list, dict, object, or primitive)
        display_field : Optional[str], default=None
            Field to extract from dict/object items
        
        Returns
        -------
        List[str]
            List of string representations of data items
        
        Notes
        -----
        DRY Helper: Eliminates 4 duplications of string normalization logic
        (lines 75, 77, 79, 105 in original)
        """
        if not isinstance(data, list):
            return [str(data)]
        
        if not data:
            return []
        
        # Extract display field if specified and data contains dicts
        if display_field and isinstance(data[0], dict):
            return [str(item.get(display_field, item)) for item in data]
        
        # Otherwise convert each item to string
        return [str(item) for item in data]

    def _build_error_menu(
        self,
        error_message: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Build fallback error menu.
        
        Creates a standardized error menu with a single error message option.
        Used when menu building fails to prevent system crashes.
        
        Args
        ----
        error_message : str
            Error message to display as menu option
        title : str
            Title for error menu
        
        Returns
        -------
        Dict[str, Any]
            Error menu object with single error option and back button
        
        Notes
        -----
        DRY Helper: Eliminates 2 duplications of error menu creation
        (lines 85, 113 in original)
        """
        return self.build([error_message], title, allow_back=True)

    def _get_timestamp(self) -> str:
        """
        Get current timestamp for menu metadata.
        
        Returns
        -------
        str
            Current timestamp in format "YYYY-MM-DD HH:MM:SS"
        
        Notes
        -----
        Used for tracking menu creation time in metadata. This can be useful
        for debugging, logging, or implementing menu caching strategies.
        """
        return time.strftime(_TIMESTAMP_FORMAT)
