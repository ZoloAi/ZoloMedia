# @temp_zKernel/errors/__init__.py
"""
Framework error handling extracted from zOS.

STAGING AREA - DO NOT USE IN PRODUCTION

This module contains framework-specific exceptions and error handling logic
that was extracted from zOS (OS primitives layer) to maintain clean separation.

These will be merged into zKernel when it joins the monorepo.

See @temp_zKernel/README.md for merge instructions.
"""

# Framework exceptions
from .exceptions import (
    # Base exception
    zKernelException,
    # Schema/Data exceptions
    SchemaNotFoundError,
    FormModelNotFoundError,
    InvalidzPathError,
    DatabaseNotInitializedError,
    TableNotFoundError,
    ValidationError,
    # UI/Parse exceptions
    zUIParseError,
    # Auth exceptions
    AuthenticationRequiredError,
    PermissionDeniedError,
    # Config exceptions
    ConfigurationError,
    # Plugin exceptions
    PluginNotFoundError,
)

# Traceback handling
from .traceback import (
    zTraceback,
    ExceptionContext,
    display_error_summary,
    display_full_traceback,
    display_formatted_traceback,
)

# Framework validation
from .validation import validate_zkernel_instance

__all__ = [
    # Validation
    "validate_zkernel_instance",
    
    # Base exception
    "zKernelException",
    
    # Schema/Data exceptions
    "SchemaNotFoundError",
    "FormModelNotFoundError",
    "InvalidzPathError",
    "DatabaseNotInitializedError",
    "TableNotFoundError",
    "ValidationError",
    
    # UI/Parse exceptions
    "zUIParseError",
    
    # Auth exceptions
    "AuthenticationRequiredError",
    "PermissionDeniedError",
    
    # Config exceptions
    "ConfigurationError",
    
    # Plugin exceptions
    "PluginNotFoundError",
    
    # Traceback
    "zTraceback",
    "ExceptionContext",
    "display_error_summary",
    "display_full_traceback",
    "display_formatted_traceback",
]
