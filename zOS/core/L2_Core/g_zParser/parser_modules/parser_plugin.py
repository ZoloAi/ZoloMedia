# zCLI/subsystems/zParser/parser_modules/parser_plugin.py

"""
Plugin invocation parser with unified filename-based syntax for zParser subsystem.

This module provides comprehensive plugin detection, loading, caching, and execution
with support for both synchronous and asynchronous functions. It uses a unified
filename-based syntax (&PluginName.function) with automatic zCLI dependency injection.

**⚠️ CRITICAL: This module is used externally by zDispatch for ALL plugin invocations.**

Key Functions
-------------
1. **is_plugin_invocation**: Detects if a value is a plugin invocation (starts with &).
   Quick check function used before attempting to resolve plugins.

2. **resolve_plugin_invocation**: Main plugin resolver that handles the full lifecycle.
   CRITICAL function used externally by dispatch_launcher.py.

3. **8 helper functions**: Internal helpers for parsing, loading, caching, and execution.

Architecture
------------
This module uses a **unified filename-based plugin system**:

**Unified Syntax**:
    &PluginName.function_name(args)
    
    Examples:
        &IDGenerator.generate_uuid()
        &test_plugin.hello_world("Alice")
        &DateUtils.get_timestamp()

**Process Flow**:
    1. **Parse**: Extract plugin name, function name, and arguments
    2. **Check Cache**: Look up plugin by filename (fast!)
    3. **Load & Cache**: If not cached, search standard paths and load
    4. **Execute**: Call function with parsed arguments
    5. **Return**: Return function result (supports async)

**Cache Strategy**:
    - Filename-based caching for fast lookups
    - Cache hit/miss logging for debugging
    - Collision detection prevents duplicate filenames
    - First load → cache by filename → reuse on subsequent calls

**Search Paths (Priority Order)**:
    1. @ (Workspace root - for demo/test plugins)
    2. @.zTestSuite.demos (Test/demo plugins)
    3. @.utils (Workspace utilities)
    4. @.plugins (Workspace plugins directory)

Async Support
-------------
The module automatically detects and handles asynchronous functions:

**Sync Functions**:
    def hello(name):
        return f"Hello, {name}!"
    
    # Direct execution, immediate return

**Async Functions (Coroutines)**:
    async def fetch_data(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    
    # Automatic detection via asyncio.iscoroutine()
    # Handles two modes:
    
    1. **Terminal Mode**: No running event loop
       - Uses asyncio.run() to create new loop
       - Executes coroutine and returns result
    
    2. **zBifrost Mode**: Running event loop detected
       - Uses asyncio.run_coroutine_threadsafe()
       - Executes in existing loop from sync context
       - 300-second timeout for long-running operations

zCLI Auto-Injection
-------------------
The module automatically injects the zcli instance if the plugin function accepts it:

**Plugin Function with zcli Parameter**:
    def my_function(arg1, arg2, zcli):
        # Access full zCLI functionality
        zcli.display.handle("Processing...")
        result = zcli.zdata.read("users")
        return result
    
**Auto-Injection Process**:
    1. Use inspect.signature() to analyze function parameters
    2. If 'zcli' parameter found, inject it as keyword argument
    3. Plugin gets full access to zCLI subsystems
    4. Transparent to caller (no manual injection needed)

**Benefits**:
    - Plugins can access display, data, config, etc.
    - No need to pass zcli explicitly in invocation
    - Keeps syntax clean: &plugin.function(args)

Argument Parsing
----------------
The module supports rich argument types in plugin invocations:

**Supported Types**:
    - Strings: "text" or 'text'
    - Integers: 42, -10, 0
    - Floats: 3.14, -2.5, 0.0
    - Booleans: True, False
    - None: None
    - Keyword arguments: key=value

**Examples**:
    &plugin.func()                      # No arguments
    &plugin.func("Hello")               # String argument
    &plugin.func(42)                    # Integer argument
    &plugin.func(3.14)                  # Float argument
    &plugin.func(True)                  # Boolean argument
    &plugin.func(None)                  # None argument
    &plugin.func("Alice", 30)           # Multiple positional
    &plugin.func(name="Bob", age=25)    # Keyword arguments
    &plugin.func("Alice", age=30)       # Mixed positional and keyword

**Smart Comma Splitting**:
    - Respects quotes when splitting arguments
    - Handles nested quotes correctly
    - Preserves strings with commas inside quotes

External Usage (CRITICAL)
--------------------------
**resolve_plugin_invocation** is used by:
    - zCLI/subsystems/zDispatch/dispatch_modules/dispatch_launcher.py
      Purpose: Execute plugin invocations in zFunc commands
      Usage: return self.zcli.zparser.resolve_plugin_invocation(func_spec)
      Context: Handles "&plugin" syntax in command dispatch

Signature must remain stable: resolve_plugin_invocation(value, zcli)

Error Handling
--------------
The module provides comprehensive error messages with hints:

**Invalid Syntax**:
    ValueError: Invalid plugin invocation syntax: &bad syntax
    Expected format: &PluginName.function_name(args)
    Examples:
      &test_plugin.hello_world('Alice')
      &IDGenerator.generate_uuid()

**Plugin Not Found**:
    ValueError: Plugin not found: MyPlugin
    Searched in: @, @.zTestSuite.demos, @.utils, @.plugins
    Hint: Use 'plugin load <zPath>' to load from custom location

**Function Not Found**:
    ValueError: Function not found in plugin 'test_plugin': invalid_func
    Available functions: hello_world, goodbye

**Execution Error**:
    ValueError: Plugin function call failed: &test.func(1, 2, 3)
    Error: func() takes 2 positional arguments but 3 were given
    Check function signature and arguments

Usage Examples
--------------
**is_plugin_invocation** - Quick detection:
    >>> is_plugin_invocation("&test_plugin.hello()")
    True
    >>> is_plugin_invocation("regular_string")
    False
    >>> is_plugin_invocation(42)
    False

**resolve_plugin_invocation** - Full resolution:
    >>> zcli = zCLI()
    
    # Simple function call
    >>> resolve_plugin_invocation("&test_plugin.hello_world('Alice')", zcli)
    "Hello, Alice!"
    
    # Function with zCLI access
    >>> resolve_plugin_invocation("&data_processor.analyze()", zcli)
    # Plugin internally uses zcli.zdata.read(), zcli.display.handle(), etc.
    {"result": "analysis complete"}
    
    # Async function (automatically awaited)
    >>> resolve_plugin_invocation("&api_client.fetch_users()", zcli)
    # Plugin returns coroutine, automatically awaited
    [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

Layer Position
--------------
Layer 1, Position 5 (zParser - Tier 0 Foundation)
    - No internal dependencies
    - Used by: zDispatch (external - CRITICAL)
    - Provides: Plugin invocation detection and resolution

Dependencies
------------
Internal:
    - None (Tier 0 - Foundation)

External:
    - zCLI typing imports (Any, Dict, List, Tuple, Callable, Optional, Union)
    - Python standard library: re, pathlib, inspect, asyncio, concurrent.futures

See Also
--------
- dispatch_launcher.py: External usage for plugin invocations in zFunc
- zLoader: Used for plugin loading and caching
- zParser: Used for zPath resolution
"""

