# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_advanced.py
"""
AdvancedData Event Package - Database Query Results with Pagination & Formatting
=================================================================================

REFACTORING v2.0 (Phase 5 Complete):
    - Decomposed monolith (1,049 lines) into 2 specialized modules
    - Extracted Pagination utility for reuse across display system
    - Extracted TableEvents for focused table rendering
    - Composition pattern: AdvancedData orchestrates specialized modules

ARCHITECTURE OVERVIEW

This module provides advanced data display capabilities for zCLI, specifically
designed for database query results from the zData subsystem.

MODULE DECOMPOSITION (Phase 5):

    advanced_pagination.py  - Pagination utility (data slicing with limit/offset)
    advanced_table.py       - Table rendering events (zTable method)
    display_event_advanced.py (Coordinator) - Composes pagination + table modules

WHY "ADVANCED" DATA?

AdvancedData is "advanced" compared to BasicData because it handles:
  • Tabular data (rows + columns) vs. simple lists/JSON
  • Pagination logic (limit/offset) for large datasets
  • Column-aware formatting (headers, alignment, truncation)
  • Dual-mode rendering (Terminal ASCII tables vs. Bifrost clean data)

Comparison:
  BasicData:    display.list(items, style="bullet")
  AdvancedData: display.zTable(title, columns, rows, limit=20, offset=0)

PAGINATION ALGORITHM (3 Modes)

**Mode 1: No Limit (Show All)**
  Input:  paginate(data, limit=None)
  Output: All items, has_more=False
  Use: Small datasets (< 50 rows)

**Mode 2: Negative Limit (Last N Items)**
  Input:  paginate(data, limit=-10)
  Output: Last 10 items
  Use: "Show last 10 log entries"

**Mode 3: Positive Limit + Offset (Standard Pagination)**
  Input:  paginate(data, limit=20, offset=40)
  Output: Items 41-60 (page 3), has_more=True
  Use: Standard query result pagination

TERMINAL VS. BIFROST RENDERING

**Terminal Mode (ASCII Table):**
  - Formatted table with box characters (─ separator)
  - Fixed-width columns (15 chars, truncate with "...")
  - Colored headers (CYAN)
  - Pagination footer ("... 23 more rows")

**Bifrost Mode (Clean JSON Event):**
  - Send raw event: {"event": "zTable", "title": ..., "columns": ..., "rows": ...}
  - Frontend handles rendering (Material-UI DataGrid, etc.)
  - No formatting/truncation (send full data)

ZDATA SUBSYSTEM INTEGRATION

**Primary Use Case: Database Query Results**

Typical workflow:
  1. User runs SQL query via zData.query("SELECT * FROM users LIMIT 20")
  2. zData executes query, fetches results as list of dicts
  3. zData formats results: title="Query Results", columns=[...], rows=[...]
  4. zData calls display.zTable(title, columns, rows, limit=20, offset=0)
  5. AdvancedData renders table in Terminal or sends event to Bifrost

PUBLIC METHODS (Delegated to Specialized Modules):

    zTable(title, columns, rows, limit, offset, show_header, interactive)
        → Delegates to: TableEvents.zTable()

VERSION INFO
Created:  Week 6.2 (zData subsystem integration)
Upgraded: Week 6.4.11c (Industry-grade: type hints, constants, docstrings)
Refactored: Phase 5 (Decomposed into 2 specialized modules + pagination utility)
Line Count: 1,049 → ~210 lines (coordinator) + 2 modules (~505 lines total)
"""

from typing import Any, Optional, List, Union, Dict

# Import specialized event modules (Phase 5 Decomposition)
from .advanced_table import TableEvents
from .advanced_pagination import DEFAULT_OFFSET


class AdvancedData:
    """
    AdvancedData Events Coordinator (v2.0 - Refactored).
    
    COORDINATOR CLASS - Orchestrates specialized event modules via composition.
    
    This class no longer contains implementation logic. Instead, it instantiates
    and coordinates the TableEvents module, delegating all public methods to it.
    
    Composition:
        - TableEvents: Table rendering with pagination
        - Pagination: Data slicing utility (via TableEvents)
    
    Usage:
        # Via zDisplay
        display.zTable(
            title="Users",
            columns=["id", "name", "email"],
            rows=[{"id": 1, "name": "Alice", "email": "alice@example.com"}],
            limit=20,
            offset=0
        )
    
    Architecture:
        Before (v1.x):  1,049 lines, monolithic
        After (v2.0):   ~210 lines, coordinator + 2 modules (~505 lines total)
    """
    
    # Class-level type declarations
    display: Any
    zPrimitives: Any
    zColors: Any
    BasicOutputs: Optional[Any]
    Signals: Optional[Any]
    
    # Specialized event modules (Phase 5 Decomposition)
    TableEvents: TableEvents
    
    def __init__(self, display_instance: Any) -> None:
        """
        Initialize AdvancedData coordinator with specialized modules.
        
        Args:
            display_instance: Parent zDisplay instance (provides zPrimitives, zColors)
        
        Returns:
            None
        
        Phase 5 Refactoring:
            - Instantiate TableEvents module
            - Setup cross-references for BasicOutputs and Signals
            - Maintain backward compatibility (same public API)
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        
        # Get references to other packages for composition
        # (set after zEvents initialization to avoid circular imports)
        self.BasicOutputs = None  # Will be set after zEvents initialization
        self.Signals = None       # Will be set after zEvents initialization
        
        # Instantiate specialized event module (Phase 5)
        # CRITICAL FIX: Pass display_instance (zDisplay) not self (AdvancedData)
        # Bug: TableEvents needs zDisplay.mode for is_bifrost_mode() to work
        self.TableEvents = TableEvents(display_instance)
        
        # Cross-wire dependencies (will be updated after zEvents init)
        self._update_cross_references()
    
    def _update_cross_references(self) -> None:
        """
        Update cross-references between specialized modules.
        
        Called after zEvents initialization to wire up dependencies:
        - BasicOutputs, Signals to TableEvents
        """
        # Wire BasicOutputs and Signals to TableEvents
        if hasattr(self, 'TableEvents'):
            self.TableEvents.BasicOutputs = self.BasicOutputs
            self.TableEvents.Signals = self.Signals
    
    # PUBLIC METHODS (Delegation to Specialized Modules)
    
    def zTable(
        self,
        title: str,
        columns: List[str],
        rows: List[Union[Dict[str, Any], List[Any]]],
        limit: Optional[int] = None,
        offset: int = DEFAULT_OFFSET,
        show_header: bool = True,
        interactive: bool = False,
        caption: Optional[str] = None
    ) -> None:
        """
        Display data table with optional pagination and formatting.
        
        Delegates to: TableEvents.zTable()
        
        Args:
            title: Table title/heading
            columns: List of column names
            rows: List of rows (dicts or lists)
            limit: Number of rows to display (None=all)
            offset: Starting row index (0-based)
            show_header: Show column headers (default: True)
            interactive: Enable keyboard navigation (Terminal-only, default: False)
            caption: Optional table caption describing the table contents
        
        Returns:
            None
        
        Usage:
            display.zTable(
                title="Users",
                caption="A list of all registered users",
                columns=["id", "name", "email"],
                rows=[{"id": 1, "name": "Alice"}],
                limit=20
            )
        """
        # Update cross-references before delegating (ensures Signals/BasicOutputs are set)
        self._update_cross_references()
        
        return self.TableEvents.zTable(
            title, columns, rows, limit, offset, show_header, interactive, caption
        )
