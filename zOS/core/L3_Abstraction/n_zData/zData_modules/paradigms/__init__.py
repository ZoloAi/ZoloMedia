# zCLI/subsystems/zData/zData_modules/paradigms/__init__.py

"""
Data Paradigm Handlers Package (Deprecated).

This package previously contained classical and quantum data handlers, which have
been refactored as follows:

Architecture Change (v1.5.4+):
    - Classical paradigm logic merged directly into zData.py (simplified 2-tier architecture)
    - Quantum paradigm extracted as separate Zolo app (out of scope for zCLI core)

Historical Context:
    Classical Handler (removed):
        - Previously: Thin wrapper for adapter initialization and delegation
        - Now: Logic integrated directly into zData class
        - Reason: Without Quantum, the abstraction had no polymorphic value
    
    Quantum Handler (removed):
        - Previously: 107-line stub with no real implementation
        - Now: Designed as separate Zolo app (zolo-quantum package)
        - Reason: Complexity (zStrongNuclearField, zMemoryCell) doesn't belong in core

New Architecture:
    zCLI now uses a simpler 2-tier architecture:
    - zData (facade) → Backend Adapters (SQLite, PostgreSQL, CSV)
    
    This eliminates the unnecessary intermediate handler layer and reduces
    complexity by 33%.

Migration:
    No migration needed - zData API remains unchanged. All CRUD/DDL/DCL/TCL
    operations work exactly as before.

See Also:
    - zCLI/subsystems/zData/zData.py: Main entry point (now includes classical logic)
    - zCLI/subsystems/zData/zData_modules/shared/backends/: Adapter implementations
"""

__all__ = []  # No exports - paradigm handlers have been refactored