import re
import inspect
import asyncio
from pathlib import Path
from zOS import Any, Dict, List, Tuple, Callable, Optional

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Regex Patterns
REGEX_PLUGIN_INVOCATION: str = r'^&([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)$'  # pylint: disable=line-too-long

# Characters
CHAR_AMPERSAND: str = '&'
CHAR_DOT: str = '.'
CHAR_COMMA: str = ','
CHAR_EQUALS: str = '='
CHAR_QUOTE_DOUBLE: str = '"'
CHAR_QUOTE_SINGLE: str = "'"
CHAR_PAREN_OPEN: str = '('
CHAR_PAREN_CLOSE: str = ')'

# File Extensions
FILE_EXT_PY: str = '.py'

# Cache Types
CACHE_TYPE_PLUGIN: str = "plugin"

# Parameter Names
PARAM_NAME_ZCLI: str = "zcli"

# String Booleans
STR_TRUE: str = 'True'
STR_FALSE: str = 'False'
STR_NONE: str = 'None'

# Special Detection Strings
STR_COLLISION: str = "collision"

# Timeouts (in seconds)
TIMEOUT_ASYNC_EXEC: int = 300  # 5 minutes for async execution

# Standard search paths for plugin discovery (in priority order)
PLUGIN_SEARCH_PATHS: List[str] = [
    "@",                   # Primary: Workspace root (for demo/test plugins)
    "@.zTestSuite.demos",  # Secondary: Test/demo plugins
    "@.utils",             # Tertiary: Workspace utilities
    "@.plugins",           # Quaternary: Workspace plugins directory
]

