# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_advanced.py
"""
AdvancedData Event Package - Database Query Results with Pagination & Formatting.

                              ARCHITECTURE OVERVIEW

This module provides advanced data display capabilities for zCLI, specifically
designed for database query results from the zData subsystem. It consists of
two main components:

1. **Pagination Helper Class**
   - Standalone utility for slicing data with limit/offset parameters
   - Supports 3 pagination modes: no limit (all), negative limit (last N), 
     positive limit + offset (standard pagination)
   - Returns comprehensive metadata: items, total, showing_start, showing_end, has_more

2. **AdvancedData Event Package**
   - Provides zTable() method for formatted table display
   - Composes with BasicOutputs (header, text) and Signals (warning, info)
   - Handles both Terminal (formatted ASCII table) and Bifrost (clean JSON) modes
   - Primary consumer: zData subsystem (query result display)


                           WHY "ADVANCED" DATA?

AdvancedData is "advanced" compared to BasicData because it handles:
  • Tabular data (rows + columns) vs. simple lists/JSON
  • Pagination logic (limit/offset) for large datasets
  • Column-aware formatting (headers, alignment, truncation)
  • Dual-mode rendering (Terminal ASCII tables vs. Bifrost clean data)

Comparison:
  BasicData:  display.list(items, style="bullet")
  AdvancedData: display.zTable(title, columns, rows, limit=20, offset=0)


                           PAGINATION ALGORITHM

The Pagination helper supports 3 modes:

**Mode 1: No Limit (Show All)**
  - Input:  paginate(data, limit=None)
  - Output: All items, showing_start=1, showing_end=len(data), has_more=False
  - Use Case: Small datasets (< 50 rows)

**Mode 2: Negative Limit (Last N Items)**
  - Input:  paginate(data, limit=-10)
  - Output: Last 10 items, showing_start=len(data)-9, showing_end=len(data)
  - Use Case: "Show me the last 10 log entries"

**Mode 3: Positive Limit + Offset (Standard Pagination)**
  - Input:  paginate(data, limit=20, offset=40)
  - Output: Items 41-60 (page 3), showing_start=41, showing_end=60, has_more=True
  - Use Case: Standard query result pagination


                         TERMINAL VS. BIFROST RENDERING

**Terminal Mode (ASCII Table):**
  - Formatted table with box characters (─ separator)
  - Fixed-width columns (15 chars, truncate with "...")
  - Colored headers (CYAN)
  - Pagination footer ("... 23 more rows")
  - Composes with BasicOutputs.header() and BasicOutputs.text()

**Bifrost Mode (Clean JSON Event):**
  - Send raw event: {"event": "zTable", "title": ..., "columns": ..., "rows": ...}
  - Frontend handles rendering (Material-UI DataGrid, AG Grid, etc.)
  - No formatting/truncation (send full data)
  - Bifrost handles pagination UI


                         ZDATA SUBSYSTEM INTEGRATION

**Primary Use Case: Database Query Results**

AdvancedData is the display layer for zData's query execution. Typical workflow:

  1. User runs SQL query via zData.query("SELECT * FROM users LIMIT 20")
  2. zData executes query, fetches results as list of dicts
  3. zData formats results: title="Query Results", columns=[...], rows=[...]
  4. zData calls display.zTable(title, columns, rows, limit=20, offset=0)
  5. AdvancedData renders table in Terminal or sends event to Bifrost

**Current zData Integration Features:**
  • Pagination: zData respects limit/offset for large result sets
  • Column headers: zData sends column names from SQL cursor description
  • Row formatting: zData sends rows as dicts (column_name: value)
  • Empty results: AdvancedData shows "No rows to display" via Signals

**Current Limitations (Fixed Column Width):**
  • All columns fixed at 15 characters (no auto-sizing)
  • All data types rendered as strings (no special formatting for numbers/dates)
  • No data type awareness (ints, floats, dates, booleans, NULLs all → str)
  • Truncation is naive (just "..." at end, no smart truncation for UUIDs/IDs)

**Usage Statistics (Typical zData Queries):**
  • Small queries: 1-10 columns, 5-50 rows (no pagination)
  • Medium queries: 5-20 columns, 50-200 rows (pagination recommended)
  • Large queries: 5-20 columns, 200+ rows (pagination required)
  • Wide queries: 20+ columns (horizontal scrolling issues in Terminal)


                  WEEK 6.6 INTEGRATION ROADMAP (FUTURE ENHANCEMENTS)

⚠️  The following enhancements should be implemented in Week 6.6 (zData refactor),
    NOT in Week 6.4. This module's Week 6.4 scope is industry-grade refactoring
    (type hints, constants, docstrings) WITHOUT adding new features.

**Enhancement 1: Column Width Auto-sizing**
  - Calculate optimal width per column based on max(header_len, max_content_len)
  - Support min_width/max_width constraints (e.g., min=8, max=50)
  - Smart truncation for IDs/UUIDs (show first 8 + "..." + last 4 chars)
  - Add column_widths parameter to zTable()

**Enhancement 2: Data Type Formatting**
  - Numbers: Right-align, thousands separators (1234567 → "1,234,567")
  - Dates: strftime formatting (datetime → "2025-10-30 14:35:22")
  - Booleans: Show as ✓/✗ symbols or "Yes"/"No" text
  - NULLs: Display as "(null)" in gray color or empty cell
  - Add column_types parameter to zTable() (e.g., ["int", "str", "date", "bool"])

**Enhancement 3: Pagination Controls (Terminal Interactive Mode)**
  - Show "Page 1 of 5 (Showing 1-20 of 87 rows)" in footer
  - Add navigation hints: "[n]ext page, [p]revious, [#] jump to page, [q]uit"
  - Wait for keypress, handle pagination commands interactively
  - Add interactive=True parameter to zTable()

**Enhancement 4: Export Support**
  - Add export_csv(filename) method: Export table as CSV file
  - Add export_json(filename) method: Export table as JSON array
  - Add copy_to_clipboard() method: Copy as TSV (Tab-Separated Values)
  - Integrate with zData query result actions menu

**Enhancement 5: Bifrost Mode Enhancements**
  - Send column metadata: {"name": "id", "type": "int", "nullable": False}
  - Support client-side sorting: Send sort instructions via WebSocket
  - Support client-side filtering: WHERE-like expressions in frontend
  - Support editable cells: Two-way binding for UPDATE operations
  - Add editable=True parameter and cell edit event handlers

**Example Week 6.6 API (After Enhancements):**

    # Current Week 6.4 API (unchanged):
    display.zTable(
        title="Users",
        columns=["id", "name", "email", "created_at"],
        rows=[{"id": 1, "name": "Alice", ...}, ...],
        limit=20,
        offset=0,
        show_header=True
    )

    # Future Week 6.6 API (with enhancements):
    display.zTable(
        title="Users",
        columns=["id", "name", "email", "created_at", "is_active"],
        rows=[{"id": 1, "name": "Alice", ...}, ...],
        limit=20,
        offset=0,
        show_header=True,
        column_types=["int", "str", "str", "datetime", "bool"],  # NEW
        column_widths={"id": 8, "name": 20, "email": 30},       # NEW
        interactive=True,                                         # NEW
        editable=True                                            # NEW (Bifrost)
    )


                              COMPOSITION PATTERN

AdvancedData composes with two other event packages (set by zEvents after init):

  1. **BasicOutputs** (Foundation Layer)
     - Used for: header() - table title, text() - formatted rows
     - Why: Provides consistent header/text styling across all events
     - Lines: 104-110 (header), 113-116 (column headers), 125-126 (rows)

  2. **Signals** (User Feedback Layer)
     - Used for: warning() - no columns, info() - no rows, info() - pagination footer
     - Why: Provides consistent colored feedback messages
     - Lines: 95-97 (warning), 120-121 (info), 130-134 (info)

This composition ensures AdvancedData doesn't duplicate formatting/coloring logic.


                              LAYER POSITION

Layer 1 (zDisplay):
  zDisplay.py → display_events.py → display_event_advanced.py (AdvancedData)
                                  ↓
                     Composes: BasicOutputs + Signals
                                  ↓
                     Delegates to: display_primitives.py (I/O)


                              THREAD SAFETY

AdvancedData is thread-safe when used through zDisplay singleton:
  - No mutable class-level state
  - Pagination helper is stateless (static method)
  - All state stored in instance attributes (per-display instance)
  - Composition references (BasicOutputs, Signals) set once during initialization


                                 USAGE EXAMPLES

**Example 1: Simple Query Results (No Pagination)**

    # zData executes: SELECT * FROM users LIMIT 10
    display.zTable(
        title="Recent Users",
        columns=["id", "username", "email"],
        rows=[
            {"id": 1, "username": "alice", "email": "alice@example.com"},
            {"id": 2, "username": "bob", "email": "bob@example.com"},
        ],
        show_header=True
    )

    # Terminal output:
    # 
    #  Recent Users (showing 1-2 of 2)
    #  id             username       email
    #  1              alice          alice@example...
    #  2              bob            bob@example.com


**Example 2: Paginated Results (Limit + Offset)**

    # zData executes: SELECT * FROM orders LIMIT 20 OFFSET 40
    display.zTable(
        title="Orders",
        columns=["id", "customer", "total", "status"],
        rows=[...],  # 20 rows
        limit=20,
        offset=40,
        show_header=True
    )

    # Terminal output:
    # 
    #  Orders (showing 41-60 of 127)
    #  id             customer       total          status
    #  41             Alice          $125.50        shipped
    #  ...
    #  60             Zara           $89.99         pending
    #  
    #  ℹ  ... 67 more rows


                             MODULE CONSTANTS
"""

