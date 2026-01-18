# zCLI/subsystems/zData/zData_modules/shared/operations/agg_aggregate.py
"""
AGGREGATE operation handler for statistical functions on table data.

This module implements the AGGREGATE operation for zData's query system. It provides
a handler for performing statistical aggregate functions (COUNT, SUM, AVG, MIN, MAX)
on table data with support for WHERE filtering and GROUP BY grouping.

Operation Overview
-----------------
The AGGREGATE operation performs statistical calculations on table data:
- count: Count rows (optionally by field for non-null counts)
- sum: Sum numeric field values
- avg: Average numeric field values
- min: Minimum field value
- max: Maximum field value

The handler supports:
- Simple aggregations (scalar result): COUNT(*), SUM(used_mb)
- Grouped aggregations (dict result): COUNT(*) GROUP BY role_id
- WHERE filtering (count active users only)
- Mode-aware output (zBifrost returns data, Terminal displays result)

Request Structure
----------------
**Simple Aggregation:**
    request = {
        "table": "users",
        "function": "count"
    }
    # Returns: 12

**Aggregation with Field:**
    request = {
        "table": "user_storage",
        "function": "sum",
        "field": "used_mb"
    }
    # Returns: 34200

**Aggregation with WHERE:**
    request = {
        "table": "users",
        "function": "count",
        "where": {"status": "active"}
    }
    # Returns: 10

**Aggregation with GROUP BY:**
    request = {
        "table": "user_roles",
        "function": "count",
        "group_by": "role_id"
    }
    # Returns: {1: 1, 2: 3, 3: 8}

Supported Functions
------------------
- **count**: Count rows or non-null values in field
  - Field optional (defaults to * for row count)
  - Returns int (0 for empty result)

- **sum**: Sum numeric values in field
  - Field required
  - Returns int/float (None for empty result)

- **avg**: Average numeric values in field
  - Field required
  - Returns float (None for empty result)

- **min**: Minimum value in field
  - Field required
  - Returns value (None for empty result)

- **max**: Maximum value in field
  - Field required
  - Returns value (None for empty result)

Mode-Aware Display
-----------------
**Terminal Mode:**
- Displays result in human-readable format
- Simple: "Total Users: 12"
- Grouped: Table with group values and counts

**zBifrost Mode:**
- Returns result data directly for frontend rendering
- Simple: {"result": 12}
- Grouped: {"result": {1: 1, 2: 3, 3: 8}}

Integration with Data Layer
---------------------------
The handler delegates to adapter.aggregate() for backend-specific execution:
- SQLite/PostgreSQL: Uses SQL aggregate functions (SELECT COUNT(*), SUM(), etc.)
- CSV: Uses pandas DataFrame aggregate methods (.count(), .sum(), .mean(), etc.)

Error Handling
-------------
The handler validates:
- Function name (must be count/sum/avg/min/max)
- Field requirement (sum/avg/min/max require field, count is optional)
- Table existence (via adapter)
- WHERE clause syntax (via adapter)

Returns "error" string and logs error on failure.

Examples
-------
**Count all users:**
    >>> request = {"table": "users", "function": "count"}
    >>> result = handle_aggregate(request, ops)
    >>> # 12

**Sum storage usage:**
    >>> request = {"table": "user_storage", "function": "sum", "field": "used_mb"}
    >>> result = handle_aggregate(request, ops)
    >>> # 34200

**Count by role:**
    >>> request = {"table": "user_roles", "function": "count", "group_by": "role_id"}
    >>> result = handle_aggregate(request, ops)
    >>> # {1: 1, 2: 3, 3: 8}

See Also
-------
- crud_read.py: READ operation with JOIN support
- base_adapter.py: Abstract aggregate() method definition
- sql_adapter.py: SQL aggregate implementation
- csv_adapter.py: pandas aggregate implementation
"""

from zOS import Dict, List, Optional, Any

# ============================================================
# Constants
# ============================================================

# Request keys
_KEY_TABLE = "table"
_KEY_FUNCTION = "function"
_KEY_FIELD = "field"
_KEY_WHERE = "where"
_KEY_GROUP_BY = "group_by"

# Error messages
_ERR_NO_TABLE = "AGGREGATE requires 'table' key"
_ERR_NO_FUNCTION = "AGGREGATE requires 'function' key"
_ERR_INVALID_FUNCTION = "Invalid aggregate function. Must be: count, sum, avg, min, max"
_ERR_MISSING_FIELD = "Aggregate function '{function}' requires 'field' key"

