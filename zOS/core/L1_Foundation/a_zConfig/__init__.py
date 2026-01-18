# zCLI/subsystems/zConfig/__init__.py
"""
zConfig - Cross-platform configuration management subsystem.

Provides hierarchical configuration loading, machine/environment detection,
session management, and logging infrastructure for the zCLI framework.

Key Responsibilities:
    - Cross-platform path resolution using OS-native conventions
    - Auto-detection of machine characteristics (OS, browser, IDE, memory, CPU)
    - Environment configuration (deployment, logging, networking, security)
    - Session lifecycle management (session ID, workspace, runtime state)
    - Logger configuration and management
    - WebSocket and HTTP server configuration
    - Configuration persistence (saving user preferences)

Exports:
    zConfig: Main configuration management class
"""

from .zConfig import zConfig

__all__ = ['zConfig']
