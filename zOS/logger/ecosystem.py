# zOS/logger/ecosystem.py
"""
zOS logger for zolo CLI operations (Layer 0).

Handles logging for OS-level ecosystem commands that don't involve zKernel:
- zolo --version
- zolo install
- zolo --help
- Other CLI operations

Independent of zKernel framework - zOS logs its own operations.
"""

import logging
from pathlib import Path
from datetime import datetime
import platform
import sys

from .formats import UnifiedFormatter


class EcosystemConsoleFormatter(logging.Formatter):
    """Custom formatter for zOS console output with PRIMARY color."""
    
    def __init__(self):
        """Initialize formatter with no date/time (mkna pattern)."""
        super().__init__()
        from zOS.formatting import Colors
        self.colors = Colors
    
    def format(self, record):
        """Format record with [zOS] prefix in PRIMARY color."""
        msg = record.getMessage()
        return f"{self.colors.PRIMARY}[zOS]{self.colors.RESET} {msg}"


class EcosystemLogger:
    """
    Logger for zOS (Zolo Operating System) CLI operations.
    
    Characteristics:
        - Logger name: "zolo.os"
        - File: zOS.log (detailed format, all levels)
        - Console: DEBUG+ in verbose mode, WARNING+ otherwise
        - Independent: No zKernel dependency
    
    Logging Principles:
        - Record everything to file (DEBUG+)
        - Console output controlled by handler level (not manual checks)
        - Standard Python logging framework handles routing
    
    Usage:
        from zOS.logger import EcosystemLogger
        
        os_logger = EcosystemLogger(verbose=True)
        os_logger.info("Installing package: zKernel")  # Shows in console (verbose)
        os_logger.debug("Download complete: 1.2MB")    # Shows in console (verbose)
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize ecosystem logger with file and console handlers.
        
        Args:
            verbose: If True, console shows DEBUG+; otherwise WARNING+
        """
        self.verbose = verbose
        self.logger = self._setup_logger(verbose)
    
    def _setup_logger(self, verbose: bool) -> logging.Logger:
        """Setup zOS logger with file and console handlers."""
        # Create logger
        logger = logging.getLogger("zolo.os")
        logger.setLevel(logging.DEBUG)  # Capture all levels
        logger.propagate = False
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Get log file path
        log_file = self._get_log_file_path()
        
        # FILE HANDLER - Detailed format, all levels
        file_formatter = UnifiedFormatter("zOS", include_details=True)
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, print warning but continue
            print(f"⚠️  Warning: Failed to setup ecosystem file logging: {e}", file=sys.stderr)
        
        # CONSOLE HANDLER - Simple format with PRIMARY color
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = logging.DEBUG if verbose else logging.WARNING
        console_handler.setLevel(console_level)
        console_handler.setFormatter(EcosystemConsoleFormatter())
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_log_file_path(self) -> Path:
        """Get zOS log file path using centralized path utilities."""
        from zOS.paths import get_ecosystem_logs
        logs_dir = get_ecosystem_logs()
        return logs_dir / "zOS.log"
    
    # Convenience logging methods
    # These delegate to the logger; handlers control console output based on level
    
    def debug(self, msg: str, *args):
        """Log debug message (file always, console if verbose)."""
        self.logger.debug(msg, *args)
    
    def info(self, msg: str, *args):
        """Log info message (file always, console if verbose or warning+)."""
        self.logger.info(msg, *args)
    
    def warning(self, msg: str, *args):
        """Log warning message (file always, console always)."""
        self.logger.warning(msg, *args)
    
    def error(self, msg: str, *args):
        """Log error message (file always, console always)."""
        self.logger.error(msg, *args)
    
    def critical(self, msg: str, *args):
        """Log critical message (file always, console always)."""
        self.logger.critical(msg, *args)
