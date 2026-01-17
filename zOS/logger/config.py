# zOS/logger/config.py
"""
Logger configuration utilities.

Provides helpers for extracting and validating log levels from zSpark configuration.
"""

from typing import Optional, Dict, Any


# Log Level Constants
LOG_LEVEL_SESSION = "SESSION"  # Session/environment/system information (level 15)
LOG_LEVEL_PROD = "PROD"  # Special level: silent console, file-only logging
LOG_LEVEL_KEY_ALIASES = ("logger", "log_level", "logLevel", "zLogger")

# Register SESSION level with Python logging (between INFO:20 and DEBUG:10)
import logging
if not hasattr(logging, 'SESSION'):
    logging.addLevelName(15, 'SESSION')
    logging.SESSION = 15


def get_log_level_from_zspark(zspark_obj: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract log level from zSpark object using known key aliases.
    
    Args:
        zspark_obj: zSpark configuration dictionary
        
    Returns:
        Log level string or None if not found
    """
    if not zspark_obj:
        return None
    
    for key in LOG_LEVEL_KEY_ALIASES:
        if key in zspark_obj:
            level = zspark_obj[key]
            return str(level).upper() if level else None
    
    return None


def should_suppress_init_prints(log_level: Optional[str]) -> bool:
    """
    Check if initialization prints should be suppressed based on log level.
    
    In PROD mode, all console output is suppressed (logs go to file only).
    
    Args:
        log_level: Log level string (e.g., "PROD", "INFO", "DEBUG")
        
    Returns:
        True if prints should be suppressed, False otherwise
    
    Note:
        This is an internal helper for backward compatibility.
        New code should use deployment mode checking instead.
    """
    if not log_level:
        return False
    
    return log_level.upper() == LOG_LEVEL_PROD

