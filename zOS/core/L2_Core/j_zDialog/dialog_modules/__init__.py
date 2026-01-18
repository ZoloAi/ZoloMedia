# zCLI/subsystems/zDialog/dialog_modules/__init__.py

"""
zDialog Module Registry - Package Aggregator.

This module serves as the Tier 3 Package Aggregator for the zDialog subsystem,
exposing the public API by aggregating all Tier 1-2 Foundation components. It
provides a centralized import point for dialog/form handling utilities with a
focus on pure declarative paradigm (dict-based submissions only).

Architecture Position
--------------------
**Tier 3: Package Aggregator** - Centralizes Tier 1-2 Foundation components

This module sits between the Tier 1-2 Foundation (dialog_context, dialog_submit)
and the Tier 4 Facade (zDialog.py). It aggregates all core utilities into a single
import point, simplifying internal imports within the zDialog subsystem.

5-Tier Architecture Flow
------------------------
1. **Tier 1 (Foundation - Context)**: Core building blocks
   - dialog_context.py: Context creation and placeholder injection (5 types)

2. **Tier 2 (Foundation - Submit)**: Submission handling
   - dialog_submit.py: Dict-based submission via zDispatch (pure declarative)

3. **Tier 3 (Package Aggregator)**: This module ⬅️
   - Aggregates and exposes all Tier 1-2 components
   - Provides centralized import point

4. **Tier 4 (Facade)**: zDialog.py
   - Main entry point: handle(zHorizontal)
   - Orchestrates form display, data collection, submission
   - Auto-validation integration

5. **Tier 5 (Package Root)**: __init__.py
   - Top-level package interface

Public API Overview
-------------------
This module exposes 3 functions from Tier 1-2:

**Context Management** (from dialog_context.py - Tier 1):
- `create_dialog_context()`: Create dialog context with placeholder setup
  - Assembles model, fields, and zConv (collected form data) into context dict
  - Prepares context for placeholder injection
  
- `inject_placeholders()`: Inject placeholders into submission expressions
  - Handles 5 placeholder types: zConv (full dict), zConv.field (dot notation),
    zConv[field] (bracket notation), embedded zConv.* in strings, regex patterns
  - Recursively processes dicts, lists, and strings

**Submission Handling** (from dialog_submit.py - Tier 2):
- `handle_submit()`: Process onSubmit expression via zDispatch (dict-based only)
  - Routes dict-based submissions to zDispatch for command execution
  - Injects placeholders (zConv.*) and model references automatically
  - Pure declarative paradigm (string-based submissions removed in v1.5.4)

Usage Patterns
--------------
**Standard Import Pattern**:
    >>> from zOS.L2_Core.j_zDialog.dialog_modules import (
    ...     create_dialog_context,
    ...     inject_placeholders,
    ...     handle_submit
    ... )
    >>> # Use functions directly

**Aggregator vs. Direct Imports**:
- **Use Aggregator**: When working within zDialog subsystem (internal usage)
- **Direct Imports**: When importing from other subsystems (external usage)

**Internal Usage** (within zDialog subsystem - zDialog.py):
    >>> from .dialog_modules import create_dialog_context, handle_submit
    >>> # Clean imports within subsystem

**External Usage** (from other subsystems):
    >>> from zOS.L2_Core.j_zDialog.dialog_modules.dialog_context import inject_placeholders
    >>> # Direct import for external usage (less common)

Integration Points
------------------
**Used By**:
- zDialog.py (Tier 4 Facade): Imports all 3 functions via this aggregator
  - Line ~80-90: create_dialog_context() for context assembly
  - Line ~143: handle_submit() for form submission processing
  - inject_placeholders() used internally via handle_submit()

**Dependencies**:
- dialog_context.py: Context and placeholder utilities (Tier 1)
- dialog_submit.py: Submission handling utilities (Tier 2)
- Both depend on zDispatch for command routing (dict-based only)

Usage Examples
--------------
Example 1: Context creation with placeholder injection
    >>> from zOS.L2_Core.j_zDialog.dialog_modules import (
    ...     create_dialog_context,
    ...     inject_placeholders
    ... )
    >>> import logging
    >>> 
    >>> logger = logging.getLogger(__name__)
    >>> model = "@.zSchema.users"
    >>> fields = [{"name": "username", "type": "text"}]
    >>> collected_data = {"username": "alice"}
    >>> 
    >>> # Step 1: Create context
    >>> context = create_dialog_context(model, fields, collected_data)
    >>> # Returns: {"model": "@.zSchema.users", "fields": [...], "zConv": {"username": "alice"}}
    >>> 
    >>> # Step 2: Inject placeholders
    >>> submit_expr = {"zCRUD": {"action": "create", "data": {"name": "zConv.username"}}}
    >>> injected = inject_placeholders(submit_expr, context, logger)
    >>> # Returns: {"zCRUD": {"action": "create", "data": {"name": "alice"}}}

Example 2: Direct submission handling
    >>> from zOS.L2_Core.j_zDialog.dialog_modules import handle_submit
    >>> from unittest.mock import Mock
    >>> 
    >>> # Setup
    >>> logger = Mock()
    >>> walker = Mock()
    >>> walker.zcli = Mock()
    >>> walker.display = Mock()
    >>> 
    >>> context = {
    ...     "model": "@.zSchema.users",
    ...     "zConv": {"username": "bob", "email": "bob@example.com"}
    ... }
    >>> submit_expr = {
    ...     "zCRUD": {
    ...         "action": "create",
    ...         "data": "zConv"
    ...     }
    ... }
    >>> 
    >>> # Execute submission
    >>> result = handle_submit(submit_expr, context, logger, walker)
    >>> # Dispatches to zDispatch with injected placeholders and model

Example 3: Complete workflow (context → submit → result)
    >>> from zOS.L2_Core.j_zDialog.dialog_modules import (
    ...     create_dialog_context,
    ...     handle_submit
    ... )
    >>> 
    >>> # Step 1: Create context from form data
    >>> context = create_dialog_context(
    ...     model="@.zSchema.users",
    ...     fields=[{"name": "username"}, {"name": "email"}],
    ...     collected_data={"username": "charlie", "email": "charlie@example.com"}
    ... )
    >>> 
    >>> # Step 2: Define submission (dict-based, pure declarative)
    >>> submit_expr = {
    ...     "zData": {
    ...         "query": "INSERT INTO users (username, email) VALUES (zConv.username, zConv.email)"
    ...     }
    ... }
    >>> 
    >>> # Step 3: Process submission
    >>> result = handle_submit(submit_expr, context, logger, walker)
    >>> # Placeholders injected automatically, query executed via zDispatch
    >>> # Returns: Database insertion result

Version History
---------------
- v1.5.4+: String-based submission removal (pure declarative) + Industry-grade upgrade
  * REMOVED: String-based submissions (zFunc integration)
  * Enhanced: Comprehensive documentation (100+ lines)
  * Added: Tier-based import organization
  * Added: 3 usage examples
- v1.5.3: Dict-based submission support added via zDispatch
- v1.5.2: Initial implementation (mixed string/dict support)
"""

# ============================================================================
# Tier 1: Foundation - Context Management
# ============================================================================

from .dialog_context import create_dialog_context, inject_placeholders

# ============================================================================
# Tier 2: Foundation - Submission Handling
# ============================================================================

from .dialog_submit import handle_submit

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "create_dialog_context",   # Context creation + placeholder setup (Tier 1)
    "inject_placeholders",      # 5 placeholder types: zConv.*, zConv[*], etc. (Tier 1)
    "handle_submit",            # Dict-based submission via zDispatch (Tier 2, pure declarative)
]
