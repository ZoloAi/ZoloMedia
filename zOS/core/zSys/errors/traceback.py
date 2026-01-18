# zSys/errors/traceback.py
"""Centralized traceback utilities with enhanced error handling and interactive UI support."""

import traceback
import sys
import logging
from pathlib import Path
from typing import Optional, Any


class zTraceback:
    """Enhanced error handling with consistent traceback formatting."""

    def __init__(self, logger=None, zcli=None):
        """Initialize zTraceback with optional logger and zCLI instance."""
        self.logger = logger
        self.zcli = zcli

        # Exception context storage for interactive handling
        self.last_exception = None
        self.last_context = {}

        # Exception hook management
        self._original_excepthook = sys.excepthook
        self._hook_installed = False

    def install_exception_hook(self):
        """Install custom exception hook for automatic interactive handling."""
        if self._hook_installed:
            return  # Already installed
        
        def custom_excepthook(exc_type, exc_value, exc_traceback):
            """Custom exception handler that launches interactive UI."""
            # Check if zTraceback is still enabled in session
            if self.zcli and hasattr(self.zcli, 'session'):
                ztraceback_enabled = self.zcli.session.get('zTraceback', False)
                if not ztraceback_enabled:
                    # Fall back to default Python behavior
                    self._original_excepthook(exc_type, exc_value, exc_traceback)
                    return
            
            # Launch interactive handler
            try:
                self.interactive_handler(
                    exc_value,
                    context={
                        'type': exc_type.__name__,
                        'auto_caught': True
                    }
                )
            except Exception as handler_error:
                # Fallback if interactive handler fails
                if self.logger:
                    self.logger.error(f"Interactive handler failed: {handler_error}")
                self._original_excepthook(exc_type, exc_value, exc_traceback)
        
        # Install the hook
        sys.excepthook = custom_excepthook
        self._hook_installed = True
    
    def uninstall_exception_hook(self):
        """Restore original exception hook."""
        if self._hook_installed:
            sys.excepthook = self._original_excepthook
            self._hook_installed = False

    def format_exception(self, exc: Exception, include_locals: bool = False) -> str:
        """Format exception with enhanced details (include_locals for debug mode)."""
        if include_locals:
            # Enhanced format with local variables
            tb_lines = traceback.format_exception(
                type(exc), exc, exc.__traceback__
            )
            return ''.join(tb_lines)

        # Standard format
        return ''.join(traceback.format_exception_only(type(exc), exc))

    def get_traceback_info(self, exc: Exception) -> dict:
        """Extract structured traceback information (file, line, function, error details)."""
        tb = exc.__traceback__
        if not tb:
            return {
                'exception_type': type(exc).__name__,
                'exception_message': str(exc)
            }

        # Get the last frame (where error occurred)
        while tb.tb_next:
            tb = tb.tb_next

        frame = tb.tb_frame
        return {
            'file': frame.f_code.co_filename,
            'line': tb.tb_lineno,
            'function': frame.f_code.co_name,
            'exception_type': type(exc).__name__,
            'exception_message': str(exc)
        }

    def log_exception(self,
                     exc: Exception, 
                     message: str = "Exception occurred",
                     context: Optional[dict] = None,
                     include_locals: bool = False):
        """Log exception with enhanced context (Week 6.1.1)."""
        # Store exception for potential interactive handling
        self.last_exception = exc
        self.last_context = context or {}

        if not self.logger:
            # Fallback to print if no logger
            print(f"{message}: {exc}", file=sys.stderr)
            traceback.print_exc()
            return

        # Log the main error message with full traceback
        self.logger.error(message + ": %s", exc, exc_info=True)

        # Add structured context if provided
        if context:
            self.logger.debug("Error context: %s", context)

        # Add enhanced details in debug mode
        if include_locals and self.logger.isEnabledFor(logging.DEBUG):
            info = self.get_traceback_info(exc)
            self.logger.debug("Error location: %s:%s in %s()",
                            info.get('file', 'unknown'),
                            info.get('line', '?'),
                            info.get('function', 'unknown'))

    def interactive_handler(self, exc: Exception, 
                          context: Optional[dict] = None) -> Any:
        """Launch interactive traceback UI (Walker) for exception handling."""
        # Store exception details for UI access
        self.last_exception = exc
        self.last_context = context or {}

        if not self.zcli:
            # Fallback: if no zcli instance, just log and return
            if self.logger:
                self.logger.error("Interactive traceback unavailable (no zcli instance)")
            print(f"Error: {exc}", file=sys.stderr)
            traceback.print_exc()
            return None

        # Launch Walker UI for interactive error handling
        try:
            # Import zCLI here to avoid circular dependency (zCLI.zCLI imports zTraceback)
            import zCLI

            # Get package directory to find UI file
            zcli_package_dir = Path(zCLI.__file__).parent

            # Get parent's deployment mode and logger level to inherit
            parent_deployment = self.zcli.config.get_environment('deployment') if self.zcli and hasattr(self.zcli, 'config') else 'Development'
            parent_logger_level = self.zcli.session.get('zLogger', 'INFO') if self.zcli and hasattr(self.zcli, 'session') else 'INFO'

            # Create new zCLI instance for traceback UI (inherit deployment and logger from parent)
            traceback_cli = zCLI.zCLI({
                "zSpace": str(zcli_package_dir),
                "zVaFile": "@.UI.zUI.zcli_sys",
                "zBlock": "Traceback",
                "deployment": parent_deployment,  # Inherit parent's deployment mode
                "logger": parent_logger_level,     # Inherit parent's logger level
            })

            # Pass traceback handler to the new instance so UI can access exception
            traceback_cli.zTraceback.last_exception = exc
            traceback_cli.zTraceback.last_context = self.last_context

            return traceback_cli.walker.run()

        except Exception as ui_error:
            # Fallback if UI launch fails
            if self.logger:
                self.logger.error("Failed to launch interactive traceback UI: %s", ui_error)
            print(f"Original Error: {exc}", file=sys.stderr)
            traceback.print_exc()
            return None


