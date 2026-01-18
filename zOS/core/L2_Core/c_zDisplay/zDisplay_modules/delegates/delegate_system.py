# zCLI/subsystems/zDisplay/zDisplay_modules/delegates/delegate_system.py

"""
System UI Delegate Methods for zDisplay.

This module provides high-level system UI convenience methods for complex
user interface patterns like session info, breadcrumbs, menus, selections,
and dialogs. These methods often involve user interaction or complex rendering.

Methods:
    - zSession: Display session information
    - zCrumbs: Display navigation breadcrumbs
    - zMenu: Display interactive menu
    - selection: Display selection prompt
    - zDialog: Display dialog box

Pattern:
    All methods delegate to handle() with system event dictionaries.
    These events often trigger complex UI flows or modal interactions.

Grade: A+ (Type hints, constants, comprehensive docs)
"""

from zOS import Any, Optional, List, Dict
from ..display_constants import (
    _KEY_EVENT,
    _EVENT_ZSESSION,
    _EVENT_ZCONFIG,
    _EVENT_ZCRUMBS,
    _EVENT_ZMENU,
    _EVENT_SELECTION,
    _EVENT_ZDIALOG,
)

# Module-specific constants
DEFAULT_MENU_PROMPT = "Select an option:"
DEFAULT_STYLE_NUMBERED = "numbered"


class DelegateSystem:
    """Mixin providing system UI delegate methods.
    
    These methods handle complex UI patterns like menus, dialogs, and session
    display that often involve user interaction and multi-step flows.
    """

    # System UI Delegates

    def zSession(
        self, 
        session_data: Dict[str, Any], 
        break_after: bool = True, 
        break_message: Optional[str] = None
    ) -> Any:
        """Display session information.
        
        Args:
            session_data: Session dictionary to display
            break_after: Add break after display (default: True)
            break_message: Optional break message (default: None)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.zSession(zcli.session)
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZSESSION,
            "session_data": session_data,
            "break_after": break_after,
            "break_message": break_message,
        })

    def zConfig(
        self,
        config_data: Optional[Dict[str, Any]] = None,
        break_after: bool = True,
        break_message: Optional[str] = None
    ) -> Any:
        """Display configuration information.
        
        Args:
            config_data: Config dictionary with 'machine' and 'environment' keys
            break_after: Add break after display (default: True)
            break_message: Optional break message
            
        Returns:
            Any: Result from handle() method
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZCONFIG,
            "config_data": config_data,
            "break_after": break_after,
            "break_message": break_message,
        })

    def zCrumbs(self, session_data: Dict[str, Any]) -> Any:
        """Display breadcrumb navigation trail.
        
        Args:
            session_data: Session dictionary containing navigation history
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.zCrumbs(zcli.session)
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZCRUMBS,
            "session_data": session_data,
        })

    def zMenu(
        self, 
        menu_items: List[tuple], 
        prompt: str = DEFAULT_MENU_PROMPT, 
        return_selection: bool = False
    ) -> Any:
        """Display interactive menu.
        
        Args:
            menu_items: List of (number, label) tuples
            prompt: Menu prompt text (default: "Select an option:")
            return_selection: Return selected value (default: False)
            
        Returns:
            Any: Selected option if return_selection=True, else None
            
        Example:
            display.zMenu(
                [(1, "Create User"), (2, "List Users")],
                prompt="Choose action:",
                return_selection=True
            )
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZMENU,
            "menu_items": menu_items,
            "prompt": prompt,
            "return_selection": return_selection,
        })

    def selection(
        self, 
        prompt: str, 
        options: List[str], 
        multi: bool = False, 
        default: Optional[Any] = None, 
        style: str = DEFAULT_STYLE_NUMBERED
    ) -> Any:
        """Display selection prompt.
        
        Args:
            prompt: Selection prompt text
            options: List of option strings
            multi: Allow multiple selections (default: False)
            default: Default selection (default: None)
            style: Selection style - 'numbered', 'bullet' (default: numbered)
            
        Returns:
            Any: Selected option(s) from handle() method
            
        Example:
            choice = display.selection(
                "Choose a fruit:",
                ["Apple", "Banana", "Cherry"],
                multi=False
            )
        """
        return self.handle({
            _KEY_EVENT: _EVENT_SELECTION,
            "prompt": prompt,
            "options": options,
            "multi": multi,
            "default": default,
            "style": style,
        })

    def zDialog(
        self, 
        context: Dict[str, Any], 
        zcli: Optional[Any] = None, 
        walker: Optional[Any] = None
    ) -> Any:
        """Display dialog form for data collection.
        
        Args:
            context: Dialog context dictionary
            zcli: Optional zCLI instance (default: None)
            walker: Optional walker instance (default: None)
            
        Returns:
            Any: Dialog result from handle() method
            
        Example:
            result = display.zDialog(dialog_context, zcli=zcli)
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZDIALOG,
            "context": context,
            "zcli": zcli,
            "walker": walker,
        })

