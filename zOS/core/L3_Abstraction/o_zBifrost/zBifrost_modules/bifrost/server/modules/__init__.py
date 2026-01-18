# zCLI/subsystems/zComm/zComm_modules/bifrost/bridge_modules/__init__.py
"""
Bifrost Bridge Modules Package.

Provides modular server-side components that power the zBifrost WebSocket bridge,
handling client connections, authentication, caching, and message routing between
Python backend and JavaScript frontend.

Exports:
    CacheManager: Manages schema and data caching for improved performance
    AuthenticationManager: Handles client authentication and authorization
    MessageHandler: Routes and dispatches messages between client and backend
    ConnectionInfoManager: Tracks connection state and client metadata

Architecture:
    These modules work together to provide a clean separation of concerns within
    the zBifrost bridge, enabling event-driven communication and maintainable
    server-side logic.
"""

from .bridge_cache import CacheManager
from .bridge_auth import AuthenticationManager
from .bridge_messages import MessageHandler
from .bridge_connection import ConnectionInfoManager

__all__ = [
    'CacheManager',
    'AuthenticationManager',
    'MessageHandler',
    'ConnectionInfoManager'
]

