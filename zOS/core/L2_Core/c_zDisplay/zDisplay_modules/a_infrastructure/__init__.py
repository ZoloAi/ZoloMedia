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
    emit_websocket_event
)

__all__ = [
    'generate_event_id',
    'is_bifrost_mode',
    'try_gui_event',
    'emit_websocket_event'
]