# Error Messages
ERROR_MSG_INVALID_SYNTAX: str = "Invalid plugin invocation syntax: {}"
ERROR_MSG_EXPECTED_FORMAT: str = "Expected format: &PluginName.function_name(args)"
ERROR_MSG_SYNTAX_EXAMPLES: str = (
    "Examples:\n"
    "  &test_plugin.hello_world('Alice')\n"
    "  &IDGenerator.generate_uuid()\n"
    "  &DateUtils.get_timestamp()"
)
ERROR_MSG_PLUGIN_NOT_FOUND: str = "Plugin not found: {}"
ERROR_MSG_SEARCHED_IN: str = "Searched in: {}"
ERROR_MSG_PLUGIN_HINT: str = "Hint: Use 'plugin load <zPath>' to load from custom location"
ERROR_MSG_FUNCTION_NOT_FOUND: str = "Function not found in plugin '{}': {}"
ERROR_MSG_AVAILABLE_FUNCTIONS: str = "Available functions: {}"
ERROR_MSG_NOT_CALLABLE: str = "'{}' in plugin '{}' is not callable"
ERROR_MSG_FUNCTION_CALL_FAILED: str = "Plugin function call failed: {}"
ERROR_MSG_CHECK_SIGNATURE: str = "Check function signature and arguments"
ERROR_MSG_EXECUTION_FAILED: str = "Plugin function execution failed: {}"

# Log Messages
LOG_MSG_CACHE_HIT: str = "Plugin cache HIT: %s"
LOG_MSG_CACHE_MISS: str = "Plugin cache MISS: %s (searching...)"
LOG_MSG_LOADING_PLUGIN: str = "Loading plugin: %s from %s"
LOG_MSG_FAILED_LOAD: str = "Failed to load from %s: %s"
LOG_MSG_AUTO_INJECT: str = "Auto-injecting zcli instance to plugin function"
LOG_MSG_COROUTINE_DETECTED: str = "Plugin function returned coroutine - awaiting in event loop"
LOG_MSG_EVENT_LOOP_RUNNING: str = "Event loop is running - using run_coroutine_threadsafe"
LOG_MSG_NO_EVENT_LOOP: str = "No running event loop - using asyncio.run()"


# ============================================================================
# FUNCTIONS
# ============================================================================

def is_plugin_invocation(value: Any) -> bool:
    """
    Check if value is a plugin invocation (starts with & and contains dot).
    
    Quick detection function to determine if a value should be processed as a
    plugin invocation. Used as a guard before attempting full resolution.
    
    Detection Criteria:
        1. Value must be a string
        2. Must start with CHAR_AMPERSAND (&)
        3. Must contain CHAR_DOT (.) for plugin.function syntax
    
    Args:
        value: Value to check (can be any type)
    
    Returns:
        bool: True if value matches plugin invocation pattern, False otherwise
    
    Examples:
        >>> is_plugin_invocation("&test_plugin.hello()")
        True
        
        >>> is_plugin_invocation("&IDGenerator.generate_uuid()")
        True
        
        >>> is_plugin_invocation("regular_string")
        False
        
        >>> is_plugin_invocation(42)
        False
        
        >>> is_plugin_invocation("&noDot")  # No dot
        False
        
        >>> is_plugin_invocation(None)
        False
    
    Notes:
        - This is a quick check, not full validation
        - Full syntax validation happens in _parse_invocation()
        - Used by dispatch_launcher.py to detect plugin calls
        - Returns False for non-string types (safe for any input)
    
    See Also:
        - resolve_plugin_invocation: Full resolution with validation
        - _parse_invocation: Regex-based syntax validation
    """
    if not isinstance(value, str):
        return False
    
    # Must start with & and contain a dot (plugin.function)
    return value.startswith(CHAR_AMPERSAND) and CHAR_DOT in value


