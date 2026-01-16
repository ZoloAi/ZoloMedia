# zOS/errors/__init__.py
"""
Error handling for zOS (OS primitives layer).

This module provides OS-level exceptions that are independent of the zKernel framework.
Framework-specific exceptions have been extracted to @temp_zKernel/errors/.

Exports:
- zMachinePathError: zConfig.machine.zolo path resolution errors
- UnsupportedOSError: Unsupported operating system detection

NOTE: Framework exceptions (zKernelException, SchemaNotFoundError, etc.) have been
moved to @temp_zKernel and will be merged into zKernel when it joins the monorepo.
"""

# OS-level exceptions only
from .exceptions import (
    zMachinePathError,
    UnsupportedOSError,
)

__all__ = [
    # OS-level exceptions
    "zMachinePathError",
    "UnsupportedOSError",
]
