# zCLI/subsystems/zNavigation/navigation_modules/navigation_menu_interaction.py

"""
Menu Interaction Handler for zNavigation - Foundation Module.

This module provides the MenuInteraction class, which implements user interaction
strategies for menu selection. It supports four distinct interaction patterns with
comprehensive input validation and an innovative search feature.

Architecture
------------
The MenuInteraction is a Tier 1 (Foundation) component with no internal dependencies.
It provides four interaction strategies optimized for different use cases:

1. Single Choice from Menu Object (get_choice):
   - Extracts options from menu object
   - Delegates to get_choice_from_list()
   - Primary method called by MenuSystem
   
2. Single Choice from List (get_choice_from_list):
   - Direct list-based selection
   - Validates digit input and range
   - Returns single selected option
   
3. Multiple Choices (get_multiple_choices):
   - Comma-separated indices input
   - Batch selection capability
   - Returns list of selected options
   
4. Choice with Search (get_choice_with_search):
   - Interactive search/filter mode
   - "/" prefix triggers filtering
   - Case-insensitive substring matching
   - Dynamic results display

Input Validation Flow
---------------------
All interaction methods follow a consistent validation pattern:

1. Display prompt or menu
2. Read user input via display.read_string()
3. Log raw input for debugging
4. Validate input format (digit check, comma parsing)
5. Validate input range (index bounds)
6. Return selected option(s)
7. Loop on error with clear feedback

Validation is centralized in helper methods for consistency and DRY.

Search Feature (Innovative)
----------------------------
The search feature provides an interactive filtering mechanism for large menus:

- **Trigger**: User enters "/search-term" instead of digit
- **Filtering**: Case-insensitive substring matching
- **Dynamic Display**: Shows filtered results after each search
- **Refinement**: Can refine search or select from filtered list
- **Reset**: Returns to full list if no matches found
- **Use Case**: Essential for menus with 10+ options

Example search flow::

    Original: 100 options
    User: /python
    Filtered: 15 options (containing "python")
    User: /django
    Filtered: 3 options (containing "python" and "django")
    User: 1
    Selected: Filtered option at index 1

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Tier 1 (Foundation)

Integration
-----------
- Called by: MenuSystem (navigation_menu_system.py)
- Uses: zDisplay for all I/O operations
- Logging: Logs all user input and selections at debug level
- No session integration (stateless interaction)

Thread Safety
-------------
MenuInteraction is thread-safe as it does not maintain state between calls.
Each interaction is independent and operates on passed parameters.

Usage Examples
--------------
Single choice from menu object::

    interaction = MenuInteraction(menu_system)
    menu_obj = {"options": ["Edit", "Delete", "View", "zBack"]}
    selected = interaction.get_choice(menu_obj, display)

Single choice from list::

    options = ["Option 1", "Option 2", "Option 3"]
    selected = interaction.get_choice_from_list(options, display)

Multiple choices (comma-separated)::

    options = ["File1.txt", "File2.txt", "File3.txt"]
    selected = interaction.get_multiple_choices(options, display)
    # User enters: "0, 2"
    # Returns: ["File1.txt", "File3.txt"]

Choice with search::

    options = [f"Module{i}" for i in range(100)]
    selected = interaction.get_choice_with_search(options, display)
    # User enters: "/auth"
    # Shows filtered results containing "auth"
    # User selects from filtered list

Module Constants
----------------
KEY_* : str
    Menu object dictionary keys
PROMPT_* : str
    Default prompts for user input
PREFIX_* : str
    Special input prefixes (newline, search)
SEPARATOR_* : str
    Input/output separators
ERR_* : str
    Error messages for validation failures
TEMPLATE_* : str
    String templates for formatting
LOG_* : str
    Logging message templates
WARN_* : str
    Warning messages for user feedback
"""

from zOS import Any, Dict, List, Union