def resolve_plugin_invocation(value: str, zcli: Any, context: Optional[Any] = None) -> Any:
    """
    Resolve plugin function invocation with unified filename-based syntax.
    
    ⚠️ CRITICAL: This function is used externally by dispatch_launcher.py for
    ALL plugin invocations. Signature must remain stable.
    
    Main entry point for plugin resolution. Handles the full lifecycle from
    parsing to execution, with support for caching, async functions, and
    automatic zCLI dependency injection and context (zHat) support.
    
    Process Flow:
        1. **Parse**: Extract plugin name, function name, args from syntax
        2. **Check Cache**: Look up plugin by filename (fast!)
        3. **Load & Cache**: If not cached, search paths and load
        4. **Get Function**: Retrieve callable from loaded module
        5. **Parse Arguments**: Convert string args to Python types
        6. **Execute**: Call function (handles sync/async)
        7. **Return**: Return function result
    
    Cache Strategy:
        - Filename-based caching for O(1) lookups
        - Cache hit: Immediate function retrieval
        - Cache miss: Search → Load → Cache → Execute
        - Collision detection prevents duplicate filenames
    
    Async Support:
        - Automatically detects async functions (coroutines)
        - Terminal mode: Uses asyncio.run()
        - zBifrost mode: Uses run_coroutine_threadsafe()
        - 300-second timeout for async execution
    
    zCLI Auto-Injection:
        - Inspects function signature for 'zcli' parameter
        - Automatically injects zcli instance as kwarg
        - Transparent to caller (no manual injection needed)
        - Enables plugins to access all zCLI subsystems
    
    Syntax:
        &PluginName.function_name(args)
    
    Args:
        value: Plugin invocation string (e.g., "&test_plugin.hello('Alice')")
        zcli: zCLI instance with plugin cache, loader, parser, logger
    
    Returns:
        Any: Result of plugin function execution (depends on function return type)
    
    Raises:
        ValueError: If syntax invalid, plugin not found, or execution fails
    
    Examples:
        >>> zcli = zCLI()
        
        # Simple function call
        >>> resolve_plugin_invocation("&test_plugin.hello_world('Alice')", zcli)
        "Hello, Alice!"
        
        # Function with integer argument
        >>> resolve_plugin_invocation("&math_utils.square(5)", zcli)
        25
        
        # Function with multiple arguments
        >>> resolve_plugin_invocation("&math_utils.add(10, 20)", zcli)
        30
        
        # Function with keyword arguments
        >>> resolve_plugin_invocation("&greeter.hello(name='Bob', formal=True)", zcli)
        "Good day, Bob!"
        
        # Async function (automatically awaited)
        >>> resolve_plugin_invocation("&api_client.fetch_data()", zcli)
        {"data": [...]}  # Coroutine automatically awaited
        
        # Function with zCLI access (auto-injected)
        >>> resolve_plugin_invocation("&data_processor.analyze()", zcli)
        # Plugin internally uses zcli.display, zcli.zdata, etc.
        {"result": "complete"}
    
    External Usage:
        dispatch_launcher.py:
            return self.zcli.zparser.resolve_plugin_invocation(func_spec)
        Purpose: Execute plugin invocations in zFunc commands
    
    Notes:
        - Signature must remain stable for backward compatibility
        - Returns original value if not a plugin invocation string
        - Cache hits are logged for debugging
        - Search paths tried in priority order
        - Collision errors are re-raised (don't suppress)
    
    See Also:
        - is_plugin_invocation: Quick detection before resolution
        - _parse_invocation: Regex-based syntax parsing
        - _execute_function: Async handling and zCLI injection
        - dispatch_launcher.py: External usage
    """
    if not isinstance(value, str) or not value.startswith(CHAR_AMPERSAND):
        return value
    
    # Step 1: Parse invocation
    plugin_name, function_name, args_str = _parse_invocation(value)
    
    # Step 2: Check cache first
    cached_module = zcli.loader.cache.get(plugin_name, cache_type=CACHE_TYPE_PLUGIN)
    
    if cached_module:
        # Cache hit!
        zcli.logger.debug(LOG_MSG_CACHE_HIT, plugin_name)
        func = _get_function_from_module(cached_module, function_name, plugin_name)
        args, kwargs = _parse_arguments(args_str)
        return _execute_function(func, args, kwargs, value, zcli, context)
    
    # Step 3: Cache miss - search and load
    zcli.logger.debug(LOG_MSG_CACHE_MISS, plugin_name)
    
    for search_path in PLUGIN_SEARCH_PATHS:
        try:
            # Construct full zPath
            zpath = f"{search_path}{CHAR_DOT}{plugin_name}"
            
            # Resolve to absolute file path
            file_path = _resolve_zpath(zpath, zcli)
            
            if not file_path.endswith(FILE_EXT_PY):
                file_path = f"{file_path}{FILE_EXT_PY}"
            
            # Check if file exists
            if not Path(file_path).is_file():
                continue
            
            # Load and cache (by filename)
            zcli.logger.debug(LOG_MSG_LOADING_PLUGIN, plugin_name, file_path)
            module = zcli.loader.cache.plugin_cache.load_and_cache(file_path, plugin_name)
            
            # Execute function
            func = _get_function_from_module(module, function_name, plugin_name)
            args, kwargs = _parse_arguments(args_str)
            return _execute_function(func, args, kwargs, value, zcli, context)
            
        except FileNotFoundError:
            continue
        except Exception as e:
            if STR_COLLISION in str(e).lower():
                raise  # Re-raise collision errors
            zcli.logger.debug(LOG_MSG_FAILED_LOAD, search_path, e)
            continue
    
    # Step 4: Not found anywhere
    search_paths_str = ", ".join(PLUGIN_SEARCH_PATHS)
    raise ValueError(
        f"{ERROR_MSG_PLUGIN_NOT_FOUND.format(plugin_name)}\n"
        f"{ERROR_MSG_SEARCHED_IN.format(search_paths_str)}\n"
        f"{ERROR_MSG_PLUGIN_HINT}"
    )


