# zCLI/subsystems/zData/zData_modules/shared/operations/crud_read.py
"""
READ operation handler with JOIN support, filtering, and mode-aware display.

This module implements the READ operation for zData's CRUD system. It provides
a comprehensive handler for querying and selecting rows from database tables with
support for single/multi-table queries, JOINs, WHERE filtering, ORDER BY, LIMIT,
mode-aware display, and pagination.

Operation Overview
-----------------
The READ operation queries rows from one or more tables. The handler supports:
- Single-table queries (SELECT * FROM users)
- Multi-table queries with JOINs (SELECT * FROM users, orders)
- Manual JOIN definitions (explicit join conditions)
- Auto-join from foreign key detection (adapter scans FK relationships)
- WHERE clause filtering (age > 18, name LIKE 'A%')
- ORDER BY sorting (order by name ASC, created DESC)
- LIMIT + OFFSET pagination (limit 10, offset 20 for page 3)
- Mode-aware display (zBifrost returns rows, Terminal displays table)
- Interactive pagination (pause + "Press Enter to continue")

Single vs Multi-Table Queries
-----------------------------
**Single-Table Query:**
    request = {"table": "users", "where": "age > 18", "order": "name", "limit": 10}
    - Queries one table
    - Simple SELECT with WHERE/ORDER/LIMIT

**Multi-Table Query:**
    request = {"tables": ["users", "orders"], "auto_join": True}
    - Queries multiple tables
    - Requires JOIN (manual or auto)
    - Returns combined result set

JOIN Support
-----------
The handler supports two JOIN mechanisms:

**1. Manual JOINs (Explicit):**
    request = {
        "tables": ["users", "orders"],
        "joins": [{"table": "orders", "on": "users.id = orders.user_id"}]
    }
    - Explicit join conditions provided in request
    - Full control over join type and conditions

**2. Auto-Join (FK Detection):**
    request = {"tables": ["users", "orders"], "auto_join": True}
    - Adapter automatically detects foreign key relationships
    - Generates JOIN conditions from schema metadata
    - Scans forward FKs (users.id → orders.user_id)
    - Scans reverse FKs (orders.user_id → users.id)

WHERE Clause Filtering
---------------------
WHERE clause supports SQL-like conditions:
- Comparison: age > 18, price <= 100
- Pattern matching: name LIKE 'A%'
- IN lists: status IN ('active', 'pending')
- NULL checks: email IS NULL, phone IS NOT NULL
- Logical: (age > 18 AND status = 'active') OR role = 'admin'

ORDER BY and LIMIT
-----------------
**ORDER BY:**
    request = {"order": "name ASC, created DESC"}
    - Sorts results by one or more columns
    - ASC (ascending) or DESC (descending)

**LIMIT:**
    request = {"limit": 10}
    - Limits number of rows returned
    - Useful for pagination

**LIMIT + OFFSET (Pagination):**
    request = {"limit": 20, "offset": 40}
    - Shows rows 41-60 (page 3, assuming 20 rows per page)
    - offset: Number of rows to skip
    - limit: Maximum rows to return
    - Common pattern: offset = (page_number - 1) * page_size

Display Integration
------------------
The handler uses zDisplay (AdvancedData) for output:
- **zDisplay.zTable(table_name, columns, rows, limit, offset):** Displays results as paginated table
- **Column extraction:** Automatically extracts column names from first row
- **Pagination metadata:** AdvancedData displays "Showing X-Y of Z" footer
- **Empty result handling:** Displays "[OK] Read 0 rows (table is empty or no matches)"

Mode-Aware Behavior
------------------
The handler adapts behavior based on zMode from session:

**Terminal Mode (zMode = "Terminal" or "Walker"):**
    - Displays results via zDisplay.zTable()
    - Pauses with "Press Enter to continue" (if pause=True)
    - Returns True (success indicator)

**zBifrost Mode (zMode = "zBifrost"):**
    - Does NOT display table (Bifrost renders on frontend)
    - Does NOT pause (non-interactive)
    - Returns rows list (for JSON serialization)

Pagination
---------
Interactive pagination controlled by:
- **pause parameter:** request.get("pause", True) - default True
- **zMode:** Only pauses in Terminal/Walker modes
- **zTraceback:** Must be True (session diagnostic mode)
- **Prompt:** "Press Enter to continue..." via zDisplay.read_string()

zSession Integration
-------------------
The handler reads session variables:
- **zMode:** Execution mode (Terminal, Walker, zBifrost)
- **zTraceback:** Diagnostic mode flag (True = enable pause/prompts)

Table Extraction
---------------
The handler supports three table sources (checked in order):

**1. tables parameter (list):**
    request = {"tables": ["users", "orders"]}
    - Most explicit, preferred source

**2. table parameter (string or list):**
    request = {"table": "users"}
    request = {"table": "users, orders"}  # Comma-separated
    - Single or comma-separated list
    - Parsed and split if contains comma

**3. model parameter (string):**
    request = {"model": "myapp.users"}
    - Extracts table name from model path
    - Supports comma-separated: "myapp.users, myapp.orders"

Usage Examples
-------------
**Basic Single-Table Read:**
    >>> request = {"table": "users"}
    >>> result = handle_read(request, ops)
    [OK] Read 15 row(s) from users

**Read with WHERE and ORDER:**
    >>> request = {"table": "users", "where": "age > 18", "order": "name"}
    >>> result = handle_read(request, ops)
    [OK] Read 8 row(s) from users

**Multi-Table with Auto-Join:**
    >>> request = {"tables": ["users", "orders"], "auto_join": True}
    >>> result = handle_read(request, ops)
    [OK] Read 42 row(s) from users + orders

**Read in zBifrost Mode (returns rows):**
    >>> ops.zcli.session["zMode"] = "zBifrost"
    >>> rows = handle_read(request, ops)
    >>> # Returns list of dicts for JSON serialization

Integration
----------
This module is used by:
- classical_data.py: Classical paradigm READ operations
- quantum_data.py: Quantum paradigm READ operations
- data_operations.py: CRUD operation router
"""

