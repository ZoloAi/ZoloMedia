# zCLI/subsystems/zFunc/zFunc_modules/func_args.py

"""
Function Argument Parsing Utilities.

This module provides utilities for parsing and processing function arguments in
the zFunc subsystem. It handles argument string parsing, context injection, and
special zCLI-specific argument types. This is a Tier 1 component in the zFunc
subsystem's 4-tier architecture.

Architecture Position
--------------------
**Tier 1: Foundation** - Core building block for argument processing

This module sits at the base of the zFunc subsystem, working in conjunction with
func_resolver.py to enable dynamic function execution. The zFunc facade (Tier 3)
delegates all argument parsing to this module.

Key Functionality
-----------------
1. **Argument String Splitting**: Parse comma-separated arguments while respecting
   nested brackets (parentheses, square brackets, curly braces)
   
2. **Context Injection**: Support 5 special argument types for zCLI integration:
   - `zContext`: Full context dictionary injection
   - `zHat`: Wizard step context (from zWizard)
   - `zConv`: Dialog conversation data (from zDialog)
   - `zConv.field`: Dialog field notation (e.g., zConv.username)
   - `this.key`: Context key notation (e.g., this.user_id)

3. **Safe Evaluation**: Delegate to zParser for safe JSON expression evaluation
   when parsing regular arguments

4. **Fallback Handling**: Treat arguments as string literals when zParser unavailable

zCLI-Specific Concepts
----------------------
**zContext**:
  Full context dictionary passed from zFunc.handle(). Contains all contextual
  data including user inputs, wizard state, dialog data, and session info.
  
**zHat**:
  Wizard step context from zWizard subsystem. Contains data collected during
  multi-step wizard workflows. Injected when function is called from wizard.
  
**zConv**:
  Dialog conversation data from zDialog subsystem. Contains form field values
  collected from interactive dialogs. Can be accessed as full dict (zConv) or
  individual fields (zConv.fieldname).
  
**this.key**:
  Generic context key access notation. Allows functions to reference any key
  from the zContext dictionary using dot notation (e.g., this.user_id).

zParser Integration
-------------------
The module uses zParser's `parse_json_expr()` method for safe evaluation of
regular arguments. This enables:

- JSON literal parsing: `{"key": "value"}`, `[1, 2, 3]`
- Number evaluation: `42`, `3.14`
- Boolean evaluation: `true`, `false`
- String evaluation: `"hello"`
- Null evaluation: `null`

When zParser is unavailable (optional parameter), arguments are treated as
string literals for safety.

Bracket Matching
----------------
The `split_arguments()` function tracks nesting depth to correctly parse
arguments containing commas within brackets. It validates:

- Opening brackets: `(`, `[`, `{`
- Closing brackets: `)`, `]`, `}`
- Proper nesting (no negative depth)
- Complete matching (final depth == 0)

Mismatched brackets raise ValueError with descriptive error messages.

Integration Points
------------------
**Used By**:
- zFunc.py (Facade): Calls parse_arguments() via _parse_args_with_display()

**Dependencies**:
- zParser: For safe JSON expression evaluation (parse_json_expr)

Usage Examples
--------------
Example 1: Context injection arguments
    >>> context = {"zHat": {"step1": "data"}, "user_id": 123}
    >>> args = parse_arguments("zContext, zHat", context, split_arguments, logger)
    >>> # Returns: [{"zHat": {...}, "user_id": 123}, {"step1": "data"}]

Example 2: Dialog field notation
    >>> context = {"zConv": {"username": "alice", "email": "alice@example.com"}}
    >>> args = parse_arguments("zConv.username, zConv.email", context, split_arguments, logger)
    >>> # Returns: ["alice", "alice@example.com"]

Example 3: Mixed argument types with zParser
    >>> context = {"this.user_id": 42}
    >>> args = parse_arguments('this.user_id, "hello", 123, true', context, split_arguments, logger, zparser)
    >>> # Returns: [42, "hello", 123, True]

Version History
---------------
- v1.5.4+: Industry-grade upgrade (type hints, comprehensive docs, validation, constants)
- v1.5.x: Initial implementation (basic argument parsing with context injection)
"""