def _parse_invocation(value: str) -> Tuple[str, str, str]:
    """
    Parse &PluginName.function_name(args) into components using regex.
    
    Uses a regex pattern to extract the three components of a plugin invocation:
    plugin name, function name, and arguments string. Validates syntax and
    provides helpful error messages with examples.
    
    Regex Pattern:
        ^&([a-zA-Z_][a-zA-Z0-9_]*)\\.([a-zA-Z_][a-zA-Z0-9_]*)\\((.*?)\\)$
        
        Breakdown:
        - ^& : Must start with ampersand
        - ([a-zA-Z_][a-zA-Z0-9_]*) : Plugin name (valid Python identifier)
        - \\. : Literal dot separator
        - ([a-zA-Z_][a-zA-Z0-9_]*) : Function name (valid Python identifier)
        - \\( : Literal opening parenthesis
        - (.*?) : Arguments (any characters, non-greedy)
        - \\) : Literal closing parenthesis
        - $ : Must end here
    
    Args:
        value: Plugin invocation string to parse
    
    Returns:
        Tuple[str, str, str]: (plugin_name, function_name, args_str)
            - plugin_name: Name of plugin file (without .py)
            - function_name: Name of function to call
            - args_str: Arguments string (may be empty)
    
    Raises:
        ValueError: If syntax doesn't match expected pattern
    
    Examples:
        >>> _parse_invocation("&test_plugin.hello('Alice')")
        ('test_plugin', 'hello', "'Alice'")
        
        >>> _parse_invocation("&IDGenerator.generate_uuid()")
        ('IDGenerator', 'generate_uuid', '')
        
        >>> _parse_invocation("&math.add(10, 20)")
        ('math', 'add', '10, 20')
        
        >>> _parse_invocation("&bad syntax")
        ValueError: Invalid plugin invocation syntax: &bad syntax
        ...
    
    Notes:
        - Plugin and function names must be valid Python identifiers
        - Arguments string is returned as-is (parsed separately)
        - Provides comprehensive error messages with examples
        - Regex is stored in REGEX_PLUGIN_INVOCATION constant
    
    See Also:
        - resolve_plugin_invocation: Uses this for parsing
        - _parse_arguments: Parses the args_str component
    """
    # Pattern: &PluginName.function_name(args)
    match = re.match(REGEX_PLUGIN_INVOCATION, value)
    
    if not match:
        raise ValueError(
            f"{ERROR_MSG_INVALID_SYNTAX.format(value)}\n"
            f"{ERROR_MSG_EXPECTED_FORMAT}\n"
            f"{ERROR_MSG_SYNTAX_EXAMPLES}"
        )
    
    plugin_name, function_name, args_str = match.groups()
    return plugin_name, function_name, args_str


def _resolve_zpath(zpath: str, zcli: Any) -> str:
    """
    Resolve zPath to absolute file path using zParser.
    
    Delegates to zParser's resolve_symbol_path() to convert a zPath string
    (e.g., "@.utils.test_plugin") into an absolute filesystem path.
    
    zPath Format:
        symbol.part1.part2.partN
        
        Where:
        - symbol: @ (workspace root), ~ (home), etc.
        - parts: Directory/file path components
    
    Args:
        zpath: zPath string (e.g., "@.utils.test_plugin")
        zcli: zCLI instance with zparser subsystem
    
    Returns:
        str: Absolute file path (without .py extension)
    
    Examples:
        >>> _resolve_zpath("@.utils.test_plugin", zcli)
        "/Users/user/workspace/utils/test_plugin"
        
        >>> _resolve_zpath("@.plugins.data_processor", zcli)
        "/Users/user/workspace/plugins/data_processor"
        
        >>> _resolve_zpath("@.zTestSuite.demos.demo_plugin", zcli)
        "/Users/user/workspace/zTestSuite/demos/demo_plugin"
    
    Notes:
        - Uses zParser's resolve_symbol_path() for resolution
        - Splits zPath by dot to extract symbol and parts
        - Returns path without .py extension (added by caller)
        - Symbol resolution follows zParser rules
    
    See Also:
        - resolve_plugin_invocation: Uses this to resolve plugin paths
        - zParser.resolve_symbol_path: Underlying resolution logic
    """
    # Parse zPath
    parts = zpath.split(CHAR_DOT)
    symbol = parts[0]
    path_parts = parts[1:]
    
    # Resolve using zParser
    return zcli.zparser.resolve_symbol_path(symbol, [symbol] + path_parts)