from .navigation_constants import (
    SESSION_KEY_VAFOLDER,
    SESSION_KEY_VAFILE,
    _PREFIX_BLOCK_DELTA,
    _CMD_EXIT,
    NAV_ZBACK,
    KEY_OPTIONS,
    _PROMPT_DEFAULT,
    _PROMPT_MULTIPLE_DEFAULT,
    _PROMPT_SEARCH_DEFAULT,
    _PREFIX_NEWLINE,
    _PREFIX_SEARCH,
    _SEPARATOR_COMMA,
    _SEPARATOR_SPACE,
    _ERR_INVALID_DIGIT,
    _ERR_OUT_OF_RANGE,
    _ERR_INVALID_COMMA,
    _ERR_INVALID_SEARCH,
    _TEMPLATE_INVALID_INDICES,
    _TEMPLATE_FILTERED_COUNT,
    _TEMPLATE_OPTION_ITEM,
    _TEMPLATE_SEARCH_PROMPT,
    _LOG_RAW_INPUT,
    _LOG_INVALID_DIGIT,
    _LOG_OUT_OF_RANGE,
    _LOG_SELECTED,
    _LOG_SELECTED_MULTIPLE,
    _LOG_SELECTED_SEARCH,
    _WARN_NO_MATCHES,
)


# ============================================================================
# MenuInteraction Class
# ============================================================================