from typing import Any, Optional, List, Dict, Union

# Module Constants

# Event name
_EVENT_ZTABLE: str = "zTable"

# Pagination metadata dictionary keys
_KEY_ITEMS: str = "items"
_KEY_TOTAL: str = "total"
KEY_SHOWING_START: str = "showing_start"
KEY_SHOWING_END: str = "showing_end"
KEY_HAS_MORE: str = "has_more"

# zTable event dictionary keys
KEY_TITLE: str = "title"
KEY_COLUMNS: str = "columns"
KEY_ROWS: str = "rows"
KEY_LIMIT: str = "limit"
KEY_OFFSET: str = "offset"
KEY_SHOW_HEADER: str = "show_header"

# Default values
DEFAULT_COL_WIDTH: int = 15
DEFAULT_OFFSET: int = 0
DEFAULT_SHOWING_START: int = 1
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

# Navigation constants (interactive mode)
NAV_PROMPT: str = "Navigate: [n]ext | [p]revious | [f]irst | [l]ast | [#] jump | [q]uit: "
NAV_COMMANDS: set = {"n", "p", "f", "l", "q"}
NAV_INVALID: str = "Invalid command. Use: n, p, f, l, # (page number), or q"
NAV_ALREADY_FIRST: str = "Already on first page"
NAV_ALREADY_LAST: str = "Already on last page"
NAV_INVALID_PAGE: str = "Invalid page. Enter 1-{total_pages}"

