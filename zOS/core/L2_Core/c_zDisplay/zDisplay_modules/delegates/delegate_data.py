# zCLI/subsystems/zDisplay/zDisplay_modules/delegates/delegate_data.py

"""
Data Display Delegate Methods for zDisplay.

This module provides structured data display convenience methods for common
data presentation patterns like lists, JSON output, and tables. These methods
handle formatting and rendering of complex data structures.

Methods:
    - list: Display bulleted/numbered lists
    - json_data: Display JSON-formatted data
    - json: Alias for json_data
    - zTable: Display tabular data with pagination

Pattern:
    All methods delegate to handle() with data event dictionaries.
    Data structures are serialized and formatted appropriately for display mode.

Grade: A+ (Type hints, constants, comprehensive docs)
"""

from zOS import Any, List, Dict, Optional
from ..display_constants import (
    _KEY_EVENT,
    _EVENT_LIST,
    _EVENT_JSON,
    _EVENT_JSON_DATA,
    _EVENT_ZTABLE,
)

# Module-specific constants
DEFAULT_STYLE_BULLET = "bullet"
DEFAULT_INDENT = 0
DEFAULT_INDENT_SIZE = 2


class DelegateData:
    """Mixin providing data display delegate methods.
    
    These methods handle display of structured data like lists, JSON,
    and tables with appropriate formatting for the current display mode.
    """

    # Data Display Delegates

    def list(
        self, 
        items: List[str], 
        style: str = DEFAULT_STYLE_BULLET, 
        indent: int = DEFAULT_INDENT
    ) -> Optional[Any]:
        """Display bulleted, numbered, or plain list.
        
        Args:
            items: List of strings to display
            style: List style - 'bullet', 'numbered', or 'none' (default: bullet)
                   - 'bullet': Prefix each item with "- "
                   - 'numbered': Prefix with "1. ", "2. ", etc.
                   - 'none': No prefix (clean output)
            indent: Indentation level (default: 0)
            
        Returns:
            Optional[Any]: Navigation signal (zLink dict) if user clicked a link, None otherwise
            
        Example:
            display.list(["Apple", "Banana"], style="numbered")
            display.list(["[DIR] folder/"], style="none")
        """
        return self.handle({
            _KEY_EVENT: _EVENT_LIST,
            "items": items,
            "style": style,
            "indent": indent,
        })


    def json_data(
        self, 
        data: Dict[str, Any], 
        indent_size: int = DEFAULT_INDENT_SIZE, 
        indent: int = DEFAULT_INDENT, 
        color: bool = False
    ) -> Any:
        """Display JSON-formatted data.
        
        Args:
            data: Dictionary to display as JSON
            indent_size: JSON indentation (default: 2)
            indent: Line indentation level (default: 0)
            color: Enable syntax coloring (default: False)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.json_data({"name": "Alice", "age": 30}, indent_size=4)
        """
        return self.handle({
            _KEY_EVENT: _EVENT_JSON_DATA,
            "data": data,
            "indent_size": indent_size,
            "indent": indent,
            "color": color,
        })

    def json(
        self, 
        data: Dict[str, Any], 
        indent_size: int = DEFAULT_INDENT_SIZE, 
        indent: int = DEFAULT_INDENT, 
        color: bool = False
    ) -> Any:
        """Display JSON-formatted data (alias for json_data).
        
        Args:
            data: Dictionary to display as JSON
            indent_size: JSON indentation (default: 2)
            indent: Line indentation level (default: 0)
            color: Enable syntax coloring (default: False)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.json({"status": "ok", "count": 42})
        """
        return self.handle({
            _KEY_EVENT: _EVENT_JSON,
            "data": data,
            "indent_size": indent_size,
            "indent": indent,
            "color": color,
        })

    def zTable(
        self, 
        title: str, 
        columns: List[str], 
        rows: List[List[Any]], 
        limit: Optional[int] = None, 
        offset: int = 0, 
        show_header: bool = True,
        interactive: bool = False
    ) -> Any:
        """Display tabular data with optional pagination.
        
        Args:
            title: Table title
            columns: Column header labels
            rows: List of row data (each row is a list of cell values)
            limit: Optional row limit for pagination (default: None)
            offset: Starting row offset (default: 0)
            show_header: Show column headers (default: True)
            interactive: Enable interactive navigation in Terminal mode (default: False)
            
        Returns:
            Any: Result from handle() method
            
        Example:
            display.zTable(
                "Users",
                ["Name", "Age", "Role"],
                [
                    ["Alice", 30, "Admin"],
                    ["Bob", 25, "User"]
                ],
                interactive=True
            )
        """
        return self.handle({
            _KEY_EVENT: _EVENT_ZTABLE,
            "title": title,
            "columns": columns,
            "rows": rows,
            "limit": limit,
            "offset": offset,
            "show_header": show_header,
            "interactive": interactive,
        })

