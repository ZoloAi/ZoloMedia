# zCLI/L2_Core/i_zFunc/zFunc_modules/func_js_executor.py

"""
JavaScript Function Execution Utilities.

This module provides the capability to execute JavaScript functions from external
.js files using Node.js, enabling cross-language function execution in zFunc.

Architecture Position
--------------------
**Tier 1: Foundation** - Extension for JavaScript function execution

This module extends the zFunc subsystem to support JavaScript alongside Python,
allowing zCLI applications to call Node.js functions seamlessly.

Key Functionality
-----------------
- Execute JavaScript functions via Node.js subprocess
- JSON-based argument passing and result parsing
- Automatic Node.js detection and validation
- Comprehensive error handling for subprocess execution
- Support for CommonJS and ES6 module formats

Security Considerations
-----------------------
⚠️ **IMPORTANT**: This module executes arbitrary JavaScript files via Node.js.

**Trust Assumptions**:
- file_path MUST point to a trusted source
- The JavaScript file will be executed with Node.js
- Arguments are serialized to JSON (ensure no sensitive data in logs)

**Recommendations**:
- Only execute JavaScript from known, trusted directories
- Validate Node.js installation before execution
- Be aware that malicious code in the target file will execute

Integration Points
------------------
**Used By**:
- func_resolver.py: Calls execute_js_function() for .js files

**Dependencies**:
- subprocess: Node.js process execution
- json: Argument serialization and result parsing

Usage Examples
--------------
Example 1: Basic JavaScript function call
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> result = execute_js_function(
    ...     "/path/to/math.js",
    ...     "add",
    ...     [5, 3],
    ...     logger
    ... )
    >>> print(result)  # Output: 8

Example 2: Error handling
    >>> try:
    ...     result = execute_js_function("/path/to/script.js", "func", [arg1], logger)
    ... except FileNotFoundError:
    ...     print("Node.js not found")
    ... except subprocess.CalledProcessError as e:
    ...     print(f"JavaScript execution failed: {e}")
"""

from zOS import os, json, subprocess, Any, List

# ============================================================================
# Constants
# ============================================================================

# Debug messages
DEBUG_MSG_JS_CALL: str = "Executing JavaScript: %s > %s with args: %s"
DEBUG_MSG_JS_RESULT: str = "JavaScript result: %s"
DEBUG_MSG_NODE_VERSION: str = "Node.js version: %s"

# Error messages
ERROR_MSG_NODE_NOT_FOUND: str = "Node.js not found. Please install Node.js to execute JavaScript functions."
ERROR_MSG_JS_FILE_NOT_FOUND: str = "JavaScript file not found: {file_path}"
ERROR_MSG_JS_EXECUTION_FAILED: str = "JavaScript execution failed for '{file_path} > {func_name}': {error}"
ERROR_MSG_JS_RESULT_PARSE: str = "Failed to parse JavaScript result as JSON: {error}"
ERROR_MSG_JS_FUNCTION_NOT_FOUND: str = "Function '{func_name}' not found in {file_path}"


# ============================================================================
# Helper Functions
# ============================================================================

