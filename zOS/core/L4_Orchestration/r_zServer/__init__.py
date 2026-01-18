# zCLI/subsystems/zServer/__init__.py

"""
zServer - HTTP/WSGI Server Subsystem

Deployment-aware HTTP server supporting both Development and Production modes:
- Development/Testing: Python's built-in http.server (background thread)
- Production: Gunicorn WSGI server (subprocess)

Features:
- Declarative routing via zServer.*.yaml files
- Auto-detection of routes configuration
- Template rendering with Jinja2
- Static file serving
- RBAC integration via zAuth
- Form handling (zDialog pattern for web)
- JSON API endpoints

Layer: 1 (Core Subsystem)
Dependencies: zConfig, zComm (network primitives), zAuth (optional for RBAC)
"""

from .zServer import zServer

__all__ = ['zServer']

# Subsystem metadata
SUBSYSTEM_NAME = "zServer"
SUBSYSTEM_LAYER = 1  # Core subsystem
SUBSYSTEM_VERSION = "1.5.8"

