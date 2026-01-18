# zCLI/subsystems/zFunc/zFunc_modules/builtin_functions.py
"""
Built-in functions for zCLI (callable via & syntax in zUI).

Functions:
    - zNow: Get current date/time formatted per zConfig
    - (future: zUser, zEnv, zMachine, etc.)
"""

from zOS import datetime, Any, Optional


def zNow(
    format_type: str = "datetime",
    custom_format: Optional[str] = None,
    zcli: Optional[Any] = None
) -> str:
    """
    Get current date/time formatted according to zConfig settings.
    
    Respects 5-tier config hierarchy:
    1. System defaults
    2. User config
    3. User legacy config
    4. Environment (.zEnv)
    5. zSpark (strongest override)
    
    Args:
        format_type: "date", "time", or "datetime" (default: "datetime")
        custom_format: Override config format (e.g., "yyyy-mm-dd")
        zcli: zCLI instance (required for config access)
        
    Returns:
        Formatted date/time string
        
    Examples:
        &zNow → "19122025 14:30:00" (datetime_format from config)
        &zNow('date') → "19122025" (date_format from config)
        &zNow('time') → "14:30:00" (time_format from config)
        &zNow(custom_format='yyyy-mm-dd') → "2025-12-19"
    """
    # Get format from config or use custom
    if custom_format:
        format_string = custom_format
    else:
        # Access zConfig.machine settings
        if not zcli:
            # Fallback to ISO format if no config access
            return datetime.now().isoformat()
        
        if format_type == "date":
            format_string = zcli.config.machine.get("date_format", "ddmmyyyy")
        elif format_type == "time":
            format_string = zcli.config.machine.get("time_format", "HH:MM:SS")
        else:  # datetime
            format_string = zcli.config.machine.get("datetime_format", "ddmmyyyy HH:MM:SS")
    
    # Convert zCLI format to Python strftime format
    py_format = _convert_format_to_strftime(format_string)
    
    # Return formatted current time
    return datetime.now().strftime(py_format)


def _convert_format_to_strftime(zcli_format: str) -> str:
    """
    Convert zCLI date format to Python strftime format.
    
    zCLI Format Tokens:
        yyyy → %Y (4-digit year)
        yy → %y (2-digit year)
        mm → %m (2-digit month)
        dd → %d (2-digit day)
        HH → %H (24-hour)
        MM → %M (minutes)
        SS → %S (seconds)
    
    Args:
        zcli_format: zCLI format string (e.g., "ddmmyyyy")
        
    Returns:
        Python strftime format string (e.g., "%d%m%Y")
    """
    conversions = {
        "yyyy": "%Y",
        "yy": "%y",
        "mm": "%m",
        "dd": "%d",
        "HH": "%H",
        "MM": "%M",
        "SS": "%S",
    }
    
    result = zcli_format
    for zcli_token, py_token in conversions.items():
        result = result.replace(zcli_token, py_token)
    
    return result

