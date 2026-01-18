"""
zSys.logger - Unified Logging System

Pre-boot and standalone logging utilities with consistent format.

Inspired by mkma's simple, consistent logging pattern:
https://github.com/israellevin/mkma/blob/master/initramfs_init.sh

Architecture:
- formats.py: Single source of truth for log format
- bootstrap.py: Pre-boot logger with buffer injection
- console.py: Minimal console logger (WSGI workers)

Philosophy:
- ONE format function (format_log_message) defines all log output
- Bootstrap, Framework, and App loggers use the SAME format
- Consistent, machine-parseable output: TIMESTAMP [CONTEXT] LEVEL: MESSAGE

Usage:
    # Bootstrap logger (pre-boot)
    from zSys.logger import BootstrapLogger
    boot_logger = BootstrapLogger()
    boot_logger.info("Starting...")
    
    # Console logger (WSGI workers)
    from zSys.logger import ConsoleLogger
    logger = ConsoleLogger("WSGI")
    logger.info("Server started")
    
    # Unified formatter (Framework/App loggers)
    from zSys.logger import UnifiedFormatter
    formatter = UnifiedFormatter("Framework", include_details=True)
    
    # Direct format functions
    from zSys.logger import format_log_message, format_bootstrap_verbose
"""

# Export bootstrap logger
from .bootstrap import BootstrapLogger

# Export console logger
from .console import ConsoleLogger

# Export unified format functions and formatter
from .formats import (
    UnifiedFormatter,
    format_log_message,
    format_bootstrap_verbose,
    FORMAT_SIMPLE,
    FORMAT_DETAILED,
    DATE_FORMAT,
)

# Export logger configuration utilities
from .config import (
    get_log_level_from_zspark,
    should_suppress_init_prints,
    LOG_LEVEL_SESSION,
    LOG_LEVEL_PROD,
)

__all__ = [
    # Loggers
    "BootstrapLogger",
    "ConsoleLogger",
    # Formatter
    "UnifiedFormatter",
    # Format functions
    "format_log_message",
    "format_bootstrap_verbose",
    # Logger configuration
    "get_log_level_from_zspark",
    "should_suppress_init_prints",
    "LOG_LEVEL_SESSION",
    "LOG_LEVEL_PROD",
    # Legacy constants
    "FORMAT_SIMPLE",
    "FORMAT_DETAILED",
    "DATE_FORMAT",
]

