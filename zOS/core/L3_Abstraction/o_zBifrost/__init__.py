# zCLI/subsystems/zBifrost/__init__.py
"""
zBifrost - Terminal↔Web Bridge Orchestrator (Layer 2)

Coordinates real-time communication between Terminal and Web environments by
orchestrating zCLI subsystems over WebSocket infrastructure.

Architecture:
    - Uses z.comm for low-level WebSocket server infrastructure
    - Coordinates z.display for rendering events to web clients
    - Integrates z.auth for three-tier client authentication
    - Manages z.data for CRUD operations from web UI

Exports:
    zBifrost: Main Layer 2 orchestrator facade

Usage:
    ```python
    from zOS import zOS
    
    z = zCLI()
    
    # Start WebSocket bridge
    z.bifrost.start()
    
    # Broadcast event to all connected clients
    z.bifrost.broadcast({"event": "update", "data": {...}})
    
    # Check bridge health
    status = z.bifrost.health_check()
    ```
"""

from .zBifrost import zBifrost

__all__ = ['zBifrost']

