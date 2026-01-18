# zCLI/subsystems/zDialog/dialog_modules/dialog_submit.py

"""
Submission handling for zDialog - Processes onSubmit expressions.

This module provides the Tier 2 Submit Handler for the zDialog subsystem,
handling two types of submission expressions: modern dict-based (via zDispatch)
and legacy string-based (via zFunc).

Architecture Position
---------------------
**Tier 2: Submit Handler** (5-Tier Pattern)
    - Tier 1: Foundation (dialog_context.py)
    - Tier 2: Submit Handler (dialog_submit.py) ← This module
    - Tier 3: Package Aggregator (dialog_modules/__init__.py)
    - Tier 4: Facade (zDialog.py)
    - Tier 5: Package Root (__init__.py)

Key Functions
-------------
1. handle_submit(): Main entry point for onSubmit processing (type dispatch)
2. _handle_dict_submit(): Processes dict-based submissions via zDispatch
3. _handle_string_submit(): Processes legacy string-based submissions via zFunc

Helper Functions
----------------
4. _inject_model_if_needed(): Handles complex model injection logic
5. _display_submit_return(): DRY helper for display return calls

Submission Type
---------------
**Dict-Based Submission (Pure Declarative)**:
    - Only approach (string-based removed in v1.5.4 for architectural purity)
    - Supports full zDispatch command dictionaries
    - Automatic placeholder injection via inject_placeholders()
    - Smart model injection for zCRUD/zData operations
    - Example: {"zData": {"query": "SELECT * FROM users WHERE id = zConv.user_id"}}

Integration Flow
----------------
Dict-Based: inject_placeholders() → handle_zDispatch() → result

Dependencies
------------
- dialog_context: inject_placeholders (placeholder resolution), KEY_MODEL, KEY_ZCONV (constants)
- zDispatch: handle_zDispatch (command dispatch)
- zDisplay: walker.display.zDeclare (visual feedback)

Integration Points
------------------
- Used by: zDialog.py (line 143 - form submission)
- Imports from: dialog_context (inject_placeholders, constants)
- Delegates to: zDispatch (dict submissions)

Usage Examples
--------------
Example 1 - Dict-based submission with zData:
    >>> submit_expr = {
    ...     "zData": {
    ...         "query": "INSERT INTO users (name, email) VALUES (zConv.name, zConv.email)"
    ...     }
    ... }
    >>> zContext = {
    ...     "model": "@.zSchema.users",
    ...     "zConv": {"name": "Alice", "email": "alice@example.com"}
    ... }
    >>> result = handle_submit(submit_expr, zContext, logger, walker)
    >>> # Executes: INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')

Example 2 - String-based submission (legacy):
    >>> submit_expr = "&UserModule.create_user(zConv.username, zConv.email)"
    >>> zContext = {"zConv": {"username": "bob", "email": "bob@example.com"}}
    >>> result = handle_submit(submit_expr, zContext, logger, walker)
    >>> # Calls: UserModule.create_user("bob", "bob@example.com")

Example 3 - Invalid submission type:
    >>> submit_expr = 123  # Invalid type
    >>> result = handle_submit(submit_expr, zContext, logger, walker)
    >>> # Logs error, returns False

Version History
---------------
- v1.5.4: Industry-grade refactor + REMOVED string-based submissions for architectural purity
  * Added: Type hints, constants, comprehensive docstrings
  * Added: Dict-based submission support via zDispatch (v1.5.3)
  * REMOVED: String-based submissions (zero users, pure declarative paradigm)
- v1.5.2: Initial implementation with string-based submissions only (zFunc)

Integration Points
------------------
- ✅ Week 6.6 (zDispatch): VERIFIED - handle_zDispatch signature is compatible
"""

from zOS import Any, Dict, Optional
from zOS.L2_Core.e_zDispatch import handle_zDispatch

from .dialog_context import inject_placeholders, KEY_MODEL, KEY_ZCONV
from .dialog_constants import (
    COLOR_DISPATCH,
    COLOR_ZDIALOG,
    KEY_ZCRUD,
    KEY_ZDATA,
    _DEBUG_CONTEXT_KEYS,
    _DEBUG_DICT_PAYLOAD,
    _DEBUG_SUBMIT_EXPR,
    _DEBUG_SUBMIT_RESULT,
    _DISPATCH_CMD_SUBMIT,
    _ERROR_DISPATCH_FAILED,
    _ERROR_INVALID_TYPE_SUBMIT,
    _ERROR_NO_WALKER,
    _INDENT_DIALOG,
    _INDENT_SUBMIT,
    _INFO_DISPATCH_DICT,
    _STYLE_SINGLE,
    _STYLE_TILDE,
)