# Log messages
_LOG_AGGREGATE_START = "Executing AGGREGATE %s(%s) on table '%s'"
_LOG_AGGREGATE_WHERE = "  WHERE: %s"
_LOG_AGGREGATE_GROUP = "  GROUP BY: %s"
_LOG_AGGREGATE_SUCCESS = "AGGREGATE completed: %s"
_LOG_AGGREGATE_FAIL = "AGGREGATE failed: %s"

# Valid functions
_VALID_FUNCTIONS = ["count", "sum", "avg", "min", "max"]

# ============================================================
# Public API
# ============================================================

__all__ = ["handle_aggregate"]


def handle_aggregate(request: Dict[str, Any], ops: Any) -> Any:
    """
    Handle AGGREGATE operation with statistical functions.
    
    Validates request parameters, delegates to adapter.aggregate(), and handles
    mode-aware display. Returns scalar for simple aggregations or dict for
    grouped aggregations.
    
    Args:
        request: Request dict with keys:
                 - table (str): Table name
                 - function (str): Aggregate function (count/sum/avg/min/max)
                 - field (str, optional): Field to aggregate
                 - where (dict, optional): WHERE clause for filtering
                 - group_by (str, optional): Field to group by
        ops: DataOperations facade instance
    
    Returns:
        Scalar value (int/float) for simple aggregation
        Dict {group_value: aggregate_value} for GROUP BY aggregation
        "error" string on failure
    
    Examples:
        >>> request = {"table": "users", "function": "count"}
        >>> result = handle_aggregate(request, ops)
        >>> # 12
        
        >>> request = {"table": "user_storage", "function": "sum", "field": "used_mb"}
        >>> result = handle_aggregate(request, ops)
        >>> # 34200
    
    Notes:
        - Validates function name and field requirement
        - Uses adapter.aggregate() for backend execution
        - Logs operation details for debugging
        - Returns "error" string on failure
    """
    logger = ops.logger
    display = ops.display
    
    # ═══════════════════════════════════════════════════════════
    # 1. VALIDATE REQUEST
    # ═══════════════════════════════════════════════════════════
    
    # Validate table
    if _KEY_TABLE not in request:
        if logger:
            logger.error(_ERR_NO_TABLE)
        if display:
            display.error(_ERR_NO_TABLE)
        return "error"
    
    table = request[_KEY_TABLE]
    
    # Validate function
    if _KEY_FUNCTION not in request:
        if logger:
            logger.error(_ERR_NO_FUNCTION)
        if display:
            display.error(_ERR_NO_FUNCTION)
        return "error"
    
    function = request[_KEY_FUNCTION]
    function_lower = function.lower()
    
    if function_lower not in _VALID_FUNCTIONS:
        if logger:
            logger.error(_ERR_INVALID_FUNCTION)
        if display:
            display.error(_ERR_INVALID_FUNCTION)
        return "error"
    
    # Extract optional parameters
    field = request.get(_KEY_FIELD)
    where = request.get(_KEY_WHERE)
    group_by = request.get(_KEY_GROUP_BY)
    
    # Validate field requirement
    if function_lower != "count" and not field:
        err_msg = _ERR_MISSING_FIELD.format(function=function)
        if logger:
            logger.error(err_msg)
        if display:
            display.error(err_msg)
        return "error"
    
    # ═══════════════════════════════════════════════════════════
    # 2. LOG OPERATION
    # ═══════════════════════════════════════════════════════════
    
    if logger:
        logger.info(_LOG_AGGREGATE_START, function, field or "*", table)
        if where:
            logger.info(_LOG_AGGREGATE_WHERE, where)
        if group_by:
            logger.info(_LOG_AGGREGATE_GROUP, group_by)
    
    # ═══════════════════════════════════════════════════════════
    # 3. EXECUTE AGGREGATION
    # ═══════════════════════════════════════════════════════════
    
    try:
        result = ops.adapter.aggregate(
            table=table,
            function=function_lower,
            field=field,
            where=where,
            group_by=group_by
        )
        
        if logger:
            logger.info(_LOG_AGGREGATE_SUCCESS, result)
        
        return result
        
    except Exception as e:
        if logger:
            logger.error(_LOG_AGGREGATE_FAIL, str(e), exc_info=True)
        if display:
            display.error(f"Aggregation failed: {str(e)}")
        return "error"

