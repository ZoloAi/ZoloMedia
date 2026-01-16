"""
zOS Open Utilities

Lightweight, dependency-free file and URL opening primitives for the zOS layer.
Provides basic OS-level opening operations without UI frameworks.

Architecture:
    - zOS Layer: Primitive operations (this module) - returns bool
    - zKernel Layer: Framework operations (zOpen with hooks/dialogs) - returns "zBack"/"stop"

Key Features:
    - Simple subprocess-based opening
    - Reads preferences from zMachine config
    - Cross-platform support (macOS, Linux, Windows)
    - No dependencies on zKernel subsystems
    - Suitable for CLI and scripting

Usage:
    from zOS.utils.open import open_file, open_url, is_url
    
    # Open file in IDE
    success = open_file("/path/to/file.py")  # Uses IDE from zConfig
    success = open_file("/path/to/file.py", editor="cursor")  # Explicit
    
    # Open URL in browser
    success = open_url("https://example.com")  # Uses browser from zConfig
    success = open_url("https://example.com", browser="chrome")  # Explicit
    
    # Detect URL
    if is_url("www.google.com"):
        open_url("www.google.com")

Version: 1.0.0
"""

from .core import open_file, open_url, is_url

__all__ = ['open_file', 'open_url', 'is_url']
