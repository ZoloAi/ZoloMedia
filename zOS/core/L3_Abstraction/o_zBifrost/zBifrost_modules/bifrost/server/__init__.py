# zCLI/subsystems/zComm/zComm_modules/bifrost/__init__.py
"""
zBifrost WebSocket Bridge Package.

Provides secure WebSocket server with event-driven architecture for real-time
communication between Python backend and JavaScript frontend clients.

Exports:
    zBifrost: Main WebSocket bridge class for server lifecycle management

Architecture:
    Uses modular implementation (bifrost_bridge.py) for improved
    maintainability and separation of concerns. Event handlers are organized
    in bridge_modules/ for clean event-driven design.
    
    Access broadcasting and server start through zCLI.comm.bifrost instance
    or create a zBifrost instance directly for full control.
"""

from .bifrost_bridge import zBifrost

__all__ = ['zBifrost']
