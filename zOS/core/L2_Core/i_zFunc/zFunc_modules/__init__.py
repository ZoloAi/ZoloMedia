# zCLI/subsystems/zFunc/zFunc_modules/__init__.py

"""
zFunc Module Registry - Package Aggregator.

This module serves as the Tier 2 Package Aggregator for the zFunc subsystem,
exposing the public API by aggregating all Tier 1 Foundation components. It
provides a centralized import point for function loading and execution utilities.

Architecture Position
--------------------
**Tier 2: Package Aggregator** - Centralizes Tier 1 Foundation components

This module sits between the Tier 1 Foundation (func_args, func_resolver) and
the Tier 3 Facade (zFunc.py). It aggregates all core utilities into a single
import point, simplifying internal imports within the zFunc subsystem.

4-Tier Architecture Flow
------------------------
1. **Tier 1 (Foundation)**: Core building blocks
   - func_resolver.py: Function resolution and loading
   - func_args.py: Argument parsing with context injection

2. **Tier 2 (Package Aggregator)**: This module ⬅️
   - Aggregates and exposes all Tier 1 components
   - Provides centralized import point

3. **Tier 3 (Facade)**: zFunc.py
   - Main entry point: handle(zHorizontal, zContext)
   - Orchestrates Tier 1 components via this aggregator

4. **Tier 4 (Package Root)**: __init__.py
   - Top-level package interface

Public API Overview
-------------------
This module exposes 3 functions from Tier 1:

**Argument Parsing** (from func_args.py):
- `parse_arguments()`: Parse function arguments with context injection support
  - Handles 5 special zCLI argument types: zContext, zHat, zConv, zConv.field, this.key
  - Delegates to zParser for safe JSON evaluation
  
- `split_arguments()`: Split argument string while respecting nested brackets
  - Validates bracket matching (parentheses, square brackets, curly braces)

**Function Resolution** (from func_resolver.py):
- `resolve_callable()`: Dynamically load and resolve Python functions from files
  - Uses importlib for module loading
  - Validates file existence, spec, loader, function existence

Usage Patterns
--------------
**Standard Import Pattern**:
    >>> from zOS.L2_Core.i_zFunc.zFunc_modules import parse_arguments, resolve_callable
    >>> # Use functions directly

**Aggregator vs. Direct Imports**:
- **Use Aggregator**: When working within zFunc subsystem (internal usage)
- **Direct Imports**: When importing from other subsystems (external usage)

**Internal Usage** (within zFunc subsystem - zFunc.py):
    >>> from .zFunc_modules import parse_arguments, resolve_callable
    >>> # Clean imports within subsystem

**External Usage** (from other subsystems):
    >>> from zOS.L2_Core.i_zFunc.zFunc_modules.func_args import parse_arguments
    >>> # Direct import for external usage (less common)

Integration Points
------------------
**Used By**:
- zFunc.py (Tier 3 Facade): Imports all 3 functions via this aggregator
  - _parse_args_with_display() uses parse_arguments + split_arguments
  - _resolve_callable_with_display() uses resolve_callable

**Dependencies**:
- func_args.py: Argument parsing utilities (Tier 1)
- func_resolver.py: Function resolution utilities (Tier 1)

Usage Examples
--------------
Example 1: Standard import and usage
    >>> from zOS.L2_Core.i_zFunc.zFunc_modules import parse_arguments, split_arguments
    >>> import logging
    >>> 
    >>> logger = logging.getLogger(__name__)
    >>> context = {"user_id": 123, "zHat": {"step1": "data"}}
    >>> 
    >>> args = parse_arguments("zContext, zHat", context, split_arguments, logger)
    >>> # Returns: [{"user_id": 123, "zHat": {...}}, {"step1": "data"}]

Example 2: Using resolve_callable standalone
    >>> from zOS.L2_Core.i_zFunc.zFunc_modules import resolve_callable
    >>> import logging
    >>> 
    >>> logger = logging.getLogger(__name__)
    >>> func = resolve_callable("/path/to/script.py", "process_data", logger)
    >>> result = func(arg1, arg2)

Example 3: Complete workflow (parse + resolve)
    >>> from zOS.L2_Core.i_zFunc.zFunc_modules import (
    ...     parse_arguments, split_arguments, resolve_callable
    ... )
    >>> 
    >>> # Step 1: Resolve function
    >>> func = resolve_callable(file_path, func_name, logger)
    >>> 
    >>> # Step 2: Parse arguments
    >>> args = parse_arguments(arg_str, context, split_arguments, logger, zparser)
    >>> 
    >>> # Step 3: Execute
    >>> result = func(*args)

Version History
---------------
- v1.5.4+: Industry-grade upgrade (comprehensive documentation, tier organization)
- v1.5.x: Initial implementation (basic aggregator)
"""

# ============================================================================
# Tier 1: Foundation - Argument Parsing
# ============================================================================

from .func_args import parse_arguments, split_arguments

# ============================================================================
# Tier 1: Foundation - Function Resolution
# ============================================================================

from .func_resolver import resolve_callable

# ============================================================================
# Tier 1: Foundation - Built-in Functions
# ============================================================================

from .builtin_functions import zNow

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "parse_arguments",    # Argument parsing with context injection (5 special types)
    "split_arguments",    # Argument string splitting with bracket matching
    "resolve_callable",   # Function resolution and loading via importlib
    "zNow",               # Built-in: Get current date/time formatted per zConfig
]
