# zSys/logger/bootstrap.py
"""
Bootstrap logger for pre-boot logging (Layer 0).

Uses Python's standard logging.MemoryHandler for industry-grade buffering.
Buffers log messages before zKernel framework is initialized, then flushes
them into zcli-framework.log once the framework logger is available.

Supports --verbose flag for CLI commands to display bootstrap process.
"""

import logging
from logging.handlers import MemoryHandler
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Import unified format functions and SESSION level
from .formats import format_bootstrap_verbose
from .config import LOG_LEVEL_SESSION


class BootstrapLogger:
    """
    Pre-boot logger using Python's standard logging.MemoryHandler.
    
    Features:
        - Uses stdlib MemoryHandler (industry standard)
        - Buffers all pre-boot logs in memory
        - Flushes to zcli-framework.log when framework ready
        - Supports --verbose flag for stdout display
        - Emergency dump on init failure
    
    Usage:
        # In main.py (ALWAYS use from first line)
        from zOS.logger import BootstrapLogger
        
        boot_logger = BootstrapLogger()
        boot_logger.info("Starting zolo-zcli...")
        boot_logger.debug("Parsing arguments...")
        
        try:
            cli = zKernel()
            # Inject buffered logs (verbose=True shows on stdout)
            boot_logger.flush_to_framework(
                cli.logger,  # Pass LoggerConfig instance
                verbose=args.verbose
            )
        except Exception as e:
            # Emergency dump to stderr + temp file
            boot_logger.emergency_dump(e)
            sys.exit(1)
    """
    
    def __init__(self, name: str = "zolo.zKernel.bootstrap"):
        """Initialize bootstrap logger with Python's MemoryHandler."""
        self.start_time = datetime.now()
        
        # Create logger instance
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Create memory handler (buffers until target is set)
        self.memory_handler = MemoryHandler(
            capacity=1000,  # Buffer up to 1000 records
            flushLevel=logging.CRITICAL + 1,  # Never auto-flush (we flush manually)
            target=None  # No target yet (set during flush_to_framework)
        )
        self.memory_handler.setLevel(logging.DEBUG)
        
        # Add memory handler to logger
        self.logger.addHandler(self.memory_handler)
        
        # Store records for verbose printing and emergency dump
        # We keep our own reference for easier access
        self.buffered_records: List[logging.LogRecord] = []
        
        # Add a secondary handler to capture records for verbose/emergency
        class RecordCapture(logging.Handler):
            """Captures records without emitting (for verbose/emergency access)."""
            def __init__(self, records_list):
                super().__init__()
                self.records = records_list
            
            def emit(self, record):
                self.records.append(record)
        
        self.capture_handler = RecordCapture(self.buffered_records)
        self.capture_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.capture_handler)
    
    # Convenience methods (delegate to stdlib logger)
    def debug(self, msg: str, *args):
        """Log debug message."""
        self.logger.debug(msg, *args)
    
    def info(self, msg: str, *args):
        """Log info message."""
        self.logger.info(msg, *args)
    
    def session(self, msg: str, *args):
        """Log session/environment/system information."""
        # Use custom SESSION level (value 15, between DEBUG and INFO)
        self.logger.log(logging.SESSION, msg, *args)
    
    def warning(self, msg: str, *args):
        """Log warning message."""
        self.logger.warning(msg, *args)
    
    def error(self, msg: str, *args):
        """Log error message."""
        self.logger.error(msg, *args)
    
    def critical(self, msg: str, *args):
        """Log critical message."""
        self.logger.critical(msg, *args)
    
    def flush_to_framework(self, logger_config, verbose: bool = False):
        """
        Flush buffered messages to framework loggers with semantic routing.
        
        Routing strategy:
            - ERROR/CRITICAL → BOTH framework and session_framework (all audiences)
            - DEBUG/INFO/SESSION → session_framework ONLY (user context)
        
        Args:
            logger_config: LoggerConfig instance (zcli.logger)
            verbose: If True, print bootstrap messages to console first (dark gray)
        
        Note:
            PHASE 1: Print bootstrap messages in real-time order (dark gray)
            PHASE 2: Flush to framework loggers (standard logging framework)
        """
        if not self.buffered_records:
            return
        
        # Calculate elapsed time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        message_count = len(self.buffered_records)
        
        # PHASE 1: Print Bootstrap messages in real-time order (dark gray mkna format)
        # These happened BEFORE framework logger exists, so print them first
        if verbose:
            for record in self.buffered_records:
                self._print_verbose_message(record)
        
        # PHASE 2: Inject all buffered records with semantic routing
        for record in self.buffered_records:
            msg = record.getMessage()
            
            # Route by severity level
            if record.levelno >= logging.ERROR:
                # ERROR/CRITICAL → BOTH loggers (framework devs + users)
                logger_config.framework.log(record.levelno, msg)
                logger_config.session_framework.log(record.levelno, msg)
            else:
                # DEBUG/INFO/SESSION → session_framework ONLY (user context)
                logger_config.session_framework.log(record.levelno, msg)
        
        # Log injection completion
        logger_config.session_framework.info(
            "[Bootstrap] Injection complete: %d messages, %.3fs", 
            message_count, 
            elapsed
        )
        
        # Clear buffer
        self.buffered_records.clear()
        self.memory_handler.flush()
        self.memory_handler.buffer.clear()
    
    def flush_to_ecosystem(self, ecosystem_logger, verbose: bool = False):
        """
        Flush buffered messages to ecosystem logger.
        
        Used for zolo CLI commands that don't initialize zKernel:
            - zolo --version
            - zolo install
            - zolo --help
        
        Args:
            ecosystem_logger: EcosystemLogger instance
            verbose: If True, print to console in mkna format (gray, simple)
        
        Note:
            FILE: Uses full format (timestamp, context, level, details)
            CONSOLE: Uses mkna format (simple gray bootstrap style)
            This maintains consistency with mkna pattern philosophy.
        """
        if not self.buffered_records:
            return

        # Calculate elapsed time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        message_count = len(self.buffered_records)

        # PHASE 1: Print Bootstrap messages in real-time order (dark gray mkna format)
        # These happened BEFORE ecosystem logger exists, so print them first
        if verbose:
            for record in self.buffered_records:
                self._print_verbose_message(record)
        
        # PHASE 2: Inject all buffered records to ecosystem logger
        for record in self.buffered_records:
            msg = record.getMessage()
            
            # Route to appropriate log level
            if record.levelno >= logging.ERROR:
                ecosystem_logger.error(msg)
            elif record.levelno >= logging.WARNING:
                ecosystem_logger.warning(msg)
            elif record.levelno >= logging.INFO:
                ecosystem_logger.info(msg)
            else:
                ecosystem_logger.debug(msg)
        
        # Log injection completion
        ecosystem_logger.info(
            "[Bootstrap] Injection complete: %d messages, %.3fs", 
            message_count, 
            elapsed
        )
        
        # Clear buffer
        self.buffered_records.clear()
        self.memory_handler.flush()
        self.memory_handler.buffer.clear()
    
    def print_buffered_logs(self):
        """
        Print all buffered logs to stdout (for cases without any logger).
        
        DEPRECATED: Use flush_to_ecosystem() instead for proper log persistence.
        This method is kept for backward compatibility but should be phased out.
        """
        if not self.buffered_records:
            return
        
        # Print all buffered messages
        for record in self.buffered_records:
            self._print_verbose_message(record)
        
        # Show completion with message count (consistent with flush_to_framework)
        elapsed = (datetime.now() - self.start_time).total_seconds()
        message_count = len(self.buffered_records)
        print(f"[Bootstrap] ✓ Initialized: {message_count} messages, {elapsed:.3f}s\n")
        
        # Clear buffer
        self.buffered_records.clear()
    
    def _print_verbose_message(self, record: logging.LogRecord):
        """Print log record to stdout in verbose mode using unified format."""
        timestamp = datetime.fromtimestamp(record.created)
        level = record.levelname
        message = record.getMessage()
        
        formatted = format_bootstrap_verbose(timestamp, level, message)
        print(formatted)
    
    def emergency_dump(self, exception: Optional[Exception] = None):
        """
        Emergency dump to stderr and temp file if framework init fails.
        
        Args:
            exception: The exception that caused init failure (if any)
        """
        print("\n" + "=" * 70, file=sys.stderr)
        print("❌ CRITICAL: zKernel Framework Initialization Failed", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        
        if exception:
            print(f"\nError: {exception}\n", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
        
        print(f"\nPre-boot log buffer ({len(self.buffered_records)} messages):\n", file=sys.stderr)
        
        # Dump buffered messages
        for record in self.buffered_records:
            timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] {record.levelname}: {record.getMessage()}", file=sys.stderr)
        
        print("\n" + "=" * 70, file=sys.stderr)
        
        # Save to temp file in current working directory as fallback
        temp_file = Path.cwd() / ".zolo-zcli-bootstrap-error.log"
        try:
            with open(temp_file, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("zCLI Bootstrap Failure Log\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")
                
                if exception:
                    f.write(f"Exception: {exception}\n\n")
                    import traceback
                    f.write(traceback.format_exc())
                    f.write("\n")
                
                f.write("Pre-boot Log Buffer:\n")
                f.write("-" * 70 + "\n\n")
                
                # Dump buffered log records
                for record in self.buffered_records:
                    timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
                    f.write(f"[{timestamp}] {record.levelname}: {record.getMessage()}\n")
            
            print(f"\n💾 Bootstrap log saved to: {temp_file}", file=sys.stderr)
        except Exception as e:
            print(f"\n⚠️  Failed to save bootstrap log: {e}", file=sys.stderr)

