# zCLI/L2_Core/c_zDisplay/zDisplay_modules/e_advanced/advanced_pagination.py
"""
Pagination Utility - Data Slicing with Limit/Offset
=====================================================

This module provides a standalone pagination utility for slicing list data
using SQL-like limit/offset parameters. It returns both the paginated items
and comprehensive metadata about the pagination state.

Purpose:
    - Paginate large datasets for display
    - Support 3 pagination modes (no limit, negative limit, positive limit+offset)
    - Calculate pagination metadata (showing_start, showing_end, has_more)
    - Thread-safe static methods for concurrent use

Public Classes:
    Pagination
        Static methods for data slicing with metadata

Use Cases:
    - Database query result pagination (zData subsystem)
    - Large list display with "... N more rows" footer
    - "Show last N log entries" feature

Dependencies:
    - None (standalone utility, pure Python)

Extracted From:
    display_event_advanced.py (lines 260-497)
"""

from typing import Any, List, Dict, Optional

# Pagination metadata dictionary keys
_KEY_ITEMS: str = "items"
_KEY_TOTAL: str = "total"
KEY_SHOWING_START: str = "showing_start"
KEY_SHOWING_END: str = "showing_end"
KEY_HAS_MORE: str = "has_more"

# Default values
DEFAULT_OFFSET: int = 0

# Pagination algorithm constants
PAGINATION_OFFSET_BASE: int = 1  # 1-based indexing for showing_start/showing_end


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
                "has_more": False
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
