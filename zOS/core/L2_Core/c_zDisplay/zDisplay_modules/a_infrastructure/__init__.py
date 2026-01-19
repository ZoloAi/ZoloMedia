# zCLI/L2_Core/c_zDisplay/zDisplay_modules/a_infrastructure/__init__.py

"""
Tier 0 Infrastructure - Display Event Helpers
==============================================

Public API for foundational infrastructure used by all display events.
"""

from .display_event_helpers import (
    generate_event_id,
    is_bifrost_mode,
    try_gui_event,
    emit_websocket_event,
    safe_get_nested
)

from .display_rendering_utilities import (
    render_field,
    render_section_title,
    get_color_code,
    output_text_via_basics,
    format_value_for_display
)

from .display_logging_helpers import (
    should_show_system_message,
    get_display_logger,
    log_event_start,
    log_event_end
)

__all__ = [
    # Event helpers
    'generate_event_id',
    'is_bifrost_mode',
    'try_gui_event',
    'emit_websocket_event',
    'safe_get_nested',
    # Rendering utilities
    'render_field',
    'render_section_title',
    'get_color_code',
    'output_text_via_basics',
    'format_value_for_display',
    # Logging helpers
    'should_show_system_message',
    'get_display_logger',
    'log_event_start',
    'log_event_end'
]

