"""
Single source of truth for ALL zKernel logging formats.

Inspired by mkma's simple, consistent logging pattern:
https://github.com/israellevin/mkma/blob/master/initramfs_init.sh

This module provides:
- format_log_message(): Single format function used by ALL loggers
- UnifiedFormatter: Python logging.Formatter that uses our format
- format_bootstrap_verbose(): Special colored format for --verbose flag

Philosophy:
- ONE format function that defines the canonical log format
- Bootstrap, Framework, and App loggers ALL use this same format
- Consistent, machine-parseable output across all systems
- Context ([Bootstrap], [Framework], [App]) makes source clear
"""

from datetime import datetime
from typing import Optional
import logging


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE FORMAT TRUTH - All loggers use this
# ═══════════════════════════════════════════════════════════════════════════════

def format_log_message(
    timestamp: datetime,
    level: str,
    context: str,
    message: str,
    include_details: bool = False,
    filename: Optional[str] = None,
    lineno: Optional[int] = None
) -> str:
    """
    Single format function for ALL zKernel logging.
    
    This is the ONLY place where log format is defined.
    Bootstrap, Framework, and App loggers ALL call this.
    
    Args:
        timestamp: When the log occurred
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        context: Logger context (Bootstrap, Framework, App, etc.)
        message: The actual log message
        include_details: If True, include filename and line number
        filename: Source file name (optional)
        lineno: Line number (optional)
    
    Returns:
        Formatted log string
    
    Examples:
        >>> now = datetime.now()
        >>> format_log_message(now, "INFO", "Bootstrap", "Starting...")
        '2025-12-27 18:00:00 [Bootstrap] INFO: Starting...'
        
        >>> format_log_message(now, "ERROR", "Framework", "Failed", True, "zKernel.py", 123)
        '2025-12-27 18:00:00 [Framework] ERROR [zKernel.py:123]: Failed'
    
    Inspired by mkma's format:
        <priority>$(date) [context]: message
    
    Our format:
        TIMESTAMP [CONTEXT] LEVEL: MESSAGE
        TIMESTAMP [CONTEXT] LEVEL [FILE:LINE]: MESSAGE  (with details)
    """
    # Base format: TIMESTAMP [CONTEXT] LEVEL: MESSAGE
    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    if include_details and filename and lineno:
        # Detailed format for file logging (includes source location)
        return f"{time_str} [{context}] {level} [{filename}:{lineno}]: {message}"
    else:
        # Simple format for console/bootstrap
        return f"{time_str} [{context}] {level}: {message}"


# ═══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP-SPECIFIC (for --verbose colored output)
# ═══════════════════════════════════════════════════════════════════════════════

def format_bootstrap_verbose(timestamp: datetime, level: str, message: str) -> str:
    """
    Format bootstrap message for --verbose colored output.
    
    This is the ONLY exception to the single format rule, used ONLY for
    --verbose flag's colored terminal output. File logs still use format_log_message().
    
    Args:
        timestamp: When the log occurred
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: The message
    
    Returns:
        Colored string for terminal display
    
    Examples:
        >>> now = datetime.now()
        >>> format_bootstrap_verbose(now, "INFO", "Starting...")
        '\033[36m[18:00:00] [Bootstrap] Starting...\033[0m'
    """
    time_str = timestamp.strftime("%H:%M:%S")
    
    # ANSI color codes for terminal output
    colors = {
        'DEBUG': '\033[90m',     # Gray
        'SESSION': '\033[96m',   # Bright Cyan (session/environment info)
        'INFO': '\033[36m',      # Cyan
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[91m',  # Bright Red
    }
    reset = '\033[0m'
    
    color = colors.get(level, '')
    return f"{color}[{time_str}] [Bootstrap] {message}{reset}"


# ═══════════════════════════════════════════════════════════════════════════════
# PYTHON LOGGING FORMATTER (uses our format function)
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedFormatter(logging.Formatter):
    """
    Python logging.Formatter that uses our single format function.
    
    This ensures Framework and App loggers use the SAME format as Bootstrap.
    All zKernel loggers should use this formatter to maintain consistency.
    
    Usage:
        # Framework logger (detailed, includes file/line)
        formatter = UnifiedFormatter("Framework", include_details=True)
        handler.setFormatter(formatter)
        
        # App logger (simple, no file/line)
        formatter = UnifiedFormatter("App", include_details=False)
        handler.setFormatter(formatter)
    """
    
    def __init__(self, context: str, include_details: bool = False):
        """
        Initialize formatter.
        
        Args:
            context: Logger context (Bootstrap, Framework, App, ConsoleLogger, etc.)
            include_details: If True, include filename and line numbers in output
        """
        super().__init__()
        self.context = context
        self.include_details = include_details
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record using our single format function.
        
        Args:
            record: Python logging.LogRecord
        
        Returns:
            Formatted log string
        """
        return format_log_message(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            context=self.context,
            message=record.getMessage(),
            include_details=self.include_details,
            filename=record.filename if self.include_details else None,
            lineno=record.lineno if self.include_details else None
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY FORMAT STRINGS (for backward compatibility if needed)
# ═══════════════════════════════════════════════════════════════════════════════

# These match the output of format_log_message() but as format strings
# Keep these for any code that expects format string constants

FORMAT_SIMPLE = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
FORMAT_DETAILED = "%(asctime)s [%(name)s] %(levelname)s [%(filename)s:%(lineno)d]: %(message)s"

# Date format that matches our timestamp format
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

