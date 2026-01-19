# zCLI/L2_Core/c_zDisplay/zDisplay_modules/e_advanced/advanced_table.py
"""
Table Events - Database Query Result Display
==============================================

This module provides table rendering events for displaying database query
results with pagination, column headers, and dual-mode rendering (Terminal
ASCII tables vs. Bifrost clean JSON events).

Purpose:
    - Display tabular data from database queries
    - Handle pagination with limit/offset
    - Format columns with fixed width and truncation
    - Support both Terminal (ASCII) and Bifrost (JSON) modes

Public Methods:
    zTable(title, columns, rows, limit, offset, show_header, interactive)
        Display data table with optional pagination

Dependencies:
    - advanced_pagination: Pagination utility for data slicing
    - display_event_helpers: is_bifrost_mode, emit_websocket_event
    - display_primitives: zPrimitives for terminal I/O
    - display_constants: Event names, keys, defaults

Extracted From:
    display_event_advanced.py (lines 501-1049)
"""

from typing import Any, Optional, List, Union, Dict

# Import pagination utility
from .advanced_pagination import (
    Pagination,
    KEY_SHOWING_START,
    KEY_SHOWING_END,
    KEY_HAS_MORE,
    DEFAULT_OFFSET
)

# Import Tier 0 infrastructure helpers
from ..a_infrastructure.display_event_helpers import (
    is_bifrost_mode,
    emit_websocket_event
)

# zTable event dictionary keys
KEY_TITLE: str = "title"
KEY_COLUMNS: str = "columns"
KEY_ROWS: str = "rows"
KEY_LIMIT: str = "limit"
KEY_OFFSET: str = "offset"
KEY_SHOW_HEADER: str = "show_header"

# Default values
DEFAULT_COL_WIDTH: int = 15
DEFAULT_SEPARATOR_WIDTH: int = 60
DEFAULT_TRUNCATE_SUFFIX: str = "..."

# Colors and styles
DEFAULT_HEADER_COLOR: str = "CYAN"
DEFAULT_TABLE_STYLE: str = "full"

# Messages
MSG_NO_COLUMNS: str = "No columns defined for table"
MSG_NO_ROWS: str = "No rows to display"
MSG_MORE_ROWS: str = "... {count} more rows"
MSG_SHOWING_RANGE: str = "{title} (showing {start}-{end} of {total})"

# Characters
CHAR_SEPARATOR: str = "─"
_CHAR_SPACE: str = " "