from zOS import Any, Callable, List, Optional


# ============================================================================
# Module Constants
# ============================================================================

# Special argument identifiers (zCLI-specific)
ARG_ZCONTEXT: str = "zContext"
ARG_ZHAT: str = "zHat"
ARG_ZCONV: str = "zConv"
ARG_ZCONV_PREFIX: str = "zConv."
ARG_THIS_PREFIX: str = "this."

# Debug message templates
DEBUG_MSG_NO_ARGS: str = "No arguments to parse"
DEBUG_MSG_RAW_ARG: str = "Raw arg string: %s"
DEBUG_MSG_SPLIT_ARGS: str = "Split args: %s"
DEBUG_MSG_INJECTED_ZCONTEXT: str = "Injected full zContext"
DEBUG_MSG_INJECTED_ZHAT: str = "Injected zHat from context: %s"
DEBUG_MSG_INJECTED_ZCONV: str = "Injected zConv from context: %s"
DEBUG_MSG_RESOLVED_ZCONV_FIELD: str = "Resolved 'zConv.%s' => %s"
DEBUG_MSG_RESOLVED_THIS_KEY: str = "Resolved 'this.%s' => %s"
DEBUG_MSG_EVALUATED_ZPARSER: str = "Evaluated via zParser '%s' => %s"
DEBUG_MSG_LITERAL_FALLBACK: str = "No zParser - using literal '%s'"
DEBUG_MSG_FINAL_ARGS: str = "Final parsed args: %s"

# Error message templates
ERROR_MSG_PARSE_FAILED: str = "Failed to parse args: %s"
ERROR_MSG_BRACKET_MISMATCH: str = "Bracket mismatch in argument string: {details}"
ERROR_MSG_INVALID_ARG_STR_TYPE: str = "arg_str must be a string, got: {arg_type}"
ERROR_MSG_INVALID_SPLIT_FN: str = "split_fn must be callable, got: {split_fn_type}"

# Bracket characters for split_arguments
BRACKETS_OPEN: str = "([{"
BRACKETS_CLOSE: str = ")]}"
DELIMITER_COMMA: str = ","


# ============================================================================
# Public API
# ============================================================================