# ============================================================================
# Module-Level Constants
# ============================================================================

# Dict Keys (imported from dialog_context: KEY_MODEL, KEY_ZCONV)

# Dispatch Command

# Display Colors

# Display Styles

# Indent Levels

# Debug Messages

# Info Messages

# Error Messages

# Module Public API
__all__ = ["handle_submit"]


# ============================================================================
# Helper: Session Interpolation
# ============================================================================

def _interpolate_session_values(obj: Any, session: Dict[str, Any], logger: Any) -> Any:
    """
    Recursively replace %session.* placeholders with actual session values.
    
    This function performs session interpolation for zDialog onSubmit expressions,
    mirroring the logic used in dispatch_launcher.py for _data blocks.
    
    Parameters
    ----------
    obj : Any
        The object to process. Can be dict, list, str, or any other type.
    session : Dict[str, Any]
        The session dictionary from zcli.session
    logger : Any
        Logger instance for debug output
    
    Returns
    -------
    Any
        Object with %session.* placeholders resolved
    
    Examples
    --------
    >>> session = {"zAuth": {"applications": {"zCloud": {"id": 1}}}}
    >>> where = {"id": "%session.zAuth.applications.zCloud.id"}
    >>> result = _interpolate_session_values(where, session, logger)
    >>> # Returns: {"id": 1}
    """
    if isinstance(obj, dict):
        # Recursively process dictionary values
        return {k: _interpolate_session_values(v, session, logger) for k, v in obj.items()}
    
    elif isinstance(obj, list):
        # Recursively process list items
        return [_interpolate_session_values(item, session, logger) for item in obj]
    
    elif isinstance(obj, str) and obj.startswith("%session."):
        # Interpolate session path
        session_path = obj[9:]  # Remove "%session." prefix
        path_parts = session_path.split('.')
        
        # Navigate session dict
        session_value = session
        for part in path_parts:
            if isinstance(session_value, dict):
                session_value = session_value.get(part)
            else:
                session_value = None
                break
        
        if session_value is not None:
            logger.debug(f"[zDialog] Session interpolation: {obj} → {session_value}")
        else:
            logger.warning(f"[zDialog] Failed to interpolate session path: {obj}")
        
        return session_value
    
    else:
        # Return unchanged (int, float, bool, None, non-session strings, etc.)
        return obj


# ============================================================================
# Public API
# ============================================================================