def check_node_available(logger_instance: Any) -> bool:
    """
    Check if Node.js is available on the system.
    
    Parameters
    ----------
    logger_instance : Any
        Logger instance for debug messages.
        
    Returns
    -------
    bool
        True if Node.js is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger_instance.debug(DEBUG_MSG_NODE_VERSION, result.stdout.strip())
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ============================================================================
# Public API
# ============================================================================

def execute_js_function(
    file_path: str,
    func_name: str,
    args: List[Any],
    logger_instance: Any
) -> Any:
    """
    Execute a JavaScript function from a file using Node.js.
    
    This function executes a JavaScript function by spawning a Node.js subprocess,
    passing arguments as JSON, and parsing the returned JSON result.
    
    The JavaScript file must export the function using CommonJS (module.exports)
    or ES6 (export) syntax.
    
    Parameters
    ----------
    file_path : str
        Absolute or relative path to the JavaScript file containing the function.
        The file must exist and be readable.
        
    func_name : str
        Name of the exported function to execute.
        The function must be exported at module level.
        
    args : List[Any]
        List of arguments to pass to the function.
        Arguments will be serialized to JSON.
        
    logger_instance : Any
        Logger instance for debug and error messages.
        
    Returns
    -------
    Any
        The result returned by the JavaScript function.
        The result is parsed from JSON.
        
    Raises
    ------
    FileNotFoundError
        If Node.js is not found or the JavaScript file doesn't exist.
        
    subprocess.CalledProcessError
        If the JavaScript execution fails (non-zero exit code).
        
    json.JSONDecodeError
        If the JavaScript function doesn't return valid JSON.
        
    ValueError
        If the JavaScript function is not found in the module.
        
    Examples
    --------
    Example 1: Call a simple function
        >>> result = execute_js_function(
        ...     "/path/to/math.js",
        ...     "add",
        ...     [5, 3],
        ...     logger
        ... )
        >>> print(result)  # Output: 8
        
    Example 2: Handle errors
        >>> try:
        ...     result = execute_js_function("/path/to/script.js", "process", [data], logger)
        ... except FileNotFoundError:
        ...     print("Node.js or file not found")
        ... except subprocess.CalledProcessError as e:
        ...     print(f"Execution failed: {e.stderr}")
        
    Notes
    -----
    - **Node.js Required**: Node.js must be installed and available in PATH.
    - **JSON Serialization**: Arguments must be JSON-serializable.
    - **Return Value**: JavaScript function must return JSON-serializable data.
    - **Performance**: Each call spawns a new Node.js process (no caching).
    - **Security**: Only execute trusted JavaScript files.
    """
    # Check if Node.js is available
    if not check_node_available(logger_instance):
        raise FileNotFoundError(ERROR_MSG_NODE_NOT_FOUND)
    
    # Check if JavaScript file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(ERROR_MSG_JS_FILE_NOT_FOUND.format(file_path=file_path))
    
    logger_instance.debug(DEBUG_MSG_JS_CALL, file_path, func_name, args)
    
    # Create a wrapper script that calls the function and outputs JSON
    wrapper_script = f"""
    const module_path = '{file_path}';
    const func_name = '{func_name}';
    const args = {json.dumps(args)};
    
    // Load the module
    const module = require(module_path);
    
    // Get the function
    const func = module[func_name];
    
    if (typeof func !== 'function') {{
        console.error(JSON.stringify({{
            __error__: true,
            message: `Function '${{func_name}}' not found in module`
        }}));
        process.exit(1);
    }}
    
    // Call the function
    try {{
        const result = func(...args);
        console.log(JSON.stringify(result));
    }} catch (error) {{
        console.error(JSON.stringify({{
            __error__: true,
            message: error.message,
            stack: error.stack
        }}));
        process.exit(1);
    }}
    """
    
    try:
        # Execute Node.js with the wrapper script
        result = subprocess.run(
            ["node", "-e", wrapper_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check for execution errors
        if result.returncode != 0:
            # Try to parse error as JSON
            try:
                error_data = json.loads(result.stderr)
                if error_data.get("__error__"):
                    if "not found in module" in error_data.get("message", ""):
                        raise ValueError(ERROR_MSG_JS_FUNCTION_NOT_FOUND.format(
                            func_name=func_name,
                            file_path=file_path
                        ))
                    raise RuntimeError(error_data.get("message", "Unknown error"))
            except json.JSONDecodeError:
                pass
            
            raise subprocess.CalledProcessError(
                result.returncode,
                ["node"],
                output=result.stdout,
                stderr=result.stderr
            )
        
        # Parse the result as JSON
        try:
            parsed_result = json.loads(result.stdout.strip())
            logger_instance.debug(DEBUG_MSG_JS_RESULT, parsed_result)
            return parsed_result
        except json.JSONDecodeError as e:
            logger_instance.error(ERROR_MSG_JS_RESULT_PARSE.format(error=str(e)))
            logger_instance.error("Raw output: %s", result.stdout)
            raise
            
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"JavaScript execution timed out after 30 seconds")
    except Exception as e:
        logger_instance.error(
            ERROR_MSG_JS_EXECUTION_FAILED.format(
                file_path=file_path,
                func_name=func_name,
                error=str(e)
            ),
            exc_info=True
        )
        raise
