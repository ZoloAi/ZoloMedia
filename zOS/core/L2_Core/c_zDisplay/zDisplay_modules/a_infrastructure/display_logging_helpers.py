# zCLI/L2_Core/c_zDisplay/zDisplay_modules/a_infrastructure/display_logging_helpers.py

"""
Display Logging Helpers - Tier 0 Infrastructure
================================================

This module provides centralized logger integration for all display events.
It standardizes how events check logging levels, access loggers, and determine
whether system messages should be displayed.

Tier Architecture:
    Tier 0: Infrastructure (THIS MODULE) - Shared logging integration
    Tier 1: Primitives - Raw I/O foundation
    Tier 2+: Event packages - Use these utilities for consistent logging

Purpose:
    - DRY: Single implementation for logger access patterns
    - Consistency: Same logging behavior across all events
    - Deployment-Aware: Respects dev/prod/testing modes
    - Testability: Easy to mock logger in tests

Functions:
    should_show_system_message(display)
        Check if system messages should be displayed based on deployment/logging level
        
    get_display_logger(display)
        Get logger instance from display hierarchy with fallback
        
    log_event_start(logger, event_name, context)
        Log event start with context (debug mode only)
        
    log_event_end(logger, event_name, duration)
        Log event completion with duration

Dependencies:
    - typing: Type hints
    - time: Duration tracking for log_event_end

Extracted From:
    - display_event_system._should_show_sysmsg() (line 2323-2386)
    - display_event_system (zDialog logging patterns)
    - display_event_timebased (logger access patterns)
"""

from typing import Any, Optional, Dict
import time


def should_show_system_message(display: Any) -> bool:
    """
    Check if system messages should be displayed based on deployment mode.
    
    System messages (zDeclare) are conditionally displayed to prevent verbose output
    in production and testing environments. This respects zCLI's logging framework
    and deployment configuration.
    
    Args:
        display: zDisplay instance (for accessing zcli.logger and zcli.config)
    
    Returns:
        bool: True if system messages should be displayed, False otherwise
    
    Check Priority:
        1. Logger method:      zcli.logger.should_show_sysmsg() (if available)
        2. Config deployment:  zcli.config.is_production() / is_testing()
        3. Legacy debug flag:  session.get("debug") (backward compatibility)
        4. Default:            True (development mode - show messages)
    
    Deployment Rules:
        - Development: Show system messages
        - Testing:     Hide system messages (clean test output)
        - Production:  Hide system messages (clean user experience)
    
    Example:
        >>> if should_show_system_message(self.display):
        >>>     self.BasicOutputs.header("Loading Config...", color="MAIN")
    
    Usage:
        # In zDeclare event
        if not should_show_system_message(self.display):
            return  # Don't display system message in prod/test
        
        # Display system message in dev mode
        self.BasicOutputs.header(label, color, indent, style)
    
    Notes:
        - Respects zCLI's logging framework
        - Falls back gracefully if logger/config not available
        - Used by zDeclare to conditionally display system messages
    
    Extracted From:
        display_event_system._should_show_sysmsg() (line 2323-2386)
    """
    if not display or not hasattr(display, 'session'):
        return True  # Default: show messages (no deployment info)
    
    session = display.session
    
    # Priority 1: Check logger's should_show_sysmsg (uses deployment internally)
    if hasattr(display, 'zcli'):
        zcli = display.zcli
        
        # Check via logger (preferred method)
        if zcli and hasattr(zcli, 'logger') and hasattr(zcli.logger, 'should_show_sysmsg'):
            return zcli.logger.should_show_sysmsg()
        
        # Priority 2: Check via config deployment mode
        if zcli and hasattr(zcli, 'config'):
            # Suppress in both Production AND Testing modes (only show in Development)
            if hasattr(zcli.config, 'is_production') and zcli.config.is_production():
                return False
            
            # Check for Testing mode
            if hasattr(zcli.config, 'environment') and hasattr(zcli.config.environment, 'is_testing'):
                if zcli.config.environment.is_testing():
                    return False
            
            # Also check deployment string directly as fallback
            if hasattr(zcli.config, 'get_environment'):
                deployment = str(zcli.config.get_environment('deployment', '')).lower()
                if deployment in ['testing', 'info', 'production']:
                    return False
            
            return True
    
    # Priority 3: Fallback to legacy session debug flag
    debug = session.get("debug")
    if debug is not None:
        return debug
    
    # Default: show messages (development mode)
    return True