from zOS import Any, Dict, List, Union

# ============================================================
# Module Constants - Operation Name
# ============================================================

_OP_READ = "READ"

# ============================================================
# Module Constants - Request Keys
# ============================================================

_KEY_TABLES = "tables"
_KEY_TABLE = "table"
_KEY_MODEL = "model"
_KEY_FIELDS = "fields"
_KEY_WHERE = "where"
_KEY_ORDER = "order"
_KEY_LIMIT = "limit"
_KEY_OFFSET = "offset"
_KEY_JOINS = "joins"
_KEY_AUTO_JOIN = "auto_join"
_KEY_PAUSE = "pause"

# Pagination limits
_DEFAULT_LIMIT = 100  # Reasonable default page size
_MAX_LIMIT = 1000     # Prevent excessive queries

# ============================================================
# Module Constants - Session Keys
# ============================================================

_SESSION_ZMODE = "zMode"
_SESSION_ZTRACEBACK = "zTraceback"

# ============================================================
# Module Constants - Mode Names
# ============================================================

_MODE_WALKER = "Walker"
_MODE_TERMINAL = "Terminal"
_MODE_ZBIFROST = "zBifrost"

# ============================================================
# Module Constants - Display Keys
# ============================================================

_DISPLAY_SEPARATOR = " + "
_DISPLAY_PROMPT = "Press Enter to continue..."

# ============================================================
# Module Constants - Log Messages
# ============================================================