def parse_arguments(
    arg_str: Optional[str],
    zContext: Any,
    split_fn: Callable[[str], List[str]],
    logger_instance: Any,
    zparser: Any = None
) -> List[Any]:
    """
    Parse function arguments from string with context injection support.
    
    This function processes a comma-separated argument string and returns a list
    of parsed values. It supports 5 special zCLI argument types for context
    injection, plus safe evaluation via zParser for regular arguments.
    
    Special Argument Types:
    1. **zContext**: Injects the full context dictionary
    2. **zHat**: Extracts zHat value from context (zWizard integration)
    3. **zConv**: Extracts zConv value from context (zDialog integration)
    4. **zConv.field**: Extracts specific field from zConv dictionary
    5. **this.key**: Extracts specific key from context dictionary
    
    Regular arguments are evaluated using zParser.parse_json_expr() if available,
    otherwise treated as string literals for safety.
    
    Parameters
    ----------
    arg_str : Optional[str]
        Comma-separated argument string to parse. Can be None or empty string
        for functions with no arguments. Example: "zContext, 123, \"hello\""
        
    zContext : Any
        Context dictionary containing all contextual data (wizard state, dialog
        data, session info). Typically a dict, but can be any type. Used for
        special argument injection (zContext, zHat, zConv, this.key).
        
    split_fn : Callable[[str], List[str]]
        Function to split arg_str into individual arguments while respecting
        nested brackets. Typically split_arguments() from this module.
        
    logger_instance : Any
        Logger instance for debug and error messages. Typically a logging.Logger
        object from Python's logging module.
        
    zparser : Any, optional
        zParser instance for safe JSON expression evaluation. If None, regular
        arguments are treated as string literals. Typically zcli.zparser.
        
    Returns
    -------
    List[Any]
        List of parsed argument values, ready to pass to target function.
        Order matches the input arg_str. Special arguments are replaced with
        their resolved values.
        
    Raises
    ------
    TypeError
        If arg_str is not a string (when not None/empty) or split_fn not callable.
        
    AttributeError
        If zContext doesn't support dict operations when required (e.g., for
        zConv.field notation when zContext is not a dict).
        
    KeyError
        If a required key is missing from zContext or zConv dictionary.
        
    Exception
        Generic catch-all for unexpected errors during parsing. Original error
        is logged and re-raised.
        
    Examples
    --------
    Example 1: Full zContext injection
        >>> context = {"user_id": 123, "session": {...}}
        >>> args = parse_arguments("zContext", context, split_arguments, logger)
        >>> print(args)
        [{"user_id": 123, "session": {...}}]
        
    Example 2: zWizard integration (zHat)
        >>> context = {"zHat": {"step1": "data", "step2": "more"}}
        >>> args = parse_arguments("zHat", context, split_arguments, logger)
        >>> print(args)
        [{"step1": "data", "step2": "more"}]
        
    Example 3: zDialog integration (zConv)
        >>> context = {"zConv": {"username": "alice", "email": "alice@example.com"}}
        >>> args = parse_arguments("zConv", context, split_arguments, logger)
        >>> print(args)
        [{"username": "alice", "email": "alice@example.com"}]
        
    Example 4: Dialog field notation (zConv.field)
        >>> context = {"zConv": {"username": "alice", "age": 30}}
        >>> args = parse_arguments("zConv.username, zConv.age", context, split_arguments, logger)
        >>> print(args)
        ["alice", 30]
        
    Example 5: Context key notation (this.key) with mixed types
        >>> context = {"user_id": 42, "name": "Bob"}
        >>> args = parse_arguments('this.user_id, this.name, 123, "hello"', 
        ...                       context, split_arguments, logger, zparser)
        >>> print(args)
        [42, "Bob", 123, "hello"]
        
    Notes
    -----
    - **Empty Arguments**: If arg_str is None or empty, returns empty list []
    
    - **zParser Delegation**: Regular arguments (not special types) are evaluated
      via zparser.parse_json_expr() for safe JSON parsing. Falls back to string
      literal if zParser unavailable.
      
    - **Context Type**: zContext is typically a dict, but can be any type. Dict
      operations (.get(), .startswith()) only used when isinstance(zContext, dict)
      check passes.
      
    - **Error Handling**: All errors are logged at error level with full traceback
      before re-raising. Debug logging tracks each parsing step.
      
    - **Order Preservation**: Output list maintains same order as input arg_str.
    """
    # Input validation
    if arg_str is not None and not isinstance(arg_str, str):
        raise TypeError(ERROR_MSG_INVALID_ARG_STR_TYPE.format(arg_type=type(arg_str).__name__))
    
    if not callable(split_fn):
        raise TypeError(ERROR_MSG_INVALID_SPLIT_FN.format(split_fn_type=type(split_fn).__name__))
    
    # Handle empty argument string
    if not arg_str:
        logger_instance.debug(DEBUG_MSG_NO_ARGS)
        return []

    try:
        logger_instance.debug(DEBUG_MSG_RAW_ARG, arg_str)
        args_raw = [arg.strip() for arg in split_fn(arg_str)]
        logger_instance.debug(DEBUG_MSG_SPLIT_ARGS, args_raw)

        parsed_args = []
        
        # DRY: Extract isinstance check once (used 4 times in loop)
        is_dict_context = isinstance(zContext, dict)

        for arg in args_raw:
            # Special argument type 1: zContext (full context injection)
            if arg == ARG_ZCONTEXT:
                parsed_args.append(zContext)
                logger_instance.debug(DEBUG_MSG_INJECTED_ZCONTEXT)
                
            # Special argument type 2: zHat (wizard context from zWizard)
            elif arg == ARG_ZHAT:
                zhat_value = zContext.get(ARG_ZHAT) if is_dict_context else None
                parsed_args.append(zhat_value)
                logger_instance.debug(DEBUG_MSG_INJECTED_ZHAT, zhat_value)
                
            # Special argument type 2b: zHat[index] or zHat[key] (wizard result access)
            elif is_dict_context and arg.startswith("zHat[") and arg.endswith("]"):
                # Extract index/key from brackets: "zHat[0]" -> "0", "zHat[step1]" -> "step1"
                index_or_key = arg[5:-1]  # Remove "zHat[" and "]"
                zhat_obj = zContext.get(ARG_ZHAT)
                
                if zhat_obj is not None:
                    try:
                        # Try as integer index first
                        idx = int(index_or_key)
                        value = zhat_obj[idx]
                        logger_instance.debug("Resolved zHat[%s] => %s", index_or_key, value)
                    except (ValueError, KeyError, IndexError, TypeError):
                        # Try as string key (remove quotes if present)
                        key = index_or_key.strip("\"'")
                        try:
                            value = zhat_obj[key]
                            logger_instance.debug("Resolved zHat['%s'] => %s", key, value)
                        except (KeyError, TypeError):
                            value = None
                            logger_instance.warning("zHat[%s] not found in context", index_or_key)
                    parsed_args.append(value)
                else:
                    parsed_args.append(None)
                    logger_instance.warning("zHat not found in context for %s", arg)
                
            # Special argument type 3: zConv (dialog data from zDialog)
            elif arg == ARG_ZCONV:
                zconv_value = zContext.get(ARG_ZCONV) if is_dict_context else None
                parsed_args.append(zconv_value)
                logger_instance.debug(DEBUG_MSG_INJECTED_ZCONV, zconv_value)
                
            # Special argument type 4: zConv.field (dialog field notation)
            elif is_dict_context and arg.startswith(ARG_ZCONV_PREFIX):
                field = arg.replace(ARG_ZCONV_PREFIX, "")
                zconv_data = zContext.get(ARG_ZCONV, {})
                value = zconv_data.get(field) if isinstance(zconv_data, dict) else None
                parsed_args.append(value)
                logger_instance.debug(DEBUG_MSG_RESOLVED_ZCONV_FIELD, field, value)
                
            # Special argument type 5: this.key (context key notation)
            elif is_dict_context and arg.startswith(ARG_THIS_PREFIX):
                key = arg.replace(ARG_THIS_PREFIX, "")
                value = zContext.get(key)
                parsed_args.append(value)
                logger_instance.debug(DEBUG_MSG_RESOLVED_THIS_KEY, key, value)
                
            # Regular argument: Use zParser for safe evaluation
            else:
                if zparser:
                    evaluated = zparser.parse_json_expr(arg)
                    logger_instance.debug(DEBUG_MSG_EVALUATED_ZPARSER, arg, evaluated)
                else:
                    # No zParser available - treat as string literal for safety
                    evaluated = arg
                    logger_instance.debug(DEBUG_MSG_LITERAL_FALLBACK, arg)
                parsed_args.append(evaluated)

        logger_instance.debug(DEBUG_MSG_FINAL_ARGS, parsed_args)
        return parsed_args

    except TypeError as e:
        logger_instance.error(ERROR_MSG_PARSE_FAILED, e, exc_info=True)
        raise
    except AttributeError as e:
        logger_instance.error(ERROR_MSG_PARSE_FAILED, e, exc_info=True)
        raise
    except KeyError as e:
        logger_instance.error(ERROR_MSG_PARSE_FAILED, e, exc_info=True)
        raise
    except Exception as e:
        logger_instance.error(ERROR_MSG_PARSE_FAILED, e, exc_info=True)
        raise