def _get_function_from_module(module: Any, function_name: str, plugin_name: str) -> Callable:
    """
    Get callable function from loaded plugin module with validation.
    
    Retrieves a function from a Python module, validates that it exists and is
    callable, and provides helpful error messages with available functions if
    the requested function is not found.
    
    Validation:
        1. Check if module has attribute with function_name
        2. If not found, list all available public functions
        3. Retrieve function via getattr()
        4. Validate that retrieved object is callable
    
    Args:
        module: Loaded Python module (plugin)
        function_name: Name of function to retrieve
        plugin_name: Plugin name for error messages
    
    Returns:
        Callable: Function object from module
    
    Raises:
        ValueError: If function not found or not callable
    
    Examples:
        >>> module = load_plugin("test_plugin")
        >>> func = _get_function_from_module(module, "hello", "test_plugin")
        >>> func("Alice")
        "Hello, Alice!"
        
        >>> _get_function_from_module(module, "invalid", "test_plugin")
        ValueError: Function not found in plugin 'test_plugin': invalid
        Available functions: hello, goodbye, get_data
    
    Notes:
        - Only lists public functions (not starting with _)
        - Uses hasattr() for existence check
        - Uses callable() for callable validation
        - Provides list of available functions in error message
        - Function names must be valid Python identifiers
    
    See Also:
        - resolve_plugin_invocation: Uses this to get function after loading
        - _execute_function: Executes the returned callable
    """
    if not hasattr(module, function_name):
        available_funcs = [name for name in dir(module) 
                          if not name.startswith('_') and callable(getattr(module, name))]
        raise ValueError(
            f"{ERROR_MSG_FUNCTION_NOT_FOUND.format(plugin_name, function_name)}\n"
            f"{ERROR_MSG_AVAILABLE_FUNCTIONS.format(', '.join(available_funcs) if available_funcs else 'none')}"
        )
    
    func = getattr(module, function_name)
    
    if not callable(func):
        raise ValueError(
            ERROR_MSG_NOT_CALLABLE.format(function_name, plugin_name)
        )
    
    return func


def _execute_function(
    func: Callable,
    args: List[Any],
    kwargs: Dict[str, Any],
    original_value: str,
    zcli: Any,
    context: Optional[Any] = None
) -> Any:
    """
    Execute plugin function with async support, error handling, zCLI and context auto-injection.
    
    Comprehensive function execution that handles:
    - zCLI auto-injection (inspect-based parameter detection)
    - Async function detection and execution (event loop handling)
    - Error handling with detailed messages
    
    zCLI Auto-Injection:
        1. Use inspect.signature() to get function parameters
        2. If 'zcli' parameter exists, inject as keyword argument
        3. Plugin gains access to all zCLI subsystems
        4. Transparent to caller (no manual injection needed)
    
    Async Support:
        **Sync Functions**:
            - Direct execution: result = func(*args, **kwargs)
            - Immediate return
        
        **Async Functions (Coroutines)**:
            - Detection: asyncio.iscoroutine(result)
            
            **Terminal Mode** (no running loop):
                - Create new loop: asyncio.run(result)
                - Execute coroutine and return
            
            **zBifrost Mode** (running loop):
                - Get running loop: asyncio.get_running_loop()
                - Execute from sync context: run_coroutine_threadsafe()
                - Wait with timeout: future.result(timeout=300)
    
    Args:
        func: Callable function to execute
        args: Positional arguments for function
        kwargs: Keyword arguments for function
        original_value: Original invocation string (for error messages)
        zcli: zCLI instance for auto-injection
    
    Returns:
        Any: Result of function execution (depends on function return type)
    
    Raises:
        ValueError: If execution fails (TypeError, general Exception)
    
    Examples:
        >>> def greet(name, zcli):
        ...     zcli.display.handle(f"Greeting {name}")
        ...     return f"Hello, {name}!"
        >>> _execute_function(greet, ["Alice"], {}, "&plugin.greet('Alice')", zcli)
        "Hello, Alice!"
        # zcli was auto-injected
        
        >>> async def fetch_data(url):
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get(url) as resp:
        ...             return await resp.json()
        >>> _execute_function(fetch_data, ["http://api.com"], {}, "&plugin.fetch('http://api.com')", zcli)
        {"data": [...]}
        # Coroutine automatically awaited
    
    Notes:
        - Uses inspect.signature() for parameter inspection
        - Async detection via asyncio.iscoroutine()
        - Event loop detection via asyncio.get_running_loop()
        - 300-second timeout for async execution
        - Detailed error messages with original invocation
        - Proper exception chaining (from e)
    
    See Also:
        - resolve_plugin_invocation: Uses this for final execution
        - _get_function_from_module: Retrieves callable before execution
    """
    try:
        # Auto-inject zcli if function accepts it
        sig = inspect.signature(func)
        if PARAM_NAME_ZCLI in sig.parameters:
            zcli.logger.debug(LOG_MSG_AUTO_INJECT)
            kwargs[PARAM_NAME_ZCLI] = zcli
        
        # Auto-inject context if function accepts it (for zWizard/zHat access)
        if 'context' in sig.parameters and context:
            zcli.logger.debug("Auto-injecting context to plugin function")
            kwargs['context'] = context
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Handle async functions (coroutines)
        if asyncio.iscoroutine(result):
            zcli.logger.debug(LOG_MSG_COROUTINE_DETECTED)
            try:
                # Check if event loop is already running (zBifrost mode)
                loop = asyncio.get_running_loop()
                zcli.logger.debug(LOG_MSG_EVENT_LOOP_RUNNING)
                
                # Use run_coroutine_threadsafe to execute coroutine from sync context
                future = asyncio.run_coroutine_threadsafe(result, loop)
                return future.result(timeout=TIMEOUT_ASYNC_EXEC)
                
            except RuntimeError:
                # No event loop running - use asyncio.run (Terminal mode)
                zcli.logger.debug(LOG_MSG_NO_EVENT_LOOP)
                return asyncio.run(result)
        
        return result
        
    except TypeError as e:
        raise ValueError(
            f"{ERROR_MSG_FUNCTION_CALL_FAILED.format(original_value)}\n"
            f"Error: {e}\n"
            f"{ERROR_MSG_CHECK_SIGNATURE}"
        ) from e
    except Exception as e:
        raise ValueError(
            f"{ERROR_MSG_EXECUTION_FAILED.format(original_value)}\n"
            f"Error: {e}"
        ) from e