_LOG_NO_TABLE = "No table specified for %s operation"
_LOG_VALIDATE_TABLES = "Validating table existence: %s"
_LOG_MULTI_TABLE = "Multi-table query detected: %s"
_LOG_SINGLE_TABLE = "Single-table query: %s"
_LOG_EXECUTE_SELECT = "Executing SELECT on %s"
_LOG_DISPLAY_RESULTS = "Displaying %d row(s) from %s"
_LOG_SUCCESS = "[OK] Read %d row(s) from %s"
_LOG_EMPTY = "[OK] Read 0 rows from %s (table is empty or no matches)"
_LOG_TABLE_NOT_EXIST = "[FAIL] Table '%s' does not exist"
_LOG_PAUSE = "Pausing for user interaction"

# ============================================================
# Module Constants - Error Messages
# ============================================================

_ERR_NO_TABLE = "No table specified"
_ERR_TABLE_NOT_EXIST = "Table does not exist"
_ERR_INVALID_TABLE = "Invalid table name"
_ERR_SELECT_FAILED = "SELECT operation failed"
_ERR_DISPLAY_FAILED = "Display operation failed"

# ============================================================
# Imports - Helper Functions
# ============================================================

try:
    from .helpers import extract_where_clause
except ImportError:
    from helpers import extract_where_clause

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_read"]


# ============================================================
# CRUD Operations - READ
# ============================================================

