# zCLI/utils/__init__.py

"""
zCLI utility modules - Backward Compatibility Layer

This module maintains backward compatibility by re-exporting utilities
that have been moved to /zSys/ (Layer 0 - System Foundation).

New code should import directly from zSys instead:
    from zSys import Colors, validate_zcli_instance, zTraceback

This module will be deprecated in a future version.
"""

# Cache utilities - lazy import to avoid circular dependency
# zCLI.utils is imported by zConfig, which is needed by zLoader
# So we can't import zLoader at module level
def _lazy_cache_utils():
    """Lazy import of cache_utils to avoid circular imports."""
    from zOS.L2_Core.h_zLoader.loader_modules import cache_utils
    return cache_utils

def create_shortcut_from_cache(*args, **kwargs):
    """Re-export from zLoader for backward compatibility."""
    return _lazy_cache_utils().create_shortcut_from_cache(*args, **kwargs)

def get_cached_files(*args, **kwargs):
    """Re-export from zLoader for backward compatibility."""
    return _lazy_cache_utils().get_cached_files(*args, **kwargs)

def get_cached_files_count(*args, **kwargs):
    """Re-export from zLoader for backward compatibility."""
    return _lazy_cache_utils().get_cached_files_count(*args, **kwargs)

def clear_system_cache(*args, **kwargs):
    """Re-export from zLoader for backward compatibility."""
    return _lazy_cache_utils().clear_system_cache(*args, **kwargs)

# Make cache_utils available as a property
class _CacheUtilsProxy:
    """Proxy to lazily load cache_utils module."""
    def __getattr__(self, name):
        return getattr(_lazy_cache_utils(), name)

cache_utils = _CacheUtilsProxy()

# Import from zSys.errors
from zSys.errors import (
    validate_zcli_instance,
    zTraceback,
    ExceptionContext,
    zCLIException,
    SchemaNotFoundError,
    DatabaseNotInitializedError,
    TableNotFoundError,
    ConfigurationError,
    ValidationError,
    zMachinePathError,
)

# Import from zSys.formatting
from zSys.formatting import (
    Colors,
    print_ready_message,
)

# Import from zSys.logger
from zSys.logger import (
    get_log_level_from_zspark,
    should_suppress_init_prints,
)

# Additional exceptions from zSys.errors
from zSys.errors import (
    FormModelNotFoundError,
    InvalidzPathError,
    zUIParseError,
    AuthenticationRequiredError,
    PermissionDeniedError,
    PluginNotFoundError,
)

__all__ = [
    # From zSys (backward compatibility)
    "Colors",
    "validate_zcli_instance",
    "zTraceback",
    "ExceptionContext",
    "zCLIException",
    "SchemaNotFoundError",
    "DatabaseNotInitializedError",
    "TableNotFoundError",
    "ConfigurationError",
    "ValidationError",
    "zMachinePathError",
    
    # From zLoader cache utilities (backward compatibility)
    "cache_utils",
    "create_shortcut_from_cache",
    "get_cached_files",
    "get_cached_files_count",
    "clear_system_cache",
    
    # Formatting utilities
    "print_ready_message",
    # Logger configuration
    "get_log_level_from_zspark",
    "should_suppress_init_prints",
    
    # Local exceptions
    "FormModelNotFoundError",
    "InvalidzPathError",
    "zUIParseError",
    "AuthenticationRequiredError",
    "PermissionDeniedError",
    "PluginNotFoundError",
]
