# zCLI/subsystems/zComm/zComm_modules/bifrost/bridge_modules/events/__init__.py
"""
zBifrost Event Handlers Package.

Provides domain-specific event handlers for the zBifrost WebSocket bridge,
enabling clean separation of concerns through event-driven architecture.
Each handler specializes in a specific aspect of bridge functionality.

Exports:
    ClientEvents: Handles client lifecycle events (connect, disconnect, input responses)
    CacheEvents: Handles cache operations (schema retrieval, cache clearing, stats)
    DiscoveryEvents: Handles model discovery and introspection requests
    DispatchEvents: Handles command dispatch and execution with caching support

Architecture:
    Event handlers are organized by domain responsibility, allowing the message
    handler to route incoming messages to the appropriate specialist. This design
    promotes maintainability and testability of the WebSocket bridge logic.

Naming Convention:
    All event handler files use the bridge_event_ prefix to distinguish them from
    other event handlers (e.g., display_event_) in the zCLI ecosystem.
"""

from .bridge_event_client import ClientEvents
from .bridge_event_cache import CacheEvents
from .bridge_event_discovery import DiscoveryEvents
from .bridge_event_dispatch import DispatchEvents

__all__ = [
    'ClientEvents',
    'CacheEvents',
    'DiscoveryEvents',
    'DispatchEvents'
]