def handle_submit(
    submit_expr: Dict[str, Any],
    zContext: Dict[str, Any],
    logger: Any,
    walker: Optional[Any] = None
) -> Any:
    """
    Handle the zDialog onSubmit expression and return submission result.

    This is the main entry point for form submission processing in zDialog.
    Only dict-based submissions are supported (string-based removed in v1.5.4
    for architectural purity - pure declarative paradigm).

    Parameters
    ----------
    submit_expr : Dict[str, Any]
        The onSubmit expression from the dialog form. Must be a dict-based
        command compatible with zDispatch. Common structures:
        - {"zData": {"query": "..."}} - Database query
        - {"zCRUD": {"action": "...", "data": {...}}} - CRUD operation
        - {"zFunc": "..."} - Function call via dispatch
        - Any other zDispatch-compatible command dict
    zContext : Dict[str, Any]
        Dialog context containing model, fields, and zConv (form data).
        Expected structure:
        {
            "model": Optional[str],     # Schema model reference
            "fields": List[Dict],       # Field definitions
            "zConv": Dict[str, Any]     # Collected form data
        }
    logger : Any
        Logger instance for debug/info/error output. Should have
        .debug(), .info(), and .error() methods.
    walker : Optional[Any], default=None
        Walker instance providing access to zcli, display, loader, etc.
        Required for submission processing (ValueError raised if None).

    Returns
    -------
    Any
        Submission result from zDispatch. Return type depends on the command executed:
        - zData queries: List of records or dict results
        - zCRUD operations: Status dict (e.g., {"status": "created", "id": 42})
        - Other commands: Varies based on command type
        - Error: Returns False if invalid submission type

    Raises
    ------
    ValueError
        If walker is None (walker is required for submission processing)
    TypeError
        If submit_expr is not a dict (string-based submissions removed in v1.5.4)

    Examples
    --------
    Example 1: Dict-based submission with zData query
        >>> submit_expr = {
        ...     "zData": {
        ...         "query": "SELECT * FROM users WHERE id = zConv.user_id"
        ...     }
        ... }
        >>> zContext = {
        ...     "model": "@.zSchema.users",
        ...     "zConv": {"user_id": 42}
        ... }
        >>> result = handle_submit(submit_expr, zContext, logger, walker)
        >>> # Returns: List of user records from database

    Example 2: Dict-based submission with zCRUD (model auto-injected)
        >>> submit_expr = {
        ...     "zCRUD": {
        ...         "action": "create",
        ...         "data": {"name": "zConv.name", "email": "zConv.email"}
        ...     }
        ... }
        >>> zContext = {
        ...     "model": "@.zSchema.users",
        ...     "zConv": {"name": "Alice", "email": "alice@example.com"}
        ... }
        >>> result = handle_submit(submit_expr, zContext, logger, walker)
        >>> # Model "@.zSchema.users" is automatically injected into zCRUD

    Example 3: Invalid submission type (error handling)
        >>> submit_expr = 123  # Invalid type
        >>> result = handle_submit(submit_expr, zContext, logger, walker)
        >>> # Logs error: "zSubmit expression must be a dict, got: <class 'int'>"
        >>> # Returns: False

    Notes
    -----
    - Only dict-based submissions are supported (architectural decision v1.5.4)
    - String-based submissions were removed for pure declarative paradigm alignment
    - Placeholders are injected via inject_placeholders() from dialog_context
    - Model injection logic is handled by _inject_model_if_needed()
    - Visual feedback is displayed via walker.display.zDeclare()
    - Walker is required (not optional despite type hint - ValueError if None)
    """
    if walker is None:
        raise ValueError(_ERROR_NO_WALKER)
    
    walker.display.zDeclare("zSubmit", color=COLOR_ZDIALOG, indent=_INDENT_DIALOG, style=_STYLE_SINGLE)

    logger.debug(_DEBUG_SUBMIT_EXPR, submit_expr)
    # Mask passwords in zConv for secure logging
    masked_zconv = _mask_passwords_in_dict(zContext.get(KEY_ZCONV))
    logger.debug(_DEBUG_CONTEXT_KEYS, list(zContext.keys()), masked_zconv)

    # Dict-based submission => zDispatch
    if isinstance(submit_expr, dict):
        return _handle_dict_submit(submit_expr, zContext, logger, walker)
    
    # Invalid type: Log error and return False
    logger.error(_ERROR_INVALID_TYPE_SUBMIT, type(submit_expr))
    return False


# ============================================================================
# Private Helpers
# ============================================================================

def _mask_password_in_zfunc_string(zfunc_str: str) -> str:
    """
    Mask password arguments in zFunc plugin call strings.
    
    Detects &auth.login() calls and masks the password (2nd argument).
    Example: "&auth.login('email@test.com', 'secret123')" 
          -> "&auth.login('email@test.com', '********')"
    
    Args:
        zfunc_str: zFunc string like "&auth.login('email', 'pass')"
    
    Returns:
        String with password argument masked
    """
    import re
    
    # Pattern to match &auth.login() with two string arguments
    # Captures: function_call, first_arg, second_arg (password)
    pattern = r"(&auth\.login\(['\"]([^'\"]+)['\"],\s*['\"])([^'\"]+)(['\"])"
    
    def mask_password(match):
        # Reconstruct with masked password
        return f"{match.group(1)}********{match.group(4)}"
    
    return re.sub(pattern, mask_password, zfunc_str)