# -----------------------------------------------------------------------
# Interactive Traceback Display Functions
# -----------------------------------------------------------------------

def display_error_summary(zcli):
    """Display error summary with details, location, and context (View Details)."""
    handler = zcli.zTraceback
    exc = handler.last_exception
    
    if not exc:
        zcli.display.warning("No exception to display")
        return None
    
    # Main header - Error Details
    zcli.display.handle({"event": "header", "label": "Error Details", "color": "RED", "style": "full"})
    
    # Exception summary with error signal
    exc_type = type(exc).__name__
    exc_message = str(exc)
    zcli.display.handle({"event": "error", "content": f"{exc_type}: {exc_message}", "indent": 0})
    
    # Location info - clean list format
    info = handler.get_traceback_info(exc)
    if info:
        zcli.display.text("\nLocation:", indent=0, break_after=False)
        location_items = [
            f"File: {info.get('file', 'unknown')}",
            f"Line: {info.get('line', '?')}",
            f"Function: {info.get('function', 'unknown')}()"
        ]
        zcli.display.list(location_items, style="none", indent=1)
    
    # Context section (if available)
    if handler.last_context:
        zcli.display.handle({"event": "header", "label": "Context", "color": "CYAN", "style": "single"})
        zcli.display.json_data(handler.last_context, indent=1, color=False)
    
    # Actionable hint (if available from zCLIException)
    if hasattr(exc, 'hint') and exc.hint:
        zcli.display.handle({"event": "header", "label": "Hint", "color": "GREEN", "style": "single"})
        hint_lines = exc.hint.split('\n')
        for line in hint_lines:
            if line.strip():
                zcli.display.text(line, indent=1, break_after=False)
    
    # Final separator and single pause
    zcli.display.handle({"event": "header", "label": "", "color": "RESET", "style": "single"})
    zcli.display.text("", indent=0, break_after=True, break_message="Press Enter to return to menu...")
    
    return None


def display_full_traceback(zcli):
    """Display complete stack trace (Full Traceback)."""
    handler = zcli.zTraceback
    exc = handler.last_exception
    
    if not exc:
        zcli.display.warning("No exception to display")
        return None
    
    # Full traceback section
    zcli.display.handle({"event": "header", "label": "Full Traceback", "color": "CYAN", "style": "full"})
    
    # Format traceback frames
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    for line in tb_lines:
        stripped = line.rstrip()
        if stripped:
            # Don't break after each line - show all at once
            zcli.display.text(stripped, indent=1, break_after=False)
    
    # Final separator and single pause
    zcli.display.handle({"event": "header", "label": "", "color": "RESET", "style": "single"})
    zcli.display.text("", indent=0, break_after=True, break_message="Press Enter to return to menu...")
    
    return None


def display_formatted_traceback(zcli):
    """Display complete formatted traceback (calls both summary and full traceback)."""
    display_error_summary(zcli)
    display_full_traceback(zcli)
    return None


class ExceptionContext:
    """Context manager for consistent exception handling with logging and optional retry."""
    
    def __init__(
        self,
        ztraceback: "zTraceback",
        operation: str,
        context: Optional[dict] = None,
        reraise: bool = False,
        default_return: Any = None
    ):
        """Initialize exception context (operation desc, context dict, reraise flag, default_return)."""
        self.ztraceback = ztraceback
        self.operation = operation
        self.context = context or {}
        self.reraise = reraise
        self.default_return = default_return
        self.exception = None
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Store the exception for potential inspection
            self.exception = exc_val

            # Log the exception
            self.ztraceback.log_exception(
                exc_val,
                message=f"Error during {self.operation}",
                context=self.context
            )

            # Reraise if requested
            if self.reraise:
                return False

            # Set default return value
            self.result = self.default_return

            # Suppress exception (return True)
            return True

        return False