# Characters
CHAR_SEPARATOR: str = "─"
_CHAR_SPACE: str = " "

# Pagination algorithm constants
PAGINATION_OFFSET_BASE: int = 1  # 1-based indexing for showing_start/showing_end

# Helper Class: Pagination


class Pagination:
    """
    Pagination Helper - Data Slicing with Limit/Offset Parameters.
    
    This is a standalone utility class for paginating list data using limit/offset
    parameters, similar to SQL LIMIT/OFFSET clauses. It returns both the paginated
    items and comprehensive metadata about the pagination state.
    
    **Algorithm Features:**
      • No Limit Mode: Return all items (limit=None)
      • Negative Limit Mode: Return last N items (limit=-10 → last 10)
      • Positive Limit + Offset Mode: Standard pagination (limit=20, offset=40 → items 41-60)
      • Pagination Metadata: showing_start, showing_end, has_more for UI display
    
    **Return Format:**
      {
          "items": [...]           # Paginated subset of data
          "total": 127             # Total item count
          "showing_start": 41      # 1-based index of first displayed item
          "showing_end": 60        # 1-based index of last displayed item
          "has_more": True         # True if more items exist beyond current page
      }
    
    **Use Cases:**
      • zData query results pagination (SELECT * FROM users LIMIT 20 OFFSET 40)
      • Large list display with "... 67 more rows" footer
      • "Show last 10 log entries" feature (negative limit)
    
    **Thread Safety:**
      This class uses only static methods and has no state, making it completely
      thread-safe and suitable for concurrent use.
    
    Example:
        # Standard pagination (page 3, 20 items per page)
        page_info = Pagination.paginate(all_rows, limit=20, offset=40)
        
        # Display results
        for row in page_info["items"]:
            print(row)
        
        # Show footer
        if page_info["has_more"]:
            print(f"... {page_info['total'] - page_info['showing_end']} more rows")
    """
    
    @staticmethod
    def paginate(
        data: List[Any],
        limit: Optional[int] = None,
        offset: int = DEFAULT_OFFSET
    ) -> Dict[str, Any]:
        """
        Paginate data with limit/offset and return dict with items and metadata.
        
        This method implements a 3-mode pagination algorithm:
        
        **Mode 1: No Limit (Show All)**
          - When limit=None, return all items
          - showing_start=1, showing_end=len(data), has_more=False
          - Use for small datasets (< 50 items)
        
        **Mode 2: Negative Limit (Last N Items)**
          - When limit < 0, return last abs(limit) items
          - Example: limit=-10 returns last 10 items
          - showing_start calculated as: max(1, total + limit + 1)
          - Use for "show last N log entries" features
        
        **Mode 3: Positive Limit + Offset (Standard Pagination)**
          - When limit > 0, return items from offset to offset+limit
          - Example: limit=20, offset=40 returns items 41-60 (page 3)
          - has_more=True if more items exist beyond current page
          - Use for standard query result pagination
        
        Args:
            data: List of items to paginate (any type)
            limit: Number of items to return (None=all, negative=last N, positive=from offset)
            offset: Starting index (0-based, default 0)
        
        Returns:
            Dictionary with 5 keys:
              - "items": List of paginated items
              - "total": Total item count
              - "showing_start": 1-based index of first displayed item (0 if empty)
              - "showing_end": 1-based index of last displayed item (0 if empty)
              - "has_more": True if more items exist beyond current page
        
        Examples:
            # No limit (show all)
            >>> Pagination.paginate([1, 2, 3, 4, 5], limit=None)
            {
                "items": [1, 2, 3, 4, 5],
                "total": 5,
                "showing_start": 1,
                "showing_end": 5,
                "has_more": False
            }
            
            # Negative limit (last 2 items)
            >>> Pagination.paginate([1, 2, 3, 4, 5], limit=-2)
            {
                "items": [4, 5],
                "total": 5,
                "showing_start": 4,
                "showing_end": 5,
                "has_more": False  # (has_more=True if limit=-2 but total=10)
            }
            
            # Positive limit + offset (page 2)
            >>> Pagination.paginate([1, 2, 3, 4, 5], limit=2, offset=2)
            {
                "items": [3, 4],
                "total": 5,
                "showing_start": 3,
                "showing_end": 4,
                "has_more": True  # Item 5 exists beyond current page
            }
            
            # Empty data
            >>> Pagination.paginate([], limit=10)
            {
                "items": [],
                "total": 0,
                "showing_start": 0,
                "showing_end": 0,
                "has_more": False
            }
        
        Notes:
            - showing_start and showing_end use 1-based indexing for human-readable display
            - Offset uses 0-based indexing (Python list slicing convention)
            - If data is empty, showing_start and showing_end are 0 (not 1)
            - has_more is calculated as: (offset + limit) < total
        """
        # Handle empty data
        if not data:
            return {
                _KEY_ITEMS: [],
                _KEY_TOTAL: 0,
                KEY_SHOWING_START: 0,
                KEY_SHOWING_END: 0,
                KEY_HAS_MORE: False
            }
        
        total = len(data)
        
        # Mode 1: No limit - show all
        if limit is None:
            return {
                _KEY_ITEMS: data,
                _KEY_TOTAL: total,
                KEY_SHOWING_START: PAGINATION_OFFSET_BASE,
                KEY_SHOWING_END: total,
                KEY_HAS_MORE: False
            }
        
        # Mode 2: Negative limit - from bottom (last N items)
        if limit < 0:
            items = data[limit:]  # Last N items (Python negative slicing)
            showing_start = max(PAGINATION_OFFSET_BASE, total + limit + PAGINATION_OFFSET_BASE)
            showing_end = total
            has_more = abs(limit) < total
            
            return {
                _KEY_ITEMS: items,
                _KEY_TOTAL: total,
                KEY_SHOWING_START: showing_start,
                KEY_SHOWING_END: showing_end,
                KEY_HAS_MORE: has_more
            }
        
        # Mode 3: Positive limit - from top with offset (standard pagination)
        start_idx = offset
        end_idx = offset + limit
        items = data[start_idx:end_idx]
        
        showing_start = start_idx + PAGINATION_OFFSET_BASE if items else 0
        showing_end = start_idx + len(items)
        has_more = end_idx < total
        
        return {
            _KEY_ITEMS: items,
            _KEY_TOTAL: total,
            KEY_SHOWING_START: showing_start,
            KEY_SHOWING_END: showing_end,
            KEY_HAS_MORE: has_more
        }


