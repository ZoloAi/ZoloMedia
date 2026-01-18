# zCLI/subsystems/zData/zData_modules/shared/parsers/__init__.py
"""
Parsing utilities for zData query operations.

This package provides two complementary parsers for converting string-based query
syntax into structured Python data that backend adapters can process.

Package Contents
---------------
**WHERE Clause Parser (where_parser.py)**:
- Converts SQL-like WHERE strings into filter dictionaries
- Supports: OR, =, !=, >, <, >=, <=, IS NULL, IS NOT NULL, LIKE, IN
- Output: Adapter-compatible dictionaries with operator keys ($or, $gte, etc.)

**Value Type Parser (value_parser.py)**:
- Converts string values into appropriate Python types
- Supports: bool, None, int, float, str
- Type detection order: bool → null → numeric → string
- Automatic quote stripping for string values

Architecture Position
--------------------
- **Layer**: Tier 0 - Foundation (no dependencies except stdlib)
- **Used By**: CRUD operations, validator, data_operations
- **Purpose**: Convert human-readable syntax to structured data

Usage Examples
-------------
WHERE clause parsing:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.parsers import parse_where_clause
    >>> parse_where_clause("age >= 18")
    {"age": {"$gte": 18}}
    >>> parse_where_clause("status IN active,pending OR age > 65")
    {"$or": [{"status": ["active", "pending"]}, {"age": {"$gt": 65}}]}

Value type parsing:
    >>> from zOS.L3_Abstraction.n_zData.zData_modules.shared.parsers import parse_value
    >>> parse_value("42")
    42
    >>> parse_value("true")
    True
    >>> parse_value('"hello"')
    'hello'

Exported Functions
-----------------
- **parse_where_clause(where_str)**: Main WHERE parser entry point
- **parse_or_where(where_str)**: Parse OR conditions specifically
- **parse_single_where(condition)**: Parse single condition (no OR)
- **parse_value(value_str)**: Convert string to Python type

Integration
----------
These parsers are foundational to all zData query operations:
- crud_read.py uses parse_where_clause() for SELECT filtering
- crud_update.py uses parse_where_clause() for UPDATE conditions  
- crud_delete.py uses parse_where_clause() for DELETE conditions
- All CRUD operations use parse_value() for type conversion
- DataValidator uses both parsers for validation rules

See Also
--------
- zData_modules/shared/operations/: CRUD operation modules using these parsers
- zData_modules/shared/backends/: Backend adapters consuming parsed output
- zData_modules/shared/validator.py: Validation using parsed conditions
"""

from .where_parser import parse_where_clause, parse_or_where, parse_single_where
from .value_parser import parse_value

__all__ = [
    "parse_where_clause",
    "parse_or_where",
    "parse_single_where",
    "parse_value",
]

