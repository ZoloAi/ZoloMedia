# zSys/errors/__init__.py
"""
Error handling subsystem for zCLI.

This module provides comprehensive error handling and runtime validation:
- Custom exceptions with actionable hints
- Interactive traceback UI via Walker
- Subsystem initialization validation
"""

# Runtime validation
from .validation import validate_zcli_instance

# All custom exceptions
from .exceptions import (
    # Base exception
    zCLIException,
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
    # System exceptions
    zMachinePathError,
    UnsupportedOSError,
)

# Traceback handling
from .traceback import (
    zTraceback,
    ExceptionContext,
    display_error_summary,
    display_full_traceback,
    display_formatted_traceback,
)

__all__ = [
    # Validation
    "validate_zcli_instance",
    
    # Base exception
    "zCLIException",
    
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
    
    # System exceptions
    "zMachinePathError",
    "UnsupportedOSError",
    
    # Traceback
    "zTraceback",
    "ExceptionContext",
    "display_error_summary",
    "display_full_traceback",
    "display_formatted_traceback",
]

