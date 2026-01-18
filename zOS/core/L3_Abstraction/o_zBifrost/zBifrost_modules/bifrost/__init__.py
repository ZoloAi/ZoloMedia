# zCLI/subsystems/zComm/zComm_modules/bifrost/__init__.py
"""
zBifrost WebSocket Bridge Package.

Provides secure WebSocket server with event-driven architecture for real-time
communication between Python backend and JavaScript frontend clients.

Exports:
    zBifrost: Main WebSocket bridge class for server lifecycle management

Architecture:
    - server/: Python backend (bifrost_bridge.py + modules)
    - client/: JavaScript client (bifrost_client.js + modules)
    - docs/: Shared documentation
    
    Access broadcasting and server start through zCLI.comm.bifrost instance
    or create a zBifrost instance directly for full control.
"""

from .server.bifrost_bridge import zBifrost

__all__ = ['zBifrost']