def split_arguments(arg_str: str) -> List[str]:
    """
    Split argument string while respecting nested brackets.
    
    This function splits a comma-separated argument string into individual
    arguments, while correctly handling commas that appear inside brackets
    (parentheses, square brackets, curly braces). It tracks nesting depth
    to distinguish delimiter commas from commas within nested structures.
    
    The function validates bracket matching and raises ValueError if brackets
    are mismatched (e.g., opening without closing, or closing without opening).
    
    Parameters
    ----------
    arg_str : str
        Comma-separated argument string to split. Must be a string.
        Example: "arg1, func(a, b), [1, 2, 3], {\"key\": \"value\"}"
        
    Returns
    -------
    List[str]
        List of argument strings, split at top-level commas only.
        Commas within brackets are preserved. Empty strings are included
        if multiple consecutive commas exist.
        
    Raises
    ------
    TypeError
        If arg_str is not a string.
        
    ValueError
        If brackets are mismatched:
        - Closing bracket without corresponding opening bracket (negative depth)
        - Unclosed brackets at end of string (final depth != 0)
        
    Examples
    --------
    Example 1: Simple comma-separated arguments
        >>> result = split_arguments("arg1, arg2, arg3")
        >>> print(result)
        ["arg1", " arg2", " arg3"]
        
    Example 2: Arguments with nested brackets
        >>> result = split_arguments("func(a, b, c), [1, 2, 3], arg3")
        >>> print(result)
        ["func(a, b, c)", " [1, 2, 3]", " arg3"]
        
    Example 3: Complex nested structures
        >>> result = split_arguments('{"key": [1, 2]}, func(x, y), "text, with, commas"')
        >>> print(result)
        ['{"key": [1, 2]}', ' func(x, y)', ' "text, with, commas"']
        
    Example 4: Mixed bracket types
        >>> result = split_arguments("outer(inner[a, b], c), [x, {y: z}]")
        >>> print(result)
        ["outer(inner[a, b], c)", " [x, {y: z}]"]
        
    Notes
    -----
    - **Bracket Types**: Tracks `(`, `[`, `{` as opening brackets and `)`, `]`, 
      `}` as closing brackets.
      
    - **Depth Tracking**: Maintains nesting depth counter. Increments on opening
      bracket, decrements on closing bracket. Splits only when depth == 0.
      
    - **Validation**: Checks for negative depth (closing without opening) and
      non-zero final depth (unclosed brackets). Raises ValueError with details.
      
    - **Whitespace**: Does NOT strip whitespace from returned arguments. Caller
      should call .strip() on results if needed (as parse_arguments() does).
      
    - **Empty Arguments**: Consecutive commas result in empty strings in output.
      Example: "a,,b" → ["a", "", "b"]
    """
    # Input validation
    if not isinstance(arg_str, str):
        raise TypeError(ERROR_MSG_INVALID_ARG_STR_TYPE.format(arg_type=type(arg_str).__name__))
    
    args = []
    buf = ''
    depth = 0

    try:
        for char in arg_str:
            # Track opening brackets
            if char in BRACKETS_OPEN:
                depth += 1
            # Track closing brackets
            elif char in BRACKETS_CLOSE:
                depth -= 1
                
                # Validation: Check for closing bracket without opening
                if depth < 0:
                    raise ValueError(
                        ERROR_MSG_BRACKET_MISMATCH.format(
                            details=f"Unexpected closing bracket '{char}' without matching opening bracket"
                        )
                    )

            # Split at comma only when at top level (depth == 0)
            if char == DELIMITER_COMMA and depth == 0:
                args.append(buf)
                buf = ''
            else:
                buf += char

        # Append final buffer if not empty
        if buf:
            args.append(buf)
        
        # Validation: Check for unclosed brackets
        if depth != 0:
            raise ValueError(
                ERROR_MSG_BRACKET_MISMATCH.format(
                    details=f"Unclosed brackets detected (depth={depth}). "
                           f"Expected {depth} more closing bracket(s)"
                )
            )

        return args
        
    except ValueError:
        # Re-raise ValueError with bracket mismatch details
        raise
    except Exception as e:
        # Wrap unexpected errors in ValueError for consistency
        raise ValueError(
            ERROR_MSG_BRACKET_MISMATCH.format(details=f"Unexpected error: {str(e)}")
        ) from e


# ============================================================================
# Module Metadata
# ============================================================================

__all__ = ["parse_arguments", "split_arguments"]