def _mask_passwords_in_dict(data: Any, password_fields: list = None) -> Any:
    """
    Recursively mask password values in dictionaries for secure logging.
    
    Masks any field containing 'password' in its name (case-insensitive)
    or in the provided password_fields list. Also masks passwords in
    zFunc plugin call strings.
    
    Args:
        data: Data to mask (dict, list, or primitive)
        password_fields: Optional list of field names to mask
    
    Returns:
        Copy of data with passwords masked as '********'
    """
    if password_fields is None:
        password_fields = []
    
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            # Check if this is a password field
            if 'password' in str(key).lower() or key in password_fields:
                masked[key] = '********'
            # Check if this is a zFunc string that might contain passwords
            elif key == 'zFunc' and isinstance(value, str) and '&auth.login' in value:
                masked[key] = _mask_password_in_zfunc_string(value)
            else:
                # Recursively mask nested structures
                masked[key] = _mask_passwords_in_dict(value, password_fields)
        return masked
    elif isinstance(data, list):
        return [_mask_passwords_in_dict(item, password_fields) for item in data]
    else:
        return data


def _handle_dict_submit(
    submit_dict: Dict[str, Any],
    zContext: Dict[str, Any],
    logger: Any,
    walker: Optional[Any] = None
) -> Any:
    """
    Handle dict-based onSubmit expression and dispatch via zDispatch.

    This function processes modern dict-based submissions by:
    1. Injecting placeholders (zConv.* → actual values)
    2. Injecting model reference if needed (for zCRUD/zData)
    3. Dispatching via handle_zDispatch()
    4. Displaying return feedback

    Parameters
    ----------
    submit_dict : Dict[str, Any]
        Dict-based submission expression. Common structures:
        - {"zData": {"query": "..."}} - Database query
        - {"zCRUD": {"action": "...", "data": {...}}} - CRUD operation
        - {"zFunc": "..."} - Function call via dispatch
        - Any other zDispatch-compatible command dict
    zContext : Dict[str, Any]
        Dialog context containing model, fields, and zConv.
    logger : Any
        Logger instance for debug/info/error output.
    walker : Optional[Any], default=None
        Walker instance for accessing zcli and display.

    Returns
    -------
    Any
        Result from handle_zDispatch(). Type depends on the command executed.

    Raises
    ------
    ImportError
        If zDispatch module cannot be imported
    AttributeError
        If handle_zDispatch function is not available
    RuntimeError
        If zDispatch execution fails

    Examples
    --------
    Example 1: zData query with placeholder injection
        >>> submit_dict = {
        ...     "zData": {"query": "SELECT * FROM users WHERE id = zConv.user_id"}
        ... }
        >>> zContext = {
        ...     "model": "@.zSchema.users",
        ...     "zConv": {"user_id": 42}
        ... }
        >>> result = _handle_dict_submit(submit_dict, zContext, logger, walker)
        >>> # After placeholder injection:
        >>> # {"zData": {"query": "SELECT * FROM users WHERE id = 42"}}

    Example 2: zCRUD with model injection
        >>> submit_dict = {
        ...     "zCRUD": {"action": "create", "data": {"name": "Alice"}}
        ... }
        >>> zContext = {"model": "@.zSchema.users", "zConv": {}}
        >>> result = _handle_dict_submit(submit_dict, zContext, logger, walker)
        >>> # Model is automatically injected:
        >>> # {"zCRUD": {"model": "@.zSchema.users", "action": "create", ...}}

    Example 3: Root-level submission without zData (model injected at root)
        >>> submit_dict = {"command": "custom", "param": "zConv.value"}
        >>> zContext = {"model": "@.zSchema.config", "zConv": {"value": "test"}}
        >>> result = _handle_dict_submit(submit_dict, zContext, logger, walker)
        >>> # Model injected at root and placeholder resolved:
        >>> # {"model": "@.zSchema.config", "command": "custom", "param": "test"}

    Notes
    -----
    - Placeholders are injected via inject_placeholders() from dialog_context
    - Model injection logic is handled by _inject_model_if_needed()
    - Model is NOT injected at root if zData is present (zData should have its own model)
    - Errors during dispatch are caught and logged
    - Visual feedback is displayed via walker.display.zDeclare()
    """
    logger.debug(_DEBUG_DICT_PAYLOAD)

    try:
        # Step 1: Inject placeholders (zConv.* => actual values)
        submit_dict = inject_placeholders(submit_dict, zContext, logger)
    
        # Step 1.5: Interpolate session values (%session.* => actual session values)
        submit_dict = _interpolate_session_values(submit_dict, walker.zcli.session, logger)
        
        # Step 2: Inject model if needed (for zCRUD/zData)
        submit_dict = _inject_model_if_needed(submit_dict, zContext)

        # Step 3: Dispatch via zDispatch
        # Mask passwords in submit_dict for secure logging
        masked_submit = _mask_passwords_in_dict(submit_dict)
        logger.info(_INFO_DISPATCH_DICT, masked_submit)
        # Pass zContext as context so zLogin and other actions can access zConv
        result = handle_zDispatch(_DISPATCH_CMD_SUBMIT, submit_dict, zcli=walker.zcli, walker=walker, context=zContext)

        # Step 4: Display return feedback
        _display_submit_return(walker)

        return result

    except (ImportError, AttributeError, RuntimeError) as e:
        logger.error(_ERROR_DISPATCH_FAILED, e)
        _display_submit_return(walker)
        return False