# Main Class: AdvancedData

class AdvancedData:
    """
    AdvancedData Event Package - Database Query Results with Pagination.
    
    This event package provides the zTable() method for displaying tabular data
    (database query results) with pagination, column headers, and dual-mode rendering
    (Terminal ASCII tables vs. Bifrost clean JSON events).
    
    **Primary Consumer: zData Subsystem**
      AdvancedData is designed specifically for zData's query result display:
        1. zData executes SQL query (SELECT * FROM users LIMIT 20 OFFSET 0)
        2. zData formats results as: title, columns (list of names), rows (list of dicts)
        3. zData calls display.zTable(title, columns, rows, limit, offset)
        4. AdvancedData renders table (Terminal) or sends event (Bifrost)
    
    **Composition with Other Event Packages:**
      AdvancedData composes with two foundational event packages:
        • BasicOutputs: For header() and text() rendering
        • Signals: For warning() and info() colored feedback messages
      
      These references are set by display_events.py after initialization to avoid
      circular imports and ensure clean dependency wiring.
    
    **Methods Provided:**
      1. zTable(title, columns, rows, limit, offset, show_header)
         - Display paginated table with column headers and row data
         - Terminal: Formatted ASCII table with fixed-width columns
         - Bifrost: Clean JSON event with raw data
      
      2. _format_row(row, columns, is_header) [Private Helper]
         - Format a single row for Terminal display
         - Handles dict vs. list rows, truncation, header coloring
    
    **Dual-Mode Rendering:**
      • Terminal Mode: Formatted ASCII table with BasicOutputs composition
      • Bifrost Mode: Clean JSON event sent via zPrimitives.send_gui_event()
    
    **Week 6.6 Integration Roadmap:**
      See module docstring for comprehensive list of future enhancements
      (column auto-sizing, data type formatting, pagination controls, export, etc.)
    
    Attributes:
        display: Reference to parent zDisplay instance
        zPrimitives: Direct reference to display_primitives for I/O
        zColors: Direct reference to colors module for ANSI coloring
        BasicOutputs: Composed event package (set after init by zEvents)
        Signals: Composed event package (set after init by zEvents)
        pagination: Internal Pagination helper instance
    
    Example:
        # Via zDisplay convenience delegate:
        display.zTable(
            title="User List",
            columns=["id", "username", "email", "created_at"],
            rows=[
                {"id": 1, "username": "alice", "email": "alice@example.com", "created_at": "2025-01-15"},
                {"id": 2, "username": "bob", "email": "bob@example.com", "created_at": "2025-01-16"},
            ],
            limit=20,
            offset=0,
            show_header=True
        )
    
    Thread Safety:
        AdvancedData is thread-safe when accessed through the zDisplay singleton.
        No mutable class-level state exists, and all state is stored in instance
        attributes that are set during initialization.
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
        Initialize AdvancedData with reference to parent display instance.
        
        Args:
            display_instance: Parent zDisplay instance (provides zPrimitives, zColors)
        
        Notes:
            - BasicOutputs and Signals are initially None
            - These will be set by display_events.py after zEvents initialization
            - This avoids circular import issues during event package composition
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        
        # Get references to other packages for composition
        # (set after zEvents initialization to avoid circular imports)
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self.Signals = None       # Will be set after zEvents initialization
        
        # Internal pagination helper
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
        
        This is the primary method of AdvancedData, designed for database query result
        display from the zData subsystem. It handles:
          • Pagination: Slice rows using limit/offset (via Pagination helper)
          • Interactive Navigation: Keyboard-driven page navigation (Terminal-only)
          • Terminal Rendering: Formatted ASCII table with column headers, separators
          • Bifrost Rendering: Clean JSON event with raw data
          • Empty State: "No columns"/"No rows" messages via Signals
          • Pagination Footer: "... N more rows" via Signals
        
        **Workflow:**
        
        1. Try Bifrost Mode First:
           - Send clean JSON event: {"event": "zTable", "title": ..., "columns": ..., "rows": ...}
           - If successful (GUI mode active), return immediately
        
        2. Terminal Mode (Fallback):
           - Validate columns exist (show warning if missing)
           - Paginate rows using Pagination helper
           - Display title + pagination info via BasicOutputs.header()
           - Display column headers (if show_header=True) via BasicOutputs.text()
           - Display separator line (─ characters)
           - Display formatted rows via _format_row() + BasicOutputs.text()
           - Display "No rows" message (if empty) via Signals.info()
           - Display pagination footer (if has_more) via Signals.info()
           - If interactive=True, enter navigation loop with keyboard commands
        
        **Terminal Output Example:**
        
            
             User List (showing 1-5 of 127)
             id             username       email          created_at
             1              alice          alice@examp... 2025-01-15
             2              bob            bob@example... 2025-01-16
             3              charlie        charlie@exa... 2025-01-17
             4              diana          diana@examp... 2025-01-18
             5              eve            eve@example... 2025-01-19
             
             ℹ  ... 122 more rows
            
        
        **Bifrost Event Format:**
        
            {
                "event": "zTable",
                "title": "User List",
                "columns": ["id", "username", "email", "created_at"],
                "rows": [
                    {"id": 1, "username": "alice", "email": "alice@example.com", "created_at": "2025-01-15"},
                    ...
                ],
                "limit": 20,
                "offset": 0,
                "show_header": True
            }
        
        **zData Integration:**
        
        This method is typically called by zData after executing a query:
        
            # zData internal workflow:
            cursor = db.execute("SELECT id, username, email FROM users LIMIT 20")
            columns = [desc[0] for desc in cursor.description]  # Column names
            rows = cursor.fetchall()  # List of dicts
            
            # Call AdvancedData.zTable()
            display.zTable(
                title=f"Query Results ({len(rows)} rows)",
                columns=columns,
                rows=rows,
                limit=20,
                offset=0
            )
        
        Args:
            title: Table title (displayed in header)
            columns: List of column names (e.g., ["id", "username", "email"])
            rows: List of row data (dicts or lists, typically dicts from SQL cursor)
            limit: Maximum rows to display (None=all, negative=last N, positive=from offset)
            offset: Starting row index (0-based, default 0)
            show_header: Whether to display column headers (default True)
            interactive: Enable keyboard navigation in Terminal mode (default False)
                        Commands: [n]ext, [p]revious, [f]irst, [l]ast, [#] jump to page, [q]uit
                        Only works with limit > 0 (pagination must be enabled)
                        Ignored in Bifrost mode
        
        Returns:
            None (output is rendered to Terminal or sent to Bifrost)
        
        Examples:
            # Simple table (no pagination)
            display.zTable(
                title="Recent Users",
                columns=["id", "username"],
                rows=[{"id": 1, "username": "alice"}, {"id": 2, "username": "bob"}]
            )
            
            # Paginated table (page 3, 20 rows per page)
            display.zTable(
                title="All Users",
                columns=["id", "username", "email"],
                rows=all_users,  # Full dataset
                limit=20,
                offset=40  # Skip first 40 rows (pages 1-2)
            )
            
            # Last 10 log entries
            display.zTable(
                title="Recent Logs",
                columns=["timestamp", "level", "message"],
                rows=all_logs,
                limit=-10  # Negative limit = last N rows
            )
            
            # Interactive navigation (Terminal-only)
            display.zTable(
                title="User Database",
                columns=["id", "name", "email"],
                rows=all_users,
                limit=20,
                offset=0,
                interactive=True  # Enable keyboard navigation (n/p/f/l/#/q)
            )
        
        Notes:
            - Column width is fixed at 15 characters in Terminal mode (Week 6.6: auto-sizing)
            - All data types are converted to strings (Week 6.6: type-aware formatting)
            - Truncation is naive ("..." at end, Week 6.6: smart truncation for UUIDs/IDs)
            - Interactive pagination available with interactive=True (Terminal-only)
            - Bifrost mode sends raw data (frontend handles rendering/pagination)
        
        Week 6.6 Enhancements (Remaining):
            - Add column_types parameter for data type formatting
            - Add column_widths parameter for auto-sizing
            - Add editable parameter for Bifrost cell editing
        """
        # Try Bifrost mode first - send clean event
        if self.zPrimitives.send_gui_event(_EVENT_ZTABLE, {
            KEY_TITLE: title,
            KEY_COLUMNS: columns,
            KEY_ROWS: rows,
            KEY_LIMIT: limit,
            KEY_OFFSET: offset,
            KEY_SHOW_HEADER: show_header,
            "interactive": interactive  # Enable frontend navigation controls
        }):
            return  # Bifrost event sent successfully
        
        # Terminal mode - display formatted table
        
        # Validate columns exist
        if not columns:
            self._signal_warning(MSG_NO_COLUMNS, indent=0)
            return
        
        # Paginate rows using Pagination helper
        page_info = self.pagination.paginate(rows, limit, offset)
        paginated_rows = page_info[_KEY_ITEMS]
        
        # Render initial page
        self._render_table_page(title, columns, page_info, paginated_rows, show_header)
        
        # Interactive navigation (Terminal-only)
        if interactive and limit and limit > 0:
            total_rows = len(rows)
            page_size = limit
            total_pages = (total_rows + page_size - 1) // page_size
            current_page = (offset // page_size) + 1
            
            while True:
                # Show navigation prompt
                command = self.zPrimitives.read_string(NAV_PROMPT).strip().lower()
                
                # Parse command
                if command == "q":
                    break
                elif command == "n":
                    # Next page
                    if current_page < total_pages:
                        current_page += 1
                    else:
                        self._signal_warning(NAV_ALREADY_LAST, indent=0)
                        continue
                elif command == "p":
                    # Previous page
                    if current_page > 1:
                        current_page -= 1
                    else:
                        self._signal_warning(NAV_ALREADY_FIRST, indent=0)
                        continue
                elif command == "f":
                    # First page
                    current_page = 1
                elif command == "l":
                    # Last page
                    current_page = total_pages
                elif command.isdigit():
                    # Jump to page number
                    page_num = int(command)
                    if 1 <= page_num <= total_pages:
                        current_page = page_num
                    else:
                        self._signal_warning(
                            NAV_INVALID_PAGE.format(total_pages=total_pages),
                            indent=0
                        )
                        continue
                else:
                    self._signal_warning(NAV_INVALID, indent=0)
                    continue
                
                # Calculate new offset and re-display table
                current_offset = (current_page - 1) * page_size
                page_info = self.pagination.paginate(rows, limit, current_offset)
                paginated_rows = page_info[_KEY_ITEMS]
                
                # Re-display table
                self._render_table_page(title, columns, page_info, paginated_rows, show_header)
    
    #                           HELPER METHODS
    
    def _render_table_page(
        self,
        title: str,
        columns: List[str],
        page_info: Dict[str, Any],
        paginated_rows: List[Union[Dict[str, Any], List[Any]]],
        show_header: bool
    ) -> None:
        """
        Render a single page of table data to Terminal.
        
        This helper method renders one page of a paginated table, including:
          • Title header with pagination info (showing X-Y of Z)
          • Column headers (if show_header=True)
          • Formatted rows
          • Pagination footer (if more rows exist)
        
        Used by zTable() for initial display and interactive navigation re-display.
        
        Args:
            title: Table title
            columns: List of column names
            page_info: Pagination metadata dict from Pagination.paginate()
            paginated_rows: Rows to display (already sliced)
            show_header: Whether to show column headers
        
        Returns:
            None (output is rendered to Terminal)
        """
        # Display title with pagination info
        self._output_text("", break_after=False)
        if self.BasicOutputs:
            self.BasicOutputs.header(
                MSG_SHOWING_RANGE.format(
                    title=title,
                    start=page_info[KEY_SHOWING_START],
                    end=page_info[KEY_SHOWING_END],
                    total=page_info[_KEY_TOTAL]
                ),
                color=DEFAULT_HEADER_COLOR,
                style=DEFAULT_TABLE_STYLE
            )
        
        # Display column headers if requested
        if show_header:
            header_row = self._format_row(columns, columns, is_header=True)
            self._output_text(header_row, indent=1, break_after=False)
            self._output_text(CHAR_SEPARATOR * DEFAULT_SEPARATOR_WIDTH, indent=1, break_after=False)
        
        # Display rows
        if not paginated_rows:
            self._signal_info(MSG_NO_ROWS, indent=1)
        else:
            for row in paginated_rows:
                formatted_row = self._format_row(row, columns)
                self._output_text(formatted_row, indent=1, break_after=False)
        
        # Display pagination footer
        if page_info[KEY_HAS_MORE]:
            remaining_count = page_info[_KEY_TOTAL] - page_info[KEY_SHOWING_END]
            self._signal_info(
                MSG_MORE_ROWS.format(count=remaining_count),
                indent=1
            )
        
        # Add closing blank line
        self._output_text("", break_after=False)
    
    def _format_row(
        self,
        row: Union[Dict[str, Any], List[Any], Any],
        columns: List[str],
        is_header: bool = False
    ) -> str:
        """
        Format a single row for display with given columns and optional header formatting.
        
        This private helper method formats a single row (dict, list, or scalar) into
        a fixed-width ASCII string suitable for Terminal display. It handles:
          • Dict rows: Extract values by column names (typical for SQL query results)
          • List rows: Use values as-is (in order)
          • Scalar rows: Single value → single column
          • Truncation: Values exceeding column width are truncated with "..."
          • Header coloring: CYAN color for column headers
          • Padding: All values left-justified to column width
        
        **Algorithm:**
        
        1. Convert row to list of string values:
           - Dict: [row.get(col, "") for col in columns]
           - List: [str(val) for val in row]
           - Scalar: [str(row)]
        
        2. For each value:
           - Truncate if len(value) > col_width: value[:12] + "..."
           - Apply CYAN color if is_header=True
           - Left-justify to col_width
        
        3. Join cells with space separator
        
        **Column Width (Fixed in Week 6.4):**
        
        All columns use a fixed width of 15 characters. This will be enhanced in
        Week 6.6 to support:
          • Auto-sizing based on max(header_len, max_content_len)
          • Per-column width constraints (min_width, max_width)
          • Smart truncation for UUIDs/IDs (show first 8 + "..." + last 4)
        
        **Truncation Behavior:**
        
        If a value exceeds 15 characters:
          • "alice@example.com" → "alice@examp..."  (naive, cuts at 12 chars)
          
        Week 6.6 smart truncation:
          • UUID: "550e8400-e29b-41d4-a716-446655440000" → "550e8400...40000"
          • Long text: "This is a very long description" → "This is a v..."
          • URLs: "https://example.com/api/v1/users/123" → "https://...s/123"
        
        Args:
            row: Row data (dict with column keys, list of values, or scalar value)
            columns: List of column names (used to extract dict values in order)
            is_header: Whether this is a header row (applies CYAN coloring)
        
        Returns:
            Formatted row string with fixed-width columns joined by spaces
        
        Examples:
            # Dict row (typical SQL query result)
            >>> _format_row(
            ...     {"id": 1, "username": "alice", "email": "alice@example.com"},
            ...     ["id", "username", "email"]
            ... )
            "1              alice          alice@examp...  "
            
            # List row
            >>> _format_row([1, "alice", "alice@example.com"], ["id", "username", "email"])
            "1              alice          alice@examp...  "
            
            # Header row (with CYAN coloring)
            >>> _format_row(["id", "username", "email"], ["id", "username", "email"], is_header=True)
            "\033[36mid\033[0m             \033[36musername\033[0m       \033[36memail\033[0m          "
            
            # Scalar row (single column)
            >>> _format_row(42, ["value"])
            "42             "
        
        Notes:
            - Column width is fixed at 15 characters (DEFAULT_COL_WIDTH)
            - Truncation uses "..." suffix (DEFAULT_TRUNCATE_SUFFIX)
            - Header coloring uses CYAN (DEFAULT_HEADER_COLOR)
            - Values are left-justified (.ljust())
            - Missing dict keys default to empty string ("")
        """
        # Convert row to list of string values
        if isinstance(row, dict):
            # Dict row: Extract values by column names (SQL query result format)
            row_values = [str(row.get(col, "")) for col in columns]
        elif isinstance(row, list):
            # List row: Use values as-is
            row_values = [str(val) for val in row]
        else:
            # Scalar row: Single value
            row_values = [str(row)]
        
        # Format each cell
        formatted_cells = []
        for i, value in enumerate(row_values):
            # Truncate if too long
            if len(value) > DEFAULT_COL_WIDTH:
                truncate_length = DEFAULT_COL_WIDTH - len(DEFAULT_TRUNCATE_SUFFIX)
                value = value[:truncate_length] + DEFAULT_TRUNCATE_SUFFIX
            
            # Apply header formatting (CYAN color for headers)
            if is_header:
                value = f"{self.zColors.CYAN}{value}{self.zColors.RESET}"
            
            # Pad to column width (left-justified)
            formatted_cells.append(value.ljust(DEFAULT_COL_WIDTH))
        
        # Join cells with space separator
        return _CHAR_SPACE.join(formatted_cells)
    
    def _output_text(self, content: str, indent: int = 0, break_after: bool = True) -> None:
        """
        Output text via BasicOutputs (DRY helper to avoid repeated checks).
        
        Args:
            content: Text content to display
            indent: Indentation level (0-3)
            break_after: Whether to add line break after text
        """
        if self.BasicOutputs:
            self.BasicOutputs.text(content, indent=indent, break_after=break_after)
    
    def _signal_warning(self, message: str, indent: int = 0) -> None:
        """
        Display warning signal via Signals (DRY helper to avoid repeated checks).
        
        Args:
            message: Warning message to display
            indent: Indentation level (0-3)
        """
        if self.Signals:
            self.Signals.warning(message, indent=indent)
    
    def _signal_info(self, message: str, indent: int = 0) -> None:
        """
        Display info signal via Signals (DRY helper to avoid repeated checks).
        
        Args:
            message: Info message to display
            indent: Indentation level (0-3)
        """
        if self.Signals:
            self.Signals.info(message, indent=indent)
