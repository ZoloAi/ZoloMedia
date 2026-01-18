# zCLI/subsystems/zParser/parser_modules/parser_functions.py
"""
Function call resolution for zParser.

Handles parsing and resolution of &function calls and %variable references in zUI content.
This enables calling built-in functions like &zNow and accessing variables like %session.username
directly from YAML configuration.
"""

import re
from zOS import Any


def resolve_variables(value: str, zcli: Any, context: Any = None) -> str:
    """
    Resolve %variable references in zUI content.
    
    Syntax:
        %session.username → session["username"]
        %session.email → session["email"]
        %data.user.name → context["_resolved_data"]["user"]["name"]  # NEW v1.5.12
        %myvar → session["zVars"]["myvar"]
        %zConv.field → (future: dialog context)
        %zHat.step → (future: wizard context)
    
    Args:
        value: String potentially containing %variable references
        zcli: zCLI instance for session access
        context: Optional execution context (contains _resolved_data from queries)
        
    Returns:
        String with variable references resolved to their values
        
    Examples:
        >>> resolve_variables("Hello %session.username!", zcli)
        "Hello Gal Nachshon!"
        
        >>> resolve_variables("Email: %session.email", zcli)
        "Email: gal.video.prod@gmail.com"
        
        >>> resolve_variables("Name: %data.user.name", zcli, context)
        "Name: Gal Nachshon"
        
        >>> resolve_variables("Var: %myvar", zcli)
        "Var: my_value"
    
    Security (v1.5.12):
        The %data.* syntax enables declarative data queries in templates while
        keeping actual database credentials in .zEnv (never committed to Git).
        This is superior to Flask/Jinja where queries are in Python code.
    """
    if not zcli or not hasattr(zcli, 'session'):
        return value
    
    # Pattern: %identifier.field.nested or %identifier.field or %identifier
    # Supports multi-level nesting: %data.user.profile.avatar
    pattern = r'%([a-zA-Z_][a-zA-Z0-9_]*)(?:\.([a-zA-Z_][a-zA-Z0-9_.]+))?'
    
    def replace_variable(match):
        namespace = match.group(1)  # e.g., "session", "data", "myvar", "zConv"
        field_path = match.group(2)  # e.g., "username", "user.name", "user.profile.avatar"
        
        # Handle session.field
        if namespace == "session" and field_path:
            # Access session["field"]
            return str(zcli.session.get(field_path, f"%session.{field_path}"))
        
        # Handle session (entire session dict)
        elif namespace == "session" and not field_path:
            return str(zcli.session)
        
        # Handle data.query.field (NEW v1.5.12 - Flask/Jinja pattern)
        elif namespace == "data" and field_path and context:
            # Access context["_resolved_data"]["query"]["field"]
            if "_resolved_data" in context:
                parts = field_path.split('.')  # "user.name" → ["user", "name"]
                result = context["_resolved_data"]
                
                try:
                    for part in parts:
                        if isinstance(result, dict):
                            # Try string key first, then integer key if part is numeric
                            if part in result:
                                result = result.get(part)
                            elif part.isdigit() and int(part) in result:
                                result = result.get(int(part))
                            else:
                                # Key not found
                                return ''
                        elif isinstance(result, list) and part.isdigit():
                            result = result[int(part)]
                        else:
                            # Can't traverse further
                            return match.group(0)
                    
                    # Successfully resolved
                    return str(result) if result is not None else ''
                except (KeyError, IndexError, TypeError):
                    # Path not found - return empty string
                    return ''
            # No _resolved_data in context
            return ''
        
        # Handle zVars (user variables)
        elif not field_path:
            # Access session["zVars"]["varname"]
            zvars = zcli.session.get("zVars", {})
            if namespace in zvars:
                return str(zvars[namespace])
            # If not found, return as-is (allows future extensions)
            return match.group(0)
        
        # Future: zConv.field, zHat.field, etc.
        # For now, return as-is
        return match.group(0)
    
    return re.sub(pattern, replace_variable, value)


def resolve_function_call(value: str, zcli: Any) -> str:
    """
    Resolve &function calls in zUI content.
    
    Syntax:
        &zNow → zNow()
        &zNow('date') → zNow('date')
        &zNow(custom_format='yyyy-mm-dd') → zNow(custom_format='yyyy-mm-dd')
    
    Args:
        value: String potentially containing &function calls
        zcli: zCLI instance for function execution
        
    Returns:
        String with function calls resolved to their values
        
    Examples:
        >>> resolve_function_call("Today is &zNow('date')", zcli)
        "Today is 19122025"
        
        >>> resolve_function_call("Report: &zNow", zcli)
        "Report: 19122025 14:30:00"
    """
    # Pattern: &functionName or &functionName(...args...)
    pattern = r'&(\w+)(?:\((.*?)\))?'
    
    def replace_function(match):
        func_name = match.group(1)
        args_str = match.group(2) if match.group(2) else ""
        
        # Handle zNow
        if func_name == "zNow":
            if not args_str:
                return zcli.zfunc.zNow()
            else:
                # Parse simple arg: 'date', 'time', or custom_format='...'
                args_str = args_str.strip().strip("'\"")
                if args_str in ["date", "time", "datetime"]:
                    return zcli.zfunc.zNow(format_type=args_str)
                elif args_str.startswith("custom_format="):
                    custom_fmt = args_str.split("=", 1)[1].strip("'\"")
                    return zcli.zfunc.zNow(custom_format=custom_fmt)
                else:
                    # Default: treat as format_type
                    return zcli.zfunc.zNow(format_type=args_str)
        
        # Unknown function - return as-is (no modification)
        return match.group(0)
    
    return re.sub(pattern, replace_function, value)

