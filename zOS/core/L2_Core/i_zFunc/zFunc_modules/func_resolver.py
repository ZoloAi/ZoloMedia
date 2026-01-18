# zCLI/subsystems/zFunc/zFunc_modules/func_resolver.py

"""
Function Resolution and Loading Utilities.

This module provides the foundation for dynamically loading and resolving Python
functions from external files using importlib. It is a Tier 1 component in the
zFunc subsystem's 4-tier architecture.

Architecture Position
--------------------
**Tier 1: Foundation** - Core building block for function loading

This module sits at the base of the zFunc subsystem, providing the fundamental
capability to load arbitrary Python functions from files. The zFunc facade (Tier 3)
delegates all function resolution to this module.

Key Functionality
-----------------
- Dynamic module loading from Python files using importlib.util
- Function extraction from loaded modules via getattr
- Robust validation (file existence, module spec, loader, function existence)
- Comprehensive error handling (FileNotFoundError, ImportError, AttributeError)
- Automatic logging of all resolution steps

Security Considerations
-----------------------
⚠️ **IMPORTANT**: This module loads and executes arbitrary Python files.

**Trust Assumptions**:
- file_path MUST point to a trusted source
- The loaded Python file will be executed during import
- Any top-level code in the file will run immediately

**Recommendations**:
- Only load functions from known, trusted directories
- Consider implementing path whitelisting in calling code
- Be aware that malicious code in the target file will execute

Caching Behavior
----------------
Python's importlib automatically caches loaded modules in sys.modules. This means:

- **First call**: Module is loaded from disk and cached
- **Subsequent calls**: Cached module is reused (fast)
- **Cache key**: Based on module_name (derived from file basename)
- **Implication**: Changes to the file require Python restart or manual cache invalidation

Integration Points
------------------
**Used By**:
- zFunc.py (Facade): Calls resolve_callable() via _resolve_callable_with_display()

**Dependencies**:
- importlib.util: Module loading and spec creation
- os.path: File existence checking and path operations

Usage Examples
--------------
Example 1: Basic function loading
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> func = resolve_callable("/path/to/script.py", "my_function", logger)
    >>> result = func(arg1, arg2)

Example 2: Error handling
    >>> try:
    ...     func = resolve_callable("/invalid/path.py", "func", logger)
    ... except FileNotFoundError as e:
    ...     print(f"File not found: {e}")
    ... except ImportError as e:
    ...     print(f"Module load failed: {e}")
    ... except AttributeError as e:
    ...     print(f"Function not found: {e}")

Version History
---------------
- v1.5.4+: Industry-grade upgrade (type hints, comprehensive docs, validation, constants)
- v1.5.x: Initial implementation (basic function loading)
"""

from zOS import os, importlib, Any, Callable


# ============================================================================
# Module Constants
# ============================================================================

# Debug message templates
DEBUG_MSG_FILE_PATH: str = "File path: %s"
DEBUG_MSG_FUNCTION_NAME: str = "Function name: %s"
DEBUG_MSG_RESOLVED: str = "Resolved callable: %s"

# Error message templates
ERROR_MSG_FILE_NOT_FOUND: str = "No such file: {file_path}"
ERROR_MSG_SPEC_NONE: str = "Failed to create module spec from: {file_path}"
ERROR_MSG_LOADER_NONE: str = "Module spec has no loader for: {file_path}"
ERROR_MSG_FUNCTION_NOT_FOUND: str = "Function '{func_name}' not found in module: {file_path}"
ERROR_MSG_RESOLUTION_FAILED: str = "Failed to resolve callable from '%s > %s': %s"


# ============================================================================
# Public API
# ============================================================================

