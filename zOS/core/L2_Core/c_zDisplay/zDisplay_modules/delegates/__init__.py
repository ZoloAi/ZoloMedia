# zCLI/subsystems/zDisplay/zDisplay_modules/delegates/__init__.py

"""
Delegate Method Categories for zDisplay.

This package organizes the 25 delegate methods into logical categories,
each in its own module. All delegates are thin wrappers that route through
the unified handle() method with event dictionaries.

Categories:
    - DelegatePrimitives: Low-level I/O (write_raw, read_string, etc.) - 7 methods
    - DelegateOutputs: Formatted output (header, text, zDeclare) - 3 methods
    - DelegateSignals: Status messages (error, warning, success, info, zMarker) - 5 methods
    - DelegateData: Structured data (list, json, zTable) - 4 methods
    - DelegateSystem: System UI (zSession, zMenu, zDialog, etc.) - 6 methods

Pattern:
    Each delegate class is a mixin that expects a handle() method from the
    parent class (zDisplay). The main zDisplayDelegates class composes all
    categories using multiple inheritance.

Industry-Grade Refactoring:
    This modular structure was created as part of Week 6.4.1 to maintain
    optimal file sizes (~100-150 lines each) while preserving all A+ grade
    improvements (type hints, constants, comprehensive documentation).
"""

from .delegate_primitives import DelegatePrimitives
from .delegate_outputs import DelegateOutputs
from .delegate_signals import DelegateSignals
from .delegate_data import DelegateData
from .delegate_system import DelegateSystem

__all__ = [
    'DelegatePrimitives',
    'DelegateOutputs',
    'DelegateSignals',
    'DelegateData',
    'DelegateSystem'
]

