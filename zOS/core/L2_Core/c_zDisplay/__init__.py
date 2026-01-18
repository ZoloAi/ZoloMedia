# zCLI/subsystems/zDisplay/__init__.py

"""
zDisplay: Layer 1 UI subsystem for zCLI.

Provides event-driven rendering, input collection, and multi-mode output
supporting both Terminal and zBifrost (WebSocket/GUI) modes.

Architecture:
    - Unified event routing through handle() method
    - Multi-mode support (Terminal, zBifrost) transparently
    - Delegates to specialized modules (primitives, events)
"""

from .zDisplay import zDisplay
from .zDisplay_modules.display_constants import *

__all__ = ['zDisplay']
