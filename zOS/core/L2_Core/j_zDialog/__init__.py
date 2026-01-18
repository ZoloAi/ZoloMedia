# zCLI/subsystems/zDialog/__init__.py

"""
zDialog Subsystem - Package Root (Tier 5).

This module serves as the top-level entry point for the zDialog subsystem,
exposing the public API for interactive form/dialog operations. It provides
access to both the modern class-based interface (zDialog) and the legacy
function-based interface (handle_zDialog) for backward compatibility.

Architecture Position
--------------------
**Tier 5: Package Root** - Top-level package interface

This module is the highest tier in the zDialog subsystem's 5-tier architecture,
serving as the entry point for zCLI.py and other subsystems that need dialog
functionality.

5-Tier Architecture
-------------------
1. **Tier 1 (Foundation - Context)**: dialog_context.py
2. **Tier 2 (Foundation - Submit)**: dialog_submit.py
3. **Tier 3 (Package Aggregator)**: dialog_modules/__init__.py
4. **Tier 4 (Facade)**: zDialog.py (main implementation)
5. **Tier 5 (Package Root)**: This module ⬅️

Public API Exports
------------------
**zDialog** (class):
- Modern class-based interface (Tier 4 Facade)
- Preferred for new code and reusable instances
- Provides handle() method for dialog operations
- Supports auto-validation, WebSocket integration, mode-agnostic rendering

**handle_zDialog** (function):
- Legacy function-based interface (backward compatibility)
- Wraps zDialog class for single-call operations
- Maintained for older code compatibility
- May be deprecated in future major versions

Usage Patterns
--------------
**Modern Approach** (Preferred):
    >>> from zOS.L2_Core.j_zDialog import zDialog
    >>> 
    >>> # Initialize once (typically in zCLI.py)
    >>> dialog = zDialog(zcli_instance, walker=walker_instance)
    >>> 
    >>> # Reuse for multiple operations
    >>> result1 = dialog.handle(form_spec1)
    >>> result2 = dialog.handle(form_spec2)

**Legacy Approach** (Backward Compatible):
    >>> from zOS.L2_Core.j_zDialog import handle_zDialog
    >>> 
    >>> # Single-call function interface
    >>> result = handle_zDialog(form_spec, zcli=zcli_instance)

Integration with zCLI.py
-------------------------
The zDialog subsystem is initialized in zCLI.py during subsystem setup:

    # zCLI.py (approximate line 200)
    self.zdialog = zDialog(self, walker=self.walker)

This makes zDialog available throughout the zCLI framework:
- Direct access: zcli.zdialog.handle(form_spec)
- Via zDispatch: {"zDialog": {"model": ..., "fields": ...}}

Version History
---------------
- v1.5.4+: Industry-grade package root upgrade
  * Enhanced: Comprehensive documentation (50+ lines)
  * Added: Architecture tier documentation
  * Added: 2 usage examples
  * Added: Integration with zCLI.py documentation
  * Added: Inline comments for __all__ items
- v1.5.0: WebSocket support for Bifrost mode
- v1.4.0: Initial implementation
"""

from .zDialog import zDialog, handle_zDialog  # noqa: F401

__all__ = [
    'zDialog',          # Main dialog facade (Tier 4 - modern class-based API)
    'handle_zDialog',   # Backward-compatible function (legacy API)
]