def resolve_callable(
    file_path: str,
    func_name: str,
    logger_instance: Any
) -> Callable[..., Any]:
    """
    Resolve and load a callable function from a Python file.
    
    This function dynamically loads a Python module from the specified file path
    and extracts a named function from it. The module is loaded using importlib,
    which means any top-level code in the file will be executed during import.
    
    The function performs comprehensive validation:
    1. File existence check
    2. Module spec creation validation
    3. Loader availability validation
    4. Function existence validation
    
    Parameters
    ----------
    file_path : str
        Absolute or relative path to the Python file containing the function.
        The file must exist and be readable.
        
    func_name : str
        Name of the function to extract from the loaded module.
        The function must be defined at module level (not nested).
        
    logger_instance : Any
        Logger instance for debug and error messages.
        Typically a logging.Logger object from Python's logging module.
        
    Returns
    -------
    Callable[..., Any]
        The resolved function object, ready to be called.
        The function signature is preserved from the original definition.
        
    Raises
    ------
    FileNotFoundError
        If the specified file_path does not exist.
        
    ImportError
        If the module cannot be loaded or executed.
        This can occur due to:
        - Syntax errors in the target file
        - Missing dependencies in the target file
        - Permission issues
        
    AttributeError
        If the specified func_name does not exist in the loaded module.
        This means the function is either:
        - Not defined in the file
        - Misspelled
        - Defined inside another function/class (nested)
        
    ValueError
        If the module spec or loader is None (internal error).
        
    Examples
    --------
    Example 1: Load and call a simple function
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> # Load function from file
        >>> add_func = resolve_callable("/path/to/math_utils.py", "add", logger)
        >>> # Call the loaded function
        >>> result = add_func(5, 3)
        >>> print(result)  # Output: 8
        
    Example 2: Handle common errors
        >>> try:
        ...     func = resolve_callable("/path/to/script.py", "process", logger)
        ...     result = func(data)
        ... except FileNotFoundError:
        ...     print("Script file not found")
        ... except AttributeError:
        ...     print("Function 'process' not found in script")
        ... except ImportError as e:
        ...     print(f"Failed to load script: {e}")
        
    Notes
    -----
    - **Caching**: Loaded modules are cached by importlib in sys.modules.
      Subsequent calls with the same file_path will reuse the cached module.
      
    - **Security**: This function executes code from the target file during import.
      Only use with trusted sources. Consider path whitelisting in production.
      
    - **Module Name**: The module name is derived from the file's basename
      (without extension). This means files with the same basename will share
      the same cache entry.
      
    - **Top-level Code**: Any code at module level in the target file will
      execute during import. Avoid side effects in target files.
      
    - **Validation**: All validation steps are logged at debug level for
      troubleshooting. Errors are logged at error level with full traceback.
    """
    try:
        # Log input parameters
        logger_instance.debug(DEBUG_MSG_FILE_PATH, file_path)
        logger_instance.debug(DEBUG_MSG_FUNCTION_NAME, func_name)

        # Validation 1: Check file existence
        if not os.path.exists(file_path):
            raise FileNotFoundError(ERROR_MSG_FILE_NOT_FOUND.format(file_path=file_path))

        # Check if this is a JavaScript file - route to JS executor
        if file_path.endswith('.js'):
            from .func_js_executor import execute_js_function
            # Return a wrapper function that executes the JS function
            def js_wrapper(*args):
                return execute_js_function(file_path, func_name, list(args), logger_instance)
            logger_instance.debug("Resolved JavaScript function: %s > %s", file_path, func_name)
            return js_wrapper

        # Load Python module from file
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        
        # Validation 2: Check if spec was created successfully
        if spec is None:
            raise ValueError(ERROR_MSG_SPEC_NONE.format(file_path=file_path))
        
        # Validation 3: Check if spec has a loader
        if spec.loader is None:
            raise ValueError(ERROR_MSG_LOADER_NONE.format(file_path=file_path))
        
        # Create module from spec and execute it
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Validation 4: Check if function exists in module before attempting getattr
        if not hasattr(module, func_name):
            raise AttributeError(
                ERROR_MSG_FUNCTION_NOT_FOUND.format(func_name=func_name, file_path=file_path)
            )
        
        # Get function from module
        func = getattr(module, func_name)
        logger_instance.debug(DEBUG_MSG_RESOLVED, func)
        return func

    except FileNotFoundError:
        # Re-raise with original message (already uses constant)
        logger_instance.error(
            ERROR_MSG_RESOLUTION_FAILED,
            file_path, func_name, "File not found",
            exc_info=True
        )
        raise
    except AttributeError as e:
        # Function not found in module
        logger_instance.error(
            ERROR_MSG_RESOLUTION_FAILED,
            file_path, func_name, str(e),
            exc_info=True
        )
        raise
    except ImportError as e:
        # Module loading failed (syntax error, missing dependency, etc.)
        logger_instance.error(
            ERROR_MSG_RESOLUTION_FAILED,
            file_path, func_name, str(e),
            exc_info=True
        )
        raise
    except ValueError as e:
        # Validation error (spec or loader is None)
        logger_instance.error(
            ERROR_MSG_RESOLUTION_FAILED,
            file_path, func_name, str(e),
            exc_info=True
        )
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger_instance.error(
            ERROR_MSG_RESOLUTION_FAILED,
            file_path, func_name, str(e),
            exc_info=True
        )
        raise


# ============================================================================
# Module Metadata
# ============================================================================

__all__ = ["resolve_callable"]