def _inject_model_if_needed(
    submit_dict: Dict[str, Any],
    zContext: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Inject model reference into submission dict if needed.

    This helper handles the complex logic for determining where to inject
    the model reference from zContext:
    - If zCRUD exists: Inject into zCRUD (legacy support)
    - If zData exists: Don't inject at root (zData should have its own model)
    - Otherwise: Inject at root level

    Parameters
    ----------
    submit_dict : Dict[str, Any]
        The submission dictionary (after placeholder injection).
    zContext : Dict[str, Any]
        Dialog context containing the model reference.

    Returns
    -------
    Dict[str, Any]
        The submission dictionary with model injected if needed.

    Examples
    --------
    Example 1: zCRUD without model (inject into zCRUD)
        >>> submit_dict = {"zCRUD": {"action": "create", "data": {...}}}
        >>> zContext = {"model": "@.zSchema.users"}
        >>> result = _inject_model_if_needed(submit_dict, zContext)
        >>> # result["zCRUD"]["model"] == "@.zSchema.users"

    Example 2: zData present (don't inject at root)
        >>> submit_dict = {"zData": {"query": "..."}}
        >>> zContext = {"model": "@.zSchema.users"}
        >>> result = _inject_model_if_needed(submit_dict, zContext)
        >>> # result has NO root-level "model" key (zData should have its own)

    Example 3: Neither zCRUD nor zData (inject at root)
        >>> submit_dict = {"command": "custom"}
        >>> zContext = {"model": "@.zSchema.config"}
        >>> result = _inject_model_if_needed(submit_dict, zContext)
        >>> # result["model"] == "@.zSchema.config"

    Notes
    -----
    - This function encapsulates the complex conditional logic from lines 38-43
    - Model injection is only performed if the model key is missing
    - The function modifies submit_dict in place but also returns it for chaining
    """
    model = zContext.get(KEY_MODEL)
    
    # Case 1: zCRUD exists => inject model into zCRUD (legacy support)
    if KEY_ZCRUD in submit_dict and isinstance(submit_dict[KEY_ZCRUD], dict):
        if KEY_MODEL not in submit_dict[KEY_ZCRUD]:
            submit_dict[KEY_ZCRUD][KEY_MODEL] = model
    
    # Case 2: zData exists => don't inject at root (zData should have its own model)
    # Case 3: zLogin exists => inject at root (zLogin needs model for auto-discovery)
    # Case 4: Neither => inject at root level
    elif KEY_MODEL not in submit_dict and KEY_ZDATA not in submit_dict:
        submit_dict[KEY_MODEL] = model
    
    return submit_dict


def _display_submit_return(walker: Any) -> None:
    """
    Display submission return feedback via walker.display.

    This DRY helper displays the standardized return feedback for both
    dict-based and string-based submissions:
    - "zSubmit Return" (indent 3)
    - "zDialog Return" (indent 2)

    Parameters
    ----------
    walker : Any
        Walker instance for accessing display.

    Notes
    -----
    - Extracted to avoid duplication in _handle_dict_submit and _handle_string_submit
    - Uses _STYLE_TILDE ("~") to indicate return/closing
    - Indent levels: _INDENT_SUBMIT (3) for zSubmit, _INDENT_DIALOG (2) for zDialog
    """
    walker.display.zDeclare("zSubmit Return", color=COLOR_ZDIALOG, indent=_INDENT_SUBMIT, style=_STYLE_TILDE)
    walker.display.zDeclare("zDialog Return", color=COLOR_ZDIALOG, indent=_INDENT_DIALOG, style=_STYLE_TILDE)