class TableEvents:
    """
    Table rendering events for database query results.
    
    Provides zTable() for displaying tabular data with pagination,
    column headers, and dual-mode rendering.
    
    Composition:
        - zPrimitives: For terminal I/O
        - zColors: For colored output
        - BasicOutputs: For header/text rendering (set after zEvents init)
        - Signals: For warning/info messages (set after zEvents init)
        - Pagination: For data slicing
    
    Usage:
        # Via AdvancedData coordinator
        display.zTable(
            title="Query Results",
            columns=["id", "name", "email"],
            rows=[{"id": 1, "name": "Alice", "email": "alice@example.com"}],
            limit=20,
            offset=0
        )
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    zColors: Any
    BasicOutputs: Optional[Any]
    Signals: Optional[Any]
    pagination: Pagination
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize TableEvents with reference to parent display instance.
        
        Args:
            display_instance: Parent display instance (AdvancedData or zDisplay)
        
        Returns:
            None
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives if hasattr(display_instance, 'zPrimitives') else None
        self.zColors = display_instance.zColors if hasattr(display_instance, 'zColors') else None
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self.Signals = None       # Will be set after zEvents initialization
        self.pagination = Pagination()
    
    def zTable(
        self,
        title: str,
        columns: List[str],
        rows: List[Union[Dict[str, Any], List[Any]]],
        limit: Optional[int] = None,
        offset: int = DEFAULT_OFFSET,
        show_header: bool = True,
        interactive: bool = False
    ) -> None:
        """
        Display data table with optional pagination and formatting for Terminal/Bifrost modes.
        
        Args:
            title: Table title/heading
            columns: List of column names
            rows: List of rows (dicts or lists)
            limit: Number of rows to display (None=all)
            offset: Starting row index (0-based)
            show_header: Show column headers (default: True)
            interactive: Enable keyboard navigation (Terminal-only, default: False)
        
        Returns:
            None
        
        Terminal Mode:
            Renders formatted ASCII table with headers, separators, fixed-width columns
        
        Bifrost Mode:
            Sends clean JSON event with raw data for frontend rendering
        
        Usage:
            display.zTable(
                title="Users",
                columns=["id", "name", "email"],
                rows=[
                    {"id": 1, "name": "Alice", "email": "alice@example.com"},
                    {"id": 2, "name": "Bob", "email": "bob@example.com"}
                ],
                limit=20
            )
        """
        # Bifrost mode - send clean JSON event
        if is_bifrost_mode(self.display):
            event_data = {
                "event": "zTable",
                KEY_TITLE: title,
                KEY_COLUMNS: columns,
                KEY_ROWS: rows,
                KEY_LIMIT: limit,
                KEY_OFFSET: offset,
                KEY_SHOW_HEADER: show_header
            }
            emit_websocket_event(self.display, event_data)
            return
        
        # Terminal mode - render ASCII table
        # Validate columns
        if not columns:
            if self.Signals:
                self.Signals.warning(MSG_NO_COLUMNS)
            return
        
        # Paginate rows
        page_info = self.pagination.paginate(rows, limit=limit, offset=offset)
        paginated_rows = page_info["items"]
        
        # Check if we have rows to display
        if not paginated_rows:
            if self.Signals:
                self.Signals.info(MSG_NO_ROWS)
            return
        
        # Display table header with pagination info
        if page_info["total"] > len(paginated_rows):
            # Show pagination range in title
            title_with_range = MSG_SHOWING_RANGE.format(
                title=title,
                start=page_info[KEY_SHOWING_START],
                end=page_info[KEY_SHOWING_END],
                total=page_info["total"]
            )
        else:
            title_with_range = title
        
        # Render table
        self._render_table_page(title_with_range, columns, paginated_rows, show_header)
        
        # Show "more rows" footer if paginated
        if page_info[KEY_HAS_MORE]:
            remaining = page_info["total"] - page_info[KEY_SHOWING_END]
            more_msg = MSG_MORE_ROWS.format(count=remaining)
            if self.Signals:
                self.Signals.info(more_msg)
    
    def _render_table_page(
        self,
        title: str,
        columns: List[str],
        rows: List[Union[Dict[str, Any], List[Any]]],
        show_header: bool
    ) -> None:
        """Render a single page of table data in Terminal mode."""
        # Table header
        if self.BasicOutputs:
            self.BasicOutputs.header(title, color=DEFAULT_HEADER_COLOR, style=DEFAULT_TABLE_STYLE)
        
        # Column headers
        if show_header:
            header_row = _CHAR_SPACE.join([col[:DEFAULT_COL_WIDTH].ljust(DEFAULT_COL_WIDTH) for col in columns])
            self._output_text(header_row)
            
            # Separator
            separator = CHAR_SEPARATOR * min(DEFAULT_SEPARATOR_WIDTH, len(header_row))
            self._output_text(separator)
        
        # Data rows
        for row in rows:
            formatted_row = self._format_row(row, columns)
            self._output_text(formatted_row)
    
    def _format_row(
        self,
        row: Union[Dict[str, Any], List[Any]],
        columns: List[str]
    ) -> str:
        """Format a single row for terminal display."""
        values = []
        
        # Convert row to list of values
        if isinstance(row, dict):
            for col in columns:
                value = row.get(col, "")
                values.append(str(value) if value is not None else "")
        elif isinstance(row, list):
            values = [str(v) if v is not None else "" for v in row]
        else:
            values = [str(row)]
        
        # Truncate and pad values to fixed width
        formatted_values = []
        for value in values:
            if len(value) > DEFAULT_COL_WIDTH:
                # Truncate with "..."
                truncated = value[:DEFAULT_COL_WIDTH - len(DEFAULT_TRUNCATE_SUFFIX)] + DEFAULT_TRUNCATE_SUFFIX
                formatted_values.append(truncated)
            else:
                # Pad to fixed width
                formatted_values.append(value.ljust(DEFAULT_COL_WIDTH))
        
        return _CHAR_SPACE.join(formatted_values)
    
    def _output_text(self, content: str, indent: int = 0, break_after: bool = True) -> None:
        """Output text using BasicOutputs or zPrimitives fallback."""
        if self.BasicOutputs:
            self.BasicOutputs.text(content, indent=indent, break_after=break_after)
        elif self.zPrimitives:
            self.zPrimitives.line(content)