class MenuInteraction:
    """
    Menu interaction engine for zNavigation.
    
    Provides four interaction strategies (single, multiple, search) for menu
    selection with comprehensive input validation. Integrates with zDisplay
    for mode-agnostic I/O.
    
    Attributes
    ----------
    menu : MenuSystem
        Reference to parent menu system
    zcli : zCLI
        Reference to zCLI core instance
    logger : logging.Logger
        Logger instance for interaction operations
    
    Methods
    -------
    get_choice(menu_obj, display)
        Get single choice from menu object
    get_choice_from_list(options, display)
        Get single choice from list of options
    get_multiple_choices(options, display, prompt)
        Get multiple choices (comma-separated)
    get_choice_with_search(options, display, search_prompt)
        Get choice with interactive search/filter
    
    Private Methods
    ---------------
    _validate_digit_input(choice, display)
        Validate that input is a digit
    _validate_index_range(index, options, display)
        Validate that index is within range
    _log_user_input(choice)
        Log raw user input (DRY helper)
    _format_option_item(index, option)
        Format option for display (DRY helper)
    _show_error(display, message)
        Show error with consistent formatting (DRY helper)
    
    Examples
    --------
    Single choice::
    
        menu_obj = {"options": ["Edit", "Delete", "View"]}
        selected = interaction.get_choice(menu_obj, display)
    
    Multiple choices::
    
        options = ["File1", "File2", "File3"]
        selected = interaction.get_multiple_choices(options, display)
        # User enters: "0, 2"
        # Returns: ["File1", "File3"]
    
    Search choice::
    
        options = [f"Module{i}" for i in range(100)]
        selected = interaction.get_choice_with_search(options, display)
        # User: "/auth" → filters results
        # User: "1" → selects from filtered
    
    Integration
    -----------
    - Called by: MenuSystem for all user interaction
    - Uses: zDisplay for all I/O operations
    - Logging: All user input logged at debug level
    """

    # Class-level type declarations
    menu: Any  # MenuSystem reference
    zcli: Any  # zCLI core instance
    logger: Any  # Logger instance

    def __init__(self, menu: Any) -> None:
        """
        Initialize menu interaction handler.
        
        Args
        ----
        menu : MenuSystem
            Parent menu system instance that provides access to zcli and logger
        
        Notes
        -----
        The MenuInteraction stores references to the parent menu system, zcli core,
        and logger for use during interaction operations. No interaction state is
        maintained between calls.
        """
        self.menu = menu
        self.zcli = menu.zcli
        self.logger = menu.logger

    def get_choice(
        self,
        menu_obj: Dict[str, Any],
        display: Any
    ) -> Union[str, Dict[str, Any]]:
        """
        Get user choice from menu object.
        
        This is a convenience wrapper that extracts options from a menu object
        and delegates to get_choice_from_list(). Primary method called by
        MenuSystem.
        
        **Delta Link Support (v1.5.9):**
        If selected option starts with $ (e.g., "$zAbout"), returns a zLink
        dict for same-file block navigation instead of a raw string.
        
        Args
        ----
        menu_obj : Dict[str, Any]
            Menu object containing "options" key with list of options
        display : Any
            Display adapter (zDisplay instance) for I/O operations
        
        Returns
        -------
        Union[str, Dict[str, Any]]
            - str: Selected option (regular key navigation)
            - Dict: zLink dict for same-file navigation ($ prefix)
        
        Examples
        --------
        Standard menu selection::
        
            menu_obj = {
                "options": ["Edit", "Delete", "View", "zBack"],
                "title": "Actions"
            }
            selected = interaction.get_choice(menu_obj, display)
            # Returns: "Edit" (string)
        
        Same-file block navigation::
        
            menu_obj = {
                "options": ["$zHome", "$zAbout", "$zFeatures"]
            }
            selected = interaction.get_choice(menu_obj, display)
            # User selects [1]
            # Returns: {zLink: "@.UI.zUI.index.zAbout"}
        
        Notes
        -----
        - Extracts options list from menu object
        - Delegates validation to get_choice_from_list()
        - Returns actual option string (not index) or zLink dict
        - $ prefix triggers same-file navigation via zLink subsystem
        """
        options = menu_obj[KEY_OPTIONS]
        return self.get_choice_from_list(options, display)

    def get_choice_from_list(
        self,
        options: List[str],
        display: Any
    ) -> Union[str, Dict[str, Any]]:
        """
        Get user choice from list of options.
        
        Core single-selection method with comprehensive input validation.
        Loops until valid input is received, providing clear error messages
        for invalid input.
        
        **Delta Link Support (v1.5.9):**
        If selected option starts with $ (e.g., "$zAbout"), it's treated as
        same-file block navigation. The $ prefix is detected, and the selection
        is transformed into a zLink dict for navigation via the existing zLink
        subsystem. No duplicate navigation logic - pure delegation.
        
        Args
        ----
        options : List[str]
            List of option strings to choose from
        display : Any
            Display adapter (zDisplay instance) for I/O operations
        
        Returns
        -------
        Union[str, Dict[str, Any]]
            - str: Selected option (regular key navigation)
            - Dict: zLink dict for same-file block navigation ($ prefix)
                   Format: {zLink: "@.VaFolder.zVaFile.BlockName"}
        
        Examples
        --------
        Regular key navigation::
        
            options = ["settingsKey", "profileKey"]
            selected = interaction.get_choice_from_list(options, display)
            # User enters: "0"
            # Returns: "settingsKey" (looks for key in current block)
        
        Same-file block navigation ($ prefix)::
        
            options = ["$zSettings", "$zProfile", "$zHome"]
            selected = interaction.get_choice_from_list(options, display)
            # User enters: "1"
            # Returns: {zLink: "@.UI.zUI.index.zProfile"}
            # → Navigates to zProfile block in same file via zLink subsystem
        
        With validation::
        
            options = ["Option A", "Option B"]
            selected = interaction.get_choice_from_list(options, display)
            # User enters: "abc" → Error: "Invalid input - enter a number."
            # User enters: "5" → Error: "Choice out of range."
            # User enters: "0" → Returns: "Option A"
        
        Text commands::
        
            # User enters: "exit" → Returns: "exit" (triggers system exit)
            # User enters: "EXIT" → Returns: "exit" (case-insensitive)
        
        Notes
        -----
        - Validation: Input must be digit and within range [0, len(options)) OR "exit"
        - Text Commands: "exit" (case-insensitive) to trigger system exit
        - Error Feedback: Clear messages for format and range errors
        - Logging: All input and errors logged at debug level
        - Loop: Continues until valid input received
        - Delta Links: $ prefix triggers same-file navigation via zLink
        - No Duplication: Reuses existing zLink subsystem for navigation
        
        Validation Flow
        ---------------
        1. Read input from display
        2. Log raw input
        3. Check for "exit" command
        4. Validate digit format
        5. Validate index range
        6. Check for $ prefix
        7. Transform to zLink dict if needed
        8. Return selected option, zLink dict, or "exit"
        """
        # Streamlined input validation loop
        while True:
            choice = display.read_string(_PROMPT_DEFAULT)
            self._log_user_input(choice)

            # Check for text command: "exit"
            if choice.lower() == _CMD_EXIT:
                self.logger.debug(f"Exit command detected: {choice}")
                return _CMD_EXIT  # Return "exit" to trigger system exit

            # Validate digit format
            if not self._validate_digit_input(choice, display):
                continue

            # Validate index range
            index = int(choice)
            if not self._validate_index_range(index, options, display):
                continue

            break  # Valid input

        selected = options[index]
        self.logger.debug(_LOG_SELECTED, selected)
        
        # Check for hierarchical menu (dict with zSub metadata)
        if isinstance(selected, dict) and len(selected) == 1:
            item_name = list(selected.keys())[0]
            item_data = selected[item_name]
            
            # Check if this item has sub-items
            if isinstance(item_data, dict) and "zSub" in item_data:
                sub_items = item_data["zSub"]
                
                # User selected a parent item with sub-items - show sub-menu
                display_name = item_name.lstrip('$')  # Strip $ for display
                self.logger.debug(f"[MenuInteraction] Sub-menu triggered for '{display_name}' with {len(sub_items)} items")
                
                # Use the menu system to create and display the sub-menu
                # allow_back=True will automatically add zBack option
                sub_choice = self.menu.zcli.navigation.create(
                    options=sub_items,
                    title=f"Sub-menu for {display_name}",
                    allow_back=True,
                    walker=None
                )
                
                # If user selected "zBack", return to parent menu (recursive call)
                if sub_choice == NAV_ZBACK:
                    self.logger.debug("[MenuInteraction] zBack selected in sub-menu, returning to parent")
                    # Re-show parent menu by recursing
                    return self.get_choice_from_list(options, display)
                
                # Construct proper zLink for hierarchical navigation
                # Terminal: Navigate to UI/zProducts/zUI.zCLI.yaml → zCLI_Details block
                # Pattern: @.UI.{parent_name}.zUI.{sub_choice}.{sub_choice}_Details
                parent_name = display_name
                block_name = f"{sub_choice}_Details"
                zlink_path = f"@.UI.{parent_name}.zUI.{sub_choice}.{block_name}"
                
                self.logger.debug(f"[MenuInteraction] Hierarchical navigation: {sub_choice} → {zlink_path}")
                
                # Return zLink dict for navigation
                return {"zLink": zlink_path}
        
        # Check for same-file block navigation ($ prefix)
        if isinstance(selected, str) and selected.startswith(_PREFIX_BLOCK_DELTA):
            # Transform $BlockName → {zLink: "@.VaFolder.zVaFile.BlockName"}
            # This reuses the existing zLink subsystem for same-file navigation
            return self._transform_delta_link(selected)
        
        return selected

    def get_multiple_choices(
        self,
        options: List[str],
        display: Any,
        prompt: str = _PROMPT_MULTIPLE_DEFAULT
    ) -> List[str]:
        """
        Get multiple choices from menu.
        
        Allows users to select multiple options using comma-separated indices.
        All indices are validated before returning results.
        
        Args
        ----
        options : List[str]
            List of option strings to choose from
        display : Any
            Display adapter (zDisplay instance) for I/O operations
        prompt : str, default="Select options (comma-separated)"
            Prompt text displayed to user
        
        Returns
        -------
        List[str]
            List of selected option strings
        
        Examples
        --------
        Multiple file selection::
        
            files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
            selected = interaction.get_multiple_choices(files, display)
            # User enters: "0, 2, 3"
            # Returns: ["file1.txt", "file3.txt", "file4.txt"]
        
        Single selection (still valid)::
        
            options = ["A", "B", "C"]
            selected = interaction.get_multiple_choices(options, display)
            # User enters: "1"
            # Returns: ["B"]
        
        Error handling::
        
            options = ["X", "Y", "Z"]
            selected = interaction.get_multiple_choices(options, display)
            # User: "0, 5" → Error: "Invalid indices: [5]"
            # User: "abc" → Error: "Invalid input - enter comma-separated numbers."
            # User: "0, 2" → Returns: ["X", "Z"]
        
        Notes
        -----
        - Input Format: Comma-separated digits (spaces optional)
        - Validation: All indices must be valid before returning
        - Error Feedback: Shows which specific indices are invalid
        - Parsing: Uses try/except for comma parsing
        
        Input Formats Accepted
        ----------------------
        - "0, 1, 2" (spaces after commas)
        - "0,1,2" (no spaces)
        - "0 , 1 , 2" (extra spaces)
        - "1" (single selection)
        """
        display.text(prompt)

        while True:
            choice = display.read_string(_PROMPT_DEFAULT)
            self._log_user_input(choice)

            try:
                # Parse comma-separated choices
                indices = [int(x.strip()) for x in choice.split(_SEPARATOR_COMMA)]
                
                # Validate all indices
                invalid_indices = [
                    i for i in indices 
                    if i < 0 or i >= len(options)
                ]
                if invalid_indices:
                    error_msg = _TEMPLATE_INVALID_INDICES.format(
                        invalid_indices=invalid_indices
                    )
                    self._show_error(display, error_msg)
                    continue

                selected = [options[i] for i in indices]
                self.logger.debug(_LOG_SELECTED_MULTIPLE, selected)
                return selected

            except ValueError:
                self._show_error(display, _ERR_INVALID_COMMA)
                continue

    def get_choice_with_search(
        self,
        options: List[str],
        display: Any,
        search_prompt: str = _PROMPT_SEARCH_DEFAULT
    ) -> str:
        """
        Get choice with interactive search functionality.
        
        Provides an innovative search/filter feature for large menus. Users can
        enter "/" followed by a search term to filter options by substring match,
        or enter a digit to select from the current filtered list.
        
        Args
        ----
        options : List[str]
            List of option strings to choose from
        display : Any
            Display adapter (zDisplay instance) for I/O operations
        search_prompt : str, default="Search"
            Prompt text for search instructions
        
        Returns
        -------
        str
            Selected option string from the (possibly filtered) list
        
        Examples
        --------
        Search and select::
        
            modules = [f"Module{i}" for i in range(100)]
            selected = interaction.get_choice_with_search(modules, display)
            # User enters: "/auth"
            # Shows: Filtered to 8 options:
            #   [0] AuthModule1
            #   [1] AuthModule2
            #   ...
            # User enters: "1"
            # Returns: "AuthModule2"
        
        Refine search::
        
            options = ["python-django", "python-flask", "ruby-rails", "java-spring"]
            selected = interaction.get_choice_with_search(options, display)
            # User: "/python" → Shows: python-django, python-flask
            # User: "/flask" → Shows: python-flask
            # User: "0" → Returns: "python-flask"
        
        No matches::
        
            options = ["Apple", "Banana", "Cherry"]
            selected = interaction.get_choice_with_search(options, display)
            # User: "/orange" → Warning: "No matches found."
            # Shows original full list again
        
        Notes
        -----
        - Search Trigger: "/" prefix on input
        - Matching: Case-insensitive substring search
        - Filtering: Updates displayed options after each search
        - Selection: Enter digit to select from current filtered list
        - Reset: No matches → returns to full list with warning
        
        Search Feature Details
        ----------------------
        - Substring Matching: Searches within entire option string
        - Case Insensitive: "AUTH" matches "authentication"
        - Progressive: Can refine searches iteratively
        - Dynamic Display: Shows filtered count and updated list
        - Validation: Same digit/range validation as single choice
        
        Input Modes
        -----------
        - "/term": Trigger search/filter by term
        - "digit": Select option at digit index
        - Invalid: Error message and retry
        """
        filtered_options = options.copy()
        prompt_text = _TEMPLATE_SEARCH_PROMPT.format(search_prompt=search_prompt)
        display.text(prompt_text)
        
        while True:
            # Show current filtered options
            if len(filtered_options) != len(options):
                count_text = _TEMPLATE_FILTERED_COUNT.format(
                    count=len(filtered_options)
                )
                display.text(_PREFIX_NEWLINE + count_text)
            
            for i, option in enumerate(filtered_options):
                display.text(self._format_option_item(i, option))

            # Get search or selection
            choice = display.read_string(_PROMPT_DEFAULT)
            
            if choice.startswith(_PREFIX_SEARCH):
                # Search mode
                search_term = choice[1:].lower()
                filtered_options = [
                    opt for opt in options 
                    if search_term in str(opt).lower()
                ]
                
                if not filtered_options:
                    display.warning(_WARN_NO_MATCHES)
                    filtered_options = options.copy()
                
                continue
            
            # Selection mode - validate digit and range
            self._log_user_input(choice)
            
            if not self._validate_digit_input(choice, display):
                self._show_error(display, _ERR_INVALID_SEARCH)
                continue

            index = int(choice)
            if not self._validate_index_range(index, filtered_options, display):
                continue

            selected = filtered_options[index]
            self.logger.debug(_LOG_SELECTED_SEARCH, selected)
            return selected

    # ========================================================================
    # Private Helper Methods (DRY)
    # ========================================================================

    def _validate_digit_input(
        self,
        choice: str,
        display: Any
    ) -> bool:
        """
        Validate that input is a digit.
        
        Args
        ----
        choice : str
            User input to validate
        display : Any
            Display adapter for error messages
        
        Returns
        -------
        bool
            True if input is digit, False otherwise
        
        Notes
        -----
        DRY Helper: Eliminates 2 duplications (lines 44, 138 in original)
        """
        if not choice.isdigit():
            self.logger.debug(_LOG_INVALID_DIGIT)
            self._show_error(display, _ERR_INVALID_DIGIT)
            return False
        return True

    def _validate_index_range(
        self,
        index: int,
        options: List[str],
        display: Any
    ) -> bool:
        """
        Validate that index is within valid range.
        
        Args
        ----
        index : int
            Index to validate
        options : List[str]
            Options list to check bounds against
        display : Any
            Display adapter for error messages
        
        Returns
        -------
        bool
            True if index is valid, False otherwise
        
        Notes
        -----
        DRY Helper: Eliminates 3 duplications (lines 50, 84, 143 in original)
        """
        if index < 0 or index >= len(options):
            self.logger.debug(_LOG_OUT_OF_RANGE, index)
            self._show_error(display, _ERR_OUT_OF_RANGE)
            return False
        return True

    def _log_user_input(self, choice: str) -> None:
        """
        Log raw user input.
        
        Args
        ----
        choice : str
            User input to log
        
        Notes
        -----
        DRY Helper: Eliminates 3 duplications (lines 42, 77, 148 in original)
        Logs at debug level for troubleshooting user interactions.
        """
        self.logger.debug(_LOG_RAW_INPUT, choice)

    def _format_option_item(self, index: int, option: str) -> str:
        """
        Format option for display.
        
        Args
        ----
        index : int
            Option index
        option : str
            Option text
        
        Returns
        -------
        str
            Formatted option string: "  [index] option"
        
        Notes
        -----
        DRY Helper: Eliminates 2 duplications (lines 118, implicit)
        Provides consistent formatting across all display methods.
        """
        return _TEMPLATE_OPTION_ITEM.format(index=index, option=option)

    def _show_error(self, display: Any, message: str) -> None:
        """
        Show error with consistent formatting.
        
        Args
        ----
        display : Any
            Display adapter for error output
        message : str
            Error message to display
        
        Notes
        -----
        DRY Helper: Eliminates 5 duplications of display.error() with newline
        Ensures consistent error formatting across all validation failures.
        """
        display.error(_PREFIX_NEWLINE + message)

    def _transform_delta_link(self, selected: str) -> Dict[str, Any]:
        """
        Transform $BlockName into zLink dict for same-file navigation.
        
        Detects $ prefix in menu selection and constructs a zLink path to the
        target block in the SAME file. This enables inline navigation without
        requiring intermediate keys or zDelta syntax.
        
        Architecture:
            - Delegates to existing zLink subsystem (no duplication)
            - Constructs full path: @.VaFolder.zVaFile.BlockName
            - Returns zLink dict for dispatch to handle
        
        Args
        ----
        selected : str
            Menu selection with $ prefix (e.g., "$zAbout")
        
        Returns
        -------
        Dict[str, Any]
            zLink navigation dict: {zLink: "@.UI.zUI.index.zAbout"}
        
        Examples
        --------
        Transform block navigation::
        
            # Menu: ["$zHome", "$zAbout"]
            # User selects: [1] $zAbout
            # Input: "$zAbout"
            # Output: {zLink: "@.UI.zUI.index.zAbout"}
        
        Full flow::
        
            1. Menu shows: [0] $zHome, [1] $zAbout
            2. User enters: 1
            3. selected = "$zAbout"
            4. _transform_delta_link("$zAbout")
            5. Returns: {zLink: "@.UI.zUI.index.zAbout"}
            6. Dispatch handles via existing zLink subsystem
            7. Navigates to zAbout block in same file
        
        Notes
        -----
        - Reuses zLink subsystem (no redundant navigation logic)
        - Constructs full file path from session
        - Strips $ prefix before building path
        - Falls back to empty strings if session values missing
        
        Session Keys Used
        -----------------
        - zVaFolder: Folder containing current file (e.g., "@.UI")
        - zVaFile: Current file name (e.g., "zUI.index")
        
        Path Construction
        -----------------
        Format: @.{VaFolder}.{zVaFile}.{BlockName}
        Example: @.UI.zUI.index.zAbout
        
        Without folder: {zVaFile}.{BlockName}
        Example: zUI.index.zAbout
        """
        # Strip $ prefix to get block name
        block_name = selected[1:] if selected.startswith(_PREFIX_BLOCK_DELTA) else selected
        
        # Get current file context from session
        session = self.zcli.session
        zVaFolder = session.get(SESSION_KEY_VAFOLDER, "")
        zVaFile = session.get(SESSION_KEY_VAFILE, "")
        
        # Construct zLink path for same-file navigation
        # Format: @.VaFolder.zVaFile.BlockName
        if zVaFolder and zVaFile:
            # Full path with folder
            if zVaFolder.startswith("@.") or zVaFolder == "@":
                # Folder already has @. prefix (e.g., "@.UI") OR is root (@)
                zLink_path = f"{zVaFolder}.{zVaFile}.{block_name}"
            else:
                # Add @. prefix to folder
                zLink_path = f"@.{zVaFolder}.{zVaFile}.{block_name}"
        elif zVaFile:
            # Just file + block (no folder)
            zLink_path = f"{zVaFile}.{block_name}"
        else:
            # Fallback: just block name (might fail, but zLink will log error)
            zLink_path = block_name
        
        self.logger.debug(f"[MenuInteraction] Delta link transformed: {selected} → zLink({zLink_path})")
        
        # Return zLink dict (dispatch will handle via zLink subsystem)
        return {"zLink": zLink_path}