def _parse_arguments(args_str: str) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Parse function arguments from string into Python types.
    
    Converts a string of arguments into Python lists and dicts, supporting
    rich types (strings, numbers, booleans, None) and both positional and
    keyword arguments.
    
    Supported Types:
        - **Strings**: "text" or 'text' (quotes removed)
        - **Integers**: 42, -10, 0
        - **Floats**: 3.14, -2.5, 0.0
        - **Booleans**: True, False
        - **None**: None
        - **Keyword args**: key=value
    
    Parsing Process:
        1. **Empty Check**: Return empty lists if args_str is empty
        2. **Smart Split**: Split by comma, respecting quotes
        3. **Classify**: Determine if each part is positional or keyword
        4. **Parse Values**: Convert strings to appropriate Python types
        5. **Return**: (args list, kwargs dict)
    
    Args:
        args_str: Arguments string from function call (may be empty)
    
    Returns:
        Tuple[List[Any], Dict[str, Any]]: (args, kwargs)
            - args: List of positional arguments
            - kwargs: Dict of keyword arguments
    
    Examples:
        >>> _parse_arguments("")
        ([], {})
        
        >>> _parse_arguments("'Alice', 30")
        (['Alice', 30], {})
        
        >>> _parse_arguments("name='Bob', age=25")
        ([], {'name': 'Bob', 'age': 25})
        
        >>> _parse_arguments("'Alice', age=30, active=True")
        (['Alice'], {'age': 30, 'active': True})
        
        >>> _parse_arguments("42, 3.14, True, None")
        ([42, 3.14, True, None], {})
        
        >>> _parse_arguments('"Hello, World"')  # Comma inside quotes
        (['Hello, World'], {})
    
    Notes:
        - Uses _smart_split() to respect quotes when splitting
        - Keyword args detected by presence of '=' (outside quotes)
        - Value parsing via _parse_value() for type conversion
        - Preserves argument order (positional before keyword)
        - Empty/whitespace-only args are filtered out
    
    See Also:
        - resolve_plugin_invocation: Uses this to parse arguments
        - _smart_split: Comma splitting with quote respect
        - _parse_value: String to Python type conversion
    """
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    
    if not args_str or not args_str.strip():
        return args, kwargs
    
    # Split by comma, but respect quotes
    parts = _smart_split(args_str)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check for keyword argument (key=value)
        if CHAR_EQUALS in part and not _is_quoted(part):
            key, value = part.split(CHAR_EQUALS, 1)
            key = key.strip()
            value = value.strip()
            kwargs[key] = _parse_value(value)
        else:
            # Positional argument
            args.append(_parse_value(part))
    
    return args, kwargs


def _smart_split(text: str) -> List[str]:
    """
    Split text by comma, respecting quotes (both single and double).
    
    Splits a string on commas while preserving quoted strings as single tokens.
    Handles both single (') and double (") quotes, tracking quote state to
    avoid splitting on commas inside quoted strings.
    
    Quote Handling:
        - Tracks in_quotes state (True/False)
        - Tracks quote_char (which quote opened: ' or ")
        - Commas inside quotes are preserved
        - Quote characters are kept in output
    
    Args:
        text: Text to split (may contain commas and quotes)
    
    Returns:
        List[str]: Split parts (empty parts are included)
    
    Examples:
        >>> _smart_split("arg1, arg2, arg3")
        ['arg1', ' arg2', ' arg3']
        
        >>> _smart_split("'Alice', 'Bob'")
        ["'Alice'", " 'Bob'"]
        
        >>> _smart_split('"Hello, World", 42')
        ['"Hello, World"', ' 42']
        
        >>> _smart_split("name='Alice', age=30")
        ["name='Alice'", " age=30"]
        
        >>> _smart_split("")
        []
    
    Notes:
        - Preserves quote characters in output
        - Handles both single (') and double (") quotes
        - Nested quotes of different types work correctly
        - Empty strings between commas are preserved
        - Caller should strip whitespace from parts
    
    See Also:
        - _parse_arguments: Uses this for argument splitting
        - _is_quoted: Checks if a string is quoted
    """
    parts: List[str] = []
    current: List[str] = []
    in_quotes = False
    quote_char: Optional[str] = None
    
    for char in text:
        if char in (CHAR_QUOTE_DOUBLE, CHAR_QUOTE_SINGLE) and (not in_quotes or char == quote_char):
            in_quotes = not in_quotes
            quote_char = char if in_quotes else None
            current.append(char)
        elif char == CHAR_COMMA and not in_quotes:
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
    
    if current:
        parts.append(''.join(current))
    
    return parts


def _is_quoted(text: str) -> bool:
    """
    Check if text is quoted (starts and ends with matching quotes).
    
    Determines if a string is enclosed in quotes by checking if it starts and
    ends with matching quote characters (either single or double quotes).
    
    Detection:
        - Strip whitespace from text
        - Check if starts with " and ends with "
        - OR check if starts with ' and ends with '
    
    Args:
        text: Text to check for quotes
    
    Returns:
        bool: True if text is quoted, False otherwise
    
    Examples:
        >>> _is_quoted('"Hello"')
        True
        
        >>> _is_quoted("'World'")
        True
        
        >>> _is_quoted('Hello')
        False
        
        >>> _is_quoted('"Mismatched\'')
        False
        
        >>> _is_quoted('  "Spaced"  ')
        True  # Whitespace is stripped first
    
    Notes:
        - Strips whitespace before checking
        - Requires matching quotes (both start and end)
        - Only checks outer quotes (doesn't validate escaping)
        - Used to detect keyword arg values that are strings
    
    See Also:
        - _parse_arguments: Uses this to detect keyword args
        - _parse_value: Uses this for quote removal
    """
    text = text.strip()
    return ((text.startswith(CHAR_QUOTE_DOUBLE) and text.endswith(CHAR_QUOTE_DOUBLE)) or
            (text.startswith(CHAR_QUOTE_SINGLE) and text.endswith(CHAR_QUOTE_SINGLE)))


def _parse_value(value: str) -> Any:
    """
    Parse a single value from string into appropriate Python type.
    
    Converts a string value into the most appropriate Python type based on
    its content. Tries types in order: quoted string, boolean, None, integer,
    float, and finally unquoted string.
    
    Type Detection Order:
        1. **Quoted String**: "text" or 'text' → str (quotes removed)
        2. **Boolean**: 'True' → True, 'False' → False
        3. **None**: 'None' → None
        4. **Integer**: '42' → 42 (via int())
        5. **Float**: '3.14' → 3.14 (via float())
        6. **Unquoted String**: fallback → str as-is
    
    Args:
        value: String value to parse
    
    Returns:
        Any: Parsed value as appropriate Python type
    
    Examples:
        >>> _parse_value('"Hello"')
        'Hello'
        
        >>> _parse_value("'World'")
        'World'
        
        >>> _parse_value('42')
        42
        
        >>> _parse_value('3.14')
        3.14
        
        >>> _parse_value('True')
        True
        
        >>> _parse_value('False')
        False
        
        >>> _parse_value('None')
        None
        
        >>> _parse_value('unquoted')
        'unquoted'
    
    Notes:
        - Strips whitespace before parsing
        - Quoted strings have quotes removed (value[1:-1])
        - Uses try/except for int and float conversion
        - Unquoted strings are returned as-is (fallback)
        - Boolean detection is case-sensitive ('True', not 'true')
    
    See Also:
        - _parse_arguments: Uses this for each argument value
        - _is_quoted: Used to detect quoted strings
    """
    value = value.strip()
    
    # Handle quoted strings
    if _is_quoted(value):
        return value[1:-1]  # Remove quotes
    
    # Handle boolean
    if value == STR_TRUE:
        return True
    if value == STR_FALSE:
        return False
    
    # Handle None
    if value == STR_NONE:
        return None
    
    # Try integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string (unquoted)
    return value