def handle_read(request: Dict[str, Any], ops: Any) -> Union[bool, List[Dict[str, Any]]]:
    """
    Handle READ operation to query and select rows from one or more tables.

    This function implements the complete READ workflow including table extraction,
    validation, JOIN support (manual + auto), WHERE filtering, ORDER BY sorting,
    LIMIT pagination, mode-aware display, and interactive pagination.

    Args:
        request: Request dictionary containing query parameters
            - "tables" (list, optional): List of table names
            - "table" (str/list, optional): Single table or comma-separated list
            - "model" (str, optional): Model path (e.g., "myapp.users")
            - "fields" (list, optional): Column names to select
            - "where" (str, optional): WHERE clause (e.g., "age > 18")
            - "order" (str, optional): ORDER BY clause (e.g., "name ASC")
            - "limit" (int, optional): LIMIT clause (e.g., 10)
            - "joins" (list, optional): Manual JOIN definitions
            - "auto_join" (bool, optional): Auto-detect JOINs from FK (default False)
            - "pause" (bool, optional): Pause after display (default True)
        ops: Operations object providing:
            - adapter: Adapter instance for table_exists() and select()
            - logger: Logger instance for diagnostic output
            - zcli.display: Display instance for zTable() and read_string()
            - zcli.session: Session dict with zMode and zTraceback

    Returns:
        Union[bool, List[Dict[str, Any]]]:
            - Terminal/Walker modes: True (success), False (failure)
            - zBifrost mode: List of row dicts (for JSON serialization)

    Raises:
        None: All errors are logged and return False

    Examples:
        >>> # Basic single-table read
        >>> request = {"table": "users"}
        >>> result = handle_read(request, ops)
        [OK] Read 15 row(s) from users

        >>> # Multi-table with auto-join
        >>> request = {"tables": ["users", "orders"], "auto_join": True}
        >>> result = handle_read(request, ops)
        [OK] Read 42 row(s) from users + orders

        >>> # zBifrost mode (returns rows)
        >>> ops.zcli.session["zMode"] = "zBifrost"
        >>> rows = handle_read(request, ops)
        >>> len(rows)
        42

    Notes:
        - Table sources checked in order: tables, table, model
        - Multi-table queries require JOIN (manual or auto_join)
        - zBifrost mode returns rows (no display)
        - Terminal mode displays table and returns True
        - Pagination only in Terminal/Walker with zTraceback=True
    """
    # Phase 1: Extract table(s) from request (may be single or comma-separated list)
    tables = request.get(_KEY_TABLES, [])
    
    # Check singular "table" parameter
    if not tables:
        table_param = request.get(_KEY_TABLE)
        if table_param:
            if isinstance(table_param, str):
                if "," in table_param:
                    tables = [t.strip() for t in table_param.split(",")]
                else:
                    tables = [table_param]
            elif isinstance(table_param, list):
                tables = table_param
    
    # Fallback to extracting from model path
    if not tables:
        model = request.get(_KEY_MODEL)
        if isinstance(model, str):
            # Check if model has comma (multi-table)
            table_name = model.split(".")[-1]
            if "," in table_name:
                tables = [t.strip() for t in table_name.split(",")]
            else:
                tables = [table_name]

    if not tables:
        ops.logger.error(_LOG_NO_TABLE, _OP_READ)
        return False

    # Phase 2: Validate all tables exist
    for tbl in tables:
        if not ops.adapter.table_exists(tbl):
            ops.logger.error(_LOG_TABLE_NOT_EXIST, tbl)
            return False

    # Phase 3: Determine if multi-table query
    is_multi_table = len(tables) > 1
    if is_multi_table:
        ops.logger.debug(_LOG_MULTI_TABLE, ", ".join(tables))
    else:
        ops.logger.debug(_LOG_SINGLE_TABLE, tables[0])

    # Phase 4: Parse query options
    fields = request.get(_KEY_FIELDS)
    order = request.get(_KEY_ORDER)
    limit = request.get(_KEY_LIMIT)
    offset = request.get(_KEY_OFFSET, 0)  # Default to 0 (no offset)
    where = extract_where_clause(request, ops, warn_if_missing=False)
    
    # Validate limit against MAX_LIMIT
    if limit and limit > _MAX_LIMIT:
        ops.logger.warning(f"Limit {limit} exceeds _MAX_LIMIT {_MAX_LIMIT}, capping to {_MAX_LIMIT}")
        limit = _MAX_LIMIT

    # Extract JOIN options
    joins = request.get(_KEY_JOINS)  # Manual join definitions
    auto_join = request.get(_KEY_AUTO_JOIN, False)  # Auto-detect from FK

    # Phase 5: Execute SELECT (single or multi-table)
    table_arg = tables[0] if len(tables) == 1 else tables
    ops.logger.debug(_LOG_EXECUTE_SELECT, table_arg)
    rows = ops.select(table_arg, fields, where=where, joins=joins, order=order, limit=limit, offset=offset, auto_join=auto_join)

    # Phase 6: Display results (mode-aware with AdvancedData pagination)
    # NEW v1.5.12: Support silent mode for background data fetching (_data blocks)
    silent = request.get("silent", False)
    
    if not silent:
        table_display = _DISPLAY_SEPARATOR.join(tables) if is_multi_table else tables[0]
        if rows:
            # Extract column names from first row (assuming dict rows)
            columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
            # Pass limit and offset to AdvancedData for pagination metadata display
            ops.zcli.display.zTable(table_display, columns, rows, limit=limit, offset=offset)
            ops.logger.info(_LOG_SUCCESS, len(rows), table_display)
        else:
            ops.logger.info(_LOG_EMPTY, table_display)

        # Phase 7: Pagination (pause after displaying results)
        pause = request.get(_KEY_PAUSE, True)  # Default to True
        # Don't pause in zBifrost mode, when zMode is not Walker/Terminal, or when zTraceback is False
        zMode = ops.zcli.session.get(_SESSION_ZMODE, "")
        zTraceback = ops.zcli.session.get(_SESSION_ZTRACEBACK, True)  # Default to True
        if pause and zTraceback and zMode in (_MODE_WALKER, _MODE_TERMINAL, ""):
            ops.logger.debug(_LOG_PAUSE)
            ops.zcli.display.read_string(_DISPLAY_PROMPT)

    # Phase 8: Return results (mode-aware)
    # NEW v1.5.12: Return rows for silent mode (background data fetching)
    # Return the actual rows for zBifrost mode or silent mode, True for terminal display mode
    zMode = ops.zcli.session.get(_SESSION_ZMODE, "")
    if silent or zMode == _MODE_ZBIFROST:
        return rows
    return True