def get_display_logger(display: Any) -> Optional[Any]:
    """
    Get logger instance from display hierarchy with fallback.
    
    This provides a centralized way to access the logger from various
    display event contexts, handling the hierarchy of logger locations.
    
    Args:
        display: zDisplay instance (or event class with display reference)
    
    Returns:
        Optional[Any]: Logger instance, or None if not available
    
    Lookup Hierarchy:
        1. display.zcli.logger (preferred - full zCLI logger)
        2. display.logger (fallback - display-local logger)
        3. None (no logger available)
    
    Example:
        >>> logger = get_display_logger(self.display)
        >>> if logger:
        >>>     logger.debug("Event processing started")
    
    Usage:
        # In any event class
        logger = get_display_logger(self.display)
        if logger:
            logger.debug(f"[{event_name}] Processing: {context}")
    
    Notes:
        - Gracefully handles missing logger (returns None)
        - Prefers full zCLI logger over display-local logger
        - Safe to call from any event context
    
    Similar To:
        Logging patterns in display_event_system (zDialog methods)
    """
    if not display:
        return None
    
    # Try zcli.logger first (preferred)
    if hasattr(display, 'zcli'):
        zcli = display.zcli
        if zcli and hasattr(zcli, 'logger'):
            return zcli.logger
    
    # Fallback to display.logger
    if hasattr(display, 'logger'):
        return display.logger
    
    # No logger available
    return None


def log_event_start(
    logger: Optional[Any],
    event_name: str,
    context: Dict[str, Any]
) -> float:
    """
    Log event start with context (debug mode only).
    
    This provides consistent event start logging with context details,
    useful for debugging and performance tracking.
    
    Args:
        logger: Logger instance from get_display_logger()
        event_name: Event name (e.g., "zDialog", "zDash", "zTable")
        context: Event context dictionary (keys only logged, not values for security)
    
    Returns:
        float: Start timestamp (for duration calculation with log_event_end)
    
    Example:
        >>> logger = get_display_logger(self.display)
        >>> start_time = log_event_start(logger, "zDialog", context)
        >>> # ... event processing ...
        >>> log_event_end(logger, "zDialog", time.time() - start_time)
    
    Usage:
        # In event method
        logger = get_display_logger(self.display)
        start_time = log_event_start(logger, "zDialog", {
            "fields": context.get("fields", []),
            "model": context.get("model")
        })
    
    Notes:
        - Only logs if logger available and in debug mode
        - Logs context keys only (not values) for security
        - Returns timestamp for duration tracking
        - Gracefully handles None logger (no-op)
    
    Similar To:
        display_event_system._log_zdialog_start() (line 1671-1679)
    """
    start_time = time.time()
    
    if not logger:
        return start_time
    
    logger.debug(f"\n{'='*80}")
    logger.debug(f"[{event_name}] 📋 EVENT STARTED - Context: {list(context.keys())}")
    logger.debug(f"{'='*80}\n")
    
    return start_time


def log_event_end(
    logger: Optional[Any],
    event_name: str,
    duration: float
) -> None:
    """
    Log event completion with duration.
    
    This provides consistent event completion logging with performance metrics.
    
    Args:
        logger: Logger instance from get_display_logger()
        event_name: Event name (e.g., "zDialog", "zDash", "zTable")
        duration: Event duration in seconds (from start_time to now)
    
    Returns:
        None
    
    Example:
        >>> start_time = log_event_start(logger, "zDialog", context)
        >>> # ... event processing ...
        >>> log_event_end(logger, "zDialog", time.time() - start_time)
    
    Usage:
        # In event method
        logger = get_display_logger(self.display)
        start_time = log_event_start(logger, "zDialog", context)
        try:
            # Event processing
            pass
        finally:
            log_event_end(logger, "zDialog", time.time() - start_time)
    
    Notes:
        - Only logs if logger available and in debug mode
        - Formats duration as milliseconds (ms) for readability
        - Gracefully handles None logger (no-op)
    
    Similar To:
        Logging patterns in display_event_timebased
    """
    if not logger:
        return
    
    duration_ms = duration * 1000  # Convert to milliseconds
    logger.debug(f"[{event_name}] ✅ EVENT COMPLETE - Duration: {duration_ms:.2f}ms")
