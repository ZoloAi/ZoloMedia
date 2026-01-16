# zOS/machine/detectors/shared.py
"""Shared utilities and constants for machine detection."""

import logging
import os
from pathlib import Path
from typing import Optional

# Module-level logger
logger = logging.getLogger("zolo.os.machine")

# Logging
LOG_PREFIX = "[MachineDetector]"

# Subprocess timeouts
SUBPROCESS_TIMEOUT_SEC = 5

# Memory conversion constants
BYTES_PER_KB = 1024
KB_PER_MB = 1024
MB_PER_GB = 1024
BYTES_PER_GB = 1024 ** 3

# Default values
DEFAULT_SHELL = "/bin/sh"
DEFAULT_TIMEZONE = "system"
DEFAULT_TIME_FORMAT = "HH:MM:SS"
DEFAULT_DATE_FORMAT = "ddmmyyyy"
DEFAULT_DATETIME_FORMAT = "ddmmyyyy HH:MM:SS"

# Logging Helpers

def _log_info(message: str, log_level: Optional[str] = None, is_production: bool = False) -> None:
    """Log info message (suppressed in Production deployment)."""
    if not is_production:
        logger.debug("%s %s", LOG_PREFIX, message)

def _log_warning(message: str, log_level: Optional[str] = None, is_production: bool = False) -> None:
    """Log warning message (suppressed in Production deployment)."""
    if not is_production:
        logger.warning("%s %s", LOG_PREFIX, message)

def _log_error(message: str, log_level: Optional[str] = None, is_production: bool = False) -> None:
    """Log error message (always shown, even in Production)."""
    logger.error("%s %s", LOG_PREFIX, message)

def _log_config(message: str, log_level: Optional[str] = None, is_production: bool = False) -> None:
    """Log config message (suppressed in Production deployment)."""
    if not is_production:
        logger.debug("%s %s", LOG_PREFIX, message)

def _safe_getcwd() -> str:
    """Get current directory, falling back to home if deleted."""
    try:
        return os.getcwd()
    except (FileNotFoundError, OSError):
        # Directory was deleted (common in tests with temp directories)
        # Fall back to home directory
        return str(Path.home())

